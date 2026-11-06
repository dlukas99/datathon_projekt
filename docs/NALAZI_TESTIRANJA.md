# Nalazi testiranja i popravci

Tester je 6. 11. 2026. prijavio osam problema. Za svaki je prvo istraženo gdje je u kodu, što je stvarni uzrok, kako ga popraviti, koliko je to zahtjevno i što se time može pokvariti. Popravci su zatim napravljeni redom, od najlakšeg prema težem, svaki u zasebnom commitu. Ono što ovisi o vanjskim podacima, licenci ili ključu nije napravljeno; to je opisano kao prijedlog.

| # | Problem | Uzrok ukratko | Procjena | Stanje |
|---|---|---|---|---|
| 1 | Skočni prozor „Pogledaj oglase” ne zatvara se | element `<details>` zatvara se samo ponovnim klikom na gumb | lako do srednje | planirano |
| 2 | Pretraga ne pronalazi neke ulice i kućne brojeve | slovo uz kućni broj gubilo se pri obradi; upit bez zareza, s poštanskim brojem ili gradom umjesto naselja nije se prepoznavao | srednje do teško | planirano |
| 3 | Gornji izbornik zbunjuje | početni ekran nema stavku u izborniku; „Pronađi mjesto” zvuči kao pretraga | lako do srednje | planirano |
| 4 | Informacija o internetu | podaci HAKOM-a postoje, ali nisu objavljeni pod otvorenom licencom | ovisi o vanjskim podacima | samo izvještaj |
| 5 | „Promet u blizini” je nelogičan | popis mjeri od središta naselja, kartica od adrese; naziv „Promet u blizini (100/100)” zvuči kao mnogo prometa; nejasne vrste cesta | srednje | planirano |
| 6 | Prikaz kvalitete zraka je prekompliciran | dvije ljestvice s oznakama i ocjena „Niska” koja zvuči kao loša kvaliteta | lako | napravljeno |
| 7 | Sumnja na netočne podatke o zelenilu | podaci su u redu, ali nije objašnjeno što se broji; „toplina” se ne mjeri | lako; bolji izvori ovise o vanjskim podacima | planirano |
| 8 | Asistent uvijek daje isti odgovor | bez ključa za jezični model pitanje bez prepoznate teme dobiva uvijek isti sažetak | srednje; jezični model ovisi o ključu | planirano |

Redoslijed rada: 6, 7, 1, 8, 3, 5, 2. Točka 4 ostaje izvještaj.

## 1. Skočni prozor „Pogledaj oglase” ne zatvara se

- **Gdje:** `frontend/src/components/ListingLinks.tsx` (komponenta `ListingLinks`), na karticama prijedloga u `FindPage.tsx` i u zaglavlju izvještaja u `ReportPage.tsx`; stil `.listings` u `index.css`.
- **Uzrok:** prozor je HTML element `<details>` sa `<summary>` kao gumbom. Takav element zatvara se samo ponovnim klikom na „Pogledaj oglase”. Klik izvan prozora i tipka Esc ne rade ništa, a ploča je postavljena preko sadržaja ispod sebe i pokriva sljedeće kartice. Polja filtara su stanje svake kartice posebno.
- **Prijedlog:** pravi gumb s `aria-expanded` i ploča kojom upravlja React:
  - zatvara se klikom izvan ploče, tipkom Esc, ponovnim klikom na gumb i kad fokus tipkovnicom izađe iz ploče (inače bi ploča pokrila element s fokusom);
  - ne zatvara se klikom unutar ploče ni dok je otvoren padajući izbornik;
  - nakon zatvaranja tipkom Esc ili klikom na prazno fokus se vraća na gumb.
- **Odluka: filtri su zajednički za sva mjesta.** „Što”, „Kako”, cijena i površina opisuju što korisnik traži, a ne mjesto. Na popisu prijedloga korisnik uspoređuje mjesta s istim uvjetima, pa bi ponovno upisivanje kod svakog mjesta bilo zamorno i podložno greškama. Zajedničke vrijednosti vrijede i na izvještaju otvorenom s popisa. Čuvaju se samo dok je stranica otvorena (u memoriji, ne u pregledniku), u skladu s pravilom da se upisi ne spremaju.
- **Procjena:** lako do srednje.
- **Rizici:** Esc na izvještaju već briše pješački put na karti; prozor mora obraditi Esc prvi i zaustaviti ga. Padajući izbornik ponaša se različito po preglednicima: u Chromiumu je provjereno automatski, u drugima ručno.

