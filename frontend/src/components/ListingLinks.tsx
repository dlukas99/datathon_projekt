import { ExternalLink } from 'lucide-react'
import { useEffect, useId, useRef, useState } from 'react'
import { setListingFilters, useListingFilters } from '../lib/listingFilters'
import { type Deal, type Kind, listingLinks, parsePositiveInt } from '../lib/listings'

/**
 * "Pogledaj oglase": builds search links on listing sites. No listing data is fetched.
 *
 * The panel closes on a click outside it, Escape, the button again, or when keyboard focus
 * leaves it (it would cover the next card). It stays open for clicks inside it and while
 * one of its drop-downs is open. The filters are shared by all places (listingFilters.ts).
 */
export function ListingLinks({
  settlement,
  municipality,
  county,
}: {
  settlement: string
  municipality: string | null
  county: string | null
}) {
  const id = useId()
  const buttonId = `${id}-button`
  const panelId = `${id}-panel`
  const filters = useListingFilters()
  const [open, setOpen] = useState(false)
  const [side, setSide] = useState<PopoverSide>('right')
  const rootRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const priceMax = parsePositiveInt(filters.price)
  const areaMax = parsePositiveInt(filters.area)
  const links = listingLinks({
    settlement,
    municipality,
    county,
    kind: filters.kind,
    deal: filters.deal,
    priceMax,
    areaMax,
  })

  useEffect(() => {
    const root = rootRef.current
    if (!open || !root) return
    const button = buttonRef.current
    const focusButton = () => button?.focus({ preventScroll: true })
    // A drop-down list opened with the mouse may be showing. Browsers close the list on the
    // next click outside before the page sees that click, so `:open` alone is not enough.
    let listShown = false

    function onPanelPointerDown(e: PointerEvent) {
      listShown = e.target instanceof HTMLSelectElement
    }
    function onListDone(e: Event) {
      // Only the drop-down itself: a text field also fires change when it loses focus.
      if (e.target instanceof HTMLSelectElement) listShown = false
    }
    function onPointerDown(e: PointerEvent) {
      if (!root || (e.target instanceof Node && root.contains(e.target))) return
      if (listShown || pickerOpen(root)) {
        // This click only closes the list: keep the panel open and the focus in the field.
        listShown = false
        const keepFocus = (m: MouseEvent) => {
          m.preventDefault()
        }
        document.addEventListener('mousedown', keepFocus, { capture: true, once: true })
        window.setTimeout(() => {
          document.removeEventListener('mousedown', keepFocus, { capture: true })
        }, 0)
        return
      }
      const hadFocus = root.contains(document.activeElement)
      setOpen(false)
      // A click on empty space leaves focus on the page or a container around the panel
      // (<main tabindex="-1">): give it back to the button. A click on a link or a field
      // elsewhere keeps the focus there.
      window.setTimeout(() => {
        const active = document.activeElement
        const empty = active === null || active === document.body || active.contains(root)
        if (hadFocus && empty) focusButton()
      }, 0)
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== 'Escape' || e.defaultPrevented || !root) return
      if (pickerOpen(root)) return
      if (listShown && e.target instanceof HTMLSelectElement) {
        listShown = false // Escape closed the list (where the page sees it)
        return
      }
      // Captured first and marked handled, so the map below does not also clear its route.
      e.preventDefault()
      setOpen(false)
      focusButton()
    }
    function onFocusOut(e: FocusEvent) {
      if (e.target instanceof HTMLSelectElement) listShown = false
      const next = e.relatedTarget
      // relatedTarget is null when the window loses focus (a link opened a new tab).
      if (next instanceof Node && root && !root.contains(next)) setOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown, true)
    document.addEventListener('keydown', onKeyDown, true)
    root.addEventListener('pointerdown', onPanelPointerDown, true)
    root.addEventListener('change', onListDone)
    root.addEventListener('focusout', onFocusOut)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown, true)
      document.removeEventListener('keydown', onKeyDown, true)
      root.removeEventListener('pointerdown', onPanelPointerDown, true)
      root.removeEventListener('change', onListDone)
      root.removeEventListener('focusout', onFocusOut)
    }
  }, [open])

  return (
    <div ref={rootRef} className={`listings no-print open-${side}`}>
      <button
        ref={buttonRef}
        id={buttonId}
        type="button"
        className="button ghost"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={(e) => {
          // Measured before the panel opens, so it never shows off screen first.
          if (!open) setSide(popoverSide(e.currentTarget.getBoundingClientRect()))
          setOpen(!open)
        }}
      >
        Pogledaj oglase
      </button>
      <div
        id={panelId}
        className="listings-body"
        role="group"
        aria-labelledby={buttonId}
        hidden={!open}
      >
        <div className="find-grid">
          <label htmlFor={`${id}-kind`}>
            Što
            <select
              id={`${id}-kind`}
              value={filters.kind}
              onChange={(e) => {
                setListingFilters({ kind: e.target.value as Kind })
              }}
            >
              <option value="house">Kuća</option>
              <option value="flat">Stan</option>
            </select>
          </label>
          <label htmlFor={`${id}-deal`}>
            Kako
            <select
              id={`${id}-deal`}
              value={filters.deal}
              onChange={(e) => {
                setListingFilters({ deal: e.target.value as Deal })
              }}
            >
              <option value="sale">Kupnja</option>
              <option value="rent">Najam</option>
            </select>
          </label>
          <WholeNumberField
            id={`${id}-price`}
            label="Najviša cijena (€)"
            value={filters.price}
            parsed={priceMax}
            onChange={(price) => {
              setListingFilters({ price })
            }}
          />
          <WholeNumberField
            id={`${id}-area`}
            label="Najviše m²"
            value={filters.area}
            parsed={areaMax}
            onChange={(area) => {
              setListingFilters({ area })
            }}
          />
        </div>
        <p className="hint">Filtri vrijede za sva mjesta dok je stranica otvorena.</p>
        <ul className="listing-list">
          {links.map((l) => (
            <li key={l.id}>
              <a href={l.url} target="_blank" rel="noopener noreferrer">
                {l.label} <ExternalLink size={14} aria-hidden="true" />
                <span className="visually-hidden"> (otvara se u novoj kartici)</span>
              </a>
              <p className="hint">{l.summary}</p>
              {l.note && <p className="hint">{l.note}</p>}
            </li>
          ))}
        </ul>
        <p className="hint">
          Vanjske stranice oglasnika. Nismo povezani ni s jednim oglasnikom i ne prikazujemo
          oglase; poveznica samo otvara pretragu s odabranim filtrima.
        </p>
      </div>
    </div>
  )
}

