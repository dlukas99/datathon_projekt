# Scenarij videa (do 3 minute)

**Priča:** obitelj razmišlja gdje živjeti u Vukovarsko-srijemskoj županiji. Prvo provjerava jednu adresu, zatim traži mjesta koja im odgovaraju i uspoređuje dvije lokacije. Kao primjer služe adrese javnih ustanova: gradska uprava Vinkovci (Bana Jelačića 1) i Općina Nijemci (Trg kralja Tomislava 6). Okolišni pregled je uvijek prvi.

**Priprema:**
- Pokrenite aplikaciju (lokalno ili javni demo) u pregledniku na 1280 × 800, u svijetloj temi, s uvećanjem od 110 %.
- Pripremite kartice:
  1. naslovnica;
  2. izvještaj za „Bana Jelačića 1, Vinkovci” s profilom „Obitelj s djecom”;
  3. „Predloži mjesto” na prvom koraku (prijedlozi se u snimci dobiju s Obitelj s djecom, Vukovarsko-srijemskom županijom, vrtićem, školom i bez poplava);
  4. usporedba Vinkovci i Nijemci;
  5. karta (`/karta?sloj=air`);
  6. `/api/docs`.
- Snimke zaslona za montažu nalaze se u `docs/images/`. Ne prikazujte privatne adrese.

| Vrijeme | Slika | Govor (prijedlog) |
|---|---|---|
| 0:00–0:15 | naslovnica: pitanje „Kako je živjeti ovdje?”, polje za adresu i naselja Hrvatske koja se pune od istoka prema zapadu (pustite da animacija završi) | „Gdje živjeti najveća je odluka u životu. Gledamo cijenu i kvadraturu, a poplave, zrak ili to možemo li bez auta otkrijemo tek kad uselimo. Ti podaci postoje, ali su rasuti po desetak institucija.” |
| 0:15–0:25 | upis „Bana Jelačića 1, Vinkovci” u polje za adresu, zatim iskaznica mjesta na vrhu izvještaja; „Gledam kao” → „Obitelj s djecom” | „Dobro mjesto je za svakoga tko bira gdje živjeti: obitelji, umirovljenike i studente. Upišem adresu i dobijem iskaznicu mjesta. Odaberem tko sam.” |
| 0:25–0:55 | izvještaj: sažetak na vrhu, kartice Poplave i Zrak (jedna rečenica, ocjena riječju), točkice zelenila, ravnalo prometnice; otvorite „Detalji i izvor” kod zraka | „Prvo okoliš. Poplave iz karata JRC-a, uz poveznicu na Hrvatske vode; kad je adresa u poplavnom području, rizik vidim kao vjerojatnost u 30 godina kredita. Zrak dobiva jednu ocjenu, a brojke i granice WHO-a i EU-a su u detaljima, zelenilo prema pravilu 3-30-300, a promet prema udaljenosti od ceste. Uz svaku brojku su izvor i datum.” |
| 0:55–1:10 | Ocjena mjesta u zaglavlju, zatim ploča s klizačima | „Ocjena mjesta sažima sve kategorije prema mom profilu. Težine su vidljive i mogu ih mijenjati, a piše i što je najbolje, a što najslabije.” |
| 1:10–1:25 | Život bez auta: karta doleti do adrese, krugovi hoda od 5, 10 i 15 minuta šire se redom, kvačice | „Hod se računa po stvarnim ulicama: što je na 5, 10 i 15 minuta i koliko od sedam svakodnevnih potreba imam bez auta.” |
| 1:25–1:50 | „Pronađi mjesto za mene”: profil „Student”, tri koraka s trakom napretka (tko traži → gdje → što je važno), prvi prijedlog s uvjetima i razlozima, „Otvori izvještaj” | „A ako još ne znam gdje? Odgovorim na tri pitanja, a aplikacija rangira 2.347 naselja. Svaki profil ima obavezne uvjete: student dobiva mjesta sa studijima, a uz svaki prijedlog piše zašto.” |
| 1:50–2:05 | „Pogledaj oglase”, zatim usporedba Vinkovci i Nijemci | „Za odabrano mjesto otvaram pretragu oglasa; mi samo slažemo poveznicu. Dvije lokacije usporedim jednu uz drugu.” |
| 2:05–2:15 | Karta: sloj „Kvaliteta zraka”, klik na Vinkovce, kartica naselja | „Na karti vidim cijelu Hrvatsku, naselje po naselje: zrak, poplave, usluge ili prijevoz. Klik daje kratak pregled i put do punog izvještaja.” |
| 2:15–2:28 | asistent: „Gdje je bliže do vrtića?” | „Asistent odgovara samo iz izračuna i ne daje savjete o kupnji.” |
| 2:28–2:40 | „O alatu”, dio „Izvori podataka”, metodologija (provjera zraka) | „Koristimo 34 otvorena skupa podataka: Portal otvorenih podataka, DGU, DZS, ministarstva, HZZO, gradove, prijevoznike, JRC, EEA, ESA, Copernicus i OpenStreetMap. Kartu zraka provjerili smo uz službene postaje.” |
| 2:40–2:55 | dijagram arhitekture iz `docs/ARHITEKTURA.md`, `/api/docs`, zatim naslovnica | „Ispod su FastAPI, Valhalla i Docker Compose, uz otvoreni REST API i kod pod licencom EUPL. Dalje: buka i internet čim postanu otvoreni, vozni redovi ostalih gradova i ugradnja u gradske portale.” |

**Napomene za snimanje:**
- Ukupno oko 300 riječi (oko 2:55 uz mirno čitanje); govorite mirno, bez zastrašivanja.
- Tijekom videa natpis: „Informativni alat, nije službena procjena.”
- Ako demo URL još nije javan, snimite lokalno (upute u `docs/RAZVOJ.md`).
