# bot/handlers/subscribe.py

import sqlite3
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.utils.database import get_all_orders, get_user_language, get_user_orders
from bot.handlers.language import get_message

import sqlite3
import requests
from telegram import InputMediaPhoto, Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackContext
from bot.handlers.addproperty import LOAD_PROPERTY_LINK, load_property_link
from bot.handlers.common import show_main_menu
from bot.handlers.language import get_message
from bot.handlers.property_search import clear_previous_messages
from bot.utils.database import add_bonus_like, add_property_to_order_db, add_to_cart_db, decrement_user_bonuses, get_bonus_likes, get_order_tasks, get_user_bonuses, get_user_language, get_user_orders, remove_bonus_like, update_property_status, update_task_status
from bs4 import BeautifulSoup
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LINKED_ORDER, LINKED_NAVIGATE_ORDERS, LINKED_BONUS_ACTIONS = range(60, 63)
LINKED_BONUS_PRICE, LINKED_BONUS_ROOMS, LINKED_BONUS_PROPERTY_TYPE, LINKED_BONUS_FURNISH, LINKED_BONUS_LIVING_TYPE, LINKED_BONUS_SHOW_RESULTS, LINKED_BONUS_NAVIGATE_RESULTS = range(63, 70)
LINKED_BONUS_LIKES, LINKED_BONUS_LIKED_PROPERTY, LINKED_BONUS_ADD_TO_ORDER_FROM_LIKES = range(70, 73)

CONFIRM_UNLINK_ORDER = range(74)



