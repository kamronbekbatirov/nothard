// /app/register/page.tsx

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "../components/ui/card"
import { useToast } from "../components/ui/use-toast"
import { Navbar } from "../components/navbar"
import { Footer } from "../components/footer"

export default function RegisterPage() {
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [telegramToken, setTelegramToken] = useState<string | null>(null)
  const router = useRouter()
  const { toast } = useToast()

  // Get API URL and Telegram Bot Username from environment variables
  const apiUrl = process.env.NEXT_PUBLIC_API_URL
  const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (password !== confirmPassword) {
      toast({
        title: "Ошибка",
        description: "Пароли не совпадают",
        variant: "destructive",
      })
      return
    }
    try {
      const response = await fetch(`${apiUrl}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, phone, email, password }),
      })
      const data = await response.json()
      if (response.ok) {
        console.log('Ответ от API:', data);
        localStorage.setItem('website_id', data.website_id.toString());
        toast({
          title: "Регистрация успешна",
          description: "Вы успешно зарегистрировались.",
        });
        router.push('/login');
      } else {
        toast({
          title: "Ошибка",
          description: data.error,
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Произошла ошибка при регистрации",
        variant: "destructive",
      })
    }
  }

  const handleTelegramRegister = async () => {
    try {
      const websiteId = localStorage.getItem('website_id')
      if (!websiteId) {
        toast({
          title: "Ошибка",
          description: "Пожалуйста, зарегистрируйтесь перед связыванием с Telegram.",
          variant: "destructive",
        })
        return
      }
      const response = await fetch(`${apiUrl}/telegram_auth_request`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'link', website_id: websiteId }),
      })
      const data = await response.json()
      if (response.ok) {
        const telegramToken = data.token
        setTelegramToken(telegramToken)
        const telegramLinkUrl = `https://t.me/${botUsername}?start=${telegramToken}`
        // Redirect the user to the Telegram bot with the token
        window.location.href = telegramLinkUrl
      } else {
        toast({
          title: "Ошибка",
          description: data.error,
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Произошла ошибка при связывании с Telegram",
        variant: "destructive",
      })
    }
  }

  // Polling to check if the user has linked their account via Telegram
  useEffect(() => {
    let interval: NodeJS.Timeout

    const checkTelegramLink = async () => {
      try {
        const response = await fetch(`${apiUrl}/check_telegram_auth`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token: telegramToken }),
        })
        const data = await response.json()
        if (response.ok && data.authenticated) {
          localStorage.setItem('user_id', data.user_id.toString())
          toast({
            title: "Telegram связан",
            description: "Ваш аккаунт успешно связан с Telegram!",
          })
          router.push('/profile')
        } else if (response.ok && !data.authenticated) {
          // Still waiting for linking
        } else {
          // Handle errors
          toast({
            title: "Ошибка",
            description: data.error || "Ошибка при проверке связывания",
            variant: "destructive",
          })
          clearInterval(interval)
        }
      } catch (error) {
        // Handle errors
        console.error(error)
        clearInterval(interval)
      }
    }

    if (telegramToken) {
      interval = setInterval(checkTelegramLink, 5000) // Check every 5 seconds
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [telegramToken, apiUrl, router, toast])

  const handleGmailRegister = () => {
    toast({
      title: "Gmail Registration",
      description: "Функция регистрации через Gmail еще не реализована",
    })
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar cartItemsCount={0} onCartClick={() => {}} />
      <main className="flex-grow flex items-center justify-center bg-gray-100 py-12">
        <Card className="w-[350px]">
          <CardHeader>
            <CardTitle>Регистрация</CardTitle>
            <CardDescription>Создайте новый аккаунт</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <div className="grid w-full items-center gap-4">
                <div className="flex flex-col space-y-1.5">
                  <Label htmlFor="name">Имя</Label>
                  <Input 
                    id="name" 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
                <div className="flex flex-col space-y-1.5">
                  <Label htmlFor="phone">Телефон</Label>
                  <Input 
                    id="phone" 
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    required
                  />
                </div>
                <div className="flex flex-col space-y-1.5">
                  <Label htmlFor="email">Email</Label>
                  <Input 
                    id="email" 
                    type="email" 
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="flex flex-col space-y-1.5">
                  <Label htmlFor="password">Пароль</Label>
                  <Input 
                    id="password" 
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="flex flex-col space-y-1.5">
                  <Label htmlFor="confirmPassword">Подтвердите пароль</Label>
                  <Input 
                    id="confirmPassword" 
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                  />
                </div>
              </div>
              <Button className="w-full mt-4" type="submit">Зарегистрироваться</Button>
            </form>
            <div className="mt-4 flex justify-between">
              <Button variant="outline" className="w-[48%]" onClick={handleTelegramRegister}>
                {/* Telegram SVG */}
                <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="none">
                  <path d="M12 0C5.371 0 0 5.371 0 12C0 18.629 5.371 24 12 24C18.629 24 24 18.629 24 12C24 5.371 18.629 0 12 0ZM17.841 7.921C17.683 9.759 16.838 14.838 16.418 17.159C16.239 18.157 15.902 18.478 15.58 18.516C14.88 18.601 14.359 18.081 13.699 17.638C12.659 16.916 12.081 16.476 11.081 15.779C9.941 14.979 10.679 14.537 11.339 13.862C11.517 13.682 14.441 11.019 14.5 10.756C14.507 10.727 14.507 10.693 14.5 10.66C14.493 10.627 14.48 10.593 14.46 10.56C14.421 10.5 14.361 10.519 14.301 10.539C14.241 10.559 12.659 11.598 9.559 13.656C9.059 13.996 8.619 14.156 8.219 14.139C7.779 14.119 6.919 13.878 6.279 13.656C5.499 13.398 4.879 13.258 4.939 12.822C4.979 12.603 5.279 12.379 5.859 12.159C9.179 10.722 11.44 9.76 12.619 9.279C15.959 7.883 16.638 7.638 17.1 7.638C17.2 7.638 17.439 7.659 17.599 7.798C17.739 7.898 17.799 8.057 17.82 8.197C17.82 8.297 17.84 8.597 17.841 7.921Z" fill="#229ED9"/>
                </svg>
                Telegram
              </Button>
              <Button variant="outline" className="w-[48%]" onClick={handleGmailRegister}>
                {/* Google SVG */}
                <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="none">
                  <path d="M21.805 10.042H21V10H12V14H17.651C16.827 16.329 14.611 18 12 18C8.686 18 6 15.314 6 12C6 8.686 8.686 6 12 6C13.529 6 14.921 6.577 15.981 7.519L18.809 4.691C17.023 3.027 14.634 2 12 2C6.478 2 2 6.478 2 12C2 17.522 6.478 22 12 22C17.522 22 22 17.522 22 12C22 11.33 21.931 10.675 21.805 10.042Z" fill="#FFC107"/>
                  <path d="M3.153 7.346L6.438 9.755C7.327 7.554 9.48 6 12 6C13.529 6 14.921 6.577 15.981 7.519L18.809 4.691C17.023 3.027 14.634 2 12 2C8.159 2 4.828 4.169 3.153 7.346Z" fill="#FF3D00"/>
                  <path d="M12 22C14.583 22 16.93 21.012 18.705 19.404L15.609 16.785C14.572 17.574 13.304 18.001 12 18C9.399 18 7.191 16.342 6.359 14.027L3.098 16.54C4.753 19.778 8.114 22 12 22Z" fill="#4CAF50"/>
                  <path d="M12 22C14.583 22 16.93 21.012 18.705 19.404L15.609 16.785C14.572 17.574 13.304 18.001 12 18C9.399 18 7.191 16.342 6.359 14.027L3.098 16.54C4.753 19.778 8.114 22 12 22Z" fill="#1976D2"/>
                </svg>
                Google
              </Button>
            </div>
          </CardContent>
          <CardFooter className="flex justify-center">
            <p className="text-sm text-gray-600">
              Уже есть аккаунт?{" "}
              <Link href="/login" className="text-blue-600 hover:underline">
                Войти
              </Link>
            </p>
          </CardFooter>
        </Card>
      </main>
      <Footer />
    </div>
  )
}