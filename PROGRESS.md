# Napredak
Zadnje ažurirano: 2026-11-08 21:30

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
- Po želji ključ za jezični model (`LLM_*`); prijedlog asistenta koji odgovara iz podataka i cijene modela su u `docs/NALAZI_TESTIRANJA.md` (točka 8).
- Zatražiti od HAKOM-a objavu slojeva dostupnosti interneta i pokrivenosti signalom pod otvorenom licencom ili dopuštenje (`docs/NALAZI_TESTIRANJA.md`, točka 4).
- Prenijeti na poslužitelj ponovno obrađene adrese, registre, točke i profile naselja (`scripts/upload_data.sh`) ili pokrenuti `make data`.
- Ručno provjeriti ploču „Pogledaj oglase” i „Izbornik” u Firefoxu i Safariju te s čitačem zaslona.
- Snimanje videa prema `docs/VIDEO_SCENARIJ.md` i poveznica u README.
- Slanje rješenja e-poštom na open.data@mpudt.hr do 9. 11. 2026. u 24:00 (popis u `docs/PREDAJA.md`).

## P3 – proširenje
Plan 4. 11. 2026. Upute tima imaju prednost pred CLAUDE.md gdje se razlikuju (naziv i svrha, skupni skor); odstupanja se bilježe u `docs/ODLUKE.md`. Nakon svake stavke: `make verify`, commit, push.

Redoslijed (procjena):
1. [x] Naziv i tri ulaza na naslovnici; naziv na jednom mjestu u kodu (1,5 h)
2. [x] Središte naselja iz OSM `place` čvorova; poruka o središtu; klik na kartu i pomična oznaka (1,5 h)
3. [x] Zrak: stupnjevana skala prema međuciljevima WHO-a, crveno samo za visoko; WHO i EU kao informacija (1 h)
4. [x] Promet u blizini umjesto „Buke”: opisne rečenice i pojasevi udaljenosti s izvorom (0,5 h)
5. [x] Razumljiv rizik: vjerojatnost barem jedne poplave u 30 godina (0,5 h)
6. [x] Skor za život: podskorovi po kategoriji u backendu, vidljive i podesive težine po profilu, rečenica što podiže i spušta (2 h)
7. [x] Pronađi mjesto za život: unaprijed izračunati profili naselja, deterministički rang, forma; jezični model samo za pretvaranje pitanja u filtre (3 h)
8. [x] Poveznice na oglase: Njuškalo s filtrima i rezervnim poveznicama; Index Oglasi i Nekretnine.hr samo rezervno ako se struktura ne potvrdi (1 h)
9. [x] Validacija zraka uz službene postaje (Zagreb, Osijek, Požega, po 4 lokacije) (1,5 h)
10. [x] ML: model za godišnji NO2/PM2,5 na postajama, leave-one-station-out, usporedba s EEA; u aplikaciju samo ako je bolji (2 h)
11. [x] Dokumentacija, scenarij videa, snimke zaslona (1 h)
12. [x] Popravak poveznica na oglasnike (5. 11.): Njuškalo, Index Oglasi i Nekretnine.hr otvaraju pretragu s mjestom, vrstom, kupnjom ili najmom, cijenom i površinom; Index treba UUID mjesta, zasad upisan za 7 lokacija (`config/listing_locations.json`), ostalo čeka odluku o pokretanju `ingest.listing_locations`.
13. [x] Karta hoda (6. 11.): karta preko cijele širine s gumbom za cijeli zaslon i legendom ispod nje; vrste mjesta kao gumbi s brojem unutar 15 min i najbližim vremenom; pješački put po ulicama do najbližeg mjesta (i izvan 15 min) iz legende, s točke na karti ili iz popisa „Svakodnevni život”, uz „Sljedeći najbliži”. Put računa vlastiti Valhalla (`GET /api/route`) istom brzinom kao izvještaj; uz put stoji isto vrijeme kao u popisu, a vrijeme same rute od njega odstupa najviše 8 s (435 mjesta, šest demo adresa). Testovi: pytest 83, Vitest 27, Playwright 44.
14. [x] Nalazi testiranja (6. 11.), osam prijava, istraživanje i popravci u `docs/NALAZI_TESTIRANJA.md`:
    - **zrak:** jedna ocjena i rečenica;
    - **„Zelenilo i hlad”:** jasno što se broji, provjera uz ortofoto;
    - **oglasi:** ploča se zatvara klikom izvan i tipkom Esc, filtri zajednički;
    - **asistent:** kaže kad ne razumije ili nema podataka;
    - **izbornik:** Provjeri adresu · Predloži mjesto, `/predlozi`;
    - **„Udaljenost od prometnica”:** vrsta ceste s oznakom;
    - **pretraga adresa:**
      - slovo i podbroj kućnog broja (19 % adresa prije nije bilo moguće pronaći), upit bez zareza, s poštanskim brojem ili općinom, drugi oblik naziva ulice i zamjenski prijedlog s napomenom;
      - 24 adrese škola: 12 → 22 točno;
      - registri ponovno geokodirani: 247 točaka na točnoj adresi umjesto sredine ulice, oko 50 premješteno iz susjednog naselja.
    - **Internet** (HAKOM bez otvorene licence) i **jezični model** samo su prijedlozi.
    - **Testovi:** pytest 139, Vitest 52, Playwright 50.
