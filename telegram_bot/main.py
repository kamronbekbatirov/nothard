# /main.py


from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler, PreCheckoutQueryHandler
from bot.handlers.addproperty import LOAD_PROPERTY_LINK, load_property_link, save_property_link
from bot.handlers.contact import show_contacts
from bot.handlers.info import show_bot_features, show_info_menu, show_useful_info
from bot.handlers.oferta import show_offer
from bot.handlers.registration import  CONFIRM_PASSWORD, PASSWORD, VERIFY_WEBSITE_ACCOUNT, WEBSITE_REGISTRATION_CHECK, confirm_password, handle_registration_start, handle_start_command, password, select_language, start, name, contact_phone, email, verify_website_account, website_registration_check
from bot.handlers.property_search import CONFIRM_REMOVE, add_property_to_cart, cancel_remove_item, clear_cart_handler, confirm_order_no, confirm_order_yes, confirm_removal, confirm_remove_item, handle_payment_choice, precheckout_callback,  property_search, price, remove_item_from_cart, remove_item_from_likes, rooms, property_type, furnish, living_type, set_task_status, show_order_admin_menu, show_order_tasks, show_results, navigate_results, like_property, add_property_to_cart, property_search_conversation_handler, show_likes, show_liked_property, show_cart, show_cart_property, remove_item_from_cart, confirm_order, successful_payment_callback, update_order_status_callback
from bot.handlers.profile_management import profile, edit_profile, update_profile_field
from bot.handlers.admin import ADD_EVENT_DESCRIPTION, ADD_EVENT_LINK, DELETE_EVENT, PROPERTIES, REQUEST_CLOUD_LINK, REQUEST_PROPERTY_CLOUD_LINK, SEND_MESSAGE_TO_USER, TASKS, VIEW_FEEDBACK, add_event, add_event_callback, admin_panel, back_to_actions_callback, back_to_main_menu, back_to_order, change_payment_status, credit_bonus, delete_event, delete_event_callback, receive_event_description, receive_event_link, request_message_for_user, save_cloud_link, save_property_cloud_link, save_task_status, select_property_status, send_message_to_user, show_order_properties, show_order_tasks_admin, skip_event_link, update_payment_status, update_property_status_callback, update_task_status, update_task_status_callback, view_events, view_feedback, view_users, view_orders, update_order_status_handler, request_order_number
from bot.handlers.feedback import feedback, save_feedback
from bot.handlers.services import services_conversation_handler, add_service_to_cart
from bot.handlers.subscribe import CONFIRM_UNLINK_ORDER, LINKED_BONUS_ACTIONS, LINKED_BONUS_FURNISH, LINKED_BONUS_LIKES, LINKED_BONUS_LIVING_TYPE, LINKED_BONUS_NAVIGATE_RESULTS, LINKED_BONUS_PRICE, LINKED_BONUS_PROPERTY_TYPE, LINKED_BONUS_ROOMS, LINKED_BONUS_SHOW_RESULTS, LINKED_NAVIGATE_ORDERS, LINKED_ORDER, ask_confirmation, confirm_unlink_order, linked_back_to_order_details, linked_back_to_orders_from_bonuses,  linked_select_order, linked_show_order_timeline, linked_show_ordered_properties, linked_show_ordered_services, linked_show_orders, remove_order
from bot.utils.database import init_db
from bot.handlers.common import show_main_menu
from bot.handlers.orders import BONUS_ACTIONS, BONUS_FURNISH, BONUS_LIKES, BONUS_LIVING_TYPE, BONUS_NAVIGATE_RESULTS, BONUS_PRICE, BONUS_PROPERTY_TYPE, BONUS_ROOMS, BONUS_SHOW_RESULTS, NAVIGATE_ORDERS, ORDER, TASK, add_own_property_to_order_with_bonus, add_property_to_order, add_property_to_order_from_likes, back_to_bonuses, back_to_bonuses_from_property_link, back_to_order_details, back_to_orders, back_to_orders_from_bonuses, back_to_task_status, bonus_furnish, bonus_living_type, bonus_navigate_results, bonus_price, bonus_property_search, bonus_property_type, bonus_rooms, bonus_save_property_link, bonus_show_property, bonus_show_results, delete_bonus_like, generate_share_link, go_back, select_order, select_task_status, show_bonus_liked_property, show_bonus_likes, show_order_timeline, show_orders, show_ordered_properties, show_ordered_services, show_user_bonuses, update_property_status_handler, update_task_status_handler
from config import BOT_TOKEN



