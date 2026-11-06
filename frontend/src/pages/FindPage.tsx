import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router'
import {
  type FindRequest,
  fetchFindOptions,
  findPlaces,
  parseFindQuestion,
} from '../lib/api'
import { ListingLinks } from '../components/ListingLinks'
import { PROFILES } from '../lib/profiles'
import { reportPath } from '../lib/urls'

const NEEDS: { id: FindRequest['must'][number]; label: string }[] = [
  { id: 'kindergarten', label: 'Vrtić' },
  { id: 'school', label: 'Osnovna škola' },
  { id: 'doctor', label: 'Obiteljski liječnik' },
  { id: 'pediatrician', label: 'Pedijatar' },
  { id: 'pharmacy', label: 'Ljekarna' },
  { id: 'grocery', label: 'Trgovina' },
  { id: 'park', label: 'Park' },
  { id: 'transit', label: 'Prijevoz svaki sat' },
]

const DEFAULT: FindRequest = {
  profile: 'opci',
  county: null,
  size: 'any',
  must: [],
  max_air: 'any',
  avoid_flood: false,
  limit: 10,
}

export function FindPage() {
  const [form, setForm] = useState<FindRequest>(DEFAULT)
  const [question, setQuestion] = useState('')
  const options = useQuery({ queryKey: ['find-options'], queryFn: ({ signal }) => fetchFindOptions(signal) })
  const search = useMutation({ mutationFn: findPlaces })
  const parse = useMutation({
    mutationFn: parseFindQuestion,
    onSuccess: (filters) => {
      const next = { ...DEFAULT, ...filters, limit: 10 }
      setForm(next)
      search.mutate(next)
    },
  })

  function set<K extends keyof FindRequest>(key: K, value: FindRequest[K]) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  return (
    <>
      <p className="eyebrow">Predloži mjesto za život</p>
      <h1>Gdje bih mogao živjeti?</h1>
      <p className="lead left">
        Zadajte što vam je važno, a aplikacija predlaže naselja u kojima je to ispunjeno, s
        razlozima i poveznicom na cijeli izvještaj.
      </p>

      {options.data?.llm && (
        <form
          className="card find-ask no-print"
          onSubmit={(e) => {
            e.preventDefault()
            if (question.trim().length >= 3) parse.mutate(question.trim())
          }}
        >
          <label htmlFor="find-question">Opišite svojim riječima</label>
          <div className="assistant-form">
            <input
              id="find-question"
              type="text"
              maxLength={300}
              placeholder="npr. manje mjesto u Osječko-baranjskoj s vrtićem i školom, bez poplava"
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value)
              }}
            />
            <button type="submit" className="button" disabled={parse.isPending}>
              {parse.isPending ? 'Tumačim…' : 'Pretvori u filtre'}
            </button>
          </div>
          <p className="hint">
            Jezični model samo popunjava filtre ispod; rang i brojke računa aplikacija.
          </p>
          {parse.isError && <p role="alert">{parse.error.message}</p>}
        </form>
      )}

      <form
        className="card find-form"
        onSubmit={(e) => {
          e.preventDefault()
          search.mutate(form)
        }}
      >
        <div className="find-grid">
          <label>
            Za koga
            <select
              value={form.profile}
              onChange={(e) => {
                set('profile', e.target.value)
              }}
            >
              {PROFILES.filter((p) => p.id !== 'vlastiti').map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Područje
            <select
              value={form.county ?? ''}
              onChange={(e) => {
                set('county', e.target.value || null)
              }}
            >
              <option value="">Cijela Hrvatska</option>
              {options.data?.counties.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
          <label>
            Veličina mjesta
            <select
              value={form.size}
              onChange={(e) => {
                set('size', e.target.value as FindRequest['size'])
              }}
            >
              <option value="any">Bilo koja</option>
              <option value="village">Manje mjesto (do 2.000)</option>
              <option value="town">Gradić (2.000–20.000)</option>
              <option value="city">Grad (više od 20.000)</option>
            </select>
          </label>
          <label>
            Zrak
            <select
              value={form.max_air}
              onChange={(e) => {
                set('max_air', e.target.value as FindRequest['max_air'])
              }}
            >
              <option value="any">Bilo koji</option>
              <option value="umjerena">Umjeren ili bolji</option>
              <option value="niska">Dobar ili bolji</option>
            </select>
          </label>
        </div>
        <fieldset className="profiles">
          <legend>Pješice do 15 minuta mora biti</legend>
          <div className="chips">
            {NEEDS.map((n) => (
              <label key={n.id} className="chip">
                <input
                  type="checkbox"
                  checked={form.must.includes(n.id)}
                  onChange={(e) => {
                    set(
                      'must',
                      e.target.checked ? [...form.must, n.id] : form.must.filter((m) => m !== n.id),
                    )
                  }}
                />
                {n.label}
              </label>
            ))}
          </div>
        </fieldset>
        <label className="chip find-flood">
          <input
            type="checkbox"
            checked={form.avoid_flood}
            onChange={(e) => {
              set('avoid_flood', e.target.checked)
            }}
          />
          Izvan modeliranih poplavnih područja
        </label>
        <div className="button-row">
          <button type="submit" className="button" disabled={search.isPending}>
            {search.isPending ? 'Tražim…' : 'Predloži mjesta'}
          </button>
        </div>
      </form>

      <section className="section" aria-live="polite" aria-label="Prijedlozi">
        {search.isError && (
          <p className="error-box" role="alert">
            Prijedlozi trenutačno nisu dostupni. Pokušajte ponovno.
          </p>
        )}
        {search.data && (
          <>
            <h2>
              {search.data.results.length > 0
                ? `Najbolje ${String(search.data.results.length)} od ${search.data.matching.toLocaleString('hr-HR')} naselja`
                : 'Nijedno naselje ne ispunjava sve uvjete'}
            </h2>
            <p className="section-intro">{search.data.criteria.join(' · ')}</p>
            <ol className="find-results">
              {search.data.results.map((r, i) => (
                <li key={r.code} className="card">
                  <div className="find-head">
                    <div>
                      <span className="find-rank">{i + 1}.</span>
                      <h3>{r.name}</h3>
                      <p className="place-line">
                        {r.municipality !== r.name ? `${r.municipality}, ` : ''}
                        {r.county} · {r.population.toLocaleString('hr-HR')} stanovnika
                      </p>
                    </div>
                    {r.score !== null && (
                      <span className="score-badge small">
                        <span className="score-badge-number">{r.score}</span>
                        <span className="score-badge-text">Skor</span>
                      </span>
                    )}
                  </div>
                  {r.reasons.length > 0 && <p className="find-reasons">{r.reasons.join(' · ')}</p>}
                  <ul className="notes">
                    {r.facts.map((f) => (
                      <li key={f}>{f}</li>
                    ))}
                  </ul>
                  <div className="button-row">
                    <Link
                      className="button"
                      to={reportPath(r.lat, r.lon, `${r.name}, ${r.municipality}`, form.profile, [], 'settlement')}
                    >
                      Otvori izvještaj
                    </Link>
                    <ListingLinks
                      settlement={r.name}
                      municipality={r.municipality}
                      county={r.county}
                    />
                  </div>
                </li>
              ))}
            </ol>
            <p className="fine-print">{search.data.note}</p>
          </>
        )}
      </section>
    </>
  )
}
