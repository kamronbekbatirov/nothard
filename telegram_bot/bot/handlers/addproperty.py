import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

from bot.handlers.common import show_main_menu
from bot.handlers.language import get_message
from bot.utils.database import add_to_cart_db, get_user_profile

LOAD_PROPERTY_LINK = range(1)

from bot.utils.database import get_user_language, get_user_profile  # Обновите импорт

async def load_property_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_id = update.message.from_user.id
        language = get_user_language(user_id)  # Загружаем язык пользователя из базы данных
        context.user_data['language'] = language  # Сохраняем язык в контексте

        context.user_data['property_link_active'] = True  # Activate link addition state
        context.user_data['property_link_started'] = True  # Flag to track the start of link input

        keyboard = [
            [KeyboardButton(get_message(language, 'back_link'))]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            get_message(language, 'load_property_link_prompt'),
            reply_markup=reply_markup
        )
        return LOAD_PROPERTY_LINK
    except Exception as e:
        logging.error(f"Error in load_property_link: {e}")
        return ConversationHandler.END

async def save_property_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_id = update.message.from_user.id
        language = get_user_language(user_id)  # Загружаем язык пользователя из базы данных

        if update.message.text == get_message(language, 'back_link'):
            return await show_main_menu(update, context)

        if context.user_data.get('property_link_started'):
            link = update.message.text.strip()

            if not link.startswith("http://") and not link.startswith("https://"):
                link = "https://" + link  # Automatically add https://

            await add_to_cart_db(user_id, 'property', link, get_message(language, 'waiting_for_agent_response'))
            await update.message.reply_text(get_message(language, 'link_added_success'))
        else:
            await update.message.reply_text(get_message(language, 'not_a_link'))

        context.user_data['property_link_active'] = False
        context.user_data['property_link_started'] = False

        return await show_main_menu(update, context)
    except Exception as e:
        logging.error(f"Error in save_property_link: {e}")
        await update.message.reply_text(get_message(language, 'link_save_error'))
        return ConversationHandler.END

async def go_back_to_main_menu_from_property_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['property_link_active'] = False
    context.user_data['property_link_started'] = False  # Reset link input start flag

    user_id = update.message.from_user.id
    language = get_user_language(user_id)  # Загружаем язык пользователя из базы данных

    await show_main_menu(update, context)
    return ConversationHandler.END