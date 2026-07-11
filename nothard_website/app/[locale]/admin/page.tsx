'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Camera, Paperclip, Pencil, Plus, Search, Star, Trash2, X } from 'lucide-react'
import { AppTopbar } from '@/app/components/app-topbar'
import { Button } from '@/app/components/button'
import { Field, Input } from '@/app/components/field'
import { ChatModal } from '@/app/components/chat'
import { useToast } from '@/app/components/toast'
import { PanelLoading } from '../runner/page'
import { useRequireRole } from '@/app/lib/use-require-role'
import {
  api,
  clearTokens,
  type Role,
  type AdminOverview,
  type AdminClient,
  type AdminAccount,
  type AdminPayments,
  type AdminReviews,
  type AdminListing,
  type AdminListings,
  type ListingStatus,
  type HousingStatus,
  type HousingItem,
} from '@/app/lib/api'
import { fmtGBP, PACKAGES, SERVICES, LONDON_AIRPORT_TERMINALS, LONDON_FLIGHTS } from '@/app/lib/data'
import { useTaskLabel } from '@/app/lib/task-label'
import { cn } from '@/app/lib/utils'

type Tab = 'overview' | 'clients' | 'runners' | 'payments' | 'team' | 'reviews' | 'listings'

// Physical / logistics services are handed over in person — no file to upload.
const NO_FILE_SERVICES = new Set(['sim', 'oyster', 'airportTransport', 'airportTaxi', 'tempHousing', 'moving'])

export default function AdminPage() {
  const t = useTranslations('Admin')
  const { toast } = useToast()
  const { ready, user } = useRequireRole(['operator'])

  const [tab, setTab] = useState<Tab>('overview')
  const [overview, setOverview] = useState<AdminOverview | null>(null)
  const [accounts, setAccounts] = useState<AdminAccount[] | null>(null)
  const [payments, setPayments] = useState<AdminPayments | null>(null)
  const [reviews, setReviews] = useState<AdminReviews | null>(null)
  const [listings, setListings] = useState<AdminListings | null>(null)

  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [chatClient, setChatClient] = useState<AdminClient | null>(null)

  const loadOverview = () => api.admin.overview().then(setOverview).catch(() => {})
  const loadAccounts = () => api.admin.accounts().then((r) => setAccounts(r.accounts)).catch(() => {})
  const loadPayments = () => api.admin.payments().then(setPayments).catch(() => {})
  const loadReviews = () => api.admin.reviews().then(setReviews).catch(() => {})
  const loadListings = () => api.admin.listings().then(setListings).catch(() => {})

  // Live board: poll the overview so completed tasks / new clients appear live.
  useEffect(() => {
    if (!ready) return
    loadOverview()
    const id = window.setInterval(loadOverview, 8000)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready])

  useEffect(() => {
    if (!ready) return
    if (tab === 'clients' || tab === 'runners' || tab === 'team') loadAccounts()
    if (tab === 'payments') loadPayments()
    if (tab === 'reviews') loadReviews()
    if (tab === 'listings') loadListings()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, tab])

  const selected =
    selectedId != null ? overview?.clients.find((c) => c.id === selectedId) ?? null : null

  function applyClient(updated: AdminClient) {
    setOverview((o) =>
      o ? { ...o, clients: o.clients.map((c) => (c.id === updated.id ? updated : c)) } : o
    )
  }

  async function assignRunner(clientId: number, runnerId?: number | null) {
    try {
      applyClient(await api.admin.assignRunner(clientId, runnerId))
      toast(t('saved'))
    } catch {}
  }
  async function assignManager(clientId: number, managerId?: number | null) {
    try {
      applyClient(await api.admin.assignManager(clientId, managerId))
      toast(t('saved'))
    } catch {}
  }
  async function setTaskStatus(taskId: number, status: string) {
    try {
      applyClient(await api.admin.setTaskStatus(taskId, status))
    } catch {}
  }
  async function renameClient(clientId: number, name: string) {
    try {
      applyClient(await api.admin.updateClient(clientId, name))
      toast(t('saved'))
    } catch {}
  }
  async function deleteClient(clientId: number) {
    try {
      await api.admin.deleteClient(clientId)
      setSelectedId(null)
      loadOverview()
      loadAccounts()
      toast(t('accounts.deleted'))
    } catch {}
  }
  async function setHousingStatus(
    id: number,
    status: HousingStatus,
    opts?: { note?: string; viewingAt?: string }
  ) {
    try {
      applyClient(await api.admin.setHousingStatus(id, status, opts))
    } catch {}
  }
  async function uploadHousingMedia(id: number, file: File) {
    try {
      applyClient(await api.admin.uploadHousingMedia(id, file))
      toast(t('saved'))
    } catch {}
  }
  async function deleteHousingMedia(mediaId: number) {
    try {
      applyClient(await api.admin.deleteHousingMedia(mediaId))
    } catch {}
  }
  async function setPackage(clientId: number, packageId: string) {
    try {
      applyClient(await api.admin.setPackage(clientId, packageId))
      toast(t('saved'))
    } catch {}
  }
  async function addService(clientId: number, serviceId: string) {
    try {
      applyClient(await api.admin.addService(clientId, serviceId))
      toast(t('saved'))
    } catch {}
  }
  async function deleteOrder(orderId: number) {
    try {
      applyClient(await api.admin.deleteOrder(orderId))
      toast(t('saved'))
    } catch {}
  }
  async function setArrival(clientId: number, fields: Record<string, string>) {
    try {
      applyClient(await api.admin.setArrival(clientId, fields))
      toast(t('saved'))
    } catch {}
  }
  async function uploadAttachment(orderId: number, file: File) {
    try {
      applyClient(await api.admin.uploadAttachment(orderId, file))
      toast(t('saved'))
    } catch {}
  }
  async function uploadTaskAttachment(taskId: number, file: File) {
    try {
      applyClient(await api.admin.uploadTaskAttachment(taskId, file))
      toast(t('saved'))
    } catch {}
  }
  async function deleteAttachment(id: number) {
    try {
      applyClient(await api.admin.deleteAttachment(id))
    } catch {}
  }

  if (!ready) return <PanelLoading />

  const menu = [
    { key: 'overview', label: t('menu.orders') },
    { key: 'clients', label: t('menu.clients') },
    { key: 'runners', label: t('menu.runners') },
    { key: 'payments', label: t('menu.payments') },
    { key: 'listings', label: t('menu.listings') },
    { key: 'reviews', label: t('menu.reviews') },
    { key: 'team', label: t('menu.team') },
  ].map((m) => ({ label: m.label, active: tab === m.key, onClick: () => setTab(m.key as Tab) }))

  return (
    <div className="min-h-screen bg-paper">
      <AppTopbar
        badge={t('badge')}
        menu={menu}
        name={user?.name}
        avatarUrl={user?.photo_url}
        onLogout={() => {
          clearTokens()
          window.location.href = '/login'
        }}
      />

      <main className="mx-auto max-w-[1240px] px-5 py-8 sm:px-8">
        {tab === 'overview' && <OverviewView data={overview} onSelect={setSelectedId} />}
        {tab === 'clients' && <ClientsView data={overview} onSelect={setSelectedId} />}
        {tab === 'runners' && <RunnersView accounts={accounts} onChanged={loadAccounts} />}
        {tab === 'payments' && <PaymentsView data={payments} onChanged={loadPayments} />}
        {tab === 'team' && <TeamView accounts={accounts} onChanged={loadAccounts} />}
        {tab === 'reviews' && <ReviewsView data={reviews} />}
        {tab === 'listings' && <ListingsView data={listings} onChanged={loadListings} />}
      </main>

      {/* Client drawer */}
      <div
        className={cn(
          'fixed inset-0 z-[99997] bg-black/25 transition-opacity',
          selected ? 'opacity-100' : 'pointer-events-none opacity-0'
        )}
        onClick={() => setSelectedId(null)}
      />
      <div
        className={cn(
          'fixed right-0 top-0 z-[99998] h-full w-[390px] max-w-[92vw] overflow-y-auto border-l border-line bg-surface shadow-drawer transition-transform duration-300',
          selected ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {selected && overview && (
          <Drawer
            client={selected}
            runners={overview.runners}
            managers={overview.managers}
            onClose={() => setSelectedId(null)}
            onChat={() => setChatClient(selected)}
            onAssignRunner={(rid) => assignRunner(selected.id, rid)}
            onAssignManager={(mid) => assignManager(selected.id, mid)}
            onSetTaskStatus={setTaskStatus}
            onRename={(name) => renameClient(selected.id, name)}
            onDelete={() => deleteClient(selected.id)}
            onHousingStatus={setHousingStatus}
            onUploadHousingMedia={uploadHousingMedia}
            onDeleteHousingMedia={deleteHousingMedia}
            onUploadAttachment={uploadAttachment}
            onUploadTaskAttachment={uploadTaskAttachment}
            onDeleteAttachment={deleteAttachment}
            onSetPackage={(pid) => setPackage(selected.id, pid)}
            onAddService={(sid) => addService(selected.id, sid)}
            onDeleteOrder={deleteOrder}
            onSetArrival={(fields) => setArrival(selected.id, fields)}
          />
        )}
      </div>

      {chatClient && (
        <ChatModal
          title={chatClient.name}
          subtitle={t('chat.title')}
          peerName={chatClient.name}
          placeholder={t('chat.placeholder')}
          emptyText={t('chat.empty')}
          meSide="manager"
          fetchMessages={() => api.admin.messages(chatClient.id).then((r) => r.messages)}
          sendMessage={(body) => api.admin.sendMessage(chatClient.id, body)}
          onClose={() => setChatClient(null)}
        />
      )}
    </div>
  )
}

/* ================= Overview (active relocations only) ================= */
function OverviewView({
  data,
  onSelect,
}: {
  data: AdminOverview | null
  onSelect: (id: number) => void
}) {
  const t = useTranslations('Admin')
  // Completed relocations drop off the board — only active work is shown here.
  const active = (data?.clients ?? []).filter((c) => c.active)
  return (
    <>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi value={String(data?.kpis.activeClients ?? '—')} label={t('kpi.activeClients')} />
        <Kpi value={String(data?.kpis.tasksToday ?? '—')} label={t('kpi.tasksToday')} />
        <Kpi
          value={data ? fmtGBP(data.kpis.awaitingPayment) : '—'}
          label={t('kpi.awaitingPayment')}
          tone="terracotta"
        />
        <Kpi value={data ? `+${data.kpis.newWeek}` : '—'} label={t('kpi.newWeek')} tone="accent" />
      </div>

      <div className="mt-7 grid gap-6 lg:grid-cols-[1fr_300px]">
        <div className="overflow-hidden rounded-xl border border-line bg-card">
          <div className="border-b border-line px-5 py-3.5">
            <h2 className="font-display text-[18px] text-ink">{t('activeTitle')}</h2>
          </div>
          <ClientsTable clients={active} onSelect={onSelect} emptyText={t('noActive')} />
        </div>

        <aside className="rounded-xl border border-line bg-card p-5">
          <h2 className="mb-4 font-display text-[17px] text-ink">{t('attentionTitle')}</h2>
          <div className="flex flex-col gap-3">
            {(data?.attention ?? []).map((a) => (
              <button
                key={a.id}
                onClick={() => onSelect(a.clientId)}
                className="w-full rounded-lg border border-line bg-surface p-3.5 text-left transition-colors hover:border-accent/40"
              >
                <div className="text-[13px] font-medium text-ink">{t(`attention.${a.type}`)}</div>
                <div className="mt-0.5 text-[12.5px] text-muted">{a.who}</div>
                <div className="mt-2 text-[12px] font-semibold text-accent">{t('openCard')} →</div>
              </button>
            ))}
            {data && data.attention.length === 0 && (
              <p className="text-[13px] text-muted">{t('attentionEmpty')}</p>
            )}
          </div>
        </aside>
      </div>
    </>
  )
}

/* ================= Clients (segmented) ================= */
type Segment = 'all' | 'relocation' | 'services' | 'completed'

function segmentOf(c: AdminClient): Segment {
  if (c.completed) return 'completed'
  if (c.hasPackage && !c.packageComplete) return 'relocation'
  return 'services'
}

function ClientsView({
  data,
  onSelect,
}: {
  data: AdminOverview | null
  onSelect: (id: number) => void
}) {
  const t = useTranslations('Admin')
  const [q, setQ] = useState('')
  const [seg, setSeg] = useState<Segment>('all')
  const all = data?.clients ?? []

  const counts = useMemo(() => {
    const c = { all: all.length, relocation: 0, services: 0, completed: 0 }
    for (const cl of all) c[segmentOf(cl)]++
    return c
  }, [all])

  const clients = useMemo(() => {
    const s = q.trim().toLowerCase()
    return all.filter(
      (c) =>
        (seg === 'all' || segmentOf(c) === seg) &&
        (!s || c.name.toLowerCase().includes(s))
    )
  }, [all, q, seg])

  const segs: { key: Segment; label: string }[] = [
    { key: 'all', label: t('segments.all') },
    { key: 'relocation', label: t('segments.relocation') },
    { key: 'services', label: t('segments.services') },
    { key: 'completed', label: t('segments.completed') },
  ]

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="nd-hscroll flex gap-1.5">
          {segs.map((s) => (
            <button
              key={s.key}
              onClick={() => setSeg(s.key)}
              className={cn(
                'shrink-0 rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-colors',
                seg === s.key ? 'bg-accent text-white' : 'bg-card text-muted hover:text-ink'
              )}
            >
              {s.label} <span className="opacity-60">{counts[s.key]}</span>
            </button>
          ))}
        </div>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t('searchClients')}
          className="w-full max-w-[240px] rounded-full border border-line bg-surface px-4 py-2 text-[13.5px] text-ink outline-none focus:border-accent"
        />
      </div>

      <div className="overflow-hidden rounded-xl border border-line bg-card">
        <ClientsTable clients={clients} onSelect={onSelect} withStatus />
      </div>
    </div>
  )
}

