# bot/handlers/orders.py

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
from datetime import datetime







logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ORDER, NAVIGATE_ORDERS, BONUS_ACTIONS = range(18, 21)
BONUS_PRICE, BONUS_ROOMS, BONUS_PROPERTY_TYPE, BONUS_FURNISH, BONUS_LIVING_TYPE, BONUS_SHOW_RESULTS, BONUS_NAVIGATE_RESULTS = range(40, 47)
BONUS_LIKES, BONUS_LIKED_PROPERTY, BONUS_ADD_TO_ORDER_FROM_LIKES = range(47, 50)


async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    orders = get_user_orders(user_id)

    # Определяем язык пользователя с помощью функции get_user_language
    language = get_user_language(user_id)
    
    if not orders:
        await (update.message or update.callback_query.message).reply_text(get_message(language, 'orders_no_orders'))
        return ConversationHandler.END

    keyboard = [
        [KeyboardButton(f"{get_message(language, 'orders_order')} #{order_id}")] for order_id in orders.keys()
    ]
    keyboard.append([KeyboardButton(get_message(language, 'orders_back_to_menu'))])
    
    await (update.message or update.callback_query.message).reply_text(
        get_message(language, 'orders_select_order'), 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return ORDER


import datetime

import re
import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup



async def select_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    order_text = update.message.text
    order_id = int(order_text.split('#')[1])
    context.user_data['selected_order_id'] = order_id

    # Получаем заказы пользователя
    orders = get_user_orders(user_id)
    order = orders[order_id]

    # Преобразование даты в нужный формат
    order_date = datetime.datetime.fromisoformat(order['date']).strftime("%d-%m-%Y %H:%M:%S")

    payment_method_map = {
        'cash': get_message(language, 'orders_payment_cash'),
        'PayMe': get_message(language, 'orders_payment_payme')
    }

    # Получение читаемого метода оплаты
    payment_method = payment_method_map.get(order.get('payment_method', 'not_specified'), get_message(language, 'orders_payment_not_specified'))
    payment_status = get_message(language, 'orders_paid') if order.get('paid', 0) == 1 else get_message(language, 'orders_not_paid')

    # Получение статуса заказа на основе языка
    order_status_key = order["status"] if order["status"].startswith('order_status_') else f'order_status_{order["status"]}'
    order_status = get_message(language, order_status_key)  # Получаем перевод статуса

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

    keyboard = [
        [KeyboardButton(get_message(language, 'orders_my_purchased_services')), KeyboardButton(get_message(language, 'orders_my_property_requests'))],
        [KeyboardButton(get_message(language, 'orders_my_bonuses')), KeyboardButton(get_message(language, 'orders_timeline'))],
        [KeyboardButton(get_message(language, 'orders_generate_share_link'))],  # Новая кнопка для таймлайна
        [KeyboardButton(get_message(language, 'orders_back_to_orders'))]
    ]

    await update.message.reply_text(
        message, 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True), 
        parse_mode='MarkdownV2'
    )
    return NAVIGATE_ORDERS



from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64
import urllib.parse

from config import SECRET_KEY
# Создаем экземпляр AES-GCM с использованием ключа
aesgcm = AESGCM(SECRET_KEY)

# Функция для шифрования данных с использованием AES-GCM
def encrypt_data_aes(data: str) -> str:
    nonce = os.urandom(12)  # Генерируем случайный 12-байтовый nonce
    encrypted_data = aesgcm.encrypt(nonce, data.encode(), None)
    return base64.urlsafe_b64encode(nonce + encrypted_data).decode()

# Функция для генерации уникальной ссылки с шифрованием AES-GCM
from telegram import KeyboardButton, ReplyKeyboardMarkup

from telegram import ReplyKeyboardRemove

async def generate_share_link(update, context) -> None:
    user_id = update.message.from_user.id
    language = get_user_language(user_id)

    # Получаем выбранный Order ID
    order_id = context.user_data.get('selected_order_id')
    
    if not order_id:
        await update.message.reply_text("Order ID is not selected.")
        return

    # Шифруем Order ID с использованием AES-GCM
    encrypted_data = encrypt_data_aes(f"{order_id}")
    
    # Генерация ссылки
    bot_username = 'notharduz_bot'
    share_link = f"https://t.me/{bot_username}?start=subscribe_{urllib.parse.quote(encrypted_data)}"
    
    # Формируем сообщение на нужном языке
    shareable_link_message = get_message(language, 'shareable_link_message')

    # Удаляем клавиатуру с кнопкой "Назад"
    await update.message.reply_text(f"{shareable_link_message}\n\n{share_link}", reply_markup=ReplyKeyboardRemove())

    # Показ главного меню
    await show_main_menu(update, context)






import re

def escape_markdown(text: str) -> str:
    """Экранирует все специальные символы для MarkdownV2."""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

from telegram import ReplyKeyboardMarkup, KeyboardButton





from datetime import datetime

async def show_order_timeline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        return await back_to_order_details(update, context)

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
        [KeyboardButton(get_message(language, 'orders_back_to_details'))]  # Кнопка "Назад к деталям"
    ]

    await update.message.reply_text(
        f"{header_text}:\n\n{timeline_text}",
        parse_mode='MarkdownV2',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return NAVIGATE_ORDERS




async def show_user_bonuses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Function show_user_bonuses called")
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя
    bonuses = get_user_bonuses(user_id)

    if bonuses > 0:
        if bonuses == 1:
            message = get_message(language, 'orders_bonuses_one_available')
        else:
            message = get_message(language, 'orders_bonuses_multiple_available', bonuses=bonuses)

        keyboard = [
            [KeyboardButton(get_message(language, 'orders_search_property')), KeyboardButton(get_message(language, 'orders_add_found_property'))],
            [KeyboardButton(get_message(language, 'orders_likes'))],
            [KeyboardButton(get_message(language, 'orders_back_to_orders'))]
        ]
    else:
        message = get_message(language, 'orders_no_bonuses_available')
        keyboard = [
            [KeyboardButton(get_message(language, 'orders_back_to_orders'))]
        ]

    if update.message:
        await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    else:
        await update.callback_query.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))

    return BONUS_ACTIONS



