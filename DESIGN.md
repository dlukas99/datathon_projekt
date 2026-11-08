---
name: Prije potpisa
description: Okolišni pregled i pregled svakodnevnog života za bilo koju adresu u Hrvatskoj, kao sustav planinarskih putokaza.
colors:
  limestone: "#f0f3ef"
  surface: "#ffffff"
  stone-mist: "#e3eae5"
  forest-ink: "#142420"
  moss-muted: "#4a5c55"
  hairline: "#d0dad4"
  control-border: "#6c7f77"
  lake-jade: "#0b6b63"
  lake-jade-deep: "#08564f"
  lake-jade-soft: "#d3ece7"
  on-jade: "#ffffff"
  sign-brown: "#5b3a1e"
  sign-ink: "#ffffff"
  sign-muted: "#e9d9c6"
  sign-edge: "#3f2713"
  focus-blue: "#1a56c4"
  good: "#1d6b3a"
  good-bg: "#e1f0e4"
  warning: "#7a5300"
  warning-bg: "#fbefd0"
  bad: "#a3231c"
  bad-bg: "#fbe4e0"
  info: "#2c4f72"
  info-bg: "#e3ecf4"
  nodata: "#545a57"
  nodata-bg: "#e7e9e6"
  dark-limestone: "#0e1714"
  dark-surface: "#15211d"
  dark-stone-mist: "#1c2a25"
  dark-forest-ink: "#e4ece7"
  dark-moss-muted: "#a3b3ac"
  dark-hairline: "#2a3a34"
  dark-control-border: "#6b8279"
  dark-lake-jade: "#6ccabc"
  dark-lake-jade-deep: "#8fdacf"
  dark-lake-jade-soft: "#143029"
  dark-on-jade: "#062420"
  dark-plank-go: "#1d6a61"
  dark-plank-go-hover: "#23796f"
  dark-sign-brown: "#6b4526"
  dark-sign-muted: "#eadbc8"
  dark-sign-edge: "#4a2e17"
  dark-focus-blue: "#8ab4ff"
  dark-good: "#8fdca9"
  dark-good-bg: "#16301f"
  dark-warning: "#f2cc72"
  dark-warning-bg: "#352a10"
  dark-bad: "#ffaaa1"
  dark-bad-bg: "#3a1b18"
  dark-info: "#a9c9ec"
  dark-info-bg: "#1a2836"
  dark-nodata: "#c3c8c5"
  dark-nodata-bg: "#222b27"
typography:
  display:
    fontFamily: "'Bricolage Grotesque Variable', 'Figtree Variable', sans-serif"
    fontSize: "clamp(2.6rem, 6.4vw, 5.4rem)"
    fontWeight: 780
    lineHeight: 0.98
    letterSpacing: "-0.04em"
    fontVariation: "'opsz' 96"
  headline:
    fontFamily: "'Bricolage Grotesque Variable', 'Figtree Variable', sans-serif"
    fontSize: "clamp(2rem, 5vw, 3.1rem)"
    fontWeight: 750
    lineHeight: 1.15
    letterSpacing: "-0.03em"
  title:
    fontFamily: "'Bricolage Grotesque Variable', 'Figtree Variable', sans-serif"
    fontSize: "clamp(1.35rem, 3vw, 1.7rem)"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  title-sm:
    fontFamily: "'Bricolage Grotesque Variable', 'Figtree Variable', sans-serif"
    fontSize: "1.12rem"
    fontWeight: 650
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  key-number:
    fontFamily: "'Bricolage Grotesque Variable', 'Figtree Variable', sans-serif"
    fontSize: "1.9rem"
    fontWeight: 750
    lineHeight: 1.15
    letterSpacing: "-0.03em"
  body:
    fontFamily: "'Figtree Variable', system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
    fontFeature: "'tnum'"
  label:
    fontFamily: "'Figtree Variable', system-ui, sans-serif"
    fontSize: "0.92rem"
    fontWeight: 600
    lineHeight: 1.6
  status:
    fontFamily: "'Figtree Variable', system-ui, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 650
rounded:
  sm: "6px"
spacing:
  xs: "0.5rem"
  sm: "0.75rem"
  md: "1rem"
  lg: "1.25rem"
  xl: "2rem"
  section: "3.5rem"
  container: "1120px"
