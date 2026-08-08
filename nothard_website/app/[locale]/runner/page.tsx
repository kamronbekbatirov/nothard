'use client'

import { useEffect, useMemo, useState } from 'react'
import { useTranslations } from 'next-intl'
import { ChevronDown, Contact, MapPin, MessageSquare, Navigation, Pencil, Phone, RotateCw, Smartphone, X } from 'lucide-react'
import { AppTopbar } from '@/app/components/app-topbar'
import { Button } from '@/app/components/button'
import { Avatar } from '@/app/components/avatar'
import { ChatModal } from '@/app/components/chat'
import { AddressField } from '@/app/components/address-field'
import { TripCard } from '@/app/components/trip-card'
import { RouteOptions } from '@/app/components/route-options'
import { AppShellSkeleton } from '@/app/components/skeleton'
import { UnreadBadge } from '@/app/components/unread-badge'
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
  type TravelMode,
  type RouteOption,
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
  // The one active trip (if any) + the phone-setup config, lifted here so the
  // live map/route can live inside the matching client's card.
  const [trip, setTrip] = useState<(TripLive & { client: { id: number; name: string } | null }) | null>(null)
  const [cfg, setCfg] = useState<TrackConfig | null>(null)
  const loadTrip = () => api.runner.trip().then((r) => setTrip(r.trip)).catch(() => {})
  useEffect(() => {
    if (!ready) return
    load()
    loadTrip()
    api.runner.trackConfig().then(setCfg).catch(() => {})
    const id = window.setInterval(() => {
      load()
      loadTrip()
    }, 8000)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready])

  // Trip controls — used by whichever client card holds the active trip.
  const [startingFor, setStartingFor] = useState<number | null>(null)
  const tripCtl = {
    // Start a trip for a client — the backend auto-derives pickup (airport),
    // destination (their drop-off) and mode from what the client booked; the
    // runner doesn't choose any of it.
    start: async (clientId: number) => {
      if (trip) return
      setStartingFor(clientId)
      try {
        await api.runner.startTrip({ client_id: clientId })
        loadTrip()
      } catch {
      } finally {
        setStartingFor(null)
      }
    },
    here: async () => {
      if (!trip) return
      try {
        const r = await api.runner.here(trip.id)
        setTrip((c) => (c ? { ...r.trip, client: c.client } : c))
      } catch {
        loadTrip()
      }
    },
    met: async () => {
      if (!trip) return
      try {
        const r = await api.runner.met(trip.id)
        setTrip((c) => (c ? { ...r.trip, client: c.client } : c))
      } catch {
        loadTrip()
      }
    },
    setMode: async (m: TravelMode) => {
      if (!trip) return
      setTrip({ ...trip, mode: m })
      try {
        const r = await api.runner.setMode(trip.id, m)
        setTrip((c) => (c ? { ...r.trip, client: c.client } : c))
      } catch {
        loadTrip()
      }
    },
    setDest: async (label: string, coords: { lat: number; lng: number } | null) => {
      if (!trip) return
      await api.runner
        .setDestination(trip.id, { dest_label: label, dest_lat: coords?.lat, dest_lng: coords?.lng })
        .catch(() => {})
      loadTrip()
    },
    rebuild: async () => {
      if (!trip) return
      await api.runner.rebuildTrip(trip.id).catch(() => {})
      loadTrip()
    },
    routeOptions: () => (trip ? api.runner.routeOptions(trip.id).then((r) => r.options) : Promise.resolve([])),
    chooseRoute: async (opt: RouteOption) => {
      if (!trip) return
      const r = await api.runner.chooseRoute(trip.id, opt)
      setTrip((c) => (c ? { ...r.trip, client: c.client } : c))
    },
    arrive: async () => {
      if (!trip) return
      await api.runner.arrive(trip.id).catch(() => {})
      loadTrip()
    },
    cancel: async () => {
      // Confirmation is handled inline in TripArea (window.confirm is flaky in
      // the Telegram WebView).
      if (!trip) return
      await api.runner.cancel(trip.id).catch(() => {})
      loadTrip()
    },
  }

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

  // Cards to render: clients with pending visits, plus the client of the active
  // trip (so its live map shows even if that client has no pending visit).
  const shownClients = useMemo(() => {
    const list = [...activeClients]
    const cid = trip?.client?.id
    if (cid != null && !list.some((c) => c.id === cid)) {
      const full = (data?.clients ?? []).find((c) => c.id === cid)
      if (full) list.unshift({ ...full, tasks: full.tasks.filter((v) => v.stage !== 'done') })
    }
    return list
  }, [activeClients, trip, data])

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
        <p className="min-w-0 truncate text-[14px] text-muted">
          {t('greeting', { name: data?.name || user?.name || '' })}
        </p>

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
                <div className="mt-0.5">{t('visitsDoneCount', { count: data.payout.visitsDone })}</div>
              </div>
            </div>
            {/* Earnings history folded into the payout card (out of the main list) */}
            {history.length > 0 && <VisitHistory rows={history} />}
          </div>
        )}

        {/* Phone setup — collapsible; the live trip lives in the client cards below */}
        <PhoneSetupCard cfg={cfg} onRegen={(id) => setCfg((c) => (c ? { ...c, deviceId: id } : c))} />

        {/* My clients — each card holds that client's visits AND their live trip */}
        <div className="mt-7">
          <div className="eyebrow mb-3">{t('clientsTitle')}</div>
          {loaded && data && data.clients.length === 0 && (
            <div className="rounded-xl border border-dashed border-line bg-surface p-8 text-center text-[14px] text-muted">
              {t('noClients')}
            </div>
          )}
          {loaded && data && data.clients.length > 0 && shownClients.length === 0 && (
            <div className="rounded-xl border border-dashed border-line bg-surface p-8 text-center text-[14px] text-muted">
              {t('allDone')}
            </div>
          )}
          <div className="flex flex-col gap-4">
            {shownClients.map((c) => (
              <ClientCard
                key={c.id}
                c={c}
                trip={trip?.client?.id === c.id ? trip : null}
                tripCtl={tripCtl}
                tripBusyElsewhere={!!trip && trip.client?.id !== c.id}
                starting={startingFor === c.id}
                onStartTrip={() => tripCtl.start(c.id)}
                onAdvance={advance}
                onChat={() => setChatClient(c)}
              />
            ))}
          </div>
        </div>

        {/* History — completed visits (the runner's earnings log) */}
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
          onClose={() => {
            setChatClient(null)
            load() // clear the unread badge immediately (don't wait for the poll)
          }}
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

