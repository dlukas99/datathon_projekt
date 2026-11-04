# Strojno učenje: preciznija procjena zraka na razini ulice?

## Pitanje

Aplikacija za zrak prikazuje godišnji prosjek iz EEA karte na mreži od 1 km. Ta karta prikazuje pozadinsku razinu, a provjera uz službene postaje (vidi [METODOLOGIJA.md](METODOLOGIJA.md)) pokazala je da su prometne postaje NO2 i do 17 µg/m³ iznad karte. Pitanje je može li model strojnog učenja, uz lokalne značajke koje aplikacija ionako zna za svaku adresu, procijeniti godišnji prosjek bolje od same karte.

## Zašto baš ova primjena

Razmotrili smo i druge mogućnosti:
- **Procjena polazaka javnog prijevoza tamo gdje nema voznog reda:** treniranje na Zagrebu i Rijeci, primjena na Split i Osijek. Odbačeno: sustavi su previše različiti, a procjena bi se prikazivala kao činjenica o voznom redu.
- **Strojno uparivanje adresa iz registara:** postojeće uparivanje već uspijeva u 86–95 % slučajeva, a za učenje nema označenih primjera.

Procjena zraka je jedina primjena koja ima službenu „istinu” za provjeru (mjerne postaje) i jasnu osnovu za usporedbu (EEA karta). Zato je to pošten test.

## Podaci i model

- **Cilj:** godišnji prosjek 2024. na službenim postajama u Hrvatskoj (verificirani podaci E1a, EEA Air Quality Download Service): 18 postaja za PM2,5 i 16 za NO2 (`ingest/stations.py`).
- **Osnova (ono što aplikacija prikazuje):** vrijednost EEA karte za 2024. na lokaciji postaje.
- **Značajke** (sve su poznate i za bilo koju adresu):
  - vrijednost EEA karte;
  - udaljenost od najbliže autoceste, brze, glavne ili važnije ceste (OSM);
  - udio izgrađenih površina i drveća u krugu od 300 m (ESA WorldCover);
  - logaritam broja stanovnika naselja (DZS).
- **Modeli:** svi predviđaju odstupanje postaje od karte, a procjena je karta plus predviđeno odstupanje:
  - korekcija prosječnog odstupanja;
  - linearna regresija;
  - Random Forest (300 stabala, najmanje 2 uzorka u listu).
- **Provjera:** leave-one-station-out. Svaka postaja predviđa se modelom koji je nikad nije vidio. Mjere su RMSE, MAE i pristranost u µg/m³.
- **Pravilo odluke** (određeno prije izračuna): model ulazi u aplikaciju samo ako je RMSE niži od osnove i za PM2,5 i za NO2.

## Rezultati

| Tvar | Postaja (n) | Model | RMSE | MAE | Pristranost |
|---|---|---|---|---|---|
| PM2,5 | 18 | EEA karta (osnova) | 1,73 | 1,39 | +0,52 |
| PM2,5 | 18 | EEA + prosječno odstupanje | 1,75 | 1,39 | -0,00 |
| PM2,5 | 18 | Linearna regresija | 1,84 | 1,42 | +0,04 |
| PM2,5 | 18 | Random Forest | 1,96 | 1,49 | -0,07 |
| NO2 | 16 | EEA karta (osnova) | 4,91 | 3,41 | -1,72 |
| NO2 | 16 | EEA + prosječno odstupanje | 4,90 | 3,60 | -0,00 |
| NO2 | 16 | Linearna regresija | 6,35 | 5,05 | -0,05 |
| NO2 | 16 | Random Forest | 4,17 | 2,87 | -0,28 |

- PM2,5: RMSE osnove 1,73, Random Forest 1,96 µg/m³ (+13 %).
- NO2: RMSE osnove 4,91, Random Forest 4,17 µg/m³ (-15 %).

**Odluka:** model ne ulazi u aplikaciju; ostaje vrijednost EEA karte.

## Tumačenje

- **NO2:** Random Forest smanjuje pogrešku za oko 15 %. Uz udaljenost od prometnice i izgrađenost, model djelomično hvata ono što karta od 1 km ne vidi: veći NO2 uz ulice. Rezultat je obećavajući, ali počiva na samo 16 postaja, od kojih su četiri prometne, pa nije dovoljno stabilan za prikaz korisnicima.
- **PM2,5:** nijedan model nije bolji od karte. PM2,5 je ravnomjernije raspoređen (veliki udio dolazi od grijanja i daljinskog prijenosa), a karta EEA-e uz te iste postaje već je kalibrirana. Zato je osnova ovdje teško nadmašiva.
- **Ograničenje:** EEA karte izrađene su i uz pomoć ovih postaja, pa osnova ima prednost koja nije neovisna. Uz tako malo postaja svaki pojedinačni rezultat treba uzeti s oprezom.

## Odluka

Prema unaprijed određenom pravilu **model ne ulazi u aplikaciju**. Aplikacija prikazuje vrijednost EEA karte, a ograničenje uz prometne ulice opisuje napomenom u kartici zraka i zasebnom kategorijom „Promet u blizini”.

## Daljnji razvoj

Za stabilniji model NO2 trebalo bi:
- uključiti gradske mjerne mreže koje nisu u verificiranom europskom skupu i postaje susjednih zemalja (s istim značajkama izvan Hrvatske);
- dodati podatke o prometnom opterećenju cesta.

## Ponavljanje

```powershell
cd backend
uv run python -m ingest.stations   # godišnji prosjeci postaja
uv run python -m analysis.ml_air   # ova tablica
```

Biblioteka: scikit-learn (BSD-3-Clause), samo u grupi za obradu podataka; nije dio API-ja.
