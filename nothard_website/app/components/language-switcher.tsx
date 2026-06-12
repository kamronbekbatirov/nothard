'use client'

import { useLocale, useTranslations } from 'next-intl'
import { useParams } from 'next/navigation'
import { useRouter, usePathname } from '@/i18n/navigation'
import { routing } from '@/i18n/routing'
import { Button } from './ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select'
import { Languages } from 'lucide-react'

const LABELS: Record<string, string> = {
  ru: 'Русский',
  en: 'English',
  uz: "O'zbek",
  'uz-cyrl': 'Ўзбек',
}

const SHORT_LABELS: Record<string, string> = {
  ru: 'RU',
  en: 'EN',
  uz: 'UZ',
  'uz-cyrl': 'ЎЗ',
}

export function LanguageSwitcher({ variant = 'select' }: { variant?: 'select' | 'list' }) {
  const locale = useLocale()
  const router = useRouter()
  const pathname = usePathname()
  const params = useParams()
  const t = useTranslations('LanguageSwitcher')

  const change = (next: string) => {
    document.cookie = `NEXT_LOCALE=${next}; path=/; max-age=${60 * 60 * 24 * 365}; samesite=lax`
    // @ts-expect-error -- next-intl handles dynamic params for known routes
    router.replace({ pathname, params }, { locale: next })
  }

  if (variant === 'list') {
    return (
      <div className="space-y-1">
        {routing.locales.map((l) => (
          <Button
            key={l}
            variant={l === locale ? 'default' : 'outline'}
            className="w-full justify-start"
            onClick={() => change(l)}
          >
            <span className="mr-2 text-xs font-mono">{SHORT_LABELS[l]}</span>
            {LABELS[l]}
          </Button>
        ))}
      </div>
    )
  }

  return (
    <Select value={locale} onValueChange={change}>
      <SelectTrigger className="w-auto gap-2 px-3" aria-label={t('label')}>
        <Languages className="h-4 w-4" />
        <SelectValue>{SHORT_LABELS[locale] ?? locale}</SelectValue>
      </SelectTrigger>
      <SelectContent align="end">
        {routing.locales.map((l) => (
          <SelectItem key={l} value={l}>
            {LABELS[l]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