type TripWithClient = TripLive & { client: { id: number; name: string } | null }
type TripCtl = {
  start: (clientId: number) => void
  here: () => void
  met: () => void
  setMode: (m: TravelMode) => void
  setDest: (label: string, coords: { lat: number; lng: number } | null) => Promise<void>
  rebuild: () => void
  routeOptions: () => Promise<RouteOption[]>
  chooseRoute: (opt: RouteOption) => Promise<void>
  arrive: () => void
  cancel: () => void
}

function ClientCard({
  c,
  trip,
  tripCtl,
  tripBusyElsewhere,
  starting,
  onStartTrip,
  onAdvance,
  onChat,
}: {
  c: RunnerClientRow
  trip: TripWithClient | null
  tripCtl: TripCtl
  tripBusyElsewhere: boolean
  starting: boolean
  onStartTrip: () => void
  onAdvance: (taskId: number) => void
  onChat: () => void
}) {
  const t = useTranslations('Runner')
  const tp = useTranslations('Packages')
  const [signOpen, setSignOpen] = useState(false)
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
            className="relative flex h-9 w-9 items-center justify-center rounded-full bg-inverse text-inverse-fg"
          >
            <MessageSquare size={16} />
            <UnreadBadge count={c.unread} className="absolute -right-1 -top-1 border-2 border-card" />
          </button>
        </div>
      </div>

      {/* Arrival details the runner needs (when / airport / flight / where to). */}
      {(c.arrival.arrivalDate || c.arrival.airport || c.arrival.dropoff) && (
        <div className="border-b border-line bg-accent-bg/30 px-4 py-3 text-[13px] text-ink-2">
          {(c.arrival.arrivalDate || c.arrival.flight) && (
            <div className="flex items-start gap-2">
              <span className="shrink-0">✈️</span>
              <span>
                {c.arrival.arrivalDate && (
                  <>
                    {fmtDate(c.arrival.arrivalDate)}
                    {c.arrival.arrivalTime ? ` · ${c.arrival.arrivalTime}` : ''}
                  </>
                )}
                {c.arrival.airport ? ` · ${c.arrival.airport}` : ''}
                {c.arrival.flight ? ` · ${t('flightShort')} ${c.arrival.flight}` : ''}
              </span>
            </div>
          )}
          {c.arrival.dropoff && (
            <div className="mt-1 flex items-start gap-2">
              <span className="shrink-0">🏠</span>
              <span className="min-w-0">{c.arrival.dropoff}</span>
            </div>
          )}
        </div>
      )}

      {/* "Show sign" — a fullscreen nothard board the runner holds up so the
          client recognises them at the airport arrivals exit. */}
      <div className="border-b border-line px-4 py-3">
        <Button variant="outline" size="block" className="gap-2" onClick={() => setSignOpen(true)}>
          <Contact size={16} /> {t('showSign')}
        </Button>
      </div>
      {signOpen && <MeetSignOverlay name={c.name} onClose={() => setSignOpen(false)} />}

      {/* Visits. Airport steps (meet/transfer) are DRIVEN by the trip buttons
          below — shown read-only here so the runner doesn't advance them twice. */}
      <div className="flex flex-col divide-y divide-line">
        {c.tasks.length === 0 && <div className="p-4 text-[13px] text-muted">{t('noVisits')}</div>}
        {c.tasks.map((v) => (
          <VisitRow
            key={v.id}
            v={v}
            driven={v.kind === 'step' && (v.key === 'airportMeet' || v.key === 'transfer')}
            onAdvance={() => onAdvance(v.id)}
          />
        ))}
      </div>

      {/* Live trip for this client */}
      <TripArea
        trip={trip}
        tripCtl={tripCtl}
        busyElsewhere={tripBusyElsewhere}
        starting={starting}
        onStart={onStartTrip}
      />
    </div>
  )
}

