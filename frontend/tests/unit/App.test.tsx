import { render, screen } from '@testing-library/react'
import App from '../../src/App'

test('renders the home page with the address search', () => {
  render(<App />)
  expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Kako je živjeti ovdje')
  expect(screen.getByRole('combobox', { name: 'Adresa ili naselje' })).toBeInTheDocument()
})
