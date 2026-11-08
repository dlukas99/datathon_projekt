import { type CSSProperties, type ReactNode, useEffect, useRef, useState } from 'react'
import type { Category, Scale, Value } from '../lib/api'
import { MoreDetails, type SourceMap, StatusBadge } from './CategoryCard'
import { CategoryIcon } from './Icons'

/**
 * The environment overview as a rack of instruments: one drawn gauge per category, each
 * showing the report's own values (nothing here is computed beyond simple ratios of them).
 * Every drawing is decorative; the numbers and sentences beside it carry the meaning.
 */

function reducedMotion(): boolean {
  return (
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
}

/** True once the element has been on screen: the gauge then moves to its reading, once. */
function useSeen<T extends Element>(): [React.RefObject<T | null>, boolean] {
  const ref = useRef<T>(null)
  const [seen, setSeen] = useState(
    () => typeof IntersectionObserver !== 'function' || reducedMotion(),
  )
  useEffect(() => {
    const el = ref.current
    if (seen || !el) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setSeen(true)
          observer.disconnect()
        }
      },
      { threshold: 0.3 },
    )
    observer.observe(el)
    return () => {
      observer.disconnect()
    }
  }, [seen])
  return [ref, seen]
}

const num = (n: number, digits = 1) => n.toLocaleString('hr-HR', { maximumFractionDigits: digits })

function valueOf(c: Category, key: string): Value | undefined {
  return c.values.find((v) => v.key === key)
}

function numberOf(c: Category, key: string): number | null {
  const v = valueOf(c, key)?.value
  return typeof v === 'number' && Number.isFinite(v) ? v : null
}

/** "80 m (županijska cesta Ž4290)" → ["80 m", "županijska cesta Ž4290"] */
function splitDisplay(display: string): [string, string | null] {
  const m = /^(.*?)\s*\((.*)\)\s*$/.exec(display)
  return m ? [m[1] ?? display, m[2] ?? null] : [display, null]
}

interface ReadoutProps {
  big: ReactNode
  unit?: string | null
  label: ReactNode
  extra?: ReactNode
}

function Readout({ big, unit, label, extra }: ReadoutProps) {
  return (
    <div className="readout">
      <p className="readout-main">
        <span className="readout-big">{big}</span>
        {unit && <span className="readout-unit">{unit}</span>}
      </p>
      <p className="readout-label">{label}</p>
      {extra}
    </div>
  )
}

/* Poplave: a water gauge. The three modelled floods are three water layers, the frequent
   one deepest; the house sits at the level of the first flood that reaches the address. */

const FLOOD_RPS = [10, 100, 500] as const
const LEVEL_Y: Record<number, number> = { 500: 40, 100: 72, 10: 104 }

function floodFacts(c: Category) {
  const flag = (k: string) => {
    const v = valueOf(c, k)?.value
    return typeof v === 'boolean' ? v : null
  }
  const rows = FLOOD_RPS.map((rp) => ({
    rp,
    point: flag(`flood_rp${String(rp)}_point`),
    near: flag(`flood_rp${String(rp)}_100m`),
  }))
  const known = rows.some((r) => r.point !== null)
  const first = rows.find((r) => r.point === true)?.rp ?? null
  return { rows, known, first }
}