/** Whether one of the panel's drop-downs shows its list (`:open`, where supported). */
function pickerOpen(root: HTMLElement): boolean {
  try {
    return Array.from(root.querySelectorAll('select')).some((s) => s.matches(':open'))
  } catch {
    return false // `:open` not supported: the browser closes its own list first
  }
}

type PopoverSide = 'right' | 'left' | 'below'

// Panel width from index.css (.listings-body): min(92vw, 420px).
const PANEL_WIDTH = 420
const EDGE = 8

/**
 * Where the panel fits: right-aligned with the button (it grows to the left), left-aligned
 * (it grows to the right), or in the flow below the button when neither fits.
 */
function popoverSide(button: DOMRect): PopoverSide {
  const width = Math.min(window.innerWidth * 0.92, PANEL_WIDTH)
  if (button.right - width >= EDGE) return 'right'
  if (button.left + width <= window.innerWidth - EDGE) return 'left'
  return 'below'
}

/** Text field for a whole number; "50.000" and "50 000" are accepted. */
function WholeNumberField({
  id,
  label,
  value,
  parsed,
  onChange,
}: {
  id: string
  label: string
  value: string
  parsed: number | null
  onChange: (value: string) => void
}) {
  const invalid = value.trim() !== '' && parsed === null
  return (
    <div>
      <label htmlFor={id}>
        {label}
        <input
          id={id}
          type="text"
          inputMode="numeric"
          value={value}
          aria-invalid={invalid || undefined}
          aria-describedby={invalid ? `${id}-error` : undefined}
          onChange={(e) => {
            onChange(e.target.value)
          }}
        />
      </label>
      {invalid && (
        <p id={`${id}-error`} className="hint">
          Upišite cijeli broj veći od nule. Dok je unos neispravan, filtar se ne primjenjuje.
        </p>
      )}
    </div>
  )
}
