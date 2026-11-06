import { ArrowRight } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { AddressSearch } from '../components/AddressSearch'
import { CategoryIcon } from '../components/Icons'
import { ProfilePicker } from '../components/ProfilePicker'
import type { Suggestion } from '../lib/api'
import { BRAND } from '../lib/brand'
import { comparePath, reportPath } from '../lib/urls'
import demo from '../../../scripts/demo_addresses.json'

type Demo = (typeof demo.addresses)[number] | undefined

const ENTRIES: { icon: string; title: string; text: string; to: (a: Demo, b: Demo) => string }[] = [
  {
    icon: 'find',
    title: 'Pronađi mjesto za život',
    text: 'Zadajte što vam treba, a aplikacija predlaže naselja s razlozima.',
    to: () => '/pronadi',
  },
  {
    icon: 'compare',
    title: 'Usporedi dvije lokacije',
    text: 'Dvije adrese jedna uz drugu, kategoriju po kategoriju.',
    to: (a, b) =>
      a && b
        ? comparePath(
            { lat: a.lat, lon: a.lon, label: a.address },
            { lat: b.lat, lon: b.lon, label: b.address },
          )
        : '/usporedi',
  },
]

const STEPS: { icon: string; title: string; text: string }[] = [
  {
    icon: 'flood',
    title: 'Okoliš',
    text: 'Poplave, zrak, zelenilo i hlad, promet u blizini, požari i sunce na krovu.',
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
    void navigate(reportPath(s.lat, s.lon, s.label, profile, custom, s.kind))
  }

  return (
    <>
      <section className="hero" aria-labelledby="home-title">
        <h1 id="home-title">Kako je živjeti ovdje?</h1>
        <p className="lead">
          {BRAND.tagline}: poplave, zrak, zelenilo, promet i sve što vam treba na dohvat ruke, iz
          otvorenih podataka.
        </p>
        <div className="search-card">
          <h2 className="entry-title">Provjeri adresu</h2>
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
      </section>

      <section className="entries" aria-label="Drugi načini">
        {ENTRIES.map((e) => (
          <Link key={e.title} className="entry-card" to={e.to(first, second)}>
            <span className="step-icon">
              <CategoryIcon id={e.icon} size={22} />
            </span>
            <span className="entry-text">
              <span className="entry-heading">{e.title}</span>
              <span className="entry-desc">{e.text}</span>
            </span>
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        ))}
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
