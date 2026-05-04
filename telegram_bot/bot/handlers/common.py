from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
import telegram
from telegram.ext import ContextTypes, ConversationHandler

from bot.handlers.language import get_message
from bot.utils.database import get_user_profile

# Define ADMIN_IDS here or import from config
ADMIN_IDS = [3461866]

def main_menu_keyboard(user_id: int, language: str) -> ReplyKeyboardMarkup:
    # Создание главного меню с кнопками на основе выбранного языка
    keyboard = [
        [KeyboardButton(get_message(language, 'search_property'))],
        [KeyboardButton(get_message(language, 'add_found_property'))],
        [KeyboardButton(get_message(language, 'my_likes')), KeyboardButton(get_message(language, 'cart'))],
        [KeyboardButton(get_message(language, 'our_services'))],
        [KeyboardButton(get_message(language, 'my_orders'))],
        [KeyboardButton(get_message(language, 'linked_orders'))],  # Новая кнопка для привязанных заказов
        [KeyboardButton(get_message(language, 'profile_menu')), KeyboardButton(get_message(language, 'contacts'))],
        [KeyboardButton(get_message(language, 'what_to_know')), KeyboardButton(get_message(language, 'leave_feedback'))],
        [KeyboardButton(get_message(language, 'offer'))]  # Кнопка "Оферта"
    ]

    # Добавление админской панели, если пользователь является администратором
    if user_id in ADMIN_IDS:
        keyboard.append([KeyboardButton(get_message(language, 'admin_panel'))])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id

    # Получение данных профиля пользователя из базы данных
    user_data = get_user_profile(user_id)
    language = user_data.get('language', 'ru')  # Используем язык из базы данных

    context.user_data['admin_menu_active'] = False

    # Очистка данных пользователя и чата
    context.user_data.clear()
    context.chat_data.clear()

    # Завершение всех активных ConversationHandlers
    for handler in context.application.handlers:
        if isinstance(handler, ConversationHandler):
            handler.end(update, context)

    # Формирование клавиатуры главного меню
    reply_markup = main_menu_keyboard(user_id, language)

    # Отправка сообщения с главным меню в зависимости от того, было ли это сообщение или callback
    if update.message:
        await update.message.reply_text(get_message(language, 'main_menu'), reply_markup=reply_markup)
    elif update.callback_query:
        try:
            await update.callback_query.message.delete()
        except telegram.error.BadRequest:
            pass  # Игнорируем ошибку, если сообщение уже было удалено

        await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text=get_message(language, 'main_menu'), reply_markup=reply_markup)

    return ConversationHandler.END