# Pristupačnost

Cilj je WCAG 2.2 razine AA. Provjera je automatska (axe-core u Playwrightu) i ručna, prema popisu u nastavku.

## Automatske provjere

`make e2e` (dio `make verify`) pokreće `frontend/tests/e2e/smoke.spec.ts`:

- **axe-core** s oznakama `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa` i `wcag22aa`:
  - na svim stranicama: naslovnica, izvještaj, usporedba, izvori i „O alatu”;
  - u svijetloj i tamnoj temi;
  - na desktopu (Desktop Chrome) i mobitelu (Pixel 7);
  - ukupno 20 provjera, a sve moraju biti bez nalaza.
- **Bez vodoravnog pomicanja** na širini od 320 px (naslovnica, izvještaj, usporedba).
- **Glavni tok tipkovnicom:** pretraga, strelica dolje i Enter do izvještaja.

Iz axe provjere izuzet je samo `canvas` karte (MapLibre), jer je karta slika bez vlastitog teksta; njezin sadržaj naveden je u tekstu uz kartu (vidi „Karta”).

`eslint-plugin-jsx-a11y` u strogom načinu provjerava kod pri svakom `make lint`.

## Što je napravljeno

| Zahtjev | Rješenje |
|---|---|
| Jezik | `<html lang="hr">`; sav tekst na hrvatskom |
| Preskakanje navigacije | poveznica „Preskoči na sadržaj” kao prvi element; nakon promjene stranice fokus prelazi na `<main>`, a naslov dokumenta se mijenja |
| Tipkovnica | sve funkcije dostupne tipkovnicom; vidljiv fokus (obrub od 3 px kontrastne boje) |
| Pretraga adrese | kombinirani okvir prema uzorku WAI-ARIA 1.2 (`role="combobox"`, `aria-expanded`, `aria-activedescendant`, `listbox`/`option`); broj prijedloga najavljuje se u području `aria-live` |
| Ciljevi dodira | najmanje 44 × 44 px (gumbi, poveznice u izborniku, odabir profila, prijedlozi) |
| Kontrast | boje teksta i statusa provjerene axe-om u obje teme (≥ 4,5:1) |
| Status nikad samo bojom | svaka oznaka statusa ima riječ („Dobro”, „Upozorenje”, „Loše”, „Nema podataka”, „Informacija”); ocjene imaju i točku u boji |
| Karta | nije jedini nositelj informacije: uz kartu je tekstualni popis onoga što je na 5, 10 i 15 minuta hoda i legenda, a ispod tablica najbližih ustanova; `<figure>` s opisom za čitače zaslona |
| Tablice | `<caption>`, zaglavlja s `scope` |
| Tamna tema | gumb „Tamna tema” (`aria-pressed`); početno prema postavci sustava (`prefers-color-scheme`); izbor se pamti u pregledniku |
| Smanjene animacije | `prefers-reduced-motion` gasi animacije |
| Mobitel | prikaz od 320 px bez vodoravnog pomicanja; tablice se pomiču unutar vlastitog okvira |
| Ispis | stil za ispis skriva navigaciju i gumbe te ispisuje adrese poveznica |
| Pogreške i učitavanje | `role="status"` za učitavanje, `role="alert"` za pogreške, jasne poruke na hrvatskom |
| Vanjske poveznice | najava „(otvara se u novoj kartici)” za čitače zaslona |

## Što još nije provjereno

Tijekom izrade napravljene su samo automatske provjere iz prethodnih odjeljaka i pregled snimki zaslona u obje teme. Nisu provedeni:
- rad s čitačem zaslona (NVDA, VoiceOver);
- uvećanje od 200 % i 400 %;
- testiranje s korisnicima s invaliditetom.

Preporuka prije službenog uvođenja: napraviti te provjere i objaviti izjavu o pristupačnosti prema Zakonu o pristupačnosti mrežnih stranica i programskih rješenja za pokretne uređaje tijela javnog sektora (NN 17/19).
