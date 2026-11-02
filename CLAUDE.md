# CLAUDE.md: Prije potpisa

Ovaj dokument je cijeli plan. Radiš samostalno, bez pitanja ljudima, od praznog repozitorija do rješenja spremnog za predaju.

## 1. Što gradimo

Web aplikaciju koja za bilo koju adresu u Hrvatskoj daje okolišni pregled za kupca kuće ili stana: poplave, zrak, toplina i zelenilo, buka, sunčev potencijal krova, život bez auta (izokrone hoda, javni prijevoz) i svakodnevne potrebe (vrtić, škola, liječnik, ljekarna, trgovina, park). Podaci su isključivo otvoreni. Ciljni korisnik je običan građanin, ne stručnjak.

- Natjecanje: Datathon Portala otvorenih podataka 2026., **izazov B: Okoliš i održivi prostor**.
- **Rok predaje: 9. 11. 2026. u 24:00.** Video, slanje e-pošte i postavljanje na poslužitelj rade ljudi (odjeljak 13).
- README.md je opis ciljanog proizvoda za ocjenjivače. Na kraju ga moraš uskladiti sa stvarnim stanjem (odjeljak 11).

Okolišni dio uvijek je prvi i najvažniji. Svakodnevne potrebe su dodatak. Ako ocjenjivači steknu dojam da je ovo aplikacija za škole i trgovine, rješenje gubi bodove na relevantnosti za izazov B.

### Kriteriji ocjenjivanja (najviše 60 bodova)

| Kriterij | Bodovi | Što to znači za nas |
|---|---|---|
| Upotreba otvorenih podataka | 1–5 | izvori preko API-ja ili automatski preuzeti i pripremljeni; prednost skupovima s data.gov.hr |
| Povezivanje javno dostupnih podataka | 1–5 | smisleno spajanje više izvora koje daje novu informaciju |
| Relevantnost rješenja | 1–5 | jasno izazov B: okoliš i održivi prostor |
| Utjecaj i korist za zajednicu | 1–5 | stvarna korist običnom čovjeku |
| Inovativnost i primjena tehnologija | 1–5 | AI i napredne tehnologije, upotrijebljene smisleno |
| Izvedivost rješenja | 1–10 | radni prototip, dovršen, spreman za upotrebu |
| Tehnička arhitektura i integracijski potencijal | 1–5 | jasno opisana, interoperabilni standardi, navedeni tehnički, organizacijski i pravni preduvjeti |
| Dojam rješenja (UI/UX) | 1–10 | jednostavno, lijepo, pristupačno |
| Prezentacija (video do 3 min) | 1–10 | snimaju ljudi; ti pripremaš scenarij |

Kod jednakog broja bodova prednost ima veća Izvedivost, a zatim Upotreba otvorenih podataka.

## 2. Način rada: potpuno samostalno

- **Ne postavljaj pitanja.** Kad nešto nije jasno, izaberi razumnu opciju, zapiši je jednim retkom u `docs/ODLUKE.md` (datum, odluka, razlog) i nastavi.
- **Ne čekaj potvrdu plana.** Plan je ovaj dokument.
- **Početak svake sesije:**
  1. `date`
  2. pročitaj `PROGRESS.md` (ako ne postoji, napravi ga iz odjeljka 4 i commitaj)
  3. `git log --oneline -15`
  4. nastavi s prvim neoznačenim zadatkom najvišeg prioriteta
- **Nakon svakog zadatka:** pokreni provjere za taj dio, označi zadatak u `PROGRESS.md` s jednom rečenicom o tome što je napravljeno (i izmjerenim brojkama, ako ih ima), commitaj s porukom u obliku `feat: …`, `fix: …`, `docs: …`. Ako postoji `origin`, pushaj.
- **Kad zapneš:** ako izvor podataka ili alat ne radi nakon tri različita pristupa ili oko 45 minuta, prijeđi na rezervni plan iz odjeljka 5. Ako rezervnog plana nema, izbaci značajku, zapiši razlog u `PROGRESS.md` pod „Odustano” i u README pod „Poznata ograničenja”, pa nastavi.
- **Datumski rezovi:** ako je `date` 7. 11. 2026. ili kasnije, ne počinji P2. Ako je 8. 11. ili kasnije, radiš samo popravke, dokumentaciju i reviziju README-a.
- **Kontekst:** velike ispise preusmjeri u datoteke i čitaj samo potrebne dijelove. Ako su dostupni subagenti, koristi ih za istraživanje izvora podataka i pregled koda.
- **Repozitorij:** ako `git status` javi da repozitorij ne postoji, napravi `git init` s granom `main`. Ne mijenjaj udaljene repozitorije (remote) i ne pravi nove na GitHubu.

