import { CircleCheck, CircleHelp, CircleMinus, ExternalLink } from 'lucide-react'
import { useId, useState } from 'react'
import { askAssistant, type AssistantBlock, type AssistantReply } from '../lib/api'
import { formatDate, KIND_LABELS } from '../lib/format'
import type { Point } from '../lib/urls'
import { StatusBadge } from './CategoryCard'
import { CategoryIcon } from './Icons'

const SUGGESTED_ONE = [
  'Kakav je zrak i ima li ljekarna blizu?',
  'Je li u poplavnom području?',
  'Mogu li ovdje živjeti bez auta?',
  'Što je u krugu 10 minuta?',
]
const SUGGESTED_TWO = [
  'Koja adresa ima bolji zrak?',
  'Gdje je bliže do vrtića?',
  'Usporedi poplave na obje adrese.',
]
const SHOWN_SUGGESTIONS = 3

// Topics the report has no data on: the "no data" icon.
const GAP_TOPICS = new Set([
  'hospital',
  'secondary_school',
  'crime',
  'earthquake',
  'internet',
  'parking',
  'temperature',
])

const CHIP_ICONS = { good: CircleCheck, missing: CircleMinus, unknown: CircleHelp } as const
// Read before each chip by screen readers, so the tone is never colour alone.
const CHIP_WORDS = { good: 'dobro: ', missing: 'slabije: ', unknown: 'nepoznato: ' } as const

interface Turn {
  question: string
  reply: AssistantReply | null
  error: string | null
}

/** Questions compare without case, spaces or the final question mark. */
function key(question: string): string {
  return question.trim().toLowerCase().replace(/[?!.\s]+$/u, '')
}

function AnswerBlock({ block, headingId }: { block: AssistantBlock; headingId: string }) {
  const icon = GAP_TOPICS.has(block.topic) ? 'no_data' : block.topic
  const hasSources = block.sources.length > 0 || block.method.length > 0
  return (
    <article className="answer-block" aria-labelledby={headingId}>
      <header className="answer-head">
        {block.address && <p className="answer-address">{block.address}</p>}
        <h3 id={headingId} className="answer-title">
          <CategoryIcon id={icon} size={18} />
          {block.title}
        </h3>
        {block.status && block.status_label && (
          <StatusBadge status={block.status} label={block.status_label} />
        )}
      </header>
      <p className="answer-text">{block.text}</p>
      {block.lines.length > 0 && (
        <dl className="answer-lines">
          {block.lines.map((line) => (
            <div key={line.label}>
              <dt>{line.label}</dt>
              <dd>{line.value}</dd>
            </div>
          ))}
        </dl>
      )}
      {block.chips.length > 0 && (
        <ul className="answer-chips">
          {block.chips.map((chip) => {
            const Icon = CHIP_ICONS[chip.tone]
            return (
              <li key={chip.label} className={`answer-chip chip-${chip.tone}`}>
                <Icon size={14} strokeWidth={2.4} aria-hidden="true" />
                <span className="visually-hidden">{CHIP_WORDS[chip.tone]}</span>
                {chip.label}
              </li>
            )
          })}
        </ul>
      )}
      {block.links.length > 0 && (
        <div className="answer-links">
          {block.links.map((link) => (
            <a
              key={link.url}
              className="button ghost small"
              href={link.url}
              target="_blank"
              rel="noreferrer"
            >
              {link.label}
              <ExternalLink size={14} aria-hidden="true" />
              <span className="visually-hidden"> (otvara se u novoj kartici)</span>
            </a>
          ))}
        </div>
      )}
      {hasSources && (
        <details className="answer-sources">
          <summary>Izvori i metoda</summary>
          {block.sources.length > 0 && (
            <ul>
              {block.sources.map((f) => (
                <li key={`${f.text}-${f.source}`}>
                  <span>{f.text}</span>
                  <span className="value-meta">
                    <span className="kind">{KIND_LABELS[f.kind]}</span>
                    <span>{f.source}</span>
                    {formatDate(f.retrieved_at) && <span>{formatDate(f.retrieved_at)}</span>}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {block.method.map((m) => (
            <p key={m}>{m}</p>
          ))}
        </details>
      )}
    </article>
  )
}

export function Assistant({ points }: { points: Point[] }) {
  const id = useId()
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [busy, setBusy] = useState(false)
  // Topics of the last answer, for a follow-up such as "A škola?"; kept only on this page.
  const [context, setContext] = useState<string[]>([])
  const [next, setNext] = useState<string[]>(points.length > 1 ? SUGGESTED_TWO : SUGGESTED_ONE)

  const asked = new Set(turns.map((t) => key(t.question)))
  const suggested = next.filter((q) => !asked.has(key(q))).slice(0, SHOWN_SUGGESTIONS)

  async function ask(q: string) {
    const text = q.trim()
    if (!text || busy) return
    setBusy(true)
    setQuestion('')
    try {
      const reply = await askAssistant(text, points, context)
      setTurns((t) => [...t, { question: text, reply, error: null }])
      if (reply.topics.length > 0) setContext(reply.topics)
      if (reply.suggestions.length > 0) setNext(reply.suggestions)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Asistent trenutačno nije dostupan.'
      setTurns((t) => [...t, { question: text, reply: null, error: message }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="assistant card no-print" aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`}>Pitajte asistenta</h2>
      <p className="hint">
        Odgovara iz izračuna za {points.length > 1 ? 'ove adrese' : 'ovu adresu'}. Možete pitati i
        više stvari odjednom, npr. „Kakav je zrak i ima li vrtić blizu?”, pa nastaviti s „A
        škola?”. Kad nešto ne zna, to i kaže.
      </p>
      <div className="assistant-log" aria-live="polite">
        {turns.map((t, i) => (
          <div key={i} className="assistant-turn">
            <div className="bubble user">
              <span className="visually-hidden">Vaše pitanje: </span>
              {t.question}
            </div>
            <div className="answer">
              <span className="visually-hidden">Odgovor: </span>
              {t.error && <p className="bubble">{t.error}</p>}
              {t.reply?.summary && <p className="answer-summary">{t.reply.summary}</p>}
              {t.reply?.blocks.map((block, j) => (
                <AnswerBlock key={j} block={block} headingId={`${id}-a${String(i)}-${String(j)}`} />
              ))}
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
          placeholder="Npr. Kakav je zrak i koliko je do ljekarne?"
          onChange={(e) => {
            setQuestion(e.target.value)
          }}
        />
        <button type="submit" className="button" disabled={busy}>
          {busy ? 'Tražim…' : 'Pitaj'}
        </button>
      </form>
      {suggested.length > 0 && (
        <div className="suggested-questions" role="group" aria-label="Prijedlozi pitanja">
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
      )}
      <p className="assistant-disclaimer">
        Informativni pregled iz otvorenih podataka, nije službena procjena ni savjet. Pitanja se
        ne spremaju.
      </p>
    </section>
  )
}
