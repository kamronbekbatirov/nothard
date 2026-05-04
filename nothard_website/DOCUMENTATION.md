# Документация проекта nothard_website

## Обзор проекта

`nothard_website` — это веб-приложение на базе Next.js 16, предназначенное для предоставления услуг по релокации в Лондон. Проект включает фронтенд на React/TypeScript и бэкенд API на Flask (Python).

## Технологический стек

### Фронтенд
- **Next.js 16.1.1** — React-фреймворк с App Router
- **React 19.2.3** — библиотека для создания пользовательского интерфейса
- **TypeScript 5.0.4** — типизированный JavaScript
- **Tailwind CSS 3.4.13** — утилитарный CSS-фреймворк
- **Radix UI** — компоненты UI (Dialog, Select, Checkbox, Toast и др.)
- **Lucide React** — иконки

### Бэкенд
- **Flask** — веб-фреймворк Python
- **SQLite** — база данных
- **Redis** — кэширование и хранение токенов
- **bcrypt** — хеширование паролей
- **Flask-CORS** — обработка CORS-запросов

## Структура проекта

```
nothard_website/
├── app/                          # Next.js App Router директория
│   ├── admin/                    # Админ-панель
│   │   └── page.tsx
│   ├── agency/                   # Панель агентства
│   │   └── page.tsx
│   ├── components/               # React компоненты
│   │   ├── cart.tsx             # Корзина покупок
│   │   ├── footer.tsx           # Футер сайта
│   │   ├── landing-page.tsx    # Главная страница
│   │   ├── navbar.tsx           # Навигационная панель
│   │   ├── profile.tsx          # Профиль пользователя
│   │   └── ui/                  # UI компоненты (shadcn/ui)
│   │       ├── badge.tsx
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── checkbox.tsx
│   │       ├── dialog.tsx
│   │       ├── input.tsx
│   │       ├── label.tsx
│   │       ├── scroll-area.tsx
│   │       ├── select.tsx
│   │       ├── separator.tsx
│   │       ├── toast.tsx
│   │       ├── toaster.tsx
│   │       └── use-toast.ts
│   ├── globals.css               # Глобальные стили
│   ├── layout.tsx                # Корневой layout
│   ├── lib/                      # Утилиты
│   │   └── utils.ts
│   ├── login/                    # Страница входа
│   │   └── page.tsx
│   ├── page.tsx                  # Главная страница (роутинг)
│   ├── profile/                  # Страница профиля
│   │   └── page.tsx
│   ├── register/                 # Страница регистрации
│   │   └── page.tsx
│   ├── runner/                   # Панель раннера
│   │   └── page.tsx
│   └── search/                   # Страница поиска
│       └── page.tsx
├── .next/                        # Собранные файлы Next.js (генерируется)
├── favicon/                      # Иконки сайта
│   ├── favicon.ico
│   ├── favicon-16x16.png
│   ├── favicon-32x32.png
│   ├── apple-touch-icon.png
│   ├── android-chrome-192x192.png
│   ├── android-chrome-512x512.png
│   └── site.webmanifest
├── lib/                          # Общие утилиты
│   └── utils.ts
├── public/                       # Статические файлы
│   ├── favicon.ico
│   ├── placeholder.svg
│   └── scraped_properties.json   # Данные о недвижимости
├── app.py                        # Flask API сервер
├── property_typefinder.py        # Утилита для классификации типов недвижимости
├── agency_platform.db            # База данных SQLite
├── package.json                  # Зависимости Node.js
├── package-lock.json
├── tsconfig.json                 # Конфигурация TypeScript
├── next.config.js                # Конфигурация Next.js
├── tailwind.config.js            # Конфигурация Tailwind CSS
├── postcss.config.js             # Конфигурация PostCSS
└── .env.local                    # Переменные окружения (локальные)

```

## Основные компоненты

### Фронтенд компоненты

#### 1. **Landing Page** (`app/components/landing-page.tsx`)
Главная страница сайта с:
- Поиском недвижимости (бюджет, количество комнат, зоны)
- Каталогом пакетов услуг
- Каталогом отдельных услуг
- Корзиной покупок
- Интеграцией с Telegram для авторизации

#### 2. **Navbar** (`app/components/navbar.tsx`)
Навигационная панель с:
- Логотипом и меню
- Авторизацией через Telegram
- Корзиной покупок
- Профилем пользователя

#### 3. **Cart** (`app/components/cart.tsx`)
Компонент корзины для управления выбранными услугами и пакетами.

#### 4. **Profile** (`app/components/profile.tsx`)
Компонент профиля пользователя с возможностью редактирования данных.

#### 5. **Footer** (`app/components/footer.tsx`)
Футер сайта с контактной информацией и ссылками.

### UI компоненты (shadcn/ui)