15. [x] Karta Hrvatske (7. 11., grana `feature/karta`):
    - **gdje:** `/karta`, „Karta” u izborniku između „Usporedi” i „O alatu”, četvrti ulaz na naslovnici;
    - **slojevi:** naselja obojena prema Skoru za život (pet profila), zraku, poplavama, uslugama pješice ili javnom prijevozu, iz istih profila naselja kao „Predloži mjesto”; legenda s nazivima iz izvještaja, izvorima i datumom;
    - **geometrija:** 6.759 granica DGU-a pojednostavljenih kao pokrivenost, u sažetom JSON-u (pregled 0,28 MB gzip, detalj 0,8 MB tek pri približavanju), pokazatelji po stupcima 0,18 MB; boje u `feature-state`;
    - **sva naselja:** profili za svih 6.759 naselja (246 s u Dockeru, sva s mrežom hoda), pa na karti nema sivih naselja; „Predloži mjesto” i dalje rangira 2.347 naselja s najmanje 200 stanovnika;
    - **klik:** kratka kartica (na mobitelu donji list) s 6 oznaka, „Otvori puni izvještaj” i „Pogledaj oglase”; šuma ili polje (naselje, udaljenost do središta, poplave i zrak na točki), more i inozemstvo s vlastitom porukom; odgovor 0,15–0,45 s;
    - **pristupačnost:** pretraživa i poredana tablica naselja ispod karte, tipkovnica (fokus na kartici, Esc vraća na redak), axe na karti s otvorenom karticom u obje teme, 320 px;
    - **učitavanje** (produkcijska izgradnja, karta s bojama i podlogom spremna): desktop 2,2 s, mobitel na 4G uz 4× sporiji procesor 4,1 s, na Fast 3G 11,7 s;
    - **snimke:** `docs/images/karta.png` i `karta-mobitel.png`; README, metodologija, arhitektura, pristupačnost, odluke i scenarij videa ažurirani;
    - **testovi:** `make verify` izlaz 0; pytest 149, Vitest 61, Playwright 58 (s 28 axe provjera), provjera README-a prolazi;
    - **usput:** lokalni obrađeni podaci ponovno izgrađeni u Docker kontejneru (`make data` iz `data/raw`), jer su bili stariji od zlatnih testova iz 6. 11.; Python alati u Makefileu pokreću se kao moduli (`python -m pytest`, `mypy`, `uvicorn`) jer Smart App Control na Windowsima blokira njihove `.exe` pokretače.

