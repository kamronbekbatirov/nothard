'use client'

import { useEffect, useRef, useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { Globe } from 'lucide-react'
import { useToast } from './toast'
import { api, getAccess } from '@/app/lib/api'
import { cn } from '@/app/lib/utils'

const LOCALES = ['ru', 'en', 'uz', 'uz-cyrl'] as const
type Loc = (typeof LOCALES)[number]

const LOCALE_RE = /^\/(ru|en|uz-cyrl|uz)(?=\/|$)/

/** Shared: switch language (cookie + account) and reload on the localized path. */
function useSwitchLocale() {
  const active = useLocale() as Loc
  const t = useTranslations('Lang')
  const { toast } = useToast()
  return {
    active,
    t,
    switchTo(loc: Loc) {
      if (loc === active) return
      document.cookie = `NEXT_LOCALE=${loc};path=/;max-age=31536000;samesite=lax`
      if (getAccess()) api.me.setLocale(loc).catch(() => {})
      const path = window.location.pathname + window.location.search
      const m = path.match(LOCALE_RE)
      const next = m ? `/${loc}${path.slice(m[0].length)}` : path
      toast(t('switched'))
      window.location.assign(next)
    },
  }
}

/**
 * Compact language control for the app top bar — a small globe + current-code
 * button that opens a dropdown. Fits on a phone alongside theme/avatar/logout,
 * where the full segmented switcher would overflow.
 */
export function LangMenu() {
  const { active, t, switchTo } = useSwitchLocale()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [])
  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={t('label')}
        aria-expanded={open}
        className="flex h-8 items-center gap-1 rounded-lg bg-capsule px-2 text-[12px] font-semibold text-ink"
      >
        <Globe size={14} className="text-gray" /> {t(active)}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-1 w-28 overflow-hidden rounded-lg border border-line bg-surface shadow-card">
          {LOCALES.map((loc) => (
            <button
              key={loc}
              type="button"
              onClick={() => {
                setOpen(false)
                switchTo(loc)
              }}
              className={cn(
                'block w-full px-3 py-2 text-left text-[13px] transition-colors',
                loc === active ? 'bg-accent-bg font-semibold text-accent' : 'text-ink-2 hover:bg-card'
              )}
            >
              {t(loc)}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export function LangSwitcher({ dark = false }: { dark?: boolean }) {
  const { active, t, switchTo } = useSwitchLocale()

  return (
    <div
      className={cn(
        'inline-flex gap-0.5 rounded-lg p-[3px]',
        dark ? 'bg-white/10' : 'bg-capsule'
      )}
    >
      {LOCALES.map((loc) => {
        const on = loc === active
        return (
          <button
            key={loc}
            onClick={() => switchTo(loc)}
            aria-pressed={on}
            className={cn(
              'rounded-md px-[9px] py-1 text-[12px] transition-colors',
              on
                ? 'bg-card font-semibold text-ink'
                : dark
                  ? 'font-medium text-white/55 hover:text-white'
                  : 'font-medium text-gray hover:text-ink'
            )}
          >
            {t(loc)}
          </button>
        )
      })}
    </div>
  )
}
