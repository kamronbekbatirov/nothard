'use client'

import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/navigation'
import { SiteNav } from './site-nav'
import { Footer } from './footer'

export function LegalDoc({ kind }: { kind: 'privacy' | 'terms' }) {
  const t = useTranslations('Legal')
  const title = kind === 'privacy' ? t('privacyTitle') : t('termsTitle')
  const sections = [0, 1, 2, 3, 4]

  return (
    <div className="min-h-screen bg-paper">
      <SiteNav />
      <main className="mx-auto max-w-[760px] px-5 py-14 sm:px-8">
        <h1 className="font-display text-[34px] text-ink sm:text-[42px]">{title}</h1>
        <p className="mt-2 text-[13.5px] text-gray">{t('updated', { date: '08.07.2026' })}</p>

        <div className="mt-4 rounded-lg border border-terracotta/25 bg-terracotta-bg px-4 py-3 text-[13.5px] text-ink-2">
          {t('placeholderNote')}
        </div>

        <div className="mt-8 flex flex-col gap-7">
          {sections.map((i) => (
            <section key={i}>
              <h2 className="mb-2 font-display text-[20px] text-ink">{t(`sections.${i}.h`)}</h2>
              <p className="text-[15px] leading-relaxed text-ink-2">{t(`sections.${i}.p`)}</p>
            </section>
          ))}
        </div>

        <Link
          href="/"
          className="mt-10 inline-block text-[14px] font-semibold text-accent hover:underline"
        >
          ← {t('backHome')}
        </Link>
      </main>
      <Footer />
    </div>
  )
}
