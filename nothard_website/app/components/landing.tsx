'use client'

import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { ArrowRight } from 'lucide-react'
import { Link, useRouter } from '@/i18n/navigation'
import { Button } from './button'
import { SiteNav, dashHref } from './site-nav'
import { Footer } from './footer'
import { TelegramIcon } from './field'
import { useToast } from './toast'
import { useAuth } from '@/app/lib/use-auth'
import { useTelegramChrome, loginWithTelegram, resumeTelegramSession } from '@/app/lib/telegram'
import { api, type CatalogListing } from '@/app/lib/api'
import {
  PACKAGES,
  HOW_STEPS,
  TEASER_SERVICE_IDS,
  SAMPLE_PROPERTIES,
  serviceById,
  fmtGBP,
  fmtUSD,
  fmtUZS,
} from '@/app/lib/data'
import { cn } from '@/app/lib/utils'

export default function Landing() {
  const t = useTranslations('Landing')
  const tp = useTranslations('Packages')
  const ts = useTranslations('Services')
  const tsr = useTranslations('Search')
  const tprof = useTranslations('Profile')
  const ta = useTranslations('Auth')
  const router = useRouter()
  const { toast } = useToast()
  const { user } = useAuth()
  const { inTelegram } = useTelegramChrome()
  const [buying, setBuying] = useState<string | null>(null)
  const [tgBusy, setTgBusy] = useState(false)
  // Avoid a hydration mismatch: Telegram-only UI is decided after mount.
  const [mounted, setMounted] = useState(false)
  const [tgResuming, setTgResuming] = useState(false)
  useEffect(() => setMounted(true), [])

  // Real housing listings (with photos) for the catalog teaser; fall back to the
  // static samples until they load or if there are none.
  const [listings, setListings] = useState<CatalogListing[] | null>(null)
  useEffect(() => {
    api.listings().then((r) => setListings(r.listings)).catch(() => setListings([]))
  }, [])
  const catalog: CatalogListing[] =
    listings && listings.length
      ? listings
      : (SAMPLE_PROPERTIES as unknown as CatalogListing[])

  // Inside the Mini App, silently resume a RETURNING (already registered) user
  // straight into their cabinet — but ONLY on a cold open. If the user navigated
  // to the landing themselves (e.g. tapped the logo from the cabinet), don't
  // bounce them back; let them see the landing. A per-session flag distinguishes
  // the cold open from in-app navigation.
  useEffect(() => {
    if (!inTelegram) return
    if (sessionStorage.getItem('nh_mini_resumed')) return
    sessionStorage.setItem('nh_mini_resumed', '1')
    let cancelled = false
    setTgResuming(true)
    ;(async () => {
      const ok = await resumeTelegramSession()
      if (cancelled) return
      if (ok) router.replace('/profile')
      else setTgResuming(false)
    })()
    return () => {
      cancelled = true
    }
  }, [inTelegram, router])

  const showTgCta = mounted && inTelegram

  async function signInWithTelegram() {
    setTgBusy(true)
    if (await loginWithTelegram()) {
      router.replace('/profile')
    } else {
      toast(ta('telegramError'))
      setTgBusy(false)
    }
  }

  async function choosePackage(id: string) {
    if (!user) {
      router.push('/register')
      return
    }
    setBuying(id)
    try {
      await api.me.checkout([{ type: 'package', id }])
      toast(tprof('purchasedToast'))
      router.push('/profile')
    } catch {
      setBuying(null)
    }
  }

  // While resuming a returning user's session inside Telegram, show a spinner
  // instead of flashing the landing before the redirect to the cabinet.
  if (mounted && inTelegram && tgResuming) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper text-[15px] text-muted">…</div>
    )
  }

  return (
    <div className="min-h-screen bg-paper">
      <SiteNav />

      {/* HERO */}
      <section className="mx-auto max-w-[1200px] px-5 pb-14 pt-12 sm:px-11 sm:pb-16 sm:pt-16">
        <div className="grid items-center gap-10 lg:grid-cols-[1.05fr_.95fr] lg:gap-11">
          <div>
            <h1 className="font-display text-[38px] leading-[1.04] text-ink sm:text-[52px] lg:text-[58px] lg:leading-[1.03]">
              {t('heroTitle')}
            </h1>
            <p className="mt-5 max-w-[46ch] text-[16px] leading-relaxed text-ink-hero sm:text-[17.5px]">
              {t('heroSubtitle')}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              {showTgCta && !user ? (
                // Inside the Mini App, lead with an explicit sign-in (initData
                // works in-Telegram; the OIDC redirect does not).
                <>
                  <Button variant="solid" size="lg" className="gap-2" onClick={signInWithTelegram} disabled={tgBusy}>
                    <TelegramIcon /> {ta('telegram')}
                  </Button>
                  <Button asChild variant="outline" size="lg">
                    <Link href="/register">{ta('registerByEmail')}</Link>
                  </Button>
                </>
              ) : showTgCta && user ? (
                <Button asChild variant="solid" size="lg">
                  <Link href={dashHref(user.role)}>{ta('openCabinet')}</Link>
                </Button>
              ) : (
                <>
                  <Button asChild variant="solid" size="lg">
                    <Link href="/#packages">{t('choosePackage')}</Link>
                  </Button>
                  <Button asChild variant="outline" size="lg">
                    <Link href="/#how">{t('howItWorksCta')}</Link>
                  </Button>
                </>
              )}
            </div>
            <div className="mt-7 flex flex-wrap items-center gap-x-4 gap-y-2 text-[13.5px] text-muted">
              {[0, 1, 2].map((i) => (
                <span key={i} className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                  {t(`heroBullets.${i}`)}
                </span>
              ))}
            </div>
          </div>

          {/* Hero visual + floating path card */}
          <div className="relative">
            <div className="relative h-[300px] overflow-hidden rounded-2xl border border-line shadow-card sm:h-[420px]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/london.jpg"
                alt="London — Tower Bridge and the Thames"
                className="h-full w-full object-cover"
                loading="eager"
              />
              <div className="pointer-events-none absolute inset-0 bg-gradient-to-tr from-ink/25 via-transparent to-transparent" />
            </div>
            <div className="absolute -bottom-6 -left-3 w-[270px] rounded-xl border border-line bg-card p-[18px] shadow-[0_18px_40px_-22px_rgba(27,26,23,.5)] sm:-left-6">
              <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.1em] text-gray">
                {t('pathCardTitle')}
              </div>
              <div className="flex flex-col gap-3">
                <PathRow state="done" label={t('how.meet.title')} />
                <PathRow state="done" label={ts('items.tempHousing.name')} />
                <PathRow state="active" label={t('pathCardActive')} />
                <PathRow state="upcoming" label="Bank · NHS" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="scroll-mt-20 border-y border-line bg-card">
        <div className="mx-auto max-w-[1200px] px-5 py-14 sm:px-11">
          <h2 className="mb-11 text-center font-display text-[28px] text-ink sm:text-[36px]">
            {t('howTitle')}
          </h2>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-5 lg:gap-4">
            {HOW_STEPS.map((step, i) => (
              <div key={step}>
                <div className="mb-2.5 font-display text-[34px] text-accent">
                  {String(i + 1).padStart(2, '0')}
                </div>
                <div className="mb-1.5 text-[15px] font-semibold text-ink">
                  {t(`how.${step}.title`)}
                </div>
                <div className="text-[13px] leading-relaxed text-muted">
                  {t(`how.${step}.desc`)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PACKAGES */}
      <section id="packages" className="scroll-mt-20">
        <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-11">
          <div className="mb-10 text-center">
            <h2 className="mb-3 font-display text-[28px] text-ink sm:text-[36px]">
              {t('packagesTitle')}
            </h2>
            <p className="text-[15px] text-muted">{t('packagesSubtitle')}</p>
          </div>
          <div className="grid items-start gap-[18px] md:grid-cols-3">
            {PACKAGES.map((pkg) => {
              const popular = !!pkg.popular
              const features = Array.from({ length: pkg.featureCount }, (_, i) =>
                tp(`${pkg.id}.features.${i}`)
              )
              return (
                <div
                  key={pkg.id}
                  className={cn(
                    'nd-lift relative rounded-xl border p-7',
                    popular
                      ? 'border-accent bg-accent text-[#eef2ee] shadow-[0_20px_44px_-26px_rgba(47,93,69,.8)]'
                      : 'border-line bg-card'
                  )}
                >
                  {popular && (
                    <span className="absolute -top-3 left-7 rounded-full bg-surface px-[11px] py-1 text-[10.5px] font-bold uppercase tracking-[0.08em] text-accent">
                      {t('popular')}
                    </span>
                  )}
                  <div className={cn('font-display text-[23px]', popular ? 'text-white' : 'text-ink')}>
                    {tp(`${pkg.id}.name`)}
                  </div>
                  <div className={cn('mb-5 text-[13px]', popular ? 'opacity-75' : 'text-gray')}>
                    {tp(`${pkg.id}.tagline`)}
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className={cn('font-display text-[38px]', popular ? 'text-white' : 'text-ink')}>
                      {fmtGBP(pkg.gbp)}
                    </span>
                    <span className={cn('text-[14px]', popular ? 'opacity-75' : 'text-gray')}>
                      / {fmtUSD(pkg.gbp)}
                    </span>
                  </div>
                  <div className={cn('mb-6 mt-0.5 text-[13px]', popular ? 'opacity-75' : 'text-gray')}>
                    {fmtUZS(pkg.gbp)}
                  </div>
                  <div className="mb-6 flex flex-col gap-3">
                    {features.map((f, i) => (
                      <div key={i} className={cn('flex gap-2.5 text-[13.5px]', popular ? 'opacity-95' : 'text-ink-2')}>
                        <span className={cn('font-bold', popular ? 'text-white' : 'text-accent')}>✓</span>
                        {f}
                      </div>
                    ))}
                  </div>
                  <Button
                    variant={popular ? 'white' : 'outline'}
                    size="block"
                    disabled={buying === pkg.id}
                    className={cn('rounded-[11px]', popular && 'font-bold text-accent')}
                    onClick={() => choosePackage(pkg.id)}
                  >
                    {t('choose')}
                  </Button>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* SERVICES TEASER */}
      <section className="border-t border-line bg-card">
        <div className="mx-auto max-w-[1200px] px-5 py-16 sm:px-11">
          <div className="mb-2 flex items-end justify-between gap-4">
            <h2 className="font-display text-[26px] text-ink sm:text-[32px]">
              {t('servicesTeaserTitle')}
            </h2>
            <Button asChild variant="soft" size="sm" className="shrink-0 gap-1.5">
              <Link href="/services">
                {t('allServices')} <ArrowRight size={15} />
              </Link>
            </Button>
          </div>
          <p className="mb-6 max-w-[60ch] text-[14px] text-muted">{t('servicesTeaserHint')}</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {TEASER_SERVICE_IDS.map((id) => {
              const svc = serviceById(id)!
              return (
                <Link
                  key={id}
                  href={`/services?add=${id}`}
                  className="nd-lift group flex items-center justify-between rounded-lg border border-line bg-surface px-5 py-4"
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <span className="truncate text-[14px] font-medium text-ink">{ts(`items.${id}.name`)}</span>
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    <span className="font-display text-[20px] text-accent">{fmtGBP(svc.price)}</span>
                    <ArrowRight
                      size={16}
                      className="text-gray-lt transition-transform group-hover:translate-x-0.5 group-hover:text-accent"
                    />
                  </span>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      {/* HOUSING CATALOG */}
      <section className="mx-auto max-w-[1200px] px-5 py-16 sm:px-11">
        <div className="mb-2 flex items-end justify-between gap-4">
          <h2 className="font-display text-[26px] text-ink sm:text-[32px]">{t('catalogTitle')}</h2>
          <Button asChild variant="soft" size="sm" className="shrink-0 gap-1.5">
            <Link href="/search">
              {t('catalogCta')} <ArrowRight size={15} />
            </Link>
          </Button>
        </div>
        <p className="mb-6 max-w-[60ch] text-[14px] text-muted">{t('catalogSubtitle')}</p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {catalog.slice(0, 3).map((p) => (
            <Link
              key={p.id}
              href="/search"
              className="nd-lift overflow-hidden rounded-xl border border-line bg-card"
            >
              {p.photoUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={p.photoUrl}
                  alt=""
                  className="h-[150px] w-full object-cover"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="photo-stripe h-[150px]" />
              )}
              <div className="p-4">
                <div className="flex items-baseline gap-1.5">
                  <span className="font-display text-[19px] text-ink">{fmtGBP(p.priceGBP)}</span>
                  <span className="text-[13px] text-gray">{tsr('perMonth')}</span>
                </div>
                <div className="mt-1 text-[14px] text-ink-2">{p.addr}</div>
                <div className="mt-2 text-[12.5px] text-muted">
                  {p.rooms === 0 ? tsr('filters.roomsOpts.studio') : tsr('meta.bed', { count: p.rooms })} ·{' '}
                  {tsr('meta.bath', { count: p.baths })}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-[1200px] px-5 py-16 sm:px-11">
        <div className="rounded-2xl bg-accent px-8 py-12 text-center sm:px-12 sm:py-14">
          <h2 className="mx-auto max-w-[20ch] font-display text-[28px] text-white sm:text-[38px]">
            {t('ctaTitle')}
          </h2>
          <p className="mx-auto mt-4 max-w-[46ch] text-[15px] leading-relaxed text-white/80">
            {t('ctaSubtitle')}
          </p>
          <Button asChild variant="white" size="lg" className="mt-7">
            <Link href="/register">{t('ctaButton')}</Link>
          </Button>
        </div>
      </section>

      <Footer />
    </div>
  )
}

function PathRow({ state, label }: { state: 'done' | 'active' | 'upcoming'; label: string }) {
  return (
    <div className="flex items-center gap-2.5">
      {state === 'done' && (
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent text-[11px] text-white">
          ✓
        </span>
      )}
      {state === 'active' && (
        <span className="nd-pulse h-5 w-5 rounded-full border-2 border-accent bg-card" />
      )}
      {state === 'upcoming' && (
        <span className="h-5 w-5 rounded-full border-2 border-line bg-surface" />
      )}
      <span
        className={cn(
          'text-[13px]',
          state === 'active'
            ? 'font-semibold text-ink'
            : state === 'done'
              ? 'text-ink-2'
              : 'text-gray-lt'
        )}
      >
        {label}
      </span>
    </div>
  )
}
