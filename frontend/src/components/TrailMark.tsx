/** The brand mark: a signpost, a post with one plank pointing the way. Drawn, not an icon font. */
export function TrailMark({ size = 30 }: { size?: number }) {
  return (
    <svg
      className="brand-mark"
      width={size}
      height={size}
      viewBox="0 0 32 32"
      aria-hidden="true"
      focusable="false"
    >
      <rect x="7" y="4" width="3.2" height="25" rx="1.2" fill="currentColor" />
      <path d="M5 7.5h17.5l5 4.5-5 4.5H5z" fill="var(--sign)" />
      <path d="M12 12h9" stroke="var(--sign-ink)" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M5 19.5h12.5l3.6 3.25-3.6 3.25H5z" fill="var(--accent)" />
    </svg>
  )
}
