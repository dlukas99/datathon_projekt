import { render, screen } from '@testing-library/react'
import App from '../../src/App'

test('renders the home page with the address search', () => {
  render(<App />)
  expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Kako je živjeti ovdje')
  expect(screen.getByRole('combobox', { name: 'Adresa ili naselje' })).toBeInTheDocument()
})

test('the old sources page leads to the sources part of "O alatu"', async () => {
  window.history.pushState({}, '', '/izvori')
  render(<App />)
  expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent('O alatu i metodologiji')
  expect(window.location.pathname).toBe('/o-alatu')
  expect(window.location.hash).toBe('#izvori')
  expect(screen.getByRole('heading', { level: 2, name: 'Izvori podataka' })).toBeInTheDocument()
  // The footer links go to the parts of the page, not to separate pages.
  const footer = screen.getByRole('navigation', { name: 'Podnožje' })
  expect(footer.querySelector('a[href="/o-alatu#izvori"]')).not.toBeNull()
  expect(footer.querySelector('a[href="/o-alatu#kako-racunamo"]')).not.toBeNull()
  window.history.pushState({}, '', '/')
})
