# Asistent

Asistent odgovara na pitanja o jednoj adresi ili o dvjema adresama u usporedbi. Dostupan je na stranici izvještaja, na stranici usporedbe i preko API-ja `POST /api/assistant`.

## Kako radi

1. **Razumijevanje pitanja.** Iz pitanja se određuju namjera i kategorije.
   - Bez ključa za jezični model to rade jednostavna pravila (ključne riječi nad tekstom bez dijakritika).
   - Ako su u `.env` postavljeni `LLM_BASE_URL`, `LLM_MODEL` i po potrebi `LLM_API_KEY`, isti posao radi jezični model preko OpenAI-kompatibilnog API-ja (`/chat/completions`). Model vraća samo JSON s namjerom i kategorijama. Ako model ne odgovori ili vrati nešto neispravno, automatski se koriste pravila.
2. **Alati.** Asistent vidi samo rezultate vlastitih alata:
   - izvještaj za adresu (`build_report`, isti kao `GET /api/report`);
   - usporedba dviju adresa (dva izvještaja i neutralna rečenica o tome gdje je vrijednost niža ili viša);
   - objašnjenje kategorije (stalni tekstovi u `backend/app/assistant.py`).
3. **Odgovor.** Svaka rečenica s brojem, nazivom ili datumom slaže se iz predložaka nad rezultatima alata: naslovne rečenice kategorija, vrijednosti s izvorom, datumom i vrstom. Jezični model ne piše tekst odgovora.

Namjere:

| Namjera | Ponašanje |
|---|---|
| `report` | činjenice iz izvještaja za tražene kategorije; bez kategorija sažetak izvještaja |
| `explain` | objašnjenje pojma (povratno razdoblje, PM2,5, pravilo 3-30-300 …) |
| `purchase_advice` | odbija savjet o kupnji i nudi činjenice |
| `out_of_scope` | odbija pitanja o cijenama, kreditima, vlasništvu i gradnji te upućuje na nadležne institucije |

Pitanja se ne spremaju i ne bilježe. Svaki odgovor završava napomenom da nije riječ o službenoj procjeni.

## Testna pitanja

Pitanja su automatski provjerena u `backend/tests/test_assistant.py` (pravila, bez jezičnog modela). Stupac „Očekivani odgovor” opisuje sadržaj; točne brojke ovise o adresi i dolaze iz izvještaja.

| # | Pitanje | Namjera | Kategorije | Očekivani odgovor |
|---|---|---|---|---|
| 1 | Je li ova kuća u poplavnom području? | report | poplave | status i naslovna rečenica poplava; dubine po povratnom razdoblju kao činjenice; poveznica na karte Hrvatskih voda |
| 2 | Može li se ovdje izliti rijeka? | report | poplave | isto kao 1 |
| 3 | Kakav je zrak na ovoj adresi? | report | zrak | PM2,5 i NO2 (µg/m³, 2024.) uz usporedbu sa smjernicom WHO-a i graničnom vrijednošću EU-a za 2030. |
| 4 | Ima li puno prašine i smoga? | report | zrak | isto kao 3 |
| 5 | Ima li dovoljno drveća i hlada ljeti? | report | toplina i zelenilo | udio drveća, zelenih i izgrađenih površina u krugu od 300 m; najbliži park |
| 6 | Koliko je daleko najbliži park? | report | toplina i zelenilo | najbliži park u minutama hoda i zračna udaljenost |
| 7 | Je li bučno zbog prometa? | report | buka | udaljenost od najbliže važnije ceste i pruge, označena kao procjena |
| 8 | Isplate li se solarni paneli na krovu? | report | sunce | kWh po kWp godišnje i optimalni nagib iz PVGIS-a (bez savjeta o isplativosti) |
| 9 | Mogu li ovdje živjeti bez auta? | report | život bez auta | „X od 7” potreba unutar 15 minuta hoda i popis onoga što nedostaje ili nije provjereno |
| 10 | Ima li autobus ili tramvaj u blizini? | report | javni prijevoz | broj stajališta unutar 10 minuta hoda; najviše polazaka na sat gdje postoji vozni red |
| 11 | Koliko je daleko vrtić? | report | vrtić | najbliži vrtić s minutama hoda i nazivom |
| 12 | Gdje je najbliža osnovna škola? | report | škola | najbliža osnovna škola s minutama hoda |
| 13 | Ima li obiteljski liječnik u blizini? | report | liječnik | najbliža ordinacija obiteljske medicine (HZZO) s minutama hoda |
| 14 | Gdje je najbliži pedijatar? | report | pedijatar | najbliža pedijatrijska ordinacija (HZZO) |
| 15 | Koliko je do ljekarne? | report | ljekarna | najbliža ljekarna s minutama hoda |
| 16 | Ima li trgovina namirnicama blizu? | report | trgovina | najbliža trgovina namirnicama (OSM) |
| 17 | Što znači povratno razdoblje poplave? | explain | poplave | objašnjenje: 100 godina = 1 % vjerojatnosti svake godine |
| 18 | Trebam li kupiti ovu kuću? | purchase_advice | — | „Ne dajem savjete o tome treba li kupiti nekretninu …” |
| 19 | Koliko košta kvadrat u ovoj ulici? | out_of_scope | — | izvan opsega; upućivanje na nadležne institucije i stručnjake |
| 20 | Je li zemljišnoknjižno stanje uredno? | out_of_scope | — | isto kao 19 |

Za usporedbu dviju adresa provjereno je i:

- „Koja adresa ima bolji zrak?”: naslovne rečenice za A i B te rečenica „Nižu godišnju koncentraciju PM2,5 ima adresa …”;
- „Gdje je bliže do vrtića?”: najbliži vrtić za A i B te „Pješice je bliže s adrese …” kad se vremena razlikuju za barem jednu minutu.

## Ograničenja

- Pravila prepoznaju ključne riječi; neobično sročena pitanja dobivaju sažetak izvještaja i prijedlog konkretnijeg pitanja.
- Asistent ne zna ništa izvan izvještaja: ne pretražuje internet i ne odgovara na pitanja o cijenama, pravu ni gradnji.
