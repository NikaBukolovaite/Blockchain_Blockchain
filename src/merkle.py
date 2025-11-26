from src.hashing import aes_hashing

def calculate_merkle_root(transactions):
    # surenkame transakcijų ID
    merkle = [tx.transaction_id for tx in transactions]

    if not merkle:
        return None

    # kartojame, kol lieka vienas hash
    while len(merkle) > 1:

        # nelyginis elementų skaičius → duplikuojame paskutinį
        if len(merkle) % 2 != 0:
            merkle.append(merkle[-1])

        new_level = []

        # imam hash'us poromis
        for i in range(0, len(merkle), 2):
            left = bytes.fromhex(merkle[i])
            right = bytes.fromhex(merkle[i+1])

            combined = left + right

            new_hash = aes_hashing(combined).hex()
            new_level.append(new_hash)

        merkle = new_level

    return merkle[0]