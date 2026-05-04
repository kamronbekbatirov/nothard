# bot/utils/notifications.py

import requests
import logging

logger = logging.getLogger(__name__)

def send_notification(chat_id: int, message: str, bot_token: str, parse_mode: str = "HTML") -> bool:
    """
    Отправляет сообщение пользователю или группе через Telegram-бота.

    Args:
        chat_id (int): ID чата получателя.
        message (str): Текст сообщения.
        bot_token (str): Токен вашего Telegram-бота.
        parse_mode (str): Режим разметки (например, 'HTML' или 'Markdown').

    Returns:
        bool: True, если сообщение отправлено успешно, иначе False.
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logger.info(f"Notification sent to chat_id {chat_id}.")
            return True
        else:
            logger.error(f"Failed to send notification to chat_id {chat_id}. Status Code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception occurred while sending notification to chat_id {chat_id}: {e}")
        return False