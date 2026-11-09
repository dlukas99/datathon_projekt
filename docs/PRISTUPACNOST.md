# Pristupačnost

Cilj je WCAG 2.2 razine AA. Provjera je automatska (axe-core u Playwrightu); ono što još nije provjereno navedeno je na kraju.

## Automatske provjere

`make e2e` (dio `make verify`) pokreće `frontend/tests/e2e/smoke.spec.ts`:

- **axe-core** s oznakama `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa` i `wcag22aa`:
  - na svim stranicama: naslovnica, izvještaj, usporedba, „Predloži mjesto”, karta (s otvorenom karticom naselja), izvori i „O alatu”;
  - u svijetloj i tamnoj temi;
  - na desktopu (Desktop Chrome) i mobitelu (Pixel 7);
  - ukupno 28 provjera, a sve moraju biti bez nalaza.
- **Bez vodoravnog pomicanja** na širini od 320 px (naslovnica, izvještaj, usporedba, karta).
- **Glavni tok tipkovnicom:** pretraga, strelica dolje i Enter do izvještaja.
- **Pješački put:** gumb vrste mjesta i redak popisa „Svakodnevni život” crtaju put, Esc ga uklanja, a axe se pokreće i dok su podaci o putu otvoreni.

Iz axe provjere izuzet je samo `canvas` karte (MapLibre), jer je karta slika bez vlastitog teksta; njezin sadržaj naveden je u tekstu uz kartu (vidi „Karta”).

`eslint-plugin-jsx-a11y` u strogom načinu provjerava kod pri svakom `make lint`.

## Što je napravljeno

| Zahtjev | Rješenje |
|---|---|
| Jezik | `<html lang="hr">`; sav tekst na hrvatskom |
| Glavni izbornik | redoslijed Provjeri adresu, Predloži mjesto, Usporedi, Karta, O alatu; trenutačna stranica ima `aria-current="page"` (na izvještaju „Provjeri adresu” ima `aria-current="true"`) i istaknutu pozadinu; ispod 760 px stavke su iza gumba „Izbornik” (`aria-expanded`) koji se zatvara tipkom Esc (fokus se vraća na gumb), klikom izvan, odlaskom fokusa i prelaskom na drugu stranicu |
| Preskakanje navigacije | poveznica „Preskoči na sadržaj” kao prvi element; nakon promjene stranice fokus prelazi na `<main>`, a naslov dokumenta se mijenja |
| Tipkovnica | sve funkcije dostupne tipkovnicom; vidljiv fokus (obrub od 3 px kontrastne boje) |
| Pretraga adrese | kombinirani okvir prema uzorku WAI-ARIA 1.2 (`role="combobox"`, `aria-expanded`, `aria-activedescendant`, `listbox`/`option`); broj prijedloga najavljuje se u području `aria-live` |
| Ciljevi dodira | najmanje 44 × 44 px (gumbi, poveznice u izborniku, odabir profila, prijedlozi) |
| Kontrast | boje teksta i statusa provjerene axe-om u obje teme (≥ 4,5:1) |
| Status nikad samo bojom | svaka oznaka statusa ima riječ („Dobro”, „Upozorenje”, „Loše”, „Nema podataka”, „Informacija”); ocjene imaju i točku u boji |
| Karta | nije jedini nositelj informacije: ispod karte je tekstualni popis onoga što je na 5, 10 i 15 minuta hoda i, za svaku vrstu mjesta, broj unutar 15 minuta i najbliže vrijeme, a ispod toga popis najbližih ustanova; `<figure>` s opisom za čitače zaslona; kontrole karte i oblačić na hrvatskom |
| Karta Hrvatske | Karta nije jedini nositelj informacije. Ispod nje je tablica pet najbolje ocijenjenih naselja za odabrani sloj, s vrijednošću riječima, i pretraga svih 6.759 naselja (i bez dijakritika; prikazuje prvih pet rezultata), pa se do svakog naselja može doći i bez karte. Naziv naselja u tablici je gumb koji otvara istu karticu kao klik na kartu. Kartica dobiva fokus na naslovu, a Esc je zatvara i vraća fokus na redak tablice. Legenda ima nazive razreda, ne samo boje. Na mobitelu je kartica donji list s gumbom „Zatvori karticu” od 44 px, a izbor sloja je red gumba koji se pomiče vodoravno unutar sebe |
| Pješački put | do puta se dolazi tipkovnicom bez karte: gumbi vrsta mjesta (pravi `<button>` s `aria-pressed`; uključeni ima kvačicu i deblji rub, ne samo boju) i retci popisa „Svakodnevni život”. Rezultat („Pješački put do odredišta …: 31 minuta, 2,4 kilometra.”) najavljuje područje `role="status"`. Esc uklanja put. Nakon „Ukloni put” fokus ostaje na gumbu vrste, a nakon klika u popisu prelazi na podatke o putu. Vrsta bez podataka je onemogućen gumb s tekstom „nema podataka u blizini” |
| „Pogledaj oglase” | pravi gumb s `aria-expanded` i `aria-controls`; ploča se zatvara tipkom Esc (fokus se vraća na gumb), klikom izvan ploče (s praznog mjesta fokus se vraća na gumb) i kad fokus tipkovnicom izađe iz nje, da ne pokrije element s fokusom (WCAG 2.4.11); dok je padajući popis otvoren, klik izvan zatvara samo popis |
| Tablice | `<caption>`, zaglavlja s `scope` |
| Tamna tema | uvijek prema postavci uređaja (`prefers-color-scheme`), i kad se ona promijeni dok je stranica otvorena; gumb „Tamna tema” (`aria-pressed`) mijenja temu samo za tu karticu, a promjena postavke uređaja ga poništava; tema se postavlja prije učitavanja aplikacije, bez bljeska |
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
