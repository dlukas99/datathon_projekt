# Metodologija

Ovaj dokument opisuje kako se računa svaka kategorija pregleda, koji se pragovi koriste i odakle dolaze. Izvori podataka s licencama i poveznicama navedeni su u [IZVORI_PODATAKA.md](IZVORI_PODATAKA.md), a odluke donesene tijekom izrade u [ODLUKE.md](ODLUKE.md).

## Načela

1. **Apsolutno značenje ispred relativnog ranga.** Pregled kaže, na primjer, „lokacija je u modeliranom poplavnom području za povratno razdoblje od 100 godina”, a ne „rizik iznad prosjeka”.
2. **Svaka kategorija ima status** prema pragu s izvorom: dobro, upozorenje, loše ili nema podataka. Kategorije za koje ne postoji općeprihvaćen prag (sunce, požari, život bez auta, javni prijevoz, svakodnevni život) imaju status „Informacija” i prikazuju samo podatak, bez ocjene. „Nema podataka” se uvijek prikazuje; kategorija se nikad tiho ne izostavlja.
3. **Skupna ocjena samo s vidljivim težinama.** Kategorije se prikazuju zasebno; „Skor za život” (odjeljak niže) je ponderirani prosjek s vidljivim i podesivim težinama. Profil mijenja redoslijed, naglasak i težine, nikad vrijednosti ni statuse.
4. **Svaka vrijednost ima izvor, datum preuzimanja i vrstu.** Vrste su:
   - `measured` (izmjereno): vrijednost iz mjerenja, voznog reda ili službenog registra;
   - `modelled` (modelirano): izračun modelom (karte poplava i zraka, satelitski pokrov tla, vrijeme hoda po mreži);
   - `estimate` (procjena): zamjenski podatak, npr. udaljenost od prometnice umjesto razine buke ili zračna udaljenost kad usmjerivač ne radi.
5. **Sažetak se slaže iz predložaka.** Dvije do četiri kratke rečenice nad statusima kategorija (`app/report.py`): ako je lokacija u poplavnom području ili blizu njega, to je prva rečenica („Pažnja: …”); zatim ono što je stvarno dobro (mirno, čist ili dobar zrak, puno zelenila, bez opasnosti od poplava), svakodnevne potrebe pješice i najviše jedna napomena „Na što obratiti pažnju: …” (velika cesta blizu, osrednji ili loš zrak, malo drveća). Kad je jedino dobro to što nema poplava, to ide u kratku rečenicu na kraju, da poplava ne bude uvijek prva. Jezični model ne piše tekst.

## Lokacija

- Adresa se pretvara u koordinate vlastitim geokoderom nad 1.683.411 adresa iz skupa „Adrese INSPIRE” Državne geodetske uprave. Upit i adrese normaliziraju se: mala slova, bez dijakritika, `đ` i `dj` kao `d`. Riječi „ulica” i „ul.” zanemaruju se jer ih službeni nazivi često nemaju („Bana Jelačića”). Kod upita od tri ili više riječi jedna riječ smije nedostajati (npr. ime u „Bana Josipa Jelačića”), ali najdulja mora odgovarati.
- **Kućni broj** ima broj, slovo i podbroj (`addressNumber`, `addressNumberExtension`, `addressNumber2ndExtension`): 23, 23A, 25/2, 12A/1. Do 6. 11. 2026. obrada je zadržavala samo broj, pa 322.198 adresa (19 %) nije bilo moguće pronaći po točnom broju. Upit prepoznaje „23a”, „23 A”, „12/B”, „12-b”, „25/2” i „bb”.
- **Mjesto** se piše iza zareza ili bez njega („Ivana Rendića 6 Rijeka”; tada riječi iza broja moraju biti naziv naselja, grada ili općine). Prihvaća se naselje, grad ili općina („Banjol 10, Rab”) i poštanski broj; „Hrvatska” se zanemaruje. Prednost imaju ulice u upisanom naselju.
- **Drugi oblik naziva ulice** („Brune Bušića” za „Bušićevu”, „Ivana Gundulića” za „Gundulićevu ulicu”) prepoznaje se po osnovi prezimena, a prijedlog kaže pod kojim je nazivom ulica upisana.
- **Kad nečega nema u registru**, prijedlog je ono najbliže što postoji, uz napomenu: isti broj bez slova, sredina ulice, a kod sela bez naziva ulica ili kad ulica nije pronađena središte naselja. Izvještaj tada piše da je prikazana sredina ulice ili središte naselja.
- **Provjera:** `scripts/geocode_check.py` pretražuje 24 adrese osnovnih škola iz registra MZOM-a (veliki grad, manji grad, selo, otok; s brojem i bez njega). Prije 6. 11. 2026. točno je bilo 12, sada 22. Za preostale dvije DGU nema upisanog kućnog broja („Jelsa 161”, „1. ulica 25/2, Blato”), pa se prikazuju središte naselja i broj 25, uz napomenu.
- Naselje, grad ili općina i županija određuju se točkom u poligonu nad DGU „Upravnim jedinicama INSPIRE”. Hijerarhija (naselje → JLS → županija) izvedena je prostorno, preko točke unutar poligona naselja, jer GDAL ne izlaže poveznice `upperLevelUnit`.
- Udaljenosti se računaju u projekciji HTRS96/TM (EPSG:3765), u metrima.

## Poplave

- **Podaci:** JRC karte opasnosti od riječnih poplava za Europu, verzija 3.1.1, dubina vode u metrima, rezolucija 3 lučne sekunde (oko 90 m), za povratna razdoblja od 10, 100 i 500 godina.
- **Izračun:** vrijednost piksela na točki i najveća dubina među pikselima čije je središte unutar 100 m od točke.
- **Status:**

| Status | Uvjet |
|---|---|
| Loše | točka je u području od 10 godina (velika vjerojatnost) ili 100 godina (srednja vjerojatnost) |
| Upozorenje | točka je u području od 500 godina (mala vjerojatnost) ili je bilo koje poplavno područje unutar 100 m |
| Dobro | ni točka ni okolica od 100 m nisu ni u jednom modeliranom području |