Проект использует библиотеку компонентов shadcn/ui на базе Radix UI:
- **Button** — кнопки
- **Card** — карточки
- **Input** — поля ввода
- **Select** — выпадающие списки
- **Checkbox** — чекбоксы
- **Dialog** — модальные окна
- **Toast** — уведомления
- **Badge** — бейджи
- **Scroll Area** — прокручиваемые области
- **Separator** — разделители

## Страницы (Routes)

### Публичные страницы
- `/` — главная страница (Landing Page)
- `/login` — страница входа
- `/register` — страница регистрации
- `/search` — страница поиска недвижимости
- `/profile` — профиль пользователя

### Защищенные страницы
- `/admin` — админ-панель (требует роль `admin`)
- `/agency` — панель агентства (требует роль `agency`)
- `/runner` — панель раннера (требует роль `runner`)

## Backend API (Flask)

### Основные эндпоинты

#### Аутентификация и авторизация
- `POST /telegram_auth_request` — запрос токена для авторизации через Telegram
- `POST /telegram_auth_confirm` — подтверждение авторизации через Telegram
- `POST /check_telegram_auth` — проверка статуса авторизации
- `POST /login` — вход по email/паролю
- `POST /register` — регистрация нового пользователя
- `POST /validate_login_token` — валидация токена входа

#### Профиль пользователя
- `GET /profile/<user_id>` — получение профиля пользователя
- `POST /update_profile` — обновление профиля

#### CRM API — Студенты
- `GET /api/students` — получение списка студентов
- `POST /api/students` — создание нового студента
- `PUT /api/students/<student_id>` — обновление данных студента
- `DELETE /api/students/<student_id>` — удаление студента
- `PUT /api/students/<student_id>/archive` — архивация студента
- `PUT /api/students/<student_id>/unarchive` — разархивация студента
- `GET /api/students/archived` — получение архивированных студентов

#### CRM API — Заявки на услуги
- `GET /api/service-requests` — получение заявок
- `POST /api/service-requests` — создание новой заявки
- `PUT /api/service-requests/<request_id>` — обновление заявки
- `DELETE /api/service-requests/<request_id>` — удаление заявки
- `PUT /api/service-requests/<request_id>/status` — обновление статуса заявки
- `PUT /api/service-requests/<request_id>/payment-status` — обновление статуса оплаты

#### CRM API — Задачи
- `GET /api/service-requests/<request_id>/tasks` — получение задач для заявки
- `PUT /api/tasks/<task_id>/status` — обновление статуса задачи

#### CRM API — Недвижимость
- `GET /api/tasks/<task_id>/properties` — получение объектов недвижимости для задачи
- `POST /api/tasks/<task_id>/properties` — добавление объекта недвижимости
- `PUT /api/properties/<property_id>` — обновление информации об объекте
- `PUT /api/properties/<property_id>/status` — обновление статуса объекта
- `PUT /api/properties/<property_id>/select-viewing` — выбор объекта для просмотра

#### CRM API — Услуги
- `GET /api/service-types` — получение типов услуг
- `GET /api/custom-services` — получение кастомных услуг агентства
- `POST /api/custom-services` — создание кастомной услуги

#### CRM API — Агентства
- `GET /api/agencies` — получение списка агентств
- `POST /api/agencies` — создание нового агентства
- `PUT /api/agencies/<agency_id>` — обновление агентства
- `DELETE /api/agencies/<agency_id>` — удаление агентства
- `GET /api/agencies/<agency_id>/pricing` — получение цен агентства
- `POST /api/agencies/<agency_id>/pricing` — установка цен агентства
- `POST /api/agencies/<agency_id>/custom-services` — добавление кастомной услуги

#### CRM API — Раннеры
- `GET /api/runners` — получение списка раннеров
- `POST /api/assign-runner` — назначение раннера на заявку

#### Админ API
- `GET /api/admin/full-data` — получение всех данных для админ-панели
- `PUT /api/users/<user_id>` — обновление пользователя
- `PUT /api/users/<user_id>/role` — обновление роли пользователя

## База данных

Проект использует SQLite базу данных (`agency_platform.db`). Основные таблицы:

- **users** — пользователи системы
- **students** — студенты
- **agencies** — агентства
- **service_types** — типы услуг
- **service_requests** — заявки на услуги
- **tasks** — задачи по заявкам
- **property_listings** — объекты недвижимости
- **agency_service_pricing** — индивидуальные цены агентств
- **agency_custom_services** — кастомные услуги агентств
- **request_status_history** — история изменений статусов заявок
- **request_files** — файлы, прикрепленные к заявкам
- **orders** — заказы
- **income** — доходы
- **expenses** — расходы

## Конфигурация

### Next.js (`next.config.js`)
- Настроены remote patterns для загрузки изображений с:
  - `media.rightmove.co.uk`
  - `*.rightmove.co.uk`
  - `lc.zoocdn.com`
  - `lid.zoocdn.com`
