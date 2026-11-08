import { ArrowRight } from 'lucide-react'
import { useEffect, useId, useRef, useState } from 'react'
import { fetchSuggestions, type Suggestion } from '../lib/api'

const KIND_TEXT: Record<Suggestion['kind'], string> = {
  address: 'adresa',
  street: 'ulica (sredina ulice)',
  settlement: 'naselje (središte)',
}

const NOTHING_FOUND =
  'Nema prijedloga. Provjerite naziv ulice i kućni broj ili upišite samo naselje.'
const UNAVAILABLE = 'Pretraga trenutačno nije dostupna.'

/** Accessible combobox (WAI-ARIA 1.2 pattern) over the backend geocoder. */
export function AddressSearch({
  onSelect,
  label = 'Adresa',
  initialValue = '',
  inputId,
  submitLabel,
}: {
  onSelect: (s: Suggestion) => void
  label?: string
  initialValue?: string
  inputId?: string
  /** Shows a visible button that does what Enter does (open the best match). */
  submitLabel?: string
}) {
  const autoId = useId()
  const id = inputId ?? `search-${autoId}`
  const listId = `${id}-list`
  const hintId = `${id}-hint`
  const statusId = `${id}-status`
  const [query, setQuery] = useState(initialValue)
  const [items, setItems] = useState<Suggestion[]>([])
  // The text the suggestions answer; while typing it lags behind the query.
  const [itemsFor, setItemsFor] = useState('')
  const [failed, setFailed] = useState(false)
  const [searching, setSearching] = useState(false)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const timer = useRef<number | undefined>(undefined)
  const enterRequest = useRef<AbortController | null>(null)

  useEffect(() => {
    window.clearTimeout(timer.current)
    const q = query.trim()
    if (q.length < 3) return
    const controller = new AbortController()
    timer.current = window.setTimeout(() => {
      fetchSuggestions(q, controller.signal)
        .then((result) => {
          // A late answer to an older query never replaces a newer one.
          if (controller.signal.aborted) return
          setItems(result)
          setItemsFor(q)
          setFailed(false)
          setActive(-1)
        })
        .catch((err: unknown) => {
          if (err instanceof DOMException && err.name === 'AbortError') return
          setItems([])
          setItemsFor(q)
          setFailed(true)
        })
    }, 200)
    return () => {
      controller.abort()
    }
  }, [query])

  useEffect(
    () => () => {
      enterRequest.current?.abort()
    },
    [],
  )

  function choose(s: Suggestion) {
    enterRequest.current?.abort()
    setSearching(false)
    setQuery(s.label)
    setOpen(false)
    setItems([])
    onSelect(s)
  }

  /** Enter before the suggestions caught up with the typing: search the text as it is now. */
  function searchNow(q: string) {
    enterRequest.current?.abort()
    const controller = new AbortController()
    enterRequest.current = controller
    setSearching(true)
    fetchSuggestions(q, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return
        setSearching(false)
        const pick = result[0]
        if (pick) {
          choose(pick)
        } else {
          setItems([])
          setItemsFor(q)
          setFailed(false)
        }
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === 'AbortError') return
        setSearching(false)
        setItemsFor(q)
        setFailed(true)
      })
  }

  /** Enter or the button: the highlighted suggestion, else search the text as it is now. */
  function submit(): boolean {
    const q = query.trim()
    const chosen = visible[active]
    if (chosen) {
      choose(chosen)
    } else if (q.length >= 3 && itemsFor !== q) {
      searchNow(q)
    } else if (visible[0]) {
      choose(visible[0])
    } else {
      return false
    }
    return true
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
      if (submit()) e.preventDefault()
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  const trimmed = query.trim()
  const short = trimmed.length < 3
  const visible = short ? [] : items
  const expanded = open && visible.length > 0
  const current = !short && itemsFor === trimmed
  const empty = current && !failed && items.length === 0
  let status = ''
  if (searching) status = 'Tražim…'
  else if (!short && failed) status = UNAVAILABLE
  else if (empty) status = NOTHING_FOUND
  else if (current) {
    status = `${String(items.length)} prijedloga. Strelicama odaberite, Enter za potvrdu.`
  }
  // "Nothing found" and errors are shown to everyone; the count only to screen readers.
  const shown = searching || (!short && failed) || empty
  return (
    <div className="search">
      <label htmlFor={id}>{label}</label>
      <div className={submitLabel ? 'search-row' : undefined}>
        <input
          id={id}
          type="text"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={expanded}
          aria-controls={listId}
          aria-describedby={shown ? `${hintId} ${statusId}` : hintId}
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
        {submitLabel && (
          <button
            type="button"
            className="search-go"
            onClick={() => {
              if (!submit()) document.getElementById(id)?.focus()
            }}
          >
            {submitLabel}
            <ArrowRight size={18} aria-hidden="true" />
          </button>
        )}
      </div>
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
            {s.note && <span className="suggestion-note">{s.note}</span>}
          </div>
        ))}
      </div>
      <p id={statusId} className={shown ? 'search-status' : 'visually-hidden'} role="status">
        {status}
      </p>
    </div>
  )
}
