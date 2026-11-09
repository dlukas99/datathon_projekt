# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primarni korisnik:** običan građanin koji bira gdje živjeti, bilo da kupuje ili unajmljuje kuću ili stan ili tek razmišlja o selidbi. Nije stručnjak za okoliš, GIS ni nekretnine. Često ima oglas otvoren u drugoj kartici i želi brzo i razumljivo saznati kako je živjeti na toj adresi.
- **Sekundarni:** ocjenjivači Datathona Portala otvorenih podataka 2026. (izazov B: Okoliš i održivi prostor). Vide isti proizvod kao građanin, preko demo poveznice, snimki zaslona i videa do 3 minute. Za njih se ne radi poseban prikaz.
- **Uređaji:** mobitel i desktop koriste se podjednako; oba moraju biti prvoklasna. Mobitel od 320 px bez vodoravnog pomicanja.

## Product Purpose

Za bilo koju adresu u Hrvatskoj aplikacija daje okolišni pregled i pregled svakodnevnog života, isključivo iz otvorenih podataka. Okolišni pregled obuhvaća poplave, zrak, prirodu i hlad, udaljenost od prometnica, požare raslinja i sunce na krovu. Svakodnevni život obuhvaća život bez auta (izokrone hoda, javni prijevoz) i svakodnevne potrebe (vrtić, škola, liječnik, ljekarna, trgovina, park).

Ti podaci postoje, ali su rasuti po institucijama i formatima i običnom čovjeku nisu ni razumljivi ni usporedivi. Ljudi okolišne rizike i ovisnost o autu najčešće otkriju tek kad usele.

Uspjeh: korisnik razumije kako je živjeti na adresi i koje mu mjesto odgovara, u apsolutnim i provjerljivim izrazima, s izvorom za svaku brojku.

## Positioning

- Jedno mjesto koje spaja 33 skupa podataka (DGU, EEA, JRC, ESA WorldCover, Copernicus EFFIS, PVGIS, GTFS voznih redova, registri ustanova, OSM) u izvještaj za točnu adresu, a ne za općinu ili prosjek.
- Apsolutno značenje ispred relativnog ranga: „u modeliranom poplavnom području za povratno razdoblje od 100 godina: da” umjesto „rizik iznad prosjeka”.
- Svaka vrijednost nosi izvor, datum preuzimanja i vrstu (izmjereno, modelirano ili procjena).
- Okoliš je uvijek prvi i najvažniji (izazov B). Svakodnevne potrebe su dodatak; proizvod ne smije izgledati kao aplikacija za škole i trgovine.

## Operating Context

- Ulazi s naslovnice:
  - Provjeri adresu: izvještaj za adresu.
  - Pronađi mjesto za mene: rangirana naselja prema profilu i njegovim obaveznim uvjetima.
  - Istraži kartu Hrvatske: svih 6.759 naselja obojeno po sloju.
- Usporedba dviju lokacija je u izborniku i u izvještaju.
- Izvještaj ima stalan redoslijed: okolišni pregled (prvi ekran), život bez auta, svakodnevni život, izvori.
- Točka se bira upisom adrese ili povlačenjem oznake na karti.
- „Pogledaj oglase” samo slaže poveznicu na vanjsku pretragu oglasa; aplikacija ne prikazuje oglase.
- Asistent odgovara na pitanja o lokaciji; brojke dolaze iz predložaka nad rezultatima alata, ne iz jezičnog modela.
- Ostale stranice: O alatu (Ukratko, Kako računamo, Izvori podataka s datumima osvježavanja uživo preko CKAN API-ja data.gov.hr, Kvaliteta podataka, Privatnost, Tim; `/izvori` vodi na dio „Izvori podataka”), ispis i dijeljenje stanja preko URL-a.

## Capabilities and Constraints

