'use client'

import { useEffect, useMemo, useState } from 'react'
import { useTranslations } from 'next-intl'
import { MapPin, Camera } from 'lucide-react'
import { AppTopbar } from '@/app/components/app-topbar'
import { Button } from '@/app/components/button'
import { useToast } from '@/app/components/toast'
import { useRequireRole } from '@/app/lib/use-require-role'
import { useTaskLabel } from '@/app/lib/task-label'
import { api, clearTokens, type RunnerTask } from '@/app/lib/api'
import { cn } from '@/app/lib/utils'

export default function RunnerPage() {
  const t = useTranslations('Runner')
  const { toast } = useToast()
  const { ready, user } = useRequireRole(['runner'])
  const [tasks, setTasks] = useState<RunnerTask[]>([])
  const [name, setName] = useState('')
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (!ready) return
    api.runner
      .tasks()
      .then((d) => {
        setTasks(d.tasks)
        setName(d.name)
      })
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [ready])

  const done = useMemo(() => tasks.filter((x) => x.stage === 'done').length, [tasks])

  async function advance(id: number) {
    try {
      const updated = await api.runner.advance(id)
      setTasks((ts) => ts.map((x) => (x.id === id ? updated : x)))
      if (updated.stage === 'done') toast(t('actions.complete'))
    } catch {}
  }

  if (!ready) return <PanelLoading />

  return (
    <div className="min-h-screen bg-paper">
      <AppTopbar
        badge={t('badge')}
        name={name || user?.name}
        avatarUrl={user?.photo_url}
        onLogout={() => {
          clearTokens()
          window.location.href = '/login'
        }}
      />

      <main className="mx-auto max-w-[600px] px-4 py-7 sm:px-6">
        <h1 className="font-display text-[24px] text-ink">
          {t('heading', { count: tasks.length, name: name || user?.name || '' })}
        </h1>
        <p className="mt-1 text-[13.5px] text-muted">{t('doneCount', { done, total: tasks.length })}</p>

        <div className="mt-6 flex flex-col gap-3">
          {tasks.map((task) => (
            <RunnerCard key={task.id} task={task} onAdvance={() => advance(task.id)} />
          ))}
          {loaded && tasks.length === 0 && (
            <p className="rounded-xl border border-line bg-card p-6 text-center text-[14px] text-muted">
              —
            </p>
          )}
        </div>
      </main>
    </div>
  )
}

function RunnerCard({ task, onAdvance }: { task: RunnerTask; onAdvance: () => void }) {
  const t = useTranslations('Runner')
  const label = useTaskLabel()
  const title = label(task.kind, task.key).title
  const active = task.stage !== 'done'
  const actionLabel =
    task.stage === 'todo'
      ? t('actions.onWay')
      : task.stage === 'onWay'
        ? t('actions.arrived')
        : t('actions.complete')

  return (
    <div
      className={cn(
        'rounded-xl border bg-card p-4',
        task.stage === 'done'
          ? 'border-line opacity-70'
          : task.stage === 'todo'
            ? 'border-line'
            : 'border-accent/40'
      )}
    >
      <div className="flex items-start gap-3">
        <span className="mt-0.5">
          {task.stage === 'done' ? (
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent text-[12px] text-white">
              ✓
            </span>
          ) : task.stage === 'todo' ? (
            <span className="block h-6 w-6 rounded-full border-2 border-line bg-surface" />
          ) : (
            <span className="nd-pulse block h-6 w-6 rounded-full border-2 border-accent bg-card" />
          )}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-[13px] font-semibold text-ink">{task.time}</span>
            {task.stage !== 'done' && task.stage !== 'todo' && (
              <span className="rounded-full bg-accent-bg px-2 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide text-accent">
                {task.stage === 'onWay' ? t('status.onWay') : t('status.arrived')}
              </span>
            )}
          </div>
          <div className="mt-0.5 text-[15px] font-medium text-ink">{title}</div>
          <div className="text-[13px] text-muted">
            {task.client} · {task.addr}
          </div>

          {active && (
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="solid" size="sm" onClick={onAdvance}>
                {actionLabel}
              </Button>
              <Button variant="outline" size="sm" className="gap-1.5">
                <MapPin size={14} /> {t('actions.route')}
              </Button>
              <Button variant="outline" size="sm" className="gap-1.5">
                <Camera size={14} /> {t('actions.photo')}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function PanelLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-paper text-[15px] text-muted">
      …
    </div>
  )
}