components:
  button-primary:
    backgroundColor: "{colors.lake-jade}"
    textColor: "{colors.on-jade}"
    rounded: "{rounded.sm}"
    padding: "0 1.1rem"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.lake-jade-deep}"
    textColor: "{colors.on-jade}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.forest-ink}"
    rounded: "{rounded.sm}"
    padding: "0 1.1rem"
    height: "44px"
  button-secondary-hover:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.lake-jade}"
  input-search:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.forest-ink}"
    rounded: "{rounded.sm}"
    padding: "0.75rem 1.1rem"
    height: "56px"
  chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.forest-ink}"
    rounded: "{rounded.sm}"
    padding: "0 0.9rem"
    height: "44px"
  chip-selected:
    backgroundColor: "{colors.lake-jade-soft}"
    textColor: "{colors.forest-ink}"
  plank-place:
    backgroundColor: "{colors.sign-brown}"
    textColor: "{colors.sign-ink}"
    rounded: "{rounded.sm}"
    padding: "0.9rem 1rem 1rem 1.1rem"
  plank-go:
    backgroundColor: "{colors.lake-jade}"
    textColor: "{colors.on-jade}"
    rounded: "{rounded.sm}"
    padding: "0.75rem 0.75rem 0.75rem 1.1rem"
    height: "64px"
  place-board-band:
    backgroundColor: "{colors.sign-brown}"
    textColor: "{colors.sign-ink}"
    padding: "1.4rem 1.5rem 1.3rem"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.forest-ink}"
    rounded: "{rounded.sm}"
    padding: "1.25rem 1.3rem"
  status-good:
    backgroundColor: "{colors.good-bg}"
    textColor: "{colors.good}"
    rounded: "{rounded.sm}"
    padding: "0.2rem 0.65rem"
  status-warning:
    backgroundColor: "{colors.warning-bg}"
    textColor: "{colors.warning}"
    rounded: "{rounded.sm}"
    padding: "0.2rem 0.65rem"
  status-bad:
    backgroundColor: "{colors.bad-bg}"
    textColor: "{colors.bad}"
    rounded: "{rounded.sm}"
    padding: "0.2rem 0.65rem"
  status-no-data:
    backgroundColor: "{colors.nodata-bg}"
    textColor: "{colors.nodata}"
    rounded: "{rounded.sm}"
    padding: "0.2rem 0.65rem"
  trail-dot:
    backgroundColor: "{colors.limestone}"
    textColor: "{colors.moss-muted}"
    size: "42px"
---

# Design System: Prije potpisa

## Overview

**Creative North Star: "Putokaz"**

Aplikacija je sustav planinarskih staza za Hrvatsku. Korisnik stoji na ishodištu staze, putokaz mu nudi dva smjera (provjeri adresu, pronađi mjesto za mene), a svaki rezultat je ploča mjesta kakva stoji na ulazu u park prirode. Svijet je posuđen iz označavanja staza i nacionalnih parkova: vapnenačka podloga, šumska tinta, jezerski žad za stazu i radnje, smeđa turistička signalizacija za identitet mjesta. Ništa ne glumi službeni znak; to je jezik orijentacije, ne jezik tijela vlasti.

Gustoća je mirna i čitljiva: jedna jasna rečenica ispred brojki, ravnala i redovi izravno na vapnencu umjesto lebdećih kartica, crte i postaje umjesto ikona u redu. Boja ima točno jedan posao. Svaki status nosi i oblik ikone i riječ, nikad samo boju. Pokret je jedna gesta po trenutku (ploča se popuni kad stigne izvještaj, karta Hrvatske izađe od istoka prema zapadu, korak vodiča klizne u smjeru hoda) i potpuno nestaje uz smanjene animacije.

Odbijeno: podijeljeni hero s karticom za pretragu i redom jednakih kartica s ikonama; crveno-zelena presuda na karti; sve što sugerira službeni status.

**Key Characteristics:**
- Jedna boja, jedan posao: žad za radnje, poveznice i stazu; smeđa samo za identitet mjesta; statusi zasebno.
- Putokaz s daskama, ploča mjesta, staza s postajama i ravnani redovi kao potpisni oblici.
- Ravnala i redovi na podlozi umjesto bijelih kartica; sjena samo na pločama koje nose identitet mjesta i na plutajućim slojevima.
- Bricolage Grotesque za naslove i brojke, Figtree za tekst, oba s vlastitog poslužitelja (OFL).
- Svijetla i tamna tema jednako dovršene; WCAG 2.2 AA, ciljevi dodira 44 px, 320 px bez vodoravnog pomicanja.

## Colors

