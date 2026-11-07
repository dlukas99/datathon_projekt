import { X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { Link } from 'react-router'
import type { MapPoint, MapRow } from '../lib/api'
import { formatDate } from '../lib/format'
import { AIR_RATING, FLOOD_SHORT, transitText } from '../lib/mapLayers'
import { getProfile } from '../lib/profiles'
import { reportPath } from '../lib/urls'
import { CategoryIcon } from './Icons'
import { ListingLinks } from './ListingLinks'

export interface Picked {
  lat: number
  lon: number
  /** "map": a click on the map; "table": a row of the table (the settlement centre). */
  from: 'map' | 'table'
}

interface Tag {
  id: string
  title: string
  text: string
}

function tags(row: MapRow, profile: string): Tag[] {
  const score = row.scores[profile] ?? null
  return [
    {
      id: 'air',
      title: 'Zrak',
      text: row.air ? (AIR_RATING[row.air] ?? row.air) : 'nema podataka',
    },
    {
      id: 'flood',
      title: 'Poplave',
      text: row.flood ? (FLOOD_SHORT[row.flood] ?? row.flood) : 'nema podataka',
    },
    {
      id: 'green',
      title: 'Zelenilo',
      text:
        row.tree === null
          ? 'nema podataka'
          : `drveće ${row.tree.toLocaleString('hr-HR', { maximumFractionDigits: 0 })} % u krugu 300 m`,
    },
    {
      id: 'car_free',
      title: 'Usluge pješice',
      text: row.needs === null ? 'nema podataka' : `${String(row.needs)} od 7 do 15 min`,
    },
    { id: 'transit', title: 'Prijevoz', text: transitText(row) },
    {
      id: 'score',
      title: 'Skor za život',
      text: score === null ? 'nema podataka' : `${String(score)} od 100`,
    },
  ]
}

/** Short card for a settlement picked on the map or in the table; not the full report. */
export function SettlementCard({
  picked,
  point,
  row,
  loading,
  error,
  profile,
  profilesDate,
  onClose,
}: {
  picked: Picked
  point: MapPoint | null
  row: MapRow | null
  loading: boolean
  error: boolean
  profile: string
  profilesDate: string | null
  onClose: () => void
}) {
  const heading = useRef<HTMLHeadingElement>(null)
  const ready = !loading && !error
  const key = `${String(picked.lat)},${String(picked.lon)},${String(ready)}`

  useEffect(() => {
    if (key.endsWith('true')) heading.current?.focus({ preventScroll: true })
  }, [key])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key !== 'Escape' || e.defaultPrevented) return
      onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
    }
  }, [onClose])

  const close = (
    <button type="button" className="icon-button atlas-close" onClick={onClose}>
      <X size={18} aria-hidden="true" />
      <span className="visually-hidden">Zatvori karticu</span>
    </button>
  )

  if (loading) {
    return (
      <div className="atlas-card" aria-busy="true">
        {close}
        <p className="hint">Tražim naselje…</p>
      </div>
    )
  }
  if (error) {
    return (
      <div className="atlas-card">
        {close}
        <p role="alert">Podaci za ovu točku trenutačno nisu dostupni. Pokušajte ponovno.</p>
      </div>
    )
  }

  const name = row?.name ?? point?.name ?? null
  if (!name || (point && point.kind !== 'settlement')) {
    return (
      <div className="atlas-card">
        {close}
        <h2 ref={heading} tabIndex={-1} className="atlas-card-title">
          {point?.message ?? 'Odaberite točku na kopnu.'}
        </h2>
      </div>
    )
  }

  const municipality = row?.municipality ?? point?.municipality ?? ''
  const county = row?.county ?? point?.county ?? ''
  const population = row?.population ?? point?.population ?? null
  const outside = picked.from === 'map' && point !== null && !point.populated
  const reportUrl =
    picked.from === 'map'
      ? reportPath(picked.lat, picked.lon, null, profile, [], 'map')
      : reportPath(picked.lat, picked.lon, `${name}, ${municipality}`, profile, [], 'settlement')
  const date = formatDate(profilesDate)

  return (
    <div className="atlas-card">
      {close}
      <p className="eyebrow">Naselje</p>
      <h2 ref={heading} tabIndex={-1} className="atlas-card-title">
        {name}
      </h2>
      <p className="place-line">
        {[municipality !== name ? municipality : '', county !== municipality ? county : '']
          .filter(Boolean)
          .join(', ')}
        {population !== null
          ? ` · ${population.toLocaleString('hr-HR')} stanovnika (Popis 2021.)`
          : ' · broja stanovnika nema u tablici Popisa 2021.'}
      </p>

      {outside && (
        <div className="atlas-note">
          <p>
            Odabrana točka je izvan naseljenog dijela; prikazujem naselje {name}
            {point.centre_km !== null &&
              ` (središte ${point.centre_km.toLocaleString('hr-HR', { maximumFractionDigits: 1 })} km)`}
            .
          </p>
          {point.at_point.length > 0 && (
            <ul className="atlas-point-values">
              {point.at_point.map((t) => (
                <li key={t.id}>
                  <strong>{t.title} na odabranoj točki:</strong>{' '}
                  {t.id === 'air' ? t.text.toLowerCase() : t.text}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {row ? (
        <>
          <ul className="atlas-tags" aria-label="Pokazatelji za središte naselja">
            {tags(row, profile).map((t) => (
              <li key={t.id}>
                <CategoryIcon id={t.id === 'score' ? 'compare' : t.id} size={16} />
                <span className="atlas-tag-title">{t.title}</span>
                <span className="atlas-tag-text">{t.text}</span>
              </li>
            ))}
          </ul>
          <p className="fine-print">
            Vrijednosti za središte naselja; skor za profil „{getProfile(profile).label}”.
            {date && ` Izračun ${date}`}, izvori na stranici <Link to="/izvori">Izvori</Link>.
          </p>
        </>
      ) : (
        <p className="hint">
          Za ovo naselje pokazatelji trenutačno nisu dostupni. Puni izvještaj izračunava ih za
          odabranu točku.
        </p>
      )}

      <div className="button-row">
        <Link className="button" to={reportUrl}>
          Otvori puni izvještaj
        </Link>
        <ListingLinks settlement={name} municipality={municipality || null} county={county || null} />
      </div>
    </div>
  )
}
