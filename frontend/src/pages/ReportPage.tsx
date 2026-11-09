import { useQuery } from '@tanstack/react-query'
import { Check, CircleHelp, Download, MapPin, Printer, Scale, Share2, X } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { Assistant } from '../components/Assistant'
import {
  CategoryCard,
  MoreDetails,
  SourceMeta,
  type SourceMap,
  StatusBadge,
} from '../components/CategoryCard'
import { CategoryIcon } from '../components/Icons'
import { InstrumentPanel } from '../components/Instruments'
import { ListingLinks } from '../components/ListingLinks'
import { FocusPicker } from '../components/ProfilePicker'
import { type WalkFocus, WalkMap } from '../components/WalkMap'
import {
  ApiError,
  type Category,
  fetchReport,
  geojsonUrl,
  type Place,
  type Report,
} from '../lib/api'
import { BRAND } from '../lib/brand'
import { formatDate, isoDatesToText, walkText } from '../lib/format'
import { categoryStats } from '../lib/places'
import { focusList, getProfile, orderByFocus, profileWeights, PROFILES } from '../lib/profiles'
import { decodeWeights, encodeWeights, lifeScore } from '../lib/score'
import { LifeScore, ScoreBadge } from '../components/LifeScore'
import { BoardTags, boardTags, ReportGuide } from '../components/PlaceBoard'
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

// The seven needs of the car-free check, as the backend names them.
const CAR_FREE_NEEDS: [string, string][] = [
  ['trgovina namirnicama', 'Trgovina'],
  ['ljekarna', 'Ljekarna'],
  ['obiteljski liječnik', 'Liječnik'],
  ['vrtić', 'Vrtić'],
  ['osnovna škola', 'Škola'],
  ['park', 'Park'],
  ['stajalište s barem jednim polaskom na sat radnim danom', 'Prijevoz svaki sat'],
]

const GUIDE = [
  { id: 'env-title', label: 'Okoliš' },
  { id: 'carfree-title', label: 'Bez auta' },
  { id: 'daily-title', label: 'Svakodnevica' },
  { id: 'ocjena', label: 'Ocjena' },
  { id: 'izvori', label: 'Izvori' },
]

export function sourceMap(report: Report): SourceMap {
  return Object.fromEntries(report.sources.map((s) => [s.id, s]))
}

export function placeLine(report: Report): string {
  const loc = report.location
  return [
    loc.settlement,
    loc.municipality !== loc.settlement ? loc.municipality : null,
    loc.county !== loc.municipality ? loc.county : null,
  ]
    .filter(Boolean)
    .join(', ')
}

