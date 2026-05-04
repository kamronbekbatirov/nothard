
# bot/handlers/admin.py

import sqlite3
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
import logging

from bot.handlers.common import show_main_menu
from bot.handlers.language import get_message
from bot.utils.database import get_all_feedbacks, get_order_subscribers, get_order_tasks, get_user_language, update_property_status
from bot.utils.notifications import send_notification

logging.basicConfig(level=logging.DEBUG)  # Установите уровень DEBUG для отладки
logger = logging.getLogger(__name__)

# Состояния для обработки админ-панели
ADMIN_PANEL, VIEW_USERS, VIEW_ORDERS, VIEW_FEEDBACK, REQUEST_ORDER_NUMBER, ORDER_ACTIONS, TASKS, PROPERTIES, REQUEST_PROPERTY_CLOUD_LINK, REQUEST_CLOUD_LINK = range(14, 24)
# Add a new state
ADMIN_BACK = 24

CHANGE_PAYMENT_STATUS = 27  # instead of range(26, 27)

ADD_EVENT_DESCRIPTION, ADD_EVENT_LINK, DELETE_EVENT= range(78, 81)
SEND_MESSAGE_TO_USER = 82


# ID администраторов
ADMIN_IDS = [3461866]

async def go_back_to_main_menu_from_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Сбрасываем активность меню отзывов
    context.user_data['admin_menu_active'] = False  
    await show_main_menu(update, context)
    return ConversationHandler.END

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await show_main_menu(update, context)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    try:
        logger.info("admin_panel function called")
        print("admin_panel function called")  # Debug log
        if update.message.from_user.id not in ADMIN_IDS:
            await update.message.reply_text("У вас нет доступа к этому разделу.")
            return ConversationHandler.END

        if context.user_data.get('admin_menu_active', False):
            # Если админка уже активна, просто возвращаем состояние
            return ADMIN_PANEL

        # Включаем флаг активности админки
        context.user_data['admin_menu_active'] = True

        keyboard = [
            [KeyboardButton("Список пользователей")],
            [KeyboardButton("Список заказов")],
            [KeyboardButton("Отзывы")],
            [KeyboardButton("Назад")]
        ]
        await update.message.reply_text("Админ-панель:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        print("Returning to ADMIN_PANEL state")  # Debug log
        return ADMIN_PANEL
    except Exception as e:
        logger.error(f"Error in admin_panel: {e}")
        return ConversationHandler.END

async def view_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("view_feedback function called")  # Debug log
    try:
        feedbacks = get_all_feedbacks()
        print(f"Retrieved feedbacks: {feedbacks}")  # Debug log
        if feedbacks:
            message = "Отзывы:\n\n"
            for feedback in feedbacks:
                message += f"ID пользователя: {feedback['user_id']}\nОтзыв: {feedback['feedback']}\n\n"
        else:
            message = "Отзывов нет."

        await update.message.reply_text(message, reply_markup=admin_panel_keyboard())
        return ADMIN_PANEL
    except Exception as e:
        print(f"Error in view_feedback: {e}")  # Debug log
        await update.message.reply_text("Произошла ошибка при получении отзывов.")
        return ADMIN_PANEL





from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Ключи для статусов
ORDER_STATUS_KEYS = {
    'accepted': 'order_status_accepted',
    'returned': 'order_status_returned',
    'cancelled': 'order_status_cancelled',
    'pending': 'order_status_pending',
    'waiting_payment': 'order_status_waiting_payment',
    'in_progress': 'order_status_in_progress',
    'completed': 'order_status_completed',
}

async def request_order_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        return await admin_panel(update, context)

    try:
        order_id = update.message.text.strip()
        order = get_order_by_id(order_id)
        if not order:
            await update.message.reply_text(
                f"Заказ с номером {order_id} не найден. Попробуйте снова.", 
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Назад")]], resize_keyboard=True)
            )
            return REQUEST_ORDER_NUMBER

        context.user_data['order_id'] = order_id

        # Определение языка пользователя для сообщений
        user_language = get_user_language(order['user_id'])

        # Логируем информацию о языке пользователя и статусе заказа
        logger.debug(f"User language: {user_language}, Order status: {order['status']}")

        # Используем ключ статуса напрямую из базы данных для получения перевода через get_message
        order_status_key = order['status']
        order_status = get_message(user_language, order_status_key)
        logger.debug(f"Order status message: {order_status}")

        # Определяем статус оплаты
        payment_status = get_message(user_language, 'payment_paid') if order.get('paid', 0) else get_message(user_language, 'payment_not_paid')
        logger.debug(f"Payment status: {payment_status}")

        # Метод оплаты с переводом
        payment_method = order.get('payment_method', 'Не указан')
        if payment_method == 'cash':
            payment_method = "💵 " + get_message(user_language, 'payment_method_cash')  # Наличные
        elif payment_method == 'PayMe':
            payment_method = "💳 PayMe"
        logger.debug(f"Payment method: {payment_method}")

        # Преобразование строки в datetime и форматирование даты
        try:
            order_date = datetime.strptime(order['order_date'], '%Y-%m-%dT%H:%M:%S.%f').strftime('%d.%m.%Y %H:%M')
        except ValueError:
            # Если формат даты не соответствует ожиданиям, используем оригинальную строку
            logger.error(f"Date format error for order date: {order['order_date']}")
            order_date = order['order_date']

        # Добавляем эмодзи к информации о заказе
        message = (
            f"📋 Информация о заказе:\n"
            f"🆔 Заказ ID: {order['order_id']}\n"
            f"👤 Пользователь ID: {order['user_id']}\n"
            f"🗓 Дата заказа: {order_date}\n"
            f"📊 Статус заказа: {order_status}\n"
            f"💰 Статус оплаты: {payment_status}\n"
            f"💳 Метод оплаты: {payment_method}\n\n"
            "Выберите действие для этого заказа:"
        )

        # Формируем клавиатуру для администратора
        keyboard = [
            # Блок статусов заказа
            [KeyboardButton(get_message('ru', ORDER_STATUS_KEYS['accepted'])), 
            KeyboardButton(get_message('ru', ORDER_STATUS_KEYS['in_progress']))],
            [KeyboardButton(get_message('ru', ORDER_STATUS_KEYS['waiting_payment'])), 
            KeyboardButton(get_message('ru', ORDER_STATUS_KEYS['completed']))],
            [KeyboardButton(get_message('ru', ORDER_STATUS_KEYS['pending'])), 
            KeyboardButton(get_message('ru', ORDER_STATUS_KEYS['cancelled']))],
            [KeyboardButton(get_message('ru', ORDER_STATUS_KEYS['returned']))],

            # Блок действий с заказом
            [KeyboardButton("Изменить статус задач")], 
            [KeyboardButton("Изменить статус запросов на недвижимость")],
            [KeyboardButton("Изменить статус оплаты")],
            
            # Навигация и просмотр событий
            [KeyboardButton("🎁 Зачислить бонус")],  # Новая кнопка
            [KeyboardButton("Отправить сообщение пользователю")],  # Новая кнопка
            [KeyboardButton("Просмотреть события")],
            [KeyboardButton("Назад")]
        ]

        # Отправляем сообщение админу с клавиатурой
        await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return ORDER_ACTIONS

    except Exception as e:
        logger.error(f"Error in request_order_number: {e}")
        await update.message.reply_text("Произошла ошибка при запросе номера заказа.")
        return ConversationHandler.END

async def handle_back_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        return await admin_panel(update, context)  # Directly go to admin panel
    return ConversationHandler.END
    
async def credit_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order_id = context.user_data.get('order_id')
    user_id = get_user_id_by_order_id(order_id)
    
    if not user_id:
        await update.message.reply_text("Не удалось найти пользователя для этого заказа.")
        return ORDER_ACTIONS

    # Зачисляем бонус пользователю
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET bonuses = bonuses + 1 WHERE user_id = ?", (user_id,))
        conn.commit()

    # Получаем язык пользователя для уведомления
    user_language = get_user_language(user_id)

    # Сообщение о начислении бонуса
    bonus_message = (
        get_message(user_language, 'bonus_received_message') + "\n\n" +
        get_message(user_language, 'bonus_usage_instructions')
    )

    # Отправляем уведомление пользователю
    await context.bot.send_message(chat_id=user_id, text=bonus_message)

    # Уведомляем администратора о зачислении бонуса
    await update.message.reply_text("Бонус успешно зачислен пользователю.")

    # Возвращаем администратора в админ-панель
    return await admin_panel(update, context)





from telegram import ReplyKeyboardMarkup, KeyboardButton

async def request_message_for_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order_id = context.user_data.get('order_id')
    user_id = get_user_id_by_order_id(order_id)

    if not user_id:
        await update.message.reply_text("Не удалось найти пользователя для этого заказа.")
        return ORDER_ACTIONS

    # Сохраняем user_id в контексте для дальнейшего использования
    context.user_data['target_user_id'] = user_id

    # Клавиатура с кнопкой "Назад"
    keyboard = [[KeyboardButton("Назад")]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    # Запрашиваем текст сообщения у администратора
    await update.message.reply_text("Введите сообщение, которое хотите отправить пользователю:", reply_markup=markup)
    return SEND_MESSAGE_TO_USER



async def send_message_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        return await admin_panel(update, context)

    user_id = context.user_data.get('target_user_id')
    message_text = update.message.text

    if not user_id:
        await update.message.reply_text("Ошибка: не удалось найти пользователя для отправки сообщения.")
        return ORDER_ACTIONS

    # Отправляем сообщение пользователю
    try:
        await context.bot.send_message(chat_id=user_id, text=message_text)
        await update.message.reply_text("Сообщение успешно отправлено пользователю.")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения пользователю: {e}")
        await update.message.reply_text("Произошла ошибка при отправке сообщения.")

    # Возвращаемся в админ-панель после отправки сообщения
    return await admin_panel(update, context)


async def view_events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order_id = context.user_data.get('order_id')
    events = get_order_events(order_id)  # Получаем события из базы данных

    # Проверяем наличие событий
    if not events:
        await update.message.reply_text("События для данного заказа отсутствуют.")

    else:
        # Формируем сообщение со списком событий
        message = "События для заказа:\n\n"
        for event in events:
            message += f"Описание: {event['event_description']}\n"
            message += f"Ссылка: {event.get('event_link', 'Нет')}\n"
            message += f"Дата и время: {event['event_timestamp']}\n"
            message += "-----------------------------\n"

        # Отправляем сообщение о событиях
        await update.message.reply_text(message)

    # Клавиатура с кнопками (даже если событий нет)
    keyboard = [
        [KeyboardButton("Добавить событие")],
        [KeyboardButton("Удалить событие")],
        [KeyboardButton("Назад")]
    ]

    # Отправляем клавиатуру
    await update.message.reply_text("Выберите действие:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return ORDER_ACTIONS





async def add_event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await add_event(update, context)  # Перенаправляем на функцию добавления события
    return ADD_EVENT_DESCRIPTION

async def delete_event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.debug("Entering delete_event_callback")
    await delete_event(update, context)  # Перенаправляем на функцию удаления события
    return DELETE_EVENT

async def back_to_actions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await request_order_number(update, context)  # Возвращаемся к действиям по заказу
    return ORDER_ACTIONS

async def delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order_id = context.user_data.get('order_id')
    events = get_order_events(order_id)

    # Если нет событий для удаления
    if not events:
        await update.message.reply_text("Нет событий для удаления.")
        return ORDER_ACTIONS

    # Если пользователь выбрал "Назад", возвращаем его к списку действий
    if update.message.text.lower() in ["назад", "orqaga", "back"]:
        return await view_events(update, context)

    # Если пользователь уже отправил номер события для удаления
    if update.message.text.isdigit():
        try:
            selected_index = int(update.message.text) - 1
            if 0 <= selected_index < len(events):
                event_id = events[selected_index]['event_id']
                event_description = events[selected_index]['event_description']

                # Логирование для отладки
                logger.debug(f"Выбранное событие для удаления: {event_description} (ID: {event_id})")

                # Удаляем событие
                delete_order_event(event_id)
                logger.debug(f"Событие с ID {event_id} успешно удалено.")

                await update.message.reply_text(f"Событие '{event_description}' успешно удалено.")
                return ORDER_ACTIONS
            else:
                logger.warning(f"Неверный выбор события: {selected_index + 1}")
                await update.message.reply_text("Неверный выбор, попробуйте снова.")
                return DELETE_EVENT
        except Exception as e:
            logger.error(f"Ошибка при удалении события: {e}")
            await update.message.reply_text("Произошла ошибка при удалении события.")
            return ORDER_ACTIONS

    # Если пользователь еще не выбрал событие
    message = "Выберите событие для удаления:\n\n"
    keyboard = []
    for i, event in enumerate(events, 1):
        message += f"{i}. {event['event_description']} - {event['event_timestamp']}\n"
        keyboard.append([KeyboardButton(str(i))])

    keyboard.append([KeyboardButton("Назад")])

    await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return DELETE_EVENT


def get_order_events(order_id: int):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT event_id, event_description, event_link, event_timestamp FROM order_events WHERE order_id = ?", (order_id,))
        return [{"event_id": row[0], "event_description": row[1], "event_link": row[2], "event_timestamp": row[3]} for row in c.fetchall()]

def delete_order_event(event_id: int):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            logger.debug(f"Executing DELETE for event ID: {event_id}")
            c.execute("DELETE FROM order_events WHERE event_id = ?", (event_id,))
            conn.commit()
            logger.debug("Event successfully deleted from the database")
    except Exception as e:
        logger.error(f"Error deleting event: {e}")

# Функция для начала добавления события
async def add_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() in ["назад", "orqaga", "back"]:
        return await view_events(update, context)  # Возвращаемся к списку событий

    user_id = update.message.from_user.id
    language = get_user_language(user_id)

    await update.message.reply_text(get_message(language, 'event_enter_description'))
    return ADD_EVENT_DESCRIPTION


import re

def escape_markdown_v2(text: str) -> str:
    """Экранирует все специальные символы для MarkdownV2."""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

from telegram import ReplyKeyboardMarkup, KeyboardButton


# Функция для получения описания события
async def receive_event_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() in ["назад", "orqaga", "back"]:
        return await view_events(update, context)  # Возвращаемся к списку событий

    try:
        # Сохраняем описание события
        event_description = update.message.text
        context.user_data['event_description'] = event_description

        user_id = update.message.from_user.id
        language = get_user_language(user_id)

        # Добавляем клавиатуру с кнопкой "Пропустить"
        keyboard = [
            [InlineKeyboardButton(get_message(language, 'skip'), callback_data='skip')],
        ]

        await update.message.reply_text(get_message(language, 'event_enter_link_optional'), reply_markup=InlineKeyboardMarkup(keyboard))

        return ADD_EVENT_LINK
    except Exception as e:
        logger.error(f"Ошибка в receive_event_description: {e}")
        await update.message.reply_text("Произошла ошибка при обработке описания события.")
        return ADMIN_PANEL



from bot.utils.notifications import send_notification
from datetime import datetime



async def receive_event_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() in ["назад", "orqaga", "back"]:
        return await view_events(update, context)  # Возвращаемся к списку событий

    try:
        # Получаем ссылку (если она указана)
        event_link = update.message.text if update.message.text.lower() != "no" else None
        event_description = context.user_data.get('event_description')

        # Проверяем, что описание события сохранено
        if not event_description:
            await update.message.reply_text("Ошибка: Описание события не найдено.")
            return ADMIN_PANEL

        # Сохраняем событие в базу данных
        add_order_event(context.user_data['order_id'], event_description, event_link)

        # Уведомляем администратора
        await notify_admin(context, context.user_data['order_id'])

        # Уведомляем пользователя и подписчиков о добавленном событии
        await notify_user_and_subscribers(context, context.user_data['order_id'], event_description, event_link)

        return ADMIN_PANEL
    except Exception as e:
        logger.error(f"Error in receive_event_link: {e}")
        await update.message.reply_text("Произошла ошибка при добавлении события.")
        return ADMIN_PANEL
    


async def skip_event_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Пропуск ввода ссылки, обработка события без ссылки
    event_description = context.user_data.get('event_description')
    event_link = None  # Ссылка не указана

    # Добавляем событие в базу данных
    add_order_event(context.user_data['order_id'], event_description, event_link)

    # Уведомляем администратора
    await notify_admin(context, context.user_data['order_id'])

    # Уведомляем пользователя и подписчиков о добавленном событии
    await notify_user_and_subscribers(context, context.user_data['order_id'], event_description, event_link)

    return ADMIN_PANEL

async def notify_admin(context: ContextTypes.DEFAULT_TYPE, order_id):
    try:
        admin_message = f"Событие успешно добавлено в таймлайн заказа #{order_id}."
        # Отправляем сообщение администратору
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(chat_id=admin_id, text=admin_message)
    except Exception as e:
        logger.error(f"Error in notify_admin: {e}")






from datetime import datetime

async def notify_user_and_subscribers(context: ContextTypes.DEFAULT_TYPE, order_id, event_description, event_link=None):
    try:
        # Получаем user_id и язык пользователя
        user_id = get_user_id_by_order_id(order_id)
        user_language = get_user_language(user_id)

        # Получаем текущую дату и форматируем ее
        formatted_date = datetime.now().strftime('%d.%m.%Y %H:%M')  # Формат: День.Месяц.Год Часы:Минуты

        # Формируем сообщение для пользователя на основе его языка
        if user_language == 'ru':
            user_message = (
                f"📢 Уважаемый клиент, событие было добавлено к вашему заказу №{order_id}:\n\n"
                f"📝 Описание: {event_description}\n"
                f"🕒 Время: {formatted_date}\n"
            )
            if event_link:
                user_message += f"🔗 Ссылка: {event_link}\n"
            user_message += (
                "\nЧтобы просмотреть все события вашего заказа, перейдите в главное меню, затем нажмите на '📦 Мои заказы', "
                "выберите нужный номер заказа и нажмите на '📅 Таймлайн заказа'."
            )
        elif user_language == 'uz':
            user_message = (
                f"📢 Hurmatli mijoz, buyurtmangizga №{order_id} yangi hodisa qo'shildi:\n\n"
                f"📝 Tavsif: {event_description}\n"
                f"🕒 Vaqt: {formatted_date}\n"
            )
            if event_link:
                user_message += f"🔗 Havola: {event_link}\n"
            user_message += (
                "\nBuyurtmangizdagi barcha voqealarni ko'rish uchun asosiy menyuga o'ting, so'ng '📦 Mening buyurtmalarim' "
                "tugmasini bosing, kerakli buyurtma raqamini tanlang va '📅 Buyurtma taymlayni' tugmasini bosing."
            )
        else:  # По умолчанию английский
            user_message = (
                f"📢 Dear customer, an event has been added to your order №{order_id}:\n\n"
                f"📝 Description: {event_description}\n"
                f"🕒 Time: {formatted_date}\n"
            )
            if event_link:
                user_message += f"🔗 Link: {event_link}\n"
            user_message += (
                "\nTo view all events of your order, go to the main menu, then click on '📦 My Orders', "
                "select the required order number and click on '📅 Order Timeline'."
            )

        # Отправляем сообщение пользователю
        await send_notification(user_id, user_message, context.bot.token)

        # Получаем подписчиков и отправляем им уведомления
        subscribers = get_order_subscribers(order_id)
        for subscriber_id in subscribers:  # Теперь subscriber_id — это целое число
            subscriber_language = get_user_language(subscriber_id)

            # Формируем сообщение для подписчиков на основе их языка
            if subscriber_language == 'ru':
                subscriber_message = (
                    f"📢 Уважаемый клиент, событие было добавлено к вашему привязанному заказу №{order_id}:\n\n"
                    f"📝 Описание: {event_description}\n"
                    f"🕒 Время: {formatted_date}\n"
                )
                if event_link:
                    subscriber_message += f"🔗 Ссылка: {event_link}\n"
                subscriber_message += (
                    "\nЧтобы просмотреть все события вашего привязанного заказа, перейдите в главное меню, затем нажмите на '🔖 Привязанные заказы', "
                    "выберите нужный номер заказа и нажмите на '📅 Таймлайн заказа'."
                )
            elif subscriber_language == 'uz':
                subscriber_message = (
                    f"📢 Hurmatli mijoz, buyurtmangizga №{order_id} yangi hodisa qo'shildi:\n\n"
                    f"📝 Tavsif: {event_description}\n"
                    f"🕒 Vaqt: {formatted_date}\n"
                )
                if event_link:
                    subscriber_message += f"🔗 Havola: {event_link}\n"
                subscriber_message += (
                    "\nBuyurtmangizdagi barcha voqealarni ko'rish uchun asosiy menyuga o'ting, so'ng '🔖 Bog'langan buyurtmalar' "
                    "tugmasini bosing, kerakli buyurtma raqamini tanlang va '📅 Buyurtma taymlayni' tugmasini bosing."
                )
            else:  # По умолчанию английский
                subscriber_message = (
                    f"📢 Dear customer, an event has been added to your linked order №{order_id}:\n\n"
                    f"📝 Description: {event_description}\n"
                    f"🕒 Time: {formatted_date}\n"
                )
                if event_link:
                    subscriber_message += f"🔗 Link: {event_link}\n"
                subscriber_message += (
                    "\nTo view all events of your linked order, go to the main menu, then click on '🔖 Linked Orders', "
                    "select the required order number and click on '📅 Order Timeline'."
                )

            # Отправляем сообщение подписчику
            await send_notification(subscriber_id, subscriber_message, context.bot.token)

    except Exception as e:
        logger.error(f"Error in notify_user_and_subscribers: {e}")





from datetime import datetime
import pytz

def add_order_event(order_id: int, event_description: str, event_link: str = None):
    # Получаем текущую дату и время в часовом поясе Лондона
    london_tz = pytz.timezone('Europe/London')
    event_timestamp = datetime.now(london_tz).strftime('%Y-%m-%d %H:%M:%S')

    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        # Сохраняем событие с меткой времени
        c.execute("""
            INSERT INTO order_events (order_id, event_description, event_link, event_timestamp) 
            VALUES (?, ?, ?, ?)""", 
            (order_id, event_description, event_link, event_timestamp)
        )
        conn.commit()


async def update_order_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        order_id = context.user_data['order_id']
        status_text = update.message.text.strip()

        # Соответствие между текстом и ключом статуса
        status_map = {
            "Принят": 'order_status_accepted',
            "Возврат": 'order_status_returned',
            "Отменен": 'order_status_cancelled',
            "Ожидание": 'order_status_pending',
            "Ожидание оплаты": 'order_status_waiting_payment',
            "Выполняется": 'order_status_in_progress',
            "Выполнен": 'order_status_completed'
        }

        # Проверка наличия статуса
        if status_text not in status_map:
            await update.message.reply_text("Неверный статус. Попробуйте снова.")
            return ORDER_ACTIONS

        # Получаем ключ статуса
        status_key = status_map[status_text]

        # Обновляем статус заказа в базе данных, сохраняем ключ
        update_order_status(order_id, status_key)

        user_id = get_user_id_by_order_id(order_id)
        order = get_order_by_id(order_id)

        # Определяем язык пользователя
        user_language = get_user_language(user_id)

        # Получаем перевод статуса на языке пользователя
        translated_status = get_message(user_language, status_key)

        # Формирование сообщения для пользователя
        additional_message = get_message(user_language, status_key + "_message")
        status_message = (
            f"{get_message(user_language, 'dear_client')}, "
            f"{get_message(user_language, 'order_status_order_status_update')} #{order_id} "
            f"{get_message(user_language, 'order_status_status_updated_to')} '{translated_status}'.\n\n"
            f"{additional_message}\n\n{get_message(user_language, 'order_status_view_orders_info')}"
        )

        # Отправка сообщения пользователю
        await context.bot.send_message(chat_id=user_id, text=status_message)

        # Получаем список подписчиков заказа
        subscribers = get_order_subscribers(order_id)
        
        # Отправляем уведомление всем подписчикам с учетом их языка
        for subscriber_id in subscribers:
            # Получаем язык подписчика
            subscriber_language = get_user_language(subscriber_id)
            
            # Определяем сообщение для подписчика на его языке
            translated_status_subscriber = get_message(subscriber_language, status_key)
            additional_message_subscriber = get_message(subscriber_language, status_key + "_message")
            status_message_subscriber = (
                f"{get_message(subscriber_language, 'dear_client')}, "
                f"{get_message(subscriber_language, 'order_status_order_status_update')} #{order_id} "
                f"{get_message(subscriber_language, 'order_status_status_updated_to')} '{translated_status_subscriber}'.\n\n"
                f"{additional_message_subscriber}\n\n{get_message(subscriber_language, 'order_subscribe_status_view_orders_info')}"
            )

            # Отправляем уведомление подписчику
            await context.bot.send_message(chat_id=subscriber_id, text=status_message_subscriber)

        # Подтверждение администратору
        await update.message.reply_text(f"Статус заказа {order_id} обновлен на '{status_text}'.", reply_markup=admin_panel_keyboard())
        return ADMIN_PANEL
    
    except Exception as e:
        logger.error(f"Error in update_order_status_handler: {e}")
        await update.message.reply_text("Произошла ошибка при обновлении статуса заказа.")
        return ConversationHandler.END



async def change_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order_id = context.user_data['order_id']
    order = get_order_by_id(order_id)
    
    if not order:
        await update.message.reply_text("Заказ не найден. Попробуйте снова.")
        return ORDER_ACTIONS
    
    # Текущий статус (на русском для админа)
    current_status = "Оплачено" if order.get('paid', 0) else "Не оплачено"
    
    # Клавиатура с вариантами статусов для админа (на русском)
    keyboard = [
        [KeyboardButton("Оплачено"), KeyboardButton("Не оплачено")],
        [KeyboardButton("Назад")]
    ]
    
    await update.message.reply_text(
        f"Текущий статус оплаты: {current_status}\n\nВыберите новый статус:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return CHANGE_PAYMENT_STATUS



async def update_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_status = update.message.text
    order_id = context.user_data['order_id']
    
    # Проверка нового статуса
    if new_status == "Оплачено":
        paid = 1
    elif new_status == "Не оплачено":
        paid = 0
    else:
        await update.message.reply_text("Неверный статус. Попробуйте снова.")
        return CHANGE_PAYMENT_STATUS
    
    try:
        # Обновляем статус оплаты в базе данных
        update_order_payment_status(order_id, paid)
        
        # Отправляем подтверждение администратору
        await update.message.reply_text(f"Статус оплаты обновлен на '{new_status}'.", reply_markup=admin_panel_keyboard())
        
        # Получаем user_id на основе order_id
        user_id = get_user_id_by_order_id(order_id)  # Функция для получения user_id по order_id
        if not user_id:
            await update.message.reply_text("Не удалось найти пользователя для этого заказа.")
            return ADMIN_PANEL

        # Получаем язык пользователя
        user_language = get_user_language(user_id)
        
        # Определяем сообщение для пользователя на его языке
        if paid:
            status_message = get_message(user_language, 'payment_paid')
        else:
            status_message = get_message(user_language, 'payment_not_paid')
        
        # Создаем сообщение для пользователя с номером заказа и новым статусом
        message_to_user = get_message(user_language, 'payment_status_updated', order_id=order_id, status=status_message)
        
        # Отправляем уведомление пользователю
        await context.bot.send_message(chat_id=user_id, text=message_to_user)
        
        # Получаем список подписчиков заказа
        subscribers = get_order_subscribers(order_id)
        
        # Отправляем уведомление всем подписчикам с учетом их языка
        for subscriber_id in subscribers:
            # Получаем язык подписчика
            subscriber_language = get_user_language(subscriber_id)
            
            # Определяем сообщение для подписчика на его языке
            if paid:
                subscriber_status_message = get_message(subscriber_language, 'payment_paid')
            else:
                subscriber_status_message = get_message(subscriber_language, 'payment_not_paid')
            
            # Создаем сообщение для подписчика
            message_to_subscriber = get_message(subscriber_language, 'payment_subscribe_status_updated', order_id=order_id, status=subscriber_status_message)
            
            # Отправляем уведомление подписчику
            await context.bot.send_message(chat_id=subscriber_id, text=message_to_subscriber)
        
        return ADMIN_PANEL
    except Exception as e:
        logger.error(f"Error in update_payment_status: {e}")
        await update.message.reply_text("Произошла ошибка при обновлении статуса оплаты.")
        return ConversationHandler.END


# Обновляем функцию, где показываются свойства заказа
async def show_order_properties(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        order_id = context.user_data['order_id']
        properties = get_order_properties(order_id)

        if not properties:
            await update.message.reply_text(f"Для заказа {order_id} нет запросов на недвижимость.", reply_markup=admin_panel_keyboard())
            return ORDER_ACTIONS

        message = ""
        messages = []
        for prop in properties:
            if 'item' in prop and prop['item'].startswith('http'):
                property_info = (
                    f"ID: {prop['order_item_id']}\n"
                    "-----------------------------\n"
                    "Недвижимость, добавленная пользователем\n"
                    f"Ссылка: {prop['item']}\n"
                    "-----------------------------\n"
                    f"Статус: {prop['status']}\n"
                    f"\n"
                )
            else:
                property_info = (
                    f"ID: {prop['order_item_id']}\n"
                    "-----------------------------\n"
                    f"Название: {prop.get('title', 'N/A')}\n"
                    f"Цена: {prop.get('price', 'N/A')}\n"
                    f"Адрес: {prop.get('address', 'N/A')}\n"
                    f"Ссылка: {prop.get('link', 'N/A')}\n"
                    "-----------------------------\n"
                    f"Статус: {prop['status']}\n"
                    f"\n"
                )

            if len(message) + len(property_info) > 4096:
                messages.append(message)
                message = property_info
            else:
                message += property_info

        if message:
            messages.append(message)

        for msg in messages:
            await update.message.reply_text(msg)

        keyboard = [[KeyboardButton(f"{prop['order_item_id']} - {prop.get('title', 'Недвижимость, добавленная пользователем')}")] for prop in properties]
        keyboard.append([KeyboardButton("Назад")])

        await update.message.reply_text("Выберите недвижимость для изменения статуса:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return PROPERTIES
    except Exception as e:
        logger.error(f"Error in show_order_properties: {e}")
        await update.message.reply_text("Произошла ошибка при показе свойств заказа.")
        return ConversationHandler.END


# Обновляем функции, где используются статусы без эмодзи
async def select_property_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        text = update.message.text
        order_item_id = int(text.split(' - ')[0])
        property = get_property_by_id(order_item_id)

        if not property:
            await update.message.reply_text("Недвижимость не найдена.")
            return PROPERTIES

        context.user_data['order_item_id'] = order_item_id
        title = property.get('title', 'Недвижимость, добавленная пользователем') if 'title' in property else 'Недвижимость, добавленная пользователем'
        message = f"Изменение статуса недвижимости {title}:\n\nТекущий статус: {property['status']}\n\nВыберите новый статус:"
        
        # Получаем кнопки для админ-панели на русском, но сохраняем ключи статусов
        keyboard = [
            [KeyboardButton(get_message('ru', 'property_status_waiting_agent')), 
             KeyboardButton(get_message('ru', 'property_status_booked'))],
            [KeyboardButton(get_message('ru', 'property_status_going')), 
             KeyboardButton(get_message('ru', 'property_status_in_progress'))],
            [KeyboardButton(get_message('ru', 'property_status_viewed')), 
             KeyboardButton(get_message('ru', 'property_status_ready'))],
            [KeyboardButton(get_message('ru', 'property_status_cancelled'))],
            [KeyboardButton("Назад")]
        ]
        await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return PROPERTIES
    except Exception as e:
        logger.error(f"Error in select_property_status: {e}")
        await update.message.reply_text("Произошла ошибка при выборе статуса недвижимости.")
        return ConversationHandler.END





async def update_property_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order_item_id = context.user_data.get('order_item_id')
    status_key = update.message.text  # Текст кнопки статуса

    # Соответствие текста кнопок с ключами статусов
    status_map = {
        "Ожидание ответа агента": 'property_status_waiting_agent',
        "Бронь забронирована": 'property_status_booked',
        "Иду смотреть": 'property_status_going',
        "Идет просмотр объекта": 'property_status_in_progress',
        "Объект просмотрен": 'property_status_viewed',
        "Результат готов": 'property_status_ready',
        "Просмотр отменен": 'property_status_cancelled',
    }

    # Проверка, существует ли ключ статуса
    if status_key not in status_map:
        await update.message.reply_text("Invalid status. Please try again.")
        return PROPERTIES

    # Получаем ключ статуса
    status = status_map[status_key]

    # Если статус "Просмотр отменен", запросить причину отмены
    if status == "property_status_cancelled":
        await update.message.reply_text("Пожалуйста, укажите причину отмены:")
        context.user_data['awaiting_reason'] = True
        return REQUEST_PROPERTY_CLOUD_LINK

    # Если статус "Результат готов", запросить ссылку на результат
    if status == "property_status_ready":
        await update.message.reply_text(get_message(context.user_data.get('language', 'ru'), "provide_result_link"))
        context.user_data['awaiting_result_link'] = True
        return REQUEST_PROPERTY_CLOUD_LINK

    # Обновляем статус недвижимости в базе данных
    update_property_status(order_item_id, status_key)  # Сохраняем статус на русском

    # Получаем данные для отправки пользователю
    order_id = get_order_id_by_order_item_id(order_item_id)
    user_id = get_user_id_by_order_id(order_id)
    user_language = get_user_language(user_id)

    property = get_property_by_id(order_item_id)
    title = property.get('title', get_message(user_language, 'property_added_by_user'))

    # Получаем сообщение для нового статуса с переводом на языке пользователя
    translated_status = get_message(user_language, status)

    # Формируем сообщение для пользователя
    status_message = (
        f"{get_message(user_language, 'dear_client')}, {get_message(user_language, 'property_status_update')} '{title}' "
        f"{get_message(user_language, 'from_order')} #{order_id} {get_message(user_language, 'status_updated_to')} '{translated_status}'.\n\n"
        f"{get_message(user_language, 'view_properties_info')}"
    )

    # Отправляем сообщение пользователю
    await context.bot.send_message(chat_id=user_id, text=status_message)

    # Получаем список подписчиков заказа
    subscribers = get_order_subscribers(order_id)

    # Отправляем уведомление всем подписчикам с учетом их языка
    for subscriber_id in subscribers:
        # Получаем язык подписчика
        subscriber_language = get_user_language(subscriber_id)

        # Определяем сообщение для подписчика на его языке
        translated_status_subscriber = get_message(subscriber_language, status)
        status_message_subscriber = (
            f"{get_message(subscriber_language, 'dear_client')}, {get_message(subscriber_language, 'property_status_update')} '{title}' "
            f"{get_message(subscriber_language, 'from_order')} #{order_id} {get_message(subscriber_language, 'status_updated_to')} '{translated_status_subscriber}'.\n\n"
            f"{get_message(subscriber_language, 'view_subscribe_properties_info')}"
        )

        # Отправляем уведомление подписчику
        await context.bot.send_message(chat_id=subscriber_id, text=status_message_subscriber)

    # Теперь уведомляем администратора, что статус был успешно изменен
    admin_message = f"Статус недвижимости '{title}' для заказа #{order_id} был изменен на '{translated_status}'."
    await update.message.reply_text(admin_message)  # Отправляем сообщение админу

    return ADMIN_PANEL



async def show_order_tasks_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        order_id = context.user_data['order_id']

        # Получаем задачи из order_tasks
        tasks = await get_order_tasks(order_id)
        # Получаем индивидуальные услуги из order_items
        individual_services = get_individual_services(order_id)

        if not tasks and not individual_services:
            await update.message.reply_text(f"Для заказа {order_id} нет задач или индивидуальных услуг.", reply_markup=admin_panel_keyboard())
            return ORDER_ACTIONS

        user_id = get_user_id_by_order_id(order_id)
        user_language = get_user_language(user_id)

        # Сообщение на русском языке
        message = f"Задачи и услуги для заказа {order_id}:\n\n"
        
        # Добавляем задачи в сообщение с переводом
        for task in tasks:
            task_description = get_message(user_language, task['task_description'])
            task_status = get_message(user_language, task['status'])
            message += f"{task['task_id']}. {task_description} - {task_status}\n"
        
        # Добавляем индивидуальные услуги в сообщение с переводом
        for service in individual_services:
            service_description = get_message(user_language, service['item'])
            service_status = get_message(user_language, service['status'])
            message += f"{service['order_item_id']}. {service_description} - {service_status}\n"

        keyboard = []
        
        # Добавляем задачи на клавиатуру
        for task in tasks:
            task_description = get_message(user_language, task['task_description'])
            keyboard.append([KeyboardButton(f"{task['task_id']} - {task_description}")])
        
        # Добавляем индивидуальные услуги на клавиатуру
        for service in individual_services:
            service_description = get_message(user_language, service['item'])
            keyboard.append([KeyboardButton(f"{service['order_item_id']} - {service_description}")])
        
        keyboard.append([KeyboardButton("Назад")])

        await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return TASKS
    except Exception as e:
        logger.error(f"Error in show_order_tasks_admin: {e}")
        await update.message.reply_text("Произошла ошибка при показе задач и услуг заказа.")
        return ConversationHandler.END





async def select_task_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        text = update.message.text
        # Извлекаем ID задачи или услуги
        item_id = int(text.split(' - ')[0].strip())

        # Проверяем сначала в таблице order_tasks
        task = get_task_by_id(item_id)

        # Если задача не найдена, проверяем таблицу order_items для индивидуальных услуг
        if not task:
            task = get_individual_service_by_id(item_id)

            # Если элемент не найден ни в одной таблице, возвращаем сообщение об ошибке
            if not task:
                await update.message.reply_text(f"Задача или услуга с ID {item_id} не найдена. Попробуйте снова.")
                return TASKS

        # Сохраняем ID задачи или услуги и тип (услуга или задача) в контексте
        context.user_data['task_id'] = item_id
        
        context.user_data['is_service'] = task.get('item_type') == 'individual_service' if 'item_type' in task else False

        # Формируем сообщение для изменения статуса
        message = f"Изменение статуса задачи {task['task_description']}:\n\nТекущий статус: {task['status']}\n\nВыберите новый статус:"
        keyboard = [
            [KeyboardButton("Выполнено"), KeyboardButton("Не выполнено")],
            [KeyboardButton("Выполняется"), KeyboardButton("Назад")]
        ]
        await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return TASKS
    except Exception as e:
        logger.error(f"Error in select_task_status: {e}")
        await update.message.reply_text("Произошла ошибка при выборе статуса задачи.")
        return ORDER_ACTIONS
    





async def back_to_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        query = update.callback_query
        order_id = int(query.data.split('_')[2])
        return await show_order_properties(update, context)
    except Exception as e:
        logger.error(f"Error in back_to_order: {e}")
        await update.message.reply_text("Произошла ошибка при возврате к заказу.")
        return ConversationHandler.END



async def update_task_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        # Extract the message text
        text = update.message.text.strip()
        logger.debug(f"Received message for task selection: '{text}'")

        # Validate and extract task_id
        if " - " not in text:
            await update.message.reply_text(
                "Неверный формат выбора задачи. Пожалуйста, выберите задачу из списка.",
                reply_markup=task_status_keyboard([])
            )
            logger.warning("Message does not contain ' - ' separator.")
            return TASKS

        task_id_str = text.split(" - ")[0].strip()
        if not task_id_str.isdigit():
            await update.message.reply_text(
                "Неверный формат ID задачи. Пожалуйста, выберите задачу из списка.",
                reply_markup=task_status_keyboard([])
            )
            logger.warning(f"Invalid task_id format: '{task_id_str}'")
            return TASKS

        task_id = int(task_id_str)
        logger.debug(f"Extracted Task ID: {task_id}")

        # Determine if it's a task or an individual service
        is_service = context.user_data.get('is_service', False)
        if is_service:
            task = get_individual_service_by_id(task_id)
            logger.debug(f"Task ID {task_id} identified as an individual service: {task}")
        else:
            task = get_task_by_id(task_id)
            logger.debug(f"Task ID {task_id} identified as a standard task: {task}")

        if not task:
            await update.message.reply_text(
                f"Задача с ID {task_id} не найдена. Попробуйте снова.",
                reply_markup=task_status_keyboard([])
            )
            logger.error(f"Task with ID {task_id} not found.")
            return TASKS

        # Store task_id in user_data for later use
        context.user_data['task_id'] = task_id
        logger.debug(f"Stored Task ID {task_id} in user_data.")

        # Retrieve user language for message translation
        user_id = task.get('user_id')
        if not user_id:
            await update.message.reply_text(
                "Ошибка: пользователь не найден для этого заказа.",
                reply_markup=admin_panel_keyboard()
            )
            logger.error(f"User ID not found for Task ID {task_id}.")
            return ADMIN_PANEL

        user_language = get_user_language(user_id)
        logger.debug(f"User language for Task ID {task_id}: {user_language}")

        # Translate task description and current status
        task_description = get_message(user_language, task['task_description'])
        task_status = get_message(user_language, task['status'])
        logger.debug(f"Translated Task Description: {task_description}")
        logger.debug(f"Translated Task Status: {task_status}")

        # Prepare the status update message
        message = (
            f"📋 **Изменение статуса задачи**\n"
            f"**Задача:** {task_description}\n"
            f"**Текущий статус:** {task_status}\n\n"
            f"Выберите новый статус:"
        )
        logger.debug("Prepared status update message.")

        # Define the keyboard for new status selection
        keyboard = [
            [KeyboardButton("Выполнено"), KeyboardButton("Не выполнено")],
            [KeyboardButton("Выполняется"), KeyboardButton("Назад")]
        ]

        # Send the message with the keyboard
        await update.message.reply_text(
            message,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode='Markdown'
        )
        logger.debug("Sent status update prompt with keyboard.")

        return TASKS

    except Exception as e:
        logger.exception(f"Unexpected error in update_task_status: {e}")
        await update.message.reply_text("Произошла ошибка при обработке запроса. Пожалуйста, попробуйте снова.")
        return ConversationHandler.END



status_map_tasks = {
    "Выполнено": "task_status_completed",
    "Не выполнено": "task_status_not_completed",
    "Выполняется": "task_status_in_progress"
}



async def update_task_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_status_text = update.message.text  # Получаем текстовый статус
    
    # Преобразуем текстовый статус в ключ
    new_status = status_map_tasks.get(new_status_text)
    
    # Если статус не найден в маппинге, вернем сообщение об ошибке
    if not new_status:
        await update.message.reply_text("Неверный статус. Попробуйте снова.")
        return TASKS
    
    # Извлекаем task_id из контекста
    task_id = context.user_data.get('task_id')
    
    if not task_id:
        await update.message.reply_text("Ошибка: задача не выбрана. Попробуйте снова.")
        return TASKS
    
    # Логирование перед сохранением
    logger.debug(f"Updating task {task_id} with status key '{new_status}'")

    # Сохраняем новый статус в базу данных
    update_order_task_status(task_id, new_status)

    # Получаем задачу и пользователя
    task = get_task_by_id(task_id)
    user_id = get_user_id_by_order_id(task['order_id'])
    user_language = get_user_language(user_id)

    # Преобразуем ключ в текст на нужном языке для пользователя
    translated_status = get_message(user_language, new_status)
    
    # Получаем мультиязычные сообщения для обновления статуса
    task_status_updated_message = get_message(user_language, 'task_status_updated_message').format(
        task_description=task['task_description'], 
        order_id=task['order_id'], 
        status=translated_status
    )
    
    # Получаем соответствующее сообщение для статуса (например, 'task_status_completed_message')
    task_status_message = get_message(user_language, f"{new_status}_message")
    view_tasks_info_message = get_message(user_language, 'view_tasks_info_message')
    
    # Формируем финальное сообщение
    status_message = f"{task_status_updated_message}\n\n{task_status_message}\n\n{view_tasks_info_message}"

    # Отправляем сообщение пользователю
    await context.bot.send_message(chat_id=user_id, text=status_message, parse_mode='Markdown')

    # Получаем список подписчиков заказа
    subscribers = get_order_subscribers(task['order_id'])

    # Отправляем уведомление всем подписчикам с учетом их языка
    for subscriber_id in subscribers:
        # Получаем язык подписчика
        subscriber_language = get_user_language(subscriber_id)

        # Преобразуем ключ в текст на нужном языке для подписчика
        translated_status_subscriber = get_message(subscriber_language, new_status)

        # Формируем сообщение для подписчика
        task_status_updated_message_subscriber = get_message(subscriber_language, 'task_status_updated_message').format(
            task_description=task['task_description'], 
            order_id=task['order_id'], 
            status=translated_status_subscriber
        )
        
        task_status_message_subscriber = get_message(subscriber_language, f"{new_status}_message")
        view_tasks_info_message_subscriber = get_message(subscriber_language, 'view_subscribe_tasks_info_message')

        status_message_subscriber = f"{task_status_updated_message_subscriber}\n\n{task_status_message_subscriber}\n\n{view_tasks_info_message_subscriber}"

        # Отправляем уведомление подписчику
        await context.bot.send_message(chat_id=subscriber_id, text=status_message_subscriber)

    # Подтверждаем администратору
    await update.message.reply_text(f"Статус задачи обновлен на '{translated_status}'", reply_markup=admin_panel_keyboard())
    
    return ADMIN_PANEL




async def save_task_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_status = update.message.text
    task_id = context.user_data.get('task_id')

    # Определяем, является ли задача индивидуальной услугой или общей задачей
    if context.user_data.get('is_service', False):
        task = get_individual_service_by_id(task_id)
    else:
        task = get_task_by_id(task_id)

    if not task:
        await update.message.reply_text(f"Задача с ID {task_id} не найдена. Попробуйте снова.", reply_markup=task_status_keyboard([]))
        return TASKS

    if new_status == "Выполнено":
        # Сохраняем статус и переходим к предоставлению ссылки на облако
        await update.message.reply_text("Пожалуйста, предоставьте ссылку на облако с фотографиями, подтверждающими выполнение задачи.")
        return REQUEST_CLOUD_LINK

    # Обновляем статус задачи
    update_order_task_status(task_id, new_status)

    # Получение данных задачи и заказа
    task = get_task_by_id(task_id) or get_individual_service_by_id(task_id)
    order_id = task['order_id']
    user_id = get_user_id_by_order_id(order_id)
    user_language = get_user_language(user_id)  # Определяем язык пользователя
    
    # Динамическое получение переведенного описания задачи/услуги (например, airport_pickup)
    task_description_key = task.get('task_description', task.get('item'))
    task_description = get_message(user_language, task_description_key)  # Получение перевода task_description

    # Получение переведенного статуса
    status_key = status_message_keys.get(new_status, "")
    translated_status = get_message(user_language, status_key)

    # Получение дополнительных частей сообщения
    status_part = get_message(user_language, 'task_status_status')
    in_order_part = get_message(user_language, 'task_status_in_order')
    has_been_updated_part = get_message(user_language, 'task_status_has_been_updated')

    # Получение дополнительного сообщения для статуса
    additional_message = get_message(user_language, f"{status_key}_message")

    # Получение информации о задачах
    view_tasks_info_message = get_message(user_language, view_tasks_info_key)

    # Формирование и отправка сообщения пользователю
    final_status_message = (f"{status_part} '{task_description}' {in_order_part} #{order_id} {has_been_updated_part} '{translated_status}'.\n\n"
                            f"{additional_message}\n\n{view_tasks_info_message}")

    # Отправляем уведомление основному пользователю
    await send_notification(user_id, final_status_message, context.bot.token)

    # Получаем список подписчиков заказа
    subscribers = get_order_subscribers(order_id)

    # Логируем подписчиков для отладки
    logger.debug(f"Subscribers for order {order_id}: {subscribers}")

    # Отправляем уведомление всем подписчикам с их языком
    for subscriber_id in subscribers:
        try:
            # Получаем язык подписчика
            subscriber_language = get_user_language(subscriber_id)

            # Переводим описание задачи на языке подписчика
            task_description_subscriber = get_message(subscriber_language, task_description_key)
            translated_status_subscriber = get_message(subscriber_language, status_key)

            # Формируем сообщение для подписчика
            final_status_message_subscriber = (
                f"{get_message(subscriber_language, 'task_status_status')} '{task_description_subscriber}' "
                f"{get_message(subscriber_language, 'task_status_in_order')} #{order_id} "
                f"{get_message(subscriber_language, 'task_status_has_been_updated')} '{translated_status_subscriber}'.\n\n"
                f"{get_message(subscriber_language, f'{status_key}_message')}\n\n"
                f"{get_message(subscriber_language, 'view_subscribe_tasks_info_message')}"
            )

            await context.bot.send_message(chat_id=subscriber_id, text=final_status_message_subscriber)
            logger.debug(f"Notification sent to subscriber {subscriber_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to subscriber {subscriber_id}: {str(e)}")

    # Подтверждение администратору
    await update.message.reply_text(f"Task status {task_id} has been updated to '{translated_status}'.", reply_markup=admin_panel_keyboard())

    return ORDER_ACTIONS




# Статусы и ключи сообщений
status_message_keys = {
    "Выполнено": "task_status_completed",
    "Не выполнено": "task_status_not_completed",
    "Выполняется": "task_status_in_progress",
}

# Ключ для информации о задачах
view_tasks_info_key = "view_tasks_info_message"




def update_individual_service_status(order_item_id, status):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE order_items SET status = ? WHERE order_item_id = ? AND item_type = 'individual_service'", (status, order_item_id))
        conn.commit()
        return c.rowcount > 0  # Возвращаем True, если была обновлена хотя бы одна строка
    



# Новая функция для сохранения ссылки на облако
async def save_cloud_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'task_id' in context.user_data:
        cloud_link = update.message.text
        task_id = context.user_data['task_id']

        # Обновляем статус задачи с новой ссылкой на облако
        update_order_task_status(task_id, 'Выполнено', cloud_link)

        # Получаем задачу и соответствующие данные
        task = get_task_by_id(task_id)
        order_id = task['order_id']
        user_id = get_user_id_by_order_id(order_id)
        user_language = get_user_language(user_id)  # Получаем язык пользователя
        task_description_key = task['task_description']

        # Переводим описание задачи (например, airport_pickup) и другие части сообщения
        task_description = get_message(user_language, task_description_key)
        status_completed_message = get_message(user_language, 'task_status_completed')
        view_tasks_info_message = get_message(user_language, view_tasks_info_key)

        # Формируем финальное сообщение для пользователя
        status_message = (
            f"{get_message(user_language, 'task_status_status')} '{task_description}' "
            f"{get_message(user_language, 'task_status_in_order')} #{order_id} "
            f"{get_message(user_language, 'task_status_has_been_updated')} '{status_completed_message}'.\n\n"
            f"{get_message(user_language, 'cloud_link_message')}: {cloud_link}\n\n"
            f"{view_tasks_info_message}"
        )

        # Отправляем уведомление основному пользователю
        await send_notification(user_id, status_message, context.bot.token)

        # Получаем список подписчиков заказа
        subscribers = get_order_subscribers(order_id)

        # Отправляем уведомление всем подписчикам с учетом их языка
        for subscriber_id in subscribers:
            try:
                # Получаем язык подписчика
                subscriber_language = get_user_language(subscriber_id)

                # Переводим описание задачи и другие части сообщения на языке подписчика
                task_description_subscriber = get_message(subscriber_language, task_description_key)
                status_completed_message_subscriber = get_message(subscriber_language, 'task_status_completed')
                view_tasks_info_message_subscriber = get_message(subscriber_language, view_tasks_info_key)

                # Формируем сообщение для подписчика
                status_message_subscriber = (
                    f"{get_message(subscriber_language, 'task_status_status')} '{task_description_subscriber}' "
                    f"{get_message(subscriber_language, 'task_status_in_order')} #{order_id} "
                    f"{get_message(subscriber_language, 'task_status_has_been_updated')} '{status_completed_message_subscriber}'.\n\n"
                    f"{get_message(subscriber_language, 'cloud_link_message')}: {cloud_link}\n\n"
                    f"{get_message(subscriber_language, 'view_subscribe_tasks_info_message')}"
                )

                # Отправляем уведомление подписчику
                await context.bot.send_message(chat_id=subscriber_id, text=status_message_subscriber)
                logger.debug(f"Notification sent to subscriber {subscriber_id}")
            except Exception as e:
                logger.error(f"Failed to send notification to subscriber {subscriber_id}: {str(e)}")

        # Подтверждение администратору
        await update.message.reply_text(f"Ссылка на результат сохранена. Статус задачи {task_id} обновлен на 'Выполнено'.", reply_markup=admin_panel_keyboard())
        return ADMIN_PANEL
    else:
        await update.message.reply_text("Ошибка: Неверный запрос. Ссылка на облако не может быть сохранена для запросов на недвижимость.")
        return ADMIN_PANEL


# Новая функция для сохранения ссылки на облако для запросов на недвижимость



# Функция для обновления ссылки на облако для недвижимости в базе данных
def update_property_cloud_link(order_item_id, cloud_link):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()

            # Обновление cloud_link по идентификатору элемента заказа
            c.execute("UPDATE order_items SET cloud_link = ? WHERE order_item_id = ?", (cloud_link, order_item_id))
            conn.commit()

            logger.info(f"Cloud link updated for order_item_id {order_item_id}")
    except sqlite3.Error as e:
        logger.error(f"Error updating property cloud link: {e}")







async def save_property_cloud_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order_item_id = context.user_data.get('order_item_id')

    if context.user_data.get('awaiting_reason', False):
        reason = update.message.text
        status = "Просмотр отменен"
        update_property_status(order_item_id, status, reason)

        # Получение информации о заказе и пользователе
        property = get_property_by_id(order_item_id)
        order_id = property['order_id']
        user_id = get_user_id_by_order_id(order_id)

        # Извлекаем язык пользователя
        user_language = get_user_language(user_id)

        # Проверяем, использовать ли ссылку на недвижимость или название (title)
        if 'title' in property and property['title']:
            title = property['title']  # Используем название объекта
        elif 'item' in property and property['item'].startswith('http'):
            title = f"<a href='{property['item']}'> {get_message(user_language, 'property_added_by_user')}</a>"
        else:
            title = get_message(user_language, 'property_added_by_user')

        # Зачисляем бонус пользователю
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET bonuses = bonuses + 1 WHERE user_id = ?", (user_id,))
            conn.commit()

        # Формирование сообщения для пользователя
        status_message = (
            f"{get_message(user_language, 'dear_client')} {get_message(user_language, 'save_property_status_update_prefix')} '{title}' "
            f"{get_message(user_language, 'save_property_in_order')} #{order_id} {get_message(user_language, 'save_property_has_been_updated_to')} '{status}'.\n\n"
            f"{get_message(user_language, 'save_property_cancellation_reason')}: {reason}\n\n"
            f"{get_message(user_language, 'save_property_bonus_received_message')}\n\n"
            f"{get_message(user_language, 'save_property_view_bonuses_info')}"
        )

        # Отправка сообщения пользователю с поддержкой HTML для ссылки
        await context.bot.send_message(chat_id=user_id, text=status_message, parse_mode='HTML')

        # Отправляем уведомления всем подписчикам с их языком
        subscribers = get_order_subscribers(order_id)
        for subscriber_id in subscribers:
            try:
                # Получаем язык подписчика
                subscriber_language = get_user_language(subscriber_id)

                # Переводим описание недвижимости на языке подписчика
                if 'title' in property and property['title']:
                    title_subscriber = property['title']
                elif 'item' in property and property['item'].startswith('http'):
                    title_subscriber = f"<a href='{property['item']}'> {get_message(subscriber_language, 'property_added_by_user')}</a>"
                else:
                    title_subscriber = get_message(subscriber_language, 'property_added_by_user')

                # Формируем сообщение для подписчика
                status_message_subscriber = (
                    f"{get_message(subscriber_language, 'dear_client')} {get_message(subscriber_language, 'save_property_status_update_prefix')} '{title_subscriber}' "
                    f"{get_message(subscriber_language, 'save_property_in_order')} #{order_id} {get_message(subscriber_language, 'save_property_has_been_updated_to')} '{status}'.\n\n"
                    f"{get_message(subscriber_language, 'save_property_cancellation_reason')}: {reason}\n\n"
                    f"{get_message(subscriber_language, 'view_bonus_tasks_properties_info')}"
                )

                await context.bot.send_message(chat_id=subscriber_id, text=status_message_subscriber, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Error sending message to subscriber {subscriber_id}: {e}")

        # Уведомление администратора
        await update.message.reply_text(
            f"{get_message(user_language, 'save_property_status_changed_to')} '{status}'. {get_message(user_language, 'save_property_reason')}: {reason}",
            reply_markup=admin_panel_keyboard()
        )
        context.user_data['awaiting_reason'] = False

    elif context.user_data.get('awaiting_result_link', False):
        cloud_link = update.message.text
        update_property_status(order_item_id, 'Результат готов', cloud_link)

        property = get_property_by_id(order_item_id)
        order_id = property['order_id']
        user_id = get_user_id_by_order_id(order_id)

        # Извлекаем язык пользователя
        user_language = get_user_language(user_id)

        # Проверяем, использовать ли ссылку на недвижимость или название (title)
        if 'title' in property and property['title']:
            title = property['title']
        else:
            title = get_message(user_language, 'property_added_by_user')

        # Формирование сообщения для пользователя
        status_message = (
            f"{get_message(user_language, 'dear_client')}, {get_message(user_language, 'save_property_status_update_prefix')} '{title}' "
            f"{get_message(user_language, 'save_property_in_order')} #{order_id} {get_message(user_language, 'save_property_has_been_updated_to')} '{get_message(user_language, 'property_status_ready')}'.\n\n"
            f"{get_message(user_language, 'save_property_link')}: <a href='{cloud_link}'>{cloud_link}</a>\n\n"
            f"{get_message(user_language, 'view_properties_info')}"
        )

        # Отправка сообщения пользователю
        await context.bot.send_message(chat_id=user_id, text=status_message, parse_mode='HTML')

        # Отправляем уведомления всем подписчикам с их языком
        subscribers = get_order_subscribers(order_id)
        for subscriber_id in subscribers:
            try:
                # Получаем язык подписчика
                subscriber_language = get_user_language(subscriber_id)

                # Переводим описание недвижимости на языке подписчика
                if 'title' in property and property['title']:
                    title_subscriber = property['title']
                else:
                    title_subscriber = get_message(subscriber_language, 'property_added_by_user')

                # Формируем сообщение для подписчика
                status_message_subscriber = (
                    f"{get_message(subscriber_language, 'dear_client')}, {get_message(subscriber_language, 'save_property_status_update_prefix')} '{title_subscriber}' "
                    f"{get_message(subscriber_language, 'save_property_in_order')} #{order_id} {get_message(subscriber_language, 'save_property_has_been_updated_to')} '{get_message(subscriber_language, 'property_status_ready')}'.\n\n"
                    f"{get_message(subscriber_language, 'save_property_link')}: <a href='{cloud_link}'>{cloud_link}</a>\n\n"
                    f"{get_message(subscriber_language, 'view_subscribe_properties_info')}"
                )

                await context.bot.send_message(chat_id=subscriber_id, text=status_message_subscriber, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Error sending message to subscriber {subscriber_id}: {e}")

        # Подтверждение администратору
        await update.message.reply_text(
            f"{get_message(user_language, 'save_property_result_link_saved')} '{title}'.",
            reply_markup=admin_panel_keyboard()
        )

        context.user_data['awaiting_result_link'] = False

    return ADMIN_PANEL





async def view_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print("view_users function called")  # Debug log

    try:
        context.user_data['admin_menu_active'] = True

        users = get_all_users()
        print(f"Retrieved users: {users}")  # Debug log
        if users:
            message = "Список пользователей:\n\n"
            for user in users:
                message += f"ID: {user['user_id']}, Имя: {user['name']}, Телефон: {user['phone']}, Email: {user['email']}\n"
        else:
            message = "Список пользователей пуст."

        await update.message.reply_text(message, reply_markup=admin_panel_keyboard())
        return ADMIN_PANEL
    except Exception as e:
        print(f"Error in view_users: {e}")  # Debug log
        await update.message.reply_text("Произошла ошибка при получении списка пользователей.")
        return ADMIN_PANEL

async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [KeyboardButton("Назад")]
    ]
    await update.message.reply_text("Укажите номер заказа:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return REQUEST_ORDER_NUMBER


# bot/handlers/admin.py

order_status_messages = {
    "Принят": "Ваш заказ принят и находится в обработке. Если вы считаете, что это ошибка, свяжитесь с нами тут: t.me/nothardchat.",
    "Возврат": "Ваш заказ был возвращен. Если вы считаете, что это ошибка, свяжитесь с нами тут: t.me/nothardchat.",
    "Отменен": "Ваш заказ был отменен. Если вы считаете, что это ошибка, свяжитесь с нами тут: t.me/nothardchat.",
    "Ожидание": "Ваш заказ находится в ожидании обработки. Если вы считаете, что это ошибка, свяжитесь с нами тут: t.me/nothardchat.",
    "Ожидание оплаты": "Ваш заказ ожидает оплаты. Если вы считаете, что это ошибка, свяжитесь с нами тут: t.me/nothardchat.",
    "Выполняется": "Ваш заказ в процессе выполнения. Если вы считаете, что это ошибка, свяжитесь с нами тут: t.me/nothardchat.",
    "Выполнен": "Ваш заказ успешно выполнен. Если вы считаете, что это ошибка, свяжитесь с нами тут: t.me/nothardchat.",
}

view_orders_info = "Для просмотра статуса ващего заказа перейдите в главное меню, затем нажмите на '📦 Мои заказы', выберите нужный номер заказа. Бот отравит вам статус вашего заказа в чат."

# Обновление статуса заказа





# Обновляем функцию admin_panel_keyboard
def admin_panel_keyboard():
    keyboard = [
        [KeyboardButton("Список пользователей")],
        [KeyboardButton("Список заказов")],
        [KeyboardButton("Отзывы")],
        [KeyboardButton("Назад")]
    ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_order_by_id(order_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT order_id, user_id, order_date, status, paid, payment_method FROM orders WHERE order_id = ?", (order_id,))
        row = c.fetchone()
        if row:
            return {
                "order_id": row[0],
                "user_id": row[1],
                "order_date": row[2],
                "status": row[3],
                "paid": row[4],
                "payment_method": row[5]  # Возвращаем метод оплаты
            }
        return None

def update_order_status(order_id, status):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        conn.commit()

def get_all_users():
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, name, phone, email FROM users")
        return [{"user_id": row[0], "name": row[1], "phone": row[2], "email": row[3]} for row in c.fetchall()]


def get_task_by_id(task_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT task_id, order_id, task_description, status, cloud_link FROM order_tasks WHERE task_id = ?", (task_id,))
        row = c.fetchone()
        if row:
            task = {
                "task_id": row[0],
                "order_id": row[1],
                "task_description": row[2],
                "status": row[3],
                "cloud_link": row[4]
            }
            # Теперь извлекаем user_id на основе order_id
            c.execute("SELECT user_id FROM orders WHERE order_id = ?", (task['order_id'],))
            user_row = c.fetchone()
            if user_row:
                task['user_id'] = user_row[0]  # Добавляем user_id в результат
            return task
        return None


def get_order_id_by_order_item_id(order_item_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT order_id FROM order_items WHERE order_item_id = ?", (order_item_id,))
        row = c.fetchone()
        return row[0] if row else None

def get_user_id_by_order_id(order_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM orders WHERE order_id = ?", (order_id,))
        row = c.fetchone()
        return row[0] if row else None
    
def update_order_payment_status(order_id, paid):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE orders SET paid = ? WHERE order_id = ?", (paid, order_id))
        conn.commit()

def property_status_keyboard(properties):
    keyboard = []
    for prop in properties:
        keyboard.append([KeyboardButton(f"{prop['order_item_id']} - {prop['item']}")])
    keyboard.append([KeyboardButton("Назад")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# Обновленные функции для работы с базой данных
def get_order_properties(order_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT order_item_id, item, status FROM order_items WHERE order_id = ? AND item_type = 'property'", (order_id,))
        properties = []
        for row in c.fetchall():
            item_html = row[1]
            if item_html.startswith('http'):
                properties.append({
                    "order_item_id": row[0],
                    "item": item_html,
                    "status": row[2]
                })
            else:
                property_soup = BeautifulSoup(item_html, "html.parser")
                title_element = property_soup.find("h2", class_="propertyCard-title")
                price_element = property_soup.find("span", class_="propertyCard-priceValue")
                address_element = property_soup.find("address", class_="propertyCard-address")
                link_element = property_soup.find("a", class_="propertyCard-link")

                title = title_element.get_text(strip=True) if title_element else "N/A"
                price = price_element.get_text(strip=True) if price_element else "N/A"
                address = address_element.get_text(strip=True) if address_element else "N/A"
                link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else "N/A"

                properties.append({
                    "order_item_id": row[0],
                    "title": title,
                    "price": price,
                    "address": address,
                    "link": link,
                    "status": row[2]
                })
        return properties


def get_property_by_id(order_item_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT order_item_id, order_id, item, status FROM order_items WHERE order_item_id = ?", (order_item_id,))
        row = c.fetchone()
        if row:
            item_html = row[2]
            if item_html.startswith('http'):
                return {"order_item_id": row[0], "order_id": row[1], "item": item_html, "status": row[3]}
            else:
                property_soup = BeautifulSoup(item_html, "html.parser")
                title_element = property_soup.find("h2", class_="propertyCard-title")
                title = title_element.get_text(strip=True) if title_element else "N/A"
                return {"order_item_id": row[0], "order_id": row[1], "title": title, "status": row[3]}
        return None


async def get_order_tasks(order_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT task_id, task_description, status FROM order_tasks WHERE order_id = ?", (order_id,))
        return [{"task_id": row[0], "task_description": row[1], "status": row[2]} for row in c.fetchall()]

def get_individual_services(order_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("""
            SELECT order_item_id, item, status
            FROM order_items
            WHERE order_id = ? AND item_type = 'individual_service'
            """, (order_id,))
        return [{"order_item_id": row[0], "item": row[1], "status": row[2]} for row in c.fetchall()]

def task_status_keyboard(tasks):
    keyboard = []
    for task in tasks:
        keyboard.append([KeyboardButton(f"{task['task_id']} - {task['task_description']}")])
    keyboard.append([KeyboardButton("Назад")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_individual_service_by_id(order_item_id):
    try:
        logger.info(f"Starting query for individual service with ID: {order_item_id} in order_items table")
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT order_item_id, order_id, item, status, item_type FROM order_items WHERE order_item_id = ?", (order_item_id,))
            row = c.fetchone()
            if row:
                logger.info(f"Query successful. Retrieved row: {row}")
                if row[4] == 'individual_service':  # Check if this is truly an individual service
                    logger.info(f"Individual service found: {row}")
                    return {"order_item_id": row[0], "order_id": row[1], "item": row[2], "status": row[3]}
                else:
                    logger.warning(f"Record found, but item_type is not 'individual_service'. Actual type: {row[4]}")
                    return {"order_item_id": row[0], "order_id": row[1], "item": row[2], "status": row[3], "item_type": row[4]}
            else:
                logger.warning(f"No individual service found with ID: {order_item_id}")
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving individual service with ID {order_item_id}: {e}")
        return None
    

def update_individual_service_status(order_item_id, status):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE order_items SET status = ? WHERE order_item_id = ? AND item_type = 'individual_service'", (status, order_item_id))
        conn.commit()
        return c.rowcount > 0  # Возвращаем True, если была обновлена хотя бы одна строка
    

import sqlite3
import logging

logger = logging.getLogger(__name__)

def update_order_task_status(task_id, status, cloud_link=None):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()

        # Проверяем, является ли статус текстом или ключом
        if status in status_map_tasks.values():
            status_to_save = status  # Если это ключ, сохраняем его как есть
        else:
            # Если это текст, преобразуем в ключ
            status_to_save = status_map_tasks.get(status, status)

        logger.debug(f"Updating task {task_id} with status key '{status_to_save}'")

        # Обновляем задачу в order_tasks
        c.execute("UPDATE order_tasks SET status = ? WHERE task_id = ?", (status_to_save, task_id))

        # Если задача не обновлена, пробуем обновить индивидуальную услугу в order_items
        if c.rowcount == 0:
            c.execute("UPDATE order_items SET status = ? WHERE order_item_id = ? AND item_type = 'individual_service'", (status_to_save, task_id))

        # Обновляем ссылку на облако, если она предоставлена
        if cloud_link:
            c.execute("UPDATE order_tasks SET cloud_link = ? WHERE task_id = ?", (cloud_link, task_id))

        conn.commit()

async def get_order_tasks(order_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT task_id, task_description, status FROM order_tasks WHERE order_id = ?", (order_id,))
        return [{"task_id": row[0], "task_description": row[1], "status": row[2]} for row in c.fetchall()]