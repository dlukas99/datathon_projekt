import type { CSSProperties, ReactNode } from 'react'
import { ChevronDown } from 'lucide-react'
import { AboutSources } from '../components/AboutSources'
import { ReportGuide } from '../components/PlaceBoard'
import { BRAND } from '../lib/brand'

export const REPO_URL = 'https://github.com/dlukas99/datathon_projekt'

/** Sections of the page; their ids are the anchors used by the footer and other pages. */
export const ABOUT_SECTIONS = [
  { id: 'ukratko', label: 'Ukratko' },
  { id: 'kako-racunamo', label: 'Kako računamo' },
  { id: 'izvori', label: 'Izvori podataka' },
  { id: 'kvaliteta', label: 'Kvaliteta podataka' },
  { id: 'privatnost', label: 'Privatnost' },
  { id: 'tim', label: 'Tim' },
]

interface Method {
  id: string
  name: string
  how: string
  threshold: ReactNode
  more: ReactNode
}

/** One row per category of the report: what we compute, the threshold and its source. */
const METHODS: Method[] = [
  {
    id: 'flood',
    name: 'Poplave',
    how: 'Dubina vode na adresi i u krugu od 100 m iz europskih karata riječnih poplava (JRC) za poplave koje se u prosjeku događaju jednom u 10, 100 i 500 godina.',
    threshold:
      'Loše ako je adresa u području poplave od 10 ili 100 godina, upozorenje za područje od 500 godina ili poplavno područje do 100 m; podjela prema Direktivi 2007/60/EZ i kartama Hrvatskih voda.',
    more: (
      <>
        Karte imaju razlučivost od oko 90 m i obuhvaćaju samo riječne poplave većih vodotoka, a ne
        bujice, more ni oborinske vode. Povratno razdoblje pretvaramo u vjerojatnost barem jedne
        poplave u 30 godina, koliko obično traje stambeni kredit: oko 96 % za 10, 26 % za 100 i 6 %
        za 500 godina. Adresa izvan modeliranog područja ne znači da rizika nema; službeni su
        preglednik i karte Hrvatskih voda.
      </>
    ),
  },
  {
    id: 'air',
    name: 'Kvaliteta zraka',
    how: 'Godišnji prosjek sitnih čestica PM2,5 i dušikova dioksida NO2 iz karata Europske agencije za okoliš za 2024., u mreži od 1 km.',
    threshold:
      'Ocjena prema lošijem od dvaju onečišćenja: vrlo dobar do preporuke WHO-a iz 2021., dobar do granice EU-a za 2030., umjeren do granice EU-a koja vrijedi danas, loš iznad nje.',
    more: (
      <>
        Granice u µg/m³ za PM2,5 i NO2: WHO 5 i 10, EU od 2030. 10 i 20, današnja granica EU-a 25
        i 40 (Direktiva (EU) 2024/2881). Karta je modelirana procjena godišnjeg prosjeka, a ne
        mjerenje na adresi; usporedili smo je sa službenim mjernim postajama u Hrvatskoj za 2024.
      </>
    ),
  },
  {
    id: 'green',
    name: 'Priroda i hlad',
    how: 'Udio prirode (drveće, grmlje, travnjaci, polja i močvare), drveća i izgrađenog u krugu od 300 m iz satelitske karte ESA WorldCover 2021. (10 m); u gradu i najbliži park iz OpenStreetMapa.',
    threshold:
      'U gusto izgrađenom području (izgrađeno više od pola kopna u krugu od 300 m) vrijedi pravilo 3-30-300 za gradove (Konijnendijk, 2023.): najmanje 30 % površine pod drvećem i park do 300 m; drugdje je dobro kad je barem pola površine priroda.',
    more: (
      <>
        Pravilo 3-30-300 namijenjeno je gradovima, pa selo okruženo poljima ne ocjenjujemo po
        njemu: oranice i livade oko kuće broje se kao priroda, a park ne tražimo. Prag od pola
        izgrađenog kopna naša je pretpostavka. Piksel karte je „drveće” kad drveće pokriva barem
        10 % njegove površine, pa udio drveća nije gustoća krošnji, a pojedinačna stabla uz
        ulice karta često ne vidi. Za naselja na karti i u prijedlozima uzimamo medijan svih
        adresa naselja (najviše 100 po naselju). More se ne broji u udio, a temperaturu ne
        mjerimo.
      </>
    ),
  },
  {
    id: 'noise',
    name: 'Udaljenost od prometnica',
    how: 'Zračna udaljenost do autoceste, brze, državne ili glavne gradske ceste i do pruge iz OpenStreetMapa; za naselje se računa za svaku adresu.',
    threshold:
      'Do 300 m: blizu prometnice; 300–500 m: rub zone prometa; dalje: podalje od prometnica. Zona utjecaja prometa prema pregledu Health Effects Institutea (2010.).',
    more: (
      <>
        Županijske ceste (oznaka Ž) se ne broje, jer prolaze kroz gotovo svako selo. Buku ne
        mjerimo: udaljenost je zamjenski pokazatelj (procjena), jer strateške karte buke nemaju
        licencu koja dopušta ovakvu upotrebu.
      </>
    ),
  },
  {
    id: 'fire',
    name: 'Požari raslinja',
    how: 'Veći požari raslinja u krugu od 2 km od 2016. iz europskog sustava EFFIS (satelitsko kartiranje): broj, godine i najveća izgorjela površina.',
    threshold: 'Informacija; za broj prošlih požara ne postoji službeni prag.',
    more: (
      <>
        EFFIS bilježi uglavnom požare od otprilike 30 ha naviše (od 2018. i neke manje), pa manji
        požari nedostaju. Prošli požari pokazuju izloženost, a ne predviđaju buduće.
      </>
    ),
  },
  {
    id: 'solar',
    name: 'Sunce na krovu',
    how: 'Godišnja proizvodnja sunčeve elektrane snage 1 kW uz optimalni nagib i 14 % gubitaka, iz servisa JRC PVGIS 5.3.',
    threshold: 'Informacija; službeni prag ne postoji.',
    more: (
      <>
        Vrijednost se dohvaća za točku i ne uzima u obzir sjenu susjednih zgrada i drveća ni
        stvarni nagib i orijentaciju krova.
      </>
    ),
  },
  {
    id: 'car_free',
    name: 'Život bez auta',
    how: 'Koliko je od sedam svakodnevnih potreba (trgovina, ljekarna, obiteljski liječnik, vrtić, osnovna škola, park i stajalište s polaskom barem svaki sat) do 15 minuta hoda po stvarnoj mreži ulica.',
    threshold:
      'Informacija: „X od 7” i popis onoga što nedostaje. Granica od 15 minuta prati koncept „grada od 15 minuta” (Moreno i sur., 2021.).',
    more: (
      <>
        Hod računa usmjerivač Valhalla nad OpenStreetMapom, brzinom od 4,5 km/h. To je nešto
        sporije od uobičajenog, kako bi vremena vrijedila i za starije osobe i roditelje s djecom.
      </>
    ),
  },
  {
    id: 'transit',
    name: 'Javni prijevoz',
    how: 'Stajališta do 10 minuta hoda i prosječan broj polazaka na sat od 6 do 20 sati radnim danom, iz voznih redova ZET-a, HŽPP-a, Autotroleja i Gradskog parkinga Šibenik.',
    threshold: 'Informacija; službeni prag ne postoji.',
    more: (
      <>
        Otvoreni vozni redovi postoje samo za ta četiri prijevoznika. Drugdje prikazujemo
        stajališta iz OpenStreetMapa s oznakom „bez voznog reda” i linije koje ondje staju prema
        OpenStreetMapu, bez broja polazaka.
      </>
    ),
  },
]

