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
3. **Odgovor.** Od 9. 11. 2026. svaki odgovor ima tri dijela:
   - jednu do dvije jednostavne rečenice koje izravno odgovaraju na pitanje (npr. „Ne. Nije u području riječnih poplava, čak ni za vrlo rijetke velike poplave.”, „Najbliža ljekarna je 5 minuta pješice (…)”, „Uglavnom da: 6 od 7 svakodnevnih potreba je do 15 minuta pješice; …”);
   - jedan redak „Izvor: … (datum)”;
   - sklopljeno „Prikaži detalje” sa svim vrijednostima i njihovom vrstom (izmjereno, procjena modela, gruba procjena) te poveznicama.

   Sve rečenice slažu se iz predložaka nad rezultatima alata (`short_answer` u `backend/app/assistant.py`). Za većinu kategorija to je naslovna rečenica kartice; za poplave izravno „Ne.” kad adresa nije u modeliranom području; za život bez auta „Da / Uglavnom da / Djelomično / Teško” prema broju potreba; za usluge „Najbliža … je X minuta pješice”. Jezični model ne piše tekst odgovora.

Namjere:

| Namjera | Ponašanje |
|---|---|
| `report` | činjenice iz izvještaja za tražene kategorije, a na pitanje o broju stanovnika broj stanovnika naselja (Popis 2021.) |
| `overview` | opće pitanje („Kakvo je ovo mjesto?”, „ukratko”, „okolina”): sažetak izvještaja i prijedlog konkretnijeg pitanja |
| `no_data` | tema za koju nemamo podatke (bolnica, sigurnost i kriminal, potres, internet, parkiranje, srednja škola, temperatura): rečenica da podataka nema i, gdje postoji, srodna kategorija (osnovna škola, priroda i hlad) |
| `unknown` | pitanje bez prepoznate teme: jedna rečenica „To ne znam: odgovaram samo o okolišu i onome što je pješice …” s primjerima pitanja; nikad sažetak koji izgleda kao odgovor |
| `explain` | objašnjenje pojma (povratno razdoblje, PM2,5, pravilo 3-30-300 …) |
| `purchase_advice` | odbija savjet o kupnji i nudi činjenice |
| `out_of_scope` | odbija pitanja o cijenama, kreditima, vlasništvu i gradnji te upućuje na nadležne institucije |

Pitanja se ne spremaju i ne bilježe. Ako je na poslužitelju uključen jezični model, tekst pitanja asistentu (bez adrese i podataka izvještaja) šalje se pružatelju tog modela. Napomena da nije riječ o službenoj procjeni prikazuje se jednom, ispod razgovora, a ne uz svaki odgovor.

## Testna pitanja

Pitanja su automatski provjerena u `backend/tests/test_assistant.py` (pravila, bez jezičnog modela). Pitanja 21–30 dodana su 6. 11. 2026. nakon prijave da asistent na svako pitanje daje isti odgovor. Stupac „Očekivani odgovor” opisuje sadržaj; točne brojke ovise o adresi i dolaze iz izvještaja.

