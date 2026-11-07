import { Menu, Moon, Sun, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router'

export type Theme = 'light' | 'dark'

/**
 * Main navigation. Wide screens show the links in the header; below 760 px they sit behind
 * "Izbornik", which closes on a link, Escape (focus back on the button), a click outside or
 * when keyboard focus leaves it.
 */
export function SiteNav({ theme, onToggleTheme }: { theme: Theme; onToggleTheme: () => void }) {
  const { pathname } = useLocation()
  // Open for one page only: going to another page (link, back button) closes the menu.
  const [openFor, setOpenFor] = useState<string | null>(null)
  const open = openFor === pathname
  const navRef = useRef<HTMLElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const nav = navRef.current
    if (!open || !nav) return
    const close = () => {
      setOpenFor(null)
    }
    function onPointerDown(e: PointerEvent) {
      if (nav && e.target instanceof Node && !nav.contains(e.target)) close()
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== 'Escape' || e.defaultPrevented) return
      e.preventDefault()
      close()
      buttonRef.current?.focus()
    }
    function onFocusOut(e: FocusEvent) {
      if (nav && e.relatedTarget instanceof Node && !nav.contains(e.relatedTarget)) close()
    }
    document.addEventListener('pointerdown', onPointerDown, true)
    document.addEventListener('keydown', onKeyDown, true)
    nav.addEventListener('focusout', onFocusOut)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown, true)
      document.removeEventListener('keydown', onKeyDown, true)
      nav.removeEventListener('focusout', onFocusOut)
    }
  }, [open])

  const closeMenu = () => {
    setOpenFor(null)
  }
  // "Provjeri adresu" leads to the search; the report it opens belongs to the same item.
  const checkCurrent = pathname === '/' ? 'page' : pathname === '/izvjestaj' ? 'true' : undefined

  return (
    <nav ref={navRef} className="site-nav" aria-label="Glavna navigacija">
      <button
        ref={buttonRef}
        type="button"
        className="menu-toggle"
        aria-expanded={open}
        aria-controls="site-menu"
        onClick={() => {
          setOpenFor(open ? null : pathname)
        }}
      >
        {open ? <X size={18} aria-hidden="true" /> : <Menu size={18} aria-hidden="true" />}
        Izbornik
      </button>
      <ul id="site-menu" className={open ? 'nav-links open' : 'nav-links'}>
        <li>
          <Link to="/" aria-current={checkCurrent} onClick={closeMenu}>
            Provjeri adresu
          </Link>
        </li>
        <li>
          <NavLink to="/predlozi" onClick={closeMenu}>
            Predloži mjesto
          </NavLink>
        </li>
        <li>
          <NavLink to="/usporedi" onClick={closeMenu}>
            Usporedi
          </NavLink>
        </li>
        <li>
          <NavLink to="/karta" onClick={closeMenu}>
            Karta
          </NavLink>
        </li>
        <li>
          <NavLink to="/o-alatu" onClick={closeMenu}>
            O alatu
          </NavLink>
        </li>
      </ul>
      <button
        type="button"
        className="theme-toggle"
        onClick={onToggleTheme}
        aria-pressed={theme === 'dark'}
        aria-label="Tamna tema"
        title="Tamna tema"
      >
        {theme === 'dark' ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
      </button>
    </nav>
  )
}
