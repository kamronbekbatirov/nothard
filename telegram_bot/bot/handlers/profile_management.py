from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from bot.handlers.common import show_main_menu
from bot.handlers.language import get_message
from bot.utils.database import get_user_profile, update_user_profile
import logging

logger = logging.getLogger(__name__)

PROFILE, EDIT_PROFILE, UPDATE_FIELD = range(11, 14)


async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Отправляем команду /start при нажатии на кнопку "Регистрация"
    await update.message.reply_text("/start")
    return await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="/start",
        parse_mode="Markdown"
    )

def register_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("Регистрация")]], resize_keyboard=True, one_time_keyboard=True)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['profile_menu_active'] = True  # Activate profile state
    user_id = update.message.from_user.id
    user_data = get_user_profile(user_id)

    if user_data:
        language = user_data.get('language', 'ru')
        logger.info(f"Language set to: {language}")

        try:
            profile_message = get_message(language, 'profile_account', profile=format_profile(user_data))
            await update.message.reply_text(profile_message, reply_markup=profile_keyboard(language))
        except KeyError as e:
            logger.error(f"KeyError: '{e.args[0]}' - Check if the key exists in the MESSAGES dictionary for language: {language}")
            await update.message.reply_text(get_message(language, "profile_load_error"))
        return PROFILE
    else:
        await update.message.reply_text(get_message('ru', "profile_not_found"), reply_markup=register_keyboard())
        return ConversationHandler.END

def format_profile(user_data):
    language = user_data.get('language', 'ru')
    
    # Get the translations for each label
    name_label = get_message(language, 'profile_name')
    phone_label = get_message(language, 'profile_phone')
    email_label = get_message(language, 'profile_email')
    language_label = get_message(language, 'profile_language')

    # Set language display based on selected language
    language_display = {
        "ru": "🇷🇺 Русский",
        "uz": "🇺🇿 O'zbekcha",
        "en": "🇬🇧 English"
    }.get(language, "🌐 Не выбран")

    # Return the formatted profile string with translated labels
    return f"{name_label}: {user_data['name']}\n{phone_label}: {user_data['phone']}\n{email_label}: {user_data['email']}\n{language_label}: {language_display}"

def profile_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton(get_message(language, 'edit_name')), KeyboardButton(get_message(language, 'edit_phone'))],
        [KeyboardButton(get_message(language, 'edit_email')), KeyboardButton(get_message(language, 'edit_language'))],
        [KeyboardButton(get_message(language, 'back_profile'))]
    ], resize_keyboard=True)

def register_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("Регистрация")]], resize_keyboard=True, one_time_keyboard=True)

async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = get_user_profile(user_id)
    language = user_data.get('language', 'ru')

    field_map = {
        get_message(language, 'edit_name').lower(): "name",
        get_message(language, 'edit_phone').lower(): "phone",
        get_message(language, 'edit_email').lower(): "email",
        get_message(language, 'edit_language').lower(): "language"
    }

    user_input = update.message.text.strip().lower()

    if user_input in field_map:
        field_name = field_map[user_input]
        context.user_data['edit_field'] = field_name
        if field_name == "language":
            return await choose_language(update, context)

        field_label = get_message(language, f'profile_{field_name}')

        await update.message.reply_text(
            get_message(language, 'enter_new_value', field=field_label),
            reply_markup=ReplyKeyboardMarkup([[get_message(language, 'back_profile')]], resize_keyboard=True)
        )
        return UPDATE_FIELD

    await update.message.reply_text(get_message(language, 'incorrect_field'), reply_markup=profile_keyboard(language))
    return PROFILE

async def update_profile_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    field = context.user_data.get('edit_field')
    new_value = update.message.text.strip()

    if field is None:
        await update.message.reply_text(get_message(context.user_data.get('language', 'ru'), "profile_load_error"), reply_markup=profile_keyboard(context.user_data.get('language', 'ru')))
        return PROFILE

    if new_value == get_message(context.user_data.get('language', 'ru'), 'back_profile'):
        return await profile(update, context)

    user_id = update.message.from_user.id
    user_data = get_user_profile(user_id)
    language = user_data.get('language', 'ru')

    if field == "language":
        language_map = {
            "🇷🇺 русский": "ru",
            "русский": "ru",
            "ru": "ru",
            "🇺🇿 o'zbekcha": "uz",
            "o'zbekcha": "uz",
            "uz": "uz",
            "🇬🇧 english": "en",
            "english": "en",
            "en": "en"
        }
        new_value = language_map.get(new_value.lower())
        if new_value is None:
            await update.message.reply_text(get_message(language, 'incorrect_language_selection'), reply_markup=profile_keyboard(language))
            return PROFILE

        # Update the language in context and in the database
        context.user_data['language'] = new_value  # Update the language in context data
        language = new_value  # Update the language for subsequent operations
        update_user_profile(user_id, 'language', new_value)  # Update in the database

    else:
        update_user_profile(user_id, field, new_value)

    # Map the field names to localized labels
    field_display_map = {
        "name": get_message(language, 'profile_name'),
        "phone": get_message(language, 'profile_phone'),
        "email": get_message(language, 'profile_email'),
        "language": get_message(language, 'profile_language')
    }
    
    await update.message.reply_text(f"{field_display_map[field]} {get_message(language, 'updated')}.")
    
    # Return to the profile view after updating the field
    return await profile(update, context)

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data = get_user_profile(user_id)
    language = user_data.get('language', 'ru')

    language_keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("🇷🇺 Русский"), KeyboardButton("🇺🇿 O'zbekcha"), KeyboardButton("🇬🇧 English")],
        [KeyboardButton(get_message(language, 'back_profile'))]
    ], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(get_message(language, 'select_language_prompt'), reply_markup=language_keyboard)
    return UPDATE_FIELD

async def go_back_to_main_menu_from_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['profile_menu_active'] = False
    user_id = update.message.from_user.id
    user_data = get_user_profile(user_id)
    language = user_data.get('language', 'ru')  # Ensure language is retrieved from the profile

    await show_main_menu(update, context)
    return ConversationHandler.END