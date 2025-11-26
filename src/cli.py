import sys
from src.models import generate_users, generate_transactions
from src.chain import Blockchain
from src.mining import mine_blockchain, distributed_mining
from src.paths import out_path

def parse_flags(argv):
    # Paprastas flag'ų parsinimas: --append, --overwrite, --users=N, --tx=N, --block-size=N, --difficulty=N, --print-txs, --tx-preview=N
    flags = {
        "append": False,
        "overwrite": True,
        "users": 1000,
        "tx": 10000,
        "block_size": 100,
        "difficulty": 3,
        "print_txs": False,  # jei True – visos TX bus spausdinamos konsolėje
        "tx_preview": 3,     # jei print_txs=False – tiek pirmų TX spausdinti
        "parallel": False,
        "candidates": 5,
        "max_attempts": 10000,
        "workers": None,
        "get_block": None,   # NEW: užklausa dėl bloko
        "get_tx": None       # NEW: užklausa dėl transakcijos
    }
    for a in argv:
        al = a.lower()
        if al == "--append":
            flags["append"] = True
            flags["overwrite"] = False
        elif al == "--overwrite":
            flags["append"] = False
            flags["overwrite"] = True
        elif al.startswith("--users="):
            try:
                flags["users"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --users reikšmė, naudosime numatytą: 1000")
        elif al.startswith("--tx="):
            try:
                flags["tx"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --tx reikšmė, naudosime numatytą: 10000")
        elif al.startswith("--block-size="):
            try:
                flags["block_size"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --block-size reikšmė, naudosime numatytą: 100")
        elif al.startswith("--difficulty="):
            try:
                flags["difficulty"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --difficulty reikšmė, naudosime numatytą: 3")
        elif al == "--print-txs":
            flags["print_txs"] = True
        elif al.startswith("--tx-preview="):
            try:
                flags["tx_preview"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --tx-preview reikšmė, naudosime numatytą: 3")
        elif al == "--parallel":
            flags["parallel"] = True
        elif al.startswith("--candidates="):
            try:
                flags["candidates"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --candidates reikšmė, naudosime 5")
        elif al.startswith("--max-attempts="):
            try:
                flags["max_attempts"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --max-attempts reikšmė, naudosime 10000")
        elif al.startswith("--workers="):
            try:
                flags["workers"] = int(al.split("=", 1)[1])
            except:
                print("Neteisinga --workers reikšmė, ignoruojame")
        elif al.startswith("--get-block="):      # NEW
            flags["get_block"] = al.split("=", 1)[1]
        elif al.startswith("--get-tx="):         # NEW
            flags["get_tx"] = al.split("=", 1)[1]
        else:
            if al.startswith("--"):
                print(f"Nežinomas flag'as: {a} (ignoruojame)")
    return flags

def main():
    # Flag'ai
    flags = parse_flags(sys.argv[1:])
    append_mode = flags["append"]
    users_n = flags["users"]
    tx_n = flags["tx"]
    block_size = flags["block_size"]
    difficulty = flags["difficulty"]

    print("Generuojame vartotojus ir transakcijas...")
    users = generate_users(users_n)
    transactions = generate_transactions(users, tx_n)
    blockchain = Blockchain(difficulty=difficulty)

    # Failų vardai pagal režimą — VISI į output/
    if flags["parallel"]:
        block_file = out_path("parallel_block_output.txt")
        mining_file = out_path("parallel_mining_log.txt")
    else:
        block_file = out_path("sequential_block_output.txt")
        mining_file = out_path("sequential_mining_log.txt")

    # Visą srautą daro kasimo funkcija, kuri pati teisingai tvarko Block ID didėjimą.
    if flags["parallel"]:
        # v0.2 — kartojam, kol mempool ištuštės
        while transactions:
            before = len(transactions)
            distributed_mining(
                blockchain,
                transactions,
                users,
                block_size=block_size,
                difficulty=difficulty,
                num_candidates=flags["candidates"],
                max_attempts=flags["max_attempts"],
                block_file=block_file,     # -> output/
                mining_file=mining_file,   # -> output/
                workers=flags["workers"],
                print_txs=flags["print_txs"],
                tx_preview=flags["tx_preview"]
            )
            # sauga nuo įstrigimo (jei dėl kokių priežasčių blokas nepašalino TX)
            after = len(transactions)
            if after >= before:
                print("Nerasta pažangos per šį ciklą, stabdome.")
                break
    else:
        mine_blockchain(
            blockchain,
            transactions,
            users,  # perduodame users, kad outputs būtų galima priskirti pagal public_key
            block_size=block_size,
            difficulty=difficulty,
            block_file=block_file,        # -> output/
            mining_file=mining_file,      # -> output/
            append_mode=append_mode,
            print_txs=flags["print_txs"],
            tx_preview=flags["tx_preview"]
        )

    # Užklausos apie bloką / transakciją po kasimo (bitcoin-cli stiliaus)
    if flags["get_block"] is not None:
        try:
            blk_id = int(flags["get_block"])
        except:
            blk_id = None
        if blk_id is None:
            print("[QUERY] Blogas --get-block parametras (turi būti sveikas skaičius).")
        else:
            blk = blockchain.find_block_by_id(blk_id)
            if blk:
                print(f"[QUERY] Block #{blk.block_id} | hash={blk.hash} | ts={blk.timestamp} | txs={len(blk.transactions)}")
            else:
                print("[QUERY] Block not found")

    if flags["get_tx"] is not None:
        tx = blockchain.find_tx_by_id(flags["get_tx"])
        if tx:
            print(f"[QUERY] TX {tx.transaction_id} | {tx.sender.name} -> {tx.receiver.name} | amount={tx.amount}")
            print(f"        inputs={tx.inputs}")
            print(f"        outputs={tx.outputs}")
        else:
            print("[QUERY] Transaction not found")

if __name__ == "__main__":
    main()
