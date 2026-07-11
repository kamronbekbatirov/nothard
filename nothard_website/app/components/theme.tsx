'use client'

import { ThemeProvider as NextThemesProvider, useTheme } from 'next-themes'
import { useEffect, useState, type ReactNode } from 'react'
import { Moon, Sun } from 'lucide-react'

// Set once the user picks a theme via the toggle. While UNSET, the app follows
// the system (OS in a browser / Telegram in the Mini App). Once SET, the manual
// choice is sticky — the system no longer overrides it, and it persists across
// reopens (next-themes stores the theme itself). This mirrors kama-next.
const MANUAL_KEY = 'nh_theme_manual'

function TelegramThemeSync() {
  const { setTheme } = useTheme()
  useEffect(() => {
    let cancelled = false
    let cleanup: (() => void) | undefined

    const init = (): boolean => {
      const tg = (window as any).Telegram?.WebApp
      if (!tg) return false
      try {
        tg.ready?.()
      } catch {}

      // In Telegram = platform set to something other than "unknown".
      const inTelegram = !!tg.platform && tg.platform !== 'unknown'

      if (inTelegram) {
        // Follow Telegram's colorScheme — but NEVER override a manual choice.
        const applyTheme = () => {
          if (!localStorage.getItem(MANUAL_KEY)) {
            setTheme(tg.colorScheme === 'dark' ? 'dark' : 'light')
          }
        }
        applyTheme()
        tg.onEvent?.('themeChanged', applyTheme)
        tg.onEvent?.('activated', applyTheme) // re-check on re-open (iOS Settings)
        cleanup = () => {
          tg.offEvent?.('themeChanged', applyTheme)
          tg.offEvent?.('activated', applyTheme)
        }
      } else if (!localStorage.getItem(MANUAL_KEY)) {
        // Regular browser — follow the OS (next-themes' `system` mode) unless the
        // user toggled manually.
        setTheme('system')
      }
      return true
    }

    if (!init()) {
      // SDK not ready yet — poll for up to ~3s (60 × 50ms).
      let attempts = 0
      const id = setInterval(() => {
        if (cancelled || init() || ++attempts >= 60) clearInterval(id)
      }, 50)
      const prev = cleanup
      cleanup = () => {
        clearInterval(id)
        prev?.()
      }
    }

    return () => {
      cancelled = true
      cleanup?.()
    }
  }, [setTheme])

  return null
}

/** App-wide theme provider. `attribute="class"` toggles the `.dark` class on
 * <html> (same proven config as kama-next). */
export function ThemeProviders({ children }: { children: ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      <TelegramThemeSync />
      {children}
    </NextThemesProvider>
  )
}

/** Sun/Moon toggle for the header. Sets a sticky manual choice that overrides
 * the system theme and persists across reopens. */
export function ThemeToggle({ className = '' }: { className?: string }) {
  const { resolvedTheme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  const isDark = resolvedTheme === 'dark'
  return (
    <button
      onClick={() => {
        localStorage.setItem(MANUAL_KEY, '1')
        setTheme(isDark ? 'light' : 'dark')
      }}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      className={`btn-motion flex h-8 w-8 items-center justify-center rounded-md text-gray hover:text-ink ${className}`}
    >
      {/* Stable icon until mounted to avoid a hydration mismatch. */}
      {mounted && isDark ? <Sun size={17} /> : <Moon size={17} />}
    </button>
  )
}
