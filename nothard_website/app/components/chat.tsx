'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { MessageSquare, Send, X } from 'lucide-react'
import { cn } from '@/app/lib/utils'
import type { ChatMessage } from '@/app/lib/api'

function initialsOf(s: string) {
  return (s.trim().charAt(0) || '?').toUpperCase()
}

function timeOf(iso: string) {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function dayKeyOf(iso: string) {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  return d.toDateString()
}

// Returns a day-separator label, or null when the message is from today.
function dayLabelOf(iso: string) {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return null
  if (d.toDateString() === new Date().toDateString()) return null
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'long' })
}

export function ChatModal({
  title,
  subtitle,
  peerName,
  peerAvatarUrl,
  placeholder,
  emptyText,
  meSide,
  fetchMessages,
  sendMessage,
  onClose,
}: {
  title: string
  subtitle?: string
  peerName?: string
  peerAvatarUrl?: string | null
  placeholder: string
  emptyText: string
  meSide: 'client' | 'manager' | 'runner'
  fetchMessages: () => Promise<ChatMessage[]>
  sendMessage: (body: string) => Promise<ChatMessage>
  onClose: () => void
}) {
  const [avatarBroken, setAvatarBroken] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)

  async function load() {
    try {
      setMessages(await fetchMessages())
    } catch {
    } finally {
      setLoaded(true)
    }
  }

  useEffect(() => {
    load()
    const id = window.setInterval(load, 5000)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const body = text.trim()
    if (!body || busy) return
    setBusy(true)
    setText('')
    try {
      const m = await sendMessage(body)
      setMessages((prev) => [...prev, m])
    } catch {
      setText(body)
    } finally {
      setBusy(false)
    }
  }

  // Group consecutive messages so the author label only shows at the start of a run,
  // and insert a date separator whenever the calendar day changes.
  const rows = useMemo(() => {
    let prevDay = ''
    return messages.map((m, i) => {
      const day = dayKeyOf(m.createdAt)
      const dayChanged = day !== prevDay
      prevDay = day
      const prev = messages[i - 1]
      const firstOfRun = !prev || prev.sender !== m.sender || dayChanged
      return { m, daySep: dayChanged ? dayLabelOf(m.createdAt) : null, firstOfRun }
    })
  }, [messages])

  const avatarChar = initialsOf(peerName || title)

  return (
    <div
      className="fixed inset-0 z-[99999] flex items-end justify-center bg-black/50 p-0 backdrop-blur-[2px] sm:items-center sm:p-6"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="flex h-[86dvh] w-full max-w-[440px] flex-col overflow-hidden rounded-t-[22px] bg-surface shadow-[0_-18px_60px_-24px_rgba(27,26,23,.6)] sm:h-[620px] sm:rounded-[20px] sm:shadow-[0_30px_80px_-30px_rgba(27,26,23,.7)]"
      >
        {/* Header */}
        <div className="shrink-0 bg-accent px-4 pb-3.5 pt-2.5 text-white">
          {/* grab-handle affordance for the mobile bottom sheet */}
          <div className="mx-auto mb-2.5 h-1 w-9 rounded-full bg-white/30 sm:hidden" />
          <div className="flex items-center gap-3">
            {peerAvatarUrl && !avatarBroken ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={peerAvatarUrl}
                alt=""
                onError={() => setAvatarBroken(true)}
                referrerPolicy="no-referrer"
                className="h-10 w-10 shrink-0 rounded-full object-cover ring-1 ring-white/20"
              />
            ) : (
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/15 text-[16px] font-semibold leading-none text-white ring-1 ring-white/20">
                {avatarChar}
              </span>
            )}
            <div className="min-w-0 flex-1">
              <div className="truncate font-display text-[17px] leading-tight text-white">{title}</div>
              {subtitle && (
                <div className="mt-0.5 flex items-center gap-1.5 text-[12px] text-white/70">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#7bd39a]" />
                  <span className="truncate">{subtitle}</span>
                </div>
              )}
            </div>
            <button
              onClick={onClose}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/10 text-white/90 transition hover:bg-white/20"
              aria-label="close"
            >
              <X size={17} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div ref={listRef} className="flex-1 overflow-y-auto bg-paper px-4 py-4">
          {loaded && messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center px-6 text-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-full bg-accent-bg text-accent">
                <MessageSquare size={24} />
              </span>
              <p className="mt-3 max-w-[26ch] text-[13.5px] leading-relaxed text-muted">{emptyText}</p>
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            {rows.map(({ m, daySep, firstOfRun }) => {
              const mine = m.sender === meSide
              return (
                <div key={m.id}>
                  {daySep && (
                    <div className="my-3 flex justify-center">
                      <span className="rounded-full bg-sub px-2.5 py-0.5 text-[11px] font-medium text-muted">
                        {daySep}
                      </span>
                    </div>
                  )}
                  <div className={cn('flex', mine ? 'justify-end' : 'justify-start', firstOfRun ? 'mt-1.5' : 'mt-0.5')}>
                    <div
                      className={cn(
                        'max-w-[82%] px-3.5 py-2 text-[14px] leading-[1.35] shadow-[0_1px_2px_rgba(27,26,23,.06)]',
                        mine
                          ? 'rounded-2xl rounded-br-md bg-accent text-white'
                          : 'rounded-2xl rounded-bl-md border border-line bg-card text-ink'
                      )}
                    >
                      {!mine && firstOfRun && (
                        <div className="mb-0.5 text-[11px] font-semibold text-accent">{m.author}</div>
                      )}
                      <div className="whitespace-pre-wrap break-words">{m.body}</div>
                      <div
                        className={cn(
                          'mt-1 text-right text-[10px] tabular-nums',
                          mine ? 'text-white/60' : 'text-gray-lt'
                        )}
                      >
                        {timeOf(m.createdAt)}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Composer — padded above the phone / Telegram home indicator */}
        <form
          onSubmit={submit}
          className="flex items-center gap-2 border-t border-line bg-surface px-3 pt-3"
          style={{
            paddingBottom:
              'calc(max(env(safe-area-inset-bottom, 0px), var(--tg-content-safe-area-inset-bottom, 0px)) + 30px)',
          }}
        >
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={placeholder}
            className="min-w-0 flex-1 rounded-full border border-line bg-card px-4 py-2.5 text-[15px] text-ink outline-none transition focus:border-accent placeholder:text-gray-lt"
          />
          <button
            type="submit"
            disabled={!text.trim() || busy}
            className="btn-motion flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent text-white shadow-sm transition disabled:opacity-40"
            aria-label="send"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  )
}