- **Izvor praga:** podjela na poplave velike, srednje (povratno razdoblje 100 godina) i male vjerojatnosti preuzeta je iz opisa karata opasnosti od poplava Hrvatskih voda (Zakon o vodama, karte 2019.), objavljenog na Portalu otvorenih podataka. Isti scenariji propisani su člankom 6. stavkom 3. Direktive 2007/60/EZ o procjeni i upravljanju rizicima od poplava („floods with a medium probability (likely return period ≥ 100 years)”).
- **Razumljiv prikaz rizika:** ako je adresa (ili okolica od 100 m) u modeliranom području, povratno razdoblje T pretvara se u vjerojatnost barem jedne takve poplave u 30 godina, uobičajenom trajanju stambenog kredita: P = 1 − (1 − 1/T)³⁰. To je oko 96 % za T = 10, 26 % za T = 100 i 6 % za T = 500. Pretpostavka je da su godine međusobno neovisne, uz godišnju vjerojatnost 1/T, što je definicija povratnog razdoblja. Službena oznaka povratnog razdoblja uvijek se prikazuje uz vjerojatnost.
- **Ograničenja:** karte JRC-a modeliraju samo riječne poplave većih vodotoka. Ne obuhvaćaju bujice, poplave mora, oborinske vode ni lokalne nasipe. Lokacija izvan modeliranog područja ne znači da rizika nema. Uz svaki izvještaj nalazi se poveznica na službeni preglednik Hrvatskih voda.

## Kvaliteta zraka

- **Podaci:** EEA interpolirane karte godišnjih prosjeka PM2,5 i NO2 za 2024. (validirane, objavljene 29. 5. 2026.), mreža od 1 km.
- **Izračun:** vrijednost ćelije u kojoj je točka.
- **Stupnjevana ljestvica** (od 4. 11. 2026.): umjesto ocjene „prolazi ili ne prolazi” prema smjernici WHO-a, koju premašuje gotovo cijela Hrvatska, vrijednost se smješta na ljestvicu s četiri razine. Granice razina su službene vrijednosti:

| Razina onečišćenja (status) | Ocjena zraka na kartici | PM2,5, godišnji prosjek | NO2, godišnji prosjek | Granica |
|---|---|---|---|---|
| vrlo niska (dobro) | Vrlo dobar | ≤ 5 µg/m³ | ≤ 10 µg/m³ | smjernica WHO-a 2021 |
| niska (dobro) | Dobar | ≤ 10 µg/m³ | ≤ 20 µg/m³ | granična vrijednost EU-a od 2030. |
| umjerena (informacija, neutralno) | Umjeren | ≤ 25 µg/m³ | ≤ 40 µg/m³ | granična vrijednost EU-a koja vrijedi danas |
| visoka (loše) | Loš | > 25 µg/m³ | > 40 µg/m³ | iznad današnje granične vrijednosti EU-a |

Crveno je samo razina iznad granice koja danas pravno vrijedi. Status kategorije je viša od dviju razina (PM2,5, NO2).

- **Prikaz** (od 6. 11. 2026.): kartica pokazuje ocjenu zraka bojom i riječju i jednu rečenicu o tome što ona znači kroz godinu. Ocjena govori o zraku, a ne o onečišćenju, pa „niska razina onečišćenja” više ne izgleda kao „niska kvaliteta”. Brojke, odnos prema smjernici WHO-a i granicama EU-a te ljestvice s oznakama granica nalaze se u „Detalji i izvor”.
- **Zašto ne Europski indeks kvalitete zraka:** indeks EEA-e od revizije 2024. računa se iz satnih koncentracija i opisuje kratkotrajni rizik, pa se ne smije primijeniti na godišnje prosjeke (ETC HE Report 2024/17). Za godišnje prosjeke vrijede smjernica WHO-a i granične vrijednosti EU-a.

- **Izvori pragova:**
  - WHO global air quality guidelines (2021), tablica 0.1: godišnja smjernica PM2,5 5 µg/m³ i NO2 10 µg/m³. https://iris.who.int/handle/10665/345329
  - Direktiva (EU) 2024/2881 o kvaliteti zraka i čišćem zraku za Europu, Prilog I., odjeljak 1., tablica 1: granične vrijednosti koje se moraju postići do 1. 1. 2030. su godišnje PM2,5 10 µg/m³ i NO2 20 µg/m³. CELEX 32024L2881.
  - Ista direktiva, Prilog I.: granične vrijednosti koje se moraju postići do 11. 12. 2026. su godišnje PM2,5 25 µg/m³ i NO2 40 µg/m³; iste vrijednosti propisuje i dosadašnja Direktiva 2008/50/EZ. To je „granica koja vrijedi danas”.
- Status kategorije je lošiji od dvaju statusa (PM2,5 i NO2).
- **Ograničenja:** karta je modelirana procjena godišnjeg prosjeka na mreži od 1 km, a ne mjerenje na adresi. Prema EEA-i ne smije se koristiti za službenu provjeru usklađenosti. Uz izvještaj je poveznica na mjerenja u stvarnom vremenu (iszz.azo.hr).

### Provjera uz službene mjerne postaje (studeni 2026.)

Vrijednosti iz aplikacije (EEA karta za 2024.) usporedili smo s godišnjim prosjekom najbliže službene postaje u 2024. godini.

- **Mjerenja:** verificirani podaci (E1a) iz EEA Air Quality Download Service za Hrvatsku. Prijavljuje ih ministarstvo nadležno za zaštitu okoliša (`aqd.azo.hr`).
- **Godišnji prosjek** je srednja vrijednost valjanih satnih ili dnevnih mjerenja (`ingest/stations.py`).
- **Postaje:** u 2024. ima 16 postaja s NO2 i 18 s PM2,5, s pokrivenošću od 77 do 100 % godine.
- **Lokacije:** središte grada i tri osnovne škole unutar 4 km, odabrane što dalje jedna od druge (javne ustanove).
- **Ponavljanje:** `uv run python -m analysis.validation`.

