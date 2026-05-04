
#bot/handlers/property_search.py

import base64
import sqlite3
from telegram import InputMediaPhoto, KeyboardButton, ReplyKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import requests
from bs4 import BeautifulSoup
import logging

from bot.handlers.language import get_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from bot.handlers.admin import ORDER_ACTIONS, TASKS, admin_panel_keyboard
from bot.utils.database import add_like, get_likes, add_to_cart_db, get_cart, clear_cart, get_user_id_by_order_id, get_user_language, get_user_profile, remove_item_from_cart_db, remove_like_from_db, update_order_status
from bot.utils.notifications import send_notification

from bot.handlers.common import show_main_menu  # Импортируем show_main_menu из common.py
from config import BOT_PAYME, BOT_TOKEN, PAYME_KEY, PAYME_MERCHANT_ID, PROVIDER_TOKEN

PRICE, ROOMS, PROPERTY_TYPE, FURNISH, LIVING_TYPE, SHOW_RESULTS, NAVIGATE_RESULTS = range(4, 11)
CONFIRM_REMOVE = range(23, 24)

# Замените правильные идентификаторы местоположения для каждого региона
def get_location_identifiers(language):
    return {
        get_message(language, 'zone_1'): "REGION%5E93817",
        get_message(language, 'zone_2'): "REGION%5E93814",
        get_message(language, 'zone_3'): "REGION%5E93883",
        get_message(language, 'zone_4'): "REGION%5E1420",
        get_message(language, 'zone_5'): "REGION%5E612",
        get_message(language, 'zone_6'): "REGION%5E1380",
        get_message(language, 'zone_unknown'): "REGION%5E82835"
    }

async def property_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Function property_search called")

    context.user_data['property_search_active'] = True  # Активируем флаг поиска недвижимости

    user_id = update.effective_user.id
    language = get_user_language(user_id)

    # Отправка сообщения о том, что поиск начался
    await update.message.reply_text(get_message(language, 'property_search_started'))

    if update.message.text == get_message(language, 'property_search_back_to_menu'):
        return await show_main_menu(update, context)

    try:
        # Отправка изображения с зонами проживания
        with open('images/zones.png', 'rb') as image_file:
            await update.message.reply_photo(photo=image_file)

        # Отправка вопроса о выборе зоны проживания
        await update.message.reply_text(get_message(language, 'property_choose_zone'), reply_markup=zone_keyboard(language))
        return PRICE
    except Exception as e:
        logger.error(f"Error in property_search: {e}")
        return ConversationHandler.END

