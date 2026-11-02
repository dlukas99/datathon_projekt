import { useEffect, useId, useRef, useState } from 'react'
import { fetchSuggestions, type Suggestion } from '../lib/api'

const KIND_TEXT: Record<Suggestion['kind'], string> = {
  address: 'adresa',
  street: 'ulica (sredina ulice)',
  settlement: 'naselje (središte)',
}

/** Accessible combobox (WAI-ARIA 1.2 pattern) over the backend geocoder. */
export function AddressSearch({
  onSelect,
  label = 'Adresa',
  initialValue = '',
  inputId,
}: {
  onSelect: (s: Suggestion) => void
  label?: string
  initialValue?: string
  inputId?: string
}) {
  const autoId = useId()
  const id = inputId ?? `search-${autoId}`
  const listId = `${id}-list`
  const hintId = `${id}-hint`
  const [query, setQuery] = useState(initialValue)
  const [items, setItems] = useState<Suggestion[]>([])
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [status, setStatus] = useState('')
  const timer = useRef<number | undefined>(undefined)

  useEffect(() => {
    window.clearTimeout(timer.current)
    const q = query.trim()
    if (q.length < 3) return
    const controller = new AbortController()
    timer.current = window.setTimeout(() => {
      fetchSuggestions(q, controller.signal)
        .then((result) => {
          setItems(result)
          setActive(-1)
          setStatus(
            result.length === 0
              ? 'Nema prijedloga. Provjerite naziv ulice i kućni broj.'
              : `${String(result.length)} prijedloga. Strelicama odaberite, Enter za potvrdu.`,
          )
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === 'AbortError') return
          setItems([])
          setStatus('Pretraga trenutačno nije dostupna.')
        })
    }, 200)
    return () => {
      controller.abort()
    }
  }, [query])

  function choose(s: Suggestion) {
    setQuery(s.label)
    setOpen(false)
    setItems([])
    onSelect(s)
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setOpen(true)
      setActive((a) => Math.min(a + 1, visible.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((a) => Math.max(a - 1, 0))
    } else if (e.key === 'Enter') {
      const pick = visible[active] ?? (visible.length > 0 ? visible[0] : undefined)
      if (pick) {
        e.preventDefault()
        choose(pick)
      }
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  const short = query.trim().length < 3
  const visible = short ? [] : items
  const expanded = open && visible.length > 0
  return (
    <div className="search">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type="text"
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={expanded}
        aria-controls={listId}
        aria-describedby={hintId}
        aria-activedescendant={expanded && active >= 0 ? `${listId}-${String(active)}` : undefined}
        autoComplete="off"
        spellCheck={false}
        placeholder="npr. Franje Kuhača 9, Osijek"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
        }}
        onKeyDown={onKeyDown}
        onFocus={() => {
          setOpen(true)
        }}
        onBlur={() => {
          window.setTimeout(() => {
            setOpen(false)
          }, 150)
        }}
      />
      <p id={hintId} className="search-hint">
        Upišite ulicu, kućni broj i mjesto. Adrese se ne spremaju.
      </p>
      <div
        id={listId}
        role="listbox"
        aria-label="Prijedlozi adresa"
        className="suggestions"
        hidden={!expanded}
      >
        {visible.map((s, i) => (
          <div
            key={`${s.label}-${String(s.lat)}`}
            id={`${listId}-${String(i)}`}
            role="option"
            tabIndex={-1}
            aria-selected={i === active}
            onMouseDown={(e) => {
              e.preventDefault()
              choose(s)
            }}
          >
            <span>{s.label}</span>
            <span className="suggestion-kind">{KIND_TEXT[s.kind]}</span>
          </div>
        ))}
      </div>
      <div className="visually-hidden" role="status" aria-live="polite">
        {short ? '' : status}
      </div>
    </div>
  )
}
