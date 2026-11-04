# Metodologija

Ovaj dokument opisuje kako se računa svaka kategorija pregleda, koji se pragovi koriste i odakle dolaze. Izvori podataka s licencama i poveznicama navedeni su u [IZVORI_PODATAKA.md](IZVORI_PODATAKA.md), a odluke donesene tijekom izrade u [ODLUKE.md](ODLUKE.md).

## Načela

1. **Apsolutno značenje ispred relativnog ranga.** Pregled kaže, na primjer, „lokacija je u modeliranom poplavnom području za povratno razdoblje od 100 godina”, a ne „rizik iznad prosjeka”.
2. **Svaka kategorija ima status** prema pragu s izvorom: dobro, upozorenje, loše ili nema podataka. Kategorije za koje ne postoji općeprihvaćen prag (sunce, buka kao procjena, život bez auta, javni prijevoz, svakodnevni život) imaju status „Informacija” i prikazuju samo podatak, bez ocjene. „Nema podataka” se uvijek prikazuje; kategorija se nikad tiho ne izostavlja.
3. **Nema skupne ocjene.** Kategorije se ne zbrajaju ni ne ponderiraju. Profil korisnika (obitelj s djecom, umirovljenik, student, rad od kuće, vlastiti) mijenja samo redoslijed i naglasak kartica, nikad vrijednosti ni statuse.
4. **Svaka vrijednost ima izvor, datum preuzimanja i vrstu.** Vrste su:
   - `measured` (izmjereno): vrijednost iz mjerenja, voznog reda ili službenog registra;
   - `modelled` (modelirano): izračun modelom (karte poplava i zraka, satelitski pokrov tla, vrijeme hoda po mreži);
   - `estimate` (procjena): zamjenski podatak, npr. udaljenost od prometnice umjesto razine buke ili zračna udaljenost kad usmjerivač ne radi.
5. **Sažetak se slaže iz predložaka.** Dvije do tri rečenice sažetka su naslovne rečenice kategorija poplava, zraka i života bez auta. Jezični model ne piše tekst.

## Lokacija

- Adresa se pretvara u koordinate vlastitim geokoderom nad 1.683.411 adresa iz skupa „Adrese INSPIRE” Državne geodetske uprave. Upit i adrese normaliziraju se: mala slova, bez dijakritika, `đ` i `dj` kao `d`. Riječi „ulica” i „ul.” zanemaruju se jer ih službeni nazivi često nemaju („Bana Jelačića”). Kod upita od tri ili više riječi jedna riječ smije nedostajati (npr. ime u „Bana Josipa Jelačića”), ali najdulja mora odgovarati.
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

| Razina (status) | PM2,5, godišnji prosjek | NO2, godišnji prosjek | Granica |
|---|---|---|---|
| vrlo niska (dobro) | ≤ 5 µg/m³ | ≤ 10 µg/m³ | smjernica WHO-a 2021 |
| niska (dobro) | ≤ 10 µg/m³ | ≤ 20 µg/m³ | granična vrijednost EU-a od 2030. |
| umjerena (informacija, neutralno) | ≤ 25 µg/m³ | ≤ 40 µg/m³ | granična vrijednost EU-a koja vrijedi danas |
| visoka (loše) | > 25 µg/m³ | > 40 µg/m³ | iznad današnje granične vrijednosti EU-a |

Crveno je samo razina iznad granice koja danas pravno vrijedi. Status kategorije je viša od dviju razina (PM2,5, NO2). Uz svaku vrijednost tekstom se navodi odnos prema smjernici WHO-a i granicama EU-a, a na kartici je ljestvica s oznakama tih granica.

- **Izvori pragova:**
  - WHO global air quality guidelines (2021), tablica 0.1: godišnja smjernica PM2,5 5 µg/m³ i NO2 10 µg/m³. https://iris.who.int/handle/10665/345329
  - Direktiva (EU) 2024/2881 o kvaliteti zraka i čišćem zraku za Europu, Prilog I., odjeljak 1., tablica 1: granične vrijednosti koje se moraju postići do 1. 1. 2030. su godišnje PM2,5 10 µg/m³ i NO2 20 µg/m³. CELEX 32024L2881.
  - Ista direktiva, Prilog I.: granične vrijednosti koje se moraju postići do 11. 12. 2026. su godišnje PM2,5 25 µg/m³ i NO2 40 µg/m³; iste vrijednosti propisuje i dosadašnja Direktiva 2008/50/EZ. To je „granica koja vrijedi danas”.