function StatusChip({ client }: { client: AdminClient }) {
  const t = useTranslations('Admin')
  const seg = segmentOf(client)
  const tone: Record<Segment, string> = {
    completed: 'bg-sub text-muted',
    relocation: 'bg-accent/15 text-accent',
    services: 'bg-sky-500/15 text-sky-700',
    all: '',
  }
  return (
    <span className={cn('rounded-full px-2 py-0.5 text-[11.5px] font-medium', tone[seg])}>
      {t(`segments.${seg}`)}
    </span>
  )
}

function ClientsTable({
  clients,
  onSelect,
  emptyText,
  withStatus,
}: {
  clients: AdminClient[]
  onSelect: (id: number) => void
  emptyText?: string
  withStatus?: boolean
}) {
  const t = useTranslations('Admin')
  const cols = withStatus ? 5 : 5
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-left">
        <thead>
          <tr className="text-[11px] uppercase tracking-wide text-gray">
            <th className="px-5 py-2.5 font-semibold">{t('cols.client')}</th>
            <th className="px-3 py-2.5 font-semibold">{t('cols.package')}</th>
            <th className="px-3 py-2.5 font-semibold">{withStatus ? t('cols.status') : t('cols.step')}</th>
            <th className="px-3 py-2.5 font-semibold">{t('cols.runner')}</th>
            <th className="px-5 py-2.5 font-semibold">{t('cols.payment')}</th>
          </tr>
        </thead>
        <tbody>
          {clients.map((c) => (
            <tr
              key={c.id}
              className="nd-row border-t border-line text-[13.5px]"
              onClick={() => onSelect(c.id)}
            >
              <td className="px-5 py-3 font-medium text-ink">{c.name}</td>
              <td className="px-3 py-3 text-ink-2">
                <PkgName pkg={c.package} />
              </td>
              <td className="px-3 py-3">{withStatus ? <StatusChip client={c} /> : <StepCell client={c} />}</td>
              <td className="px-3 py-3">
                {c.runner ? (
                  <span className="text-ink-2">{c.runner}</span>
                ) : (
                  <span className="text-terracotta">{t('noRunner')}</span>
                )}
              </td>
              <td className="px-5 py-3">
                <PaymentPill paid={c.paid} paidLabel={t('paid')} unpaidLabel={t('unpaid')} />
              </td>
            </tr>
          ))}
          {clients.length === 0 && (
            <tr>
              <td colSpan={cols} className="px-5 py-8 text-center text-[13.5px] text-muted">
                {emptyText || '—'}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

/* ================= Runners ================= */
function RunnersView({
  accounts,
  onChanged,
}: {
  accounts: AdminAccount[] | null
  onChanged: () => void
}) {
  const t = useTranslations('Admin')
  const [editing, setEditing] = useState<AdminAccount | 'new' | null>(null)
  const runners = (accounts ?? []).filter((a) => a.role === 'runner')

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-display text-[20px] text-ink">{t('menu.runners')}</h2>
        <Button variant="dark" size="sm" className="gap-1.5" onClick={() => setEditing('new')}>
          <Plus size={15} /> {t('accounts.addRunner')}
        </Button>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {runners.map((r) => {
          const total = r.taskTotal ?? 0
          const done = r.taskDone ?? 0
          const pct = total ? Math.round((done / total) * 100) : 0
          return (
            <div key={r.id} className="rounded-xl border border-line bg-card p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2.5">
                  <Avatar url={r.photoUrl} name={r.name} size={40} />
                  <div>
                    <div className="text-[14.5px] font-semibold text-ink">{r.name}</div>
                    <div className="text-[12px] text-muted">
                      {r.active ? t('accounts.active') : t('accounts.inactive')}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setEditing(r)}
                  className="text-gray hover:text-ink"
                  aria-label="edit"
                >
                  <Pencil size={15} />
                </button>
              </div>
              <div className="mt-3 flex items-center justify-between text-[12.5px] text-muted">
                <span>{t('accounts.workload', { done, total })}</span>
                <span className="font-medium text-accent">{pct}%</span>
              </div>
              <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-track">
                <div className="h-full rounded-full bg-accent" style={{ width: `${pct}%` }} />
              </div>
            </div>
          )
        })}
        {runners.length === 0 && <p className="text-[13.5px] text-muted">—</p>}
      </div>

      {editing && (
        <AccountModal
          account={editing === 'new' ? null : editing}
          fixedRole="runner"
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            onChanged()
          }}
        />
      )}
    </div>
  )
}

