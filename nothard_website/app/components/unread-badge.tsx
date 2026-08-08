import { cn } from '@/app/lib/utils'

/**
 * A small red count pill for unread chat messages. Renders nothing when count is
 * 0, so callers can drop it in unconditionally. `9+` caps large counts.
 */
export function UnreadBadge({ count, className }: { count?: number; className?: string }) {
  if (!count || count < 1) return null
  return (
    <span
      className={cn(
        'inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-terracotta px-1 text-[11px] font-bold leading-none text-white',
        className
      )}
    >
      {count > 9 ? '9+' : count}
    </span>
  )
}
