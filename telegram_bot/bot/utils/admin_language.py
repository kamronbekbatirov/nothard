# bot/handlers/language.py

messages = {
        'package_meet_me': "Пакет «Встреть меня»",
        'airport_pickup': "✈️ Встреча в аэропорту",
        'transport_to_residence': "🚌 Транспорт до места проживания (общественным транспортом)",
        'sim_card_assistance': "📱 Помощь с подключением SIM-карты",
        'oyster_card_assistance': "🎫 Получение Oyster-карты (транспортная карта)",
        'regular_reports_to_parents': "📧 Регулярные отчеты родителям",

        'package_housing': "Пакет «Жилье»",
        'all_services_meet_me': "🏠 Все услуги из пакета «Встреть меня».",
        'housing_search': "🔍 Поиск и подбор вариантов жилья (до 3 вариантов)",
        'area_consultation': "📍 Консультация по выбору района для проживания",
        'apartment_viewing': "🏢 Организация просмотра недвижимости (до 3 вариантов) с видео и фотообзором.",
        'temporary_housing_assistance': "🏨 Помощь с временным жильем на первые дни",
        'moving_assistance': "🚚 Перевозка вещей",

        'premium_package': "Премиум пакет",
        'all_services_housing': "🏠 Все услуги из пакета «Жилье».",
        'local_registration_assistance': "📝 Помощь с регистрацией в Local GP (NHS, медицинская страховка)",
        '24_7_support': "🕐 Поддержка 24/7 на первые 7 дней после заезда в страну через Telegram",
        'neighbourhood_review': "📊 Оценка района проживания (Neighbourhood review)",
        'utility_connection': "💡 Подключение к коммунальным услугам",
        'bank_account_assistance': "🏦 Помощь с открытием банковского счета",
        'lease_agreement_assistance': "📜 Перевод и помощь с подписанием договора аренды",
        'premium_moving_assistance': "🚚 Перевозка вещей",
        'gift_from_company': "🎁 Маленький подарок от компании",
        

        'public_transport_service': "✈️ Встреча в аэропорту + 🚌 Транспорт до места проживания (общественным транспортом).",
        'private_transfer_service': "✈️ Встреча в аэропорту + 🚗 Транспорт до места проживания (частный трансфер)",
        'sim_card_assistance_service': "📱 Помощь с подключением SIM-карты",
        'oyster_card_assistance_service': "🎫 Получение Oyster-карты (транспортная карта)",
        'regular_reports_service': "📧 Регулярные отчеты родителям",
        'housing_search_service': "🔍 Поиск и подбор вариантов жилья (до 3 вариантов)",
        'area_consultation_service': "📍 Консультация по выбору района для проживания",
        'temporary_housing_assistance_service': "🏨 Помощь с временным жильем на первые дни",
        'moving_assistance_service': "🚚 Перевозка вещей",
        'local_registration_service': "📝 Помощь с регистрацией в Local GP (NHS, медицинская страховка)",
        'support_24_7_service': "🕐 Поддержка 24/7 на первые 7 дней после заезда в страну",
        'neighbourhood_review_service': "📊 Оценка района проживания (Neighbourhood review)",
        'utility_connection_service': "💡 Подключение к коммунальным услугам",
        'bank_account_assistance_service': "🏦 Помощь с открытием банковского счета",
        'lease_agreement_assistance_service': "📜 Перевод и помощь с подписанием договора аренды",
        'document_translation': "📄 Перевод документов",

        'task_status_completed': 'Выполнено',
        'task_status_not_completed': 'Не выполнено',
        'task_status_in_progress': 'Выполняется',

        'Ожидание ответа агента': 'Ожидание ответа агента',
        'Бронь забронирована': 'Бронь забронирована',
        'Иду смотреть': 'Иду смотреть',
        'Идет просмотр объекта': 'Идет просмотр объекта',
        'Объект просмотрен': 'Объект просмотрен',
        'Результат готов': 'Результат готов',
        'Просмотр отменен': 'Просмотр отменен',

        'property_added_by_user': 'Недвижимость, добавленная пользователем',
        'link_to_object': 'Ссылка на объект',
}

def get_message(key: str) -> str:
    """
    Возвращает переведённое сообщение для данного ключа.
    Если ключ не найден, возвращает сам ключ.
    """
    return messages.get(key, key)