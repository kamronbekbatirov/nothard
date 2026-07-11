'use client'

import * as React from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { cn } from '@/app/lib/utils'

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'w-full rounded-md border border-line bg-card px-3.5 py-3 text-[15px] text-ink placeholder:text-gray-lt',
        className
      )}
      {...props}
    />
  )
)
Input.displayName = 'Input'

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      'w-full rounded-md border border-line bg-card px-3.5 py-3 text-[15px] text-ink placeholder:text-gray-lt',
      className
    )}
    {...props}
  />
))
Textarea.displayName = 'Textarea'

/** Password input with a show/hide eye toggle. */
export const PasswordInput = React.forwardRef<
  HTMLInputElement,
  Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'>
>(({ className, ...props }, ref) => {
  const [show, setShow] = React.useState(false)
  return (
    <div className="relative">
      <Input ref={ref} {...props} type={show ? 'text' : 'password'} className={cn('pr-11', className)} />
      <button
        type="button"
        onClick={() => setShow((v) => !v)}
        className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-gray hover:text-ink"
        aria-label={show ? 'hide password' : 'show password'}
        tabIndex={-1}
      >
        {show ? <EyeOff size={17} /> : <Eye size={17} />}
      </button>
    </div>
  )
})
PasswordInput.displayName = 'PasswordInput'

export function Field({
  label,
  htmlFor,
  children,
}: {
  label: string
  htmlFor?: string
  children: React.ReactNode
}) {
  return (
    <label htmlFor={htmlFor} className="block">
      <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{label}</span>
      {children}
    </label>
  )
}

/**
 * Native date / time input sized to match our other fields.
 *
 * WebKit (iOS / Telegram webview) can't reliably centre or size a native
 * date/time control — its value top-aligns and the box grows taller than
 * siblings. So when the field is IDLE we show our own flex-centred label
 * (placeholder, or the value formatted as DD.MM.YYYY) in a fixed-height box. On
 * focus we reveal the real native control over it (opacity 0→1) so the desktop
 * calendar/clock and the iOS wheel picker both work; `showPicker()` opens it on
 * click too. On blur we go back to the clean centred display.
 */
function fmtDateTime(type: 'date' | 'time', v: string): string {
  if (!v) return ''
  if (type === 'time') return v
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(v)
  return m ? `${m[3]}.${m[2]}.${m[1]}` : v
}

export function DateTimeInput({
  type,
  value,
  onChange,
  placeholder,
  compact = false,
}: {
  type: 'date' | 'time'
  value: string
  onChange: (v: string) => void
  placeholder: string
  compact?: boolean
}) {
  const [focused, setFocused] = React.useState(false)
  const box = compact ? 'h-9 text-[12.5px]' : 'h-11 text-[15px]'
  const pad = compact ? 'px-2' : 'px-3'
  const display = fmtDateTime(type, value)
  return (
    <div
      className={cn(
        'relative box-border flex w-full min-w-0 items-center rounded-md border bg-card',
        focused ? 'border-accent' : 'border-line',
        box,
        pad
      )}
    >
      {!focused && (
        <span className={cn('pointer-events-none truncate', value ? 'text-ink' : 'text-gray-lt')}>
          {display || placeholder}
        </span>
      )}
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={(e) => {
          setFocused(true)
          const el = e.currentTarget as HTMLInputElement & { showPicker?: () => void }
          try {
            el.showPicker?.()
          } catch {}
        }}
        onBlur={() => setFocused(false)}
        aria-label={placeholder}
        className={cn(
          'absolute inset-0 h-full w-full cursor-pointer bg-transparent text-ink outline-none',
          pad,
          focused ? 'opacity-100' : 'opacity-0'
        )}
      />
    </div>
  )
}

/**
 * Pick from a list, or choose "Other" to type a custom value. The native
 * <select> gives a proper mobile wheel-picker; picking the "other" option
 * reveals a text field. Good for airports / flight numbers where most people
 * choose from the list but some need to enter their own.
 */
export function PickOrType({
  label,
  options,
  value,
  onChange,
  placeholder,
  otherLabel,
  pickLabel,
  compact = false,
}: {
  label?: string
  options: readonly string[]
  value: string
  onChange: (v: string) => void
  placeholder?: string
  otherLabel: string
  pickLabel: string
  compact?: boolean
}) {
  const known = !!value && options.includes(value)
  const [other, setOther] = React.useState<boolean>(!!value && !known)

  const control = compact
    ? 'box-border h-9 w-full min-w-0 rounded-md border border-line bg-card px-2 text-[12.5px] text-ink'
    : 'box-border block h-11 w-full min-w-0 rounded-md border border-line bg-card px-3 text-[15px] text-ink'

  const field = (
    <>
      <select
        value={other ? '__other__' : value}
        onChange={(e) => {
          const v = e.target.value
          if (v === '__other__') {
            setOther(true)
            onChange('')
          } else {
            setOther(false)
            onChange(v)
          }
        }}
        className={control}
      >
        <option value="">{pickLabel}</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
        <option value="__other__">{otherLabel}</option>
      </select>
      {other && (
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoFocus
          className={cn(control, 'mt-2')}
        />
      )}
    </>
  )

  if (!label) return field
  return (
    <label className="block">
      <span className="mb-1.5 block text-[13px] font-medium text-ink-2">{label}</span>
      {field}
    </label>
  )
}

/** Inline Telegram glyph. */
// Renders in Telegram brand blue (#229ED9) by default so the logo reads as
// Telegram even inside an accent/green button. Pass `className` to override.
export function TelegramIcon({ size = 18, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className ?? 'text-[#229ED9]'}
    >
      <path d="M21.94 4.6l-3.32 15.66c-.25 1.1-.9 1.38-1.83.86l-5.05-3.72-2.44 2.35c-.27.27-.5.5-1.02.5l.36-5.15L18.02 6.5c.41-.37-.09-.57-.63-.2L6.1 13.55l-5-1.57c-1.09-.34-1.11-1.09.23-1.61l19.55-7.54c.9-.34 1.7.2 1.4 1.77z" />
    </svg>
  )
}
