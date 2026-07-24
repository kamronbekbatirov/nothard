'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { ChevronDown, MapPin, MessageSquare, Pencil, Phone, Smartphone } from 'lucide-react'
import { AppTopbar } from '@/app/components/app-topbar'
import { Button } from '@/app/components/button'
import { Avatar } from '@/app/components/avatar'
import { ChatModal } from '@/app/components/chat'
import { Input } from '@/app/components/field'
import { LangSwitcher } from '@/app/components/lang-switcher'
import { AddressField } from '@/app/components/address-field'
import { TripCard } from '@/app/components/trip-card'
import { ModeSelector } from '@/app/components/travel-mode'
import { useToast } from '@/app/components/toast'
import { useRequireRole } from '@/app/lib/use-require-role'
import { useTaskLabel } from '@/app/lib/task-label'
import {
  api,
  clearTokens,
  type RunnerDashboard,
  type RunnerClientRow,
  type RunnerVisitRow,
  type TripLive,
  type TrackConfig,
  type GeoResult,
  type TravelMode,
} from '@/app/lib/api'
import { fmtGBP } from '@/app/lib/data'
import { cn } from '@/app/lib/utils'

export default function RunnerPage() {
  const t = useTranslations('Runner')
  const { toast } = useToast()
  const { ready, user } = useRequireRole(['runner'])
  const [data, setData] = useState<RunnerDashboard | null>(null)
  const [loaded, setLoaded] = useState(false)
  const [chatClient, setChatClient] = useState<RunnerClientRow | null>(null)

  const load = () => api.runner.dashboard().then(setData).catch(() => {}).finally(() => setLoaded(true))
  useEffect(() => {
    if (!ready) return
    load()
    const id = window.setInterval(load, 8000)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready])

  async function advance(taskId: number) {
    try {
      const r = await api.runner.advance(taskId)
      if (r.stage === 'done') toast(t('actions.complete'))
      load()
    } catch {}
  }

  // Active work = clients with at least one pending visit (only their pending
  // visits shown). Completed visits move to the History log below.
  const activeClients = useMemo(
    () =>
      (data?.clients ?? [])
        .map((c) => ({ ...c, tasks: c.tasks.filter((v) => v.stage !== 'done') }))
        .filter((c) => c.tasks.length > 0),
    [data]
  )
  const history = useMemo(() => {
    const rows: (RunnerVisitRow & { client: string })[] = []
    for (const c of data?.clients ?? []) {
      for (const v of c.tasks) if (v.stage === 'done') rows.push({ ...v, client: c.name })
    }
    return rows.sort((a, b) => (b.completedAt || '').localeCompare(a.completedAt || ''))
  }, [data])

  if (!ready) return <PanelLoading />

  return (
    <div className="min-h-screen bg-paper">
      <AppTopbar
        badge={t('badge')}
        name={data?.name || user?.name}
        avatarUrl={data?.photoUrl ?? user?.photo_url}
        onLogout={() => {
          clearTokens()
          window.location.href = '/login'
        }}
      />

      <main className="mx-auto max-w-[680px] px-4 py-6 sm:px-6">
        <div className="flex items-center justify-between gap-3">
          <p className="min-w-0 truncate text-[14px] text-muted">
            {t('greeting', { name: data?.name || user?.name || '' })}
          </p>
          {/* The topbar hides the language switcher on mobile; the runner panel is
              phone-first, so surface it here too. */}
          <div className="shrink-0">
            <LangSwitcher />
          </div>
        </div>

        {/* Stats */}
        <div className="mt-3 grid grid-cols-4 gap-2.5">
          <Stat value={data?.stats.clients} label={t('statClients')} />
          <Stat value={data?.stats.visitsActive} label={t('statActive')} tone="accent" />
          <Stat value={data?.stats.visitsDone} label={t('statDone')} />
          <Stat value={data?.stats.visitsTotal} label={t('statVisits')} />
        </div>

        {/* Payout */}
        {data && (
          <div className="mt-4 rounded-2xl border border-line bg-card p-5">
            <div className="eyebrow mb-3">{t('payoutTitle')}</div>
            <div className="flex items-end justify-between">
              <div>
                <div className="font-display text-[32px] leading-none text-accent">{fmtGBP(data.payout.owedGBP)}</div>
                <div className="mt-1 text-[12.5px] text-muted">{t('owed')}</div>
              </div>
              <div className="text-right text-[12.5px] text-muted">
                <div>
                  {t('paid')}: <span className="font-medium text-ink">{fmtGBP(data.payout.paidGBP)}</span>
                </div>
                <div className="mt-0.5">
                  {fmtGBP(data.payout.visitFee)} · {t('perVisit')}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Live tracking — phone setup + start/stop a trip */}
        <TrackingSection clients={(data?.clients ?? []).map((c) => ({ id: c.id, name: c.name }))} />

        {/* Active work — clients with pending visits */}
        <div className="mt-7">
          <div className="eyebrow mb-3">{t('clientsTitle')}</div>
          {loaded && data && data.clients.length === 0 && (
            <div className="rounded-xl border border-dashed border-line bg-surface p-8 text-center text-[14px] text-muted">
              {t('noClients')}
            </div>
          )}
          {loaded && data && data.clients.length > 0 && activeClients.length === 0 && (
            <div className="rounded-xl border border-dashed border-line bg-surface p-8 text-center text-[14px] text-muted">
              {t('allDone')}
            </div>
          )}
          <div className="flex flex-col gap-4">
            {activeClients.map((c) => (
              <ClientCard
                key={c.id}
                c={c}
                onAdvance={advance}
                onChat={() => setChatClient(c)}
              />
            ))}
          </div>
        </div>

        {/* History — completed visits (the runner's earnings log) */}
        {history.length > 0 && <VisitHistory rows={history} fee={data?.payout.visitFee ?? 0} />}
      </main>

      {chatClient && (
        <ChatModal
          title={chatClient.name}
          subtitle={t('clientChatSubtitle')}
          peerName={chatClient.name}
          peerAvatarUrl={chatClient.photoUrl}
          placeholder={t('chatPlaceholder')}
          emptyText={t('chatEmpty')}
          meSide="runner"
          fetchMessages={() => api.runner.messages(chatClient.id).then((r) => r.messages)}
          sendMessage={(body) => api.runner.sendMessage(chatClient.id, body)}
          onClose={() => setChatClient(null)}
        />
      )}
    </div>
  )
}

function Stat({ value, label, tone }: { value?: number; label: string; tone?: 'accent' }) {
  return (
    <div className="rounded-xl border border-line bg-card px-2 py-3 text-center">
      <div className={cn('font-display text-[24px] leading-none', tone === 'accent' ? 'text-accent' : 'text-ink')}>
        {value ?? '—'}
      </div>
      <div className="mt-1 text-[11px] leading-tight text-muted">{label}</div>
    </div>
  )
}

function ClientCard({
  c,
  onAdvance,
  onChat,
}: {
  c: RunnerClientRow
  onAdvance: (taskId: number) => void
  onChat: () => void
}) {
  const t = useTranslations('Runner')
  const tp = useTranslations('Packages')
  const active = useMemo(() => c.tasks.filter((v) => v.stage !== 'done'), [c.tasks])
  const done = c.tasks.length - active.length

  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-card">
      {/* Client header */}
      <div className="flex items-center gap-3 border-b border-line p-4">
        <Avatar url={c.photoUrl} name={c.name} size={44} />
        <div className="min-w-0 flex-1">
          <div className="truncate text-[15.5px] font-semibold text-ink">{c.name}</div>
          <div className="text-[12.5px] text-muted">
            {c.package ? tp(`${c.package}.name` as any) : t('pkgLabel')}
            {c.tasks.length > 0 && ` · ${done}/${c.tasks.length} ${t('visitsWord')}`}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {c.phone && (
            <a
              href={`tel:${c.phone}`}
              aria-label={t('call')}
              className="flex h-9 w-9 items-center justify-center rounded-full border border-line text-ink-2 hover:text-accent"
            >
              <Phone size={16} />
            </a>
          )}
          <button
            onClick={onChat}
            aria-label={t('writeChat')}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-inverse text-inverse-fg"
          >
            <MessageSquare size={16} />
          </button>
        </div>
      </div>

      {/* Visits */}
      <div className="flex flex-col divide-y divide-line">
        {c.tasks.length === 0 && <div className="p-4 text-[13px] text-muted">{t('noVisits')}</div>}
        {c.tasks.map((v) => (
          <VisitRow key={v.id} v={v} onAdvance={() => onAdvance(v.id)} />
        ))}
      </div>
    </div>
  )
}

