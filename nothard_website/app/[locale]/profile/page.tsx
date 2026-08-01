'use client'

import { useEffect, useState } from 'react'
import { useTranslations, useLocale } from 'next-intl'
import { Check, CheckCircle2, ChevronDown, ChevronRight, Copy, ExternalLink, History, Home, Paperclip, Phone, Plus, Share2, ShoppingBag, Star, Trash2, X } from 'lucide-react'
import { Link, useRouter } from '@/i18n/navigation'
import { AppTopbar } from '@/app/components/app-topbar'
import { Button } from '@/app/components/button'
import { Logo } from '@/app/components/logo'
import { DateTimeInput, Input, PickOrType, TelegramIcon } from '@/app/components/field'
import { Avatar } from '@/app/components/avatar'
import { SettingsModal } from '@/app/components/settings-modal'
import { DuplicateWarningModal } from '@/app/components/duplicate-warning'
import { TripCard } from '@/app/components/trip-card'
import { AddressField } from '@/app/components/address-field'
import { ChatModal } from '@/app/components/chat'
import { useToast } from '@/app/components/toast'
import { useAuth } from '@/app/lib/use-auth'
import {
  useTelegramChrome,
  getTelegramUser,
  telegramDisplayName,
  canRequestContact,
  requestTelegramContact,
} from '@/app/lib/telegram'
import { flushPendingHousing } from '@/app/lib/housing-cart'
import { useTaskLabel } from '@/app/lib/task-label'
import {
  api,
  clearTokens,
  getAccess,
  type Attachment,
  type DashboardData,
  type HousingItem,
  type OrderHistoryItem,
  type PendingReview,
  type TripLive,
} from '@/app/lib/api'
import {
  PACKAGES,
  SERVICES,
  SERVICE_STAGES,
  AIRPORT_PACKAGES,
  AIRPORT_SERVICES,
  packageCovers,
  coveredServices,
  LONDON_AIRPORT_TERMINALS,
  LONDON_FLIGHTS,
  VIEWING_PRICE,
  ARRANGEMENT_PRICE,
  fmtGBP,
  fmtUZS,
} from '@/app/lib/data'
import { cn } from '@/app/lib/utils'

const DOC_KEYS = ['passport', 'visa', 'lease', 'bank', 'nhs'] as const

// Display a YYYY-MM-DD date as DD.MM.YYYY.
function fmtDate(d?: string): string {
  if (!d) return ''
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d)
  return m ? `${m[3]}.${m[2]}.${m[1]}` : d
}

// A friendly "in X days / X hours / X min" until an arrival date+time, or null if past/unknown.
function arrivalCountdown(
  date?: string,
  time?: string,
): { days: number; hours: number; minutes: number } | null {
  if (!date) return null
  const dt = new Date(`${date}T${time || '00:00'}:00`)
  if (isNaN(dt.getTime())) return null
  const diff = dt.getTime() - Date.now()
  if (diff <= 0) return null
  return {
    days: Math.floor(diff / 86400000),
    hours: Math.floor((diff % 86400000) / 3600000),
    minutes: Math.floor((diff % 3600000) / 60000),
  }
}

