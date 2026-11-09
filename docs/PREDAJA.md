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
| Popis skupova podataka s izvorima i licencama | `docs/IZVORI_PODATAKA.md` (i dio „Izvori podataka” na stranici „O alatu” u aplikaciji) |
| Metodologija i pragovi | `docs/METODOLOGIJA.md` |
| Kvaliteta podataka na Portalu | `docs/KVALITETA_PODATAKA.md` |
| Pristupačnost | `docs/PRISTUPACNOST.md` |
| Asistent i testna pitanja | `docs/ASISTENT.md` |
| Odluke tijekom izrade | `docs/ODLUKE.md` |
| Alati, biblioteke i AI alati s licencama | `docs/ALATI_I_LICENCE.md` |
| Model za zrak (evaluacija) | `docs/ML.md` |
| Pokretanje za razvoj | `docs/RAZVOJ.md` |
| Nalazi testiranja | `docs/NALAZI_TESTIRANJA.md` |
| Upute za postavljanje | `docs/DEPLOY.md` |
| Snimke zaslona | `docs/images/` (`make screenshots`) |
| Scenarij videa | `docs/VIDEO_SCENARIJ.md` |

## Tim

- **Tim „Požega”:** Domagoj Lukas i Fabio Mandić, studenti diplomskog studija Računarstvo, smjer Podatkovna znanost.
- **Mentor i voditelj tima:** dr. sc. Matej Džijan (FERIT).
- **Visoko učilište:** Fakultet elektrotehnike, računarstva i informacijskih tehnologija Osijek (FERIT), Sveučilište J. J. Strossmayera u Osijeku.

## Što moraju napraviti ljudi

Rok predaje je **ponedjeljak 9. 11. 2026. u 24:00**. Uz svaku stavku je preporučeni rok.

1. **Javni repozitorij** (9. 11. do 12:00): https://github.com/dlukas99/datathon_projekt, grana `main`. Postaviti ga kao **javni** (Settings → General → Danger Zone → Change visibility) i provjeriti da u njemu nema `.env` ni mape `data/` (u `.gitignore` su).
2. **Poslužitelj i domena** (9. 11. do 14:00) prema [DEPLOY.md](DEPLOY.md): Linux s Dockerom, 2 vCPU, 4 GB RAM-a, 10 GB diska i domena s DNS zapisom. Podatke prenijeti skriptom `scripts/upload_data.sh` (ili `make data` na poslužitelju). U `.env` na poslužitelju upisati `CONTACT_EMAIL` (ide u User-Agent prema izvorima podataka) i `DOMAIN`.
   - Provjeriti `https://DOMENA/api/health` te izvještaj za svih šest demo adresa iz `scripts/demo_addresses.json`, „Predloži mjesto” i kartu.
3. **Demo URL u README-u** (odmah nakon postavljanja): u `README.md` zamijeniti obje oznake `TODO(ljudi)` za demo javnim URL-om.
4. **Ključ za jezični model** (neobavezno): `LLM_BASE_URL`, `LLM_API_KEY` i `LLM_MODEL` u `.env` na poslužitelju (bilo koji OpenAI-kompatibilni API, npr. lokalni Ollama s otvorenim modelom). Bez ključa asistent radi s pravilima.
5. **Video** (9. 11. do 18:00): snimiti prema [VIDEO_SCENARIJ.md](VIDEO_SCENARIJ.md), do 3 minute, na javnoj demo inačici. Objaviti (npr. YouTube kao „neizlistano”) i poveznicu upisati u `README.md` umjesto `TODO(ljudi)` u retku „Prezentacija rješenja”.
6. **Završna provjera** (9. 11. do 20:00): `python scripts/check_readme.py` ne smije ispisati nijednu oznaku `TODO(ljudi)`; commit i push na `main`.
7. **Slanje e-pošte** (mentor, 9. 11. najkasnije do 24:00, preporuka do 21:00) na **open.data@mpudt.hr**, prema nacrtu ispod.

## Nacrt e-pošte (šalje mentor)

**Prima:** open.data@mpudt.hr
**Predmet:** Datathon Portala otvorenih podataka 2026 – Izazov B – Tim Požega – Dobro mjesto

> Poštovani,
>
> u ime tima „Požega” šaljem rješenje za Datathon Portala otvorenih podataka 2026., izazov B: Okoliš i održivi prostor.
>
> **Rješenje:** Dobro mjesto, web aplikacija koja za bilo koju adresu u Hrvatskoj iz otvorenih podataka pokazuje okoliš (poplave, zrak, zelenilo, udaljenost od prometnica, požari, sunce) i što je pješice na dohvat ruke, a za odabrani profil (obitelj, umirovljenik, student, rad od kuće) predlaže mjesta za život s obrazloženjem.
>
> **Poveznice:**
> - javni repozitorij (izvorni kod, licenca EUPL-1.2): https://github.com/dlukas99/datathon_projekt
> - demo: [javni URL]
> - video (do 3 minute): [poveznica na video]
> - dokumentacija: README (https://github.com/dlukas99/datathon_projekt#readme), arhitektura (docs/ARHITEKTURA.md), skupovi podataka s izvorima i licencama (docs/IZVORI_PODATAKA.md), metodologija (docs/METODOLOGIJA.md), alati i licence (docs/ALATI_I_LICENCE.md)
>
> **Tim:** Domagoj Lukas i Fabio Mandić, studenti diplomskog studija Računarstvo, smjer Podatkovna znanost, Fakultet elektrotehnike, računarstva i informacijskih tehnologija Osijek (FERIT), Sveučilište J. J. Strossmayera u Osijeku.
> **Mentor i voditelj tima:** dr. sc. Matej Džijan (FERIT).
>
> **AI alati:** pri izradi koda i dokumentacije korišten je Claude Code (Anthropic), a za pregled dizajna sučelja dodatak (skill) Impeccable (Apache-2.0). Asistent u aplikaciji može koristiti bilo koji jezični model preko OpenAI-kompatibilnog API-ja, a bez modela radi s pravilima; brojke u odgovorima uvijek dolaze iz izračuna, ne iz modela. Popis je u docs/ALATI_I_LICENCE.md.
>
> Molim potvrdu primitka.
>
> Srdačan pozdrav,
> dr. sc. Matej Džijan
> FERIT, Sveučilište J. J. Strossmayera u Osijeku

## Poznata ograničenja koja treba imati na umu

- Vozni red HŽPP-a vrijedi do 13. 12. 2026.
- Ako Valhalla na poslužitelju još gradi pločice (prvih 2–3 minute nakon prvog pokretanja), kategorije hoda prikazuju „Nema podataka”. Pričekajte prije snimanja ili ocjenjivanja.
- Izvori bez navedene licence (HZZO, HŽPP) koriste se uz obrazloženje u `docs/ODLUKE.md`. Prije stvarnog uvođenja preporučuje se pisana potvrda izdavača.