- Status kategorije je lošiji od dvaju statusa (PM2,5 i NO2).
- **Ograničenja:** karta je modelirana procjena godišnjeg prosjeka na mreži od 1 km, a ne mjerenje na adresi. Prema EEA-i ne smije se koristiti za službenu provjeru usklađenosti. Uz izvještaj je poveznica na mjerenja u stvarnom vremenu (iszz.azo.hr).

## Toplina i zelenilo

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
- **Ograničenja:** WorldCover mjeri pokrov tla iz satelita i ne razlikuje javne od privatnih vrtova. OSM parkovi su izvan gradova nepotpuni. Dio pravila „3 stabla vidljiva s prozora” ne može se izračunati iz otvorenih podataka.

## Promet u blizini (procjena; ranije „Buka”)

- **Podaci:** autoceste, brze, glavne i važnije ceste (`highway=motorway|trunk|primary|secondary`) i pruge (`railway=rail`, bez sporednih kolosijeka) iz OpenStreetMapa.
- **Izračun:** zračna udaljenost do najbliže takve ceste i najbliže pruge, do 2 km. Buku ne mjerimo; udaljenost je zamjenski pokazatelj, vrste „procjena”.
- **Pojasevi:**

| Udaljenost od ceste | Oznaka | Status |
|---|---|---|
| do 300 m | Blizu prometnice | upozorenje |
| 300–500 m | Rub zone prometa | informacija |
| više od 500 m | Podalje od prometnica | dobro |

- **Izvor pojaseva:** Health Effects Institute (2010.), *Traffic-Related Air Pollution: A Critical Review of the Literature on Emissions, Exposure, and Health Effects*, Special Report 17. Zona najjačeg utjecaja prometa je približno 300 do 500 m od autoceste ili velike prometnice, a dalje koncentracije padaju na pozadinsku razinu.
- **Pruga:** navodi se opisno ako je do 500 m. Pregled HEI-ja odnosi se na cestovni promet, pa pruga ne mijenja status.
- **Kontekst:** smjernice WHO-a za buku okoliša (2018.) preporučuju cestovni promet ispod 53 dB Lden i 45 dB Lnight (https://iris.who.int/handle/10665/279952). Strateške karte buke EEA-e nemaju otvorenu licencu, pa ih samo povezujemo.
- Zašto i `secondary`: vidi [ODLUKE.md](ODLUKE.md).

## Požari raslinja

- **Podaci:** EFFIS (Copernicus European Forest Fire Information System), opožarene površine kartirane iz satelitskih snimaka MODIS, sloj `ms:modis.ba.poly` preuzet preko javnog WFS-a za Hrvatsku (1.030 površina od 2016.). Skupno preuzimanje traži račun, a WFS ne.
- **Izračun:** opožarene površine čiji poligon dodiruje krug od 2 km oko točke: broj, godine, najbliža (udaljenost do ruba) i najveća (ha).
- **Status:** „Informacija”, jer za broj prošlih požara ne postoji prag s izvorom. Prošli požari pokazuju izloženost, a ne predviđaju buduće.
- **Ograničenja:** satelitsko kartiranje ne bilježi sve manje požare; podaci počinju 2016.

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
- Ako usmjerivač ne odgovara, prikazuje se zračna udaljenost s oznakom „procjena”, a kategorije koje ovise o hodu prikazuju „Nema podataka”.

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
- **Izvori voznih redova:** ZET (GTFS), HŽPP (GTFS) i Autotrolej (vozni red radnim danom, JSON). Drugdje se prikazuju stajališta iz OpenStreetMapa s oznakom „bez voznog reda”. OSM stajališta unutar 60 m od stajališta s voznim redom smatraju se istim stajalištem.

## Asistent

Vidi [ASISTENT.md](ASISTENT.md).
