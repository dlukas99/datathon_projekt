import { useEffect, useState } from 'react'

export type Theme = 'light' | 'dark'

export function currentTheme(): Theme {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

/** The page theme (sun button in the header), followed while a component is mounted. */
export function useDocumentTheme(): Theme {
  const [theme, setTheme] = useState<Theme>(currentTheme)
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setTheme(currentTheme())
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => {
      observer.disconnect()
    }
  }, [])
  return theme
}
