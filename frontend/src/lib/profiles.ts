// A profile changes the order, emphasis and Skor za život weights, never the values.
import shared from '../../../config/profiles.json'


export type ProfileId = 'opci' | 'obitelj' | 'umirovljenik' | 'student' | 'rad-od-kuce' | 'vlastiti'

export interface Profile {
  id: ProfileId
  label: string
  description: string
  // Category ids and daily item keys, most important first.
  focus: string[]
  // Skor za život weights per category, 0–3.
  weights: Record<string, number>
}

// Profiles and their Skor za život weights live in config/profiles.json (shared with the backend).
export const PROFILES: Profile[] = shared.profiles.map((p) => ({ ...p, id: p.id as ProfileId }))

export const SCORE_CATEGORIES: { id: string; label: string }[] = shared.categories

export function profileWeights(id: string | null): Record<string, number> {
  return { ...getProfile(id).weights }
}

export const FOCUS_OPTIONS: { id: string; label: string }[] = [
  { id: 'flood', label: 'Poplave' },
  { id: 'air', label: 'Kvaliteta zraka' },
  { id: 'green', label: 'Priroda i hlad' },
  { id: 'noise', label: 'Udaljenost od prometnica' },
  { id: 'fire', label: 'Požari raslinja' },
  { id: 'solar', label: 'Sunce na krovu' },
  { id: 'car_free', label: 'Život bez auta' },
  { id: 'transit', label: 'Javni prijevoz' },
  { id: 'kindergarten', label: 'Vrtić' },
  { id: 'school', label: 'Osnovna škola' },
  { id: 'doctor', label: 'Obiteljski liječnik' },
  { id: 'pediatrician', label: 'Pedijatar' },
  { id: 'pharmacy', label: 'Ljekarna' },
  { id: 'grocery', label: 'Trgovina namirnicama' },
  { id: 'playground', label: 'Igralište' },
  { id: 'recycling', label: 'Reciklaža' },
]

const DEFAULT_PROFILE = PROFILES[0] as Profile

export function getProfile(id: string | null): Profile {
  return PROFILES.find((p) => p.id === id) ?? DEFAULT_PROFILE
}

export function focusList(profileId: string | null, custom: string | null): string[] {
  if (profileId === 'vlastiti') return (custom ?? '').split(',').filter(Boolean)
  return getProfile(profileId).focus
}

/** Stable sort: focused ids first, in focus order; the rest keep their original order. */
export function orderByFocus<T>(items: T[], key: (item: T) => string, focus: string[]): T[] {
  const rank = (item: T) => {
    const i = focus.indexOf(key(item))
    return i === -1 ? focus.length : i
  }
  return items
    .map((item, index) => ({ item, index }))
    .sort((a, b) => rank(a.item) - rank(b.item) || a.index - b.index)
    .map((x) => x.item)
}