bonus_location_identifiers = {
    # Зона 1
    "Зона 1": "REGION%5E93817",  # Русский язык
    "Zone 1": "REGION%5E93817",  # Английский язык
    "1-Zona": "REGION%5E93817",  # Узбекский язык

    # Зона 2
    "Зона 2": "REGION%5E93814",  # Русский язык
    "Zone 2": "REGION%5E93814",  # Английский язык
    "2-Zona": "REGION%5E93814",  # Узбекский язык

    # Зона 3
    "Зона 3": "REGION%5E93883",  # Русский язык
    "Zone 3": "REGION%5E93883",  # Английский язык
    "3-Zona": "REGION%5E93883",  # Узбекский язык

    # Зона 4
    "Зона 4": "REGION%5E1420",  # Русский язык
    "Zone 4": "REGION%5E1420",  # Английский язык
    "4-Zona": "REGION%5E1420",  # Узбекский язык

    # Зона 5
    "Зона 5": "REGION%5E612",  # Русский язык
    "Zone 5": "REGION%5E612",  # Английский язык
    "5-Zona": "REGION%5E612",  # Узбекский язык

    # Зона 6
    "Зона 6": "REGION%5E1380",  # Русский язык
    "Zone 6": "REGION%5E1380",  # Английский язык
    "6-Zona": "REGION%5E1380",  # Узбекский язык

    # Неизвестная зона
    "Я не знаю": "REGION%5E87490",  # Русский язык
    "I don't know": "REGION%5E87490",  # Английский язык
    "Bilmayman": "REGION%5E87490",  # Узбекский язык
}



async def bonus_property_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Function bonus_property_search called")
    
    user_id = update.message.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    await update.message.reply_text(get_message(language, 'property_search_started'))

    if update.message.text == get_message(language, 'orders_back_to_orders'):
        return await show_user_bonuses(update, context)  # Возвращаемся к бонусам

    try:
        # Отправка изображения с зонами проживания
        with open('images/zones.png', 'rb') as image_file:
            await update.message.reply_photo(photo=image_file)

        await update.message.reply_text(get_message(language, 'bonus_select_zone'), reply_markup=bonus_zone_keyboard(language))
        return BONUS_PRICE
    except Exception as e:
        logger.error(f"Error in bonus_property_search: {e}")
        return ConversationHandler.END