Ako ponestane vremena, režem ovim redom:
- ML ostaje samo evaluacija u `docs/ML.md`;
- tumačenje slobodnog pitanja jezičnim modelom u tražilici mjesta (ostaje forma);
- usporedba zraka s ostatkom RH;
- Index Oglasi i Nekretnine.hr samo kao rezervna poveznica.
16. [x] Redizajn „Putokaz” (7.–8. 11., grana `feature/redesign`, oznaka za povratak `pre-redesign`), uz Impeccable:
    - **izgled:** sustav oznaka parka prirode: vapnenačka podloga, jezerska zelenoplava za radnje i stazu, smeđa turističkog putokaza za mjesto; fontovi Bricolage Grotesque i Figtree (OFL, vlastiti poslužitelj);
    - **naslovnica:** pitanje „Kako je živjeti ovdje?”, putokaz s dvije daske (adresa s gumbom „Prikaži”, „Pronađi mjesto za mene”), svih 6.759 naselja na platnu koja se pune od istoka prema zapadu i vode na kartu, „Kako radi” u tri postaje;
    - **Predloži mjesto:** čarobnjak s jednim pitanjem po koraku i trakom napretka, okoliš prvi, težine pod „Napredno”, stanje u URL-u, tipka natrag vraća korak; prijedlozi kao retci;
    - **izvještaj:** iskaznica mjesta (smeđi pojas s adresom, sažetak iz predložaka, šest oznaka sa statusom, skor), traka „Dijelovi izvještaja”, karta doleti do adrese, a krugovi hoda šire se redom;
    - **karta:** jezerska ljestvica, legenda uz kartu, kartica naselja sa smeđim pojasom;
    - **provjere:** kritika (dizajn i detektor) i popravci, detektor bez nalaza; `make verify` prolazi (pytest 149, Vitest 61, Playwright 60, axe u obje teme i 320 px); snimke prije u `docs/images/prije-redizajna/`, poslije u `docs/images/`.
    - **završni pregled (Impeccable, dva kruga):** riješeno tijelo izvještaja kao retci, staza „Dijelovi izvještaja”, gumb uz adresu na mobitelu; otvoreno (odluka tima): prijedlozi kao „iskaznice” sa smeđim pojasom, popis „Svakodnevni život” kao putokazi, oznaka „Predloži mjesto za život” iznad trake (drži je postojeći e2e test navigacije), nacrtana strelica padajućih izbornika.
17. [x] Zeleniji „Putokaz” s instrumentima (8. 11., grana `feature/instrumenti`; kratki smjer „Instrumenti” s papirom, tintom i serifom korisnik je odbio):
    - **izgled:** putokaz s daskama i ploča mjesta vraćeni; šumska zelena za radnje i stazu, livadna podloga, boja prirode za svako mjerenje; zelena ljestvica karte;
    - **izvještaj:** okolišni pregled kao instrumenti (vodomjer, ravnala zraka s pragovima WHO-a i EU-a, krug zelenila od točkica, ravnalo prometnice, radar požara, luk sunca) sa zaglavljem u boji mjerenja; ključne činjenice s točkom boje vode na svoj instrument;
    - **naslovnica:** „Šest mjerenja okoliša za svaku adresu” u bojama izvještaja;
    - **interakcija i poravnanje:** glatki prijelazi i podizanje ploča na hover, crta staze u navigaciji raste, iste težine poveznica i `scrollbar-gutter: stable` (ništa se ne pomiče između stranica); Impeccable detektor bez nalaza na naslovnici i izvještaju.
