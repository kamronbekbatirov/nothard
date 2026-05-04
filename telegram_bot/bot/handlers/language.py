# bot/handlers/language.py
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


MESSAGES = {
    'ru': {
        'invoice_link_message': "Пожалуйста, оплатите заказ, перейдя по [ссылке]({invoice_link}).",
        'invoice_creation_error': "Ошибка при создании ссылки на инвойс.",

        'new_admin_message': (
            "❗ Дорогой клиент, 👋\n\n"
            "Вы получили новое сообщение по заказу #{order_id}. 📨\n\n"
            "Сообщение от администратора: 📝\n"
            "{message_text}\n\n"
        ),

        # subscribe.py
        'orders_generate_share_link': '🔗 Сгенерировать ссылку',
        'orders_share_link_generated': 'Ссылка на ваш заказ была сгенерирована: {share_link}',

        # Сообщения без вставки order_id
        'subscription_success_unregistered': "🎉 Вы успешно привязали заказ. Теперь вы сможете получить доступ к заказу после завершения регистрации, пройдя в главное меню и нажав на «🔖 Привязанные заказы».",
        'already_subscribed_registered': 'Вы уже привезали этот заказ к своему аккаунту. Вы можете просмотреть его пройдя в главном меню, и нажав на «🔖 Привязанные заказы».',
        'subscription_success_registered': '🎉 Вы успешно привязали заказ. Вы можете просмотреть его пройдя в главном меню, и нажав на «🔖 Привязанные заказы».',
        'already_subscribed_unregistered': (
                    "🇷🇺 Вы уже привязаны к заказу. Пожалуйста, завершите регистрацию, чтобы получить доступ к заказу.\n\n"
                    "Чтобы начать регистрацию, введите команду «/start».\n\n"
                    "🇺🇿 Buyurtmaga allaqachon bog'langansiz. Iltimos, buyurtmaga kirish uchun ro'yxatdan o'tishni yakunlang.\n\n"
                    "Ro'yxatdan o'tishni boshlash uchun «/start» buyrug'ini kiriting.\n\n"
                    "🇬🇧 You are already subscribed to the order. Please complete the registration to access the order.\n\n"
                    "To start the registration, please enter the command «/start»."
        ),
        'shareable_link_message': 'Вот ссылка, по которой вы можете поделиться с кем угодно. Эта ссылка позволит им видеть ваш заказ и отслеживать статус приобретенных услуг.',

        'start_registration': 'Начать регистрацию',
        'invalid_link': 'Неверная ссылка',

        'linked_orders': '🔖 Привязанные заказы',
        'change_language': '🌐 Изменить язык',
        'select_language_prompt': 'Выберите язык',


        'linked_orders_no_orders': "У вас нет привязанных заказов.",

        'orders_remove_order': '❌ Отвязать заказ',
        'orders_order_unlinked': 'Заказ был успешно отвязан.',

        'orders_confirm_unlink': 'Точно ли вы хотите отвязать этот заказ от себя?',
        'order_unlinked_part1': 'Заказ',
        'order_unlinked_part2': 'был отвязан.',
        'yes': '✅ Да',
        'no': '❌ Нет',
        'orders_canceled_unlink': 'Отвязка заказа отменена.',
        'orders_invalid_input': 'Пожалуйста, выберите "✅ Да" или "Нет".',

        'view_subscribe_properties_info': "Для просмотра статуса заказа на недвижимость привязанного заказа перейдите в главное меню, затем нажмите на '🔖 Привязанные заказы', выберите нужный номер заказа и нажмите на '🏡 Мои запросы на недвижимость'.",
        'view_subscribe_tasks_info_message': "Для просмотра статуса всех задач привязанного заказа перейдите в главное меню, затем нажмите на '🔖 Привязанные заказы', выберите нужный номер заказа и нажмите на '📦 Мои приобретенные услуги'.",
        'view_bonus_tasks_properties_info': "Для просмотра статуса привязанного заказа перейдите в главное меню, затем нажмите на '🔖 Привязанные заказы', выберите нужный номер заказа и нажмите на '🏡 Мои запросы на недвижимость'.",
        'order_subscribe_status_view_orders_info': "Для просмотра статуса привязанного заказа перейдите в главное меню, затем нажмите на '🔖 Привязанные заказы', выберите нужный номер заказа.",
        'view_subscribe_events_info_message': "Для просмотра всех событий привязанного заказа перейдите в главное меню, затем нажмите на '🔖 Привязанные заказы', выберите нужный номер заказа и нажмите на '📅 Таймлайн заказа'.",
        'view_user_events_info_message': "Для просмотра всех событий вашего заказа перейдите в главное меню, затем нажмите на '📦 Мои заказы', выберите нужный номер заказа и нажмите на '📅 Таймлайн заказа'.",


        'payment_subscribe_status_updated': "Дорогой клиент, статус оплаты привязанного заказа #{order_id} был обновлен на '{status}'.\n\nДля просмотра статуса привязоного заказа перейдите в главное меню, затем нажмите на '🔖 Привязанные заказы', выберите Заказ #{order_id}.",

        'orders_timeline': "📅 Таймлайн заказа",

        'event_enter_description': "Введите описание события:",
        'event_enter_link_optional': "Введите ссылку на результат (необязательно):",
        'event_added_success': "Событие успешно добавлено в таймлайн заказа.",
        'skip': "Пропустить",

        'orders_no_timeline_events': "В таймлайне заказа нет событий.",


        'event_added_to_order_part1': "📢 Дорогой клиент, к вашему заказу №",
        'event_added_to_order_part1_subscriber': "📢 Дорогой клиент, к привязанному заказу №",

        'event_added_to_order_part2': "было добавлено событие:",


        'event_added_to_order': "Дорогой клиент, к вашему заказу №{order_id} было добавлено событие:",
        'event_description': "Описание события",
        'event_timestamp': "Когда это произошло",
        'event_link': "Ссылка для просмотра",

        "bonus_received_message": "💡 Вы получили 1 бонусный балл, который можете использовать для добавления другой недвижимости в заказ.",
        "bonus_usage_instructions": "Для того чтобы воспользоваться бонусом, перейдите в главное меню, затем нажмите на '📦 Мои заказы', выберите нужный номер заказа и нажмите на '🎁 Мои бонусы'.",

        # addproperty.py
        'load_property_link_prompt': (
            "Если вы нашли подходящий вариант недвижимости на другом сайте, вы можете добавить его в корзину. "
            "Просто отправьте ссылку на страницу с этой недвижимостью в чат.\n\n"
            "Если вы еще не нашли то, что вам нужно, вы можете воспользоваться нашей функцией «🏡 Поиск недвижимости» для поиска вариантов."
        ),
        'link_added_success': "Ссылка на найденную недвижимость успешно добавлена в корзину!",
        'not_a_link': "Ваше сообщение не зарегистрировано как ссылка на недвижимость.",
        'link_save_error': "Произошла ошибка при сохранении ссылки. Попробуйте еще раз.",
        'back_link': "Назад",

        # oferta.py
        "offer_view": "Посмотреть публичную оферту",
        "offer_message": "Вы можете ознакомиться с публичной офертой, нажав на кнопку ниже:",

        # common.py
        'main_menu': "Главное меню:",
        'search_property': "🏡 Поиск недвижимости",
        'add_found_property': "🔗 Добавить найденную недвижимость",
        'my_likes': "❤️ Мои лайки",
        'cart': "🛒 Корзина",
        'our_services': "💠 Наши Услуги",
        'my_orders': "📦 Мои заказы",
        'profile_menu': "👤 Профиль / 🌐 Языки",
        'contacts': "📞 Контакты",
        'what_to_know': "ℹ️ О чем нужно знать",
        'leave_feedback': "📝 Оставить отзыв",
        'offer': "📄 Оферта",
        'admin_panel': "⚙️ Админка",

        # admin.py

        'payment_method_cash': 'Наличные',
        'dear_client': 'Дорогой клиент',
        'order_status_order_status_update': 'статус вашего заказа',
        'order_status_order_status_update_subscriber': 'статус привязанного заказа',
        'order_status_status_updated_to': 'был обновлен на',
        'order_status_view_orders_info': "Для просмотра статуса вашего заказа перейдите в главное меню, затем нажмите на '📦 Мои заказы', выберите нужный номер заказа.",
        
        # Статусы заказа
        'order_status_accepted_message': "Ваш заказ принят и находится в обработке.",
        'order_status_returned_message': "Ваш заказ был возвращен.",
        'order_status_cancelled_message': "Ваш заказ был отменен.",
        'order_status_pending_message': "Ваш заказ находится в ожидании.",
        'order_status_waiting_payment_message': "Ваш заказ ожидает оплаты.",
        'order_status_in_progress_message': "Ваш заказ выполняется.",
        'order_status_completed_message': "Ваш заказ был выполнен.",
        'order_status_accepted': 'Принят',
        'order_status_returned': 'Возврат',
        'order_status_cancelled': 'Отменен',
        'order_status_pending': 'Ожидание',
        'order_status_waiting_payment': 'Ожидание оплаты',
        'order_status_in_progress': 'Выполняется',
        'order_status_completed': 'Выполнен',

        'payment_paid': 'Оплачено',
        'payment_not_paid': 'Не оплачено',
        'payment_status_updated': "Дорогой клиент, статус оплаты вашего заказа #{order_id} был обновлен на '{status}'.\n\nДля просмотра статуса вашего заказа перейдите в главное меню, затем нажмите на '📦 Мои заказы', выберите Заказ #{order_id}.",
        'payment_status_updated_subscriber': "Дорогой клиент, статус оплаты привязанного заказа #{order_id} был обновлен на '{status}'.\n\nДля просмотра статуса привязоного заказа перейдите в главное меню, затем нажмите на '🔖 Привязанные заказы', выберите Заказ #{order_id}.",
        'order_status_Оплачено': 'Оплачено',

        'payment_successful': "Ваш платеж за заказ №{order_id} успешно завершен. Спасибо за покупку!",
        'payment_error': "Произошла ошибка при обработке платежа. Пожалуйста, попробуйте снова.",

        'reservation_date_message': "Дата и время просмотра",

        'property_status_waiting_agent': 'В данный момент мы ждём ответа от агентства, которое владеет выбранной вами недвижимостью.',
        'property_status_booked': 'Мы связались с агентом и назначили день для просмотра данной недвижимости.',
        'property_status_going': 'Агент направляется к недвижимости для проведения просмотра.',
        'property_status_in_progress': 'Агент проводит фото - и видеосъёмку объекта.',
        'property_status_viewed': 'Агент завершил просмотр и скоро поделится материалами с вами.',
        'property_status_ready': 'Спасибо за ожидание. Мы прикладываем фото - и видеообзоры для вашего просмотра.',
        'property_status_cancelled': 'К сожалению, просмотр вашей недвижимости был отменён.',
        'view_properties_info': "Для просмотра статусов всех запросов на недвижимость перейдите в главное меню, затем нажмите на '📦 Мои заказы', выберите нужный номер заказа и нажмите на '🏡 Мои запросы на недвижимость'.",

        'dear_client': 'Дорогой клиент',
        'property_status_update': 'статус вашей недвижимости',
        'from_order': 'из заказа',
        'from_order_subscriber': 'из привязанного заказа',

        'status_updated_to': 'был обновлен на',
        'property_added_by_user': 'Недвижимость, добавленная пользователем',

        'task_status_completed': 'Выполнено',
        'task_status_not_completed': 'Не выполнено',
        'task_status_in_progress': 'Выполняется',

        'task_status_status': "Cтатус задачи или услуги",
        'task_status_in_order': "из заказа",
        'task_status_has_been_updated': "был обновлен на",
        'task_status_completed_message': "Задача успешно завершена.",
        'task_status_not_completed_message': "Задача не была выполнена. Если вы считаете, что задача должна была быть выполнена, свяжитесь с нами [тут](t.me/nothardchat).",
        'task_status_in_progress_message': "Задача находится в процессе выполнения. Мы сообщим вам о её завершении.",
        'view_tasks_info_message': "Для просмотра статусов всех задач перейдите в главное меню, затем нажмите на '📦 Мои заказы', выберите нужный номер заказа и нажмите на '📦 Мои приобретенные услуги'.",

        'cloud_link_message': "Ссылка на результат",

        'save_property_dear_client': "Дорогой клиент,",
        'save_property_status_update_prefix': "Статус вашей недвижимости",
        'save_property_in_order': "из заказа",
        'save_property_has_been_updated_to': "был обновлен на",
        'save_property_cancellation_reason': "Причина отмены",
        'save_property_bonus_received_message': "💡 Вы получили 1 бонусный балл, который можете использовать для добавления другой недвижимости в заказ.",
        'save_property_view_bonuses_info': "Для этого перейдите в главное меню, затем нажмите на '📦 Мои заказы', выберите нужный номер заказа и нажмите на '🎁 Мои бонусы'.",
        'save_property_status_changed_to': "Статус изменен на",
        'save_property_reason': "Причина",
        'save_property_result_link_saved_for_property': "Ссылка на результат для недвижимости",
        'save_property_link': "Ссылка на результат",
        'save_property_result_link_saved': "Ссылка на результат сохранена для недвижимости",

        'view_tasks_intro': "Для просмотра всех задач перейдите в главное меню, нажмите '📦 Мои заказы', выберите заказ",
        'view_tasks_instruction': "затем перейдите в '🏡 Мои запросы на недвижимость",

        
        'provide_result_link': "Пожалуйста, отправьте ссылку на результат для недвижимости",

        # contacts.py
        'contact_info': (
        "Связь с поддержкой онлайн 24/7:\n"
        "Telegram: [t.me/nothardchat](http://t.me/nothardchat)\n"
        "Email: helpme@nothard.uz\n"
        "Телефон - Ташкент: +998 88 089 89 10 (Временно не доступен)\n"
        "Телефон - Лондон: +44 7990 381454\n"
        ),

        # feedback.py
        "feedback_back": "🔙 Назад",
        "feedback_please_leave": "Пожалуйста, оставьте свой отзыв:",
        "feedback_thank_you": "Спасибо за ваш отзыв!",
        "feedback_not_registered": "Ваше сообщение не зарегистрировано как отзыв.",

        # orders.py
        'orders_no_orders': "У вас нет заказов.",

        'orders_select_order': "Выберите заказ:",
        'orders_order': "Заказ",
        'orders_back_to_menu': "🔙 Вернуться в меню",

        'orders_payment_cash': "Наличные 💵",
        'orders_payment_payme': "PayMe 💳",
        'orders_payment_not_specified': "Не указан",
        'orders_paid': "Оплачено ✅",
        'orders_not_paid': "Не оплачено ❌",
        'orders_details': (
            "📝 Детали заказа: \\#{order_id}\n"
            "📅 Дата и Время: {order_date}\n"
            "📦 Статус: {status}\n"
            "💰 Метод оплаты: {payment_method}\n"
            "💳 Статус оплаты: {payment_status}"
        ),

        'orders_subscriber_purchased_services': "📦 Приобретенные услуги",
        'orders_subscriber_property_requests': "🏡 Запросы на недвижимость",


        'orders_my_purchased_services': "📦 Мои приобретенные услуги",
        'orders_my_property_requests': "🏡 Мои запросы на недвижимость",

        'orders_my_bonuses': "🎁 Мои бонусы",
        'orders_back_to_orders': "🔙 Вернуться к заказам",

        'orders_user_added_property': '🏠 Недвижимость, добавленная пользователем',
        'orders_status': 'Статус',
        'orders_result_ready': 'Результат готов',
        'orders_view_cancelled': 'Просмотр отменен',
        'orders_cancellation_reason': 'Причина отмены',
        'orders_report': 'Отчет',
        'orders_property_name': 'Название',
        'orders_price': 'Цена',
        'orders_address': 'Адрес',
        'orders_not_available': 'N/A',
        'orders_no_properties': 'У вас нет арендованной недвижимости.',
        'orders_back': '🔙 Назад',
        'orders_link': 'Ссылка',

        'orders_order_not_found': "Ошибка: Заказ не найден.",
        'orders_in_progress': "Выполняется",
        'orders_not_completed': "Не выполнено",
        'orders_completed': "Выполнено",
        'orders_package': "Пакет",
        'orders_package_status': "Статус пакета",
        'orders_no_services': "У вас нет приобретенных услуг.",

        'orders_document_translation_service': "📄 Перевод документов",
        'orders_lease_agreement_assistance_service': "📜 Перевод и помощь с подписанием договора аренды",
        'orders_airport_pickup': "✈️ Встреча в аэропорту",
        'orders_transport_to_residence': "🚌 Транспорт до места проживания",
        'orders_sim_card_assistance': "📱 Помощь с подключением SIM-карты",
        'orders_oyster_card_assistance': "🎫 Получение Oyster-карты",
        'orders_regular_reports_to_parents': "📧 Регулярные отчеты родителям",
        'orders_housing_search': "🔍 Поиск и подбор вариантов жилья",
        'orders_area_consultation': "📍 Консультация по выбору района для проживания",
        'orders_apartment_viewing': "🏢 Организация просмотра квартир",
        'orders_temporary_housing_assistance': "🏨 Помощь с временным жильем на первые дни",
        'orders_moving_assistance': "🚚 Перевозка вещей",

        'in_progress': "🔄",
        'not_completed': "❌",
        'completed': "✅",

        'orders_bonuses_one_available': "🎁 У вас есть 1 бесплатное добавление недвижимости.",
        'orders_bonuses_multiple_available': "🎁 У вас есть {bonuses} бесплатных добавлений недвижимости.",
        'orders_no_bonuses_available': "❌ У вас нет доступных бонусов.",
        'orders_search_property': "🔍 Искать недвижимость",
        'orders_add_found_property': "➕ Добавить найденную недвижимость",
        'orders_likes': "❤️ Лайки",
        'orders_back_to_orders': "🔙 Вернуться к заказам",


        'bonus_zone_1': "Зона 1",
        'bonus_zone_2': "Зона 2",
        'bonus_zone_3': "Зона 3",
        'bonus_zone_4': "Зона 4",
        'bonus_zone_5': "Зона 5",
        'bonus_zone_6': "Зона 6",
        'bonus_zone_unknown': "Я не знаю",
        'bonus_property_search_waiting': "Подождите немного, мы запускаем поиск недвижимости...",
        'bonus_select_zone': "Выберите зону проживания:",


        'bonus_enter_max_price': "Укажите максимальную сумму в фунтах, которую вы готовы потратить в месяц. Введите только цифры, без символов (например, 1500):",
        'bonus_select_rooms': "Сколько комнат вы хотите?",

        'bonus_studio': "Студия",
        'bonus_unknown': "Я не знаю",
        'bonus_back': "🔙 Назад",
        'bonus_select_property_type': "Какой тип недвижимости вас интересует?",
        'bonus_flat': "Квартира",
        'bonus_house': "Дом",
        'bonus_student_housing': "Студенческое общежитие",
        'bonus_furnish_question': "Должно ли жилье быть меблированным?",
        'bonus_furnished': "Меблированное",
        'bonus_unfurnished': "Без мебели",
        'bonus_part_furnished': "Частично меблированное",
        'bonus_living_type_question': "Хотите ли вы видеть варианты с совместным проживанием (House Share)?",
        'bonus_show_house_share': "Да, показывать House Share",
        'bonus_dont_show_house_share': "Нет, не показывать House Share",

        'bonus_no_results': "Не удалось найти подходящих вариантов.",
        'bonus_main_menu': "Главное меню",

        'bonus_property_liked': "Объект добавлен в лайки!",
        'bonus_no_properties_found': "Не удалось найти подходящих вариантов.",
        'bonus_not_available': "N/A",
        'bonus_price': "Цена",
        'bonus_address': "Адрес",
        'bonus_link': "Ссылка",
        'bonus_of': "из",
        'bonus_prev': "⬅️ Назад",
        'bonus_next': "Вперед ➡️",
        'bonus_like': "Лайкнуть",
        'bonus_add_to_order': "Добавить в заказ",
        'bonus_back_to_bonuses': "Вернуться к бонусам",

        'bonus_order_not_found': "Ошибка: заказ не найден.",
        'bonus_no_properties_available': "Ошибка: нет доступных объектов для добавления.",
        'bonus_no_bonuses_left': "У вас не осталось бонусов для добавления недвижимости в заказ.",
        'bonus_property_added': "Недвижимость добавлена в заказ, и один бонус был списан!",
        'bonus_back_to_bonuses': "🔙 Вернуться к бонусам",
        'bonus_enter_property_link': "Пожалуйста, введите ссылку на найденную недвижимость или нажмите 'Назад', чтобы вернуться к бонусам.",

        'bonus_enter_property_link': "Пожалуйста, отправьте ссылку на найденную недвижимость.",
        'bonus_property_link_added': "Ссылка на найденную недвижимость успешно добавлена в заказ, и один бонус был списан!",
        'bonus_order_not_found': "Ошибка: заказ не найден.",
        'bonus_unexpected_link': "Ошибка: бот не ожидал получения ссылки.",
        'bonus_link_save_error': "Произошла ошибка при сохранении ссылки. Попробуйте еще раз.",

        'bonus_no_likes': "У вас нет понравившихся объектов, добавленных через бонусы.",
        'bonus_not_available': "N/A",
        'bonus_price': "Цена",
        'bonus_address': "Адрес",
        'bonus_link': "Ссылка",
        'bonus_of': "из",
        'bonus_prev': "⬅️ Назад",
        'bonus_next': "Вперед ➡️",
        'bonus_add_to_order': "Добавить в заказ",
        'bonus_delete_like': "🗑️ Удалить",
        'bonus_back_to_bonuses': "🔙 Вернуться к бонусам",

        'bonus_invalid_index': "Ошибка: Неверный индекс.",
        'bonus_no_bonuses_left': "У вас не осталось бонусов для добавления недвижимости в заказ.",
        'bonus_property_added_from_likes': "Недвижимость успешно добавлена в заказ! Один бонусный балл списан.",
        'bonus_like_deleted': "Объект удален из лайков!",

        'bonus_select_zone': "Выберите зону проживания:",
        'bonus_enter_price': "Укажите максимальную сумму в фунтах, которую вы готовы потратить в месяц. Введите только цифры, без символов (например, 1500):",
        'bonus_how_many_rooms': "Сколько комнат вы хотите?",
        'bonus_select_property_type': "Какой тип недвижимости вас интересует?",
        'bonus_furnish': "Должно ли жилье быть меблированным?",

        # info.py
        "info_choose_info": "Выберите, что вы хотите узнать:",
        "info_bot_features": "💡 Что этот бот умеет",
        "info_useful_info": "ℹ️ Полезная информация",
        "info_back": "🔙 Назад",
        "info_features_message": (
            "❓ *Что этот бот умеет*\n\n"
            "1. 🏡 *Поиск недвижимости*: Бот предложит вам подходящие варианты. "
            "Вы можете просматривать, лайкать и добавлять объекты в корзину для оформления заказа.\n\n"
            "2. 🔗 *Добавить найденную недвижимость*: Если вы нашли объект на другом сайте, просто отправьте ссылку, и бот добавит её в корзину.\n\n"
            "3. ❤️ *Мои лайки*: Сохранённые вами объекты недвижимости, которые вы лайкнули.\n\n"
            "4. 🛒 *Корзина*: Все товары и услуги, которые вы собрали, будут храниться здесь для оформления заказа.\n\n"
            "5. 💠 *Наши Услуги*: Здесь вы найдёте наши пакеты услуг и индивидуальные услуги, которые можно добавить в корзину.\n\n"
            "6. 📦 *Мои заказы*: Здесь вы можете отслеживать свои заказы, просматривать статусы и использовать бонусы, если они доступны.\n\n"
            "7. 🔖 *Привязанные заказы*: Здесь отображаются заказы, которыми с вами поделились другие пользователи. Вы можете просматривать приобретённые услуги и детали заказа.\n\n"
            "8. 👤 *Профиль*: Управляйте своими личными данными, такими как имя, телефон и email.\n\n"
            "9. 📞 *Контакты*: Информация о том, как с нами связаться.\n\n"
            "10. 📝 *Оставить отзыв*: Поделитесь своими впечатлениями о нашем сервисе.\n\n"
            "11. ℹ️ *О чём нужно знать*: Важные советы и информация, которые помогут вам при поиске недвижимости.\n\n"
            "12. 📄 *Оферта*: Ознакомьтесь с нашей публичной офертой."
        ),
        "info_useful_info_message": (
            "ℹ️ *Полезная информация*\n\n"
            "1. Многие владельцы недвижимости в Лондоне требуют предоставления гаранторов, если вы иностранный гражданин. "
            "Если у вас нет гарантора, вам нужно будет предоставить предоплату за 6 месяцев. Это не касается общежитий.\n\n"
            "2. Общежития не требуют гаранторов, но многие требуют предоплату за 3 месяца и оплату ежеквартально или по семестрам.\n\n"
            "3. При аренде жилья через агентства могут потребоваться дополнительные документы, такие как подтверждение дохода, трудовой договор и банковские выписки.\n\n"
            "4. Всегда проверяйте условия аренды и узнавайте о всех дополнительных платежах, таких как счета за коммунальные услуги и интернет.\n\n"
            "5. При подписании договора аренды убедитесь, что все условия ясны и записаны в договоре, включая сроки аренды, условия оплаты и правила проживания.\n\n"
            "6. При поиске жилья используйте проверенные сайты и агентства, чтобы избежать мошенничества.\n\n"
            "7. Ознакомьтесь с районами, где вы планируете жить, чтобы убедиться, что они соответствуют вашим требованиям по безопасности, инфраструктуре и удобствам.\n\n"
            "8. Если у вас есть вопросы или проблемы с арендой, обращайтесь за помощью к юристам или в организации по защите прав арендаторов."
        ),

        # profile.py
        'profile_not_found': "Профиль не найден. Пожалуйста, зарегистрируйтесь.",
        'profile_account': "Ваш профиль:\n{profile}",
        'edit_name': "✏️ Изменить имя",
        'edit_phone': "📞 Изменить телефон",
        'edit_email': "✉️ Изменить email",
        'edit_language': "🌐 Изменить язык",
        'profile_name': "Имя",
        'profile_phone': "Телефон",
        'profile_email': "Email",
        'enter_new_value': "Введите новое значение для {field}:",
        'profile_language': "Язык",
        'back_profile': "🔙 Назад",
        'updated': "обновлено",
        'incorrect_language_selection': "Пожалуйста, выберите язык из предложенных вариантов.",
        'select_language_prompt': "Выберите язык:",
        'registration': "Регистрация",
        'incorrect_field': "Некорректное поле. Пожалуйста, выберите снова.",
        'field_updated': "{field} обновлено.",

        # property_search.py
        'property_search_started': "Подождите немного, мы запускаем поиск недвижимости...",
        'property_choose_zone': "Выберите зону проживания:",
        'property_enter_max_price': "Укажите максимальную сумму в фунтах, которую вы готовы потратить в месяц. Введите только цифры, без символов (например, 1500):",
        'property_enter_room_count': "Сколько комнат вы хотите?",
        'property_choose_property_type': "Какой тип недвижимости вас интересует?",
        'property_should_furnished': "Должно ли жилье быть меблированным?",
        'property_house_share_option': "Хотите ли вы видеть варианты с совместным проживанием (House Share)?\n\n1. Да — показывать варианты с House Share.\n2. Нет — показывать только варианты, где проживание только для вас.",
        'property_results_not_found': "Не удалось найти подходящих вариантов.",
        'property_added_to_likes': "Мы добавили объект в ваш список понравившихся!",
        'property_added_to_cart': "Недвижимость добавлена в корзину!",
        'property_no_properties_in_cart': "Нет доступных объектов для добавления в корзину.",
        'property_likes_empty': "У вас нет понравившихся объектов.",
        'property_cart_empty': "Ваша корзина пуста.",
        'property_order_confirmed': "Спасибо за оплату! Ваш заказ подтвержден.",
        'property_order_placed': "Ваш заказ оформлен! Спасибо за ваш заказ.",
        'property_order_cancelled': "Ваш заказ был отменен.",
        'property_order_status_updated': "Статус заказа обновлен на '{status}'",
        'property_back_to_main_menu': "Вернуться в меню",
        'property_delete_property_confirmation': "Вы уверены, что хотите удалить {item} из корзины?",
        'property_removed': "Элемент успешно удален.",
        'property_removal_cancelled': "Удаление отменено.",
        'property_basket_summary': "Корзина\n\n{summary}",
        'property_order_details': "Детали заказа\n\n{details}\n\nОплата: {payment_method}\nИтого: {total_price}$",
        'property_place_order_confirmation': "Сумма заказа: {total_price}$\n💳 Оплата через PayMe принимается только картами Uzcard и Humo.\nЕсли вы хотите оплатить с помощью Visa, MasterCard или других карт, выберите опцию 'Оплата наличными'. Наш менеджер свяжется с вами.",
        'property_new_order_notification': "Новый заказ от пользователя: {details}",
        'payme_payment_url': "Ссылка для оплаты через PayMe: {payme_url}",
        'property_search_back_to_menu': "🔙 Вернуться в меню",
        'property_search_go_back': "⬅️ Назад",
        'property_search_next': "Вперед ➡️",
        'property_search_like': "❤️ Лайк",
        'property_search_add_to_cart': "🛒 Корзина",
        'property_property': "🏡 *Недвижимость*",
        'property_price': "💷 *Цена*",
        'property_address': "📍 *Адрес*",
        'property_link': "🔗 Посмотреть объект",
        'property_out_of': "из",

        'property_summary_count': "Просмотр {count} объектов",
        'property_included_in_package': "включено в пакет",
        'property_additional_views': "дополнительных просмотров",
        'property_search_delete': "🗑️ Удалить",

        'payment_method': "Метод оплаты",

        'bonus_show_property': "🏡 *Недвижимость:* {title}\n💰 *Цена:* {price}\n📍 *Адрес:* {address}\n🔗 [Посмотреть объект]({link})\n\nОбъект {current_index} из {total_properties}",
        
        'zone_1': "Зона 1",
        'zone_2': "Зона 2",
        'zone_3': "Зона 3",
        'zone_4': "Зона 4",
        'zone_5': "Зона 5",
        'zone_6': "Зона 6",
        'zone_unknown': "Я не знаю",
        'studio': "Студия",
        'rooms_1': "1",
        'rooms_2': "2",
        'rooms_3': "3",
        'rooms_4_plus': "4+",
        'furnished': "Меблированное",
        'unfurnished': "Без мебели",
        'part_furnished': "Частично меблированное",
        'house_share_yes': "Да, показывать House Share",
        'house_share_no': "Нет, не показывать House Share",
        'property_type_flat': "Квартира",
        'property_type_house': "Дом",
        'property_type_private_halls': "Студенческое общежитие",
        'go_back': "⬅️ Назад",
        'confirm_removal_button': "Да",
        'cancel_removal_button': "Нет",

        'cart_is_empty': "🛒 Ваша корзина пуста.",
        'cart_title': "🛒 *Корзина*\n\n",
        'property_section_title': "🏡 *Недвижимость:*",
        'no_properties_in_cart': "Нет добавленных объектов недвижимости.",
        'package_section_title': "📦 *Пакетные услуги:*",
        'individual_services_section_title': "🛠️ *Индивидуальные услуги:*",
        'no_individual_services': "Нет добавленных индивидуальных услуг.",
        'total_price': "💰 *Итого: {total_price}$*",
        'property_summary_with_extra': "Просмотр {property_count} объектов (3 включено в пакет, {extra_properties} дополнительных просмотров по 50$ каждый)",
        'property_summary_without_extra': "Просмотр {property_count} объектов (3 включено в пакет)",
        'property_summary_no_package': "Просмотр {property_count} объектов ({price}$)",
        'delete_property_button': "🗑 Удалить недвижимость: {title}",
        'delete_package_button': "🗑 Удалить пакет: {service_title}",
        'delete_service_button': "🗑 Удалить услугу: {service_title}",
        'delete_individual_service_button': "🗑 Удалить индивидуальную услугу: {service_title}",
        'place_order_button': "🛒 Оформить",
        'main_menu_button_text': "Главное меню",
        'back_to_main_menu': "Чтобы вернуться назад, нажмите 'Главное меню'",

        'property_remove_like': "Вы уверены, что хотите удалить {item} из понравившихся?",
        'property_like_removed': "Объект успешно удален из понравившихся!",
        'property_like_removal_cancelled': "Удаление отменено.",
        'property_remove_cart': "Вы уверены, что хотите удалить {item} из корзины?",
        'property_cart_item_removed': "Элемент успешно удален из корзины!",
        'property_cart_removal_cancelled': "Удаление из корзины отменено.",
        'property_add_to_cart_success': "Недвижимость добавлена в корзину!",
        'property_confirm_remove': "Да",
        'property_cancel_remove': "Нет",
        'property_error_invalid_index': "Ошибка: индекс элемента неверен.",
        'property_view': "Просмотр объекта",
        'property_remove_cart_question': "Вы уверены, что хотите удалить",
        'property_remove_cart_footer': "из корзины?",

        'confirm_check_info': "Проверьте информацию еще раз",
        'confirm_all_correct': "Все правильно",
        'confirm_agreement': "Нажимая «Да», вы соглашаетесь с условиями Публичной оферты на оказание услуг и подтверждаете правильность введенной информации.",
        'ordered_items': "Заказанные объекты",
        'package_services': "📦 Пакетные услуги",
        'individual_services': "🛠️ Индивидуальные услуги",
        'no_properties': "Нет добавленных объектов недвижимости.",
        'no_packages': "Нет добавленных пакетов.",
        'no_individual_services': "Нет добавленных индивидуальных услуг.",
        'confirm_order_yes': "Да",
        'confirm_order_no': "Нет",
        'property_view_summary': "Просмотр {property_count} объектов (3 включено в пакет, {extra_properties} дополнительных просмотров по 50$ каждый)",
        'property_view_included': "Просмотр {property_count} объектов (3 включено в пакет)",
        'property_view_individual': "Просмотр {property_count} объектов (50$ каждый)",

        'payme_button': "Оплатить через PayMe ({total_price_in_sums} сум)",
        'cash_payment_button': "Оплатить наличными",
        'payment_instructions': (
            "Сумма заказа: {total_price}$\n"
            "💳 Оплата через PayMe принимается только картами Uzcard и Humo.\n\n"
            "Если вы хотите оплатить с помощью Visa, MasterCard или других карт, пожалуйста, выберите опцию 'Оплата наличными'. "
            "Наш менеджер свяжется с вами. Вы также можете связаться с нами [здесь](t.me/nothardchat)."
        ),
        'user_added_property': "Недвижимость, добавленная пользователем",

        'language_label': "🇷🇺 Русский",

        'cash_payment': "Наличные",
        'payme_payment': "PayMe",

        'order_details': "Детали заказа",
        'order_number': "Номер заказа",

        'precheckout_error': "Что-то пошло не так. Попробуйте снова.",

        'payment_successful': "Спасибо за оплату! Ваш заказ #{order_id} был подтвержден и оплачен.",
        'payment_error': "Произошла ошибка при обработке платежа. Попробуйте снова.",

        'order_accepted': "Ваш заказ номер #{order_id} принят и выполняется. Если у вас возникнут вопросы, задавайте их [тут](t.me/nothardchat).",
        'order_returned': "Ваш заказ номер #{order_id} был возвращен. Если у вас возникнут вопросы, задавайте их [тут](t.me/nothardchat).",
        'order_canceled': "Ваш заказ номер #{order_id} был отменен. Если у вас возникнут вопросы, задавайте их [тут](t.me/nothardchat).",
        'order_pending': "Ваш заказ номер #{order_id} находится в ожидании. Если у вас возникнут вопросы, задавайте их [тут](t.me/nothardchat).",
        'order_payment_pending': "Ваш заказ номер #{order_id} находится в ожидании оплаты. Если у вас возникнут вопросы, задавайте их [тут](t.me/nothardchat).",
        'order_in_progress': "Ваш заказ номер #{order_id} сейчас выполняется. Если у вас возникнут вопросы, задавайте их [тут](t.me/nothardchat).",
        'order_completed': "Ваш заказ номер #{order_id} был выполнен. Если у вас возникнут вопросы, задавайте их [тут](t.me/nothardchat).",

        'invoice_title': "Оплата за заказ №{order_id}",
        'invoice_description': "Спасибо за ваш заказ! Пожалуйста, ознакомьтесь с деталями и завершите оплату.",
        'invoice_details': "Детали заказа",
        'invoice_confirmation': "Подтверждая оплату, вы соглашаетесь с условиями заказа и подтверждаете, что все детали были проверены.",
        'invoice_total_price_label': "Общая сумма",


        # registration.py
        'registration_prompt_name': "Привет! Пожалуйста, зарегистрируйтесь, чтобы начать. Укажите ваше имя.",
        'registration_cancelled': "Регистрация отменена. Вы можете начать заново, используя команду /start.",
        'registration_prompt_phone': "Пожалуйста, укажите ваш номер телефона или поделитесь им через Telegram:",
        'registration_prompt_email': "Пожалуйста, укажите ваш email:",
        'registration_completed': "Регистрация завершена! Теперь вы можете пользоваться ботом.",
        'registration_error': "Произошла ошибка при регистрации. Попробуйте еще раз.",
        'welcome_back': "Рады вас видеть снова!",
        'share_phone': "Поделиться номером телефона",
        'back': "🔙 Назад",


        # services.py
        'our_packages': "Наши пакеты",
        'individual_services': "Индивидуальные услуги",
        'back_services': "Назад",
        'orders_back_to_details': "🔙 Назад к деталям заказа",
        'linked_orders_back_to_details': "🔙 Вернуться к деталям",
        'select_service_type': "Выберите тип услуги:",
        'press_back_to_return': "Для возврата нажмите 'Назад'",

        'package_meet_me': "Пакет «Встреть меня»",
        'airport_pickup': "✈️ Встреча в аэропорту - Сопровождение по прибытии и до места отправки.",
        'transport_to_residence': "🚌 Транспорт до места проживания (общественным транспортом) - Сопровождение до вашего места проживания. Транспорт включён в стоимость.",
        'sim_card_assistance': "📱 Помощь с подключением SIM-карты - Предоставление и активация SIM-карты, включено в стоимость.",
        'oyster_card_assistance': "🎫 Получение Oyster-карты (транспортная карта) - Помощь в получении Oyster-карты, включено в стоимость.",
        'regular_reports_to_parents': "📧 Регулярные отчеты родителям - Предоставление регулярных отчетов вашим родителям о вашем процессе через Telegram-бота.",

        'package_housing': "Пакет «Жилье»",
        'all_services_meet_me': "🏠 Все услуги из пакета «Встреть меня».",
        'housing_search': "🔍 Поиск и подбор вариантов жилья (до 3 вариантов) - Поиск подходящих вариантов жилья по вашим критериям.",
        'area_consultation': "📍 Консультация по выбору района для проживания - Помощь в выборе наиболее подходящего района для проживания.",
        'apartment_viewing': "🏢 Организация просмотра недвижимости (до 3 вариантов) с видео и фотообзором. Агент посетит недвижимость и сделает обзор, который будет отправлен через Telegram.",
        'temporary_housing_assistance': "🏨 Помощь с временным жильем на первые дни - Временное жилье, если постоянное жилье не готово.",
        'moving_assistance': "🚚 Перевозка вещей - Помощь с организацией перевозки вещей, если вы уже проживаете в Лондоне. Стоимость транспорта оплачивается отдельно.",

        'premium_package': "Премиум пакет",
        'all_services_housing': "🏠 Все услуги из пакета «Жилье».",
        'local_registration_assistance': "📝 Помощь с регистрацией в Local GP (NHS, медицинская страховка) - Поддержка в процессе регистрации.",
        'support_24_7': "🕐 Поддержка 24/7 на первые 7 дней после заезда в страну через Telegram - Полная поддержка онлайн.",
        'neighbourhood_review': "📊 Оценка района проживания (Neighbourhood review) - Подробный анализ района, где вы планируете проживать.",
        'utility_connection': "💡 Подключение к коммунальным услугам - Помощь в подключении интернета, электричества, газа и других услуг.",
        'bank_account_assistance': "🏦 Помощь с открытием банковского счета - Помощь в процессе открытия счета в банке.",
        'lease_agreement_assistance': "📜 Перевод и помощь с подписанием договора аренды - Поддержка при переводе и подписании договора аренды.",
        'premium_moving_assistance': "🚚 Перевозка вещей - Организация перевозки ваших вещей. Стоимость транспорта оплачивается отдельно.",
        'gift_from_company': "🎁 Маленький подарок от компании - Полезные советы и небольшой сюрприз от нас.",
        

        'public_transport_service': "✈️ Встреча в аэропорту + 🚌 Транспорт до места проживания (общественным транспортом) - £99 ($130). Сопровождение до вашего места проживания. Транспорт включён в стоимость.",
        'private_transfer_service': "✈️ Встреча в аэропорту + 🚗 Транспорт до места проживания (частный трансфер) - £228 ($300). Сопровождение до вашего места проживания.",
        'sim_card_assistance_service': "📱 Помощь с подключением SIM-карты - £23 ($30). Помощь в получении и активации SIM-карты.",
        'oyster_card_assistance_service': "🎫 Получение Oyster-карты (транспортная карта) - £23 ($30). Помощь в получении и активации карты.",
        'regular_reports_service': "📧 Регулярные отчеты родителям - £38 ($50). Предоставление регулярных отчетов о вашем процессе адаптации через Telegram-бота.",
        'housing_search_service': "🔍 Поиск и подбор вариантов жилья (до 3 вариантов) - £45 ($60). Поиск подходящих вариантов жилья.",
        'area_consultation_service': "📍 Консультация по выбору района для проживания - £23 ($30). Помощь в выборе наиболее подходящего района для проживания.",
        'temporary_housing_assistance_service': "🏨 Помощь с временным жильем на первые дни - £38 ($50). Временное жилье на первые дни, если постоянное жилье не готово.",
        'moving_assistance_service': "🚚 Перевозка вещей - £76 ($100). Помощь с организацией перевозки вещей. Стоимость транспорта оплачивается отдельно.",
        'local_registration_service': "📝 Помощь с регистрацией в Local GP (NHS, медицинская страховка) - £76 ($100). Поддержка в процессе регистрации.",
        'support_24_7_service': "🕐 Поддержка 24/7 на первые 7 дней после заезда в страну - £76 ($100). Полная поддержка через Telegram.",
        'neighbourhood_review_service': "📊 Оценка района проживания (Neighbourhood review) - £38 ($50). Подробный анализ района проживания.",
        'utility_connection_service': "💡 Подключение к коммунальным услугам - £76 ($100). Помощь в подключении интернета, электричества и газа.",
        'bank_account_assistance_service': "🏦 Помощь с открытием банковского счета - £38 ($50). Помощь в процессе открытия банковского счета.",
        'lease_agreement_assistance_service': "📜 Перевод и помощь с подписанием договора аренды - £38 ($50). Поддержка при переводе и подписании договора аренды.",
        'document_translation': "📄 Перевод документов - £20 ($26) за документ. Перевод и помощь в оформлении документов.",


        'price': "Цена",
        'package_already_in_cart': "Вы уже добавили пакет в корзину. Вы не можете добавить более одного пакета.",
        'service_already_in_cart': "Эта услуга уже добавлена в корзину.",
        'service_added_to_cart': "Услуга добавлена в корзину!",


        'back_ser': "Назад",
        'next_ser': "Вперед",
        'add_to_cart_services': "Добавить в корзину",
        'main_menu_services': "Главное меню",
        'price_services': "Цена",
        'services_services': "Услуги",
        'out_of_services': "из",
        'press_back_or_main_menu_services': "Для возврата нажмите 'Назад' или 'Главное меню'",
    },


    'uz': {

        'order_status_order_status_update_subscriber': "bog‘langan buyurtmaning holati",

        'payment_status_updated_subscriber': "Aziz mijoz, bog‘langan buyurtma #{order_id} ning to‘lov holati '{status}' ga yangilandi.\n\nBog‘langan buyurtma holatini ko‘rish uchun asosiy menyuga o‘ting, so‘ng '🔖 Bog‘langan buyurtmalar' tugmasini bosing, #{order_id} Buyurtmasini tanlang.",

        'from_order_subscriber': "bog‘langan buyurtmadan",

        'event_added_to_order_part1_subscriber': "📢 Aziz mijoz, bog‘langan buyurtma №",

        'new_admin_message': (
            "❗ Ҳурматли мижоз, 👋\n\n"
            "Сизга буюртма #{order_id} бўйича янги хабар келди. 📨\n\n"
            "Администратордан хабар: 📝\n"
            "{message_text}\n\n"
        ),

        # subscribe.py
        'orders_generate_share_link': '🔗 Havolani yaratish',
        'orders_share_link_generated': 'Sizning buyurtmangiz uchun havola yaratildi: {share_link}',

        # Order ID bo'lmagan xabarlar
        'subscription_success_unregistered': "🎉 Buyurtma muvaffaqiyatli bog'landi. Ro'yxatdan o'tishni tugatgandan so'ng, bosh menyudan «🔖 Bog'langan buyurtmalar» tugmasini bosib buyurtmaga kirishingiz mumkin.",
        'already_subscribed_registered': 'Siz bu buyurtmani hisobingizga allaqachon bog`lagansiz. Bosh menyudan «🔖 Bog`langan buyurtmalar» tugmasini bosib uni ko`rishingiz mumkin.',
        'subscription_success_registered': '🎉 Buyurtma muvaffaqiyatli bog`landi. Siz bosh menyudan «🔖 Bog`langan buyurtmalar» tugmasini bosib uni ko`rishingiz mumkin.',
        'already_subscribed_unregistered': (
                "🇷🇺 Siz buyurtmaga allaqachon bog'langansiz. Buyurtmaga kirish uchun ro'yxatdan o'tishni tugating.\n\n"
                "Ro'yxatdan o'tishni boshlash uchun «/start» buyrug'ini kiriting.\n\n"
                "🇺🇿 Buyurtmaga allaqachon bog'langansiz. Iltimos, buyurtmaga kirish uchun ro'yxatdan o'tishni yakunlang.\n\n"
                "Ro'yxatdan o'tishni boshlash uchun «/start» buyrug'ini kiriting.\n\n"
                "🇬🇧 You are already subscribed to the order. Please complete the registration to access the order.\n\n"
                "To start the registration, please enter the command «/start»."
        ),
        'shareable_link_message': 'Mana havola, siz uni istalgan kishi bilan ulashishingiz mumkin. Ushbu havola orqali ular sizning buyurtmangizni ko`rishi va sotib olingan xizmatlarning holatini kuzatishi mumkin.',

        'start_registration': 'Ro\'yxatdan o\'tishni boshlash',
        'invalid_link': 'Noto\'g\'ri havola',

        'linked_orders': '🔖 Bog\'langan buyurtmalar',
        'change_language': '🌐 Tilni o\'zgartirish',
        'select_language_prompt': 'Tilni tanlang',

        'linked_orders_no_orders': "Sizda bog'langan buyurtmalar yo'q.",

        'orders_remove_order': '❌ Buyurtmani bog\'dan ajratish',
        'orders_order_unlinked': 'Buyurtma muvaffaqiyatli ajratildi.',

        'orders_confirm_unlink': 'Bu buyurtmani o\'zingizdan ajratishni xohlaysizmi?',
        'order_unlinked_part1': 'Buyurtma',
        'order_unlinked_part2': 'ajratildi.',
        'yes': '✅ Ha',
        'no': '❌ Yo\'q',
        'orders_canceled_unlink': 'Buyurtmani ajratish bekor qilindi.',
        'orders_invalid_input': 'Iltimos, "✅ Ha" yoki "Yo\'q" ni tanlang.',

        'view_subscribe_properties_info': "Bog'langan buyurtmani ko'rish uchun bosh menyuga o'ting, keyin '🔖 Bog'langan buyurtmalar' tugmasini bosing, kerakli buyurtma raqamini tanlang va '🏡 Mening ko'chmas mulk so'roqlarim' tugmasini bosing.",
        'view_subscribe_tasks_info_message': "Barcha bog'langan buyurtmaning vazifalarini ko'rish uchun bosh menyuga o'ting, keyin '🔖 Bog'langan buyurtmalar' tugmasini bosing, kerakli buyurtma raqamini tanlang va '📦 Mening sotib olingan xizmatlarim' tugmasini bosing.",
        'view_bonus_tasks_properties_info': "Bog'langan buyurtmani ko'rish uchun bosh menyuga o'ting, keyin '🔖 Bog'langan buyurtmalar' tugmasini bosing, kerakli buyurtma raqamini tanlang va '🏡 Mening ko'chmas mulk so'roqlarim' tugmasini bosing.",
        'order_subscribe_status_view_orders_info': "Bog'langan buyurtma holatini ko'rish uchun bosh menyuga o'ting, keyin '🔖 Bog'langan buyurtmalar' tugmasini bosing, kerakli buyurtma raqamini tanlang.",
        'view_subscribe_events_info_message': "Bog‘langan buyurtmaning barcha voqealarini ko‘rish uchun asosiy menyuga o‘ting, so‘ng '🔖 Bog‘langan buyurtmalar' tugmasini bosing, kerakli buyurtma raqamini tanlang va '📅 Buyurtma vaqt jadvali' tugmasini bosing.",

        'payment_subscribe_status_updated': "Hurmatli mijoz, sizning bog'langan buyurtmangiz #{order_id} to'lovi holati '{status}' ga yangilandi.\n\nBog'langan buyurtma holatini ko'rish uchun bosh menyuga o'ting, keyin '🔖 Bog'langan buyurtmalar' tugmasini bosing va Buyurtma #{order_id} ni tanlang.",

        'orders_timeline': "📅 Buyurtma vaqt jadvali",

        'event_enter_description': "Voqea tavsifini kiriting:",
        'event_enter_link_optional': "Natija havolasini kiriting (ixtiyoriy):",
        'event_added_success': "Voqea buyurtma vaqti bo'yicha muvaffaqiyatli qo'shildi.",
        'skip': "O'tkazib yuborish",

        'orders_no_timeline_events': "Buyurtma vaqtida hech qanday voqealar yo'q.",

        'event_added_to_order_part1': "📢 Hurmatli mijoz, sizning buyurtma №",
        'event_added_to_order_part2': "ga hodisa qo‘shildi:",

        'event_added_to_order': "Hurmatli mijoz, sizning buyurtmangiz №{order_id} ga voqea qo'shildi:",
        'event_description': "Voqea tavsifi",
        'event_timestamp': "Bu qachon sodir bo'ldi",
        'event_link': "Ko'rish uchun havola",

        "bonus_received_message": "💡 Sizga 1 bonus balli berildi, uni boshqa ko'chmas mulkni buyurtmaga qo'shish uchun ishlatishingiz mumkin.",
        "bonus_usage_instructions": "Bonusingizdan foydalanish uchun bosh menyuga o'ting, keyin '📦 Mening buyurtmalarim' tugmasini bosing, kerakli buyurtma raqamini tanlang va '🎁 Mening bonuslarim' tugmasini bosing.",

        # addproperty.py
        'load_property_link_prompt': (
            "Agar boshqa saytda tegishli ko'chmas mulk variantini topsangiz, uni savatga qo'shishingiz mumkin. "
            "Shunchaki ushbu ko'chmas mulk sahifasiga havolani chatga yuboring.\n\n"
            "Agar siz hali kerakli narsani topmagan bo'lsangiz, variantlarni qidirish uchun «🏡 Ko'chmas mulkni qidirish» funksiyamizdan foydalanishingiz mumkin."
        ),
        'link_added_success': "Topilgan ko'chmas mulk havolasi savatga muvaffaqiyatli qo'shildi!",
        'not_a_link': "Xabaringiz ko'chmas mulkka havola sifatida ro'yxatga olinmadi.",
        'link_save_error': "Havolani saqlashda xatolik yuz berdi. Iltimos, yana bir bor urinib ko'ring.",

        # oferta.py
        "offer_view": "Ommaviy oferta bilan tanishish",
        "offer_message": "Quyidagi tugmani bosib, ommaviy oferta bilan tanishishingiz mumkin:",


        # common.py
        'back_link': "Orqaga",
        'main_menu': "Asosiy menyu:",
        'search_property': "🏡 Ko'chmas mulkni qidirish",
        'add_found_property': "🔗 Topilgan ko'chmas mulkni qo'shish",
        'my_likes': "❤️ Mening yoqtirishlarim",
        'cart': "🛒 Savat",
        'our_services': "💠 Bizning xizmatlarimiz",
        'my_orders': "📦 Mening buyurtmalarim",
        'profile_menu': "👤 Profil / 🌐 Tillar",
        'contacts': "📞 Kontaktlar",
        'what_to_know': "ℹ️ Nima bilish kerak",
        'leave_feedback': "📝 Fikr qoldirish",
        'offer': "📄 Oferta", 
        'admin_panel': "⚙️ Admin paneli",

        # admin.py

        'dear_client': 'Hurmatli mijoz',
        'order_status_order_status_update': 'buyurtmangizning holati',
        'order_status_status_updated_to': 'o‘zgartirildi',
        'order_status_view_orders_info': "Buyurtmangiz holatini ko‘rish uchun asosiy menyuga o‘ting, so‘ng '📦 Mening buyurtmalarim' tugmasini bosing va kerakli buyurtmani tanlang.",
        
        # Buyurtma holatlari
        'order_status_accepted_message': "Sizning buyurtmangiz qabul qilindi va qayta ishlanmoqda.",
        'order_status_returned_message': "Sizning buyurtmangiz qaytarildi.",
        'order_status_cancelled_message': "Sizning buyurtmangiz bekor qilindi.",
        'order_status_pending_message': "Sizning buyurtmangiz kutish holatida.",
        'order_status_waiting_payment_message': "Sizning buyurtmangiz to‘lovni kutmoqda.",
        'order_status_in_progress_message': "Sizning buyurtmangiz bajarilmoqda.",
        'order_status_completed_message': "Sizning buyurtmangiz bajarildi.",
        'order_status_accepted': 'Qabul qilindi',
        'order_status_returned': 'Qaytarildi',
        'order_status_cancelled': 'Bekor qilingan',
        'order_status_pending': 'Kutilmoqda',
        'order_status_waiting_payment': 'To\'lov kutilmoqda',
        'order_status_in_progress': 'Bajarilmoqda',
        'order_status_completed': 'Bajarilgan',

        'payment_paid': 'Toʻlangan',
        'payment_not_paid': 'Toʻlanmagan',
        'payment_status_updated': "Hurmatli mijoz, sizning buyurtma #{order_id} uchun to'lov holati '{status}' ga yangilandi.\n\nBuyurtma holatini tekshirish uchun bosh menyuga o'ting, keyin '📦 Mening buyurtmalarim' ni tanlang va buyurtma #{order_id} tanlang.",

        'order_status_Оплачено': 'Toʻlangan',

        'payment_successful': "Buyurtma uchun to'lov №{order_id} muvaffaqiyatli amalga oshirildi. Xaridingiz uchun rahmat!",
        'payment_error': "To'lovni amalga oshirishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",

        'reservation_date_message': "Ko‘rish sanasi va vaqti",

        'property_status_waiting_agent': 'Hozirda biz siz tanlagan ko‘chmas mulk egasi bo‘lgan agentlikning javobini kutyapmiz.',
        'property_status_booked': 'Biz agent bilan bog‘landik va ushbu ko‘chmas mulkni ko‘rish kunini belgiladik.',
        'property_status_going': 'Agent ko‘chmas mulkni ko‘rish uchun yo‘lga chiqdi.',
        'property_status_in_progress': 'Agent obyektning foto va video tasvirlarini olmoqda.',
        'property_status_viewed': 'Agent ko‘rikni yakunladi va tez orada materiallarni siz bilan bo‘lishadi.',
        'property_status_ready': 'Kutinganingiz uchun rahmat. Ko‘rishingiz uchun foto va video sharhlarni ilova qilamiz.',
        'property_status_cancelled': 'Afsuski, ko‘chmas mulkingizni ko‘rish bekor qilindi.',
        'view_properties_info': "Barcha koʻchmas mulk soʻrovlarini koʻrish uchun asosiy menyuga o'ting, keyin '📦 Mening buyurtmalarim' ni tanlang va kerakli buyurtma raqamini bosing.",

        'dear_client': 'Hurmatli mijoz',
        'property_status_update': 'ko\'chmas mulkingizning holati',
        'from_order': 'buyurtmadan',
        'status_updated_to': 'holatiga o\'zgartirildi',
        'property_added_by_user': 'Foydalanuvchi tomonidan qo\'shilgan ko\'chmas mulk',

        'task_status_completed': 'Bajarildi',
        'task_status_not_completed': 'Bajarilmadi',
        'task_status_in_progress': 'Bajarilmoqda',

        'task_status_status': "Xizmat yoki vazifaning holati",
        'task_status_in_order': "buyurtma",
        'task_status_has_been_updated': "yangilandi",
        'task_status_completed_message': "Vazifa muvaffaqiyatli bajarildi.",
        'task_status_not_completed_message': "Vazifa bajarilmadi. Agar bu xato deb o'ylasangiz, biz bilan [bu yerda](t.me/nothardchat) bog'laning.",
        'task_status_in_progress_message': "Vazifa bajarilmoqda. Uni tugatganimizda sizga xabar beramiz.",
        'view_tasks_info_message': "Barcha vazifalar holatini ko'rish uchun bosh menyuga o'ting, '📦 Buyurtmalarim' ni tanlang va '📦 Xarid qilingan xizmatlarim' ga o'ting.",

        'cloud_link_message': "Natija uchun havola",

        'save_property_dear_client': "Hurmatli mijoz,",
        'save_property_status_update_prefix': "ko'chmas mulkingizning holati",
        'save_property_in_order': "buyurtma raqami",
        'save_property_has_been_updated_to': "yangilandi",
        'save_property_cancellation_reason': "Bekor qilish sababi",
        'save_property_bonus_received_message': "💡 Sizga 1 bonus balli berildi, uni boshqa ko'chmas mulkni buyurtmaga qo'shish uchun ishlatishingiz mumkin.",
        'save_property_view_bonuses_info': "Buning uchun asosiy menyuga o'ting, '📦 Mening buyurtmalarim'ni bosing, buyurtma raqamini tanlang va '🎁 Mening bonuslarim'ni tanlang.",
        'save_property_status_changed_to': "Holat o'zgartirildi",
        'save_property_reason': "Sabab",
        'save_property_result_link_saved_for_property': "Ko'chmas mulk uchun natija havolasi",
        'save_property_link': "Havola",
        'save_property_result_link_saved': "Natija havolasi saqlandi",

        'property_status_ready_message': "Hurmatli mijoz, sizning ko'chmas mulkingizning ko'rib chiqish holati {title} buyurtma #{order_id} da 'Natija tayyor' ga yangilandi.",
        'property_result_link': "Natija havolasi: <a href='{cloud_link}'>{cloud_link}</a>.",
        'view_all_tasks_info': "Barcha vazifalarni ko'rish uchun asosiy menyuga o'ting, '📦 Mening buyurtmalarim' tugmasini bosing, buyurtma raqamini tanlang va '🏡 Mening ko'chmas mulk so'roqlarim' ga o'ting.",

        'view_tasks_intro': "Barcha vazifalarni ko'rish uchun asosiy menyuga o'ting, '📦 Mening buyurtmalarim' tugmasini bosing, keyin buyurtmani tanlang",
        'view_tasks_instruction': "so'ng '🏡 Mening mulk so'rovlarim' bo'limiga o'ting",

        # contacts.py
        'contact_info': (
        "24/7 qo'llab-quvvatlash bilan bog'lanish:\n"
        "Telegram: [t.me/nothardchat](http://t.me/nothardchat)\n"
        "Email: helpme@nothard.uz\n"
        "Telefon - Toshkent: +998 88 089 89 10 (Vaqtinchalik mavjud emas)\n"
        "Telefon - London: +44 7990 381454\n"
        ),

        # feedback.py
        "feedback_back": "🔙 Orqaga",
        "feedback_please_leave": "Iltimos, fikr-mulohazangizni qoldiring:",
        "feedback_thank_you": "Fikr-mulohazangiz uchun rahmat!",
        "feedback_not_registered": "Xabaringiz fikr-mulohaza sifatida ro'yxatga olinmadi.",

        # orders.py
        'orders_no_orders': "Sizda buyurtmalar yo'q.",
        'orders_select_order': "Buyurtmani tanlang:",
        'orders_order': "Buyurtma",
        'orders_back_to_menu': "🔙 Menyuga qaytish",

        'orders_payment_cash': "Naqd pul 💵",
        'orders_payment_payme': "PayMe 💳",
        'orders_payment_not_specified': "Ko'rsatilmagan",
        'orders_paid': "To'langan ✅",
        'orders_not_paid': "To'lanmagan ❌",
        'orders_details': (
            "📝 Buyurtma tafsilotlari: \\#{order_id}\n"
            "📅 Sana va Vaqt: {order_date}\n"
            "📦 Holat: {status}\n"
            "💰 To'lov usuli: {payment_method}\n"
            "💳 To'lov holati: {payment_status}"
        ),


        'orders_subscriber_purchased_services': "📦 Sotib olingan xizmatlar",
        'orders_subscriber_property_requests': "🏡 Ko‘chmas mulk so‘rovlari",

        'orders_my_purchased_services': "📦 Mening sotib olingan xizmatlarim",
        'orders_my_property_requests': "🏡 Mening ko'chmas mulk so'rovlarim",
        'orders_my_bonuses': "🎁 Mening bonuslarim",
        'orders_back_to_orders': "🔙 Buyurtmalarga qaytish",

        'orders_user_added_property': '🏠 Foydalanuvchi tomonidan qo\'shilgan ko\'chmas mulk',
        'orders_status': 'Holat',
        'orders_result_ready': 'Natija tayyor',
        'orders_view_cancelled': 'Ko\'rish bekor qilindi',
        'orders_cancellation_reason': 'Bekor qilish sababi',
        'orders_report': 'Hisobot',
        'orders_property_name': 'Nomi',
        'orders_price': 'Narx',
        'orders_address': 'Manzil',
        'orders_not_available': 'N/A',
        'orders_no_properties': 'Ijaraga olingan ko\'chmas mulkingiz yo\'q.',
        'orders_back': '🔙 Orqaga',
        'orders_link': 'Havola',


        'orders_order_not_found': "Xato: Buyurtma topilmadi.",
        'orders_in_progress': "Jarayonda",
        'orders_not_completed': "Bajarilmagan",
        'orders_completed': "Bajarildi",
        'orders_package': "Paket",
        'orders_package_status': "Paket holati",
        'orders_no_services': "Sizda hech qanday sotib olingan xizmatlar yo'q.",

        'orders_document_translation_service': "📄 Hujjatlarni tarjima qilish",
        'orders_lease_agreement_assistance_service': "📜 Ijara shartnomasini tarjima qilish va yordam",
        'orders_airport_pickup': "✈️ Aeroportda kutib olish",
        'orders_transport_to_residence': "🚌 Yashash joyiga transport",
        'orders_sim_card_assistance': "📱 SIM-kartaga yordam",
        'orders_oyster_card_assistance': "🎫 Oyster kartaga yordam",
        'orders_regular_reports_to_parents': "📧 Ota-onaga muntazam hisobotlar",
        'orders_housing_search': "🔍 Uy-joy qidiruvi va tanlovi",
        'orders_area_consultation': "📍 Hudud bo'yicha maslahat",
        'orders_apartment_viewing': "🏢 Kvartira ko'rigi",
        'orders_temporary_housing_assistance': "🏨 Birinchi kunlar uchun vaqtinchalik uy-joy yordami",
        'orders_moving_assistance': "🚚 Buyumlarni ko'chirish yordami",


        'in_progress': "🔄",
        'not_completed': "❌",
        'completed': "✅",


        'orders_bonuses_one_available': "🎁 Sizda 1 ta bepul ko‘chmas mulk qo‘shish imkoniyati bor.",
        'orders_bonuses_multiple_available': "🎁 Sizda {bonuses} ta bepul ko‘chmas mulk qo‘shish imkoniyati bor.",
        'orders_no_bonuses_available': "❌ Sizda mavjud bonuslar yo‘q.",
        'orders_search_property': "🔍 Ko‘chmas mulk qidirish",
        'orders_add_found_property': "➕ Topilgan ko‘chmas mulkni qo‘shish",
        'orders_likes': "❤️ Yoqtirganlar",
        'orders_back_to_orders': "🔙 Buyurtmalarga qaytish",

        'bonus_zone_1': "1-Zona",
        'bonus_zone_2': "2-Zona",
        'bonus_zone_3': "3-Zona",
        'bonus_zone_4': "4-Zona",
        'bonus_zone_5': "5-Zona",
        'bonus_zone_6': "6-Zona",
        'bonus_zone_unknown': "Bilmayman",
        'bonus_back': "🔙 Orqaga",
        'bonus_property_search_waiting': "Iltimos kuting, biz mulk qidiryapmiz...",
        'bonus_select_zone': "Yashash zonangizni tanlang:",

        'bonus_enter_max_price': "Oylik sarflamoqchi bo'lgan maksimal summani kiriting (funt sterlingda). Faqat raqamlar kiriting, belgilarsiz (masalan, 1500):",
        'bonus_select_rooms': "Nechta xona xohlaysiz?",

        'bonus_studio': "Studiya",
        'bonus_unknown': "Bilmayman",
        'bonus_select_property_type': "Qanday turdagi ko'chmas mulkni xohlaysiz?",
        'bonus_flat': "Kvartira",
        'bonus_house': "Uy",
        'bonus_student_housing': "Talabalar turar joyi",
        'bonus_furnish_question': "Uy jihozlangan bo'lishi kerakmi?",
        'bonus_furnished': "Jihozlangan",
        'bonus_unfurnished': "Jihozlanmagan",
        'bonus_part_furnished': "Qisman jihozlangan",
        'bonus_living_type_question': "Siz House Share (birgalikda yashash) variantlarini ko'rishni xohlaysizmi?",
        'bonus_show_house_share': "Ha, House Share ko'rsatilsin",
        'bonus_dont_show_house_share': "Yo'q, faqat o'zim uchun",

        'bonus_no_results': "Mos keladigan variantlar topilmadi.",
        'bonus_main_menu': "Asosiy menyu",

        'bonus_property_liked': "Ob'ektga layk qo'yildi!",
        'bonus_no_properties_found': "Mos keladigan variantlar topilmadi.",
        'bonus_not_available': "N/A",
        'bonus_price': "Narx",
        'bonus_address': "Manzil",
        'bonus_link': "Havola",
        'bonus_of': "dan",
        'bonus_prev': "⬅️ Orqaga",
        'bonus_next': "Oldinga ➡️",
        'bonus_like': "Layk qo'yish",
        'bonus_add_to_order': "Buyurtmaga qo'shish",
        'bonus_back_to_bonuses': "Bonuslarga qaytish",

        'bonus_order_not_found': "Xatolik: buyurtma topilmadi.",
        'bonus_no_properties_available': "Xatolik: qo'shish uchun mavjud obyektlar yo'q.",
        'bonus_no_bonuses_left': "Sizda buyurtmaga ko'chmas mulk qo'shish uchun bonus qolmadi.",
        'bonus_property_added': "Ko'chmas mulk buyurtmaga qo'shildi va bir bonus o'chirildi!",
        'bonus_back_to_bonuses': "🔙 Bonuslarga qaytish",
        'bonus_enter_property_link': "Iltimos, topilgan ko'chmas mulkning havolasini kiriting yoki 'Orqaga' tugmasini bosing, bonuslarga qaytish uchun.",

        'bonus_enter_property_link': "Iltimos, topilgan ko'chmas mulkning havolasini yuboring.",
        'bonus_property_link_added': "Topilgan ko'chmas mulkning havolasi muvaffaqiyatli buyurtmaga qo'shildi va bir bonus o'chirildi!",
        'bonus_order_not_found': "Xatolik: buyurtma topilmadi.",
        'bonus_unexpected_link': "Xatolik: bot havola olishni kutmagan.",
        'bonus_link_save_error': "Havolani saqlashda xatolik yuz berdi. Iltimos, yana bir bor urinib ko'ring.",

        'bonus_no_likes': "Sizda bonuslar orqali qo'shilgan yoqqan obyektlar yo'q.",
        'bonus_not_available': "N/A",
        'bonus_price': "Narx",
        'bonus_address': "Manzil",
        'bonus_link': "Havola",
        'bonus_of': "dan",
        'bonus_prev': "⬅️ Orqaga",
        'bonus_next': "Oldinga ➡️",
        'bonus_add_to_order': "Buyurtmaga qo'shish",
        'bonus_delete_like': "🗑️ O'chirish",
        'bonus_back_to_bonuses': "🔙 Bonuslarga qaytish",

        'bonus_invalid_index': "Xatolik: Noto'g'ri indeks.",
        'bonus_no_bonuses_left': "Sizda buyurtmaga ko'chmas mulk qo'shish uchun bonus qolmadi.",
        'bonus_property_added_from_likes': "Ko'chmas mulk muvaffaqiyatli tarzda buyurtmaga qo'shildi! Bir bonus kamaytirildi.",
        'bonus_like_deleted': "Ob'ekt layklardan o'chirildi!",

        'bonus_select_zone': "Yashash zonangizni tanlang:",
        'bonus_enter_price': "Oylik qancha mablag' sarflashni rejalashtirganingizni kiriting. Faqat raqamlar, belgilarsiz (masalan, 1500):",
        'bonus_how_many_rooms': "Nechta xona xohlaysiz?",
        'bonus_select_property_type': "Qaysi turdagi ko'chmas mulk sizni qiziqtiradi?",
        'bonus_furnish': "Uy jihozlangan bo'lishi kerakmi?",

        # info.py
        "info_choose_info": "Nimani bilishni xohlaysiz:",
        "info_bot_features": "💡 Bot nimalarni qila oladi",
        "info_useful_info": "ℹ️ Foydali ma'lumotlar",
        "info_back": "🔙 Orqaga",
        "info_features_message": (
            "❓ *Bot nimalarni qila oladi*\n\n"
            "1. 🏡 *Ko‘chmas mulk qidirish*: Bot sizga mos keladigan variantlarni taklif qiladi. "
            "Siz ko‘rib chiqishingiz, yoqtirishingiz va buyurtma berish uchun obyektlarni savatga qo‘shishingiz mumkin.\n\n"
            "2. 🔗 *Topilgan ko‘chmas mulkni qo‘shish*: Agar siz boshqa saytdan obyekt topsangiz, havolani yuboring, va bot uni savatga qo‘shadi.\n\n"
            "3. ❤️ *Mening yoqtirganlarim*: Siz yoqtirgan ko‘chmas mulk obyektlari saqlanadi.\n\n"
            "4. 🛒 *Savat*: Siz to‘plagan barcha mahsulot va xizmatlar bu yerda buyurtma berish uchun saqlanadi.\n\n"
            "5. 💠 *Bizning xizmatlarimiz*: Bu yerdan siz bizning xizmat paketlarimiz va individual xizmatlarimizni topishingiz mumkin, ular savatga qo‘shilishi mumkin.\n\n"
            "6. 📦 *Mening buyurtmalarim*: Bu yerda siz buyurtmalaringizni kuzatishingiz, holatlarini ko‘rishingiz va agar mavjud bo‘lsa, bonuslardan foydalanishingiz mumkin.\n\n"
            "7. 🔖 *Bog‘langan buyurtmalar*: Boshqa foydalanuvchilar siz bilan bo‘lishgan buyurtmalar bu yerda ko‘rsatiladi. Siz sotib olingan xizmatlar va buyurtma tafsilotlarini ko‘rishingiz mumkin.\n\n"
            "8. 👤 *Profil*: Ism, telefon va email kabi shaxsiy ma'lumotlaringizni boshqaring.\n\n"
            "9. 📞 *Kontaktlar*: Biz bilan qanday bog‘lanish haqida ma'lumot.\n\n"
            "10. 📝 *Fikr qoldirish*: Bizning xizmatimiz haqidagi fikrlaringizni baham ko‘ring.\n\n"
            "11. ℹ️ *Nimani bilish kerak*: Ko‘chmas mulk qidirishda sizga yordam beradigan muhim maslahatlar va ma'lumotlar.\n\n"
            "12. 📄 *Oferta*: Bizning ommaviy ofertamizni o‘qib chiqing."
        ),
        "info_useful_info_message": (
            "ℹ️ *Foydali ma'lumotlar*\n\n"
            "1. Londonda ko‘chmas mulk egalari chet el fuqarolaridan kafillarni talab qilishi mumkin. "
            "Agar sizda kafillik yo‘q bo‘lsa, 6 oylik oldindan to‘lovni taqdim etishingiz kerak bo‘ladi. Bu talab yotoqxonalarga taalluqli emas.\n\n"
            "2. Yotoqxonalar kafillarni talab qilmaydi, lekin ko‘pchilik 3 oylik oldindan to‘lov va choraklik yoki semestrlik to‘lovlarni talab qiladi.\n\n"
            "3. Agentliklar orqali uy-joy ijaraga olayotganda, daromadni tasdiqlovchi hujjatlar, ish shartnomasi va bank hisobotlari kabi qo‘shimcha hujjatlar talab qilinishi mumkin.\n\n"
            "4. Ijara shartlarini doimo tekshiring va kommunal xizmatlar va internet kabi qo‘shimcha to‘lovlar haqida bilib oling.\n\n"
            "5. Ijara shartnomasini imzolashda, barcha shartlar aniq va shartnomada yozilganligiga ishonch hosil qiling, shu jumladan ijara muddati, to‘lov shartlari va yashash qoidalari.\n\n"
            "6. Firibgarlikdan qochish uchun uy-joy qidirishda ishonchli saytlar va agentliklardan foydalaning.\n\n"
            "7. Yashashni rejalashtirayotgan hududlar bilan tanishing, ular xavfsizlik, infratuzilma va qulayliklar bo‘yicha talablaringizga mos kelishiga ishonch hosil qiling.\n\n"
            "8. Agar sizda ijara bilan bog‘liq savollar yoki muammolar bo‘lsa, yuristlarga yoki ijara huquqlarini himoya qilish tashkilotlariga murojaat qiling."
        ),

        # profile.py
        'profile_not_found': "Profil topilmadi. Iltimos, ro'yxatdan o'ting.",
        'profile_account': "Sizning profilingiz:\n{profile}",
        'edit_name': "✏️ Ismni o'zgartirish",
        'edit_phone': "📞 Telefonni o'zgartirish",
        'edit_email': "✉️ Emailni o'zgartirish",
        'edit_language': "🌐 Tilni o'zgartirish",
        'profile_name': "Ism",
        'profile_phone': "Telefon",
        'profile_email': "Email",
        'profile_language': "Til",
        'back_profile': "🔙 Orqaga",
        'incorrect_language_selection': "Iltimos, taklif qilingan tillardan birini tanlang.",
        'updated': "yangilandi",
        'select_language_prompt': "Tilni tanlang:",
        'registration': "Ro'yxatdan o'tish",
        'enter_new_value': "{field} uchun yangi qiymatni kiriting:",
        'incorrect_field': "Noto'g'ri maydon. Iltimos, qayta tanlang.",
        'field_updated': "{field} yangilandi.",

        # property_search.py
        'property_search_started': "Biroz kutib turing, biz ko'chmas mulk qidirishni boshladik...",
        'property_choose_zone': "Qaysi joyda yashashni xohlaysiz?",
        'property_enter_max_price': "Har oyda sarflashga tayyor bo'lgan funtlar miqdorini kiriting. Faqat raqamlarni kiriting, simvollarsiz (masalan, 1500):",
        'property_enter_room_count': "Qancha xonali uy xohlaysiz?",
        'property_choose_property_type': "Qanday turdagi ko'chmas mulk qiziqtiradi?",
        'property_should_furnished': "Joy mebellangan bo'lishi kerakmi?",
        'property_house_share_option': "Birga yashash (House Share) variantlarini ko'rishni xohlaysizmi?\n\n1. Ha — House Share variantlarini ko'rsating.\n2. Yo'q — faqat siz uchun mo'ljallangan variantlarni ko'rsating.",
        'property_results_not_found': "Mos variantlar topilmadi.",
        'property_added_to_likes': "Biz ushbu ob'ektni sizning yoqtirilganlar ro'yxatiga qo'shdik!",
        'property_added_to_cart': "Ko'chmas mulk savatga qo'shildi!",
        'property_no_properties_in_cart': "Savatga qo'shish uchun hech qanday ob'ekt mavjud emas.",
        'property_likes_empty': "Sizda yoqtirilgan ob'ektlar yo'q.",
        'property_cart_empty': "Sizning savatingiz bo'sh.",
        'property_order_confirmed': "To'lovingiz uchun rahmat! Sizning buyurtmangiz tasdiqlandi.",
        'property_order_placed': "Buyurtmangiz qabul qilindi! Buyurtmangiz uchun rahmat.",
        'property_order_cancelled': "Buyurtmangiz bekor qilindi.",
        'property_order_status_updated': "Buyurtma holati '{status}'ga o'zgartirildi",
        'property_back_to_main_menu': "Menyuga qaytish",
        'property_delete_property_confirmation': "Siz {item}ni savatdan olib tashlashni xohlaysizmi?",
        'property_removed': "Ob'ekt muvaffaqiyatli o'chirildi.",
        'property_removal_cancelled': "O'chirish bekor qilindi.",
        'property_basket_summary': "Savat\n\n{summary}",
        'property_order_details': "Buyurtma tafsilotlari\n\n{details}\n\nTo'lov: {payment_method}\nJami: {total_price}$",
        'property_place_order_confirmation': "Buyurtma summasi: {total_price}$\n💳 PayMe orqali to'lov faqat Uzcard va Humo kartalari bilan qabul qilinadi.\nAgar siz Visa, MasterCard yoki boshqa kartalar bilan to'lov qilishni xohlasangiz, 'Naqd to'lov' opsiyasini tanlang. Bizning menejerimiz siz bilan bog'lanadi.",
        'property_new_order_notification': "Foydalanuvchidan yangi buyurtma: {details}",
        'payme_payment_url': "PayMe orqali to'lov qilish uchun havola: {payme_url}",
        'property_search_back_to_menu': "🔙 Menyuga qaytish",
        'property_search_go_back': "⬅️ Orqaga",
        'property_search_next': "Oldinga ➡️",
        'property_search_like': "❤️ Layk",
        'property_search_add_to_cart': "🛒 Savat",
        'property_property': "🏡 *Mulk*",
        'property_price': "💷 *Narxi*",
        'property_address': "📍 *Manzil*",
        'property_link': "🔗 Mulkni ko'rish",
        'property_out_of': "dan",
        'property_view': "Ob'ektni ko'rish",

        'bonus_show_property': "🏡 *Mulk:* {title}\n💰 *Narxi:* {price}\n📍 *Manzil:* {address}\n🔗 [Mulkni ko'rish]({link})\n\nMulk {current_index} / {total_properties}",

        'zone_1': "Zona 1",
        'zone_2': "Zona 2",
        'zone_3': "Zona 3",
        'zone_4': "Zona 4",
        'zone_5': "Zona 5",
        'zone_6': "Zona 6",
        'zone_unknown': "Men bilmayman",
        'studio': "Studiya",
        'rooms_1': "1",
        'rooms_2': "2",
        'rooms_3': "3",
        'rooms_4_plus': "4+",
        'furnished': "Mebellangan",
        'unfurnished': "Mebelsiz",
        'part_furnished': "Qisman mebellangan",
        'house_share_yes': "Ha, House Share ko'rsating",
        'house_share_no': "Yo'q, House Share ko'rsatmang",
        'property_type_flat': "Kvartira",
        'property_type_house': "Uy",
        'property_type_private_halls': "Studentlar yotoqxonasi",
        'go_back': "⬅️ Orqaga",
        'confirm_removal_button': "Ha",
        'cancel_removal_button': "Yo'q",
        'property_search_delete': "🗑️ O'chirish",

        'payment_method': "To'lov usuli",

        'cart_is_empty': "🛒 Savatingiz bo'sh.",
        'cart_title': "🛒 Savat",
        'property_section_title': "\n\n🏡 *Ko'chmas mulk:*",
        'no_properties_in_cart': "Qo'shilgan ko'chmas mulk yo'q.",
        'package_section_title': "📦 *Paket xizmatlari:*",
        'individual_services_section_title': "🛠️ *Alohida xizmatlar:*",
        'no_individual_services': "Qo'shilgan alohida xizmatlar yo'q.",
        'total_price': "💰 *Jami: {total_price}$*",
        'property_summary_with_extra': "{property_count} ta ob'ekt ko'rib chiqildi (3 tasi paketga kiritilgan, {extra_properties} ta qo'shimcha ko'rib chiqish har biri 50$)",
        'property_summary_without_extra': "{property_count} ta ob'ekt ko'rib chiqildi (3 tasi paketga kiritilgan)",
        'property_summary_no_package': "{property_count} ta ob'ekt ko'rib chiqildi ({price}$)",
        'delete_property_button': "🗑 Ko'chmas mulkni o'chirish: {title}",
        'delete_package_button': "🗑 Paketni o'chirish: {service_title}",
        'delete_service_button': "🗑 Xizmatni o'chirish: {service_title}",
        'delete_individual_service_button': "🗑 Alohida xizmatni o'chirish: {service_title}",
        'place_order_button': "🛒 Buyurtma qilish",
        'main_menu_button_text': "Asosiy menyu",
        'back_to_main_menu': "Orqaga qaytish uchun 'Asosiy menyu' tugmasini bosing",

        'property_remove_like': "Siz {item} ni yoqtirganlardan o'chirmoqchimisiz?",
        'property_like_removed': "Obyekt muvaffaqiyatli ravishda yoqtirganlardan o'chirildi!",
        'property_like_removal_cancelled': "O'chirish bekor qilindi.",
        'property_remove_cart': "Siz {item} ni savatchadan o'chirmoqchimisiz?",
        'property_cart_item_removed': "Element savatchadan muvaffaqiyatli o'chirildi!",
        'property_cart_removal_cancelled': "Savatchadan o'chirish bekor qilindi.",
        'property_add_to_cart_success': "Ko'chmas mulk savatchaga qo'shildi!",
        'property_confirm_remove': "Ha",
        'property_cancel_remove': "Yo'q",
        'property_error_invalid_index': "Xato: element indeksi noto'g'ri.",
        'property_view': "Obyektni ko'rish",
        'property_remove_cart_question': "Siz bu narsani savatdan olib tashlamoqchimisiz",
        'property_remove_cart_footer': "savatchadan olib tashlashni istaysizmi?",

        'confirm_check_info': "Ma'lumotlarni yana bir bor tekshiring",
        'confirm_all_correct': "Hammasi to'g'ri",
        'confirm_agreement': "«Ha» tugmasini bosish orqali siz xizmat ko'rsatish bo'yicha Ommaviy oferta shartlariga rozilik bildirasiz va kiritilgan ma'lumotlarning to'g'riligini tasdiqlaysiz.",
        'ordered_items': "Buyurtma qilingan narsalar",
        'package_services': "📦 Paket xizmatlari",
        'individual_services': "🛠️ Alohida xizmatlar",
        'no_properties': "Qo'shilgan ko'chmas mulk yo'q.",
        'no_packages': "Qo'shilgan paketlar yo'q.",
        'no_individual_services': "Qo'shilgan alohida xizmatlar yo'q.",
        'confirm_order_yes': "Ha",
        'confirm_order_no': "Yo'q",
        'property_view_summary': "{property_count} ta ob'ekt ko'rib chiqildi (3 tasi paketga kiritilgan, {extra_properties} ta qo'shimcha ko'rib chiqish har biri 50$)",
        'property_view_included': "{property_count} ta ob'ekt ko'rib chiqildi (3 tasi paketga kiritilgan)",
        'property_view_individual': "{property_count} ta ob'ekt ko'rib chiqildi (har biri 50$)",

        'payme_button': "PayMe orqali to'lash ({total_price_in_sums} so'm)",
        'cash_payment_button': "Naqd pul bilan to'lash",
        'payment_instructions': (
            "Buyurtma summasi: {total_price}$\n"
            "💳 PayMe orqali to'lov faqat Uzcard va Humo kartalari bilan qabul qilinadi.\n\n"
            "Agar siz Visa, MasterCard yoki boshqa kartalar bilan to'lamoqchi bo'lsangiz, iltimos, 'Naqd pul bilan to'lash' variantini tanlang. "
            "Bizning menejerimiz siz bilan bog'lanadi. Shuningdek, biz bilan [bu yerda](t.me/nothardchat) bog'lanishingiz mumkin."
        ),
        'user_added_property': "Foydalanuvchi qo'shgan ko'chmas mulk",

        'language_label': "🇺🇿 O'zbek",

        'cash_payment': "Naqd pul",
        'payme_payment': "PayMe",

        'order_details': "Buyurtma tafsilotlari",
        'order_number': "Buyurtma raqami",

        'precheckout_error': "Nimadir xato ketdi. Iltimos, qayta urinib ko'ring.",

        'payment_successful': "To'lovingiz uchun rahmat! Buyurtmangiz #{order_id} tasdiqlandi va to'landi.",
        'payment_error': "To'lovni qayta ishlashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",

        'order_accepted': "Sizning buyurtmangiz #{order_id} qabul qilindi va qayta ishlanmoqda. Agar savollaringiz bo'lsa, ularni [bu yerda](t.me/nothardchat) so'rashingiz mumkin.",
        'order_returned': "Sizning buyurtmangiz #{order_id} qaytarildi. Agar savollaringiz bo'lsa, ularni [bu yerda](t.me/nothardchat) so'rashingiz mumkin.",
        'order_canceled': "Sizning buyurtmangiz #{order_id} bekor qilindi. Agar savollaringiz bo'lsa, ularni [bu yerda](t.me/nothardchat) so'rashingiz mumkin.",
        'order_pending': "Sizning buyurtmangiz #{order_id} kutilmoqda. Agar savollaringiz bo'lsa, ularni [bu yerda](t.me/nothardchat) so'rashingiz mumkin.",
        'order_payment_pending': "Sizning buyurtmangiz #{order_id} to'lovni kutmoqda. Agar savollaringiz bo'lsa, ularni [bu yerda](t.me/nothardchat) so'rashingiz mumkin.",
        'order_in_progress': "Sizning buyurtmangiz #{order_id} hozirda qayta ishlanmoqda. Agar savollaringiz bo'lsa, ularni [bu yerda](t.me/nothardchat) so'rashingiz mumkin.",
        'order_completed': "Sizning buyurtmangiz #{order_id} bajarildi. Agar savollaringiz bo'lsa, ularni [bu yerda](t.me/nothardchat) so'rashingiz mumkin.",

        'invoice_title': "Buyurtma uchun toʻlov №{order_id}",
        'invoice_description': "Buyurtmangiz uchun rahmat! Tafsilotlarni koʻrib chiqib, toʻlovni amalga oshiring.",
        'invoice_details': "Buyurtma tafsilotlari",
        'invoice_confirmation': "Toʻlovni tasdiqlash orqali siz buyurtma shartlariga rozilik bildirasiz va barcha tafsilotlarni koʻrib chiqqaningizni tasdiqlaysiz.",
        'invoice_total_price_label': "Umumiy summa",


        # registration.py
        'registration_prompt_name': "Salom! Botdan foydalanishni boshlash uchun ro'yxatdan o'ting. Iltimos, ismingizni kiriting.",
        'registration_cancelled': "Ro'yxatdan o'tish bekor qilindi. Siz /start buyrug'i yordamida qaytadan boshlashingiz mumkin.",
        'registration_prompt_phone': "Iltimos, telefon raqamingizni kiriting yoki Telegram orqali uni ulashing:",
        'registration_prompt_email': "Iltimos, emailingizni kiriting:",
        'registration_completed': "Ro'yxatdan o'tish yakunlandi! Endi botdan foydalanishingiz mumkin.",
        'registration_error': "Ro'yxatdan o'tishda xatolik yuz berdi. Iltimos, yana bir bor urinib ko'ring.",
        'welcome_back': "Sizni yana ko'rishdan xursandmiz!",
        'share_phone': "Telefon raqamini ulashish",
        'back': "🔙 Orqaga",


        # services.py
        'our_packages': "Bizning paketlar",
        'individual_services': "Shaxsiy xizmatlar",
        'back_services': "Orqaga",
        'orders_back_to_details': "🔙 Buyurtma tafsilotlariga qaytish",
        'linked_orders_back_to_details': "🔙 Buyurtma tafsilotlari",
        'select_service_type': "Xizmat turini tanlang:",
        'press_back_to_return': "Qaytish uchun 'Orqaga' tugmasini bosing",

        'package_meet_me': "«Meni qarshi oling» paketi",
        'airport_pickup': "✈️ Aeroportda kutib olish - Qarshi olish va jo'natish joyigacha kuzatib qo'yish.",
        'transport_to_residence': "🚌 Turar joyga jamoat transportida olib borish - Siz bilan turar joygacha kuzatib qo'yish. Transport xizmatlari narxga kiritilgan.",
        'sim_card_assistance': "📱 SIM-karta ulanilishiga yordam - SIM-karta topshirilishi va aktivlashtirilishi, narxga kiritilgan.",
        'oyster_card_assistance': "🎫 Oyster-kartasini olish - Oyster-kartani olishga yordam, narxga kiritilgan.",
        'regular_reports_to_parents': "📧 Ota-onangizga muntazam hisobotlar - Telegram-bot orqali ota-onangizga sizning jarayoningiz haqida muntazam hisobotlar taqdim etiladi.",

        'package_housing': "«Turar joy» paketi",
        'all_services_meet_me': "🏠 «Meni qarshi oling» paketidagi barcha xizmatlar.",
        'housing_search': "🔍 Turar joy variantlarini qidirish va tanlash (3 tagacha variant) - Sizning mezonlaringizga muvofiq turar joylarni qidirish.",
        'area_consultation': "📍 Turar joy maskani bo'yicha konsultatsiya - Eng maqbul hududni tanlashda yordam.",
        'apartment_viewing': "🏢 Turar joylarni ko'zdan kechirish (3 tagacha variant) video va fotoobzor bilan. Agent turar joyni ko'rib chiqadi va Telegram orqali surat va videoobzor yuboriladi.",
        'temporary_housing_assistance': "🏨 Birinchi kunlar uchun vaqtinchalik turar joy yordami - Agar doimiy turar joy tayyor bo'lmasa, vaqtinchalik turar joy ta'minlanadi.",
        'moving_assistance': "🚚 Yuklarni ko'chirish yordami - Londonda yashab turgan bo'lsangiz, yuklaringizni ko'chirishga yordam. Transport xizmati alohida to'lanadi.",

        'premium_package': "Premium paketi",
        'all_services_housing': "🏠 «Turar joy» paketidagi barcha xizmatlar.",
        'local_registration_assistance': "📝 Local GP (NHS, tibbiy sug'urta) da ro'yxatdan o'tish yordami - Ro'yxatdan o'tish jarayonida yordam.",
        '24_7_support': "🕐 Kelgandan keyingi ilk 7 kun davomida 24/7 yordam Telegram orqali - Onlayn to'liq qo'llab-quvvatlash.",
        'neighbourhood_review': "📊 Turar joy maskani tahlili (Neighbourhood review) - Yashash hududi haqida batafsil tahlil.",
        'utility_connection': "💡 Kommunal xizmatlar ulanilishi - Internet, elektr, gaz va boshqa xizmatlarni ulashga yordam.",
        'bank_account_assistance': "🏦 Bank hisob raqamini ochishga yordam - Bankda hisob raqamini ochish jarayonida yordam.",
        'lease_agreement_assistance': "📜 Ijara shartnomasini tarjima qilish va imzolashga yordam - Shartnomani tarjima qilish va imzolash jarayonida yordam.",
        'premium_moving_assistance': "🚚 Yuklarni ko'chirish yordami - Yuklaringizni ko'chirishni tashkil qilish. Transport xizmati alohida to'lanadi.",
        'gift_from_company': "🎁 Kompaniyadan kichik sovg'a - Foydali maslahatlar va bizdan kichik syurpriz.",

        'public_transport_service': "✈️ Aeroportda kutib olish + 🚌 Jamoat transportida turar joygacha yetkazib qo'yish - £99 ($130). Transport narxga kiritilgan.",
        'private_transfer_service': "✈️ Aeroportda kutib olish + 🚗 Shaxsiy transferda turar joygacha yetkazib qo'yish - £228 ($300).",
        'sim_card_assistance_service': "📱 SIM-kartani ulanilishiga yordam - £23 ($30). SIM-kartani olish va uni faollashtirish.",
        'oyster_card_assistance_service': "🎫 Oyster-kartasini olish - £23 ($30). Kartani olish va faollashtirishga yordam.",
        'regular_reports_service': "📧 Ota-onangizga muntazam hisobotlar - £38 ($50). Telegram-bot orqali sizning jarayoningiz haqida muntazam hisobotlar.",
        'housing_search_service': "🔍 Turar joy variantlarini qidirish va tanlash (3 tagacha variant) - £45 ($60).",
        'area_consultation_service': "📍 Turar joy maskani bo'yicha konsultatsiya - £23 ($30).",
        'temporary_housing_assistance_service': "🏨 Birinchi kunlar uchun vaqtinchalik turar joy yordami - £38 ($50). Agar doimiy turar joy tayyor bo'lmasa.",
        'moving_assistance_service': "🚚 Yuklarni ko'chirish yordami - £76 ($100). Yuklarni ko'chirishni tashkil qilish. Transport xizmati alohida to'lanadi.",
        'local_registration_service': "📝 Local GP (NHS, tibbiy sug'urta) da ro'yxatdan o'tish yordami - £76 ($100). Ro'yxatdan o'tish jarayonida yordam.",
        'support_24_7_service': "🕐 Kelgandan keyingi ilk 7 kun davomida 24/7 yordam - £76 ($100). Telegram orqali to'liq qo'llab-quvvatlash.",
        'neighbourhood_review_service': "📊 Turar joy maskani tahlili (Neighbourhood review) - £38 ($50).",
        'utility_connection_service': "💡 Kommunal xizmatlarni ulanilishi - £76 ($100).",
        'bank_account_assistance_service': "🏦 Bank hisob raqamini ochishga yordam - £38 ($50).",
        'lease_agreement_assistance_service': "📜 Ijara shartnomasini tarjima qilish va imzolashga yordam - £38 ($50).",
        'document_translation': "📄 Hujjatlarni tarjima qilish - £20 ($26) har bir hujjat uchun.",

        'price': "Narx",
        'package_already_in_cart': "Siz allaqachon paketni savatga qo'shdingiz. Bir nechta paket qo'shishingiz mumkin emas.",
        'service_already_in_cart': "Ushbu xizmat allaqachon savatga qo'shilgan.",
        'service_added_to_cart': "Xizmat savatga qo'shildi!",

        'back_ser': "Orqaga",
        'next_ser': "Keyingisi",
        'add_to_cart_services': "Savatchaga qo'shish",
        'main_menu_services': "Asosiy menyu",
        'price_services': "Narxi",
        'services_services': "Xizmatlar",
        'out_of_services': "dan",
        'press_back_or_main_menu_services': "Qaytish uchun 'Orqaga' yoki 'Asosiy menyu' ni bosing",
    },

    'en': {

        'order_status_order_status_update_subscriber': "status of the linked order",

        'payment_status_updated_subscriber': "Dear customer, the payment status of linked order #{order_id} has been updated to '{status}'.\n\nTo view the status of the linked order, go to the main menu, then click on '🔖 Linked Orders', select Order #{order_id}.",

        'from_order_subscriber': "from the linked order",

        'event_added_to_order_part1_subscriber': "📢 Dear customer, to the linked order №",

        'new_admin_message': (
            "❗ Dear customer, 👋\n\n"
            "You have received a new message regarding order #{order_id}. 📨\n\n"
            "Message from the administrator: 📝\n"
            "{message_text}\n\n"
        ),

        # subscribe.py
        'orders_generate_share_link': '🔗 Generate link',
        'orders_share_link_generated': 'A link for your order has been generated: {share_link}',

        # Messages without order_id insertion
        'subscription_success_unregistered': "🎉 You have successfully linked the order. After completing the registration, you can access the order by going to the main menu and clicking on «🔖 Linked Orders».",
        'already_subscribed_registered': 'You have already linked this order to your account. You can view it by going to the main menu and clicking on «🔖 Linked Orders».',
        'subscription_success_registered': '🎉 You have successfully linked the order. You can view it by going to the main menu and clicking on «🔖 Linked Orders».',
        'already_subscribed_unregistered': (
                "🇷🇺 You are already subscribed to the order. Please complete the registration to access the order.\n\n"
                "To start the registration, please enter the command «/start».\n\n"
                "🇺🇿 Buyurtmaga allaqachon bog'langansiz. Iltimos, buyurtmaga kirish uchun ro'yxatdan o'tishni yakunlang.\n\n"
                "Ro'yxatdan o'tishni boshlash uchun «/start» buyrug'ini kiriting.\n\n"
                "🇬🇧 You are already subscribed to the order. Please complete the registration to access the order.\n\n"
                "To start the registration, please enter the command «/start»."
        ),
        'shareable_link_message': 'Here is the link that you can share with anyone. This link will allow them to view your order and track the status of purchased services.',

        'start_registration': 'Start registration',
        'invalid_link': 'Invalid link',

        'linked_orders': '🔖 Linked Orders',
        'change_language': '🌐 Change Language',
        'select_language_prompt': 'Select a language',

        'linked_orders_no_orders': "You have no linked orders.",

        'orders_remove_order': '❌ Unlink order',
        'orders_order_unlinked': 'The order has been successfully unlinked.',

        'orders_confirm_unlink': 'Are you sure you want to unlink this order from yourself?',
        'order_unlinked_part1': 'Order',
        'order_unlinked_part2': 'has been unlinked.',
        'yes': '✅ Yes',
        'no': '❌ No',
        'orders_canceled_unlink': 'Order unlinking has been canceled.',
        'orders_invalid_input': 'Please choose "✅ Yes" or "No".',

        'view_subscribe_properties_info': "To view the status of your linked real estate order, go to the main menu, then click on '🔖 Linked Orders', select the desired order number, and click on '🏡 My Real Estate Requests'.",
        'view_subscribe_tasks_info_message': "To view the status of all tasks in your linked order, go to the main menu, then click on '🔖 Linked Orders', select the desired order number, and click on '📦 My Purchased Services'.",
        'view_bonus_tasks_properties_info': "To view the status of your linked order, go to the main menu, then click on '🔖 Linked Orders', select the desired order number, and click on '🏡 My Real Estate Requests'.",
        'order_subscribe_status_view_orders_info': "To view the status of your linked order, go to the main menu, then click on '🔖 Linked Orders', select the desired order number.",
        'view_subscribe_events_info_message': "To view all events of the linked order, go to the main menu, then click on '🔖 Linked Orders', select the desired order number, and click on '📅 Order Timeline'.",

        'payment_subscribe_status_updated': "Dear customer, the payment status of your linked order #{order_id} has been updated to '{status}'.\n\nTo view the status of your linked order, go to the main menu, then click on '🔖 Linked Orders' and select Order #{order_id}.",

        'orders_timeline': "📅 Order Timeline",

        'event_enter_description': "Enter the event description:",
        'event_enter_link_optional': "Enter the link to the result (optional):",
        'event_added_success': "The event has been successfully added to the order timeline.",
        'skip': "Skip",

        'orders_no_timeline_events': "There are no events in the order timeline.",

        'event_added_to_order_part1': "📢 Dear client, an event has been added to your order №",
        'event_added_to_order_part2': ":",

        'event_added_to_order': "Dear customer, an event has been added to your order №{order_id}:",
        'event_description': "Event description",
        'event_timestamp': "When it occurred",
        'event_link': "Link for viewing",

        "bonus_received_message": "💡 You have received 1 bonus point, which you can use to add another real estate property to your order.",
        "bonus_usage_instructions": "To use your bonus, go to the main menu, then click on '📦 My Orders', select the desired order number, and click on '🎁 My Bonuses'.",



        # addproperty.py
        'load_property_link_prompt': (
            "If you have found a suitable property option on another website, you can add it to the cart. "
            "Just send the link to the page with this property in the chat.\n\n"
            "If you haven't found what you need yet, you can use our '🏡 Search Property' feature to find options."
        ),
        'link_added_success': "The link to the found property has been successfully added to the cart!",
        'not_a_link': "Your message is not recognized as a property link.",
        'link_save_error': "An error occurred while saving the link. Please try again.",
        'back_link': "Back",

        # oferta.py
        "offer_view": "View the Terms and Conditions",
        "offer_message": "You can view the Terms and Conditions by clicking the button below:",

        # common.py
        'main_menu': "Main Menu:",
        'search_property': "🏡 Search Property",
        'add_found_property': "🔗 Add Found Property",
        'my_likes': "❤️ My Likes",
        'cart': "🛒 Cart",
        'our_services': "💠 Our Services",
        'my_orders': "📦 My Orders",
        'profile_menu': "👤 Profile / 🌐 Languages",
        'contacts': "📞 Contacts",
        'what_to_know': "ℹ️ What to Know",  
        'leave_feedback': "📝 Leave Feedback",
        'offer': "📄 Terms and Conditions",
        'admin_panel': "⚙️ Admin Panel",

        # admin.py
        'order_status_accepted': 'Accepted',
        'order_status_returned': 'Returned',
        'order_status_cancelled': 'Cancelled',
        'order_status_pending': 'Pending',
        'order_status_waiting_payment': 'Waiting for payment',
        'order_status_in_progress': 'In Progress',
        'order_status_completed': 'Completed',


        'payment_paid': 'Paid',
        'payment_not_paid': 'Not Paid',
        'payment_status_updated': "Dear customer, the payment status of your order #{order_id} has been updated to '{status}'.\n\nTo check the status of your order, go to the main menu, then select '📦 My Orders' and choose order #{order_id}.",

        'order_status_Оплачено': 'Paid',

        'payment_successful': "Your payment for order #{order_id} was successful. Thank you for your purchase!",
        'payment_error': "An error occurred during payment processing. Please try again.",

        'reservation_date_message': "Date and time of viewing",


        'property_status_waiting_agent': 'At the moment, we are waiting for a response from the agency that owns the property you selected.',
        'property_status_booked': 'We have contacted the agent and scheduled a day for viewing this property.',
        'property_status_going': 'The agent is heading to the property to conduct the viewing.',
        'property_status_in_progress': 'The agent is conducting photo and video shooting of the property.',
        'property_status_viewed': 'The agent has completed the viewing and will share the materials with you soon.',
        'property_status_ready': 'Thank you for waiting. We are attaching photo and video overviews for your review.',
        'property_status_cancelled': 'Unfortunately, the viewing of your property has been canceled.',
        'view_properties_info': "To view the status of all property requests, go to the main menu, then click '📦 My Orders', select the appropriate order number, and click '🏡 My Property Requests'.",

        'dear_client': 'Dear client',
        'property_status_update': 'the status of your property',
        'from_order': 'from order',
        'status_updated_to': 'has been updated to',
        'property_added_by_user': 'Property added by user',

        'task_status_completed': 'Completed',
        'task_status_not_completed': 'Not completed',
        'task_status_in_progress': 'In progress',


        'task_status_status': "The status of the task or service",
        'task_status_in_order': "in order",
        'task_status_has_been_updated': "has been updated to",
        'task_status_completed_message': "Task successfully completed.",
        'task_status_not_completed_message': "The task was not completed. If you believe this is a mistake, contact us [here](t.me/nothardchat).",
        'task_status_in_progress_message': "The task is in progress. We will notify you when it is completed.",
        'view_tasks_info_message': "To view the status of all tasks, go to the main menu, then click on '📦 My Orders', select the order number, and click on '📦 My Purchased Services'.",
        
        'cloud_link_message': "Link to the result",

        'save_property_dear_client': "Dear client,",
        'save_property_status_update_prefix': "The status of your property",
        'save_property_in_order': "in order",
        'save_property_has_been_updated_to': "has been updated to",
        'save_property_cancellation_reason': "Cancellation reason",
        'save_property_bonus_received_message': "💡 You have received 1 bonus point, which you can use to add another property to the order.",
        'save_property_view_bonuses_info': "To do this, go to the main menu, click on '📦 My Orders', select the order number, and click on '🎁 My Bonuses'.",
        'save_property_status_changed_to': "Status changed to",
        'save_property_reason': "Reason",
        'save_property_result_link_saved_for_property': "The result link for the property",
        'save_property_link': "Link",
        'save_property_result_link_saved': "The result link has been saved for the property",

        'dear_client': 'Dear client',
        'order_status_order_status_update': 'the status of your order',
        'order_status_status_updated_to': 'has been updated to',
        'order_status_view_orders_info': "To view the status of your order, go to the main menu, then click on '📦 My Orders' and select the appropriate order number.",

        'property_status_ready_message': "Dear client, the status of your property viewing {title} from order #{order_id} has been updated to 'Result ready'.",
        'property_result_link': "Result link: <a href='{cloud_link}'>{cloud_link}</a>.",
        'view_all_tasks_info': "To view all tasks, go to the main menu, click '📦 My Orders', select order #{order_id}, and then go to '🏡 My Property Requests'.",
        

        'view_tasks_intro': "To view all tasks, go to the main menu, click '📦 My Orders', then select the order",
        'view_tasks_instruction': "and then go to '🏡 My Property Requests'",

        

        # Order statuses
        'order_status_accepted_message': "Your order has been accepted and is being processed.",
        'order_status_returned_message': "Your order has been returned.",
        'order_status_cancelled_message': "Your order has been cancelled.",
        'order_status_pending_message': "Your order is pending.",
        'order_status_waiting_payment_message': "Your order is awaiting payment.",
        'order_status_in_progress_message': "Your order is in progress.",
        'order_status_completed_message': "Your order has been completed.",

        # contacts.py
        'contact_info': (
            "24/7 support contact:\n"
            "Telegram: [t.me/nothardchat](http://t.me/nothardchat)\n"
            "Email: helpme@nothard.uz\n"
            "Phone - Tashkent: +998 88 089 89 10 (Temporarily unavailable)\n"
            "Phone - London: +44 7990 381454\n"
        ),

        # feedback.py
        "feedback_back": "🔙 Back",
        "feedback_please_leave": "Please leave your feedback:",
        "feedback_thank_you": "Thank you for your feedback!",
        "feedback_not_registered": "Your message is not registered as feedback.",

        # orders.py
        'orders_no_orders': "You have no orders.",
        'orders_select_order': "Select an order:",
        'orders_order': "Order",
        'orders_back_to_menu': "🔙 Return to Menu",

        'orders_payment_cash': "Cash 💵",
        'orders_payment_payme': "PayMe 💳",
        'orders_payment_not_specified': "Not specified",
        'orders_paid': "Paid ✅",
        'orders_not_paid': "Not paid ❌",
        'orders_details': (
            "📝 Order Details: \\#{order_id}\n"
            "📅 Date and Time: {order_date}\n"
            "📦 Status: {status}\n"
            "💰 Payment Method: {payment_method}\n"
            "💳 Payment Status: {payment_status}"
        ),

        'orders_subscriber_purchased_services': "📦 Purchased services",
        'orders_subscriber_property_requests': "🏡 Property requests",
        
        'orders_my_purchased_services': "📦 My Purchased Services",
        'orders_my_property_requests': "🏡 My Property Requests",
        'orders_my_bonuses': "🎁 My Bonuses",
        'orders_back_to_orders': "🔙 Back to orders",

        'orders_user_added_property': '🏠 Property added by user',
        'orders_status': 'Status',
        'orders_result_ready': 'Result ready',
        'orders_view_cancelled': 'Viewing canceled',
        'orders_cancellation_reason': 'Cancellation reason',
        'orders_report': 'Report',
        'orders_property_name': 'Property Name',
        'orders_price': 'Price',
        'orders_address': 'Address',
        'orders_not_available': 'N/A',
        'orders_no_properties': 'You have no rented properties.',
        'orders_back': '🔙 Back',
        'orders_link': 'Link',

        'orders_order_not_found': "Error: Order not found.",
        'orders_in_progress': "In Progress",
        'orders_not_completed': "Not Completed",
        'orders_completed': "Completed",
        'orders_package': "Package",
        'orders_package_status': "Package Status",
        'orders_no_services': "You have no purchased services.",

        'orders_document_translation_service': "📄 Translation and signing assistance",
        'orders_lease_agreement_assistance_service': "📜 Lease Agreement Translation and Assistance",
        'orders_airport_pickup': "✈️ Airport Pickup",
        'orders_transport_to_residence': "🚌 Transport to Residence",
        'orders_sim_card_assistance': "📱 SIM Card Assistance",
        'orders_oyster_card_assistance': "🎫 Oyster Card Assistance",
        'orders_regular_reports_to_parents': "📧 Regular Reports to Parents",
        'orders_housing_search': "🔍 Housing Search and Selection",
        'orders_area_consultation': "📍 Area Consultation",
        'orders_apartment_viewing': "🏢 Apartment Viewing",
        'orders_temporary_housing_assistance': "🏨 Temporary Housing Assistance",
        'orders_moving_assistance': "🚚 Moving Assistance",


        'in_progress': "🔄",
        'not_completed': "❌",
        'completed': "✅",


        'orders_bonuses_one_available': "🎁 You have 1 free property addition.",
        'orders_bonuses_multiple_available': "🎁 You have {bonuses} free property additions.",
        'orders_no_bonuses_available': "❌ You have no available bonuses.",
        'orders_search_property': "🔍 Search Property",
        'orders_add_found_property': "➕ Add Found Property",
        'orders_likes': "❤️ Likes",
        'orders_back_to_orders': "🔙 Back to Orders",


        'bonus_zone_1': "Zone 1",
        'bonus_zone_2': "Zone 2",
        'bonus_zone_3': "Zone 3",
        'bonus_zone_4': "Zone 4",
        'bonus_zone_5': "Zone 5",
        'bonus_zone_6': "Zone 6",
        'bonus_zone_unknown': "I don't know",
        'bonus_property_search_waiting': "Please wait, we are searching for properties...",
        'bonus_select_zone': "Select your living zone:",

        'bonus_enter_max_price': "Enter the maximum amount you are willing to spend per month in pounds. Only enter numbers without symbols (e.g., 1500):",
        'bonus_select_rooms': "How many rooms do you want?",

        'bonus_studio': "Studio",
        'bonus_unknown': "I don't know",
        'bonus_select_property_type': "What type of property are you interested in?",
        'bonus_flat': "Flat",
        'bonus_house': "House",
        'bonus_student_housing': "Student accommodation",
        'bonus_furnish_question': "Should the property be furnished?",
        'bonus_furnished': "Furnished",
        'bonus_unfurnished': "Unfurnished",
        'bonus_part_furnished': "Partially furnished",
        'bonus_living_type_question': "Do you want to see options with shared living (House Share)?",
        'bonus_show_house_share': "Yes, show House Share",
        'bonus_dont_show_house_share': "No, don't show House Share",

        'bonus_no_results': "No suitable options were found.",
        'bonus_main_menu': "Main menu",

        'bonus_property_liked': "Property added to likes!",
        'bonus_no_properties_found': "No suitable properties found.",
        'bonus_not_available': "N/A",
        'bonus_price': "Price",
        'bonus_address': "Address",
        'bonus_link': "Link",
        'bonus_of': "of",
        'bonus_prev': "⬅️ Back",
        'bonus_next': "Next ➡️",
        'bonus_like': "Like",
        'bonus_add_to_order': "Add to order",
        'bonus_back_to_bonuses': "Back to bonuses",

        'bonus_order_not_found': "Error: order not found.",
        'bonus_no_properties_available': "Error: no available properties to add.",
        'bonus_no_bonuses_left': "You have no bonuses left to add property to the order.",
        'bonus_property_added': "Property added to the order, and one bonus was deducted!",
        'bonus_back_to_bonuses': "🔙 Back to bonuses",
        'bonus_enter_property_link': "Please enter the link to the found property or press 'Back' to return to bonuses.",

        'bonus_back': "🔙 Back",
        'bonus_enter_property_link': "Please send the link to the found property.",
        'bonus_property_link_added': "The link to the found property has been successfully added to the order, and one bonus was deducted!",
        'bonus_order_not_found': "Error: order not found.",
        'bonus_unexpected_link': "Error: the bot did not expect to receive a link.",
        'bonus_link_save_error': "An error occurred while saving the link. Please try again.",

        'bonus_no_likes': "You have no liked properties added via bonuses.",
        'bonus_not_available': "N/A",
        'bonus_price': "Price",
        'bonus_address': "Address",
        'bonus_link': "Link",
        'bonus_of': "of",
        'bonus_prev': "⬅️ Back",
        'bonus_next': "Next ➡️",
        'bonus_add_to_order': "Add to order",
        'bonus_delete_like': "🗑️ Delete",
        'bonus_back_to_bonuses': "🔙 Back to bonuses",

        'bonus_invalid_index': "Error: Invalid index.",
        'bonus_no_bonuses_left': "You have no bonuses left to add property to the order.",
        'bonus_property_added_from_likes': "Property successfully added to the order! One bonus was deducted.",
        'bonus_like_deleted': "Property removed from likes!",

        'bonus_select_zone': "Select your living zone:",
        'bonus_enter_price': "Enter the maximum amount you're willing to spend per month. Enter only numbers, no symbols (e.g., 1500):",
        'bonus_how_many_rooms': "How many rooms do you want?",
        'bonus_select_property_type': "What type of property are you interested in?",
        'bonus_furnish': "Should the property be furnished?",
        
        # info.py
        "info_choose_info": "Choose what you want to know:",
        "info_bot_features": "💡 What this bot can do",
        "info_useful_info": "ℹ️ Useful Information",
        "info_back": "🔙 Back",
        "info_features_message": (
            "❓ *What this bot can do*\n\n"
            "1. 🏡 *Property Search*: The bot will offer you suitable options. "
            "You can browse, like, and add properties to the cart for ordering.\n\n"
            "2. 🔗 *Add Found Property*: If you found a property on another site, just send the link, and the bot will add it to your cart.\n\n"
            "3. ❤️ *My Likes*: Saved properties that you have liked.\n\n"
            "4. 🛒 *Cart*: All the goods and services you have collected will be stored here for ordering.\n\n"
            "5. 💠 *Our Services*: Here you will find our service packages and individual services that can be added to the cart.\n\n"
            "6. 📦 *My Orders*: Here you can track your orders, view statuses, and use bonuses if available.\n\n"
            "7. 🔖 *Linked Orders*: Orders shared with you by other users are displayed here. You can view purchased services and order details.\n\n"
            "8. 👤 *Profile*: Manage your personal data such as name, phone, and email.\n\n"
            "9. 📞 *Contacts*: Information on how to contact us.\n\n"
            "10. 📝 *Leave a Review*: Share your impressions of our service.\n\n"
            "11. ℹ️ *What You Need to Know*: Important tips and information to help you when searching for property.\n\n"
            "12. 📄 *Public Offer*: Read our public offer agreement."
        ),
        "info_useful_info_message": (
            "ℹ️ *Useful Information*\n\n"
            "1. Many property owners in London require guarantors if you are a foreign citizen. "
            "If you don't have a guarantor, you will need to provide a 6-month prepayment. This does not apply to dormitories.\n\n"
            "2. Dormitories do not require guarantors, but many require a 3-month prepayment and quarterly or semester payments.\n\n"
            "3. When renting housing through agencies, additional documents may be required, such as proof of income, employment contract, and bank statements.\n\n"
            "4. Always check the rental conditions and find out about all additional payments, such as utility bills and internet.\n\n"
            "5. When signing a lease agreement, make sure all terms are clear and recorded in the contract, including rental periods, payment terms, and house rules.\n\n"
            "6. Use trusted websites and agencies when searching for housing to avoid fraud.\n\n"
            "7. Familiarize yourself with the areas where you plan to live to ensure they meet your requirements for safety, infrastructure, and amenities.\n\n"
            "8. If you have questions or issues with renting, seek assistance from lawyers or tenant protection organizations."
        ),

        # profile.py
        'profile_not_found': "Profile not found. Please register.",
        'profile_account': "Your profile:\n{profile}",
        'edit_name': "✏️ Edit Name",
        'edit_phone': "📞 Edit Phone",
        'edit_email': "✉️ Edit Email",
        'edit_language': "🌐 Edit Language",
        'profile_name': "Name",
        'profile_phone': "Phone",
        'profile_email': "Email",
        'profile_language': "Language",
        'back_profile': "🔙 Back",
        'incorrect_language_selection': "Please choose a language from the offered options.",
        'updated': "updated",
        'select_language_prompt': "Select language:",
        'registration': "Registration",
        'enter_new_value': "Enter a new value for {field}:",
        'incorrect_field': "Incorrect field. Please choose again.",
        'field_updated': "{field} updated.",

        # property_search.py
        'property_search_started': "Please wait a moment, we are starting the property search...",
        'property_choose_zone': "Select your living area:",
        'property_enter_max_price': "Enter the maximum amount in pounds you're willing to spend per month. Please enter only numbers, without symbols (e.g., 1500):",
        'property_enter_room_count': "How many rooms do you want?",
        'property_choose_property_type': "What type of property are you interested in?",
        'property_should_furnished': "Should the property be furnished?",
        'property_house_share_option': "Would you like to see options with shared living (House Share)?\n\n1. Yes — show options with House Share.\n2. No — show only options where you will live alone.",
        'property_results_not_found': "No suitable options found.",
        'property_added_to_likes': "We have added this property to your liked list!",
        'property_added_to_cart': "The property has been added to the cart!",
        'property_no_properties_in_cart': "There are no available properties to add to the cart.",
        'property_likes_empty': "You have no liked properties.",
        'property_cart_empty': "Your cart is empty.",
        'property_order_confirmed': "Thank you for your payment! Your order has been confirmed.",
        'property_order_placed': "Your order has been placed! Thank you for your order.",
        'property_order_cancelled': "Your order has been canceled.",
        'property_order_status_updated': "The order status has been updated to '{status}'",
        'property_back_to_main_menu': "Return to menu",
        'property_delete_property_confirmation': "Are you sure you want to remove {item} from the cart?",
        'property_removed': "The item has been successfully removed.",
        'property_removal_cancelled': "Removal has been canceled.",
        'property_basket_summary': "Cart\n\n{summary}",
        'property_order_details': "Order Details\n\n{details}\n\nPayment: {payment_method}\nTotal: {total_price}$",
        'property_place_order_confirmation': "Order total: {total_price}$\n💳 Payment via PayMe is accepted only with Uzcard and Humo cards.\nIf you want to pay with Visa, MasterCard, or other cards, select the 'Cash Payment' option. Our manager will contact you.",
        'property_new_order_notification': "New order from user: {details}",
        'payme_payment_url': "Payment link via PayMe: {payme_url}",
        'property_search_back_to_menu': "🔙 Return to menu",
        'property_search_go_back': "⬅️ Back",
        'property_search_next': "Next ➡️",
        'property_search_like': "❤️ Like",
        'property_search_add_to_cart': "🛒 Cart",
        'property_property': "🏡 *Property*",
        'property_price': "💷 *Price*",
        'property_address': "📍 *Address*",
        'property_link': "🔗 View Property",
        'property_out_of': "out of",
        
        'bonus_show_property': "🏡 *Property:* {title}\n💰 *Price:* {price}\n📍 *Address:* {address}\n🔗 [View Property]({link})\n\nProperty {current_index} out of {total_properties}",


        'zone_1': "Zone 1",
        'zone_2': "Zone 2",
        'zone_3': "Zone 3",
        'zone_4': "Zone 4",
        'zone_5': "Zone 5",
        'zone_6': "Zone 6",
        'zone_unknown': "I don't know",
        'studio': "Studio",
        'rooms_1': "1",
        'rooms_2': "2",
        'rooms_3': "3",
        'rooms_4_plus': "4+",
        'furnished': "Furnished",
        'unfurnished': "Unfurnished",
        'part_furnished': "Partially furnished",
        'house_share_yes': "Yes, show House Share",
        'house_share_no': "No, don't show House Share",
        'property_type_flat': "Flat",
        'property_type_house': "House",
        'property_type_private_halls': "Private Halls",
        'go_back': "⬅️ Back",
        'confirm_removal_button': "Yes",
        'cancel_removal_button': "No",
        'property_search_delete': "🗑️ Delete",


        'payment_method': "Payment Method",


        'cart_is_empty': "🛒 Your cart is empty.",
        'cart_title': "🛒 *Cart*\n\n",
        'property_section_title': "🏡 *Properties:*",
        'no_properties_in_cart': "No properties added.",
        'package_section_title': "📦 *Package Services:*",
        'individual_services_section_title': "🛠️ *Individual Services:*",
        'no_individual_services': "No individual services added.\n",
        'total_price': "💰 *Total: {total_price}$*",
        'property_summary_with_extra': "Viewing {property_count} properties (3 included in the package, {extra_properties} additional viewings at $50 each)",
        'property_summary_without_extra': "Viewing {property_count} properties (3 included in the package)",
        'property_summary_no_package': "Viewing {property_count} properties ({price}$)",
        'delete_property_button': "🗑 Remove property: {title}",
        'delete_package_button': "🗑 Remove package: {service_title}",
        'delete_service_button': "🗑 Remove service: {service_title}",
        'delete_individual_service_button': "🗑 Remove individual service: {service_title}",
        'place_order_button': "🛒 Place Order",
        'main_menu_button_text': "Main Menu",
        'back_to_main_menu': "To return back, press 'Main Menu'",

        'property_remove_like': "Are you sure you want to remove {item} from likes?",
        'property_like_removed': "The item was successfully removed from likes!",
        'property_like_removal_cancelled': "Removal has been canceled.",
        'property_remove_cart': "Are you sure you want to remove {item} from the cart?",
        'property_cart_item_removed': "The item was successfully removed from the cart!",
        'property_cart_removal_cancelled': "Cart removal has been canceled.",
        'property_add_to_cart_success': "The property has been added to the cart!",
        'property_confirm_remove': "Yes",
        'property_cancel_remove': "No",
        'property_error_invalid_index': "Error: The index of the item is invalid.",
        'property_view': "View Property",
        'property_remove_cart_question': "Are you sure you want to remove",
        'property_remove_cart_footer': "from the cart?",

        'confirm_check_info': "Check the information again",
        'confirm_all_correct': "Is everything correct",
        'confirm_agreement': "By clicking 'Yes', you agree to the terms of the Public Offer for service provision and confirm the accuracy of the entered information.",
        'ordered_items': "Ordered items",
        'package_services': "📦 Package Services",
        'individual_services': "🛠️ Individual Services",
        'no_properties': "No properties added.",
        'no_packages': "No packages added.",
        'no_individual_services': "No individual services added.",
        'confirm_order_yes': "Yes",
        'confirm_order_no': "No",
        'property_view_summary': "Viewing {property_count} properties (3 included in the package, {extra_properties} additional viewings at $50 each)",
        'property_view_included': "Viewing {property_count} properties (3 included in the package)",
        'property_view_individual': "Viewing {property_count} properties ($50 each)",

        'payme_button': "Pay via PayMe ({total_price_in_sums} UZS)",
        'cash_payment_button': "Pay in Cash",
        'payment_instructions': (
            "Order amount: {total_price}$\n"
            "💳 Payment via PayMe is only accepted with Uzcard and Humo cards.\n\n"
            "If you want to pay with Visa, MasterCard, or other cards, please select the 'Pay in Cash' option. "
            "Our manager will contact you. You can also reach us [here](t.me/nothardchat)."
        ),
        'user_added_property': "Property added by user",

        'language_label': "🇬🇧 English",  

        'cash_payment': "Cash",  
        'payme_payment': "PayMe",  

        'order_details': "Order Details",
        'order_number': "Order Number",

        'precheckout_error': "Something went wrong. Please try again.",

        'payment_successful': "Thank you for your payment! Your order #{order_id} has been confirmed and paid.",
        'payment_error': "An error occurred while processing your payment. Please try again.",


        'order_accepted': "Your order #{order_id} has been accepted and is being processed. If you have any questions, ask them [here](t.me/nothardchat).",
        'order_returned': "Your order #{order_id} has been returned. If you have any questions, ask them [here](t.me/nothardchat).",
        'order_canceled': "Your order #{order_id} has been canceled. If you have any questions, ask them [here](t.me/nothardchat).",
        'order_pending': "Your order #{order_id} is pending. If you have any questions, ask them [here](t.me/nothardchat).",
        'order_payment_pending': "Your order #{order_id} is pending payment. If you have any questions, ask them [here](t.me/nothardchat).",
        'order_in_progress': "Your order #{order_id} is currently being processed. If you have any questions, ask them [here](t.me/nothardchat).",
        'order_completed': "Your order #{order_id} has been completed. If you have any questions, ask them [here](t.me/nothardchat).",


        'invoice_title': "Payment for Order #{order_id}",
        'invoice_description': "Thank you for your order! Please review the details and proceed with payment.",
        'invoice_details': "Order Details",
        'invoice_confirmation': "By confirming payment, you agree to the order conditions and confirm that all details were reviewed.",
        'invoice_total_price_label': "Total Price",


        # registration.py
        'registration_prompt_name': "Hello! Please register to get started. Provide your name.",
        'registration_cancelled': "Registration canceled. You can start over using the /start command.",
        'registration_prompt_phone': "Please provide your phone number or share it via Telegram:",
        'registration_prompt_email': "Please provide your email:",
        'registration_completed': "Registration completed! You can now use the bot.",
        'registration_error': "An error occurred during registration. Please try again.",
        'welcome_back': "Glad to see you again!",
        'share_phone': "Share phone number",
        'back': "🔙 Back",


        # services.py
        'our_packages': "Our Packages",
        'individual_services': "Individual Services",
        'back_services': "Back",
        'orders_back_to_details': "🔙 Back to order details",
        'linked_orders_back_to_details': "🔙 Back to details",
        'select_service_type': "Select the type of service:",
        'press_back_to_return': "Press 'Back' to return",

        'package_meet_me': "Meet Me Package",
        'airport_pickup': "✈️ Airport Pickup - Escort upon arrival and to the departure point.",
        'transport_to_residence': "🚌 Transport to Residence (by public transport) - Escort to your residence. Transport is included in the price.",
        'sim_card_assistance': "📱 SIM Card Assistance - Provision and activation of the SIM card, included in the price.",
        'oyster_card_assistance': "🎫 Oyster Card Assistance (transport card) - Help with obtaining an Oyster card, included in the price.",
        'regular_reports_to_parents': "📧 Regular Reports to Parents - Providing regular updates to your parents about your process through the Telegram bot.",

        'package_housing': "Housing Package",
        'all_services_meet_me': "🏠 All services from the 'Meet Me' package.",
        'housing_search': "🔍 Housing Search and Selection (up to 3 options) - Searching for suitable housing based on your criteria.",
        'area_consultation': "📍 Area Consultation - Assistance in choosing the most suitable area to live.",
        'apartment_viewing': "🏢 Property Viewing (up to 3 options) with video and photo review. The agent will visit the property, create a review, and share it via Telegram.",
        'temporary_housing_assistance': "🏨 Temporary Housing Assistance for the first few days - Temporary accommodation if the permanent housing is not ready.",
        'moving_assistance': "🚚 Moving Assistance - Help with organizing the transportation of your belongings if you already live in London. The cost of transportation is paid separately.", 

        'premium_package': "Premium Package",
        'all_services_housing': "🏠 All services from the 'Housing' package.",
        'local_registration_assistance': "📝 Assistance with Local Registration (NHS, medical insurance) - Support during the registration process.",
        '24_7_support': "🕐 24/7 Support for the first 7 days after arrival via Telegram - Full online support.",
        'neighbourhood_review': "📊 Neighbourhood Review - A detailed analysis of the area where you plan to live.",
        'utility_connection': "💡 Utility Connection - Assistance in connecting to internet, electricity, gas, and other services.",
        'bank_account_assistance': "🏦 Bank Account Assistance - Support in opening a bank account.",
        'lease_agreement_assistance': "📜 Lease Agreement Translation and Signing Assistance - Support with the translation and signing of the lease agreement.",
        'premium_moving_assistance': "🚚 Moving Assistance - Organization of moving your belongings. The cost of transportation is paid separately.",
        'gift_from_company': "🎁 A Small Gift from the Company - Useful tips and a small surprise from us.",

        'public_transport_service': "✈️ Airport Pickup + 🚌 Transport to Residence (by public transport) - £99 ($130). Escort to your residence. Transport is included in the price.",
        'private_transfer_service': "✈️ Airport Pickup + 🚗 Transport to Residence (by private transfer) - £228 ($300).",
        'sim_card_assistance_service': "📱 SIM Card Assistance - £23 ($30). Help with obtaining and activating a SIM card.",
        'oyster_card_assistance_service': "🎫 Oyster Card Assistance - £23 ($30). Help with obtaining and activating the card.",
        'regular_reports_service': "📧 Regular Reports to Parents - £38 ($50). Providing regular updates to your parents about your process through the Telegram bot.",
        'housing_search_service': "🔍 Housing Search and Selection (up to 3 options) - £45 ($60).",
        'area_consultation_service': "📍 Area Consultation - £23 ($30). Assistance in choosing the most suitable area to live.",
        'temporary_housing_assistance_service': "🏨 Temporary Housing Assistance for the first few days - £38 ($50). Temporary accommodation if the permanent housing is not ready.",
        'moving_assistance_service': "🚚 Moving Assistance - £76 ($100). Help with organizing the transportation of your belongings. The cost of transportation is paid separately.",
        'local_registration_service': "📝 Assistance with Local GP Registration (NHS, medical insurance) - £76 ($100). Support during the registration process.",
        'support_24_7_service': "🕐 24/7 Support for the first 7 days after arrival - £76 ($100). Full support through Telegram.",
        'neighbourhood_review_service': "📊 Neighbourhood Review - £38 ($50). A detailed analysis of the area.",
        'utility_connection_service': "💡 Utility Connection - £76 ($100). Assistance in connecting internet, electricity, and gas.",
        'bank_account_assistance_service': "🏦 Bank Account Assistance - £38 ($50). Support in opening a bank account.",
        'lease_agreement_assistance_service': "📜 Lease Agreement Translation and Signing Assistance - £38 ($50). Support with translation and signing of the lease agreement.",
        'document_translation': "📄 Document Translation - £20 ($26) per document. Translation and assistance with document processing.",


        'price': "Price",
        'package_already_in_cart': "You have already added a package to the cart. You cannot add more than one package.",
        'service_already_in_cart': "This service is already in the cart.",
        'service_added_to_cart': "The service has been added to the cart!",

        'back_ser': "Back",
        'next_ser': "Next",
        'add_to_cart_services': "Add to Cart",
        'main_menu_services': "Main Menu",
        'price_services': "Price",
        'services_services': "Services",
        'out_of_services': "out of",
        'press_back_or_main_menu_services': "To return, press 'Back' or 'Main Menu'",
    },
}

def get_message(language, key, **kwargs):
    # Получаем словарь сообщений для указанного языка, если язык не найден, используем 'ru' по умолчанию
    messages = MESSAGES.get(language, MESSAGES['ru'])
    
    # Получаем шаблон сообщения по ключу, если ключ не найден, возвращаем сообщение с указанием отсутствующего ключа
    message_template = messages.get(key, f"Сообщение не найдено для ключа: '{key}'")
    
    # Проверка наличия всех необходимых ключей в kwargs перед форматированием
    try:
        return message_template.format(**kwargs)
    except KeyError as e:
        # Логируем ошибку, включая информацию о недостающем ключе
        missing_key = e.args[0]
        logger.error(f"KeyError: Missing key '{missing_key}' for message '{key}' in language '{language}'. Provided kwargs: {kwargs}")
        return f"Ошибка: недопустимый формат сообщения. Отсутствует ключ: {missing_key}"
    except Exception as e:
        # Логируем другие возможные ошибки
        logger.error(f"Unexpected error while formatting message '{key}' in language '{language}': {str(e)}")
        return "Ошибка: недопустимый формат сообщения."