export default function ProfilePage() {
  const t = useTranslations('Profile')
  const { toast } = useToast()
  const router = useRouter()
  const { inTelegram } = useTelegramChrome()
  const { user, loading, refresh: refreshAuth } = useAuth()
  const [data, setData] = useState<DashboardData | null>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)
  // Which chat thread is open — with the manager or the field companion (runner).
  const [chatWith, setChatWith] = useState<'manager' | 'runner' | null>(null)
  const [buying, setBuying] = useState(false)
  // Arrival-details intake for an airport meet (a package OR a standalone
  // transport/taxi service). Holds the whole selection so it checks out together.
  const [intake, setIntake] = useState<{ pkgId: string | null; services: string[] } | null>(null)
  // "?pkg=" — a package picked on the landing, preselected in the picker below.
  const [presetPkg, setPresetPkg] = useState<string | null>(null)
  useEffect(() => {
    const p = new URLSearchParams(window.location.search).get('pkg')
    if (p && PACKAGES.some((x) => x.id === p)) setPresetPkg(p)
  }, [])

  // Live "your host is on the way" trip — polled while the cabinet is open.
  const [trip, setTrip] = useState<TripLive | null>(null)
  useEffect(() => {
    if (!user) return
    let alive = true
    const load = () => api.me.trip().then((r) => alive && setTrip(r.trip)).catch(() => {})
    load()
    const id = window.setInterval(load, 8000)
    return () => {
      alive = false
      clearInterval(id)
    }
  }, [user])

  useEffect(() => {
    // Only bounce to /login once we're sure there's no session. If a token was
    // just set (e.g. by the Mini App initData exchange) whoami is still in-flight
    // — `user` is momentarily null but a token exists, so don't redirect yet.
    if (!loading && !user && !getAccess()) router.replace('/login')
  }, [loading, user, router])

  const refresh = () => api.me.dashboard().then(setData).catch(() => {})
  // Live cabinet: poll so operator-side task/status changes appear without a reload.
  useEffect(() => {
    if (!user) return
    refresh()
    const id = window.setInterval(refresh, 5000)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  // A guest who built a housing shortlist / added links before signing up: replay
  // that selection into the cabinet now that they're logged in.
  useEffect(() => {
    if (!user) return
    flushPendingHousing().then((n) => {
      if (n > 0) {
        toast(t('housing.pendingAdded', { count: n }))
        refresh()
      }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  /**
   * Buy a package and any extra services as ONE order — the backend checkout
   * already accepts mixed items, so there's no need to pay twice. Packages with
   * an airport pickup collect arrival details first (the services ride along).
   */
  function buySelection(pkgId: string | null, serviceIds: string[] = []) {
    // Ask for arrival details when the selection includes an airport meet —
    // whether it's an airport PACKAGE or a standalone transport/taxi SERVICE.
    const needsArrival =
      (pkgId != null && AIRPORT_PACKAGES.has(pkgId)) ||
      serviceIds.some((s) => AIRPORT_SERVICES.has(s))
    if (needsArrival) {
      setIntake({ pkgId, services: serviceIds })
    } else {
      void confirmSelection(pkgId, serviceIds, {})
    }
  }

  async function confirmSelection(
    pkgId: string | null,
    serviceIds: string[],
    details: Record<string, string>
  ) {
    const items = [
      ...(pkgId ? [{ type: 'package' as const, id: pkgId }] : []),
      ...serviceIds.map((id) => ({ type: 'service' as const, id })),
    ]
    if (!items.length) return
    setBuying(true)
    try {
      const d = await api.me.checkout(items, details)
      setData(d)
      setIntake(null)
      toast(t('purchasedToast'))
    } catch {
    } finally {
      setBuying(false)
    }
  }

  // The populated cabinet's "add / upgrade package" buttons buy a single package.
  function buyPackage(id: string) {
    buySelection(id, [])
  }

  function logout() {
    void api.logout() // revoke this device's session server-side (best-effort)
    clearTokens()
    // Inside the Mini App the landing silently resumes the Telegram session on
    // open; mark it as already-resumed so an explicit logout actually sticks
    // instead of signing them straight back in.
    try {
      sessionStorage.setItem('nh_mini_resumed', '1')
    } catch {}
    window.location.href = '/login'
  }

  /** Declining the terms cancels the registration and removes the fresh account. */
  async function declineTerms() {
    try {
      await api.me.declineTerms()
    } catch {}
    clearTokens()
    try {
      sessionStorage.setItem('nh_mini_resumed', '1')
    } catch {}
    window.location.href = '/'
  }

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper text-[15px] text-muted">…</div>
    )
  }

  // First-time users must accept Privacy + Terms before using the cabinet.
  if (!user.termsAccepted) {
    return (
      <ConsentGate
        user={user}
        inTelegram={inTelegram}
        onLogout={logout}
        onDecline={declineTerms}
        onAccept={async () => {
          try {
            await api.me.acceptTerms()
            await refreshAuth()
          } catch {}
        }}
      />
    )
  }

  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper text-[15px] text-muted">…</div>
    )
  }

  return (
    <div className="min-h-screen bg-paper">
      <AppTopbar
        name={user.name}
        avatarUrl={user.photo_url}
        tgId={user.telegram_id}
        onSettings={() => setSettingsOpen(true)}
        onLogout={logout}
      />

      <main className="mx-auto max-w-[1240px] px-5 py-8 sm:px-8">
        {data.hasOrders ? (
          // Greeting + live map live INSIDE the populated cabinet so the mobile
          // order is: greeting → map → package/arrival → path → people.
          <PopulatedCabinet
            data={data}
            trip={trip}
            onChat={(who = 'manager') => setChatWith(who)}
            onBuy={buyPackage}
            onCheckout={buySelection}
            buying={buying}
            onRefresh={refresh}
          />
        ) : (
          <>
            {trip && trip.status !== 'cancelled' && (
              <div className="mb-6">
                <TripCard trip={trip} minimal />
              </div>
            )}
            <EmptyCabinet onCheckout={buySelection} buying={buying} initialPkg={presetPkg} />
          </>
        )}
      </main>

      {settingsOpen && (
        <SettingsModal
          user={data.user}
          telegram={data.telegram}
          hasPassword={data.hasPassword}
          inTelegram={inTelegram}
          onClose={() => setSettingsOpen(false)}
          onChanged={refresh}
          onDeleted={() => {
            clearTokens()
            window.location.href = '/'
          }}
        />
      )}

      {chatWith === 'manager' && (
        <ChatModal
          title={data.manager.assigned && data.manager.name ? data.manager.name : t('chat.title')}
          subtitle={data.manager.assigned ? t('managerHours') : t('managerPending')}
          peerName={data.manager.name || t('chat.title')}
          peerAvatarUrl={data.manager.photoUrl}
          placeholder={t('chat.placeholder')}
          emptyText={data.manager.assigned ? t('chat.empty') : t('chat.noManagerYet')}
          meSide="client"
          fetchMessages={() => api.me.messages('manager').then((r) => r.messages)}
          sendMessage={(body) => api.me.sendMessage(body, 'manager')}
          onClose={() => setChatWith(null)}
        />
      )}

      {chatWith === 'runner' && (
        <ChatModal
          title={data.runner.name || t('runnerChatTitle')}
          subtitle={t('runnerRole')}
          peerName={data.runner.name || t('runnerChatTitle')}
          peerAvatarUrl={data.runner.photoUrl}
          placeholder={t('chat.placeholder')}
          emptyText={t('runnerChatEmpty')}
          meSide="client"
          fetchMessages={() => api.me.messages('runner').then((r) => r.messages)}
          sendMessage={(body) => api.me.sendMessage(body, 'runner')}
          onClose={() => setChatWith(null)}
        />
      )}

      {intake && (
        <PackageIntakeModal
          pkgId={intake.pkgId}
          serviceIds={intake.services}
          busy={buying}
          onClose={() => setIntake(null)}
          onConfirm={(details) => confirmSelection(intake.pkgId, intake.services, details)}
        />
      )}

      {data.pendingReview && (
        <ReviewModal
          key={data.pendingReview.orderId}
          review={data.pendingReview}
          onSubmit={async (stars, text) => {
            try {
              setData(await api.me.review(data.pendingReview!.orderId, stars, text))
              toast(t('review.thanks'))
            } catch {}
          }}
          onSkip={async () => {
            try {
              setData(await api.me.skipReview(data.pendingReview!.orderId))
            } catch {}
          }}
        />
      )}
    </div>
  )
}

/* ---------- Consent gate (first sign-in) ---------- */
/**
 * First-run onboarding: welcome (greets them by their Telegram name + avatar) →
 * name (prefilled from Telegram, editable) → phone (typed, or pulled from
 * Telegram via requestContact). Terms are accepted on the LAST step, so
 * `!user.termsAccepted` keeps this mounted for the whole wizard.
 */
function ConsentGate({
  user,
  inTelegram,
  onAccept,
  onLogout,
  onDecline,
}: {
  user: {
    name: string
    phone?: string | null
    photo_url?: string | null
    telegram_id?: string | null
  }
  inTelegram: boolean
  onAccept: () => Promise<void> | void
  onLogout?: () => void
  /** Refuse the terms — cancels the registration and deletes the new account. */
  onDecline: () => void
}) {
  const t = useTranslations('Consent')
  const [step, setStep] = useState(0)
  const [busy, setBusy] = useState(false)
  const [confirmDecline, setConfirmDecline] = useState(false)

  // Prefer what Telegram tells us, fall back to the saved account name.
  const tgName = inTelegram ? telegramDisplayName() : ''
  const tgUser = inTelegram ? getTelegramUser() : null
  const [name, setName] = useState((user.name || tgName || '').trim())
  const [phone, setPhone] = useState(user.phone || '')
  const [waitingPhone, setWaitingPhone] = useState(false)
  const [phoneNote, setPhoneNote] = useState('')

  const avatarUrl = user.photo_url || tgUser?.photo_url || null
  const greetName = (name || tgName || '').split(' ')[0]

  /**
   * "Take from Telegram" — two paths:
   *  - Inside the Mini App: native requestContact(); Telegram sends the number to
   *    the BOT, so we poll our profile until the bot has stored it.
   *  - On the web (desktop): bounce to the bot with a one-time code, the user taps
   *    "share number" there, and we poll the code until it lands.
   */
  async function takePhoneFromTelegram() {
    setPhoneNote('')
    if (inTelegram && canRequestContact()) {
      const shared = await requestTelegramContact()
      if (!shared) {
        setPhoneNote(t('phone.declined'))
        return
      }
      setWaitingPhone(true)
      for (let i = 0; i < 15; i++) {
        await new Promise((r) => setTimeout(r, 1200))
        try {
          const me = await api.whoami()
          if (me.phone) {
            setPhone(me.phone)
            setWaitingPhone(false)
            return
          }
        } catch {}
      }
      setWaitingPhone(false)
      setPhoneNote(t('phone.timeout'))
      return
    }
    // Web path — open the bot, poll the one-time code.
    setWaitingPhone(true)
    let code = ''
    try {
      const r = await api.telegram.phoneStart()
      code = r.code
      window.open(r.url, '_blank', 'noopener')
    } catch {
      setWaitingPhone(false)
      setPhoneNote(t('phone.timeout'))
      return
    }
    for (let i = 0; i < 40; i++) {
      await new Promise((r) => setTimeout(r, 2000))
      try {
        const { phone: p } = await api.telegram.phonePoll(code)
        if (p) {
          setPhone(p)
          setWaitingPhone(false)
          return
        }
      } catch {}
    }
    setWaitingPhone(false)
    setPhoneNote(t('phone.timeout'))
  }

  async function finish() {
    setBusy(true)
    try {
      await api.me.updateProfile({ name: name.trim(), phone: phone.trim() })
    } catch {}
    await onAccept()
  }

  const steps = [t('steps.0'), t('steps.1'), t('steps.2')]

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-5 py-10">
      <div className="w-full max-w-[420px]">
        <div className="overflow-hidden rounded-[22px] border border-line bg-card shadow-card">
          {/* Hero — avatar + a personal greeting when we know who they are */}
          <div className="bg-accent-bg px-7 pb-7 pt-9 text-center">
            {avatarUrl || greetName ? (
              <Avatar
                url={avatarUrl}
                name={name || tgName || greetName}
                tgId={tgUser?.id ?? user.telegram_id}
                size={64}
                className="mx-auto shadow-sm"
              />
            ) : (
              <span className="mx-auto inline-flex items-center rounded-full bg-card px-4 py-2 shadow-sm">
                <Logo asLink={false} size={22} />
              </span>
            )}
            <h1 className="mt-4 font-display text-[26px] leading-tight text-ink">
              {greetName ? t('hello', { name: greetName }) : t('title')}
            </h1>
            <p className="mx-auto mt-1.5 max-w-[34ch] text-[14px] leading-relaxed text-muted">
              {step === 0 ? t('subtitle') : steps[step]}
            </p>
            {tgUser?.username && step === 0 && (
              <p className="mt-1 text-[12.5px] text-gray">@{tgUser.username}</p>
            )}
          </div>

          {/* Progress dots */}
          <div className="flex justify-center gap-1.5 pt-5">
            {steps.map((_, i) => (
              <span
                key={i}
                className={cn(
                  'h-1.5 rounded-full transition-all',
                  i === step ? 'w-5 bg-accent' : 'w-1.5 bg-line'
                )}
              />
            ))}
          </div>

          <div className="px-7 pb-6 pt-4">
            {step === 0 && (
              <>
                <ul className="flex flex-col gap-3.5">
                  {[0, 1, 2].map((i) => (
                    <li key={i} className="flex items-start gap-3">
                      <CheckCircle2 size={19} className="mt-px shrink-0 text-accent" />
                      <span className="text-[14px] leading-snug text-ink-2">
                        {t(`points.${i}` as any)}
                      </span>
                    </li>
                  ))}
                </ul>

                {/* Legal — full-width rows so long titles don't overflow */}
                <div className="mt-6 flex flex-col gap-2">
                  <Link
                    href="/privacy"
                    className="flex items-center justify-between gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 text-[13.5px] font-medium text-accent transition-colors hover:border-accent/40"
                  >
                    {t('privacy')} <ChevronRight size={16} className="shrink-0 text-accent/70" />
                  </Link>
                  <Link
                    href="/terms"
                    className="flex items-center justify-between gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 text-[13.5px] font-medium text-accent transition-colors hover:border-accent/40"
                  >
                    {t('terms')} <ChevronRight size={16} className="shrink-0 text-accent/70" />
                  </Link>
                </div>

                <Button variant="solid" size="block" className="mt-5" onClick={() => setStep(1)}>
                  {t('continue')}
                </Button>
                <p className="mx-auto mt-3 max-w-[38ch] text-center text-[12px] leading-relaxed text-gray">
                  {t('agree')}
                </p>
                {/* Declining cancels the registration — confirm, it deletes the
                    freshly-created account. */}
                {confirmDecline ? (
                  <div className="mt-4 rounded-lg border border-line bg-surface p-3.5">
                    <p className="text-center text-[13px] leading-snug text-ink-2">
                      {t('declineConfirm')}
                    </p>
                    <div className="mt-3 flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => setConfirmDecline(false)}
                      >
                        {t('back')}
                      </Button>
                      <Button
                        variant="solid"
                        size="sm"
                        className="flex-1"
                        onClick={onDecline}
                      >
                        {t('declineYes')}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirmDecline(true)}
                    className="mx-auto mt-3 block text-[13px] text-gray hover:text-ink"
                  >
                    {t('decline')}
                  </button>
                )}
              </>
            )}

            {step === 1 && (
              <>
                <label className="mb-1.5 block text-[13px] font-medium text-ink-2">
                  {t('name.label')}
                </label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={t('name.placeholder')}
                  autoFocus
                />
                <p className="mt-2 text-[12.5px] leading-snug text-gray">{t('name.hint')}</p>
                <Button
                  variant="solid"
                  size="block"
                  className="mt-5"
                  disabled={!name.trim()}
                  onClick={() => setStep(2)}
                >
                  {t('continue')}
                </Button>
                <button
                  onClick={() => setStep(0)}
                  className="mx-auto mt-3 block text-[13px] text-gray hover:text-ink"
                >
                  {t('back')}
                </button>
              </>
            )}

            {step === 2 && (
              <>
                <label className="mb-1.5 block text-[13px] font-medium text-ink-2">
                  {t('phone.label')}
                </label>
                <Input
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+998 90 123 45 67"
                  inputMode="tel"
                />
                {/* Mini App → native requestContact; web → bounce to the bot. Both
                    land in takePhoneFromTelegram. Hidden only on an old Mini App
                    client that supports neither. */}
                {(canRequestContact() || !inTelegram) && (
                  <Button
                    variant="outline"
                    size="block"
                    className="mt-2.5 gap-2 text-accent"
                    disabled={waitingPhone}
                    onClick={takePhoneFromTelegram}
                  >
                    <TelegramIcon /> {waitingPhone ? t('phone.waiting') : t('phone.fromTelegram')}
                  </Button>
                )}
                <p className="mt-2 text-[12.5px] leading-snug text-gray">
                  {phoneNote || (inTelegram ? t('phone.hint') : t('phone.hintWeb'))}
                </p>
                <Button
                  variant="solid"
                  size="block"
                  className="mt-5"
                  disabled={busy}
                  onClick={finish}
                >
                  {t('finish')}
                </Button>
                <button
                  onClick={() => setStep(1)}
                  className="mx-auto mt-3 block text-[13px] text-gray hover:text-ink"
                >
                  {t('back')}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ---------- Review prompt (package completed) ---------- */
function ReviewModal({
  review,
  onSubmit,
  onSkip,
}: {
  review: PendingReview
  onSubmit: (stars: number, text: string) => Promise<void>
  onSkip: () => Promise<void>
}) {
  const t = useTranslations('Profile')
  const tp = useTranslations('Packages')
  const ts = useTranslations('Services')
  const [stars, setStars] = useState(5)
  const [hover, setHover] = useState(0)
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)

  const itemName =
    review.itemType === 'package'
      ? tp(`${review.itemId}.name` as any)
      : ts(`items.${review.itemId}.name` as any)

  return (
    <div className="fixed inset-0 z-[99999] flex items-end justify-center bg-black/50 p-0 backdrop-blur-[2px] sm:items-center sm:p-6">
      <div className="w-full max-w-[440px] overflow-hidden rounded-t-2xl bg-surface sm:rounded-2xl">
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <span className="text-[13px] font-semibold text-muted">{t('review.eyebrow')}</span>
          <button
            onClick={() => !busy && onSkip()}
            className="text-gray hover:text-ink"
            aria-label="close"
          >
            <X size={18} />
          </button>
        </div>
        <div className="p-6 text-center">
          <div className="text-[34px]">🎉</div>
          <h3 className="mt-1 font-display text-[22px] text-ink">
            {t('review.title', { pkg: itemName })}
          </h3>
          <p className="mt-1.5 text-[13.5px] text-muted">{t('review.subtitle')}</p>

          <div className="mt-4 flex justify-center gap-1.5">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                onMouseEnter={() => setHover(n)}
                onMouseLeave={() => setHover(0)}
                onClick={() => setStars(n)}
                aria-label={`${n}`}
                className="p-0.5"
              >
                <Star
                  size={30}
                  className={cn(
                    'transition-colors',
                    (hover || stars) >= n ? 'fill-amber-400 text-amber-400' : 'text-gray-lt'
                  )}
                />
              </button>
            ))}
          </div>

          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={t('review.placeholder')}
            rows={3}
            className="mt-4 w-full resize-none rounded-lg border border-line bg-card px-3.5 py-2.5 text-[14px] text-ink outline-none focus:border-accent placeholder:text-gray-lt"
          />

          <Button
            variant="solid"
            size="block"
            className="mt-4"
            disabled={busy}
            onClick={async () => {
              setBusy(true)
              try {
                await onSubmit(stars, text.trim())
              } finally {
                setBusy(false)
              }
            }}
          >
            {t('review.submit')}
          </Button>
          <button
            onClick={() => !busy && onSkip()}
            className="mt-3 text-[13px] text-gray hover:text-ink"
          >
            {t('review.skip')}
          </button>
        </div>
      </div>
    </div>
  )
}

