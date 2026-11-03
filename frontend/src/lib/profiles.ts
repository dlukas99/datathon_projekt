// A profile changes only the order and emphasis of categories, never the values.

export type ProfileId = 'opci' | 'obitelj' | 'umirovljenik' | 'student' | 'rad-od-kuce' | 'vlastiti'

export interface Profile {
  id: ProfileId
  label: string
  description: string
  // Category ids and daily item keys, most important first.
  focus: string[]
}

export const PROFILES: Profile[] = [
  { id: 'opci', label: 'Općenito', description: 'Bez posebnog naglaska.', focus: [] },
  {
    id: 'obitelj',
    label: 'Obitelj s djecom',
    description: 'Naglasak na zraku, zelenilu, vrtiću, školi, pedijatru i igralištu.',
    focus: ['air', 'green', 'flood', 'kindergarten', 'school', 'pediatrician', 'playground', 'car_free'],
  },
  {
    id: 'umirovljenik',
    label: 'Umirovljenik',
    description: 'Naglasak na vrućinama, liječniku, ljekarni i javnom prijevozu.',
    focus: ['green', 'air', 'doctor', 'pharmacy', 'transit', 'grocery', 'car_free'],
  },
  {
    id: 'student',
    label: 'Student',
    description: 'Naglasak na javnom prijevozu i životu bez auta.',
    focus: ['transit', 'car_free', 'grocery', 'air', 'noise'],
  },
  {
    id: 'rad-od-kuce',
    label: 'Rad od kuće',
    description: 'Naglasak na buci, zelenilu i suncu na krovu.',
    focus: ['noise', 'green', 'solar', 'air', 'grocery'],
  },
  {
    id: 'vlastiti',
    label: 'Vlastiti',
    description: 'Sami odaberite što vam je važno.',
    focus: [],
  },
]

export const FOCUS_OPTIONS: { id: string; label: string }[] = [
  { id: 'flood', label: 'Poplave' },
  { id: 'air', label: 'Kvaliteta zraka' },
  { id: 'green', label: 'Toplina i zelenilo' },
  { id: 'noise', label: 'Buka' },
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
