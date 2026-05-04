from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.handlers.language import get_message
from bot.utils.database import get_user_language

async def show_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    # Устанавливаем ссылку на оферту в зависимости от языка пользователя
    if language == 'en':
        offer_url = "https://docs.google.com/document/d/1wXBLwR9IDWLgFovJe9vbtiPezk9agjUyrG6c4dMmjdY/edit?usp=sharing"
    elif language == 'uz':
        offer_url = "https://docs.google.com/document/d/1VYVwQ2Q-Qqm873bYGAHk9nD8GY6IPUcv9vUjy9aBhZU/edit?usp=sharing"
    else:  # Предполагается, что язык по умолчанию — русский
        offer_url = "https://docs.google.com/document/d/10-ve6ckrbhgBva7wNDch813MaXj_i2QZA1SgXY3RXPE/edit?usp=sharing"

    # Создаем inline-кнопку для открытия оферты
    keyboard = [
        [InlineKeyboardButton(get_message(language, "offer_view"), url=offer_url)]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с соответствующей ссылкой
    if update.message:
        await update.message.reply_text(get_message(language, "offer_message"), reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(get_message(language, "offer_message"), reply_markup=reply_markup)