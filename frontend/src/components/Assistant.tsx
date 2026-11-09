import { useId, useState } from 'react'
import { askAssistant, type AssistantReply } from '../lib/api'
import { ChevronDown } from 'lucide-react'
import { formatDate } from '../lib/format'
import { KindTag } from './KindTag'
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
        o kupnji. Prepoznaje teme pitanja (npr. poplave, zrak, priroda, promet, vrtić, škola,
        prijevoz); kad nešto ne zna, to i kaže. Pitanja se ne spremaju.
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
              {t.reply && <ReplyDetails reply={t.reply} />}
            </div>
          </div>
        ))}
      </div>
      {turns.length > 0 && (
        <p className="assistant-disclaimer">
          Ovo je informativni pregled iz otvorenih podataka, a ne službena procjena ni savjet.
        </p>
      )}
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

/** "Izvor: …" in one line, then every value and link folded under "Prikaži detalje". */
function ReplyDetails({ reply }: { reply: AssistantReply }) {
  const sources = reply.sources ?? []
  const kinds = [...new Set(reply.facts.map((f) => f.kind))]
  return (
    <>
      {sources.length > 0 && (
        <p className="reply-source">
          Izvor:{' '}
          {sources
            .map((s) => {
              const date = formatDate(s.retrieved_at)
              return date ? `${s.title} (${date})` : s.title
            })
            .join('; ')}
        </p>
      )}
      {(reply.facts.length > 0 || reply.links.length > 0) && (
        <details className="more reply-more">
          <summary>
            Prikaži detalje <ChevronDown size={16} aria-hidden="true" className="chevron" />
          </summary>
          <div className="more-body">
            {kinds.length > 0 && (
              <p className="value-meta kinds">
                {kinds.map((k) => (
                  <KindTag key={k} kind={k} />
                ))}
              </p>
            )}
            {reply.facts.length > 0 && (
              <ul className="notes">
                {reply.facts.map((f) => (
                  <li key={f.text}>{f.text}</li>
                ))}
              </ul>
            )}
            {reply.links.length > 0 && (
              <ul className="notes">
                {reply.links.map((l) => (
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
      )}
    </>
  )
}
