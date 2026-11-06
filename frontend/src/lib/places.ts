// Kinds of places on the walking map: colours, names and per-kind summaries.
import type { Place } from './api'

/** The car-free check and the "within 15 minutes" counts (backend analysis/daily.py). */
export const WALK_LIMIT_MIN = 15
/** The backend sends the three nearest places of each kind (analysis/walking.py). */
export const NEAREST_COUNT = 3

export const PLACE_ORDER = [
  'park',
  'grocery',
  'pharmacy',
  'doctor',
  'pediatrician',
  'kindergarten',
  'school',
  'playground',
  'stop',
  'recycling',
]

export const PLACE_COLORS: Record<string, string> = {
  park: '#2e8b57',
  grocery: '#c0662b',
  pharmacy: '#c23b5a',
  doctor: '#b03030',
  pediatrician: '#d4508a',
  kindergarten: '#d9a400',
  school: '#7a52b3',
  playground: '#2a9d8f',
  stop: '#2f5fa8',
  recycling: '#6b7d2a',
}

/** Lower-case names, for use inside sentences. */
export const PLACE_NAMES: Record<string, string> = {
  park: 'park',
  grocery: 'trgovina namirnicama',
  pharmacy: 'ljekarna',
  doctor: 'obiteljski liječnik',
  pediatrician: 'pedijatar',
  kindergarten: 'vrtić',
  school: 'osnovna škola',
  playground: 'igralište',
  stop: 'stajalište',
  recycling: 'reciklaža',
}

export const PLACE_LABELS: Record<string, string> = {
  park: 'Park',
  grocery: 'Trgovina namirnicama',
  pharmacy: 'Ljekarna',
  doctor: 'Obiteljski liječnik',
  pediatrician: 'Pedijatar',
  kindergarten: 'Vrtić',
  school: 'Osnovna škola',
  playground: 'Igralište',
  stop: 'Stajalište',
  recycling: 'Reciklaža',
}

// "najbliži vrtić", "najbliža ljekarna", "najbliže igralište": the word follows the noun.
const NEAREST_WORD: Record<string, string> = {
  park: 'najbliži',
  grocery: 'najbliža',
  pharmacy: 'najbliža',
  doctor: 'najbliži',
  pediatrician: 'najbliži',
  kindergarten: 'najbliži',
  school: 'najbliža',
  playground: 'najbliže',
  stop: 'najbliže',
  recycling: 'najbliža',
}

export function nearestWord(category: string): string {
  return NEAREST_WORD[category] ?? 'najbliže'
}

/** Identifies a place across renders and in map features. */
export function placeKey(p: Pick<Place, 'category' | 'lat' | 'lon' | 'name'>): string {
  return `${p.category}|${p.lat.toFixed(6)}|${p.lon.toFixed(6)}|${p.name}`
}

/** Name to show for a place; places without a name are called by their kind. */
export function placeTitle(p: Pick<Place, 'category' | 'name'>): string {
  const name = p.name.trim()
  if (name && name !== 'bez naziva') return name
  return `${PLACE_LABELS[p.category] ?? 'Mjesto'} bez naziva`
}

export interface CategoryStats {
  /** Places of this kind reachable within 15 minutes. */
  count15: number
  /** The nearest place with a walking time, if any. */
  nearest: Place | null
  /** Up to three nearest places, nearest first ("Sljedeći najbliži"). */
  candidates: Place[]
}

export function categoryStats(places: Place[], category: string): CategoryStats {
  const routed = places
    .filter((p) => p.category === category && p.walk_minutes !== null)
    .sort((a, b) => (a.walk_minutes ?? 0) - (b.walk_minutes ?? 0))
  return {
    count15: routed.filter((p) => (p.walk_minutes ?? Infinity) <= WALK_LIMIT_MIN).length,
    nearest: routed[0] ?? null,
    candidates: routed.slice(0, NEAREST_COUNT),
  }
}
