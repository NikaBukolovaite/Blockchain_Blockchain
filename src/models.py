import random
from src.hashing import aes_hashing

# Vartotojas su UTXO
class User:
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key
        self._utxos = []  # Private UTXO
        self._balance = 0  # Private balance

    def add_utxo(self, amount):
        utxo = aes_hashing(f"{self.public_key}|{amount}|{random.randint(1, 10000)}".encode()).hex()
        self._utxos.append((utxo, amount))
        self._balance += amount

    def get_balance(self):
        return self._balance

    def get_utxos(self):
        return self._utxos

    def remove_utxos(self, used_utxos):
        self._utxos = [utxo for utxo in self._utxos if utxo[0] not in used_utxos]
        self._balance = sum([value for _, value in self._utxos])

# Vartotojų generavimas (~1000 vartotojų)
def generate_users(num_users=1000):
    users = []
    for i in range(num_users):
        name = f"User_{i+1}"
        public_key = aes_hashing(f"{name}{random.randint(1, 10000)}".encode()).hex()
        user = User(name, public_key)
        # vietoje fiksuotu 10 mazu UTXO – parenkame tiksline pradine suma ir suskaidome i kelis UTXO
        target_total = random.randint(100, 1000000)
        if target_total < 1000:
            user.add_utxo(target_total)
        else:
            # atsitiktinis UTXO kiekis (5–15), kad islaikyti realistiška „mozaika“
            n_utxos = random.randint(5, 15)
            remaining = target_total
            for _ in range(n_utxos - 1):
                low = max(100, remaining // 100)
                high = max(low, remaining // 5)
                chunk = random.randint(low, high)
                remaining -= chunk
                user.add_utxo(chunk)
                if remaining <= 100:
                    break
            if remaining > 0:
                user.add_utxo(remaining)
        users.append(user)
    return users

# Transakcija (UTXO modelis)
class Transaction:
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.inputs = []
        self.outputs = []
        self.transaction_id = None
        # pridėtas tx_nonce, kad id būtų sunkiau koliduoti bei patogiau validacijai
        self.tx_nonce = random.randint(1, 1000000000)

    def _compute_tx_id(self):
        # skaičiuojame hash nuo VISKO: sender_pk, receiver_pk, amount, tx_nonce, surikiuoti inputs/outputs
        sender_pk = self.sender.public_key
        receiver_pk = self.receiver.public_key

        # surikiuojame inputs pagal UTXO id
        sorted_inputs = sorted(self.inputs, key=lambda x: x[0])  # (utxo_id, utxo_value)
        # surikiuojame outputs pagal (pk, amount)
        sorted_outputs = sorted(self.outputs, key=lambda x: (x[0], x[1]))  # (pk, amount)

        parts = []
        parts.append(f"sender={sender_pk}")
        parts.append(f"receiver={receiver_pk}")
        parts.append(f"amount={self.amount}")
        parts.append(f"tx_nonce={self.tx_nonce}")
        parts.append("inputs=[")
        for utxo_id, utxo_val in sorted_inputs:
            parts.append(f"{utxo_id}:{utxo_val}")
        parts.append("]")
        parts.append("outputs=[")
        for pk, val in sorted_outputs:
            parts.append(f"{pk}:{val}")
        parts.append("]")

        serialized = "|".join(parts).encode()
        return aes_hashing(serialized).hex()

    def generate_transaction(self):
        # čia UTXO NEUŽRAŠOM – tik parenkame inputs ir suformuojame outputs (įskaitant grąžą)
        remaining_amount = self.amount
        available_utxos = self.sender.get_utxos()
        total_utxo_value = sum(value for _, value in available_utxos)

        if total_utxo_value < self.amount:
            print(f"Siuntėjas {self.sender.name} turi tik {total_utxo_value} pinigų, bet reikia {self.amount}.")
            raise ValueError("Siuntėjas neturi pakankamai pinigų.")

        used = []
        acc = 0
        for utxo, value in available_utxos:
            used.append((utxo, value))
            acc += value
            if acc >= remaining_amount:
                break

        if acc < remaining_amount:
            print(f"Siuntėjas {self.sender.name} turi tik {total_utxo_value} pinigų, bet reikia {self.amount}.")
            raise ValueError("Siuntėjas neturi pakankamai pinigų.")  # papildoma sauga

        # inputs = sunaudojame pilnus UTXO (klasikinis UTXO modelis)
        self.inputs = used[:]  

        # outputs = 1) gavėjui visa suma 2) siuntėjui grąža (jei liko)
        change = acc - remaining_amount
        self.outputs = [(self.receiver.public_key, self.amount)]
        if change > 0:
            self.outputs.append((self.sender.public_key, change))

        # transaction_id (pilna informacija)
        self.transaction_id = self._compute_tx_id()

    def validate_transaction_id(self):
        id_validation = self._compute_tx_id()
        return id_validation == self.transaction_id

# Transakcijų generavimas (~10 000)
def generate_transactions(users, num_transactions=10000):
    transactions = []
    for _ in range(num_transactions):
        sender = random.choice(users)
        receiver = random.choice(users)
        amount = random.randint(1, 1000)
        tx = Transaction(sender, receiver, amount)
        try:
            tx.generate_transaction()
            if not tx.validate_transaction_id():
                raise ValueError(f"Transakcijos ID neteisingas: {tx.transaction_id}")
            transactions.append(tx)
        except ValueError as e:
            print(f"Transakcija nepavyko: {e}")
    return transactions
