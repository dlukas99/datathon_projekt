import type { Scale } from '../lib/api'

/** A value on a graded scale. Decorative: the same facts are in the text next to it. */
export function ScaleBar({ scale }: { scale: Scale }) {
  const finite = scale.bands.map((b) => b.upto).filter((u): u is number => u !== null)
  const last = finite[finite.length - 1] ?? scale.value
  const max = Math.max(last * 1.35, scale.value * 1.1)
  const ends = scale.bands.map((b) => b.upto ?? max)
  const segments = scale.bands.map((b, i) => {
    const start = i === 0 ? 0 : (ends[i - 1] ?? 0)
    const end = ends[i] ?? max
    return { ...b, left: (start / max) * 100, width: ((end - start) / max) * 100 }
  })
  const pos = Math.min(scale.value / max, 1) * 100
  return (
    <div className="scale">
      <div className="scale-head">
        <span>{scale.label}</span>
        <strong>
          {scale.value.toLocaleString('hr-HR')} {scale.unit} · {scale.band}
        </strong>
      </div>
      <div className="scale-bar" aria-hidden="true">
        {segments.map((s) => (
          <span
            key={s.label}
            className={`scale-seg seg-${s.status}`}
            style={{ left: `${String(s.left)}%`, width: `${String(s.width)}%` }}
          />
        ))}
        {scale.markers.map((m) => (
          <span
            key={m.label}
            className="scale-tick"
            style={{ left: `${String((m.value / max) * 100)}%` }}
          >
            <span className="scale-tick-label">{m.label}</span>
          </span>
        ))}
        <span className="scale-pin" style={{ left: `${String(pos)}%` }} />
      </div>
    </div>
  )
}
