# Kvaliteta podataka

Nalazi su utvrđeni tijekom izrade rješenja: provjerom izvora 2. 11. 2026. i automatskom obradom (`make data`). Tablice u ovom dokumentu izvedene su iz zapisa obrade (`data/processed/geocoding_report.json` i `data/processed/recycling_ckan.json`). Cilj je pomoći izdavačima da podatke učine upotrebljivijima.

## Sažetak

1. **Registri bez koordinata.** Registar dječjih vrtića, popis osnovnih škola i popisi ugovornih ordinacija i ljekarni HZZO-a nemaju koordinate. Svaki ih korisnik mora sam geokodirati.
2. **Registri pravnih osoba umjesto lokacija.** Registar vrtića navodi pravne osobe (885 redaka), a ne sve objekte: u Zagrebu ima 199 redaka, a gradski geoportal 323 objekta. Popis škola nema područne škole.
3. **Općinski skupovi o otpadu su neujednačeni.** Od 33 pronađena skupa o reciklažnim dvorištima i zelenim otocima samo 11 ima upotrebljive koordinate. Isti se podaci objavljuju u 3–4 oblika (CSV, JSON, XLSX, PDF), u barem tri različite strukture stupaca.
4. **Neispravne poveznice i metapodaci.**
   - Poveznica na vozni red HŽPP-a na Portalu vraća 404.
   - Resurs ATOM skupa „Adrese INSPIRE” ima praznu poveznicu.
   - Resurs „GeoJSON” Geoportala dječjih vrtića Grada Zagreba vodi na `format=fgdb`.
5. **Licence.** HZZO-ovi popisi i GTFS HŽPP-a nemaju navedenu licencu. DGU skupovi istodobno navode Otvorenu dozvolu i „ograničenje javnog pristupa” prema INSPIRE direktivi. JRC karte poplava navode dvije različite licence.

## Geokodiranje registara

Vlastiti geokoder uspoređuje adresu iz registra s 1.683.411 adresa DGU-a (poštanski broj ili naselje, kućni broj i riječi naziva ulice). „Sredina ulice” znači da kućni broj nije pronađen pa je uzeta srednja adresa iste ulice.

| Skup | Adresa točno | Sredina ulice | Nije pronađeno | Uspješnost |
|---|---|---|---|---|
| Registar dječjih vrtića (MZOM), izvan Zagreba | 493 | 158 | 51 | 92,7 % |
| Osnovne škole (MZOM), izvan Zagreba | 675 | 76 | 58 | 92,8 % |
| HZZO, ordinacije obiteljske medicine (jedinstvene adrese) | 1048 | 63 | 90 | 92,5 % |
| HZZO, pedijatrijske ordinacije (jedinstvene adrese) | 180 | 4 | 10 | 94,8 % |
| HZZO, ugovorene ljekarne (jedinstvene adrese) | 861 | 175 | 165 | 86,3 % |

Najčešći razlozi neuspjeha:
- nazivi ulica u drugom obliku nego u registru DGU-a (skraćenice poput „J.J.Strossmayera”, stari nazivi);
- adrese bez kućnog broja ili s oznakom „bb”;
- mjesto u registru je poštanski ured, a ne naselje.

Neuspjeli zapisi ne prikazuju se. U njihovoj blizini pregled pokazuje sljedeću najbližu ustanovu ili, za vrtiće, škole i ljekarne, objekt iz OpenStreetMapa.

## Pojedinačni nalazi po izvoru

