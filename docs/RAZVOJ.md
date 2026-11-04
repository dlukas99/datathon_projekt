# Upute za razvoj: od praznog računala do aplikacije koja radi

Ova uputa vodi korak po korak kroz pokretanje projekta „Prije potpisa” na vlastitom računalu (Windows 10/11) i rad u vlastitoj grani. Naredbe su pisane za **PowerShell u VS Codeu** (Terminal → New Terminal).

Treba vam oko **1 sat** prvi put: veći dio je čekanje na preuzimanje podataka.

---

## 1. Što instalirati (jednom)

| Program | Čemu služi | Gdje |
|---|---|---|
| **Git** | preuzimanje koda i rad u granama | https://git-scm.com/download/win |
| **VS Code** | uređivač koda | https://code.visualstudio.com/ |
| **uv** | Python i njegove biblioteke za backend (sam instalira Python 3.12) | https://docs.astral.sh/uv/getting-started/installation/ |
| **Node.js 22 ili noviji** (LTS) | frontend (React) | https://nodejs.org/ |
| **Docker Desktop** | Valhalla, program koji računa hod po ulicama | https://www.docker.com/products/docker-desktop/ |

Napomene:
- Pri instalaciji Gita ostavite zadane postavke.
- **Docker Desktop** nakon instalacije pokrenite barem jednom i pričekajte da u donjem lijevom kutu piše da radi („Engine running”). Docker treba oko 2 GB slobodnog RAM-a.
- Nakon instalacija **zatvorite i ponovno otvorite VS Code**, da terminal vidi nove programe.

Provjerite u terminalu da je sve tu (svaka naredba treba ispisati verziju):

```powershell
git --version
uv --version
node --version
npm --version
docker --version
```

### Preporučena proširenja za VS Code

U VS Codeu otvorite Extensions (Ctrl+Shift+X) i instalirajte:
- **Python** (Microsoft)
- **Ruff** (Astral Software)
- **ESLint** (Microsoft)

---

## 2. Preuzimanje projekta

U VS Codeu: **File → Open Folder** i odaberite mapu u kojoj želite projekt (npr. `Documents`). Zatim u terminalu:

```powershell
git clone https://github.com/dlukas99/datathon_projekt.git
cd datathon_projekt
code .
```

Otvorit će se novi prozor VS Codea s projektom. U njemu otvorite novi terminal (Terminal → New Terminal); sve sljedeće naredbe pokreću se iz korijena projekta (mapa `datathon_projekt`).

Odmah uključite zaštitu od slučajnog pusha na `main` (jednom po klonu):

```powershell
git config core.hooksPath .githooks
```

Ta naredba ne ispisuje ništa. Od tada git odbija svaki `git push` na granu `main` (više u odjeljku 7).

Postavite i svoje ime i e-poštu za commitove (ako to već niste napravili na ovom računalu):

```powershell
git config --global user.name "Ime Prezime"
git config --global user.email "vas@email.com"
```

---

## 3. Postavke (`.env`)

```powershell
Copy-Item .env.example .env
```

Otvorite `.env` i upišite svoju e-poštu u `CONTACT_EMAIL=` (ide u User-Agent kad preuzimamo podatke, da izvori znaju tko ih preuzima). Ostala polja ostavite prazna. `.env` se nikad ne commita (u `.gitignore` je).

---

## 4. Instalacija biblioteka (jednom, oko 3–5 minuta)

```powershell
cd backend
uv sync
cd ..\frontend
npm ci
npx playwright install chromium
cd ..
```

- `uv sync` instalira Python 3.12 i sve backend biblioteke u `backend\.venv`.
- `npm ci` instalira frontend biblioteke u `frontend\node_modules`.
- `npx playwright install chromium` preuzima preglednik za automatske testove.

---

## 5. Preuzimanje i obrada podataka (jednom, oko 20–30 minuta)

Podaci nisu u gitu (prevelike su datoteke). Jedna naredba ih preuzme sa službenih izvora i pripremi:

```powershell
cd backend
$env:PYTHONUTF8 = "1"
uv run python -m ingest.run_all
cd ..
```

Što se događa (redom, svaki korak ispisuje naslov i trajanje):

