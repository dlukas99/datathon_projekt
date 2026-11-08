const SEGMENTS = ['flood', 'air', 'green', 'noise', 'fire', 'solar']

/** The brand mark: a dial in the six colours of the environmental readings, with a needle. */
export function BrandMark({ size = 32 }: { size?: number }) {
  const r = 12
  const cx = 16
  const cy = 19
  const point = (t: number) => {
    const a = Math.PI * (1 - t)
    return `${(cx + r * Math.cos(a)).toFixed(2)} ${(cy - r * Math.sin(a)).toFixed(2)}`
  }
  return (
    <svg
      className="brand-mark"
      width={size}
      height={size}
      viewBox="0 0 32 32"
      aria-hidden="true"
      focusable="false"
    >
      {SEGMENTS.map((id, i) => (
        <path
          key={id}
          d={`M${point(i / 6 + 0.012)} A${String(r)} ${String(r)} 0 0 1 ${point((i + 1) / 6 - 0.012)}`}
          fill="none"
          stroke={`var(--c-${id})`}
          strokeWidth="4.2"
        />
      ))}
      <path d={`M${String(cx)} ${String(cy)} L 22.5 9.5`} stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="2.8" fill="currentColor" />
      <path d="M4 27.5h24" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}