def zone_keyboard(language):
    keyboard = [
        [KeyboardButton(get_message(language, 'zone_1')), KeyboardButton(get_message(language, 'zone_2'))],
        [KeyboardButton(get_message(language, 'zone_3')), KeyboardButton(get_message(language, 'zone_4'))],
        [KeyboardButton(get_message(language, 'zone_5')), KeyboardButton(get_message(language, 'zone_6'))],
        [KeyboardButton(get_message(language, 'zone_unknown'))],
        [KeyboardButton(get_message(language, 'property_search_back_to_menu'))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('property_search_active'):
        return ConversationHandler.END  # Завершаем, если поиск не активен

    context.user_data.setdefault('state_stack', []).append(PRICE)

    logger.info("Function price called")

    user_id = update.effective_user.id
    language = get_user_language(user_id)

    try:
        context.user_data['zone'] = get_location_identifiers(language).get(update.message.text, "REGION%5E82835")
        context.user_data['current_state'] = PRICE  # Сохранение текущего шага как предыдущего
        await update.message.reply_text(get_message(language, 'property_enter_max_price'), reply_markup=back_keyboard_property_search(language))
        return ROOMS
    except Exception as e:
        logger.error(f"Error in price: {e}")
        return ConversationHandler.END


async def rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('property_search_active'):
        return ConversationHandler.END  # Завершаем, если поиск не активен

    context.user_data.setdefault('state_stack', []).append(ROOMS)

    logger.info("Function rooms called")

    user_id = update.effective_user.id
    language = get_user_language(user_id)

    try:
        context.user_data['price'] = update.message.text
        context.user_data['current_state'] = ROOMS  # Сохранение текущего шага как предыдущего
        await update.message.reply_text(get_message(language, 'property_enter_room_count'), reply_markup=rooms_keyboard(language))
        return PROPERTY_TYPE
    except Exception as e:
        logger.error(f"Error in rooms: {e}")
        return ConversationHandler.END


def rooms_keyboard(language):
    keyboard = [
        [KeyboardButton(get_message(language, 'studio')), KeyboardButton(get_message(language, 'rooms_1'))],
        [KeyboardButton(get_message(language, 'rooms_2')), KeyboardButton(get_message(language, 'rooms_3'))],
        [KeyboardButton(get_message(language, 'rooms_4_plus'))],
        [KeyboardButton(get_message(language, 'go_back'))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

async def property_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('property_search_active'):
        return ConversationHandler.END  # Завершаем, если поиск не активен

    context.user_data.setdefault('state_stack', []).append(PROPERTY_TYPE)

    logger.info("Function property_type called")

    user_id = update.effective_user.id
    language = get_user_language(user_id)

    try:
        context.user_data['rooms'] = update.message.text
        context.user_data['current_state'] = PROPERTY_TYPE  # Сохранение текущего шага как предыдущего
        await update.message.reply_text(get_message(language, 'property_choose_property_type'), reply_markup=property_type_keyboard(language))
        return FURNISH
    except Exception as e:
        logger.error(f"Error in property_type: {e}")
        return ConversationHandler.END

def property_type_keyboard(language):
    keyboard = [
        [KeyboardButton(get_message(language, 'property_type_flat')), KeyboardButton(get_message(language, 'property_type_house'))],
        [KeyboardButton(get_message(language, 'property_type_private_halls')), KeyboardButton(get_message(language, 'zone_unknown'))],
        [KeyboardButton(get_message(language, 'go_back'))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


async def furnish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('property_search_active'):
        return ConversationHandler.END  # Завершаем, если поиск не активен

    context.user_data.setdefault('state_stack', []).append(FURNISH)

    logger.info("Function furnish called")

    user_id = update.effective_user.id
    language = get_user_language(user_id)

    try:
        context.user_data['property_type'] = update.message.text
        context.user_data['current_state'] = FURNISH  # Сохранение текущего шага
        await update.message.reply_text(get_message(language, 'property_should_furnished'), reply_markup=furnish_keyboard(language))
        return LIVING_TYPE
    except Exception as e:
        logger.error(f"Error in furnish: {e}")
        return ConversationHandler.END
    
def furnish_keyboard(language):
    keyboard = [
        [KeyboardButton(get_message(language, 'furnished')), KeyboardButton(get_message(language, 'unfurnished'))],
        [KeyboardButton(get_message(language, 'part_furnished'))],
        [KeyboardButton(get_message(language, 'go_back'))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


async def living_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get('property_search_active'):
        return ConversationHandler.END  # Завершаем, если поиск не активен

    context.user_data.setdefault('state_stack', []).append(LIVING_TYPE)

    logger.info("Function living_type called")

    user_id = update.effective_user.id
    language = get_user_language(user_id)

    try:
        context.user_data['furnish'] = update.message.text
        context.user_data['current_state'] = LIVING_TYPE  # Сохранение текущего шага как предыдущего
        await update.message.reply_text(get_message(language, 'property_house_share_option'), reply_markup=living_type_keyboard(language))
        return SHOW_RESULTS
    except Exception as e:
        logger.error(f"Error in living_type: {e}")
        return ConversationHandler.END

def living_type_keyboard(language):
    keyboard = [
        [KeyboardButton(get_message(language, 'house_share_yes')), KeyboardButton(get_message(language, 'house_share_no'))],
        [KeyboardButton(get_message(language, 'go_back'))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def back_keyboard_property_search(language):
    return ReplyKeyboardMarkup([[KeyboardButton(get_message(language, 'go_back'))]], resize_keyboard=True, one_time_keyboard=True)


async def go_back_property_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Проверяем, есть ли история состояний в контексте пользователя
    if 'state_stack' not in context.user_data:
        context.user_data['state_stack'] = []

    # Если есть хотя бы одно состояние в стеке, возвращаемся к предыдущему состоянию
    if context.user_data['state_stack']:
        previous_state = context.user_data['state_stack'].pop()
    else:
        previous_state = None

    user_id = update.effective_user.id
    language = get_user_language(user_id)

    if previous_state == PRICE:
        context.user_data['current_state'] = PRICE
        await update.message.reply_text(get_message(language, 'property_choose_zone'), reply_markup=zone_keyboard(language))
        return PRICE
    elif previous_state == ROOMS:
        context.user_data['current_state'] = ROOMS
        await update.message.reply_text(get_message(language, 'property_enter_max_price'), reply_markup=back_keyboard_property_search(language))
        return ROOMS
    elif previous_state == PROPERTY_TYPE:
        context.user_data['current_state'] = PROPERTY_TYPE
        await update.message.reply_text(get_message(language, 'property_enter_room_count'), reply_markup=rooms_keyboard(language))
        return PROPERTY_TYPE
    elif previous_state == FURNISH:
        context.user_data['current_state'] = FURNISH
        await update.message.reply_text(get_message(language, 'property_choose_property_type'), reply_markup=property_type_keyboard(language))
        return FURNISH
    elif previous_state == LIVING_TYPE:
        context.user_data['current_state'] = LIVING_TYPE
        await update.message.reply_text(get_message(language, 'property_should_furnished'), reply_markup=furnish_keyboard(language))
        return LIVING_TYPE
    else:
        logger.error("Unexpected state, returning to main menu.")
        return await show_main_menu(update, context)


async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Function show_results called")

    user_id = update.effective_user.id
    language = get_user_language(user_id)

    if update.message.text == get_message(language, 'go_back'):
        return await go_back_property_search(update, context)

    try:
        if 'zone' not in context.user_data or 'price' not in context.user_data:
            logger.error("Context data missing for property search.")
            return await show_main_menu_with_error(update, context, get_message(language, 'property_results_not_found'))

        context.user_data['living_type'] = update.message.text
        location_identifier = context.user_data['zone']
        max_price = int(context.user_data['price'])
        min_price = 0

        # Преобразование текстовых значений для количества комнат в числовые
        rooms_value = context.user_data['rooms']
        if rooms_value == get_message(language, 'studio'):
            min_bedrooms = 0
            max_bedrooms = 0
        elif rooms_value == get_message(language, 'rooms_1'):
            min_bedrooms = 1
            max_bedrooms = 1
        elif rooms_value == get_message(language, 'rooms_2'):
            min_bedrooms = 2
            max_bedrooms = 2
        elif rooms_value == get_message(language, 'rooms_3'):
            min_bedrooms = 3
            max_bedrooms = 3
        elif rooms_value == get_message(language, 'rooms_4_plus'):
            min_bedrooms = 4
            max_bedrooms = None
        else:
            min_bedrooms = None
            max_bedrooms = None

        property_types = {
            get_message(language, 'property_type_flat'): "flat",
            get_message(language, 'property_type_house'): "detached",
            get_message(language, 'property_type_private_halls'): "private-halls"
        }
        property_type = property_types.get(context.user_data['property_type'], "flat")

        furnish_types = {
            get_message(language, 'furnished'): "furnished",
            get_message(language, 'unfurnished'): "unfurnished",
            get_message(language, 'part_furnished'): "part-furnished"
        }
        furnish_type = furnish_types.get(context.user_data['furnish'], "")

        dont_show = "houseShare" if context.user_data['living_type'] == get_message(language, 'house_share_no') else ""

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
            return await show_main_menu_with_error(update, context, get_message(language, 'property_results_not_found'))

        context.user_data['properties'] = properties
        context.user_data['current_index'] = 0

        return await show_property(update, context)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error in show_results: {e}")
        return await show_main_menu_with_error(update, context, get_message(language, 'property_results_not_found'))
    except Exception as e:
        logger.error(f"Error in show_results: {e}")
        return await show_main_menu_with_error(update, context, get_message(language, 'property_results_not_found'))


async def show_main_menu_with_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error_message: str) -> int:
    main_menu_button = [[KeyboardButton("Главное меню")]]
    reply_markup = ReplyKeyboardMarkup(main_menu_button, resize_keyboard=True)

    if update.message:
        await update.message.reply_text(error_message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(error_message, reply_markup=reply_markup)

    return ConversationHandler.END

async def show_property(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_id = update.effective_user.id
        language = get_user_language(user_id)
        
        properties = context.user_data.get('properties', [])
        current_index = context.user_data.get('current_index', 0)
        total_properties = len(properties)

        if not properties:
            no_properties_message = get_message(language, 'property_results_not_found')
            if update.message:
                await update.message.reply_text(no_properties_message)
            else:
                await update.callback_query.message.reply_text(no_properties_message)
            return ConversationHandler.END

        property = properties[current_index]

        title_element = property.find("h2", class_="propertyCard-title")
        price_element = property.find("span", class_="propertyCard-priceValue")
        address_element = property.find("address", class_="propertyCard-address")
        link_element = property.find("a", class_="propertyCard-link")
        image_element = property.find("img", class_="propertyCard-img")

        title = title_element.get_text(strip=True) if title_element else "N/A"
        price = price_element.get_text(strip=True) if price_element else "N/A"
        address = address_element.get_text(strip=True) if address_element else "N/A"
        link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else "N/A"
        image_url = image_element["src"] if image_element else None

        message = (f"{get_message(language, 'property_property')}: {title}\n"
                   f"{get_message(language, 'property_price')}: {price}\n"
                   f"{get_message(language, 'property_address')}: {address}\n"
                   f"[{get_message(language, 'property_link')}]({link})\n\n"
                   f"{current_index + 1} {get_message(language, 'property_out_of')} {total_properties}")

        keyboard = [
            [
                InlineKeyboardButton(get_message(language, 'property_search_go_back'), callback_data="prev"),
                InlineKeyboardButton(get_message(language, 'property_search_next'), callback_data="next")
            ],
            [
                InlineKeyboardButton(get_message(language, 'property_search_like'), callback_data="like"),
                InlineKeyboardButton(get_message(language, 'property_search_add_to_cart'), callback_data="cart")
            ],
            [
                InlineKeyboardButton(get_message(language, 'property_search_back_to_menu'), callback_data="back_to_menu")
            ]
        ]

        try:
            if update.message:
                if image_url:
                    await update.message.reply_photo(photo=image_url, caption=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
                else:
                    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                if image_url:
                    await update.callback_query.message.edit_media(
                        media=InputMediaPhoto(media=image_url, caption=message, parse_mode='Markdown'),
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    if update.callback_query.message.text != message:
                        await update.callback_query.message.edit_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to edit message in show_property: {e}")
            return ConversationHandler.END

        return NAVIGATE_RESULTS
    except Exception as e:
        logger.error(f"Error in show_property: {e}")
        return ConversationHandler.END



# Define ADMIN_IDS here or import from config
ADMIN_IDS = [3461866]

from bot.utils.database import add_like, get_likes

async def like_property(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    language = get_user_language(user_id)

    current_property = context.user_data['properties'][context.user_data['current_index']]

    add_like(user_id, str(current_property))

    like_message = get_message(language, 'property_added_to_likes')
    await query.answer()
    await query.message.reply_text(like_message)

from bot.utils.database import add_to_cart_db, get_cart, clear_cart, remove_item_from_cart_db

async def add_property_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    language = get_user_language(user_id)

    if 'properties' in context.user_data:
        properties = context.user_data['properties']
        current_index = context.user_data['current_index']
    else:
        likes_key = f'likes_{user_id}'
        properties = context.user_data.get(likes_key, [])
        current_index = context.user_data.get('likes_index', 0)

    if not properties:
        no_properties_message = get_message(language, 'property_no_properties_in_cart')
        await query.answer(no_properties_message)
        return NAVIGATE_RESULTS

    if current_index < 0 or current_index >= len(properties):
        error_message = get_message(language, 'property_results_not_found')
        await query.answer(error_message)
        return NAVIGATE_RESULTS

    current_property = properties[current_index]

    item_type = 'property'
    await add_to_cart_db(user_id, item_type, str(current_property))

    if 'cart_items' not in context.user_data:
        context.user_data['cart_items'] = []
    context.user_data['cart_items'].append(current_property)

    cart_message = get_message(language, 'property_added_to_cart')
    await query.answer(cart_message)
    await query.message.reply_text(cart_message)

    return NAVIGATE_RESULTS


async def show_likes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя

    if 'likes_index' in context.user_data:
        context.user_data.pop('likes_index')
        await update.message.delete() if update.message else await update.callback_query.message.delete()
        return await show_likes(update, context)

    context.user_data[f'likes_{user_id}'] = get_likes(user_id)

    if not context.user_data[f'likes_{user_id}']:
        empty_likes_message = get_message(language, 'property_likes_empty')
        await update.message.reply_text(empty_likes_message)
        return ConversationHandler.END

    context.user_data['likes_index'] = 0
    return await show_liked_property(update, context)




async def show_liked_property(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    language = get_user_language(user_id)  # Получаем язык пользователя
    likes_key = f'likes_{user_id}'
    likes = context.user_data.get(likes_key, [])
    current_index = context.user_data.get('likes_index', 0)
    total_properties = len(likes)

    if not likes:
        no_likes_message = get_message(language, 'property_likes_empty')
        await (update.message or update.callback_query.message).reply_text(no_likes_message)
        return ConversationHandler.END

    current_property_html = likes[current_index]
    current_property = BeautifulSoup(current_property_html, "html.parser")

    title_element = current_property.find("h2", class_="propertyCard-title")
    price_element = current_property.find("span", class_="propertyCard-priceValue")
    address_element = current_property.find("address", class_="propertyCard-address")
    link_element = current_property.find("a", class_="propertyCard-link")
    image_element = current_property.find("img", class_="propertyCard-img")

    title = title_element.get_text(strip=True) if title_element else "N/A"
    price = price_element.get_text(strip=True) if price_element else "N/A"
    address = address_element.get_text(strip=True) if address_element else "N/A"
    link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else "N/A"
    image_url = image_element["src"] if image_element else None

    message = get_message(language, 'bonus_show_property', title=title, price=price, address=address, link=link, current_index=current_index + 1, total_properties=total_properties)

    keyboard = [
        [
            InlineKeyboardButton(get_message(language, 'property_search_go_back'), callback_data="prev_like"),
            InlineKeyboardButton(get_message(language, 'property_search_next'), callback_data="next_like")
        ],
        [
            InlineKeyboardButton(get_message(language, 'property_search_add_to_cart'), callback_data=f"add_cart_{current_index}"),
            InlineKeyboardButton(get_message(language, 'property_search_delete'), callback_data=f"remove_like_{current_index}")
        ],
        [
            InlineKeyboardButton(get_message(language, 'property_search_back_to_menu'), callback_data="back_to_menu")
        ]
    ]

    try:
        if update.message:
            if image_url:
                await update.message.reply_photo(photo=image_url, caption=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            if image_url:
                await update.callback_query.message.edit_media(
                    media=InputMediaPhoto(media=image_url, caption=message, parse_mode='Markdown'),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.callback_query.message.edit_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception as e:
        print(f"Failed to edit message: {e}")
        return ConversationHandler.END

    return NAVIGATE_RESULTS


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    language = get_user_language(user_id)
    cart_items = await get_cart(user_id)

    if not cart_items:
        empty_cart_message = get_message(language, 'cart_is_empty')
        if update.callback_query:
            await update.callback_query.message.edit_text(empty_cart_message)
        else:
            await update.message.reply_text(empty_cart_message)
        return ConversationHandler.END

    basket_text = f"*{get_message(language, 'cart_title')}*"
    total_price = 0
    property_count = 0
    package_price = 0
    individual_services_price = 0
    package_name = ""
    has_meet_package = False
    has_housing_package = False
    individual_services = []
    properties = []
    package_items = []

    property_counter = 1
    package_counter = 1
    individual_service_counter = 1

    for item in cart_items:
        item_status = item.get('status', get_message(language, 'unknown_status'))

        if item['item_type'] == 'property':
            property_count += 1
            if item['item'].startswith('http'):
                properties.append(
                    f"{property_counter}. 🏠 {get_message(language, 'user_added_property')}\n"
                    f"({get_message(language, 'property_view')})\n"
                    f"[{get_message(language, 'property_link')}]({item['item']})"
                )
            else:
                property_soup = BeautifulSoup(item['item'], "html.parser")
                title_element = property_soup.find("h2", class_="propertyCard-title")
                price_element = property_soup.find("span", class_="propertyCard-priceValue")
                address_element = property_soup.find("address", class_="propertyCard-address")
                link_element = property_soup.find("a", class_="propertyCard-link")

                title = title_element.get_text(strip=True) if title_element else "N/A"
                price = price_element.get_text(strip=True) if price_element else "N/A"
                address = address_element.get_text(strip=True) if address_element else "N/A"
                link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else "N/A"

                property_text = (
                    f"{property_counter}. 🏡 {title} ({get_message(language, 'property_view')})\n"
                    f"    {get_message(language, 'property_price')}: {price}\n"
                    f"    {get_message(language, 'property_address')}: {address}\n"
                    f"    [{get_message(language, 'property_link')}]({link})"
                )
                properties.append(property_text)
            property_counter += 1

        elif item['item_type'] == 'service':
            service_data = item['item']
            service_key = service_data['key']
            service_title = get_message(language, service_key)
            service_price_str = service_data['price']
            service_details = "\n".join([f"- {get_message(language, detail_key)}" for detail_key in service_data['details']])

            extracted_price = extract_dollar_amount(service_price_str)

            if service_key == 'package_meet_me':
                has_meet_package = True
                package_price += extracted_price  # Добавляем к общей цене пакетов
                package_name = get_message(language, 'package_meet_me')
                package_items.append(
                    f"{package_counter}. {service_title}\n{service_price_str}\n{service_details}"
                )
            elif service_key == 'package_housing' or service_key == 'premium_package':
                package_price += extracted_price  # Добавляем к общей цене пакетов
                if service_key == 'package_housing':
                    has_housing_package = True
                package_name = get_message(language, service_key)
                package_items.append(
                    f"{package_counter}. {service_title}\n{service_price_str}\n{service_details}"
                )
            package_counter += 1

        elif item['item_type'] == 'individual_service':
            service_data = item['item']
            service_title = get_message(language, service_data['key'])
            individual_services.append(f"{individual_service_counter}. {service_title}")

            # Извлечение цены в долларах
            price_start = service_data['price'].find('($') + 2
            price_end = service_data['price'].find(')', price_start)
            if price_start != -1 and price_end != -1:
                price_str = service_data['price'][price_start:price_end].replace(',', '')
                try:
                    service_price = float(price_str)
                    individual_services_price += service_price
                except ValueError:
                    pass
            individual_service_counter += 1

    # Сначала добавляем раздел с недвижимостью
    basket_text += f"\n{get_message(language, 'property_section_title')}\n\n"
    basket_text += "\n\n".join(properties) if properties else get_message(language, 'no_properties_in_cart')

    # Затем добавляем раздел с пакетными услугами
    basket_text += f"\n\n*{get_message(language, 'package_services')}:*\n\n"
    basket_text += "\n\n".join(package_items) if package_items else get_message(language, 'no_packages')

    # И наконец, раздел с индивидуальными услугами
    basket_text += f"\n\n{get_message(language, 'individual_services_section_title')}\n\n"
    basket_text += "\n\n".join(individual_services) if individual_services else get_message(language, 'no_individual_services')

    if has_housing_package:
        extra_properties = max(0, property_count - 3)
        extra_price = extra_properties * 50
        if extra_properties > 0:
            property_text_summary = get_message(
                language, 
                'property_summary_with_extra', 
                property_count=property_count, 
                extra_properties=extra_properties
            )
        else:
            property_text_summary = get_message(
                language, 
                'property_summary_without_extra', 
                property_count=property_count
            )
    else:
        extra_properties = 0
        extra_price = property_count * 50
        property_text_summary = get_message(
            language, 
            'property_summary_no_package', 
            property_count=property_count, 
            price=extra_price
        )

    total_price = package_price + individual_services_price + extra_price

    basket_text += f"\n\n*{get_message(language, 'total_price', total_price=int(total_price))}*"
    if property_text_summary:
        basket_text += f"\n{property_text_summary}"

    keyboard = []
    for item in cart_items:
        item_status = item.get('status', get_message(language, 'unknown_status'))
        if item['item_type'] == 'property':
            if item['item'].startswith('http'):
                delete_button_text = get_message(language, 'delete_property_button', title=item['item'])
                keyboard.append([
                    InlineKeyboardButton(delete_button_text, callback_data=f"remove_cart_{item['id']}")
                ])
            else:
                property_soup = BeautifulSoup(item['item'], "html.parser")
                title_element = property_soup.find("h2", class_="propertyCard-title")
                title = title_element.get_text(strip=True) if title_element else "N/A"
                delete_button_text = get_message(language, 'delete_property_button', title=title)
                keyboard.append([
                    InlineKeyboardButton(delete_button_text, callback_data=f"remove_cart_{item['id']}")
                ])
        elif item['item_type'] == 'service':
            service_data = item['item']
            service_title = get_message(language, service_data['key'])
            delete_button_text = get_message(language, 'delete_package_button', service_title=service_title)
            keyboard.append([
                InlineKeyboardButton(delete_button_text, callback_data=f"remove_cart_{item['id']}")
            ])
        elif item['item_type'] == 'individual_service':
            service_title = get_message(language, item['item']['key'])
            delete_button_text = get_message(language, 'delete_individual_service_button', service_title=service_title)
            keyboard.append([
                InlineKeyboardButton(delete_button_text, callback_data=f"remove_cart_{item['id']}")
            ])
    keyboard.append([
        InlineKeyboardButton(f"{get_message(language, 'place_order_button')}", callback_data="place_order")
    ])

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(
                basket_text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode='Markdown'
            )
        except Exception as e:
            await update.callback_query.message.reply_text(
                basket_text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            basket_text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='Markdown'
        )

    # Добавить кнопку главного меню
    main_menu_button = [[KeyboardButton(get_message(language, 'main_menu_button_text'))]]
    reply_markup = ReplyKeyboardMarkup(main_menu_button, resize_keyboard=True)

    if update.message:
        await update.message.reply_text(get_message(language, 'back_to_main_menu'), reply_markup=reply_markup)
    
    return NAVIGATE_RESULTS


async def navigate_results(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    user_id = update.effective_user.id
    language = get_user_language(user_id)  # Определяем язык пользователя

    await query.answer()

    if query.data.startswith("remove_like_"):
        index = int(query.data.split("_")[-1])
        likes_key = f'likes_{user_id}'
        likes = context.user_data.get(likes_key, [])

        if 0 <= index < len(likes):
            item_to_remove = likes.pop(index)
            remove_like_from_db(user_id, item_to_remove)  # Удаление из БД

            if likes:
                context.user_data[likes_key] = likes
                context.user_data['likes_index'] = 0
                return await show_liked_property(update, context)
            else:
                await query.message.edit_text(get_message(language, 'property_likes_empty'))
                return ConversationHandler.END
        else:
            await query.answer(get_message(language, 'property_error_invalid_index'))
            return await show_liked_property(update, context)

    elif query.data.startswith("remove_cart_"):
        item_id = int(query.data.split("_")[-1])
        cart_items = await get_cart(user_id)
        item_to_remove = next((item for item in cart_items if item['id'] == item_id), None)

        if item_to_remove:
            context.user_data['item_to_remove'] = item_to_remove

            item_html = item_to_remove['item']
            item_type = item_to_remove.get('item_type', '')

            if item_type == 'property':
                item_soup = BeautifulSoup(item_html, "html.parser")
                title_element = item_soup.find("h2", class_="propertyCard-title")
                price_element = item_soup.find("span", class_="propertyCard-priceValue")
                address_element = item_soup.find("address", class_="propertyCard-address")
                link_element = item_soup.find("a", class_="propertyCard-link")

                if title_element:
                    title = title_element.get_text(strip=True)
                    price = price_element.get_text(strip=True) if price_element else "N/A"
                    address = address_element.get_text(strip=True) if address_element else "N/A"
                    link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else "N/A"
                    
                    # Здесь изменен порядок и формат текста
                    message = (
                        f"{get_message(language, 'property_remove_cart_question')}\n\n"
                        f"🏡 {title} ({get_message(language, 'property_view')})\n"
                        f"     {get_message(language, 'property_price')}: {price}\n"
                        f"     {get_message(language, 'property_address')}: {address}\n"
                        f"     [{get_message(language, 'property_link')}]({link})\n\n"
                        f"{get_message(language, 'property_remove_cart_footer')}\n"
                    )
                else:
                    message = (
                        f"{get_message(language, 'property_remove_cart_question')}\n\n"
                        f"🏠 {get_message(language, 'user_added_property')}\n"
                        f" [{get_message(language, 'property_link')}]({item_to_remove['item']})\n\n"
                        f"{get_message(language, 'property_remove_cart_footer')}\n"

                    )
            elif item_type == 'service':
                # Формирование сообщения для пакета услуг
                service_title = get_message(language, item_to_remove['item']['key'])
                message = (
                    f"{get_message(language, 'property_remove_cart_question')}\n\n"
                    f"{service_title}\n\n"
                    f"{get_message(language, 'property_remove_cart_footer')}\n"
                )
            elif item_type == 'individual_service':
                # Формирование сообщения для индивидуальной услуги
                service_title = get_message(language, item_to_remove['item']['key'])
                message = (
                    f"{get_message(language, 'property_remove_cart_question')}\n\n"
                    f"{service_title}\n\n"
                    f"{get_message(language, 'property_remove_cart_footer')}\n"
                )

            keyboard = [
                [InlineKeyboardButton(get_message(language, 'property_confirm_remove'), callback_data=f"confirm_remove_{item_id}")],
                [InlineKeyboardButton(get_message(language, 'property_cancel_remove'), callback_data="cancel_remove")]
            ]
            await query.message.edit_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return CONFIRM_REMOVE

        else:
            await query.answer(get_message(language, 'property_error_remove_item_failed'))
            return await show_cart(update, context)

    elif query.data.startswith("confirm_remove_"):
        item_id = int(query.data.split("_")[-1])
        cart_items = await get_cart(user_id)
        item_to_remove = next((item for item in cart_items if item['id'] == item_id), None)

        if item_to_remove:
            remove_item_from_cart_db(user_id, item_id)  # Удаление из базы данных
            cart_items = [item for item in cart_items if item['id'] != item_id]
            context.user_data['cart_items'] = cart_items

            if cart_items:
                return await show_cart(update, context)
            else:
                await query.message.edit_text(get_message(language, 'cart_is_empty'))
                return ConversationHandler.END
        else:
            await query.answer(get_message(language, 'property_error_remove_item_failed'))
            return await show_cart(update, context)

    elif query.data == "cancel_remove":
        await query.answer(get_message(language, 'property_remove_cancelled'))
        return await show_cart(update, context)

    elif query.data.startswith("add_cart_"):
        index = int(query.data.split("_")[-1])
        item = context.user_data[f'likes_{user_id}'][index]
        if f'cart_{user_id}' not in context.user_data:
            context.user_data[f'cart_{user_id}'] = []
        context.user_data[f'cart_{user_id}'].append(item)
        add_to_cart_db(user_id, 'property', str(item))  # Добавление в БД
        await query.message.reply_text(get_message(language, 'property_add_to_cart_success'))
        return NAVIGATE_RESULTS

    elif query.data == "place_order":
        return await confirm_order(update, context)
    
    elif query.data == "next":
        context.user_data['current_index'] = (context.user_data['current_index'] + 1) % len(context.user_data['properties'])
    elif query.data == "prev":
        context.user_data['current_index'] = (context.user_data['current_index'] - 1) % len(context.user_data['properties'])
    
    elif query.data == "back_to_menu":
        await clear_previous_messages(context)
        await show_main_menu(update, context)
        return ConversationHandler.END
    
    elif query.data == "next_like":
        context.user_data['likes_index'] = (context.user_data['likes_index'] + 1) % len(context.user_data[f'likes_{user_id}'])
        return await show_liked_property(update, context)
    
    elif query.data == "prev_like":
        context.user_data['likes_index'] = (context.user_data['likes_index'] - 1) % len(context.user_data[f'likes_{user_id}'])
        return await show_liked_property(update, context)
    
    elif query.data == "next_cart":
        context.user_data['cart_index'] = (context.user_data['cart_index'] + 1) % len(context.user_data[f'cart_{user_id}'])
        return await show_cart_property(update, context)
    
    elif query.data == "prev_cart":
        context.user_data['cart_index'] = (context.user_data['cart_index'] - 1) % len(context.user_data[f'cart_{user_id}'])
        return await show_cart_property(update, context)

    return await show_property(update, context)
# -1002216078572


async def clear_previous_messages(context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'message_ids' in context.user_data:
        for message_id in context.user_data['message_ids']:
            try:
                await context.bot.delete_message(chat_id=context.user_data['chat_id'], message_id=message_id)
            except Exception as e:
                print(f"Failed to delete message {message_id}: {e}")
        context.user_data['message_ids'] = []



async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    language = get_user_language(user_id)
    user_profile = get_user_profile(user_id)
    cart_items = await get_cart(user_id)

    if not cart_items:
        await query.message.reply_text(get_message(language, 'cart_is_empty'))
        return ConversationHandler.END

    property_items = []
    package_items = []
    individual_services = []
    property_count = 0
    total_price = 0
    package_price = 0
    individual_services_price = 0
    has_housing_package = False
    extra_properties = 0

    for item in cart_items:
        if item['item_type'] == 'property':
            property_count += 1
            if item['item'].startswith('http'):
                property_items.append(
                    f"🏠 {get_message(language, 'user_added_property')}\n"
                    f"({get_message(language, 'property_view')})\n"
                    f"[{get_message(language, 'property_link')}]({item['item']})"
                )
            else:
                property_soup = BeautifulSoup(item['item'], "html.parser")
                title_element = property_soup.find("h2", class_="propertyCard-title")
                price_element = property_soup.find("span", class_="propertyCard-priceValue")
                address_element = property_soup.find("address", class_="propertyCard-address")
                link_element = property_soup.find("a", class_="propertyCard-link")

                title = title_element.get_text(strip=True) if title_element else "N/A"
                price = price_element.get_text(strip=True) if price_element else "N/A"
                address = address_element.get_text(strip=True) if address_element else "N/A"
                link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else "N/A"

                property_items.append(
                    f"🏡 {title} ({get_message(language, 'property_view')})\n"
                    f"  {get_message(language, 'property_price')}: {price}\n"
                    f" {get_message(language, 'property_address')}: {address}\n"
                    f"[{get_message(language, 'property_link')}]({link})"
                )

        elif item['item_type'] == 'service':
            service_data = item['item']
            service_key = service_data['key']
            service_title = get_message(language, service_key)
            service_price = service_data['price']
            service_details = "\n".join([f"- {get_message(language, detail_key)}" for detail_key in service_data['details']])

            if service_key == 'package_meet_me':
                extracted_price = extract_dollar_amount(service_price)
                package_price += extracted_price
                package_items.append(f"📦 {service_title}\n{service_price}\n{service_details}")
            elif service_key == 'package_housing' or service_key == 'premium_package':
                extracted_price = extract_dollar_amount(service_price)
                package_price += extracted_price
                if service_key == 'package_housing':
                    has_housing_package = True
                package_items.append(f"📦 {service_title}\n{service_price}\n{service_details}")

        elif item['item_type'] == 'individual_service':
            service_data = item['item']
            service_title = get_message(language, service_data['key'])
            individual_services.append(f"{service_title}")

            # Извлечение цены в долларах
            price_start = service_data['price'].find('($') + 2
            price_end = service_data['price'].find(')', price_start)
            if price_start != -1 and price_end != -1:
                price_str = service_data['price'][price_start:price_end].replace(',', '')
                try:
                    service_price = float(price_str)
                    individual_services_price += service_price
                except ValueError:
                    pass

    # Расчёт дополнительных свойств и их стоимости
    extra_properties = max(0, property_count - 3) if has_housing_package else property_count
    extra_price = extra_properties * 50
    total_price = package_price + individual_services_price + extra_price

    property_text = "\n\n".join(property_items) if property_items else get_message(language, 'no_properties')
    package_text = "\n\n".join(package_items) if package_items else get_message(language, 'no_packages')
    individual_services_text = "\n\n".join(individual_services) if individual_services else get_message(language, 'no_individual_services')

    message = (
        f"{get_message(language, 'confirm_check_info')}: \n\n"
        f"{get_message(language, 'confirm_all_correct')}? \n\n"
        f"👤 {get_message(language, 'profile_name')}: {user_profile['name']}\n"
        f"📞 {get_message(language, 'profile_phone')}: {user_profile['phone']}\n"
        f"📧 Email: {user_profile['email']}\n\n"
        f"{get_message(language, 'ordered_items')}:\n\n"
        f"{get_message(language, 'property_section_title')}\n\n"
        f"{property_text}\n\n"
        f"*{get_message(language, 'package_services')}:*\n\n"
        f"{package_text}\n\n"
        f"{get_message(language, 'individual_services_section_title')}\n\n"
        f"{individual_services_text}\n\n"
        f"{get_message(language, 'total_price', total_price=int(total_price))}\n"
    )

    if has_housing_package:
        if extra_properties > 0:
            message += get_message(language, 'property_summary_with_extra', property_count=property_count, extra_properties=extra_properties) + "\n\n"
        else:
            message += get_message(language, 'property_summary_without_extra', property_count=property_count) + "\n\n"
    else:
        message += get_message(language, 'property_summary_no_package', property_count=property_count, price=extra_price) + "\n\n"

    message += f"{get_message(language, 'confirm_agreement')}\n\n"

    keyboard = [
        [InlineKeyboardButton(get_message(language, 'confirm_order_yes'), callback_data="confirm_order_yes")],
        [InlineKeyboardButton(get_message(language, 'confirm_order_no'), callback_data="confirm_order_no")]
    ]

    await query.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return NAVIGATE_RESULTS


# Функция обработки ответа "Нет"
async def confirm_order_no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await show_cart(update, context)
    return NAVIGATE_RESULTS


import re

def extract_dollar_amount(price_str):
    """
    Извлекает сумму в долларах из строки цены.
    Например, из "£114 ($150)" извлекает 150.
    """
    match = re.search(r'\$\d+', price_str)
    if match:
        return float(match.group()[1:])  # Убираем знак $
    else:
        return 0.0  # Или обработать ошибку иначе
    
    
# Функция обработки ответа "Да"
async def confirm_order_yes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    language = get_user_language(user_id)
    cart_items = await get_cart(user_id)
    user_profile = get_user_profile(user_id)

    if not cart_items:
        await query.message.reply_text(get_message(language, 'cart_is_empty'))
        return ConversationHandler.END

    # Переменные для подсчёта
    property_items = []
    package_items = []
    individual_services = []
    property_count = 0
    total_price = 0
    package_price = 0
    individual_services_price = 0
    has_housing_package = False

    for item in cart_items:
        if item['item_type'] == 'property':
            property_count += 1
            # Парсинг деталей недвижимости
            if item['item'].startswith('http'):
                property_items.append(f"🏠 {get_message(language, 'user_added_property')} ({get_message(language, 'property_view')})\n [{get_message(language, 'property_link')}]({item['item']})")
            else:
                property_soup = BeautifulSoup(item['item'], "html.parser")
                title_element = property_soup.find("h2", class_="propertyCard-title")
                price_element = property_soup.find("span", class_="propertyCard-priceValue")
                address_element = property_soup.find("address", class_="propertyCard-address")
                link_element = property_soup.find("a", class_="propertyCard-link")

                title = title_element.get_text(strip=True) if title_element else "N/A"
                price = price_element.get_text(strip=True) if price_element else "N/A"
                address = address_element.get_text(strip=True) if address_element else "N/A"
                link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else "N/A"

                property_items.append(f"🏡 {title} ({get_message(language, 'property_view')})\n {get_message(language, 'property_price')}: {price}\n {get_message(language, 'property_address')}: {address}\n [{get_message(language, 'property_link')}]({link})")

        elif item['item_type'] == 'service':
            service_data = item['item']
            service_key = service_data['key']
            service_title = get_message(language, service_data['key'])
            service_price = service_data['price']
            service_details = "\n".join([f"- {get_message(language, detail_key)}" for detail_key in service_data['details']])

            if service_key == 'package_meet_me':
                package_price = extract_dollar_amount(service_price)  # Извлечение 150
                package_items.append(f"📦 {service_title}\n{service_price}\n{service_details}")
            elif service_key == 'package_housing' or service_key == 'premium_package':
                package_price = extract_dollar_amount(service_price)  # Извлечение 450 или 850
                has_housing_package = True
                package_items.append(f"📦 {service_title}\n{service_price}\n{service_details}")

        elif item['item_type'] == 'individual_service':
            service_data = item['item']
            service_title = get_message(language, service_data['key'])
            individual_services.append(f"{service_title}")

            # Извлечение цены в долларах
            price_start = service_data['price'].find('($') + 2
            price_end = service_data['price'].find(')', price_start)
            if price_start != -1 and price_end != -1:
                price_str = service_data['price'][price_start:price_end].replace(',', '')
                try:
                    service_price = float(price_str)
                    individual_services_price += service_price
                except ValueError:
                    pass

    # Расчёт дополнительных свойств и их стоимости
    extra_properties = max(0, property_count - 3) if has_housing_package else property_count
    extra_price = extra_properties * 50
    total_price = package_price + individual_services_price + extra_price

    # Конвертация суммы в сомы
    total_price_in_sums = convert_to_sums(total_price)

    # Создание кнопок для выбора метода оплаты
    keyboard = [
        [InlineKeyboardButton(get_message(language, 'payme_button', total_price_in_sums=total_price_in_sums), callback_data="confirm_payment")],
        [InlineKeyboardButton(get_message(language, 'cash_payment_button'), callback_data="pay_later")]
    ]

    await query.message.reply_text(
        get_message(language, 'payment_instructions', total_price=int(total_price)),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

    context.user_data['total_price_in_dollars'] = total_price
    context.user_data['cart_items'] = cart_items

    return NAVIGATE_RESULTS


def convert_to_sums(dollar_amount):
    exchange_rate = 12650  # Примерный курс обмена сумм за 1 доллар
    sums = dollar_amount * exchange_rate
    return int(sums)


def generate_payme_url(merchant_id, order_id, amount_in_sums, return_url):
    amount_in_tiyins = int(amount_in_sums * 100)  # Correct conversion to tyiyns
    logging.info(f"Amount in tyiyns: {amount_in_tiyins}")  # Debug logging
    
    params = f"m={merchant_id};ac.order_id={order_id};a={amount_in_tiyins};c={return_url};ct=3000;cr=860"
    encoded_params = base64.urlsafe_b64encode(params.encode()).decode()
    
    logging.info(f"Generated Payme URL: https://checkout.paycom.uz/{encoded_params}")  # Debug logging
    return f"https://checkout.paycom.uz/{encoded_params}"

async def handle_return_from_payment(update: Update, context: CallbackContext) -> int:
    query = update.message.text
    if query == '/start order_confirmed':
        order_id = context.user_data.get('order_id')
        if order_id:
            update_order_status(order_id, 'Оплачено')
            await update.message.reply_text(f"Спасибо за оплату! Ваш заказ #{order_id} подтвержден.")

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    order_id = context.user_data.get('order_id')

    if order_id:
        update_order_status(order_id, "Отменен")
        await query.message.reply_text(f"Ваш заказ #{order_id} был отменен.")
    return await show_main_menu(update, context)



async def handle_payment_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    logger.info(f"Payment choice callback received: {query.data}")
    user_id = query.from_user.id
    language = get_user_language(user_id)  # Определяем язык пользователя
    cart_items = context.user_data.get('cart_items', [])
    total_price_in_dollars = context.user_data.get('total_price_in_dollars', 0)

    if query.data == "pay_later":
        # Создание заказа с оплатой наличными (paid=False)
        order_id = create_order(user_id, cart_items, payment_method="cash", paid=False, amount=total_price_in_dollars)

        if order_id is None:
            logger.error(f"Failed to create order for user_id={user_id}.")
            await query.message.reply_text(get_message(language, 'order_creation_error'))
            return NAVIGATE_RESULTS

        user_profile = get_user_profile(user_id)
        property_items, package_items, individual_services = [], [], []
        property_count = 0

        for item in cart_items:
            if item['item_type'] == 'property':
                property_count += 1
                if item['item'].startswith('http'):
                    property_items.append(f"🏠 {get_message(language, 'user_added_property')} ({get_message(language, 'property_view')})\n   [{get_message(language, 'property_link')}]({item['item']})")
                else:
                    property_soup = BeautifulSoup(item['item'], "html.parser")
                    title_element = property_soup.find("h2", class_="propertyCard-title")
                    price_element = property_soup.find("span", class_="propertyCard-priceValue")
                    address_element = property_soup.find("address", class_="propertyCard-address")
                    link_element = property_soup.find("a", class_="propertyCard-link")

                    title = title_element.get_text(strip=True) if title_element else "N/A"
                    price = price_element.get_text(strip=True) if price_element else "N/A"
                    address = address_element.get_text(strip=True) if address_element else "N/A"
                    link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else "N/A"

                    property_items.append(f"🏡 {title}\n     {get_message(language, 'property_price')}: {price}\n     {get_message(language, 'property_address')}: {address}\n     [{get_message(language, 'property_link')}]({link})")
            elif item['item_type'] == 'service':
                service_data = item['item']
                service_title = get_message(language, service_data['key'])
                service_details = "\n".join([f"- {get_message(language, detail_key)}" for detail_key in service_data['details']])
                package_items.append(f" 📦 {service_title}\n{service_details}")
            elif item['item_type'] == 'individual_service':
                service_data = item['item']
                service_title = get_message(language, service_data['key'])
                individual_services.append(f"{service_title}")

        property_text = "\n\n".join(property_items) if property_items else get_message(language, 'no_properties')
        package_text = "\n\n".join(package_items) if package_items else get_message(language, 'no_packages')
        individual_services_text = "\n\n".join(individual_services) if individual_services else get_message(language, 'no_individual_services')

        message = (
            f"📄 *{get_message(language, 'order_details')}*\n\n"
            f"🆔 {get_message(language, 'order_number')}: #{order_id}\n\n"
            f"👤 {get_message(language, 'profile_name')}: {user_profile['name']}\n"
            f"📞 {get_message(language, 'profile_phone')}: {user_profile['phone']}\n"
            f"📧 Email: {user_profile['email']}\n\n"
            f"{get_message(language, 'ordered_items')}:\n\n"
            f"{get_message(language, 'property_section_title')}\n\n{property_text}\n\n"
            f"*{get_message(language, 'package_services')}:*\n\n{package_text}\n\n"
            f"{get_message(language, 'individual_services_section_title')}\n\n{individual_services_text}\n\n"
            f"💵 *{get_message(language, 'payment_method')}: {get_message(language, 'cash_payment')}*\n"
            f"*{get_message(language, 'total_price', total_price=int(total_price_in_dollars))}*\n\n"
        )

        await query.message.reply_text(message, parse_mode='Markdown')

        # Уведомление администраторов о новом заказе
        group_chat_id = -1002216078572  # Укажите ID вашей группы
        user_language = language  # Используем переменную language, которая определяет язык пользователя
        language_label = get_message(user_language, 'language_label')  # Добавляем метку языка

        admin_message = (
            f"Новый заказ от пользователя:\n\n"
            f"🆔 Номер заказа: #{order_id}\n\n"
            f"👤 Имя: {user_profile['name']}\n"
            f"📞 Телефон: {user_profile['phone']}\n"
            f"📧 Email: {user_profile['email']}\n\n"
            f"Заказанные объекты:\n\n{property_text}\n\n"
            f"Пакетные услуги:\n\n{package_text}\n\n"
            f"🛠️ Индивидуальные услуги:\n\n{individual_services_text}\n\n"
            f"💵 Оплата: Наличные\n"
            f"💰 Сумма заказа: {total_price_in_dollars}$\n\n"
            f"🌐 Язык пользователя: {language_label}"
        )

        keyboard = [
            [InlineKeyboardButton("Принят", callback_data=f"update_status_{order_id}_Принят")],
            [InlineKeyboardButton("Возврат", callback_data=f"update_status_{order_id}_Возврат"),
             InlineKeyboardButton("Отменен", callback_data=f"update_status_{order_id}_Отменен")],
            [InlineKeyboardButton("Ожидание", callback_data=f"update_status_{order_id}_Ожидание")],
            [InlineKeyboardButton("Ожидание оплаты", callback_data=f"update_status_{order_id}_Ожидание оплаты")],
            [InlineKeyboardButton("Выполняется", callback_data=f"update_status_{order_id}_Выполняется")],
            [InlineKeyboardButton("Выполнен", callback_data=f"update_status_{order_id}_Выполнен")]
        ]

        await context.bot.send_message(chat_id=group_chat_id, text=admin_message, reply_markup=InlineKeyboardMarkup(keyboard))

        clear_cart(user_id)

        return await show_main_menu(update, context)


    elif query.data == "confirm_payment":
        total_price_in_dollars = context.user_data.get('total_price_in_dollars', 0)
        language = get_user_language(user_id)
        user_profile = get_user_profile(user_id)
        cart_items = context.user_data.get('cart_items', [])

        # Создание заказа с оплатой через PayMe (paid=False, amount=total_price_in_dollars)
        order_id = create_order(user_id, cart_items, payment_method="PayMe", paid=False, amount=total_price_in_dollars)

        if order_id is None:
            logger.error(f"Failed to create order for user_id={user_id}.")
            await query.message.reply_text(get_message(language, 'order_creation_error'))
            return NAVIGATE_RESULTS

        # Здесь ваш код для формирования деталей заказа
        property_items, package_items, individual_services = [], [], []
        property_count = 0

        for item in cart_items:
            if item['item_type'] == 'property':
                property_count += 1
                if item['item'].startswith('http'):
                    property_items.append(f"🏠 {get_message(language, 'user_added_property')} ({get_message(language, 'property_view')})\n   [{get_message(language, 'property_link')}]({item['item']})")
                else:
                    property_soup = BeautifulSoup(item['item'], "html.parser")
                    title_element = property_soup.find("h2", class_="propertyCard-title")
                    price_element = property_soup.find("span", class_="propertyCard-priceValue")
                    address_element = property_soup.find("address", class_="propertyCard-address")
                    link_element = property_soup.find("a", class_="propertyCard-link")

                    title = title_element.get_text(strip=True) if title_element else "N/A"
                    price = price_element.get_text(strip=True) if price_element else "N/A"
                    address = address_element.get_text(strip=True) if address_element else "N/A"
                    link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else "N/A"

                    property_items.append(f"🏡 {title}\n     {get_message(language, 'property_price')}: {price}\n     {get_message(language, 'property_address')}: {address}\n     [{get_message(language, 'property_link')}]({link})")
            elif item['item_type'] == 'service':
                service_data = item['item']
                service_title = get_message(language, service_data['key'])
                service_details = "\n".join([f"- {get_message(language, detail_key)}" for detail_key in service_data['details']])
                package_items.append(f" 📦 {service_title}\n{service_details}")
            elif item['item_type'] == 'individual_service':
                service_data = item['item']
                service_title = get_message(language, service_data['key'])
                individual_services.append(f"{service_title}")

        property_text = "\n\n".join(property_items) if property_items else get_message(language, 'no_properties')
        package_text = "\n\n".join(package_items) if package_items else get_message(language, 'no_packages')
        individual_services_text = "\n\n".join(individual_services) if individual_services else get_message(language, 'no_individual_services')

        message = (
            f"📄 *{get_message(language, 'order_details')}*\n\n"
            f"🆔 {get_message(language, 'order_number')}: #{order_id}\n\n"
            f"👤 {get_message(language, 'profile_name')}: {user_profile['name']}\n"
            f"📞 {get_message(language, 'profile_phone')}: {user_profile['phone']}\n"
            f"📧 Email: {user_profile['email']}\n\n"
            f"{get_message(language, 'ordered_items')}:\n\n"
            f"{get_message(language, 'property_section_title')}\n\n{property_text}\n\n"
            f"*{get_message(language, 'package_services')}:*\n\n{package_text}\n\n"
            f"{get_message(language, 'individual_services_section_title')}\n\n{individual_services_text}\n\n"
            f"💵 *{get_message(language, 'payment_method')}: {get_message(language, 'payme_payment')}*\n"
            f"*{get_message(language, 'total_price', total_price=int(total_price_in_dollars))}*\n\n"
        )

        await query.message.reply_text(message, parse_mode='Markdown')

        # Подготовка суммы в тийинах (1 сум = 100 тийинов)
        exchange_rate = 12650  # Текущий курс доллара к суму
        total_price_in_sums = total_price_in_dollars * exchange_rate
        amount_in_tiyins = int(total_price_in_sums * 100)

        # Настройка запроса к PayMe API
        payme_api_url = "https://checkout.paycom.uz/api"
        headers = {
            "X-Auth": f"{PAYME_MERCHANT_ID}:{PAYME_KEY}",  # Замените на ваши учетные данные
            "Content-Type": "application/json"
        }

        payload = {
            "id": 1,
            "method": "receipts.create",
            "params": {
                "amount": amount_in_tiyins,
                "account": {
                    "order_id": str(order_id)
                }
            }
        }

        try:
            response = requests.post(payme_api_url, json=payload, headers=headers)
            response_data = response.json()

            # Проверка ответа на наличие ошибок
            if response.status_code == 200 and "result" in response_data:
                receipt_id = response_data["result"]["receipt"]["_id"]
                # Генерация ссылки для оплаты на PayMe
                payme_link = f"https://checkout.payme.uz/{receipt_id}"

                # Сохраняем receipt_id для дальнейшего использования (если необходимо)
                context.user_data['receipt_id'] = receipt_id

                # Вставляем информацию о транзакции в базу данных
                create_time = int(time.time() * 1000)  # Текущее время в миллисекундах
                state = 0  # Чек создан, ожидается оплата
                perform_time = None  # Платеж еще не выполнен

                # Вызов функции для создания транзакции в базе данных
                create_transaction_in_db(
                    transaction_id=receipt_id,
                    order_id=order_id,
                    amount=amount_in_tiyins,
                    create_time=create_time,
                    state=state,
                    perform_time=perform_time
                )

                # Формируем сообщение для пользователя
                if language == 'ru':
                    payment_message = f"Пожалуйста, перейдите по следующей ссылке, чтобы оплатить ваш заказ: {payme_link}"
                elif language == 'en':
                    payment_message = f"Please follow this link to pay for your order: {payme_link}"
                elif language == 'uz':
                    payment_message = f"Iltimos, buyurtmangizni to'lash uchun ushbu havolaga o'ting: {payme_link}"
                else:
                    payment_message = f"Please follow this link to pay for your order: {payme_link}"
                await query.message.reply_text(payment_message)

                # Сообщаем пользователю, что он получит уведомление после оплаты
                if language == 'ru':
                    pending_message = "После оплаты вы получите уведомление."
                elif language == 'en':
                    pending_message = "After payment, you will receive a notification."
                elif language == 'uz':
                    pending_message = "To'lovdan so'ng sizga xabar yuboriladi."
                else:
                    pending_message = "After payment, you will receive a notification."
                await query.message.reply_text(pending_message)
            else:
                logger.error(f"Error in PayMe API response: {response_data}")
                if language == 'ru':
                    error_message = "Ошибка при создании заказа. Пожалуйста, попробуйте снова."
                elif language == 'en':
                    error_message = "Error creating order. Please try again."
                elif language == 'uz':
                    error_message = "Buyurtma yaratishda xatolik. Iltimos, qayta urinib ko'ring."
                else:
                    error_message = "Error creating order. Please try again."
                await query.message.reply_text(error_message)

        except Exception as e:
            logger.error(f"Error creating PayMe receipt: {e}")
            if language == 'ru':
                error_message = "Ошибка при создании заказа. Пожалуйста, попробуйте снова."
            elif language == 'en':
                error_message = "Error creating order. Please try again."
            elif language == 'uz':
                error_message = "Buyurtma yaratishda xatolik. Iltimos, qayta urinib ko'ring."
            else:
                error_message = "Error creating order. Please try again."
            await query.message.reply_text(error_message)

        # Сохраняем идентификатор заказа для дальнейшего использования
        context.user_data['order_id'] = order_id

        # Отправляем уведомление администраторам
        group_chat_id = -1002216078572  # Замените на ID вашей группы
        language_label = get_message(language, 'language_label')

        admin_message = (
            f"Новый заказ от пользователя:\n\n"
            f"🆔 Номер заказа: #{order_id}\n\n"
            f"👤 Имя: {user_profile['name']}\n"
            f"📞 Телефон: {user_profile['phone']}\n"
            f"📧 Email: {user_profile['email']}\n\n"
            f"Заказанные объекты:\n\n{property_text}\n\n"
            f"Пакетные услуги:\n\n{package_text}\n\n"
            f"🛠️ Индивидуальные услуги:\n\n{individual_services_text}\n\n"
            f"💵 Оплата: PayMe\n"
            f"💰 Сумма заказа: {total_price_in_dollars}$\n\n"
            f"🌐 Язык пользователя: {language_label}"
        )

        keyboard = [
            [InlineKeyboardButton("Принят", callback_data=f"update_status_{order_id}_Принят")],
            [InlineKeyboardButton("Возврат", callback_data=f"update_status_{order_id}_Возврат"),
            InlineKeyboardButton("Отменен", callback_data=f"update_status_{order_id}_Отменен")],
            [InlineKeyboardButton("Ожидание", callback_data=f"update_status_{order_id}_Ожидание")],
            [InlineKeyboardButton("Ожидание оплаты", callback_data=f"update_status_{order_id}_Ожидание оплаты")],
            [InlineKeyboardButton("Выполняется", callback_data=f"update_status_{order_id}_Выполняется")],
            [InlineKeyboardButton("Выполнен", callback_data=f"update_status_{order_id}_Выполнен")]
        ]

        await context.bot.send_message(chat_id=group_chat_id, text=admin_message, reply_markup=InlineKeyboardMarkup(keyboard))

        # Очищаем корзину пользователя
        clear_cart(user_id)

        return NAVIGATE_RESULTS
    

def create_transaction_in_db(transaction_id, order_id, amount, create_time, state, perform_time):
    # Подключаемся к базе данных
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    # Вставляем новую запись в таблицу transactions
    cursor.execute("""
        INSERT INTO transactions (transaction_id, order_id, amount, create_time, state, perform_time)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (transaction_id, order_id, amount, create_time, state, perform_time))
    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

import requests

def check_perform_transaction(amount_in_tiyins, order_id):
    url = "https://checkout.paycom.uz/api"
    headers = {
        "X-Auth": f"{PAYME_MERCHANT_ID}:{PAYME_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "id": 2,  # Уникальный ID запроса
        "method": "CheckPerformTransaction",
        "params": {
            "amount": amount_in_tiyins,
            "account": {
                "order_id": str(order_id)
            }
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Использование функции
amount_in_tiyins = 100000  # Пример суммы в тийинах
order_id = 123456  # Пример номера заказа
response = check_perform_transaction(amount_in_tiyins, order_id)
print(response)



import time

def create_transaction(transaction_id, amount_in_tiyins, order_id):
    url = "https://checkout.paycom.uz/api"
    headers = {
        "X-Auth": f"{PAYME_MERCHANT_ID}:{PAYME_KEY}",
        "Content-Type": "application/json"
    }
    current_time = int(time.time() * 1000)  # Текущие время в миллисекундах
    payload = {
        "id": 3,  # Уникальный ID запроса
        "method": "CreateTransaction",
        "params": {
            "id": transaction_id,
            "time": current_time,
            "amount": amount_in_tiyins,
            "account": {
                "order_id": str(order_id)
            }
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Использование функции
transaction_id = "some_unique_transaction_id"  # Генерируем уникальный идентификатор транзакции
response = create_transaction(transaction_id, amount_in_tiyins, order_id)
print(response)


def perform_transaction(transaction_id):
    url = "https://checkout.paycom.uz/api"
    headers = {
        "X-Auth": f"{PAYME_MERCHANT_ID}:{PAYME_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "id": 4,  # Уникальный ID запроса
        "method": "PerformTransaction",
        "params": {
            "id": transaction_id
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Использование функции
response = perform_transaction(transaction_id)
print(response)


async def precheckout_callback(update: Update, context: CallbackContext):
    query = update.pre_checkout_query
    user_id = query.from_user.id
    language = get_user_language(user_id)  # Определяем язык пользователя

    # Проверяем данные payload, чтобы убедиться, что это наш заказ
    if query.invoice_payload.startswith("order_id_"):
        await query.answer(ok=True)  # Подтверждаем pre-checkout
    else:
        error_message = get_message(language, 'precheckout_error')  # Получаем сообщение об ошибке на нужном языке
        await query.answer(ok=False, error_message=error_message)

async def successful_payment_callback(update: Update, context: CallbackContext):
    try:
        payment = update.message.successful_payment

        # Получение ID заказа из payload
        order_id = int(payment.invoice_payload.split("_")[2])

        # Обновление статуса заказа в базе данных на "Оплачено" и установка paid = 1
        update_order_status(order_id, "Оплачено", paid=1)

        # Очищаем корзину пользователя после успешной оплаты
        user_id = update.message.from_user.id
        language = get_user_language(user_id)  # Определяем язык пользователя
        clear_cart(user_id)

        success_message = get_message(language, 'payment_successful').format(order_id=order_id)
        await update.message.reply_text(success_message)
    except Exception as e:
        logging.error(f"Error in successful_payment_callback: {e}")
        error_message = get_message(language, 'payment_error')
        await update.message.reply_text(error_message)

from bot.utils.database import get_order_tasks, update_task_status


async def update_order_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data.split("_")
    order_id = int(data[2])
    status = data[3]

    update_order_status(order_id, status)

    user_id = get_user_id_by_order_id(order_id)
    language = get_user_language(user_id)  # Определяем язык пользователя

    # Определяем сообщение в зависимости от статуса и языка
    if status == "Принят":
        status_message = get_message(language, 'order_accepted', order_id=order_id)
    elif status == "Возврат":
        status_message = get_message(language, 'order_returned', order_id=order_id)
    elif status == "Отменен":
        status_message = get_message(language, 'order_canceled', order_id=order_id)
    elif status == "Ожидание":
        status_message = get_message(language, 'order_pending', order_id=order_id)
    elif status == "Ожидание оплаты":
        status_message = get_message(language, 'order_payment_pending', order_id=order_id)
    elif status == "Выполняется":
        status_message = get_message(language, 'order_in_progress', order_id=order_id)
    elif status == "Выполнен":
        status_message = get_message(language, 'order_completed', order_id=order_id)

    await context.bot.send_message(chat_id=user_id, text=status_message, parse_mode='Markdown')
    await show_order_admin_menu(update, context, order_id)  # Передаем order_id в аргументе



async def show_order_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int) -> None:
    query = update.callback_query

    keyboard = [
        [InlineKeyboardButton("Принят", callback_data=f"update_status_{order_id}_Принят")],
        [InlineKeyboardButton("Возврат", callback_data=f"update_status_{order_id}_Возврат"),
        InlineKeyboardButton("Отменен", callback_data=f"update_status_{order_id}_Отменен")],
        [InlineKeyboardButton("Ожидание", callback_data=f"update_status_{order_id}_Ожидание")],
        [InlineKeyboardButton("Ожидание оплаты", callback_data=f"update_status_{order_id}_Ожидание оплаты")],
        [InlineKeyboardButton("Выполняется", callback_data=f"update_status_{order_id}_Выполняется")],
        [InlineKeyboardButton("Выполнен", callback_data=f"update_status_{order_id}_Выполнен")]
    ]

    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


async def show_order_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order_id = context.user_data['order_id']
    tasks = get_order_tasks(order_id)

    if not tasks:
        await update.message.reply_text(f"Для заказа {order_id} нет задач.", reply_markup=admin_panel_keyboard())
        return ORDER_ACTIONS

    message = f"Задачи для заказа {order_id}:\n\n"
    for task in tasks:
        message += f"{task['task_id']}. {task['task_description']} - {task['status']}\n"

    keyboard = []
    for task in tasks:
        keyboard.append([KeyboardButton(f"{task['task_id']} - {task['task_description']}")])
    keyboard.append([KeyboardButton("Назад")])

    await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return TASKS




    
async def set_task_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data.split('_')
    if len(data) < 4:
        await query.answer("Неверный формат данных.")
        return

    task_id = int(data[2])
    status = data[3]

    update_task_status(task_id, status)

    await query.answer(f"Статус задачи обновлен на '{status}'")
    await show_order_tasks(update, context)  # Обновите задачи, чтобы отобразить новые статусы


from bot.utils.database import create_order, get_all_orders, clear_cart

async def place_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.callback_query.from_user.id
    cart_items = await get_cart(user_id)

    if not cart_items:
        await update.callback_query.message.reply_text("Ваша корзина пуста.")
        return ConversationHandler.END

    for item in cart_items:
        create_order(user_id, item['item_type'], item['item'])

    clear_cart(user_id)

    await update.callback_query.message.reply_text("Ваш заказ оформлен! Спасибо за ваш заказ.")
    return await show_main_menu(update, context)


async def remove_item_from_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    index_to_remove = int(update.callback_query.data.split('_')[-1])
    likes_key = f'likes_{user_id}'
    likes = context.user_data.get(likes_key, [])
    
    if 0 <= index_to_remove < len(likes):
        item_to_remove = likes.pop(index_to_remove)
        
        # Удаляем элемент из базы данных
        remove_like_from_db(user_id, item_to_remove)
        
        context.user_data[likes_key] = likes
        
        if likes:
            context.user_data['likes_index'] = 0
            return await show_liked_property(update, context)
        else:
            await update.callback_query.message.edit_text("У вас нет понравившихся объектов.")
            return ConversationHandler.END
    else:
        await update.callback_query.answer("Не удалось удалить элемент. Попробуйте снова.")
        return await show_liked_property(update, context)


async def remove_item_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_id = int(query.data.split("_")[-1])
    context.user_data['item_to_remove'] = item_id

    # Получаем информацию об элементе для отображения в сообщении
    cart_items = context.user_data.get('cart_items', [])
    item_to_remove = next((item for item in cart_items if item['id'] == item_id), None)

    if item_to_remove:
        item_html = item_to_remove['item']
        item_soup = BeautifulSoup(item_html, "html.parser")
        title_element = item_soup.find("h2", class_="propertyCard-title")
        item_title = title_element.get_text(strip=True) if title_element else "Недвижимость"

        keyboard = [
            [InlineKeyboardButton("Да", callback_data=f"confirm_remove_{item_id}")],
            [InlineKeyboardButton("Нет", callback_data="cancel_remove")]
        ]

        await query.message.reply_text(
            f"Вы уверены, что хотите удалить '{item_title}' из корзины?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.answer("Элемент не найден. Попробуйте снова.")
        return await show_cart(update, context)


# Функция для подтверждения удаления элемента из корзины
async def confirm_remove_item(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    item_to_remove = context.user_data.get('item_to_remove')
    user_id = query.from_user.id

    if item_to_remove:
        try:
            remove_item_from_cart_db(user_id, item_to_remove['id'])
            cart_items = context.user_data.get('cart_items', [])
            cart_items.remove(item_to_remove)
            context.user_data['cart_items'] = cart_items
            await query.answer("Элемент успешно удален.")
        except Exception as e:
            await query.answer("Ошибка при удалении элемента. Попробуйте снова.")
            return await show_cart(update, context)

        if cart_items:
            return await show_cart(update, context)
        else:
            await query.message.edit_text("Ваша корзина пуста.")
            return ConversationHandler.END
    else:
        await query.answer("Не удалось удалить элемент. Попробуйте снова.")
        return await show_cart(update, context)

async def cancel_remove_item(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer("Удаление отменено.")
    return await show_cart(update, context)


async def confirm_removal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id

    item_index = context.user_data.get('item_to_remove')
    if item_index is None:
        await query.answer("Не удалось удалить элемент. Попробуйте снова.")
        return await show_cart(update, context)

    cart_items = context.user_data.get('cart_items', [])
    if 0 <= item_index < len(cart_items):
        item_to_remove = cart_items.pop(item_index)
        
        # Удаляем элемент из базы данных
        remove_item_from_cart_db(user_id, item_to_remove['id'])
        
        context.user_data['cart_items'] = cart_items
        
        if cart_items:
            context.user_data['cart_index'] = 0
            return await show_cart(update, context)
        else:
            await query.message.edit_text("Ваша корзина пуста.")
            return ConversationHandler.END
    else:
        await query.answer("Не удалось удалить элемент. Попробуйте снова.")
        return await show_cart(update, context)
    

async def clear_cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.callback_query.from_user.id

    clear_cart(user_id)

    context.user_data['cart_items'] = []

    await update.callback_query.message.reply_text("Корзина очищена!")
    return await show_main_menu(update, context)

async def show_cart_property(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    cart = context.user_data.get(f'cart_{user_id}', [])
    current_index = context.user_data.get('cart_index', 0)
    total_properties = len(cart)

    if not cart:
        await (update.message or update.callback_query.message).reply_text("Ваша корзина пуста.")
        return ConversationHandler.END

    current_property_html = cart[current_index]
    current_property = BeautifulSoup(current_property_html, "html.parser")

    title_element = current_property.find("h2", class_="propertyCard-title")
    price_element = current_property.find("span", class_="propertyCard-priceValue")
    address_element = current_property.find("address", class_="propertyCard-address")
    link_element = current_property.find("a", class_="propertyCard-link")
    image_element = current_property.find("img", class_="propertyCard-img")

    title = title_element.get_text(strip=True) if title_element else "N/A"
    price = price_element.get_text(strip=True) if price_element else "N/A"
    address = address_element.get_text(strip=True) if address_element else "N/A"
    link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else "N/A"
    image_url = image_element["src"] if image_element else None

    message = f"{title}\nЦена: {price}\nАдрес: {address}\n[Ссылка]({link})\n\n{current_index + 1} из {total_properties}"

    keyboard = [
        [
            InlineKeyboardButton("⬅️ Назад", callback_data="prev_cart"),
            InlineKeyboardButton("Вперед ➡️", callback_data="next_cart")
        ],
        [
            InlineKeyboardButton("🗑 Удалить", callback_data=f"remove_cart_{current_index}")
        ],
        [
            InlineKeyboardButton("Вернуться в меню", callback_data="back_to_menu")
        ]
    ]

    try:
        if update.message:
            if image_url:
                await update.message.reply_photo(photo=image_url, caption=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else:
                await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            if image_url:
                await update.callback_query.message.edit_media(
                    media=InputMediaPhoto(media=image_url, caption=message, parse_mode='Markdown'),
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.callback_query.message.edit_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    except Exception as e:
        print(f"Failed to edit message: {e}")

    return NAVIGATE_RESULTS

async def go_back_to_main_menu_from_property_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['property_search_active'] = False  # Сбрасываем активность поиска недвижимости
    return await show_main_menu(update, context)

def property_search_conversation_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏡 Поиск недвижимости$|^🏡 Ko'chmas mulk qidirish$|^🏡 Search Property$"), property_search)],
        states={
            PRICE: [
                MessageHandler(filters.Regex("^🔙 Вернуться в меню$|^🔙 Menyuga qaytish$|^🔙 Return to menu$"), go_back_property_search),
                MessageHandler(filters.TEXT & ~filters.COMMAND, price)
            ],
            ROOMS: [
                MessageHandler(filters.Regex("^⬅️ Назад$|^⬅️ Orqaga$|^⬅️ Back$"), go_back_property_search),
                MessageHandler(filters.TEXT & ~filters.COMMAND, rooms)
            ],
            PROPERTY_TYPE: [
                MessageHandler(filters.Regex("^⬅️ Назад$|^⬅️ Orqaga$|^⬅️ Back$"), go_back_property_search),
                MessageHandler(filters.TEXT & ~filters.COMMAND, property_type)
            ],
            FURNISH: [
                MessageHandler(filters.Regex("^⬅️ Назад$|^⬅️ Orqaga$|^⬅️ Back$"), go_back_property_search),
                MessageHandler(filters.TEXT & ~filters.COMMAND, furnish)
            ],
            LIVING_TYPE: [
                MessageHandler(filters.Regex("^⬅️ Назад$|^⬅️ Orqaga$|^⬅️ Back$"), go_back_property_search),
                MessageHandler(filters.TEXT & ~filters.COMMAND, living_type)
            ],
            SHOW_RESULTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, show_results)
            ],
            NAVIGATE_RESULTS: [
                CallbackQueryHandler(navigate_results, pattern="^(next|prev|back_to_menu|next_like|prev_like|next_cart|prev_cart)$"),
                CallbackQueryHandler(like_property, pattern="^like$"),
                CallbackQueryHandler(add_property_to_cart, pattern="^cart$"),
                CallbackQueryHandler(handle_payment_choice, pattern="^(pay_later|confirm_payment)$"),
                CallbackQueryHandler(cancel_order, pattern="^cancel_order$")
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Вернуться в меню$|^🔙 Menyuga qaytish$|^🔙 Return to Menu$"), show_main_menu)],
        allow_reentry=True
    )