## 2. Pretraga adresa ne pronalazi sve ulice i kućne brojeve

- **Gdje:**
  - `backend/ingest/dgu.py`, funkcija `addresses`: obrada skupa „Adrese INSPIRE” u `data/processed/addresses.parquet`;
  - `backend/app/geocode.py`, `Geocoder.search` i `_match_streets`: pretraga, `GET /api/geocode`;
  - `frontend/src/components/AddressSearch.tsx`: polje za pretragu.
- **Geokoder:** vlastiti, bez vanjskog servisa, nad 1.683.411 adresa Državne geodetske uprave (ATOM preuzimanje, Otvorena dozvola RH). Vraća do 8 prijedloga. Upit i adrese normaliziraju se: mala slova, bez dijakritika, `đ` i `dj` kao `d`. Riječi „ulica”, „ul.” i „u” zanemaruju se. Zarez dijeli ulicu i broj od mjesta.
- **Polje za pretragu:** čeka 200 ms nakon tipkanja, traži barem 3 znaka i prekida prethodni upit, pa stariji odgovor ne može prepisati noviji. Dva nedostatka:
  - poruku „Nema prijedloga” čuju samo čitači zaslona, a ostali korisnici ne vide ništa;
  - Enter odmah nakon tipkanja može odabrati prijedlog za prethodni, kraći upit.
- **Mjerenje:** `scripts/geocode_check.py` pretražuje 24 stvarne adrese osnovnih škola iz registra Ministarstva znanosti, obrazovanja i mladih: veliki grad, manji grad, selo i otok, s kućnim brojem i bez njega, u oblicima u kojima ih ljudi pišu. Prije popravka: **12 od 24 točno, za 12 nije bilo nijednog prijedloga.**

| Uzrok | Primjeri iz testa | Objašnjenje |
|---|---|---|
| slovo uz kućni broj | „Gundulićeva 23 A, Zagreb”, „Drinska 12/B, Osijek”, „Sveti Martin pod Okićem 37b”, „Gora 61 a” | Obrada je uzimala samo prvi dio oznake (`addressNumber`), a slovo (`addressNumberExtension`) i podbroj (`addressNumber2ndExtension`) odbacivala. U prvih 401.839 adresa skupa 60.030 ima slovo, a 7.139 podbroj. Takvu adresu nije bilo moguće pronaći, a upit „23” mogao je vratiti položaj zgrade 23A. |
| upit bez zareza | „Ivana Rendića 6 Rijeka”, „Bartola Kašića 48 Vinkovci” | Naziv mjesta tumačio se kao dio naziva ulice. |
| poštanski broj ili država | „Brune Bušića 30, 21000 Split”, „Omladinska 11, 51550 Mali Lošinj, Hrvatska” | Mjesto se uspoređivalo kao tekst, pa „21000 split” nije počinjao s „split”. |
| grad ili općina umjesto naselja | „Banjol 10, Rab” | Adresa je u naselju Banjol (Grad Rab), a mjesto se uspoređivalo samo s nazivom naselja. |
| podbroj | „1. ulica 25/2, Blato” | „2” se tumačio kao kućni broj, a „25” kao dio ulice. |
| adresa koje nema u registru | „Jelsa 161” | U skupu DGU-a nema kućnog broja 161 u Jelsi. Nije bilo zamjenskog prijedloga (ulica ili naselje). |

  Dijakritici, „ul.” i „Ulica”, rimski brojevi („Pape Ivana Pavla II.”) i brojevi u nazivu ulice („Šetalište 20. travnja”) već su radili. Upit u kojem broj dolazi prije ulice nije podržan i nije u testu, jer se u Hrvatskoj tako ne piše.

- **Prijedlog:**
  1. U obradi spojiti broj, slovo i podbroj (23A, 25/2) i ponovno obraditi adrese iz već preuzete datoteke.
  2. U pretrazi prepoznati kućni broj sa slovom ili podbrojem i oznaku „bb”; maknuti poštanski broj i „Hrvatska”; prepoznati mjesto i bez zareza; prihvatiti naselje, grad ili općinu i poštanski broj.
  3. Postupna zamjena: ako kućnog broja nema, prijedlog je ulica, a ako ni ulice nema, naselje. Uz takav prijedlog jasno piše što je pronađeno.
  4. U polju za pretragu vidljiva poruka kad nema prijedloga, a Enter uvijek bira prijedlog za upisani tekst.
