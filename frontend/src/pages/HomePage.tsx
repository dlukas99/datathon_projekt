import { ArrowRight } from 'lucide-react'
import { Link, useNavigate } from 'react-router'
import { AddressSearch } from '../components/AddressSearch'
import { CroatiaMosaic } from '../components/CroatiaMosaic'
import { CategoryIcon } from '../components/Icons'
import type { Suggestion } from '../lib/api'
import { PALETTES } from '../lib/mapLayers'
import { useDocumentTheme } from '../lib/useDocumentTheme'
import { comparePath, reportPath } from '../lib/urls'
import demo from '../../../scripts/demo_addresses.json'

// What the report measures, in the colours the report uses for each reading.
const MEASURES: { id: string; title: string; text: string; source: string }[] = [
  {
    id: 'flood',
    title: 'Poplave',
    text: 'Modelirana područja riječnih poplava za 10, 100 i 500 godina, na adresi i do 100 m.',
    source: 'JRC',
  },
  {
    id: 'air',
    title: 'Zrak',
    text: 'Godišnji prosjek PM2,5 i NO2 uz preporuke WHO-a i granice EU-a.',
    source: 'EEA',
  },
  {
    id: 'green',
    title: 'Zelenilo i hlad',
    text: 'Drveće, zelene i izgrađene površine u krugu od 300 m te najbliži park.',
    source: 'ESA WorldCover',
  },
  {
    id: 'noise',
    title: 'Prometnice',
    text: 'Udaljenost od velikih cesta i pruga, kao procjena izloženosti buci.',
    source: 'OpenStreetMap',
  },
  {
    id: 'fire',
    title: 'Požari raslinja',
    text: 'Opožarene površine snimljene sa satelita u krugu od 2 km.',
    source: 'Copernicus EFFIS',
  },
  {
    id: 'solar',
    title: 'Sunce na krovu',
    text: 'Koliko struje godišnje daje kilovat solarnih panela i pod kojim nagibom.',
    source: 'PVGIS',
  },
]

const STATIONS: { title: string; text: string }[] = [
  {
    title: 'Upišite adresu',
    text: 'Ulicu i kućni broj, samo naselje ili točku na karti. Adresu ne spremamo.',
  },
  {
    title: 'Spajamo otvorene podatke',
    text: 'Karte poplava, kvalitete zraka i pokrova tla, vozne redove, vrtiće, škole i ordinacije, za točno to mjesto.',
  },
  {
    title: 'Čitate iskaznicu mjesta',
    text: 'Najprije okoliš, zatim život bez auta i svakodnevica. Uz svaku brojku su izvor i datum.',
  },
]

export function HomePage() {
  const navigate = useNavigate()
  const theme = useDocumentTheme()
  const [first, second] = demo.addresses
  // One example per town (Vinkovci has two public institutions in the demo list).
  const examples = demo.addresses.filter(
    (d, i, all) => all.findIndex((x) => x.address.split(', ').pop() === d.address.split(', ').pop()) === i,
  )

  function open(s: Suggestion) {
    void navigate(reportPath(s.lat, s.lon, s.label, 'opci', [], s.kind))
  }

  return (
    <>
      <section className="hero" aria-labelledby="home-title">
        <div className="hero-text">
          <h1 id="home-title">
            Kako je živjeti <em>ovdje</em>?
          </h1>
          <p className="hero-lead">
            Upišite adresu bilo gdje u Hrvatskoj i saznajte, iz otvorenih podataka, kakav je ondje
            okoliš i što vam je pješice na dohvat ruke.
          </p>

          <div className="hero-search">
            <AddressSearch
              onSelect={open}
              label="Adresa ili naselje"
              inputId="home-search"
              submitLabel="Prikaži"
            />
          </div>
          <Link className="hero-find" to="/predlozi">
            <span className="hero-find-title">Pronađi mjesto za mene</span>
            <span className="hero-find-sub">Tri pitanja, pa prijedlog naselja s razlozima</span>
            <ArrowRight className="hero-find-arrow" size={22} aria-hidden="true" />
          </Link>

          <div className="examples">
            <span className="examples-label" id="demo-title">
              Ili pogledajte primjer:
            </span>
            <ul className="example-list" aria-labelledby="demo-title">
              {examples.map((d) => (
                <li key={d.id}>
                  <Link to={reportPath(d.lat, d.lon, d.address, 'opci')}>
                    {d.institution.replace(/ \(.*\)$/, '')}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <figure className="hero-map">
          <Link to="/karta" className="mosaic-link" aria-label="Istraži kartu Hrvatske: sva naselja prema Skoru za život">
            <CroatiaMosaic />
          </Link>
          <figcaption>
            <span className="mosaic-scale" aria-hidden="true">
              {PALETTES[theme].steps.map((c) => (
                <span key={c} style={{ background: c }} />
              ))}
            </span>
            <span>
              Sva naselja Hrvatske prema Skoru za život:{' '}
              {theme === 'dark' ? 'svjetlije' : 'tamnije'} je bolje.{' '}
              <Link to="/karta">Istraži kartu Hrvatske</Link>
            </span>
          </figcaption>
        </figure>
      </section>

      <section className="measures" aria-labelledby="measures-title">
        <h2 id="measures-title">Šest mjerenja okoliša za svaku adresu</h2>
        <ul className="measure-list">
          {MEASURES.map((m) => (
            <li key={m.id} className={`measure cat-${m.id}`}>
              <span className="measure-icon">
                <CategoryIcon id={m.id} size={24} />
              </span>
              <h3>{m.title}</h3>
              <p>{m.text}</p>
              <p className="measure-source">{m.source}</p>
            </li>
          ))}
        </ul>
        <p className="measures-more">
          Zatim život bez auta: koliko je od sedam svakodnevnih potreba na 15 minuta hoda i kako
          vozi javni prijevoz.
        </p>
      </section>

      <section className="how" aria-labelledby="how-title">
        <h2 id="how-title">Kako radi</h2>
        <ol className="stations">
          {STATIONS.map((s, i) => (
            <li key={s.title} className="station">
              <span className="station-mark" aria-hidden="true">
                {i + 1}
              </span>
              <h3>{s.title}</h3>
              <p>{s.text}</p>
            </li>
          ))}
        </ol>
        <p className="how-more">
          Dvoumite se između dvije adrese?{' '}
          <Link
            to={
              first && second
                ? comparePath(
                    { lat: first.lat, lon: first.lon, label: first.address },
                    { lat: second.lat, lon: second.lon, label: second.address },
                  )
                : '/usporedi'
            }
          >
            Usporedite ih jednu uz drugu
          </Link>
          .
        </p>
      </section>

      <p className="fine-print center">
        Informativni alat, a ne službena procjena. <Link to="/o-alatu">Kako računamo</Link>
      </p>
    </>
  )
}
