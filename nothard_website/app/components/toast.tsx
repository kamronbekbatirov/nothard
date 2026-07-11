'use client'

import { createContext, useCallback, useContext, useEffect, useState } from 'react'

type ToastItem = { id: number; message: string }
type ToastCtx = { toast: (message: string) => void }

const Ctx = createContext<ToastCtx>({ toast: () => {} })

export function useToast() {
  return useContext(Ctx)
}

/** Bottom-center ink toast (matches prototype .nd-toast). ~2.4s visible. */
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])

  const toast = useCallback((message: string) => {
    const id = Date.now() + Math.random()
    setItems((prev) => [...prev, { id, message }])
    window.setTimeout(() => {
      setItems((prev) => prev.filter((t) => t.id !== id))
    }, 2600)
  }, [])

  return (
    <Ctx.Provider value={{ toast }}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-7 z-[99999] flex flex-col items-center gap-2 px-4">
        {items.map((t) => (
          <ToastView key={t.id} message={t.message} />
        ))}
      </div>
    </Ctx.Provider>
  )
}

function ToastView({ message }: { message: string }) {
  const [show, setShow] = useState(false)
  useEffect(() => {
    const r = requestAnimationFrame(() => setShow(true))
    const h = window.setTimeout(() => setShow(false), 2350)
    return () => {
      cancelAnimationFrame(r)
      clearTimeout(h)
    }
  }, [])
  return (
    <div
      className="max-w-[340px] rounded-xl bg-inverse px-5 py-3 text-[13.5px] font-semibold leading-snug text-inverse-fg shadow-toast transition-all duration-300"
      style={{
        opacity: show ? 1 : 0,
        transform: show ? 'translateY(0)' : 'translateY(16px)',
      }}
    >
      {message}
    </div>
  )
}
