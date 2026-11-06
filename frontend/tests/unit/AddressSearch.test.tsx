import { act, fireEvent, render, screen } from '@testing-library/react'
import { AddressSearch } from '../../src/components/AddressSearch'
import type { Suggestion } from '../../src/lib/api'

const fetchSuggestions = vi.hoisted(() => vi.fn<(q: string, signal?: AbortSignal) => Promise<Suggestion[]>>())
vi.mock('../../src/lib/api', () => ({ fetchSuggestions }))

function suggestion(label: string, note: string | null = null): Suggestion {
  return { label, lat: 45, lon: 16, kind: note ? 'street' : 'address', source: 'dgu_ad', note }
}

async function settle() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(250)
  })
}

beforeEach(() => {
  vi.useFakeTimers()
  fetchSuggestions.mockReset()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('AddressSearch', () => {
  it('says so, visibly, when nothing is found', async () => {
    fetchSuggestions.mockResolvedValue([])
    render(<AddressSearch onSelect={vi.fn()} label="Adresa" />)
    fireEvent.change(screen.getByRole('combobox', { name: 'Adresa' }), {
      target: { value: 'Nepostojeća 5' },
    })
    await settle()
    expect(screen.getByRole('status')).toHaveTextContent(/^Nema prijedloga\./)
    expect(screen.getByRole('status')).toBeVisible()
    expect(screen.getByRole('status')).toHaveClass('search-status')
  })

  it('shows the note of a street offered instead of a missing house number', async () => {
    const note = 'Kućni broj 999 nije u registru adresa; prikazana je sredina ulice.'
    fetchSuggestions.mockResolvedValue([suggestion('Ilica, Zagreb', note)])
    render(<AddressSearch onSelect={vi.fn()} label="Adresa" />)
    const input = screen.getByRole('combobox', { name: 'Adresa' })
    fireEvent.focus(input)
    fireEvent.change(input, { target: { value: 'Ilica 999' } })
    await settle()
    expect(screen.getByRole('option', { name: /Ilica, Zagreb/ })).toHaveTextContent(note)
  })

  it('Enter before the suggestions caught up searches the text as typed', async () => {
    fetchSuggestions.mockImplementation((q) =>
      Promise.resolve(q === 'Ilica' ? [suggestion('Ilica, Zagreb')] : [suggestion('Ilica 1, Zagreb')]),
    )
    const onSelect = vi.fn()
    render(<AddressSearch onSelect={onSelect} label="Adresa" />)
    const input = screen.getByRole('combobox', { name: 'Adresa' })
    fireEvent.change(input, { target: { value: 'Ilica' } })
    await settle()
    fireEvent.change(input, { target: { value: 'Ilica 1, Zagreb' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    await act(async () => {
      await vi.runAllTimersAsync()
    })
    expect(onSelect).toHaveBeenCalledTimes(1)
    expect(onSelect.mock.calls[0]?.[0]).toMatchObject({ label: 'Ilica 1, Zagreb' })
  })

  it('a late answer to an older query does not replace the newer one', async () => {
    let releaseOld: (v: Suggestion[]) => void = () => undefined
    fetchSuggestions.mockImplementation((q, signal) =>
      q === 'Ilic'
        ? new Promise<Suggestion[]>((resolve, reject) => {
            releaseOld = resolve
            signal?.addEventListener('abort', () => {
              reject(new DOMException('aborted', 'AbortError'))
            })
          })
        : Promise.resolve([suggestion('Ilica 1, Zagreb')]),
    )
    render(<AddressSearch onSelect={vi.fn()} label="Adresa" />)
    const input = screen.getByRole('combobox', { name: 'Adresa' })
    fireEvent.focus(input)
    fireEvent.change(input, { target: { value: 'Ilic' } })
    await settle()
    fireEvent.change(input, { target: { value: 'Ilica 1' } })
    await settle()
    releaseOld([suggestion('Ilica, Zagreb')])
    await settle()
    expect(screen.getAllByRole('option').map((o) => o.textContent)).toEqual([
      expect.stringContaining('Ilica 1, Zagreb'),
    ])
  })
})