- Отключена оптимизация изображений (`unoptimized: true`)

### TypeScript (`tsconfig.json`)
- Строгий режим включен
- Поддержка JSX
- Пути настроены для использования `@/*` алиаса

### Tailwind CSS (`tailwind.config.js`)
- Настроена темная тема (class-based)
- Кастомные цвета и переменные CSS
- Анимации для аккордеонов
- Плагин `tailwindcss-animate`

## Утилиты

### `property_typefinder.py`
Python-скрипт для классификации типов недвижимости:
- Маппинг различных названий типов недвижимости в канонические категории
- Поддерживаемые типы: `detached`, `semi-detached`, `terraced`, `flat`
- Функция подсчета объектов по типам из JSON-файла

## Переменные окружения

Проект использует следующие переменные окружения (в `.env.local`):
- `REDIS_HOST` — хост Redis
- `REDIS_PORT` — порт Redis
- `REDIS_PASSWORD` — пароль Redis
- `BOT_TOKEN` — токен Telegram бота
- `BOT_USERNAME` — username Telegram бота
- `API_URL` — URL API сервера

## Роли пользователей

Система поддерживает следующие роли:
- **student** — студент
- **agency** — агентство
- **runner** — раннер (исполнитель услуг)
- **admin** — администратор

## Особенности

1. **Интеграция с Telegram** — авторизация через Telegram бота
2. **Многоязычность** — поддержка русского языка
3. **CRM система** — управление студентами, заявками, задачами
4. **Управление недвижимостью** — поиск и управление объектами недвижимости
5. **Индивидуальные цены** — агентства могут устанавливать свои цены на услуги
6. **Кастомные услуги** — агентства могут создавать собственные услуги
7. **Архивация** — возможность архивировать студентов и их заявки
8. **Workflow статусы** — настраиваемые статусы для разных типов услуг

## Запуск проекта

### Фронтенд (Next.js)
```bash
npm install
npm run dev      # Режим разработки
npm run build    # Сборка для продакшена
npm start        # Запуск продакшен версии
```

### Бэкенд (Flask)
```bash
python app.py
```

## Зависимости

### Основные зависимости (package.json)
- `next` — фреймворк Next.js
- `react` и `react-dom` — React библиотеки
- `@radix-ui/*` — UI компоненты
- `tailwindcss` — CSS фреймворк
- `lucide-react` — иконки
- `class-variance-authority` — управление вариантами компонентов
- `clsx` и `tailwind-merge` — утилиты для работы с классами

### Python зависимости (app.py)
- `flask` — веб-фреймворк
- `flask-cors` — CORS поддержка
- `sqlite3` — база данных (встроенная)
- `bcrypt` — хеширование паролей
- `redis` — Redis клиент
- `python-dotenv` — загрузка переменных окружения

## Структура данных

### Пользователь (users)
- `id` — внутренний ID
- `user_id` — Telegram user ID
- `website_id` — ID для веб-сайта
- `name` — имя
- `email` — email
- `phone` — телефон
- `role` — роль (student/agency/runner/admin)
- `password_hash` — хеш пароля
- `bonuses` — бонусы
- `language` — язык интерфейса

### Студент (students)
- `student_id` — ID студента
- `first_name`, `last_name` — имя и фамилия
- `date_of_birth` — дата рождения
- `nationality` — национальность
- `passport_number` — номер паспорта
- `email`, `phone` — контакты
- `telegram_username` — Telegram username
- `university` — университет
- `city` — город
- `course` — курс
- `start_date`, `end_date` — даты обучения
- `agency_id` — ID агентства
- `archived` — флаг архивации

### Заявка на услугу (service_requests)
- `request_id` — ID заявки
- `student_id` — ID студента
- `agency_id` — ID агентства
- `service_type_id` — ID типа услуги
- `title` — название
- `description` — описание
- `status` — статус (new/assigned/in_progress/completed/cancelled)
- `priority` — приоритет (low/medium/high/urgent)
- `price` — цена
- `payment_status` — статус оплаты (paid/unpaid/partial)
- `runner_id` — ID назначенного раннера
- `scheduled_date` — запланированная дата
- `location` — местоположение
- `notes` — заметки

## Безопасность

1. **Хеширование паролей** — используется bcrypt
2. **CORS** — настроен для домена `https://nothard.uz`
3. **Токены** — временные токены с истечением срока действия (5 минут)
4. **Валидация данных** — проверка обязательных полей на сервере
5. **Роли и права доступа** — разграничение доступа по ролям

## Дальнейшее развитие

Возможные улучшения:
- Добавление больше типов услуг
- Расширение функционала поиска недвижимости
- Интеграция с платежными системами
- Улучшение UI/UX
- Добавление аналитики и отчетов
- Мобильное приложение
- Расширение интеграции с Telegram

---

**Версия документации:** 1.0  
**Дата создания:** 27 января 2026
