'use client'

import { useState } from 'react'
import { useLocale, useTranslations } from 'next-intl'
import { Link, useRouter } from '@/i18n/navigation'
import { AuthShell } from '@/app/components/auth-shell'
import { Button } from '@/app/components/button'
import { Field, Input, PasswordInput, TelegramIcon } from '@/app/components/field'
import { useToast } from '@/app/components/toast'
import { useTelegramChrome, loginWithTelegram } from '@/app/lib/telegram'
import { api, setTokens } from '@/app/lib/api'

export default function RegisterPage() {
  const t = useTranslations('Auth')
  const locale = useLocale()
  const router = useRouter()
  const { toast } = useToast()
  const { inTelegram: inTg } = useTelegramChrome()
  const [form, setForm] = useState({ name: '', phone: '', email: '', password: '', confirm: '' })
  const [busy, setBusy] = useState(false)
  const [tgBusy, setTgBusy] = useState(false)
  const [error, setError] = useState('')

  async function signInWithTelegram() {
    setTgBusy(true)
    if (await loginWithTelegram()) {
      router.replace('/profile')
    } else {
      setError(t('telegramError'))
      setTgBusy(false)
    }
  }

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) {
      setError(t('passwordMismatch'))
      return
    }
    setBusy(true)
    try {
      const res = await api.register({
        email: form.email,
        password: form.password,
        name: form.name,
        phone: form.phone || undefined,
        locale,
      })
      setTokens(res.access_token, res.refresh_token)
      toast(t('registerSuccess'))
      router.replace('/profile')
    } catch (err: any) {
      setError(err?.code === 'email_taken' ? t('emailTaken') : err?.message || t('emailTaken'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell title={t('registerTitle')} subtitle={t('registerSubtitle')}>
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label={t('name')} htmlFor="name">
          <Input id="name" required value={form.name} onChange={set('name')} placeholder="—" />
        </Field>
        <Field label={t('phone')} htmlFor="phone">
          <Input id="phone" type="tel" value={form.phone} onChange={set('phone')} placeholder="+998…" />
        </Field>
        <Field label={t('email')} htmlFor="email">
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={form.email}
            onChange={set('email')}
            placeholder="you@example.com"
          />
        </Field>
        <Field label={t('password')} htmlFor="password">
          <PasswordInput
            id="password"
            autoComplete="new-password"
            required
            value={form.password}
            onChange={set('password')}
            placeholder="••••••••"
          />
        </Field>
        <Field label={t('confirmPassword')} htmlFor="confirm">
          <PasswordInput
            id="confirm"
            autoComplete="new-password"
            required
            value={form.confirm}
            onChange={set('confirm')}
            placeholder="••••••••"
          />
        </Field>
        {error && <p className="text-[13px] text-terracotta">{error}</p>}
        <p className="text-[12px] text-gray">{t('verifyLater')}</p>
        <Button type="submit" variant="solid" size="block" disabled={busy}>
          {busy ? t('registerTitle') + '…' : t('registerSubmit')}
        </Button>
      </form>

      <div className="my-5 flex items-center gap-3">
        <span className="h-px flex-1 bg-sub" />
        <span className="text-[12px] uppercase tracking-wide text-gray">{t('orDivider')}</span>
        <span className="h-px flex-1 bg-sub" />
      </div>

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
        {t('haveAccount')}{' '}
        <Link href="/login" className="font-semibold text-accent">
          {t('goLogin')}
        </Link>
      </p>
    </AuthShell>
  )
}