function VisitRow({ v, onAdvance }: { v: RunnerVisitRow; onAdvance: () => void }) {
  const t = useTranslations('Runner')
  const label = useTaskLabel()
  const title = label(v.kind, v.key).title
  const done = v.stage === 'done'
  const stageBadge =
    v.stage === 'onWay' ? t('status.onWay') : v.stage === 'arrived' ? t('status.arrived') : null
  const actionLabel =
    v.stage === 'todo' || v.stage === 'inProgress'
      ? t('actions.onWay')
      : v.stage === 'onWay'
        ? t('actions.arrived')
        : t('actions.complete')

  return (
    <div className={cn('p-4', done && 'opacity-70')}>
      <div className="flex items-start gap-3">
        <span className="mt-0.5">
          {done ? (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent text-[11px] text-white">✓</span>
          ) : v.stage === 'todo' ? (
            <span className="block h-5 w-5 rounded-full border-2 border-line bg-surface" />
          ) : (
            <span className="nd-pulse block h-5 w-5 rounded-full border-2 border-accent bg-card" />
          )}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-[14.5px] font-medium text-ink">{title}</span>
            {stageBadge && (
              <span className="rounded-full bg-accent-bg px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide text-accent">
                {stageBadge}
              </span>
            )}
          </div>
          <div className="mt-0.5 text-[12.5px] text-muted">
            {v.time ? `${t('scheduledFor')}: ${v.time.replace('T', ' ')}` : t('notScheduled')}
            {v.addr ? ` · ${v.addr}` : ''}
          </div>

          {!done && (
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="solid" size="sm" onClick={onAdvance}>
                {actionLabel}
              </Button>
              {v.addr && (
                <Button asChild variant="outline" size="sm" className="gap-1.5">
                  <a href={`https://maps.google.com/?q=${encodeURIComponent(v.addr)}`} target="_blank" rel="noreferrer">
                    <MapPin size={14} /> {t('actions.route')}
                  </a>
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function VisitHistory({ rows, fee }: { rows: (RunnerVisitRow & { client: string })[]; fee: number }) {
  const t = useTranslations('Runner')
  const label = useTaskLabel()
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-8">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-2 rounded-xl border border-line bg-card px-4 py-3.5 text-left"
      >
        <span className="text-[14.5px] font-semibold text-ink">{t('historyTitle', { count: rows.length })}</span>
        <span className="text-[12.5px] text-muted">{open ? t('hide') : t('show')}</span>
      </button>
      {open && (
        <div className="mt-3 flex flex-col gap-2">
          {rows.map((v) => (
            <div key={v.id} className="flex items-center justify-between gap-3 rounded-xl border border-line bg-card px-4 py-3">
              <div className="min-w-0">
                <div className="truncate text-[13.5px] font-medium text-ink">{label(v.kind, v.key).title}</div>
                <div className="text-[12px] text-muted">
                  {v.client}
                  {v.completedAt ? ` · ${fmtDateTime(v.completedAt)}` : ''}
                </div>
              </div>
              <span className="shrink-0 text-[13px] font-semibold text-accent">+{fmtGBP(fee)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function fmtDateTime(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleDateString(undefined, { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function PanelLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-paper text-[15px] text-muted">…</div>
  )
}

/* ---------- Live tracking: phone setup + trip control ---------- */
function CopyRow({
  label,
  value,
  onCopy,
  copyLabel,
}: {
  label: string
  value: string
  onCopy: () => void
  copyLabel: string
}) {
  return (
    <div>
      <div className="mb-1 text-[11.5px] font-medium uppercase tracking-wide text-gray">{label}</div>
      <div className="flex items-stretch gap-2">
        <code className="min-w-0 flex-1 truncate rounded-lg border border-line bg-surface px-3 py-2 text-[12.5px] text-ink">
          {value || '—'}
        </code>
        <Button variant="outline" size="sm" onClick={onCopy} disabled={!value}>
          {copyLabel}
        </Button>
      </div>
    </div>
  )
}

function TrackingSection({ clients }: { clients: { id: number; name: string }[] }) {
  const t = useTranslations('Tracking')
  const { toast } = useToast()
  const [cfg, setCfg] = useState<TrackConfig | null>(null)
  const [trip, setTrip] = useState<(TripLive & { client: { id: number; name: string } | null }) | null>(null)
  const [clientId, setClientId] = useState('')
  const [dest, setDest] = useState('')
  // Exact coords when an address was picked from the suggestions (else null →
  // the backend geocodes the free text as a fallback).
  const [destCoords, setDestCoords] = useState<{ lat: number; lng: number } | null>(null)
  const [origin, setOrigin] = useState('')
  const [mode, setMode] = useState<TravelMode>('car')
  const [busy, setBusy] = useState(false)
  const [copied, setCopied] = useState('')
  // Mid-trip destination change (the route changed on the way).
  const [editDest, setEditDest] = useState(false)
  const [newDest, setNewDest] = useState('')
  const [newDestCoords, setNewDestCoords] = useState<{ lat: number; lng: number } | null>(null)
  const [savingDest, setSavingDest] = useState(false)
  // Phone-setup card is collapsible and remembers "done" per device, so it
  // isn't a wall of instructions every time.
  const [setupOpen, setSetupOpen] = useState(true)
  useEffect(() => {
    setSetupOpen(localStorage.getItem('nh_track_setup_done') !== '1')
  }, [])

  const loadTrip = () => api.runner.trip().then((r) => setTrip(r.trip)).catch(() => {})
  useEffect(() => {
    api.runner.trackConfig().then(setCfg).catch(() => {})
    loadTrip()
    const id = window.setInterval(loadTrip, 8000)
    return () => clearInterval(id)
  }, [])

  async function copy(text: string, which: string) {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(which)
      toast(t('copied'))
      setTimeout(() => setCopied(''), 1500)
    } catch {}
  }
  async function regen() {
    if (!window.confirm(t('regenConfirm'))) return
    try {
      const r = await api.runner.regenToken()
      setCfg((c) => (c ? { ...c, deviceId: r.deviceId } : c))
    } catch {}
  }
  async function start() {
    if (!clientId) return
    if (!dest.trim()) {
      toast(t('needDest'))
      return
    }
    setBusy(true)
    try {
      const r = await api.runner.startTrip({
        client_id: Number(clientId),
        dest_label: dest.trim(),
        dest_lat: destCoords?.lat,
        dest_lng: destCoords?.lng,
        origin_label: origin.trim() || undefined,
        mode,
      })
      if (!r.geocoded) toast(t('geocodeWarn'))
      setDest('')
      setDestCoords(null)
      setOrigin('')
      loadTrip()
    } catch {
    } finally {
      setBusy(false)
    }
  }
  async function switchMode(m: TravelMode) {
    if (!trip) return
    setTrip({ ...trip, mode: m }) // optimistic
    try {
      const r = await api.runner.setMode(trip.id, m)
      setTrip((cur) => (cur ? { ...r.trip, client: cur.client } : cur))
    } catch {
      loadTrip()
    }
  }
  async function changeDestination() {
    if (!trip || !newDest.trim()) return
    setSavingDest(true)
    try {
      await api.runner.setDestination(trip.id, {
        dest_label: newDest.trim(),
        dest_lat: newDestCoords?.lat,
        dest_lng: newDestCoords?.lng,
      })
      setEditDest(false)
      setNewDest('')
      setNewDestCoords(null)
      loadTrip()
    } catch {
    } finally {
      setSavingDest(false)
    }
  }
  async function arrive() {
    if (!trip) return
    await api.runner.arrive(trip.id).catch(() => {})
    loadTrip()
  }
  async function cancel() {
    if (!trip || !window.confirm(t('cancelConfirm'))) return
    await api.runner.cancel(trip.id).catch(() => {})
    loadTrip()
  }

  const control =
    'box-border h-11 w-full min-w-0 rounded-md border border-line bg-card px-3 text-[15px] text-ink'

  return (
    <div className="mt-7">
      <div className="eyebrow mb-3">{t('runnerTitle')}</div>

      {trip && trip.status === 'active' ? (
        <div className="flex flex-col gap-3">
          {trip.client && (
            <div className="text-[13px] text-muted">
              {t('toClient')}: <span className="font-medium text-ink">{trip.client.name}</span>
            </div>
          )}
          <ModeSelector value={trip.mode} onChange={switchMode} />
          <TripCard trip={trip} />

          {/* Change destination mid-trip (route changed on the way) */}
          {editDest ? (
            <div className="rounded-xl border border-line bg-card p-3.5">
              <span className="mb-1 block text-[12.5px] font-medium text-ink-2">{t('destLabel')}</span>
              <AddressField
                search={(q) => api.runner.geocode(q).then((r) => r.results)}
                value={newDest}
                placeholder={t('destPlaceholder')}
                onPick={(label, coords) => {
                  setNewDest(label)
                  setNewDestCoords(coords)
                }}
              />
              <div className="mt-2.5 flex gap-2">
                <Button
                  variant="solid"
                  size="sm"
                  className="flex-1"
                  disabled={savingDest || !newDest.trim()}
                  onClick={changeDestination}
                >
                  {t('save')}
                </Button>
                <Button variant="outline" size="sm" className="flex-1" onClick={() => setEditDest(false)}>
                  {t('back')}
                </Button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => {
                setNewDest(trip.dest.label || '')
                setNewDestCoords(null)
                setEditDest(true)
              }}
              className="flex items-center justify-center gap-1.5 rounded-lg border border-line bg-card py-2 text-[13px] font-medium text-accent transition-colors hover:border-accent/50"
            >
              <Pencil size={13} /> {t('changeDest')}
            </button>
          )}

          <div className="rounded-xl border border-line bg-accent-bg/50 px-3.5 py-2.5 text-[12.5px] text-ink-2">
            {t('trackingOn')}
          </div>
          <div className="flex gap-2">
            <Button variant="solid" size="block" className="flex-1" onClick={arrive}>
              {t('arriveBtn')}
            </Button>
            <Button variant="outline" size="block" className="flex-1" onClick={cancel}>
              {t('cancelBtn')}
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {/* Start a trip — the primary action, on top */}
          <div className="rounded-2xl border border-line bg-card p-5">
            <div className="text-[14px] font-semibold text-ink">{t('startTitle')}</div>
            {clients.length === 0 ? (
              <p className="mt-2 text-[13px] text-muted">{t('noClients')}</p>
            ) : (
              <div className="mt-3 flex flex-col gap-3">
                <label className="block">
                  <span className="mb-1 block text-[12.5px] font-medium text-ink-2">{t('pickClient')}</span>
                  <select value={clientId} onChange={(e) => setClientId(e.target.value)} className={control}>
                    <option value="">{t('pickClientPlaceholder')}</option>
                    {clients.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="mb-1 block text-[12.5px] font-medium text-ink-2">{t('destLabel')}</span>
                  <AddressField
                    search={(q) => api.runner.geocode(q).then((r) => r.results)}
                    value={dest}
                    placeholder={t('destPlaceholder')}
                    onPick={(label, coords) => {
                      setDest(label)
                      setDestCoords(coords)
                    }}
                  />
                </label>
                <label className="block">
                  <span className="mb-1 block text-[12.5px] font-medium text-ink-2">{t('originLabel')}</span>
                  <AddressField
                    search={(q) => api.runner.geocode(q).then((r) => r.results)}
                    value={origin}
                    placeholder={t('originPlaceholder')}
                    onPick={(label) => setOrigin(label)}
                  />
                </label>
                <div>
                  <span className="mb-1 block text-[12.5px] font-medium text-ink-2">{t('modeLabel')}</span>
                  <ModeSelector value={mode} onChange={setMode} />
                  {mode === 'transit' && (
                    <p className="mt-1.5 text-[11.5px] leading-snug text-gray">{t('transitEstimate')}</p>
                  )}
                </div>
                <Button variant="solid" size="block" disabled={busy || !clientId} onClick={start}>
                  {busy ? t('starting') : t('startBtn')}
                </Button>
              </div>
            )}
          </div>

          {/* Phone setup — collapsible (remembered once done) */}
          <div className="rounded-2xl border border-line bg-card">
            <button
              type="button"
              onClick={() => setSetupOpen((v) => !v)}
              className="flex w-full items-center justify-between gap-2 px-5 py-4 text-left"
            >
              <span className="flex items-center gap-2 text-[14px] font-semibold text-ink">
                <Smartphone size={16} className="text-accent" /> {t('setupTitle')}
              </span>
              <ChevronDown
                size={18}
                className={cn('shrink-0 text-gray transition-transform', setupOpen && 'rotate-180')}
              />
            </button>
            {!setupOpen && (
              <p className="-mt-1 px-5 pb-4 text-[12px] leading-snug text-muted">
                {t('setupCollapsedHint')}
              </p>
            )}
            {setupOpen && (
              <div className="px-5 pb-5">
                <p className="text-[12.5px] leading-snug text-muted">{t('setupIntro')}</p>
                <ol className="mt-3 flex flex-col gap-1.5 text-[13px] leading-snug text-ink-2">
                  <li>1. {t('installStep')}</li>
                  <li>2. {t('settingsStep')}</li>
                </ol>
                <div className="mt-3 flex flex-col gap-2.5">
                  <CopyRow
                    label={t('serverUrlLabel')}
                    value={cfg?.serverUrl || ''}
                    onCopy={() => cfg && copy(cfg.serverUrl, 'url')}
                    copyLabel={copied === 'url' ? t('copied') : t('copy')}
                  />
                  <CopyRow
                    label={t('deviceIdLabel')}
                    value={cfg?.deviceId || ''}
                    onCopy={() => cfg && copy(cfg.deviceId, 'id')}
                    copyLabel={copied === 'id' ? t('copied') : t('copy')}
                  />
                </div>
                <p className="mt-2.5 text-[11.5px] text-gray">{t('recommended')}</p>
                <div className="mt-3 flex items-center justify-between gap-2">
                  <button
                    onClick={regen}
                    className="text-[12.5px] text-gray underline underline-offset-2 hover:text-ink"
                  >
                    {t('regenToken')}
                  </button>
                  <button
                    onClick={() => {
                      localStorage.setItem('nh_track_setup_done', '1')
                      setSetupOpen(false)
                    }}
                    className="text-[12.5px] font-medium text-accent hover:underline"
                  >
                    {t('setupDone')}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
