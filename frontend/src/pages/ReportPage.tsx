import { useQuery } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { Assistant } from '../components/Assistant'
import { CategoryCard, SourceMeta, type SourceMap, StatusBadge } from '../components/CategoryCard'
import { ProfilePicker } from '../components/ProfilePicker'
import { ISOCHRONE_COLORS, PLACE_COLORS, PLACE_NAMES, ReportMap } from '../components/ReportMap'
import { ApiError, type Category, fetchReport, geojsonUrl, type Place, type Report } from '../lib/api'
import { formatDate } from '../lib/format'
import { focusList, getProfile, orderByFocus } from '../lib/profiles'
import { comparePath } from '../lib/urls'

const DAILY_ORDER = [
  'kindergarten',
  'school',
  'doctor',
  'pediatrician',
  'pharmacy',
  'grocery',
  'playground',
  'recycling',
]

export function sourceMap(report: Report): SourceMap {
  return Object.fromEntries(report.sources.map((s) => [s.id, s]))
}

export function placeLine(report: Report): string {
  const loc = report.location
  return [loc.settlement, loc.municipality !== loc.settlement ? loc.municipality : null, loc.county]
    .filter(Boolean)
    .join(', ')
}

export function LoadingReport() {
  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      Računam pregled: čitam karte poplava, zraka i pokrova tla te rute hoda…
    </div>
  )
}

export function ReportError({ error }: { error: unknown }) {
  const message =
    error instanceof ApiError
      ? error.message
      : 'Pregled trenutačno nije moguće izračunati. Pokušajte ponovno za nekoliko trenutaka.'
  return (
    <div className="error-box" role="alert">
      <p>
        <strong>Pregled nije dostupan.</strong> {message}
      </p>
      <Link to="/">Natrag na pretragu</Link>
    </div>
  )
}