/* ---------- Per-client live trip area (inside the client card) ---------- */
function TripArea({
  trip,
  tripCtl,
  busyElsewhere,
  starting,
  onStart,
}: {
  trip: TripWithClient | null
  tripCtl: TripCtl
  busyElsewhere: boolean
  starting: boolean
  onStart: () => void
}) {
  const t = useTranslations('Tracking')
  const [editDest, setEditDest] = useState(false)
  const [newDest, setNewDest] = useState('')
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null)
  const [confirmCancel, setConfirmCancel] = useState(false)
  const [showRoutes, setShowRoutes] = useState(false)

  if (!trip) {
    return (
      <div className="border-t border-line p-4">
        {busyElsewhere ? (
          <p className="text-center text-[12.5px] text-muted">{t('busyElsewhere')}</p>
        ) : (
          <Button variant="outline" size="block" className="gap-1.5 text-accent" disabled={starting} onClick={onStart}>
            <Navigation size={14} /> {starting ? t('starting') : t('startTitle')}
          </Button>
        )}
      </div>
    )
  }

  const toPickup = trip.phase === 'toPickup'
  const waiting = toPickup && trip.atPickup

  return (
    <div className="flex flex-col gap-3 border-t border-line bg-accent-bg/30 p-4">
      {/* Phase banner — going to the airport, waiting there, or taking the client home */}
      <div className="rounded-lg bg-card px-3 py-2 text-[12.5px] leading-snug">
        <span className="font-semibold text-accent">
          {waiting ? t('phaseWaiting') : toPickup ? t('phasePickup') : t('phaseDest')}
        </span>{' '}
        <span className="text-ink-2">
          {toPickup ? trip.pickup.label || '—' : trip.dest.label || '—'}
        </span>
      </div>

      {/* Choose the route (all modes/alternatives) instead of an auto-picked one. */}
      {showRoutes ? (
        <div className="rounded-lg border border-line bg-surface p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[12px] font-medium text-ink-2">{t('chooseRoute')}</span>
            <button onClick={() => setShowRoutes(false)} className="text-[12px] text-gray hover:text-ink">
              {t('back')}
            </button>
          </div>
          <RouteOptions
            load={tripCtl.routeOptions}
            onChoose={async (opt) => {
              await tripCtl.chooseRoute(opt)
              setShowRoutes(false)
            }}
          />
        </div>
      ) : (
        <Button variant="outline" size="block" className="gap-1.5" onClick={() => setShowRoutes(true)}>
          <Navigation size={13} /> {t('chooseRoute')}
        </Button>
      )}
      <TripCard trip={trip} runnerView />

      {trip.offRoute && (
        <div className="flex items-center justify-between gap-2 rounded-lg border border-amber-500/50 bg-amber-500/10 px-3 py-2 text-[12.5px] text-amber-700">
          <span>{t('offRoute')}</span>
          <button onClick={tripCtl.rebuild} className="shrink-0 font-semibold underline">
            {t('rebuild')}
          </button>
        </div>
      )}

      {editDest ? (
        <div className="rounded-lg border border-line bg-surface p-3">
          <span className="mb-1 block text-[12px] font-medium text-ink-2">{t('destLabel')}</span>
          <AddressField
            search={(q) => api.runner.geocode(q).then((r) => r.results)}
            value={newDest}
            placeholder={t('destPlaceholder')}
            onPick={(l, cc) => {
              setNewDest(l)
              setCoords(cc)
            }}
          />
          <div className="mt-2 flex gap-2">
            <Button
              variant="solid"
              size="sm"
              className="flex-1"
              disabled={!newDest.trim()}
              onClick={async () => {
                await tripCtl.setDest(newDest.trim(), coords)
                setEditDest(false)
              }}
            >
              {t('save')}
            </Button>
            <Button variant="outline" size="sm" className="flex-1" onClick={() => setEditDest(false)}>
              {t('back')}
            </Button>
          </div>
        </div>
      ) : (
        <Button
          variant="outline"
          size="block"
          className="gap-1.5"
          onClick={() => {
            setNewDest(trip.dest.label || '')
            setCoords(null)
            setEditDest(true)
          }}
        >
          <Pencil size={12} /> {t('changeDest')}
        </Button>
      )}

      {confirmCancel ? (
        // Inline confirm — window.confirm is unreliable inside the Telegram WebView.
        // Buttons stacked full-width so long labels never overflow on a phone.
        <div className="rounded-lg border border-terracotta/40 bg-terracotta/5 p-3">
          <p className="mb-2.5 text-center text-[13px] text-ink-2">{t('cancelConfirm')}</p>
          <div className="flex flex-col gap-2">
            <Button
              variant="danger"
              size="block"
              onClick={() => {
                setConfirmCancel(false)
                tripCtl.cancel()
              }}
            >
              {t('cancelYes')}
            </Button>
            <Button variant="outline" size="block" onClick={() => setConfirmCancel(false)}>
              {t('back')}
            </Button>
          </div>
        </div>
      ) : (
        // Primary action is full-width on its own line; cancel is a quiet text
        // button below — two wide nowrap buttons side by side overflowed on phones.
        // Phase 1 is a two-tap flow: "I'm at the airport" (here) → "Met the client"
        // (met); phase 2 is a single "Arrived" — each tap also advances the client's
        // step status, so the runner never ticks the steps off separately.
        <>
          <Button
            variant="solid"
            size="block"
            onClick={waiting ? tripCtl.met : toPickup ? tripCtl.here : tripCtl.arrive}
          >
            {waiting ? t('metBtn') : toPickup ? t('hereBtn') : t('arriveBtn')}
          </Button>
          <button
            onClick={() => setConfirmCancel(true)}
            className="mx-auto text-[12.5px] text-gray underline underline-offset-2 hover:text-terracotta"
          >
            {t('cancelBtn')}
          </button>
        </>
      )}
    </div>
  )
}

