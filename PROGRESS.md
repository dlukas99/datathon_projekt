# Napredak
Zadnje ažurirano: 2026-11-03 10:30

## P0
- [x] **Kostur:** `Makefile`, `backend/` (uv, FastAPI, ruff, mypy strict, pytest), `frontend/` (Vite, React 19, TypeScript, ESLint s typescript-eslint i jsx-a11y), `LICENSE` (EUPL-1.2), `.env.example`, `.gitignore`, `docs/ODLUKE.md`. `make verify` prolazi na praznom projektu. (Lint, testovi, build i e2e s axeom prolaze od prvog dana; provjera README-a prolazi nakon revizije.)
- [x] **Istraživanje izvora:** svi izvori iz odjeljka 5 provjereni su stvarnim preuzimanjem 2. 11. 2026. i zapisani u `docs/IZVORI_PODATAKA.md` sa statusom i rezervnim planom. Buka EEA-e ne koristi se jer licenca nije otvorena (rezervni plan: OSM).
- [x] **Geokodiranje:** vlastiti geokoder nad 1.683.411 DGU adresa (`GET /api/geocode`), naselje, grad ili općina i županija iz DGU upravnih jedinica (`/api/reverse`); šest demo adresa javnih ustanova (Vinkovci ×2, Osijek, Zagreb, Split, Nijemci) u `scripts/demo_addresses.json`.
- [x] **Poplave:** JRC v3.1.1 za 10, 100 i 500 godina, na točki i u krugu od 100 m; status prema scenarijima Hrvatskih voda i Direktive 2007/60/EZ; poveznica na `preglednik.voda.hr`.
- [x] **Zrak:** EEA karte PM2,5 i NO2 za 2024. (validirane, lipanj 2026.), usporedba s WHO 2021 (5/10 µg/m³) i EU 2030 (10/20 µg/m³).
- [x] **Toplina i zelenilo:** ESA WorldCover u krugu od 300 m (drveće, zelenilo, izgrađeno) i najbliži OSM park u minutama hoda; status prema pravilu 3-30-300.
- [x] **Mreža hoda:** Valhalla 3.9.1 u Dockeru (pločice za Hrvatsku za oko 3 min, imenovani volumen); izokrone od 5, 10 i 15 min i jedna matrica vremena hoda po izvještaju, pri 4,5 km/h.
- [x] **Svakodnevne potrebe:** vrtići (MZOM + Zagreb + OSM), škole (MZOM + Zagreb + OSM), liječnici i pedijatri (HZZO), ljekarne (HZZO + OSM), trgovine, igrališta i reciklaža; registri geokodirani s 86–95 % uspjeha; najbliže i broj unutar 15 min.
- [x] **Javni prijevoz:** ZET i HŽPP GTFS i Autotrolej JSON (4.047 stajališta s polascima na sat od 6 do 20 h radnim danom), drugdje OSM stajališta „bez voznog reda”.
- [x] **Sunce:** PVGIS 5.3, kWh po kWp i optimalni nagib; predmemorija po koordinatama zaokruženima na 0,01°; upit u pozadini (najviše 6 s čekanja), zagrijavanje demo adresa pri pokretanju.
- [x] **API izvještaja:** `GET /api/report` (JSON i `format=geojson`), svaka vrijednost sa `source`, `retrieved_at` i `kind`; OpenAPI na `/api/docs`; izvještaj traje oko 1 s.
- [x] **Sučelje:** naslovnica (pretraga, profili, primjeri), izvještaj (okolišni pregled prvi, karta s izokronama i tekstualnim ekvivalentom, život bez auta, svakodnevni život, izvori), mobilni prikaz od 320 px, tamna tema.
- [x] **Usporedba:** `/usporedi?a=…&b=…` s tablicom kategorija jedna uz drugu i asistentom za dvije adrese.
- [x] **Testovi:**
  - backend (pytest, 57 testova): zlatni testovi za 6 demo adresa, pragovi, API ugovor, 20 pitanja asistenta, PVGIS;
  - frontend: Vitest;
  - Playwright e2e (32 testa): glavni tok, profil, asistent, usporedba, pogreška, 320 px, axe bez nalaza na 5 stranica × 2 teme × 2 uređaja.

