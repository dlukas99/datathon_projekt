import { createSingleClick, SINGLE_CLICK_DELAY_MS } from '../../src/lib/singleClick'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('createSingleClick', () => {
  it('a single click acts after the delay, not before', () => {
    const onSingle = vi.fn()
    const handler = createSingleClick<string>(onSingle)
    handler.click('A', 1)
    vi.advanceTimersByTime(SINGLE_CLICK_DELAY_MS - 1)
    expect(onSingle).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(onSingle).toHaveBeenCalledExactlyOnceWith('A')
  })

  it('a double click (second click with detail 2, then dblclick) never acts', () => {
    const onSingle = vi.fn()
    const handler = createSingleClick<string>(onSingle)
    handler.click('A', 1)
    vi.advanceTimersByTime(120)
    handler.cancel() // mousedown of the second click
    handler.click('A', 2)
    handler.cancel() // dblclick
    vi.advanceTimersByTime(SINGLE_CLICK_DELAY_MS * 4)
    expect(onSingle).not.toHaveBeenCalled()
  })

  it('a second click with detail 2 alone also drops the first', () => {
    const onSingle = vi.fn()
    const handler = createSingleClick<string>(onSingle)
    handler.click('A', 1)
    handler.click('B', 2)
    vi.advanceTimersByTime(SINGLE_CLICK_DELAY_MS * 4)
    expect(onSingle).not.toHaveBeenCalled()
  })

  it('movestart before the delay ends cancels the click', () => {
    const onSingle = vi.fn()
    const handler = createSingleClick<string>(onSingle)
    handler.click('A', 1)
    vi.advanceTimersByTime(SINGLE_CLICK_DELAY_MS / 2)
    handler.cancel() // movestart, zoomstart or dragstart
    vi.advanceTimersByTime(SINGLE_CLICK_DELAY_MS * 4)
    expect(onSingle).not.toHaveBeenCalled()
  })

  it('two slow single clicks each act once', () => {
    const onSingle = vi.fn()
    const handler = createSingleClick<string>(onSingle)
    handler.click('A', 1)
    vi.advanceTimersByTime(SINGLE_CLICK_DELAY_MS)
    handler.click('B', 1)
    vi.advanceTimersByTime(SINGLE_CLICK_DELAY_MS)
    expect(onSingle.mock.calls).toEqual([['A'], ['B']])
  })

  it('cancel without a waiting click does nothing', () => {
    const onSingle = vi.fn()
    const handler = createSingleClick<string>(onSingle)
    expect(() => {
      handler.cancel()
    }).not.toThrow()
    expect(onSingle).not.toHaveBeenCalled()
  })
})
