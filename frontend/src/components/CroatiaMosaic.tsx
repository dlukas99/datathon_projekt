import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useRef } from 'react'
import { fetchMapGeometry, fetchMapTable } from '../lib/api'
import { featureState, PALETTES } from '../lib/mapLayers'
import { decodeGeometry } from '../lib/settlementGeometry'
import { useDocumentTheme } from '../lib/useDocumentTheme'

// The drawn extent: Croatia with a little air around it (same as the map page).
const WEST = 13.3
const EAST = 19.75
const SOUTH = 42.35
const NORTH = 46.6
const REVEAL_MS = 1600

const merc = (lat: number) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360))
const TOP = merc(NORTH)
const BOTTOM = merc(SOUTH)
/** Width over height of the drawn extent in Web Mercator. */
export const MOSAIC_ASPECT = ((EAST - WEST) * Math.PI) / 180 / (TOP - BOTTOM)

interface Shape {
  rings: [number, number][][]
  colour: number
  east: number
}

function reducedMotion(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Every settlement of Croatia drawn on a canvas and coloured by the general Skor za život.
 * The same data (and the same cached requests) as the map page. It fills in from east to
 * west once, like a sunrise; with reduced motion it appears at once. Purely a picture:
 * the text beside it says what it shows and links to the map.
 */
export function CroatiaMosaic() {
  const theme = useDocumentTheme()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const played = useRef(false)
  const geometry = useQuery({
    queryKey: ['map-geometry', 'overview'],
    queryFn: ({ signal }) => fetchMapGeometry('overview', signal),
    select: decodeGeometry,
    staleTime: Infinity,
  })
  const table = useQuery({
    queryKey: ['map-table'],
    queryFn: ({ signal }) => fetchMapTable(signal),
    staleTime: Infinity,
  })

  const shapes = useMemo<Shape[] | null>(() => {
    if (!geometry.data || !table.data) return null
    const classes = new Map<number, number>()
    for (const row of table.data.rows) classes.set(row.id, featureState(row).score_opci ?? -1)
    const out: Shape[] = []
    for (const f of geometry.data.features) {
      if (f.geometry.type !== 'MultiPolygon') continue
      const rings = f.geometry.coordinates.flat() as [number, number][][]
      const outer = rings[0]
      if (!outer) continue
      let east = 0
      for (const [x] of outer) east += x
      out.push({ rings, colour: classes.get(Number(f.id)) ?? -1, east: east / outer.length })
    }
    // Sunrise order: the easternmost settlements first.
    out.sort((a, b) => b.east - a.east)
    return out
  }, [geometry.data, table.data])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !shapes) return
    const palette = PALETTES[theme]
    let frame = 0
    let start = 0

    function setup(): CanvasRenderingContext2D | null {
      if (!canvas) return null
      const ratio = Math.min(window.devicePixelRatio || 1, 2)
      const width = canvas.clientWidth
      const height = canvas.clientHeight
      canvas.width = Math.round(width * ratio)
      canvas.height = Math.round(height * ratio)
      const ctx = canvas.getContext('2d')
      if (!ctx) return null
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
      ctx.clearRect(0, 0, width, height)
      ctx.lineJoin = 'round'
      ctx.lineWidth = 0.35
      ctx.strokeStyle = theme === 'dark' ? 'rgb(14 23 20 / 70%)' : 'rgb(240 243 239 / 85%)'
      return ctx
    }

    function draw(ctx: CanvasRenderingContext2D, from: number, to: number) {
      if (!canvas) return
      const width = canvas.clientWidth
      const height = canvas.clientHeight
      const kx = width / (EAST - WEST)
      const ky = height / (TOP - BOTTOM)
      for (let i = from; i < to; i++) {
        const shape = shapes?.[i]
        if (!shape) continue
        ctx.beginPath()
        for (const ring of shape.rings) {
          ring.forEach(([lon, lat], j) => {
            const x = (lon - WEST) * kx
            const y = (TOP - merc(lat)) * ky
            if (j === 0) ctx.moveTo(x, y)
            else ctx.lineTo(x, y)
          })
          ctx.closePath()
        }
        ctx.fillStyle = palette.steps[shape.colour] ?? palette.none
        ctx.fill('evenodd')
        ctx.stroke()
      }
    }

    const ctx = setup()
    if (!ctx) return
    const total = shapes.length
    if (played.current || reducedMotion()) {
      draw(ctx, 0, total)
      played.current = true
    } else {
      let done = 0
      const step = (now: number) => {
        if (!start) start = now
        const t = Math.min(1, (now - start) / REVEAL_MS)
        // Exponential ease-out: most of the country arrives early, the west settles last.
        const eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t)
        const next = Math.round(eased * total)
        draw(ctx, done, next)
        done = next
        if (t < 1) frame = requestAnimationFrame(step)
        else played.current = true
      }
      frame = requestAnimationFrame(step)
    }

    const observer = new ResizeObserver(() => {
      if (!played.current) return
      const again = setup()
      if (again) draw(again, 0, total)
    })
    observer.observe(canvas)
    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
    }
  }, [shapes, theme])

  const failed = geometry.isError || table.isError
  return (
    <div
      className="mosaic"
      data-state={shapes ? 'ready' : failed ? 'error' : 'loading'}
      role="img"
      aria-label={
        shapes
          ? `Karta Hrvatske: ${shapes.length.toLocaleString('hr-HR')} naselja obojenih prema Skoru za život; ${theme === 'dark' ? 'svjetlija' : 'tamnija'} boja znači viši skor.`
          : 'Karta Hrvatske s naseljima se učitava.'
      }
    >
      <canvas ref={canvasRef} className="mosaic-canvas" aria-hidden="true" />
    </div>
  )
}
