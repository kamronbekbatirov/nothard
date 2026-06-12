import LandingPage from '../components/landing-page'
import { setRequestLocale } from 'next-intl/server'

export default async function Home({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params
  setRequestLocale(locale)
  return <LandingPage />
}
