# Asistent

Asistent odgovara na pitanja o jednoj adresi ili o dvjema adresama u usporedbi. Dostupan je na stranici izvještaja, na stranici usporedbe i preko API-ja `POST /api/assistant`.

## Kako radi

1. **Razumijevanje pitanja (pravila, bez jezičnog modela).**
   - Poruka se dijeli na dijelove (zarez, upitnik, „i”, „a”, „ili”…). U svakom dijelu traže se početci riječi u tekstu bez dijakritika, pa „zrak”, „zraka” i „zraku”, „skola” i „škole” ili „ljecnik” i „liječnik” znače isto.
   - Prepoznaju se i sinonimi: apoteka (ljekarna), doktor ili liječnik opće prakse (obiteljski liječnik), bus, tramvaj i autobus (prijevoz), park i zelena površina (zelenilo).
   - Jedna poruka može imati više tema („Kakav je zrak, ima li vrtić i koliko je do ljekarne?”). Svaka dobiva svoj blok, redom kojim je postavljena.
   - **Nastavna pitanja:** stranica uz pitanje šalje teme prethodnog odgovora (`context`), pa „A škola?” nakon vrtića odgovara o školi, „A pješice?” daje hod i zračnu udaljenost do istog mjesta, a „Zašto?” objašnjenje prethodne teme. Ništa se ne sprema; kontekst postoji samo dok je stranica otvorena.
   - Ako dio pitanja nije u podacima („… i ima li u blizini pikado klub?”), asistent odgovori na ostalo i kratko kaže što ne može procijeniti.
   - Jezični model (ako je postavljen u `.env`: `LLM_BASE_URL`, `LLM_MODEL`, po potrebi `LLM_API_KEY`) pita se samo kad pravila ne prepoznaju ništa, i to samo za teme pitanja. Odgovor nikad ne piše.
2. **Alati.** Asistent vidi samo rezultate vlastitih alata: izvještaj za adresu (`build_report`, isti kao `GET /api/report`), usporedbu dviju adresa i stalna objašnjenja pojmova u `backend/app/assistant.py`.
3. **Odgovor.** Svaka rečenica s brojem, nazivom ili datumom slaže se iz predložaka nad izvještajem. Za svaku temu dolazi blok:
   - naslov s ikonom i statusnom oznakom (bojom, oblikom i riječima);
   - izravan odgovor u jednoj ili dvije rečenice; na pitanje da/ne prva riječ je „Da” ili „Ne”;
   - do četiri retka s ključnim brojevima („PM2,5: 18,2 µg/m³ – umjerena razina”, „Pješice: 7 min hoda (zračno 370 m)”);
   - čipovi za ono što postoji, nedostaje ili nije provjereno;
   - korisne poveznice kao gumbi;
   - sklopivi dio „Izvori i metoda” (zatvoren): izvor, datum, vrsta vrijednosti (izmjereno, modelirano, procjena) i kratka metoda.

   Kad su postavljene više od dvije teme, na vrhu je jedna rečenica sažetka. Napomena da je riječ o informativnom pregledu, a ne službenoj procjeni ni savjetu, prikazuje se jednom ispod razgovora.
4. **Prijedlozi pitanja** prate odgovor (nakon zraka: „A buka i promet?”, „Ima li zelenila u blizini?”), a već postavljena pitanja se ne nude ponovno.

Vrste dijelova pitanja:

| Vrsta | Ponašanje |
|---|---|
| tema izvještaja | blok za kategoriju (poplave, zrak, zelenilo, promet, požari, sunce, život bez auta, prijevoz) ili za svakodnevnu potrebu (vrtić, škola, liječnik, pedijatar, ljekarna, trgovina, igralište, reciklaža) |
| što je u blizini | „Što je najbliže?”, „Što je u krugu 10 minuta?”: mjesta po minutama hoda |
| prednosti i slabosti | teme s dobrom i slabijom ocjenom; izričito nije savjet o kupnji |
| opće pitanje | sažetak izvještaja („Kakva je okolina?”) |
| što ne znamo | „Što ne znaš?”, „Što nije provjereno?”: neprovjereno, procjene i teme bez podataka |
| broj stanovnika | broj stanovnika naselja (Popis 2021.) |
| bez podataka | bolnica, sigurnost, potres, internet, parkiranje, srednja škola, temperatura: rečenica da podataka nema i, gdje postoji, srodna tema |
| objašnjenje | „Što znači…”, „Zašto?”: stalni tekst o pojmu |
| savjet o kupnji, izvan opsega | odbija se taj dio, ostatak pitanja dobiva odgovor |
| nije u podacima | dio pitanja bez prepoznate teme, uz druge teme: „Za „pikado klub” nemamo podatke” |

