import { fireEvent, render, screen, within } from '@testing-library/react'
import { Assistant } from '../../src/components/Assistant'
import type { AssistantBlock, AssistantReply } from '../../src/lib/api'

const askAssistant = vi.hoisted(() =>
  vi.fn<(q: string, points: unknown[], context?: string[]) => Promise<AssistantReply>>(),
)
vi.mock('../../src/lib/api', () => ({ askAssistant }))

const POINT = { lat: 45.29, lon: 18.81, label: 'Bana Jelačića 1, Vinkovci' }

function block(overrides: Partial<AssistantBlock>): AssistantBlock {
  return {
    topic: 'air',
    title: 'Kvaliteta zraka',
    address: null,
    status: 'info',
    status_label: 'Umjeren',
    text: 'Kroz godinu je zrak ovdje umjereno onečišćen.',
    lines: [],
    chips: [],
    links: [],
    sources: [],
    method: [],
    ...overrides,
  }
}

function reply(blocks: AssistantBlock[], extra: Partial<AssistantReply> = {}): AssistantReply {
  return {
    answer: blocks.map((b) => b.text).join(' '),
    summary: null,
    blocks,
    topics: blocks.map((b) => b.topic),
    suggestions: [],
    facts: [],
    links: [],
    mode: 'rules',
    ...extra,
  }
}

async function askViaForm(text: string) {
  fireEvent.change(screen.getByRole('textbox', { name: 'Pitanje' }), { target: { value: text } })
  fireEvent.click(screen.getByRole('button', { name: 'Pitaj' }))
  await screen.findByText(text)
}

beforeEach(() => {
  askAssistant.mockReset()
})

test('an answer reads as blocks: title, status in words, short lines, sources folded away', async () => {
  askAssistant.mockResolvedValue(
    reply([
      block({
        lines: [{ label: 'PM2,5', value: '18,2 µg/m³ – umjerena razina' }],
        links: [{ label: 'Kvaliteta zraka u stvarnom vremenu', url: 'https://iszz.azo.hr/' }],
        sources: [
          {
            text: 'PM2,5, godišnji prosjek 2024.',
            source: 'EEA',
            retrieved_at: '2026-11-05T19:54:11+00:00',
            kind: 'modelled',
          },
        ],
        method: ['Karta EEA-e na mreži od 1 km.'],
      }),
      block({
        topic: 'car_free',
        title: 'Život bez auta',
        text: '6 od 7 svakodnevnih potreba dostupno je unutar 15 minuta hoda.',
        chips: [{ label: 'nije provjereno: stajalište', tone: 'unknown' }],
      }),
    ]),
  )
  render(<Assistant points={[POINT]} />)
  await askViaForm('Kakav je zrak i mogu li bez auta?')

  const air = screen.getByRole('article', { name: 'Kvaliteta zraka' })
  expect(within(air).getByText('Umjeren')).toBeVisible()
  expect(within(air).getByText('PM2,5')).toBeVisible()
  expect(within(air).getByText('18,2 µg/m³ – umjerena razina')).toBeVisible()
  expect(within(air).queryByText(/Za ovu adresu/)).toBeNull()
  expect(within(air).getByRole('link', { name: /Kvaliteta zraka u stvarnom vremenu/ })).toHaveAttribute(
    'target',
    '_blank',
  )

  // Sources and method are in a closed disclosure that opens from the keyboard too.
  const summary = within(air).getByText('Izvori i metoda')
  const details = summary.closest('details')
  expect(details).not.toHaveAttribute('open')
  expect(within(air).getByText('modelirano')).not.toBeVisible()
  fireEvent.click(summary)
  expect(details).toHaveAttribute('open')

  const carFree = screen.getByRole('article', { name: 'Život bez auta' })
  expect(within(carFree).getByRole('listitem')).toHaveTextContent(
    'nepoznato: nije provjereno: stajalište',
  )
})

test('the disclaimer is shown once, not in every answer', async () => {
  askAssistant.mockResolvedValue(reply([block({})]))
  render(<Assistant points={[POINT]} />)
  await askViaForm('Kakav je zrak?')
  await askViaForm('A zrak zimi?')
  expect(screen.getAllByText(/nije službena procjena ni savjet/)).toHaveLength(1)
})

test('a follow-up question sends the topics of the previous answer', async () => {
  askAssistant.mockResolvedValueOnce(
    reply([block({ topic: 'kindergarten', title: 'Vrtić', text: 'Najbliži vrtić je 7 min hoda.' })]),
  )
  askAssistant.mockResolvedValueOnce(
    reply([block({ topic: 'school', title: 'Osnovna škola', text: 'Škola je 4 min hoda.' })]),
  )
  render(<Assistant points={[POINT]} />)
  await askViaForm('Koliko je do vrtića?')
  await askViaForm('A škola?')
  expect(askAssistant.mock.calls[0]?.[2]).toEqual([])
  expect(askAssistant.mock.calls[1]?.[2]).toEqual(['kindergarten'])
})

test('suggestions follow the answer and leave out questions already asked', async () => {
  askAssistant.mockResolvedValue(
    reply([block({})], {
      suggestions: ['Kakav je zrak?', 'A buka i promet?', 'Ima li zelenila u blizini?', 'Što znači PM2,5?'],
    }),
  )
  render(<Assistant points={[POINT]} />)
  await askViaForm('Kakav je zrak')
  const group = screen.getByRole('group', { name: 'Prijedlozi pitanja' })
  expect(within(group).getAllByRole('button').map((b) => b.textContent)).toEqual([
    'A buka i promet?',
    'Ima li zelenila u blizini?',
    'Što znači PM2,5?',
  ])
})
