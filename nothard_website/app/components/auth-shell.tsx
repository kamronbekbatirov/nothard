import { Logo } from './logo'
import { LangSwitcher } from './lang-switcher'

export function AuthShell({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle: string
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <header className="mx-auto flex w-full max-w-[1200px] items-center justify-between px-5 py-5 sm:px-11">
        <Logo size={26} />
        <LangSwitcher />
      </header>

      <main className="flex flex-1 items-center justify-center px-5 py-8">
        <div className="w-full max-w-[420px]">
          <div className="mb-7 text-center">
            <h1 className="font-display text-[30px] text-ink">{title}</h1>
            <p className="mt-2 text-[14.5px] text-muted">{subtitle}</p>
          </div>
          <div className="rounded-2xl border border-line bg-card p-7 shadow-card">
            {children}
          </div>
        </div>
      </main>
    </div>
  )
}
