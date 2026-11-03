import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { AddressSearch } from '../components/AddressSearch'
import { Assistant } from '../components/Assistant'
import { StatusBadge } from '../components/CategoryCard'
import { fetchReport, type Report } from '../lib/api'
import { comparePath, parsePoint, type Point, reportPath } from '../lib/urls'
import { LoadingReport, placeLine, ReportError } from './ReportPage'

const ROWS = ['flood', 'air', 'green', 'noise', 'solar', 'car_free', 'transit']
const DAILY = [
  'kindergarten',
  'school',
  'doctor',
  'pediatrician',
  'pharmacy',
  'grocery',
  'playground',
  'recycling',
]

function useReport(point: Point | null) {
  return useQuery({
    queryKey: ['report', point?.lat, point?.lon],
    queryFn: ({ signal }) => {
      if (!point) throw new Error('no point')
      return fetchReport(point.lat, point.lon, signal)
    },
    enabled: point !== null,
  })
}

function name(point: Point, report: Report | undefined): string {
  return point.label ?? report?.location.label ?? `${point.lat.toFixed(5)}, ${point.lon.toFixed(5)}`
}

function CompareTable({ a, b, ra, rb }: { a: Point; b: Point; ra: Report; rb: Report }) {
  const cat = (r: Report, id: string) => r.categories.find((c) => c.id === id)
  const dailyValue = (r: Report, key: string) =>
    cat(r, 'daily')?.values.find((v) => v.key === `nearest_${key}`)
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="compare-table">
        <caption className="visually-hidden">Usporedba dviju adresa po kategorijama</caption>
        <thead>
          <tr>
            <th scope="col">Kategorija</th>
            <th scope="col">
              A: {name(a, ra)}
              <br />
              <span className="place-line">{placeLine(ra)}</span>
            </th>
            <th scope="col">
              B: {name(b, rb)}
              <br />
              <span className="place-line">{placeLine(rb)}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {ROWS.map((id) => {
            const ca = cat(ra, id)
            const cb = cat(rb, id)
            if (!ca || !cb) return null
            return (
              <tr key={id} data-category={id}>
                <th scope="row">{ca.title}</th>
                {[ca, cb].map((c, i) => (
                  <td key={i}>
                    <StatusBadge status={c.status} label={c.status_label} />
                    <p style={{ marginTop: '0.4rem' }}>{c.headline}</p>
                  </td>
                ))}
              </tr>
            )
          })}
          {DAILY.map((key) => {
            const va = dailyValue(ra, key)
            const vb = dailyValue(rb, key)
            if (!va || !vb) return null
            return (
              <tr key={key}>
                <th scope="row">{va.label}</th>
                <td>{va.display}</td>
                <td>{vb.display}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export function ComparePage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const a = parsePoint(params.get('a'), params.get('la'))
  const b = parsePoint(params.get('b'), params.get('lb'))
  const qa = useReport(a)
  const qb = useReport(b)

  return (
    <>
      <h1>Usporedba dviju adresa</h1>
      <p className="section-intro">
        Iste kategorije, jedna uz drugu. Vrijednosti se ne zbrajaju u skupnu ocjenu: odlučite sami
        što vam je važno.
      </p>
      <div className="compare-grid no-print">
        {(['a', 'b'] as const).map((slot) => {
          const point = slot === 'a' ? a : b
          return (
            <div key={slot} className="card">
              <AddressSearch
                key={`${slot}-${point?.label ?? ''}`}
                label={slot === 'a' ? 'Adresa A' : 'Adresa B'}
                inputId={`compare-${slot}`}
                initialValue={point?.label ?? ''}
                onSelect={(s) => {
                  const picked = { lat: s.lat, lon: s.lon, label: s.label }
                  void navigate(comparePath(slot === 'a' ? picked : a, slot === 'b' ? picked : b))
                }}
              />
              {point && (
                <p style={{ marginTop: '0.5rem' }}>
                  <Link to={reportPath(point.lat, point.lon, point.label, 'opci')}>
                    Cijeli pregled za adresu {slot.toUpperCase()}
                  </Link>
                </p>
              )}
            </div>
          )
        })}
      </div>
      {(!a || !b) && <p style={{ marginTop: '1rem' }}>Odaberite obje adrese za usporedbu.</p>}
      {a && b && (qa.isPending || qb.isPending) && <LoadingReport />}
      {qa.isError && <ReportError error={qa.error} />}
      {qb.isError && <ReportError error={qb.error} />}
      {a && b && qa.data && qb.data && (
        <section className="section" aria-label="Rezultat usporedbe">
          <CompareTable a={a} b={b} ra={qa.data} rb={qb.data} />
          <Assistant points={[a, b]} />
          <p className="disclaimer">{qa.data.disclaimer}</p>
        </section>
      )}
    </>
  )
}
