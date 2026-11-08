---
name: Prije potpisa
description: Okolišni pregled i pregled svakodnevnog života za bilo koju adresu u Hrvatskoj, kao ploča mjernih instrumenata.
colors:
  paper: "#f6f5f1"
  surface: "#ffffff"
  paper-2: "#ecebe5"
  ink: "#15171a"
  muted: "#55595f"
  hairline: "#dcdad2"
  control-border: "#7a7d82"
  link: "#1d4fc4"
  focus: "#1d4fc4"
  c-flood: "#1f55d0"
  c-air: "#6a46d1"
  c-green: "#18804a"
  c-noise: "#a85a00"
  c-fire: "#c4381a"
  c-solar: "#845800"
  c-solar-fill: "#f5b800"
  c-car-free: "#0b7480"
  c-transit: "#b02a6a"
  good: "#1d6b3a"
  good-bg: "#e1f0e4"
  warning: "#7a5300"
  warning-bg: "#fbefd0"
  bad: "#a3231c"
  bad-bg: "#fbe4e0"
  nodata: "#545a57"
  nodata-bg: "#e8e7e2"
  dark-paper: "#111316"
  dark-surface: "#181b1f"
  dark-paper-2: "#22262b"
  dark-ink: "#efede7"
  dark-muted: "#a9adb3"
  dark-hairline: "#2d3137"
  dark-link: "#8fb0ff"
  dark-c-flood: "#82a8ff"
  dark-c-air: "#b9a4ff"
  dark-c-green: "#6fd59b"
  dark-c-noise: "#ffb85c"
  dark-c-fire: "#ff8f6b"
  dark-c-solar: "#ffd04d"
  dark-c-car-free: "#5fd0da"
  dark-c-transit: "#ff8fc2"
typography:
  display:
    fontFamily: "'Instrument Serif', Georgia, serif"
    fontWeight: 400
    use: "h1, h2, velika očitanja instrumenata, skor"
  text:
    fontFamily: "'Instrument Sans Variable', system-ui, sans-serif"
    fontWeight: "400–700"
    use: "tekst, h3, gumbi, oznake"
rounded:
  sm: "8px"
  md: "14px"
spacing:
  container: "1160px"
  section: "3.5rem"
---

# Sustav dizajna: „Instrumenti”

**Creative North Star: „Ploča instrumenata za mjesto”.** Izvještaj se čita kao ploča mjernih uređaja: svaka okolišna kategorija ima svoj instrument koji pokazuje stvarnu vrijednost s adrese. Sve ostalo je papir i tinta, mirno i čisto, da očitanja budu ono što se vidi.

## Boje

- **Papir i tinta.** Podloga je topli papir (`paper`), ploče su bijele, tekst je tinta. Radnje (gumbi, odabrani čipovi, aktivna stavka navigacije) su u tinti, a poveznice plave.
- **Jedna boja po mjerenju.** Boja nikad nije ukras: gdje se pojavi, imenuje ono što se mjeri. Poplave kobaltna, zrak ljubičasta, zelenilo zelena, prometnice jantarna, požari crvenonarančasta, sunce zlatna, život bez auta tirkizna, javni prijevoz magenta. Iste boje nose naslovnica („Šest mjerenja okoliša”), traka ključnih očitanja na vrhu izvještaja, instrumenti i znak aplikacije (brojčanik u šest boja).
- **Status je zaseban.** Dobro, upozorenje, loše i nema podataka imaju svoje boje i uvijek ikonu i riječ. Boja kategorije nikad ne glumi status.
- **Karte** koriste žuto-zeleno-plavu ljestvicu u pet koraka (prema ColorBrewer YlGnBu), bez crveno-zelene presude; siva je „nema podataka”.

## Tipografija

Instrument Serif (jedna težina) za naslove i velika očitanja; Instrument Sans za sve ostalo. `font-synthesis: none` sprječava lažno podebljanje serifa. Brojke u tablicama su tabularne. Naslovnica koristi kurziv za jednu riječ („ovdje”) u boji poplava.

## Oblici

- **Ploča instrumenta:** bijela, tanka linija, kut 14 px, traka od 4 px u boji mjerenja na vrhu. U zaglavlju ikona u krugu boje mjerenja, naziv i status. Ispod: očitanje (velik serif, jedinica, jedna rečenica), crtež, rečenica iz predloška i „Detalji i izvor”.
- **Raspored:** mreža od 12 stupaca; poplave i zrak po pola širine, zelenilo, prometnica i požari po trećinu, sunce cijelom širinom. Na 980 px po dvije, na 680 px jedna ispod druge.
- **Vrh izvještaja:** adresa velikim serifom iznad crte od 2 px u tinti, skor kao očitanje u okviru, sažetak od dvije do tri rečenice i šest pločica ključnih očitanja (svaka u boji svog mjerenja, vodi na svoj instrument).

## Instrumenti (svi crteži su `aria-hidden`; brojke i rečenice uz njih nose značenje)

- **Poplave, vodomjer:** tri modelirana sloja vode (10, 100 i 500 godina), češći dublji; kuća stoji na razini prve poplave koja doseže adresu, ili iznad najviše. Uz crtež popis „adresa / do 100 m” po povratnom razdoblju.
- **Zrak, ravnala:** PM2,5 i NO2 s pragovima WHO-a i EU-a i iglom na godišnjem prosjeku; pritisak na ravnalo bira onečišćivač za veliko očitanje. Jedini izračun: omjer prema preporuci WHO-a.
- **Zelenilo, krug od 300 m:** stotinjak točkica zemljišta obojenih po udjelima drveća, ostalog zelenila i izgrađenog; prijelaz preko legende ističe njezine točkice.
- **Prometnica, ravnalo do 700 m** s područjima do 300 i 500 m.
- **Požari, radar kruga od 2 km:** broj opožarenih površina; položaji se ne crtaju.
- **Sunce, luk i panel** pod optimalnim nagibom, s godišnjom proizvodnjom po kW.

## Pokret

Jedan trenutak: kad instrument dođe u pogled, jednom se pomakne na vrijednost (voda se diže, igla klizi, točkice niču, crta se izvlači, radar prebriše, sunce se popne), eksponencijalnim usporavanjem. Mozaik naselja na naslovnici puni se od istoka prema zapadu. Uz `prefers-reduced-motion` sve odmah stoji na vrijednosti; za ispis isto.

## Pravila

- **Do** koristiti boju samo za ono što se mjeri, i uvijek istu boju za isto mjerenje.
- **Do** crtati instrumente samo iz vrijednosti izvještaja; ako vrijednosti nema, ploča piše „Nema podataka” bez crteža.
- **Don't** koristiti boju kategorije kao status ili za radnju.
- **Don't** dodavati natpise iznad naslova, sjene kao ukras ni kartice unutar kartica.
