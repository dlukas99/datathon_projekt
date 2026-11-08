/**
 * Tells a single click from the first click of a double click.
 *
 * The browser (and MapLibre) fire `click` for both clicks of a double click, and the
 * first one has `detail === 1`: at that moment nobody knows a second one is coming.
 * So a single click acts only after a short delay; a second click, a `dblclick` or
 * any camera movement in the meantime cancels it.
 */

/** Long enough for a quick second click or tap, short enough not to feel slow. */
export const SINGLE_CLICK_DELAY_MS = 280

export interface SingleClick<T> {
  /** A click with its value; `detail` is the browser's click count (MouseEvent.detail). */
  click: (value: T, detail?: number) => void
  /** Drops a click that is still waiting (double click, pan, zoom, unmount). */
  cancel: () => void
}

export function createSingleClick<T>(
  onSingle: (value: T) => void,
  delay: number = SINGLE_CLICK_DELAY_MS,
): SingleClick<T> {
  let timer: ReturnType<typeof setTimeout> | undefined
  const cancel = () => {
    if (timer !== undefined) clearTimeout(timer)
    timer = undefined
  }
  const click = (value: T, detail = 1) => {
    cancel()
    // The second (or third) click of a multiple click: never a choice of its own.
    if (detail > 1) return
    timer = setTimeout(() => {
      timer = undefined
      onSingle(value)
    }, delay)
  }
  return { click, cancel }
}