- **Drugi pružatelj:** nije potreban. Javni Nominatim po pravilima korištenja ne dopušta pretragu dok korisnik tipka. Pružatelji nad OpenStreetMapom (Nominatim, Photon) oslanjaju se na OSM, koji za Hrvatsku ima 268.457 adresa s kućnim brojem (naš izvadak), a DGU 1.683.411. Službeni adresni podaci DGU-a već se koriste; problem nije bio u izvoru nego u obradi i tumačenju upita. Komercijalni geokoderi traže ključ i plaćanje.
- **Procjena:** srednje do teško (obrada adresa, pretraga, sučelje, ponovna obrada podataka).
- **Rizici:** nova adresna tablica pri sljedećem `make data` mijenja i geokodiranje registara (vrtići, škole, liječnici, ljekarne) jer se adrese sa slovom tada pronalaze točno. Opuštenije prepoznavanje mjesta može ponuditi istoimenu ulicu u drugom naselju; zato se prednost daje rezultatima u upisanom mjestu. Obrađene podatke na poslužitelju treba ponovno prenijeti.

## 3. Preuređenje gornjeg izbornika

- **Gdje:** `frontend/src/App.tsx` (zaglavlje, rute i naslovi stranica), `pages/HomePage.tsx` (ulazi na naslovnici), `pages/FindPage.tsx` (nadnaslov), `index.css` (`.site-nav`), e2e testovi te README i dokumentacija.
- **Uzrok:** početni ekran nema stavku u izborniku; do njega vodi samo logo. „Pronađi mjesto” vodi na prijedloge naselja, ali zvuči kao pretraga s početnog ekrana. Posebnog mobilnog izbornika nema: na uskom zaslonu skraćuju se nazivi, a „O alatu” se skriva.
- **Prijedlog:** Dobro mjesto (logo) · **Provjeri adresu** · **Predloži mjesto** · Usporedi · O alatu · tema.
  - **„Provjeri adresu” umjesto „Istraži mjesto”:** tako se već zove okvir za pretragu na početnom ekranu, pa naziv u izborniku odgovara onome što korisnik vidi kad klikne. Naziv opisuje radnju: upišete adresu i dobijete izvještaj. Uz to se „Istraži mjesto” i „Predloži mjesto” razlikuju samo glagolom, a upravo takvu zamjenu tester je prijavio.
  - Aktivna stavka označena je za trenutačnu stranicu; „Provjeri adresu” je aktivna i na izvještaju.
  - Ruta `/pronadi` postaje `/predlozi`, a stara adresa preusmjerava na novu i zadržava parametre. Usklađeni su nadnaslov, naslovi stranica, ulaz na naslovnici i dokumentacija.
  - Na zaslonu užem od 760 px stavke su u izborniku iza gumba „Izbornik” jer četiri stavke i gumb za temu ne stanu u 320 px.
- **Procjena:** lako do srednje.
- **Rizici:** poveznice i oznake na `/pronadi` (dokumentacija, scenarij videa) treba uskladiti; preusmjeravanje čuva stare poveznice.

## 4. Informacija o pokrivenosti internetom

- **Postoji li nešto slično:** ne. U kodu i podacima nema ničega o internetu ni mobilnom signalu.
- **Mogući izvori:**

