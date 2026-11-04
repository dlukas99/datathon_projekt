// Links to listing searches. We only build URLs; we never fetch or show listings.
import config from '../../../config/listings.json'

export type Deal = 'sale' | 'rent'
export type Kind = 'house' | 'flat'

export interface ListingQuery {
  place: string
  municipality: string
  kind: Kind
  deal: Deal
  priceMax: number | null
  areaMax: number | null
}

export interface ListingLink {
  id: string
  label: string
  url: string
  // True when the place is part of the URL; otherwise the user picks it on the site.
  placeInUrl: boolean
}

interface Njuskalo {
  base: string
  categories: Record<string, { path: string }>
  locations: Record<string, string>
  filters: { price_max: string; area_max: string }
}

const providers = config.providers

export function njuskaloUrl(q: ListingQuery): ListingLink {
  const p = providers.find((x) => x.id === 'njuskalo') as unknown as Njuskalo & { label: string }
  const category = p.categories[`${q.kind}-${q.deal}`]?.path ?? 'prodaja-kuca'
  const slug = p.locations[`${q.municipality}|${q.place}`]
  const params = new URLSearchParams()
  if (q.priceMax) params.set(p.filters.price_max, String(q.priceMax))
  if (q.areaMax) params.set(p.filters.area_max, String(q.areaMax))
  const qs = params.toString()
  const path = slug ? `/${category}/${slug}` : `/${category}`
  return {
    id: 'njuskalo',
    label: p.label,
    url: `${p.base}${path}${qs ? `?${qs}` : ''}`,
    placeInUrl: Boolean(slug),
  }
}

export function listingLinks(q: ListingQuery): ListingLink[] {
  const others = providers
    .filter((x) => x.id !== 'njuskalo')
    .map((x) => ({
      id: x.id,
      label: x.label,
      url: (x as { fallback: string }).fallback,
      placeInUrl: false,
    }))
  return [njuskaloUrl(q), ...others]
}
