'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Button } from './ui/button'
import { Menu, X, ShoppingCart, User, LogOut } from 'lucide-react'
import { Badge } from './ui/badge'
import { ModeToggle } from './mode-toggle'

interface NavbarProps {
  cartItemsCount: number
  onCartClick: () => void
}

export function Navbar({ cartItemsCount, onCartClick }: NavbarProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userRole, setUserRole] = useState<string>('')
  const [userName, setUserName] = useState<string>('')
  const router = useRouter()

  useEffect(() => {
    const checkLoginStatus = () => {
      const userId = localStorage.getItem('user_id')
      const role = localStorage.getItem('user_role') || ''
      const name = localStorage.getItem('user_name') || ''
      setIsLoggedIn(!!userId)
      setUserRole(role)
      setUserName(name)
    }

    checkLoginStatus()
    window.addEventListener('storage', checkLoginStatus)
    return () => window.removeEventListener('storage', checkLoginStatus)
  }, [])

  const handleNavigation = (section: string) => {
    router.push(`/?section=${section}`)
  }

  const handleLogout = () => {
    localStorage.removeItem('user_id')
    localStorage.removeItem('website_id')
    localStorage.removeItem('user_role')
    localStorage.removeItem('user_name')
    setIsLoggedIn(false)
    setUserRole('')
    setUserName('')
    router.push('/login')
  }

  const getRoleBasedDashboard = () => {
    switch (userRole) {
      case 'admin':
        return { link: '/admin', label: 'Админ панель' }
      case 'agency':
        return { link: '/agency', label: 'Панель агентства' }
      case 'runner':
        return { link: '/runner', label: 'Панель раннера' }
      default:
        return { link: '/profile', label: 'Профиль' }
    }
  }

  return (
    <nav className="border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex flex-wrap items-center justify-between px-4 py-3">
        <div className="flex items-center space-x-2">
          <Link href="/" className="text-xl font-bold tracking-tight sm:text-2xl">
            Nothard
          </Link>
          <Button variant="ghost" className="hidden lg:inline-flex" onClick={() => handleNavigation('packages')}>
            Пакеты
          </Button>
          <Button variant="ghost" className="hidden lg:inline-flex" onClick={() => handleNavigation('services')}>
            Индивидуальные услуги
          </Button>
        </div>
        <div className="flex items-center space-x-2 sm:space-x-3">
          {isLoggedIn ? (
            <>
              <Link href={getRoleBasedDashboard().link} passHref>
                <Button variant="outline" className="hidden sm:inline-flex">
                  <User className="mr-2 h-4 w-4" />
                  {getRoleBasedDashboard().label}
                </Button>
              </Link>
              {userName && (
                <span className="hidden text-sm text-muted-foreground sm:inline-flex">
                  Привет, {userName.split(' ')[0]}
                </span>
              )}
              <Button variant="outline" className="hidden sm:inline-flex" onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Выйти
              </Button>
            </>
          ) : (
            <>
              <Link href="/login" passHref>
                <Button variant="outline" className="hidden sm:inline-flex">
                  Вход
                </Button>
              </Link>
              <Link href="/register" passHref>
                <Button variant="outline" className="hidden sm:inline-flex">
                  Регистрация
                </Button>
              </Link>
            </>
          )}
          <Button className="hidden sm:inline-flex">Связаться с нами</Button>
          <ModeToggle />
          <div className="relative">
            <Button variant="ghost" size="icon" onClick={onCartClick} aria-label="Корзина">
              <ShoppingCart className="h-5 w-5" />
              {cartItemsCount > 0 && (
                <Badge variant="destructive" className="absolute -right-2 -top-2">
                  {cartItemsCount}
                </Badge>
              )}
            </Button>
          </div>
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setIsMenuOpen(!isMenuOpen)} aria-label="Меню">
            {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>
      {isMenuOpen && (
        <div className="container mx-auto space-y-2 px-4 pb-4 lg:hidden">
          <Button variant="ghost" className="w-full justify-start" onClick={() => handleNavigation('packages')}>
            Пакеты
          </Button>
          <Button variant="ghost" className="w-full justify-start" onClick={() => handleNavigation('services')}>
            Индивидуальные услуги
          </Button>
          {isLoggedIn ? (
            <>
              <Link href={getRoleBasedDashboard().link} passHref>
                <Button variant="outline" className="w-full">
                  {getRoleBasedDashboard().label}
                </Button>
              </Link>
              {userName && (
                <div className="py-2 text-center text-sm text-muted-foreground">Привет, {userName}</div>
              )}
              <Button variant="outline" className="w-full" onClick={handleLogout}>
                Выйти
              </Button>
            </>
          ) : (
            <>
              <Link href="/login" passHref>
                <Button variant="outline" className="w-full">
                  Вход
                </Button>
              </Link>
              <Link href="/register" passHref>
                <Button variant="outline" className="w-full">
                  Регистрация
                </Button>
              </Link>
            </>
          )}
          <Button className="w-full">Связаться с нами</Button>
        </div>
      )}
    </nav>
  )
}
