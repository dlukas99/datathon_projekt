import { ExternalLink } from 'lucide-react'
import { useId, useState } from 'react'
import { type Deal, type Kind, listingLinks, parsePositiveInt } from '../lib/listings'

/** "Pogledaj oglase": builds search links on listing sites. No listing data is fetched. */
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
  const [kind, setKind] = useState<Kind>('house')
  const [deal, setDeal] = useState<Deal>('sale')
  const [price, setPrice] = useState('')
  const [area, setArea] = useState('')
  const [side, setSide] = useState<PopoverSide>('right')
  const priceMax = parsePositiveInt(price)
  const areaMax = parsePositiveInt(area)
  const links = listingLinks({ settlement, municipality, county, kind, deal, priceMax, areaMax })
  return (
    <details className={`listings no-print open-${side}`}>
      <summary
        className="button ghost"
        onClick={(e) => {
          // Measured before the panel opens, so it never shows off screen first.
          setSide(popoverSide(e.currentTarget.getBoundingClientRect()))
        }}
      >
        Pogledaj oglase
      </summary>
      <div className="listings-body">
        <div className="find-grid">
          <label htmlFor={`${id}-kind`}>
            Što
            <select
              id={`${id}-kind`}
              value={kind}
              onChange={(e) => {
                setKind(e.target.value as Kind)
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
              value={deal}
              onChange={(e) => {
                setDeal(e.target.value as Deal)
              }}
            >
              <option value="sale">Kupnja</option>
              <option value="rent">Najam</option>
            </select>
          </label>
          <WholeNumberField
            id={`${id}-price`}
            label="Najviša cijena (€)"
            value={price}
            parsed={priceMax}
            onChange={setPrice}
          />
          <WholeNumberField
            id={`${id}-area`}
            label="Najviše m²"
            value={area}
            parsed={areaMax}
            onChange={setArea}
          />
        </div>
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
    </details>
  )
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
