'use client'

import { useEffect, useState } from 'react'
import { useTranslations } from 'next-intl'
import { Check } from 'lucide-react'
import { Button } from './button'
import { DuplicateWarningModal } from './duplicate-warning'
import {
  PACKAGES,
  SERVICES,
  SERVICE_STAGES,
  coveredServices,
  packageCovers,
  fmtGBP,
  fmtUZS,
} from '@/app/lib/data'
import { cn } from '@/app/lib/utils'

/**
 * The shared "choose a package and/or services" UI. A package and any extra
 * services are chosen together and paid for in ONE checkout. Used both as the
 * first-run empty cabinet (`barMode="fixed"`, full page) and inside the
 * re-purchase sheet opened from the populated cabinet (`barMode="inline"`).
 * `ownedServices` are shown as already-active and can't be re-picked.
 */
export function PackagePicker({
  onCheckout,
  buying,
  initialPkg,
  initialServices,
  ownedServices = [],
  heading,
  barMode = 'fixed',
}: {
  onCheckout: (pkgId: string | null, serviceIds: string[]) => void
  buying: boolean
  initialPkg?: string | null
  initialServices?: string[]
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
  const [services, setServices] = useState<string[]>(initialServices ?? [])
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