Hladna, prigušena paleta prirodnih materijala (vapnenac, šuma, jezero, drvo) u kojoj svaka boja ima samo jednu ulogu.

### Primary
- **Jezerski žad** (`lake-jade`; tamna tema `dark-lake-jade`): sve radnje, poveznice, crta staze, oznake postaja, odabrani čipovi, kursor u poljima i oznaka trenutne stranice u navigaciji. Hover tamni na `lake-jade-deep` (u tamnoj temi svijetli na `dark-lake-jade-deep`). `lake-jade-soft` je podloga odabranog izbora. U tamnoj temi daska „Pronađi mjesto za mene” koristi zaseban, tamniji `dark-plank-go` kako bi bijeli tekst zadržao kontrast.
- **Sekvencijalna žad-ljestvica karte** (pet koraka, `frontend/src/lib/mapLayers.ts`): svijetlo `#dcefe9 → #a3d5c9 → #5fb0a0 → #1f8273 → #0a4f47`, tamno `#1d3c36 → #2b675d → #479a8b → #82cdbf → #cdf1e9`; „nema podataka” je siva (`#c4cbc7` / `#323b37`). Jedna nijansa, od slabijeg prema jačem, bez crveno-zelene presude. Ista ljestvica boji mozaik naselja na naslovnici i kartu Hrvatske.

### Secondary
- **Smeđa turistička signalizacija** (`sign-brown`, s `sign-ink` bijelim tekstom, `sign-muted` za sporedni tekst i `sign-edge` za rub i stup): isključivo identitet mjesta. Daska za adresu na putokazu, traka ploče mjesta s nazivom, naslovna traka kartice naselja na karti, prvo mjesto u rangu prijedloga i postaja „ovdje ste” u vodiču. Rub je uvijek unutarnja donja crta u `sign-edge`.

### Tertiary
- **Statusne boje** (`good`, `warning`, `bad`, `info`, `nodata`, svaka s pripadnom `-bg` podlogom): samo za statuse kategorija, potreba i ključnih činjenica. Tekst statusa u boji ide na njegovoj podlozi; uz njega uvijek stoji ikona vlastitog oblika (krug s kvačicom, trokut, osmerokut, „i”, upitnik) i riječ.
- **Fokusno plava** (`focus-blue` / `dark-focus-blue`): samo obris fokusa tipkovnicom. Nije žad, kako se fokus nikad ne bi pomiješao s odabirom.

### Neutral
- **Vapnenac** (`limestone`; tamno `dark-limestone`): podloga stranice, zaglavlja i ljepljivog vodiča.
- **Bijela ploča** (`surface`): kartice, polja, čipovi, padajući popisi.
- **Kamena izmaglica** (`stone-mist`): tihe podloge (napomena o ograničenju, mjehurić asistenta, prazna traka ljestvice, status „informacija” u karticama).
- **Šumska tinta** (`forest-ink`): sav tekst i naslovi, i ravnalo od 2 px koje otvara odjeljak izvještaja.
- **Mahovinasto siva** (`moss-muted`): sporedni tekst, oznake, metapodaci, nepređeni dio staze.
- **Tanka linija** (`hairline`): rubovi ploča, ravnala redova, razdjelnici.
- **Rub kontrole** (`control-border`): rub svakog interaktivnog elementa (polja, sekundarni gumbi, čipovi, izbori), dovoljno taman za 3:1 prema podlozi.

### Named Rules
**The One Job Rule.** Svaka boja ima jedan posao. Žad znači „ovuda se ide ili ovo se može pritisnuti”, smeđa znači „ovo je mjesto”, statusne boje znače stanje. Žad nikad ne označava status, smeđa nikad radnju.

**The Colour Plus Shape Plus Word Rule.** Status je uvijek boja, oblik ikone i riječ zajedno. Gdje je riječ vizualno izostavljena (ključne činjenice ploče), stoji u skrivenom tekstu za čitač zaslona.

**The No Verdict Map Rule.** Karte boje jednom nijansom žada od slabijeg prema jačem; crveno-zelena ljestvica se ne koristi.

## Typography

**Display Font:** Bricolage Grotesque Variable (s rezervom Figtree Variable, sans-serif)
**Body Font:** Figtree Variable (s rezervom system-ui, sans-serif)

**Character:** Bricolage daje naslovima toplinu otisnute table i optičku veličinu za veliki naslov; Figtree je otvoren, prijateljski i čitljiv u malim veličinama. Oba fonta su pod licencom OFL i poslužuju se s vlastitog poslužitelja preko `@fontsource-variable`.

