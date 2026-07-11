'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { ArrowLeft, Check, Heart } from 'lucide-react'
import { Link } from '@/i18n/navigation'
import { SiteNav } from '@/app/components/site-nav'
import { Footer } from '@/app/components/footer'
import { Button } from '@/app/components/button'
import { useToast } from '@/app/components/toast'
import { api, type ListingDetail } from '@/app/lib/api'
import { cart, type ShortlistItem } from '@/app/lib/housing-cart'
import { fmtGBP } from '@/app/lib/data'
import { cn } from '@/app/lib/utils'

export default function ListingDetailPage() {
  const params = useParams<{ id: string }>()
  const id = Number(params?.id)
  const t = useTranslations('Search')
  const tc = useTranslations('Common')
  const { toast } = useToast()

  const [listing, setListing] = useState<ListingDetail | null>(null)
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [active, setActive] = useState(0)
  const [fav, setFav] = useState(false)
  const [shortlisted, setShortlisted] = useState(false)

  useEffect(() => {
    if (!Number.isFinite(id)) {
      setState('error')
      return
    }
    api
      .listingDetail(id)
      .then((l) => {
        setListing(l)
        setState('ready')
      })
      .catch(() => setState('error'))
  }, [id])

  useEffect(() => {
    setFav(cart.getFav().has(id))
    setShortlisted(cart.getShortlist().some((s) => s.id === id))
  }, [id])

  function toggleFav() {
    const s = cart.getFav()
    if (s.has(id)) {
      s.delete(id)
      toast(t('unfavToast'))
    } else {
      s.add(id)
      toast(t('favToast'))
    }
    cart.setFav(s)
    setFav(s.has(id))
  }

  function toggleShortlist() {
    if (!listing) return
    const list = cart.getShortlist()
    const has = list.some((s) => s.id === id)
    let next: ShortlistItem[]
    if (has) {
      next = list.filter((s) => s.id !== id)
    } else {
      next = [...list, { id, addr: listing.addr, priceGBP: listing.priceGBP }]
    }
    cart.setShortlist(next)
    cart.markPending()
    setShortlisted(!has)
  }

  return (
    <div className="min-h-screen bg-paper">
      <SiteNav />
      <main className="mx-auto max-w-[1000px] px-5 py-10 sm:px-11">
        <Link
          href="/search"
          className="mb-5 inline-flex items-center gap-1.5 text-[14px] font-medium text-muted transition-colors hover:text-accent"
        >
          <ArrowLeft size={16} /> {t('back')}
        </Link>

        {state === 'loading' && (
          <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
            <div className="h-[340px] animate-pulse rounded-2xl bg-track" />
            <div className="h-[340px] animate-pulse rounded-2xl bg-track" />
          </div>
        )}

        {state === 'error' && (
          <div className="rounded-2xl border border-line bg-card p-10 text-center">
            <p className="text-[15px] text-muted">{t('detail.notFound')}</p>
            <Button asChild variant="outline" size="md" className="mt-5">
              <Link href="/search">{t('back')}</Link>
            </Button>
          </div>
        )}

        {state === 'ready' && listing && (
          <div className="grid gap-8 lg:grid-cols-[1.4fr_1fr]">
            {/* Gallery */}
            <div>
              <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-track">
                {listing.photos.length > 0 ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={listing.photos[active]}
                    alt={listing.addr}
                    className="h-full w-full object-cover"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <div className="photo-stripe h-full w-full" />
                )}
                <button
                  onClick={toggleFav}
                  aria-label="favourite"
                  className="nd-heart absolute right-4 top-4 text-[26px]"
                  style={{ color: fav ? 'rgb(var(--terracotta))' : 'rgb(var(--gray-lt))' }}
                >
                  {fav ? '♥' : '♡'}
                </button>
              </div>
              {listing.photos.length > 1 && (
                <div className="mt-3 grid grid-cols-4 gap-2.5 sm:grid-cols-5">
                  {listing.photos.map((p, i) => (
                    <button
                      key={p + i}
                      onClick={() => setActive(i)}
                      className={cn(
                        'aspect-square overflow-hidden rounded-lg border-2 transition',
                        i === active ? 'border-accent' : 'border-transparent opacity-80 hover:opacity-100'
                      )}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={p} alt="" className="h-full w-full object-cover" referrerPolicy="no-referrer" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Summary + actions */}
            <div className="lg:sticky lg:top-24 lg:self-start">
              <div className="flex items-baseline gap-2">
                <span className="font-display text-[30px] text-ink">{fmtGBP(listing.priceGBP)}</span>
                <span className="text-[14px] text-gray">{t('perMonth')}</span>
              </div>
              <div className="mt-1 text-[16px] text-ink-2">{listing.addr}</div>

              <div className="mt-4 flex flex-wrap gap-2">
                <Facet>{t(`types.${listing.propertyType || 'flat'}` as any)}</Facet>
                <Facet>
                  {listing.rooms === 0 ? t('filters.roomsOpts.studio') : t('meta.bed', { count: listing.rooms })}
                </Facet>
                <Facet>{t('meta.bath', { count: listing.baths })}</Facet>
                <Facet>{listing.furnished ? t('detail.furnishedYes') : t('detail.furnishedNo')}</Facet>
              </div>

              {/* Key facts */}
              <dl className="mt-5 divide-y divide-line rounded-xl border border-line bg-card text-[13.5px]">
                {listing.availableFrom && (
                  <FactRow label={t('detail.availableFrom')} value={fmtDate(listing.availableFrom)} />
                )}
                {listing.depositGBP > 0 && (
                  <FactRow label={t('detail.deposit')} value={fmtGBP(listing.depositGBP)} />
                )}
                <FactRow label={t('detail.type')} value={t(`types.${listing.propertyType || 'flat'}` as any)} />
              </dl>

              <div className="mt-5 flex flex-col gap-2.5">
                <Button
                  variant={shortlisted ? 'solid' : 'outline'}
                  size="block"
                  className="gap-1.5"
                  onClick={toggleShortlist}
                >
                  {shortlisted ? (
                    <>
                      <Check size={16} /> {t('detail.inShortlist')}
                    </>
                  ) : (
                    <>
                      <Heart size={16} /> {t('detail.addShortlist')}
                    </>
                  )}
                </Button>
                <p className="text-[12.5px] leading-relaxed text-muted">{t('detail.viewingNote')}</p>
              </div>
            </div>

            {/* Description */}
            {listing.description && (
              <section className="lg:col-span-2">
                <h2 className="font-display text-[20px] text-ink">{t('detail.about')}</h2>
                <p className="mt-2 max-w-[70ch] text-[14.5px] leading-relaxed text-ink-2">{listing.description}</p>
              </section>
            )}

            {/* Amenities */}
            {listing.amenities.length > 0 && (
              <section className="lg:col-span-2">
                <h2 className="font-display text-[20px] text-ink">{t('detail.amenities')}</h2>
                <div className="mt-3 flex flex-wrap gap-2">
                  {listing.amenities.map((a) => (
                    <span
                      key={a}
                      className="rounded-full border border-line bg-card px-3 py-1.5 text-[13px] text-ink-2"
                    >
                      {hasAmenLabel(a) ? t(`amen.${a}` as any) : a}
                    </span>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </main>
      <Footer />
    </div>
  )
}

// Amenity slugs we ship labels for; unknown slugs render verbatim.
const AMEN_KEYS = new Set(['wifi', 'washer', 'dishwasher', 'heating', 'lift', 'parking', 'balcony', 'furnished'])
function hasAmenLabel(a: string) {
  return AMEN_KEYS.has(a)
}

function fmtDate(iso: string) {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
}

function Facet({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full bg-accent-bg px-3 py-1 text-[12.5px] font-medium text-accent">{children}</span>
  )
}

function FactRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between px-4 py-3">
      <dt className="text-muted">{label}</dt>
      <dd className="font-medium text-ink">{value}</dd>
    </div>
  )
}
