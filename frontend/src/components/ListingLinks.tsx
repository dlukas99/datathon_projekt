import { ExternalLink } from 'lucide-react'
import { useId, useState } from 'react'
import { type Deal, type Kind, listingLinks } from '../lib/listings'

/** "Pogledaj oglase": builds search links on listing sites. No listing data is fetched. */
export function ListingLinks({
  place,
  municipality,
}: {
  place: string
  municipality: string
}) {
  const id = useId()
  const [kind, setKind] = useState<Kind>('house')
  const [deal, setDeal] = useState<Deal>('sale')
  const [price, setPrice] = useState('')
  const [area, setArea] = useState('')
  const links = listingLinks({
    place,
    municipality,
    kind,
    deal,
    priceMax: Number(price) > 0 ? Number(price) : null,
    areaMax: Number(area) > 0 ? Number(area) : null,
  })
  return (
    <details className="listings no-print">
      <summary className="button ghost">Pogledaj oglase</summary>
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
          <label htmlFor={`${id}-price`}>
            Najviša cijena (€)
            <input
              id={`${id}-price`}
              type="text"
              inputMode="numeric"
              value={price}
              onChange={(e) => {
                setPrice(e.target.value.replace(/\D/g, ''))
              }}
            />
          </label>
          <label htmlFor={`${id}-area`}>
            Najviše m²
            <input
              id={`${id}-area`}
              type="text"
              inputMode="numeric"
              value={area}
              onChange={(e) => {
                setArea(e.target.value.replace(/\D/g, ''))
              }}
            />
          </label>
        </div>
        <ul className="listing-list">
          {links.map((l) => (
            <li key={l.id}>
              <a href={l.url} target="_blank" rel="noopener noreferrer">
                {l.label} <ExternalLink size={14} aria-hidden="true" />
                <span className="visually-hidden"> (otvara se u novoj kartici)</span>
              </a>
              {!l.placeInUrl && (
                <span className="hint"> · u pretrazi odaberite mjesto {place}</span>
              )}
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