function VisitRow({ v, onAdvance, driven = false }: { v: RunnerVisitRow; onAdvance: () => void; driven?: boolean }) {
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

          {/* Airport steps are advanced by the trip buttons below — show a hint
              instead of a duplicate action here. */}
          {!done && driven && (
            <div className="mt-2 text-[12px] text-muted">{t('drivenByTrip')}</div>
          )}
          {!done && !driven && (
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

function VisitHistory({ rows }: { rows: (RunnerVisitRow & { client: string })[] }) {
  const t = useTranslations('Runner')
  const label = useTaskLabel()
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-4 border-t border-line pt-4">
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
              <span className="shrink-0 text-[13px] font-semibold text-accent">+{fmtGBP(v.fee)}</span>
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

function fmtDate(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'long' })
}

/* ---------- Airport "meeting sign" the runner holds up ---------- */
/**
 * A fullscreen white board with the big nothard wordmark (+ the client's name),
 * so the runner can hold their phone up at the arrivals exit and the client
 * recognises them. Fixed light colours (it's a physical sign) regardless of theme.
 */
function MeetSignOverlay({ name, onClose }: { name: string; onClose: () => void }) {
  // Controls are hidden for a clean board; a tap toggles them. A rotate button
  // spins the sign 90° at a time — useful to show it landscape when the phone's
  // auto-rotate is locked.
  const [showCtl, setShowCtl] = useState(false)
  const [deg, setDeg] = useState(0)
  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = prev
      document.removeEventListener('keydown', onKey)
    }
  }, [onClose])
  const sideways = deg % 180 !== 0
  return (
    <div
      onClick={() => setShowCtl((s) => !s)}
      className="fixed inset-0 z-[100000] flex items-center justify-center overflow-hidden bg-white"
    >
      {/* Rotatable board — when sideways, swap width/height to fill the screen. */}
      <div
        className="flex flex-col items-center justify-center px-6 transition-transform duration-300"
        style={{
          width: sideways ? '100dvh' : '100dvw',
          height: sideways ? '100dvw' : '100dvh',
          transform: `rotate(${deg}deg)`,
        }}
      >
        <span
          className="font-display leading-none"
          style={{ fontSize: 'clamp(56px, 22vmin, 200px)', letterSpacing: '-0.02em' }}
        >
          <span style={{ color: '#1B1A17' }}>not</span>
          <span style={{ color: '#2F5D45' }}>hard.</span>
        </span>
        {name && (
          <div
            className="mt-8 text-center font-semibold text-[#1B1A17]"
            style={{ fontSize: 'clamp(30px, 11vmin, 84px)' }}
          >
            {name}
          </div>
        )}
      </div>

      {/* Controls appear only after a tap. stopPropagation so tapping a button
          performs its action without also toggling the controls off. */}
      {showCtl && (
        <>
          <button
            onClick={(e) => {
              e.stopPropagation()
              setDeg((d) => (d + 90) % 360)
            }}
            aria-label="rotate"
            className="absolute left-4 top-4 flex h-11 w-11 items-center justify-center rounded-full bg-black/5 text-[#1B1A17]"
          >
            <RotateCw size={22} />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onClose()
            }}
            aria-label="close"
            className="absolute right-4 top-4 flex h-11 w-11 items-center justify-center rounded-full bg-black/5 text-[#1B1A17]"
          >
            <X size={22} />
          </button>
        </>
      )}
    </div>
  )
}

