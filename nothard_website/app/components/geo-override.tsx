'use client'

import { useEffect } from 'react'
import { useLocale } from 'next-intl'
import { useRouter, usePathname } from '@/i18n/navigation'

export function GeoOverride() {
  const locale = useLocale()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    const hasCookie = document.cookie.split('; ').some((c) => c.startsWith('NEXT_LOCALE='))
    if (hasCookie) return
    if (locale === 'ru') return

    let tz = ''
    try {
      tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''
    } catch {
      return
    }
    if (tz === 'Asia/Tashkent' || tz === 'Asia/Samarkand') {
      document.cookie = `NEXT_LOCALE=ru; path=/; max-age=${60 * 60 * 24 * 365}; samesite=lax`
      router.replace(pathname, { locale: 'ru' })
    }
  }, [locale, pathname, router])

  return null
}