function MethodRow({ method }: { method: Method }) {
  return (
    <li className="method-row measured" style={{ '--c': `var(--c-${method.id})` } as CSSProperties}>
      <h3 className="method-name">{method.name}</h3>
      <div className="method-body">
        <p>{method.how}</p>
        <p className="method-threshold">
          <span className="method-label">Prag i izvor: </span>
          {method.threshold}
        </p>
        <details className="more">
          <summary>
            Više
            <ChevronDown size={16} className="chevron" aria-hidden="true" />
          </summary>
          <p className="more-body">{method.more}</p>
        </details>
      </div>
    </li>
  )
}

export function AboutPage() {
  return (
    <>
      <h1>O alatu i metodologiji</h1>
      <ReportGuide sections={ABOUT_SECTIONS} label="Dijelovi stranice" />

      <section className="section about-section" aria-labelledby="ukratko">
        <h2 id="ukratko">Ukratko</h2>
        <p className="about-lead">
          {BRAND.name} iz otvorenih podataka pokazuje kako je živjeti na nekoj adresi: kakav je
          okoliš i što vam je pješice na dohvat ruke. Pomaže i pronaći mjesto za život koje
          odgovara vama, bilo da ste obitelj, student, umirovljenik ili radite od kuće.
        </p>
        <p className="disclaimer">
          Ovo je informativni alat, a ne službena procjena rizika, geodetski ni građevinski
          pregled. Ne zamjenjuje karte i upozorenja Hrvatskih voda, DHMZ-a i civilne zaštite.
        </p>
        <ul className="about-principles">
          <li>
            Svaka vrijednost ima izvor, datum i vrstu: <strong>izmjereno</strong> (mjerenje, vozni
            red ili službeni registar), <strong>procjena modela</strong> (izračunato iz karata i
            modela, a ne izmjereno na adresi) ili <strong>gruba procjena</strong> (zamjenski
            podatak, npr. udaljenost od ceste umjesto buke).
          </li>
          <li>„Nema podataka” uvijek se prikazuje; kategorija se nikad tiho ne izostavlja.</li>
          <li>
            Sažetak i odgovori asistenta slažu se iz predložaka nad izračunima; jezični model ne
            smišlja brojke.
          </li>
        </ul>
        <p className="about-links">
          Otvoreni API s opisom OpenAPI: <a href="/api/docs">/api/docs</a>. Kod, detaljna
          metodologija i odluke:{' '}
          <a href={REPO_URL} target="_blank" rel="noreferrer">
            repozitorij na GitHubu
            <span className="visually-hidden"> (otvara se u novoj kartici)</span>
          </a>
          .
        </p>
      </section>

      <section className="section about-section" aria-labelledby="kako-racunamo">
        <h2 id="kako-racunamo">Kako računamo</h2>
        <p className="section-intro">
          Svaka kategorija ima vlastito značenje i status prema pragu s izvorom. Brojke i izvori za
          konkretnu adresu nalaze se u izvještaju pod „Detalji i izvor”.
        </p>
        <ul className="method-list">
          {METHODS.map((m) => (
            <MethodRow key={m.id} method={m} />
          ))}
        </ul>

        <h3 className="about-subtitle">Ocjena mjesta, profili i prijedlozi</h3>
        <ul className="method-list">
          <li className="method-row">
            <h4 className="method-name">Ocjena mjesta</h4>
            <div className="method-body">
              <p>
                Broj od 0 do 100 koji spaja sve kategorije prema tome koliko vam je koja važna.
                Svaka kategorija dobiva bodove (na primjer poplave: dobro 100, upozorenje 50, loše
                0), a ocjena je njihov prosjek u kojem važnije kategorije vrijede više. Važnost
                možete mijenjati; kategorije bez podataka se preskaču.
              </p>
              <details className="more">
                <summary>
                  Više
                  <ChevronDown size={16} className="chevron" aria-hidden="true" />
                </summary>
                <p className="more-body">
                  Ocjena mjesta je pomoć pri usporedbi, a ne sud o kvaliteti života. Granice razreda dolaze
                  iz izvora navedenih gore, a bodovi unutar razreda (na primjer 100, 80, 50 i 10 za
                  zrak) naša su prozirna normalizacija, opisana u metodologiji u repozitoriju.
                </p>
              </details>
            </div>
          </li>
          <li className="method-row">
            <h4 className="method-name">Profili</h4>
            <div className="method-body">
              <p>
                Obitelj s djecom, umirovljenik, student, rad od kuće ili vlastiti profil mijenjaju
                redoslijed, naglasak i važnost u ocjeni mjesta, a nikad same vrijednosti.
              </p>
            </div>
          </li>
          <li className="method-row">
            <h4 className="method-name">Predloži mjesto: obavezni uvjeti</h4>
            <div className="method-body">
              <p>Naselje ulazi u prijedloge samo ako ispunjava uvjete profila:</p>
              <dl className="rules">
                <div>
                  <dt>Obitelj s djecom</dt>
                  <dd>vrtić i osnovna škola do 15 minuta hoda</dd>
                </div>
                <div>
                  <dt>Umirovljenik</dt>
                  <dd>trgovina, ljekarna i obiteljski liječnik do 15 minuta hoda</dd>
                </div>
                <div>
                  <dt>Student</dt>
                  <dd>
                    studiji u naselju ili veće studijsko središte (barem 20 studijskih programa) do
                    15 km, uz stajalište do 10 minuta hoda
                  </dd>
                </div>
                <div>
                  <dt>Rad od kuće i općenito</dt>
                  <dd>trgovina do 15 minuta hoda</dd>
                </div>
              </dl>
              <p>
                Rangiraju se naselja s najmanje 200 stanovnika (2.347 naselja, 92 % stanovništva
                prema Popisu 2021.). Isti upit uvijek daje isti poredak, a jezični model ne
                sudjeluje u rangu.
              </p>
            </div>
          </li>
        </ul>
      </section>

      <AboutSources />

      <section className="section about-section" aria-labelledby="kvaliteta">
        <h2 id="kvaliteta">Kvaliteta podataka</h2>
        <p className="section-intro">Što smo naučili spajajući izvore, kako bi ih izdavači mogli poboljšati.</p>
        <ul className="about-findings">
          <li>
            <strong>Vrtići i škole bez koordinata.</strong> Registar dječjih vrtića i popis osnovnih
            škola nemaju koordinate; geokodirali smo ih vlastitim geokoderom nad 1.683.411 adresa
            Državne geodetske uprave (uspješno 92,9 % vrtića i 93,0 % škola izvan Zagreba). Registar
            vrtića navodi pravne osobe, a ne sve objekte (u Zagrebu 199 redaka, a gradski geoportal
            323 objekta), a popis škola nema područne škole.
          </li>
          <li>
            <strong>HZZO.</strong> Popisi ugovornih ordinacija i ljekarni objavljeni su kao tablice
            bez koordinata i bez navedene licence. Geokodirano je 92,5 % adresa ordinacija
            obiteljske medicine, 94,8 % pedijatrijskih i 86,4 % ljekarni. Popis ljekarni zadnji je
            put izmijenjen 28. 9. 2023.
          </li>
          <li>
            <strong>Reciklaža.</strong> Od 33 općinska skupa o reciklažnim dvorištima i zelenim
            otocima na Portalu samo 11 ima upotrebljive koordinate. Isti se podaci objavljuju u 3–4
            oblika (CSV, JSON, XLSX, PDF), u barem tri različite strukture stupaca.
          </li>
          <li>
            <strong>Vozni red HŽPP-a.</strong> Poveznica na Portalu vraća grešku 404, dok datoteka
            na stranicama HŽPP-a radi i osvježava se svakodnevno.
          </li>
        </ul>
      </section>

      <section className="section about-section" aria-labelledby="privatnost">
        <h2 id="privatnost">Privatnost</h2>
        <p className="about-text">
          Upisane adrese i pitanja asistentu ne spremaju se i ne bilježe. Ako je uključen jezični
          model, samo tekst pitanja (bez adrese) šalje se njegovu pružatelju. Nema kolačića za
          praćenje ni analitike. Fontovi se poslužuju s našeg poslužitelja.
        </p>
      </section>

      <section className="section about-section" aria-labelledby="tim">
        <h2 id="tim">Tim</h2>
        <p className="about-text">
          Tim „Požega”: Domagoj Lukas i Fabio Mandić, studenti diplomskog studija Računarstvo, smjer
          Podatkovna znanost. Mentor i voditelj tima: dr. sc. Matej Džijan. Fakultet elektrotehnike,
          računarstva i informacijskih tehnologija Osijek (FERIT), Sveučilište J. J. Strossmayera u
          Osijeku. Izrađeno za Datathon Portala otvorenih podataka 2026., izazov B: Okoliš i održivi
          prostor.
        </p>
      </section>
    </>
  )
}