def bonus_zone_keyboard(language):
    keyboard = [
        [KeyboardButton(get_message(language, 'bonus_zone_1')), KeyboardButton(get_message(language, 'bonus_zone_2'))],
        [KeyboardButton(get_message(language, 'bonus_zone_3')), KeyboardButton(get_message(language, 'bonus_zone_4'))],
        [KeyboardButton(get_message(language, 'bonus_zone_5')), KeyboardButton(get_message(language, 'bonus_zone_6'))],
        [KeyboardButton(get_message(language, 'bonus_zone_unknown'))],
        [KeyboardButton(get_message(language, 'orders_back_to_orders'))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)




import logging

# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def bonus_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    logger.info(f"User {user_id} entered bonus_price. Input: {update.message.text}")

    # Проверяем, нажал ли пользователь "Назад"
    if update.message.text == get_message(language, 'bonus_back'):
        logger.info(f"User {user_id} pressed Back, returning to previous state.")
        return await go_back(update, context)  # Переход на предыдущий шаг

    try:
        # Сохраняем выбранную зону
        context.user_data['zone'] = bonus_location_identifiers.get(update.message.text, "REGION%5E82835")
        context.user_data['current_state'] = BONUS_PRICE  # Сохраняем текущее состояние
        
        # Спрашиваем о максимальной цене
        await update.message.reply_text(get_message(language, 'property_enter_max_price'), reply_markup=back_keyboard(language))
        return BONUS_ROOMS
    except Exception as e:
        logger.error(f"Error in bonus_price: {e}")
        return ConversationHandler.END




async def bonus_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    logger.info(f"User {user_id} in bonus_rooms. Current state: {context.user_data.get('current_state')}, Input: {update.message.text}")

    # Проверяем, нажал ли пользователь "Назад"
    if update.message.text == get_message(language, 'bonus_back'):
        logger.info(f"User {user_id} pressed Back, returning to previous state.")
        return await go_back(update, context)

    try:
        context.user_data['price'] = update.message.text
        context.user_data['current_state'] = BONUS_ROOMS  # Сохраняем текущее состояние
        
        # Спрашиваем о количестве комнат
        await update.message.reply_text(get_message(language, 'property_enter_room_count'), reply_markup=bonus_rooms_keyboard(language))
        return BONUS_PROPERTY_TYPE
    except Exception as e:
        logger.error(f"Error in bonus_rooms: {e}")
        return ConversationHandler.END


def bonus_rooms_keyboard(language):
    keyboard = [
        [KeyboardButton(get_message(language, 'bonus_studio')), KeyboardButton("1")],
        [KeyboardButton("2"), KeyboardButton("3")],
        [KeyboardButton("4+")],
        [KeyboardButton(get_message(language, 'bonus_unknown'))],
        [KeyboardButton(get_message(language, 'bonus_back'))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)



async def bonus_property_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Function bonus_property_type called")
    user_id = update.message.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    # Проверяем, нажал ли пользователь "Назад"
    if update.message.text == get_message(language, 'bonus_back'):
        return await go_back(update, context)

    try:
        context.user_data['rooms'] = update.message.text
        context.user_data['current_state'] = BONUS_PROPERTY_TYPE  # Сохраняем текущее состояние
        await update.message.reply_text(get_message(language, 'bonus_select_property_type'), reply_markup=bonus_property_type_keyboard(language))
        return BONUS_FURNISH
    except Exception as e:
        logger.error(f"Error in bonus_property_type: {e}")
        return ConversationHandler.END
    


def bonus_property_type_keyboard(language):
    keyboard = [
        [KeyboardButton(get_message(language, 'bonus_flat')), KeyboardButton(get_message(language, 'bonus_house'))],
        [KeyboardButton(get_message(language, 'bonus_student_housing')), KeyboardButton(get_message(language, 'bonus_unknown'))],
        [KeyboardButton(get_message(language, 'bonus_back'))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)



async def bonus_furnish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Function bonus_furnish called")
    user_id = update.message.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    # Проверяем, нажал ли пользователь "Назад"
    if update.message.text == get_message(language, 'bonus_back'):
        return await go_back(update, context)

    try:
        context.user_data['property_type'] = update.message.text
        context.user_data['current_state'] = BONUS_FURNISH  # Сохраняем текущее состояние
        await update.message.reply_text(get_message(language, 'bonus_furnish_question'), reply_markup=bonus_furnish_keyboard(language))
        return BONUS_LIVING_TYPE
    except Exception as e:
        logger.error(f"Error in bonus_furnish: {e}")
        return ConversationHandler.END
    



def bonus_furnish_keyboard(language):
    keyboard = [
        [KeyboardButton(get_message(language, 'bonus_furnished')), KeyboardButton(get_message(language, 'bonus_unfurnished'))],
        [KeyboardButton(get_message(language, 'bonus_part_furnished'))],
        [KeyboardButton(get_message(language, 'bonus_unknown'))],
        [KeyboardButton(get_message(language, 'bonus_back'))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)



async def bonus_living_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Function bonus_living_type called")
    user_id = update.message.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    # Проверяем, нажал ли пользователь "Назад"
    if update.message.text == get_message(language, 'bonus_back'):
        logger.info(f"User {user_id} pressed Back, returning to BONUS_FURNISH state.")
        return await go_back(update, context)

    try:
        # Обработка ответа пользователя, если не было нажатия "Назад"
        context.user_data['furnish'] = update.message.text
        context.user_data['current_state'] = BONUS_LIVING_TYPE  # Сохранение текущего шага
        await update.message.reply_text(
            get_message(language, 'bonus_living_type_question'),
            reply_markup=bonus_living_type_keyboard(language)
        )
        return BONUS_SHOW_RESULTS
    except Exception as e:
        logger.error(f"Error in living_type: {e}")
        return ConversationHandler.END

def bonus_living_type_keyboard(language):
    keyboard = [
        [KeyboardButton(get_message(language, 'bonus_show_house_share')), KeyboardButton(get_message(language, 'bonus_dont_show_house_share'))],
        [KeyboardButton(get_message(language, 'bonus_back'))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    current_state = context.user_data.get('current_state')

    user_id = update.effective_user.id
    language = get_user_language(user_id)

    # Логируем текущее состояние
    logger.info(f"User {user_id} is going back from state: {current_state}")

    # Проверяем текущее состояние и возвращаем пользователя на соответствующий предыдущий шаг
    if current_state == BONUS_PRICE:
        context.user_data['current_state'] = BONUS_PRICE  # Обновляем состояние на BONUS_PRICE
        await update.message.reply_text(get_message(language, 'bonus_select_zone'), reply_markup=bonus_zone_keyboard(language))
        return BONUS_PRICE
    elif current_state == BONUS_ROOMS:
        context.user_data['current_state'] = BONUS_PRICE  # Обновляем состояние на BONUS_PRICE, так как это шаг до комнат
        await update.message.reply_text(get_message(language, 'property_enter_max_price'), reply_markup=back_keyboard(language))
        return BONUS_PRICE
    elif current_state == BONUS_PROPERTY_TYPE:
        context.user_data['current_state'] = BONUS_ROOMS  # Обновляем состояние на BONUS_ROOMS
        await update.message.reply_text(get_message(language, 'property_enter_room_count'), reply_markup=bonus_rooms_keyboard(language))
        return BONUS_ROOMS
    elif current_state == BONUS_FURNISH:
        context.user_data['current_state'] = BONUS_PROPERTY_TYPE  # Обновляем состояние на BONUS_PROPERTY_TYPE
        await update.message.reply_text(get_message(language, 'bonus_select_property_type'), reply_markup=bonus_property_type_keyboard(language))
        return BONUS_PROPERTY_TYPE
    elif current_state == BONUS_LIVING_TYPE:
        context.user_data['current_state'] = BONUS_FURNISH  # Обновляем состояние на BONUS_FURNISH
        await update.message.reply_text(get_message(language, 'bonus_furnish_question'), reply_markup=bonus_furnish_keyboard(language))
        return BONUS_FURNISH
    else:
        logger.error("Unexpected state, returning to main menu.")
        return await show_user_bonuses(update, context)

async def bonus_show_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Function bonus_show_results called")
    user_id = update.message.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    # Проверяем, вернулся ли пользователь назад, и если да, возвращаем его на предыдущий шаг
    if update.message.text == get_message(language, 'bonus_back'):
        return await go_back(update, context)

    try:
        if 'zone' not in context.user_data or 'price' not in context.user_data:
            logger.error("Context data missing for property search.")
            return await show_main_menu_with_error(update, context, get_message(language, 'bonus_no_results'))

        context.user_data['living_type'] = update.message.text
        location_identifier = context.user_data['zone']
        max_price = int(context.user_data['price'])
        min_price = 0

        # Преобразование текстовых значений для количества комнат в числовые
        rooms_value = context.user_data['rooms']
        if rooms_value == get_message(language, 'bonus_studio'):
            min_bedrooms = 0
            max_bedrooms = 0
        elif rooms_value == "1":
            min_bedrooms = 1
            max_bedrooms = 1
        elif rooms_value == "2":
            min_bedrooms = 2
            max_bedrooms = 2
        elif rooms_value == "3":
            min_bedrooms = 3
            max_bedrooms = 3
        elif rooms_value == "4+":
            min_bedrooms = 4
            max_bedrooms = None
        else:
            min_bedrooms = None
            max_bedrooms = None

        property_types = {
            get_message(language, 'bonus_flat'): "flat",
            get_message(language, 'bonus_house'): "detached",
            get_message(language, 'bonus_student_housing'): "private-halls"
        }
        property_type = property_types.get(context.user_data['property_type'], "flat")

        furnish_types = {
            get_message(language, 'bonus_furnished'): "furnished",
            get_message(language, 'bonus_unfurnished'): "unfurnished",
            get_message(language, 'bonus_part_furnished'): "part-furnished"
        }
        furnish_type = furnish_types.get(context.user_data['furnish'], "")

        dont_show = "houseShare" if context.user_data['living_type'] == get_message(language, 'bonus_dont_show_house_share') else ""

        url = (f"https://www.rightmove.co.uk/property-to-rent/find.html?"
               f"locationIdentifier={location_identifier}"
               f"&maxPrice={max_price}&minPrice={min_price}&propertyTypes={property_type}"
               f"&includeLetAgreed=false&furnishTypes={furnish_type}&dontShow={dont_show}")

        if min_bedrooms is not None:
            url += f"&minBedrooms={min_bedrooms}"

        if max_bedrooms is not None:
            url += f"&maxBedrooms={max_bedrooms}"

        logger.info(f"Generated URL: {url}")

        response = requests.get(url)
        response.raise_for_status()
        content = response.content.decode('utf-8')

        soup = BeautifulSoup(content, "html.parser")
        properties = soup.find_all("div", class_="l-searchResult is-list")

        if not properties:
            return await show_main_menu_with_error(update, context, get_message(language, 'bonus_no_results'))

        context.user_data['properties'] = properties
        context.user_data['current_index'] = 0

        return await bonus_show_property(update, context)
    except Exception as e:
        logger.error(f"Error in show_results: {e}")
        return ConversationHandler.END

async def show_main_menu_with_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: str) -> int:
    user_id = update.message.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    main_menu_button = [[KeyboardButton(get_message(language, 'bonus_main_menu'))]]
    reply_markup = ReplyKeyboardMarkup(main_menu_button, resize_keyboard=True)

    if update.message:
        await update.message.reply_text(error_message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(error_message, reply_markup=reply_markup)

    return ConversationHandler.END


async def back_to_bonuses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
        language = get_user_language(user_id)

        # Clear all property search-related context
        keys_to_remove = ['properties', 'current_index', 'zone', 'price', 'rooms', 'property_type', 'furnish', 'living_type']
        for key in keys_to_remove:
            context.user_data.pop(key, None)

        # Returning to bonuses menu
        return await show_user_bonuses(update, context)
    except Exception as e:
        logger.error(f"Error in back_to_bonuses: {e}")
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



async def back_to_order_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    if 'selected_order_id' not in context.user_data:
        await update.message.reply_text(
            get_message(language, 'orders_order_not_found'),
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(get_message(language, 'orders_back_to_orders'))]], resize_keyboard=True)
        )
        return ORDER  # Возвращаем пользователя к выбору заказа

    order_id = context.user_data['selected_order_id']
    orders = get_user_orders(user_id)
    order = orders.get(order_id)

    if not order:
        await update.message.reply_text(
            get_message(language, 'orders_order_not_found'),
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton(get_message(language, 'orders_back_to_orders'))]], resize_keyboard=True)
        )
        return ORDER  # Возвращаем пользователя к выбору заказа

    # Преобразование даты в нужный формат
    order_date = datetime.datetime.fromisoformat(order['date']).strftime("%d-%m-%Y %H:%M:%S")

    payment_method_map = {
        'cash': get_message(language, 'orders_payment_cash'),
        'PayMe': get_message(language, 'orders_payment_payme')
    }

    # Получение читаемого метода оплаты
    payment_method = payment_method_map.get(order.get('payment_method', 'not_specified'), get_message(language, 'orders_payment_not_specified'))
    payment_status = get_message(language, 'orders_paid') if order.get('paid', 0) == 1 else get_message(language, 'orders_not_paid')

    order_status_key = order["status"] if order["status"].startswith('order_status_') else f'order_status_{order["status"]}'
    order_status = get_message(language, order_status_key)  # Получаем перевод статуса

    # Формирование сообщения с экранированием символов для MarkdownV2
    message = get_message(
        language,
        'orders_details',
        order_id=escape_markdown_v2(str(order_id)),
        order_date=escape_markdown_v2(order_date),
        status=escape_markdown_v2(order_status),  # Используем переведенный статус
        payment_method=escape_markdown_v2(payment_method),
        payment_status=escape_markdown_v2(payment_status)
    )

    keyboard = [
        [KeyboardButton(get_message(language, 'orders_my_purchased_services')), KeyboardButton(get_message(language, 'orders_my_property_requests'))],
        [KeyboardButton(get_message(language, 'orders_my_bonuses')), KeyboardButton(get_message(language, 'orders_timeline'))],
        [KeyboardButton(get_message(language, 'orders_generate_share_link'))],  # Новая кнопка для таймлайна
        [KeyboardButton(get_message(language, 'orders_back_to_orders'))]
    ]
    
    await update.message.reply_text(
        message, 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True),
        parse_mode='MarkdownV2'
    )
    
    return NAVIGATE_ORDERS