| Grad | Lokacija | Tvar | Aplikacija (EEA karta) | Najbliža postaja (vrsta) | Udaljenost | Postaja, prosjek 2024. | Razlika | Zaključak |
|---|---|---|---|---|---|---|---|---|
| Zagreb | središte (Zagreb) | PM2,5 | 18,0 | ZAGREB PPI PM2,5 - Ksaverska cesta (pozadinska) | 2,4 km | 13,9 | 4,1 | karta viša od mjerenja |
| Zagreb | središte (Zagreb) | NO2 | 24,2 | ZAGREB-1 (prometna) | 1,4 km | 38,0 | -13,8 | karta niža: postaja je uz promet, karta prikazuje pozadinu |
| Zagreb | OSNOVNA ŠKOLA KUSTOŠIJA | PM2,5 | 17,9 | ZAGREB PPI PM2,5 - Ksaverska cesta (pozadinska) | 4,7 km | 13,9 | 4,0 | karta viša od mjerenja |
| Zagreb | OSNOVNA ŠKOLA KUSTOŠIJA | NO2 | 21,3 | ZAGREB-1 (prometna) | 4,0 km | 38,0 | -16,7 | karta niža: postaja je uz promet, karta prikazuje pozadinu |
| Zagreb | OSNOVNA ŠKOLA ZAPRUĐE | PM2,5 | 19,1 | ZAGREB PPI PM2,5 - Ksaverska cesta (pozadinska) | 6,1 km | 13,9 | 5,2 | karta viša od mjerenja |
| Zagreb | OSNOVNA ŠKOLA ZAPRUĐE | NO2 | 24,3 | ZAGREB-3 (pozadinska) | 2,0 km | 28,4 | -4,1 | karta niža od mjerenja |
| Zagreb | OSNOVNA ŠKOLA ANTUNA GUSTAVA MATOŠA | PM2,5 | 18,1 | ZAGREB PPI PM2,5 - Ksaverska cesta (pozadinska) | 4,1 km | 13,9 | 4,2 | karta viša od mjerenja |
| Zagreb | OSNOVNA ŠKOLA ANTUNA GUSTAVA MATOŠA | NO2 | 23,3 | ZAGREB-1 (prometna) | 4,5 km | 38,0 | -14,6 | karta niža: postaja je uz promet, karta prikazuje pozadinu |
| Osijek | središte (Osijek) | PM2,5 | 16,3 | OSIJEK-2 PPI PM2,5 (pozadinska) | 2,8 km | 15,6 | 0,7 | dobro slaganje |
| Osijek | središte (Osijek) | NO2 | 18,9 | OSIJEK-1 (prometna) | 0,5 km | 23,5 | -4,7 | karta niža: postaja je uz promet, karta prikazuje pozadinu |
| Osijek | Osnovna škola Retfala | PM2,5 | 16,5 | OSIJEK-2 PPI PM2,5 (pozadinska) | 6,6 km | 15,6 | 0,9 | dobro slaganje |
| Osijek | Osnovna škola Retfala | NO2 | 18,2 | OSIJEK-1 (prometna) | 4,1 km | 23,5 | -5,3 | karta niža: postaja je uz promet, karta prikazuje pozadinu |
| Osijek | Osnovna škola Ljudevita Gaja | PM2,5 | 16,1 | OSIJEK-2 PPI PM2,5 (pozadinska) | 0,1 km | 15,6 | 0,5 | dobro slaganje |
| Osijek | Osnovna škola Ljudevita Gaja | NO2 | 17,9 | OSIJEK-1 (prometna) | 2,4 km | 23,5 | -5,6 | karta niža: postaja je uz promet, karta prikazuje pozadinu |
| Osijek | Osnovna škola Grigor Vitez | PM2,5 | 16,2 | OSIJEK-2 PPI PM2,5 (pozadinska) | 1,8 km | 15,6 | 0,5 | dobro slaganje |
| Osijek | Osnovna škola Grigor Vitez | NO2 | 18,3 | OSIJEK-1 (prometna) | 1,7 km | 23,5 | -5,2 | karta niža: postaja je uz promet, karta prikazuje pozadinu |
| Požega | središte (Požega) | PM2,5 | 18,9 | SLAVONSKI BROD-1 (pozadinska) | 31,5 km | 25,2 | -6,3 | postaja je daleko, usporedba je samo okvirna |
| Požega | središte (Požega) | NO2 | 13,4 | SLAVONSKI BROD-1 (pozadinska) | 31,5 km | 14,1 | -0,7 | postaja je daleko, usporedba je samo okvirna |
| Požega | Osnovna škola Dobriša Cesarić | PM2,5 | 18,8 | SLAVONSKI BROD-1 (pozadinska) | 31,9 km | 25,2 | -6,4 | postaja je daleko, usporedba je samo okvirna |
| Požega | Osnovna škola Dobriša Cesarić | NO2 | 15,4 | SLAVONSKI BROD-1 (pozadinska) | 31,9 km | 14,1 | 1,3 | postaja je daleko, usporedba je samo okvirna |
| Požega | Osnovna škola Julija Kempfa | PM2,5 | 18,8 | SLAVONSKI BROD-1 (pozadinska) | 31,6 km | 25,2 | -6,4 | postaja je daleko, usporedba je samo okvirna |
| Požega | Osnovna škola Julija Kempfa | NO2 | 15,4 | SLAVONSKI BROD-1 (pozadinska) | 31,6 km | 14,1 | 1,3 | postaja je daleko, usporedba je samo okvirna |
| Požega | Katolička Osnovna škola U Požegi | PM2,5 | 18,9 | SLAVONSKI BROD-1 (pozadinska) | 31,4 km | 25,2 | -6,3 | postaja je daleko, usporedba je samo okvirna |
| Požega | Katolička Osnovna škola U Požegi | NO2 | 13,4 | SLAVONSKI BROD-1 (pozadinska) | 31,4 km | 14,1 | -0,7 | postaja je daleko, usporedba je samo okvirna |

**Zaključci:**
- **PM2,5:**
  - U Osijeku se karta i pozadinska postaja slažu unutar 1 µg/m³.
  - U Zagrebu je karta oko 4–5 µg/m³ viša od jedine verificirane postaje za PM2,5 (Ksaverska cesta, pozadinska, na sjevernom rubu grada).
  - Razina na ljestvici (umjerena) se ni u jednom slučaju ne mijenja.
- **NO2:**
  - Karta je 5–17 µg/m³ niža od prometnih postaja (Zagreb-1, Osijek-1). To je očekivano: karta EEA-e procjenjuje pozadinsku razinu na mreži od 1 km, a prometne postaje mjere uz samu ulicu.
  - Od pozadinske postaje Zagreb-3 karta je niža za 4 µg/m³.
  - Zato kartica zraka napominje da uz prometne ulice NO2 može biti znatno viši, a kategorija „Udaljenost od prometnica” to pokazuje zasebno.
