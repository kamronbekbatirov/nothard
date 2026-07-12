'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Eye, Heart, ImagePlus, Pencil, Plus, Trash2, X } from 'lucide-react'
import { AppTopbar } from '@/app/components/app-topbar'
import { Button } from '@/app/components/button'
import { Field, Input } from '@/app/components/field'
import { useToast } from '@/app/components/toast'
import { PanelLoading } from '../runner/page'
import { useRequireRole } from '@/app/lib/use-require-role'
import { api, clearTokens, type AgencyData, type AgencyMatch, type Listing, type ListingInput } from '@/app/lib/api'
import { fmtGBP } from '@/app/lib/data'
import { cn } from '@/app/lib/utils'

type Section = 'listings' | 'matches'
type StatusFilter = 'all' | 'published' | 'moderation'
const AREAS = ['whitechapel', 'stratford', 'canadaWater', 'woolwich'] as const
const TYPES = ['flat', 'studio', 'house', 'room'] as const

export default function AgencyPage() {
  const t = useTranslations('Agency')
  const ts = useTranslations('Search')
  const { toast } = useToast()
  const { ready, user } = useRequireRole(['agency'])
  const [data, setData] = useState<AgencyData | null>(null)
  const [matches, setMatches] = useState<{ matches: AgencyMatch[]; total: number } | null>(null)
  const [section, setSection] = useState<Section>('listings')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [editing, setEditing] = useState<Listing | 'new' | null>(null)

  const loadListings = () => api.agency.listings().then(setData).catch(() => {})
  const loadMatches = () => api.agency.matches().then(setMatches).catch(() => {})
  useEffect(() => {
    if (!ready) return
    loadListings()
    loadMatches()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready])

  const filtered = useMemo(() => {
    const list = data?.listings ?? []
    return statusFilter === 'all' ? list : list.filter((l) => l.status === statusFilter)
  }, [data, statusFilter])

  function upsert(l: Listing) {
    setData((d) => {
      if (!d) return d
      const exists = d.listings.some((x) => x.id === l.id)
      const listings = exists ? d.listings.map((x) => (x.id === l.id ? l : x)) : [l, ...d.listings]
      return { ...d, listings }
    })
  }
  function removeLocal(id: number) {
    setData((d) => (d ? { ...d, listings: d.listings.filter((l) => l.id !== id) } : d))
  }

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
          { label: t('menu.listings'), active: section === 'listings', onClick: () => setSection('listings') },
          { label: t('menu.matches'), active: section === 'matches', onClick: () => setSection('matches') },
        ]}
        name={user?.name}
        avatarUrl={user?.photo_url}
        onLogout={() => {
          clearTokens()
          window.location.href = '/login'
        }}
        right={
          <Button variant="solid" size="sm" className="gap-1.5" onClick={() => setEditing('new')}>
            <Plus size={15} /> <span className="hidden sm:inline">{t('addVariant')}</span>
          </Button>
        }
      />

      <main className="mx-auto max-w-[1240px] px-5 py-8 sm:px-8">
        {/* KPIs — always visible */}
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

        {section === 'listings' ? (
          <>
            <div className="mt-7 flex gap-2">
              {(['all', 'published', 'moderation'] as StatusFilter[]).map((tb) => (
                <button
                  key={tb}
                  onClick={() => setStatusFilter(tb)}
                  className={cn(
                    'rounded-full px-3.5 py-1.5 text-[13px] font-medium transition-colors',
                    statusFilter === tb ? 'bg-inverse text-inverse-fg' : 'bg-card text-muted hover:text-ink'
                  )}
                >
                  {t(`tabs.${tb}`)}
                </button>
              ))}
            </div>

            {filtered.length === 0 ? (
              <div className="mt-6 rounded-2xl border border-dashed border-line bg-surface p-10 text-center">
                <p className="text-[14px] text-muted">{t('empty')}</p>
              </div>
            ) : (
              <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {filtered.map((l) => (
                  <ListingCard
                    key={l.id}
                    l={l}
                    onEdit={() => setEditing(l)}
                    onDeleted={() => removeLocal(l.id)}
                  />
                ))}
              </div>
            )}
          </>
        ) : (
          <MatchesSection data={matches} />
        )}
      </main>

      {editing && (
        <ListingEditor
          listing={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={(l) => {
            upsert(l)
            setEditing(null)
            loadListings()
            toast(t('saved'))
          }}
          areaLabel={(a) => ts(`filters.areaOpts.${a}` as any)}
        />
      )}
    </div>
  )
}

