'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslations } from 'next-intl'
import { ArrowLeft, Check, Heart, Plus, X } from 'lucide-react'
import { Link, useRouter } from '@/i18n/navigation'
import { SiteNav } from '@/app/components/site-nav'
import { Footer } from '@/app/components/footer'
import { Button } from '@/app/components/button'
import { Input } from '@/app/components/field'
import { useToast } from '@/app/components/toast'
import { useAuth } from '@/app/lib/use-auth'
import { api, type CatalogListing } from '@/app/lib/api'
import { cart } from '@/app/lib/housing-cart'
import { SAMPLE_PROPERTIES, fmtGBP, type Property } from '@/app/lib/data'
import { cn } from '@/app/lib/utils'

type RoomsFilter = 'any' | 'studio' | 'one' | 'two' | 'three'
type PriceFilter = 'any' | 'lt1500' | '1500to2000' | 'gt2000'
type AreaFilter = 'any' | Property['area']

const ROOMS: RoomsFilter[] = ['any', 'studio', 'one', 'two', 'three']
const PRICES: PriceFilter[] = ['any', 'lt1500', '1500to2000', 'gt2000']
const AREAS: AreaFilter[] = ['any', 'whitechapel', 'stratford', 'canadaWater', 'woolwich']

type OG = { photo?: string; title?: string; description?: string; price?: number }
type LinkItem = { url: string; host: string; meta: OG | null; loading: boolean }

function hostOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

