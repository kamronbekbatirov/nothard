'use client'

import { useLocale, useTranslations } from 'next-intl'
import { useToast } from './toast'
import { api, getAccess } from '@/app/lib/api'
import { cn } from '@/app/lib/utils'

const LOCALES = ['ru', 'en', 'uz', 'uz-cyrl'] as const
type Loc = (typeof LOCALES)[number]

const LOCALE_RE = /^\/(ru|en|uz-cyrl|uz)(?=\/|$)/

export function LangSwitcher({ dark = false }: { dark?: boolean }) {
  const active = useLocale() as Loc
  const t = useTranslations('Lang')
  const { toast } = useToast()

  function switchTo(loc: Loc) {
    if (loc === active) return
    document.cookie = `NEXT_LOCALE=${loc};path=/;max-age=31536000;samesite=lax`
    // Persist to the account (so Telegram messages + re-login use this language).
    if (getAccess()) api.me.setLocale(loc).catch(() => {})
    const path = window.location.pathname + window.location.search
    const m = path.match(LOCALE_RE)
    const next = m ? `/${loc}${path.slice(m[0].length)}` : path
    toast(t('switched'))
    window.location.assign(next)
  }

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