### PROGRESS.md

```
# Napredak
Zadnje ažurirano: <datum i vrijeme>

## P0
- [x] Zadatak (rezultat u jednoj rečenici)
- [ ] Zadatak
## P1
## P2
## Odustano
- Zadatak: razlog
## Za ljude
- što samo ljudi mogu napraviti
```

## 3. Tvrda pravila (bez iznimke)

1. **Nikad izmišljeni podaci.** Nijedna brojka, naziv ustanove, datum ni tvrdnja u sučelju, README-u ili dokumentaciji ne smije biti izmišljena. Testni podaci postoje samo u `backend/tests/fixtures/` i nikad se ne prikazuju u aplikaciji.
2. **Svaka vrijednost ima izvor.** Svaka vrijednost u API-ju nosi `source`, `retrieved_at` i `kind` (`measured`, `modelled` ili `estimate`). Sučelje to prikazuje.
3. **Licence prije upotrebe.** Prije korištenja izvora zapiši licencu u `docs/IZVORI_PODATAKA.md`. Izvor čija licenca ne dopušta upotrebu ne koristiš. Karte Hrvatskih voda samo povezuješ, ne izvodiš iz njih podatke, osim ako licenca to izričito dopušta.
4. **Konstante s izvorom.** Svaki prag i svaka konstanta (WHO, EU, brzina hoda, faktori) imaju izvor u `docs/METODOLOGIJA.md`. Ako izvor ne možeš pronaći, izbaci značajku.
5. **Tajne.** Ključevi samo u `.env`, koji je u `.gitignore`. U repozitoriju je samo `.env.example`.
6. **Pristojno preuzimanje.** User-Agent `PrijePotpisa/0.1 (+$CONTACT_EMAIL)`, najmanje jedna sekunda između zahtjeva prema HTML stranicama, sirove datoteke u `data/raw/` (u `.gitignore`). Ne zaobilaziš prijave, CAPTCHA ni ograničenja.
7. **Instalacija** samo preko `uv`, `npm` i `docker pull`. Nikad `curl … | bash`.
8. **Privatnost.** Ne spremaj upisane adrese ni pitanja; dopušten je samo anonimni brojač upita po općini i kategoriji. U demo materijalima, testovima i snimkama zaslona koristi isključivo adrese javnih ustanova (gradske uprave, knjižnice, škole), nikad privatne kuće.
9. **Ne mijenjaj CLAUDE.md.** Ne postavljaj ništa na produkcijski poslužitelj.
10. **Jezik.** Sučelje i dokumentacija na standardnom hrvatskom, bez srbizama i anglizama gdje postoji hrvatska riječ. Identifikatori u kodu i komentari na engleskom.
11. **Ton.** Neutralan, bez zastrašivanja. Uvijek jasno: informativni alat, nije službena procjena.
12. **Bez skupne ocjene sa skrivenim težinama.** Svaka kategorija ima vlastito značenje. Profil mijenja redoslijed i naglasak, nikad vrijednosti.

## 4. Zadaci i prioriteti

P0 mora raditi do 5. 11., P1 do 7. 11., P2 samo ako ostane vremena. Ovo je početni sadržaj `PROGRESS.md`.

### P0

