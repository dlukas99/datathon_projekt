import { useQuery } from '@tanstack/react-query'
import { ChevronDown } from 'lucide-react'
import { fetchLiveSources, fetchSources } from '../lib/api'
import { formatDate, isoDatesToText } from '../lib/format'
import { groupSources, SOURCE_NOTES, type SourceGroup, type SourceRow } from '../lib/sourceGroups'

const NEW_TAB = <span className="visually-hidden"> (otvara se u novoj kartici)</span>

/** "preuzeto" for downloaded data, "izračunato" for what the application computes itself. */
function dateText(row: SourceRow, derived: boolean): string | null {
  const date = formatDate(row.retrieved_at)
  if (!date) return null
  return `${derived ? 'izračunato' : 'preuzeto'} ${date}`
}

/** Reference date of the data; timetables say which working day they describe. */
function dataDateText(row: SourceRow): string | null {
  if (!row.data_date) return null
  const text = isoDatesToText(row.data_date)
  return text.startsWith('radni dan') ? `vozni red za ${text}` : `podaci: ${text}`
}

function PortalTag() {
  return (
    <span className="portal-tag" title="Skup s Portala otvorenih podataka (data.gov.hr)">
      Portal
    </span>
  )
}

function SourceTitle({ row }: { row: SourceRow }) {
  if (!row.url) return <span className="source-title">{row.title}</span>
  return (
    <a className="source-title" href={row.url} target="_blank" rel="noreferrer">
      {row.title}
      {NEW_TAB}
    </a>
  )
}

function Row({ row, derived, note }: { row: SourceRow; derived: boolean; note?: string }) {
  const portalDate = formatDate(row.portalModified)
  const dataDate = dataDateText(row)
  const date = dateText(row, derived)
  return (
    <li className="source-row">
      <div className="source-head">
        <SourceTitle row={row} />
        {row.portal && <PortalTag />}
      </div>
      <p className="source-meta">
        <span>{row.publisher}</span>
        <span>{row.license}</span>
        {date && <span>{date}</span>}
        {dataDate && <span>{dataDate}</span>}
        {row.portal && portalDate && <span>zadnja izmjena na Portalu: {portalDate}</span>}
      </p>
      {note && <p className="source-note">Za: {note}</p>}
    </li>
  )
}

/** Municipal recycling datasets: one row that opens into the list of municipalities. */
function RecyclingRow({ rows }: { rows: SourceRow[] }) {
  const licences = [...new Set(rows.map((r) => r.license))].join(', ')
  const retrieved = [...new Set(rows.map((r) => formatDate(r.retrieved_at)).filter(Boolean))]
  return (
    <li className="source-row">
      <details className="source-fold">
        <summary>
          <span className="source-head">
            <span className="source-title">
              Reciklažna dvorišta i zeleni otoci: {rows.length} općinskih skupova
            </span>
            <PortalTag />
            <ChevronDown size={16} className="chevron" aria-hidden="true" />
          </span>
          <span className="source-meta">
            <span>gradovi i općine</span>
            <span>{licences}</span>
            {retrieved.length > 0 && <span>preuzeto {retrieved.join(', ')}</span>}
          </span>
        </summary>
        <ul className="source-sublist">
          {rows.map((r) => {
            const portalDate = formatDate(r.portalModified)
            return (
              <li key={r.id}>
                <a href={r.url} target="_blank" rel="noreferrer">
                  {r.publisher}
                  {NEW_TAB}
                </a>
                <span className="source-meta">
                  <span>{r.title}</span>
                  {portalDate && <span>zadnja izmjena na Portalu: {portalDate}</span>}
                </span>
              </li>
            )
          })}
        </ul>
      </details>
      <p className="source-note">
        Za: reciklažna dvorišta i zeleni otoci, uz spremnike za reciklažu iz OpenStreetMapa.
      </p>
    </li>
  )
}

