'use client'

import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Link, useRouter } from '@/i18n/navigation'
import { AuthShell } from '@/app/components/auth-shell'
import { Button } from '@/app/components/button'
import { Field, Input, PasswordInput, TelegramIcon } from '@/app/components/field'
import { useToast } from '@/app/components/toast'
import { dashHref } from '@/app/components/site-nav'
import { useTelegramChrome, loginWithTelegram } from '@/app/lib/telegram'
import { useAuth } from '@/app/lib/use-auth'
import { api, setTokens } from '@/app/lib/api'

export default function LoginPage() {
  const t = useTranslations('Auth')
  const router = useRouter()
  const { toast } = useToast()
  const [mode, setMode] = useState<'password' | 'code'>('password')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [code, setCode] = useState('')
  const [codeSent, setCodeSent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  // Inside the Mini App, Telegram sign-in uses initData (the OIDC redirect can't
  // open Telegram-in-Telegram). We brand the chrome and offer an explicit button.
  const { inTelegram: inTg } = useTelegramChrome()
  const [tgBusy, setTgBusy] = useState(false)
  const { user: tgUser } = useAuth()
  // If already signed in (e.g. token still valid), skip straight to the cabinet.
  useEffect(() => {
    if (tgUser) router.replace(dashHref(tgUser.role))
  }, [tgUser, router])

  async function signInWithTelegram() {
    setTgBusy(true)
    if (await loginWithTelegram()) {
      router.replace('/profile')
    } else {
      setError(t('telegramError'))
      setTgBusy(false)
    }
  }

  function done(res: {
    access_token: string
    refresh_token?: string
    user: { role: string; locale?: string }
  }) {
    setTokens(res.access_token, res.refresh_token)
    toast(t('loginSuccess'))
    const loc = res.user.locale
    if (loc && ['ru', 'en', 'uz', 'uz-cyrl'].includes(loc)) {
      document.cookie = `NEXT_LOCALE=${loc};path=/;max-age=31536000;samesite=lax`
      router.replace(dashHref(res.user.role), { locale: loc as any })
    } else {
      router.replace(dashHref(res.user.role))
    }
  }

  async function submitPassword(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      done(await api.login({ email, password }))
    } catch {
      setError(t('invalidCredentials'))
    } finally {
      setBusy(false)
    }
  }

  async function requestCode(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim()) return
    setBusy(true)
    setError('')
    try {
      await api.emailRequest(email.trim())
      setCodeSent(true)
      toast(t('codeSent'))
    } catch {
      setError(t('invalidCredentials'))
    } finally {
      setBusy(false)
    }
  }

  async function verifyCode(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      done(await api.emailLogin(email.trim(), code.trim()))
    } catch {
      setError(t('invalidCode'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell title={t('loginTitle')} subtitle={t('loginSubtitle')}>
      {mode === 'password' ? (
        <form onSubmit={submitPassword} className="flex flex-col gap-4">
          <Field label={t('email')} htmlFor="email">
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </Field>
          <Field label={t('password')} htmlFor="password">
            <PasswordInput
              id="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </Field>
          {error && <p className="text-[13px] text-terracotta">{error}</p>}
          <Button type="submit" variant="solid" size="block" disabled={busy}>
            {busy ? t('loginTitle') + '…' : t('loginSubmit')}
          </Button>
          <button
            type="button"
            onClick={() => {
              setMode('code')
              setError('')
            }}
            className="text-center text-[13px] font-medium text-accent hover:underline"
          >
            {t('loginByCode')}
          </button>
        </form>
      ) : (
        <form onSubmit={codeSent ? verifyCode : requestCode} className="flex flex-col gap-4">
          <Field label={t('email')} htmlFor="email2">
            <Input
              id="email2"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              readOnly={codeSent}
            />
          </Field>
          {codeSent && (
            <Field label={t('code')} htmlFor="code">
              <Input
                id="code"
                inputMode="numeric"
                required
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="123456"
              />
            </Field>
          )}
          {error && <p className="text-[13px] text-terracotta">{error}</p>}
          <Button type="submit" variant="solid" size="block" disabled={busy}>
            {codeSent ? t('loginSubmit') : t('sendCode')}
          </Button>
          <button
            type="button"
            onClick={() => {
              setMode('password')
              setCodeSent(false)
              setCode('')
              setError('')
            }}
            className="text-center text-[13px] font-medium text-accent hover:underline"
          >
            {t('loginByPassword')}
          </button>
        </form>
      )}

      <Divider label={t('orDivider')} />
      {inTg ? (
        <Button
          variant="outline"
          size="block"
          className="gap-2 text-accent"
          onClick={signInWithTelegram}
          disabled={tgBusy}
        >
          <TelegramIcon /> {t('telegram')}
        </Button>
      ) : (
        <a href={api.telegram.startUrl()}>
          <Button variant="outline" size="block" className="gap-2 text-accent">
            <TelegramIcon /> {t('telegram')}
          </Button>
        </a>
      )}

      <p className="mt-6 text-center text-[13.5px] text-muted">
        {t('noAccount')}{' '}
        <Link href="/register" className="font-semibold text-accent">
          {t('goRegister')}
        </Link>
      </p>
    </AuthShell>
  )
}

function Divider({ label }: { label: string }) {
  return (
    <div className="my-5 flex items-center gap-3">
      <span className="h-px flex-1 bg-sub" />
      <span className="text-[12px] uppercase tracking-wide text-gray">{label}</span>
      <span className="h-px flex-1 bg-sub" />
    </div>
  )
}