function FloodGauge({ c }: { c: Category }) {
  const { rows, known, first } = floodFacts(c)
  // House base: under the first flood that reaches it, or above the highest one.
  const base = first === null ? 36 : (LEVEL_Y[first] ?? 36) + 10
  return (
    <div className="flood-gauge">
      <svg viewBox="0 0 320 150" className="gauge-svg" aria-hidden="true" focusable="false">
        <g className="flood-water">
          <path className="water w500" d="M40 40 Q 60 34 80 40 T 120 40 T 160 40 T 200 40 T 240 40 T 280 40 T 320 40 V 150 H 40 Z" />
          <rect className="water w100" x="40" y="72" width="280" height="78" />
          <rect className="water w10" x="40" y="104" width="280" height="46" />
        </g>
        {FLOOD_RPS.map((rp) => (
          <g key={rp} className="flood-level">
            <line x1="40" x2="320" y1={LEVEL_Y[rp]} y2={LEVEL_Y[rp]} />
            <text x="0" y={(LEVEL_Y[rp] ?? 0) + 4}>
              {rp} g
            </text>
          </g>
        ))}
        <g className="flood-house" style={{ '--base': `${String(base)}px` } as CSSProperties}>
          <path d={`M222 ${String(base)} V ${String(base - 20)} L 240 ${String(base - 34)} L 258 ${String(base - 20)} V ${String(base)} Z`} />
          <line x1="212" x2="268" y1={base} y2={base} />
        </g>
      </svg>
      {known && (
        <dl className="flood-rows">
          {[...rows].reverse().map((r) => (
            <div key={r.rp} className={r.point ? 'wet' : r.near ? 'near' : undefined}>
              <dt>{r.rp} godina</dt>
              <dd>
                adresa: <strong>{r.point === null ? '?' : r.point ? 'da' : 'ne'}</strong>
                <span aria-hidden="true"> · </span>
                <span className="visually-hidden">, </span>
                do 100 m: <strong>{r.near === null ? '?' : r.near ? 'da' : 'ne'}</strong>
              </dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  )
}

function floodReadout(c: Category): ReadoutProps {
  const { known, first, rows } = floodFacts(c)
  if (!known) return { big: 'Nema podataka', label: 'za modelirana poplavna područja' }
  if (first !== null)
    return {
      big: 'Unutar',
      label: `modeliranog poplavnog područja za povratno razdoblje od ${String(first)} godina`,
    }
  const near = rows.find((r) => r.near)?.rp
  return {
    big: 'Izvan',
    label: near
      ? `modeliranih poplavnih područja; područje za ${String(near)} godina je unutar 100 m`
      : 'modeliranih poplavnih područja za 10, 100 i 500 godina',
  }
}

/* Zrak: two rulers with the WHO and EU limits; the needle settles at the annual mean. */

const POLLUTANT: Record<string, ReactNode> = {
  pm25: 'PM2,5',
  no2: (
    <>
      NO<sub>2</sub>
    </>
  ),
}

function rulerMax(scale: Scale): number {
  const finite = scale.bands.map((b) => b.upto).filter((u): u is number => u !== null)
  const last = finite[finite.length - 1] ?? scale.value
  return Math.max(last * 1.3, scale.value * 1.1)
}

function AirRuler({
  scale,
  selected,
  onSelect,
}: {
  scale: Scale
  selected: boolean
  onSelect: () => void
}) {
  const max = rulerMax(scale)
  const pct = (v: number) => `${String(Math.min(v / max, 1) * 100)}%`
  const ends = scale.bands.map((b) => Math.min(b.upto ?? max, max))
  return (
    <button type="button" className="air-ruler" aria-pressed={selected} onClick={onSelect}>
      <span className="air-name">{POLLUTANT[scale.key] ?? scale.label}</span>
      <span className="air-value">
        {num(scale.value)} {scale.unit} · {scale.band}
      </span>
      <span className="ruler" aria-hidden="true">
        {scale.bands.map((b, i) => {
          const start = i === 0 ? 0 : (ends[i - 1] ?? 0)
          const end = ends[i] ?? max
          return (
            <span
              key={b.label}
              className={`ruler-band band-${String(i)}`}
              style={{ left: pct(start), width: `${String(((end - start) / max) * 100)}%` }}
            />
          )
        })}
        {scale.markers.map((m, i) => (
          <span
            key={m.label}
            className={i % 2 ? 'ruler-tick up' : 'ruler-tick'}
            style={{ left: pct(m.value) }}
          >
            <span className="ruler-tick-label">
              {m.label} {num(m.value)}
            </span>
          </span>
        ))}
        <span className="needle-track" style={{ '--to': pct(scale.value) } as CSSProperties}>
          <span className="needle" />
        </span>
      </span>
    </button>
  )
}

function AirInstrument({ c }: { c: Category }) {
  const scales = c.scales ?? []
  const [pick, setPick] = useState(scales[0]?.key ?? '')
  const scale = scales.find((s) => s.key === pick) ?? scales[0]
  if (!scale) return <Readout big="Nema podataka" label="za kvalitetu zraka" />
  const who = scale.markers.find((m) => m.label === 'WHO')
  const eu = scale.markers.find((m) => m.label.startsWith('EU 2030'))
  const valueLabel = c.values.find((v) => v.key.startsWith(scale.key))?.label
  const ratio = who ? scale.value / who.value : null
  return (
    <>
      <Readout
        big={num(scale.value)}
        unit={scale.unit}
        label={
          <>
            {POLLUTANT[scale.key]}, {valueLabel?.split(', ').slice(1).join(', ') ?? 'godišnji prosjek'}
          </>
        }
        extra={
          <ul className="readout-facts">
            {who && ratio !== null && (
              <li>
                {ratio > 1
                  ? `${num(ratio)} puta više od preporuke WHO-a (${num(who.value)} ${scale.unit})`
                  : `unutar preporuke WHO-a (${num(who.value)} ${scale.unit})`}
              </li>
            )}
            {eu && (
              <li>
                {scale.value > eu.value ? 'iznad' : 'unutar'} granice EU-a za 2030. ({num(eu.value)}{' '}
                {scale.unit})
              </li>
            )}
          </ul>
        }
      />
      <div className="air-rulers" role="group" aria-label="Onečišćivač za prikaz">
        {scales.map((s) => (
          <AirRuler
            key={s.key}
            scale={s}
            selected={s.key === scale.key}
            onSelect={() => {
              setPick(s.key)
            }}
          />
        ))}
      </div>
    </>
  )
}

/* Zelenilo: the 300 m circle as a hundred dots of land, coloured by land cover. */

const DOTS: { x: number; y: number }[] = (() => {
  const out: { x: number; y: number }[] = []
  for (let y = -6; y <= 6; y++)
    for (let x = -6; x <= 6; x++) if (x * x + y * y <= 5.65 * 5.65 && (x || y)) out.push({ x, y })
  // A fixed shuffle so cover looks like patches on the ground, not stripes.
  let seed = 7
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647
  return out
    .map((d) => ({ d, k: rnd() + Math.hypot(d.x - 2, d.y + 1) * 0.05 }))
    .sort((a, b) => a.k - b.k)
    .map(({ d }) => d)
})()

function GreenInstrument({ c }: { c: Category }) {
  const tree = numberOf(c, 'tree_share_300m')
  const green = numberOf(c, 'green_share_300m')
  const built = numberOf(c, 'built_share_300m')
  const park = valueOf(c, 'nearest_park')
  if (tree === null) return <Readout big="Nema podataka" label="za pokrov tla u krugu od 300 m" />
  const n = DOTS.length
  const nTree = Math.round((tree / 100) * n)
  const nGreen = green === null ? nTree : Math.max(nTree, Math.round((green / 100) * n))
  const nBuilt = built === null ? 0 : Math.min(n - nGreen, Math.round((built / 100) * n))
  const kind = (i: number) =>
    i < nTree ? 'tree' : i < nGreen ? 'grass' : i < nGreen + nBuilt ? 'built' : 'other'
  return (
    <>
      <Readout
        big={num(tree, 0)}
        unit="%"
        label="drveća u krugu od 300 m"
        extra={
          <ul className="readout-facts">
            <li>preporuka: najmanje 30 % (pravilo 3-30-300)</li>
            {park && <li>najbliži park: {park.display}</li>}
          </ul>
        }
      />
      <div className="green-gauge">
        <svg viewBox="-7 -7 14 14" className="gauge-svg dots" aria-hidden="true" focusable="false">
          <circle className="dots-edge" r="6.4" />
          {DOTS.map((d, i) => (
            <circle
              key={`${String(d.x)},${String(d.y)}`}
              className={`dot d-${kind(i)}`}
              cx={d.x}
              cy={d.y}
              r="0.36"
              style={{ '--i': i } as CSSProperties}
            />
          ))}
          <circle className="dots-home" r="0.5" />
        </svg>
        <ul className="dots-legend">
          <li className="lg-tree">Drveće {num(tree, 0)} %</li>
          {green !== null && <li className="lg-grass">Sve zelene površine {num(green, 0)} %</li>}
          {built !== null && <li className="lg-built">Izgrađeno {num(built, 0)} %</li>}
          <li className="lg-other">Ostalo (oranice, golo tlo)</li>
        </ul>
      </div>
    </>
  )
}

/* Prometnica: a ruler from the address to the nearest major road. */

const ROAD_RULER = 700

function NoiseInstrument({ c }: { c: Category }) {
  const road = valueOf(c, 'distance_road')
  const rail = valueOf(c, 'distance_rail')
  const metres = numberOf(c, 'distance_road')
  if (!road || metres === null) return <Readout big="Nema podataka" label="za udaljenost od prometnica" />
  const [dist, what] = splitDisplay(road.display)
  const at = Math.min(metres, ROAD_RULER) / ROAD_RULER
  const [big, unit] = dist.split(' ')
  return (
    <>
      <Readout
        big={big}
        unit={unit}
        label={what ? `do najbliže velike prometnice: ${what}` : 'do najbliže velike prometnice'}
        extra={
          rail && (
            <ul className="readout-facts">
              <li>pruga: {splitDisplay(rail.display)[0]}</li>
            </ul>
          )
        }
      />
      <div
        className="road-ruler"
        aria-hidden="true"
        style={{ '--at': at, '--beyond': metres > ROAD_RULER ? 1 : 0 } as CSSProperties}
      >
        <span className="road-zone z-near" style={{ width: `${String((300 / ROAD_RULER) * 100)}%` }} />
        <span className="road-zone z-edge" style={{ left: `${String((300 / ROAD_RULER) * 100)}%`, width: `${String((200 / ROAD_RULER) * 100)}%` }} />
        <span className="road-line" />
        <span className="road-home" />
        <span className="road-mark" />
        {[300, 500].map((m) => (
          <span key={m} className="road-tick" style={{ left: `${String((m / ROAD_RULER) * 100)}%` }}>
            {m} m
          </span>
        ))}
        <span className="road-tick end">{metres > ROAD_RULER ? '700 m +' : '700 m'}</span>
      </div>
    </>
  )
}

/* Požari: a radar of the 2 km circle; it sweeps once. Positions of fires are not drawn. */

function FireInstrument({ c }: { c: Category }) {
  const burnt = valueOf(c, 'burnt_areas_2km')
  if (!burnt || burnt.value === null) return <Readout big="Nema podataka" label="za opožarene površine" />
  return (
    <>
      <Readout big={burnt.display} label={burnt.label.toLowerCase()} />
      <svg viewBox="-60 -60 120 120" className="gauge-svg radar" aria-hidden="true" focusable="false">
        <circle r="56" />
        <circle r="28" />
        <line x1="-56" x2="56" y1="0" y2="0" />
        <line y1="-56" y2="56" x1="0" x2="0" />
        <path className="radar-sweep" d="M0 0 L0 -56 A56 56 0 0 1 48.5 -28 Z" />
        <circle className="radar-home" r="3.5" />
        <text x="3" y="-31">1 km</text>
        <text x="3" y="-59">2 km</text>
      </svg>
    </>
  )
}

/* Sunce: the sun's arc over a panel at the optimal slope. */

function SolarInstrument({ c }: { c: Category }) {
  const kwh = valueOf(c, 'pv_kwh_per_kwp')
  const slope = numberOf(c, 'pv_optimal_slope')
  if (!kwh || kwh.value === null) return <Readout big="Nema podataka" label="za proizvodnju sunčeve energije" />
  const [big] = kwh.display.split(' ')
  const a = ((slope ?? 30) * Math.PI) / 180
  const px = 40 + Math.cos(a) * 60
  const py = 110 - Math.sin(a) * 60
  return (
    <>
      <Readout
        big={big}
        unit="kWh"
        label="godišnje po kW snage panela"
        extra={
          slope !== null && (
            <ul className="readout-facts">
              <li>najbolji nagib panela: {num(slope, 0)}°</li>
            </ul>
          )
        }
      />
      <svg viewBox="0 0 240 120" className="gauge-svg sun" aria-hidden="true" focusable="false">
        <path className="sun-arc" d="M28 110 A92 92 0 0 1 212 110" />
        <line className="sun-ground" x1="0" x2="240" y1="110" y2="110" />
        <g className="sun-body">
          <circle cx="120" cy="18" r="11" />
        </g>
        <line className="sun-panel" x1="40" y1="110" x2={px} y2={py} />
        <path className="sun-angle" d={`M70 110 A30 30 0 0 0 ${String(40 + Math.cos(a) * 30)} ${String(110 - Math.sin(a) * 30)}`} />
        {slope !== null && (
          <text x="76" y="104">
            {num(slope, 0)}°
          </text>
        )}
      </svg>
    </>
  )
}

const INSTRUMENTS: Record<string, (props: { c: Category }) => ReactNode> = {
  air: AirInstrument,
  green: GreenInstrument,
  noise: NoiseInstrument,
  fire: FireInstrument,
  solar: SolarInstrument,
}

export function InstrumentPanel({
  category,
  sources,
  focused = false,
}: {
  category: Category
  sources: SourceMap
  focused?: boolean
}) {
  const [ref, seen] = useSeen<HTMLElement>()
  const titleId = `cat-${category.id}`
  const Body = INSTRUMENTS[category.id]
  return (
    <article
      ref={ref}
      className={`inst inst-${category.id}${focused ? ' focused' : ''}`}
      aria-labelledby={titleId}
      data-category={category.id}
      data-on={seen ? 'true' : 'false'}
    >
      <div className="inst-head">
        <span className="inst-icon">
          <CategoryIcon id={category.id} size={22} />
        </span>
        <h3 id={titleId}>{category.title}</h3>
        <StatusBadge status={category.status} label={category.status_label} />
      </div>
      {focused && <p className="focus-tag">Važno za odabrani profil</p>}
      <div className="inst-body">
        {category.id === 'flood' ? (
          <>
            <Readout {...floodReadout(category)} />
            <FloodGauge c={category} />
          </>
        ) : Body ? (
          <Body c={category} />
        ) : null}
      </div>
      <p className="headline">{category.headline}</p>
      <MoreDetails category={category} sources={sources} />
    </article>
  )
}
