import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { AddressSearch } from '../components/AddressSearch'
import { ProfilePicker } from '../components/ProfilePicker'
import type { Suggestion } from '../lib/api'
import { reportPath } from '../lib/urls'
import demo from '../../../scripts/demo_addresses.json'

export function HomePage() {
  const navigate = useNavigate()
  const [profile, setProfile] = useState('opci')
  const [custom, setCustom] = useState<string[]>([])

  function open(s: Suggestion) {
    void navigate(reportPath(s.lat, s.lon, s.label, profile, custom))
  }

  return (
    <>
      <section className="hero" aria-labelledby="home-title">
        <h1 id="home-title">Kakav je okoliš oko kuće ili stana koji kupujete?</h1>
        <p className="lead">
          Za bilo koju adresu u Hrvatskoj: poplave, kvaliteta zraka, toplina i zelenilo, buka i
          sunce na krovu, a zatim što je dostupno pješice. Iz otvorenih podataka, s izvorom i
          datumom uz svaku brojku.
        </p>
        <div className="card">
          <AddressSearch onSelect={open} label="Adresa ili naselje" inputId="home-search" />
          <ProfilePicker
            profile={profile}
            custom={custom}
            onProfile={setProfile}
            onCustom={setCustom}
          />
        </div>
      </section>

      <section className="section" aria-labelledby="demo-title">
        <h2 id="demo-title">Primjeri</h2>
        <p className="section-intro">Isprobajte na adresama javnih ustanova:</p>
        <ul className="demo-list">
          {demo.addresses.map((d) => (
            <li key={d.id}>
              <Link to={reportPath(d.lat, d.lon, d.address, profile, custom)}>
                {d.institution}
              </Link>
            </li>
          ))}
        </ul>
        <p style={{ marginTop: '1rem' }}>
          <Link
            className="button secondary"
            to={`/usporedi?a=${String(demo.addresses[0]?.lat)},${String(demo.addresses[0]?.lon)}&la=${encodeURIComponent(demo.addresses[0]?.address ?? '')}&b=${String(demo.addresses[1]?.lat)},${String(demo.addresses[1]?.lon)}&lb=${encodeURIComponent(demo.addresses[1]?.address ?? '')}`}
          >
            Primjer usporedbe dviju adresa
          </Link>
        </p>
      </section>

      <section className="section features" aria-labelledby="what-title">
        <h2 id="what-title">Što dobivate</h2>
        <div className="grid">
          <div className="card">
            <h3>1. Okolišni pregled</h3>
            <p>
              Je li lokacija u modeliranom poplavnom području, kakav je zrak u usporedbi sa
              smjernicama Svjetske zdravstvene organizacije i EU-a, koliko je drveća i zelenila,
              koliko su blizu prometnice i koliko struje bi dala sunčana elektrana na krovu.
            </p>
          </div>
          <div className="card">
            <h3>2. Život bez auta</h3>
            <p>
              Što je na 5, 10 i 15 minuta hoda po stvarnoj mreži ulica, stajališta javnog
              prijevoza s brojem polazaka i koliko svakodnevnih potreba pokrivate pješice.
            </p>
          </div>
          <div className="card">
            <h3>3. Svakodnevni život</h3>
            <p>
              Najbliži vrtić, osnovna škola, obiteljski liječnik, pedijatar, ljekarna, trgovina i
              igralište, s minutama hoda.
            </p>
          </div>
        </div>
        <p className="disclaimer">
          Informativni alat, a ne službena procjena. Svaka kategorija ima vlastito značenje i
          prag s izvorom; nema skupne ocjene sa skrivenim težinama. Više u odjeljku{' '}
          <Link to="/o-alatu">O alatu</Link>.
        </p>
      </section>
    </>
  )
}
