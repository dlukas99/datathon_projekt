# Alati, biblioteke i licence

Pravila natjecanja traže popis korištenih alata, uključujući alate umjetne inteligencije. Kod rješenja je pod licencom **EUPL-1.2** ([LICENSE](../LICENSE)), a izvedeni podaci pod CC BY 4.0; licence izvora podataka su u [IZVORI_PODATAKA.md](IZVORI_PODATAKA.md). Sve navedene biblioteke imaju licence otvorenog koda spojive s EUPL-1.2 (stanje 8. 11. 2026., prema metapodacima instaliranih paketa).

## Alati umjetne inteligencije

| Alat | Uloga | Licenca |
|---|---|---|
| Claude Code (Anthropic) | pisanje koda, testova i dokumentacije uz pregled i odluke tima | vlasnički alat, uvjeti korištenja Anthropica |
| Impeccable (dodatak za Claude Code) | pregled dizajna sučelja i provjera uzoraka; razvojni alat, nije dio aplikacije | Apache-2.0 |
| Jezični model asistenta (neobavezno) | samo prepoznavanje namjere pitanja i pretvaranje pitanja u filtre; brojke nikad ne dolaze iz modela | bilo koji model preko OpenAI-kompatibilnog API-ja (npr. lokalni Ollama s otvorenim modelom); u demou bez ključa asistent radi s pravilima |

## Backend (Python 3.12, upravitelj paketa uv)

| Biblioteka | Uloga | Licenca |
|---|---|---|
| FastAPI | API | MIT |
| Uvicorn | poslužitelj API-ja | BSD-3-Clause |
| Pydantic, pydantic-settings | modeli i postavke | MIT |
| httpx | HTTP klijent | BSD-3-Clause |
| NumPy | izračuni | BSD-3-Clause |
| pandas | tablice | BSD-3-Clause |
| PyArrow | GeoParquet i Parquet | Apache-2.0 |
| rasterio | rasteri (GeoTIFF) | BSD-3-Clause |
| Shapely | geometrija | BSD-3-Clause |
| pyproj | koordinatni sustavi | MIT |
| GeoPandas, pyogrio | obrada vektorskih slojeva (samo obrada) | BSD-3-Clause, MIT |
| pyosmium | čitanje OpenStreetMapa (samo obrada) | BSD-2-Clause |
| openpyxl, xlrd | tablice HZZO-a (samo obrada) | MIT, BSD |
| scikit-learn | evaluacija modela za zrak ([ML.md](ML.md)) | BSD-3-Clause |
| pytest, ruff, mypy, pandas-stubs | testovi i provjere | MIT, MIT, MIT, BSD-3-Clause |

## Frontend (TypeScript, npm)

| Biblioteka | Uloga | Licenca |
|---|---|---|
| React, React DOM | sučelje | MIT |
| React Router | stranice | MIT |
| TanStack Query | dohvat podataka | MIT |
| MapLibre GL JS | karte | BSD-3-Clause |
| Lucide (lucide-react) | ikone | ISC |
| Bricolage Grotesque, Figtree (@fontsource-variable) | fontovi s vlastitog poslužitelja | OFL-1.1 |
| Vite, @vitejs/plugin-react, Vitest | izgradnja i testovi | MIT |
| TypeScript | jezik | Apache-2.0 |
| ESLint, typescript-eslint, eslint-plugin-jsx-a11y, eslint-plugin-react-hooks | provjera koda i pristupačnosti | MIT |
| Testing Library, jsdom | testovi komponenti | MIT |
| Playwright | testovi u pregledniku i snimke zaslona | Apache-2.0 |
| axe-core (@axe-core/playwright) | automatska provjera pristupačnosti | MPL-2.0 |

`npm audit` za ovisnosti koje se koriste pri radu aplikacije ne javlja ranjivosti; sedam umjerenih nalaza odnosi se samo na razvojni alat ESLint.

## Usluge i infrastruktura

| Komponenta | Uloga | Licenca |
|---|---|---|
| Valhalla | pješačka mreža, izokrone i rute | MIT |
| Caddy | HTTPS i posluživanje frontenda | Apache-2.0 |
| Docker, Docker Compose | pokretanje | Apache-2.0 |
| OpenFreeMap | podloga karte | stil i softver MIT; podaci © OpenMapTiles i suradnici OpenStreetMapa (ODbL) |
| JRC PVGIS API | sunčev potencijal, uživo | slobodna upotreba uz navođenje izvora |
