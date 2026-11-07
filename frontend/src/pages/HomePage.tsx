import { ArrowRight } from 'lucide-react'
import { Link, useNavigate } from 'react-router'
import { AddressSearch } from '../components/AddressSearch'
import { CroatiaMosaic } from '../components/CroatiaMosaic'
import type { Suggestion } from '../lib/api'
import { PALETTES } from '../lib/mapLayers'
import { useDocumentTheme } from '../lib/useDocumentTheme'
import { comparePath, reportPath } from '../lib/urls'
import demo from '../../../scripts/demo_addresses.json'

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

  function open(s: Suggestion) {
    void navigate(reportPath(s.lat, s.lon, s.label, 'opci', [], s.kind))
  }

  return (
    <>
      <section className="trailhead" aria-labelledby="home-title">
        <div className="trailhead-text">
          <h1 id="home-title">Kako je živjeti ovdje?</h1>
          <p className="trailhead-lead">
            Upišite adresu bilo gdje u Hrvatskoj i saznajte, iz otvorenih podataka, kakav je ondje
            okoliš i što vam je pješice na dohvat ruke.
          </p>

          <div className="signpost">
            <div className="plank plank-place">
              <AddressSearch onSelect={open} label="Adresa ili naselje" inputId="home-search" />
            </div>
            <Link className="plank plank-go" to="/predlozi">
              <span className="plank-title">Pronađi mjesto za mene</span>
              <span className="plank-sub">Tri pitanja, pa prijedlog naselja s razlozima</span>
              <ArrowRight className="plank-arrow" size={22} aria-hidden="true" />
            </Link>
          </div>

          <div className="examples">
            <span className="examples-label" id="demo-title">
              Ili pogledajte primjer:
            </span>
            <ul className="example-list" aria-labelledby="demo-title">
              {demo.addresses.map((d) => (
                <li key={d.id}>
                  <Link to={reportPath(d.lat, d.lon, d.address, 'opci')}>
                    {d.institution.replace(/ \(.*\)$/, '')}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <figure className="trailhead-map">
          <CroatiaMosaic />
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
