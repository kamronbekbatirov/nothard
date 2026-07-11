'use client'

import { useEffect, useState } from 'react'
import { useTranslations, useLocale } from 'next-intl'
import { CheckCircle2, ChevronDown, ExternalLink, History, Home, Paperclip, Plus, Share2, Star, Trash2, X } from 'lucide-react'
import { Link, useRouter } from '@/i18n/navigation'
import { AppTopbar } from '@/app/components/app-topbar'
import { Button } from '@/app/components/button'
import { Logo } from '@/app/components/logo'
import { DateTimeInput, Input, PickOrType } from '@/app/components/field'
import { SettingsModal } from '@/app/components/settings-modal'
import { ChatModal } from '@/app/components/chat'
import { useToast } from '@/app/components/toast'
import { useAuth } from '@/app/lib/use-auth'
import { useTelegramChrome } from '@/app/lib/telegram'
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
} from '@/app/lib/api'
import {
  PACKAGES,
  AIRPORT_PACKAGES,
  LONDON_AIRPORT_TERMINALS,
  LONDON_FLIGHTS,
  VIEWING_PRICE,
  fmtGBP,
  fmtUSD,
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
  const [intakePkg, setIntakePkg] = useState<string | null>(null)

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

  // Packages with an airport pickup ask arrival details first; others buy directly.
  function buyPackage(id: string) {
    if (AIRPORT_PACKAGES.has(id)) {
      setIntakePkg(id)
    } else {
      void confirmPackage(id, {})
    }
  }

  async function confirmPackage(id: string, details: Record<string, string>) {
    setBuying(true)
    try {
      const d = await api.me.checkout([{ type: 'package', id }], details)
      setData(d)
      setIntakePkg(null)
      toast(t('purchasedToast'))
    } catch {
    } finally {
      setBuying(false)
    }
  }

  function logout() {
    void api.logout() // revoke this device's session server-side (best-effort)
    clearTokens()
    window.location.href = '/login'
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
        onLogout={inTelegram ? undefined : logout}
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
        onSettings={() => setSettingsOpen(true)}
        onLogout={inTelegram ? undefined : logout}
      />

      <main className="mx-auto max-w-[1240px] px-5 py-8 sm:px-8">
        {data.hasOrders ? (
          <PopulatedCabinet
            data={data}
            onChat={(who = 'manager') => setChatWith(who)}
            onBuy={buyPackage}
            buying={buying}
            onRefresh={refresh}
          />
        ) : (
          <EmptyCabinet onBuy={buyPackage} buying={buying} />
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

      {intakePkg && (
        <PackageIntakeModal
          pkgId={intakePkg}
          busy={buying}
          onClose={() => setIntakePkg(null)}
          onConfirm={(details) => confirmPackage(intakePkg, details)}
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
function ConsentGate({ onAccept, onLogout }: { onAccept: () => void; onLogout?: () => void }) {
  const t = useTranslations('Consent')
  const [busy, setBusy] = useState(false)
  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-5 py-10">
      <div className="w-full max-w-[420px]">
        <div className="overflow-hidden rounded-[22px] border border-line bg-card shadow-card">
          {/* Hero — wordmark logo + welcome */}
          <div className="bg-accent-bg px-7 pb-7 pt-9 text-center">
            <span className="mx-auto inline-flex items-center rounded-full bg-card px-4 py-2 shadow-sm">
              <Logo asLink={false} size={22} />
            </span>
            <h1 className="mt-4 font-display text-[26px] text-ink">{t('title')}</h1>
            <p className="mx-auto mt-1.5 max-w-[34ch] text-[14px] leading-relaxed text-muted">
              {t('subtitle')}
            </p>
          </div>

          {/* What we do */}
          <div className="px-7 py-6">
            <ul className="flex flex-col gap-3.5">
              {[0, 1, 2].map((i) => (
                <li key={i} className="flex items-start gap-3">
                  <CheckCircle2 size={19} className="mt-px shrink-0 text-accent" />
                  <span className="text-[14px] leading-snug text-ink-2">{t(`points.${i}` as any)}</span>
                </li>
              ))}
            </ul>

            {/* Legal — full-width rows so long titles don't overflow */}
            <div className="mt-6 flex flex-col gap-2">
              <Link
                href="/privacy"
                className="flex items-center justify-between gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 text-[13.5px] font-medium text-accent transition-colors hover:border-accent/40"
              >
                {t('privacy')} <span aria-hidden>→</span>
              </Link>
              <Link
                href="/terms"
                className="flex items-center justify-between gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 text-[13.5px] font-medium text-accent transition-colors hover:border-accent/40"
              >
                {t('terms')} <span aria-hidden>→</span>
              </Link>
            </div>

            <Button
              variant="solid"
              size="block"
              className="mt-5"
              disabled={busy}
              onClick={async () => {
                setBusy(true)
                await onAccept()
              }}
            >
              {t('accept')}
            </Button>
            <p className="mx-auto mt-3 max-w-[38ch] text-center text-[12px] leading-relaxed text-gray">
              {t('agree')}
            </p>
            {onLogout && (
              <button
                onClick={onLogout}
                className="mx-auto mt-3 block text-[13px] text-gray hover:text-ink"
              >
                {t('decline')}
              </button>
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
  busy,
  onClose,
  onConfirm,
}: {
  pkgId: string
  busy: boolean
  onClose: () => void
  onConfirm: (details: Record<string, string>) => void
}) {
  const t = useTranslations('Profile')
  const tp = useTranslations('Packages')
  const [arrivalDate, setArrivalDate] = useState('')
  const [arrivalTime, setArrivalTime] = useState('')
  const [airport, setAirport] = useState<string>('')
  const [flight, setFlight] = useState('')

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
            {t('intake.subtitle', { pkg: tp(`${pkgId}.name` as any) })}
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
function PurchasePanel({ onBuy, buying }: { onBuy: (id: string) => void; buying: boolean }) {
  const t = useTranslations('Profile')
  const tp = useTranslations('Packages')

  return (
    <div className="rounded-xl border border-line bg-card p-5">
      <div className="eyebrow mb-3">{t('buyPackageTitle')}</div>
      <div className="flex flex-col gap-2">
        {PACKAGES.map((pkg) => (
          <button
            key={pkg.id}
            onClick={() => onBuy(pkg.id)}
            disabled={buying}
            className="nd-chip flex items-center justify-between rounded-lg border border-line bg-surface px-3.5 py-2.5 text-left hover:border-accent disabled:opacity-50"
          >
            <span className="min-w-0">
              <span className="block truncate text-[13.5px] font-semibold text-ink">
                {tp(`${pkg.id}.name`)}
              </span>
              {pkg.popular && <span className="text-[11px] font-medium text-accent">★ {t('popularHint')}</span>}
            </span>
            <span className="ml-2 shrink-0 font-display text-[16px] text-accent">{fmtGBP(pkg.gbp)}</span>
          </button>
        ))}
      </div>

      <div className="mt-4 border-t border-line pt-4">
        <div className="eyebrow mb-2">{t('buyServiceTitle')}</div>
        <p className="mb-3 text-[12.5px] leading-snug text-muted">{t('buyServiceHint')}</p>
        <Button asChild variant="outline" size="block">
          <Link href="/services">{t('emptyBrowseServices')}</Link>
        </Button>
      </div>
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
  if (!telegram && !phone) return null
  return (
    <div className="mt-3 flex flex-col gap-1.5 text-[13px]">
      {telegram && (
        <a
          href={`https://t.me/${telegram}`}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 font-medium text-accent hover:underline"
        >
          @{telegram}
        </a>
      )}
      {phone && (
        <a href={`tel:${phone}`} className="inline-flex items-center gap-1.5 text-ink-2 hover:text-accent">
          {phone}
        </a>
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
  onRequestViewing,
}: {
  h: HousingItem
  onRemove: (id: number) => void
  onRequestViewing: (id: number) => Promise<void>
}) {
  const t = useTranslations('Profile')
  const [busy, setBusy] = useState(false)
  // Once a viewing is scheduled (or already happened) the request CTA is moot.
  const canRequestViewing =
    !h.viewingRequested && ['new', 'reached', 'busy'].includes(h.status)
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

        {h.status === 'viewing' && h.viewingAt && (
          <div className="mt-2.5 rounded-lg bg-sky-500/10 px-3 py-2 text-[13px] font-medium text-sky-700">
            📅 {t('housing.viewingAt', { when: h.viewingAt.replace('T', ' ') })}
          </div>
        )}
        {h.note && <div className="mt-2 text-[12.5px] leading-snug text-ink-2">{h.note}</div>}

        {/* Accompanied viewing — £30 per property, requested from the shortlist. */}
        {canRequestViewing ? (
          <Button
            variant="outline"
            size="sm"
            className="mt-3 w-full"
            disabled={busy}
            onClick={async () => {
              setBusy(true)
              try {
                await onRequestViewing(h.id)
              } finally {
                setBusy(false)
              }
            }}
          >
            {t('housing.requestViewing', { price: VIEWING_PRICE })}
          </Button>
        ) : h.viewingRequested && h.status !== 'viewing' ? (
          <div className="mt-3 rounded-lg bg-accent-bg px-3 py-2 text-[12.5px] font-medium text-accent">
            {t('housing.viewingRequested')}
          </div>
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
  async function requestViewing(id: number) {
    try {
      await api.me.requestViewing(id)
      onRefresh()
      toast(t('housing.viewingRequested'))
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
            <HousingCard key={h.id} h={h} onRemove={remove} onRequestViewing={requestViewing} />
          ))}
        </div>
      )}
    </div>
  )
}

/* ---------- Empty (first-time) ---------- */
function PackageGrid({ onBuy, buying }: { onBuy: (id: string) => void; buying: boolean }) {
  const t = useTranslations('Profile')
  const tp = useTranslations('Packages')
  const tl = useTranslations('Landing')
  return (
    <div className="grid items-start gap-4 md:grid-cols-3">
      {PACKAGES.map((pkg) => {
        const popular = !!pkg.popular
        const features = Array.from({ length: pkg.featureCount }, (_, i) => tp(`${pkg.id}.features.${i}`))
        return (
          <div
            key={pkg.id}
            className={cn(
              'relative rounded-xl border p-6',
              popular ? 'border-accent bg-accent text-[#eef2ee]' : 'border-line bg-card'
            )}
          >
            {popular && (
              <span className="absolute -top-3 left-6 rounded-full bg-surface px-[11px] py-1 text-[10.5px] font-bold uppercase tracking-[0.08em] text-accent">
                {tl('popular')}
              </span>
            )}
            <div className={cn('font-display text-[22px]', popular ? 'text-white' : 'text-ink')}>
              {tp(`${pkg.id}.name`)}
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className={cn('font-display text-[34px]', popular ? 'text-white' : 'text-ink')}>
                {fmtGBP(pkg.gbp)}
              </span>
              <span className={cn('text-[13px]', popular ? 'opacity-75' : 'text-gray')}>/ {fmtUSD(pkg.gbp)}</span>
            </div>
            <div className={cn('mb-5 mt-0.5 text-[12.5px]', popular ? 'opacity-75' : 'text-gray')}>
              {fmtUZS(pkg.gbp)}
            </div>
            <div className="mb-5 flex flex-col gap-2.5">
              {features.map((f, i) => (
                <div key={i} className={cn('flex gap-2 text-[13px]', popular ? 'opacity-95' : 'text-ink-2')}>
                  <span className={cn('font-bold', popular ? 'text-white' : 'text-accent')}>✓</span>
                  {f}
                </div>
              ))}
            </div>
            <Button
              variant={popular ? 'white' : 'outline'}
              size="block"
              disabled={buying}
              className={cn(popular && 'font-bold text-accent')}
              onClick={() => onBuy(pkg.id)}
            >
              {t('emptyChoosePackage')}
            </Button>
          </div>
        )
      })}
    </div>
  )
}

function EmptyCabinet({ onBuy, buying }: { onBuy: (id: string) => void; buying: boolean }) {
  const t = useTranslations('Profile')

  return (
    <div className="mx-auto max-w-[1000px]">
      <div className="text-center">
        <h1 className="font-display text-[30px] text-ink sm:text-[36px]">{t('emptyTitle')}</h1>
        <p className="mx-auto mt-3 max-w-[52ch] text-[15px] leading-relaxed text-muted">{t('emptyText')}</p>
      </div>

      <div className="mt-9">
        <PackageGrid onBuy={onBuy} buying={buying} />
      </div>

      <div className="mt-8 text-center">
        <Link href="/services" className="text-[14px] font-semibold text-accent hover:underline">
          {t('emptyBrowseServices')} →
        </Link>
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
  // Only surface the history once the client has at least one COMPLETED order —
  // there's nothing to look back on before that. Once shown, it stays.
  if (!items || !items.some((it) => it.status === 'done')) return null

  const nameOf = (it: OrderHistoryItem) =>
    it.type === 'package'
      ? tp(`${it.id}.name` as any)
      : it.type === 'viewing'
        ? t('history.viewing')
        : ts(`items.${it.id}.name` as any)

  return (
    <div className="mt-8">
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
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-[14.5px] font-semibold text-ink">{nameOf(it)}</span>
                      <span
                        className={cn(
                          'shrink-0 rounded-full px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide',
                          done ? 'bg-accent-bg text-accent' : 'bg-sub text-muted'
                        )}
                      >
                        {done ? t('history.done') : t('history.active')}
                      </span>
                    </div>
                    <div className="mt-0.5 text-[12px] text-muted">
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
  onChat,
  onBuy,
  buying,
  onRefresh,
}: {
  data: DashboardData
  onChat: (who?: 'manager' | 'runner') => void
  onBuy: (id: string) => void
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
    <div className="grid gap-8 lg:grid-cols-[296px_1fr]">
      {/* Left rail */}
      <aside className="flex flex-col gap-5">
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
        ) : (
          /* No active package → buy a new one right here (no redirect) */
          <PurchasePanel onBuy={onBuy} buying={buying} />
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
                  <div className="text-[12.5px] text-muted">{t('managerHours')}</div>
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

        {data.package && (
          <Button asChild variant="outline" size="block">
            <Link href="/services">{t('addServices')}</Link>
          </Button>
        )}

        {/* Share the relocation with family (read-only public page) */}
        {data.hasOrders && (
          <Button variant="ghost" size="block" className="gap-2" onClick={() => setShareOpen(true)}>
            <Share2 size={15} /> {t('share.cta')}
          </Button>
        )}
      </aside>

      {/* Main */}
      <section>
        <p className="text-[14px] text-muted">{t('greeting', { name: data.user.name })}</p>

        {hasPackage ? (
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
                  const isArrivalStep =
                    step.key === 'airportMeet' && !!data.package?.hasAirportMeet && !done
                  const hasArrivalTime = isArrivalStep && !!data.package?.details?.arrivalDate
                  const countdown = isArrivalStep
                    ? arrivalCountdown(data.package?.details?.arrivalDate, data.package?.details?.arrivalTime)
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

        {/* Order history — everything bought, its status and completion times */}
        <OrderHistory items={data.history} />
      </section>

      {arrivalOpen && data.package && (
        <ArrivalEditModal
          details={data.package.details || {}}
          onClose={() => setArrivalOpen(false)}
          onSaved={() => {
            setArrivalOpen(false)
            onRefresh()
            toast(t('arrival.saved'))
          }}
        />
      )}

      {shareOpen && <ShareModal onClose={() => setShareOpen(false)} />}
    </div>
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
              className="text-center text-[13px] font-medium text-accent hover:underline"
            >
              {t('share.open')} →
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
          <Button
            variant="solid"
            size="block"
            disabled={busy}
            onClick={async () => {
              setBusy(true)
              try {
                await api.me.updateArrival({ arrivalDate, arrivalTime, airport, flight: flight.trim() })
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

