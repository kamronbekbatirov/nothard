import { setRequestLocale } from 'next-intl/server'
import { LegalDoc } from '@/app/components/legal-doc'

export default async function PrivacyPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params
  setRequestLocale(locale)
  return <LegalDoc kind="privacy" />
}
