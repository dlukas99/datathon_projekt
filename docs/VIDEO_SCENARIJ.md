# Scenarij videa (do 3 minute)

**Priča:** kupac bira između dviju lokacija u Vinkovcima. Kao primjer služe adrese javnih ustanova: gradska uprava (Bana Jelačića 1) i Općina Nijemci (Trg kralja Tomislava 6). Okolišni pregled je prvi, zatim usporedba, asistent i izvori.

**Priprema:**
- Pokrenite aplikaciju (`make dev` ili javni demo) u pregledniku na 1280 × 800, u svijetloj temi, s uvećanjem od 110 %.
- Pripremite kartice:
  1. naslovnica;
  2. izvještaj za „Bana Jelačića 1, Vinkovci”;
  3. usporedba s „Trg kralja Tomislava 6, Nijemci”;
  4. stranica „Izvori”;
  5. `/api/docs`.
- Snimke zaslona za montažu nalaze se u `docs/images/`.
- Ne prikazujte privatne adrese.

| Vrijeme | Slika | Govor (prijedlog) |
|---|---|---|
| 0:00–0:15 | naslovnica | „Kupnja doma je najveća odluka u životu. Gledamo cijenu i kvadraturu, a poplave, zrak ili to možemo li bez auta otkrijemo tek kad uselimo. Ti podaci postoje, ali su rasuti po desetak institucija.” |
| 0:15–0:25 | upis „Bana Jelačića 1, Vinkovci”, prijedlozi se pojavljuju | „Prije potpisa daje okolišni pregled za bilo koju adresu u Hrvatskoj. Upišem adresu i odaberem tko sam, npr. obitelj s djecom.” |
| 0:25–0:55 | izvještaj: sažetak i kartice Poplave, Kvaliteta zraka, Toplina i zelenilo | „Prvo okoliš. Lokacija nije u modeliranom poplavnom području; uz to je poveznica na službene karte Hrvatskih voda. Zrak uspoređujemo sa smjernicom WHO-a i graničnom vrijednošću EU-a za 2030. Zelenilo mjerimo satelitskom kartom ESA-e prema pravilu 3-30-300. Svaka brojka ima izvor, datum i oznaku je li izmjerena, modelirana ili procjena.” |
| 0:55–1:05 | kartice Buka i Sunce na krovu | „Buka je jasno označena kao procjena, a sunčana elektrana od jednog kilovata ovdje bi dala oko 1.250 kWh godišnje, prema JRC-ovu PVGIS-u.” |
| 1:05–1:25 | „Život bez auta”: karta s izokronama, „X od 7” | „Mreža hoda računa se po stvarnim ulicama. Na karti je dokle stignete za 5, 10 i 15 minuta, a ispod koliko od sedam svakodnevnih potreba imate bez auta: trgovinu, ljekarnu, liječnika, vrtić, školu, park i stajalište s polascima iz voznih redova.” |
| 1:25–1:35 | tablica „Svakodnevni život” | „Vrtići i škole dolaze iz registra Ministarstva, liječnici i ljekarne iz HZZO-a. Te registre bez koordinata sami smo geokodirali nad 1,7 milijuna adresa DGU-a.” |
| 1:35–1:55 | „Usporedi s drugom adresom” → usporedba s Nijemcima | „Dvije adrese jedna uz drugu. Nema skupne ocjene sa skrivenim težinama: vidite razlike i sami odlučujete. Profil mijenja samo redoslijed, nikad vrijednosti.” |
| 1:55–2:15 | asistent: „Gdje je bliže do vrtića?” | „Asistent odgovara samo iz izračuna. Brojke dolaze iz predložaka, pa ih jezični model ne može izmisliti. Na pitanje treba li kupiti kuću ne odgovara.” |
| 2:15–2:35 | stranica „Izvori”, zatim `/api/docs` | „Koristimo 28 otvorenih skupova podataka i PVGIS API: Portal otvorenih podataka, DGU, Ministarstvo, HZZO, Grad Zagreb, ZET, HŽPP, Autotrolej, općine, JRC, EEA, ESA i OpenStreetMap. Datume osvježavanja provjeravamo uživo preko CKAN API-ja Portala, a nalaze o kvaliteti podataka vraćamo izdavačima. Sve je dostupno i kao REST API s OpenAPI opisom i GeoJSON-om.” |
| 2:35–2:50 | dijagram arhitekture iz README-a | „Arhitektura: FastAPI, Valhalla za mrežu hoda, React i MapLibre, a sve se diže jednom Docker Compose naredbom. Kod je otvoren pod licencom EUPL.” |
| 2:50–3:00 | naslovnica, logo | „Sljedeći koraci: obavijest kad se promijeni službena karta poplava i ugradnja u oglasnike nekretnina. Prije potpisa: provjerite okoliš prije nego potpišete.” |

**Napomene za snimanje:**
- Ukupno oko 400 riječi; govorite mirno, bez zastrašivanja.
- Na kraju, ili kao natpis tijekom cijelog videa: „Informativni alat, nije službena procjena.”
- Ako demo URL još nije javan, snimite lokalno (`make dev`).