# Определяем все состояния
LANGUAGE, WEBSITE_REGISTRATION_CHECK, VERIFY_WEBSITE_ACCOUNT, NAME, CONTACT_PHONE, EMAIL, PASSWORD, CONFIRM_PASSWORD = range(8)
PRICE, ROOMS, PROPERTY_TYPE, FURNISH, LIVING_TYPE, SHOW_RESULTS, NAVIGATE_RESULTS = range(4, 11)
PROFILE, EDIT_PROFILE, UPDATE_FIELD = range(11, 14)
ADMIN_PANEL, VIEW_USERS, VIEW_ORDERS, VIEW_FEEDBACK, REQUEST_ORDER_NUMBER, ORDER_ACTIONS, TASKS, PROPERTIES, REQUEST_PROPERTY_CLOUD_LINK = range(14, 23)
CONTACT = 20
INFO = 21
FEEDBACK = 22
SELECT_BONUS_ACTION, = range(25, 26)  # Задайте уникальный номер состояния
CHANGE_PAYMENT_STATUS = 27

def main() -> None:
    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    registration_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE: [CallbackQueryHandler(select_language)],
            WEBSITE_REGISTRATION_CHECK: [CallbackQueryHandler(website_registration_check)],
            VERIFY_WEBSITE_ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_website_account)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            CONTACT_PHONE: [MessageHandler(filters.CONTACT | filters.TEXT & ~filters.COMMAND, contact_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password)],
            CONFIRM_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_password)],
        },
        fallbacks=[CommandHandler('start', start)]
    )


    # ConversationHandler для обработки привязанных заказов
    linked_orders_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔖 Привязанные заказы$|^🔖 Bog'langan buyurtmalar$|^🔖 Linked Orders$"), linked_show_orders)],
        states={
            LINKED_ORDER: [
                MessageHandler(filters.Regex("^Заказ #\\d+$|^Buyurtma #\\d+$|^Order #\\d+$"), linked_select_order),
                MessageHandler(filters.Regex("^🔙 Вернуться в меню$|^🔙 Menyuga qaytish$|^🔙 Return to Menu$"), show_main_menu),
            ],
            LINKED_NAVIGATE_ORDERS: [
                MessageHandler(filters.Regex("^🔗 Сгенерировать ссылку$|^🔗 Havolani yaratish$|^🔗 Generate link$"), generate_share_link),  # Add this handler
                MessageHandler(filters.Regex("^📦 Приобретенные услуги$|^📦 Sotib olingan xizmatlar$|^📦 Purchased services$"), linked_show_ordered_services),
                MessageHandler(filters.Regex("^🏡 Запросы на недвижимость$|^🏡 Ko‘chmas mulk so‘rovlari$|^🏡 Property requests$"), linked_show_ordered_properties),
                MessageHandler(filters.Regex("^📅 Таймлайн заказа$|^📅 Buyurtma vaqt jadvali$|^📅 Order Timeline$"), linked_show_order_timeline),
                MessageHandler(filters.Regex("^❌ Отвязать заказ$|^❌ Buyurtmani olib tashlash$|^❌ Unlink Order$"), ask_confirmation),
                MessageHandler(filters.Regex("^🔙 Вернуться к заказам$|^🔙 Buyurtmalarga qaytish$|^🔙 Back to Orders$"), linked_show_orders),
                MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Orqaga$|^🔙 Back$"), linked_back_to_order_details),
            ],
            CONFIRM_UNLINK_ORDER: [
            MessageHandler(filters.Regex("^✅ Да$|^✅ Ha$|^✅ Yes$"), confirm_unlink_order),  # Подтверждение отвязки
            MessageHandler(filters.Regex("^❌ Нет$|^❌ Yo'q$|^❌ No$"), linked_show_orders),  # Отмена отвязки
            ],
            LINKED_BONUS_NAVIGATE_RESULTS: [
                CallbackQueryHandler(bonus_navigate_results, pattern="^(next|prev)$"),
                CallbackQueryHandler(add_property_to_order, pattern="^add_to_order$"),
                CallbackQueryHandler(back_to_bonuses, pattern="^back_to_bonuses$")
            ],
            LINKED_BONUS_LIKES: [
                CallbackQueryHandler(show_bonus_liked_property, pattern="^(next_bonus_like|prev_bonus_like)$"),
                CallbackQueryHandler(add_property_to_order_from_likes, pattern="^add_to_order_.*$"),
                CallbackQueryHandler(delete_bonus_like, pattern="^delete_bonus_like_.*$"),
                CallbackQueryHandler(back_to_bonuses, pattern="^back_to_bonuses$"),
                MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Orqaga$|^🔙 Back$"), back_to_orders_from_bonuses),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Вернуться в меню$|^🔙 Menyuga qaytish$|^🔙 Return to Menu$"), show_main_menu)],
        allow_reentry=True
    )
    
    property_search_handler = property_search_conversation_handler()

    profile_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("👤 Профиль / 🌐 Языки|👤 Profil / 🌐 Tillar|👤 Profile / 🌐 Languages"), profile)],
        states={
            PROFILE: [
                MessageHandler(filters.Regex("^✏️ Изменить имя$|^✏️ Ismni o'zgartirish$|^✏️ Edit Name$"), edit_profile),
                MessageHandler(filters.Regex("^📞 Изменить телефон$|^📞 Telefonni o'zgartirish$|^📞 Edit Phone$"), edit_profile),
                MessageHandler(filters.Regex("^✉️ Изменить email$|^✉️ Emailni o'zgartirish$|^✉️ Edit Email$"), edit_profile),
                MessageHandler(filters.Regex("^🌐 Изменить язык$|^🌐 Tilni o'zgartirish$|^🌐 Edit Language$"), edit_profile),
                MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Orqaga$|^🔙 Back$"), show_main_menu)
            ],
            UPDATE_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, update_profile_field)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Orqaga$|^🔙 Back$"), show_main_menu)],
        allow_reentry=True
    )

    admin_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("⚙️ Админка|⚙️ Admin paneli|⚙️ Admin Panel"), admin_panel)],
        states={
            ADMIN_PANEL: [
                MessageHandler(filters.Regex("^Список пользователей$|^Foydalanuvchilar ro'yxati$|^User List$"), view_users),
                MessageHandler(filters.Regex("^Список заказов$|^Buyurtmalar ro'yxati$|^Order List$"), view_orders),
                MessageHandler(filters.Regex("^Отзывы$|^Fikrlar$|^Feedback$"), view_feedback),
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), back_to_main_menu)
            ],
            VIEW_USERS: [
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), admin_panel)
            ],
            VIEW_ORDERS: [
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), admin_panel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, request_order_number)
            ],
            VIEW_FEEDBACK: [
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), admin_panel)
            ],
            REQUEST_ORDER_NUMBER: [
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), admin_panel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, request_order_number)
            ],
            ORDER_ACTIONS: [
                MessageHandler(
                    filters.Regex(
                        "^Принят$|^Qabul qilingan$|^Accepted$|"
                        "^Возврат$|^Qaytarildi$|^Returned$|"
                        "^Отменен$|^Bekor qilingan$|^Canceled$|"
                        "^Ожидание$|^Kutilmoqda$|^Pending$|"
                        "^Ожидание оплаты$|^Toʻlov kutilmoqda$|^Waiting for payment$|"
                        "^Выполняется$|^Bajarilmoqda$|^In progress$|"
                        "^Выполнен$|^Bajarildi$|^Completed$"
                    ),
                    update_order_status_handler
                ),   
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), admin_panel),
                MessageHandler(filters.Regex("^Изменить статус задач$|^Vazifa holatini o'zgartirish$|^Change Task Status$"), show_order_tasks_admin),
                MessageHandler(filters.Regex("^Изменить статус запросов на недвижимость$|^Ko'chmas mulk so'rovlarini o'zgartirish$|^Change Property Request Status$"), show_order_properties),
                MessageHandler(filters.Regex("^Изменить статус оплаты$|^To'lov holatini o'zgartirish$|^Change Payment Status$"), change_payment_status),  # Новая опция для изменения статуса оплаты
                MessageHandler(filters.Regex("^🎁 Зачислить бонус$|^🎁 Bonus qo'shish$|^🎁 Credit Bonus$"), credit_bonus),  # Новая опция для изменения статуса оплаты  
                MessageHandler(filters.Regex("^Отправить сообщение пользователю$|^Foydalanuvchiga xabar yuborish$|^Send a message to the user$"), request_message_for_user),  # Новая опция для изменения статуса оплаты                
                MessageHandler(filters.Regex("^Просмотреть события$|^Hodisalarni ko'rish$|^View Events$|^To'lov holatini o'zgartirish$|^Change Payment Status$"), view_events),                
                MessageHandler(filters.Regex("^Ожидание ответа агента$|^Agen javobini kutish$|^Awaiting Agent Response$|^Бронь забронирована$|^Rezervatsiya amalga oshirildi$|^Reservation Made$|^Иду смотреть$|^Ko'rishga boryapman$|^Going to View$|^Идет просмотр объекта$|^Ko'rilmoqda$|^Viewing Property$|^Объект просмотрен$|^Ko'rib chiqildi$|^Property Viewed$|^Результат готов$|^Natija tayyor$|^Result Ready$|^Просмотр отменен$|^Ko'rish bekor qilindi$|^Viewing Canceled$"), update_property_status_callback),
                MessageHandler(filters.Regex("^Просмотреть события$"), view_events),
                MessageHandler(filters.Regex("^Добавить событие$"), add_event_callback),
                MessageHandler(filters.Regex("^Удалить событие$"), delete_event_callback),
                MessageHandler(filters.Regex("^Назад$"), back_to_actions_callback),  # Обычная кнопка "Назад"

            ],
            CHANGE_PAYMENT_STATUS: [
                MessageHandler(filters.Regex("^Оплачено$|^To'langan$|^Paid$|^Не оплачено$|^To'lanmagan$|^Unpaid$"), update_payment_status),
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), request_order_number)
            ],
            TASKS: [
                MessageHandler(filters.Regex("^[0-9]+ - "), update_task_status),
                MessageHandler(filters.Regex("^Выполнено$|^Bajarildi$|^Completed$|^Не выполнено$|^Bajarilmadi$|^Not Completed$|^Выполняется$|^Bajarilmoqda$|^In Progress$"), save_task_status),
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), request_order_number)  # Return to ORDER_ACTIONS state
            ],
            PROPERTIES: [
                MessageHandler(filters.Regex("^[0-9]+ - "), update_task_status_callback),
                MessageHandler(filters.Regex("^Ожидание ответа агента$|^Agen javobini kutish$|^Awaiting Agent Response$|^Бронь забронирована$|^Rezervatsiya amalga oshirildi$|^Reservation Made$|^Иду смотреть$|^Ko'rishga boryapman$|^Going to View$|^Идет просмотр объекта$|^Ko'rilmoqda$|^Viewing Property$|^Объект просмотрен$|^Ko'rib chiqildi$|^Property Viewed$|^Результат готов$|^Natija tayyor$|^Result Ready$|^Выполнено$|^Bajarildi$|^Completed$|^Просмотр отменен$|^Ko'rish bekor qilindi$|^Viewing Canceled$"), update_property_status_callback),
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), request_order_number)  # Return to ORDER_ACTIONS state
            ],
            REQUEST_CLOUD_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_cloud_link)
            ],
            REQUEST_PROPERTY_CLOUD_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_property_cloud_link)
            ],
            ADD_EVENT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_event_description)
            ],
            ADD_EVENT_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_event_link),
                CallbackQueryHandler(skip_event_link, pattern='^skip$')
            ],
            DELETE_EVENT: [
                MessageHandler(filters.Regex("^[0-9]+$"), delete_event),  # Обработчик для выбора события для удаления
                MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), view_events)  # Кнопка "Назад" для возврата к списку событий
            ],
            SEND_MESSAGE_TO_USER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_message_to_user),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), admin_panel),
            CommandHandler('start', start)  # Add this line
        ],
        allow_reentry=True
    )


    feedback_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Оставить отзыв$|^📝 Fikr qoldirish$|^📝 Leave Feedback$"), feedback)],
        states={
            FEEDBACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_feedback)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), show_main_menu)],
        allow_reentry=True
    )

    likes_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^❤️ Мои лайки$|^❤️ Mening yoqtirishlarim$|^❤️ My Likes$"), show_likes)],
        states={
            NAVIGATE_RESULTS: [
                CallbackQueryHandler(navigate_results, pattern="^(next_like|prev_like|back_to_menu)$"),
                CallbackQueryHandler(like_property, pattern="^like$"),
                CallbackQueryHandler(add_property_to_cart, pattern="^add_cart_.*$"),
                CallbackQueryHandler(navigate_results, pattern="^remove_like_.*$")
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Вернуться в меню$|^Menyuga qaytish$|^Return to Menu$"), show_main_menu)],
        allow_reentry=True
    )

    cart_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🛒 Корзина$|^🛒 Savat$|^🛒 Cart$"), show_cart)],
        states={
            NAVIGATE_RESULTS: [
                CallbackQueryHandler(navigate_results, pattern="^(next_cart|prev_cart|back_to_menu|remove_cart_.*)$"),
                CallbackQueryHandler(show_cart, pattern="^cart$"),
                CallbackQueryHandler(confirm_order, pattern="^place_order$")
            ],
            CONFIRM_REMOVE: [
                CallbackQueryHandler(confirm_remove_item, pattern="^confirm_remove$"),
                CallbackQueryHandler(cancel_remove_item, pattern="^cancel_remove$")
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Вернуться в меню$|^Return to Menu$|^Menyuga qaytish$"), show_main_menu)],
        allow_reentry=True
    )

    order_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📦 Мои заказы$|^📦 Mening buyurtmalarim$|^📦 My Orders$"), show_orders)],
        states={
            ORDER: [
                MessageHandler(filters.Regex("^Заказ #\\d+$|^Buyurtma #\\d+$|^Order #\\d+$"), select_order),
                MessageHandler(filters.Regex("^🔙 Вернуться в меню$|^🔙 Menyuga qaytish$|^🔙 Return to Menu$"), show_main_menu),
            ],
            NAVIGATE_ORDERS: [
                MessageHandler(filters.Regex("^🔗 Сгенерировать ссылку$|^🔗 Havolani yaratish$|^🔗 Generate link$"), generate_share_link),  # Add this handler
                MessageHandler(filters.Regex("^📦 Мои приобретенные услуги$|^📦 Mening sotib olingan xizmatlarim$|^📦 My Purchased Services$"), show_ordered_services),
                MessageHandler(filters.Regex("^🏡 Мои запросы на недвижимость$|^🏡 Mening ko'chmas mulk so'rovlarim$|^🏡 My Property Requests$"), show_ordered_properties),
                MessageHandler(filters.Regex("^🎁 Мои бонусы$|^🎁 Mening bonuslarim$|^🎁 My Bonuses$"), show_user_bonuses),
                MessageHandler(filters.Regex("^📅 Таймлайн заказа$|^📅 Buyurtma vaqt jadvali$|^📅 Order Timeline$"), show_order_timeline),
                MessageHandler(filters.Regex("^🔙 Вернуться к заказам$|^🔙 Buyurtmalarga qaytish$|^🔙 Back to Orders$"), show_orders),
                MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Orqaga$|^🔙 Back$"), back_to_order_details),
            ],
            BONUS_ACTIONS: [
                MessageHandler(filters.Regex("^🔍 Искать недвижимость$|^🔍 Ko‘chmas mulk qidirish$|^🔍 Search Property$"), bonus_property_search),
                MessageHandler(filters.Regex("^➕ Добавить найденную недвижимость$|^➕ Topilgan ko‘chmas mulkni qo‘shish$|^➕ Add Found Property$"), add_own_property_to_order_with_bonus),
                MessageHandler(filters.Regex("^❤️ Лайки$|^❤️ Yoqtirganlar$|^❤️ Likes$"), show_bonus_likes),
                MessageHandler(filters.Regex("^🔙 Вернуться к заказам$|^🔙 Buyurtmalarga qaytish$|^🔙 Back to Orders$"), back_to_orders_from_bonuses)
            ],
            BONUS_PRICE: [
                MessageHandler(filters.Regex("^🔙 Вернуться к заказам$|^🔙 Buyurtmalarga qaytish$|^🔙 Back to Orders$"), show_user_bonuses),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bonus_price)
            ],
            BONUS_ROOMS: [
                MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Orqaga$|^🔙 Back$"), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bonus_rooms)
            ],
            BONUS_PROPERTY_TYPE: [
                MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Orqaga$|^🔙 Back$"), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bonus_property_type)
            ],
            BONUS_FURNISH: [
                MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Orqaga$|^🔙 Back$"), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bonus_furnish)
            ],
            BONUS_LIVING_TYPE: [
                MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Orqaga$|^🔙 Back$"), go_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bonus_living_type)
            ],
            BONUS_SHOW_RESULTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bonus_show_results)
            ],
            BONUS_NAVIGATE_RESULTS: [
                CallbackQueryHandler(bonus_navigate_results, pattern="^(next|prev)$"),
                CallbackQueryHandler(add_property_to_order, pattern="^add_to_order$"),
                CallbackQueryHandler(back_to_bonuses, pattern="^back_to_bonuses$")
            ],
            BONUS_LIKES: [
                CallbackQueryHandler(show_bonus_liked_property, pattern="^(next_bonus_like|prev_bonus_like)$"),
                CallbackQueryHandler(add_property_to_order_from_likes, pattern="^add_to_order_.*$"),
                CallbackQueryHandler(delete_bonus_like, pattern="^delete_bonus_like_.*$"),
                CallbackQueryHandler(back_to_bonuses, pattern="^back_to_bonuses$"),
                MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Orqaga$|^🔙 Back$"), back_to_orders_from_bonuses),
            ],
            LOAD_PROPERTY_LINK: [
                MessageHandler(filters.Regex("^🔙 Вернуться к бонусам$|^🔙 Bonuslarga qaytish$|^🔙 Back to Bonuses$"), back_to_bonuses_from_property_link),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bonus_save_property_link)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^🔙 Вернуться в меню$|^🔙 Menyuga qaytish$|^🔙 Return to Menu$"), show_main_menu)],
        allow_reentry=True
    )

    info_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^ℹ️ О чем нужно знать$|^ℹ️ Nima bilish kerak$|^ℹ️ What to Know$"), show_info_menu)],
        states={
            INFO: [
                MessageHandler(filters.Regex("^💡 Что этот бот умеет$|^💡 Ushbu bot nima qila oladi$|^💡 What this bot can do$"), show_bot_features),
                MessageHandler(filters.Regex("^ℹ️ Полезная информация$|^ℹ️ Foydali ma'lumot$|^ℹ️ Useful Information$"), show_useful_info),
                MessageHandler(filters.Regex("^🔙 Назад$|^🔙 Orqaga$|^🔙 Back$"), show_main_menu)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), show_main_menu)],
        allow_reentry=True
    )

    load_property_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔗 Добавить найденную недвижимость$|^🔗 Topilgan ko'chmas mulkni qo'shish$|^🔗 Add Found Property$"), load_property_link)],
        states={
            LOAD_PROPERTY_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_property_link)]
        },
        fallbacks=[MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), show_main_menu)],
        allow_reentry=True
    )

    main_menu_handler = MessageHandler(filters.Regex("^Главное меню$|^Asosiy menyu$|^Main Menu$"), show_main_menu)
    services_handler = services_conversation_handler()
    
    application.add_handler(registration_handler)
    application.add_handler(property_search_handler)
    application.add_handler(profile_handler)
    application.add_handler(admin_handler)
    application.add_handler(feedback_handler)
    application.add_handler(likes_handler)
    application.add_handler(cart_handler)
    application.add_handler(services_handler)
    application.add_handler(order_handler)
    application.add_handler(info_handler)
    application.add_handler(load_property_handler)
    application.add_handler(main_menu_handler)
    application.add_handler(linked_orders_handler)


    application.add_handler(CallbackQueryHandler(confirm_remove_item, pattern="^confirm_remove_.*$"))
    application.add_handler(CallbackQueryHandler(cancel_remove_item, pattern="^cancel_remove$"))
    application.add_handler(CallbackQueryHandler(navigate_results, pattern="^(next_like|prev_like|back_to_menu|next_cart|prev_cart|remove_cart_.*|remove_like_.*)$"))
    application.add_handler(CallbackQueryHandler(like_property, pattern="^like$"))
    application.add_handler(CallbackQueryHandler(add_property_to_cart, pattern="^cart$"))
    application.add_handler(CallbackQueryHandler(confirm_removal, pattern="^confirm_remove_.*$"))
    application.add_handler(CallbackQueryHandler(remove_item_from_cart, pattern="^remove_cart_.*$"))
    application.add_handler(CallbackQueryHandler(remove_item_from_likes, pattern="^remove_like_.*$"))
    application.add_handler(CallbackQueryHandler(update_order_status_callback, pattern="^update_status_.*$"))
    application.add_handler(CallbackQueryHandler(update_task_status_callback, pattern="^update_task_.*$"))
    application.add_handler(CallbackQueryHandler(set_task_status, pattern="^set_task_status_.*$"))
    application.add_handler(CallbackQueryHandler(update_task_status_handler, pattern="^update_task_.*$"))
    application.add_handler(CallbackQueryHandler(select_task_status, pattern="^select_task_status_.*$"))
    application.add_handler(CallbackQueryHandler(show_order_tasks, pattern="^show_tasks_.*$"))
    application.add_handler(CallbackQueryHandler(back_to_task_status, pattern="^back_to_task_status_.*$"))
    application.add_handler(CallbackQueryHandler(show_order_admin_menu, pattern="^show_order_admin_menu_.*$"))
    application.add_handler(CallbackQueryHandler(confirm_order, pattern="^confirm_order$"))
    application.add_handler(CallbackQueryHandler(confirm_order_yes, pattern="^confirm_order_yes$"))
    application.add_handler(CallbackQueryHandler(confirm_order_no, pattern="^confirm_order_no$"))
    application.add_handler(CallbackQueryHandler(update_property_status_handler, pattern="^update_property_status_.*$"))
    application.add_handler(CallbackQueryHandler(show_order_properties, pattern="^show_properties_.*$"))
    application.add_handler(CallbackQueryHandler(add_property_to_order, pattern="^add_to_order$"))
    application.add_handler(CallbackQueryHandler(back_to_bonuses, pattern="^back_to_bonuses$"))
    application.add_handler(CommandHandler('start', show_main_menu))  
    application.add_handler(MessageHandler(filters.Regex("^Главное меню$|^Asosiy menyu$|^Main Menu$"), show_main_menu))
    application.add_handler(MessageHandler(filters.Regex("^🔙 Вернуться в меню$|^🔙 Menyuga qaytish$|^🔙 Return to Menu$"), show_main_menu))
    application.add_handler(MessageHandler(filters.Regex("^Назад$|^Orqaga$|^Back$"), show_main_menu))
    application.add_handler(MessageHandler(filters.Regex("^📞 Контакты$|^📞 Kontaktlar$|^📞 Contacts$"), show_contacts))   
    application.add_handler(MessageHandler(filters.Regex("^📄 Оферта$|^📄 Oferta$|^📄 Terms and Conditions$"), show_offer))
    application.add_handler(MessageHandler(filters.Regex("^🔙 Назад к деталям заказа$|^🔙 Buyurtma tafsilotlariga qaytish$|^🔙 Back to order details$"), back_to_order_details))
    application.add_handler(MessageHandler(filters.Regex("^🔙 Вернуться к деталям$|^🔙 Buyurtma tafsilotlari$|^🔙 Back to details$"), linked_back_to_order_details))    
    application.add_handler(CallbackQueryHandler(bonus_show_property, pattern="^bonus_like_.*$"))
    application.add_handler(CallbackQueryHandler(handle_payment_choice, pattern="^(pay_later|confirm_payment)$"))
    application.add_handler(CallbackQueryHandler(handle_registration_start, pattern='^start_registration$'))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    application.run_polling()

if __name__ == '__main__':
    main()