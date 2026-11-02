import { Link } from 'react-router'

export function NotFoundPage() {
  return (
    <>
      <h1>Stranica nije pronađena</h1>
      <p>
        Provjerite adresu stranice ili se vratite na <Link to="/">pretragu</Link>.
      </p>
    </>
  )
}