| # | Pitanje | Namjera | Kategorije | Očekivani odgovor |
|---|---|---|---|---|
| 1 | Je li ova kuća u poplavnom području? | report | poplave | „Ne. Nije u području riječnih poplava, čak ni za vrlo rijetke velike poplave.” (ili naslovna rečenica kad jest); Izvor: karte JRC-a; u detaljima područja za 10, 100 i 500 godina i poveznica na karte Hrvatskih voda |
| 2 | Može li se ovdje izliti rijeka? | report | poplave | isto kao 1 |
| 3 | Kakav je zrak na ovoj adresi? | report | zrak | ocjena zraka jednom rečenicom (npr. „Zrak je osrednji: onečišćeniji je nego što preporučuje Svjetska zdravstvena organizacija i nego što EU dopušta od 2030.”); Izvor: karte EEA-e; PM2,5 i NO2 u detaljima |
| 4 | Ima li puno prašine i smoga? | report | zrak | isto kao 3 |
| 5 | Ima li dovoljno drveća i hlada ljeti? | report | priroda i hlad | udio prirode, drveća i izgrađenog u krugu od 300 m; u gradu najbliži park |
| 6 | Koliko je daleko najbliži park? | report | priroda i hlad | u gradu najbliži park u minutama hoda i zračna udaljenost (izvan grada park se ne traži) |
| 7 | Je li bučno zbog prometa? | report | udaljenost od prometnica | udaljenost od najbliže autoceste, brze ili državne ceste ili glavne gradske ulice (s oznakom, npr. D8) i pruge, označena kao procjena |
| 8 | Isplate li se solarni paneli na krovu? | report | sunce | kWh po kWp godišnje i optimalni nagib iz PVGIS-a (bez savjeta o isplativosti) |
| 9 | Mogu li ovdje živjeti bez auta? | report | život bez auta | „Da / Uglavnom da / Djelomično / Teško: X od 7 svakodnevnih potreba je do 15 minuta pješice”, uz ono što nedostaje ili nije provjereno |
| 10 | Ima li autobus ili tramvaj u blizini? | report | javni prijevoz | broj stajališta unutar 10 minuta hoda; najviše polazaka na sat gdje postoji vozni red |
| 11 | Koliko je daleko vrtić? | report | vrtić | najbliži vrtić s minutama hoda i nazivom |
| 12 | Gdje je najbliža osnovna škola? | report | škola | najbliža osnovna škola s minutama hoda |
| 13 | Ima li obiteljski liječnik u blizini? | report | liječnik | najbliža ordinacija obiteljske medicine (HZZO) s minutama hoda |
| 14 | Gdje je najbliži pedijatar? | report | pedijatar | najbliža pedijatrijska ordinacija (HZZO) |
| 15 | Koliko je do ljekarne? | report | ljekarna | „Najbliža ljekarna je X minuta pješice (naziv).”; Izvor: HZZO |
| 16 | Ima li trgovina namirnicama blizu? | report | trgovina | najbliža trgovina namirnicama (OSM) |
| 17 | Što znači povratno razdoblje poplave? | explain | poplave | objašnjenje: 100 godina = 1 % vjerojatnosti svake godine |
| 18 | Trebam li kupiti ovu kuću? | purchase_advice | — | „Ne dajem savjete o tome treba li kupiti nekretninu …” |
| 19 | Koliko košta kvadrat u ovoj ulici? | out_of_scope | — | izvan opsega; upućivanje na nadležne institucije i stručnjake |
| 20 | Je li zemljišnoknjižno stanje uredno? | out_of_scope | — | isto kao 19 |
| 21 | Kakva je okolina? | overview | — | sažetak izvještaja (poplave, zrak, život bez auta) i prijedlog konkretnijeg pitanja |
| 22 | Je li ovo dobro mjesto za obitelj s djecom? | overview | — | isto kao 21 |
| 23 | Gdje je najbliža bolnica? | no_data | — | „O bolnicama i hitnoj pomoći nemamo podatke …” |
| 24 | Je li sigurno za život? | no_data | — | „O sigurnosti i kriminalu nemamo podatke.” |
| 25 | Je li sigurno od poplava? | report | poplave | isto kao 1 („sigurno” uz temu ne znači kriminal) |
| 26 | Ima li ovdje optički internet? | no_data | — | „O internetu i mobilnom signalu nemamo podatke.” |
| 27 | Gdje je najbliža srednja škola? | no_data | škola | da podataka o srednjim školama nema, i najbliža osnovna škola |
| 28 | Koliko ima stanovnika? | report | — | broj stanovnika naselja iz Popisa 2021. |
| 29 | Je li ulica tiha? | report | udaljenost od prometnica | isto kao 7 |
| 30 | Što mislite o ovome? | unknown | — | „To ne znam: odgovaram samo o okolišu i onome što je pješice …” |

Za usporedbu dviju adresa provjereno je i:

- „Koja adresa ima bolji zrak?”: naslovne rečenice za A i B te rečenica „Nižu godišnju koncentraciju PM2,5 ima adresa …”;
- „Gdje je bliže do vrtića?”: najbliži vrtić za A i B te „Pješice je bliže s adrese …” kad se vremena razlikuju za barem jednu minutu.

## Ograničenja

- Pravila prepoznaju ključne riječi. Neobično sročeno pitanje dobiva odgovor „To ne znam …” s primjerima pitanja, a ne sažetak koji bi izgledao kao odgovor. Do 6. 11. 2026. svako takvo pitanje dobivalo je isti sažetak, pa je izgledalo kao da asistent uvijek odgovara isto.
- Jezični model (ako je postavljen) i dalje samo prepoznaje namjeru i kategorije; odgovor uvijek dolazi iz predložaka. Prijedlog modela koji piše odgovor iz podataka izvještaja, s provjerom brojki, opisan je u [NALAZI_TESTIRANJA.md](NALAZI_TESTIRANJA.md).
- Asistent ne zna ništa izvan izvještaja: ne pretražuje internet i ne odgovara na pitanja o cijenama, pravu ni gradnji.