| Izvor | Nalaz |
|---|---|
| DGU Adrese INSPIRE | `Address.gml` je jedan redak od 2,6 GB; bez strujnog čitanja ga nije moguće obraditi. Adrese nemaju poveznicu na JLS, samo na naselje. ISO metapodaci navode format SHP, a isporučuje se GML. Javni WFS je isključen. |
| DGU Upravne jedinice | Poveznice na nadređenu jedinicu (`upperLevelUnit`) postoje u GML-u, ali ih GDAL ne izlaže, pa smo hijerarhiju izveli prostorno. |
| DZS Popis 2021. po naseljima | Tablica nema šifre naselja ni JLS-a, samo nazive; spajanje s DGU naseljima moguće je samo po imenu grada ili općine i naselja. Spojeno je 6.633 od 6.759 DGU naselja (98,1 %); za ostala se broj stanovnika ne prikazuje. |
| MZOM Registar dječjih vrtića | Bez koordinata i identifikatora. Stupac `Zupanija` ima suvišne razmake. Posljednja izmjena na Portalu 15. 4. 2026. |
| MZOM Osnovne škole | Bez koordinata. Naziv stupca `Župnija` (umjesto „Županija”). Stupac `Ravnatelj` sadrži osobna imena (ne prikazujemo ih). Velika i mala slova u adresama nisu ujednačena. |
| HZZO ordinacije | Tablice u XLSX-u s dvostrukim zaglavljem; 81 tim opće medicine nema ulicu. Datoteke sadrže imena liječnika; prikazujemo samo adresu ordinacije. Licenca nije navedena. |
| HZZO ljekarne | Posljednja izmjena datoteke 28. 9. 2023.; poveznica „Popis dežurnih ljekarni” vraća 404. Skupovi HZZO-a na Portalu vode na datoteke iz 2018. |
| ZET GTFS | `calendar.txt` ima sve dane u tjednu postavljene na 0; stvarni dani prometa nalaze se samo u `calendar_dates.txt`. Dva stajališta imaju koordinate 0, 0. |
| HŽPP GTFS | Poveznica na Portalu (`…/Media/Default/GTFS/GTFS_files.zip`) vraća 404; datoteka na `https://www.hzpp.hr/GTFS_files.zip` radi i osvježava se svakodnevno. Licenca nije navedena. Vozni red vrijedi do 13. 12. 2026. |
| Autotrolej | GTFS na `gt.autotrolej.hr` ima istekao TLS certifikat; koristimo JSON vozni red s Portala (CC BY 4.0). |
| Hrvatske vode, karte poplava | Licenca nije navedena; dostupni su preglednik i WMS, pa karte samo povezujemo. |
| EEA strateške karte buke | Hrvatska je uključena, ali je licenca ograničena na istraživanje i neprofitnu upotrebu; ne koristimo ih. |
| JRC karte poplava | Katalog i README navode ODbL 1.0, a `copyright.txt` CC BY 4.0. |

## Reciklažna dvorišta i zeleni otoci (CKAN)

Pretraga Portala (`package_search`) za „reciklažno dvorište”, „reciklažna dvorišta”, „zeleni otok” i „zeleni otoci” vraća 33 skupa. Obrada za svaki skup čita CSV, JSON ili XLSX resurse i traži stupce s koordinatama. Prepoznaje i zamijenjenu geografsku širinu i dužinu te uzima jedan resurs po skupu, jer se isti podaci objavljuju u više oblika.