/* ---------- Package intake (arrival details for airport pickup) ---------- */
function PackageIntakeModal({
  pkgId,
  serviceIds = [],
  busy,
  onClose,
  onConfirm,
}: {
  pkgId: string | null
  serviceIds?: string[]
  busy: boolean
  onClose: () => void
  onConfirm: (details: Record<string, string>) => void
}) {
  const t = useTranslations('Profile')
  const tp = useTranslations('Packages')
  const ts = useTranslations('Services')
  // Name the thing being bought: the package, else the airport service.
  const airportSvc = serviceIds.find((s) => AIRPORT_SERVICES.has(s))
  const itemLabel = pkgId
    ? tp(`${pkgId}.name` as any)
    : airportSvc
      ? ts(`items.${airportSvc}.name` as any)
      : ''
  const [arrivalDate, setArrivalDate] = useState('')
  const [arrivalTime, setArrivalTime] = useState('')
  const [airport, setAirport] = useState<string>('')
  const [flight, setFlight] = useState('')
  const [dropoff, setDropoff] = useState('')
  const [dropoffCoords, setDropoffCoords] = useState<{ lat: number; lng: number } | null>(null)

  return (
    <div className="fixed inset-0 z-[99999] flex items-end justify-center bg-black/50 p-0 backdrop-blur-[2px] sm:items-center sm:p-6">
      <div className="max-h-[92vh] w-full max-w-[440px] overflow-y-auto rounded-t-2xl bg-surface sm:rounded-2xl">
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <h2 className="font-display text-[18px] text-ink">{t('intake.title')}</h2>
          <button onClick={onClose} className="text-gray hover:text-ink" aria-label="close">
            <X size={18} />
          </button>
        </div>
        <div className="flex flex-col gap-4 p-6">
          <p className="-mt-1 text-[13.5px] leading-snug text-muted">
            {t('intake.subtitle', { pkg: itemLabel })}
          </p>

          <label className="block">
            <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{t('intake.date')}</span>
            <DateTimeInput type="date" value={arrivalDate} onChange={setArrivalDate} placeholder={t('intake.datePick')} />
          </label>
          <label className="block">
            <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{t('intake.time')}</span>
            <DateTimeInput type="time" value={arrivalTime} onChange={setArrivalTime} placeholder={t('intake.timePick')} />
          </label>

          <PickOrType
            label={t('intake.airport')}
            options={LONDON_AIRPORT_TERMINALS}
            value={airport}
            onChange={setAirport}
            pickLabel={t('intake.airportPickList')}
            otherLabel={t('intake.other')}
            placeholder={t('intake.airportOther')}
          />

          <PickOrType
            label={t('intake.flight')}
            options={LONDON_FLIGHTS}
            value={flight}
            onChange={setFlight}
            pickLabel={t('intake.flightPickList')}
            otherLabel={t('intake.other')}
            placeholder={t('intake.flightOther')}
          />

          <label className="block">
            <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{t('intake.dropoff')}</span>
            <AddressField
              search={(q) => api.me.geocode(q).then((r) => r.results)}
              value={dropoff}
              placeholder={t('intake.dropoffPlaceholder')}
              onPick={(label, coords) => {
                setDropoff(label)
                setDropoffCoords(coords)
              }}
            />
          </label>

          <Button
            variant="solid"
            size="block"
            disabled={busy}
            onClick={() =>
              onConfirm({
                arrivalDate,
                arrivalTime,
                airport,
                flight: flight.trim(),
                dropoff: dropoff.trim(),
                ...(dropoffCoords
                  ? { dropoffLat: String(dropoffCoords.lat), dropoffLng: String(dropoffCoords.lng) }
                  : {}),
              })
            }
          >
            {t('intake.confirm')}
          </Button>
        </div>
      </div>
    </div>
  )
}

/* ---------- Inline purchase (rail; shown when no active package) ---------- */
function PurchasePanel({
  onCheckout,
  buying,
  ownedServices = [],
}: {
  onCheckout: (pkgId: string | null, serviceIds: string[]) => void
  buying: boolean
  /** Services the client already paid for separately. */
  ownedServices?: string[]
}) {
  const t = useTranslations('Profile')
  // One button opens the full onboarding-style picker (packages + services) in a
  // sheet — no more cramped inline list / separate detour to /services.
  const [sheetOpen, setSheetOpen] = useState(false)

  return (
    <div className="rounded-xl border border-line bg-card p-5 text-center">
      <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-accent-bg">
        <ShoppingBag size={20} className="text-accent" />
      </span>
      <div className="mt-3 font-display text-[17px] text-ink">{t('buyPackageTitle')}</div>
      <p className="mx-auto mt-1 max-w-[34ch] text-[12.5px] leading-snug text-muted">
        {t('buyServiceHint')}
      </p>
      <Button variant="solid" size="block" className="mt-4" disabled={buying} onClick={() => setSheetOpen(true)}>
        {t('pick.sheetTitle')}
      </Button>

      {sheetOpen && (
        <PurchaseSheet
          buying={buying}
          ownedServices={ownedServices}
          onCheckout={onCheckout}
          onClose={() => setSheetOpen(false)}
        />
      )}
    </div>
  )
}

/* ---------- People (manager / runner) ---------- */
function PersonAvatar({ url, name }: { url?: string | null; name?: string | null }) {
  const [failed, setFailed] = useState(false)
  useEffect(() => setFailed(false), [url])
  if (url && !failed)
    // eslint-disable-next-line @next/next/no-img-element
    return (
      <img
        src={url}
        alt={name || ''}
        className="h-11 w-11 shrink-0 rounded-full object-cover"
        referrerPolicy="no-referrer"
        onError={() => setFailed(true)}
      />
    )
  return (
    <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent-bg font-display text-[16px] text-accent">
      {(name || '?').charAt(0)}
    </span>
  )
}

function PersonContact({ telegram, phone }: { telegram?: string | null; phone?: string | null }) {
  const t = useTranslations('Profile')
  const { toast } = useToast()
  const [copied, setCopied] = useState(false)
  if (!telegram && !phone) return null

  async function copyPhone() {
    if (!phone) return
    try {
      await navigator.clipboard.writeText(phone)
      setCopied(true)
      toast(t('contact.copied'))
      setTimeout(() => setCopied(false), 1500)
    } catch {}
  }

  return (
    <div className="mt-3 flex flex-col gap-2">
      {telegram && (
        <a
          href={`https://t.me/${telegram}`}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2.5 rounded-lg border border-line bg-surface px-3 py-2 text-[13px] transition-colors hover:border-accent/40"
        >
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent-bg text-accent">
            <TelegramIcon />
          </span>
          <span className="min-w-0 flex-1">
            <span className="block text-[10.5px] font-medium uppercase tracking-wide text-gray">
              {t('contact.telegram')}
            </span>
            <span className="block truncate font-medium text-accent">@{telegram}</span>
          </span>
          <ExternalLink size={13} className="shrink-0 text-gray" />
        </a>
      )}
      {phone && (
        // tel: opens the dialer on a phone; the copy button makes the number
        // usable on desktop and inside the Telegram WebView (where tel: is inert).
        <div className="flex items-center gap-2.5 rounded-lg border border-line bg-surface px-3 py-2 text-[13px]">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent-bg text-accent">
            <Phone size={14} />
          </span>
          <a href={`tel:${phone}`} className="min-w-0 flex-1">
            <span className="block text-[10.5px] font-medium uppercase tracking-wide text-gray">
              {t('contact.phone')}
            </span>
            <span className="block truncate font-medium text-ink">{phone}</span>
          </a>
          <button
            type="button"
            onClick={copyPhone}
            aria-label={t('contact.copy')}
            className="shrink-0 text-gray transition-colors hover:text-accent"
          >
            {copied ? <Check size={14} className="text-accent" /> : <Copy size={14} />}
          </button>
        </div>
      )}
    </div>
  )
}

