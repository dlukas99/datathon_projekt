# Scenarij videa (do 3 minute)

**Priča:** obitelj razmišlja gdje živjeti u Vukovarsko-srijemskoj županiji. Prvo provjerava jednu adresu, zatim traži mjesta koja im odgovaraju i uspoređuje dvije lokacije. Kao primjer služe adrese javnih ustanova: gradska uprava Vinkovci (Bana Jelačića 1) i Općina Nijemci (Trg kralja Tomislava 6). Okolišni pregled je uvijek prvi.

**Priprema:**
- Pokrenite aplikaciju (lokalno ili javni demo) u pregledniku na 1280 × 800, u svijetloj temi, s uvećanjem od 110 %.
- Pripremite kartice:
  1. naslovnica;
  2. izvještaj za „Bana Jelačića 1, Vinkovci” s profilom „Obitelj s djecom”;
  3. „Predloži mjesto” s Vukovarsko-srijemskom županijom, vrtićem, školom i bez poplava;
  4. usporedba Vinkovci i Nijemci;
  5. karta (`/karta?sloj=air`);
  6. `/api/docs`.
- Snimke zaslona za montažu nalaze se u `docs/images/`. Ne prikazujte privatne adrese.

| Vrijeme | Slika | Govor (prijedlog) |
|---|---|---|
| 0:00–0:15 | naslovnica s četiri ulaza | „Gdje živjeti najveća je odluka u životu. Gledamo cijenu i kvadraturu, a poplave, zrak ili to možemo li bez auta otkrijemo tek kad uselimo. Ti podaci postoje, ali su rasuti po desetak institucija.” |
| 0:15–0:25 | upis „Bana Jelačića 1, Vinkovci”, odabir „Obitelj s djecom” | „Dobro mjesto daje okoliš i svakodnevni život za svaku adresu u Hrvatskoj. Upišem adresu i odaberem tko sam.” |
| 0:25–0:55 | izvještaj: Poplave, Kvaliteta zraka (ocjena), Zelenilo i hlad, Udaljenost od prometnica | „Prvo okoliš. Poplave iz karata JRC-a, uz poveznicu na Hrvatske vode; kad je adresa u poplavnom području, rizik vidim kao vjerojatnost u 30 godina kredita. Zrak ima jednu ocjenu, a granice WHO-a i EU-a su u detaljima, zelenilo prema pravilu 3-30-300, a promet prema udaljenosti od ceste. Uz svaku brojku su izvor i datum.” |
| 0:55–1:10 | Skor za život u zaglavlju, zatim ploča s klizačima | „Skor za život sažima sve kategorije prema mom profilu. Težine su vidljive i mogu ih mijenjati, a piše i što skor najviše podiže i spušta.” |
| 1:10–1:25 | Život bez auta: karta s izokronama, kvačice | „Hod se računa po stvarnim ulicama: što je na 5, 10 i 15 minuta i koliko od sedam svakodnevnih potreba imam bez auta.” |
| 1:25–1:50 | Predloži mjesto: filtri, rezultati s razlozima, „Otvori izvještaj” | „A ako još ne znam gdje? Zadam županiju, vrtić, školu i bez poplava, a aplikacija rangira 2.347 naselja i objasni zašto. Izračun je deterministički; jezični model smije samo pretvoriti moje pitanje u filtre.” |
| 1:50–2:05 | „Pogledaj oglase”, zatim usporedba Vinkovci i Nijemci | „Za odabrano mjesto otvaram pretragu oglasa; mi samo slažemo poveznicu. Dvije lokacije usporedim jednu uz drugu.” |
| 2:05–2:15 | Karta: sloj „Kvaliteta zraka”, klik na Vinkovce, kartica naselja | „Na karti vidim cijelu Hrvatsku, naselje po naselje: zrak, poplave, usluge ili prijevoz. Klik daje kratak pregled i put do punog izvještaja.” |
| 2:15–2:28 | asistent: „Gdje je bliže do vrtića?” | „Asistent odgovara samo iz izračuna i ne daje savjete o kupnji.” |
| 2:28–2:45 | stranica „Izvori”, metodologija (provjera zraka), `/api/docs` | „Koristimo 31 otvoreni skup podataka: Portal otvorenih podataka, DGU, DZS, Ministarstvo, HZZO, gradove, ZET, HŽPP, JRC, EEA, ESA, Copernicus i OpenStreetMap. Kartu zraka provjerili smo uz službene postaje, a Random Forest model pošteno usporedili s njom. Sve je dostupno kao REST API s OpenAPI opisom.” |
| 2:45–3:00 | naslovnica | „Kod je otvoren pod licencom EUPL. Dobro mjesto: okoliš i svakodnevni život za svaku adresu u Hrvatskoj.” |

**Napomene za snimanje:**
- Ukupno oko 425 riječi; govorite mirno, bez zastrašivanja.
- Tijekom videa natpis: „Informativni alat, nije službena procjena.”
- Ako demo URL još nije javan, snimite lokalno (upute u `docs/RAZVOJ.md`).
