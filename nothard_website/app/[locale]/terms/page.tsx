import { setRequestLocale } from 'next-intl/server'
import { LegalDoc } from '@/app/components/legal-doc'

export default async function TermsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params
  setRequestLocale(locale)
  return <LegalDoc kind="terms" />
}