- **Stog:** React 19, TypeScript, Vite, React Router, TanStack Query, MapLibre GL JS s podlogom OpenFreeMap; backend FastAPI. Fontovi Bricolage Grotesque (naslovi) i Figtree (tekst), OFL, s vlastitog poslužitelja.
- **Kategorije i statusi:** svaka kategorija ima status (dobro, upozorenje, loše ili nema podataka) prema pragu s izvorom. „Nema podataka” se uvijek prikazuje, nikad se kategorija tiho ne izostavlja.
- **Ocjena mjesta (0–100):** sažima kategorije s vidljivim i podesivim težinama profila (obitelj s djecom, umirovljenik, student, rad od kuće, vlastiti). Profil mijenja redoslijed i naglasak, nikad vrijednosti.
- **Pragovi:** zrak prema WHO 2021 i EU 2030; buka prema smjernicama WHO 2018. Svi pragovi i izvori su u `docs/METODOLOGIJA.md`.
- **Podaci:** nikad izmišljeni. Testni podaci postoje samo u `backend/tests/fixtures/` i nikad se ne prikazuju u aplikaciji.
- **Privatnost:** upisane adrese i pitanja se ne spremaju; nema analitike ni kolačića za praćenje.
- **Demo materijali:** isključivo adrese javnih ustanova (`scripts/demo_addresses.json`), nikad privatne kuće.
- **Jezik:** sučelje na standardnom hrvatskom, bez srbizama i anglizama gdje postoji hrvatska riječ; brojevi u hrvatskom formatu (6.759; 4,5 km/h).
- **Rok:** predaja 9. 11. 2026. u 24:00. Od 8. 11. samo popravci, dokumentacija i revizija README-a.
- **Neodlučeno:** konačan naziv proizvoda.

## Brand Commitments

- **Naziv:** „Dobro mjesto” je radni naziv i nije konačan. Naziv postoji samo u `frontend/src/lib/brand.ts` i `backend/app/brand.py`, a dizajn ne smije ovisiti o njemu.
- **Ton:** neutralan i miran, bez zastrašivanja. Uvijek je jasno da je riječ o informativnom alatu, a ne službenoj procjeni; svaki izvještaj ima napomenu s poveznicom na metodologiju.
- **Zabrane:** bez maskote i emojija. Bez grba RH i logotipa tijela javne vlasti; ništa ne smije sugerirati službeni status.
- **Asistent:** ne daje savjete o kupnji („kupite”, „nemojte kupiti”), nego činjenice i upute na službene izvore.

## Evidence on Hand

- Stvarni izračuni za demo adrese javnih ustanova (Vinkovci, Osijek, Zagreb, Split i jedno manje naselje): `scripts/demo_addresses.json`; zlatne snimke u `backend/tests/fixtures/golden/`.
- Snimke zaslona: `docs/images/` (izvještaj, usporedba, karta i drugi zasloni, desktop i mobitel).
- Izvori s licencama i datumima: `docs/IZVORI_PODATAKA.md`; nalazi o kvaliteti podataka: `docs/KVALITETA_PODATAKA.md`.
- **Ne postoji i ne smije se izmisliti:** korisnička iskustva, citati korisnika, broj korisnika, nagrade, partneri, mediji, službene potvrde ni demo URL (postavljanje rade ljudi).

## Product Principles

1. **Okoliš prvi.** Okolišni pregled je prvo što korisnik vidi; ostalo je ispod njega.
2. **Istina ispred dojma.** Apsolutna, provjerljiva značenja s izvorom, datumom i vrstom vrijednosti; nesigurnost i „nema podataka” prikazuju se otvoreno.
3. **Razumljivo laiku.** Jedna jasna rečenica ispred stručnih brojki; stručni detalji su dostupni, ali ne smetaju.
4. **Bez skrivenih sudova.** Nema skupne ocjene sa skrivenim težinama ni savjeta o kupnji; korisnik sam odlučuje.
5. **Karta nikad nije jedini nositelj informacije.** Sve što je na karti piše i u tekstu.

## Accessibility & Inclusion

- WCAG 2.2 razine AA; axe bez nalaza na svim stranicama, u svijetloj i tamnoj temi, na desktopu i mobitelu.
- Ciljevi dodira najmanje 44 px; poštuju se smanjene animacije; `lang="hr"`.
- Statusi se prikazuju bojom i riječima, nikad samo bojom.
- Detalji provjera: `docs/PRISTUPACNOST.md`.
