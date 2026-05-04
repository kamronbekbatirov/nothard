import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from bot.handlers.addproperty import go_back_to_main_menu_from_property_link
from bot.handlers.admin import go_back_to_main_menu_from_admin
from bot.handlers.common import main_menu_keyboard, show_main_menu
from bot.handlers.feedback import go_back_to_main_menu_from_feedback
from bot.handlers.info import go_back_to_main_menu
from bot.handlers.language import get_message
from bot.handlers.profile_management import go_back_to_main_menu_from_profile
from bot.handlers.property_search import go_back_to_main_menu_from_property_search
from bot.handlers.services import go_back_to_main_menu_from_services
from bot.utils.database import (
    get_user_language,
    get_user_profile,
    save_user,
    is_user_registered,
    update_user_profile,
    find_user_by_phone_or_email,
    get_next_website_id,
    update_user_profile_by_website_id,
)
import sqlite3
import urllib.parse
import bcrypt
import requests 


from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64
from config import SECRET_KEY  # Импортируем ключ из конфигурации

aesgcm = AESGCM(SECRET_KEY)

# Определение состояний для ConversationHandler
LANGUAGE, WEBSITE_REGISTRATION_CHECK, VERIFY_WEBSITE_ACCOUNT, NAME, CONTACT_PHONE, EMAIL, PASSWORD, CONFIRM_PASSWORD = range(8)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_IDS = [3461866]

def back_keyboard(language):
    return ReplyKeyboardMarkup([[KeyboardButton(get_message(language, "back"))]], resize_keyboard=True)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def yes_no_keyboard(language):
    if language == 'ru':
        buttons = [
            [InlineKeyboardButton('Да', callback_data='yes')],
            [InlineKeyboardButton('Нет', callback_data='no')]
        ]
    elif language == 'uz':
        buttons = [
            [InlineKeyboardButton('Ha', callback_data='yes')],
            [InlineKeyboardButton('Yo\'q', callback_data='no')]
        ]
    else:
        buttons = [
            [InlineKeyboardButton('Yes', callback_data='yes')],
            [InlineKeyboardButton('No', callback_data='no')]
        ]
    return InlineKeyboardMarkup(buttons)

def phone_keyboard(language):
    return ReplyKeyboardMarkup([
        [KeyboardButton(get_message(language, "share_phone"), request_contact=True)],
        [KeyboardButton(get_message(language, "back"))]
    ], resize_keyboard=True)

# Функция для дешифрования данных
def decrypt_data_aes(encrypted_data: str) -> str:
    encrypted_data_bytes = base64.urlsafe_b64decode(encrypted_data)  # Декодируем из Base64
    nonce = encrypted_data_bytes[:12]  # Первые 12 байт — это nonce
    ciphertext = encrypted_data_bytes[12:]  # Остальное — это зашифрованные данные

    try:
        decrypted_data = aesgcm.decrypt(nonce, ciphertext, None).decode()
        print(f"DECRYPTED DATA: {decrypted_data}")  # Логируем расшифрованные данные
        return decrypted_data
    except Exception as e:
        print(f"Error while decrypting data: {e}")
        raise

# Функция для подписки пользователя на заказ
def subscribe_user_to_order(order_id: int, user_id: int) -> bool:
    """
    Добавляет пользователя в таблицу подписчиков заказа. Возвращает True, если пользователь уже был подписан.

    :param order_id: ID заказа
    :param user_id: ID пользователя
    :return: True, если пользователь уже подписан
    """
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()

            # Проверяем, существует ли запись для этого пользователя и заказа
            c.execute("SELECT * FROM order_subscribers WHERE order_id = ? AND user_id = ?", (order_id, user_id))
            if c.fetchone():
                print(f"User {user_id} is already subscribed to order {order_id}.")
                return True  # Пользователь уже подписан

            # Добавляем нового подписчика
            c.execute("INSERT INTO order_subscribers (order_id, user_id) VALUES (?, ?)", (order_id, user_id))
            conn.commit()
            print(f"User {user_id} subscribed to order {order_id} successfully.")
            return False  # Новый подписчик
    except sqlite3.Error as e:
        print(f"An error occurred while subscribing user to order: {e}")
        return False

