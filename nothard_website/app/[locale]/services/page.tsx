'use client'

import { useEffect, useMemo, useState } from 'react'
import { useTranslations } from 'next-intl'
import { ArrowLeft, X } from 'lucide-react'
import { Link, useRouter } from '@/i18n/navigation'
import { SiteNav } from '@/app/components/site-nav'
import { Footer } from '@/app/components/footer'
import { Button } from '@/app/components/button'
import { Field, Input } from '@/app/components/field'
import { useToast } from '@/app/components/toast'
import { useAuth } from '@/app/lib/use-auth'
import { api } from '@/app/lib/api'
import {
  SERVICE_STAGES,
  SERVICES,
  serviceById,
  fmtGBP,
  fmtUSD,
  fmtUZS,
  fieldsForItems,
  FIELD_TYPE,
} from '@/app/lib/data'
import { cn } from '@/app/lib/utils'

export default function ServicesPage() {
  const t = useTranslations('Services')
  const tc = useTranslations('Cart')
  const tco = useTranslations('Checkout')
  const tcommon = useTranslations('Common')
  const { toast } = useToast()
  const router = useRouter()
  const { user } = useAuth()

  const [cart, setCart] = useState<Set<string>>(new Set())
  const [checkout, setCheckout] = useState(false)

  // Pre-select a service when arriving from a landing-page tile (/services?add=<id>).
  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get('add')
    if (id && serviceById(id)) {
      setCart((s) => (s.has(id) ? s : new Set(s).add(id)))
      toast(tc('addedToast'))
      // Clean the query so a refresh doesn't re-add it.
      window.history.replaceState(null, '', window.location.pathname)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const items = useMemo(
    () => Array.from(cart).map((id) => serviceById(id)!).filter(Boolean),
    [cart]
  )
  const total = items.reduce((s, i) => s + i.price, 0)

  function toggle(id: string) {
    setCart((s) => {
      const n = new Set(s)
      if (n.has(id)) {
        n.delete(id)
        toast(tc('removed'))
      } else {
        n.add(id)
        toast(tc('addedToast'))
      }
      return n
    })
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
            <ArrowLeft size={16} /> {tcommon('toCabinet')}
          </Link>
        )}
        <div className="mb-2 flex gap-2">
          <Link href="/#packages" className="rounded-full px-3.5 py-1.5 text-[13px] font-medium text-muted hover:text-ink">
            {t('tabPackages')}
          </Link>
          <span className="rounded-full bg-accent-bg px-3.5 py-1.5 text-[13px] font-semibold text-accent">
            {t('tabServices')}
          </span>
        </div>
        <h1 className="font-display text-[30px] text-ink sm:text-[38px]">{t('title')}</h1>
        <p className="mt-2 max-w-[62ch] text-[15px] leading-relaxed text-muted">{t('subtitle')}</p>

        <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_300px]">
          {/* Services by stage */}
          <div className="flex flex-col gap-9">
            {SERVICE_STAGES.map((stage) => {
              const list = SERVICES.filter((s) => s.stage === stage)
              return (
                <div key={stage}>
                  <div className="eyebrow mb-4">{t(`stages.${stage}`)}</div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {list.map((svc) => {
                      const added = cart.has(svc.id)
                      return (
                        <div
                          key={svc.id}
                          className={cn(
                            'nd-svc flex min-h-[132px] flex-col justify-between rounded-lg border bg-card p-4',
                            svc.online ? 'border-accent/[.28]' : 'border-line'
                          )}
                        >
                          <div>
                            <div className="flex items-start justify-between gap-2">
                              <div className="text-[14px] font-semibold text-ink">
                                {t(`items.${svc.id}.name`)}
                              </div>
                            </div>
                            <div className="mt-1 text-[12.5px] leading-snug text-muted">
                              {t(`items.${svc.id}.desc`)}
                            </div>
                            {svc.online && (
                              <span className="mt-2 inline-block rounded-full bg-accent-bg px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide text-accent">
                                {tcommon('online')}
                              </span>
                            )}
                          </div>
                          <div className="mt-3 flex items-end justify-between gap-2">
                            <div>
                              <div className="font-display text-[22px] text-accent">{fmtGBP(svc.price)}</div>
                              <div className="text-[11.5px] text-gray">
                                {fmtUSD(svc.price)} · {fmtUZS(svc.price)}
                              </div>
                            </div>
                            <Button
                              variant={added ? 'solid' : 'outline'}
                              size="sm"
                              className={cn(!added && 'border-accent/50 text-accent')}
                              onClick={() => toggle(svc.id)}
                            >
                              {added ? tcommon('added') : tcommon('add')}
                            </Button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Cart */}
          <aside className="lg:sticky lg:top-24 lg:self-start">
            <div className="rounded-xl border border-line bg-card p-5">
              <div className="flex items-baseline justify-between">
                <h2 className="font-display text-[20px] text-ink">{tc('title')}</h2>
                <span className="text-[13px] text-gray">{tc('items', { count: items.length })}</span>
              </div>

              {items.length === 0 ? (
                <p className="mt-4 text-[13.5px] text-muted">{tc('empty')}</p>
              ) : (
                <div className="mt-4 flex flex-col gap-2.5">
                  {items.map((i) => (
                    <div key={i.id} className="flex items-center justify-between gap-2 text-[13.5px]">
                      <span className="truncate text-ink-2">{t(`items.${i.id}.name`)}</span>
                      <span className="flex items-center gap-2">
                        <span className="font-medium text-ink">{fmtGBP(i.price)}</span>
                        <button
                          onClick={() => toggle(i.id)}
                          className="text-gray hover:text-terracotta"
                          aria-label="remove"
                        >
                          <X size={15} />
                        </button>
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-5 flex items-baseline justify-between border-t border-line pt-4">
                <span className="text-[13px] text-muted">{tc('total')}</span>
                <span className="font-display text-[26px] text-ink">{fmtGBP(total)}</span>
              </div>

              <Button
                variant="solid"
                size="block"
                className="mt-4"
                disabled={items.length === 0}
                onClick={() => (user ? setCheckout(true) : router.push('/register'))}
              >
                {tc('checkout')}
              </Button>
              <p className="mt-3 text-center text-[12px] text-gray">{tcommon('currencyNote')}</p>
            </div>
          </aside>
        </div>
      </main>
      <Footer />

      {checkout && (
        <CheckoutModal
          total={total}
          serviceIds={items.map((i) => i.id)}
          needName={!user?.name?.trim()}
          onClose={() => setCheckout(false)}
          onDone={() => {
            setCheckout(false)
            setCart(new Set())
            toast(tco('paidToast'))
            router.push('/profile')
          }}
        />
      )}
    </div>
  )
}

function CheckoutModal({
  total,
  serviceIds,
  needName,
  onClose,
  onDone,
}: {
  total: number
  serviceIds: string[]
  needName: boolean
  onClose: () => void
  onDone: () => void
}) {
  const t = useTranslations('Checkout')
  const ts = useTranslations('Search')
  const fields = useMemo(() => fieldsForItems(serviceIds), [serviceIds])
  const hasDetails = needName || fields.length > 0
  const [step, setStep] = useState<'details' | 'pay'>(hasDetails ? 'details' : 'pay')
  const [details, setDetails] = useState<Record<string, string>>({})
  const [paid, setPaid] = useState(false)

  const set = (k: string, v: string) => setDetails((d) => ({ ...d, [k]: v }))
  const areaKeys = ['whitechapel', 'stratford', 'canadaWater', 'woolwich'] as const
  const bankKeys = ['monzo', 'revolut', 'starling'] as const

  return (
    <div className="fixed inset-0 z-[99998] flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-6">
      <div className="w-full max-w-[440px] overflow-hidden rounded-t-2xl bg-surface sm:rounded-2xl">
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <span className="text-[13px] font-semibold text-muted">
            {step === 'details' ? t('steps.details') : t('steps.payment')}
          </span>
          <button onClick={onClose} className="text-gray hover:text-ink" aria-label="close">
            <X size={18} />
          </button>
        </div>

        {step === 'details' ? (
          <div className="flex flex-col gap-4 p-6">
            <h3 className="font-display text-[22px] text-ink">{t('steps.details')}</h3>
            <p className="-mt-2 text-[13px] text-muted">
              {fields.length > 0 ? t('detailsSubtitle') : t('noFieldsNote')}
            </p>

            {needName && (
              <Field label={t('form.name')}>
                <Input value={details.name || ''} onChange={(e) => set('name', e.target.value)} placeholder="—" />
              </Field>
            )}

            {fields.map((f) => {
              const type = FIELD_TYPE[f]
              if (type === 'bank') {
                return (
                  <div key={f}>
                    <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{t(`fields.${f}`)}</span>
                    <div className="flex gap-2">
                      {bankKeys.map((b) => (
                        <button
                          key={b}
                          onClick={() => set(f, b)}
                          className={cn(
                            'nd-chip rounded-md border px-3.5 py-2 text-[13px] font-medium',
                            details[f] === b
                              ? 'border-accent bg-accent text-white'
                              : 'border-line bg-card text-ink-2'
                          )}
                        >
                          {t(`banks.${b}`)}
                        </button>
                      ))}
                    </div>
                  </div>
                )
              }
              if (type === 'area') {
                return (
                  <label key={f} className="block">
                    <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{t(`fields.${f}`)}</span>
                    <select
                      value={details[f] || ''}
                      onChange={(e) => set(f, e.target.value)}
                      className="w-full rounded-md border border-line bg-card px-3 py-3 text-[15px] text-ink"
                    >
                      <option value="">—</option>
                      {areaKeys.map((a) => (
                        <option key={a} value={a}>
                          {ts(`filters.areaOpts.${a}`)}
                        </option>
                      ))}
                    </select>
                  </label>
                )
              }
              return (
                <Field key={f} label={t(`fields.${f}`)}>
                  <Input
                    type={type === 'date' ? 'date' : type === 'number' ? 'number' : 'text'}
                    value={details[f] || ''}
                    onChange={(e) => set(f, e.target.value)}
                  />
                </Field>
              )
            })}

            <Button variant="solid" size="block" onClick={() => setStep('pay')}>
              {t('form.toPayment')}
            </Button>
          </div>
        ) : (
          <div className="bg-accent p-7 text-center text-white">
            <h3 className="font-display text-[24px] text-white">{t('payTitle')}</h3>
            <div className="mt-2 font-display text-[40px] text-white">{fmtGBP(total)}</div>
            <Button
              variant="white"
              size="block"
              className="mt-6 text-accent"
              disabled={paid}
              onClick={async () => {
                setPaid(true)
                try {
                  await api.me.checkout(
                    serviceIds.map((id) => ({ type: 'service' as const, id })),
                    details
                  )
                } catch {}
                setTimeout(onDone, 600)
              }}
            >
              {paid ? t('paid') : t('payButton')}
            </Button>
            <p className="mx-auto mt-4 max-w-[34ch] text-[12.5px] leading-relaxed text-white/75">
              {t('payNote')}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
