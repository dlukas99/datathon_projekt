import { useId } from 'react'
import type { Value } from '../lib/api'
import { KIND_HELP, KIND_LABELS } from '../lib/format'

/**
 * What kind of value this is ("izmjereno", "procjena modela", "gruba procjena"), with a short
 * explanation on hover, tap or keyboard focus. A button so touch and keyboard reach it; the
 * explanation is also its accessible description.
 */
export function KindTag({ kind }: { kind: Value['kind'] }) {
  const id = useId()
  return (
    <span className="kind-wrap">
      <button type="button" className="kind" aria-describedby={id}>
        {KIND_LABELS[kind]}
      </button>
      <span role="tooltip" id={id} className="kind-tip">
        {KIND_HELP[kind]}
      </span>
    </span>
  )
}
