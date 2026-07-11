import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/app/lib/utils'

const button = cva(
  'btn-motion inline-flex items-center justify-center gap-2 font-semibold whitespace-nowrap disabled:pointer-events-none disabled:opacity-50 select-none',
  {
    variants: {
      variant: {
        // Solid green — primary CTA (white text on green in both themes)
        solid: 'bg-accent text-white',
        // Outline on the page surface
        outline: 'border border-line bg-transparent text-ink hover:border-accent/60',
        // High-emphasis fill that inverts (dark on light theme, light on dark)
        dark: 'bg-inverse text-inverse-fg',
        // Fixed light button — sits on colored / dark blocks in both themes
        white: 'bg-[#f4f1ea] text-[#1b1a17]',
        // Subtle
        soft: 'bg-accent-bg text-accent',
        // Text-only
        ghost: 'bg-transparent text-ink-2 hover:text-accent',
        // Destructive / terracotta
        danger: 'bg-terracotta text-white',
      },
      size: {
        sm: 'text-[13px] px-3.5 py-2 rounded-md',
        md: 'text-[14px] px-[18px] py-[11px] rounded-md',
        lg: 'text-[15px] px-6 py-[13px] rounded-lg',
        block: 'text-[15px] px-6 py-[13px] rounded-lg w-full',
      },
    },
    defaultVariants: { variant: 'solid', size: 'md' },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof button> {
  asChild?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'
    return <Comp ref={ref} className={cn(button({ variant, size }), className)} {...props} />
  }
)
Button.displayName = 'Button'
