import { type CSSProperties, type ReactNode, useEffect, useRef, useState } from 'react'
import type { Category, Value } from '../lib/api'
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

/* Poplave, zrak i požari: one plain sentence first, one short explanation under it.
   The scenario table, numbers, limits and sources stay under "Detalji i izvor". */

function Statement({ text }: { text: string }) {
  // A sentence ends at a full stop followed by a capital letter ("2016. Satelit"), not at
  // an ordinal date inside it ("2017. do 2021.").
  const m = /\.\s+(?=[A-ZČĆĐŠŽ])/.exec(text)
  const first = m ? text.slice(0, m.index + 1) : text
  const rest = m ? text.slice(m.index + m[0].length) : ''
  return (
    <div className="readout statement">
      <p className="statement-main">{first}</p>
      {rest && <p className="readout-label">{rest}</p>}
    </div>
  )
}

/* Zrak: the rating in one word and a four-step scale; the WHO and EU limits are in the details. */

const AIR_STEPS = ['Vrlo dobar', 'Dobar', 'Umjeren', 'Loš'] as const

function AirInstrument({ c }: { c: Category }) {
  const at = AIR_STEPS.findIndex((s) => s === c.status_label)
  if (at === -1) return <Readout big="Nema podataka" label="za kvalitetu zraka" />
  return (
    <>
      <Readout big={c.status_label} label={c.headline} />
      <ol className="air-steps" aria-label="Ljestvica kvalitete zraka">
        {AIR_STEPS.map((step, i) => (
          <li key={step} className={`air-step step-${String(i)}`} aria-current={i === at ? 'true' : undefined}>
            {step}
          </li>
        ))}
      </ol>
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
  solar: SolarInstrument,
}

// These categories say everything in their sentence; the headline is not repeated below.
const SENTENCE_ONLY = new Set(['flood', 'fire'])
const NO_HEADLINE = new Set(['flood', 'fire', 'air'])

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
        {SENTENCE_ONLY.has(category.id) ? (
          <Statement text={category.headline} />
        ) : Body ? (
          <Body c={category} />
        ) : null}
      </div>
      {!NO_HEADLINE.has(category.id) && <p className="headline">{category.headline}</p>}
      <MoreDetails category={category} sources={sources} />
    </article>
  )
}