export function LoadingReport() {
  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      Pripremam pregled za ovu adresu…
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

function DailyList({
  category,
  sources,
  focus,
  places,
  onShow,
}: {
  category: Category
  sources: SourceMap
  focus: string[]
  /** Places on the map; a row whose nearest place is there opens its walking route. */
  places: Place[]
  onShow: (place: Place) => void
}) {
  const rows = orderByFocus(DAILY_ORDER, (k) => k, focus)
  const byKey = Object.fromEntries(category.values.map((v) => [v.key, v]))
  return (
    <>
      <ul className="daily-list">
        {rows.map((key) => {
          const nearest = byKey[`nearest_${key}`]
          if (!nearest) return null
          const minutes = nearest.unit === 'min' && typeof nearest.value === 'number'
          const name = nearest.display.match(/\(([^)]*)\)\s*$/)?.[1]
          const place = minutes ? categoryStats(places, key).nearest : null
          const content = (
            <>
              <span className="daily-icon">
                <CategoryIcon id={key} />
              </span>
              <span className="daily-main">
                <span className="daily-label">{nearest.label}</span>
                <span className="daily-name">{name && name !== 'bez naziva' ? name : ''}</span>
              </span>
              <span className="daily-end">
                <span className={`daily-time${minutes ? '' : ' muted'}`}>
                  {minutes
                    ? walkText(nearest.value as number)
                    : nearest.display.replace(/\s*\(.*\)$/, '')}
                </span>
                {place && (
                  <span className="daily-show no-print">
                    <MapPin size={14} aria-hidden="true" />
                    Prikaži na karti
                  </span>
                )}
              </span>
            </>
          )
          return (
            <li key={key} className={focus.includes(key) ? 'focused' : undefined}>
              {place ? (
                <button
                  type="button"
                  className="daily-row"
                  onClick={() => {
                    onShow(place)
                  }}
                >
                  {content}
                </button>
              ) : (
                <div className="daily-row">{content}</div>
              )}
            </li>
          )
        })}
      </ul>
      <MoreDetails category={{ ...category, values: [] }} sources={sources}>
        <table className="mini-table">
          <caption className="visually-hidden">Izvori za svakodnevni život</caption>
          <thead>
            <tr>
              <th scope="col">Što</th>
              <th scope="col">Najbliže</th>
              <th scope="col">Izvor</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((key) => {
              const v = byKey[`nearest_${key}`]
              if (!v) return null
              return (
                <tr key={key}>
                  <th scope="row">{v.label}</th>
                  <td>{v.display}</td>
                  <td>
                    <SourceMeta
                      source={v.source}
                      retrievedAt={v.retrieved_at}
                      kind={v.kind}
                      sources={sources}
                    />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </MoreDetails>
    </>
  )
}

function NeedsChecklist({ carFree }: { carFree: Category }) {
  const missing = carFree.values.find((v) => v.key === 'needs_missing')?.display ?? ''
  const unknown = carFree.values.find((v) => v.key === 'needs_unknown')?.display ?? ''
  return (
    <ul className="needs">
      {CAR_FREE_NEEDS.map(([name, short]) => {
        const state = unknown.includes(name) ? 'unknown' : missing.includes(name) ? 'missing' : 'ok'
        const Icon = state === 'ok' ? Check : state === 'missing' ? X : CircleHelp
        const text = state === 'ok' ? 'ima' : state === 'missing' ? 'nema' : 'nije provjereno'
        return (
          <li key={name} className={`need need-${state}`}>
            <Icon size={16} aria-hidden="true" />
            {short}
            <span className="visually-hidden">: {text}</span>
          </li>
        )
      })}
    </ul>
  )
}

function Actions({ report }: { report: Report }) {
  const [copied, setCopied] = useState('')
  const loc = report.location
  return (
    <div className="actions no-print">
      <Link
        className="button"
        to={comparePath({ lat: loc.lat, lon: loc.lon, label: loc.label }, null)}
      >
        <Scale size={18} aria-hidden="true" />
        Usporedi s drugom adresom
      </Link>
      <button
        type="button"
        className="button ghost"
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
        <Share2 size={18} aria-hidden="true" />
        Kopiraj poveznicu
      </button>
      <button
        type="button"
        className="button ghost"
        onClick={() => {
          window.print()
        }}
      >
        <Printer size={18} aria-hidden="true" />
        Ispiši
      </button>
      {loc.settlement && (
        <ListingLinks
          settlement={loc.settlement}
          municipality={loc.municipality}
          county={loc.county}
        />
      )}
      <span className="copied" role="status" aria-live="polite">
        {copied}
      </span>
    </div>
  )
}

export function ReportView({
  report,
  focus,
  onPick,
  walkFocus,
  onWalkFocus,
}: {
  report: Report
  focus: string[]
  onPick?: (lat: number, lon: number) => void
  walkFocus: WalkFocus | null
  onWalkFocus: (focus: WalkFocus | null) => void
}) {
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
    () => report.nearby_places.filter((p) => p.walk_minutes !== null),
    [report],
  )
  const needs = carFree?.values.find((v) => v.key === 'needs_within_15min')

  return (
    <>
      <section className="section" aria-labelledby="env-title">
        <h2 id="env-title">Okolišni pregled</h2>
        <div className="instruments">
          {environment.map((c) => (
            <InstrumentPanel key={c.id} category={c} sources={sources} focused={focus.includes(c.id)} />
          ))}
        </div>
      </section>

      <section className="section" aria-labelledby="carfree-title">
        <h2 id="carfree-title">Život bez auta</h2>
        <div className="grid two">
          {carFree && (
            <article
              className={`card category${focus.includes('car_free') ? ' focused' : ''}`}
              aria-labelledby="cat-car_free"
              data-category="car_free"
            >
              <div className="card-top">
                <span className="card-icon">
                  <CategoryIcon id="car_free" />
                </span>
                <StatusBadge status={carFree.status} label={carFree.status_label} />
              </div>
              <h3 id="cat-car_free">Svakodnevne potrebe pješice</h3>
              {needs && (
                <p className="key-value">
                  <span className="key-number">
                    {String(needs.value)} <span className="key-of">{needs.unit}</span>
                  </span>
                  <span className="key-label">unutar 15 minuta hoda</span>
                </p>
              )}
              <NeedsChecklist carFree={carFree} />
              <p className="headline">{carFree.headline}</p>
              <MoreDetails category={carFree} sources={sources}>
                <p className="route-note">
                  Pješački put na karti računa se tek kad ga zatražite, istim usmjerivačem i
                  istom brzinom hoda (4,5 km/h) kao vremena u izvještaju. Rute: Valhalla, podaci
                  © suradnici OpenStreetMapa.
                </p>
              </MoreDetails>
            </article>
          )}
          {transit && (
            <CategoryCard category={transit} sources={sources} focused={focus.includes('transit')} />
          )}
        </div>
        <WalkMap
          report={report}
          places={mapPlaces}
          sources={sources}
          onPick={onPick}
          focus={walkFocus}
          onFocus={onWalkFocus}
        />
        {!report.isochrones && (
          <p className="muted-note">Karta hoda trenutačno nije dostupna.</p>
        )}
      </section>

      {daily && (
        <section className="section" aria-labelledby="daily-title">
          <h2 id="daily-title">Svakodnevni život</h2>
          <p className="section-intro">{daily.headline}</p>
          <div className="card">
            <DailyList
              category={daily}
              sources={sources}
              focus={focus}
              places={mapPlaces}
              onShow={(place) => {
                onWalkFocus({ category: place.category, place, reveal: true })
              }}
            />
          </div>
        </section>
      )}
    </>
  )
}

export function SourcesList({ report }: { report: Report }) {
  const loc = report.location
  return (
    <details id="izvori" className="section sources-fold">
      <summary>
        <h2>Izvori podataka ({report.sources.length})</h2>
      </summary>
      <ul className="source-list">
        {report.sources.map((s) => (
          <li key={s.id}>
            <strong>{s.title}</strong>
            <span className="value-meta">
              <span>{s.publisher}</span>
              <span>Licenca: {s.license}</span>
              {formatDate(s.retrieved_at) && <span>preuzeto {formatDate(s.retrieved_at)}</span>}
              {s.data_date && <span>podaci: {isoDatesToText(s.data_date)}</span>}
            </span>
            {s.url && (
              <a href={s.url} target="_blank" rel="noreferrer">
                Izvorni skup podataka
                <span className="visually-hidden"> (otvara se u novoj kartici)</span>
              </a>
            )}
          </li>
        ))}
      </ul>
      <p className="muted-note">
        <a href={geojsonUrl(loc.lat, loc.lon)} download={`${BRAND.fileSlug}.geojson`}>
          <Download size={16} aria-hidden="true" /> Preuzmi ovaj pregled kao GeoJSON
        </a>
        {' · '}
        <Link to="/o-alatu#kako-racunamo">Kako računamo</Link>
      </p>
    </details>
  )
}

export function ReportPage() {
  const [params, setParams] = useSearchParams()
  const lat = Number(params.get('lat'))
  const lon = Number(params.get('lon'))
  const label = params.get('adresa')
  const pointKind = params.get('tip')
  const profile = params.get('profil') ?? 'opci'
  const custom = params.get('vazno')
  const customIds = (custom ?? '').split(',').filter(Boolean)
  const focus = focusList(profile, custom)
  const customWeights = decodeWeights(params.get('tezine'))
  const weights = { ...profileWeights(profile), ...(customWeights ?? {}) }
  const valid =
    Number.isFinite(lat) && Number.isFinite(lon) && params.has('lat') && params.has('lon')

  const query = useQuery({
    queryKey: ['report', lat, lon],
    queryFn: ({ signal }) => fetchReport(lat, lon, signal),
    enabled: valid,
  })

  function updateProfile(id: string, ids: string[] = []) {
    const next = new URLSearchParams(params)
    if (id === 'opci') next.delete('profil')
    else next.set('profil', id)
    if (id === 'vlastiti' && ids.length > 0) next.set('vazno', ids.join(','))
    else next.delete('vazno')
    if (id !== profile) next.delete('tezine')
    setParams(next, { replace: true })
  }

  // The walking route on the map. A new report point removes the route; if a category was
  // chosen, the route to its nearest place is drawn again for the new point.
  const [walkFocus, setWalkFocus] = useState<WalkFocus | null>(null)

  const pickPoint = useCallback(
    (newLat: number, newLon: number) => {
      const next = new URLSearchParams(params)
      next.set('lat', newLat.toFixed(6))
      next.set('lon', newLon.toFixed(6))
      next.delete('adresa')
      next.set('tip', 'karta')
      setWalkFocus((current) => current && { category: current.category, place: null })
      setParams(next)
    },
    [params, setParams, setWalkFocus],
  )

  if (!valid) {
    return <ReportError error={new ApiError('Nedostaju koordinate lokacije.', 400)} />
  }

  const report = query.data
  const score = report ? lifeScore(report.categories, weights) : null

  function setWeight(id: string, value: number) {
    const next = new URLSearchParams(params)
    next.set('tezine', encodeWeights({ ...weights, [id]: value }))
    setParams(next, { replace: true })
  }

  function resetWeights() {
    const next = new URLSearchParams(params)
    next.delete('tezine')
    setParams(next, { replace: true })
  }

  return (
    <>
      <header className="place-board" data-ready={report ? 'true' : undefined}>
        <div className="board-band">
          <div className="board-title">
            <h1>
              {label ??
                (pointKind === 'karta' ? 'Odabrana točka' : `${lat.toFixed(5)}, ${lon.toFixed(5)}`)}
            </h1>
            <p className="board-place">
              {report ? placeLine(report) : 'Pregled adrese'}
              {report?.location.population && <> · {report.location.population.display}</>}
            </p>
          </div>
          {score && <ScoreBadge result={score} />}
        </div>
        <div className="board-body">
          {report && (
            <>
              <div className="board-summary">
                {report.summary.map((s) => (
                  <p key={s}>{s}</p>
                ))}
              </div>
              <BoardTags tags={boardTags(report)} />
            </>
          )}
          {(pointKind === 'naselje' || pointKind === 'ulica') && (
            <p className="notice">
              Prikazano je {pointKind === 'naselje' ? 'središte naselja' : 'sredina ulice'}.
              Vrijednosti na vašoj adresi mogu se razlikovati: za točan izvještaj upišite ulicu i
              kućni broj ili povucite oznaku na karti. Ocjena mjesta ovdje vrijedi za tu jednu točku,
              pa se može razlikovati od ocjene na Karti, koja vrijedi za cijelo naselje.{' '}
              <Link to="/">Nova pretraga</Link>
            </p>
          )}
          {!query.isError && (
          <div className="report-tools no-print">
            <label className="profile-select">
              <span>Gledam kao</span>
              <select
                value={profile}
                onChange={(e) => {
                  updateProfile(e.target.value, customIds)
                }}
              >
                {PROFILES.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label}
                  </option>
                ))}
              </select>
            </label>
            {report && <Actions report={report} />}
          </div>
          )}
          {profile === 'vlastiti' && (
            <FocusPicker
              custom={customIds}
              onCustom={(ids) => {
                updateProfile('vlastiti', ids)
              }}
            />
          )}
        </div>
      </header>
      {report && <ReportGuide sections={GUIDE} />}
      {query.isPending && <LoadingReport />}
      {query.isError && <ReportError error={query.error} />}
      {report && (
        <>
          <ReportView
            report={report}
            focus={focus}
            onPick={pickPoint}
            walkFocus={walkFocus}
            onWalkFocus={setWalkFocus}
          />
          {score && (
            <LifeScore
              categories={report.categories}
              weights={weights}
              result={score}
              profileLabel={getProfile(profile).label}
              customised={customWeights !== null}
              onWeight={setWeight}
              onReset={resetWeights}
            />
          )}
          <Assistant points={[{ lat: report.location.lat, lon: report.location.lon, label }]} />
          <SourcesList report={report} />
          <p className="fine-print">
            {report.disclaimer} Izračunato {formatDate(report.generated_at)}
          </p>
        </>
      )}
    </>
  )
}