1. OpenStreetMap izvadak za Hrvatsku (oko 200 MB) i izdvajanje trgovina, parkova, stajališta i adresa
2. Adrese i upravne jedinice Državne geodetske uprave (oko 300 MB)
3. Broj stanovnika po naseljima (DZS)
4. Karte poplava (JRC), kvalitete zraka (EEA) i pokrova tla (ESA WorldCover), ukupno oko 1,5 GB
5. Opožarene površine (EFFIS)
6. Vozni redovi ZET-a, HŽPP-a i Autotroleja
7. Registri vrtića, škola, ordinacija i ljekarni, geokodirani nad adresama
8. Reciklažna dvorišta s Portala otvorenih podataka
9. Spajanje svih točaka u jedan sloj

Rezultat:
- `data\raw\` (izvorne datoteke, oko 2,6 GB)
- `data\processed\` (pripremljeni slojevi koje aplikacija čita, oko 550 MB)

Dobro je znati:
- **Prekid nije problem.** Ako preuzimanje pukne (npr. prekid veze), samo ponovno pokrenite istu naredbu: već preuzete datoteke se preskaču, a prekinuta se nastavlja.
- Na kraju mora pisati da nijedan korak nije pao. Ako neki padne, ispisat će se `GREŠKA` i naziv koraka; ponovite naredbu.

---

## 6. Pokretanje aplikacije

Trebaju **tri dijela**, svaki u svom terminalu (u VS Codeu: ikona **+** u panelu terminala otvara novi).

### Terminal 1: Valhalla (mreža hoda)

Docker Desktop mora biti pokrenut.

```powershell
docker compose -f deploy/docker-compose.dev.yml up -d
```

- **Prvi put** Valhalla oko 3 minute gradi „pločice” iz OSM izvatka. Kad je gotova, http://localhost:8002/status vraća tekst s `"version"`.
- Ova naredba se vrati odmah jer Valhalla radi u pozadini, pa terminal možete koristiti dalje.
- **Pokrenite je tek nakon koraka 5.** Treba datoteku `data\raw\osm\croatia-latest.osm.pbf`.

### Terminal 2: backend (API)

```powershell
cd backend
$env:PYTHONUTF8 = "1"
uv run uvicorn app.main:app --reload --port 8000 --no-access-log
```

Provjera: http://localhost:8000/api/health vraća `{"status":"ok"}`, a opis API-ja je na http://localhost:8000/api/docs.

### Terminal 3: frontend

```powershell
cd frontend
npm run dev
```

**Aplikacija je na http://localhost:5173.** Promjene u kodu frontenda vide se odmah; backend se zbog `--reload` sam ponovno pokrene kad spremite Python datoteku.

Zaustavljanje: u terminalima 2 i 3 pritisnite **Ctrl+C**, a Valhallu zaustavite naredbom `docker compose -f deploy/docker-compose.dev.yml down`. Pločice ostaju spremljene, pa sljedeće pokretanje traje nekoliko sekundi.

### Ako imate `make`

Na Linuxu, Macu ili Windowsima s MSYS2 sve gore radi i preko Makefilea: `make setup`, `make data`, `make dev`, `make verify`. Na običnim Windowsima `make` ne postoji, pa koristite naredbe iz ove upute. Rezultat je isti.

---

## 7. Rad u vlastitoj grani (obavezno pročitati)

### Zašto grane

- **`main`** je glavna verzija projekta. Ona se predaje i mora uvijek raditi.
- **Grana** (branch) je vaša privatna kopija za jedan zadatak. U njoj možete slobodno mijenjati, griješiti i commitati, a `main` ostaje netaknut.
- Kad je zadatak gotov, na GitHubu otvorite **pull request** (PR): zahtjev da se vaša grana spoji u `main`. Vlasnik repozitorija (dlukas99) ga pregleda i spoji.

**Zlatno pravilo: nikad ne commitajte i ne pushajte izravno na `main`.** Zaštita iz koraka 2 (`git config core.hooksPath .githooks`) odbije svaki push na `main` i ispiše što napraviti. Ako je niste uključili, uključite je sada.

### Kako znati na kojoj ste grani

- U VS Codeu **dolje lijevo** u statusnoj traci piše ime grane (npr. `main` ili `dorada-karte`).
- Ili u terminalu:

```powershell
git branch --show-current
```

Ako piše `main`, **ne mijenjajte kod** dok ne napravite granu.

### Rad na jednom zadatku, korak po korak

**1. Osvježite `main`** prije nego počnete, da radite na najnovijoj verziji:

```powershell
git switch main
git pull
```

Očekivano: `Already up to date.` ili popis novih promjena.

**2. Napravite svoju granu.** Ime neka kaže što radite: mala slova, crtice, bez razmaka i dijakritika, npr. `dorada-karte`, `fix-pretraga`, `docs-video`:

```powershell
git switch -c dorada-karte
```

Očekivano: `Switched to a new branch 'dorada-karte'`. Dolje lijevo u VS Codeu sada piše `dorada-karte`.

**3. Radite i spremajte promjene (commit).** Pogledajte što ste promijenili:

```powershell
git status
```

Dodajte promjene i spremite ih s porukom:

```powershell
git add .
git commit -m "feat: veća karta na mobitelu"
```

Poruke počnite s:
- `feat:` za novu stvar,
- `fix:` za popravak,
- `docs:` za dokumentaciju.

Commitajte često, nakon svake manje gotove cjeline.

**4. Prije slanja pokrenite provjere** iz koraka 8. Sve mora proći.

**5. Pošaljite granu na GitHub (push).** Prvi put za tu granu:

```powershell
git push -u origin dorada-karte
```

Svaki sljedeći put na istoj grani dovoljno je:

```powershell
git push
```

**6. Otvorite pull request:**
1. Otvorite https://github.com/dlukas99/datathon_projekt. Pojavit će se žuta traka „dorada-karte had recent pushes” s gumbom **Compare & pull request**. Kliknite ga.
2. Provjerite da piše **base: `main`** ← **compare: `dorada-karte`**.
3. Upišite naslov i kratko što ste napravili i kako ste provjerili.
4. Kliknite **Create pull request** i javite vlasniku repozitorija.

Dok PR čeka, možete nastaviti raditi na istoj grani (`git commit` pa `git push`); PR se sam osvježi.

**7. Nakon što je PR spojen**, vratite se na `main`, povucite novu verziju i obrišite staru granu:

```powershell
git switch main
git pull
git branch -d dorada-karte
```

Za sljedeći zadatak ponovite od koraka 1 s novom granom.

### Kad netko drugi promijeni `main` dok radite

Da vaša grana ima najnovije promjene (i da kasnije ne bude sukoba):

```powershell
git switch main
git pull
git switch dorada-karte
git merge main
```

Ako git javi **CONFLICT**, iste je retke mijenjalo dvoje ljudi:
1. U VS Codeu otvorite datoteke označene slovom **C** (Source Control panel, Ctrl+Shift+G). Vidjet ćete obje verzije s gumbima **Accept Current Change**, **Accept Incoming Change** i **Accept Both Changes**.
2. Odaberite što treba ostati i spremite datoteku.
3. Završite spajanje:

```powershell
git add .
git commit -m "merge: main u dorada-karte"
```

Ako niste sigurni, ne pogađajte: pitajte vlasnika repozitorija prije commita.

### Ako ste nešto zabrljali

| Situacija | Što napraviti |
|---|---|
| Promijenili ste kod, a još ste na `main` (niste commitali) | `git switch -c nova-grana`. Promjene idu s vama u novu granu, a `main` ostaje čist. |
| Commitali ste na `main`, ali **niste pushali** | Napravite granu s tim commitom: `git branch spas-grana`. Vratite lokalni `main` na stanje s GitHuba: `git reset --hard origin/main`. Nastavite u grani: `git switch spas-grana`. |
| Push na `main` javlja „STOP: push na granu main nije dopušten” | Zaštita radi kako treba. Postupite kao u retku iznad, zatim `git push -u origin spas-grana` i otvorite PR. |
| Želite odbaciti sve nespremljene promjene u jednoj datoteci | `git restore putanja/do/datoteke` (nepovratno briše te promjene). |
| Ne znate u kojem ste stanju | `git status` i `git log --oneline -5`. Pošaljite ispis vlasniku repozitorija. |

### Isto to bez terminala (VS Code)

- **Grana:** klik na ime grane dolje lijevo → **Create new branch…** → upišite ime.
- **Commit:** Source Control panel (Ctrl+Shift+G) → upišite poruku → **Commit** (kvačica). Ako pita za „stage all changes”, odaberite **Yes**.
- **Push:** gumb **Publish Branch** (prvi put) ili **Sync Changes**.
- Prije commita uvijek pogledajte ime grane dolje lijevo.

### Za vlasnika repozitorija (dlukas99, jednom)

Najsigurnija zaštita je na samom GitHubu: **Settings → Branches → Add branch protection rule** (ili **Rules → Rulesets**):
1. Za **Branch name pattern** upišite `main`.
2. Uključite **Require a pull request before merging**.
3. Spremite.

Tada GitHub odbije svaki izravni push na `main`, bez obzira na lokalne postavke. Kolegu dodajte pod **Settings → Collaborators → Add people**.

---

## 8. Provjere prije commita

Backend:

```powershell
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest -q
cd ..
```

Frontend:

```powershell
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
cd ..
```

Automatski test cijele aplikacije u pregledniku, s provjerom pristupačnosti (axe). Pokreće se nakon `npm run build`, treba pokrenutu Valhallu, a backend i frontend testovi pokreću sami:

```powershell
cd frontend
npx playwright test
cd ..
```

Sve mora proći (0 grešaka).

- `ruff format .` (bez `--check`) sam uredi Python kod.
- Zlatni testovi uspoređuju izvještaje za demo adrese sa snimkama u `backend\tests\fixtures\golden\`. Ako namjerno promijenite izračun ili osvježite podatke, snimke osvježite naredbom `uv run python -m tests.golden --update` (u mapi `backend`) i commitajte ih.

---

## 9. Gdje je što

```
backend/
  app/        API (FastAPI): main.py su rute, report.py sastavlja izvještaj, assistant.py je asistent
  analysis/   izračuni po kategorijama (environment.py: poplave, zrak, zelenilo, buka, požari)
  ingest/     preuzimanje i obrada izvora (run_all.py pokreće sve)
  tests/      testovi