Pitanje koje se uopće ne odnosi na adresu dobiva „To pitanje ne mogu povezati s podacima za ovu adresu” i tri prijedloga pitanja.

## Testna pitanja

Pitanja su automatski provjerena u `backend/tests/test_assistant.py` (pravila, bez jezičnog modela). Pitanja 31–40 dodana su 8. 11. 2026. uz više tema po poruci i nastavna pitanja. Pitanja 21–30 dodana su 6. 11. 2026. nakon prijave da asistent na svako pitanje daje isti odgovor. Stupac „Očekivani odgovor” opisuje sadržaj; točne brojke ovise o adresi i dolaze iz izvještaja.

| # | Pitanje | Vrsta | Kategorije | Očekivani odgovor |
|---|---|---|---|---|
| 1 | Je li ova kuća u poplavnom području? | tema izvještaja | poplave | status i naslovna rečenica poplava; dubine po povratnom razdoblju kao činjenice; poveznica na karte Hrvatskih voda |
| 2 | Može li se ovdje izliti rijeka? | tema izvještaja | poplave | isto kao 1 |
| 3 | Kakav je zrak na ovoj adresi? | tema izvještaja | zrak | PM2,5 i NO2 (µg/m³, 2024.) uz usporedbu sa smjernicom WHO-a i graničnom vrijednošću EU-a za 2030. |
| 4 | Ima li puno prašine i smoga? | tema izvještaja | zrak | isto kao 3 |
| 5 | Ima li dovoljno drveća i hlada ljeti? | tema izvještaja | zelenilo i hlad | udio drveća, zelenih i izgrađenih površina u krugu od 300 m; najbliži park |
| 6 | Koliko je daleko najbliži park? | tema izvještaja | zelenilo i hlad | najbliži park u minutama hoda i zračna udaljenost |
| 7 | Je li bučno zbog prometa? | tema izvještaja | udaljenost od prometnica | udaljenost od najbliže autoceste, brze, državne ili županijske ceste (s oznakom, npr. D8) i pruge, označena kao procjena |
| 8 | Isplate li se solarni paneli na krovu? | tema izvještaja | sunce | kWh po kWp godišnje i optimalni nagib iz PVGIS-a (bez savjeta o isplativosti) |
| 9 | Mogu li ovdje živjeti bez auta? | tema izvještaja | život bez auta | „X od 7” potreba unutar 15 minuta hoda i popis onoga što nedostaje ili nije provjereno |
| 10 | Ima li autobus ili tramvaj u blizini? | tema izvještaja | javni prijevoz | broj stajališta unutar 10 minuta hoda; najviše polazaka na sat gdje postoji vozni red |
| 11 | Koliko je daleko vrtić? | tema izvještaja | vrtić | najbliži vrtić s minutama hoda i nazivom |
| 12 | Gdje je najbliža osnovna škola? | tema izvještaja | škola | najbliža osnovna škola s minutama hoda |
| 13 | Ima li obiteljski liječnik u blizini? | tema izvještaja | liječnik | najbliža ordinacija obiteljske medicine (HZZO) s minutama hoda |
| 14 | Gdje je najbliži pedijatar? | tema izvještaja | pedijatar | najbliža pedijatrijska ordinacija (HZZO) |
| 15 | Koliko je do ljekarne? | tema izvještaja | ljekarna | najbliža ljekarna s minutama hoda |
| 16 | Ima li trgovina namirnicama blizu? | tema izvještaja | trgovina | najbliža trgovina namirnicama (OSM) |
| 17 | Što znači povratno razdoblje poplave? | objašnjenje | poplave | objašnjenje: 100 godina = 1 % vjerojatnosti svake godine |
| 18 | Trebam li kupiti ovu kuću? | savjet o kupnji | — | „Ne dajem savjete o tome treba li kupiti nekretninu …” |
| 19 | Koliko košta kvadrat u ovoj ulici? | izvan opsega | — | izvan opsega; upućivanje na nadležne institucije i stručnjake |
| 20 | Je li zemljišnoknjižno stanje uredno? | izvan opsega | — | isto kao 19 |
| 21 | Kakva je okolina? | opće pitanje | — | sažetak izvještaja (poplave, zrak, život bez auta) i prijedlog konkretnijeg pitanja |
| 22 | Je li ovo dobro mjesto za obitelj s djecom? | opće pitanje | — | isto kao 21 |
| 23 | Gdje je najbliža bolnica? | bez podataka | — | „O bolnicama i hitnoj pomoći nemamo podatke …” |
| 24 | Je li sigurno za život? | bez podataka | — | „O sigurnosti i kriminalu nemamo podatke.” |
| 25 | Je li sigurno od poplava? | tema izvještaja | poplave | isto kao 1 („sigurno” uz temu ne znači kriminal) |
| 26 | Ima li ovdje optički internet? | bez podataka | — | „O internetu i mobilnom signalu nemamo podatke.” |
| 27 | Gdje je najbliža srednja škola? | bez podataka | škola | da podataka o srednjim školama nema, i najbliža osnovna škola |
| 28 | Koliko ima stanovnika? | broj stanovnika | — | broj stanovnika naselja iz Popisa 2021. |
| 29 | Je li ulica tiha? | tema izvještaja | udaljenost od prometnica | isto kao 7 |
| 30 | Što mislite o ovome? | nije o adresi | — | „To pitanje ne mogu povezati s podacima za ovu adresu …” i tri prijedloga pitanja |
| 31 | Kakav je zrak, ima li vrtić i koliko je do ljekarne? | tri teme | zrak, vrtić, ljekarna | tri bloka redom i rečenica sažetka na vrhu |
| 32 | A škola? (nakon pitanja o vrtiću) | nastavno | škola | najbliža osnovna škola s minutama hoda |
| 33 | A pješice? (nakon pitanja o vrtiću) | nastavno | vrtić | minute hoda i zračna udaljenost do istog vrtića |
| 34 | ima li skola i ljecnik u blizini | bez dijakritika | škola, liječnik | dva bloka |
| 35 | Ima li apoteka i bus? | sinonimi | ljekarna, prijevoz | dva bloka; „Da – najbliža ljekarna je …” |
| 36 | Kakav je zrak i ima li u blizini pikado klub? | djelomično pokriveno | zrak | blok za zrak i „Za „pikado klub” nemamo podatke” |
| 37 | Što je u krugu 10 minuta? | u blizini | — | mjesta unutar 10 minuta hoda i ona dalje |
| 38 | Koje su glavne prednosti i mane ove lokacije? | prednosti i slabosti | — | teme s dobrom i slabijom ocjenom, bez savjeta o kupnji |
| 39 | Što ne znaš? | što ne znamo | — | neprovjereno, procjene i teme bez podataka |
| 40 | Isplati li se kupiti i kakav je zrak? | savjet o kupnji + tema | zrak | odbija savjet, odgovara o zraku |

Za usporedbu dviju adresa provjereno je i:

- „Koja adresa ima bolji zrak?”: naslovne rečenice za A i B te rečenica „Nižu godišnju koncentraciju PM2,5 ima adresa …”;
- „Gdje je bliže do vrtića?”: najbliži vrtić za A i B te „Pješice je bliže s adrese …” kad se vremena razlikuju za barem jednu minutu.

## Ograničenja

- Pravila prepoznaju početke riječi i sinonime s popisa. Neobično sročeno pitanje može ostati neprepoznato; tada asistent to kaže i predlaže pitanja, a ne daje sažetak koji bi izgledao kao odgovor.
- Nastavno pitanje vidi samo teme prethodnog odgovora, ne cijeli razgovor.
- Jezični model (ako je postavljen) samo imenuje teme kad pravila ne prepoznaju ništa; odgovor uvijek dolazi iz predložaka. Prijedlog modela koji piše odgovor iz podataka izvještaja, s provjerom brojki, opisan je u [NALAZI_TESTIRANJA.md](NALAZI_TESTIRANJA.md).
- Asistent ne zna ništa izvan izvještaja: ne pretražuje internet i ne odgovara na pitanja o cijenama, pravu ni gradnji.
