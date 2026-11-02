# Izvori podataka

Svaki izvor provjeren je stvarnim preuzimanjem 2. 11. 2026. Za svaki je naveden status (**radi**, **djelomično**, **ne radi**), licenca, format i odabrani rezervni plan. Datumi preuzimanja pojedine datoteke zapisuju se automatski u `data/processed/manifest.json` pri pokretanju `make data` i prikazuju se uz svaku vrijednost u aplikaciji.

Sva preuzimanja šalju User-Agent `PrijePotpisa/0.1 (+CONTACT_EMAIL)`, ponovno koriste već preuzete datoteke iz `data/raw/` i između zahtjeva istom poslužitelju čekaju najmanje jednu sekundu.

## Pregled

| Područje | Izvor | Status | Licenca | Upotreba |
|---|---|---|---|---|
| Adrese | DGU, Adrese INSPIRE | radi | Otvorena dozvola RH | geokodiranje, geokodiranje registara |
| Upravne jedinice | DGU, Upravne jedinice INSPIRE | radi | Otvorena dozvola RH | naselje, općina ili grad, županija |
| Stanovništvo | DZS, Popis 2021., stanovništvo po naseljima | radi | Otvorena dozvola RH | broj stanovnika naselja |
| Poplave | JRC, karte opasnosti od riječnih poplava (CEMS-EFAS) v3.1.1 | radi | ODbL 1.0 / CC BY 4.0 (vidi napomenu) | dubina vode za povratna razdoblja 10, 100 i 500 godina |
| Poplave (službeno) | Hrvatske vode, karte opasnosti od poplava 2019. | samo poveznica | nije navedena | poveznica na preglednik |
| Zrak | EEA, interpolirane karte kvalitete zraka 2024., 1 km | radi | CC BY 4.0 | PM2,5 i NO2 |
| Zelenilo | ESA WorldCover 10 m 2021 v200 | radi | CC BY 4.0 | drveće, zelene i izgrađene površine |
| Buka | EEA, strateške karte buke (END 2022) | ne koristi se | ograničena (istraživanje i neprofitna upotreba) | rezervni plan: udaljenost od prometnica (OSM) |
| Sunce | JRC PVGIS 5.3 API | radi | slobodna upotreba uz navođenje izvora | kWh po kWp godišnje |
| Mreža hoda | OpenStreetMap (Geofabrik) + Valhalla | radi | ODbL 1.0 | izokrone i vremena hoda |
| Vrtići | MZOM, Registar dječjih vrtića | djelomično | Otvorena dozvola RH | vrtići (geokodirani) |
| Vrtići, Zagreb | Grad Zagreb, Geoportal dječji vrtići | radi | CC BY 4.0 | vrtići u Zagrebu s koordinatama |
| Škole | MZOM, Osnovne škole | djelomično | Otvorena dozvola RH | matične osnovne škole (geokodirane) |
| Škole, Zagreb | Grad Zagreb, Geoportal osnovne škole | radi | Otvorena dozvola RH | matične i područne škole u Zagrebu |
| Liječnici | HZZO, ugovoreni timovi opće/obiteljske medicine i pedijatrije | radi | nije navedena (vidi napomenu) | ordinacije (geokodirane) |
| Ljekarne | HZZO, popis ugovorenih ljekarni | djelomično (zastarjelo, 2023.) | nije navedena | ljekarne (geokodirane), dopunjene OSM-om |
| Trgovine, igrališta, parkovi | OpenStreetMap | radi | ODbL 1.0 | svakodnevne potrebe |
| Javni prijevoz, Zagreb | ZET GTFS | radi | Otvorena dozvola RH | polasci po satu |
| Javni prijevoz, vlak | HŽPP GTFS | radi | nije navedena (vidi napomenu) | polasci po satu |
| Javni prijevoz, Rijeka | Autotrolej, vozni red radnim danom (JSON) | radi | CC BY 4.0 | polasci po satu |
| Javni prijevoz, ostalo | OpenStreetMap stajališta | radi | ODbL 1.0 | stajališta bez voznog reda |
| Reciklaža | općinski skupovi na data.gov.hr + OSM | djelomično | Otvorena dozvola RH / CC BY 4.0 / ODbL | reciklažna dvorišta i spremnici |
| Datumi osvježavanja | CKAN API data.gov.hr | radi | — | stranica „Izvori” uživo |
| Podloga karte | OpenFreeMap | radi | MIT (softver), ODbL (podaci) | kartografska podloga |

## Detalji po izvorima