| Izvor | Što sadrži | Licenca | Smijemo li koristiti | Preciznost | Svježina |
|---|---|---|---|---|---|
| HAKOM, interaktivni portal (ekarta.hakom.hr), sloj „Dostupnost širokopojasnog pristupa” | nepokretni pristup po razredima brzine (od 0–2 Mbit/s do ≥ 10 Gbit/s) i broj operatora | nije navedena; nije objavljen kao otvoreni podatak | ne bez dopuštenja HAKOM-a (pravilo 3) | područja (poligoni) | nije navedena |
| HAKOM, isti portal, karte pokrivenosti i korisnička mjerenja | izmjerene brzine preuzimanja i slanja te kašnjenje za A1, HT i Telemach po tehnologiji (2G, 3G, 4G, 5G), za zadnji mjesec, 3 i 6 mjeseci te 1 i 2 godine | nije navedena | ne bez dopuštenja HAKOM-a | pojedinačna mjerenja s koordinatama | zadnji mjesec |
| HAKOM na data.gov.hr: namjere gradnje svjetlovodne mreže (WFS) | planirane, ne postojeće mreže | Otvorena dozvola RH | da, ali ne govori o dostupnosti danas | područja | 15. 4. 2026. |
| HAKOM na data.gov.hr: popis odašiljača (WFS) | radijski i televizijski odašiljači (DAB+, DVB-T2) | Otvorena dozvola RH | da, ali nije mobilna mreža | točke | 30. 4. 2026. |
| Ookla Open Data | prosječna brzina i kašnjenje, nepokretna i pokretna mreža odvojeno | CC BY-NC-SA 4.0 | ne: licenca je samo za nekomercijalnu upotrebu, kao i karte buke EEA-e koje smo zato odbacili | pločice od oko 430 m u Hrvatskoj (razina 16) | tromjesečno |
| M-Lab | pojedinačna mjerenja brzine | CC0 | da | razina grada (lokacija prema IP adresi) | stalno |
| operateri (A1, Hrvatski Telekom, Telemach) | karte pokrivenosti | vlasničke | samo poveznica | — | — |

- **Zaključak:** jedini izvor koji odgovara na pitanje za adresu (optika, 4G i 5G, izmjerena brzina) je HAKOM, a njegovi slojevi nisu objavljeni pod otvorenom licencom. Otvoreni izvori su planovi gradnje, odašiljači za radio i televiziju te mjerenja na razini grada, pa ne odgovaraju na pitanje.
- **Što bi trebalo:** zatražiti od HAKOM-a objavu slojeva dostupnosti i pokrivenosti na data.gov.hr (kao što je već objavio dva skupa) ili pisano dopuštenje za korištenje.
- **Kako bi izgledalo u sučelju:** nova kartica „Internet i mobilni signal” u skupini „Svakodnevni život”, istog izgleda kao ostale, sa statusom „Informacija” (bez ocjene, jer nema općeprihvaćenog praga):
  - „Nepokretni internet: do 1 Gbit/s, 3 operatora”;
  - „Mobilna mreža u krugu od 500 m, zadnjih 6 mjeseci: 4G medijan X Mbit/s iz N mjerenja, 5G …”;
  - izvor HAKOM, vrsta „izmjereno”, datum i poveznica na portal.
- **Procjena:** ovisi o vanjskim podacima. Ništa nije napravljeno s procijenjenim podacima.

## 5. „Promet u blizini” je nelogičan

- **Gdje:**
  - `backend/ingest/osm.py`: izdvajanje cesta i pruga u `osm_noise_lines.parquet`;
  - `backend/analysis/environment.py`, `noise_category`: izračun i tekst;
  - `backend/analysis/score.py`, `_traffic`: podskor;
  - `backend/app/finder.py`, `_reasons`: „Najjače” i „Najslabije”;
  - `config/profiles.json`: nazivi u skoru.
- **Podaci:** OpenStreetMap, ceste `highway=motorway|trunk|primary|secondary` i pruge `railway=rail` bez sporednih kolosijeka.
- **Što je „važnija” cesta:** u sučelju je `primary` „glavna”, a `secondary` „važnija” cesta. Prema hrvatskim pravilima označavanja u OSM-u (wiki „Croatia/Ceste”):
  - `motorway` je autocesta;
  - `trunk` je brza cesta;
  - `primary` je državna cesta (oznaka D);
  - `secondary` je županijska cesta ili bivša županijska cesta u gradu;
  - `tertiary` je lokalna cesta.

  U našim podacima 19.042 dionice `primary` imaju oznaku D, a 16.463 dionice `secondary` četveroznamenkastu oznaku županijske ceste. Sporedne ulice nisu uključene; `secondary` je uključen jer su glavne gradske prometnice tako označene (odluka od 2. 11.).