### Hierarchy
- **Display** (780, `clamp(2.6rem, 6.4vw, 5.4rem)`, 0,98, optička veličina 96): samo pitanje na ishodištu naslovnice, najviše 9ch u retku.
- **Headline** (750, `clamp(2rem, 5vw, 3.1rem)`, 1,15): naslov stranice. Na ploči mjesta naslov je manji (`clamp(1.7rem, 4.4vw, 2.7rem)`) i bijel na smeđoj traci.
- **Title** (700, `clamp(1.35rem, 3vw, 1.7rem)`; naslovi odjeljaka izvještaja do `2rem`): naslovi odjeljaka i pitanja vodiča.
- **Title small** (650, 1,12–1,2 rem): naslovi kartica, postaja i dasaka.
- **Key number** (Bricolage 750, 1,9 rem): glavna brojka kategorije; skor u znački (800, 2 rem) i skor za život (800, 2,6 rem).
- **Body** (400, 1 rem, 1,6): sav tekst; uvodi i sažetak ploče najviše 62–65ch.
- **Label** (600, 0,92 rem): oznake polja, postaja, poveznice vodiča, oznake ključnih činjenica.
- **Status** (650, 0,8 rem): tekst statusne oznake.

### Named Rules
**The Tabular Figures Rule.** Tekst koristi tablične brojke (`tabular-nums`) kako bi se brojke u redovima i tablicama poravnale; naslovi koriste proporcionalne brojke s poravnatom visinom.

**The Display Earns Its Size Rule.** Display veličina postoji samo za jedno pitanje na naslovnici. Ostali naslovi ostaju na Headline ljestvici.

## Layout

Sadržaj je u spremniku širine najviše 1120 px s bočnim razmakom 1,25 rem. Odjeljci izvještaja razmaknuti su 3,5 rem; unutar ploča razmaci su 0,5, 0,75, 1 i 1,25 rem. Zaglavlje je ljepljivo, visoko 64 px; ispod njega na izvještaju lijepi se vodič „Ovdje ste”, pa sidra odjeljaka imaju `scroll-margin-top` 130 px.

Naslovnica je ishodište: na desktopu tekst i putokaz lijevo, mozaik naselja Hrvatske desno, puštene do desnog ruba prozora. Na 900 px i manje sve ide u jedan stupac: pitanje, putokaz, mozaik. Tri postaje „Kako radi” stoje u retku spojene isprekidanom crtom žada, a na 640 px i manje postaju okomita staza.

Rešetke kartica su `auto-fill` sa stupcima od najmanje 300 px (dvostupčane od 360 px). Karta Hrvatske ima kartu lijevo i stupac od 340 px desno (odabrano naselje iznad legende); na 760 px i manje to postaje jedan stupac, a kartica naselja postaje donja ploča preko karte. Prijelomne točke: 440, 480, 560, 640, 760 i 900 px; na 480 px i manje gumb pretrage ide ispod polja. Na 760 px i manje navigacija se sklapa u izbornik.

## Elevation & Depth

Sustav je ravan po zadanom: dubinu nose podloge (vapnenac ispod, bijela ploča iznad) i tanka linija, a ne sjene. Sjena postoji na dvije vrste površina: na pločama koje nose identitet mjesta (ploča mjesta izvještaja, kartica naselja na karti) i na slojevima koji plutaju iznad sadržaja (prijedlozi pretrage, panel oglasa, otvoreni mobilni izbornik, skočni prozor karte, donja ploča).

### Shadow Vocabulary
- **Ploča** (`0 1px 2px rgb(20 36 32 / 6%), 0 6px 18px -8px rgb(20 36 32 / 14%)`; tamno `0 1px 2px rgb(0 0 0 / 30%), 0 8px 20px -10px rgb(0 0 0 / 50%)`): ploča mjesta, kartica naselja, padajući slojevi.
- **Skočni prozor karte** (`0 4px 18px rgb(0 0 0 / 22%)`): oblačić na karti.
- **Donja ploča** (`0 -8px 24px rgb(0 0 0 / 18%)`): kartica naselja kao donja ploča na mobitelu.
- **Rub table** (`inset 0 -3px 0 var(--sign-edge)`, na ploči mjesta 4 px): donji rub smeđih dasaka i traka, debljina drva, ne lebdenje.

