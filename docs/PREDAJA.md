# Predaja rješenja

**Natjecanje:** Datathon Portala otvorenih podataka 2026., izazov B: Okoliš i održivi prostor.
**Rok predaje:** ponedjeljak, 9. 11. 2026. u 24:00.
**Predaja:** e-poštom na open.data@mpudt.hr.

Pravila natjecanja traže:
- izvorni kod ili javni repozitorij;
- tehničku i projektnu dokumentaciju (arhitektura i popis skupova podataka s izvorima);
- demo materijale (poveznica na prototip, snimke zaslona);
- video do 3 minute.

## Što je spremno u repozitoriju

| Zahtjev | Gdje |
|---|---|
| Izvorni kod | `backend/`, `frontend/`, `deploy/`, `scripts/` (licenca EUPL-1.2, `LICENSE`) |
| Opis rješenja | `README.md` |
| Arhitektura, standardi, tehnički, organizacijski i pravni preduvjeti | `docs/ARHITEKTURA.md` |
| Popis skupova podataka s izvorima i licencama | `docs/IZVORI_PODATAKA.md` (i stranica „Izvori” u aplikaciji) |
| Metodologija i pragovi | `docs/METODOLOGIJA.md` |
| Kvaliteta podataka na Portalu | `docs/KVALITETA_PODATAKA.md` |
| Pristupačnost | `docs/PRISTUPACNOST.md` |
| Asistent i testna pitanja | `docs/ASISTENT.md` |
| Odluke tijekom izrade | `docs/ODLUKE.md` |
| Upute za postavljanje | `docs/DEPLOY.md` |
| Snimke zaslona | `docs/images/` (`make screenshots`) |
| Scenarij videa | `docs/VIDEO_SCENARIJ.md` |

## Što moraju napraviti ljudi

Redoslijed je važan; uz svaku stavku je preporučeni rok.

1. **Imena tima, mentora i visokog učilišta** (do 6. 11.): upisati u `README.md` umjesto oznaka `TODO(tim)`.
2. **`CONTACT_EMAIL`** (do 6. 11.): upisati u `.env` i na poslužitelju. Adresa ide u User-Agent prema izvorima podataka.
3. **Javni repozitorij na GitHubu** (do 6. 11.):
   - napraviti repozitorij (npr. `prije-potpisa`), dodati `origin` i pushati granu `main`:
     ```bash
     git remote add origin git@github.com:KORISNIK/prije-potpisa.git
     git push -u origin main
     ```
   - provjeriti da u repozitoriju nema `.env` ni mape `data/` (u `.gitignore` su).
4. **Poslužitelj i domena** (do 7. 11.): prema `docs/DEPLOY.md`.
   - Treba Linux s Dockerom, 2 vCPU, 4 GB RAM-a i 10 GB diska, te domena s DNS zapisom na poslužitelj.
   - Podaci se prenose skriptom `scripts/upload_data.sh` ili pripremaju na poslužitelju s `make data`.
   - Provjeriti `https://DOMENA/api/health` i izvještaj za svih pet demo adresa iz `scripts/demo_addresses.json`.
5. **Demo URL u README-u** (odmah nakon postavljanja): zamijeniti `TODO(ljudi)` u odjeljku „Demo” javnim URL-om.
6. **Ključ za jezični model** (neobavezno): ako želite asistenta s modelom, u `.env` na poslužitelju postaviti `LLM_BASE_URL`, `LLM_API_KEY` i `LLM_MODEL` (bilo koji OpenAI-kompatibilni API, npr. lokalni Ollama s otvorenim modelom). Bez ključa asistent radi s pravilima.
7. **Snimanje videa** (do 8. 11.): prema `docs/VIDEO_SCENARIJ.md`, do 3 minute. Objaviti ga (npr. YouTube kao „neizlistano”) i poveznicu upisati u `README.md` (redak „Prezentacija rješenja” u tablici kriterija).
8. **Završna provjera** (9. 11. do 18:00):
   - `make verify` na čistom klonu s pripremljenim podacima;
   - `python scripts/check_readme.py` ispisuje preostale oznake `TODO(tim)` i `TODO(ljudi)`; sve trebaju biti zamijenjene.
9. **Slanje e-pošte** (9. 11., najkasnije do 24:00) na **open.data@mpudt.hr**, s naslovom npr. „Datathon 2026 – izazov B – Prije potpisa”. Sadržaj:
   - naziv rješenja i izazov (B: Okoliš i održivi prostor);
   - imena članova tima, mentora i visokog učilišta;
   - poveznica na javni repozitorij;
   - poveznica na demo;
   - poveznica na video;
   - poveznice na dokumentaciju u repozitoriju (`README.md`, `docs/ARHITEKTURA.md`, `docs/IZVORI_PODATAKA.md`).

## Poznata ograničenja koja treba imati na umu

- Vozni red HŽPP-a vrijedi do 13. 12. 2026.
- Ako Valhalla na poslužitelju još gradi pločice (prvih 2–3 minute nakon prvog pokretanja), kategorije hoda prikazuju „Nema podataka”. Pričekajte prije snimanja ili ocjenjivanja.
- Izvori bez navedene licence (HZZO, HŽPP) koriste se uz obrazloženje u `docs/ODLUKE.md`. Prije stvarnog uvođenja preporučuje se pisana potvrda izdavača.