- **Od čega i do čega se mjeri:** zračna udaljenost od točke izvještaja do najbliže točke osi ceste, ne do čvora. Točka je adresa ili središte naselja, ovisno o tome što je otvoreno.
- **Kako se udaljenost pretvara u skor:** do 300 m daje 25, od 300 do 500 m 60, a dalje od 500 m 100 (pojasevi prema pregledu HEI-ja iz 2010.). **100/100 znači „daleko od velikih prometnica”**, a smjer je isti u svim kategorijama: više je povoljnije.
- **Zašto se popis i kartica razlikuju:** popis „Predloži mjesto” računa za središte naselja (OSM čvor `place`), a izvještaj za odabranu adresu. Za Split središte je 530 m od najbliže državne ceste (podskor 100), a adresa uz tu cestu može biti 10 m od nje. Obje brojke su točne, ali za različite točke. Zbunjuje i naziv: „Promet u blizini (100/100)” zvuči kao mnogo prometa.
- **Je li „10 m” stvarno:** točke adresa DGU-a leže na zgradi, a zgrada uz cestu udaljena je od osi ceste nekoliko metara (pola kolnika i nogostup). Za središta naselja često je 0 m jer OSM čvor `place` leži na samoj cesti (Osijek, Zadar). Provjera na adresama javnih ustanova: vidi stanje točke.
- **Prijedlog:**
  - vrste cesta iz oznaka: „autocesta A1”, „brza cesta”, „državna cesta D8”, „županijska cesta Ž2001”, a dionica bez oznake je „županijska ili glavna gradska cesta”;
  - tekst „od lokacije” umjesto „od adrese”, jer točka može biti i središte naselja;
  - kategorija se zove „Udaljenost od prometnica”: tada 100/100 znači „daleko”, a podnaslov kaže koje se ceste broje.
- **Procjena:** srednje.
- **Rizici:** promjena naziva kategorije mijenja tekstove u zlatnim testovima, profilima i dokumentaciji. Vrijednosti, pojasevi i podskorovi ostaju isti.

## 6. Prikaz kvalitete zraka je prekompliciran

- **Gdje:** `backend/analysis/environment.py` (kategorija `air`), `frontend/src/components/CategoryCard.tsx` (kartica), `docs/METODOLOGIJA.md`.
- **Uzrok:** kartica odjednom prikazuje dvije ljestvice (PM2,5 i NO2) s po tri oznake granica i rečenicu s razinom. Oznaka statusa „Niska” odnosi se na onečišćenje, ali uz naslov „Kvaliteta zraka” čita se kao „niska kvaliteta”.
- **Prijedlog:**
  - ocjena kvalitete zraka bojom i riječju: „Vrlo dobar”, „Dobar”, „Umjeren” ili „Loš”;
  - jedna rečenica što to znači kroz godinu;
  - ljestvice, brojke i izvor u „Detalji i izvor”.
- **Pragovi:** ostaju isti, službeni i s izvorom:
  - smjernica Svjetske zdravstvene organizacije iz 2021.;
  - granične vrijednosti EU-a za 2030. i današnje, iz Direktive (EU) 2024/2881.

  Europski indeks kvalitete zraka (EEA) ne koristi se: od revizije 2024. računa se iz satnih koncentracija i opisuje kratkotrajan rizik, a naše karte su godišnji prosjeci.
- **Procjena:** lako.
- **Rizici:** mijenjaju se oznaka i rečenica u zlatnim testovima; status i podskor ostaju isti.
- **Stanje: napravljeno.**
  - Kartica pokazuje ocjenu (npr. „Umjeren”) i jednu rečenicu, na primjer: „Kroz godinu je zrak ovdje umjereno onečišćen: prosjek je unutar granice EU-a koja vrijedi danas, ali iznad strože granice za 2030.”
  - Ljestvice, brojke, izvor i objašnjenje ocjene su u „Detalji i izvor”.
  - Razine onečišćenja ostale su ključevi za skor i tražilicu mjesta; skor sada razinu čita iz ljestvica, a ne iz natpisa.
  - Filtar zraka u „Predloži mjesto” nudi „Umjeren ili bolji” i „Dobar ili bolji”.
  - Za šest demo adresa statusi i podskorovi su isti kao prije (Split 80, ostale 50).

## 7. Toplina i zelenilo: sumnja na netočne podatke