### DGU: Adrese INSPIRE
- Skup: https://data.gov.hr/ckan/dataset/adrese-inspire (resurs ATOM u CKAN-u ima praznu poveznicu, pa se koristi ATOM feed).
- ATOM: https://geoportal.dgu.hr/services/atom/ad/xml
- Preuzimanje: `https://geoportal.dgu.hr/services/atom/INSPIRE_Addresses_(AD).zip` (≈ 90 MB ZIP, 2,68 GB GML nakon raspakiranja).
- Format: INSPIRE GML 3.2.1, EPSG:3035. `Address.gml` sadrži 1.683.411 adresa; ulice su u `ThoroughfareName.gml`, naselja u `AdminUnitName.gml`, poštanski brojevi u `PostalDescriptor.gml`.
- Licenca: Otvorena dozvola RH (https://data.gov.hr/id/licence/otvorena-dozvola-rh). ATOM feed istodobno navodi „ograničenje javnog pristupa prema članku 13. stavku 1. točki (e) INSPIRE Direktive”; koristimo licencu iz kataloga Portala (vidi `docs/ODLUKE.md`).
- Javni WFS je isključen; dostupni su samo ATOM ZIP i WMS.
- Rezervni plan: adrese iz OSM izvatka (`addr:*`, 267.889 adresa).

### DGU: Upravne jedinice INSPIRE
- Skup: https://data.gov.hr/ckan/dataset/upravne-jedinice-inspire
- Preuzimanje: `https://geoportal.dgu.hr/services/atom/INSPIRE_Administrative_Units_(AU).zip` (≈ 209 MB).
- Format: GML 3.2.1, EPSG:3035. 21 županija, 556 jedinica lokalne samouprave, 6.759 naselja (i statistički i popisni krugovi, koje ne koristimo). Hijerarhija naselje → JLS → županija preko `au:upperLevelUnit`.
- Licenca: Otvorena dozvola RH.
- Rezervni plan: granice iz OSM-a (`boundary=administrative`).

### DZS: Popis 2021., stanovništvo po naseljima
- Skup: https://data.gov.hr/ckan/dataset/statistika-u-nizu-popis-stanovnistva-kucanstava-i-stanova-2021
- Datoteka: https://podaci.dzs.hr/media/rqybclnx/popis_2021-stanovnistvo_po_naseljima.xlsx (list `1.`, zaglavlje u 8. retku).
- Nema šifri naselja ni koordinata; spaja se s DGU naseljima po imenu naselja i JLS-a (99,8 % naselja nakon skraćivanja dvojezičnih naziva).
- Licenca: Otvorena dozvola RH, uz navođenje izvora (DZS).
- Rezervni plan: izostaviti broj stanovnika.

### JRC: karte opasnosti od riječnih poplava za Europu
- Katalog: https://data.jrc.ec.europa.eu/dataset/1d128b6c-a4ee-4858-9e34-6210707f3c81 (DOI 10.2905/1D128B6C-A4EE-4858-9E34-6210707F3C81).
- Mapa: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-EFAS/flood_hazard/ (verzija 3.1.1 od 5. 3. 2026.)
- Datoteke: `Europe_RP10_filled_depth.tif`, `Europe_RP100_filled_depth.tif`, `Europe_RP500_filled_depth.tif` (260–334 MB). Jedna datoteka za cijelu Europu po povratnom razdoblju; isijecamo Hrvatsku.
- Format: GeoTIFF, EPSG:4326, 3 lučne sekunde (≈ 90 m), float32, dubina vode u metrima, suho = -9999.
- Licenca: katalog i README navode ODbL 1.0, a `copyright.txt` u mapi CC BY 4.0. Obje dopuštaju upotrebu uz navođenje izvora; poštujemo strožu (ODbL) i navodimo izvor.
- Citat: Baugh, C., Colonese, J., D'Angelo, C., Dottori, F., Neal, J., Prudhomme, C., Salamon, P. (2024). Global river flood hazard maps. European Commission, Joint Research Centre.
- Rezervni plan: samo poveznica na preglednik Hrvatskih voda.

### Hrvatske vode: karte opasnosti od poplava
- Preglednik: https://preglednik.voda.hr/ (sloj „Karta vjerojatnosti pojavljivanja 2019.”), stranica https://www.voda.hr/hr/karte-opasnosti-od-poplava-i-karte-rizika-od-poplava-2019
- WMS: https://servisi.voda.hr/poplave_opasnosti/wms
- Licenca nije navedena, pa karte samo povezujemo i ne izvodimo podatke iz njih (CLAUDE.md, pravilo 3).
- Opis skupa na Portalu definira scenarije: velika vjerojatnost, srednja vjerojatnost (povratno razdoblje 100 godina) i mala vjerojatnost.

### EEA: interpolirane karte kvalitete zraka
- PM2,5 2024.: https://sdi.eea.europa.eu/webdav/datastore/public/eea_r_3035_1_km_aq-interpolated-pm25_p_2024_v01_r00/pm25_avg_24.tif (zapis: https://sdi.eea.europa.eu/catalogue/srv/api/records/c3db03e4-82e9-4a40-acb1-a5bd15f11f8c)
- NO2 2024.: https://sdi.eea.europa.eu/webdav/datastore/public/eea_r_3035_1_km_aq-interpolated-no2_p_2024_v01_r00/no2_avg_24.tif (zapis: https://sdi.eea.europa.eu/catalogue/srv/api/records/4c6361bd-cfd4-48de-9b4b-101cfb37f1f0)
- Objavljeno 29. 5. 2026. („validated data, June 2026”). Postoje i privremene karte za 2025.; koristimo validirane za 2024.
- Format: GeoTIFF, EPSG:3035, 1 km, float32, µg/m³.
- Licenca: CC BY 4.0, nositelj prava EEA. Napomena izvora: karte se ne smiju koristiti za službenu provjeru usklađenosti s propisanim standardima.
- Rezervni plan: najbliža mjerna postaja (nije bio potreban).

### ESA WorldCover 10 m 2021 v200
- Pločice: `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{N42E012,N42E015,N42E018,N45E012,N45E015,N45E018}_Map.tif` (≈ 461 MB ukupno).
- Format: COG, EPSG:4326, 10 m, uint8, 0 = bez podataka. Razredi: 10 drveće, 20 grmlje, 30 travnjaci, 40 poljoprivredne površine, 50 izgrađeno, 60 golo tlo, 80 vode, 90 močvare.
- Priručnik: https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/docs/WorldCover_PUM_V2.0.pdf
- Licenca: CC BY 4.0. Atribucija: „© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium”.
- Rezervni plan: OSM `landuse`, `leisure=park`, `natural=wood` (nije bio potreban).

### EEA: strateške karte buke (direktiva o buci okoliša)
- Zapis END 2022: https://sdi.eea.europa.eu/catalogue/srv/api/records/853e72e4-4642-47d1-8556-2cc231bd43e0; Hrvatska: `HR.gpkg` (≈ 1,4 GB).
- Licenca: „public access limited according to Article 13(1)(e) of the INSPIRE Directive … available for research and non-profit purposes”. To nije otvorena licenca.
- **Ne koristi se.** Rezervni plan: udaljenost od autocesta, brzih i glavnih cesta te pruga iz OSM-a, označena kao procjena, uz poveznicu na preglednik EEA-e (https://noise.discomap.eea.europa.eu/).

### JRC PVGIS
- API: `https://re.jrc.ec.europa.eu/api/v5_3/PVcalc?lat=…&lon=…&peakpower=1&loss=14&optimalangles=1&outputformat=json`
- Vrijednost: `outputs.totals.fixed.E_y` (kWh godišnje za 1 kWp), nagib `inputs.mounting_system.fixed.slope.value`.
- Ograničenja: 30 zahtjeva u sekundi po IP adresi; pozivi iz preglednika (AJAX) nisu dopušteni, pa poziva poslužitelj i predmemorira rezultat po koordinatama zaokruženima na 0,01°.
- Uvjeti: podaci su besplatni za javnu upotrebu uz navođenje izvora („PVGIS © European Communities, 2001-2026”).
- Rezervni plan: izostaviti uz napomenu (sučelje prikazuje „Nema podataka” ako servis ne odgovori).

### OpenStreetMap i Valhalla
- Izvadak: https://download.geofabrik.de/europe/croatia-latest.osm.pbf (≈ 201 MB).
- Licenca: ODbL 1.0, © suradnici OpenStreetMapa.
- Usmjerivač: Valhalla 3.9.1 (`ghcr.io/valhalla/valhalla-scripted:3.9.1`, MIT), pješački profil uz brzinu 4,5 km/h.
- Oznake: trgovine `shop=supermarket|convenience|greengrocer`; igrališta `leisure=playground`; parkovi `leisure=park`; ljekarne `amenity=pharmacy`; liječnici `amenity=doctors`; vrtići `amenity=kindergarten`; škole `amenity=school`; reciklaža `amenity=recycling`; stajališta `highway=bus_stop`, `public_transport=platform` + `bus=yes`, `railway=tram_stop|halt|station`; prometnice `highway=motorway|trunk|primary`, pruge `railway=rail`.

### MZOM: Registar dječjih vrtića i osnovne škole
- Vrtići: https://data.gov.hr/ckan/dataset/djecji-vrtici (CSV, 885 redaka: `Naziv, Adresa, Mjesto, ePosta, Telefon, Zupanija, PostanskiBroj`).
- Škole: https://data.gov.hr/ckan/dataset/osnovne-skole (CSV, 926 redaka; samo matične škole, bez područnih).
- Licenca: Otvorena dozvola RH.
- Bez koordinata: geokodiraju se vlastitim geokoderom nad DGU adresama. Registar vrtića navodi pravne osobe, a ne sve objekte, pa se dopunjuje OSM-om i podacima Grada Zagreba.
- Zagreb: Geoportal dječji vrtići (CC BY 4.0, 323 objekta s koordinatama) i Geoportal osnovne škole (Otvorena dozvola, 177 točaka).
- Rezervni plan: OSM `amenity=kindergarten`, `amenity=school`.

### HZZO: ugovorne ordinacije i ljekarne
- Opća/obiteljska medicina: https://hzzo.hr/sites/default/files/web_opca_092026_0.xlsx (2.274 tima).
- Pedijatrija: https://hzzo.hr/sites/default/files/web_ped_092026_0.xlsx (282 tima).
- Ljekarne: https://hzzo.hr/sites/default/files/inline-files/Popis%20ugovorenih%20ljekarni%20u%20RH_1.xls (zadnja izmjena 28. 9. 2023.).
- Izvorna stranica: https://hzzo.hr/zdravstvena-zastita/zdravstvena-zastita-pokrivena-obveznim-zdravstvenim-osiguranjem/ugovoreni
- Licenca nije navedena. Riječ je o javno objavljenim informacijama tijela javne vlasti; koristimo samo adrese ordinacija i ljekarni, bez imena liječnika (vidi `docs/ODLUKE.md`).
- robots.txt dopušta `/sites/default/files/`.
- Rezervni plan: OSM `amenity=doctors`, `amenity=pharmacy`.

### Javni prijevoz
- ZET GTFS: https://zet.hr/gtfs-scheduled/latest; licenca: Otvorena dozvola RH (https://www.zet.hr/odredbe/datoteke-u-gtfs-formatu/669). Dani prometa samo u `calendar_dates.txt`.
- HŽPP GTFS: https://www.hzpp.hr/GTFS_files.zip (poveznica na Portalu, `…/Media/Default/GTFS/GTFS_files.zip`, vraća 404). Licenca nije navedena; opis skupa na Portalu kaže da se podaci objavljuju kako bi ih javnost mogla „koristiti za izradu aplikacija ili ostala istraživanja”. Vozni red vrijedi do 13. 12. 2026.
- Autotrolej: https://data.gov.hr/ckan/dataset/at-vozni-redovi, vozni red radnim danom `http://e-usluge2.rijeka.hr/OpenData/ATvoznired-tjedan.json`; licenca CC BY 4.0. GTFS na `gt.autotrolej.hr` ima istekao TLS certifikat i ne koristi se.
- Šibenik (Gradski parking) objavljuje GTFS bez navedene licence; ne koristi se.
- Split, Osijek, Zadar, Pula i Dubrovnik nemaju javno dostupan GTFS: prikazuju se stajališta iz OSM-a s oznakom „bez voznog reda”.

### Reciklaža
- CKAN pretraga Portala („reciklažno dvorište”, „zeleni otok” …) vraća 35 skupova; samo 13 ima koordinate. Detaljni nalazi su u `docs/KVALITETA_PODATAKA.md`.
- Osnova je OSM `amenity=recycling`, dopunjena općinskim skupovima s koordinatama.

### OpenFreeMap
- Stilovi: https://tiles.openfreemap.org/styles/positron (svijetli) i https://tiles.openfreemap.org/styles/dark (tamni), bez ključa.
- Atribucija: „OpenFreeMap © OpenMapTiles Data from OpenStreetMap”.
- Uvjeti: https://openfreemap.org/tos/

### Pragovi i reference
- WHO Global Air Quality Guidelines (2021): https://iris.who.int/handle/10665/345329 — godišnje PM2,5 5 µg/m³, NO2 10 µg/m³ (tablica 0.1).
- Direktiva (EU) 2024/2881 (CELEX 32024L2881), Prilog I., tablica 1: granične vrijednosti od 1. 1. 2030. — godišnje PM2,5 10 µg/m³, NO2 20 µg/m³.
- WHO Environmental Noise Guidelines for the European Region (2018): https://iris.who.int/handle/10665/279952 — cestovni promet 53 dB Lden, 45 dB Lnight.
- Pravilo 3-30-300: Konijnendijk, C. C. (2023). Evidence-based guidelines for greener, healthier, more resilient neighbourhoods: Introducing the 3–30–300 rule. Journal of Forestry Research 34, 821–830. https://doi.org/10.1007/s11676-022-01523-z
