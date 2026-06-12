import { useTranslations } from 'next-intl'
import { Link } from '@/i18n/navigation'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Separator } from './ui/separator'
import { Instagram, Mail, Phone, MapPin } from 'lucide-react'

export function Footer() {
  const t = useTranslations('Footer')
  return (
    <footer className="border-t border-border bg-muted/40">
      <div className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-2 lg:grid-cols-4">
          <div>
            <h3 className="mb-4 text-xl font-bold tracking-tight">Nothard</h3>
            <p className="mb-4 text-sm text-muted-foreground">{t('tagline')}</p>
            <div className="flex space-x-3">
              <a
                href="#"
                aria-label="Instagram"
                className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:bg-foreground hover:text-background"
              >
                <Instagram className="h-4 w-4" />
              </a>
            </div>
          </div>
          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              {t('contacts')}
            </h3>
            <ul className="space-y-3 text-sm">
              <li className="flex items-start gap-2">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                <span>Mizzen Mast House, Mast Quay, Woolwich, London, SE18 5NP</span>
              </li>
              <li className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <a href="tel:+447440781874" className="transition-colors hover:text-foreground">
                  +44 7440 781874
                </a>
              </li>
              <li className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <a href="mailto:info@nothard.uz" className="transition-colors hover:text-foreground">
                  info@nothard.uz
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              {t('navigation')}
            </h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/" className="transition-colors hover:text-foreground">
                  {t('home')}
                </Link>
              </li>
              <li>
                <Link href={'/?section=packages' as any} className="transition-colors hover:text-foreground">
                  {t('packages')}
                </Link>
              </li>
              <li>
                <Link href={'/?section=services' as any} className="transition-colors hover:text-foreground">
                  {t('services')}
                </Link>
              </li>
              <li>
                <Link href="/login" className="transition-colors hover:text-foreground">
                  {t('login')}
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              {t('newsletter')}
            </h3>
            <p className="mb-4 text-sm text-muted-foreground">{t('newsletterText')}</p>
            <form className="flex flex-col gap-2">
              <Input type="email" placeholder={t('emailPlaceholder')} />
              <Button type="submit" className="w-full">
                {t('subscribe')}
              </Button>
            </form>
          </div>
        </div>
        <Separator className="my-10" />
        <div className="flex flex-col items-center justify-between gap-4 text-sm text-muted-foreground sm:flex-row">
          <p>{t('rights', { year: new Date().getFullYear() })}</p>
          <div className="flex gap-6">
            <a href="/privacy" className="transition-colors hover:text-foreground">
              {t('privacy')}
            </a>
            <a href="/terms" className="transition-colors hover:text-foreground">
              {t('terms')}
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
