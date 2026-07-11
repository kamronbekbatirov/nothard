'use client'

import { useTranslations } from 'next-intl'

/** Localizes a task/path item by (kind, key): steps via Profile.steps, services via Services.items. */
export function useTaskLabel() {
  const tp = useTranslations('Profile')
  const ts = useTranslations('Services')
  return (kind: 'step' | 'service', key: string) => {
    if (kind === 'service') {
      return { title: ts(`items.${key}.name` as any), desc: ts(`items.${key}.desc` as any) }
    }
    return { title: tp(`steps.${key}.title` as any), desc: tp(`steps.${key}.desc` as any) }
  }
}
