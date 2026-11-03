import { ArrowRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { AddressSearch } from '../components/AddressSearch'
import { CategoryIcon } from '../components/Icons'
import { ProfilePicker } from '../components/ProfilePicker'
import type { Suggestion } from '../lib/api'
import { comparePath, reportPath } from '../lib/urls'
import demo from '../../../scripts/demo_addresses.json'

const STEPS: { icon: string; title: string; text: string }[] = [
  {
    icon: 'flood',
    title: 'Okoliš',
    text: 'Poplave, zrak, zelenilo i vrućine, buka, požari i sunce na krovu.',
  },
  {
    icon: 'car_free',
    title: 'Život bez auta',
    text: 'Što je na 5, 10 i 15 minuta hoda i koliko često vozi javni prijevoz.',
  },
  {
    icon: 'kindergarten',
    title: 'Svakodnevica',
    text: 'Vrtić, škola, liječnik, ljekarna i trgovina, u minutama hoda.',
  },
]

export function HomePage() {
  const navigate = useNavigate()
  const [profile, setProfile] = useState('opci')
  const [custom, setCustom] = useState<string[]>([])
  const [first, second] = demo.addresses

  function open(s: Suggestion) {
    void navigate(reportPath(s.lat, s.lon, s.label, profile, custom))
  }

  return (
    <>
      <section className="hero" aria-labelledby="home-title">
        <h1 id="home-title">Kakav je okoliš oko doma koji kupujete?</h1>
        <p className="lead">
          Upišite adresu i saznajte ono što oglas ne kaže, iz otvorenih podataka.
        </p>
        <div className="search-card">
          <AddressSearch onSelect={open} label="Adresa ili naselje" inputId="home-search" />
          <ProfilePicker
            profile={profile}
            custom={custom}
            onProfile={setProfile}
            onCustom={setCustom}
          />
        </div>
        <div className="examples">
          <span className="examples-label" id="demo-title">
            Primjeri:
          </span>
          <ul className="example-list" aria-labelledby="demo-title">
            {demo.addresses.map((d) => (
              <li key={d.id}>
                <Link to={reportPath(d.lat, d.lon, d.address, profile, custom)}>
                  {d.institution.replace(/ \(.*\)$/, '')}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        {first && second && (
          <p className="compare-cta">
            <Link
              to={comparePath(
                { lat: first.lat, lon: first.lon, label: first.address },
                { lat: second.lat, lon: second.lon, label: second.address },
              )}
            >
              Ili usporedite dvije adrese <ArrowRight size={16} aria-hidden="true" />
            </Link>
          </p>
        )}
      </section>

      <section className="steps" aria-label="Što dobivate">
        {STEPS.map((s) => (
          <div key={s.title} className="step">
            <span className="step-icon">
              <CategoryIcon id={s.icon} size={22} />
            </span>
            <h2>{s.title}</h2>
            <p>{s.text}</p>
          </div>
        ))}
      </section>

      <p className="fine-print center">
        Informativni alat, a ne službena procjena. Uz svaku brojku su izvor i datum.{' '}
        <Link to="/o-alatu">Kako računamo</Link>
      </p>
    </>
  )
}