/* ================= Payments ================= */
function PaymentsView({
  data,
  onChanged,
}: {
  data: AdminPayments | null
  onChanged: () => void
}) {
  const t = useTranslations('Admin')
  const ts = useTranslations('Services')
  const tp = useTranslations('Packages')
  const { toast } = useToast()

  async function toggle(id: number, paid: boolean) {
    try {
      await api.admin.setOrderPaid(id, paid)
      toast(t('saved'))
      onChanged()
    } catch {}
  }
  async function refund(id: number) {
    try {
      await api.admin.refundOrder(id)
      toast(t('payments.refunded'))
      onChanged()
    } catch {}
  }

  return (
    <div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi value={data ? fmtGBP(data.totals.paid) : '—'} label={t('payments.totalPaid')} tone="accent" />
        <Kpi
          value={data ? fmtGBP(data.totals.unpaid) : '—'}
          label={t('payments.totalUnpaid')}
          tone="terracotta"
        />
        <Kpi value={data ? fmtGBP(data.totals.refunded) : '—'} label={t('payments.totalRefunded')} />
        <Kpi value={String(data?.totals.count ?? '—')} label={t('payments.count')} />
      </div>

      <div className="mt-7 overflow-hidden rounded-xl border border-line bg-card">
        <div className="border-b border-line px-5 py-3.5">
          <h2 className="font-display text-[18px] text-ink">{t('menu.payments')}</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[680px] text-left">
            <thead>
              <tr className="text-[11px] uppercase tracking-wide text-gray">
                <th className="px-5 py-2.5 font-semibold">{t('cols.client')}</th>
                <th className="px-3 py-2.5 font-semibold">{t('payments.item')}</th>
                <th className="px-3 py-2.5 font-semibold">{t('payments.amount')}</th>
                <th className="px-3 py-2.5 font-semibold">{t('cols.payment')}</th>
                <th className="px-5 py-2.5 font-semibold"></th>
              </tr>
            </thead>
            <tbody>
              {(data?.orders ?? []).map((o) => (
                <tr key={o.id} className="border-t border-line text-[13.5px]">
                  <td className="px-5 py-3 font-medium text-ink">{o.clientName || '—'}</td>
                  <td className="px-3 py-3 text-ink-2">
                    {o.itemType === 'package' ? (
                      <>{tp(`${o.itemId}.name` as any)}</>
                    ) : (
                      <>{ts(`items.${o.itemId}.name` as any)}</>
                    )}
                  </td>
                  <td className="px-3 py-3 font-medium text-ink">{fmtGBP(o.amountGBP)}</td>
                  <td className="px-3 py-3">
                    {o.status === 'refunded' ? (
                      <span className="rounded-full bg-sub px-2.5 py-1 text-[12px] font-medium text-muted">
                        {t('payments.refundedBadge')}
                      </span>
                    ) : (
                      <PaymentPill paid={o.paid} paidLabel={t('paid')} unpaidLabel={t('unpaid')} />
                    )}
                  </td>
                  <td className="px-5 py-3">
                    {o.status !== 'refunded' && (
                      <span className="flex gap-2">
                        <button
                          onClick={() => toggle(o.id, !o.paid)}
                          className={cn(
                            'rounded-full border px-2.5 py-1 text-[11.5px] font-medium transition-colors',
                            o.paid
                              ? 'border-line text-muted hover:text-ink'
                              : 'border-accent/40 text-accent hover:bg-accent-bg'
                          )}
                        >
                          {o.paid ? t('payments.markUnpaid') : t('payments.markPaid')}
                        </button>
                        {o.paid && (
                          <button
                            onClick={() => refund(o.id)}
                            className="rounded-full border border-terracotta/40 px-2.5 py-1 text-[11.5px] font-medium text-terracotta hover:bg-terracotta-bg"
                          >
                            {t('payments.refund')}
                          </button>
                        )}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {data && data.orders.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-[13.5px] text-muted">
                    —
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

/* ================= Team ================= */
const TEAM_ROLES: Role[] = ['operator', 'admin', 'agency', 'runner', 'client']

function TeamView({
  accounts,
  onChanged,
}: {
  accounts: AdminAccount[] | null
  onChanged: () => void
}) {
  const t = useTranslations('Admin')
  const [editing, setEditing] = useState<AdminAccount | 'new' | null>(null)
  const [query, setQuery] = useState('')
  const [roleFilter, setRoleFilter] = useState<'all' | Role>('all')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const all = accounts ?? []

  const list = useMemo(() => {
    const q = query.trim().toLowerCase()
    return all.filter((a) => {
      if (roleFilter !== 'all' && a.role !== roleFilter) return false
      if (statusFilter === 'active' && !a.active) return false
      if (statusFilter === 'inactive' && a.active) return false
      if (q) {
        const hay = `${a.name} ${a.email || ''} ${a.telegram || ''} ${a.phone || ''}`.toLowerCase()
        if (!hay.includes(q)) return false
      }
      return true
    })
  }, [all, query, roleFilter, statusFilter])

  // Role chips carry a live count so the operator can see the team breakdown.
  const roleChips: { key: 'all' | Role; label: string; count: number }[] = [
    { key: 'all', label: t('segments.all'), count: all.length },
    ...TEAM_ROLES.map((r) => ({
      key: r,
      label: t(`roles.${r}`),
      count: all.filter((a) => a.role === r).length,
    })),
  ]

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-display text-[20px] text-ink">{t('menu.team')}</h2>
        <Button variant="dark" size="sm" className="gap-1.5" onClick={() => setEditing('new')}>
          <Plus size={15} /> {t('accounts.add')}
        </Button>
      </div>

      {/* Search + filters — so the team stays findable as it grows */}
      <div className="mb-4 flex flex-col gap-3">
        <div className="relative">
          <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-lt" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('accounts.search')}
            className="pl-9"
          />
        </div>
        <div className="nd-hscroll flex gap-1.5">
          {roleChips.map((c) => (
            <button
              key={c.key}
              onClick={() => setRoleFilter(c.key)}
              className={cn(
                'shrink-0 rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-colors',
                roleFilter === c.key ? 'bg-accent text-white' : 'bg-card text-muted hover:text-ink'
              )}
            >
              {c.label} <span className="opacity-60">{c.count}</span>
            </button>
          ))}
        </div>
        <div className="flex gap-1.5">
          {(['all', 'active', 'inactive'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={cn(
                'rounded-full px-3 py-1 text-[12.5px] font-medium transition-colors',
                statusFilter === s ? 'bg-inverse text-inverse-fg' : 'bg-card text-muted hover:text-ink'
              )}
            >
              {s === 'all' ? t('segments.all') : s === 'active' ? t('accounts.active') : t('accounts.inactive')}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-line bg-card">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left">
            <thead>
              <tr className="text-[11px] uppercase tracking-wide text-gray">
                <th className="px-5 py-2.5 font-semibold">{t('accounts.name')}</th>
                <th className="px-3 py-2.5 font-semibold">{t('accounts.role')}</th>
                <th className="px-3 py-2.5 font-semibold">{t('accounts.contact')}</th>
                <th className="px-3 py-2.5 font-semibold">{t('accounts.status')}</th>
                <th className="px-5 py-2.5 font-semibold"></th>
              </tr>
            </thead>
            <tbody>
              {list.map((a) => (
                <tr key={a.id} className="border-t border-line text-[13.5px]">
                  <td className="px-5 py-3">
                    <span className="flex items-center gap-2.5">
                      <Avatar url={a.photoUrl} name={a.name} size={30} />
                      <span className="font-medium text-ink">{a.name}</span>
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <RolePill role={a.role} />
                  </td>
                  <td className="px-3 py-3 text-muted">
                    {a.email || (a.telegram ? `@${a.telegram}` : '—')}
                  </td>
                  <td className="px-3 py-3">
                    <span
                      className={cn(
                        'rounded-full px-2 py-0.5 text-[11.5px] font-medium',
                        a.active ? 'bg-accent/15 text-accent' : 'bg-sub text-muted'
                      )}
                    >
                      {a.active ? t('accounts.active') : t('accounts.inactive')}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => setEditing(a)}
                      className="text-gray hover:text-ink"
                      aria-label="edit"
                    >
                      <Pencil size={15} />
                    </button>
                  </td>
                </tr>
              ))}
              {list.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-[13.5px] text-muted">
                    —
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {editing && (
        <AccountModal
          account={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            onChanged()
          }}
        />
      )}
    </div>
  )
}

function RolePill({ role }: { role: Role }) {
  const t = useTranslations('Admin')
  const tone: Record<string, string> = {
    admin: 'bg-inverse text-inverse-fg',
    operator: 'bg-accent/15 text-accent',
    agency: 'bg-amber-500/15 text-amber-700',
    runner: 'bg-sky-500/15 text-sky-700',
    client: 'bg-sub text-muted',
  }
  return (
    <span className={cn('rounded-full px-2 py-0.5 text-[11.5px] font-medium', tone[role] || tone.client)}>
      {t(`roles.${role}`)}
    </span>
  )
}

function AccountModal({
  account,
  fixedRole,
  onClose,
  onSaved,
}: {
  account: AdminAccount | null
  fixedRole?: Role
  onClose: () => void
  onSaved: () => void
}) {
  const t = useTranslations('Admin')
  const tc = useTranslations('Common')
  const isNew = !account
  const [name, setName] = useState(account?.name ?? '')
  const [role, setRole] = useState<Role>(fixedRole ?? account?.role ?? 'runner')
  const [email, setEmail] = useState(account?.email ?? '')
  const [phone, setPhone] = useState(account?.phone ?? '')
  const [telegram, setTelegram] = useState(account?.telegram ?? '')
  const [password, setPassword] = useState('')
  const [active, setActive] = useState(account?.active ?? true)
  const [photo, setPhoto] = useState<string | null>(account?.photoUrl ?? null)
  const [confirmDel, setConfirmDel] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  async function save() {
    if (!name.trim()) return
    setBusy(true)
    setErr('')
    try {
      if (isNew) {
        await api.admin.createAccount({
          name: name.trim(),
          role,
          email: email.trim() || undefined,
          password: password || undefined,
          phone: phone.trim() || undefined,
          telegram: telegram.trim() || undefined,
        })
      } else {
        await api.admin.updateAccount(account!.id, {
          name: name.trim(),
          role,
          email: email.trim(),
          active,
          password: password || undefined,
          phone: phone.trim(),
          telegram: telegram.trim(),
        })
      }
      onSaved()
    } catch (e: any) {
      setErr(e?.code === 'email_taken' ? t('accounts.emailTaken') : tc('error'))
      setBusy(false)
    }
  }

  async function onPhoto(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (!f || !account) return
    setBusy(true)
    try {
      const updated = await api.admin.uploadPhoto(account.id, f)
      setPhoto(updated.photoUrl)
    } catch {
      setErr(tc('error'))
    } finally {
      setBusy(false)
    }
  }

  async function del() {
    if (!account) return
    setBusy(true)
    try {
      await api.admin.deleteAccount(account.id)
      onSaved()
    } catch {
      setErr(tc('error'))
      setBusy(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-[99999] flex items-end justify-center bg-black/50 p-0 backdrop-blur-[2px] sm:items-center sm:p-6"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="max-h-[92vh] w-full max-w-[420px] overflow-y-auto rounded-t-2xl bg-surface sm:rounded-2xl"
      >
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <h2 className="font-display text-[18px] text-ink">
            {isNew ? t('accounts.newTitle') : t('accounts.editTitle')}
          </h2>
          <button onClick={onClose} className="text-gray hover:text-ink" aria-label="close">
            <X size={18} />
          </button>
        </div>

        <div className="flex flex-col gap-4 p-6">
          {/* Photo (existing accounts) */}
          {!isNew && (
            <div className="flex items-center gap-3">
              {photo ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={photo} alt="" className="h-16 w-16 rounded-full object-cover" referrerPolicy="no-referrer" />
              ) : (
                <span className="flex h-16 w-16 items-center justify-center rounded-full bg-accent text-[22px] font-semibold text-white">
                  {(name || '?').charAt(0).toUpperCase()}
                </span>
              )}
              <div>
                <input ref={fileRef} type="file" accept="image/*" onChange={onPhoto} className="hidden" />
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-1.5"
                  disabled={busy}
                  onClick={() => fileRef.current?.click()}
                >
                  <Camera size={15} /> {t('accounts.uploadPhoto')}
                </Button>
              </div>
            </div>
          )}

          <Field label={t('accounts.name')}>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="—" />
          </Field>

          {!fixedRole && (
            <label className="block">
              <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{t('accounts.role')}</span>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as Role)}
                className="w-full rounded-md border border-line bg-card px-3 py-3 text-[15px] text-ink"
              >
                {TEAM_ROLES.map((r) => (
                  <option key={r} value={r}>
                    {t(`roles.${r}`)}
                  </option>
                ))}
              </select>
            </label>
          )}

          <Field label={t('accounts.email')}>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@nothard.uz"
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label={t('accounts.phone')}>
              <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+998…" />
            </Field>
            <Field label={t('accounts.telegramUser')}>
              <Input value={telegram} onChange={(e) => setTelegram(e.target.value)} placeholder="@username" />
            </Field>
          </div>

          <Field label={isNew ? t('accounts.password') : t('accounts.newPassword')}>
            <Input
              type="text"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••"
            />
            <span className="mt-1.5 block text-[12px] text-gray">{t('accounts.passwordHint')}</span>
          </Field>

          {!isNew && (
            <label className="flex items-center justify-between rounded-lg border border-line bg-card px-3.5 py-3">
              <span className="text-[13.5px] font-medium text-ink">{t('accounts.activeLabel')}</span>
              <button
                onClick={() => setActive((v) => !v)}
                className={cn(
                  'relative h-6 w-11 rounded-full transition-colors',
                  active ? 'bg-accent' : 'bg-sub'
                )}
                aria-label="toggle active"
              >
                <span
                  className={cn(
                    'absolute top-0.5 h-5 w-5 rounded-full bg-card transition-transform',
                    active ? 'left-[22px]' : 'left-0.5'
                  )}
                />
              </button>
            </label>
          )}

          {err && <p className="text-[13px] text-terracotta">{err}</p>}

          <Button variant="solid" size="block" disabled={busy} onClick={save}>
            {isNew ? t('accounts.create') : t('accounts.save')}
          </Button>

          {/* Danger zone */}
          {!isNew &&
            (confirmDel ? (
              <div className="rounded-lg border border-terracotta/40 bg-terracotta-bg/50 p-3.5">
                <p className="text-[13px] text-ink">{t('accounts.deleteConfirm')}</p>
                <div className="mt-3 flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => setConfirmDel(false)}>
                    {tc('cancel')}
                  </Button>
                  <button
                    onClick={del}
                    disabled={busy}
                    className="rounded-md bg-terracotta px-3 py-1.5 text-[13px] font-medium text-white disabled:opacity-50"
                  >
                    {t('accounts.deleteCta')}
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setConfirmDel(true)}
                className="flex items-center justify-center gap-1.5 text-[13px] font-medium text-terracotta hover:underline"
              >
                <Trash2 size={14} /> {t('accounts.delete')}
              </button>
            ))}
        </div>
      </div>
    </div>
  )
}

/* ================= Shared cells ================= */
function Kpi({ value, label, tone }: { value: string; label: string; tone?: 'terracotta' | 'accent' }) {
  return (
    <div className="rounded-xl border border-line bg-card p-4">
      <div
        className={cn(
          'font-display text-[30px]',
          tone === 'terracotta' ? 'text-terracotta' : tone === 'accent' ? 'text-accent' : 'text-ink'
        )}
      >
        {value}
      </div>
      <div className="mt-1 text-[12.5px] text-muted">{label}</div>
    </div>
  )
}

function PkgName({ pkg }: { pkg: string | null }) {
  const t = useTranslations('Packages')
  if (!pkg) return <span className="text-gray-lt">—</span>
  return <>{t(`${pkg}.name` as any)}</>
}

function Avatar({ url, name, size = 40 }: { url?: string | null; name: string; size?: number }) {
  const [broken, setBroken] = useState(false)
  if (url && !broken)
    // eslint-disable-next-line @next/next/no-img-element
    return (
      <img
        src={url}
        alt={name}
        onError={() => setBroken(true)}
        style={{ width: size, height: size }}
        className="shrink-0 rounded-full object-cover"
        referrerPolicy="no-referrer"
      />
    )
  // No photo (or it failed to load, e.g. a Telegram photo that 404s) → a green
  // circle with the first letter of the name.
  return (
    <span
      style={{ width: size, height: size, fontSize: size * 0.4 }}
      className="flex shrink-0 items-center justify-center rounded-full bg-accent font-semibold text-white"
    >
      {(name || '?').trim().charAt(0).toUpperCase() || '?'}
    </span>
  )
}

function StepCell({ client }: { client: AdminClient }) {
  const t = useTranslations('Admin')
  const label = useTaskLabel()
  // Package finished — surface the current in-progress service (one at a time),
  // or a "done" state when there's nothing left.
  if (client.packageComplete || !client.stepTotal) {
    if (client.activeService)
      return (
        <span className="text-[12.5px] text-ink-2">
          <span className="mr-1 text-accent">•</span>
          {label('service', client.activeService).title}
        </span>
      )
    if (!client.stepTotal && !client.hasServices)
      return <span className="text-[12.5px] text-gray-lt">—</span>
    return <span className="text-[12.5px] font-medium text-accent">{t('relocationDone')}</span>
  }
  const idx = Math.min(Math.max(client.stepIndex, 0), client.stepTotal - 1)
  const pct = Math.round((client.stepIndex / client.stepTotal) * 100)
  const key = client.steps[idx]?.key
  return (
    <div className="min-w-[130px]">
      <div className="text-[12.5px] text-ink-2">{key ? label('step', key).title : '—'}</div>
      <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-track">
        <div className="h-full rounded-full bg-accent" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

/* ================= Reviews ================= */
function ReviewsView({ data }: { data: AdminReviews | null }) {
  const t = useTranslations('Admin')
  const tp = useTranslations('Packages')
  const ts = useTranslations('Services')
  return (
    <div>
      <div className="mb-5 flex items-center gap-4">
        <h2 className="font-display text-[20px] text-ink">{t('menu.reviews')}</h2>
        {data && data.count > 0 && (
          <span className="flex items-center gap-1.5 rounded-full bg-amber-400/15 px-3 py-1 text-[13px] font-semibold text-amber-700">
            <Star size={14} className="fill-amber-400 text-amber-400" />
            {data.avg} · {data.count}
          </span>
        )}
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {(data?.reviews ?? []).map((r) => (
          <div key={r.id} className="rounded-xl border border-line bg-card p-4">
            <div className="flex items-center justify-between">
              <span className="text-[14px] font-semibold text-ink">{r.clientName || '—'}</span>
              <span className="flex gap-0.5">
                {[1, 2, 3, 4, 5].map((n) => (
                  <Star
                    key={n}
                    size={14}
                    className={n <= r.stars ? 'fill-amber-400 text-amber-400' : 'text-gray-lt'}
                  />
                ))}
              </span>
            </div>
            <div className="mt-0.5 text-[12px] text-muted">
              {r.itemType === 'package'
                ? tp(`${r.itemId}.name` as any)
                : ts(`items.${r.itemId}.name` as any)}
            </div>
            {r.body && <p className="mt-2 text-[13.5px] leading-snug text-ink-2">“{r.body}”</p>}
          </div>
        ))}
        {data && data.reviews.length === 0 && <p className="text-[13.5px] text-muted">{t('reviewsEmpty')}</p>}
      </div>
    </div>
  )
}

/* ================= Listings moderation ================= */
type ListingSeg = 'all' | 'moderation' | 'published' | 'rejected'

function ListingsView({
  data,
  onChanged,
}: {
  data: AdminListings | null
  onChanged: () => void
}) {
  const t = useTranslations('Admin')
  const ts = useTranslations('Search')
  const { toast } = useToast()
  const [seg, setSeg] = useState<ListingSeg>('moderation')
  const [editing, setEditing] = useState<AdminListing | null>(null)
  const all = data?.listings ?? []

  const counts = useMemo(() => {
    const c = { all: all.length, moderation: 0, published: 0, rejected: 0 }
    for (const l of all) c[l.status]++
    return c
  }, [all])

  const list = useMemo(
    () => (seg === 'all' ? all : all.filter((l) => l.status === seg)),
    [all, seg]
  )

  async function setStatus(id: number, status: ListingStatus) {
    try {
      await api.admin.setListingStatus(id, status)
      onChanged()
      toast(t('saved'))
    } catch {}
  }
  async function del(id: number) {
    try {
      await api.admin.deleteListing(id)
      onChanged()
      toast(t('accounts.deleted'))
    } catch {}
  }

  const segs: { key: ListingSeg; label: string }[] = [
    { key: 'moderation', label: t('listingStatus.moderation') },
    { key: 'published', label: t('listingStatus.published') },
    { key: 'rejected', label: t('listingStatus.rejected') },
    { key: 'all', label: t('segments.all') },
  ]
  // Solid white pill (not translucent) so the status stays legible over bright
  // photos; only the text is colour-coded.
  const tone: Record<string, string> = {
    published: 'bg-white text-accent',
    moderation: 'bg-white text-amber-600',
    rejected: 'bg-white text-terracotta',
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-display text-[20px] text-ink">{t('menu.listings')}</h2>
      </div>
      <div className="nd-hscroll mb-4 flex gap-1.5">
        {segs.map((s) => (
          <button
            key={s.key}
            onClick={() => setSeg(s.key)}
            className={cn(
              'shrink-0 rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-colors',
              seg === s.key ? 'bg-accent text-white' : 'bg-card text-muted hover:text-ink'
            )}
          >
            {s.label} <span className="opacity-60">{counts[s.key]}</span>
          </button>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {list.map((l) => (
          <div key={l.id} className="overflow-hidden rounded-xl border border-line bg-card">
            <div className="relative h-[120px]">
              {l.photoUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={l.photoUrl} alt="" className="h-full w-full object-cover" />
              ) : (
                <div className="photo-stripe h-full w-full" />
              )}
              <span
                className={cn(
                  'absolute left-3 top-3 rounded-full px-2.5 py-1 text-[11px] font-semibold shadow-sm',
                  tone[l.status]
                )}
              >
                {t(`listingStatus.${l.status}`)}
              </span>
            </div>
            <div className="p-4">
              <div className="font-display text-[18px] text-ink">
                {fmtGBP(l.priceGBP)} <span className="text-[12.5px] font-normal text-gray">{ts('perMonth')}</span>
              </div>
              <div className="mt-0.5 text-[13.5px] text-ink-2">{l.addr}</div>
              <div className="mt-1 text-[12px] text-muted">
                {l.rooms === 0 ? ts('filters.roomsOpts.studio') : ts('meta.bed', { count: l.rooms })} ·{' '}
                {ts('meta.bath', { count: l.baths })} · {l.agency || '—'}
              </div>
              <div className="mt-3 flex flex-wrap gap-2 border-t border-line pt-3">
                {l.status !== 'published' && (
                  <button
                    onClick={() => setStatus(l.id, 'published')}
                    className="rounded-full border border-accent/40 px-3 py-1 text-[12px] font-medium text-accent hover:bg-accent-bg"
                  >
                    {t('listings.approve')}
                  </button>
                )}
                {l.status === 'published' && (
                  <button
                    onClick={() => setStatus(l.id, 'moderation')}
                    className="rounded-full border border-line px-3 py-1 text-[12px] font-medium text-muted hover:text-ink"
                  >
                    {t('listings.unpublish')}
                  </button>
                )}
                {l.status !== 'rejected' && (
                  <button
                    onClick={() => setStatus(l.id, 'rejected')}
                    className="rounded-full border border-terracotta/40 px-3 py-1 text-[12px] font-medium text-terracotta hover:bg-terracotta-bg"
                  >
                    {t('listings.reject')}
                  </button>
                )}
                <button
                  onClick={() => setEditing(l)}
                  className="rounded-full border border-line px-3 py-1 text-[12px] font-medium text-muted hover:text-ink"
                >
                  {t('listings.edit')}
                </button>
                <button
                  onClick={() => del(l.id)}
                  className="ml-auto text-gray-lt hover:text-terracotta"
                  aria-label="delete"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </div>
        ))}
        {data && list.length === 0 && <p className="text-[13.5px] text-muted">—</p>}
      </div>

      {editing && (
        <ListingModal
          listing={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            onChanged()
          }}
        />
      )}
    </div>
  )
}

const LISTING_AREAS = ['whitechapel', 'stratford', 'canadaWater', 'woolwich'] as const
const LISTING_TYPES = ['flat', 'studio', 'house', 'room'] as const

function ListingModal({
  listing,
  onClose,
  onSaved,
}: {
  listing: AdminListing
  onClose: () => void
  onSaved: () => void
}) {
  const t = useTranslations('Admin')
  const ts = useTranslations('Search')
  const ta = useTranslations('Agency')
  const tc = useTranslations('Common')
  const { toast } = useToast()
  const [form, setForm] = useState({
    price: String(listing.priceGBP),
    addr: listing.addr,
    area: listing.area,
    rooms: String(listing.rooms),
    baths: String(listing.baths),
    furnished: listing.furnished,
    propertyType: listing.propertyType || 'flat',
    description: listing.description ?? '',
    amenities: (listing.amenities ?? []).join(', '),
    availableFrom: listing.availableFrom ?? '',
    depositGBP: listing.depositGBP ? String(listing.depositGBP) : '',
  })
  const [photos, setPhotos] = useState<string[]>(
    listing.photos && listing.photos.length ? listing.photos : listing.photoUrl ? [listing.photoUrl] : []
  )
  const [busy, setBusy] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  async function save() {
    setBusy(true)
    try {
      await api.admin.updateListing(listing.id, {
        priceGBP: Number(form.price) || 0,
        addr: form.addr.trim(),
        area: form.area,
        rooms: Number(form.rooms) || 0,
        baths: Number(form.baths) || 1,
        furnished: form.furnished,
        propertyType: form.propertyType,
        description: form.description,
        amenities: form.amenities.split(',').map((s) => s.trim()).filter(Boolean),
        availableFrom: form.availableFrom,
        depositGBP: Number(form.depositGBP) || 0,
      })
      onSaved()
    } catch {
      setBusy(false)
    }
  }
  async function onPhoto(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f) return
    setBusy(true)
    try {
      const updated = await api.admin.uploadListingPhoto(listing.id, f)
      setPhotos(updated.photos && updated.photos.length ? updated.photos : updated.photoUrl ? [updated.photoUrl] : [])
      toast(t('saved'))
    } catch {
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-[99999] flex items-end justify-center bg-black/50 p-0 backdrop-blur-[2px] sm:items-center sm:p-6"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="max-h-[92vh] w-full max-w-[480px] overflow-y-auto rounded-t-2xl bg-surface sm:rounded-2xl"
      >
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <h2 className="font-display text-[18px] text-ink">{t('listings.editTitle')}</h2>
          <button onClick={onClose} className="text-gray hover:text-ink" aria-label="close">
            <X size={18} />
          </button>
        </div>

        <div className="flex flex-col gap-4 p-6">
          {/* Photos */}
          <div>
            <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{ta('photos')}</span>
            <div className="flex flex-wrap gap-2">
              {photos.map((p, i) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img key={p + i} src={p} alt="" className="h-16 w-16 rounded-lg object-cover" referrerPolicy="no-referrer" />
              ))}
              <button
                onClick={() => fileRef.current?.click()}
                disabled={busy}
                className="flex h-16 w-16 items-center justify-center rounded-lg border border-dashed border-line text-gray hover:text-accent"
              >
                <Camera size={17} />
              </button>
            </div>
            <input ref={fileRef} type="file" accept="image/*" onChange={onPhoto} className="hidden" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label={ta('form.price')}>
              <Input type="number" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
            </Field>
            <Field label={ta('form.deposit')}>
              <Input type="number" value={form.depositGBP} onChange={(e) => setForm({ ...form, depositGBP: e.target.value })} />
            </Field>
          </div>

          <Field label={ta('form.addr')}>
            <Input value={form.addr} onChange={(e) => setForm({ ...form, addr: e.target.value })} />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{ta('form.area')}</span>
              <select
                value={form.area}
                onChange={(e) => setForm({ ...form, area: e.target.value })}
                className="w-full rounded-md border border-line bg-card px-2.5 py-3 text-[14px] text-ink"
              >
                {LISTING_AREAS.map((a) => (
                  <option key={a} value={a}>{ts(`filters.areaOpts.${a}` as any)}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{ta('form.type')}</span>
              <select
                value={form.propertyType}
                onChange={(e) => setForm({ ...form, propertyType: e.target.value })}
                className="w-full rounded-md border border-line bg-card px-2.5 py-3 text-[14px] text-ink"
              >
                {LISTING_TYPES.map((tp) => (
                  <option key={tp} value={tp}>{ta(`types.${tp}` as any)}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Field label={ta('form.rooms')}>
              <Input type="number" min={0} value={form.rooms} onChange={(e) => setForm({ ...form, rooms: e.target.value })} />
            </Field>
            <Field label={ta('form.baths')}>
              <Input type="number" min={1} value={form.baths} onChange={(e) => setForm({ ...form, baths: e.target.value })} />
            </Field>
            <Field label={ta('form.availableFrom')}>
              <Input type="date" value={form.availableFrom} onChange={(e) => setForm({ ...form, availableFrom: e.target.value })} />
            </Field>
          </div>

          <label className="flex items-center gap-2.5 text-[14px] text-ink-2">
            <input
              type="checkbox"
              checked={form.furnished}
              onChange={(e) => setForm({ ...form, furnished: e.target.checked })}
              className="h-4 w-4 accent-[rgb(var(--accent))]"
            />
            {ta('form.furnished')}
          </label>

          <label className="block">
            <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{ta('form.description')}</span>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
              placeholder={ta('form.descriptionPlaceholder')}
              className="w-full rounded-md border border-line bg-card px-3 py-2.5 text-[14px] text-ink"
            />
          </label>

          <Field label={ta('form.amenities')}>
            <Input value={form.amenities} onChange={(e) => setForm({ ...form, amenities: e.target.value })} placeholder={ta('form.amenitiesPlaceholder')} />
          </Field>

          <Button variant="solid" size="block" disabled={busy} onClick={save}>
            {tc('save')}
          </Button>
        </div>
      </div>
    </div>
  )
}

function PaymentPill({ paid, paidLabel, unpaidLabel }: { paid: boolean; paidLabel: string; unpaidLabel: string }) {
  return (
    <span
      className={cn(
        'rounded-full px-2.5 py-1 text-[12px] font-medium',
        paid ? 'bg-accent/15 text-accent' : 'bg-terracotta-bg text-terracotta'
      )}
    >
      {paid ? paidLabel : unpaidLabel}
    </span>
  )
}

/* ================= Drawer ================= */
function Drawer({
  client,
  runners,
  managers,
  onClose,
  onChat,
  onAssignRunner,
  onAssignManager,
  onSetTaskStatus,
  onRename,
  onDelete,
  onHousingStatus,
  onUploadHousingMedia,
  onDeleteHousingMedia,
  onUploadAttachment,
  onUploadTaskAttachment,
  onDeleteAttachment,
  onSetPackage,
  onAddService,
  onDeleteOrder,
  onSetArrival,
}: {
  client: AdminClient
  runners: { id: number; name: string }[]
  managers: { id: number; name: string }[]
  onClose: () => void
  onChat: () => void
  onAssignRunner: (runnerId?: number | null) => void
  onAssignManager: (managerId?: number | null) => void
  onSetTaskStatus: (taskId: number, status: string) => void
  onRename: (name: string) => void
  onDelete: () => void
  onHousingStatus: (id: number, status: HousingStatus, opts?: { note?: string; viewingAt?: string }) => void
  onUploadHousingMedia: (id: number, file: File) => void
  onDeleteHousingMedia: (mediaId: number) => void
  onUploadAttachment: (orderId: number, file: File) => void
  onUploadTaskAttachment: (taskId: number, file: File) => void
  onDeleteAttachment: (id: number) => void
  onSetPackage: (packageId: string) => void
  onAddService: (serviceId: string) => void
  onDeleteOrder: (orderId: number) => void
  onSetArrival: (fields: Record<string, string>) => void
}) {
  const t = useTranslations('Admin')
  const tc = useTranslations('Common')
  const tpk = useTranslations('Packages')
  const ts = useTranslations('Services')
  const label = useTaskLabel()
  const [editingName, setEditingName] = useState(false)
  const [name, setName] = useState(client.name)
  const [confirmDel, setConfirmDel] = useState(false)

  type Row = {
    taskId: number | null
    kind: 'step' | 'service'
    key: string
    status: string
    paid?: boolean
    orderId?: number
  }
  const rows: Row[] = [
    ...client.steps.map((s) => ({ taskId: s.taskId, kind: 'step' as const, key: s.key, status: s.status })),
    ...client.services.map((s) => ({
      taskId: s.taskId,
      kind: 'service' as const,
      key: s.id,
      status: s.status,
      paid: s.paid,
      orderId: s.orderId,
    })),
  ]

  return (
    <div className="flex min-h-full flex-col p-6">
      <div className="flex items-start justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <Avatar url={client.photoUrl} name={client.name} size={48} />
          <div className="min-w-0">
            {editingName ? (
              <div className="flex items-center gap-2">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-[150px] rounded-md border border-line bg-card px-2 py-1 text-[15px] text-ink"
                  autoFocus
                />
                <button
                  onClick={() => {
                    if (name.trim() && name.trim() !== client.name) onRename(name.trim())
                    setEditingName(false)
                  }}
                  className="text-[12.5px] font-semibold text-accent"
                >
                  {t('accounts.save')}
                </button>
              </div>
            ) : (
              <button
                onClick={() => {
                  setName(client.name)
                  setEditingName(true)
                }}
                className="group flex items-center gap-1.5"
              >
                <span className="truncate font-display text-[20px] text-ink">{client.name}</span>
                <Pencil size={13} className="shrink-0 text-gray-lt group-hover:text-ink" />
              </button>
            )}
            <div className="flex items-center gap-2 text-[12.5px] text-muted">
              {client.package ? tpk(`${client.package}.name` as any) : '—'}
              {client.completed && (
                <span className="rounded-full bg-accent/15 px-1.5 py-0.5 text-[10.5px] font-semibold text-accent">
                  {t('relocationDone')}
                </span>
              )}
            </div>
          </div>
        </div>
        <button onClick={onClose} className="text-gray hover:text-ink" aria-label="close">
          <X size={18} />
        </button>
      </div>

      {(client.email || client.telegram || client.phone) && (
        <div className="mt-4 flex flex-col gap-1.5 rounded-lg border border-line bg-card p-3 text-[13px]">
          {client.telegram && (
            <a
              href={`https://t.me/${client.telegram}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex w-fit items-center gap-1.5 font-medium text-accent hover:underline"
            >
              @{client.telegram}
            </a>
          )}
          {client.email && <span className="break-all text-ink-2">{client.email}</span>}
          {client.phone && (
            <a href={`tel:${client.phone}`} className="w-fit text-ink-2 hover:text-accent">
              {client.phone}
            </a>
          )}
        </div>
      )}

      {/* Package management: change / upgrade / remove + add service */}
      <div className="mt-4 rounded-lg border border-line bg-card p-3">
        <div className="mb-2 text-[11px] uppercase tracking-wide text-gray">{t('manage.title')}</div>
        <label className="block">
          <span className="mb-1 block text-[12px] text-muted">{t('manage.package')}</span>
          <div className="flex gap-2">
            <select
              value={client.package || ''}
              onChange={(e) => e.target.value && onSetPackage(e.target.value)}
              className="min-w-0 flex-1 rounded-md border border-line bg-surface px-2.5 py-2 text-[13px] text-ink"
            >
              <option value="">{t('manage.noPackage')}</option>
              {PACKAGES.map((p) => (
                <option key={p.id} value={p.id}>
                  {tpk(`${p.id}.name` as any)} · {fmtGBP(p.gbp)}
                </option>
              ))}
            </select>
            {client.packageOrderId && (
              <button
                onClick={() => onDeleteOrder(client.packageOrderId!)}
                className="shrink-0 rounded-md border border-terracotta/40 px-2.5 text-[12px] font-medium text-terracotta hover:bg-terracotta-bg"
              >
                {t('manage.remove')}
              </button>
            )}
          </div>
        </label>

        <label className="mt-3 block">
          <span className="mb-1 block text-[12px] text-muted">{t('manage.addService')}</span>
          <select
            value=""
            onChange={(e) => e.target.value && onAddService(e.target.value)}
            className="w-full rounded-md border border-line bg-surface px-2.5 py-2 text-[13px] text-ink"
          >
            <option value="">{t('manage.pickService')}</option>
            {SERVICES.filter((s) => !client.services.some((cs) => cs.id === s.id && !cs.done)).map((s) => (
              <option key={s.id} value={s.id}>
                {ts(`items.${s.id}.name` as any)} · {fmtGBP(s.price)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Arrival details — editable */}
      {client.hasPackage && (
        <ArrivalRow details={client.packageDetails || {}} onSave={onSetArrival} />
      )}

      <div className="mt-4 grid grid-cols-2 gap-3">
        <Meta label={t('drawer.payment')}>
          <PaymentPill paid={client.paid} paidLabel={t('paid')} unpaidLabel={t('unpaid')} />
        </Meta>
        <Meta label={t('drawer.package')}>{fmtGBP(client.amount)}</Meta>
      </div>

      {/* Manager / runner assignment */}
      <div className="mt-4 flex flex-col gap-3">
        <label className="block">
          <span className="mb-1.5 block text-[11px] uppercase tracking-wide text-gray">{t('manager')}</span>
          <select
            value={client.managerId ?? ''}
            onChange={(e) => onAssignManager(e.target.value ? Number(e.target.value) : null)}
            className="w-full rounded-md border border-line bg-card px-3 py-2.5 text-[13.5px] text-ink"
          >
            <option value="">{t('managerNone')}</option>
            {managers.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="mb-1.5 block text-[11px] uppercase tracking-wide text-gray">{t('drawer.runner')}</span>
          <select
            value={client.runnerId ?? ''}
            onChange={(e) => onAssignRunner(e.target.value ? Number(e.target.value) : null)}
            className="w-full rounded-md border border-line bg-card px-3 py-2.5 text-[13.5px] text-ink"
          >
            <option value="">{t('noRunner')}</option>
            {runners.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {rows.length > 0 && (
        <div className="mt-6">
          <div className="eyebrow mb-3">{t('tasksTitle')}</div>
          <div className="flex flex-col gap-2">
            {rows.map((r, i) => {
              const done = r.status === 'done'
              return (
                <div
                  key={`${r.kind}-${r.key}-${i}`}
                  className="flex items-center justify-between gap-2 rounded-lg border border-line bg-card px-3 py-2"
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <span className={cn('h-2 w-2 shrink-0 rounded-full', done ? 'bg-accent' : 'bg-line')} />
                    <span className={cn('truncate text-[13px]', done ? 'text-ink-2' : 'text-ink')}>
                      {label(r.kind, r.key).title}
                    </span>
                  </span>
                  <span className="flex shrink-0 items-center gap-1.5">
                    {r.taskId != null && r.kind === 'step' ? (
                      // Parallel path: mark each step Pending / In progress / Done
                      // independently (several steps run at once).
                      <div className="flex overflow-hidden rounded-full border border-line">
                        {(['todo', 'inProgress', 'done'] as const).map((st) => {
                          const activeSt =
                            r.status === st ||
                            (st === 'inProgress' && (r.status === 'onWay' || r.status === 'arrived'))
                          return (
                            <button
                              key={st}
                              onClick={() => onSetTaskStatus(r.taskId!, st)}
                              className={cn(
                                'px-2 py-1 text-[11px] font-medium transition-colors',
                                activeSt
                                  ? st === 'done'
                                    ? 'bg-accent text-white'
                                    : st === 'inProgress'
                                      ? 'bg-amber-500/15 text-amber-700'
                                      : 'bg-line text-ink'
                                  : 'text-muted hover:text-ink'
                              )}
                            >
                              {t(`stepStatus.${st}` as any)}
                            </button>
                          )
                        })}
                      </div>
                    ) : r.taskId != null ? (
                      <button
                        onClick={() => onSetTaskStatus(r.taskId!, done ? 'todo' : 'done')}
                        className={cn(
                          'rounded-full border px-2.5 py-1 text-[11.5px] font-medium transition-colors',
                          done
                            ? 'border-line text-muted hover:text-ink'
                            : 'border-accent/40 text-accent hover:bg-accent-bg'
                        )}
                      >
                        {done ? t('reopen') : t('markDone')}
                      </button>
                    ) : null}
                    {r.kind === 'service' && r.orderId != null && (
                      <button
                        onClick={() => onDeleteOrder(r.orderId!)}
                        className="text-gray-lt hover:text-terracotta"
                        aria-label="remove service"
                      >
                        <Trash2 size={13} />
                      </button>
                    )}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Document files — for document steps (lease / bank / NHS) */}
      {client.steps.filter((s) => s.canUpload && s.taskId).length > 0 && (
        <div className="mt-6">
          <div className="eyebrow mb-3">{t('docFilesTitle')}</div>
          <div className="flex flex-col gap-2.5">
            {client.steps
              .filter((s) => s.canUpload && s.taskId)
              .map((s) => (
                <ServiceFilesRow
                  key={s.taskId}
                  title={label('step', s.key).title}
                  orderId={s.taskId!}
                  files={s.attachments}
                  onUpload={onUploadTaskAttachment}
                  onDelete={onDeleteAttachment}
                />
              ))}
          </div>
        </div>
      )}

      {/* Service files — operator uploads, client sees them (physical services excluded) */}
      {client.services.filter((s) => !NO_FILE_SERVICES.has(s.id)).length > 0 && (
        <div className="mt-6">
          <div className="eyebrow mb-3">{t('filesTitle')}</div>
          <div className="flex flex-col gap-2.5">
            {client.services
              .filter((s) => !NO_FILE_SERVICES.has(s.id))
              .map((s) => (
                <ServiceFilesRow
                  key={s.orderId}
                  title={ts(`items.${s.id}.name` as any)}
                  orderId={s.orderId}
                  files={s.attachments}
                  onUpload={onUploadAttachment}
                  onDelete={onDeleteAttachment}
                />
              ))}
          </div>
        </div>
      )}

      {/* Housing shortlist — status, viewing time, photos/videos */}
      {client.housing.length > 0 && (
        <div className="mt-6">
          <div className="eyebrow mb-3">{t('housingTitle')}</div>
          <div className="flex flex-col gap-3">
            {client.housing.map((h) => (
              <HousingRow
                key={h.id}
                h={h}
                onStatus={onHousingStatus}
                onUpload={onUploadHousingMedia}
                onDeleteMedia={onDeleteHousingMedia}
              />
            ))}
          </div>
        </div>
      )}

      {/* Purchase history — what was bought and when each part was completed.
          Kept for finished clients as a record. */}
      {client.history.length > 0 && (
        <div className="mt-6">
          <div className="eyebrow mb-3">{t('history.title')}</div>
          <div className="flex flex-col gap-2.5">
            {client.history.map((o, i) => {
              const title =
                o.type === 'package' ? tpk(`${o.id}.name` as any) : label('service', o.id).title
              return (
                <div key={i} className="rounded-lg border border-line bg-card p-3 text-[13px]">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="font-medium text-ink">{title}</div>
                      <div className="mt-0.5 text-[12px] text-muted">
                        {o.type === 'package' ? t('history.package') : t('history.service')} · {fmtGBP(o.amountGBP)}
                        {o.createdAt ? ` · ${t('history.bought')} ${fmtDateTime(o.createdAt)}` : ''}
                      </div>
                    </div>
                    <span
                      className={cn(
                        'shrink-0 rounded-full px-2 py-0.5 text-[10.5px] font-semibold',
                        o.status === 'done' ? 'bg-accent/15 text-accent' : 'bg-amber-500/15 text-amber-700'
                      )}
                    >
                      {o.status === 'done' ? t('history.done') : t('history.inProgress')}
                    </span>
                  </div>
                  {o.status === 'done' && o.completedAt && (
                    <div className="mt-1 text-[12px] text-accent">
                      {t('history.completed')} {fmtDateTime(o.completedAt)}
                    </div>
                  )}
                  {o.steps && o.steps.length > 0 && (
                    <ul className="mt-2 flex flex-col gap-1 border-t border-line pt-2">
                      {o.steps.map((s) => (
                        <li key={s.key} className="flex items-center justify-between gap-2 text-[12px]">
                          <span className="flex items-center gap-1.5 text-ink-2">
                            <span
                              className="h-1.5 w-1.5 rounded-full"
                              style={{ background: s.status === 'done' ? 'rgb(var(--accent))' : 'rgb(var(--line))' }}
                            />
                            {label('step', s.key).title}
                          </span>
                          <span className="text-gray">
                            {s.status === 'done'
                              ? s.completedAt
                                ? fmtDateTime(s.completedAt)
                                : t('history.done')
                              : t('history.inProgress')}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      <div className="mt-auto flex flex-col gap-2 pt-6">
        <Button variant="dark" size="block" onClick={onChat}>
          {t('drawer.writeClient')}
        </Button>
        {confirmDel ? (
          <div className="rounded-lg border border-terracotta/40 bg-terracotta-bg/50 p-3.5">
            <p className="text-[13px] text-ink">{t('deleteClientConfirm')}</p>
            <div className="mt-3 flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setConfirmDel(false)}>
                {tc('cancel')}
              </Button>
              <button
                onClick={onDelete}
                className="rounded-md bg-terracotta px-3 py-1.5 text-[13px] font-medium text-white"
              >
                {t('accounts.deleteCta')}
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setConfirmDel(true)}
            className="flex items-center justify-center gap-1.5 py-1 text-[13px] font-medium text-terracotta hover:underline"
          >
            <Trash2 size={14} /> {t('deleteClient')}
          </button>
        )}
      </div>
    </div>
  )
}

function Meta({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-card p-3">
      <div className="text-[11px] uppercase tracking-wide text-gray">{label}</div>
      <div className="mt-1 text-[13.5px] font-medium text-ink">{children}</div>
    </div>
  )
}

function fmtDMY(d?: string): string {
  if (!d) return ''
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d)
  return m ? `${m[3]}.${m[2]}.${m[1]}` : d
}

// DD.MM.YYYY HH:MM in the viewer's local time (backend sends UTC with a Z).
function fmtDateTime(iso?: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const p = (n: number) => String(n).padStart(2, '0')
  return `${p(d.getDate())}.${p(d.getMonth() + 1)}.${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}`
}

function ArrivalRow({
  details,
  onSave,
}: {
  details: Record<string, string>
  onSave: (fields: Record<string, string>) => void
}) {
  const t = useTranslations('Admin')
  const [editing, setEditing] = useState(false)
  const [date, setDate] = useState(details.arrivalDate || '')
  const [time, setTime] = useState(details.arrivalTime || '')
  const [airport, setAirport] = useState(details.airport || '')
  const [flight, setFlight] = useState(details.flight || '')

  if (!editing) {
    return (
      <div className="mt-4 rounded-lg border border-line bg-card p-3 text-[13px]">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-[11px] uppercase tracking-wide text-gray">{t('arrivalInfo')}</span>
          <button onClick={() => setEditing(true)} className="text-[12px] font-medium text-accent hover:underline">
            {t('manage.edit')}
          </button>
        </div>
        {details.arrivalDate || details.flight ? (
          <>
            {details.arrivalDate && (
              <div className="text-ink-2">
                ✈️ {fmtDMY(details.arrivalDate)} {details.arrivalTime}
                {details.airport ? ` · ${details.airport}` : ''}
              </div>
            )}
            {details.flight && <div className="text-ink-2">{t('flightNo')}: {details.flight}</div>}
          </>
        ) : (
          <div className="text-gray-lt">—</div>
        )}
      </div>
    )
  }

  return (
    <div className="mt-4 rounded-lg border border-accent/25 bg-card p-3">
      <div className="mb-2 text-[11px] uppercase tracking-wide text-gray">{t('arrivalInfo')}</div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="box-border w-full min-w-0 rounded-md border border-line bg-card px-2 py-1.5 text-[12.5px]" />
        <input type="time" value={time} onChange={(e) => setTime(e.target.value)} className="box-border w-full min-w-0 rounded-md border border-line bg-card px-2 py-1.5 text-[12.5px]" />
      </div>
      <select value={airport} onChange={(e) => setAirport(e.target.value)} className="mt-2 box-border w-full min-w-0 rounded-md border border-line bg-card px-2 py-1.5 text-[12.5px]">
        <option value="">{t('manage.airport')}</option>
        {LONDON_AIRPORT_TERMINALS.map((a) => (
          <option key={a} value={a}>{a}</option>
        ))}
      </select>
      <input value={flight} onChange={(e) => setFlight(e.target.value)} placeholder={t('flightNo')} list="nh-flights-admin" className="mt-2 box-border w-full min-w-0 rounded-md border border-line bg-card px-2 py-1.5 text-[12.5px]" />
      <datalist id="nh-flights-admin">
        {LONDON_FLIGHTS.map((f) => (
          <option key={f} value={f} />
        ))}
      </datalist>
      <div className="mt-2 flex gap-2">
        <button
          onClick={() => {
            onSave({ arrivalDate: date, arrivalTime: time, airport, flight: flight.trim() })
            setEditing(false)
          }}
          className="rounded-md bg-accent px-3 py-1.5 text-[12.5px] font-medium text-white"
        >
          {t('accounts.save')}
        </button>
        <button onClick={() => setEditing(false)} className="text-[12.5px] text-muted">
          {t('manage.cancel')}
        </button>
      </div>
    </div>
  )
}

const HOUSING_STATUSES_UI: HousingStatus[] = ['new', 'viewing', 'viewed', 'secured', 'completed', 'busy', 'declined']

function HousingRow({
  h,
  onStatus,
  onUpload,
  onDeleteMedia,
}: {
  h: HousingItem
  onStatus: (id: number, status: HousingStatus, opts?: { viewingAt?: string }) => void
  onUpload: (id: number, file: File) => void
  onDeleteMedia: (mediaId: number) => void
}) {
  const t = useTranslations('Admin')
  const fileRef = useRef<HTMLInputElement>(null)
  const [viewingAt, setViewingAt] = useState(h.viewingAt || '')

  return (
    <div className="rounded-lg border border-line bg-card p-3">
      <div className="flex gap-3">
        {h.photoUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={h.photoUrl} alt="" className="h-14 w-14 shrink-0 rounded-md object-cover" referrerPolicy="no-referrer" />
        ) : (
          <div className="photo-stripe h-14 w-14 shrink-0 rounded-md" />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <span className="min-w-0 truncate text-[13px] font-medium text-ink">
              {h.title || h.addr || h.ref}
            </span>
            {h.priceGBP > 0 && <span className="shrink-0 text-[12.5px] text-accent">{fmtGBP(h.priceGBP)}</span>}
          </div>
          {h.description && (
            <p className="line-clamp-2 text-[11.5px] leading-snug text-ink-2">{h.description}</p>
          )}
          {h.source === 'link' && (
            <a href={h.ref} target="_blank" rel="noreferrer" className="block truncate text-[11px] text-muted hover:text-accent">
              {h.ref}
            </a>
          )}
        </div>
      </div>

      <select
        value={h.status}
        onChange={(e) => onStatus(h.id, e.target.value as HousingStatus)}
        className="mt-2 w-full rounded-md border border-line bg-surface px-2.5 py-2 text-[12.5px] text-ink"
      >
        {HOUSING_STATUSES_UI.map((st) => (
          <option key={st} value={st}>
            {t(`housingStatus.${st}`)}
          </option>
        ))}
      </select>

      {h.status === 'viewing' && (
        <div className="mt-2 flex gap-2">
          <input
            type="datetime-local"
            value={viewingAt}
            onChange={(e) => setViewingAt(e.target.value)}
            className="min-w-0 flex-1 rounded-md border border-line bg-card px-2.5 py-2 text-[12.5px] text-ink"
          />
          <button
            onClick={() => onStatus(h.id, 'viewing', { viewingAt })}
            className="shrink-0 rounded-md border border-accent/40 px-2.5 py-1 text-[12px] font-medium text-accent hover:bg-accent-bg"
          >
            {t('housingViewingSave')}
          </button>
        </div>
      )}

      {/* Viewing photos/videos */}
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        {h.media.map((m) => (
          <div key={m.id} className="relative">
            {m.kind === 'video' ? (
              <video src={m.url} className="h-12 w-12 rounded object-cover" />
            ) : (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={m.url} alt="" className="h-12 w-12 rounded object-cover" />
            )}
            <button
              onClick={() => onDeleteMedia(m.id)}
              className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-inverse text-inverse-fg"
              aria-label="delete media"
            >
              <X size={9} />
            </button>
          </div>
        ))}
        <input
          ref={fileRef}
          type="file"
          accept="image/*,video/*"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) onUpload(h.id, f)
            e.target.value = ''
          }}
        />
        <button
          onClick={() => fileRef.current?.click()}
          className="flex h-12 w-12 items-center justify-center rounded border border-dashed border-line text-gray hover:border-accent hover:text-accent"
          aria-label="upload media"
        >
          <Plus size={16} />
        </button>
      </div>
    </div>
  )
}

function ServiceFilesRow({
  title,
  orderId,
  files,
  onUpload,
  onDelete,
}: {
  title: string
  orderId: number
  files: { id: number; filename: string; url: string }[]
  onUpload: (orderId: number, file: File) => void
  onDelete: (id: number) => void
}) {
  const t = useTranslations('Admin')
  const ref = useRef<HTMLInputElement>(null)
  return (
    <div className="rounded-lg border border-line bg-card p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="min-w-0 truncate text-[13px] font-medium text-ink">{title}</span>
        <input
          ref={ref}
          type="file"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) onUpload(orderId, f)
            e.target.value = ''
          }}
        />
        <button
          onClick={() => ref.current?.click()}
          className="flex shrink-0 items-center gap-1 rounded-full border border-accent/40 px-2.5 py-1 text-[11.5px] font-medium text-accent hover:bg-accent-bg"
        >
          <Paperclip size={12} /> {t('uploadFile')}
        </button>
      </div>
      {files.length > 0 && (
        <div className="mt-2 flex flex-col gap-1.5">
          {files.map((f) => (
            <div key={f.id} className="flex items-center justify-between gap-2 text-[12.5px]">
              <a
                href={f.url}
                target="_blank"
                rel="noreferrer"
                className="min-w-0 truncate text-accent hover:underline"
              >
                {f.filename}
              </a>
              <button
                onClick={() => onDelete(f.id)}
                className="shrink-0 text-gray-lt hover:text-terracotta"
                aria-label="delete file"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
