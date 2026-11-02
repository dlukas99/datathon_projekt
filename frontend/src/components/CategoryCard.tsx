import type { Category, SourceInfo, Status, Value } from '../lib/api'
import { formatDate, KIND_HELP, KIND_LABELS } from '../lib/format'

export function StatusBadge({ status, label }: { status: Status; label: string }) {
  return <span className={`status status-${status}`}>{label}</span>
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
  kind: Value['kind']
  sources: SourceMap
}) {
  const info = sources[source]
  const date = formatDate(retrievedAt ?? info?.retrieved_at)
  return (
    <span className="value-meta">
      <span className="kind" title={KIND_HELP[kind]}>
        {KIND_LABELS[kind]}
      </span>
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
      <div className="value-label">{value.label}</div>
      <div className="value-display">{value.display}</div>
      {value.note && <div className="value-label">{value.note}</div>}
      {showSource && (
        <SourceMeta
          source={value.source}
          retrievedAt={value.retrieved_at}
          kind={value.kind}
          sources={sources}
        />
      )}
    </li>
  )
}

/** All values share one source, date and kind: show the provenance once. */
function sharedSource(values: Value[]): Value | null {
  const first = values[0]
  if (!first || values.length < 2) return null
  const same = values.every(
    (v) => v.source === first.source && v.kind === first.kind && v.retrieved_at === first.retrieved_at,
  )
  return same ? first : null
}

const FLOOD_RPS = [10, 100, 500]

function FloodTable({ values }: { values: Value[] }) {
  const byKey = Object.fromEntries(values.map((v) => [v.key, v]))
  return (
    <table className="place-table" style={{ marginTop: '0.75rem' }}>
      <caption className="visually-hidden">Modelirana poplavna područja po povratnom razdoblju</caption>
      <thead>
        <tr>
          <th scope="col">Povratno razdoblje</th>
          <th scope="col">Na adresi</th>
          <th scope="col">U krugu od 100 m</th>
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

export function CategoryCard({
  category,
  sources,
  focused = false,
  headingLevel = 3,
}: {
  category: Category
  sources: SourceMap
  focused?: boolean
  headingLevel?: 3 | 4
}) {
  const Heading = headingLevel === 3 ? 'h3' : 'h4'
  const titleId = `cat-${category.id}`
  const shared = category.id === 'flood' ? (category.values[0] ?? null) : sharedSource(category.values)
  return (
    <article
      className={`card${focused ? ' focused' : ''}`}
      aria-labelledby={titleId}
      data-category={category.id}
    >
      <div className="card-header">
        <div>
          <Heading id={titleId}>{category.title}</Heading>
          {focused && <span className="focus-tag">Važno za odabrani profil</span>}
        </div>
        <StatusBadge status={category.status} label={category.status_label} />
      </div>
      <p className="headline">{category.headline}</p>
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
        <p style={{ marginTop: '0.5rem' }}>
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
        <ul className="notes">
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
    </article>
  )
}