async def bonus_navigate_results(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    # Ensure index only updates once per call
    current_index = context.user_data.get('current_index', 0)
    total_properties = len(context.user_data.get('properties', []))

    if query.data.startswith("back_to_bonuses"):
        await clear_previous_messages(context)
        return await back_to_bonuses(update, context)


    context.user_data['current_index'] = current_index
    return await bonus_show_property(update, context)




async def bonus_show_property(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Function bonus_show_property called")
    try:
        user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
        language = get_user_language(user_id)  # Получаем язык пользователя

        properties = context.user_data.get('properties', [])
        current_index = context.user_data.get('current_index', 0)

        if update.callback_query:
            await update.callback_query.answer()  # Отправляем пустой ответ сразу после нажатия кнопки
            query_data = update.callback_query.data
            if query_data == "next":
                current_index = (current_index + 1) % len(properties)
            elif query_data == "prev":
                current_index = (current_index - 1) % len(properties)
            elif query_data.startswith("bonus_like_"):
                logger.info(f"Button 'Лайкнуть' clicked, current index: {current_index}")
                order_id = context.user_data.get('selected_order_id')
                current_property = str(properties[current_index])  # Сохраняем весь HTML-код
                
                # Логирование перед вызовом функции
                logger.info(f"Saving like for user {user_id}, order {order_id}, property {current_property[:100]}...")

                # Сохранение лайка в базе данных
                add_bonus_like(user_id, order_id, current_property)

                # Отправляем сообщение в чат о том, что объект добавлен в лайки
                await update.callback_query.message.reply_text(get_message(language, 'bonus_property_liked'))

                return BONUS_NAVIGATE_RESULTS

            context.user_data['current_index'] = current_index

        # Проверка на наличие недвижимости
        if not properties:
            await update.message.reply_text(get_message(language, 'bonus_no_properties_found'))
            return ConversationHandler.END

        property = properties[current_index]
        title_element = property.find("h2", class_="propertyCard-title")
        price_element = property.find("span", class_="propertyCard-priceValue")
        address_element = property.find("address", class_="propertyCard-address")
        link_element = property.find("a", class_="propertyCard-link")
        image_element = property.find("img", class_="propertyCard-img")

        title = title_element.get_text(strip=True) if title_element else get_message(language, 'bonus_not_available')
        price = price_element.get_text(strip=True) if price_element else get_message(language, 'bonus_not_available')
        address = address_element.get_text(strip=True) if address_element else get_message(language, 'bonus_not_available')
        link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else get_message(language, 'bonus_not_available')
        image_url = image_element["src"] if image_element else None

        message = (f"{title}\n"
                   f"{get_message(language, 'bonus_price')}: {price}\n"
                   f"{get_message(language, 'bonus_address')}: {address}\n"
                   f"[{get_message(language, 'bonus_link')}]({link})\n\n"
                   f"{current_index + 1} {get_message(language, 'bonus_of')} {len(properties)}")

        keyboard = [
            [
                InlineKeyboardButton(get_message(language, 'bonus_prev'), callback_data="prev"),
                InlineKeyboardButton(get_message(language, 'bonus_next'), callback_data="next")
            ],
            [
                InlineKeyboardButton(get_message(language, 'bonus_like'), callback_data=f"bonus_like_{context.user_data['selected_order_id']}"),
                InlineKeyboardButton(get_message(language, 'bonus_add_to_order'), callback_data="add_to_order")
            ],
            [
                InlineKeyboardButton(get_message(language, 'bonus_back_to_bonuses'), callback_data="back_to_bonuses")
            ]
        ]

        if update.message:
            if image_url:
                await update.message.reply_photo(photo=image_url, caption=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            current_message = update.callback_query.message
            # Проверяем, нужно ли обновлять сообщение
            if current_message.caption != message or current_message.reply_markup != InlineKeyboardMarkup(keyboard):
                if current_message.photo:
                    await current_message.edit_media(
                        media=InputMediaPhoto(media=image_url, caption=message, parse_mode='Markdown'),
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await current_message.edit_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                logger.info("Message content and markup are the same, skipping edit.")

        return BONUS_NAVIGATE_RESULTS
    except Exception as e:
        logger.error(f"Error in bonus_show_property: {e}")
        return ConversationHandler.END



async def add_property_to_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    # Получаем ID заказа из context.user_data или другой логики
    selected_order_id = context.user_data.get('selected_order_id')

    if not selected_order_id:
        error_message = get_message(language, 'bonus_order_not_found')
        if update.message:
            await update.message.reply_text(error_message)
        else:
            await update.callback_query.message.reply_text(error_message)
        return BONUS_NAVIGATE_RESULTS

    # Получаем информацию о недвижимости
    if 'properties' in context.user_data:
        properties = context.user_data['properties']
        current_index = context.user_data['current_index']
    else:
        error_message = get_message(language, 'bonus_no_properties_available')
        if update.message:
            await update.message.reply_text(error_message)
        else:
            await update.callback_query.message.reply_text(error_message)
        return BONUS_NAVIGATE_RESULTS

    # Проверяем количество бонусов
    bonuses = get_user_bonuses(user_id)
    if bonuses <= 0:
        no_bonuses_message = get_message(language, 'bonus_no_bonuses_left')
        if update.message:
            await update.message.reply_text(no_bonuses_message)
        else:
            await update.callback_query.message.reply_text(no_bonuses_message)
        return BONUS_NAVIGATE_RESULTS

    current_property = properties[current_index]

    # Добавляем недвижимость в заказ
    add_property_to_order_db(selected_order_id, 'property', str(current_property), 'Ожидание ответа агента')

    # Списываем один бонус у пользователя
    decrement_user_bonuses(user_id)

    success_message = get_message(language, 'bonus_property_added')
    if update.message:
        await update.message.reply_text(success_message)
    else:
        await update.callback_query.message.reply_text(success_message)

    # Сохраняем состояние для возврата к бонусам
    return BONUS_NAVIGATE_RESULTS


async def back_to_bonuses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
        language = get_user_language(user_id)  # Получаем язык пользователя

        # Удаляем сообщение с результатами поиска недвижимости
        if update.callback_query:
            await update.callback_query.message.delete()

        # Очищаем только данные, связанные с поиском недвижимости, не трогая данные заказа
        keys_to_remove = ['properties', 'current_index', 'zone', 'price', 'rooms', 'property_type', 'furnish', 'living_type']
        for key in keys_to_remove:
            context.user_data.pop(key, None)

        # Возвращение к бонусам, сохраняем текущее состояние
        return await show_user_bonuses(update, context)
    except Exception as e:
        logger.error(f"Error in back_to_bonuses: {e}")
        return ConversationHandler.END


async def add_own_property_to_order_with_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        user_id = update.callback_query.from_user.id
        await update.callback_query.answer()
    else:
        user_id = update.message.from_user.id

    language = get_user_language(user_id)  # Получаем язык пользователя

    # Добавляем кнопку "Назад" для возврата к бонусам
    keyboard = [
        [KeyboardButton(get_message(language, 'bonus_back_to_bonuses'))]
    ]

    await update.message.reply_text(get_message(language, 'bonus_enter_property_link'), reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

    # Сохраните контекст, что бот ожидает ссылку
    context.user_data['waiting_for_property_link'] = True

    return LOAD_PROPERTY_LINK



async def back_to_bonuses_from_property_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    # Очищаем состояние ожидания ссылки
    context.user_data.pop('waiting_for_property_link', None)

    # Возвращаем пользователя к бонусам
    return await show_user_bonuses(update, context)

# Обработчик для загрузки ссылки на недвижимость
async def bonus_load_property_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя
    
    try:
        keyboard = [
            [KeyboardButton(get_message(language, 'bonus_back'))]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(get_message(language, 'bonus_enter_property_link'), reply_markup=reply_markup)
        return LOAD_PROPERTY_LINK
    except Exception as e:
        logging.error(f"Error in load_property_link: {e}")
        return ConversationHandler.END

# Обработчик для сохранения ссылки на недвижимость
async def bonus_save_property_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    if context.user_data.get('waiting_for_property_link', False):
        # Проверяем, нажал ли пользователь кнопку "Назад"
        if update.message.text == get_message(language, 'bonus_back_to_bonuses'):
            # Убираем состояние ожидания ссылки
            context.user_data.pop('waiting_for_property_link', None)
            # Возвращаем пользователя к бонусам
            return await back_to_bonuses(update, context)

        # Проверяем, является ли введенный текст ссылкой
        link = update.message.text.strip()
        if not link.startswith("http://") and not link.startswith("https://"):
            link = "https://" + link

        selected_order_id = context.user_data.get('selected_order_id')

        if selected_order_id:
            logger.info(f"Adding property to order: order_id={selected_order_id}, link={link}")
            add_property_to_order_db(selected_order_id, 'property', link, 'Ожидание ответа агента')

            # Списываем один бонус у пользователя
            decrement_user_bonuses(user_id)

            await update.message.reply_text(get_message(language, 'bonus_property_link_added'))
        else:
            await update.message.reply_text(get_message(language, 'bonus_order_not_found'))

        # Убираем состояние ожидания ссылки
        context.user_data.pop('waiting_for_property_link', None)

        return await show_main_menu(update, context)
    else:
        await update.message.reply_text(get_message(language, 'bonus_unexpected_link'))
        return ConversationHandler.END
    


async def show_bonus_likes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя
    order_id = context.user_data['selected_order_id']
    bonus_likes_key = f'bonus_likes_{user_id}_{order_id}'
    context.user_data[bonus_likes_key] = get_bonus_likes(user_id, order_id)

    if not context.user_data[bonus_likes_key]:
        keyboard = [
            [KeyboardButton(get_message(language, 'bonus_back'))]
        ]
        await update.message.reply_text(
            get_message(language, 'bonus_no_likes'),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return BONUS_LIKES  # Обратите внимание, что возвращаемся в состояние BONUS_LIKES

    context.user_data['bonus_likes_index'] = 0
    return await show_bonus_liked_property(update, context)


async def show_bonus_liked_property(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("show_bonus_liked_property called")
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя
    order_id = context.user_data['selected_order_id']
    bonus_likes_key = f'bonus_likes_{user_id}_{order_id}'
    likes = context.user_data.get(bonus_likes_key, [])
    current_index = context.user_data.get('bonus_likes_index', 0)
    total_properties = len(likes)

    if not likes:
        keyboard = [
            [InlineKeyboardButton(get_message(language, 'bonus_back_to_bonuses'), callback_data="back_to_bonuses")]
        ]
        await (update.message or update.callback_query.message).reply_text(
            get_message(language, 'bonus_no_likes'),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return BONUS_ACTIONS

    if update.callback_query:
        query_data = update.callback_query.data
        logger.info(f"Callback data received: {query_data}")

        if query_data == "next_bonus_like":
            current_index = (current_index + 1) % total_properties  # Обновляем индекс для следующего объекта
        elif query_data == "prev_bonus_like":
            current_index = (current_index - 1) % total_properties  # Обновляем индекс для предыдущего объекта

        context.user_data['bonus_likes_index'] = current_index  # Сохраняем обновленный индекс
        await update.callback_query.answer()

    current_property_html = likes[current_index]
    current_property = BeautifulSoup(current_property_html, "html.parser")

    title_element = current_property.find("h2", class_="propertyCard-title")
    price_element = current_property.find("span", class_="propertyCard-priceValue")
    address_element = current_property.find("address", class_="propertyCard-address")
    link_element = current_property.find("a", class_="propertyCard-link")
    image_element = current_property.find("img", class_="propertyCard-img")

    title = title_element.get_text(strip=True) if title_element else get_message(language, 'bonus_not_available')
    price = price_element.get_text(strip=True) if price_element else get_message(language, 'bonus_not_available')
    address = address_element.get_text(strip=True) if address_element else get_message(language, 'bonus_not_available')
    link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else get_message(language, 'bonus_not_available')
    image_url = image_element["src"] if image_element else None

    message = f"{title}\n{get_message(language, 'bonus_price')}: {price}\n{get_message(language, 'bonus_address')}: {address}\n[{get_message(language, 'bonus_link')}]({link})\n\n{current_index + 1} {get_message(language, 'bonus_of')} {total_properties}"

    keyboard = [
        [
            InlineKeyboardButton(get_message(language, 'bonus_prev'), callback_data="prev_bonus_like"),
            InlineKeyboardButton(get_message(language, 'bonus_next'), callback_data="next_bonus_like")
        ],
        [
            InlineKeyboardButton(get_message(language, 'bonus_add_to_order'), callback_data=f"add_to_order_{current_index}"),
            InlineKeyboardButton(get_message(language, 'bonus_delete_like'), callback_data=f"delete_bonus_like_{current_index}")
        ],
        [
            InlineKeyboardButton(get_message(language, 'bonus_back_to_bonuses'), callback_data="back_to_bonuses")
        ]
    ]

    try:
        if update.message:
            if image_url:
                await update.message.reply_photo(photo=image_url, caption=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            current_message = update.callback_query.message
            # Проверяем, нужно ли обновлять сообщение
            if current_message.caption != message or current_message.reply_markup != InlineKeyboardMarkup(keyboard):
                if current_message.photo:
                    await current_message.edit_media(
                        media=InputMediaPhoto(media=image_url, caption=message, parse_mode='Markdown'),
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await current_message.edit_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                logger.info("Message content and markup are the same, skipping edit.")

        return BONUS_LIKES
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        return ConversationHandler.END


async def add_property_to_order_from_likes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя
    index = int(query.data.split("_")[-1])

    likes_key = f'bonus_likes_{user_id}_{context.user_data["selected_order_id"]}'
    liked_properties = context.user_data.get(likes_key, [])

    if index < 0 or index >= len(liked_properties):
        await query.answer(get_message(language, 'bonus_invalid_index'))
        return BONUS_LIKES

    # Проверяем количество бонусов
    bonuses = get_user_bonuses(user_id)
    logger.info(f"Проверка бонусов: {bonuses} бонусов у пользователя {user_id}")
    if bonuses <= 0:
        await query.message.reply_text(get_message(language, 'bonus_no_bonuses_left'))
        await query.answer()  # Закрываем уведомление о нажатии кнопки
        return BONUS_LIKES

    selected_property = liked_properties[index]

    # Добавляем выбранную недвижимость в заказ
    add_property_to_order_db(context.user_data['selected_order_id'], 'property', selected_property, 'Ожидание ответа агента')

    # Уменьшаем количество бонусных баллов на 1
    decrement_user_bonuses(user_id)

    # Отправляем сообщение с подтверждением
    await query.message.reply_text(get_message(language, 'bonus_property_added_from_likes'))

    # Закрываем уведомление о нажатии кнопки
    await query.answer()

    return BONUS_LIKES  # Оставляем пользователя на том же этапе


async def delete_bonus_like(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя
    index = int(query.data.split("_")[-1])

    order_id = context.user_data['selected_order_id']
    likes_key = f'bonus_likes_{user_id}_{order_id}'
    liked_properties = context.user_data.get(likes_key, [])

    if index < 0 or index >= len(liked_properties):
        await query.answer(get_message(language, 'bonus_invalid_index'))
        return BONUS_LIKES

    # Получаем HTML объекта для удаления
    property_to_delete = liked_properties.pop(index)

    # Удаляем объект из базы данных
    remove_bonus_like(user_id, property_to_delete)

    # Обновляем сохраненные лайки в контексте
    context.user_data[likes_key] = liked_properties

    await query.answer(get_message(language, 'bonus_like_deleted'))

    # Если остались объекты, показываем следующий объект, иначе возвращаемся к бонусам
    if liked_properties:
        context.user_data['bonus_likes_index'] = 0  # Сбрасываем индекс
        return await show_bonus_liked_property(update, context)
    else:
        return await show_user_bonuses(update, context)




# Функция для клавиатуры с кнопкой "Назад"
def back_keyboard(language):
    return ReplyKeyboardMarkup([[KeyboardButton(get_message(language, 'bonus_back'))]], resize_keyboard=True, one_time_keyboard=True)




def translate_status(status, language):
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





async def show_ordered_properties(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order_id = context.user_data['selected_order_id']
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя
    orders = get_user_orders(user_id)
    properties = []

    for item in orders[order_id]['items']:
        if item[0] == 'property':
            status = item[2] if len(item) > 2 else get_message(language, 'orders_not_available')
            status_translated = translate_status(status, language)  # Переводим статус
            cloud_link = item[3] if len(item) > 3 else None
            reason = cloud_link if status == 'Просмотр отменен' else None  # Прямое сравнение со статусом из базы

            if item[1].startswith('http'):
                property_info = (f"{get_message(language, 'orders_user_added_property')}\n"
                                 f"🔗 [{get_message(language, 'orders_link')}]({item[1]})\n"
                                 f"🏷️ {get_message(language, 'orders_status')}: {escape_markdown_v2(status_translated)}")

                # Обработка различных статусов
                if status_translated == translate_status('Результат готов', language) and cloud_link:
                    report_label = get_report_label(language)  # Получаем перевод слова "Report"
                    property_info += f"\n📄 {report_label} : [Link for viewing]({escape_markdown_v2(cloud_link)})"

                elif status_translated == translate_status('Просмотр отменен', language) and reason:
                    property_info += f"\n🚫 {get_message(language, 'orders_cancellation_reason')}: {escape_markdown_v2(reason)}"

                elif status_translated == translate_status('Бронь забронирована', language) and cloud_link:
                    property_info += f"\n📅 {get_message(language, 'reservation_date_message')}: {escape_markdown_v2(cloud_link)}"

                properties.append(property_info)

            else:
                property_soup = BeautifulSoup(item[1], "html.parser")
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
                                 f"🔗 [{get_message(language, 'orders_link')}]({link})\n"
                                 f"🏷️ {get_message(language, 'orders_status')}: {escape_markdown_v2(status_translated)}")

                # Обработка различных статусов
                if status_translated == translate_status('Результат готов', language) and cloud_link:
                    report_label = get_report_label(language)  # Получаем перевод слова "Report"
                    property_info += f"\n📄 {report_label} : [Link for viewing]({escape_markdown_v2(cloud_link)})"

                elif status_translated == translate_status('Просмотр отменен', language) and reason:
                    property_info += f"\n🚫 {get_message(language, 'orders_cancellation_reason')}: {escape_markdown_v2(reason)}"

                elif status_translated == translate_status('Бронь забронирована', language) and cloud_link:
                    property_info += f"\n📅 {get_message(language, 'reservation_date_message')}: {escape_markdown_v2(cloud_link)}"

                properties.append(property_info)

    properties_text = "\n\n".join(properties) if properties else escape_markdown_v2(get_message(language, 'orders_no_properties'))

    keyboard = [[KeyboardButton(get_message(language, 'orders_back'))]]
    await update.message.reply_text(properties_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True), parse_mode='MarkdownV2')    
    return NAVIGATE_ORDERS



def get_report_label(language):
    """Возвращает перевод слова 'Report' в зависимости от языка пользователя"""
    if language == 'ru':
        return 'Отчет'
    elif language == 'uz':
        return 'Hisobot'
    else:
        return 'Report'



async def update_property_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    await show_ordered_properties(update, context)


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

async def show_ordered_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_id = update.effective_user.id
        language = get_user_language(user_id)
        logger.debug(f"User ID: {user_id}, Language: {language}")

        order_id = context.user_data.get('selected_order_id')
        if not order_id:
            logger.error("No selected_order_id found in user data.")
            await update.message.reply_text(get_message(language, 'orders_order_not_found'))
            return NAVIGATE_ORDERS

        orders = get_user_orders(user_id)
        logger.debug(f"Orders: {orders}")

        if not orders or order_id not in orders:
            logger.error(f"Order ID {order_id} not found in user's orders.")
            await update.message.reply_text(get_message(language, 'orders_order_not_found'))
            return NAVIGATE_ORDERS

        services = []
        status_emoji_map = {
            'completed': "✅",
            'in_progress': "🔄",
            'not_completed': "❌"
        }

        task_icons = {
            # Define specific icons for tasks if needed
        }

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

        keyboard = [[KeyboardButton(get_message(language, 'orders_back_to_details'))]]  
        await update.message.reply_text(services_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True), parse_mode='MarkdownV2')
        return NAVIGATE_ORDERS
    
    except Exception as e:
        logger.error(f"An error occurred in show_ordered_services: {str(e)}")
        await update.message.reply_text("An unexpected error occurred.")
        return NAVIGATE_ORDERS






async def back_to_orders_from_bonuses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Вызываем функцию, которая покажет заказы, возвращая к состоянию NAVIGATE_ORDERS
    return await back_to_order_details(update, context)



async def update_task_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def back_to_task_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

    await query.message.edit_text("Выберите статус задачи:", reply_markup=task_status_keyboard(order_id))
    return TASK  # Обновляем состояние


def task_status_keyboard(order_id):
    tasks = get_order_tasks(order_id)
    keyboard = []
    for task in tasks:
        keyboard.append([InlineKeyboardButton(f"{task['description']} - Выполнено", callback_data=f"update_task_{task['task_id']}_Выполнено")])
        keyboard.append([InlineKeyboardButton(f"{task['description']} - Выполняется", callback_data=f"update_task_{task['task_id']}_Выполняется")])
        keyboard.append([InlineKeyboardButton(f"{task['description']} - Не выполнено", callback_data=f"update_task_{task['task_id']}_Не_выполнено")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_task_status_{order_id}")])
    return InlineKeyboardMarkup(keyboard)


async def select_task_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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


async def back_to_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.message.delete()
    return await show_orders(update, context)
