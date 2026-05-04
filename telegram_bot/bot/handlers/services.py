#bot/handlers/services.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from bot.handlers.common import show_main_menu
from bot.handlers.language import get_message
from bot.utils.database import add_to_cart_db, get_cart, get_user_language

SERVICES, INDIVIDUAL_SERVICES, PACKAGE_SERVICES, NAVIGATE_SERVICES = range(23, 27)


def services_keyboard(language):
    keyboard = [
        [InlineKeyboardButton(get_message(language, 'our_packages'), callback_data="packages")],
        [InlineKeyboardButton(get_message(language, 'individual_services'), callback_data="individual_services")],
    ]
    return InlineKeyboardMarkup(keyboard)

def services_reply_keyboard(language):
    keyboard = [
        [get_message(language, 'back_services')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['services_menu_active'] = True  # Активируем состояние услуг
    # Полная очистка контекста пользователя для предотвращения конфликтов данных
    context.user_data.clear()
    
    # Сохраняем текущий сервис для восстановления при возврате
    context.user_data['current_service'] = 'services'

    user_id = update.effective_user.id
    language = get_user_language(user_id)  # Определяем язык пользователя

    if update.message:
        await update.message.reply_text(get_message(language, 'select_service_type'), reply_markup=services_keyboard(language))
        await update.message.reply_text(get_message(language, 'press_back_to_return'), reply_markup=services_reply_keyboard(language))
    elif update.callback_query:
        await update.callback_query.message.edit_text(get_message(language, 'select_service_type'), reply_markup=services_keyboard(language))
    return SERVICES


def get_services(language='ru'):
    services = [
        # Индивидуальные услуги
        {
            "title_key": 'public_transport_service',
            "price": "£99 ($130)"
        },
        {
            "title_key": 'private_transfer_service',
            "price": "£300 ($381)"
        },
        {
            "title_key": 'sim_card_assistance_service',
            "price": "£23 ($30)"
        },
        {
            "title_key": 'oyster_card_assistance_service',
            "price": "£23 ($30)"
        },
        {
            "title_key": 'regular_reports_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'housing_search_service',
            "price": "£45 ($60)"
        },
        {
            "title_key": 'area_consultation_service',
            "price": "£23 ($30)"
        },
        {
            "title_key": 'temporary_housing_assistance_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'moving_assistance_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'local_registration_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'support_24_7_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'neighbourhood_review_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'utility_connection_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'bank_account_assistance_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'lease_agreement_assistance_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'document_translation',
            "price": "£20 ($26)"
        },
        # Пакеты услуг
        {
            "title_key": 'package_meet_me',
            "price": "£114 ($150)",
            "details": [
                'airport_pickup',
                'transport_to_residence',
                'sim_card_assistance',
                'oyster_card_assistance',
                'regular_reports_to_parents'
            ]
        },
        {
            "title_key": 'package_housing',
            "price": "£342 ($450)",
            "details": [
                'all_services_meet_me',
                'housing_search',
                'area_consultation',
                'apartment_viewing',
                'temporary_housing_assistance',
                'moving_assistance'
            ]
        },
        {
            "title_key": 'premium_package',
            "price": "£647 ($850)",
            "details": [
                'all_services_housing',
                'local_registration_assistance',
                'support_24_7',
                'neighbourhood_review',
                'utility_connection',
                'bank_account_assistance',
                'lease_agreement_assistance',
                'premium_moving_assistance',
                'gift_from_company'
            ]
        }
    ]

    # Переводим названия услуг
    for service in services:
        service['title'] = get_message(language, service['title_key'])
    return services


async def show_packages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = get_user_language(user_id)  # Определяем язык пользователя

    context.user_data['package_services'] = [
        {
            "title_key": 'package_meet_me',  # Сохраняем ключ
            "price": "£114 ($150)",
            "details": [
                'airport_pickup',
                'transport_to_residence',
                'sim_card_assistance',
                'oyster_card_assistance',
                'regular_reports_to_parents'
            ]
        },
        {
            "title_key": 'package_housing',  # Сохраняем ключ
            "price": "£342 ($450)",
            "details": [
                'all_services_meet_me',
                'housing_search',
                'area_consultation',
                'apartment_viewing',
                'temporary_housing_assistance',
                'moving_assistance'
            ]
        },
        {
            "title_key": 'premium_package',  # Сохраняем ключ
            "price": "£647 ($850)",
            "details": [
                'all_services_housing',
                'local_registration_assistance',
                '24_7_support',
                'neighbourhood_review',
                'utility_connection',
                'bank_account_assistance',
                'lease_agreement_assistance',
                'premium_moving_assistance',
                'gift_from_company'
            ]
        }
    ]
    context.user_data['current_index'] = 0
    return await navigate_services(update, context)


async def show_individual_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = get_user_language(user_id)  # Определяем язык пользователя

    context.user_data['individual_services'] = [
        {
            "title_key": 'public_transport_service',
            "price": "£99 ($130)"
        },
        {
            "title_key": 'private_transfer_service',
            "price": "£300 ($381)"
        },
        {
            "title_key": 'sim_card_assistance_service',
            "price": "£23 ($30)"
        },
        {
            "title_key": 'oyster_card_assistance_service',
            "price": "£23 ($30)"
        },
        {
            "title_key": 'regular_reports_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'housing_search_service',
            "price": "£45 ($60)"
        },
        {
            "title_key": 'area_consultation_service',
            "price": "£23 ($30)"
        },
        {
            "title_key": 'temporary_housing_assistance_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'moving_assistance_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'local_registration_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'support_24_7_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'neighbourhood_review_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'utility_connection_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'bank_account_assistance_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'lease_agreement_assistance_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'document_translation',
            "price": "£20 ($0.01)"
        }
    ]
    context.user_data['current_index'] = 0
    return await navigate_services(update, context)



async def add_service_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    language = get_user_language(user_id)

    cart_items = await get_cart(user_id)
    
    # Определяем, какие услуги сейчас активны
    if 'package_services' in context.user_data:
        services_key = 'package_services'
    elif 'individual_services' in context.user_data:
        services_key = 'individual_services'
    else:
        await query.message.reply_text(get_message(language, 'service_selection_error'))
        return NAVIGATE_SERVICES

    service_index = context.user_data['current_index']
    service_item = context.user_data[services_key][service_index]

    if isinstance(service_item, dict):
        service_key = service_item['title_key']
        service_data = {
            'key': service_key,
            'price': service_item['price'],
        }
        if 'details' in service_item:
            service_data['details'] = service_item['details']

        # Проверка на наличие пакета в корзине
        if services_key == 'package_services' and any(item['item']['key'].startswith('package_') for item in cart_items if item['item_type'] == 'service'):
            await query.answer(get_message(language, 'package_already_in_cart'))
            await query.message.reply_text(get_message(language, 'package_already_in_cart'))
            return NAVIGATE_SERVICES

        item_type = 'service' if services_key == 'package_services' else 'individual_service'
    else:
        service_data = service_item  # Для индивидуальных услуг
        if any(service_item == item['item'] for item in cart_items):
            await query.answer(get_message(language, 'service_already_in_cart'))
            await query.message.reply_text(get_message(language, 'service_already_in_cart'))
            return NAVIGATE_SERVICES
        item_type = 'individual_service'

    await add_to_cart_db(user_id, item_type, service_data)

    if 'cart_items' not in context.user_data:
        context.user_data['cart_items'] = []
    context.user_data['cart_items'].append({'item_type': item_type, 'item': service_data})

    await query.answer(get_message(language, 'service_added_to_cart'))
    await query.message.reply_text(get_message(language, 'service_added_to_cart'))

    return NAVIGATE_SERVICES



def navigate_services_keyboard(language):
    keyboard = [
        [
            InlineKeyboardButton("⬅️ " + get_message(language, 'back_ser'), callback_data="prev_service"),
            InlineKeyboardButton(get_message(language, 'next_ser') + " ➡️", callback_data="next_service")
        ],
        [
            InlineKeyboardButton("🛒 " + get_message(language, 'add_to_cart_services'), callback_data="add_service_to_cart")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def navigate_reply_keyboard(language):
    keyboard = [
        [get_message(language, 'back_services'), get_message(language, 'main_menu_services')]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)



async def navigate_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    # Определяем, какие услуги сейчас активны
    if 'package_services' in context.user_data:
        services_key = 'package_services'
    elif 'individual_services' in context.user_data:
        services_key = 'individual_services'
    else:
        await query.message.reply_text(get_message(language, 'service_selection_error'))
        return NAVIGATE_SERVICES

    if query:
        await query.answer()
        if query.data == "next_service":
            context.user_data['current_index'] = (context.user_data['current_index'] + 1) % len(context.user_data[services_key])
        elif query.data == "prev_service":
            context.user_data['current_index'] = (context.user_data['current_index'] - 1) % len(context.user_data[services_key])
        elif query.data == "back_to_services":
            return await show_services(update, context)
        elif query.data == "add_service_to_cart":
            return await add_service_to_cart(update, context)

    current_index = context.user_data['current_index']
    services = context.user_data[services_key]
    total_services = len(services)
    current_service = services[current_index]

    # Логика отображения счётчика услуг
    if language == "ru":
        service_count_message = f"{current_index + 1} из {total_services}"
    elif language == "uz":
        service_count_message = f"{current_index + 1} dan {total_services}"
    else:
        service_count_message = f"{current_index + 1} of {total_services}"

    # Формирование сообщения с использованием get_message для ключа 'public_transport_service'
    if 'details' in current_service:
        message = (
            f"*{get_message(language, current_service['title_key'])}*\n\n"
            f"{service_count_message}\n\n"
            f"{get_message(language, 'price_services')}: {current_service['price']}\n\n"
            f"{get_message(language, 'services_services')}:\n" +
            "\n".join([f"- {get_message(language, detail_key)}" for detail_key in current_service['details']])
        )
    else:
        message = (
            f"*{get_message(language, current_service['title_key'])}*\n\n"
            f"{service_count_message}\n\n"
            f"{get_message(language, 'price_services')}: {current_service['price']}"
        )

    # Отправка сообщения в зависимости от типа запроса
    if update.message:
        await update.message.reply_text(message, reply_markup=navigate_services_keyboard(language), parse_mode='Markdown')
        await update.message.reply_text(get_message(language, 'press_back_or_main_menu_services'), reply_markup=navigate_reply_keyboard(language))
    elif query:
        await query.message.edit_text(message, reply_markup=navigate_services_keyboard(language), parse_mode='Markdown')

    return NAVIGATE_SERVICES


async def go_back_to_main_menu_from_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Сбрасываем активность меню услуг
    context.user_data['services_menu_active'] = False  
    await show_main_menu(update, context)
    return ConversationHandler.END

def services_conversation_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("💠 Наши Услуги|💠 Bizning xizmatlarimiz|💠 Our Services"), show_services)],
        states={
            SERVICES: [
                CallbackQueryHandler(show_packages, pattern="packages"),
                CallbackQueryHandler(show_individual_services, pattern="individual_services"),
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), show_main_menu)
            ],
            PACKAGE_SERVICES: [
                CallbackQueryHandler(navigate_services, pattern="^(next_service|prev_service|back_to_services|add_service_to_cart)$"),
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), show_services)
            ],
            INDIVIDUAL_SERVICES: [
                CallbackQueryHandler(navigate_services, pattern="^(next_service|prev_service|back_to_services|add_service_to_cart)$"),
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), show_services)
            ],
            NAVIGATE_SERVICES: [
                CallbackQueryHandler(navigate_services, pattern="^(next_service|prev_service|back_to_services|add_service_to_cart)$"),
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), show_services),
                MessageHandler(filters.Regex("^Главное меню$|^Asosiy menyu$|^Main Menu$"), show_main_menu)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Главное меню$|^Asosiy menyu$|^Main Menu$"), show_main_menu)],
        allow_reentry=True  # Позволяет возвращаться к этому ConversationHandler после перезапуска
    )