### Named Rules
**The Boards Not Cards Rule.** Ispod ploče mjesta izvještaj nema bijelih kartica: svaki odjeljak otvara ravnalo od 2 px u tinti, a kategorije su redovi na vapnencu odvojeni tankom linijom. Gdje ploča ostaje (stranice izvan izvještaja), ravna je: bijela podloga, jedna tanka linija, bez sjene. Odabrano dobiva žad, ne sjenu.

## Shapes

Mali, odlučni kutovi od 6 px (`rounded.sm`) za sve: gumbe, polja, čipove, daske, oznake, ploče i karte. Jedan kut za cijeli svijet, kao rub table. Čipovi namjerno nisu pilule, jer se tekst na mobitelu može prelomiti u dva retka. Krug je rezerviran za postaje staze, rang prijedloga i točke legende. Daske putokaza zaobljene su samo s lijeve strane, a desno završavaju šiljkom strelice (`clip-path` trokut širine 26 px). Staza je crta debljine 3 px: puna gdje je pređena, isprekidana ispred.

## Components

### Buttons
Čvrsti i jasni, nikad ukrasni.
- **Shape:** blago zaobljeni (6 px), visina najmanje 44 px (u vodiču 48 px).
- **Primary:** žad podloga i rub, bijeli tekst težine 700, razmak `0 1.1rem`.
- **Hover / Focus:** podloga i rub prelaze na `lake-jade-deep` u 160 ms; fokus je obris od 3 px u `focus-blue` s odmakom 2 px.
- **Secondary / Ghost:** bijela podloga, `control-border` rub, tekst u tinti; na hover rub i tekst prelaze u žad.
- **Link button:** tekst u žadu, podvučen, težine 600.

### Chips
- **Style:** bijela podloga, rub `control-border`, kut 6 px, visina 44 px, težina 500.
- **State:** odabrani dobiva rub u žadu, podlogu `lake-jade-soft` i težinu 650; čip mjesta na karti uz to ima rub od 2 px i kvačicu, ne samo boju.

### Cards / Containers
- **Corner Style:** 6 px.
- **Background:** bijela ploča na vapnencu, ali samo izvan izvještaja (izvori, usporedba, karta); u izvještaju odjeljci gube ljusku kartice (vidi The Boards Not Cards Rule).
- **Shadow Strategy:** ravno; sjena samo na ploči mjesta i kartici naselja.
- **Border:** 1 px `hairline`; odjeljak izvještaja: gornje ravnalo od 2 px u tinti (u žadu kad je važan za profil).
- **Internal Padding:** `1.25rem 1.3rem` na ploči; u redu kategorije `1.25rem 0 1.1rem`.
- **Red kategorije:** na desktopu dva stupca (naziv, status i ključna brojka lijevo do 15 rem; objašnjenje i detalji desno, razmak 2 rem); na 640 px i manje jedan stupac.

### Inputs / Fields
- **Style:** bijela podloga, rub `control-border` od 1 px, kut 6 px, visina 48 px; polje pretrage adrese 56 px, 1,1 rem.
- **Focus:** obris od 3 px u `focus-blue`; hover potamni rub do boje teksta.
- **Prijedlozi:** padajuća ploča sa sjenom „Ploča”, opcije od najmanje 48 px; aktivna opcija ima `stone-mist` podlogu i obris od 2 px u fokusno plavoj.

### Navigation
Brend je znak putokaza (stup, smeđa i žad daska) i naziv u Bricolageu 750. Poveznice su visine 44 px, težine 500, na hover žad. Trenutna stranica je deblja (700) i ima kratak komad staze ispod: crtu od 3 px u žadu. Na 760 px i manje poveznice se sklapaju pod gumb izbornika, a oznaka postaje okomita crta lijevo.

### Putokaz (signpost)
Potpisni element naslovnice. Stup od 9 px u `sign-edge` lijevo, na njemu daske sa šiljkom strelice. Smeđa daska nosi polje adrese (oznaka u Bricolageu 700, 1,2 rem, bijela); daska „Pronađi mjesto za mene” je u žadu jer vodi na stazu, visine najmanje 64 px, i na hover se pomakne 4 px udesno u 220 ms.

### Ploča mjesta (place board)
Vrh svakog izvještaja. Smeđa traka s nazivom mjesta i skorom u žad znački obrubljenoj sa 3 px `sign-edge`, ispod nje sažetak od dvije do tri rečenice (najviše 62ch) i šest ključnih činjenica. Kad izvještaj stigne, sažetak i činjenice se popune pokretom (`translateY(10px) scale(0.97)`, 440–520 ms, činjenice s odmakom od 55 ms); prozirnost se ne animira, pa je tekst čitljiv u svakom trenutku.

