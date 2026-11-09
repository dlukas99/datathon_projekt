import { ChevronDown, CircleCheck, CircleHelp, Info, OctagonAlert, TriangleAlert } from 'lucide-react'
import type { Category, SourceInfo, Status, Value } from '../lib/api'
import { formatDate } from '../lib/format'
import { KindTag } from './KindTag'
import { CategoryIcon } from './Icons'
import { ScaleBar } from './ScaleBar'

const STATUS_ICONS = {
  good: CircleCheck,
  warning: TriangleAlert,
  bad: OctagonAlert,
  info: Info,
  no_data: CircleHelp,
} as const

/** Status in colour, shape and words: never colour alone. */
export function StatusBadge({ status, label }: { status: Status; label: string }) {
  const Icon = STATUS_ICONS[status]
  return (
    <span className={`status status-${status}`}>
      <Icon size={15} strokeWidth={2.4} aria-hidden="true" />
      {label}
    </span>
  )
}

export type SourceMap = Record<string, SourceInfo | undefined>

export function SourceMeta({
  source,
  retrievedAt,
  kind,
  sources,
}: {
  source: string
  retrievedAt: string | null
  /** Shown once per card (with the key number and in the details), not on every row. */
  kind?: Value['kind']
  sources: SourceMap
}) {
  const info = sources[source]
  const date = formatDate(retrievedAt ?? info?.retrieved_at)
  return (
    <span className="value-meta">
      {kind && <KindTag kind={kind} />}
      <span>
        Izvor: {info ? info.title : source}
        {info?.data_date ? ` (${info.data_date})` : ''}
      </span>
      {date && <span>preuzeto {date}</span>}
    </span>
  )
}

export function ValueItem({
  value,
  sources,
  showSource = true,
}: {
  value: Value
  sources: SourceMap
  showSource?: boolean
}) {
  return (
    <li className="value">
      <span className="value-label">{value.label}</span>
      <span className="value-display">{value.display}</span>
      {value.note && <span className="value-note">{value.note}</span>}
      {showSource && (
        <SourceMeta source={value.source} retrievedAt={value.retrieved_at} sources={sources} />
      )}
    </li>
  )
}

/** All values share one source, date and kind: show the provenance once. */
function sharedSource(values: Value[]): Value | null {
  const first = values[0]
  if (!first || values.length < 2) return null
  const same = values.every(
    (v) =>
      v.source === first.source && v.kind === first.kind && v.retrieved_at === first.retrieved_at,
  )
  return same ? first : null
}

// The one number people look for first in each category.
const KEY_VALUE: Record<string, string> = {
  flood: 'flood_30y_probability',
  green: 'tree_share_300m',
  noise: 'distance_road',
  fire: 'burnt_areas_2km',
  solar: 'pv_kwh_per_kwp',
}

const FLOOD_RPS = [10, 100, 500]

// Air shows only a rating on its card; the WHO and EU scales are in the details.
const SCALES_IN_DETAILS = new Set<string>(['air'])

function FloodTable({ values }: { values: Value[] }) {
  const byKey = Object.fromEntries(values.map((v) => [v.key, v]))
  return (
    <table className="mini-table">
      <caption className="visually-hidden">
        Modelirana poplavna područja po povratnom razdoblju
      </caption>
      <thead>
        <tr>
          <th scope="col">Povratno razdoblje</th>
          <th scope="col">Na adresi</th>
          <th scope="col">Do 100 m</th>
        </tr>
      </thead>
      <tbody>
        {FLOOD_RPS.map((rp) => (
          <tr key={rp}>
            <th scope="row">{rp} godina</th>
            <td>{byKey[`flood_rp${String(rp)}_point`]?.display ?? 'nema podataka'}</td>
            <td>{byKey[`flood_rp${String(rp)}_100m`]?.display ?? 'nema podataka'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

/** Details, caveats, links and provenance, folded away until asked for. */
export function MoreDetails({
  category,
  sources,
  children,
}: {
  category: Category
  sources: SourceMap
  children?: React.ReactNode
}) {
  const shared =
    category.id === 'flood' ? (category.values[0] ?? null) : sharedSource(category.values)
  const kinds = [...new Set(category.values.map((v) => v.kind))]
  return (
    <details className="more">
      <summary>
        Detalji i izvor <ChevronDown size={16} aria-hidden="true" className="chevron" />
      </summary>
      <div className="more-body">
        {!shared && kinds.length > 0 && (
          <p className="value-meta kinds">
            {kinds.map((k) => (
              <KindTag key={k} kind={k} />
            ))}
          </p>
        )}
        {children}
        {SCALES_IN_DETAILS.has(category.id) &&
          category.scales?.map((s) => <ScaleBar key={s.key} scale={s} />)}
        {category.id === 'flood' && category.values.length > 0 ? (
          <FloodTable values={category.values} />
        ) : (
          category.values.length > 0 && (
            <ul className="values">
              {category.values.map((v) => (
                <ValueItem key={v.key} value={v} sources={sources} showSource={!shared} />
              ))}
            </ul>
          )
        )}
        {shared && (
          <p className="shared-source">
            <SourceMeta
              source={shared.source}
              retrievedAt={shared.retrieved_at}
              kind={shared.kind}
              sources={sources}
            />
          </p>
        )}
        {category.notes.length > 0 && (
          <ul className="notes">
            {category.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        )}
        {category.links.length > 0 && (
          <ul className="links">
            {category.links.map((l) => (
              <li key={l.url}>
                <a href={l.url} target="_blank" rel="noreferrer">
                  {l.label}
                  <span className="visually-hidden"> (otvara se u novoj kartici)</span>
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </details>
  )
}

export function CategoryCard({
  category,
  sources,
  focused = false,
}: {
  category: Category
  sources: SourceMap
  focused?: boolean
}) {
  const titleId = `cat-${category.id}`
  const keyName =
    category.id === 'green' &&
    !category.values.some((v) => v.key === 'urban_area' && v.value === 1)
      ? 'nature_share_300m'
      : KEY_VALUE[category.id]
  const key = category.values.find((v) => v.key === keyName)
  return (
    <article
      className={`card category${focused ? ' focused' : ''}`}
      aria-labelledby={titleId}
      data-category={category.id}
    >
      {/* The name, status and key value; a column of its own where categories are rows. */}
      <div className="category-head">
        <div className="card-top">
          <span className="card-icon">
            <CategoryIcon id={category.id} />
          </span>
          <StatusBadge status={category.status} label={category.status_label} />
        </div>
        <h3 id={titleId}>{category.title}</h3>
        {focused && <p className="focus-tag">Važno za odabrani profil</p>}
        {key && (
          <p className="key-value">
            <span className="key-number">{key.display}</span>
            <span className="key-label">{key.label}</span>
            <KindTag kind={key.kind} />
          </p>
        )}
      </div>
      {!SCALES_IN_DETAILS.has(category.id) &&
        category.scales?.map((s) => <ScaleBar key={s.key} scale={s} />)}
      <p className="headline">{category.headline}</p>
      <MoreDetails category={category} sources={sources} />
    </article>
  )
}
