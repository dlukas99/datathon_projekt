# Napredak
Zadnje ažurirano: 2026-11-02 20:45

## P0
- [x] **Kostur:** `Makefile`, `backend/` (uv, FastAPI, ruff, mypy strict, pytest), `frontend/` (Vite, React 19, TypeScript, ESLint s typescript-eslint i jsx-a11y), `LICENSE` (EUPL-1.2), `.env.example`, `.gitignore`, `docs/ODLUKE.md`. `make verify` prolazi na praznom projektu. (lint, testovi, build i e2e s axeom prolaze; provjera README-a namjerno pada do revizije, vidi `docs/ODLUKE.md`.)
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

## P1
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

## P2
- [ ] **Požari:** EFFIS opožarene površine, samo ako se preuzimaju bez računa.
- [ ] **Procjena auto-kilometara i CO2:** samo s citiranim faktorima emisije i jasno opisanim pretpostavkama.
- [ ] **Izvoz PDF-a** izvještaja.

## Odustano

## Za ljude
- Upisati `CONTACT_EMAIL` u `.env` (ide u User-Agent prema izvorima podataka).
