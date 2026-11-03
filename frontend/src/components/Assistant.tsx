import { useId, useState } from 'react'
import { askAssistant, type AssistantReply } from '../lib/api'
import { formatDate, KIND_LABELS } from '../lib/format'
import type { Point } from '../lib/urls'

const SUGGESTED_ONE = [
  'Je li ova kuća u poplavnom području?',
  'Mogu li ovdje živjeti bez auta?',
  'Kakav je zrak?',
  'Koliko je daleko najbliža ljekarna?',
]
const SUGGESTED_TWO = [
  'Koja adresa ima bolji zrak?',
  'Gdje je bliže do vrtića?',
  'Usporedi poplave na obje adrese.',
]

interface Turn {
  question: string
  reply: AssistantReply | null
  error: string | null
}

export function Assistant({ points }: { points: Point[] }) {
  const id = useId()
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [busy, setBusy] = useState(false)

  async function ask(q: string) {
    const text = q.trim()
    if (!text || busy) return
    setBusy(true)
    setQuestion('')
    try {
      const reply = await askAssistant(text, points)
      setTurns((t) => [...t, { question: text, reply, error: null }])
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Asistent trenutačno nije dostupan.'
      setTurns((t) => [...t, { question: text, reply: null, error: message }])
    } finally {
      setBusy(false)
    }
  }

  const suggested = points.length > 1 ? SUGGESTED_TWO : SUGGESTED_ONE
  return (
    <section className="assistant card no-print" aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`}>Pitajte asistenta</h2>
      <p className="hint">
        Odgovara samo iz izračuna za {points.length > 1 ? 'ove adrese' : 'ovu adresu'}, bez savjeta
        o kupnji. Pitanja se ne spremaju.
      </p>
      <div className="assistant-log" aria-live="polite">
        {turns.map((t, i) => (
          <div key={i}>
            <div className="bubble user">
              <span className="visually-hidden">Vaše pitanje: </span>
              {t.question}
            </div>
            <div className="bubble" style={{ marginTop: '0.5rem' }}>
              <span className="visually-hidden">Odgovor: </span>
              {t.error ?? t.reply?.answer}
              {t.reply && t.reply.facts.length > 0 && (
                <ul className="notes">
                  {t.reply.facts.map((f) => (
                    <li key={f.text}>
                      {f.text}{' '}
                      <span className="value-meta" style={{ display: 'inline-flex' }}>
                        <span className="kind">{KIND_LABELS[f.kind]}</span>
                        <span>izvor: {f.source}</span>
                        {formatDate(f.retrieved_at) && <span>{formatDate(f.retrieved_at)}</span>}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              {t.reply && t.reply.links.length > 0 && (
                <ul className="notes">
                  {t.reply.links.map((l) => (
                    <li key={l.url}>
                      <a href={l.url} target="_blank" rel="noreferrer">
                        {l.label}
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ))}
      </div>
      <form
        className="assistant-form"
        onSubmit={(e) => {
          e.preventDefault()
          void ask(question)
        }}
      >
        <label htmlFor={`${id}-q`} className="visually-hidden">
          Pitanje
        </label>
        <input
          id={`${id}-q`}
          type="text"
          value={question}
          maxLength={300}
          placeholder="Npr. Je li ova kuća u poplavnom području?"
          onChange={(e) => {
            setQuestion(e.target.value)
          }}
        />
        <button type="submit" className="button" disabled={busy}>
          {busy ? 'Tražim…' : 'Pitaj'}
        </button>
      </form>
      <div className="suggested-questions">
        {suggested.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => {
              void ask(q)
            }}
          >
            {q}
          </button>
        ))}
      </div>
    </section>
  )
}
