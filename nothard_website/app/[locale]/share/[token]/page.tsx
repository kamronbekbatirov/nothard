'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { useTranslations } from 'next-intl'
import { CheckCircle2 } from 'lucide-react'
import { Link } from '@/i18n/navigation'
import { Footer } from '@/app/components/footer'
import { useTaskLabel } from '@/app/lib/task-label'
import { api, type SharedRelocation } from '@/app/lib/api'
import { cn } from '@/app/lib/utils'

export default function SharePage() {
  const params = useParams<{ token: string }>()
  const token = params?.token
  const t = useTranslations('SharePage')
  const tp = useTranslations('Packages')
  const ts = useTranslations('Services')
  const label = useTaskLabel()

  const [data, setData] = useState<SharedRelocation | null>(null)
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading')

  useEffect(() => {
    if (!token) {
      setState('error')
      return
    }
    let cancelled = false
    // Poll so family watching the page see status changes live (the client cabinet
    // polls too), without a manual reload. Only the first load can flip to error.
    const load = (first: boolean) =>
      api
        .sharedRelocation(token)
        .then((d) => {
          if (cancelled) return
          setData(d)
          setState('ready')
        })
        .catch(() => {
          if (!cancelled && first) setState('error')
        })
    load(true)
    const id = window.setInterval(() => load(false), 7000)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [token])

  const percent =
    data && data.progress.total > 0
      ? Math.round((data.progress.done / data.progress.total) * 100)
      : 0

  function stepState(status: string): 'done' | 'active' | 'pending' {
    if (status === 'done') return 'done'
    if (status === 'inProgress' || status === 'onWay' || status === 'arrived') return 'active'
    return 'pending'
  }

  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b border-line">
        <div className="mx-auto flex max-w-[760px] items-center justify-between px-5 py-4 sm:px-8">
          <Link href="/" className="font-display text-[18px] font-semibold text-ink">
            Nothard
          </Link>
          <span className="text-[12.5px] text-muted">{t('tagline')}</span>
        </div>
      </header>

      <main className="mx-auto max-w-[760px] px-5 py-10 sm:px-8">
        {state === 'loading' && (
          <div className="space-y-4">
            <div className="h-8 w-2/3 animate-pulse rounded bg-track" />
            <div className="h-40 animate-pulse rounded-2xl bg-track" />
          </div>
        )}

        {state === 'error' && (
          <div className="rounded-2xl border border-line bg-card p-10 text-center">
            <p className="text-[15px] text-muted">{t('notFound')}</p>
          </div>
        )}

        {state === 'ready' && data && (
          <>
            <h1 className="font-display text-[28px] leading-tight text-ink sm:text-[34px]">
              {data.clientName ? t('heading', { name: data.clientName }) : t('headingNoName')}
            </h1>

            {data.package && (
              <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-accent-bg px-3 py-1 text-[13px] font-medium text-accent">
                {t('packageLabel')}: {tp(`${data.package.id}.name` as any)}
              </div>
            )}

            {/* Progress */}
            {data.progress.total > 0 && (
              <div className="mt-6">
                <div className="flex items-end justify-between">
                  <span className="text-[13px] text-muted">
                    {t('progress', { done: data.progress.done, total: data.progress.total })}
                  </span>
                  <span className="font-display text-[26px] text-accent">{percent}%</span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-track">
                  <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${percent}%` }} />
                </div>
              </div>
            )}

            {data.packageComplete && (
              <div className="mt-6 rounded-2xl bg-accent px-6 py-6 text-center text-white">
                <div className="font-display text-[20px]">{t('completed')}</div>
              </div>
            )}

            {/* People */}
            {(data.manager || data.runner) && (
              <div className="mt-8 grid gap-3 sm:grid-cols-2">
                {data.manager && <Person label={t('managerLabel')} person={data.manager} />}
                {data.runner && <Person label={t('companionLabel')} person={data.runner} />}
              </div>
            )}

            {/* Path */}
            {data.path.length > 0 && (
              <section className="mt-8">
                <div className="eyebrow mb-3">{t('pathLabel')}</div>
                <div className="flex flex-col gap-2">
                  {data.path.map((step, i) => {
                    const st = stepState(step.status)
                    return (
                      <div
                        key={`${step.key}-${i}`}
                        className="flex items-center justify-between gap-3 rounded-xl border border-line bg-card px-4 py-3"
                      >
                        <span className="flex min-w-0 items-center gap-2.5">
                          <span
                            className={cn(
                              'flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px]',
                              st === 'done'
                                ? 'bg-accent text-white'
                                : st === 'active'
                                  ? 'border-2 border-accent bg-card'
                                  : 'border-2 border-line bg-surface'
                            )}
                          >
                            {st === 'done' ? '✓' : ''}
                          </span>
                          <span className={cn('truncate text-[14px]', st === 'pending' ? 'text-gray-lt' : 'text-ink')}>
                            {label('step', step.key).title}
                          </span>
                        </span>
                        <span
                          className={cn(
                            'shrink-0 text-[12px] font-medium',
                            st === 'done' ? 'text-accent' : st === 'active' ? 'text-amber-600' : 'text-gray-lt'
                          )}
                        >
                          {st === 'done' ? t('done') : st === 'active' ? t('inProgress') : t('pending')}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </section>
            )}

            {/* Extra services */}
            {data.services.length > 0 && (
              <section className="mt-8">
                <div className="eyebrow mb-3">{t('servicesLabel')}</div>
                <div className="flex flex-wrap gap-2">
                  {data.services.map((s) => (
                    <span
                      key={s.id}
                      className={cn(
                        'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[13px]',
                        s.done ? 'border-accent/30 bg-accent-bg text-accent' : 'border-line bg-card text-ink-2'
                      )}
                    >
                      {s.done && <CheckCircle2 size={13} />}
                      {ts(`items.${s.id}.name` as any)}
                    </span>
                  ))}
                </div>
              </section>
            )}

            <div className="mt-10 text-center">
              <Link href="/" className="text-[14px] font-semibold text-accent hover:underline">
                {t('cta')} →
              </Link>
            </div>
          </>
        )}
      </main>
      <Footer />
    </div>
  )
}

function Person({
  label,
  person,
}: {
  label: string
  person: { name: string; photoUrl: string | null }
}) {
  const [broken, setBroken] = useState(false)
  return (
    <div className="flex items-center gap-3 rounded-xl border border-line bg-card p-4">
      {person.photoUrl && !broken ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={person.photoUrl}
          alt=""
          onError={() => setBroken(true)}
          className="h-11 w-11 shrink-0 rounded-full object-cover"
          referrerPolicy="no-referrer"
        />
      ) : (
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent text-[17px] font-semibold text-white">
          {(person.name || '?').trim().charAt(0).toUpperCase() || '?'}
        </span>
      )}
      <div className="min-w-0">
        <div className="text-[11px] font-semibold uppercase tracking-wide text-gray">{label}</div>
        <div className="truncate text-[15px] font-semibold text-ink">{person.name}</div>
      </div>
    </div>
  )
}