export function PanelLoading() {
  return <AppShellSkeleton />
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

/* ---------- Phone setup (collapsible) ---------- */
function PhoneSetupCard({
  cfg,
  onRegen,
}: {
  cfg: TrackConfig | null
  onRegen: (deviceId: string) => void
}) {
  const t = useTranslations('Tracking')
  const { toast } = useToast()
  // Collapsed by default — the runner opens the setup instructions themselves
  // instead of them re-expanding on every visit.
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState('')
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
      onRegen(r.deviceId)
    } catch {}
  }
  return (
    <div className="mt-4 rounded-2xl border border-line bg-card">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-2 px-5 py-4 text-left"
      >
        <span className="flex items-center gap-2 text-[14px] font-semibold text-ink">
          <Smartphone size={16} className="text-accent" /> {t('setupTitle')}
        </span>
        <ChevronDown size={18} className={cn('shrink-0 text-gray transition-transform', open && 'rotate-180')} />
      </button>
      {!open && <p className="-mt-1 px-5 pb-4 text-[12px] leading-snug text-muted">{t('setupCollapsedHint')}</p>}
      {open && (
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
            <button onClick={regen} className="text-[12.5px] text-gray underline underline-offset-2 hover:text-ink">
              {t('regenToken')}
            </button>
            <button
              onClick={() => setOpen(false)}
              className="text-[12.5px] font-medium text-accent hover:underline"
            >
              {t('setupDone')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
