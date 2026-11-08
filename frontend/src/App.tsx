import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrandMark } from './components/BrandMark'
import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, NavLink, Route, Routes, useLocation } from 'react-router'
import { SiteNav, type Theme } from './components/SiteNav'
import { BRAND } from './lib/brand'
import { AboutPage } from './pages/AboutPage'
import { ComparePage } from './pages/ComparePage'
import { FindPage } from './pages/FindPage'
import { HomePage } from './pages/HomePage'
import { MapPage } from './pages/MapPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ReportPage } from './pages/ReportPage'
import { SourcesPage } from './pages/SourcesPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 10 * 60 * 1000, refetchOnWindowFocus: false } },
})

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
  '/': `${BRAND.name}: ${BRAND.tagline}`,
  '/izvjestaj': `Izvještaj za adresu · ${BRAND.name}`,
  '/usporedi': `Usporedba dviju lokacija · ${BRAND.name}`,
  '/predlozi': `Predloži mjesto za život · ${BRAND.name}`,
  '/karta': `Karta Hrvatske · ${BRAND.name}`,
  '/izvori': `Izvori podataka · ${BRAND.name}`,
  '/o-alatu': `O alatu i metodologiji · ${BRAND.name}`,
}

function TitleAndFocus() {
  const { pathname } = useLocation()
  useEffect(() => {
    document.title = TITLES[pathname] ?? BRAND.name
    document.getElementById('main')?.focus({ preventScroll: true })
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

/** The old address of "Predloži mjesto" (until 6. 11. 2026.), with its query kept. */
function FindRedirect() {
  const { search, hash } = useLocation()
  return <Navigate to={{ pathname: '/predlozi', search, hash }} replace />
}

function Layout() {
  const [theme, toggleTheme] = useTheme()
  return (
    <>
      <a className="skip-link" href="#main">
        Preskoči na sadržaj
      </a>
      <header className="site-header">
        <div className="container header-row">
          <NavLink to="/" className="brand" aria-label={`${BRAND.name}, naslovnica`}>
            <BrandMark />
            <span className="brand-name">{BRAND.name}</span>
          </NavLink>
          <SiteNav theme={theme} onToggleTheme={toggleTheme} />
        </div>
      </header>
      <TitleAndFocus />
      <main id="main" tabIndex={-1}>
        <div className="container">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/izvjestaj" element={<ReportPage />} />
            <Route path="/usporedi" element={<ComparePage />} />
            <Route path="/predlozi" element={<FindPage />} />
            <Route path="/karta" element={<MapPage />} />
            <Route path="/pronadi" element={<FindRedirect />} />
            <Route path="/izvori" element={<SourcesPage />} />
            <Route path="/o-alatu" element={<AboutPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </div>
      </main>
      <footer className="site-footer">
        <div className="container footer-row">
          <p>
            {BRAND.name} · informativni alat iz otvorenih podataka, nije službena procjena. U
            hitnoj situaciji nazovite 112.
          </p>
          <nav aria-label="Podnožje">
            <ul>
              <li>
                <NavLink to="/izvori">Izvori podataka</NavLink>
              </li>
              <li>
                <NavLink to="/o-alatu">Kako računamo</NavLink>
              </li>
              <li>
                <a href="/api/docs">API</a>
              </li>
            </ul>
          </nav>
          <p className="footer-small">
            © suradnici OpenStreetMapa (ODbL) · podloga karte OpenFreeMap, OpenMapTiles · kod
            EUPL-1.2 · adrese i pitanja se ne spremaju
          </p>
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
