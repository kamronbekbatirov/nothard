from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from bot.handlers.common import show_main_menu
from bot.handlers.language import get_message
from bot.utils.database import get_user_language

INFO, BOT_FEATURES, USEFUL_INFO = range(21, 24)

async def show_info_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    # Очистка данных пользователя и чата
    context.user_data.clear()
    context.chat_data.clear()

    # Установка активности меню
    context.user_data['info_menu_active'] = True

    # Генерация кнопок с мультиязычными сообщениями
    keyboard = [
        [KeyboardButton(get_message(language, "info_bot_features")), KeyboardButton(get_message(language, "info_useful_info"))],
        [KeyboardButton(get_message(language, "info_back"))]
    ]

    await update.message.reply_text(
        get_message(language, "info_choose_info"),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return INFO

async def show_bot_features(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    # Получение мультиязычного сообщения с описанием функций бота
    features_message = get_message(language, "info_features_message")

    # Клавиатура с кнопкой "Назад"
    keyboard = [
        [KeyboardButton(get_message(language, "info_back"))]
    ]

    # Отправка сообщения с функциями бота
    await update.message.reply_text(features_message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True), parse_mode='Markdown')
    return INFO

async def show_useful_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    # Получение мультиязычного сообщения с полезной информацией
    info_message = get_message(language, "info_useful_info_message")

    # Клавиатура с кнопкой "Назад"
    keyboard = [
        [KeyboardButton(get_message(language, "info_back"))]
    ]

    # Отправка сообщения с полезной информацией
    await update.message.reply_text(info_message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True), parse_mode='Markdown')
    return INFO

async def go_back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Сброс активности меню
    context.user_data['info_menu_active'] = False

    # Возвращение в главное меню
    await show_main_menu(update, context)
    return ConversationHandler.END