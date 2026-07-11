'use client'

import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Link, useRouter } from '@/i18n/navigation'
import { Logo } from '@/app/components/logo'
import { Button } from '@/app/components/button'
import { dashHref } from '@/app/components/site-nav'
import { api, setTokens } from '@/app/lib/api'

export default function TelegramCallbackPage() {
  const t = useTranslations('Auth')
  const router = useRouter()
  const [error, setError] = useState(false)

  useEffect(() => {
    const ticket = new URLSearchParams(window.location.search).get('ticket')
    if (!ticket) {
      setError(true)
      return
    }
    api.telegram
      .exchange(ticket)
      .then((res) => {
        setTokens(res.access_token, res.refresh_token)
        router.replace(dashHref(res.user.role))
      })
      .catch(() => setError(true))
  }, [router])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-5 bg-paper px-6 text-center">
      <Logo size={30} asLink={false} />
      {error ? (
        <>
          <p className="font-display text-[22px] text-ink">{t('tgCallbackError')}</p>
          <Button asChild variant="solid" size="md">
            <Link href="/login">{t('goLogin')}</Link>
          </Button>
        </>
      ) : (
        <p className="text-[15px] text-muted">{t('tgCallbackLoading')}</p>
      )}
    </main>
  )
}
