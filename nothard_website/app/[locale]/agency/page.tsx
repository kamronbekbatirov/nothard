'use client'

import { useEffect, useMemo, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Plus, X } from 'lucide-react'
import { AppTopbar } from '@/app/components/app-topbar'
import { Button } from '@/app/components/button'
import { Field, Input } from '@/app/components/field'
import { useToast } from '@/app/components/toast'
import { PanelLoading } from '../runner/page'
import { useRequireRole } from '@/app/lib/use-require-role'
import { api, clearTokens, type AgencyData, type Listing } from '@/app/lib/api'
import { fmtGBP } from '@/app/lib/data'
import { cn } from '@/app/lib/utils'

type Tab = 'all' | 'published' | 'moderation'
const AREAS = ['whitechapel', 'stratford', 'canadaWater', 'woolwich'] as const

export default function AgencyPage() {
  const t = useTranslations('Agency')
  const ts = useTranslations('Search')
  const { toast } = useToast()
  const { ready, user } = useRequireRole(['agency'])
  const [data, setData] = useState<AgencyData | null>(null)
  const [tab, setTab] = useState<Tab>('all')
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    if (ready) api.agency.listings().then(setData).catch(() => {})
  }, [ready])

  const filtered = useMemo(() => {
    const list = data?.listings ?? []
    return tab === 'all' ? list : list.filter((l) => l.status === tab)
  }, [data, tab])

  if (!ready) return <PanelLoading />

  const kpis = data
    ? ([
        { key: 'published', value: data.kpis.published },
        { key: 'moderation', value: data.kpis.moderation, warn: true },
        { key: 'matches', value: data.kpis.matches },
        { key: 'views', value: data.kpis.views },
      ] as const)
    : []

  return (
    <div className="min-h-screen bg-paper">
      <AppTopbar
        badge={t('badge')}
        menu={[
          { label: t('menu.listings'), active: true },
          { label: t('menu.matches') },
          { label: t('menu.views') },
        ]}
        name={user?.name}
        avatarUrl={user?.photo_url}
        onLogout={() => {
          clearTokens()
          window.location.href = '/login'
        }}
        right={
          <Button variant="solid" size="sm" className="gap-1.5" onClick={() => setAdding(true)}>
            <Plus size={15} /> <span className="hidden sm:inline">{t('addVariant')}</span>
          </Button>
        }
      />

      <main className="mx-auto max-w-[1240px] px-5 py-8 sm:px-8">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {kpis.map((k) => (
            <div key={k.key} className="rounded-xl border border-line bg-card p-4">
              <div className={cn('font-display text-[30px]', (k as any).warn ? 'text-terracotta' : 'text-ink')}>
                {k.value}
              </div>
              <div className="mt-1 text-[12.5px] text-muted">{t(`kpi.${k.key}`)}</div>
            </div>
          ))}
        </div>

        <div className="mt-7 flex gap-2">
          {(['all', 'published', 'moderation'] as Tab[]).map((tb) => (
            <button
              key={tb}
              onClick={() => setTab(tb)}
              className={cn(
                'rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-colors',
                tab === tb ? 'bg-inverse text-inverse-fg' : 'bg-card text-muted hover:text-ink'
              )}
            >
              {t(`tabs.${tb}`)}
            </button>
          ))}
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((l) => (
            <div key={l.id} className="nd-lift overflow-hidden rounded-xl border border-line bg-card">
              <div className="photo-stripe relative h-[150px]">
                <span
                  className={cn(
                    'absolute left-3 top-3 rounded-full px-2.5 py-1 text-[11px] font-semibold text-white',
                    l.status === 'published' ? 'bg-accent' : 'bg-terracotta'
                  )}
                >
                  {t(`status.${l.status}`)}
                </span>
              </div>
              <div className="p-4">
                <div className="font-display text-[19px] text-ink">
                  {fmtGBP(l.priceGBP)} <span className="text-[13px] font-normal text-gray">{t('perMonth')}</span>
                </div>
                <div className="mt-1 text-[13.5px] text-ink-2">{l.addr}</div>
                {l.status === 'published' && (
                  <div className="mt-3 border-t border-line pt-3 text-[12.5px] text-accent">
                    {t('matchesClients', { count: l.matches })}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>

      {adding && (
        <AddListing
          onClose={() => setAdding(false)}
          onAdded={(l) => {
            setData((d) =>
              d
                ? {
                    ...d,
                    listings: [l, ...d.listings],
                    kpis: { ...d.kpis, moderation: d.kpis.moderation + 1 },
                  }
                : d
            )
            setAdding(false)
            toast(t('addVariant'))
          }}
          areaLabel={(a) => ts(`filters.areaOpts.${a}` as any)}
        />
      )}
    </div>
  )
}

function AddListing({
  onClose,
  onAdded,
  areaLabel,
}: {
  onClose: () => void
  onAdded: (l: Listing) => void
  areaLabel: (a: string) => string
}) {
  const t = useTranslations('Agency')
  const [form, setForm] = useState({ priceGBP: '', addr: '', area: 'whitechapel', rooms: '1', baths: '1', furnished: true })
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      const l = await api.agency.add({
        priceGBP: Number(form.priceGBP) || 0,
        addr: form.addr,
        area: form.area,
        rooms: Number(form.rooms) || 0,
        baths: Number(form.baths) || 1,
        furnished: form.furnished,
      })
      onAdded(l)
    } catch {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[99998] flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-6" onClick={onClose}>
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={submit}
        className="w-full max-w-[440px] overflow-hidden rounded-t-2xl bg-surface p-6 sm:rounded-2xl"
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-display text-[20px] text-ink">{t('addVariant')}</h3>
          <button type="button" onClick={onClose} className="text-gray hover:text-ink">
            <X size={18} />
          </button>
        </div>
        <div className="flex flex-col gap-3">
          <Field label="£ / мес">
            <Input type="number" required value={form.priceGBP} onChange={(e) => setForm({ ...form, priceGBP: e.target.value })} placeholder="1500" />
          </Field>
          <Field label="Адрес">
            <Input required value={form.addr} onChange={(e) => setForm({ ...form, addr: e.target.value })} placeholder="—" />
          </Field>
          <div className="grid grid-cols-3 gap-3">
            <label className="block">
              <span className="mb-1.5 block text-[13px] font-medium text-ink-2">Район</span>
              <select
                value={form.area}
                onChange={(e) => setForm({ ...form, area: e.target.value })}
                className="w-full rounded-md border border-line bg-card px-2.5 py-3 text-[14px] text-ink"
              >
                {AREAS.map((a) => (
                  <option key={a} value={a}>
                    {areaLabel(a)}
                  </option>
                ))}
              </select>
            </label>
            <Field label="Комн.">
              <Input type="number" min={0} value={form.rooms} onChange={(e) => setForm({ ...form, rooms: e.target.value })} />
            </Field>
            <Field label="С/у">
              <Input type="number" min={1} value={form.baths} onChange={(e) => setForm({ ...form, baths: e.target.value })} />
            </Field>
          </div>
        </div>
        <Button type="submit" variant="solid" size="block" className="mt-5" disabled={busy}>
          {t('addVariant')}
        </Button>
      </form>
    </div>
  )
}
