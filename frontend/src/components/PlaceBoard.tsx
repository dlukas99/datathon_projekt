import { CircleCheck, CircleHelp, Info, OctagonAlert, TriangleAlert } from 'lucide-react'
import { type CSSProperties, useEffect, useState } from 'react'
import type { Category, Report, Status } from '../lib/api'

const STATUS_WORD: Record<Status, string> = {
  good: 'dobro',
  warning: 'upozorenje',
  bad: 'loše',
  info: 'informacija',
  no_data: 'nema podataka',
}

const STATUS_ICON = {
  good: CircleCheck,
  warning: TriangleAlert,
  bad: OctagonAlert,
  info: Info,
  no_data: CircleHelp,
} as const

export interface BoardTag {
  id: string
  label: string
  value: string
  status: Status
}

function display(c: Category, key: string): string | null {
  return c.values.find((v) => v.key === key)?.display ?? null
}

function stopsText(n: string): string {
  const count = Number(n)
  if (!Number.isFinite(count)) return n
  return `${n} ${count % 10 === 1 && count % 100 !== 11 ? 'stajalište' : 'stajališta'} do 10 minuta`
}

/** The key facts for the top of the report, each with its own status, from the report itself. */
export function boardTags(report: Report): BoardTag[] {
  const byId = Object.fromEntries(report.categories.map((c) => [c.id, c]))
  const out: BoardTag[] = []
  const add = (id: string, label: string, value: (c: Category) => string | null) => {
    const c = byId[id]
    if (!c) return
    const v = c.status === 'no_data' ? null : value(c)
    out.push({ id, label, value: v ?? STATUS_WORD.no_data, status: v ? c.status : 'no_data' })
  }
  add('flood', 'Poplave', (c) => c.status_label.toLowerCase())
  add('air', 'Zrak', (c) => c.status_label.toLowerCase())
  add('green', 'Drveće', (c) => display(c, 'tree_share_300m'))
  add('noise', 'Prometnica', (c) => display(c, 'distance_road')?.split(' (')[0] ?? null)
  add('car_free', 'Pješice', (c) => {
    const n = display(c, 'needs_within_15min')
    return n ? `${n} potreba` : null
  })
  add('transit', 'Prijevoz', (c) => {
    const n = display(c, 'stops_10min')
    return n ? stopsText(n) : null
  })
  return out
}

export function BoardTags({ tags }: { tags: BoardTag[] }) {
  return (
    <ul className="board-tags" aria-label="Ukratko">
      {tags.map((t, i) => {
        const Icon = STATUS_ICON[t.status]
        return (
          <li
            key={t.id}
            className={`board-tag tag-${t.status} cat-${t.id}`}
            style={{ '--i': i } as CSSProperties}
          >
            <a href={`#cat-${t.id}`}>
              <span className="board-tag-label">{t.label}</span>
              <span className="board-tag-value">
                <Icon size={16} strokeWidth={2.4} aria-hidden="true" />
                {t.value}
              </span>
              {t.status !== 'info' && t.status !== 'no_data' && (
                <span className="visually-hidden"> ({STATUS_WORD[t.status]})</span>
              )}
            </a>
          </li>
        )
      })}
    </ul>
  )
}

/**
 * "Ovdje ste": the report's sections as a short trail that stays at the top while reading
 * and marks the section in view.
 */
export function ReportGuide({
  sections,
  label = 'Dijelovi izvještaja',
}: {
  sections: { id: string; label: string }[]
  label?: string
}) {
  const [current, setCurrent] = useState<string | null>(null)

  useEffect(() => {
    let frame = 0
    const update = () => {
      frame = 0
      let active: string | null = null
      for (const s of sections) {
        const el = document.getElementById(s.id)
        if (el && el.getBoundingClientRect().top < window.innerHeight * 0.35) active = s.id
      }
      setCurrent(active)
    }
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update)
    }
    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
    }
  }, [sections])

  return (
    <nav className="report-guide no-print" aria-label={label}>
      <ol>
        {sections.map((s) => (
          <li key={s.id}>
            <a href={`#${s.id}`} aria-current={current === s.id ? 'location' : undefined}>
              {s.label}
            </a>
          </li>
        ))}
      </ol>
    </nav>
  )
}