- [ ] **Kostur:** `Makefile`, `backend/` (uv, FastAPI, ruff, mypy strict, pytest), `frontend/` (Vite, React 19, TypeScript, ESLint s typescript-eslint i jsx-a11y), `LICENSE` (EUPL-1.2), `.env.example`, `.gitignore`, `docs/ODLUKE.md`. `make verify` prolazi na praznom projektu.
- [ ] **Istraživanje izvora:** za svaki izvor iz odjeljka 5 provjeri dostupnost, URL, format, licencu i datum, isprobaj preuzimanje i zapiši u `docs/IZVORI_PODATAKA.md` sa statusom (radi, djelomično, ne radi) i odabranim rezervnim planom.
- [ ] **Geokodiranje:** adrese (DGU, rezerva OSM), `GET /api/geocode?q=` s prijedlozima, naselje, općina i županija za točku (DGU granice). Pet demo adresa javnih ustanova u `scripts/demo_addresses.json` (Vinkovci, Osijek, Zagreb, Split i jedno manje naselje).
- [ ] **Poplave:** JRC karte za povratna razdoblja 10, 100 i 500 godina, vrijednost na točki i u krugu od 100 m; poveznica na službeni preglednik Hrvatskih voda.
- [ ] **Zrak:** EEA godišnje karte PM2,5 i NO2 (najnovija dostupna godina), usporedba s WHO 2021 i EU 2030.
- [ ] **Toplina i zelenilo:** ESA WorldCover, udio drveća, zelenih i izgrađenih površina u krugu od 300 m; najbliži park (OSM) u minutama hoda.
- [ ] **Mreža hoda:** Valhalla u Dockeru s OSM izvatkom za Hrvatsku; izokrone od 5, 10 i 15 minuta; vrijeme hoda do točaka.
- [ ] **Svakodnevne potrebe:** vrtići (registar Ministarstva, geokodirani), osnovne škole, obiteljski liječnici i pedijatri (HZZO), ljekarne, trgovine namirnicama, igrališta (OSM): najbliži i broj unutar 15 minuta hoda.
- [ ] **Javni prijevoz:** stajališta unutar 10 minuta hoda i polasci po satu radnim danom iz GTFS-a (ZET, Autotrolej, HŽPP); drugdje stajališta iz OSM-a s oznakom „bez voznog reda”.
- [ ] **Sunce:** JRC PVGIS API, godišnja proizvodnja u kWh po kWp uz optimalni nagib; predmemorija po zaokruženim koordinatama.
- [ ] **API izvještaja:** `GET /api/report?lat=&lon=` sa svim kategorijama i poljima iz pravila 2, i isti izvještaj kao GeoJSON (`format=geojson`); OpenAPI dostupan na `/api/docs`.
- [ ] **Sučelje:** naslovnica (pretraga i odabir profila), izvještaj (okolišni pregled prvi, karta s izokronama, život bez auta, svakodnevni život, izvori), mobilni prikaz.
- [ ] **Usporedba:** `/usporedi?a=…&b=…`, dvije adrese jedna uz drugu.
- [ ] **Testovi:** zlatni testovi izvještaja za demo adrese, e2e glavnog toka (Playwright) i axe bez nalaza.

### P1