# Функция для проверки, является ли пользователь владельцем заказа
def is_order_owner(order_id: int, user_id: int) -> bool:
    """
    Проверяет, является ли данный пользователь владельцем указанного заказа.
    :param order_id: ID заказа
    :param user_id: ID пользователя
    :return: True, если пользователь владелец заказа, иначе False
    """
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM orders WHERE order_id = ?", (order_id,))
            owner_id = c.fetchone()
            if owner_id and owner_id[0] == user_id:
                return True
            return False
    except sqlite3.Error as e:
        print(f"An error occurred while checking order ownership: {e}")
        return False

async def handle_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    language = get_user_language(user_id) or 'ru'  # Default to Russian if language not set

    # Check if there are arguments in the /start command
    if context.args:
        arg = context.args[0]
        if arg.startswith('subscribe_'):
            try:
                encrypted_data = urllib.parse.unquote(arg.split('subscribe_')[1])
                decrypted_data = decrypt_data_aes(encrypted_data)
                order_id = int(decrypted_data)

                # Check if the user is the owner of the order
                if is_order_owner(order_id, user_id):
                    if language == 'ru':
                        message = "Извините, но вы не можете привязывать свой же заказ."
                    elif language == 'uz':
                        message = "Kechirasiz, lekin siz o'zingizning buyurtmangizni bog'lay olmaysiz."
                    else:
                        message = "Sorry, but you cannot link your own order."

                    await update.message.reply_text(message)
                    return ConversationHandler.END

                # Check if the user is already subscribed to this order
                already_subscribed = subscribe_user_to_order(order_id, user_id)

                # Check if the user is registered
                if is_user_registered(user_id):
                    if already_subscribed:
                        # If the user is already subscribed and registered
                        if not context.user_data.get(f'subscription_message_sent_{order_id}'):
                            if language == 'ru':
                                message = f"Вы уже привязали заказ №{order_id} к своему аккаунту. Вы можете просмотреть его, пройдя в главное меню и нажав на «🔖 Привязанные заказы»."
                            elif language == 'uz':
                                message = f"Siz bu buyurtmani №{order_id} allaqachon akkauntingizga bog'lagansiz. Asosiy menyuda «🔖 Bog'langan buyurtmalar» tugmasini bosib uni ko'rishingiz mumkin."
                            else:
                                message = f"You have already subscribed to order №{order_id} with your account. You can view it by going to the main menu and clicking on «🔖 Linked orders»."

                            await update.message.reply_text(message)
                            context.user_data[f'subscription_message_sent_{order_id}'] = True
                        return ConversationHandler.END
                    else:
                        if language == 'ru':
                            message = f"🎉 Вы успешно привязали заказ №{order_id}. Вы можете просмотреть его, пройдя в главное меню и нажав на «🔖 Привязанные заказы»."
                        elif language == 'uz':
                            message = f"🎉 Buyurtma raqami №{order_id} ga muvaffaqiyatli bog'landingiz. Asosiy menyuda «🔖 Bog'langan buyurtmalar» tugmasini bosib uni ko'rishingiz mumkin."
                        else:
                            message = f"🎉 You have successfully subscribed to order №{order_id}. You can view it by going to the main menu and clicking on «🔖 Linked orders»."

                        await update.message.reply_text(message)
                        context.user_data.pop(f'subscription_message_sent_{order_id}', None)
                        return ConversationHandler.END
                else:
                    if already_subscribed:
                        # If the user is not registered but already subscribed
                        message = (
                            f"🇷🇺 Вы уже привязаны к заказу №{order_id}, но не завершили регистрацию. "
                            "Чтобы начать регистрацию, введите команду /start.\n\n"
                            f"🇺🇿 Siz buyurtmaga allaqachon bog'langansiz №{order_id}, lekin ro'yxatdan o'tishni tugatmagansiz. "
                            "Ro'yxatdan o'tishni boshlash uchun /start buyrug'ini kiriting.\n\n"
                            f"🇬🇧 You are already subscribed to order №{order_id}, but haven’t completed registration. "
                            "To start the registration, please enter the command /start."
                        )

                        await update.message.reply_text(message)
                        return ConversationHandler.END

                    else:
                        # Link the order to an unregistered user
                        context.user_data['order_id'] = order_id
                        keyboard = [
                            [InlineKeyboardButton("🇷🇺 Русский", callback_data='ru')],
                            [InlineKeyboardButton("🇺🇿 O‘zbek", callback_data='uz')],
                            [InlineKeyboardButton("🇬🇧 English", callback_data='en')]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await update.message.reply_text(
                            f"Перед тем как мы привяжем заказ с номером №{order_id} к вашему аккаунту, вы должны зарегистрироваться.\n\n"
                            f"Buyurtmani akkauntingizga bog'lashdan oldin, biz buyurtma raqami №{order_id} ni akkauntingizga bog'laymiz. Ro'yxatdan o'tish zarur.\n\n"
                            f"Before we link the order number №{order_id} to your account, you must register. Please select a language:",
                            reply_markup=reply_markup
                        )
                        return LANGUAGE

            except Exception as e:
                logger.error(f"Error while decrypting data: {e}")
                await update.message.reply_text("Ошибка обработки ссылки. Пожалуйста, попробуйте снова.")
                return ConversationHandler.END

        elif arg.startswith('auth_') or arg.startswith('link_'):
            token = arg
            # Send a request to your website to confirm authentication or linking
            api_url = 'https://nothard.uz/api/telegram_auth_confirm'

            payload = {
                'token': token,
                'user_id': user_id  # Use user_id instead of telegram_id
            }

            try:
                response = requests.post(api_url, json=payload, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('message') == 'Authorization successful':
                        # Process successful response
                        user_profile = data.get('user_profile', {})
                        if user_profile:
                            # Ensure 'language' is present in user_profile
                            if 'language' not in user_profile:
                                # Try to get language from existing user data or set default
                                existing_user_data = get_user_profile(user_id)
                                if existing_user_data and 'language' in existing_user_data:
                                    user_profile['language'] = existing_user_data['language']
                                else:
                                    user_profile['language'] = 'ru'  # Default to Russian

                            # Update the user's profile
                            save_user(user_profile)
                            context.user_data.update(user_profile)

                        # Get login_token from the response
                        login_token = data.get('login_token')

                        if is_user_registered(user_id):
                            language = user_profile['language']
                            if language == 'ru':
                                message = 'Отлично, вы вошли!'
                                button_text = 'Перейти на сайт'
                            elif language == 'uz':
                                message = 'Ajoyib, siz tizimga kirdingiz!'
                                button_text = 'Saytga o‘tish'
                            else:
                                message = 'Great, you have logged in!'
                                button_text = 'Go to website'

                            # Form URL with login_token
                            url = f'https://nothard.uz/profile?login_token={login_token}'

                            keyboard = [
                                [InlineKeyboardButton(button_text, url=url)]
                            ]
                            reply_markup = InlineKeyboardMarkup(keyboard)

                            await update.message.reply_text(message, reply_markup=reply_markup)
                            return ConversationHandler.END
                        else:
                            if language == 'ru':
                                message = 'Пожалуйста, сначала зарегистрируйтесь.'
                            elif language == 'uz':
                                message = 'Iltimos, avval ro‘yxatdan o‘ting.'
                            else:
                                message = 'Please register first.'

                            await update.message.reply_text(message)
                            return await start(update, context)
                    else:
                        # Handle error message from the server
                        error_message = data.get('error', 'Ошибка авторизации. Пожалуйста, попробуйте снова.')
                        await update.message.reply_text(error_message)
                        return ConversationHandler.END
                else:
                    await update.message.reply_text('Ошибка связи с сервером. Пожалуйста, попробуйте позже.')
                    return ConversationHandler.END
            except requests.RequestException as e:
                logger.error(f"Request exception: {e}")
                await update.message.reply_text('Ошибка связи с сервером. Пожалуйста, попробуйте позже.')
                return ConversationHandler.END

        else:
            # If there are no special tokens, continue the standard process
            return await start(update, context)

    # Основная функция start
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            # End all active ConversationHandler
            for handler in context.application.handlers:
                if isinstance(handler, ConversationHandler):
                    handler.end(update, context)

            # Determine whether the update is from a message or a callback query
            if update.message:
                user_id = update.message.from_user.id
            elif update.callback_query:
                user_id = update.callback_query.from_user.id
                await update.callback_query.answer()  # Acknowledge the callback query
            else:
                logger.error("Update has neither message nor callback query")
                return ConversationHandler.END

            # Check if there are arguments in the /start command
            if context.args:
                arg = context.args[0]
                if arg.startswith('subscribe_'):
                    # Decode the argument if it's a subscribe token
                    arg = urllib.parse.unquote(arg)
                    context.args[0] = arg  # Update the argument in context.args
                    return await handle_start_command(update, context)
                elif arg.startswith('auth_') or arg.startswith('link_'):
                    # For auth_ and link_ tokens, do not decode
                    return await handle_start_command(update, context)

            # If the user was in any menu like info, profile, etc., exit them
            if (
                context.user_data.get('info_menu_active') or
                context.user_data.get('profile_menu_active') or
                context.user_data.get('feedback_menu_active') or
                context.user_data.get('services_menu_active') or
                context.user_data.get('property_link_active') or
                context.user_data.get('property_search_active') or
                context.user_data.get('admin_menu_active')
            ):
                if context.user_data.get('info_menu_active'):
                    return await go_back_to_main_menu(update, context)
                elif context.user_data.get('profile_menu_active'):
                    return await go_back_to_main_menu_from_profile(update, context)
                elif context.user_data.get('feedback_menu_active'):
                    return await go_back_to_main_menu_from_feedback(update, context)
                elif context.user_data.get('services_menu_active'):
                    return await go_back_to_main_menu_from_services(update, context)
                elif context.user_data.get('property_link_active'):
                    return await go_back_to_main_menu_from_property_link(update, context)
                elif context.user_data.get('property_search_active'):
                    return await go_back_to_main_menu_from_property_search(update, context)
                elif context.user_data.get('admin_menu_active'):
                    return await go_back_to_main_menu_from_admin(update, context)

            # Completely clear user and chat data
            context.user_data.clear()
            context.chat_data.clear()

            # Check if the user is already registered
            if is_user_registered(user_id):
                user_data = get_user_profile(user_id)
                if user_data is None or 'language' not in user_data:
                    # Handle missing language
                    language = 'ru'  # Default language
                    user_data = user_data or {}
                    user_data['language'] = language
                else:
                    language = user_data['language']
                context.user_data.update(user_data)
                await update.effective_chat.send_message(
                    get_message(language, 'welcome_back'),
                    reply_markup=main_menu_keyboard(user_id, language)
                )
            else:
                # If the user is not registered, offer language selection
                keyboard = [
                    [InlineKeyboardButton("🇷🇺 Русский", callback_data='ru')],
                    [InlineKeyboardButton("🇺🇿 O‘zbek", callback_data='uz')],
                    [InlineKeyboardButton("🇬🇧 English", callback_data='en')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.effective_chat.send_message(
                    "Выберите язык / Tilni tanlang / Choose your language:",
                    reply_markup=reply_markup
                )
                return LANGUAGE

            return ConversationHandler.END
        except Exception as e:
            logger.exception(f"Error in start: {e}, user_data={context.user_data}")
            return ConversationHandler.END

# Основная функция start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        # End all active ConversationHandler
        for handler in context.application.handlers:
            if isinstance(handler, ConversationHandler):
                handler.end(update, context)

        # Determine whether the update is from a message or a callback query
        if update.message:
            user_id = update.message.from_user.id
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
            await update.callback_query.answer()  # Acknowledge the callback query
        else:
            logger.error("Update has neither message nor callback query")
            return ConversationHandler.END

        # Check if there are arguments in the /start command
        if context.args:
            arg = context.args[0]
            if arg.startswith('subscribe_'):
                # Decode the argument if it's a subscribe token
                arg = urllib.parse.unquote(arg)
                context.args[0] = arg  # Update the argument in context.args
                return await handle_start_command(update, context)
            elif arg.startswith('auth_') or arg.startswith('link_'):
                # For auth_ and link_ tokens, do not decode
                return await handle_start_command(update, context)

        # If the user was in any menu like info, profile, etc., exit them
        if context.user_data.get('info_menu_active') or context.user_data.get('profile_menu_active') or context.user_data.get('feedback_menu_active') or context.user_data.get('services_menu_active') or context.user_data.get('property_link_active') or context.user_data.get('property_search_active') or context.user_data.get('admin_menu_active'):
            if context.user_data.get('info_menu_active'):
                return await go_back_to_main_menu(update, context)
            elif context.user_data.get('profile_menu_active'):
                return await go_back_to_main_menu_from_profile(update, context)
            elif context.user_data.get('feedback_menu_active'):
                return await go_back_to_main_menu_from_feedback(update, context)
            elif context.user_data.get('services_menu_active'):
                return await go_back_to_main_menu_from_services(update, context)
            elif context.user_data.get('property_link_active'):
                return await go_back_to_main_menu_from_property_link(update, context)
            elif context.user_data.get('property_search_active'):
                return await go_back_to_main_menu_from_property_search(update, context)
            elif context.user_data.get('admin_menu_active'):
                return await go_back_to_main_menu_from_admin(update, context)

        # Completely clear user and chat data
        context.user_data.clear()
        context.chat_data.clear()

        # Check if the user is already registered
        if is_user_registered(user_id):
            user_data = get_user_profile(user_id)
            if user_data is None or 'language' not in user_data:
                # Handle missing language
                language = 'ru'  # Default language
                user_data['language'] = language
            else:
                language = user_data['language']
            context.user_data.update(user_data)
            await update.effective_chat.send_message(get_message(language, 'welcome_back'), reply_markup=main_menu_keyboard(user_id, language))
        else:
            # If the user is not registered, offer language selection
            keyboard = [
                [InlineKeyboardButton("🇷🇺 Русский", callback_data='ru')],
                [InlineKeyboardButton("🇺🇿 O‘zbek", callback_data='uz')],
                [InlineKeyboardButton("🇬🇧 English", callback_data='en')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.effective_chat.send_message(
                "Выберите язык / Tilni tanlang / Choose your language:",
                reply_markup=reply_markup
            )
            return LANGUAGE

        return ConversationHandler.END
    except Exception as e:
        logger.exception(f"Error in start: {e}, user_data={context.user_data}")
        return ConversationHandler.END

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    language = query.data  # Get selected language
    user_id = query.from_user.id

    # Save the selected language in user_data and update user profile
    context.user_data['language'] = language
    update_user_profile(user_id, 'language', language)

    # If there is an order_id, continue the subscription process
    order_id = context.user_data.get('order_id')
    if order_id:
        if language == 'ru':
            message = (
                f"🎉 Вы успешно привязали заказ №{order_id}. "
                "Теперь вы сможете получить доступ к заказу после завершения регистрации, пройдя в главное меню и нажав на «🔖 Привязанные заказы»."
            )
            button_text = "Начать регистрацию"
        elif language == 'uz':
            message = (
                f"🎉 Buyurtma raqami №{order_id} ga muvaffaqiyatli bog'landingiz. "
                "Endi buyurtmaga kirish uchun ro'yxatdan o'tishni tugatganingizdan so'ng asosiy menyuda «🔖 Bog'langan buyurtmalar» tugmasini bosib kirishingiz mumkin."
            )
            button_text = "Ro'yxatdan o'tishni boshlash"
        else:  # English by default
            message = (
                f"🎉 You have successfully subscribed to order №{order_id}. "
                "You will be able to access the order after completing the registration by going to the main menu and clicking on «🔖 Linked orders»."
            )
            button_text = "Start registration"

        registration_button = InlineKeyboardMarkup([[InlineKeyboardButton(button_text, callback_data="start_registration")]])
        await query.message.edit_text(message, reply_markup=registration_button)
        return WEBSITE_REGISTRATION_CHECK  # Proceed to the next step of registration

    # Else, continue with registration
    # Ask if the user is registered on the website
    if language == 'ru':
        message = 'Вы уже регистрировались на нашем сайте https://nothard.uz? Пожалуйста, выберите "Да" или "Нет".'
    elif language == 'uz':
        message = 'Siz bizning https://nothard.uz saytimizda ro\'yxatdan o\'tganmisiz? Iltimos, "Ha" yoki "Yo\'q" ni tanlang.'
    else:
        message = 'Have you already registered on our website https://nothard.uz? Please choose "Yes" or "No".'

    await query.message.edit_text(message, reply_markup=yes_no_keyboard(language))
    return WEBSITE_REGISTRATION_CHECK

async def website_registration_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    language = context.user_data.get('language')
    response = query.data

    if response == 'yes':
        if language == 'ru':
            message = 'Пожалуйста, введите ваш номер телефона или email для проверки.'
        elif language == 'uz':
            message = 'Iltimos, tekshirish uchun telefon raqamingizni yoki email manzilingizni kiriting.'
        else:
            message = 'Please enter your phone number or email for verification.'

        await query.message.edit_text(message)
        return VERIFY_WEBSITE_ACCOUNT

    elif response == 'no':
        if language == 'ru':
            message = 'Пожалуйста, укажите ваше имя:'
        elif language == 'uz':
            message = 'Iltimos, ismingizni kiriting:'
        else:
            message = 'Please enter your name:'

        await query.message.edit_text(message)
        return NAME

    else:
        if language == 'ru':
            message = 'Пожалуйста, ответьте "Да" или "Нет".'
        elif language == 'uz':
            message = 'Iltimos, "Ha" yoki "Yo\'q" deb javob bering.'
        else:
            message = 'Please answer "Yes" or "No".'

        await query.message.edit_text(message, reply_markup=yes_no_keyboard(language))
        return WEBSITE_REGISTRATION_CHECK

# Проверка учетной записи на сайте
async def verify_website_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = context.user_data.get('language')
    user_input = update.message.text.strip()

    # Check in the database if a user with this phone or email exists
    user_data = find_user_by_phone_or_email(user_input)

    if user_data:
        # User exists, link their Telegram account
        user_id = update.message.from_user.id
        update_user_profile_by_website_id(user_data['website_id'], 'user_id', user_id)
        context.user_data.update(user_data)

        if language == 'ru':
            message = 'Ваш аккаунт успешно связан с вашим Telegram аккаунтом.'
        elif language == 'uz':
            message = 'Hisobingiz Telegram hisobingiz bilan muvaffaqiyatli bog\'landi.'
        else:
            message = 'Your account has been successfully linked with your Telegram account.'

        await update.message.reply_text(message, reply_markup=main_menu_keyboard(user_id, language))
        return ConversationHandler.END

    else:
        # User not found, proceed with registration
        if language == 'ru':
            message = 'Аккаунт не найден. Пожалуйста, продолжите регистрацию.\nПожалуйста, укажите ваше имя:'
        elif language == 'uz':
            message = 'Hisob topilmadi. Iltimos, ro\'yxatdan o\'tishni davom eting.\nIltimos, ismingizni kiriting:'
        else:
            message = 'Account not found. Please proceed with registration.\nPlease enter your name:'

        await update.message.reply_text(message)
        return NAME

# Функция для получения имени пользователя
async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = context.user_data.get('language')  # Получаем язык из user_data

    if update.message.text == get_message(language, "back"):
        await update.message.reply_text(get_message(language, "registration_cancelled"), reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    try:
        context.user_data['name'] = update.message.text
        await update.message.reply_text(get_message(language, "registration_prompt_phone"), reply_markup=phone_keyboard(language))
        return CONTACT_PHONE  # Переход к шагу ввода телефона
    except Exception as e:
        logger.error(f"Error in name: {e}")
        return ConversationHandler.END

# Функция для получения контактного телефона
async def contact_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = context.user_data.get('language')  # Получаем язык из user_data

    if update.message.text == get_message(language, "back"):
        await update.message.reply_text(get_message(language, "registration_prompt_name"), reply_markup=back_keyboard(language))
        return NAME

    try:
        if update.message.contact:
            context.user_data['phone'] = update.message.contact.phone_number
        else:
            context.user_data['phone'] = update.message.text

        await update.message.reply_text(get_message(language, "registration_prompt_email"), reply_markup=back_keyboard(language))
        return EMAIL  # Переход к шагу ввода email
    except Exception as e:
        logger.error(f"Error in contact_phone: {e}")
        return ConversationHandler.END

# Функция для получения email
async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = context.user_data.get('language')  # Получаем язык из user_data

    if update.message.text == get_message(language, "back"):
        await update.message.reply_text(get_message(language, "registration_prompt_phone"), reply_markup=phone_keyboard(language))
        return CONTACT_PHONE

    try:
        context.user_data['email'] = update.message.text

        # Now, prompt for password
        if language == 'ru':
            message = 'Введите пароль для того чтобы у вас был доступ через кабинет нашего сайта nothard.uz'
        elif language == 'uz':
            message = 'Iltimos, parolni kiriting, shunda nothard.uz sayti orqali hisobingizga kirishingiz mumkin bo\'ladi.'
        else:
            message = 'Please enter a password so that you can access your account through our website nothard.uz'

        await update.message.reply_text(message, reply_markup=back_keyboard(language))
        return PASSWORD

    except Exception as e:
        logger.error(f"Error in email: {e}")
        await update.message.reply_text(get_message(language, "registration_error"))
        return ConversationHandler.END

# Функция для получения пароля
async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = context.user_data.get('language')
    if update.message.text == get_message(language, "back"):
        await update.message.reply_text(get_message(language, "registration_prompt_email"), reply_markup=back_keyboard(language))
        return EMAIL

    password = update.message.text.strip()
    context.user_data['password'] = password

    if language == 'ru':
        message = 'Введите пароль еще раз:'
    elif language == 'uz':
        message = 'Parolni qaytadan kiriting:'
    else:
        message = 'Please re-enter your password:'

    await update.message.reply_text(message, reply_markup=back_keyboard(language))
    return CONFIRM_PASSWORD

# Функция для подтверждения пароля
# Функция для подтверждения пароля
async def confirm_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = context.user_data.get('language')
    if update.message.text == get_message(language, "back"):
        await update.message.reply_text(get_message(language, "registration_prompt_password"), reply_markup=back_keyboard(language))
        return PASSWORD

    password = context.user_data.get('password')
    confirm_password_text = update.message.text.strip()

    if password != confirm_password_text:
        if language == 'ru':
            message = 'Пароли не совпадают. Пожалуйста, попробуйте снова. Введите пароль:'
        elif language == 'uz':
            message = 'Parollar mos kelmaydi. Iltimos, qayta urinib ko\'ring. Parolni kiriting:'
        else:
            message = 'Passwords do not match. Please try again. Enter password:'

        await update.message.reply_text(message, reply_markup=back_keyboard(language))
        return PASSWORD

    # Пароли совпадают, сохраняем пользователя
    user_data = {
        'user_id': update.message.from_user.id,
        'name': context.user_data.get('name', ''),
        'phone': context.user_data.get('phone', ''),
        'email': context.user_data['email'],
        'language': context.user_data.get('language'),
        'password_hash': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),  # Сохраните как строку
        'website_id': get_next_website_id()
    }
    save_user(user_data)

    # Удалите 'password' из user_data, чтобы избежать хранения пароля в памяти
    context.user_data.pop('password', None)

    # Сообщение о завершении регистрации
    if language == 'ru':
        registration_completed_message = (
            "✅ Регистрация завершена!\n\n"
            "Этот бот поможет вам найти недвижимость для аренды или купли-продажи в Лондоне, а также предложит многие другие полезные услуги.\n\n"
            "📖 Краткое руководство по использованию бота:\n\n"
            "1. 🏡 Поиск недвижимости: Если вы еще не нашли недвижимость, нажмите здесь для поиска. Вы сможете просмотреть предложения и добавить понравившуюся в корзину.\n"
            "2. 🔗 Добавить найденную недвижимость: Если вы уже нашли недвижимость, отправьте ссылку, и мы ее просмотрим.\n"
            "3. 💠 Наши Услуги: Ознакомьтесь с нашими услугами, включая встречу в аэропорту и другие пакеты.\n"
            "4. ℹ️ О чем нужно знать: Узнайте подробнее о всех функциях этого бота."
        )
    elif language == 'uz':
        registration_completed_message = (
            "✅ Ro'yxatdan o'tish tugallandi!\n\n"
            "Bu bot sizga Londonda ijaraga yoki sotib olish uchun ko'chmas mulkni topishga, shuningdek boshqa ko'plab foydali xizmatlarni taklif qiladi.\n\n"
            "📖 Botdan foydalanish bo'yicha qisqacha qo'llanma:\n\n"
            "1. 🏡 Ko'chmas mulkni qidirish: Agar siz hali ko'chmas mulkni topmagan bo'lsangiz, bu yerga bosing va qidirish jarayonini boshlang. Siz ko'chmas mulkni ko'rib chiqishingiz va savatchaga qo'shishingiz mumkin.\n"
            "2. 🔗 Topilgan ko'chmas mulkni qo'shish: Agar siz allaqachon ko'chmas mulk topgan bo'lsangiz, uning havolasini yuboring, biz uni ko'rib chiqamiz.\n"
            "3. 💠 Bizning xizmatlar: Aeroportda kutib olish va boshqa xizmatlarimiz bilan tanishing.\n"
            "4. ℹ️ Nima bilish kerak: Ushbu botning barcha funksiyalari haqida ko'proq bilib oling."
        )
    else:  # Английский по умолчанию
        registration_completed_message = (
            "✅ Registration Completed!\n\n"
            "This bot will help you find property for rent or purchase in London, as well as many other useful services.\n\n"
            "📖 Quick guide on how to use the bot:\n\n"
            "1. 🏡 Search Property: If you haven't found a property yet, click here to start searching. You can browse properties and add the ones you like to your cart.\n"
            "2. 🔗 Add Found Property: If you've already found a property, send the link, and we'll review it for you.\n"
            "3. 💠 Our Services: Explore our services, including airport pickup and various service packages.\n"
            "4. ℹ️ What to Know: Learn more about all the features this bot offers."
        )

    # Отправка сообщения после завершения регистрации
    await update.message.reply_text(registration_completed_message, reply_markup=main_menu_keyboard(update.message.from_user.id, language))
    return ConversationHandler.END

# Не забудьте добавить обработчик для 'start_registration' callback
async def handle_registration_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id

    # Получаем язык из user_data
    language = context.user_data.get('language')

    if not language:
        # Если почему-то язык не сохранен, достаем его из профиля пользователя
        language = get_user_language(user_id)

    # Переход к следующему этапу регистрации
    await query.message.edit_text(get_message(language, 'registration_prompt_name'))
    return WEBSITE_REGISTRATION_CHECK
