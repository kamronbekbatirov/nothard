'use client'

import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Laptop, LogOut, Smartphone, Tablet, X } from 'lucide-react'
import { Button } from './button'
import { Field, Input, PasswordInput, TelegramIcon } from './field'
import { LangSwitcher } from './lang-switcher'
import { useToast } from './toast'
import { api, type DeviceSession, type User } from '@/app/lib/api'

export function SettingsModal({
  user,
  telegram,
  hasPassword,
  inTelegram = false,
  onClose,
  onChanged,
  onDeleted,
}: {
  user: User
  telegram: { linked: boolean; username: string | null }
  hasPassword: boolean
  inTelegram?: boolean
  onClose: () => void
  onChanged: () => void
  onDeleted: () => void
}) {
  const t = useTranslations('Profile')
  const ta = useTranslations('Auth')
  const tc = useTranslations('Common')
  const { toast } = useToast()
  const [name, setName] = useState(user.name)
  const [oldPw, setOldPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [pwErr, setPwErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  // Email linking (email + password → code → verify)
  const [email, setEmail] = useState('')
  const [emailPw, setEmailPw] = useState('')
  const [code, setCode] = useState('')
  const [emailStage, setEmailStage] = useState<'idle' | 'code'>('idle')
  const [emailErr, setEmailErr] = useState('')
  const [delivered, setDelivered] = useState(true)
  // Active sessions (devices signed in to this account).
  const [sessions, setSessions] = useState<DeviceSession[] | null>(null)

  const loadSessions = () =>
    api.me.sessions().then((r) => setSessions(r.sessions)).catch(() => setSessions([]))
  useEffect(() => {
    loadSessions()
  }, [])

  async function revokeSession(id: number) {
    try {
      await api.me.revokeSession(id)
      setSessions((prev) => (prev ? prev.filter((s) => s.id !== id) : prev))
    } catch {}
  }
  async function revokeOthers() {
    try {
      await api.me.revokeOtherSessions()
      toast(t('settings.sessionsSignedOutOthers'))
      loadSessions()
    } catch {}
  }

  const canUnlinkTg = telegram.linked && (!!user.email || hasPassword)

  async function sendCode(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim()) return
    if (!hasPassword && emailPw.length < 6) {
      setEmailErr(t('settings.passwordTooShort'))
      return
    }
    setBusy(true)
    setEmailErr('')
    try {
      const r = await api.me.emailStart(email.trim())
      setDelivered(r.delivered)
      setEmailStage('code')
    } catch (err: any) {
      setEmailErr(err?.code === 'email_taken' ? t('settings.emailTaken') : t('settings.emailInvalid'))
    } finally {
      setBusy(false)
    }
  }
  async function verifyCode(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setEmailErr('')
    try {
      await api.me.emailVerifyWithPassword(code.trim(), emailPw)
      window.dispatchEvent(new Event('nh-auth'))
      toast(t('settings.emailLinked'))
      setEmailStage('idle')
      setCode('')
      setEmailPw('')
      onChanged()
    } catch (err: any) {
      setEmailErr(
        err?.code === 'expired'
          ? t('settings.emailExpired')
          : err?.code === 'weak_password'
            ? t('settings.passwordTooShort')
            : t('settings.emailBadCode')
      )
    } finally {
      setBusy(false)
    }
  }

  async function saveName(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || name.trim() === user.name) return
    try {
      await api.me.updateName(name.trim())
      window.dispatchEvent(new Event('nh-auth'))
      toast(t('settings.nameSaved'))
      onChanged()
    } catch {}
  }

  async function savePassword(e: React.FormEvent) {
    e.preventDefault()
    setPwErr('')
    if (newPw.length < 6) {
      setPwErr(t('settings.passwordTooShort'))
      return
    }
    setBusy(true)
    try {
      await api.me.changePassword(oldPw, newPw)
      toast(t('settings.passwordChanged'))
      setOldPw('')
      setNewPw('')
      onChanged()
    } catch (err: any) {
      setPwErr(err?.code === 'wrong_password' ? t('settings.wrongPassword') : t('settings.passwordTooShort'))
    } finally {
      setBusy(false)
    }
  }

  async function linkTelegram() {
    try {
      const { url } = await api.telegram.linkStart()
      window.location.href = url
    } catch {}
  }
  async function unlinkTelegram() {
    try {
      await api.telegram.unlink()
      toast(t('tgUnlinkedToast'))
      onChanged()
    } catch {}
  }
  async function deleteAccount() {
    try {
      await api.me.deleteAccount()
      onDeleted()
    } catch {}
  }

  return (
    <div className="fixed inset-0 z-[99998] flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-6" onClick={onClose}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="max-h-[90vh] w-full max-w-[440px] overflow-y-auto rounded-t-2xl bg-surface sm:rounded-2xl"
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-surface px-6 py-4">
          <h2 className="font-display text-[20px] text-ink">{t('settings.title')}</h2>
          <button onClick={onClose} className="text-gray hover:text-ink" aria-label="close">
            <X size={18} />
          </button>
        </div>

        <div className="flex flex-col gap-6 p-6">
          {/* Account — editable name */}
          <section>
            <div className="eyebrow mb-3">{t('settings.account')}</div>
            <form onSubmit={saveName} className="flex flex-col gap-3">
              <Field label={t('settings.name')}>
                <div className="flex gap-2">
                  <Input value={name} onChange={(e) => setName(e.target.value)} />
                  <Button
                    type="submit"
                    variant="solid"
                    size="sm"
                    disabled={!name.trim() || name.trim() === user.name}
                  >
                    {t('settings.save')}
                  </Button>
                </div>
              </Field>
              {user.email && (
                <div className="flex justify-between rounded-lg border border-line bg-card px-4 py-2.5 text-[14px]">
                  <span className="text-muted">{ta('email')}</span>
                  <span className="font-medium text-ink">{user.email}</span>
                </div>
              )}
            </form>
          </section>

          {/* Language */}
          <section>
            <div className="eyebrow mb-3">{t('settings.language')}</div>
            <LangSwitcher />
          </section>

          {/* Email — link so you can also sign in with a code by email */}
          {!user.email && (
            <section>
              <div className="eyebrow mb-3">{t('settings.emailTitle')}</div>
              <div className="rounded-lg border border-line bg-card p-4">
                <p className="mb-3 text-[13px] leading-snug text-muted">{t('settings.emailHint')}</p>
                {emailStage === 'idle' ? (
                  <form onSubmit={sendCode} className="flex flex-col gap-2">
                    <Input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@email.com"
                      autoComplete="email"
                    />
                    {!hasPassword && (
                      <PasswordInput
                        value={emailPw}
                        onChange={(e) => setEmailPw(e.target.value)}
                        placeholder={t('settings.emailPasswordPlaceholder')}
                        autoComplete="new-password"
                      />
                    )}
                    {emailErr && <p className="text-[13px] text-terracotta">{emailErr}</p>}
                    <Button type="submit" variant="solid" size="block" disabled={busy || !email.trim()}>
                      {t('settings.emailSend')}
                    </Button>
                  </form>
                ) : (
                  <form onSubmit={verifyCode} className="flex flex-col gap-2">
                    <p className="text-[13px] text-muted">{t('settings.emailCodeSent', { email })}</p>
                    {!delivered && (
                      <p className="text-[12px] text-terracotta">{t('settings.emailDevNote')}</p>
                    )}
                    <Input
                      value={code}
                      onChange={(e) => setCode(e.target.value)}
                      placeholder="123456"
                      inputMode="numeric"
                    />
                    {emailErr && <p className="text-[13px] text-terracotta">{emailErr}</p>}
                    <Button type="submit" variant="solid" size="block" disabled={busy || !code.trim()}>
                      {t('settings.emailVerify')}
                    </Button>
                    <button
                      type="button"
                      onClick={() => {
                        setEmailStage('idle')
                        setEmailErr('')
                      }}
                      className="text-[12.5px] text-gray hover:text-ink"
                    >
                      {tc('cancel')}
                    </button>
                  </form>
                )}
              </div>
            </section>
          )}

          {/* Telegram */}
          <section>
            <div className="eyebrow mb-3">{t('settings.telegram')}</div>
            <div className="rounded-lg border border-line bg-card p-4">
              {telegram.linked ? (
                <div>
                  <div className="flex items-center gap-2.5">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-accent-bg text-accent">
                      <TelegramIcon size={17} />
                    </span>
                    <div className="min-w-0">
                      <div className="text-[14px] font-medium text-ink">{t('linkTgLinked')}</div>
                      {telegram.username && (
                        <a
                          href={`https://t.me/${telegram.username}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[12.5px] text-accent hover:underline"
                        >
                          @{telegram.username}
                        </a>
                      )}
                    </div>
                  </div>
                  {canUnlinkTg ? (
                    <button
                      onClick={unlinkTelegram}
                      className="mt-3 w-full rounded-md border border-terracotta/30 py-2 text-[13px] font-medium text-terracotta hover:bg-terracotta-bg"
                    >
                      {t('unlinkTg')}
                    </button>
                  ) : (
                    <p className="mt-3 rounded-md bg-sub px-3 py-2 text-[12.5px] leading-snug text-muted">
                      {t('settings.unlinkNeedEmail')}
                    </p>
                  )}
                </div>
              ) : (
                <Button variant="outline" size="block" className="gap-2 text-accent" onClick={linkTelegram}>
                  <TelegramIcon /> {t('linkTgButton')}
                </Button>
              )}
            </div>
          </section>

          {/* Password */}
          <section>
            <div className="eyebrow mb-3">
              {hasPassword ? t('settings.changePassword') : t('settings.setPassword')}
            </div>
            <form onSubmit={savePassword} className="flex flex-col gap-3">
              {hasPassword && (
                <Field label={t('settings.oldPassword')}>
                  <PasswordInput value={oldPw} onChange={(e) => setOldPw(e.target.value)} autoComplete="current-password" />
                </Field>
              )}
              <Field label={t('settings.newPassword')}>
                <PasswordInput value={newPw} onChange={(e) => setNewPw(e.target.value)} autoComplete="new-password" />
              </Field>
              {pwErr && <p className="text-[13px] text-terracotta">{pwErr}</p>}
              <Button type="submit" variant="solid" size="block" disabled={busy}>
                {t('settings.save')}
              </Button>
            </form>
          </section>

          {/* Active sessions */}
          <section>
            <div className="eyebrow mb-3">{t('settings.sessionsTitle')}</div>
            <p className="mb-3 text-[13px] leading-snug text-muted">{t('settings.sessionsHint')}</p>
            <div className="flex flex-col gap-2">
              {sessions === null ? (
                <div className="text-[13px] text-muted">{tc('loading')}</div>
              ) : sessions.length === 0 ? (
                <div className="text-[13px] text-muted">{t('settings.sessionsEmpty')}</div>
              ) : (
                sessions.map((s) => (
                  <SessionRow
                    key={s.id}
                    s={s}
                    thisDeviceLabel={t('settings.thisDevice')}
                    revokeLabel={t('settings.revokeSession')}
                    onRevoke={() => revokeSession(s.id)}
                  />
                ))
              )}
            </div>
            {sessions && sessions.filter((s) => !s.current).length > 0 && (
              <Button variant="outline" size="block" className="mt-3 gap-2 text-terracotta" onClick={revokeOthers}>
                <LogOut size={15} /> {t('settings.sessionsRevokeOthers')}
              </Button>
            )}
          </section>

          {/* Danger zone */}
          <section>
            <div className="eyebrow mb-3 text-terracotta">{t('settings.dangerZone')}</div>
            {confirmDelete ? (
              <div className="rounded-lg border border-terracotta/30 bg-terracotta-bg p-4">
                <p className="text-[13.5px] text-ink">{t('settings.deleteConfirm')}</p>
                <p className="mt-1 text-[12.5px] text-muted">{t('settings.deleteWarn')}</p>
                <div className="mt-3 flex gap-2">
                  <Button variant="danger" size="sm" onClick={deleteAccount}>
                    {t('settings.deleteCta')}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(false)}>
                    {tc('cancel')}
                  </Button>
                </div>
              </div>
            ) : (
              <Button variant="outline" size="block" className="text-terracotta" onClick={() => setConfirmDelete(true)}>
                {t('settings.deleteAccount')}
              </Button>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}

function SessionRow({
  s,
  thisDeviceLabel,
  revokeLabel,
  onRevoke,
}: {
  s: DeviceSession
  thisDeviceLabel: string
  revokeLabel: string
  onRevoke: () => void
}) {
  const Icon = s.device === 'Mobile' ? Smartphone : s.device === 'Tablet' ? Tablet : Laptop
  const when = s.lastSeenAt ? new Date(s.lastSeenAt).toLocaleString() : ''
  const meta = [s.os, s.ip, when].filter(Boolean).join(' · ')
  return (
    <div className="flex items-center gap-3 rounded-lg border border-line bg-card p-3">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-sub text-ink">
        <Icon size={17} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-[14px] font-medium text-ink">{s.browser}</span>
          {s.current && (
            <span className="rounded-full bg-accent-bg px-2 py-0.5 text-[10.5px] font-semibold text-accent">
              {thisDeviceLabel}
            </span>
          )}
        </div>
        <div className="truncate text-[12px] text-muted">{meta}</div>
      </div>
      {!s.current && (
        <button
          onClick={onRevoke}
          className="shrink-0 rounded-md border border-terracotta/30 px-2.5 py-1.5 text-[12px] font-medium text-terracotta hover:bg-terracotta-bg"
        >
          {revokeLabel}
        </button>
      )}
    </div>
  )
}
