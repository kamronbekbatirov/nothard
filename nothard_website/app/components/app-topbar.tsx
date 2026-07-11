'use client'

import { useEffect, useState } from 'react'
import { LogOut, Settings } from 'lucide-react'
import { Logo } from './logo'
import { LangSwitcher } from './lang-switcher'
import { ThemeToggle } from './theme'
import { cn } from '@/app/lib/utils'

export type TopMenuItem = { label: string; active?: boolean; onClick?: () => void }

export function AppTopbar({
  badge,
  menu,
  name,
  avatarUrl,
  onLogout,
  onSettings,
  right,
  hideLang = false,
}: {
  badge?: string
  menu?: TopMenuItem[]
  name?: string
  avatarUrl?: string | null
  onLogout?: () => void
  onSettings?: () => void
  right?: React.ReactNode
  hideLang?: boolean
}) {
  const [menuOpen, setMenuOpen] = useState(false)
  // Fall back to the initials circle if the avatar fails to load (e.g. a Mini App
  // photo that isn't ready yet) instead of showing a broken "?" image.
  const [imgFailed, setImgFailed] = useState(false)
  useEffect(() => setImgFailed(false), [avatarUrl])
  const initials = (name || 'N')
    .split(' ')
    .map((s) => s[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-surface/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1240px] items-center justify-between gap-4 px-5 py-3.5 sm:px-8">
        <div className="flex items-center gap-3">
          <Logo size={22} />
          {badge && (
            <span className="rounded-full bg-inverse px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-inverse-fg">
              {badge}
            </span>
          )}
        </div>

        {menu && menu.length > 0 && (
          <nav className="hidden items-center gap-1 md:flex">
            {menu.map((m) => (
              <button
                key={m.label}
                onClick={m.onClick}
                className={cn(
                  'rounded-md px-3 py-1.5 text-[13.5px] font-medium transition-colors',
                  m.active ? 'bg-accent-bg text-accent' : 'text-muted hover:text-ink'
                )}
              >
                {m.label}
              </button>
            ))}
          </nav>
        )}

        <div className="flex items-center gap-3">
          {right}
          <ThemeToggle />
          {!hideLang && (
            <div className="hidden sm:block">
              <LangSwitcher />
            </div>
          )}
          {name && (
            <div className="flex items-center gap-2">
              {avatarUrl && !imgFailed ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={avatarUrl}
                  alt={name}
                  className="h-8 w-8 rounded-full object-cover"
                  referrerPolicy="no-referrer"
                  onError={() => setImgFailed(true)}
                />
              ) : (
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-[12px] font-semibold text-white">
                  {initials}
                </span>
              )}
              <span className="hidden text-[13.5px] font-medium text-ink sm:inline">{name}</span>
            </div>
          )}
          {onSettings && (
            <button
              onClick={onSettings}
              aria-label="settings"
              className="btn-motion flex h-8 w-8 items-center justify-center rounded-md text-gray hover:text-ink"
            >
              <Settings size={17} />
            </button>
          )}
          {onLogout && (
            <button
              onClick={onLogout}
              aria-label="logout"
              className="btn-motion flex h-8 w-8 items-center justify-center rounded-md text-gray hover:text-terracotta"
            >
              <LogOut size={16} />
            </button>
          )}
        </div>
      </div>

      {menu && menu.length > 0 && (
        <div className="nd-hscroll flex gap-1 border-t border-line px-4 py-2 md:hidden">
          {menu.map((m) => (
            <button
              key={m.label}
              onClick={m.onClick}
              className={cn(
                'shrink-0 rounded-md px-3 py-1.5 text-[13px] font-medium',
                m.active ? 'bg-accent-bg text-accent' : 'text-muted'
              )}
            >
              {m.label}
            </button>
          ))}
        </div>
      )}
    </header>
  )
}