# Функция для получения привязанных заказов
def get_user_linked_orders(user_id: int):
    """
    Получаем привязанные заказы пользователя.
    
    :param user_id: ID пользователя
    :return: Список ID заказов или пустой список, если нет привязанных заказов
    """
    try:
        with sqlite3.connect('bot.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Получаем все заказы, к которым пользователь привязан
            c.execute("SELECT order_id FROM order_subscribers WHERE user_id = ?", (user_id,))
            orders = c.fetchall()

        # Преобразуем результат в список
        order_ids = [order['order_id'] for order in orders]
        
        return order_ids  # Возвращаем пустой список, если нет заказов
    except sqlite3.Error as e:
        print(f"Произошла ошибка при получении привязанных заказов: {e}")
        return []
    


import logging
logger = logging.getLogger(__name__)

async def linked_show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    
    # Получаем привязанные заказы пользователя
    linked_orders = get_user_linked_orders(user_id)

    # Логируем результат
    logger.info(f"Linked orders for user {user_id}: {linked_orders}")

    # Определяем язык пользователя с помощью функции get_user_language
    language = get_user_language(user_id)
    
    if not linked_orders:
        await (update.message or update.callback_query.message).reply_text(get_message(language, 'linked_orders_no_orders'))
        return ConversationHandler.END

    # Формируем клавиатуру с привязанными заказами
    keyboard = [
        [KeyboardButton(f"{get_message(language, 'orders_order')} #{order_id}")] for order_id in linked_orders
    ]
    keyboard.append([KeyboardButton(get_message(language, 'orders_back_to_menu'))])
    
    # Отправляем сообщение с выбором заказа
    await (update.message or update.callback_query.message).reply_text(
        get_message(language, 'orders_select_order'), 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    
    return LINKED_ORDER

import datetime

import re
import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup



import datetime

async def linked_select_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = get_user_language(update.effective_user.id)  # Получаем язык пользователя

    # Получаем текст сообщения и извлекаем номер заказа
    order_text = update.message.text
    try:
        order_id = int(order_text.split('#')[1])
    except (IndexError, ValueError):
        await update.message.reply_text(get_message(language, 'orders_order_not_found'))
        return LINKED_ORDER
    
    # Сохраняем order_id в context.user_data
    context.user_data['selected_order_id'] = order_id

    # Логирование для проверки
    logger.info(f"Selected order_id: {order_id}")
    # Получаем все заказы
    orders = get_all_orders()

    # Поиск нужного заказа в списке
    order = None
    for o in orders:
        if o['order_id'] == order_id:
            order = o
            break

    # Проверка, найден ли заказ
    if not order:
        await update.message.reply_text(get_message(language, 'orders_order_not_found'))
        return ConversationHandler.END

    # Проверка наличия поля 'order_date' и его правильного формата
    if 'order_date' in order:
        try:
            order_date = datetime.datetime.fromisoformat(order['order_date']).strftime("%d-%m-%Y %H:%M:%S")
        except ValueError:
            order_date = get_message(language, 'orders_invalid_date')  # Если дата некорректна
    else:
        order_date = get_message(language, 'orders_date_not_available')  # Если дата отсутствует

    payment_method_map = {
        'cash': get_message(language, 'orders_payment_cash'),
        'PayMe': get_message(language, 'orders_payment_payme')
    }

    # Получение метода оплаты и статуса заказа
    payment_method = payment_method_map.get(order.get('payment_method', 'not_specified'), get_message(language, 'orders_payment_not_specified'))
    payment_status = get_message(language, 'orders_paid') if order.get('paid', 0) == 1 else get_message(language, 'orders_not_paid')

    # Получение статуса заказа
    order_status_key = order["status"] if order["status"].startswith('order_status_') else f'order_status_{order["status"]}'
    order_status = get_message(language, order_status_key)

    # Формирование сообщения
    message = get_message(
        language,
        'orders_details',
        order_id=escape_markdown_v2(str(order_id)),
        order_date=escape_markdown_v2(order_date),
        status=escape_markdown_v2(order_status),
        payment_method=escape_markdown_v2(payment_method),
        payment_status=escape_markdown_v2(payment_status)
    )

    # Формирование клавиатуры
    keyboard = [
        [KeyboardButton(get_message(language, 'orders_subscriber_purchased_services')), KeyboardButton(get_message(language, 'orders_subscriber_property_requests'))],
        [KeyboardButton(get_message(language, 'orders_timeline'))],  # Добавляем кнопку "RemoveOrder"
        [KeyboardButton(get_message(language, 'orders_remove_order'))],  # Добавляем кнопку "RemoveOrder"
        [KeyboardButton(get_message(language, 'orders_back_to_orders'))]
    ]

    await update.message.reply_text(
        message, 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True), 
        parse_mode='MarkdownV2'
    )
    
    return LINKED_NAVIGATE_ORDERS


import re

def escape_markdown(text: str) -> str:
    """Экранирует все специальные символы для MarkdownV2."""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

from telegram import ReplyKeyboardMarkup, KeyboardButton




async def linked_show_order_timeline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    order_id = context.user_data.get('selected_order_id')
    language = get_user_language(user_id)

    # Получаем события для данного заказа
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT event_description, event_timestamp, event_link FROM order_events WHERE order_id = ? ORDER BY event_timestamp ASC", (order_id,))
        events = c.fetchall()

    if not events:
        # Отправляем сообщение о том, что событий нет
        await update.message.reply_text(get_message(language, 'orders_no_timeline_events'))
        return await linked_back_to_order_details(update, context)

    # Заголовки для таймлайна и ссылки на трех языках
    headers = {
        'ru': '📅 Таймлайн заказа',
        'uz': '📅 Buyurtma vaqti',
        'en': '📅 Order Timeline'
    }

    link_texts = {
        'ru': 'Ссылка',
        'uz': 'Havola',
        'en': 'Link'
    }

    # Заголовок для таймлайна и текста для ссылки в зависимости от языка
    header_text = headers.get(language, headers['en'])
    link_text = link_texts.get(language, link_texts['en'])

    # Формируем текст для отображения с эмодзи и экранированием
    timeline_text = ""
    for event in events:
        # Преобразуем строку timestamp в объект datetime и форматируем в "день-месяц-год часы:минуты"
        event_time = datetime.datetime.strptime(event[1], '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M')
        event_time = escape_markdown(event_time)
        event_description = escape_markdown(event[0])
        event_link = event[2]

        # Добавляем эмодзи и текст с экранированием
        event_text = f"📝 {event_description}\n🕒 {event_time}"

        # Если есть ссылка, добавляем её под статусом с многоязычной поддержкой
        if event_link:
            event_text += f"\n🔗 [{link_text}]({event_link})"
        
        # Добавляем экранированный разделитель между событиями
        timeline_text += event_text + "\n\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\n"

    # Добавляем кнопку «Назад» для возврата к деталям заказа
    keyboard = [
        [KeyboardButton(get_message(language, 'linked_orders_back_to_details'))]  # Кнопка "Назад к деталям"
    ]

    await update.message.reply_text(
        f"{header_text}:\n\n{timeline_text}",
        parse_mode='MarkdownV2',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return LINKED_NAVIGATE_ORDERS


async def remove_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    order_id = context.user_data.get('selected_order_id')

    if not order_id:
        await update.message.reply_text("Order ID not found!")
        return LINKED_ORDER
    
    language = get_user_language(user_id)  # Получаем язык пользователя
    
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()

            # Удаляем запись из order_subscribers
            c.execute("DELETE FROM order_subscribers WHERE user_id = ? AND order_id = ?", (user_id, order_id))
            conn.commit()

        # Подтверждаем отвязывание заказа на нужном языке, разделив сообщение на две части
        part1 = get_message(language, 'order_unlinked_part1')
        part2 = get_message(language, 'order_unlinked_part2')
        
        await update.message.reply_text(f"{part1} #{order_id} {part2}")

        # Возвращаемся к выбору привязанных заказов

    except sqlite3.Error as e:
        await update.message.reply_text(f"An error occurred while removing the order: {e}")
        return LINKED_ORDER


async def ask_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = get_user_language(update.effective_user.id)

    # Формируем клавиатуру с кнопками "Да" и "Нет"
    keyboard = [
        [KeyboardButton(get_message(language, 'yes')), KeyboardButton(get_message(language, 'no'))]
    ]

    await update.message.reply_text(
        get_message(language, 'orders_confirm_unlink'),  # Вопрос на подтверждение
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )

    return CONFIRM_UNLINK_ORDER  # Переходим в состояние подтверждения


async def confirm_unlink_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = get_user_language(update.effective_user.id)
    user_id = update.message.from_user.id

    user_response = update.message.text.lower()

    if user_response == get_message(language, 'yes').lower():
        # Пользователь подтвердил удаление
        await remove_order(update, context)  # Отвязываем заказ

        # Проверяем, есть ли у пользователя еще заказы
        linked_orders = get_user_linked_orders(user_id)

        if linked_orders:
            # Если есть заказы, возвращаем его на выбор заказов
            await linked_show_orders(update, context)
            return LINKED_ORDER
        else:
            # Если заказов больше нет, возвращаем в главное меню
            await show_main_menu(update, context)
            return ConversationHandler.END

    elif user_response == get_message(language, 'no').lower():
        # Пользователь отказался, возвращаемся к выбору заказа
        await update.message.reply_text(get_message(language, 'orders_canceled_unlink'))
        return await linked_show_orders(update, context)  # Показать заказы снова
    else:
        # Неверный ввод, повторяем запрос
        await update.message.reply_text(get_message(language, 'orders_invalid_input'))
        return CONFIRM_UNLINK_ORDER


async def linked_show_main_menu_with_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: str) -> int:
    user_id = update.message.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    main_menu_button = [[KeyboardButton(get_message(language, 'bonus_main_menu'))]]
    reply_markup = ReplyKeyboardMarkup(main_menu_button, resize_keyboard=True)

    if update.message:
        await update.message.reply_text(error_message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(error_message, reply_markup=reply_markup)

    return ConversationHandler.END




import re
import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup

def escape_markdown_v2(text: str) -> str:
    """
    Helper function to escape characters for Telegram's MarkdownV2.
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)


async def linked_back_to_order_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    # Проверка, был ли выбран заказ ранее
    if 'selected_order_id' not in context.user_data:
        logger.error("No selected_order_id found in context.")
        await update.message.reply_text(
            get_message(language, 'orders_order_not_found'),
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(get_message(language, 'orders_back_to_orders'))]], resize_keyboard=True)
        )
        return LINKED_ORDER  # Возвращаем пользователя к выбору заказа

    # Получаем ID выбранного заказа
    order_id = context.user_data['selected_order_id']
    logger.info(f"Using selected_order_id from context: {order_id}")

    # Получаем все заказы
    orders = get_all_orders()
    logger.debug(f"Retrieved all orders: {orders}")

    # Ищем заказ по order_id
    order = next((o for o in orders if o['order_id'] == order_id), None)
    
    if not order:
        logger.error(f"Order with ID {order_id} not found in retrieved orders.")
        await update.message.reply_text(
            get_message(language, 'orders_order_not_found'),
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(get_message(language, 'orders_back_to_orders'))]], resize_keyboard=True)
        )
        return LINKED_ORDER  # Возвращаем пользователя к выбору заказа

    # Преобразуем дату заказа в нужный формат
    if 'order_date' in order:
        try:
            order_date = datetime.datetime.fromisoformat(order['order_date']).strftime("%d-%m-%Y %H:%M:%S")
        except ValueError:
            order_date = get_message(language, 'orders_invalid_date')
    else:
        order_date = get_message(language, 'orders_date_not_available')

    # Сопоставление метода оплаты
    payment_method_map = {
        'cash': get_message(language, 'orders_payment_cash'),
        'PayMe': get_message(language, 'orders_payment_payme')
    }
    payment_method = payment_method_map.get(order.get('payment_method', 'not_specified'), get_message(language, 'orders_payment_not_specified'))

    # Определение статуса оплаты
    payment_status = get_message(language, 'orders_paid') if order.get('paid', 0) == 1 else get_message(language, 'orders_not_paid')

    # Получение статуса заказа
    order_status_key = order["status"] if order["status"].startswith('order_status_') else f'order_status_{order["status"]}'
    order_status = get_message(language, order_status_key)

    # Формирование сообщения
    message = get_message(
        language,
        'orders_details',
        order_id=escape_markdown_v2(str(order_id)),
        order_date=escape_markdown_v2(order_date),
        status=escape_markdown_v2(order_status),
        payment_method=escape_markdown_v2(payment_method),
        payment_status=escape_markdown_v2(payment_status)
    )

    # Формирование клавиатуры
    keyboard = [
        [KeyboardButton(get_message(language, 'orders_subscriber_purchased_services')), KeyboardButton(get_message(language, 'orders_subscriber_property_requests'))],
        [KeyboardButton(get_message(language, 'orders_timeline'))],  # Добавляем кнопку "RemoveOrder"
        [KeyboardButton(get_message(language, 'orders_remove_order'))],  # Добавляем кнопку "RemoveOrder"
        [KeyboardButton(get_message(language, 'orders_back_to_orders'))]
    ]

    # Отправляем сообщение с деталями заказа
    await update.message.reply_text(
        message, 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True), 
        parse_mode='MarkdownV2'
    )
    
    return LINKED_NAVIGATE_ORDERS







# Функция для клавиатуры с кнопкой "Назад"
def linked_back_keyboard(language):
    return ReplyKeyboardMarkup([[KeyboardButton(get_message(language, 'bonus_back'))]], resize_keyboard=True, one_time_keyboard=True)




def linked_translate_status(status, language):
    status_translations = {
    'Ожидание ответа агента': {
        'ru': 'Ожидание ответа агента',
        'en': 'Waiting for agent response',
        'uz': 'Agentdan javob kutilyapti'
    },
    'Бронь забронирована': {
        'ru': 'Бронь забронирована',
        'en': 'Viewing booked',
        'uz': 'Koʻrish uchun joy band qilindi'
    },
    'Иду смотреть': {
        'ru': 'Иду смотреть',
        'en': 'Going to view',
        'uz': 'Koʻrishga ketyapman'
    },
    'Идет просмотр объекта': {
        'ru': 'Идет просмотр объекта',
        'en': 'Viewing in progress',
        'uz': 'Koʻrish jarayonida'
    },
    'Объект просмотрен': {
        'ru': 'Объект просмотрен',
        'en': 'Property viewed',
        'uz': 'Koʻrilgan'
    },
    'Результат готов': {
        'ru': 'Результат готов',
        'en': 'Result ready',
        'uz': 'Natija tayyor'
    },
    'Просмотр отменен': {
        'ru': 'Просмотр отменен',
        'en': 'Viewing cancelled',
        'uz': 'Koʻrish bekor qilindi'
    }
}
        # Проверяем, есть ли перевод для данного статуса
    if status in status_translations:
        return status_translations[status].get(language, status)
    return status  # Если нет перевода, возвращаем исходный статус





import asyncio  # Для задержек, если они понадобятся

def escape_markdown_v2(text: str) -> str:
    """
    Helper function to escape characters for Telegram's MarkdownV2.
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)



async def linked_show_ordered_properties(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        # Получаем язык пользователя
        user_id = update.effective_user.id
        language = get_user_language(user_id)

        # Получаем order_id из контекста
        order_id = context.user_data.get('selected_order_id')
        if not order_id:
            logger.error("No selected_order_id found in user data.")
            await update.message.reply_text(get_message(language, 'orders_order_not_found'))
            return await linked_back_to_order_details(update, context)

        logger.info(f"Using selected_order_id: {order_id}")

        # Получаем элементы заказа (недвижимость) из таблицы order_items по OrderId
        order_items = linked_get_order_items_by_order_id(order_id)
        logger.debug(f"Order items for order_id={order_id}: {order_items}")

        # Если нет объектов недвижимости, отправляем сообщение с кнопкой "Назад"
        if not order_items:
            logger.error(f"No items found for order_id={order_id}")

            # Формируем клавиатуру с кнопкой "Назад"
            keyboard = [[KeyboardButton(get_message(language, 'orders_back'))]]
            
            # Отправляем сообщение с информацией о том, что недвижимости нет
            await update.message.reply_text(
                escape_markdown_v2(get_message(language, 'orders_no_properties')), 
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
                parse_mode='MarkdownV2'
            )

            return LINKED_NAVIGATE_ORDERS

        properties = []

        # Обработка недвижимости для заказа
        for item in order_items:
            if item['item_type'] == 'property':  # Проверяем тип элемента
                status = item['status'] or get_message(language, 'orders_not_available')
                status_translated = linked_translate_status(status, language)  # Перевод статуса

                cloud_link = item.get('cloud_link')
                # Определяем причину или дату брони на основе исходного статуса
                if status == 'Просмотр отменен':
                    reason = cloud_link
                elif status == 'Бронь забронирована':
                    reservation_datetime = cloud_link
                else:
                    reason = None
                    reservation_datetime = None

                # Проверяем, является ли это ссылкой на недвижимость
                if item.get('item', '').startswith('http'):
                    property_info = (f"{get_message(language, 'orders_user_added_property')}\n"
                                     f"🔗 [{get_message(language, 'orders_link')}]({item['item']})\n"
                                     f"🏷️ {get_message(language, 'orders_status')}: {escape_markdown_v2(status_translated)}")

                    # Обработка различных статусов
                    if status_translated == linked_translate_status('Результат готов', language) and cloud_link:
                        report_label = linked_get_report_label(language)  # Получаем перевод слова "Report"
                        property_info += f"\n📄 {report_label} : [Link for viewing]({escape_markdown_v2(cloud_link)})"

                    elif status_translated == linked_translate_status('Просмотр отменен', language) and reason:
                        property_info += f"\n🚫 {get_message(language, 'orders_cancellation_reason')}: {escape_markdown_v2(reason)}"

                    elif status_translated == linked_translate_status('Бронь забронирована', language) and reservation_datetime:
                        property_info += f"\n📅 {get_message(language, 'reservation_date_message')}: {escape_markdown_v2(reservation_datetime)}"

                    properties.append(property_info)
                else:
                    # Обрабатываем HTML содержимое
                    property_soup = BeautifulSoup(item['item'], "html.parser")
                    title_element = property_soup.find("h2", class_="propertyCard-title")
                    price_element = property_soup.find("span", class_="propertyCard-priceValue")
                    address_element = property_soup.find("address", class_="propertyCard-address")
                    link_element = property_soup.find("a", class_="propertyCard-link")

                    title = title_element.get_text(strip=True) if title_element else get_message(language, 'orders_not_available')
                    price = price_element.get_text(strip=True) if price_element else get_message(language, 'orders_not_available')
                    address = address_element.get_text(strip=True) if address_element else get_message(language, 'orders_not_available')
                    link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else get_message(language, 'orders_not_available')

                    property_info = (f"🏡 {get_message(language, 'orders_property_name')}: {escape_markdown_v2(title)}\n"
                                     f"💰 {get_message(language, 'orders_price')}: {escape_markdown_v2(price)}\n"
                                     f"📍 {get_message(language, 'orders_address')}: {escape_markdown_v2(address)}\n"
                                     f"🔗 [{get_message(language, 'orders_link')}]({escape_markdown_v2(link)})\n"
                                     f"🏷️ {get_message(language, 'orders_status')}: {escape_markdown_v2(status_translated)}")

                    # Обработка различных статусов
                    if status_translated == linked_translate_status('Результат готов', language) and cloud_link:
                        report_label = linked_get_report_label(language)  # Получаем перевод слова "Report"
                        property_info += f"\n📄 {report_label} : [Link for viewing]({escape_markdown_v2(cloud_link)})"

                    elif status_translated == linked_translate_status('Просмотр отменен', language) and reason:
                        property_info += f"\n🚫 {get_message(language, 'orders_cancellation_reason')}: {escape_markdown_v2(reason)}"

                    elif status_translated == linked_translate_status('Бронь забронирована', language) and reservation_datetime:
                        property_info += f"\n📅 {get_message(language, 'reservation_date_message')}: {escape_markdown_v2(reservation_datetime)}"

                    properties.append(property_info)

        # Формируем сообщение для пользователя
        properties_text = "\n\n".join(properties) if properties else escape_markdown_v2(get_message(language, 'orders_no_properties'))

        # Формируем клавиатуру с кнопкой "Назад"
        keyboard = [[KeyboardButton(get_message(language, 'orders_back'))]]

        # Отправляем сообщение с заказами и клавиатурой
        await update.message.reply_text(
            properties_text, 
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
            parse_mode='MarkdownV2'
        )
        
        return LINKED_NAVIGATE_ORDERS

    except Exception as e:
        logger.error(f"An error occurred in linked_show_ordered_properties: {str(e)}")
        await update.message.reply_text("An unexpected error occurred.")
        return await linked_back_to_order_details(update, context)




def linked_get_order_items_by_order_id(order_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT item_type, item, status, cloud_link FROM order_items WHERE order_id = ?", (order_id,))
            items = []
            for row in c.fetchall():
                items.append({
                    "item_type": row[0],
                    "item": row[1],
                    "status": row[2],
                    "cloud_link": row[3]
                })
            logger.info(f"Retrieved order items for order_id={order_id}: {items}")
            return items
    except sqlite3.Error as e:
        logger.error(f"Error retrieving order items for order_id={order_id}: {e}")
        return []
    


def linked_get_report_label(language):
    """Возвращает перевод слова 'Report' в зависимости от языка пользователя"""
    if language == 'ru':
        return 'Отчет'
    elif language == 'uz':
        return 'Hisobot'
    else:
        return 'Report'



async def linked_update_property_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data.split('_')

    if len(data) < 4 or data[0] != 'update' or data[1] != 'property':
        await query.answer("Неверный формат данных.")
        return

    try:
        order_item_id = int(data[2])
        status = data[3]
    except (ValueError, IndexError):
        await query.answer("Неверный формат данных.")
        return

    update_property_status(order_item_id, status)

    await query.answer(f"Статус недвижимости обновлен на '{status}'")
    await linked_show_ordered_properties(update, context)


TASK, UPDATE_TASK = range(2)



import re

def escape_markdown_v2(text: str) -> str:
    """
    Helper function to escape characters for Telegram's MarkdownV2.
    """
    # Пропускаем экранирование в URL, оставляя точки нетронутыми
    def escape_callback(match):
        url = match.group(0)
        return re.sub(r'([_*[\]()~`>#+=|{}.!-])', r'\\\1', url)

    text = re.sub(r'https?://\S+', escape_callback, text)
    
    # Экранируем остальные символы
    return re.sub(r'([_*[\]()~`>#+=|{}.!-])', r'\\\1', text)



import logging

logger = logging.getLogger(__name__)





def escape_markdown_v2(text: str) -> str:
    """
    Helper function to escape characters for Telegram's MarkdownV2.
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

async def linked_show_ordered_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        # Получаем язык пользователя
        language = get_user_language(update.effective_user.id)

        # Получаем order_id из контекста
        order_id = context.user_data.get('selected_order_id')
        if not order_id:
            logger.error("No selected_order_id found in user data.")
            await update.message.reply_text(get_message(language, 'orders_order_not_found'))
            return LINKED_NAVIGATE_ORDERS

        logger.info(f"Using selected_order_id: {order_id}")

        # Получаем все заказы (больше не нужно учитывать user_id, только order_id)
        orders = get_all_orders()  # Функция теперь возвращает все заказы
        logger.debug(f"Orders: {orders}")

        # Проверяем, существует ли заказ с данным order_id
        order = next((o for o in orders if o['order_id'] == order_id), None)
        if not order:
            logger.error(f"Order ID {order_id} not found.")
            await update.message.reply_text(get_message(language, 'orders_order_not_found'))
            return LINKED_NAVIGATE_ORDERS

        services = []
        status_emoji_map = {
            'completed': "✅",
            'in_progress': "🔄",
            'not_completed': "❌"
        }

        task_icons = {
            # Define specific icons for tasks if needed
        }

        # Получаем задачи для данного заказа
        service_tasks = await get_order_tasks(order_id)
        logger.debug(f"Service tasks for order {order_id}: {service_tasks}")

        if service_tasks:
            for task in service_tasks:
                task_key = task['task_description']
                task_icon = task_icons.get(task_key, '📌')
                task_description = get_message(language, task_key)

                status_cleaned = task['status'].replace('task_status_', '')
                task_status = get_message(language, f'task_status_{status_cleaned}')
                task_status_emoji = status_emoji_map.get(status_cleaned, "❌")

                # Escape the task description and status, not the URL
                task_info = f"{task_icon} {escape_markdown_v2(task_description)}:\n{task_status_emoji} {escape_markdown_v2(task_status)}"

                # If the task is completed and has a cloud link, show the link without escaping it
                if status_cleaned == 'completed' and task.get('cloud_link'):
                    report_label = {
                        'ru': "📃 Отчет :",
                        'uz': "📃 Hisobot :",
                        'en': "📃 Report :"
                    }[language]
                    cloud_link = escape_markdown_v2(task['cloud_link'])

                    task_info += f"\n{escape_markdown_v2(report_label)} [{cloud_link}]({cloud_link})"
                services.append(task_info)

        services_text = "\n\n".join(services) if services else escape_markdown_v2(get_message(language, 'orders_no_services'))

        # Формируем клавиатуру
        keyboard = [[KeyboardButton(get_message(language, 'linked_orders_back_to_details'))]]  
        await update.message.reply_text(
            services_text, 
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True), 
            parse_mode='MarkdownV2'
        )
        return LINKED_NAVIGATE_ORDERS
    
    except Exception as e:
        logger.error(f"An error occurred in show_ordered_services: {str(e)}")
        await update.message.reply_text("An unexpected error occurred.")
        return LINKED_NAVIGATE_ORDERS






async def linked_back_to_orders_from_bonuses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Вызываем функцию, которая покажет заказы, возвращая к состоянию NAVIGATE_ORDERS
    return await linked_back_to_order_details(update, context)



async def linked_update_task_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from bot.handlers.property_search import show_order_tasks

    query = update.callback_query
    data = query.data.split('_')

    if len(data) < 5 or data[0] != 'update' or data[1] != 'task':
        await query.answer("Неверный формат данных.")
        return

    try:
        order_id = int(data[2])
        task_id = int(data[3])
        status = data[4]
    except (ValueError, IndexError):
        await query.answer("Неверный формат данных.")
        return

    update_task_status(task_id, status)

    await query.answer(f"Статус задачи обновлен на '{status}'")
    await show_order_tasks(update, context)


def get_task(task_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT task_id, order_id, task_description, status FROM order_tasks WHERE task_id = ?", (task_id,))
        row = c.fetchone()
        if row:
            return {"task_id": row[0], "order_id": row[1], "description": row[2], "status": row[3]}
        return None


async def linked_back_to_task_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = query.data.split("_")
    if len(data) < 3:
        await query.answer("Неверный формат данных.")
        return TASK  # Обновляем состояние

    try:
        order_id = int(data[2])
    except ValueError:
        await query.answer("Неверный формат данных.")
        return TASK  # Обновляем состояние

    await query.message.edit_text("Выберите статус задачи:", reply_markup=linked_task_status_keyboard(order_id))
    return TASK  # Обновляем состояние


def linked_task_status_keyboard(order_id):
    tasks = get_order_tasks(order_id)
    keyboard = []
    for task in tasks:
        keyboard.append([InlineKeyboardButton(f"{task['description']} - Выполнено", callback_data=f"update_task_{task['task_id']}_Выполнено")])
        keyboard.append([InlineKeyboardButton(f"{task['description']} - Выполняется", callback_data=f"update_task_{task['task_id']}_Выполняется")])
        keyboard.append([InlineKeyboardButton(f"{task['description']} - Не выполнено", callback_data=f"update_task_{task['task_id']}_Не_выполнено")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_task_status_{order_id}")])
    return InlineKeyboardMarkup(keyboard)


async def linked_select_task_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = query.data.split('_')
    print(f"Received callback data: {data}")  # Отладочное сообщение
    if len(data) < 4:
        await query.answer("Неверный формат данных.")
        return TASK

    try:
        order_id = int(data[2])
        task_id = int(data[3])
    except ValueError:
        await query.answer("Неверный формат данных.")
        return TASK

    print(f"Order ID: {order_id}, Task ID: {task_id}")  # Отладочное сообщение

    task = get_task(task_id)

    if not task:
        await query.answer("Задача не найдена.")
        return TASK

    keyboard = [
        [InlineKeyboardButton("Выполняется", callback_data=f"update_task_{order_id}_{task_id}_Выполняется")],
        [InlineKeyboardButton("Выполнено", callback_data=f"update_task_{order_id}_{task_id}_Выполнено")],
        [InlineKeyboardButton("Не выполнено", callback_data=f"update_task_{order_id}_{task_id}_Не_выполнено")],
        [InlineKeyboardButton("Назад", callback_data=f"show_order_tasks_{order_id}")]
    ]

    await query.message.edit_text(f"Изменить статус задачи: {task['description']}", reply_markup=InlineKeyboardMarkup(keyboard))
    return TASK


async def linked_back_to_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.message.delete()
    return await linked_show_orders(update, context)