## P1
- [x] **Buka:** EEA karte nisu otvorene licence (samo poveznica); procjena prema udaljenosti od autocesta, glavnih i važnijih cesta te pruga iz OSM-a, oznaka „procjena”.
- [x] **Asistent:** `POST /api/assistant`; OpenAI-kompatibilni model samo za namjeru i kategorije, bez ključa pravila; odgovori iz predložaka; 20 testnih pitanja u `docs/ASISTENT.md` (sva prolaze).
- [x] **Reciklaža:** CKAN pretraga 33 općinska skupa, 11 s koordinatama (45 točaka), spojeno s 2.071 OSM točkom; nalazi u `docs/KVALITETA_PODATAKA.md`.
- [x] **Profili:** obitelj s djecom, umirovljenik, student, rad od kuće i vlastiti; mijenjaju samo redoslijed i naglasak (provjereno e2e testom).
- [x] **Ispis i dijeljenje:** CSS za ispis, stanje izvještaja (koordinate, adresa, profil) u URL-u, kopiranje poveznice, preuzimanje GeoJSON-a.
- [x] **Stranica „Izvori”:** datumi zadnje izmjene uživo preko CKAN API-ja (`/api/sources/live`, jedan upit, predmemorija i zadnji dobar odgovor), svi izvori s licencama i nalazi o kvaliteti.
- [x] **Postavljanje:** `deploy/docker-compose.yml` (Caddy s frontendom, API, Valhalla), `docs/DEPLOY.md`, `scripts/upload_data.sh`; lokalno provjereno na `https://localhost`.
- [x] **Dokumentacija:** `docs/ARHITEKTURA.md`, `docs/METODOLOGIJA.md`, `docs/PRISTUPACNOST.md`, `docs/KVALITETA_PODATAKA.md`, `docs/VIDEO_SCENARIJ.md`, `docs/PREDAJA.md`, uz `docs/IZVORI_PODATAKA.md`, `docs/ASISTENT.md` i `docs/ODLUKE.md`.
- [x] **Snimke zaslona:** `make screenshots` snima 7 slika u `docs/images/` (naslovnica, izvještaj, život bez auta, mobitel u tamnoj temi, usporedba, asistent, izvori); uključene u README.
- [x] **Revizija README-a:** tvrdnje usklađene s kodom i podacima; primjer sa stvarnim izračunom (Vinkovci i Nijemci); stvarni nalazi o kvaliteti i ograničenja; `scripts/check_readme.py` prolazi.

## P2
- [x] **Požari:** EFFIS opožarene površine preko javnog WFS-a bez računa (1.030 površina od 2016.), kategorija „Požari raslinja” (krug od 2 km, status „Informacija”).
- [ ] **Procjena auto-kilometara i CO2:** samo s citiranim faktorima emisije i jasno opisanim pretpostavkama.
- [ ] **Izvoz PDF-a** izvještaja.

## Odustano
- Strateške karte buke EEA-e: licenca je ograničena na istraživanje i neprofitnu upotrebu (nije otvorena); koristi se rezervni plan (udaljenost od prometnica iz OSM-a).
- GTFS Autotroleja (`gt.autotrolej.hr`): istekao TLS certifikat; zamijenjen JSON voznim redom s Portala (CC BY 4.0).
- GTFS Šibenika: bez navedene licence i bez objave na Portalu.

## Za ljude
- Upisati `CONTACT_EMAIL` u `.env` (ide u User-Agent prema izvorima podataka).
- Imena tima, mentora i visokog učilišta u README (`TODO(tim)`).
- Javni repozitorij na GitHubu i push grane `main`.
- Poslužitelj, domena i postavljanje prema `docs/DEPLOY.md`; demo URL u README (`TODO(ljudi)`).
- Po želji ključ za jezični model (`LLM_*`).
- Snimanje videa prema `docs/VIDEO_SCENARIJ.md` i poveznica u README.
- Slanje rješenja e-poštom na open.data@mpudt.hr do 9. 11. 2026. u 24:00 (popis u `docs/PREDAJA.md`).

## P3 – proširenje
Plan 4. 11. 2026. Upute tima imaju prednost pred CLAUDE.md gdje se razlikuju (naziv i svrha, skupni skor); odstupanja se bilježe u `docs/ODLUKE.md`. Nakon svake stavke: `make verify`, commit, push.

Redoslijed (procjena):
1. [x] Naziv i tri ulaza na naslovnici; naziv na jednom mjestu u kodu (1,5 h)
2. [x] Središte naselja iz OSM `place` čvorova; poruka o središtu; klik na kartu i pomična oznaka (1,5 h)
3. [ ] Zrak: stupnjevana skala prema međuciljevima WHO-a, crveno samo za visoko; WHO i EU kao informacija (1 h)
4. [ ] Promet u blizini umjesto „Buke”: opisne rečenice i pojasevi udaljenosti s izvorom (0,5 h)
5. [ ] Razumljiv rizik: vjerojatnost barem jedne poplave u 30 godina (0,5 h)
6. [ ] Skor za život: podskorovi po kategoriji u backendu, vidljive i podesive težine po profilu, rečenica što podiže i spušta (2 h)
7. [ ] Pronađi mjesto za život: unaprijed izračunati profili naselja, deterministički rang, forma; jezični model samo za pretvaranje pitanja u filtre (3 h)
8. [ ] Poveznice na oglase: Njuškalo s filtrima i rezervnim poveznicama; Index Oglasi i Nekretnine.hr samo rezervno ako se struktura ne potvrdi (1 h)
9. [ ] Validacija zraka uz službene postaje (Zagreb, Osijek, Požega, po 4 lokacije) (1,5 h)
10. [ ] ML: model za godišnji NO2/PM2,5 na postajama, leave-one-station-out, usporedba s EEA; u aplikaciju samo ako je bolji (2 h)
11. [ ] Dokumentacija, scenarij videa, snimke zaslona (1 h)

Ako ponestane vremena, režem ovim redom:
- ML ostaje samo evaluacija u `docs/ML.md`;
- tumačenje slobodnog pitanja jezičnim modelom u tražilici mjesta (ostaje forma);
- usporedba zraka s ostatkom RH;
- Index Oglasi i Nekretnine.hr samo kao rezervna poveznica.