| Izdavač | Skup | Oblici | Koordinate | Nalazi |
|---|---|---|---|---|
| Grad Hvar | Reciklažno dvorište na području Grada Hvara | csv, xlsx | da (1) | — |
| Grad Zagreb | Geoportal Reciklažna dvorišta grada Zagreba | csv, gdb, geojson, kml, shp | da (20) | — |
| Općina Bistra | Reciklažno dvorište na području općine Bistra | csv, xlsx | da (1) | — |
| Općina Cernik | Reciklažno dvorište, Općina Cernik | csv, json, pdf, xlsx | da (1) | — |
| Općina Dugopolje | Reciklažno dvorište Općine Dugopolje | csv, json, pdf, xlsx | da (1) | — |
| Općina Kalinovac | Zeleni otoci i reciklažna dvorišta na području Općine Kalinovac | csv, json, xlsx | da (5) | — |
| Općina Kloštar Podravski | Reciklažno dvorište Općine Kloštar Podravski | csv, json, pdf, xlsx | da (1) | — |
| Općina Mikleuš | Reciklažna dvorišta i zeleni otoci | csv, json, pdf, xlsx | da (1) | neispravne koordinate (4) |
| Općina Posedarje | Zeleni otoci | csv, pdf, xlsx | da (2) | — |
| Općina Sopje | Zeleni otoci na području Općine Sopje | csv, json, pdf, xlsx | da (6) | neispravne koordinate (3) |
| Općina Velika Ludina | Reciklažna dvorišta i zeleni otoci | csv, json, pdf, xlsx | da (7) | — |
| Grad Grubišno Polje | Reciklažno dvorište Grubišno Polje | bez oznake | ne | — |
| Grad Karlovac | Reciklažna dvorišta i komunalni otpad - Grad Karlovac | bez oznake | ne | — |
| Grad Karlovac | Grad Karlovac - Otpad i zaštita okoliša | bez oznake | ne | — |
| Grad Osijek | Reciklažna dvorišta i kompostana | html | ne | — |
| Grad Prelog | Podaci o reciklažnom dvorištu na području Grada Preloga | csv | ne | — |
| Grad Rijeka | Reciklažna dvorišta | csv | ne | koordinate u neispravnom obliku broja (6) |
| Grad Rijeka | Raspored mobilnih reciklažnih dvorišta u Rijeci | xls | ne | — |
| Grad Rijeka | Lokacije posuda za prikupljanje otpada u Rijeci | html | ne | — |
| Grad Rijeka | Zelene javne površine u Rijeci | wms | ne | — |
| Grad Zagreb | Lokacije zelenih otoka | csv, xlsx | ne | — |
| Grad Zlatar | Reciklažno dvorište Grada Zlatara | html | ne | — |
| Hrvatska agencija za okoliš i prirodu (NEAKTIVAN) | ENVI Atlas okoliša | html | ne | — |
| Općina Erdut | https://www.cvorkovac.hr/index.php/zastita-okolisa/reciklazno-dvoriste-studenac | bez oznake | ne | resurs bez poveznice |
| Općina Erdut | PROSTORNI PODACI OPĆINE ERDUT | bez oznake | ne | resurs bez poveznice |
| Općina Gradec | Zeleni otoci na području opčine Gradec | csv, json, xlsx | ne | CSV nije dostupan ili čitljiv (ValueError) |
| Općina Lasinja | Lokacije zelenih otoka | docx | ne | — |
| Općina Maruševec | Reciklažno dvorište, isporučitelji komunalnih i dimnjačarskih usluga | xlsx | ne | — |
| Općina Petrovsko | Reciklažno dvorište, komunalni otpad i ugostiteljski objekti | csv | ne | — |
| Općina Rugvica | Reciklažna dvorišta i zeleni otoci | pdf | ne | — |
| Općina Semeljci | KOMUNALNI OTPAD, RECIKLAŽNO DVORIŠTE | bez oznake | ne | — |
| Općina Stari Jankovci | Reciklažno dvorište - Općina Stari Jankovci | bez oznake | ne | — |
| Općina Vinica | Reciklažna dvorišta | docx, html, jpeg | ne | — |

Općinske točke spajaju se s OpenStreetMapom (`amenity=recycling`). OSM točke unutar 30 m od općinske smatraju se istom lokacijom.

**Preporuka izdavačima:** jedinstveni predložak na razini države (naziv, adresa, vrsta: reciklažno dvorište ili zeleni otok, vrste otpada, radno vrijeme, geografska širina i dužina u WGS84 kao decimalni brojevi s točkom) i jedan strojno čitljiv oblik (CSV ili GeoJSON) umjesto PDF-a i poveznica na web stranice. Spojeni sloj iz ovog rješenja mogao bi se vratiti na Portal kao nacionalni skup.