### Statusne oznake i ključne činjenice
Statusna oznaka: podloga statusa, tekst u boji statusa (650, 0,8 rem), ikona od 15 px. Ključna činjenica ploče: oznaka (sporedni tekst), vrijednost (700) i ikona statusa od 16 px u boji statusa, na podlozi statusa; „nema podataka” uvijek se prikazuje.

### Staza s postajama (trail stepper)
Vodič „Predloži mjesto za život” ima četiri postaje od 42 px s obrubom od 3 px. Pređena postaja je puna žad s kvačicom i može se pritisnuti za povratak; trenutna je smeđa („ovdje ste”) s prstenom od 4 px; buduća je vapnenac sa sivim obrubom. Crta između postaja je puna žad iza i isprekidana siva ispred. Korak ulazi klizanjem od 28 px u smjeru hoda (natrag s lijeva), 360 ms. Ista gramatika vrijedi za tri postaje „Kako radi” na naslovnici.

### Ravnani redovi rezultata
Prijedlozi naselja su redovi na jednom popisu odvojeni tankim linijama, ne niz jednakih kartica. Rang je krug od 40 px s obrubom u žadu; prvi u rangu je smeđi. Isti obrazac vrijedi za svakodnevne potrebe (red s nazivom i vremenom hoda desno) i za tablice.

### Vodič „Ovdje ste”
Ljepljiva traka odjeljaka izvještaja ispod zaglavlja (visina poveznice 48 px). Svaki odjeljak je postaja: prsten od 12 px s obrubom od 3 px u žadu, a odjeljci su spojeni isprekidanom crtom od 3 px u `control-border`. Trenutni odjeljak ima punu smeđu postaju s prstenom („ovdje ste”) i tekst težine 700. Na uskom zaslonu se pomiče vodoravno s izblijedjelim desnim rubom.

### Mozaik naselja
Svih 6.759 naselja na platnu, obojenih žad-ljestvicom po Skoru za život, s tekstnim opisom i poveznicom na kartu. Pojavljuje se od istoka prema zapadu u 1,6 s (eksponencijalno usporavanje); uz smanjene animacije odmah je cijel.

## Do's and Don'ts

### Do:
- **Do** koristiti žad (`lake-jade`) za svaku radnju, poveznicu i crtu staze, i samo za to.
- **Do** koristiti smeđu tablu (`sign-brown` s bijelim tekstom i rubom `sign-edge`) za naziv i identitet mjesta: daska adrese, traka ploče mjesta, naslov kartice naselja, „ovdje ste”, prvo mjesto u rangu.
- **Do** prikazati svaki status bojom, oblikom ikone i riječju; „nema podataka” uvijek prikazati.
- **Do** držati svaki interaktivni cilj na najmanje 44 px i fokus kao obris od 3 px u `focus-blue`.
- **Do** koristiti pokret samo kao gestu (ploča se popuni, korak klizne, mozaik izađe), s `cubic-bezier(0.16, 1, 0.3, 1)`; uz `prefers-reduced-motion` ukinuti pomake i animacije, a prijelaze boje i ruba zadržati jer su povratna informacija.
- **Do** provjeriti svaki novi par boja za kontrast od 4,5:1 u svijetloj i tamnoj temi, i rasporede na 320 px bez vodoravnog pomicanja.
- **Do** slagati rezultate i kategorije kao ravnane redove na jednom popisu, a odjeljke izvještaja otvarati ravnalom od 2 px u tinti.

### Don't:
- **Don't** koristiti žad za status ili smeđu za radnju (osim smeđe daske adrese koja nosi polje, ne gumb).
- **Don't** bojiti karte crveno-zelenom ljestvicom; jedna nijansa žada, siva za „nema podataka”.
- **Don't** graditi podijeljeni hero s karticom za pretragu i redom jednakih kartica s ikonama.
- **Don't** vraćati bijele kartice u izvještaj ispod ploče mjesta ni dodavati sjenu pločama; sjena pripada pločama mjesta i plutajućim slojevima.
- **Don't** praviti čipove kao pilule; kut je 6 px.
- **Don't** animirati prozirnost teksta koji se mora pročitati.
- **Don't** koristiti maskotu, emojije, grb ili oznake koje sugeriraju službeni status.
