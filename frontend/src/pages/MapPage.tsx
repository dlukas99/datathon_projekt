import { useQuery } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { CroatiaMap, type MapFocus } from '../components/CroatiaMap'
import { type Picked, SettlementCard } from '../components/SettlementCard'
import { fetchMapGeometry, fetchMapPoint, fetchMapTable, type MapRow } from '../lib/api'
import { formatDate } from '../lib/format'
import {
  LAYERS,
  MAP_PROFILES,
  PALETTES,
  getLayer,
  matches,
  sortRows,
} from '../lib/mapLayers'
import { getProfile } from '../lib/profiles'
import { decodeGeometry } from '../lib/settlementGeometry'
import { useDocumentTheme } from '../lib/useDocumentTheme'

// The list under the map is short: the five best, or the first five search results.
const SHOWN = 5
// The best-rated list leaves out hamlets, as "Predloži mjesto" does.
const MIN_POPULATION = 200

export function MapPage() {
  const [params, setParams] = useSearchParams()
  const layer = getLayer(params.get('sloj'))
  const profileParam = params.get('profil') ?? 'opci'
  const profile = (MAP_PROFILES as readonly string[]).includes(profileParam) ? profileParam : 'opci'
  const [picked, setPicked] = useState<Picked | null>(null)
  const [focus, setFocus] = useState<MapFocus | null>(null)
  const [query, setQuery] = useState('')
  const [mapReady, setMapReady] = useState(false)
  const started = useRef(0)
  const focusCount = useRef(0)
  const [loadMs, setLoadMs] = useState<number | null>(null)
  const opener = useRef<HTMLElement | null>(null)
  const theme = useDocumentTheme()

  useEffect(() => {
    started.current = performance.now()
  }, [])

  const geometry = useQuery({
    queryKey: ['map-geometry', 'overview'],
    queryFn: ({ signal }) => fetchMapGeometry('overview', signal),
    select: decodeGeometry,
    staleTime: Infinity,
  })
  const table = useQuery({
    queryKey: ['map-table'],
    queryFn: ({ signal }) => fetchMapTable(signal),
    staleTime: Infinity,
  })
  const point = useQuery({
    queryKey: ['map-point', picked?.lat, picked?.lon],
    queryFn: ({ signal }) => fetchMapPoint(picked?.lat ?? 0, picked?.lon ?? 0, signal),
    enabled: picked?.from === 'map',
    staleTime: Infinity,
  })

  const rows = useMemo(() => table.data?.rows ?? [], [table.data])
  const byId = useMemo(() => new Map(rows.map((r) => [r.id, r])), [rows])
  const sorted = useMemo(() => sortRows(rows, layer, profile, true), [rows, layer, profile])
  const searching = query.trim() !== ''
  const filtered = useMemo(
    () =>
      searching
        ? sorted.filter((r) => matches(r, query))
        : sorted.filter((r) => (r.population ?? 0) >= MIN_POPULATION),
    [sorted, query, searching],
  )

  const selectedRow: MapRow | null =
    picked?.from === 'map'
      ? point.data?.id != null
        ? (byId.get(point.data.id) ?? null)
        : null
      : picked
        ? (rows.find((r) => r.lat === picked.lat && r.lon === picked.lon) ?? null)
        : null
  const selectedId = picked?.from === 'map' ? (point.data?.id ?? null) : (selectedRow?.id ?? null)

  function setParam(key: string, value: string | null) {
    const next = new URLSearchParams(params)
    if (value === null) next.delete(key)
    else next.set(key, value)
    setParams(next, { replace: true })
  }

  const onPick = useCallback((lat: number, lon: number) => {
    opener.current = null
    setPicked({ lat, lon, from: 'map' })
    // On a phone the card covers the lower half of the screen: show the whole map above it.
    if (window.matchMedia('(width <= 760px)').matches) {
      document.querySelector('.atlas')?.scrollIntoView({ block: 'start' })
    }
  }, [])

  const onClose = useCallback(() => {
    setPicked(null)
    const back = opener.current
    opener.current = null
    back?.focus()
  }, [])

  const onReady = useCallback(() => {
    setMapReady(true)
    setLoadMs(Math.round(performance.now() - started.current))
  }, [])

  function pickRow(row: MapRow, button: HTMLElement) {
    opener.current = button
    setPicked({ lat: row.lat, lon: row.lon, from: 'table' })
    // Bring the map and the card into view; the card heading then takes the focus.
    document.querySelector('.atlas')?.scrollIntoView({ block: 'start' })
    focusCount.current += 1
    setFocus({ lat: row.lat, lon: row.lon, key: focusCount.current })
  }

  const sources = table.data?.sources[layer.id] ?? []
  const palette = PALETTES[theme]
  const date = formatDate(table.data?.profiles_date)

  return (
    <>
      <h1>Istraži kartu Hrvatske</h1>
      <p className="lead left">
        Naselja obojena prema okolišu, uslugama i prijevozu. Kliknite naselje za kratak pregled ili
        ga potražite u tablici ispod karte.
      </p>

      <div className="atlas-controls">
        <fieldset className="atlas-layers">
          <legend>Što prikazati</legend>
          <div className="chips">
            {LAYERS.map((l) => (
              <label key={l.id} className="chip">
                <input
                  type="radio"
                  name="sloj"
                  value={l.id}
                  checked={layer.id === l.id}
                  onChange={() => {
                    setParam('sloj', l.id === 'score' ? null : l.id)
                  }}
                />
                {l.title}
              </label>
            ))}
          </div>
        </fieldset>
        {layer.id === 'score' && (
          <label className="atlas-profile">
            Profil
            <select
              value={profile}
              onChange={(e) => {
                setParam('profil', e.target.value === 'opci' ? null : e.target.value)
              }}
            >
              {MAP_PROFILES.map((p) => (
                <option key={p} value={p}>
                  {getProfile(p).label}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      <div className={picked ? 'atlas has-card' : 'atlas'}>
        <div
          className="atlas-map-wrap"
          data-ready={mapReady && table.isSuccess ? 'true' : 'false'}
          data-load-ms={loadMs ?? undefined}
        >
          {geometry.isError || table.isError ? (
            <div className="atlas-map atlas-map-failed" role="alert">
              Karta trenutačno nije dostupna. Pokušajte ponovno za nekoliko trenutaka.
            </div>
          ) : (
            <CroatiaMap
              geometry={geometry.data ?? null}
              rows={rows}
              layer={layer.id}
              profile={profile}
              selectedId={selectedId}
              picked={picked}
              focus={focus}
              onPick={onPick}
              onReady={onReady}
            />
          )}
          {!mapReady && !geometry.isError && !table.isError && (
            <p className="atlas-loading" role="status">
              Učitavam naselja…
            </p>
          )}
        </div>

        <aside className="atlas-panel" aria-label="Odabrano naselje" aria-live="polite">
          {picked ? (
            <SettlementCard
              picked={picked}
              point={picked.from === 'map' ? (point.data ?? null) : null}
              row={selectedRow}
              loading={picked.from === 'map' && point.isPending}
              error={picked.from === 'map' && point.isError}
              profile={profile}
              profilesDate={table.data?.profiles_date ?? null}
              onClose={onClose}
            />
          ) : (
            <p className="hint atlas-placeholder">
              Kliknite naselje na karti ili ga odaberite u tablici ispod.
            </p>
          )}
        </aside>

        <section className="atlas-legend" aria-labelledby="legend-title">
          <h2 id="legend-title" className="atlas-legend-title">
            {layer.title}
            {layer.id === 'score' && `: ${getProfile(profile).label}`}
          </h2>
          <ul className="legend-list">
            {[...layer.classes].reverse().map((c) => (
              <li key={c.label}>
                <span className="legend-swatch" style={{ background: palette.steps[c.step] }} />
                {c.label}
              </li>
            ))}
            <li>
              <span className="legend-swatch" style={{ background: palette.none }} />
              Nema podataka
            </li>
          </ul>
          <p className="hint">
            {layer.explain} Vrijednosti su za naselje, a ne za pojedinu adresu.
          </p>
          <p className="fine-print">
            Izvori:{' '}
            {sources
              .map((s) => `${s.title}${s.retrieved_at ? ` (preuzeto ${formatDate(s.retrieved_at) ?? ''})` : ''}`)
              .join(' · ')}
            {date && `. Izračun za naselja: ${date}`} Granice naselja: DGU. Detalji na stranici{' '}
            <Link to="/o-alatu">Kako računamo</Link>.
          </p>
        </section>
      </div>

      <section className="section" aria-labelledby="table-title">
        <h2 id="table-title">{searching ? 'Pronađena naselja' : 'Najbolje ocijenjena naselja'}</h2>
        <div className="atlas-table-tools">
          <label htmlFor="atlas-search">
            Traži naselje
            <input
              id="atlas-search"
              type="search"
              value={query}
              placeholder="npr. Đakovo"
              onChange={(e) => {
                setQuery(e.target.value)
              }}
            />
          </label>
        </div>
        <p className="hint" aria-live="polite">
          {table.isPending
            ? 'Učitavam naselja…'
            : searching
              ? filtered.length === 0
                ? 'Nijedno naselje ne odgovara pretrazi.'
                : filtered.length > SHOWN
                  ? `Prvih ${String(SHOWN)} od ${filtered.length.toLocaleString('hr-HR')}; upišite više slova za užu pretragu.`
                  : ''
              : `Pet najboljih prema sloju „${layer.title}” među naseljima s najmanje ${String(MIN_POPULATION)} stanovnika.`}
        </p>
        <div className="table-scroll">
          <table className="place-table atlas-table">
            <caption className="visually-hidden">
              {searching ? 'Pronađena naselja' : `Najbolje ocijenjena naselja, sloj ${layer.title}`}
            </caption>
            <thead>
              <tr>
                <th scope="col">Naselje</th>
                <th scope="col" className="hide-narrow">
                  Grad ili općina
                </th>
                <th scope="col" className="num">
                  Stanovnika
                </th>
                <th scope="col">{layer.title}</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, SHOWN).map((r) => {
                const c = layer.classOf(r, profile)
                const step = c === null ? null : layer.classes[c]?.step
                return (
                  <tr key={r.id} className={selectedId === r.id ? 'selected' : undefined}>
                    <th scope="row">
                      <button
                        type="button"
                        className="link-button"
                        onClick={(e) => {
                          pickRow(r, e.currentTarget)
                        }}
                      >
                        {r.name}
                      </button>
                      <span className="show-narrow">{r.municipality !== r.name ? r.municipality : ''}</span>
                    </th>
                    <td className="hide-narrow">{r.municipality}</td>
                    <td className="num">{r.population === null ? '–' : r.population.toLocaleString('hr-HR')}</td>
                    <td>
                      <span
                        className="legend-swatch"
                        style={{ background: step == null ? palette.none : palette.steps[step] }}
                      />
                      {layer.text(r, profile)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}
