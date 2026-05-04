# bot/handlers/contact.py

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from bot.handlers.language import get_message  # Импортируем вашу функцию для получения сообщений

from bot.utils.database import get_user_language

async def show_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Получаем user_id из update
    user_id = update.effective_user.id

    # Извлекаем язык пользователя из базы данных
    language = get_user_language(user_id)

    # Получаем сообщение на нужном языке
    contact_info = get_message(language, 'contact_info')

    # Отправляем сообщение
    await update.message.reply_text(
        contact_info,
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton(get_message(language, 'back_link'))]], resize_keyboard=True),
        parse_mode="Markdown"
    )