- [ ] **Buka:** strateške karte buke (EEA, podaci prijavljeni prema direktivi o buci okoliša) gdje postoje; drugdje udaljenost od glavnih cesta i pruga (OSM) s oznakom „procjena”.
- [ ] **Asistent:** OpenAI-kompatibilni API iz `.env` (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`) s alatima nad vlastitim API-jem; bez ključa jednostavna pravila; brojke isključivo iz predložaka; dvadesetak testnih pitanja u `docs/ASISTENT.md` s očekivanim odgovorima.
- [ ] **Reciklaža:** OSM i općinski skupovi s Portala preko CKAN API-ja (pretraga, spajanje, uklanjanje duplikata); nalazi u `docs/KVALITETA_PODATAKA.md`.
- [ ] **Profili:** obitelj s djecom, umirovljenik, student, rad od kuće i vlastiti; mijenjaju redoslijed i naglasak.
- [ ] **Ispis i dijeljenje:** CSS za ispis; stanje izvještaja u URL-u.
- [ ] **Stranica „Izvori”:** datumi osvježavanja uživo preko CKAN API-ja data.gov.hr i nalazi o kvaliteti podataka.
- [ ] **Postavljanje:** `deploy/docker-compose.yml` (backend, Valhalla, Caddy s izgrađenim frontendom), `docs/DEPLOY.md`, skripta za prijenos obrađenih podataka na poslužitelj.
- [ ] **Dokumentacija:** `docs/ARHITEKTURA.md` (s tehničkim, organizacijskim i pravnim preduvjetima), `docs/METODOLOGIJA.md`, `docs/PRISTUPACNOST.md`, `docs/KVALITETA_PODATAKA.md`, `docs/VIDEO_SCENARIJ.md`, `docs/PREDAJA.md`.
- [ ] **Snimke zaslona:** `make screenshots` (Playwright) u `docs/images/`, uključene u README.
- [ ] **Revizija README-a:** odjeljak 11.

### P2

- [ ] **Požari:** EFFIS opožarene površine, samo ako se preuzimaju bez računa.
- [ ] **Procjena auto-kilometara i CO2:** samo s citiranim faktorima emisije i jasno opisanim pretpostavkama.
- [ ] **Izvoz PDF-a** izvještaja.

## 5. Izvori podataka i rezervni planovi

Prije upotrebe svaki izvor provjeri; URL-ovi i formati se mijenjaju. Prednost imaju skupovi s data.gov.hr (pretražuj CKAN API: `https://data.gov.hr/ckan/api/3/action/package_search?q=…`).

| Područje | Primarni izvor | Rezervni plan |
|---|---|---|
| Adrese | DGU adrese (INSPIRE, data.gov.hr ili geoportal DGU-a) | adrese iz OSM izvatka (`addr:*`); zatim središta naselja |
| Upravne jedinice | DGU „Upravne jedinice INSPIRE” (data.gov.hr) | granice iz OSM-a (`boundary=administrative`) |
| Stanovništvo | DZS Popis 2021. (data.gov.hr) | izostaviti kontekst naselja |
| Poplave | JRC karte opasnosti od poplava za Europu | samo poveznica na preglednik Hrvatskih voda, uz jasnu napomenu |
| Zrak | EEA interpolirane karte kvalitete zraka (godišnje) | najbliža mjerna postaja (EEA ili MZOZT) s udaljenošću i oznakom |
| Zelenilo i izgrađenost | ESA WorldCover 10 m (preuzimanje pločica za Hrvatsku) | OSM `landuse`, `leisure=park`, `natural=wood` |
| Buka | EEA podaci o buci prema direktivi o buci okoliša | udaljenost od cesta `motorway`, `trunk`, `primary` i pruga iz OSM-a, oznaka „procjena” |
| Sunce | JRC PVGIS API (bez ključa) | izostaviti uz napomenu |
| Mreža hoda | Valhalla (Docker, OSM izvadak Hrvatske s Geofabrika) | vlastiti Dijkstra nad pješačkom mrežom iz OSM-a (pyrosm ili osmnx), po pločicama |
| Vrtići | Registar dječjih vrtića, Ministarstvo znanosti, obrazovanja i mladih (data.gov.hr) | OSM `amenity=kindergarten` |
| Škole | popis škola Ministarstva (data.gov.hr) | OSM `amenity=school` |
| Liječnici | HZZO popis ugovornih ordinacija PZZ (hzzo.hr) | OSM `amenity=doctors` |
| Ljekarne | HZZO popis ugovornih ljekarni | OSM `amenity=pharmacy` |
| Trgovine, igrališta, parkovi | OSM | nema; navesti nepotpunost |
| Javni prijevoz | GTFS: ZET, Autotrolej, HŽPP | OSM stajališta bez voznog reda |
| Reciklaža | općinski skupovi na data.gov.hr (CKAN) i OSM `amenity=recycling` | samo OSM |
| Podloga karte | OpenFreeMap (bez ključa) | OSM rasterske pločice uz poštivanje pravila korištenja |

Za adrese koje treba geokodirati (vrtići, ordinacije) koristi vlastito geokodiranje nad DGU ili OSM adresama. Vanjski geokoderi (npr. javni Nominatim) dopušteni su samo za povremene provjere u razvoju, uz njihova pravila korištenja.

Obrađeni podaci idu u `data/processed/` kao GeoParquet i GeoTIFF (COG). Ne commitaj ništa veće od 20 MB. Male izvatke za testove spremi u `backend/tests/fixtures/`.

## 6. Metodologija

Detalji u `docs/METODOLOGIJA.md`. Načela:

- **Apsolutno značenje ispred relativnog ranga.** „U modeliranom poplavnom području za povratno razdoblje od 100 godina: da” je bolje od „rizik iznad prosjeka”.
- **Svaka kategorija ima status** (dobro, upozorenje, loše ili nema podataka) prema pragu s izvorom. „Nema podataka” se uvijek prikazuje, nikad se kategorija tiho ne izostavlja.
- **Zrak:** WHO 2021 (godišnje PM2,5 5 µg/m³, NO2 10 µg/m³) i granične vrijednosti EU-a za 2030. (godišnje PM2,5 10 µg/m³, NO2 20 µg/m³). Provjeri vrijednosti u izvornim dokumentima i citiraj ih.
- **Buka:** smjernice WHO-a iz 2018. za cestovni promet (Lden 53 dB, Lnight 45 dB). Provjeri i citiraj.
- **Hod:** brzina 4,5 km/h kao zadana vrijednost, s izvorom ili jasnom obrazloženom pretpostavkom u `docs/ODLUKE.md`.
- **Život bez auta:** broj svakodnevnih potreba unutar 15 minuta hoda (trgovina namirnicama, ljekarna, obiteljski liječnik, vrtić, osnovna škola, park, stajalište s barem jednim polaskom na sat radnim danom). Prikaži „X od 7”, s popisom što nedostaje.
- **Vrsta vrijednosti:** svaka je izmjerena, modelirana ili procjena, i to se vidi u sučelju.
- **Sažetak** od dvije do tri rečenice slaže se iz predložaka nad statusima, nikad iz slobodnog teksta jezičnog modela.

## 7. Arhitektura i tehnologije

- **Backend:** Python 3.12, uv, FastAPI, Pydantic v2, httpx, rasterio, Shapely 2, pyproj, GeoPandas i pyogrio (samo za obradu), PyArrow. Pri pokretanju se obrađeni slojevi učitavaju u memorijske indekse (STRtree), a rasteri se čitaju preko rasterio. Ciljano vrijeme izvještaja: ispod 2 s uz zagrijanu predmemoriju.
- **Usmjeravanje:** Valhalla u Dockeru, pješački profil.
- **Frontend:** React 19, TypeScript, Vite, React Router, TanStack Query, MapLibre GL JS sa stilom OpenFreeMapa. Font pod licencom OFL, s vlastitog poslužitelja.
- **Kvaliteta:** ruff, mypy `--strict`, pytest, ESLint, `tsc`, Playwright s `@axe-core/playwright`.
- **Postavljanje:** Docker Compose (backend, Valhalla, Caddy koji poslužuje izgrađeni frontend i prosljeđuje `/api`), HTTPS preko Caddyja i varijable `DOMAIN`.

### Struktura repozitorija (README je navodi, drži je)

```
backend/    app/ (API), ingest/ (konektori izvora), analysis/ (izračuni), tests/
frontend/   React aplikacija
deploy/     docker-compose.yml, Caddyfile, postavke Valhalle
docs/       ARHITEKTURA, METODOLOGIJA, IZVORI_PODATAKA, KVALITETA_PODATAKA, PRISTUPACNOST,
            ASISTENT, ODLUKE, VIDEO_SCENARIJ, DEPLOY, PREDAJA, images/
scripts/    check_readme.py, demo_addresses.json, snimke zaslona
data/       raw/ i processed/ (u .gitignore)
Makefile
PROGRESS.md
```

### Naredbe (README ih navodi, moraju raditi točno ovako)

| Naredba | Što radi |
|---|---|
| `make setup` | ovisnosti backenda i frontenda |
| `make data` | preuzimanje i obrada svih izvora, uz ponovno korištenje već preuzetih datoteka |
| `make dev` | Valhalla, backend na portu 8000 i frontend na portu 5173 |
| `make test` | pytest i testovi frontenda |
| `make lint` | ruff, mypy, ESLint, tsc |
| `make e2e` | Playwright i axe nad pokrenutom aplikacijom |
| `make screenshots` | snimke zaslona za README i dokumentaciju |
| `make verify` | lint, test, build, e2e i `python scripts/check_readme.py`; izlaz 0 samo ako sve prolazi |

## 8. Sučelje i pristupačnost

- **Prvi ekran izvještaja je okolišni pregled.** Ispod njega su život bez auta, zatim svakodnevni život, pa izvori.
- Mobilni prikaz od 320 px bez vodoravnog pomicanja, ciljevi dodira najmanje 44 px, tamna tema, smanjene animacije.
- WCAG 2.2 razine AA; axe bez nalaza na svim stranicama u svijetloj i tamnoj temi.
- Karta nikad nije jedini nositelj informacije: sve što je na karti piše i u tekstu.
- Miran, uredan izgled, bez maskote i emojija. Statusi bojom i riječima, nikad samo bojom.
- Na svakom izvještaju kratka napomena da je riječ o informativnom alatu, s poveznicom na metodologiju.

## 9. Asistent

- Alati: izvještaj za adresu, usporedba dviju adresa, objašnjenje kategorije. Asistent vidi samo rezultate alata.
- Brojke, nazivi i datumi u odgovorima dolaze iz predložaka nad rezultatima alata, ne iz modela.
- Bez ključa radi jednostavno prepoznavanje namjere (ključne riječi) nad istim alatima.
- Ne daje savjete o kupnji („kupite” ili „nemojte kupiti”), nego činjenice i upute na službene izvore.
- Odbija pitanja izvan opsega i upućuje na nadležne institucije.

## 10. Provjere i definicija gotovog

Prije svakog commita pokreni provjere za dio koji si mijenjao. Prije označavanja P0 ili P1 kao gotovih pokreni `make verify`.

Rješenje je gotovo kad:

1. svi zadaci P0 i P1 u `PROGRESS.md` su označeni ili premješteni u „Odustano” s razlogom;
2. `make verify` završava s izlazom 0 i to je vidljivo u ispisu;
3. `python scripts/check_readme.py` prolazi;
4. izvještaj se otvara za svih pet demo adresa, a snimke zaslona su u `docs/images/`;
5. `docs/PREDAJA.md` sadrži točan popis onoga što ljudi moraju napraviti.

## 11. Revizija README-a

README je napisan unaprijed kao opis ciljanog proizvoda. Na kraju:

- svaku tvrdnju provjeri prema kodu i podacima; neistinito ispravi ili ukloni, a ono što nije napravljeno premjesti u „Daljnji razvoj” ili „Poznata ograničenja”;
- zamijeni sve oznake `<!-- AUTO: … -->` stvarnim sadržajem (primjer s izračunom za demo adresu i datumom podataka, nalazi o kvaliteti podataka, dodatna ograničenja);
- tablica izvora mora odgovarati onome što se stvarno koristi;
- naredbe iz „Pokretanja” moraju raditi;
- dodaj snimke zaslona.

`scripts/check_readme.py` mora pasti ako u README-u ostane `AUTO:`, ako poveznica na datoteku u repozitoriju ne postoji ili ako se naredba `make` iz README-a ne nalazi u `Makefile`-u. Dopuštene preostale oznake su samo `TODO(tim)` i `TODO(ljudi)`; skripta ih ispisuje kao popis za ljude, ali ne pada zbog njih.

## 12. Dokumentacija za predaju

Pravila natjecanja traže: izvorni kod ili javni repozitorij, tehničku i projektnu dokumentaciju s opisom arhitekture i popisom skupova podataka s izvorima, demo materijale (poveznica na prototip, snimke zaslona) i video do 3 minute.

- `docs/VIDEO_SCENARIJ.md`: scenarij do 3 minute s vremenskim oznakama koji obuhvaća problem, ciljne korisnike, izvore podataka, funkcionalnosti, tehničku arhitekturu, korisničku vrijednost i daljnji razvoj. Priča: kupac bira između dvije adrese (javne ustanove). Okolišni pregled prvi, zatim usporedba, asistent, izvori.
- `docs/PREDAJA.md`: popis za ljude (repozitorij javno na GitHubu, postavljanje na poslužitelj, demo URL u README, imena tima, snimanje videa, e-pošta na open.data@mpudt.hr s poveznicama), s rokom.

## 13. Što rade samo ljudi

Ovo ne pokušavaš napraviti; samo to pripremiš i zapišeš u `docs/PREDAJA.md` i u odjeljak „Za ljude” u `PROGRESS.md`:

- imena tima, mentora i visokog učilišta (`TODO(tim)`);
- javni repozitorij na GitHubu i push;
- poslužitelj, domena i postavljanje prema `docs/DEPLOY.md`, te demo URL u README (`TODO(ljudi)`);
- ključ za jezični model, ako se asistent želi s modelom;
- snimanje videa i poveznica na njega;
- slanje rješenja e-poštom do roka.