/* ---------- Attachments (files uploaded by the operator) ---------- */
function AttachmentChips({ files }: { files: Attachment[] }) {
  if (!files || files.length === 0) return null
  return (
    <div className="mt-2.5 flex flex-wrap gap-1.5">
      {files.map((f) => (
        <a
          key={f.id}
          href={f.url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 rounded-full border border-accent/30 bg-accent-bg px-2.5 py-1 text-[12px] font-medium text-accent transition-colors hover:bg-accent hover:text-white"
        >
          <Paperclip size={12} /> <span className="max-w-[150px] truncate">{f.filename}</span>
        </a>
      ))}
    </div>
  )
}

/* ---------- Housing shortlist ---------- */
function hostOf(u: string) {
  try {
    return new URL(u).hostname.replace(/^www\./, '')
  } catch {
    return u
  }
}

// Solid, opaque chips: these sit over housing photos (often light), so a
// transparent tint washes out. White base + colored text stays legible on any image.
const HOUSING_TONE: Record<string, string> = {
  new: 'bg-card text-ink ring-1 ring-line',
  requested: 'bg-card text-amber-700 ring-1 ring-line',
  approved: 'bg-accent-bg text-accent ring-1 ring-accent/30',
  arranging: 'bg-card text-sky-700 ring-1 ring-line',
  viewing: 'bg-card text-sky-700 ring-1 ring-line',
  viewed: 'bg-card text-accent ring-1 ring-line',
  reached: 'bg-card text-accent ring-1 ring-line',
  busy: 'bg-card text-amber-700 ring-1 ring-line',
  secured: 'bg-card text-accent ring-1 ring-line',
  completed: 'bg-accent text-white',
  declined: 'bg-card text-terracotta ring-1 ring-line',
}

function HousingStatusBadge({ status }: { status: string }) {
  const t = useTranslations('Profile')
  return (
    <span
      className={cn(
        'rounded-full px-2.5 py-1 text-[11px] font-semibold shadow-sm',
        HOUSING_TONE[status] || HOUSING_TONE.new
      )}
    >
      {t(`housing.status.${status}` as any)}
    </span>
  )
}

function HousingCard({
  h,
  onRemove,
  onRequest,
  onPay,
}: {
  h: HousingItem
  onRemove: (id: number) => void
  onRequest: (id: number) => Promise<void>
  onPay: (id: number) => Promise<void>
}) {
  const t = useTranslations('Profile')
  const [busy, setBusy] = useState(false)
  const isCatalog = h.source === 'catalog'
  const run = async (fn: (id: number) => Promise<void>) => {
    setBusy(true)
    try {
      await fn(h.id)
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-card">
      <div className="relative h-[160px]">
        {h.photoUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={h.photoUrl} alt="" className="h-full w-full object-cover" referrerPolicy="no-referrer" />
        ) : (
          <div className="photo-stripe h-full w-full" />
        )}
        <span className="absolute left-3 top-3">
          <HousingStatusBadge status={h.status} />
        </span>
        <button
          onClick={() => onRemove(h.id)}
          className="absolute right-3 top-3 flex h-7 w-7 items-center justify-center rounded-full bg-white/85 text-gray hover:text-terracotta"
          aria-label="remove"
        >
          <Trash2 size={14} />
        </button>
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <span className="min-w-0 truncate text-[14.5px] font-semibold text-ink">
            {h.title || h.addr || hostOf(h.ref)}
          </span>
          {h.priceGBP > 0 && (
            <span className="shrink-0 font-display text-[17px] text-accent">{fmtGBP(h.priceGBP)}</span>
          )}
        </div>
        {h.description && (
          <p className="mt-1 line-clamp-2 text-[12.5px] leading-snug text-ink-2">{h.description}</p>
        )}
        {h.source === 'link' && (
          <a
            href={h.ref}
            target="_blank"
            rel="noreferrer"
            className="mt-1 inline-flex items-center gap-1 text-[12px] text-muted hover:text-accent"
          >
            <ExternalLink size={11} /> {hostOf(h.ref)}
          </a>
        )}

        {(h.status === 'viewing' || h.status === 'approved') && h.viewingAt && (
          <div className="mt-2.5 rounded-lg bg-sky-500/10 px-3 py-2 text-[13px] font-medium text-sky-700">
            📅 {t('housing.viewingAt', { when: h.viewingAt.replace('T', ' ') })}
          </div>
        )}
        {h.note && <div className="mt-2 text-[12.5px] leading-snug text-ink-2">{h.note}</div>}

        {/* Request → operator review → pay. Catalog = £100 arrangement (no visit);
            custom link = £30 accompanied viewing after a slot is set. */}
        {h.status === 'new' || h.status === 'declined' ? (
          <Button variant="outline" size="sm" className="mt-3 w-full" disabled={busy} onClick={() => run(onRequest)}>
            {isCatalog ? t('housing.wantCatalog') : t('housing.wantCustom')}
          </Button>
        ) : h.status === 'requested' ? (
          <div className="mt-3 rounded-lg bg-accent-bg px-3 py-2 text-[12.5px] font-medium text-accent">
            {t('housing.requestedInfo')}
          </div>
        ) : h.status === 'approved' ? (
          isCatalog ? (
            <Button variant="solid" size="sm" className="mt-3 w-full" disabled={busy} onClick={() => run(onPay)}>
              {t('housing.arrangePay', { price: ARRANGEMENT_PRICE })}
            </Button>
          ) : h.viewingAt ? (
            <Button variant="solid" size="sm" className="mt-3 w-full" disabled={busy} onClick={() => run(onPay)}>
              {t('housing.viewingPay', { price: VIEWING_PRICE })}
            </Button>
          ) : (
            <div className="mt-3 rounded-lg bg-accent-bg px-3 py-2 text-[12.5px] font-medium text-accent">
              {t('housing.approvedWait')}
            </div>
          )
        ) : null}

        {h.media.length > 0 && (
          <div className="mt-3">
            <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-gray">
              {t('housing.mediaTitle')}
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {h.media.map((m) =>
                m.kind === 'video' ? (
                  <video key={m.id} src={m.url} controls className="h-16 w-full rounded-md object-cover" />
                ) : (
                  <a key={m.id} href={m.url} target="_blank" rel="noreferrer">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={m.url} alt="" className="h-16 w-full rounded-md object-cover" />
                  </a>
                )
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function HousingSection({ items, onRefresh }: { items: HousingItem[]; onRefresh: () => void }) {
  const t = useTranslations('Profile')
  const { toast } = useToast()
  const [url, setUrl] = useState('')
  const [busy, setBusy] = useState(false)

  async function add() {
    const ref = url.trim()
    if (!ref || busy) return
    setBusy(true)
    try {
      await api.me.addHousing({ source: 'link', ref, title: hostOf(ref) })
      setUrl('')
      onRefresh()
      toast(t('housing.added'))
    } catch {
    } finally {
      setBusy(false)
    }
  }
  async function remove(id: number) {
    try {
      await api.me.deleteHousing(id)
      onRefresh()
    } catch {}
  }
  async function requestHousing(id: number) {
    try {
      await api.me.requestHousing(id)
      onRefresh()
      toast(t('housing.requestedInfo'))
    } catch {}
  }
  async function payHousing(id: number) {
    try {
      await api.me.payHousing(id)
      onRefresh()
      toast(t('housing.paidToast'))
    } catch {}
  }

  return (
    <div className="mt-9">
      <div className="eyebrow mb-1">{t('housing.title')}</div>
      <p className="mb-4 max-w-[60ch] text-[13.5px] leading-relaxed text-muted">{t('housing.subtitle')}</p>

      {/* Prominent catalog CTA */}
      <Link
        href="/search"
        className="nd-lift mb-5 flex items-center justify-between gap-4 rounded-xl bg-accent p-5 text-white"
      >
        <span className="flex items-center gap-3.5">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white/15">
            <Home size={20} />
          </span>
          <span>
            <span className="block font-display text-[18px] text-white">{t('housing.browse')}</span>
            <span className="block text-[12.5px] text-white/75">{t('housing.browseHint')}</span>
          </span>
        </span>
        <span className="text-[20px] text-white/80">→</span>
      </Link>

      {/* Paste a link */}
      <div className="mb-5 flex flex-col gap-2 rounded-xl border border-line bg-card p-4 sm:flex-row sm:items-center">
        <Input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder={t('housing.linkPlaceholder')}
          className="flex-1"
        />
        <Button variant="dark" size="md" className="shrink-0 gap-1.5" onClick={add} disabled={busy || !url.trim()}>
          <Plus size={15} /> {t('housing.add')}
        </Button>
      </div>

      {items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-line bg-surface p-8 text-center">
          <Home size={22} className="mx-auto text-gray-lt" />
          <p className="mt-2 text-[13.5px] text-muted">{t('housing.empty')}</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {items.map((h) => (
            <HousingCard key={h.id} h={h} onRemove={remove} onRequest={requestHousing} onPay={payHousing} />
          ))}
        </div>
      )}
    </div>
  )
}

/* ---------- Package + services picker ---------- */
/**
 * The shared "choose a package and/or services" UI. A package and any extra
 * services are chosen together and paid for in ONE checkout. Used both as the
 * first-run empty cabinet (`barMode="fixed"`, full page) and inside the
 * re-purchase sheet opened from the populated cabinet (`barMode="inline"`).
 * `ownedServices` are shown as already-active and can't be re-picked.
 */
function PackagePicker({
  onCheckout,
  buying,
  initialPkg,
  ownedServices = [],
  heading,
  barMode = 'fixed',
}: {
  onCheckout: (pkgId: string | null, serviceIds: string[]) => void
  buying: boolean
  initialPkg?: string | null
  ownedServices?: string[]
  heading?: React.ReactNode
  barMode?: 'fixed' | 'inline'
}) {
  const t = useTranslations('Profile')
  const tp = useTranslations('Packages')
  const ts = useTranslations('Services')
  const tl = useTranslations('Landing')
  const td = useTranslations('Duplicate')
  const [pkg, setPkg] = useState<string | null>(initialPkg ?? null)
  const [services, setServices] = useState<string[]>([])
  const [warnDupes, setWarnDupes] = useState(false)
  // The landing's "?pkg=" arrives after mount (read from the URL in an effect).
  useEffect(() => {
    if (initialPkg) setPkg(initialPkg)
  }, [initialPkg])

  // Services the chosen package already covers — warned about, never blocked.
  const dupes = coveredServices(pkg, services)

  function submit() {
    if (dupes.length) setWarnDupes(true)
    else onCheckout(pkg, services)
  }

  const toggleService = (id: string) =>
    setServices((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))

  const pkgPrice = pkg ? (PACKAGES.find((p) => p.id === pkg)?.gbp ?? 0) : 0
  const svcPrice = services.reduce(
    (sum, id) => sum + (SERVICES.find((s) => s.id === id)?.price ?? 0),
    0
  )
  const total = pkgPrice + svcPrice
  const nothingPicked = !pkg && services.length === 0

  return (
    <div className={cn('mx-auto max-w-[1000px]', barMode === 'fixed' ? 'pb-44' : 'pb-4')}>
      {heading}

      {/* ---- Step 1 — pick a package (or skip straight to services) ---- */}
      <div className="mt-10">
        <div className="mb-4 flex items-baseline gap-2.5">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent text-[12px] font-bold text-white">
            1
          </span>
          <h2 className="font-display text-[19px] text-ink">{t('pick.packagesTitle')}</h2>
        </div>

        <div className="grid items-stretch gap-4 md:grid-cols-3">
          {PACKAGES.map((p) => {
            const selected = pkg === p.id
            const features = Array.from({ length: p.featureCount }, (_, i) =>
              tp(`${p.id}.features.${i}`)
            )
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => setPkg(selected ? null : p.id)}
                className={cn(
                  'relative flex flex-col rounded-xl border p-5 text-left transition-all',
                  selected
                    ? 'border-accent bg-accent-bg ring-2 ring-accent'
                    : 'border-line bg-card hover:border-accent/40'
                )}
              >
                {p.popular && !selected && (
                  <span className="absolute -top-2.5 left-5 rounded-full bg-accent px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.08em] text-white">
                    {tl('popular')}
                  </span>
                )}
                <div className="flex items-start justify-between gap-2">
                  <span className="font-display text-[19px] text-ink">{tp(`${p.id}.name`)}</span>
                  <span
                    className={cn(
                      'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border',
                      selected ? 'border-accent bg-accent' : 'border-line bg-surface'
                    )}
                  >
                    {selected && <Check size={13} strokeWidth={3.5} className="text-white" />}
                  </span>
                </div>
                <div className="mt-2 font-display text-[27px] text-ink">{fmtGBP(p.gbp)}</div>
                <div className="text-[12px] text-gray">{fmtUZS(p.gbp)}</div>
                <div className="mt-3 flex flex-col gap-1.5">
                  {features.map((f, i) => (
                    <span key={i} className="flex gap-1.5 text-[12.5px] leading-snug text-ink-2">
                      <span className="font-bold text-accent">✓</span>
                      {f}
                    </span>
                  ))}
                </div>
              </button>
            )
          })}
        </div>
        <p className="mt-3 text-center text-[13px] text-gray">{t('pick.packagesHint')}</p>
      </div>

      {/* ---- Step 2 — optional extra services ---- */}
      <div className="mt-10">
        <div className="mb-4 flex items-baseline gap-2.5">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent text-[12px] font-bold text-white">
            2
          </span>
          <h2 className="font-display text-[19px] text-ink">{t('pick.servicesTitle')}</h2>
        </div>

        <div className="flex flex-col gap-6">
          {SERVICE_STAGES.map((stage) => {
            const list = SERVICES.filter((s) => s.stage === stage)
            if (!list.length) return null
            return (
              <div key={stage}>
                <div className="eyebrow mb-2.5">{ts(`stages.${stage}`)}</div>
                <div className="grid gap-2 sm:grid-cols-2">
                  {list.map((s) => {
                    const owned = ownedServices.includes(s.id)
                    const on = services.includes(s.id)
                    const included = packageCovers(pkg, s.id)
                    return (
                      <button
                        key={s.id}
                        type="button"
                        disabled={owned}
                        onClick={() => toggleService(s.id)}
                        className={cn(
                          'flex items-start gap-3 rounded-lg border p-3.5 text-left transition-colors',
                          owned
                            ? 'cursor-default border-line bg-card opacity-55'
                            : on && included
                              ? 'border-amber-500/60 bg-amber-500/10'
                              : on
                                ? 'border-accent bg-accent-bg'
                                : included
                                  ? 'border-line bg-card opacity-60 hover:border-accent/40'
                                  : 'border-line bg-card hover:border-accent/40'
                        )}
                      >
                        <span
                          className={cn(
                            'mt-0.5 flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-[5px] border',
                            on || owned ? 'border-accent bg-accent' : 'border-line bg-surface'
                          )}
                        >
                          {(on || owned) && <Check size={12} strokeWidth={3.5} className="text-white" />}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="flex items-baseline justify-between gap-2">
                            <span className="text-[13.5px] font-medium text-ink">
                              {ts(`items.${s.id}.name`)}
                            </span>
                            <span className="shrink-0 text-[13px] font-semibold text-accent">
                              {fmtGBP(s.price)}
                            </span>
                          </span>
                          {owned ? (
                            <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-accent/12 px-2 py-0.5 text-[11px] font-medium text-accent">
                              {t('pick.owned')}
                            </span>
                          ) : included ? (
                            <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-amber-500/15 px-2 py-0.5 text-[11px] font-medium text-amber-700">
                              {td('inPackage')}
                            </span>
                          ) : (
                            <span className="mt-0.5 block text-[12.5px] leading-snug text-muted">
                              {ts(`items.${s.id}.desc`)}
                            </span>
                          )}
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ---- Floating total + single checkout ----
          Lifted off the bottom edge (safe-area + margin) so it stays comfortably
          reachable and doesn't collide with phone/Telegram bottom bars. */}
      <div
        className={cn(
          barMode === 'fixed'
            ? 'pointer-events-none fixed inset-x-0 bottom-0 z-40 px-4 pb-[calc(env(safe-area-inset-bottom,0px)+1.25rem)] pt-2'
            : 'sticky bottom-3 z-40 pt-3'
        )}
      >
        <div
          className={cn(
            'mx-auto max-w-[1000px] rounded-2xl border border-line bg-surface/95 shadow-card backdrop-blur',
            barMode === 'fixed' && 'pointer-events-auto'
          )}
        >
          {dupes.length > 0 && (
            <div className="flex items-start gap-2 border-b border-line px-5 py-2.5 text-[12.5px] leading-snug text-amber-700">
              <span className="mt-[5px] h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
              {td('body', { pkg: pkg ? tp(`${pkg}.name`) : '' })}
            </div>
          )}
          <div className="flex items-center gap-4 px-5 py-3">
            <div className="min-w-0 flex-1">
              {nothingPicked ? (
                <div className="text-[13px] text-muted">{t('pick.nothing')}</div>
              ) : (
                <div className="flex flex-wrap items-center gap-1.5">
                  {pkg && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-accent/12 px-2.5 py-1 text-[12px] font-semibold text-accent">
                      {tp(`${pkg}.name`)}
                      <span className="font-normal opacity-70">{fmtGBP(pkgPrice)}</span>
                    </span>
                  )}
                  {services.length > 0 && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-ink/[.06] px-2.5 py-1 text-[12px] font-medium text-ink-2">
                      {t('pick.servicesCount', { count: services.length })}
                      <span className="opacity-70">{fmtGBP(svcPrice)}</span>
                    </span>
                  )}
                </div>
              )}
              <div className="mt-1 flex items-baseline gap-1.5">
                <span className="text-[11.5px] uppercase tracking-wide text-gray">{t('pick.total')}</span>
                <span className="font-display text-[21px] leading-none text-ink">{fmtGBP(total)}</span>
              </div>
            </div>
            <Button variant="solid" disabled={buying || nothingPicked} onClick={submit}>
              {t('pick.checkout')}
            </Button>
          </div>
        </div>
      </div>

      {warnDupes && (
        <DuplicateWarningModal
          pkgName={pkg ? tp(`${pkg}.name`) : ''}
          serviceNames={dupes.map((id) => ts(`items.${id}.name`))}
          onCancel={() => {
            // "Remove extras" — drop just the duplicated ones, keep the rest.
            setServices((s) => s.filter((id) => !dupes.includes(id)))
            setWarnDupes(false)
          }}
          onProceed={() => {
            setWarnDupes(false)
            onCheckout(pkg, services)
          }}
        />
      )}
    </div>
  )
}

/* ---------- Empty (first-time) cabinet — the picker with a welcome heading ---------- */
function EmptyCabinet({
  onCheckout,
  buying,
  initialPkg,
}: {
  onCheckout: (pkgId: string | null, serviceIds: string[]) => void
  buying: boolean
  initialPkg?: string | null
}) {
  const t = useTranslations('Profile')
  return (
    <PackagePicker
      onCheckout={onCheckout}
      buying={buying}
      initialPkg={initialPkg}
      heading={
        <div className="text-center">
          <h1 className="font-display text-[30px] text-ink sm:text-[36px]">{t('emptyTitle')}</h1>
          <p className="mx-auto mt-3 max-w-[52ch] text-[15px] leading-relaxed text-muted">
            {t('emptyText')}
          </p>
        </div>
      }
    />
  )
}

/* ---------- Re-purchase sheet — the same picker in a full-screen overlay ---------- */
/**
 * Opened from the populated cabinet's "buy a package or service" button so a
 * returning client gets the exact same picker they saw during onboarding,
 * instead of a cramped inline list. `ownedServices` are shown as already-active.
 */
function PurchaseSheet({
  onCheckout,
  buying,
  ownedServices,
  onClose,
}: {
  onCheckout: (pkgId: string | null, serviceIds: string[]) => void
  buying: boolean
  ownedServices: string[]
  onClose: () => void
}) {
  const t = useTranslations('Profile')
  return (
    <div className="fixed inset-0 z-[9990] flex flex-col bg-paper">
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-surface px-5 py-4 sm:px-8">
        <h2 className="font-display text-[18px] text-ink">{t('pick.sheetTitle')}</h2>
        <button onClick={onClose} className="text-gray hover:text-ink" aria-label="close">
          <X size={20} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-5 py-6 sm:px-8">
        <PackagePicker
          barMode="inline"
          buying={buying}
          ownedServices={ownedServices}
          onCheckout={(pkgId, serviceIds) => {
            onClose()
            onCheckout(pkgId, serviceIds)
          }}
        />
      </div>
    </div>
  )
}

/* ---------- Populated ---------- */
function ServiceStatusBadge({ status }: { status: string }) {
  const t = useTranslations('Profile')
  const done = status === 'done'
  return (
    <span
      className={cn(
        'rounded-full px-2 py-0.5 text-[11px] font-medium',
        done ? 'bg-accent/15 text-accent' : 'bg-amber-500/15 text-amber-700'
      )}
    >
      {done ? t('serviceDone') : t('serviceInProgress')}
    </span>
  )
}

/* ---------- Airport greeter: "how to find the person meeting you" ---------- */
// A friendly character — smiling face, tilted head, holding a sign at chest
// height that shows the real Nothard wordmark (not = ink, hard. = green) one-to-one.
// Self-contained fixed palette (it's an illustration/sticker) so it reads clearly
// in both light and dark themes.
function GreeterSign({ size = 128 }: { size?: number }) {
  return (
    <svg
      viewBox="0 0 140 118"
      role="img"
      aria-label="Nothard greeter smiling and holding a sign"
      style={{ width: size }}
      className="h-auto shrink-0"
    >
      {/* soft backdrop panel */}
      <rect x="0" y="0" width="140" height="118" rx="16" fill="#f1eee6" />
      {/* shoulders / torso — green shirt */}
      <path d="M32 118C32 86 46 72 70 72s38 14 38 46Z" fill="#2f5d45" />
      {/* neck */}
      <rect x="63" y="56" width="14" height="13" rx="5" fill="#f2cda8" />
      {/* face */}
      <circle cx="70" cy="40" r="19" fill="#f2cda8" />
      {/* soft cheeks */}
      <circle cx="59.5" cy="46" r="3" fill="#e8917a" opacity="0.35" />
      <circle cx="80.5" cy="46" r="3" fill="#e8917a" opacity="0.35" />
      {/* hair — a tidy cap over the top */}
      <path
        d="M51 43 C51 11 89 11 89 43 C84 36 77 34 70 34 C63 34 56 36 51 43 Z"
        fill="#3a332c"
      />
      {/* eyes */}
      <circle cx="63" cy="41" r="2" fill="#3a332c" />
      <circle cx="77" cy="41" r="2" fill="#3a332c" />
      {/* gentle smile */}
      <path d="M64 48 Q70 53 76 48" fill="none" stroke="#3a332c" strokeWidth="2.4" strokeLinecap="round" />
      {/* the sign — held at chest height */}
      <rect x="22" y="82" width="96" height="32" rx="8" fill="#ffffff" stroke="#e5e0d5" strokeWidth="1.5" />
      <text
        x="70"
        y="103"
        textAnchor="middle"
        fontFamily="var(--font-onest), sans-serif"
        fontSize="16.5"
        fontWeight="700"
        letterSpacing="-0.02em"
      >
        <tspan fill="#1b1a17">not</tspan>
        <tspan fill="#2f5d45">hard.</tspan>
      </text>
      {/* hands gripping the top corners */}
      <rect x="26" y="78" width="12" height="10" rx="4" fill="#f2cda8" />
      <rect x="102" y="78" width="12" height="10" rx="4" fill="#f2cda8" />
    </svg>
  )
}

function MeetingSignNote() {
  const t = useTranslations('Profile')
  return (
    <div className="mt-3 flex items-center gap-4 rounded-xl border border-line bg-surface p-4">
      <GreeterSign size={116} />
      <div className="min-w-0">
        <div className="text-[13.5px] font-semibold text-ink">{t('meetSign.title')}</div>
        <p className="mt-1 text-[12.5px] leading-relaxed text-muted">{t('meetSign.body')}</p>
      </div>
    </div>
  )
}

/* ---------- Order history (past & current purchases) ---------- */
function fmtDateTime(iso?: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleString(undefined, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function OrderHistory({ items }: { items: OrderHistoryItem[] }) {
  const t = useTranslations('Profile')
  const tp = useTranslations('Packages')
  const ts = useTranslations('Services')
  const label = useTaskLabel()
  const [open, setOpen] = useState(false)
  // Show only once the client has at least one COMPLETED order — nothing to look
  // back on before that. Once shown, it stays (includes active orders too).
  if (!items || !items.some((it) => it.status === 'done')) return null

  const nameOf = (it: OrderHistoryItem) =>
    it.type === 'package'
      ? tp(`${it.id}.name` as any)
      : it.type === 'viewing'
        ? t('history.viewing')
        : it.type === 'arrangement'
          ? t('history.arrangement')
          : ts(`items.${it.id}.name` as any)

  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="btn-motion flex w-full items-center gap-3 rounded-xl border border-line bg-card px-4 py-3.5 text-left transition-colors hover:border-accent/40"
      >
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent-bg text-accent">
          <History size={17} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-[14.5px] font-semibold text-ink">{t('history.title', { count: items.length })}</span>
          <span className="block text-[12.5px] text-muted">{open ? t('history.hide') : t('history.show')}</span>
        </span>
        <ChevronDown size={18} className={cn('shrink-0 text-gray transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="mt-3 flex flex-col gap-3">
          {items.map((it, i) => {
            const done = it.status === 'done'
            return (
              <div key={`${it.type}-${it.id}-${i}`} className="rounded-xl border border-line bg-card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="min-w-0 truncate text-[14.5px] font-semibold text-ink">{nameOf(it)}</span>
                      <span
                        className={cn(
                          'shrink-0 rounded-full px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide',
                          done ? 'bg-accent-bg text-accent' : 'bg-sub text-muted'
                        )}
                      >
                        {done ? t('history.done') : t('history.active')}
                      </span>
                    </div>
                    <div className="mt-0.5 text-[12px] leading-snug text-muted">
                      {it.createdAt && <>{t('history.bought')}: {fmtDateTime(it.createdAt)}</>}
                      {done && it.completedAt && (
                        <> · {t('history.completed')}: {fmtDateTime(it.completedAt)}</>
                      )}
                    </div>
                  </div>
                  <span className="shrink-0 font-display text-[16px] text-accent">{fmtGBP(it.amountGBP)}</span>
                </div>

                {it.steps && it.steps.length > 0 && (
                  <ul className="mt-3 flex flex-col gap-1.5 border-t border-line pt-3">
                    {it.steps.map((s) => (
                      <li key={s.key} className="flex items-center justify-between gap-2 text-[12.5px]">
                        <span className="flex min-w-0 items-center gap-2 text-ink-2">
                          <span
                            className="h-1.5 w-1.5 shrink-0 rounded-full"
                            style={{ background: s.status === 'done' ? 'rgb(var(--accent))' : 'rgb(var(--line))' }}
                          />
                          <span className="truncate">{label('step', s.key).title}</span>
                        </span>
                        <span className="shrink-0 text-gray-lt">
                          {s.status === 'done' && s.completedAt ? fmtDateTime(s.completedAt) : ''}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function PopulatedCabinet({
  data,
  trip,
  onChat,
  onBuy,
  onCheckout,
  buying,
  onRefresh,
}: {
  data: DashboardData
  trip: TripLive | null
  onChat: (who?: 'manager' | 'runner') => void
  onBuy: (id: string) => void
  onCheckout: (pkgId: string | null, serviceIds: string[]) => void
  buying: boolean
  onRefresh: () => void
}) {
  const t = useTranslations('Profile')
  const tp = useTranslations('Packages')
  const ts = useTranslations('Services')
  const label = useTaskLabel()
  const { toast } = useToast()
  const [arrivalOpen, setArrivalOpen] = useState(false)
  const [shareOpen, setShareOpen] = useState(false)

  const steps = data.path.filter((p) => p.kind === 'step')
  const total = steps.length
  const hasPackage = !!data.package && total > 0
  // Show the relocation path whenever there are steps — including the two arrival
  // steps a standalone airport service now creates (not only for a full package).
  const hasPath = total > 0
  const completedServices = data.completedServices || []
  // Parallel path: each step carries its own status (housing search, temp stay and
  // viewings can all run at once), so progress is simply how many are done — not a
  // single "current" cursor.
  const doneCount = steps.filter((s) => s.status === 'done').length
  const percent = total ? Math.round((doneCount / total) * 100) : 0
  const documents = data.documents || {}
  const docKeys = DOC_KEYS.filter((d) => d in documents)
  const manager = data.manager

  return (
    <>
      {/* Greeting — always first, on mobile and desktop */}
      <div className="mb-6">
        <h2 className="font-display text-[24px] leading-tight text-ink sm:text-[27px]">
          {t('greetingHi')}, {data.user.name.split(' ')[0]} <span className="ml-0.5 align-middle">👋</span>
        </h2>
      </div>

      {/* Live "your host is on the way" map — right under the greeting */}
      {trip && trip.status !== 'cancelled' && (
        <div className="mb-6">
          <TripCard trip={trip} minimal />
        </div>
      )}

      {/* Mobile order: package/arrival → path → people. Desktop: a two-column grid
          where package (top) + people (below) share the left rail and the path
          spans the right. Explicit grid placement + `order-*` gives both layouts. */}
      <div className="flex flex-col gap-8 lg:grid lg:grid-cols-[296px_1fr] lg:items-start">
        {/* Block 1 — your package / arrival details (min-w-0 so wide content can't
            push a grid column past a phone's viewport). */}
        <div className="order-1 flex min-w-0 flex-col gap-5 lg:col-start-1 lg:row-start-1">
        {data.package ? (
          <div className="rounded-xl bg-accent p-5 text-white">
            <div className="flex items-center justify-between">
              <div className="text-[11px] font-semibold uppercase tracking-[0.1em] text-white/60">
                {t('packageCard')}
              </div>
              <span
                className={cn(
                  'rounded-full px-2 py-0.5 text-[10.5px] font-semibold',
                  data.package.paid ? 'bg-white/20 text-white' : 'bg-card text-terracotta'
                )}
              >
                {data.package.paid ? t('paidBadge') : t('unpaidBadge')}
              </span>
            </div>
            <div className="mt-2 font-display text-[24px] text-white">{tp(`${data.package.id}.name` as any)}</div>
            <div className="mt-3 flex items-baseline justify-between">
              <span className="text-[12.5px] text-white/70">{t('amount')}</span>
              <span className="font-display text-[22px] text-white">{fmtGBP(data.package.amountGBP)}</span>
            </div>

            {/* Arrival details — editable by the client */}
            {data.package.hasAirportMeet && (
              <div className="mt-4 rounded-lg bg-white/10 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold uppercase tracking-wide text-white/60">
                    {t('arrival.title')}
                  </span>
                  <button
                    onClick={() => setArrivalOpen(true)}
                    className="text-[12px] font-medium text-white/85 underline underline-offset-2 hover:text-white"
                  >
                    {t('arrival.edit')}
                  </button>
                </div>
                {data.package.details?.arrivalDate || data.package.details?.flight ? (
                  <div className="mt-1.5 text-[13px] text-white/90">
                    {data.package.details.arrivalDate && (
                      <div>
                        ✈️ {fmtDate(data.package.details.arrivalDate)} {data.package.details.arrivalTime}
                        {data.package.details.airport ? ` · ${data.package.details.airport}` : ''}
                      </div>
                    )}
                    {data.package.details.flight && (
                      <div className="text-white/75">{t('intake.flight')}: {data.package.details.flight}</div>
                    )}
                  </div>
                ) : (
                  <div className="mt-1 text-[12.5px] text-white/60">{t('arrival.none')}</div>
                )}
              </div>
            )}

          </div>
        ) : data.arrival.hasAirportMeet ? (
          /* Standalone airport service — arrival info is the priority (like a
             package card), so buying more is pushed lower/less prominent. */
          <div className="rounded-xl bg-accent p-5 text-white">
            <div className="text-[11px] font-semibold uppercase tracking-[0.1em] text-white/60">
              {t('arrival.title')}
            </div>
            <div className="mt-2 font-display text-[19px] leading-tight text-white">{t('arrival.serviceCard')}</div>
            <div className="mt-3 rounded-lg bg-white/10 p-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase tracking-wide text-white/60">
                  {t('arrival.details')}
                </span>
                <button
                  onClick={() => setArrivalOpen(true)}
                  className="text-[12px] font-medium text-white/85 underline underline-offset-2 hover:text-white"
                >
                  {t('arrival.edit')}
                </button>
              </div>
              {data.arrival.details.arrivalDate || data.arrival.details.dropoff ? (
                <div className="mt-1.5 space-y-0.5 text-[13px] text-white/90">
                  {data.arrival.details.arrivalDate && (
                    <div>
                      ✈️ {fmtDate(data.arrival.details.arrivalDate)} {data.arrival.details.arrivalTime}
                      {data.arrival.details.airport ? ` · ${data.arrival.details.airport}` : ''}
                    </div>
                  )}
                  {data.arrival.details.dropoff && <div>🏠 {data.arrival.details.dropoff}</div>}
                </div>
              ) : (
                <div className="mt-1 text-[12.5px] text-white/60">{t('arrival.none')}</div>
              )}
            </div>
          </div>
        ) : (
          /* Nothing active → buy a package right here (prominent, no redirect) */
          <PurchasePanel
            onCheckout={onCheckout}
            buying={buying}
            ownedServices={data.services.map((s) => s.id)}
          />
        )}

        {/* Buy more — small/secondary while there's active work (package or
            airport service); the prominent buy panel only shows when idle. */}
        {(data.package || data.arrival.hasAirportMeet) && (
          <Button asChild variant="outline" size="block">
            <Link href="/services">{t('addServices')}</Link>
          </Button>
        )}

        {/* Extra services (rail) — only alongside a package */}
        {hasPackage && data.services.length > 0 && (
          <div className="rounded-xl border border-line bg-card p-5">
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.1em] text-gray">
              {t('ordersTitle')}
            </div>
            <ul className="flex flex-col gap-3">
              {data.services.map((s) => (
                <li key={s.id} className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between gap-2 text-[13.5px]">
                    <span className="min-w-0 truncate text-ink-2">{ts(`items.${s.id}.name` as any)}</span>
                    <ServiceStatusBadge status={s.taskStatus} />
                  </div>
                  <AttachmentChips files={s.attachments} />
                </li>
              ))}
            </ul>
          </div>
        )}
        </div>

        {/* Block 3 — people & extras (manager, companion, documents, share,
            history): after the path on mobile, the lower-left rail on desktop. */}
        <div className="order-3 flex min-w-0 flex-col gap-5 lg:col-start-1 lg:row-start-2">
        {/* Manager — shown while there's active work; hidden once everything is
            done (the completed banner + order history take over) until a new buy. */}
        {data.state === 'active' && (
        <div className="rounded-xl border border-line bg-card p-5">
          <div className="text-[11px] font-semibold uppercase tracking-[0.1em] text-gray">{t('managerTitle')}</div>
          {manager.assigned ? (
            <>
              <div className="mt-3 flex items-center gap-3">
                <PersonAvatar url={manager.photoUrl} name={manager.name} />
                <div className="min-w-0">
                  <div className="truncate text-[15px] font-semibold text-ink">{manager.name}</div>
                  <div className="text-[12.5px] text-muted">{t('managerRole')}</div>
                </div>
              </div>
              <PersonContact telegram={manager.telegram} phone={manager.phone} />
              <Button variant="dark" size="block" className="mt-4" onClick={() => onChat('manager')}>
                {t('writeChat')}
              </Button>
            </>
          ) : (
            <>
              <div className="mt-3 flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-full bg-sub text-[18px] text-gray-lt">
                  …
                </span>
                <div className="text-[13px] leading-snug text-muted">{t('managerPending')}</div>
              </div>
              <Button variant="outline" size="block" className="mt-4" onClick={() => onChat('manager')}>
                {t('chat.open')}
              </Button>
            </>
          )}
        </div>
        )}

        {/* Runner — shown only while there's active field work left. Once every
            visit is done the companion card disappears (manager stays). */}
        {data.state === 'active' && data.needsRunner && (
        <div className="rounded-xl border border-line bg-card p-5">
          <div className="text-[11px] font-semibold uppercase tracking-[0.1em] text-gray">{t('runnerTitle')}</div>
          {data.runner.assigned ? (
            <>
              <div className="mt-3 flex items-center gap-3">
                <PersonAvatar url={data.runner.photoUrl} name={data.runner.name} />
                <div className="min-w-0">
                  <div className="truncate text-[15px] font-semibold text-ink">{data.runner.name}</div>
                  <div className="text-[12.5px] text-muted">{t('runnerRole')}</div>
                </div>
              </div>
              <PersonContact telegram={data.runner.telegram} phone={data.runner.phone} />
              <Button variant="dark" size="block" className="mt-4" onClick={() => onChat('runner')}>
                {t('writeChat')}
              </Button>
            </>
          ) : (
            <div className="mt-3 flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-full bg-sub text-[18px] text-gray-lt">
                …
              </span>
              <div className="text-[13px] leading-snug text-muted">{t('runnerPending')}</div>
            </div>
          )}
        </div>
        )}

        {/* Documents — only the ones this order actually involves */}
        {docKeys.length > 0 && (
          <div className="rounded-xl border border-line bg-card p-5">
            <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.1em] text-gray">
              {t('documentsTitle')}
            </div>
            <ul className="flex flex-col gap-2.5">
              {docKeys.map((d) => {
                const files = data.documentFiles?.[d] || []
                const ready = !!documents[d] || files.length > 0
                return (
                  <li key={d} className="text-[13.5px]">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2.5 text-ink-2">
                        <span className="h-2 w-2 rounded-full" style={{ background: ready ? 'rgb(var(--accent))' : 'rgb(var(--line))' }} />
                        {t(`documents.${d}`)}
                      </span>
                      <span className={cn('text-[12px]', ready ? 'text-accent' : 'text-gray-lt')}>
                        {ready ? t('docReady') : t('docPending')}
                      </span>
                    </div>
                    {files.length > 0 && <AttachmentChips files={files} />}
                  </li>
                )
              })}
            </ul>
          </div>
        )}

        {/* Share the relocation (read-only public page) — only when there's
            something meaningful to show: an active package, or any service or
            apartment. Hidden on an empty or fully-finished-and-nothing-else cabinet. */}
        {((data.package && !data.packageComplete) ||
          (data.arrival.hasAirportMeet && data.state === 'active') ||
          data.services.length > 0 ||
          data.completedServices.length > 0 ||
          data.housing.length > 0) && (
          <Button variant="ghost" size="block" className="gap-2" onClick={() => setShareOpen(true)}>
            <Share2 size={15} /> {t('share.cta')}
          </Button>
        )}

        {/* Order history — collapsible, tucked in the side rail (out of the main flow) */}
        <OrderHistory items={data.history} />
        </div>

        {/* Block 2 — your relocation path (leads after the map on mobile; the right
            column, spanning both left-rail rows, on desktop). */}
        <section className="order-2 min-w-0 lg:col-start-2 lg:row-start-1 lg:row-span-2">
        {hasPath ? (
          <>
            <h1 className="mt-1 font-display text-[28px] text-ink sm:text-[30px]">{t('heading')}</h1>

            {/* Progress — flush left */}
            <div className="mt-3 flex items-baseline gap-2.5">
              <span className="font-display text-[34px] leading-none text-accent">{percent}%</span>
              <span className="text-[13px] text-muted">{t('progressLabel', { done: doneCount, total })}</span>
            </div>

            <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-track">
              <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${percent}%` }} />
            </div>

            <div className="relative mt-8 pl-8">
              <span className="absolute left-[9px] top-1 h-[calc(100%-1rem)] w-0.5 bg-track" />
              <div className="flex flex-col gap-4">
                {steps.map((step, i) => {
                  const done = step.status === 'done'
                  // onWay/arrived are runner field-visit stages; inProgress is a
                  // non-runner step actively being worked. Any of them = in progress.
                  const active =
                    step.status === 'inProgress' ||
                    step.status === 'onWay' ||
                    step.status === 'arrived'
                  const { title, desc } = label('step', step.key)
                  // The airport-meet step, once an arrival time is set, always stays
                  // expanded and "live": a countdown while the flight is in the future,
                  // then "сейчас" (now) once the meeting time has arrived — it must NOT
                  // collapse when the clock hits 0. It only leaves this state when the
                  // operator marks it done.
                  // Arrival details come from the package OR a standalone airport
                  // service (top-level data.arrival), so the countdown works either way.
                  const arrivalDetails = data.arrival.details
                  const isArrivalStep = step.key === 'airportMeet' && data.arrival.hasAirportMeet && !done
                  const hasArrivalTime = isArrivalStep && !!arrivalDetails.arrivalDate
                  const countdown = isArrivalStep
                    ? arrivalCountdown(arrivalDetails.arrivalDate, arrivalDetails.arrivalTime)
                    : null
                  // Expand a card for every in-progress step (several can run at once)
                  // and for the arrival step once a time is set (countdown → "now").
                  const expanded = active || hasArrivalTime
                  return (
                    <div key={`${step.key}-${i}`} className="relative">
                      <span className="absolute -left-8 top-0.5">
                        {done && (
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent text-[11px] text-white">
                            ✓
                          </span>
                        )}
                        {!done && expanded && (
                          <span className="nd-pulse block h-5 w-5 rounded-full border-2 border-accent bg-card" />
                        )}
                        {!done && !expanded && (
                          <span className="block h-5 w-5 rounded-full border-2 border-line bg-surface" />
                        )}
                      </span>

                      {expanded ? (
                        <div className="rounded-xl border border-accent/25 bg-card p-4">
                          <div className="flex items-center gap-2">
                            <h3 className="font-display text-[18px] text-ink">{title}</h3>
                            <span className="rounded-full bg-accent-bg px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide text-accent">
                              {countdown
                                ? countdown.days > 0
                                  ? t('arrival.inDays', {
                                      days: countdown.days,
                                      hours: countdown.hours,
                                      minutes: countdown.minutes,
                                    })
                                  : t('arrival.inHours', {
                                      hours: countdown.hours,
                                      minutes: countdown.minutes,
                                    })
                                : t('stepBadgeNow')}
                            </span>
                          </div>
                          <p className="mt-1.5 text-[13.5px] leading-relaxed text-muted">{desc}</p>
                          {step.key === 'airportMeet' && <MeetingSignNote />}
                          <div className="mt-3 flex flex-wrap gap-2">
                            <Button variant="dark" size="sm" onClick={() => onChat('manager')}>
                              {t('stepActions.chat')}
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="py-0.5">
                          <h3 className={cn('font-display text-[16px]', done ? 'text-ink' : 'text-gray-lt')}>
                            {title}
                          </h3>
                          {done && <p className="text-[12.5px] text-muted">{desc}</p>}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </>
        ) : data.services.length > 0 ? (
          /* Services-only view — no relocation path */
          <>
            <h1 className="mt-1 font-display text-[28px] text-ink sm:text-[30px]">{t('servicesMainTitle')}</h1>
            <p className="mt-1 text-[14px] text-muted">{t('servicesMainSubtitle')}</p>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              {data.services.map((s) => {
                const { title, desc } = label('service', s.id)
                return (
                  <div key={s.id} className="rounded-xl border border-line bg-card p-4">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-[15px] font-semibold text-ink">{title}</h3>
                      <ServiceStatusBadge status={s.taskStatus} />
                    </div>
                    <p className="mt-1 text-[13px] leading-snug text-muted">{desc}</p>
                    <AttachmentChips files={s.attachments} />
                    <div className="mt-3 flex items-center justify-between border-t border-line pt-3">
                      <span className="font-display text-[18px] text-accent">{fmtGBP(s.amountGBP)}</span>
                      <span className={cn('text-[12px]', s.paid ? 'text-accent' : 'text-terracotta')}>
                        {s.paid ? t('paidBadge') : t('unpaidBadge')}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        ) : (
          /* Everything is done — a calm completed banner, purchase lives in the rail */
          <div className="rounded-2xl bg-accent px-6 py-10 text-center text-white">
            <div className="text-[38px]">🎉</div>
            <h1 className="mt-1 font-display text-[26px] text-white sm:text-[30px]">{t('completedTitle')}</h1>
            <p className="mx-auto mt-2 max-w-[42ch] text-[14.5px] leading-relaxed text-white/80">
              {t('completedText')}
            </p>
          </div>
        )}

        {/* Housing search — pick from the catalog or paste a link */}
        {(data.housingSearch || data.housing.length > 0) && (
          <HousingSection items={data.housing} onRefresh={onRefresh} />
        )}

        {/* Completed services history */}
        {completedServices.length > 0 && (
          <div className="mt-8">
            <div className="eyebrow mb-3">{t('completedServicesTitle')}</div>
            <div className="grid gap-3 sm:grid-cols-2">
              {completedServices.map((s) => {
                const { title } = label('service', s.id)
                return (
                  <div
                    key={s.id}
                    className="rounded-xl border border-line bg-card px-4 py-3.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="flex min-w-0 items-center gap-2.5 text-[14px] text-ink">
                        <CheckCircle2 size={17} className="shrink-0 text-accent" />
                        <span className="truncate">{title}</span>
                      </span>
                      <span className="shrink-0 text-[12px] font-medium text-accent">{t('serviceDone')}</span>
                    </div>
                    <AttachmentChips files={s.attachments} />
                  </div>
                )
              })}
            </div>
          </div>
        )}

      </section>
      </div>

      {arrivalOpen && (data.package || data.arrival.hasAirportMeet) && (
        <ArrivalEditModal
          details={data.package?.details || data.arrival.details || {}}
          onClose={() => setArrivalOpen(false)}
          onSaved={() => {
            setArrivalOpen(false)
            onRefresh()
            toast(t('arrival.saved'))
          }}
        />
      )}

      {shareOpen && <ShareModal onClose={() => setShareOpen(false)} />}
    </>
  )
}

/* ---------- Share with family (public read-only link) ---------- */
function ShareModal({ onClose }: { onClose: () => void }) {
  const t = useTranslations('Profile')
  const locale = useLocale()
  const { toast } = useToast()
  const [url, setUrl] = useState<string | null>(null)

  useEffect(() => {
    api.me
      .shareLink()
      .then(({ token }) => setUrl(`${window.location.origin}/${locale}/share/${token}`))
      .catch(() => {})
  }, [locale])

  async function copy() {
    if (!url) return
    try {
      await navigator.clipboard.writeText(url)
      toast(t('share.copied'))
    } catch {}
  }
  async function nativeShare() {
    if (!url) return
    try {
      await navigator.share({ url, title: 'Nothard', text: t('share.title') })
    } catch {}
  }
  const canNativeShare = typeof navigator !== 'undefined' && !!(navigator as any).share

  return (
    <div
      className="fixed inset-0 z-[99999] flex items-end justify-center bg-black/50 p-0 backdrop-blur-[2px] sm:items-center sm:p-6"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-[420px] overflow-hidden rounded-t-2xl bg-surface sm:rounded-2xl"
      >
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <h2 className="font-display text-[18px] text-ink">{t('share.title')}</h2>
          <button onClick={onClose} className="text-gray hover:text-ink" aria-label="close">
            <X size={18} />
          </button>
        </div>
        <div className="flex flex-col gap-4 p-6">
          <p className="-mt-1 text-[13.5px] leading-relaxed text-muted">{t('share.subtitle')}</p>
          <div className="flex items-center gap-2 rounded-lg border border-line bg-card px-3 py-2.5">
            <span className="min-w-0 flex-1 truncate text-[13px] text-ink-2">{url || '…'}</span>
          </div>
          <div className="flex gap-2">
            <Button variant="solid" size="block" disabled={!url} onClick={copy}>
              {t('share.copy')}
            </Button>
            {canNativeShare && (
              <Button variant="outline" size="block" disabled={!url} onClick={nativeShare}>
                {t('share.shareNative')}
              </Button>
            )}
          </div>
          {url && (
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-1.5 text-center text-[13px] font-medium text-accent hover:underline"
            >
              {t('share.open')} <ExternalLink size={13} className="shrink-0" />
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

/* ---------- Arrival edit ---------- */
function ArrivalEditModal({
  details,
  onClose,
  onSaved,
}: {
  details: Record<string, string>
  onClose: () => void
  onSaved: () => void
}) {
  const t = useTranslations('Profile')
  const [arrivalDate, setArrivalDate] = useState(details.arrivalDate || '')
  const [arrivalTime, setArrivalTime] = useState(details.arrivalTime || '')
  const [airport, setAirport] = useState(details.airport || '')
  const [flight, setFlight] = useState(details.flight || '')
  const [dropoff, setDropoff] = useState(details.dropoff || '')
  const [dropoffCoords, setDropoffCoords] = useState<{ lat: number; lng: number } | null>(null)
  const [busy, setBusy] = useState(false)

  return (
    <div className="fixed inset-0 z-[99999] flex items-end justify-center bg-black/50 p-0 backdrop-blur-[2px] sm:items-center sm:p-6">
      <div className="max-h-[92vh] w-full max-w-[420px] overflow-y-auto rounded-t-2xl bg-surface sm:rounded-2xl">
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <h2 className="font-display text-[18px] text-ink">{t('arrival.editTitle')}</h2>
          <button onClick={onClose} className="text-gray hover:text-ink" aria-label="close">
            <X size={18} />
          </button>
        </div>
        <div className="flex flex-col gap-4 p-6">
          <label className="block">
            <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{t('intake.date')}</span>
            <DateTimeInput type="date" value={arrivalDate} onChange={setArrivalDate} placeholder={t('intake.datePick')} />
          </label>
          <label className="block">
            <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{t('intake.time')}</span>
            <DateTimeInput type="time" value={arrivalTime} onChange={setArrivalTime} placeholder={t('intake.timePick')} />
          </label>
          <PickOrType
            label={t('intake.airport')}
            options={LONDON_AIRPORT_TERMINALS}
            value={airport}
            onChange={setAirport}
            pickLabel={t('intake.airportPickList')}
            otherLabel={t('intake.other')}
            placeholder={t('intake.airportOther')}
          />
          <PickOrType
            label={t('intake.flight')}
            options={LONDON_FLIGHTS}
            value={flight}
            onChange={setFlight}
            pickLabel={t('intake.flightPickList')}
            otherLabel={t('intake.other')}
            placeholder={t('intake.flightOther')}
          />
          <label className="block">
            <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{t('intake.dropoff')}</span>
            <AddressField
              search={(q) => api.me.geocode(q).then((r) => r.results)}
              value={dropoff}
              placeholder={t('intake.dropoffPlaceholder')}
              onPick={(label, coords) => {
                setDropoff(label)
                setDropoffCoords(coords)
              }}
            />
          </label>
          <Button
            variant="solid"
            size="block"
            disabled={busy}
            onClick={async () => {
              setBusy(true)
              try {
                await api.me.updateArrival({
                  arrivalDate, arrivalTime, airport, flight: flight.trim(),
                  dropoff: dropoff.trim(),
                  ...(dropoffCoords
                    ? { dropoffLat: String(dropoffCoords.lat), dropoffLng: String(dropoffCoords.lng) }
                    : {}),
                })
                onSaved()
              } catch {
                setBusy(false)
              }
            }}
          >
            {t('settings.save')}
          </Button>
        </div>
      </div>
    </div>
  )
}