export default function SearchPage() {
  const t = useTranslations('Search')
  const tc = useTranslations('Common')
  const { toast } = useToast()
  const { user } = useAuth()
  const router = useRouter()
  const [submitting, setSubmitting] = useState(false)

  const [rooms, setRooms] = useState<RoomsFilter>('any')
  const [price, setPrice] = useState<PriceFilter>('any')
  const [area, setArea] = useState<AreaFilter>('any')
  const [fav, setFav] = useState<Set<number>>(new Set())
  const [shortlist, setShortlist] = useState<Set<number>>(new Set())
  const [linkItems, setLinkItems] = useState<LinkItem[]>([])
  const [linkInput, setLinkInput] = useState('')
  const [linkErr, setLinkErr] = useState('')
  const [listings, setListings] = useState<CatalogListing[] | null>(null)
  const fetching = useRef<Set<string>>(new Set())

  // Restore browser-saved selections once on mount.
  useEffect(() => {
    setFav(cart.getFav())
    setShortlist(new Set(cart.getShortlist().map((i) => i.id)))
    setLinkItems(cart.getLinks().map((url) => ({ url, host: hostOf(url), meta: null, loading: true })))
  }, [])

  // Real agency listings from the DB; falls back to the sample set until loaded / if empty.
  useEffect(() => {
    api.listings().then((r) => setListings(r.listings)).catch(() => setListings([]))
  }, [])

  const source: CatalogListing[] =
    listings && listings.length ? listings : (SAMPLE_PROPERTIES as unknown as CatalogListing[])

  // Persist selections so they survive a reload — and a sign-up (see profile flush).
  useEffect(() => {
    cart.setFav(fav)
  }, [fav])
  useEffect(() => {
    // Wait for real listings before persisting — otherwise the sample set (which
    // lacks real ids) would overwrite a restored shortlist with an empty one.
    if (listings === null) return
    cart.setShortlist(source.filter((p) => shortlist.has(p.id)).map((p) => ({ id: p.id, addr: p.addr, priceGBP: p.priceGBP })))
  }, [shortlist, source, listings])
  useEffect(() => {
    cart.setLinks(linkItems.map((i) => i.url))
  }, [linkItems])

  // Fetch the OpenGraph preview (photo / title / price) for any link that needs one.
  useEffect(() => {
    linkItems.forEach((it) => {
      if (!it.loading || fetching.current.has(it.url)) return
      fetching.current.add(it.url)
      api
        .ogPreview(it.url)
        .then((m) => {
          const has = m && (m.photo || m.title || m.price)
          setLinkItems((prev) => prev.map((x) => (x.url === it.url ? { ...x, meta: has ? m : null, loading: false } : x)))
        })
        .catch(() => setLinkItems((prev) => prev.map((x) => (x.url === it.url ? { ...x, meta: null, loading: false } : x))))
        .finally(() => fetching.current.delete(it.url))
    })
  }, [linkItems])

  const results = useMemo(
    () =>
      source.filter((p) => {
        if (rooms === 'studio' && p.rooms !== 0) return false
        if (rooms === 'one' && p.rooms !== 1) return false
        if (rooms === 'two' && p.rooms !== 2) return false
        if (rooms === 'three' && p.rooms < 3) return false
        if (price === 'lt1500' && p.priceGBP >= 1500) return false
        if (price === '1500to2000' && (p.priceGBP < 1500 || p.priceGBP > 2000)) return false
        if (price === 'gt2000' && p.priceGBP <= 2000) return false
        if (area !== 'any' && p.area !== area) return false
        return true
      }),
    [rooms, price, area, source]
  )

  function toggleFav(id: number) {
    setFav((s) => {
      const n = new Set(s)
      if (n.has(id)) {
        n.delete(id)
        toast(t('unfavToast'))
      } else {
        n.add(id)
        toast(t('favToast'))
      }
      return n
    })
  }

  function toggleShortlist(id: number) {
    setShortlist((s) => {
      const n = new Set(s)
      n.has(id) ? n.delete(id) : n.add(id)
      return n
    })
  }

  function addLink() {
    const raw = linkInput.trim()
    if (!raw) return
    const url = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`
    try {
      // eslint-disable-next-line no-new
      new URL(url)
    } catch {
      setLinkErr(t('linkInvalid'))
      return
    }
    if (linkItems.some((i) => i.url === url)) {
      setLinkErr(t('linkExists'))
      return
    }
    setLinkErr('')
    setLinkInput('')
    setLinkItems((prev) => [...prev, { url, host: hostOf(url), meta: null, loading: true }])
  }

  function removeLink(url: string) {
    setLinkItems((prev) => prev.filter((i) => i.url !== url))
  }

  const total = shortlist.size + linkItems.length

  // Submit everything (catalog shortlist + pasted links) to the cabinet. A guest
  // is sent to sign up first; the selection is replayed after they log in.
  async function submit() {
    if (total === 0 || submitting) return
    if (!user) {
      cart.setShortlist(source.filter((p) => shortlist.has(p.id)).map((p) => ({ id: p.id, addr: p.addr, priceGBP: p.priceGBP })))
      cart.setLinks(linkItems.map((i) => i.url))
      cart.markPending()
      router.push('/register')
      return
    }
    setSubmitting(true)
    try {
      for (const p of source.filter((x) => shortlist.has(x.id))) {
        await api.me.addHousing({ source: 'catalog', ref: `catalog:${p.id}`, title: p.addr, priceGBP: p.priceGBP, addr: p.addr })
      }
      for (const it of linkItems) {
        await api.me.addHousing({ source: 'link', ref: it.url, title: it.meta?.title || it.host })
      }
      cart.clear()
      toast(t('shortlistSubmitted'))
      router.push('/profile')
    } catch {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-paper">
      <SiteNav />
      <main className="mx-auto max-w-[1200px] px-5 py-10 sm:px-11">
        {user && (
          <Link
            href="/profile"
            className="mb-5 inline-flex items-center gap-1.5 text-[14px] font-medium text-muted transition-colors hover:text-accent"
          >
            <ArrowLeft size={16} /> {tc('toCabinet')}
          </Link>
        )}
        <h1 className="font-display text-[30px] text-ink sm:text-[38px]">{t('title')}</h1>

        {/* Filters */}
        <div className="mt-6 flex flex-col gap-3">
          <ChipRow label={t('filters.rooms')}>
            {ROOMS.map((r) => (
              <Chip key={r} on={rooms === r} onClick={() => setRooms(r)}>
                {t(`filters.roomsOpts.${r}`)}
              </Chip>
            ))}
          </ChipRow>
          <ChipRow label={t('filters.price')}>
            {PRICES.map((p) => (
              <Chip key={p} on={price === p} onClick={() => setPrice(p)}>
                {t(`filters.priceOpts.${p}`)}
              </Chip>
            ))}
          </ChipRow>
          <ChipRow label={t('filters.area')}>
            {AREAS.map((a) => (
              <Chip key={a} on={area === a} onClick={() => setArea(a)}>
                {t(`filters.areaOpts.${a}`)}
              </Chip>
            ))}
          </ChipRow>
        </div>

        <p className="mt-6 text-[14px] text-muted">{t('found', { count: results.length })}</p>

        {/* Cards */}
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {results.map((p) => (
            <div key={p.id} className="nd-lift overflow-hidden rounded-xl border border-line bg-card">
              <div className="relative h-[168px]">
                {(p as CatalogListing).photoUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={(p as CatalogListing).photoUrl!} alt="" className="h-full w-full object-cover" referrerPolicy="no-referrer" />
                ) : (
                  <div className="photo-stripe h-full w-full" />
                )}
                <button
                  onClick={() => toggleFav(p.id)}
                  aria-label="favourite"
                  className="nd-heart absolute right-3 top-3 text-[22px]"
                  style={{ color: fav.has(p.id) ? 'rgb(var(--terracotta))' : 'rgb(var(--gray-lt))' }}
                >
                  {fav.has(p.id) ? '♥' : '♡'}
                </button>
              </div>
              <div className="p-4">
                <div className="flex items-baseline gap-1.5">
                  <span className="font-display text-[19px] text-ink">{fmtGBP(p.priceGBP)}</span>
                  <span className="text-[13px] text-gray">{t('perMonth')}</span>
                </div>
                <div className="mt-1 text-[14px] text-ink-2">{p.addr}</div>
                <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[12.5px] text-muted">
                  <span>{p.rooms === 0 ? t('filters.roomsOpts.studio') : t('meta.bed', { count: p.rooms })}</span>
                  <span>· {t('meta.bath', { count: p.baths })}</span>
                  {p.furnished && <span>· {t('meta.furnished')}</span>}
                </div>
                <Button
                  variant={shortlist.has(p.id) ? 'solid' : 'outline'}
                  size="sm"
                  className="mt-4 w-full gap-1.5"
                  onClick={() => toggleShortlist(p.id)}
                >
                  {shortlist.has(p.id) ? (
                    <>
                      <Check size={15} /> {t('shortlisted')}
                    </>
                  ) : (
                    <>
                      <Heart size={15} /> {t('shortlist')}
                    </>
                  )}
                </Button>
              </div>
            </div>
          ))}
        </div>

        {/* No match — add your own links (with live previews) */}
        <div className="mt-14 grid gap-8 rounded-2xl bg-panel-dark p-7 text-white sm:p-9 lg:grid-cols-2">
          <div>
            <h2 className="font-display text-[24px] text-white">{t('noMatchTitle')}</h2>
            <p className="mt-3 max-w-[46ch] text-[14px] leading-relaxed text-white/70">{t('noMatchText')}</p>
            <div className="mt-4 flex gap-2">
              <Input
                value={linkInput}
                onChange={(e) => {
                  setLinkInput(e.target.value)
                  setLinkErr('')
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addLink()
                  }
                }}
                placeholder={t('linkPlaceholder')}
                className="min-w-0 flex-1 border-white/15 bg-white/5 text-white placeholder:text-white/35"
              />
              <Button variant="solid" size="md" className="shrink-0 gap-1.5" onClick={addLink}>
                <Plus size={16} /> {t('addLink')}
              </Button>
            </div>
            {linkErr && <p className="mt-2 text-[12.5px] text-[#e8a58f]">{linkErr}</p>}
            <p className="mt-3 text-[12.5px] text-white/60">{t('pricingNote')}</p>
          </div>

          <div className="rounded-xl bg-white/[.04] p-5">
            {linkItems.length === 0 ? (
              <>
                <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.1em] text-white/50">
                  {t('howItWorks')}
                </div>
                <ol className="flex flex-col gap-3">
                  {[0, 1, 2].map((i) => (
                    <li key={i} className="flex gap-3 text-[14px] text-white/80">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/10 text-[12px] text-white">
                        {i + 1}
                      </span>
                      {t(`howSteps.${i}`)}
                    </li>
                  ))}
                </ol>
              </>
            ) : (
              <div className="flex flex-col gap-2.5">
                <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.1em] text-white/50">
                  {t('yourLinks', { count: linkItems.length })}
                </div>
                {linkItems.map((it) => (
                  <LinkCard key={it.url} it={it} onRemove={() => removeLink(it.url)} perMonth={t('perMonth')} loadingLabel={tc('loading')} />
                ))}
              </div>
            )}
          </div>
        </div>
        {total > 0 && <div className="h-20" />}
      </main>

      {/* Sticky submit bar — the whole selection (shortlist + links) at once */}
      {total > 0 && (
        <div className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-surface/95 backdrop-blur-md">
          <div className="mx-auto flex max-w-[1200px] items-center justify-between gap-4 px-5 py-3.5 sm:px-11">
            <span className="text-[14px] font-medium text-ink">{t('selectionCount', { count: total })}</span>
            <Button variant="solid" size="md" onClick={submit} disabled={submitting}>
              {user ? t('submitSelection') : t('shortlistLogin')}
            </Button>
          </div>
        </div>
      )}

      <Footer />
    </div>
  )
}

function LinkCard({
  it,
  onRemove,
  perMonth,
  loadingLabel,
}: {
  it: LinkItem
  onRemove: () => void
  perMonth: string
  loadingLabel: string
}) {
  return (
    <div className="flex w-full gap-3 overflow-hidden rounded-lg bg-white/[.05] p-2.5">
      <div className="h-14 w-14 shrink-0 overflow-hidden rounded-md bg-white/10">
        {it.meta?.photo ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={it.meta.photo} alt="" className="h-full w-full object-cover" referrerPolicy="no-referrer" />
        ) : null}
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-[13.5px] font-medium text-white/90">
          {it.loading ? loadingLabel : it.meta?.title || it.host}
        </div>
        <div className="mt-0.5 flex min-w-0 items-center gap-2 text-[12px] text-white/55">
          <span className="min-w-0 truncate">{it.host}</span>
          {it.meta?.price ? (
            <span className="shrink-0 text-[#8fd0ad]">
              £{it.meta.price.toLocaleString()} {perMonth}
            </span>
          ) : null}
        </div>
      </div>
      <button onClick={onRemove} aria-label="remove" className="shrink-0 self-start text-white/40 hover:text-white">
        <X size={15} />
      </button>
    </div>
  )
}

function ChipRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="mr-1 w-16 shrink-0 text-[12px] font-semibold uppercase tracking-wide text-gray">
        {label}
      </span>
      <div className="nd-hscroll flex gap-2">{children}</div>
    </div>
  )
}

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'nd-chip shrink-0 rounded-full border px-3.5 py-1.5 text-[13px] font-medium',
        on ? 'border-accent bg-accent text-white' : 'border-line bg-card text-ink-2 hover:border-accent/50'
      )}
    >
      {children}
    </button>
  )
}
