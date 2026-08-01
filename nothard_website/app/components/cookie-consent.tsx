'use client'

import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Cookie } from 'lucide-react'
import { Link } from '@/i18n/navigation'
import { Button } from './button'

const KEY = 'nh_cookie_consent'

/**
 * A small, dismissible cookie-consent banner. We only set functional cookies
 * (the chosen language), so this is a single "Got it" acknowledgement rather than
 * a granular consent manager. The choice is remembered in localStorage so it
 * never shows again once accepted.
 */
export function CookieConsent() {
  const t = useTranslations('Cookies')
  // Start hidden and reveal after mount so it never flashes for users who already
  // accepted (and never renders mismatched HTML on the server).
  const [show, setShow] = useState(false)

  useEffect(() => {
    try {
      if (localStorage.getItem(KEY) !== '1') setShow(true)
    } catch {}
  }, [])

  function accept() {
    try {
      localStorage.setItem(KEY, '1')
    } catch {}
    setShow(false)
  }

  if (!show) return null

  return (
    <div className="fixed inset-x-0 bottom-0 z-[60] px-3 pb-3 sm:px-5 sm:pb-5">
      <div className="mx-auto flex max-w-[560px] flex-col gap-3 rounded-2xl border border-line bg-card p-4 shadow-card sm:flex-row sm:items-center sm:gap-4 sm:p-5">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent-bg text-accent">
          <Cookie size={19} />
        </span>
        <p className="flex-1 text-[13px] leading-relaxed text-ink-2">
          {t('text')}{' '}
          <Link href="/privacy" className="font-medium text-accent hover:underline">
            {t('learnMore')}
          </Link>
        </p>
        <Button variant="solid" size="sm" className="shrink-0 sm:px-6" onClick={accept}>
          {t('accept')}
        </Button>
      </div>
    </div>
  )
}
