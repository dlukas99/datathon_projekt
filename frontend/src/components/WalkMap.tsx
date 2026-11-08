import { Check } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import type { Place, Report } from '../lib/api'
import { metresLabel, minutesText } from '../lib/format'
import {
  type CategoryStats,
  categoryStats,
  nearestWord,
  PLACE_COLORS,
  PLACE_LABELS,
  PLACE_NAMES,
  PLACE_ORDER,
  placeKey,
  placeTitle,
  WALK_LIMIT_MIN,
} from '../lib/places'
import {
  type RouteClient,
  routeAnnouncement,
  routeClient as sharedClient,
  RouteError,
  type RouteFailure,
  routeKey,
  ROUTE_MESSAGES,
  straightDistance,
  type WalkRoute,
} from '../lib/route'
import { type SourceMap, SourceMeta } from './CategoryCard'
import { ISOCHRONE_COLORS, ReportMap } from './ReportMap'

/** What the walking route shows. Kept by the report page, so it survives a new point. */
export interface WalkFocus {
  category: string
  /** A chosen place; null means the nearest place of the category. */
  place: Place | null
  /** Scroll to the map and focus the route details (a click in the daily list). */
  reveal?: boolean
}

type RouteResult = { key: string; route: WalkRoute } | { key: string; failure: RouteFailure }

function isEditable(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))
  )
}

function prefersReducedMotion(): boolean {
  return (
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
}

function capitalise(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1)
}

/** The place the route goes to: the chosen one if it is on this map, else the nearest. */
function routeTarget(
  focus: WalkFocus | null,
  stats: CategoryStats | undefined,
  places: Place[],
): Place | null {
  if (!focus || !stats) return null
  if (focus.place) {
    const key = placeKey(focus.place)
    const match = places.find((p) => placeKey(p) === key)
    if (match) return match
  }
  return stats.nearest
}

function IsochroneLegend({ places }: { places: Place[] }) {
  const bands = [5, 10, WALK_LIMIT_MIN].map((limit) => {
    const counts = new Map<string, number>()
    for (const category of PLACE_ORDER) {
      const n = places.filter(
        (p) => p.category === category && p.walk_minutes !== null && p.walk_minutes <= limit,
      ).length
      if (n > 0) counts.set(category, n)
    }
    return { limit, counts }
  })
  return (
    <ul className="iso-legend">
      {bands.map(({ limit, counts }) => (
        <li key={limit}>
          <span
            className="legend-swatch"
            style={{ background: ISOCHRONE_COLORS[limit] }}
            aria-hidden="true"
          />
          <span>
            <strong>{limit} minuta</strong>{' '}
            <span className="legend-text">
              {counts.size === 0
                ? 'ništa od prikazanog'
                : [...counts]
                    .map(([category, n]) => `${PLACE_NAMES[category] ?? category} ${String(n)}`)
                    .join(' · ')}
            </span>
          </span>
        </li>
      ))}
    </ul>
  )
}

