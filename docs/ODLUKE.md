# Odluke

Jedna odluka po retku: datum, odluka, razlog.

- 2026-11-02: Glavna grana je `main`. Razlog: CLAUDE.md, odjeljak 2.
- 2026-11-02: ESLint 9 umjesto 10. Razlog: `eslint-plugin-jsx-a11y` 6.10 još ne podržava ESLint 10.
- 2026-11-02: TypeScript 5.9 umjesto 7.0 iz predloška Vitea. Razlog: `typescript-eslint` traži API TypeScripta 5.x.
- 2026-11-02: Font Inter (`@fontsource-variable/inter`, OFL-1.1), poslužen iz vlastitog builda. Razlog: dobra podrška za hrvatske dijakritike, bez vanjskih poslužitelja fontova.
- 2026-11-02: Valhalla iz slike `ghcr.io/valhalla/valhalla-scripted`, pločice se grade iz OSM izvatka Geofabrika pri prvom pokretanju. Razlog: službena slika projekta, bez ručne izgradnje.
- 2026-11-02: Na Windowsima se `make` pokreće iz MSYS2 (`C:\msys64\usr\bin`). Razlog: Makefile koristi POSIX ljusku.
- 2026-11-02: `CONTACT_EMAIL` se ne popunjava automatski; dok ga tim ne upiše, User-Agent je `PrijePotpisa/0.1 (+datathon prototype)`. Razlog: adresu e-pošte bira tim.
- 2026-11-02: Tijekom razvoja `scripts/check_readme.py` namjerno pada zbog oznaka `AUTO:` u README-u; prolazi tek nakon revizije README-a (zadatak P1). Razlog: README se piše na kraju prema stvarnom stanju.
- 2026-11-02: Uz statuse dobro, upozorenje, loše i nema podataka uveden je status „Bez ocjene” (info) za kategorije bez praga s izvorom (npr. sunce). Razlog: pravilo 4 zabranjuje pragove bez izvora, a vrijednost je i dalje korisna.
- 2026-11-02: Brzina hoda 4,5 km/h (1,25 m/s) kao obrazložena pretpostavka: nešto sporije od zadane vrijednosti Valhalle za pješake (5,1 km/h), kako bi vremena bila realna i za starije osobe i roditelje s djecom. Razlog: CLAUDE.md, odjeljak 6.
- 2026-11-02: Procjena buke uz autoceste, brze i glavne ceste uključuje i ceste označene `highway=secondary`. Razlog: u hrvatskom OSM-u glavne gradske prometnice (npr. Ulica grada Vukovara, Savska cesta i Ilica u Zagrebu) uglavnom su označene kao `secondary`, pa bi se bez njih buka u gradovima sustavno podcjenjivala.
- 2026-11-02: EEA strateške karte buke ne koriste se jer licenca dopušta samo istraživanje i neprofitnu upotrebu (nije otvorena); koristi se rezervni plan iz CLAUDE.md (udaljenost od prometnica iz OSM-a) uz poveznicu na preglednik EEA-e. Razlog: CLAUDE.md traži isključivo otvorene podatke.
- 2026-11-02: Licenca JRC karata poplava navedena je proturječno (ODbL 1.0 u katalogu, CC BY 4.0 u copyright.txt); navodimo obje i poštujemo strožu (ODbL). Razlog: obje dopuštaju upotrebu uz navođenje izvora.
- 2026-11-02: HZZO popisi ordinacija i ljekarni i HŽPP GTFS nemaju navedenu licencu, ali su javno objavljeni za ponovnu upotrebu (HŽPP izričito „za izradu aplikacija”); koriste se uz navođenje izvora, a od HZZO-a samo adrese ordinacija i ljekarni, bez imena liječnika. GTFS Šibenika nema licencu ni objavu na Portalu i ne koristi se. Razlog: pravilo 3 i privatnost.
- 2026-11-02: Obiteljski liječnici i pedijatri dolaze isključivo iz HZZO-a, a OSM samo dopunjuje vrtiće, osnovne škole (prema nazivu) i ljekarne udaljene više od 100 m od službenih. Razlog: OSM `amenity=doctors` uključuje specijaliste i privatne ordinacije bez ugovora s HZZO-om.
- 2026-11-02: Ako u blizini postoje stajališta, ali nema voznog reda u otvorenom obliku, potreba „stajalište s barem jednim polaskom na sat” prikazuje se kao „nije provjereno”, a ne kao „nedostaje”. Razlog: izostanak podatka nije dokaz da polazaka nema.
- 2026-11-03: PVGIS se pita u pozadini (najviše dva istodobna upita); izvještaj čeka najviše 6 s, a odgovor se sprema u memorijsku predmemoriju za sljedeći posjet. Demo adrese zagrijavaju se pri pokretanju. Razlog: izmjereno vrijeme odziva PVGIS-a bilo je 2–12 s, a izvještaj treba biti brz.
- 2026-11-03: Broj stanovnika naselja (DZS, Popis 2021.) spaja se s DGU naseljima po imenu grada ili općine i naselja (98,1 % naselja), jer tablica DZS-a nema šifre. Razlog: jedini način spajanja; nespojena naselja ne prikazuju broj.
- 2026-11-03: Pristupni zapisi su isključeni (uvicorn `--no-access-log`, Caddy `output discard`). Razlog: koordinate u upitu otkrivaju adresu, a CLAUDE.md zabranjuje spremanje adresa.
- 2026-11-03: Požari (P2) iz EFFIS-ova javnog WFS-a umjesto skupnog preuzimanja. Razlog: skupno preuzimanje traži račun (HTTP 403), a CLAUDE.md dopušta požare samo bez računa.
