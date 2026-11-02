import { useQuery } from '@tanstack/react-query'
import { fetchLiveSources, fetchSources } from '../lib/api'
import { formatDate } from '../lib/format'

export function SourcesPage() {
  const sources = useQuery({ queryKey: ['sources'], queryFn: ({ signal }) => fetchSources(signal) })
  const live = useQuery({
    queryKey: ['sources-live'],
    queryFn: ({ signal }) => fetchLiveSources(signal),
  })

  return (
    <>
      <h1>Izvori podataka</h1>
      <p className="section-intro">
        Svi podaci su otvoreni. Uz svaki izvor navedeni su izdavač, licenca i datum kad smo ga
        preuzeli. Na Portalu otvorenih podataka provjeravamo uživo kad je koji skup zadnji put
        osvježen.
      </p>

      <section className="section" aria-labelledby="live-title">
        <h2 id="live-title">Uživo s Portala otvorenih podataka (data.gov.hr)</h2>
        {live.isPending && (
          <p role="status" aria-live="polite">
            Provjeravam Portal…
          </p>
        )}
        {live.isError && (
          <p className="error-box" role="alert">
            Portal trenutačno ne odgovara; datumi uživo nisu dostupni.
          </p>
        )}
        {live.data && !live.data.available && (
          <p className="disclaimer">
            Portal trenutačno ne odgovara. Prikazani su zadnji poznati datumi (provjereno{' '}
            {formatDate(live.data.checked_at)}).
          </p>
        )}
        {live.data && (
          <div style={{ overflowX: 'auto' }}>
            <table className="place-table">
              <caption className="visually-hidden">Skupovi s Portala i datum zadnje izmjene</caption>
              <thead>
                <tr>
                  <th scope="col">Skup podataka</th>
                  <th scope="col">Izdavač</th>
                  <th scope="col">Zadnja izmjena na Portalu</th>
                </tr>
              </thead>
              <tbody>
                {live.data.datasets.map((d) => (
                  <tr key={d.ckan_name}>
                    <td>
                      <a href={d.url} target="_blank" rel="noreferrer">
                        {d.title}
                      </a>
                    </td>
                    <td>{d.organization}</td>
                    <td>{formatDate(d.metadata_modified) ?? 'nepoznato'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="section" aria-labelledby="all-title">
        <h2 id="all-title">Svi izvori</h2>
        {sources.isPending && <p role="status">Učitavam…</p>}
        {sources.isError && (
          <p className="error-box" role="alert">
            Popis izvora trenutačno nije dostupan.
          </p>
        )}
        <ul className="source-list">
          {sources.data?.map((s) => (
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
      </section>

      <section className="section" aria-labelledby="quality-title">
        <h2 id="quality-title">Što smo naučili o kvaliteti podataka</h2>
        <QualityFindings />
      </section>
    </>
  )
}

function QualityFindings() {
  return (
    <ul>
      <li>
        Registar dječjih vrtića i popis osnovnih škola nemaju koordinate; geokodirali smo ih
        vlastitim geokoderom nad adresama Državne geodetske uprave. Registar vrtića navodi pravne
        osobe, a ne sve objekte, a popis škola nema područne škole.
      </li>
      <li>
        Popisi ugovornih ordinacija i ljekarni HZZO-a objavljeni su kao tablice bez koordinata i
        bez navedene licence; popis ljekarni zadnji je put izmijenjen u rujnu 2023.
      </li>
      <li>
        Općine objavljuju lokacije reciklažnih dvorišta i zelenih otoka u desetak različitih
        oblika (CSV, XLSX, PDF, poveznice na web stranice); koordinate ima tek manji dio skupova.
      </li>
      <li>
        Poveznica na vozni red HŽPP-a na Portalu ne radi (404), dok datoteka na stranicama HŽPP-a
        radi i osvježava se svakodnevno.
      </li>
    </ul>
  )
}
