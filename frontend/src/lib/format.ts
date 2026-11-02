import type { Kind } from './api'

const dateFormat = new Intl.DateTimeFormat('hr-HR', {
  day: 'numeric',
  month: 'numeric',
  year: 'numeric',
})

export function formatDate(iso: string | null | undefined): string | null {
  if (!iso) return null
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return null
  return dateFormat.format(date)
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

export function minutesLabel(minutes: number | null): string {
  if (minutes === null) return 'nije izračunato'
  if (minutes < 1) return 'manje od 1 min'
  return `${String(Math.round(minutes))} min`
}

export function metresLabel(metres: number | null): string {
  if (metres === null) return ''
  if (metres >= 1000) {
    return `${(metres / 1000).toLocaleString('hr-HR', { maximumFractionDigits: 1 })} km`
  }
  return `${String(Math.round(metres / 10) * 10)} m`
}
