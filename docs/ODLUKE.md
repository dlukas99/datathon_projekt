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