- **Požega** nema službenu postaju. Najbliža je Slavonski Brod-1 na 31 km, pa je usporedba samo okvirna.
- **Ograničenje provjere:** EEA karte izrađene su i uz pomoć istih postaja, pa ovo nije potpuno neovisna provjera. Pokazuje ipak kako se karta ponaša uz pozadinske, a kako uz prometne postaje.

## Zelenilo i hlad (ranije „Toplina i zelenilo”)

- **Podaci:** ESA WorldCover 2021 v200 (10 m) i parkovi iz OpenStreetMapa (`leisure=park`).
- **Izračun:** udio piksela unutar 300 m od točke, bez vodenih površina (razred 80):
  - drveće: razred 10;
  - zelene površine: razredi 10, 20, 30 i 90 (drveće, grmlje, travnjaci, močvare);
  - izgrađeno: razred 50.
- Najbliži park je najbliža točka ruba poligona parka (ili sama točka ako je unutar parka), s vremenom hoda po mreži i zračnom udaljenošću.
- **Pravilo 3-30-300:** Konijnendijk, C. C. (2023.). Evidence-based guidelines for greener, healthier, more resilient neighbourhoods: Introducing the 3–30–300 rule. *Journal of Forestry Research* 34(3), 821–830. https://doi.org/10.1007/s11676-022-01523-z. Iz pravila koristimo:
  - „no less than a 30% tree canopy in every neighbourhood”;
  - „no more than 300 m to the nearest public green space from every residence”.
- **Status:** dobro ako su ispunjena oba uvjeta (drveće ≥ 30 % u krugu od 300 m i park na zračnoj udaljenosti ≤ 300 m), upozorenje ako je ispunjen jedan, loše ako nije nijedan.
- **Temperatura se ne mjeri.** Drveće i park su pokazatelj hlada i ublažavanja vrućina; zato se kategorija od 6. 11. 2026. zove „Zelenilo i hlad”, a ne „Toplina i zelenilo”.
- **Provjera (6. 11. 2026.):** za pet središta naselja (Split, Osijek, Požega, Nijemci, Hvar) udio drveća iz WorldCovera (11–33 %) uspoređen je s ortofotom DGU-a iz 2023. i s kartom gustoće krošanja Copernicus HRL 2018 (EEA). Brojke su ispravno izračunate i odgovaraju ortofotu; HRL daje još manje vrijednosti (1–11 %). Detalji su u [NALAZI_TESTIRANJA.md](NALAZI_TESTIRANJA.md).
- **Ograničenja:** WorldCover mjeri pokrov tla iz satelita i ne razlikuje javne od privatnih vrtova. U rezoluciji 10 m ne razlikuje pojedinačna stabla u dvorištima i uz ulice kad je oko njih izgrađeno, pa je udio drveća u gusto izgrađenim središtima vjerojatno nešto veći. OSM parkovi su izvan gradova nepotpuni. Dio pravila „3 stabla vidljiva s prozora” ne može se izračunati iz otvorenih podataka.

## Udaljenost od prometnica (procjena; ranije „Promet u blizini” i „Buka”)

- **Podaci:** ceste `highway=motorway|trunk|primary` i `secondary` bez županijske oznake (glavne gradske ulice) te pruge (`railway=rail`, bez sporednih kolosijeka) iz OpenStreetMapa. Županijske ceste (`secondary` s četveroznamenkastom oznakom Ž) i ostale ulice se od 8. 11. 2026. ne broje: kroz gotovo svako selo prolazi neka županijska cesta, pa je 79 % naselja bilo „blizu prometnice” i podatak nije razlikovao mirna mjesta od prometnih.
- **Vrsta ceste** prema hrvatskim pravilima označavanja u OSM-u (wiki „Croatia/Ceste”):

| OSM | U izvještaju | Primjer |
|---|---|---|
| `motorway` | autocesta i oznaka | autocesta A1 |
| `trunk` | brza cesta i oznaka | brza cesta D1 |
| `primary` s oznakom D | državna cesta i oznaka | državna cesta D8 |
| `primary` bez oznake D | glavna cesta | |
| `secondary` s četveroznamenkastom oznakom | ne broji se (županijska cesta) | županijska cesta Ž2001 |
| `secondary` bez oznake | glavna gradska cesta (bivše županijske ceste u gradovima) | |

  U podacima 19.042 dionice `primary` imaju oznaku D, a 16.463 dionice `secondary` županijsku oznaku; 3.910 dionica `secondary` nema oznaku, uglavnom u gradovima.
- **Izračun:** zračna udaljenost od lokacije (adrese ili središta naselja) do najbliže točke osi takve ceste i do najbliže pruge, do 2 km. Buku ne mjerimo; udaljenost je zamjenski pokazatelj, vrste „procjena”. Za središta naselja udaljenost je često 0 m jer OSM čvor naselja leži na samoj cesti; za adresu uz cestu nekoliko je metara (točka adrese je na zgradi).
- **Pojasevi:**

| Udaljenost od ceste | Oznaka | Status |
|---|---|---|
| do 300 m | Blizu prometnice | upozorenje |
| 300–500 m | Rub zone prometa | informacija |
| više od 500 m | Podalje od prometnica | dobro |