18. [x] Pravila profila u „Predloži mjesto” (8. 11., grana `feature/profili-uvjeti`): za Studenta je prije prvi bio Kastav jer je profil mijenjao samo težine.
    - **pravila:** `config/finder_rules.json` po profilu ima obavezne uvjete, važne kriterije s težinama i obrazloženje (Student: studiji u naselju ili veće studijsko središte do 15 km uz stajalište; Umirovljenik: trgovina, ljekarna i liječnik do 15 min hoda; Obitelj: vrtić i škola do 15 min hoda; Općenito i Rad od kuće: trgovina pješice); uz manje od 5 naselja koja ispunjavaju uvjete dodaju se ona kojima nedostaje jedan uvjet, s napomenom;
    - **novi izvori:** MZOM „Ustanove iz sustava visokog obrazovanja” i „Studijski programi visokih učilišta” (data.gov.hr, Otvorena dozvola; 28 mjesta, svih 28 spareno s naseljima DGU-a), OSM opće i kliničke bolnice (35), studentski domovi (21) i studentske menze (4); planirana optika nema otvoreni skup pa se ne boduje;
    - **profili naselja** dobili minute hoda do najbližeg mjesta svake vrste (ponovni izračun 783 s, svih 6.759 naselja s mrežom hoda, postojeće vrijednosti nepromijenjene);
    - **čarobnjak:** uz svaki profil piše što zahtijeva, uz prijedlog „Zašto je predloženo” s vrijednostima i „Što nedostaje”; broj uz prijedlog je „za profil”;
    - **provjera smislenosti:** top 10 za svaki profil u RH i Osječko-baranjskoj; Student: Zagreb, Split, Osijek, Rijeka, Zadar, Pula, Dubrovnik, Velika Gorica, Zaprešić, Varaždin (u OBŽ Osijek pa njegova predgrađa i Đakovo); testovi pravila u `backend/tests/test_finder_rules.py` (pytest 165, Vitest 64, Playwright 60, `make verify` prolazi);
    - **prometnice (8. 11.):** Split je bio prvi gotovo u svakom profilu jer mu je središte u pješačkoj staroj jezgri (100/100), a 79 % naselja bilo je „blizu prometnice” zbog županijske ceste kroz selo. Sad se županijske ceste (Ž) ne broje, a za naselje se računa udio svih 1.683.411 adresa DGU-a po pojasevima (`ingest/settlement_traffic.py`, 19 s); Split ima 48/100 (57 % adresa do 300 m od velike ceste), Zagreb 70, Osijek 46. Zlatni testovi ažurirani (Vinkovci, Nijemci), novi `tests/test_traffic.py`;
    - **usput:** `deploy/Dockerfile.web` kopira `config/`, bez čega se frontend ne bi izgradio u Dockeru (uvozi `profiles.json` i `finder_rules.json`).
19. [x] Dorada sučelja prema primjedbama korisnika (8. 11., grana `feature/dorada-sucelja`):
    - **naslovnica:** bez primjera adresa i bez retka s izjavom; izjava ostaje jednom na dnu izvještaja, u podnožju (dva retka) i na „O alatu”;
    - **izvještaj:** kraći i topliji sažetak iz predložaka (poplava prva samo kad prijeti); poplave i požari jednom rečenicom bez crteža, zrak ocjenom riječju i ljestvicom od četiri razine, brojke i pragovi pod „Detalji i izvor”; požari pošteno: EFFIS bilježi uglavnom požare od otprilike 30 ha naviše; karta hoda kao jedan popis „Najbliže pješice” (npr. „Trgovina – 3 minute”), pojasevi 5/10/15 u detaljima, jedna uputa;
    - **svugdje „minuta”:** `fmt.minutes` i `minutesText` („manje od minute”, „1 minuta”, „4 minute”, „12 minuta”); „Split” umjesto „Split, Split”;
    - **Karta:** pet najbolje ocijenjenih naselja (najmanje 200 stanovnika) ili pet rezultata pretrage; jednostavnije kartice naselja; razlika Skora na Karti (naselje, 83 za Split) i u izvještaju (točka, 92) objašnjena na kartici i u izvještaju;
    - **Predloži mjesto:** uz prijedlog uvjeti profila (✓), dva do tri obična razloga, jedna napomena „Na što obratiti pažnju”, brojke pod „Detalji”;
    - **usput:** CSS točkica zelenila skrivao je točkice boje na karti hoda (greška iz prošlog redizajna); `make verify` prolazi (pytest 170, Vitest 64, Playwright 60), snimke osvježene.
