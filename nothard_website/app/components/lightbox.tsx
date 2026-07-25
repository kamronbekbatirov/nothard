'use client'

import { useCallback, useEffect } from 'react'
import { ChevronLeft, ChevronRight, X } from 'lucide-react'

/**
 * Fullscreen photo viewer. Give it a list of image URLs and the index to open
 * at; pass `index = null` to close. Keyboard: ← / → navigate, Esc closes; the
 * backdrop and the × button also close.
 */
export function Lightbox({
  photos,
  index,
  onIndex,
  onClose,
}: {
  photos: string[]
  index: number | null
  onIndex: (i: number) => void
  onClose: () => void
}) {
  const open = index !== null && photos.length > 0
  const go = useCallback(
    (delta: number) => {
      if (index === null) return
      onIndex((index + delta + photos.length) % photos.length)
    },
    [index, photos.length, onIndex]
  )

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      else if (e.key === 'ArrowLeft') go(-1)
      else if (e.key === 'ArrowRight') go(1)
    }
    window.addEventListener('keydown', onKey)
    // Lock body scroll while open.
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [open, go, onClose])

  if (!open || index === null) return null
  const many = photos.length > 1

  return (
    <div
      className="fixed inset-0 z-[100000] flex items-center justify-center bg-black/90 p-4"
      onClick={onClose}
    >
      <button
        aria-label="close"
        onClick={onClose}
        className="absolute right-4 top-4 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20"
      >
        <X size={20} />
      </button>

      {many && (
        <button
          aria-label="previous"
          onClick={(e) => {
            e.stopPropagation()
            go(-1)
          }}
          className="absolute left-3 flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20 sm:left-6"
        >
          <ChevronLeft size={24} />
        </button>
      )}

      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={photos[index]}
        alt=""
        onClick={(e) => e.stopPropagation()}
        className="max-h-[90vh] max-w-[92vw] rounded-lg object-contain"
        referrerPolicy="no-referrer"
      />

      {many && (
        <button
          aria-label="next"
          onClick={(e) => {
            e.stopPropagation()
            go(1)
          }}
          className="absolute right-3 flex h-11 w-11 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20 sm:right-6"
        >
          <ChevronRight size={24} />
        </button>
      )}

      {many && (
        <div className="absolute bottom-5 left-1/2 -translate-x-1/2 rounded-full bg-white/10 px-3 py-1 text-[12.5px] text-white">
          {index + 1} / {photos.length}
        </div>
      )}
    </div>
  )
}