- **Gdje:** `backend/analysis/environment.py` (`read_landcover`, `green_category`), `backend/analysis/score.py` (`_green`), `backend/app/finder.py` (činjenica „Drveće pokriva … okolice središta”).
- **Izvor:** ESA WorldCover 2021 v200, rezolucija 10 m, i parkovi iz OpenStreetMapa (`leisure=park`).
- **Što se broji:** udio piksela razreda „drveće” u krugu od 300 m od točke izvještaja (adresa ili središte naselja). Zelene površine su drveće, grmlje, travnjaci i močvare; izgrađeno je razred „izgrađeno”.
- **More i voda:** **ne ulaze u nazivnik.** Razred „vodene površine” izuzima se prije računanja udjela, pa obalna mjesta nisu zakinuta. Za Hvar bi udio s morom bio 15,4 %, a bez mora je 17,9 %.
- **„Toplina”:** ne računa se. Naziv kategorije obećava podatak o temperaturi kojeg nema; drveće i park služe kao pokazatelj hlada.
- **Skor:** do 60 bodova za udio drveća (30 % i više daje puni broj bodova) i do 40 bodova za park unutar 300 m (20 do 600 m). Za Split 11,1 % drveća daje 22 boda, a park unutar 300 m 40 bodova, ukupno 62/100.
- **Provjera na pet mjesta** (krug od 300 m oko središta naselja). Ortofoto DGU-a iz 2023. korišten je samo za provjeru i nije dio aplikacije.

| Mjesto | Vrsta | Drveće, WorldCover | Voda u krugu | Gustoća krošanja, HRL 2018. (EEA) | Ortofoto DGU-a 2023. |
|---|---|---|---|---|---|
| Split | obalni grad | 11,1 % | 0 % | 1,1 % | gusto izgrađeno staro središte, drveće u parku i pojedinačno u dvorištima |
| Osijek | kontinentalni grad | 30,6 % | 0 % | 3,6 % | mnogo drveća uz ulice i u parkovima |
| Požega | manje mjesto | 32,9 % | 0 % | 10,8 % | izgrađeno središte, šumovito brdo na rubu kruga |
| Nijemci | selo | 18,3 % | 8,6 % (rijeka) | 3,4 % | kuće s vrtovima, drveće uz rijeku |
| Hvar | otok | 17,9 % | 13,8 % (more) | 1,3 % | gusto izgrađeno središte, šumovito brdo iznad njega |

- **Zaključak:**
  - Brojke su ispravno izračunate iz izvora i u skladu su s ortofotom.
  - WorldCover u rezoluciji 10 m ne vidi pojedinačna stabla u dvorištima i uz ulice kad je oko njih izgrađeno. Zato je stvarni udio krošanja u gusto izgrađenim središtima i selima s vrtovima vjerojatno nešto veći.
  - Drugi otvoreni izvor iste rezolucije (Copernicus HRL Tree Cover Density) daje još manje vrijednosti, pa zamjena ne bi pomogla.
  - U šumi (Medvednica) i parku (Maksimir) oba izvora pokazuju pretežno drveće: WorldCover 93–98 %, HRL u prosjeku 69 %.
- **Prijedlog (bez novih podataka):**
  - kategorija „Zelenilo i hlad”, jer temperaturu ne mjerimo;
  - u rečenici i napomenama jasno: udio drveća u kopnu (bez mora), krug od 300 m od lokacije, satelitska karta rezolucije 10 m i njezino ograničenje;
  - na popisu „Predloži mjesto” „od središta naselja”.
- **Prijedlog uz nove podatke (traži odobrenje):**
  - karta visine krošanja rezolucije 1 m (npr. Meta i WRI, CC BY 4.0) za točniji udio drveća;
  - toplinski podaci (npr. površinska temperatura iz programa Copernicus) za stvarnu „toplinu”.
- **Procjena:** lako; bolji izvori ovise o vanjskim podacima.
- **Rizici:** promjena naziva kategorije mijenja tekstove u zlatnim testovima, profilima, README-u i scenariju videa. Vrijednosti i podskorovi ostaju isti.

## 8. AI asistent uvijek daje isti odgovor

