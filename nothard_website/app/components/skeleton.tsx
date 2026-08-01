'use client'

import { cn } from '@/app/lib/utils'

/**
 * Skeleton loaders — the calm "component outlines" shown while a page's data is
 * loading, instead of a bare spinner. All pieces pulse with `animate-pulse` and
 * use the theme's `track` colour so they read the same in light and dark.
 */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('animate-pulse rounded-md bg-track', className)} />
}

/** A sticky top bar placeholder that mirrors AppTopbar (logo + right controls). */
function TopbarSkeleton() {
  return (
    <div className="sticky top-0 z-30 border-b border-line bg-surface/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1240px] items-center justify-between gap-4 px-5 py-3.5 sm:px-8">
        <Skeleton className="h-6 w-28 rounded-full" />
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-8 rounded-full" />
          <Skeleton className="h-8 w-8 rounded-full" />
        </div>
      </div>
    </div>
  )
}

/** A single card outline (title line + a couple of content lines). */
export function CardSkeleton({ className, lines = 3 }: { className?: string; lines?: number }) {
  return (
    <div className={cn('rounded-2xl border border-line bg-card p-5', className)}>
      <Skeleton className="h-4 w-1/3" />
      <div className="mt-4 flex flex-col gap-2.5">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} className={cn('h-3.5', i === lines - 1 && 'w-2/3')} />
        ))}
      </div>
    </div>
  )
}

/**
 * Full-page shell used while a cabinet/panel loads: a top bar, a greeting line,
 * a row of small tiles and a responsive grid of card outlines.
 */
export function AppShellSkeleton() {
  return (
    <div className="min-h-screen bg-paper">
      <TopbarSkeleton />
      <main className="mx-auto max-w-[1240px] px-5 py-8 sm:px-8">
        <Skeleton className="h-7 w-56" />
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
        <div className="mt-8 grid gap-6 lg:grid-cols-[296px_1fr]">
          <div className="flex flex-col gap-5">
            <Skeleton className="h-40 rounded-2xl" />
            <CardSkeleton lines={3} />
            <CardSkeleton lines={2} />
          </div>
          <div className="flex flex-col gap-4">
            <Skeleton className="h-9 w-2/3" />
            <Skeleton className="h-2 w-full rounded-full" />
            <div className="mt-2 flex flex-col gap-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-16 rounded-xl" />
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

/** Lighter shell for the public landing (nav bar + a hero block). */
export function LandingSkeleton() {
  return (
    <div className="min-h-screen bg-paper">
      <div className="border-b border-line">
        <div className="mx-auto flex max-w-[1160px] items-center justify-between px-5 py-4 sm:px-8">
          <Skeleton className="h-6 w-28 rounded-full" />
          <div className="flex items-center gap-2">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-8 w-20 rounded-lg" />
          </div>
        </div>
      </div>
      <div className="mx-auto max-w-[1160px] px-5 py-16 sm:px-8">
        <Skeleton className="h-5 w-40 rounded-full" />
        <Skeleton className="mt-5 h-12 w-4/5" />
        <Skeleton className="mt-3 h-12 w-3/5" />
        <Skeleton className="mt-6 h-4 w-2/3" />
        <div className="mt-8 flex gap-3">
          <Skeleton className="h-11 w-40 rounded-xl" />
          <Skeleton className="h-11 w-32 rounded-xl" />
        </div>
        <div className="mt-14 grid gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-2xl" />
          ))}
        </div>
      </div>
    </div>
  )
}
