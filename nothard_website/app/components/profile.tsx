// /app/profile/page.tsx

'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { useToast } from "../components/ui/use-toast";

type UserProfile = {
  user_id: number | null;
  name: string;
  phone: string;
  email: string;
  website_id: number | null;
  telegram_linked: boolean; // Добавленное поле для статуса Telegram
};

function ProfileContent() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [telegramToken, setTelegramToken] = useState<string | null>(null);
  const router = useRouter();
  const { toast } = useToast();

  // Получите API URL и имя бота из переменных окружения
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME;

  const searchParams = useSearchParams();
  const loginToken = searchParams.get('login_token');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        let user_id = localStorage.getItem('user_id');
        let website_id = localStorage.getItem('website_id');

        if (loginToken) {
          const response = await fetch(`${apiUrl}/validate_login_token`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ login_token: loginToken }),
          });
          const data = await response.json();
          if (response.ok) {
            user_id = data.user_id;
            if (user_id) {
              localStorage.setItem('user_id', user_id.toString());
            } else {
              toast({
                title: "Ошибка",
                description: "Не удалось получить user_id",
                variant: "destructive",
              });
              return;
            }
            router.replace('/profile'); // Удалите login_token из URL
          } else {
            toast({
              title: "Ошибка",
              description: data.error || "Не удалось войти",
              variant: "destructive",
            });
            return;
          }
        }

        if (!user_id && !website_id) {
          router.push('/login');
          return;
        }

        const id = user_id || website_id;

        const response = await fetch(`${apiUrl}/profile/${id}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (response.ok) {
          const data = await response.json();
          setProfile(data);
        } else {
          const errorData = await response.json();
          toast({
            title: "Ошибка",
            description: errorData.error || "Не удалось загрузить профиль",
            variant: "destructive",
          });
        }
      } catch (error) {
        toast({
          title: "Ошибка",
          description: "Произошла ошибка при загрузке профиля",
          variant: "destructive",
        });
      }
    };

    fetchProfile();
  }, [apiUrl, router, toast, loginToken]);

  const handleLogout = () => {
    localStorage.removeItem('user_id');
    localStorage.removeItem('website_id');
    router.push('/login');
  };

  const handleTelegramLink = async () => {
    try {
      const websiteId = localStorage.getItem('website_id');
      if (!websiteId) {
        toast({
          title: "Ошибка",
          description: "Не удалось найти ваш Website ID. Пожалуйста, войдите снова.",
          variant: "destructive",
        });
        router.push('/login');
        return;
      }
      const response = await fetch(`${apiUrl}/telegram_auth_request`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'link', website_id: websiteId }),
      });
      const data = await response.json();
      if (response.ok) {
        const telegramToken = data.token;
        setTelegramToken(telegramToken);
        const telegramLinkUrl = `https://t.me/${botUsername}?start=${telegramToken}`;
        // Перенаправление пользователя в Telegram бота
        window.location.href = telegramLinkUrl;
      } else {
        toast({
          title: "Ошибка",
          description: data.error,
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Ошибка",
        description: "Произошла ошибка при связывании с Telegram",
        variant: "destructive",
      });
    }
  };

  // Проверка статуса связывания с Telegram
  useEffect(() => {
    let interval: NodeJS.Timeout;

    const checkTelegramLink = async () => {
      try {
        const response = await fetch(`${apiUrl}/check_telegram_auth`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token: telegramToken }),
        });
        const data = await response.json();
        if (response.ok && data.authenticated) {
          localStorage.setItem('user_id', data.user_id.toString());
          toast({
            title: "Telegram связан",
            description: "Ваш аккаунт успешно связан с Telegram!",
          });
          // Обновите профиль
          setProfile(prevProfile => prevProfile ? { ...prevProfile, user_id: data.user_id } : prevProfile);
          clearInterval(interval);
        } else if (response.ok && !data.authenticated) {
          // Всё ещё ожидается связывание
        } else {
          // Обработка ошибок
          toast({
            title: "Ошибка",
            description: data.error || "Ошибка при проверке связывания",
            variant: "destructive",
          });
          clearInterval(interval);
        }
      } catch (error) {
        // Обработка ошибок
        console.error(error);
        clearInterval(interval);
      }
    };

    if (telegramToken) {
      interval = setInterval(checkTelegramLink, 5000); // Проверять каждые 5 секунд
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [telegramToken, apiUrl, router, toast]);

  if (!profile) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  const isTelegramLinked = profile.user_id !== null;

  return (
    <div className="flex flex-col items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md mx-auto">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Профиль пользователя</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500">Имя</h3>
              <p className="mt-1 text-sm text-gray-900">{profile.name}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Телефон</h3>
              <p className="mt-1 text-sm text-gray-900">{profile.phone}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Email</h3>
              <p className="mt-1 text-sm text-gray-900">{profile.email}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Website ID</h3>
              <p className="mt-1 text-sm text-gray-900">{profile.website_id || "Не установлен"}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Telegram</h3>
              <p className="mt-1 text-sm text-gray-900">
                {isTelegramLinked ? "Аккаунт связан" : "Аккаунт не связан"}
              </p>
              {!isTelegramLinked && (
                <Button onClick={handleTelegramLink} className="mt-2">
                  Связать с Telegram
                </Button>
              )}
            </div>
            <Button onClick={handleLogout} className="w-full mt-4">Выйти</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function Profile() {
  return (
    <Suspense fallback={<div className="flex justify-center items-center h-screen">Loading...</div>}>
      <ProfileContent />
    </Suspense>
  )
}
