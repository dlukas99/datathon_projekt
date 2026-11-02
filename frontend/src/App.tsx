import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { BrowserRouter, NavLink, Route, Routes, useLocation } from 'react-router'
import { AboutPage } from './pages/AboutPage'
import { ComparePage } from './pages/ComparePage'
import { HomePage } from './pages/HomePage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ReportPage } from './pages/ReportPage'
import { SourcesPage } from './pages/SourcesPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 10 * 60 * 1000, refetchOnWindowFocus: false } },
})

type Theme = 'light' | 'dark'
const THEME_KEY = 'prije-potpisa-tema'

function initialTheme(): Theme {
  try {
    const saved = localStorage.getItem(THEME_KEY)
    if (saved === 'light' || saved === 'dark') return saved
  } catch {
    // storage unavailable
  }
  return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light'
}

function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(initialTheme)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])
  const toggle = () => {
    const next: Theme = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    try {
      localStorage.setItem(THEME_KEY, next)
    } catch {
      // storage unavailable
    }
  }
  return [theme, toggle]
}

const TITLES: Record<string, string> = {
  '/': 'Prije potpisa: okolišni pregled adrese',
  '/izvjestaj': 'Izvještaj za adresu · Prije potpisa',
  '/usporedi': 'Usporedba dviju adresa · Prije potpisa',
  '/izvori': 'Izvori podataka · Prije potpisa',
  '/o-alatu': 'O alatu i metodologiji · Prije potpisa',
}

function TitleAndFocus() {
  const { pathname } = useLocation()
  useEffect(() => {
    document.title = TITLES[pathname] ?? 'Prije potpisa'
    document.getElementById('main')?.focus({ preventScroll: true })
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function Layout() {
  const [theme, toggleTheme] = useTheme()
  return (
    <>
      <a className="skip-link" href="#main">
        Preskoči na sadržaj
      </a>
      <header className="site-header">
        <div className="container">
          <NavLink to="/" className="brand" aria-label="Prije potpisa, naslovnica">
            <span className="brand-mark" aria-hidden="true" />
            Prije potpisa
          </NavLink>
          <nav className="site-nav" aria-label="Glavna navigacija">
            <ul>
              <li>
                <NavLink to="/" end>
                  Pretraga
                </NavLink>
              </li>
              <li>
                <NavLink to="/usporedi">Usporedi</NavLink>
              </li>
              <li>
                <NavLink to="/izvori">Izvori</NavLink>
              </li>
              <li>
                <NavLink to="/o-alatu">O alatu</NavLink>
              </li>
              <li>
                <button type="button" className="theme-toggle" onClick={toggleTheme} aria-pressed={theme === 'dark'}>
                  Tamna tema
                </button>
              </li>
            </ul>
          </nav>
        </div>
      </header>
      <TitleAndFocus />
      <main id="main" tabIndex={-1}>
        <div className="container">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/izvjestaj" element={<ReportPage />} />
            <Route path="/usporedi" element={<ComparePage />} />
            <Route path="/izvori" element={<SourcesPage />} />
            <Route path="/o-alatu" element={<AboutPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </div>
      </main>
      <footer className="site-footer">
        <div className="container">
          <p>
            Prije potpisa informativni je alat izrađen iz otvorenih podataka za Datathon Portala
            otvorenih podataka 2026. Nije službena procjena rizika. U hitnoj situaciji nazovite 112.
          </p>
          <p>
            Podaci: Državna geodetska uprava, Ministarstvo znanosti, obrazovanja i mladih, HZZO,
            Grad Zagreb, Grad Rijeka, ZET, HŽPP, JRC, EEA, ESA WorldCover, © suradnici
            OpenStreetMapa (ODbL). Podloga karte: OpenFreeMap, OpenMapTiles. Potpun popis na
            stranici <NavLink to="/izvori">Izvori</NavLink>.
          </p>
          <p>Kod je objavljen pod licencom EUPL-1.2. Upisane adrese i pitanja ne spremaju se.</p>
        </div>
      </footer>
    </>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
