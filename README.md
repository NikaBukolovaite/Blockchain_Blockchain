# 💻 Blockchain

Supaprastinta **blokų grandinė**, imituojanti UTXO modelį, transakcijų atranką į blokus, Merkle šaknį ir Proof‑of‑Work (PoW) kasimą. Visos maišos daromos su užduotyje pateikta **AES pagrindu sukurta maišos funkcija**.

---

# Blockchain papildoma

## Turinys

- [Libbitcoin diegimas]()
- [Merkle.cpp failo sukūrimas]()
- [Kompiliavimas ir klaidų taisymas]()
- [Bitcoin bloko #100000 testavimas]()
- [create_merkle integravimas į Python blockchain projektą]()
- [Naudotos nuotraukos]()

---

## Libbitcoin diegimas

Kadangi mano kompiuteryje Windows, tai turėjau per "Turn Windows features on or off" įjungti "Windows Subsystem for Linux".

Tada atsisiunčiau "Ubuntu 22.04.5 LTS".

Pirmą kartą paleidžiant Ubuntu:

- sistema paprašė susikurti naudotojo vardą, ir slaptažodį.

Kai paruošiau terminalą, į jį suvedžiau:

```bash
sudo apt update
sudo apt install build-essential autoconf automake libtool pkg-config git wget -y
```

```bash
wget https://raw.githubusercontent.com/libbitcoin/libbitcoin/version3/install.sh
chmod +x install.sh
```

```bash
./install.sh --prefix=$HOME/libbitcoin --build-boost --disable-shared
```

---

## Merkle.cpp failo sukūrimas

Kad pratestuoti duotą kodą, sukūriau atskirą aplankalą Merkle testui:

```bash
mkdir ~/libbitcoin-merkle
cd ~/libbitcoin-merkle
```

Tam folder'yje sukūriau failą:

```bash
nano merkle.cpp
```

ir įkėliau užduotyje pateiktą c++ kodą.

---

## Kompiliavimas ir klaidų taisymas

Pirmas bandymas kompiliuoti:

```bash
g++ -std=c++11 merkle.cpp $(pkg-config --cflags --libs libbitcoin-system) -o merkle_test
```

Klaida:

```bash
error: ‘system’ is not a namespace-name
namespace bc = libbitcoin::system;
```

Kad pataisyti, turėjau ištrinti ::system ir pailikti:

```bash
namespace bc = libbitcoin;
```

Po pataisymo kodas sėkmingai veikė.

---

## c++ implemintavimas

Užduotyje pateiktą c++ create_merkle() funkciją perrašiau į Python, bet su AI pagalba perrašiau prie blockchain projekto:

- vietoj SHA256 naudojame mūsų aes_hashing()
- vietoj libbitcoin – paprastas sąrašas

Galutinė Python versija:

```bash
from src.hashing import aes_hashing

def calculate_merkle_root(transactions):
    merkle = [tx.transaction_id for tx in transactions]
    if not merkle:
        return None
    while len(merkle) > 1:
        if len(merkle) % 2 != 0:
            merkle.append(merkle[-1])
        new_level = []
        for i in range(0, len(merkle), 2):
            left = bytes.fromhex(merkle[i])
            right = bytes.fromhex(merkle[i+1])
            combined = left + right
            new_level.append(aes_hashing(combined).hex())
        merkle = new_level
    return merkle[0]
```

---

## Bitcoin bloko 100000 patikrinimas

Kad patikrinti kodą su originaliais bitcoin blokais šiame tinklapyje - https://bitaps.com/100000
Įkėliau 4 tranzakcijų hash ir tada paleidau programą, bet pirmą kartą paleidus rezultatas nesutapo su originaliu Merkle root.

<div align="center">
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234916.png" alt="sequential_block_output.txt ištrauka" width="380" />
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/6b4b44aab9c552a3966e6cb2fa18f3faee8469dc/imagines/blokas.png" alt="block_output.txt ištrauka" width="380" />
</div>

Kad pataisyti šitą kode reikėjo pakeisti šią eilutę

```bash
bc::encode_base16(merkle_root)
```

į šią

```bash
bc::encode_hash(merkle_root)

```

Ir rezultatas gavosi teisingas

---

# Blockchain

## Turinys

- [Apžvalga](#apžvalga)
- [Projekto struktūra](#projekto-struktūra)
- [Funkcijos](#funkcijos)
- [Ekrano nuotraukos ir demonstracija](#ekrano-nuotraukos-ir-demonstracija)
- [Architektūra](#architektūra)
- [Programos paleidimas](#programos-paleidimas)
- [Neteisingų flag’ų atvejai](#neteisingų-flagų-atvejai)
- [Konfigūracija (CLI flag'ai)](#konfigūracija-cli-flagai)
- [Neteisingų flag'ų atvejai](#neteisingų-flagų-atvejai)
- [Išvesties režimai](#išvesties-režimai)
- [Kaip tai veikia?](#kaip-tai-veikia)
- [Unit testai](#unit-testai)
- [AI pagalba](#ai-pagalba)

---

## Apžvalga

Programa generuoja vartotojus (UTXO mozaika), kuria atsitiktines transakcijas, formuoja blokus, apskaičiuoja **Merkle root** ir kasa blokus pagal **PoW**: kol bloko antraštės maiša prasideda `difficulty` nuliais. Patvirtinus bloką atnaujinamos UTXO būsenos.

---

## Programos struktūra

projekto_aplankas/
├─ src/
│ ├─ hashing.py # AES pagrindu hash funkcija ir helper’iai
│ ├─ models.py # User, Transaction; generate_users(), generate_transactions()
│ ├─ merkle.py # calculate_merkle_root()
│ ├─ block.py # Block klasė, bloko header/hash
│ ├─ chain.py # Blockchain klasė, create_new_block()
│ ├─ mining.py # mine_blockchain(), distributed_mining(), išvedimai į failus
│ ├─ cli.py # įėjimo taškas: flag’ai ir main()
│ └─ paths.py # output/ katalogo utilitai: ensure_output_dir(), out_path()
├─ tests/
│ └─ test_blockchain.py
└─ output/ # visi .txt išvedimai

---

## Funkcijos

- **UTXO modelis** su grąža siuntėjui.
- **Transakcijų ID** iš kanonizuotos reprezentacijos per `aes_hashing()`.
- **Merkle root** su poravimu ir dubliavimu nelyginiam kiekiui.
- **PoW kasimas** su `difficulty` nuliais hash pradžioje.
- **Dviginės panaudos prevencija** kasimo metu (tikrinami įėjimo UTXO egzistavimai).
- **Išvedimai**: konsolėje ir tekstiniuose failuose.
- **Konsolės peržiūra**: po kiekvieno bloko į konsolę išvedamos pirmos N transakcijų (numatytai N=3) arba visos, jei taip nurodoma flag’u.
- **Lygiagretus kasimas**: keli kandidatų blokai kasama su `ProcessPoolExecutor`. Laimi pirmas radęs tinkamą hash; palaikomi `--candidates`, `--workers`, `--max-attempts`.

---

## Ekrano nuotraukos ir demonstracija

**Konsolės eiga (kasimas):**

<div align="center">
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234453.png" alt="Konsolės ištrauka" width="380" />
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234506.png" alt="Konsolės ištrauka" width="380" />
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234732.png" alt="Konsolės ištrauka, kai lygiagretus kasimas" width="380" />
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234751.png" alt="Konsolės ištrauka, kai lygiagretus kasimas" width="380" />
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234809.png" alt="Konsolės ištrauka, kai paleidžiami Unit testai" width="380" />
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/6b4b44aab9c552a3966e6cb2fa18f3faee8469dc/imagines/blokas.png" alt="block_output.txt ištrauka" width="380" />
</div>

**Failų išvestys:**

<div align="center">
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234916.png" alt="sequential_block_output.txt ištrauka" width="380" />
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234924.png" alt="sequential_mining_log ištrauka" width="380" />
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234846.png" alt="parallel_block_output.txt ištrauka" width="380" />
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234856.png" alt="parallel_mining_log.txt ištrauka" width="380" />
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234821.png" alt="block_output.txt ištrauka" width="380" />
  <img src="https://github.com/NikaBukolovaite/Blockchain_Blockchain/blob/0cee6598fa6e569a3a6f64a41375377524a6ebdf/imagines/Screenshot%202025-11-05%20234829.png" alt="mining_log.txt ištrauka" width="380" />
</div>

---

## Architektūra

- **User** – vardas, `public_key` (iš `aes_hashing`), privatūs UTXO ir balansas.
- **Transaction** – `sender`, `receiver`, `amount`, `inputs`, `outputs`, `tx_nonce`, `transaction_id`.
- **Block** – `block_id`, `prev_block_hash`, `timestamp`, `version`, `merkle_root`, `nonce`, `difficulty`, transakcijų sąrašas.
- **Blockchain** – blokų seka ir pagalbinės funkcijos (`get_last_hash`, `add_block`).
- **Merkle** – poruojami TX ID (`hex` → `bytes`), dubliuojamas paskutinis, kol lieka šaknis.
- **PoW** – `calculate_hash()` virš 6 antraštės laukų; ieškoma `0...` prefikso.

---

## Programos paleidimas

Paleisti programą su default nustatymais galima į konsolę įvedus:

```bash
python -m src.cli
```

Norint paleisti programą su pasirinktu(ais) parametrais:

```bash
python -m src.cli --users=1000 --tx=10000 --block-size=100 --difficulty=3 --overwrite
```

> Pastaba: nebūtina nurodyti visų flagų — galite pasirinkti tik reikiamus, o likusieji bus pritaikyti pagal numatytąsias reikšmes.
> Pastaba: flag'ai nurodyti skiltyje - [Konfigūracija (CLI flag'ai)](#konfigūracija-cli-flagai)

## Neteisingų flag’ų atvejai

- **Neatpažintas flag’as** (pvz., `--usres=10`, `--users` be `=`)  
  → Išvedamas pranešimas _„Nežinomas flag'as: … (ignoruojame)”_, flag’as **ignoruojamas**, taikomos **numatytosios** reikšmės.

- **Teisingas flag’as, bet bloga reikšmė** (pvz., `--users=abc`, `--tx=10k`, `--difficulty=low`)  
  → Išvedamas pranešimas _„Neteisinga --<pavadinimas> reikšmė, naudosime numatytą: …”_, o reikšmė nustatoma į **default** (`users=1000`, `tx=10000`, `block_size=100`, `difficulty=3`).

- **Mišinys: keli teisingi + keli klaidingi**  
  → Teisingi pritaikomi, klaidingi **ignoruojami** arba **nustatomi į default**. Programa **tęsia darbą** (klaidos nefatalinės).

- **Dublikatai** (tą patį parametrą nurodei kelis kartus)  
  → „Laimi“ **paskutinis** paminėjimas eilėje.  
  Pvz.: `--users=500 --users=2000` ⇒ galutinis `users=2000`.

- **`--append` ir `--overwrite` kartu**  
  → „Laimi“ **paskutinis**:  
  `--append --overwrite` ⇒ **perrašys** failus;  
  `--overwrite --append` ⇒ **pridės** prie esamų failų.

> Pastaba: loginės ribos šiuo metu netikrinamos (tik ar reikšmė paverčiama į `int`).

### Pavyzdžiai

```bash
# Klaidinga reikšmė ir neatpažintas flag'as:
python -m src.cli --users=abc --tx=5000 --foo=bar
# Rezultatas: users → 1000 (default), tx → 5000; --foo ignoruotas.

# Dublikatai:
python -m src.cli --users=500 --users=2000
# Rezultatas: users → 2000

# Abu režimai paminėti:
python -m src.cli --append --overwrite
# Rezultatas: rašys per naują (overwrite), nes paskutinis nugalėjo.
```

---

## Konfigūracija (CLI flag'ai)

| Flag                 | Reikšmė                                                 |  Numatytoji | Pastabos                                       |
| -------------------- | ------------------------------------------------------- | ----------: | ---------------------------------------------- |
| `--users=INT`        | Sugeneruojamų vartotojų skaičius                        |      `1000` | Didesnės reikšmės – daugiau RAM/CPU            |
| `--tx=INT`           | Sugeneruojamų transakcijų skaičius                      |     `10000` |                                                |
| `--block-size=INT`   | Transakcijų sk. viename bloke                           |       `100` | Parenkama iki `block-size` **atsitiktinių** TX |
| `--difficulty=INT`   | PoW sudėtingumas (nuliai hash pradžioje)                |         `3` | `3` → `000…` prefiksas                         |
| `--append`           | Rašyti **pridedant** prie failų                         |           — | Jei nenurodyta – veikia kaip `--overwrite`     |
| `--overwrite`        | Failus **perrašyti** nuo tuščio                         | **įjungta** |                                                |
| `--print-txs`        | Į konsolę spausdinti **visas** TX                       |           — | Jei nenaudojamas – rodomas tik **preview**     |
| `--tx-preview=INT`   | Į konsolę spausdinti **pirmas N** TX                    |         `3` | Ignoruojama, jei naudojamas `--print-txs`      |
| `--parallel`         | Įjungia lygiagretų kasimą                               |           — |                                                |
| `--candidates=INT`   | Kiek kandidatinių blokų kurti lygiagretam kasimui       |         `5` |                                                |
| `--max-attempts=INT` | Bandymų sk. kandidatui (didinamas, jei nieko neranda)   |     `10000` |                                                |
| `--workers=INT`      | Proceso skaičius (jei nenurodyta – parenkama pagal CPU) |           — |                                                |
| `--get-block=N`      | Po kasimo atspausdina bloko #N santrauką                |           — |                                                |
| `--get-tx=HEX`       | Po kasimo atspausdina transakciją pagal jos ID          |           — |                                                |

---

## Išvesties režimai

### 1) Sekvencinis paleidimas (numatytasis)

- Paleidimas: **be** `--parallel`.
- Failai:
  - `output/sequential_block_output.txt`
  - `output/sequential_mining_log.txt`
- Konsolė:
  - `Kasamas blokas X su N transakciju...`
  - `Blokas iskastas! Nonce=... Hash=...`
  - Gali būti daug **įspėjimų**:  
    `ĮSPĖJIMAS: TX praleista (nebėra input UTXO). Siuntėjas=User_...`  
    (tai vyksta dėl **UTXO validacijos po kasimo**).
  - Santrauka su `[SUMMARY] ...` (įtrauktų TX skaičius, likęs mempool, grandinės ilgis).

### 2) Lygiagretus paleidimas

- Paleidimas: su `--parallel` (ir, jei reikia, `--candidates`, `--workers`, `--max-attempts`).
- Failai:
  - `output/parallel_block_output.txt`
  - `output/parallel_mining_log.txt`
- Konsolė:
  - `Sukurta K kandidatinių blokų, pradedamas LYGIAGRETUS kasimas (W proc.)...`
  - Pirmasis radęs tinkamą hash laimi:  
    `Block #X mined. Attempts = A. Nonce = N`
  - **Įspėjimų apie praleistas TX nerasite** (šiame režime tik laimėtojo bloko TX tiesiogiai taikomi UTXO, be papildomo „missing inputs“ tikrinimo).
  - Galutinis `[SUMMARY]` vienoje eilutėje + `Block added...`.

### 3) Unit testų paleidimas

- Paleidimas: `python -m unittest discover -s tests -p "test_*.py" -v`
- Failai (pagal `mining.py` numatytas reikšmes, nes testai jų nepersiunčia):
  - `output/block_output.txt`
  - `output/mining_log.txt`
- Konsolė:
  - Testai nutildo `stdout/stderr`, todėl pamatysite tik unittest išvestį.
  - Vidiniai kasimo pranešimai/įspėjimai vis tiek rašomi į **failus** `output/`.

**Greitas pavyzdys:**

```bash
Kasamas blokas 100 su 83 transakciju...
Blokas iskastas! Nonce=5069 Hash=0004b6601ee36dcf8d40de14d884e9fc

ĮSPĖJIMAS: TX praleista (nebėra input UTXO). Siuntėjas=User_172
ĮSPĖJIMAS: TX praleista (nebėra input UTXO). Siuntėjas=User_351
ĮSPĖJIMAS: TX praleista (nebėra input UTXO). Siuntėjas=User_310
... (daug panašių įspėjimų praleista) ...
ĮSPĖJIMAS: TX praleista (nebėra input UTXO). Siuntėjas=User_759

Block ID: 100
Block Timestamp: 2025-11-05 22:54:48
Block Hash: 0004b6601ee36dcf8d40de14d884e9fc
  Transakcijų peržiūra (pirmos 3 iš 83):
  TX#1: User_172 -> User_506, amount=614
    Inputs:  [('7d426ce49609063b4876e3b855f29032', 8611)]
    Outputs: [('efd4fe88cdc292cd20ef6f6507177148', 614), ('1c8565212d3262dcdc9d6b7b61d91dcb', 7997)]
  TX#2: User_351 -> User_623, amount=973
    Inputs:  [('0f288fed00e1d343758b07378b95c4fb', 48914)]
    Outputs: [('0d7f28dd79f5258a263dba56a52a84a9', 973), ('ba33d7efe4db47bcf059af332fc1d579', 47941)]
  TX#3: User_310 -> User_423, amount=714
    Inputs:  [('ea9883cafa85feb0b9599a6d6738a9ae', 113084)]
    Outputs: [('0d962c24b86f4b7526913abc30af1991', 714), ('481c0754944851a859bb6897e7551e71', 112370)]
  … ir dar 80 transakcijų (pilna versija: block_output.txt)

[SUMMARY] Block #100 mined at difficulty 3
[SUMMARY] Hash=0004b6601ee36dcf8d40de14d884e9fc, nonce=5069
[SUMMARY] Included TXs: 0, mempool left: 0
[SUMMARY] Chain length: 100

```

---

## Kaip tai veikia?

Žemiau pateiktas pilnas duomenų srautas nuo atsitiktinių duomenų generavimo iki bloko įtraukimo į grandinę ir žurnalų išrašymo.

### 1) Duomenų generavimas

- `generate_users(N)`:
  - Sukuria ~N vartotojų su `name` ir `public_key` (pastarasis gaunamas iš `aes_hashing()`).
  - Kiekvienam vartotojui parenkama tikslinė suma `[100 .. 1_000_000]` ir suskaidoma į kelis UTXO (5–15 vnt., jei suma didesnė), kad gautųsi realistiškesnė „mozaika“.
- `generate_transactions(M)`:
  - Atsitiktinai parenka siuntėją ir gavėją, parenka sumą `[1 .. 1000]`.
  - `Transaction.generate_transaction()` **NEKEIČIA** bendros UTXO būsenos: tik **parenka** įėjimus (pilnus UTXO), apskaičiuoja grąžą ir suformuoja `outputs`.
  - `transaction_id` skaičiuojamas deterministiškai (`_compute_tx_id()`): `sender_pk`, `receiver_pk`, `amount`, `tx_nonce`, bei **surikiuoti** `inputs` ir `outputs` → `aes_hashing()`.

> Pastaba: šiame etape UTXO **dar nenuimami** — jie lieka pas siuntėją iki sėkmingo kasimo.

---

### 2) Bloko kandidatūra

- `create_new_block(transactions, block_id, prev_block_hash, block_size, difficulty)`:
  - Iš didesnio transakcijų sąrašo atsitiktinai paima iki `block_size` **kandidatų**.
  - Sukuria `Block`:
    - `prev_block_hash` gaunamas iš `Blockchain.get_last_hash()`:
      - jei grandinė tuščia → `00..00` (64 nuliai),
      - kitaip → paskutinio bloko `hash`.
    - `timestamp` (`YYYY-MM-DD HH:MM:SS`), `version=1`, `difficulty`, `nonce=0`.
    - `merkle_root = calculate_merkle_root(kandidatai)`.

> Pasirinktų transakcijų turinys (ir jų hash’ai) įeina į `merkle_root`, todėl **kasimas visada vyksta virš konkretaus kandidatų rinkinio**.

---

### 3) Merkle root (`calculate_merkle_root()`)

- Paimami visų kandidatinių transakcijų `transaction_id` (hex).
- Poravimas atliekamas baitų lygmeniu (`bytes.fromhex(h1) + bytes.fromhex(h2)`), rez. maišoma per `aes_hashing()`.
- Jei lygyje transakcijų nelyginis skaičius — paskutinė **dubliuojama**.
- Procesas kartojamas, kol lieka viena šaknis → tai ir yra `merkle_root`.

---

### 4) Kasimas (Proof-of-Work)

- `Block.calculate_hash()` sudeda **6 antraštės laukus**:
  - `prev_block_hash`, `timestamp`, `version`, `merkle_root`, `nonce`, `difficulty`.
- Kol `hash` **neprasideda** `difficulty` skaičiumi nulių:
  - didinamas `nonce` (`0, 1, 2, …`) ir vėl skaičiuojamas `calculate_hash()`.
- Radus tinkamą `hash`:
  - `new_block.hash = hash`,
  - baigiamas kasimas ir pereinama prie būsenos atnaujinimo.

> Intuityviai: kuo didesnis `difficulty`, tuo rečiau sutinkami „teisingi“ hash’ai → ilgiau kasama.

---

### 5) Patvirtinimas ir UTXO atnaujinimas

**1) Duomenų generavimas**

- `generate_users(N)`: sukuria ~N vartotojų su `public_key` (per `aes_hashing`) ir realistiška UTXO mozaika (tikslinė suma `[100..1_000_000]` → 1 arba 5–15 UTXO).
- `generate_transactions(M)`: suformuoja TX **nekeisdama globalios būsenos** – parenka `inputs` (pilnus UTXO), sukuria `outputs` (įskaitant grąžą), apskaičiuoja **deterministinį** `transaction_id` iš `sender_pk`, `receiver_pk`, `amount`, `tx_nonce`, **surikiuotų** `inputs` ir `outputs` → `aes_hashing()`.

**2) Bloko kandidatūra**

- `create_new_block(...)`: iš mempool paima iki `block_size` TX, suformuoja `Block` (`prev_block_hash`, `timestamp`, `version=1`, `difficulty`, `nonce=0`, `merkle_root`).

**3) Merkle root**

- TX ID (hex) poruojami baitų lygiu, nelyginiam kiekiui dubliuojamas paskutinis; iteruojama, kol lieka 1 hash.

**4) Kasimas (PoW)**

- Hash’inami 6 header laukai: `prev_hash | timestamp | version | merkle_root | nonce | difficulty`.
- Didinamas `nonce`, kol `hash` prasideda nulių prefiksu pagal `difficulty`.

**5) Patvirtinimas ir UTXO atnaujinimas**

- **Sekvencinis**: kiekvienai TX tikrinama, ar `input` UTXO dar egzistuoja; jei trūksta – **praleidžiama** (įspėjimas). Galiojančioms: `remove_utxos()` + `add_utxo()` adresatams; iš mempool pašalinamos **visos parinktos** TX (įsk. praleistas).
- **Lygiagretus**: taikomos **tik laimėtojo bloko** TX; `remove_utxos()` + `add_utxo()` be „missing inputs“ įspėjimų; iš mempool pašalinamos **tik laimėtojo** TX.

**6) Išvestis**

- Failai į `output/` (žr. [Išvesties režimai](#išvesties-režimai)).
  - **Konsolė** — po kiekvieno bloko: transakcijų peržiūra (N pirmų arba visos, pagal flag’us).

---

## Unit testai

- Paleidimas: `python -m unittest discover -s tests -p "test_*.py" -v`
- Tikrinama:
  - UTXO elgsena (`add_utxo`, `remove_utxos`, balansas).
  - Deterministinis `transaction_id` ir jo validacija.
  - Merkle root stabilumas / jautrumas pokyčiams.
  - PoW logika (nonce įtaka hash, prefiksas su nuliais).
  - Lygiagretus kasimas (bent vienas blokas, `hash` ilgis 32 hex, `merkle_root` nenulis).
- Testai nutildo SUMMARY, bet failai rašomi į `output/block_output.txt` ir `output/mining_log.txt`.

---

## AI pagalba

Šiame projekte AI asistentas prisidėjo taip:

- Parengė **Merkle root** skaičiavimo pseudokodą, pagal kurį buvo realizuota funkcija.
- **UTXO** daliai (2 versijai) paaiškino, kaip suprojektuoti ir parašyti kodą (inputs/outputs, grąža, UTXO atnaujinimas).
- Apskritai paaiškino, **kaip įgyvendinti UTXO modelį** šiame projekte.
- Paaiškino, kaip sukurti **lygiagretų kasimą** (kandidatinių blokų generavimas, `ProcessPoolExecutor`, laimėtojo parinkimas).
- Paaiškino, kaip teisingai **implementuoti CLI flag’us** (parsavimas, numatytosios reikšmės, elgsena su `--append/--overwrite` ir kt.).
- **Pataisė gramatines klaidas** dokumentacijoje ir pranešimuose (konsolės išvestis, README.md).
- **Padėjo ištaisyti programines klaidas** (pvz., rašybos klaida `block_transactions` → `block.transactions`, numatytieji išvesties keliai į `output/`, smulkūs patikimumo/saugumo patobulinimai).
