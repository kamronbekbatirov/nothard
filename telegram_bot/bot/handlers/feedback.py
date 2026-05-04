from bot.handlers.admin import ADMIN_IDS
from bot.handlers.common import show_main_menu
from bot.utils.database import save_feedback_to_db
from bot.handlers.language import get_message
from bot.utils.database import get_user_language
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

FEEDBACK = 22

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    language = get_user_language(user_id)

    context.user_data['feedback_menu_active'] = True  # Активируем состояние отзывов
    context.user_data['feedback_started'] = True  # Флаг для отслеживания начала ввода отзыва
    keyboard = [
        [KeyboardButton(get_message(language, "feedback_back"))]  # Используем мультиязычный текст для кнопки
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(get_message(language, "feedback_please_leave"), reply_markup=reply_markup)  # Мультиязычный текст для сообщения
    return FEEDBACK

async def save_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    language = get_user_language(user_id)
    feedback_text = update.message.text

    # Проверяем, действительно ли пользователь оставил отзыв в активном контексте
    if context.user_data.get('feedback_started'):
        if feedback_text == get_message(language, "feedback_back"):  # Проверка кнопки "Назад"
            return await show_main_menu(update, context)

        # Сохранение отзыва в базу данных
        save_feedback_to_db(user_id, feedback_text)

        # Отправляем благодарственное сообщение
        await update.message.reply_text(get_message(language, "feedback_thank_you"))
    else:
        await update.message.reply_text(get_message(language, "feedback_not_registered"))

    # Сбрасываем флаги активности после завершения действия
    context.user_data['feedback_menu_active'] = False
    context.user_data['feedback_started'] = False

    # Возвращаем пользователя в главное меню
    return await show_main_menu(update, context)

async def go_back_to_main_menu_from_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Сбрасываем активность меню отзывов
    context.user_data['feedback_menu_active'] = False  
    context.user_data['feedback_started'] = False  # Сбрасываем флаг начала ввода отзыва
    await show_main_menu(update, context)
    return ConversationHandler.END