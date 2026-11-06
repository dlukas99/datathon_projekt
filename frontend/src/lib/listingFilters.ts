// Filters of "Pogledaj oglase", shared by every place: they describe what the person is
// looking for, not the place. Kept in memory only, never in the browser's storage.
import { useSyncExternalStore } from 'react'
import type { Deal, Kind } from './listings'

export interface ListingFilters {
  kind: Kind
  deal: Deal
  // As typed; parsePositiveInt() decides whether the filter applies.
  price: string
  area: string
}

const INITIAL: ListingFilters = { kind: 'house', deal: 'sale', price: '', area: '' }

let current = INITIAL
const listeners = new Set<() => void>()

function emit() {
  for (const listener of listeners) listener()
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

function snapshot() {
  return current
}

export function setListingFilters(patch: Partial<ListingFilters>): void {
  current = { ...current, ...patch }
  emit()
}

/** Back to the defaults (tests). */
export function resetListingFilters(): void {
  current = INITIAL
  emit()
}

export function useListingFilters(): ListingFilters {
  return useSyncExternalStore(subscribe, snapshot, snapshot)
}
