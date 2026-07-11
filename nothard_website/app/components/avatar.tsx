'use client'

import { useEffect, useState } from 'react'
import { cn } from '@/app/lib/utils'

/**
 * Round avatar with a robust fallback: when there's no photo — or the photo URL
 * fails to load (e.g. a Telegram photo that isn't ready / 404s) — it shows a
 * green circle with the first letter of the name, like everywhere else.
 */
export function Avatar({
  url,
  name,
  size = 40,
  className,
}: {
  url?: string | null
  name?: string | null
  size?: number
  className?: string
}) {
  const [broken, setBroken] = useState(false)
  useEffect(() => setBroken(false), [url])

  const letter = (name || '').trim().charAt(0).toUpperCase() || '?'
  const showImg = !!url && !broken

  return showImg ? (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={url!}
      alt={name || ''}
      onError={() => setBroken(true)}
      referrerPolicy="no-referrer"
      style={{ width: size, height: size }}
      className={cn('shrink-0 rounded-full object-cover', className)}
    />
  ) : (
    <span
      style={{ width: size, height: size, fontSize: Math.round(size * 0.42) }}
      className={cn(
        'flex shrink-0 items-center justify-center rounded-full bg-accent font-semibold text-white',
        className
      )}
    >
      {letter}
    </span>
  )
}
