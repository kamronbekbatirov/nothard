import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/navigation'
import { Logo } from './logo'

export function Footer() {
  const t = useTranslations('Footer')
  const year = new Date().getFullYear()

  const nav = [
    { label: t('home'), href: '/' },
    { label: t('packages'), href: '/#packages' },
    { label: t('services'), href: '/services' },
    { label: t('search'), href: '/search' },
    { label: t('login'), href: '/login' },
  ]

  return (
    <footer id="contacts" className="border-t border-line bg-surface">
      <div className="mx-auto max-w-[1200px] px-5 py-11 sm:px-11">
        <div className="grid gap-10 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <Logo size={24} asLink={false} />
            <p className="mt-4 max-w-[36ch] text-[14px] leading-relaxed text-muted">
              {t('tagline')}
            </p>
          </div>

          <div>
            <div className="eyebrow mb-4">{t('contacts')}</div>
            <address className="not-italic text-[14px] leading-relaxed text-ink-2">
              {t('address')}
              <br />
              <a href={`tel:${t('phone').replace(/\s/g, '')}`} className="nd-nav mt-2 inline-block">
                {t('phone')}
              </a>
              <br />
              <a href={`mailto:${t('email')}`} className="nd-nav inline-block">
                {t('email')}
              </a>
            </address>
          </div>

          <div>
            <div className="eyebrow mb-4">{t('navigation')}</div>
            <ul className="flex flex-col gap-2.5 text-[14px] text-ink-2">
              {nav.map((n) => (
                <li key={n.href}>
                  <Link href={n.href as any} className="nd-nav">
                    {n.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 flex flex-col items-start justify-between gap-3 border-t border-line pt-6 text-[13px] text-muted sm:flex-row sm:items-center">
          <span>{t('rights', { year })}</span>
          <div className="flex gap-5">
            <Link href="/privacy" className="nd-nav">
              {t('privacy')}
            </Link>
            <Link href="/terms" className="nd-nav">
              {t('terms')}
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