frontend/
  src/pages/       stranice (naslovnica, izvještaj, usporedba, izvori, o alatu)
  src/components/  dijelovi (kartica kategorije, karta, pretraga, asistent)
  src/index.css    sav izgled (boje, razmaci, tamna tema)
  tests/           unit i e2e testovi
deploy/       Docker za produkciju i razvoj
docs/         dokumentacija (metodologija, izvori, arhitektura, predaja…)
scripts/      demo adrese, provjera README-a, prijenos podataka na poslužitelj
```

Važni dokumenti:
- [METODOLOGIJA.md](METODOLOGIJA.md): kako se računa i koji su pragovi
- [IZVORI_PODATAKA.md](IZVORI_PODATAKA.md): svi izvori s licencama
- [ODLUKE.md](ODLUKE.md): zašto je nešto napravljeno baš tako
- [PREDAJA.md](PREDAJA.md): što još treba za predaju

Pravila projekta (npr. nikad izmišljeni podaci, svaka brojka ima izvor) nalaze se u `CLAUDE.md` u korijenu projekta.

---

## 10. Česti problemi

| Problem | Rješenje |
|---|---|
| `uv`, `node` ili `docker` „is not recognized” | Zatvorite i ponovno otvorite VS Code (terminal ne vidi nove programe). Ako ne pomogne, ponovno pokrenite računalo. |
| `UnicodeEncodeError` ili čudni znakovi umjesto č, ć, ž | Prije Python naredbi pokrenite `$env:PYTHONUTF8 = "1"` (vrijedi za taj terminal). |
| `os error 4551` / „An Application Control policy has blocked this file” | Windows (Smart App Control) blokira Python koji je preuzeo uv. Instalirajte **Python 3.12** s https://www.python.org/downloads/ pa u mapi `backend` napravite okruženje na njemu: `Remove-Item -Recurse -Force .venv`, zatim `$env:UV_PYTHON_PREFERENCE = "only-system"` i `uv sync --python 3.12`. Varijablu `UV_PYTHON_PREFERENCE` postavljajte u svakom novom terminalu prije `uv` naredbi. |
| `docker: ... cannot find the file specified` / `daemon is not running` | Docker Desktop nije pokrenut. Pokrenite ga i pričekajte „Engine running”. |
| Valhalla se ne pokreće ili `/status` ne odgovara | Pogledajte zapis: `docker logs prijepotpisa-valhalla-dev`. Prvi put gradi pločice oko 3 minute. Ako je pokrenuta prije koraka 5, zaustavite je (`... down`), napravite korak 5 i pokrenite ponovno. |
| U izvještaju „Mreža hoda trenutačno nije dostupna” | Valhalla ne radi ili još gradi pločice (vidi gore). Ostale kategorije rade i bez nje. |
| „Sunce na krovu” piše da servis sporo odgovara | Vanjski servis PVGIS je spor; osvježite stranicu za nekoliko sekundi. |
| Port 8000 ili 5173 je zauzet | Neki stari proces još radi. Zatvorite stare terminale ili ponovno pokrenite računalo. |
| Preuzimanje podataka puklo | Ponovite naredbu iz koraka 5; nastavlja gdje je stala. |
| `npm ci` javlja grešku | Provjerite `node --version` (mora biti 22 ili noviji). |
| Playwright: „Executable doesn't exist” | U mapi `frontend` pokrenite `npx playwright install chromium`. |