export function WalkMap({
  report,
  places,
  sources,
  onPick,
  focus,
  onFocus,
  client = sharedClient,
}: {
  report: Report
  /** Places with a walking time (report.nearby_places). */
  places: Place[]
  sources: SourceMap
  onPick?: (lat: number, lon: number) => void
  focus: WalkFocus | null
  onFocus: (focus: WalkFocus | null) => void
  client?: RouteClient
}) {
  const stats = useMemo(
    () => new Map(PLACE_ORDER.map((category) => [category, categoryStats(places, category)])),
    [places],
  )
  const active = focus?.category ?? null
  const activeStats = active ? stats.get(active) : undefined
  const target = routeTarget(focus, activeStats, places)
  const from = report.location
  const [attempt, setAttempt] = useState(0)
  const [result, setResult] = useState<RouteResult | null>(null)
  const [cleared, setCleared] = useState(false)
  const wrap = useRef<HTMLDivElement>(null)
  const panel = useRef<HTMLDivElement>(null)
  const chips = useRef(new Map<string, HTMLButtonElement>())
  const requestKey = target ? `${routeKey(from, target)}#${String(attempt)}` : null

  // Ask for the route only now, on the user's choice. Choosing another place cancels the
  // request in flight.
  useEffect(() => {
    if (!target || !requestKey) return
    const controller = new AbortController()
    client.get(from, target, controller.signal).then(
      (route) => {
        setResult({ key: requestKey, route })
      },
      (error: unknown) => {
        if (error instanceof RouteError && error.reason === 'aborted') return
        const failure =
          error instanceof RouteError && error.reason !== 'aborted' ? error.reason : 'unavailable'
        setResult({ key: requestKey, failure })
      },
    )
    return () => {
      controller.abort()
    }
  }, [client, from, target, requestKey])

  useEffect(() => {
    if (!focus) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' || e.defaultPrevented || isEditable(e.target)) return
      setCleared(true)
      onFocus(null)
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
    }
  }, [focus, onFocus])

  useEffect(() => {
    if (!focus?.reveal) return
    wrap.current?.scrollIntoView({
      behavior: prefersReducedMotion() ? 'auto' : 'smooth',
      block: 'start',
    })
    panel.current?.focus({ preventScroll: true })
  }, [focus])

  const current = result && result.key === requestKey ? result : null
  const route: WalkRoute | null =
    current && 'route' in current
      ? current.route
      : ((target && client.cached(from, target)) ?? null)
  const failure = current && 'failure' in current ? current.failure : null
  const status = !target ? 'idle' : route ? 'ready' : failure ? 'error' : 'loading'
  // Minutes as in the list "Svakodnevni život" (same router and speed; the route's own
  // time differs by at most a few seconds).
  const minutes = target?.walk_minutes ?? route?.minutes ?? null

  function choose(next: WalkFocus | null) {
    setCleared(next === null)
    onFocus(next)
  }

  // The button that was pressed disappears with the panel: keep the keyboard focus on the
  // category it belonged to, without scrolling the page.
  function clear() {
    const category = active
    choose(null)
    if (category) chips.current.get(category)?.focus({ preventScroll: true })
  }

  function showNext() {
    if (!active || !activeStats || !target) return
    const list = activeStats.candidates
    const index = list.findIndex((p) => placeKey(p) === placeKey(target))
    const next = list[(index + 1) % list.length]
    if (next) choose({ category: active, place: next })
  }

  let live = ''
  if (focus && target && status === 'ready' && route && minutes !== null) {
    live = routeAnnouncement(placeTitle(target), minutes, route.distanceM)
  } else if (focus && target && failure) {
    live = ROUTE_MESSAGES[failure]
  } else if (!focus && cleared) {
    live = 'Put je uklonjen.'
  }

  const rank =
    activeStats && target
      ? activeStats.candidates.findIndex((p) => placeKey(p) === placeKey(target))
      : -1
  const kicker = !active
    ? ''
    : rank === 0
      ? `${capitalise(nearestWord(active))} ${PLACE_NAMES[active] ?? active}`
      : rank > 0
        ? `${String(rank + 1)}. ${nearestWord(active)} ${PLACE_NAMES[active] ?? active}`
        : (PLACE_LABELS[active] ?? active)
  const color = active ? PLACE_COLORS[active] : undefined

  return (
    <div className="map-wrap" ref={wrap} id="karta-hoda">
      <ReportMap
        report={report}
        places={places}
        activeCategory={active}
        target={target}
        route={status === 'ready' ? route : null}
        onPick={onPick}
        onShowRoute={(place) => {
          choose({ category: place.category, place })
        }}
      >
        {focus && (
          <div
            className="route-panel"
            ref={panel}
            tabIndex={-1}
            role="group"
            aria-label="Pješački put"
          >
            <p className="route-kicker">
              <span className="dot" style={{ background: color }} aria-hidden="true" />
              {kicker}
            </p>
            {target ? (
              <p className="route-title">{placeTitle(target)}</p>
            ) : (
              <p className="route-status">Nema podataka u blizini.</p>
            )}
            {status === 'loading' && <p className="route-status">Računam pješački put…</p>}
            {status === 'ready' && route && minutes !== null && (
              <>
                <p className="route-summary">
                  <strong>{minutesText(minutes)}</strong> · {metresLabel(route.distanceM)}{' '}
                  pješice
                </p>
                <SourceMeta
                  source={route.source}
                  retrievedAt={route.retrievedAt}
                  kind={route.kind}
                  sources={sources}
                />
              </>
            )}
            {status === 'error' && failure && target && (
              <p className="route-error">
                {ROUTE_MESSAGES[failure]} Zračna udaljenost:{' '}
                {metresLabel(straightDistance(from, target))}.
              </p>
            )}
            <div className="button-row">
              {status === 'error' && (
                <button
                  type="button"
                  className="button ghost small"
                  onClick={() => {
                    setAttempt((n) => n + 1)
                  }}
                >
                  Pokušaj ponovno
                </button>
              )}
              {activeStats && activeStats.candidates.length > 1 && (
                <button type="button" className="button ghost small" onClick={showNext}>
                  Sljedeći najbliži
                </button>
              )}
              <button type="button" className="button ghost small" onClick={clear}>
                Ukloni put
              </button>
            </div>
          </div>
        )}
      </ReportMap>
      <p className="visually-hidden" role="status">
        {live}
      </p>
      <div className="walk-legend">
        <h3 className="legend-title">Najbliže pješice</h3>
        <p className="muted-note no-print">
          Odaberite stavku za pješački put do nje
          {onPick ? '; klik na kartu otvara izvještaj za tu točku.' : '.'}
        </p>
        <ul className="place-chips">
          {PLACE_ORDER.map((category) => {
            const s = stats.get(category)
            const nearest = s?.nearest ?? null
            const pressed = active === category
            return (
              <li key={category}>
                <button
                  type="button"
                  className="place-chip"
                  aria-pressed={pressed}
                  disabled={!nearest}
                  ref={(el) => {
                    if (el) chips.current.set(category, el)
                    else chips.current.delete(category)
                  }}
                  onClick={() => {
                    choose(pressed ? null : { category, place: null })
                  }}
                >
                  <span
                    className="dot"
                    style={{ background: PLACE_COLORS[category] }}
                    aria-hidden="true"
                  />
                  {pressed && <Check size={16} aria-hidden="true" className="chip-check" />}
                  <span className="place-chip-text">
                    <span className="place-chip-name">{PLACE_LABELS[category]}</span>
                    <span className="place-chip-meta">
                      {nearest && nearest.walk_minutes !== null
                        ? ` – ${minutesText(nearest.walk_minutes)}`
                        : ' – nije u blizini'}
                    </span>
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
        <details className="more walk-more">
          <summary>Koliko je mjesta unutar 5, 10 i 15 minuta</summary>
          <div className="more-body">
            <IsochroneLegend places={places} />
          </div>
        </details>
      </div>
    </div>
  )
}