function DailyTable({
  category,
  sources,
  focus,
}: {
  category: Category
  sources: SourceMap
  focus: string[]
}) {
  const rows = orderByFocus(DAILY_ORDER, (k) => k, focus)
  const byKey = Object.fromEntries(category.values.map((v) => [v.key, v]))
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="place-table">
        <caption className="visually-hidden">
          Najbliže ustanove i trgovine s vremenom hoda i brojem unutar 15 minuta
        </caption>
        <thead>
          <tr>
            <th scope="col">Što</th>
            <th scope="col">Najbliže</th>
            <th scope="col">Unutar 15 min</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((key) => {
            const nearest = byKey[`nearest_${key}`]
            const count = byKey[`count15_${key}`]
            if (!nearest) return null
            return (
              <tr key={key}>
                <th scope="row">
                  {nearest.label}
                  {focus.includes(key) && (
                    <>
                      <br />
                      <span className="focus-tag">Važno za profil</span>
                    </>
                  )}
                </th>
                <td>
                  {nearest.display}
                  <br />
                  <SourceMeta
                    source={nearest.source}
                    retrievedAt={nearest.retrieved_at}
                    kind={nearest.kind}
                    sources={sources}
                  />
                </td>
                <td>{count?.display ?? ''}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function WalkSummary({ places }: { places: Place[] }) {
  const bands = [5, 10, 15].map((limit) => {
    const inBand = places.filter(
      (p) => p.walk_minutes !== null && p.walk_minutes <= limit && p.category in PLACE_NAMES,
    )
    const counts: Record<string, number> = {}
    for (const p of inBand) counts[p.category] = (counts[p.category] ?? 0) + 1
    return { limit, counts }
  })
  return (
    <div>
      <h3>Pješice do</h3>
      <ul className="legend">
        {bands.map(({ limit, counts }) => (
          <li key={limit}>
            <span
              className="legend-swatch"
              style={{ background: ISOCHRONE_COLORS[limit] }}
              aria-hidden="true"
            />
            <strong>{limit} min:</strong>{' '}
            {Object.keys(counts).length === 0
              ? 'ništa od prikazanog'
              : Object.entries(counts)
                  .map(([cat, n]) => `${PLACE_NAMES[cat] ?? cat} (${String(n)})`)
                  .join(', ')}
          </li>
        ))}
      </ul>
      <h3 style={{ marginTop: '1rem' }}>Oznake na karti</h3>
      <ul className="legend">
        {Object.entries(PLACE_NAMES).map(([cat, name]) => (
          <li key={cat}>
            <span className="legend-swatch" style={{ background: PLACE_COLORS[cat] }} aria-hidden="true" />
            {name}
          </li>
        ))}
      </ul>
    </div>
  )
}

function ShareButtons({ report }: { report: Report }) {
  const [copied, setCopied] = useState('')
  const loc = report.location
  return (
    <div className="button-row no-print">
      <Link className="button" to={comparePath({ lat: loc.lat, lon: loc.lon, label: loc.label }, null)}>
        Usporedi s drugom adresom
      </Link>
      <button
        type="button"
        className="button secondary"
        onClick={() => {
          window.print()
        }}
      >
        Ispiši
      </button>
      <button
        type="button"
        className="button secondary"
        onClick={() => {
          navigator.clipboard
            .writeText(window.location.href)
            .then(() => {
              setCopied('Poveznica je kopirana.')
            })
            .catch(() => {
              setCopied('Kopiranje nije uspjelo; kopirajte adresu iz preglednika.')
            })
        }}
      >
        Kopiraj poveznicu
      </button>
      <a className="button secondary" href={geojsonUrl(loc.lat, loc.lon)} download="prije-potpisa.geojson">
        Preuzmi GeoJSON
      </a>
      <span role="status" aria-live="polite">
        {copied}
      </span>
    </div>
  )
}

export function ReportView({ report, focus }: { report: Report; focus: string[] }) {
  const sources = useMemo(() => sourceMap(report), [report])
  const byId = Object.fromEntries(report.categories.map((c) => [c.id, c]))
  const environment = orderByFocus(
    report.categories.filter((c) => c.group === 'environment'),
    (c) => c.id,
    focus,
  )
  const carFree = byId.car_free
  const transit = byId.transit
  const daily = byId.daily
  const mapPlaces = useMemo(
    () => report.categories.flatMap((c) => c.places).filter((p) => p.walk_minutes !== null),
    [report],
  )
  const needs = carFree?.values.find((v) => v.key === 'needs_within_15min')

  return (
    <>
      <section className="summary" aria-labelledby="summary-title">
        <h2 id="summary-title" className="visually-hidden">
          Sažetak
        </h2>
        {report.summary.map((s) => (
          <p key={s}>{s}</p>
        ))}
      </section>
      <p className="disclaimer">
        Informativni alat iz otvorenih podataka, a ne službena procjena.{' '}
        <Link to="/o-alatu">Kako računamo i koji su pragovi</Link>
      </p>

      <section className="section" aria-labelledby="env-title">
        <h2 id="env-title">Okolišni pregled</h2>
        <p className="section-intro">
          Svaka kategorija ima vlastiti prag s izvorom. „Bez ocjene” znači da za tu vrijednost ne
          postoji općeprihvaćen prag, pa prikazujemo samo podatak.
        </p>
        <div className="grid">
          {environment.map((c) => (
            <CategoryCard key={c.id} category={c} sources={sources} focused={focus.includes(c.id)} />
          ))}
        </div>
      </section>

      <section className="section" aria-labelledby="carfree-title">
        <h2 id="carfree-title">Život bez auta</h2>
        <div className="grid">
          {carFree && (
            <article className={`card${focus.includes('car_free') ? ' focused' : ''}`} aria-labelledby="cat-car_free">
              <div className="card-header">
                <h3 id="cat-car_free">Svakodnevne potrebe pješice</h3>
                <StatusBadge status={carFree.status} label={carFree.status_label} />
              </div>
              {needs && (
                <p className="big-number">
                  {String(needs.value)} <span style={{ fontSize: '1.1rem' }}>{needs.unit}</span>
                </p>
              )}
              <p className="headline">{carFree.headline}</p>
              <p className="search-hint">
                Trgovina namirnicama, ljekarna, obiteljski liječnik, vrtić, osnovna škola, park i
                stajalište s barem jednim polaskom na sat radnim danom, unutar 15 minuta hoda
                brzinom od 4,5 km/h.
              </p>
            </article>
          )}
          {transit && <CategoryCard category={transit} sources={sources} focused={focus.includes('transit')} />}
        </div>
        <div className="map-wrap section">
          <ReportMap report={report} places={mapPlaces} />
          <WalkSummary places={mapPlaces} />
        </div>
        {!report.isochrones && (
          <p className="disclaimer">Izokrone hoda trenutačno nisu dostupne (usmjerivač ne odgovara).</p>
        )}
      </section>

      {daily && (
        <section className="section" aria-labelledby="daily-title">
          <div className="card-header">
            <h2 id="daily-title">Svakodnevni život</h2>
            <StatusBadge status={daily.status} label={daily.status_label} />
          </div>
          <p className="headline">{daily.headline}</p>
          <DailyTable category={daily} sources={sources} focus={focus} />
          <ul className="notes">
            {daily.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </section>
      )}
    </>
  )
}

export function SourcesList({ report }: { report: Report }) {
  return (
    <section className="section" aria-labelledby="src-title">
      <h2 id="src-title">Izvori za ovaj pregled</h2>
      <ul className="source-list">
        {report.sources.map((s) => (
          <li key={s.id} className="card">
            <strong>{s.title}</strong>
            <div className="value-meta">
              <span>{s.publisher}</span>
              <span>Licenca: {s.license}</span>
              {formatDate(s.retrieved_at) && <span>preuzeto {formatDate(s.retrieved_at)}</span>}
              {s.data_date && <span>podaci: {s.data_date}</span>}
            </div>
            {s.url && (
              <a href={s.url} target="_blank" rel="noreferrer">
                Izvorni skup podataka
                <span className="visually-hidden"> (otvara se u novoj kartici)</span>
              </a>
            )}
          </li>
        ))}
      </ul>
      <p>
        Pragovi, formule i ograničenja opisani su u odjeljku <Link to="/o-alatu">O alatu</Link>.
      </p>
    </section>
  )
}

export function ReportPage() {
  const [params, setParams] = useSearchParams()
  const lat = Number(params.get('lat'))
  const lon = Number(params.get('lon'))
  const label = params.get('adresa')
  const profile = params.get('profil') ?? 'opci'
  const custom = params.get('vazno')
  const focus = focusList(profile, custom)
  const valid = Number.isFinite(lat) && Number.isFinite(lon) && params.has('lat') && params.has('lon')

  const query = useQuery({
    queryKey: ['report', lat, lon],
    queryFn: ({ signal }) => fetchReport(lat, lon, signal),
    enabled: valid,
  })

  function updateProfile(id: string, customIds: string[] = []) {
    const next = new URLSearchParams(params)
    if (id === 'opci') next.delete('profil')
    else next.set('profil', id)
    if (id === 'vlastiti' && customIds.length > 0) next.set('vazno', customIds.join(','))
    else next.delete('vazno')
    setParams(next, { replace: true })
  }

  if (!valid) {
    return <ReportError error={new ApiError('Nedostaju koordinate lokacije.', 400)} />
  }

  const report = query.data
  return (
    <>
      <div className="report-header">
        <div>
          <h1>{label ?? `${lat.toFixed(5)}, ${lon.toFixed(5)}`}</h1>
          {report && <p className="place-line">{placeLine(report)}</p>}
          {report?.location.population && (
            <p className="place-line">
              Naselje {report.location.settlement}: {report.location.population.display}{' '}
              <SourceMeta
                source={report.location.population.source}
                retrievedAt={report.location.population.retrieved_at}
                kind={report.location.population.kind}
                sources={sourceMap(report)}
              />
            </p>
          )}
          {report && (
            <p className="place-line">
              Izračunato {formatDate(report.generated_at)} · profil: {getProfile(profile).label}
            </p>
          )}
        </div>
      </div>
      {report && <ShareButtons report={report} />}
      <details className="no-print" style={{ marginTop: '0.75rem' }}>
        <summary>Promijeni profil</summary>
        <ProfilePicker
          profile={profile}
          custom={(custom ?? '').split(',').filter(Boolean)}
          onProfile={(id) => {
            updateProfile(id, (custom ?? '').split(',').filter(Boolean))
          }}
          onCustom={(ids) => {
            updateProfile('vlastiti', ids)
          }}
        />
      </details>
      {query.isPending && <LoadingReport />}
      {query.isError && <ReportError error={query.error} />}
      {report && (
        <>
          <ReportView report={report} focus={focus} />
          <Assistant points={[{ lat: report.location.lat, lon: report.location.lon, label }]} />
          <SourcesList report={report} />
          <p className="disclaimer">{report.disclaimer}</p>
        </>
      )}
    </>
  )
}
