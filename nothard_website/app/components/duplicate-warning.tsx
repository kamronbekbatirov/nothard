'use client'

import { useTranslations } from 'next-intl'
import { AlertTriangle } from 'lucide-react'
import { Button } from './button'

/**
 * Warns that the chosen services are already part of the selected package, so
 * the customer doesn't pay twice for the same thing. Deliberately a WARNING and
 * not a block — they can always continue if they really want the extra.
 */
export function DuplicateWarningModal({
  pkgName,
  serviceNames,
  body,
  cancelLabel,
  onCancel,
  onProceed,
}: {
  pkgName: string
  serviceNames: string[]
  /** Override the default "you picked services already in the package" wording. */
  body?: string
  /** Override the dismiss button (defaults to "remove the extras"). */
  cancelLabel?: string
  onCancel: () => void
  onProceed: () => void
}) {
  const t = useTranslations('Duplicate')

  return (
    <div
      className="fixed inset-0 z-[99999] flex items-end justify-center bg-black/50 p-0 backdrop-blur-[2px] sm:items-center sm:p-6"
      onClick={onCancel}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-[420px] overflow-hidden rounded-t-2xl bg-surface sm:rounded-2xl"
      >
        <div className="flex flex-col items-center px-6 pb-2 pt-7 text-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-500/15">
            <AlertTriangle size={24} className="text-amber-600" />
          </span>
          <h2 className="mt-3.5 font-display text-[20px] text-ink">{t('title')}</h2>
          <p className="mt-1.5 text-[13.5px] leading-relaxed text-muted">
            {body ?? t('body', { pkg: pkgName })}
          </p>
        </div>

        <ul className="mx-6 mt-3 flex flex-col gap-1.5 rounded-lg border border-line bg-card p-3.5">
          {serviceNames.map((n) => (
            <li key={n} className="flex items-start gap-2 text-[13.5px] text-ink-2">
              <span className="mt-[3px] h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
              {n}
            </li>
          ))}
        </ul>

        <p className="px-6 pt-3 text-center text-[12.5px] leading-snug text-gray">{t('hint')}</p>

        <div className="flex flex-col gap-2 p-6 pt-4">
          <Button variant="solid" size="block" onClick={onCancel}>
            {cancelLabel ?? t('remove')}
          </Button>
          <Button variant="outline" size="block" onClick={onProceed}>
            {t('proceed')}
          </Button>
        </div>
      </div>
    </div>
  )
}
