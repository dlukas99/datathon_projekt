import type { Kind } from './api'


export function formatDate(iso: string | null | undefined): string | null {
  if (!iso) return null
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return null
  // Croatian standard form without leading zeros: "8. 11. 2026."
  return `${String(date.getDate())}. ${String(date.getMonth() + 1)}. ${String(date.getFullYear())}.`
}

/** "radni dan 2026-11-11" → "radni dan 11. 11. 2026." in notes that come from the data. */
export function isoDatesToText(text: string): string {
  return text.replace(/(\d{4})-(\d{2})-(\d{2})/g, (_m, y: string, mo: string, d: string) =>
    `${String(Number(d))}. ${String(Number(mo))}. ${y}.`,
  )
}

/** Walking time for a list of nearest places: beyond an hour it is simply "not nearby". */
export function walkText(minutes: number): string {
  return minutes > 60 ? 'više od sat hoda' : minutesText(minutes)
}

export const KIND_LABELS: Record<Kind, string> = {
  measured: 'izmjereno',
  modelled: 'modelirano',
  estimate: 'procjena',
}

export const KIND_HELP: Record<Kind, string> = {
  measured: 'Vrijednost potječe iz mjerenja, voznog reda ili službenog registra.',
  modelled: 'Vrijednost je izračunata modelom iz otvorenih podataka.',
  estimate: 'Gruba procjena iz zamjenskih podataka; tumačite je s oprezom.',
}

/** Walking time in words, everywhere in the interface: "manje od minute", "1 minuta",
 * "4 minute", "12 minuta", "21 minuta". */
export function minutesText(minutes: number): string {
  return minutes < 1 ? 'manje od minute' : minutesSpoken(minutes)
}

export function minutesLabel(minutes: number | null): string {
  return minutes === null ? 'nije izračunato' : minutesText(minutes)
}

export function metresLabel(metres: number | null): string {
  if (metres === null) return ''
  if (metres >= 1000) {
    return `${(metres / 1000).toLocaleString('hr-HR', { maximumFractionDigits: 1 })} km`
  }
  return `${String(Math.round(metres / 10) * 10)} m`
}

/** Whole minutes as the report shows them: at least 1 ("31 min"). */
export function wholeMinutes(minutes: number): number {
  return Math.max(1, Math.round(minutes))
}

/** Croatian noun form for a whole number: 1 minuta, 2 minute, 5 minuta, 21 minuta. */
export function plural(n: number, one: string, few: string, many: string): string {
  const lastDigit = n % 10
  const lastTwo = n % 100
  if (lastDigit === 1 && lastTwo !== 11) return one
  if (lastDigit >= 2 && lastDigit <= 4 && (lastTwo < 12 || lastTwo > 14)) return few
  return many
}

/** "31 minuta", "2 minute", for screen reader announcements. */
export function minutesSpoken(minutes: number): string {
  const n = wholeMinutes(minutes)
  return `${String(n)} ${plural(n, 'minuta', 'minute', 'minuta')}`
}

/** "2,4 kilometra", "3 kilometra", "850 metara": the same rounding as `metresLabel`. */
export function distanceSpoken(metres: number): string {
  if (metres >= 1000) {
    const km = Math.round(metres / 100) / 10
    const text = km.toLocaleString('hr-HR', { maximumFractionDigits: 1 })
    // decimals take the genitive singular: "2,4 kilometra"
    if (!Number.isInteger(km)) return `${text} kilometra`
    return `${text} ${plural(km, 'kilometar', 'kilometra', 'kilometara')}`
  }
  const m = Math.round(metres / 10) * 10
  return `${String(m)} ${plural(m, 'metar', 'metra', 'metara')}`
}
