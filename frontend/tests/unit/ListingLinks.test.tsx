import { act, fireEvent, render, screen, within } from '@testing-library/react'
import { ListingLinks } from '../../src/components/ListingLinks'
import { resetListingFilters } from '../../src/lib/listingFilters'

afterEach(() => {
  act(() => {
    resetListingFilters()
  })
})

function renderPlaces() {
  render(
    <div>
      <ListingLinks settlement="Split" municipality="Split" county="Splitsko-dalmatinska županija" />
      <ListingLinks settlement="Rijeka" municipality="Rijeka" county="Primorsko-goranska županija" />
      <p>Izvan prozora</p>
      <button type="button">Sljedeća kartica</button>
    </div>,
  )
  const [split, rijeka] = screen.getAllByRole('button', { name: 'Pogledaj oglase' })
  if (!split || !rijeka) throw new Error('two buttons expected')
  return { split, rijeka }
}

function panelOf(button: HTMLElement): HTMLElement {
  const id = button.getAttribute('aria-controls')
  const panel = id ? document.getElementById(id) : null
  if (!panel) throw new Error('panel not found')
  return panel
}

describe('Pogledaj oglase', () => {
  it('opens and closes with the button', () => {
    const { split } = renderPlaces()
    expect(split).toHaveAttribute('aria-expanded', 'false')
    expect(panelOf(split)).not.toBeVisible()
    fireEvent.click(split)
    expect(split).toHaveAttribute('aria-expanded', 'true')
    expect(panelOf(split)).toBeVisible()
    fireEvent.click(split)
    expect(split).toHaveAttribute('aria-expanded', 'false')
  })

  it('stays open for clicks inside and closes on a click outside, focus back on the button', () => {
    vi.useFakeTimers()
    try {
      const { split } = renderPlaces()
      fireEvent.click(split)
      const price = within(panelOf(split)).getByLabelText('Najviša cijena (€)')
      price.focus()
      fireEvent.pointerDown(price)
      expect(split).toHaveAttribute('aria-expanded', 'true')

      fireEvent.pointerDown(screen.getByText('Izvan prozora'))
      expect(split).toHaveAttribute('aria-expanded', 'false')
      // Empty space takes no focus; the button gets it back.
      price.blur()
      act(() => {
        vi.runAllTimers()
      })
      expect(split).toHaveFocus()
    } finally {
      vi.useRealTimers()
    }
  })

  it('a click outside while a drop-down list is open only closes the list', () => {
    const { split } = renderPlaces()
    fireEvent.click(split)
    const kind = within(panelOf(split)).getByLabelText('Što')
    fireEvent.pointerDown(kind) // opens the list
    const outside = screen.getByText('Izvan prozora')
    fireEvent.pointerDown(outside)
    expect(fireEvent.mouseDown(outside)).toBe(false) // focus stays in the field
    expect(split).toHaveAttribute('aria-expanded', 'true')
    fireEvent.pointerDown(outside)
    expect(split).toHaveAttribute('aria-expanded', 'false')
  })

  it('after a choice in the list, a click outside closes the panel', () => {
    const { split } = renderPlaces()
    fireEvent.click(split)
    const kind = within(panelOf(split)).getByLabelText('Što')
    fireEvent.pointerDown(kind)
    fireEvent.change(kind, { target: { value: 'flat' } })
    fireEvent.pointerDown(screen.getByText('Izvan prozora'))
    expect(split).toHaveAttribute('aria-expanded', 'false')
  })

  it('closes on Escape, returns focus and stops the key there', () => {
    const { split } = renderPlaces()
    fireEvent.click(split)
    const kind = within(panelOf(split)).getByLabelText('Što')
    kind.focus()
    const notHandled = fireEvent.keyDown(kind, { key: 'Escape' })
    expect(notHandled).toBe(false) // preventDefault: the map's Escape does not also fire
    expect(split).toHaveAttribute('aria-expanded', 'false')
    expect(split).toHaveFocus()
  })

  it('closes when keyboard focus leaves the panel, not when it moves inside', () => {
    const { split } = renderPlaces()
    fireEvent.click(split)
    const panel = panelOf(split)
    const kind = within(panel).getByLabelText('Što')
    fireEvent.focusOut(kind, { relatedTarget: within(panel).getByLabelText('Kako') })
    expect(split).toHaveAttribute('aria-expanded', 'true')
    fireEvent.focusOut(kind, { relatedTarget: null }) // a link opened a new tab
    expect(split).toHaveAttribute('aria-expanded', 'true')
    fireEvent.focusOut(kind, { relatedTarget: screen.getByRole('button', { name: 'Sljedeća kartica' }) })
    expect(split).toHaveAttribute('aria-expanded', 'false')
  })

  it('keeps the filters after closing and shares them between places', () => {
    const { split, rijeka } = renderPlaces()
    fireEvent.click(split)
    const splitPanel = panelOf(split)
    fireEvent.change(within(splitPanel).getByLabelText('Što'), { target: { value: 'flat' } })
    fireEvent.change(within(splitPanel).getByLabelText('Najviša cijena (€)'), {
      target: { value: '200.000' },
    })
    fireEvent.click(split)
    fireEvent.click(split)
    expect(within(splitPanel).getByLabelText('Najviša cijena (€)')).toHaveValue('200.000')

    fireEvent.click(rijeka)
    const rijekaPanel = panelOf(rijeka)
    expect(within(rijekaPanel).getByLabelText('Što')).toHaveValue('flat')
    expect(within(rijekaPanel).getByLabelText('Najviša cijena (€)')).toHaveValue('200.000')
    const hrefs = within(rijekaPanel)
      .getAllByRole('link')
      .map((a) => a.getAttribute('href') ?? '')
    expect(hrefs.some((h) => h.includes('200000'))).toBe(true)
  })
})
