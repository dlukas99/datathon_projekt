# Postavljanje na poslužitelj

Produkcija je jedan Docker Compose stog (`deploy/docker-compose.yml`) s tri usluge:

| Usluga | Slika | Uloga |
|---|---|---|
| `web` | `deploy/Dockerfile.web` (Node 22 za izgradnju, Caddy 2 za posluživanje) | HTTPS (automatski certifikat za `DOMAIN`), izgrađeni frontend, prosljeđivanje `/api/*` na API |
| `api` | `deploy/Dockerfile.api` (Python 3.12, uv) | FastAPI s obrađenim podacima iz `data/processed/` |
| `valhalla` | `ghcr.io/valhalla/valhalla-scripted:3.9.1` | mreža hoda; pločice se grade iz OSM izvatka pri prvom pokretanju |

Postavljanje je lokalno provjereno na Docker Desktopu s `DOMAIN=localhost` (`https://localhost/`).

## Preduvjeti

- Poslužitelj s Linuxom, Dockerom i Docker Composeom (v2).
- Najmanje 2 vCPU, 4 GB RAM-a i 10 GB diska. Izgradnja pločica Valhalle za Hrvatsku traje oko 2–3 minute i troši do 1,9 GB RAM-a; u radu koristi oko 0,5 GB.
- Domena čiji DNS zapis A/AAAA pokazuje na poslužitelj; otvoreni portovi 80 i 443.
- Obrađeni podaci (`data/processed/`, oko 0,6 GB) i OSM izvadak (`data/raw/osm/croatia-latest.osm.pbf`, oko 0,2 GB).

## Koraci

1. Na poslužitelju klonirajte repozitorij, npr. u `/opt/prije-potpisa`.
2. Na vlastitom računalu pripremite podatke i prenesite ih:

   ```bash
   make data
   scripts/upload_data.sh korisnik@poslužitelj /opt/prije-potpisa
   ```

   Podatke možete pripremiti i izravno na poslužitelju: `make setup` pa `make data` (traje oko 20 minuta, ovisno o vezi).
3. Na poslužitelju u korijenu repozitorija napravite `.env` iz `.env.example`. Postavite `DOMAIN`, `CONTACT_EMAIL` i, po želji, `LLM_*`.
4. Pokrenite:

   ```bash
   docker compose --env-file .env -f deploy/docker-compose.yml up -d --build
   ```

5. Provjerite:

   ```bash
   curl https://DOMENA/api/health          # {"status":"ok"}
   docker compose -f deploy/docker-compose.yml logs valhalla | grep "Tile extract"
   ```

   Dok Valhalla gradi pločice (prvo pokretanje), izvještaji prikazuju „Mreža hoda trenutačno nije dostupna” za kategorije hoda; ostale kategorije rade odmah.

6. Upišite javni URL u `README.md` (odjeljak „Demo”).

## Osvježavanje podataka

```bash
make data                                       # ponovno koristi već preuzete datoteke
scripts/upload_data.sh korisnik@poslužitelj /opt/prije-potpisa
docker compose -f deploy/docker-compose.yml restart api
```

Za potpuno svježe izvore obrišite odgovarajuće datoteke u `data/raw/` prije `make data`. Novi OSM izvadak traži ponovnu izgradnju pločica:

```bash
docker compose -f deploy/docker-compose.yml down
docker volume rm prijepotpisa_valhalla_tiles
docker compose -f deploy/docker-compose.yml up -d
```

Vozni red HŽPP-a vrijedi do 13. 12. 2026.; nakon toga treba ponoviti `make data`. Vozni red Gradskog parkinga Šibenik vrijedi do 7. 6. 2027.

`make data` uz vozne redove izrađuje i `osm_stop_lines.parquet` (linije na stajalištima iz OSM izvatka, nekoliko sekundi). Pri prijenosu prenesite cijelu mapu `data/processed/`.

## Privatnost i sigurnost

- Caddy ne vodi pristupni zapis (`log { output discard }`), a API se pokreće s `--no-access-log`, pa se upisane adrese i koordinate nigdje ne spremaju.
- API radi kao korisnik bez administratorskih prava. Ključevi se čitaju samo iz okoline (`.env`) i nikad ne ulaze u sliku.
- Caddy postavlja zaglavlja `Strict-Transport-Security`, `X-Content-Type-Options`, `Referrer-Policy: no-referrer` i `Permissions-Policy`.
