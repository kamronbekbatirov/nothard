'use client'

import { useState } from 'react'
import { LogOut, Settings } from 'lucide-react'
import { Logo } from './logo'
import { LangMenu } from './lang-switcher'
import { ThemeToggle } from './theme'
import { Avatar } from './avatar'
import { cn } from '@/app/lib/utils'

export type TopMenuItem = { label: string; active?: boolean; onClick?: () => void }

export function AppTopbar({
  badge,
  menu,
  name,
  avatarUrl,
  tgId,
  onLogout,
  onSettings,
  right,
  hideLang = false,
}: {
  badge?: string
  menu?: TopMenuItem[]
  name?: string
  avatarUrl?: string | null
  /** Telegram user id — gives the fallback Telegram's own gradient colours. */
  tgId?: string | number | null
  onLogout?: () => void
  onSettings?: () => void
  right?: React.ReactNode
  hideLang?: boolean
}) {
  const [menuOpen, setMenuOpen] = useState(false)

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
          <nav className="hidden items-center gap-1 lg:flex">
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
          {/* Compact language menu — available on every panel and every screen size
              (was desktop-only, so mobile panels had no way to change language). */}
          {!hideLang && <LangMenu />}
          {name && (
            <div className="flex items-center gap-2">
              <Avatar url={avatarUrl} name={name} tgId={tgId} size={32} />
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
        <div className="nd-hscroll flex gap-1.5 border-t border-line px-4 py-2 lg:hidden">
          {menu.map((m) => (
            <button
              key={m.label}
              onClick={m.onClick}
              ref={(el) => {
                // Keep the active tab scrolled into view on mobile.
                if (el && m.active) el.scrollIntoView({ block: 'nearest', inline: 'center' })
              }}
              className={cn(
                'shrink-0 whitespace-nowrap rounded-lg px-3.5 py-2 text-[13.5px] font-medium transition-colors',
                m.active ? 'bg-accent-bg text-accent' : 'text-muted hover:text-ink'
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
