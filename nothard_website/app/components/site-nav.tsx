'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Menu, X } from 'lucide-react'
import { Link } from '@/i18n/navigation'
import { Logo } from './logo'
import { LangSwitcher } from './lang-switcher'
import { ThemeToggle } from './theme'
import { Button } from './button'
import { useAuth } from '@/app/lib/use-auth'

type NavLink = { label: string; href: string }

export function SiteNav() {
  const t = useTranslations('Nav')
  const { user } = useAuth()
  const [open, setOpen] = useState(false)

  const links: NavLink[] = [
    { label: t('howItWorks'), href: '/#how' },
    { label: t('packages'), href: '/#packages' },
    { label: t('services'), href: '/services' },
    { label: t('housing'), href: '/search' },
    { label: t('contacts'), href: '/#contacts' },
  ]

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface/85 backdrop-blur-md">
      <nav className="mx-auto flex max-w-[1200px] items-center justify-between px-5 py-4 sm:px-11 sm:py-5">
        <Logo size={26} />

        <div className="hidden items-center gap-[30px] lg:flex">
          {links.map((l) => (
            <Link key={l.href} href={l.href as any} className="nd-nav text-[14px] font-medium text-ink-2">
              {l.label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-4">
          <ThemeToggle />
          <div className="hidden sm:block">
            <LangSwitcher />
          </div>
          {user ? (
            <Button asChild variant="outline" size="sm" className="hidden sm:inline-flex">
              <Link href={dashHref(user.role)}>{t('profile')}</Link>
            </Button>
          ) : (
            <Button asChild variant="outline" size="sm" className="hidden sm:inline-flex">
              <Link href="/login">{t('login')}</Link>
            </Button>
          )}
          <button
            className="btn-motion inline-flex h-9 w-9 items-center justify-center rounded-md border border-line text-ink lg:hidden"
            onClick={() => setOpen((v) => !v)}
            aria-label="Menu"
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </nav>

      {open && (
        <div className="border-t border-line bg-surface px-5 py-4 lg:hidden">
          <div className="flex flex-col gap-1">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href as any}
                onClick={() => setOpen(false)}
                className="rounded-md px-2 py-2.5 text-[15px] font-medium text-ink-2 hover:bg-sub"
              >
                {l.label}
              </Link>
            ))}
            <div className="mt-3 flex items-center justify-between">
              <LangSwitcher />
              <Button asChild variant="solid" size="sm">
                <Link href={user ? dashHref(user.role) : '/login'}>
                  {user ? t('profile') : t('login')}
                </Link>
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}

export function dashHref(role: string): '/profile' | '/admin' | '/agency' | '/runner' {
  switch (role) {
    case 'operator':
    case 'admin':
      return '/admin'
    case 'agency':
      return '/agency'
    case 'runner':
      return '/runner'
    default:
      return '/profile'
  }
}