- **Izvor pojaseva:** Health Effects Institute (2010.), *Traffic-Related Air Pollution: A Critical Review of the Literature on Emissions, Exposure, and Health Effects*, Special Report 17. Zona najjačeg utjecaja prometa je približno 300 do 500 m od autoceste ili velike prometnice, a dalje koncentracije padaju na pozadinsku razinu.
- **Pruga:** navodi se opisno ako je do 500 m. Pregled HEI-ja odnosi se na cestovni promet, pa pruga ne mijenja status.
- **Kontekst:** smjernice WHO-a za buku okoliša (2018.) preporučuju cestovni promet ispod 53 dB Lden i 45 dB Lnight (https://iris.who.int/handle/10665/279952). Strateške karte buke EEA-e nemaju otvorenu licencu, pa ih samo povezujemo.
- **Smjer podskora:** veći broj znači manje prometa. 100 je dalje od 500 m od takve ceste, 60 od 300 do 500 m, a 25 do 300 m. Naziv kategorije od 6. 11. 2026. je „Udaljenost od prometnica”, da „100/100” ne zvuči kao „mnogo prometa”.
- **Naselje (karta i „Predloži mjesto”):** jedna točka ne opisuje naselje (središte Splita je u pješačkoj staroj jezgri, a središte gotovo svakog sela na cesti kroz selo), pa se za svako naselje računa pojas za **svaku adresu DGU-a** u njemu (1.683.411 adresa, `ingest/settlement_traffic.py`). Podskor naselja je prosjek podskorova adresa (100, 60 ili 25), a uz prijedlog piše koliki udio adresa je do 300 m i koliki dalje od 500 m od velike prometnice. Naselja bez adresa (17) zadržavaju vrijednost u središtu. Izvještaj za adresu i dalje računa za tu adresu.
- **Ograničenje:** prometnija županijska cesta kroz središte grada (npr. Ž4290 u Vinkovcima) ne broji se kao prometnica; buku i broj vozila ne mjerimo.
- Zašto i `secondary`: vidi [ODLUKE.md](ODLUKE.md).

## Požari raslinja

- **Podaci:** EFFIS (Copernicus European Forest Fire Information System), opožarene površine kartirane iz satelitskih snimaka MODIS, sloj `ms:modis.ba.poly` preuzet preko javnog WFS-a za Hrvatsku (1.030 površina od 2016.). Skupno preuzimanje traži račun, a WFS ne.
- **Izračun:** opožarene površine čiji poligon dodiruje krug od 2 km oko točke: broj, godine, najbliža (udaljenost do ruba) i najveća (ha).
- **Status:** „Informacija”, jer za broj prošlih požara ne postoji prag s izvorom. Prošli požari pokazuju izloženost, a ne predviđaju buduće.
- **Najmanja površina:** EFFIS-ova procjena štete bilježila je do 2017. požare od otprilike 30 ha naviše; od 2018. snimke Sentinel-2 hvataju i neke manje (EFFIS, „Rapid damage assessment”, https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/rapid-damage-assessment, provjereno 8. 11. 2026.). U našem izvatku 410 od 1.030 površina ima manje od 30 ha, pa prag nije tvrd. Kartica zato piše „veći požar” i „satelit bilježi uglavnom požare od otprilike 30 hektara naviše, pa manji požari ovdje nisu vidljivi”, a ne „nijedan požar”.
- **Kartica:** jedna rečenica (nije zabilježen veći požar od 2016. ili broj, godine i najveća izgorjela površina) i rečenica o veličini; broj, najbliža i najveća površina pod „Detalji i izvor”.
- **Ograničenja:** podaci počinju 2016.

## Sunce na krovu

- **Podaci:** JRC PVGIS 5.3, `PVcalc`, snaga 1 kWp, gubici sustava 14 % (zadana vrijednost PVGIS-a), optimalni nagib i azimut, baza zračenja PVGIS-SARAH3 (2005.–2023.).
- **Vrijednost:** `E_y`, prosječna godišnja proizvodnja u kWh za 1 kWp.
- **Status:** „Informacija”.
- **Ograničenja:** ne uzima u obzir sjenu susjednih zgrada i drveća ni stvarni nagib i orijentaciju krova. Rezultat se predmemorira po koordinatama zaokruženima na 0,01°.

## Mreža hoda

- **Usmjerivač:** Valhalla 3.9.1 nad OSM izvatkom za Hrvatsku, pješački profil.
- **Brzina hoda:** 4,5 km/h (1,25 m/s). To je obrazložena pretpostavka, nešto sporija od zadane vrijednosti Valhalle (5,1 km/h, `src/sif/pedestriancost.cc`), kako bi vremena bila realna i za starije osobe i roditelje s djecom (vidi [ODLUKE.md](ODLUKE.md)).
- **Izokrone:** 5, 10 i 15 minuta.
- **Vremena hoda:** jedan poziv matrice `sources_to_targets` po izvještaju. Kandidati su sve ustanove unutar 1.300 m zračne udaljenosti, a izvan toga tri najbliže unutar 15 km. 15 minuta pri 4,5 km/h je 1.125 m mrežom, što nikad nije kraće od zračne udaljenosti, pa krug od 1.300 m sadrži sve ustanove unutar 15 minuta.
- **Mjesta na karti** (`nearby_places` u izvještaju): sva mjesta do 15 minuta hoda i tri najbliža svake vrste, s vremenom hoda iz iste matrice. Iz njih su brojevi „unutar 15 min” i najbliže vrijeme u legendi karte.
- **Pješački put do mjesta** (`GET /api/route`) računa se samo kad ga korisnik zatraži, istim usmjerivačem, profilom i brzinom kao izokrone i matrica. Duljina je duljina puta po mreži, a minute su vrijeme usmjerivača, ne duljina podijeljena brzinom (vidi tablicu ispod). Uz put se prikazuje vrijeme mjesta iz izvještaja, isti broj kao u popisu „Svakodnevni život”. Točke udaljene više od 20 km zračno se ne usmjeravaju. Ako put nije moguće izračunati, prikazuje se poruka i zračna udaljenost; ravna crta se ne crta.
- Ako usmjerivač ne odgovara, prikazuje se zračna udaljenost s oznakom „procjena”, a kategorije koje ovise o hodu prikazuju „Nema podataka”.

Valhalla na pojedinim mjestima mreže dodaje vrijeme hoda, pa je duljina puta podijeljena brzinom kraća od vremena u izvještaju. Mjereno na 435 mjesta oko šest demo adresa (6. 11. 2026.):

| Način | Odstupanje od vremena u izvještaju | Drukčija cijela minuta |
|---|---|---|
| vrijeme rute iz Valhalle | najviše 0,13 min (8 s) | 15 mjesta, sve uz granicu zaokruživanja |
| duljina / 4,5 km/h | medijan 0,1 min (oko demo adrese u Splitu 0,5 min), najviše 1,5 min | 97 mjesta |

## Svakodnevne potrebe

| Potreba | Izvor (prednost) | Dopuna |
|---|---|---|
| Vrtić | Registar dječjih vrtića (MZOM), geokodiran; u Zagrebu Geoportal Grada Zagreba | OSM `amenity=kindergarten` dalje od 100 m od službenih |
| Osnovna škola | Popis osnovnih škola (MZOM), geokodiran; u Zagrebu Geoportal Grada Zagreba | OSM `amenity=school` s nazivom osnovne ili područne škole, dalje od 100 m od službenih |
| Obiteljski liječnik | HZZO, ugovoreni timovi opće/obiteljske medicine, geokodirani | nema (OSM `amenity=doctors` miješa specijaliste) |
| Pedijatar | HZZO, ugovoreni timovi zdravstvene zaštite predškolske djece | nema |
| Ljekarna | HZZO, ugovorene ljekarne, geokodirane | OSM `amenity=pharmacy` dalje od 100 m od službenih |
| Trgovina namirnicama | OSM `shop=supermarket|convenience|greengrocer` | — |
| Igralište | OSM `leisure=playground` | — |

- **Geokodiranje registara:** adresa iz registra uspoređuje se s DGU adresama istog poštanskog broja ili naselja i istog kućnog broja. Ulica se uspoređuje po riječima, a najdulja riječ (obično prezime) mora odgovarati. Ako kućni broj nije pronađen, koristi se sredina ulice. Uspješnost geokodiranja: [KVALITETA_PODATAKA.md](KVALITETA_PODATAKA.md).
- **Za svaku potrebu prikazuje se:** najbliža ustanova s minutama hoda i broj ustanova unutar 15 minuta hoda.

## Život bez auta

- Sedam svakodnevnih potreba unutar 15 minuta hoda: trgovina namirnicama, ljekarna, obiteljski liječnik, vrtić, osnovna škola, park i stajalište s barem jednim polaskom na sat radnim danom.
- Prikazuje se „X od 7” i popis onoga što nedostaje.
- Ako u blizini postoje stajališta, ali za to područje nema voznog reda u otvorenom obliku, potreba za stajalištem prikazuje se kao „nije provjereno”, a ne kao „nedostaje”.
- Granica od 15 minuta prati koncept „grada od 15 minuta” (Moreno, C., Allam, Z., Chabaud, D., Gall, C., Pratlong, F. (2021.). Introducing the “15-Minute City”: Sustainability, Resilience and Place Identity in Future Post-Pandemic Cities. *Smart Cities* 4(1), 93–111. https://doi.org/10.3390/smartcities4010006).

## Javni prijevoz

- Stajališta unutar 10 minuta hoda.
- **Polasci na sat:** broj polazaka sa stajališta od 6 do 20 sati jednog radnog dana, podijeljen s 14.
  - Polazak je svaki `stop_times` zapis putovanja aktivnog tog dana, osim dolaska na zadnje stajalište putovanja.
  - Radni dan je prva srijeda od dana obrade za koju postoji promet (`calendar.txt` i `calendar_dates.txt`).
- Prikazuje se najveći broj polazaka na sat od svih stajališta unutar 10 minuta hoda.
- **Stajališta s voznim redom i bez njega zajedno** (npr. željeznička postaja HŽPP-a među gradskim autobusnim i tramvajskim stajalištima u Osijeku, Bjelovaru ili Šibeniku): najveći broj polazaka odnosi se samo na stajališta s voznim redom i to piše u kartici. Za stajališta bez voznog reda broj polazaka nije poznat, pa potreba „stajalište s barem jednim polaskom na sat” tada nije „nedostaje”, nego „nije provjereno”, osim ako neko stajalište s voznim redom ima barem jedan polazak na sat. Polasci se broje samo od 6 do 20 sati jednog radnog dana, pa noćna stanka u prometu ne utječe na rezultat.
- **Linije na stajalištima bez voznog reda:** gdje broj polazaka nije poznat (stajališta bez otvorenog voznog reda, a nijedno stajalište s voznim redom nema 6 polazaka na sat), kartice „Javni prijevoz” i „Život bez auta” navode koje linije ondje staju prema relacijama linija u OpenStreetMapu (npr. „tramvaj 1 i 2, autobus 3, 4, 5, 7 i 8 (GPP Osijek)”). Linija se pridružuje stajalištu ako je njezino stajalište u OSM-u do 30 m daleko. Izostavljene su međugradske linije: relacija čija su stajališta više od 30 km udaljena ili koja ima manje od 5 ucrtanih stajališta. To je podatak o linijama, ne o učestalosti: ne ulazi u broj ispunjenih potreba ni u Skor za život.
- **Izvori voznih redova:** ZET (GTFS), HŽPP (GTFS), Gradski parking Šibenik (GTFS, gradske i prigradske linije) i Autotrolej (vozni red radnim danom, JSON). Drugdje se prikazuju stajališta iz OpenStreetMapa s oznakom „bez voznog reda”. OSM stajališta unutar 60 m od stajališta s voznim redom smatraju se istim stajalištem.

## Skor za život

Od 4. 11. 2026. izvještaj ima i skupni „Skor za život” (0–100). To je svjesno odstupanje od načela „bez skupne ocjene”, dopušteno jer su težine vidljive i podesive (vidi [ODLUKE.md](ODLUKE.md)). Vrijednosti i statusi kategorija se ne mijenjaju.

- **Podskor kategorije (0–100), `backend/analysis/score.py`:**

| Kategorija | Pravilo | Osnova |
|---|---|---|
| Poplave | dobro 100, upozorenje 50, loše 0 | scenariji Hrvatskih voda i Direktive 2007/60/EZ |
| Kvaliteta zraka | vrlo niska 100, niska 80, umjerena 50, visoka 10 (viša od razina PM2,5 i NO2) | WHO 2021 i granice EU-a |
| Zelenilo i hlad | do 60 bodova za udio drveća (30 % = puni bodovi) i 40 bodova za park do 300 m (20 do 600 m) | pravilo 3-30-300 |
| Udaljenost od prometnica | podalje 100, rub zone 60, blizu 25 (veći broj znači manje prometa) | HEI 2010 (300/500 m) |
| Požari raslinja | 0 požara 100, 1 požar 60, 2 i više 30 | naša normalizacija |
| Sunce na krovu | linearno od 1.000 (0) do 1.500 kWh/kWp (100) | naša normalizacija; Hrvatska je u tom rasponu |
| Život bez auta | broj potreba od 7 × 100 / 7 | — |
| Javni prijevoz | najviše polazaka na sat / 6 × 100 (polazak svakih 10 min = 100); bez voznog reda nema podskora, a ni kad uz stajališta s manje od 6 polazaka na sat postoje i stajališta bez voznog reda | naša normalizacija |
| Svakodnevni život | udio vrsta ustanova unutar 15 minuta hoda | — |

- **Skor:** ponderirani prosjek podskorova; kategorije bez podskora (nema podataka ili nepoznat vozni red) se preskaču. Težine 0–3 po profilu nalaze se u `config/profiles.json` (jedan izvor za backend i frontend) i mogu se mijenjati klizačima; prilagođene težine spremaju se u URL.
- **Objašnjenje:** „najviše podiže” i „najviše spušta” su kategorije s najvećim pozitivnim, odnosno negativnim doprinosom: težina × (podskor − skor).
- **Ograničenje:** skor je pomoć pri usporedbi, a ne ocjena kvalitete života. Normalizacije označene kao „naše” nisu službeni pragovi.

## Predloži mjesto za život (ranije „Pronađi mjesto”)

- **Obuhvat:** profili se računaju za svih 6.759 naselja (za kartu), a tražilica rangira naselja s najmanje 200 stanovnika (2.347 naselja, 92 % stanovništva Hrvatske prema Popisu 2021.). Manja naselja rijetko imaju ikakve usluge, a s čistim zrakom i bez poplava inače bi zauzela vrh popisa.
- **Priprema** (`ingest/settlement_profiles.py`, dio `make data`): za središte svakog naselja (OSM čvor `place`, vidi „Lokacija”) računaju se iste kategorije kao u izvještaju (poplave, zrak, zelenilo, promet, požari, hod, javni prijevoz, svakodnevne potrebe) i njihovi podskorovi. Sunce na krovu se izostavlja jer je PVGIS servis uživo.
- **Rang** (`app/finder.py`, `app/finder_rules.py`):
  1. filtri: županija, veličina (do 2.000, 2.000–20.000, više od 20.000 stanovnika), što mora biti do 15 minuta hoda od središta, najviša dopuštena razina zraka, izvan modeliranih poplavnih područja;
  2. **obavezni uvjeti profila** (vidi „Pravila profila u Predloži mjesto”): naselje koje ih ne ispunjava ne ulazi u prijedloge;
  3. rang za profil: ponderirani prosjek podskorova Skora za život s težinama profila i **važnih kriterija profila** s težinama iz `config/finder_rules.json`;
  4. pri jednakom rangu prednost ima veće naselje.

  Izračun je deterministički: isti upit uvijek daje isti poredak. Jezični model ne sudjeluje u rangu.
- **Razlozi:** uz svaki prijedlog „Ispunjava uvjete profila” (s vrijednostima, npr. „Ljekarna: 4 minute hoda”, „Studiji u mjestu: 156 studijskih programa, npr. Sveučilište Josipa Jurja Strossmayera u Osijeku”), dva do tri obična razloga za profil i najviše jedna napomena „Na što obratiti pažnju”; brojke iz izračuna (poplave, zrak, prometnice, hod, prijevoz, drveće; za umirovljenika najbliža bolnica, za studenta studentski dom i menza iz OSM-a) su pod „Detalji”.

- **Opis uz prijedlog** (`app/finder_rules.py`, `highlights` i `caution`): uvjeti profila koje mjesto ispunjava (s vrijednostima), zatim dva do tri kratka razloga redoslijedom važnim za profil (npr. za umirovljenika bolnica blizu, zelenilo, mir; za obitelj pedijatar i igralište; za studenta javni prijevoz i sve pješice) i najviše jedna napomena „Na što obratiti pažnju: …”. Razlozi nemaju bodove ni postotke; brojke su pod „Detalji”. „Dobar zrak” nije razlog, jer ga ima većina Hrvatske; razlog je samo „čist zrak” (vrlo dobar), a „dobar, ali ne izvrstan” je napomena.

### Pravila profila u Predloži mjesto

Profil više nije samo skup težina: ima obavezne uvjete kakve bi postavio čovjek („Osijek je studentski grad jer ima studije”) i važne kriterije koji podižu rang. Sva pravila, pragovi i obrazloženja su u jednoj datoteci, `config/finder_rules.json`; čarobnjak iz nje prikazuje što profil zahtijeva.

| Profil | Obavezno | Važno (uz težine Skora za život profila) |
|---|---|---|
| Općenito | trgovina namirnicama do 15 min hoda | ljekarna (1) i liječnik (1) pješice; uravnoteženo, sve kategorije Skora za život |
| Obitelj s djecom | vrtić i osnovna škola do 15 min hoda | pedijatar (2), igralište (1) i park (1) pješice; zrak, poplave i zelenilo s pojačanim težinama |
| Umirovljenik | trgovina, ljekarna i obiteljski liječnik do 15 min hoda | opća ili klinička bolnica u blizini (2), park pješice (1); zelenilo i hlad, javni prijevoz s pojačanim težinama |
| Student | studiji u naselju, ili veće studijsko središte (barem 20 studijskih programa) do 15 km zračne linije uz stajalište javnog prijevoza do 10 min hoda | izbor studija (8); javni prijevoz i život bez auta s pojačanim težinama |
| Rad od kuće | trgovina namirnicama do 15 min hoda | park (1), ljekarna (1) i liječnik (1) pješice; mir (udaljenost od prometnica) i zelenilo s pojačanim težinama |

- **Pješice (15 min):** isti prag i ista mreža hoda kao „Život bez auta” (vidi „Mreža hoda”). Važni kriteriji pješice boduju se po minutama do najbližeg mjesta: 100 do 5 minuta, linearno do 0 na 30 minuta (naša prozirna normalizacija, kao kod ostalih podskorova).
- **Izbor studija:** broj preddiplomskih, diplomskih, integriranih, kratkih i specijalističkih diplomskih stručnih programa koji se izvode u naselju (MZOM, „Studijski programi visokih učilišta”; poslijediplomski se ne broje). Podskor je 60 + 40 · ln(1 + n) / ln(1 + 200), najviše 100: svaki studij daje čvrstu osnovu, a veći izbor podiže rang sve do 200 programa (Osijek, Rijeka i Split su blizu, Zagreb iznad). Mjesta s jednim programom (60–65) tako su ispod sveučilišnih gradova (90–100).
- **Predgrađe za studenta:** ulazi samo ako je do 15 km zračne linije od središta naselja s barem 20 programa i ima stajalište javnog prijevoza do 10 minuta hoda. Podskor mu je podskor tog središta × 0,75 × (1 − 0,5 · km / 15), pa je predgrađe uvijek ispod svojeg grada i pada s udaljenošću. Vrijeme vožnje se ne računa: otvoreni vozni redovi postoje samo za ZET, Autotrolej i HŽPP, pa za ostala mjesta pišemo udaljenost i postoji li stajalište, a ne izmišljamo minute.
- **Bolnica za umirovljenika:** najbliža opća ili klinička bolnica iz OSM-a (`amenity=hospital`, bez specijalnih, psihijatrijskih, lječilišta i bolnica preko granice), zračna linija od središta naselja: 100 do 10 km, linearno do 0 na 40 km (prozirna normalizacija).
- **Studentski dom i menza** (OSM, prema nazivu) prikazuju se kao činjenica uz prijedlog, ali se ne boduju: OSM ih ne bilježi potpuno, pa bi bodovanje kažnjavalo gradove u kojima ih nitko nije ucrtao.
- **Premalo rezultata:** ako na odabranom području obavezne uvjete ispunjava manje od 5 naselja, ispod njih se prikazuju naselja kojima nedostaje točno jedan uvjet, uz napomenu na vrhu i oznaku „Ne ispunjava jedan uvjet profila” s opisom što nedostaje.
- **Što se ne boduje:** planirana optička mreža za rad od kuće (HAKOM na Portalu objavljuje samo namjere gradnje svjetlovodne mreže, WFS pod Otvorenom dozvolom, a ne postojeću dostupnost; nije uključeno do roka, vidi „Daljnji razvoj” u README-u), sunce na krovu (PVGIS je servis uživo).
- **Provjera smislenosti:** `backend/tests/test_finder_rules.py` provjerava pravila, ne gradove (svaki prijedlog za studenta ima studije u naselju ili u dosegu, svaki za umirovljenika trgovinu, ljekarnu i liječnika pješice, svaki za obitelj vrtić i školu, grad sa studijima je iznad svojeg predgrađa), a nad stvarnim podacima i to da top 10 za svaki profil u Hrvatskoj i u Osječko-baranjskoj županiji poštuje obavezne uvjete.
- **Jezični model** (neobavezan): samo pretvara slobodno pitanje u iste filtre (`POST /api/find/parse`). Ne vidi podatke i ne piše brojke. Bez modela radi forma.
- **Ograničenje:** vrijednosti vrijede za središte naselja; za konkretnu adresu treba otvoriti izvještaj.

### Pretpostavke bez vanjskog izvora

Izvori iz ovog dokumenta određuju granice razreda (WHO, EU, HEI, 3-30-300, scenariji poplava). Bodovi unutar razreda i nekoliko udaljenosti naša su prozirna normalizacija, zapisana i u [ODLUKE.md](ODLUKE.md):
- bodovi podskorova: poplave 100/50/0, zrak 100/80/50/10, prometnice 100/60/25, zelenilo 60 + 40 i 20 bodova za park do 600 m;
- krug od 2 km za požare, 10 minuta hoda do stajališta, razdoblje polazaka od 6 do 20 sati radnim danom, 30 godina kao trajanje stambenog kredita;
- udaljenosti za spajanje duplikata točaka (100, 60 i 30 m) i faktor predgrađa za studenta 0,75 · (1 − 0,5 · km / 15).

## Karta Hrvatske

- **Što se boji:** svih 6.759 naselja iz upravnih jedinica DGU-a, prema vrijednosti u svojem središtu iz profila naselja (vidi „Predloži mjesto za život”). Pri kliku na naselje ništa se ne računa.
- **Slojevi i razredi** (`frontend/src/lib/mapLayers.ts`), od najslabijeg do najboljeg:

| Sloj | Razredi | Osnova |
|---|---|---|
| Skor za život | 0–19, 20–39, 40–59, 60–79, 80–100 za odabrani profil | skor kao u izvještaju; koraci od 20 služe samo prikazu |
| Kvaliteta zraka | loš, umjeren, dobar, vrlo dobar | isti pragovi kao u izvještaju (WHO 2021, EU 2030., EU danas) |
| Poplave | u modeliranom području (10 ili 100 godina); područje od 500 godina ili do 100 m; izvan modeliranih područja | statusi iz izvještaja (scenariji Hrvatskih voda) |
| Usluge pješice | 0–1, 2–3, 4–5, 6–7 od 7 svakodnevnih potreba do 15 min | brojanje iz Života bez auta; parovi služe samo prikazu |
| Javni prijevoz | nema stajališta do 10 min; stajališta bez voznog reda; manje od 1 polaska na sat; 1 do 6; 6 i više | 1 na sat iz Života bez auta, 6 na sat iz Skora za život |

- **Popis ispod karte:** pet najbolje ocijenjenih naselja s najmanje 200 stanovnika za odabrani sloj (kao u „Predloži mjesto”), ili prvih pet rezultata pretrage. Pretraga postoji da se do svakog naselja može doći i bez karte (pristupačnost).
- **Skor na Karti i u izvještaju:** Karta i kartica naselja daju Skor za naselje (udaljenost od prometnica za sve adrese naselja, ostalo za središte, bez sunca na krovu jer je PVGIS servis uživo). Izvještaj računa za jednu točku i uključuje sunce, pa se brojevi razlikuju (npr. Split); kartica i izvještaj to pišu.
- **Boje:** zelena ljestvica u pet koraka, od livadne žute do šumske zelene (u svijetloj temi tamnija je bolja, u tamnoj svjetlija) i siva za „nema podataka”. Boja nije jedini nositelj informacije: legenda ima nazive, a tablica ispod karte daje iste vrijednosti riječima.
- **Klik na kartu** (`GET /api/map/point`):
  - točka u naselju, a u njezinoj ili susjednoj ćeliji od 150 m postoji kućni broj (DGU ili OSM): kartica naselja;
  - točka u naselju bez kućnih brojeva u blizini (šuma, polje): kartica naselja uz napomenu „Odabrana točka je izvan naseljenog dijela; prikazujem naselje X (središte N km)” te poplave i zrak na samoj točki iz rastera;
  - točka izvan svih naselja na kojoj ESA WorldCover pokazuje vodu ili nema podatka: „Odaberite točku na kopnu”;
  - kopno izvan svih naselja: „Podaci su dostupni samo za Hrvatsku”.
- **Geometrija:** granice naselja DGU-a pojednostavljene kao pokrivenost (300 m za cijelu Hrvatsku, 80 m nakon približavanja). Pojednostavljene granice služe samo prikazu, a klik se provjerava nad izvornim granicama.
- **Ograničenje:** boja vrijedi za središte naselja, a ne za svaku kuću u njemu. Za konkretnu adresu treba otvoriti puni izvještaj.

## Asistent

Vidi [ASISTENT.md](ASISTENT.md).