- **Gdje:** `backend/app/assistant.py` (`understand_rules`, `understand_llm`, `answer`), `POST /api/assistant` u `backend/app/main.py`, `frontend/src/components/Assistant.tsx`.
- **Postoji li poziv jezičnom modelu:** da, ali neobavezan i samo za prepoznavanje teme pitanja: OpenAI-kompatibilni `/chat/completions` preko `httpx`, ključ iz `LLM_BASE_URL`, `LLM_API_KEY` i `LLM_MODEL`. Model nikad ne piše odgovor; odgovor se slaže iz predložaka nad izvještajem (CLAUDE.md, odjeljak 9).
- **Je li ključ postavljen:** nije (`.env` ima prazne `LLM_*`), pa radi način bez modela, s prepoznavanjem ključnih riječi.
- **Uzrok „istog odgovora”:**
  - pitanje bez ijedne prepoznate riječi (npr. „Kakva je okolina?”, „Je li sigurno?”, „Gdje je bolnica?”, „Koliko ima stanovnika?”) dobiva uvijek isti odgovor, sažetak izvještaja i „Pitajte me konkretnije”;
  - to izgleda kao da asistent ne čita pitanje.
- **Što je provjereno:**
  - pitanje se šalje modelu ili pravilima ispravno;
  - predmemorije odgovora nema;
  - lažnog (mock) ili demo načina rada nema;
  - pogreška modela prelazi na pravila, a ne na fiksni tekst;
  - pitanja s prepoznatom temom (zrak, zelenilo, buka, škola, poplave, vrtić, prijevoz) dobivaju različite, točne odgovore.
- **Prijedlog bez modela:**
  - pitanje koje asistent ne razumije dobiva iskren odgovor: što nije prepoznato i o čemu može odgovoriti;
  - teme o kojima podataka nema (bolnica, sigurnost, stanovništvo) dobivaju jasno „to ne znamo”;
  - sažetak samo za opća pitanja („Kakvo je ovo mjesto?”, „ukratko”);
  - sučelje kaže da asistent prepoznaje teme.
- **Prijedlog s jezičnim modelom (traži odobrenje i ključ):**
  - **Poziv samo iz backenda;** ključ nikad ne ide u frontend.
  - **Što model dobiva:** izvještaj za adresu kao JSON (vrijednosti, izvori, datumi, vrste) i upute da odgovara samo iz tih podataka, na hrvatskom, i da kaže kad nešto ne zna.
  - **Provjera brojki:** CLAUDE.md traži da brojke dolaze iz predložaka, a ne iz modela. Zato bi poslužitelj provjerio da se svaka brojka iz odgovora nalazi u podacima; ako se ne nalazi, vraća se odgovor iz predložaka. Ispod odgovora i dalje stoje činjenice s izvorom.
  - **Streaming:** odgovor se šalje dio po dio (Server-Sent Events).
  - **Ograničenja:** najviše N pitanja po IP adresi na sat, dnevni limit ukupnog broja poziva i najviše oko 500 tokena po odgovoru.
  - **Kad nešto ne radi:** jasna poruka, a odgovor se vraća iz predložaka; nikad izmišljen odgovor.
  - **Varijable:** postojeće `LLM_BASE_URL`, `LLM_API_KEY` i `LLM_MODEL` za OpenAI-kompatibilnog pružatelja; za Claude `ANTHROPIC_API_KEY` i službeni paket `anthropic` (nova ovisnost); nove `LLM_MAX_PER_HOUR` i `LLM_MAX_PER_DAY`.
  - **Modeli i cijene** (Anthropic, cjenik od 6. 10. 2026., za milijun tokena):

  | Model | Ulaz | Izlaz |
  |---|---|---|
  | Claude Haiku 5.5 | 0,10 $ | 0,50 $ |
  | Claude Sonnet 5.5 | 2 $ | 10 $ |
  | Claude Opus 5.5 | 4 $ | 20 $ |

  Uz pretpostavku od oko 5.000 tokena ulaza (izvještaj i upute) i 300 tokena odgovora, jedno pitanje stoji oko 0,00065 $ s Haikuom, 0,013 $ sa Sonnetom i 0,026 $ s Opusom. To je procjena, a ne izmjereni trošak. Izbor modela je vaša odluka.
- **Procjena:** srednje; jezični model ovisi o ključu i odobrenju.
- **Rizici:** odgovor modela može biti netočan ili izvan opsega, što ublažava provjera brojki; trošak i zlouporaba ublažavaju se ograničenjima.

## Kako ponoviti mjerenja

- Pretraga adresa: `cd backend && uv run python ../scripts/geocode_check.py` (treba `data/processed/addresses.parquet`).
- Zelenilo: brojke WorldCovera daje izvještaj za središte naselja (`/api/report`); HRL i ortofoto su provjereni ručno, preko javnih servisa EEA-e i DGU-a, uz razmak od barem sekunde između zahtjeva.