function Group({ group }: { group: SourceGroup }) {
  const derived = group.id === 'derived'
  return (
    <div className="source-group">
      <h3>{group.title}</h3>
      <ul className="source-rows">
        {group.id === 'recycling' ? (
          <RecyclingRow rows={group.rows} />
        ) : (
          group.rows.map((r) => (
            <Row
              key={r.id}
              row={r}
              derived={derived}
              note={SOURCE_NOTES[r.id]}
            />
          ))
        )}
      </ul>
    </div>
  )
}

const TOOLS = [
  {
    name: 'JRC PVGIS 5.3',
    what: 'servis Europske komisije za sunce na krovu, upit uživo za točku',
    license: 'slobodna upotreba uz navođenje izvora',
    url: 'https://re.jrc.ec.europa.eu/pvg_tools/en/',
  },
  {
    name: 'Valhalla 3.9.1',
    what: 'usmjerivač za izokrone i vremena hoda, nad mrežom ulica iz OpenStreetMapa',
    license: 'MIT',
    url: 'https://github.com/valhalla/valhalla',
  },
  {
    name: 'OpenFreeMap',
    what: 'podloga karte',
    license: 'MIT; podaci © OpenMapTiles i suradnici OpenStreetMapa (ODbL)',
    url: 'https://openfreemap.org/',
  },
  {
    name: 'CKAN API Portala otvorenih podataka',
    what: 'datumi zadnje izmjene skupova s Portala, uživo',
    license: 'javni API',
    url: 'https://data.gov.hr/ckan/api/3',
  },
]

export function AboutSources() {
  const sources = useQuery({ queryKey: ['sources'], queryFn: ({ signal }) => fetchSources(signal) })
  const live = useQuery({
    queryKey: ['sources-live'],
    queryFn: ({ signal }) => fetchLiveSources(signal),
  })
  const groups = sources.data ? groupSources(sources.data, live.data) : []
  const portalCount = groups.flatMap((g) => g.rows).filter((r) => r.portal).length

  return (
    <section className="section about-section" aria-labelledby="izvori">
      <h2 id="izvori">Izvori podataka</h2>
      <p className="section-intro">
        Svi podaci su otvoreni. Uz svaki izvor su izdavač, licenca i datum preuzimanja.
        {portalCount > 0 && (
          <>
            {' '}
            Oznaka <PortalTag /> znači skup s Portala otvorenih podataka (data.gov.hr), ukupno{' '}
            {portalCount}; kad je koji zadnji put izmijenjen, provjeravamo uživo.
          </>
        )}
      </p>
      <p className="source-live" role="status" aria-live="polite">
        {live.isPending && 'Provjeravam datume na Portalu…'}
        {live.isError && 'Portal trenutačno ne odgovara; datumi izmjene na Portalu nisu dostupni.'}
        {live.data &&
          (live.data.available
            ? `Datumi s Portala provjereni ${formatDate(live.data.checked_at) ?? 'upravo'}`
            : `Portal trenutačno ne odgovara; prikazani su zadnji poznati datumi (provjereno ${formatDate(live.data.checked_at) ?? 'ranije'}).`)}
      </p>

      {sources.isPending && <p role="status">Učitavam izvore…</p>}
      {sources.isError && (
        <p className="error-box" role="alert">
          Popis izvora trenutačno nije dostupan. Potpun popis je u datoteci
          docs/IZVORI_PODATAKA.md u repozitoriju.
        </p>
      )}
      {groups.map((g) => (
        <Group key={g.id} group={g} />
      ))}

      <div className="source-group">
        <h3>Servisi i softver</h3>
        <ul className="source-rows">
          {TOOLS.map((t) => (
            <li key={t.name} className="source-row">
              <div className="source-head">
                <a className="source-title" href={t.url} target="_blank" rel="noreferrer">
                  {t.name}
                  {NEW_TAB}
                </a>
              </div>
              <p className="source-meta">
                <span>{t.what}</span>
                <span>{t.license}</span>
              </p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