function MatchesSection({ data }: { data: { matches: AgencyMatch[]; total: number } | null }) {
  const t = useTranslations('Agency')
  const ts = useTranslations('Search')
  const statusLabel = (s: string) =>
    s === 'viewing'
      ? t('statusViewing')
      : s === 'reached'
        ? t('statusReached')
        : s === 'secured' || s === 'completed'
          ? t('statusSecured')
          : t('statusNew')

  if (data && data.matches.length === 0) {
    return (
      <div className="mt-6 rounded-2xl border border-dashed border-line bg-surface p-10 text-center">
        <Heart size={22} className="mx-auto text-gray-lt" />
        <p className="mx-auto mt-2 max-w-[46ch] text-[14px] leading-relaxed text-muted">{t('matchesEmpty')}</p>
      </div>
    )
  }

  return (
    <div className="mt-7">
      <div className="eyebrow mb-3">{t('matchesTitle')}</div>
      <div className="flex flex-col gap-4">
        {data?.matches.map((m) => (
          <div key={m.listing.id} className="overflow-hidden rounded-2xl border border-line bg-card">
            <div className="flex items-center gap-3 border-b border-line p-4">
              <div className="h-12 w-16 shrink-0 overflow-hidden rounded-lg bg-track">
                {m.listing.photoUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={m.listing.photoUrl} alt="" className="h-full w-full object-cover" referrerPolicy="no-referrer" />
                ) : (
                  <div className="photo-stripe h-full w-full" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="font-display text-[17px] text-ink">
                  {fmtGBP(m.listing.priceGBP)} <span className="text-[12.5px] font-normal text-gray">{ts('perMonth')}</span>
                </div>
                <div className="truncate text-[13px] text-ink-2">{m.listing.addr}</div>
              </div>
              <span className="shrink-0 rounded-full bg-accent-bg px-2.5 py-1 text-[12px] font-semibold text-accent">
                {t('interested', { count: m.clients.length })}
              </span>
            </div>
            <div className="flex flex-wrap gap-2 p-4">
              {m.clients.map((c, i) => (
                <span key={i} className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1.5 text-[13px]">
                  <span className="font-medium text-ink">{c.name}</span>
                  <span className="text-gray-lt">·</span>
                  <span className="text-muted">{statusLabel(c.status)}</span>
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ListingCard({ l, onEdit, onDeleted }: { l: Listing; onEdit: () => void; onDeleted: () => void }) {
  const t = useTranslations('Agency')
  const { toast } = useToast()
  const [confirm, setConfirm] = useState(false)
  const [busy, setBusy] = useState(false)

  async function del() {
    setBusy(true)
    try {
      await api.agency.remove(l.id)
      toast(t('deleted'))
      onDeleted()
    } catch {
      setBusy(false)
    }
  }

  const badge =
    l.status === 'published' ? 'bg-accent' : l.status === 'rejected' ? 'bg-terracotta' : 'bg-amber-500'

  return (
    <div className="nd-lift overflow-hidden rounded-xl border border-line bg-card">
      <div className="relative h-[150px]">
        {l.photoUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={l.photoUrl} alt="" className="h-full w-full object-cover" referrerPolicy="no-referrer" />
        ) : (
          <div className="photo-stripe h-full w-full" />
        )}
        <span className={cn('absolute left-3 top-3 rounded-full px-2.5 py-1 text-[11px] font-semibold text-white', badge)}>
          {t(`status.${l.status}` as any)}
        </span>
        {(l.photos?.length ?? 0) > 1 && (
          <span className="absolute right-3 top-3 rounded-full bg-black/55 px-2 py-0.5 text-[11px] font-medium text-white">
            {l.photos!.length} {t('photos').toLowerCase()}
          </span>
        )}
      </div>
      <div className="p-4">
        <div className="font-display text-[19px] text-ink">
          {fmtGBP(l.priceGBP)} <span className="text-[13px] font-normal text-gray">{t('perMonth')}</span>
        </div>
        <div className="mt-1 truncate text-[13.5px] text-ink-2">{l.addr}</div>
        {l.status === 'published' && (
          <div className="mt-3 flex items-center gap-4 border-t border-line pt-3 text-[12.5px]">
            <span className="inline-flex items-center gap-1.5 text-muted">
              <Eye size={14} /> {l.views ?? 0} {t('views').toLowerCase()}
            </span>
            <span className="inline-flex items-center gap-1.5 text-accent">
              <Heart size={14} /> {l.matches} {t('matchesShort').toLowerCase()}
            </span>
          </div>
        )}

        {confirm ? (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-[12.5px] text-muted">{t('confirmDelete')}</span>
            <Button variant="danger" size="sm" className="ml-auto" disabled={busy} onClick={del}>
              {t('delete')}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setConfirm(false)}>
              {t('cancel')}
            </Button>
          </div>
        ) : (
          <div className="mt-3 flex gap-2">
            <Button variant="outline" size="sm" className="flex-1 gap-1.5" onClick={onEdit}>
              <Pencil size={13} /> {t('edit')}
            </Button>
            <Button variant="ghost" size="sm" className="text-gray hover:text-terracotta" onClick={() => setConfirm(true)}>
              <Trash2 size={14} />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

function ListingEditor({
  listing,
  onClose,
  onSaved,
  areaLabel,
}: {
  listing: Listing | null
  onClose: () => void
  onSaved: (l: Listing) => void
  areaLabel: (a: string) => string
}) {
  const t = useTranslations('Agency')
  const { toast } = useToast()
  const fileRef = useRef<HTMLInputElement>(null)
  const isEdit = !!listing

  const [form, setForm] = useState({
    priceGBP: listing ? String(listing.priceGBP) : '',
    addr: listing?.addr ?? '',
    area: listing?.area || 'whitechapel',
    rooms: listing ? String(listing.rooms) : '1',
    baths: listing ? String(listing.baths) : '1',
    furnished: listing?.furnished ?? true,
    propertyType: listing?.propertyType || 'flat',
    description: listing?.description ?? '',
    amenities: (listing?.amenities ?? []).join(', '),
    availableFrom: listing?.availableFrom ?? '',
    depositGBP: listing?.depositGBP ? String(listing.depositGBP) : '',
  })
  // Photos are only editable once a listing exists (needs an id to upload to).
  const [photos, setPhotos] = useState<string[]>(listing?.photos ?? [])
  const [saved, setSaved] = useState<Listing | null>(listing)
  const [busy, setBusy] = useState(false)

  function payload(): ListingInput {
    return {
      priceGBP: Number(form.priceGBP) || 0,
      addr: form.addr,
      area: form.area,
      rooms: Number(form.rooms) || 0,
      baths: Number(form.baths) || 1,
      furnished: form.furnished,
      propertyType: form.propertyType,
      description: form.description,
      amenities: form.amenities.split(',').map((s) => s.trim()).filter(Boolean),
      availableFrom: form.availableFrom,
      depositGBP: Number(form.depositGBP) || 0,
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      const l = isEdit ? await api.agency.update(listing!.id, payload()) : await api.agency.add(payload())
      onSaved(l)
    } catch {
      setBusy(false)
    }
  }

  // Photo upload needs a listing id. For a brand-new listing, create it first
  // (as a draft) on the first upload, then keep appending photos to it.
  async function uploadPhoto(file: File) {
    setBusy(true)
    try {
      let target = saved
      if (!target) {
        target = await api.agency.add(payload())
        setSaved(target)
      }
      const updated = await api.agency.uploadPhoto(target.id, file)
      setSaved(updated)
      setPhotos(updated.photos ?? [])
      toast(t('saved'))
    } catch {
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[99998] flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-6" onClick={onClose}>
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={submit}
        className="max-h-[92vh] w-full max-w-[520px] overflow-y-auto rounded-t-2xl bg-surface p-6 sm:rounded-2xl"
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-display text-[20px] text-ink">{isEdit ? t('editListing') : t('addVariant')}</h3>
          <button type="button" onClick={onClose} className="text-gray hover:text-ink">
            <X size={18} />
          </button>
        </div>

        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-3">
            <Field label={t('form.price')}>
              <Input type="number" required value={form.priceGBP} onChange={(e) => setForm({ ...form, priceGBP: e.target.value })} placeholder="1500" />
            </Field>
            <Field label={t('form.deposit')}>
              <Input type="number" value={form.depositGBP} onChange={(e) => setForm({ ...form, depositGBP: e.target.value })} placeholder="2250" />
            </Field>
          </div>

          <Field label={t('form.addr')}>
            <Input required value={form.addr} onChange={(e) => setForm({ ...form, addr: e.target.value })} placeholder="—" />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <SelectField label={t('form.area')} value={form.area} onChange={(v) => setForm({ ...form, area: v })}>
              {AREAS.map((a) => (
                <option key={a} value={a}>{areaLabel(a)}</option>
              ))}
            </SelectField>
            <SelectField label={t('form.type')} value={form.propertyType} onChange={(v) => setForm({ ...form, propertyType: v })}>
              {TYPES.map((tp) => (
                <option key={tp} value={tp}>{t(`types.${tp}` as any)}</option>
              ))}
            </SelectField>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Field label={t('form.rooms')}>
              <Input type="number" min={0} value={form.rooms} onChange={(e) => setForm({ ...form, rooms: e.target.value })} />
            </Field>
            <Field label={t('form.baths')}>
              <Input type="number" min={1} value={form.baths} onChange={(e) => setForm({ ...form, baths: e.target.value })} />
            </Field>
            <Field label={t('form.availableFrom')}>
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
            {t('form.furnished')}
          </label>

          <label className="block">
            <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{t('form.description')}</span>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3}
              placeholder={t('form.descriptionPlaceholder')}
              className="w-full rounded-md border border-line bg-card px-3 py-2.5 text-[14px] text-ink"
            />
          </label>

          <Field label={t('form.amenities')}>
            <Input value={form.amenities} onChange={(e) => setForm({ ...form, amenities: e.target.value })} placeholder={t('form.amenitiesPlaceholder')} />
          </Field>

          {/* Photos */}
          <div>
            <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{t('photos')}</span>
            <div className="flex flex-wrap gap-2">
              {photos.map((p, i) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img key={p + i} src={p} alt="" className="h-16 w-16 rounded-lg object-cover" referrerPolicy="no-referrer" />
              ))}
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                disabled={busy}
                className="flex h-16 w-16 items-center justify-center rounded-lg border border-dashed border-line text-gray hover:text-accent"
              >
                <ImagePlus size={18} />
              </button>
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) uploadPhoto(f)
                e.target.value = ''
              }}
            />
          </div>
        </div>

        <Button type="submit" variant="solid" size="block" className="mt-5" disabled={busy}>
          {isEdit ? t('save') : t('addVariant')}
        </Button>
      </form>
    </div>
  )
}

function SelectField({
  label,
  value,
  onChange,
  children,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  children: React.ReactNode
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-line bg-card px-2.5 py-3 text-[14px] text-ink"
      >
        {children}
      </select>
    </label>
  )
}
