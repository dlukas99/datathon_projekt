// The report state lives in the URL, so every report can be shared or bookmarked.

/** "Tenja, Osijek", but just "Split" when the settlement and the town share the name. */
export function placeName(settlement: string, municipality: string | null | undefined): string {
  return municipality && municipality !== settlement ? `${settlement}, ${municipality}` : settlement
}

export function reportPath(
  lat: number,
  lon: number,
  label: string | null,
  profile: string,
  custom: string[] = [],
  kind: 'address' | 'street' | 'settlement' | 'map' = 'address',
): string {
  const params = new URLSearchParams({ lat: lat.toFixed(6), lon: lon.toFixed(6) })
  if (label) params.set('adresa', label)
  if (kind === 'settlement') params.set('tip', 'naselje')
  if (kind === 'street') params.set('tip', 'ulica')
  if (kind === 'map') params.set('tip', 'karta')
  if (profile !== 'opci') params.set('profil', profile)
  if (profile === 'vlastiti' && custom.length > 0) params.set('vazno', custom.join(','))
  return `/izvjestaj?${params.toString()}`
}

export interface Point {
  lat: number
  lon: number
  label: string | null
}

export function parsePoint(value: string | null, label: string | null): Point | null {
  if (!value) return null
  const [lat, lon] = value.split(',').map(Number)
  if (lat === undefined || lon === undefined || !Number.isFinite(lat) || !Number.isFinite(lon)) {
    return null
  }
  return { lat, lon, label }
}

export function comparePath(a: Point | null, b: Point | null): string {
  const params = new URLSearchParams()
  if (a) {
    params.set('a', `${a.lat.toFixed(6)},${a.lon.toFixed(6)}`)
    if (a.label) params.set('la', a.label)
  }
  if (b) {
    params.set('b', `${b.lat.toFixed(6)},${b.lon.toFixed(6)}`)
    if (b.label) params.set('lb', b.label)
  }
  return `/usporedi?${params.toString()}`
}
