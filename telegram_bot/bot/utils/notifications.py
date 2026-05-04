# bot/utils/notifications.py
from telegram import Bot

async def send_notification(user_id, message, token):
    bot = Bot(token=token)
    msg = await bot.send_message(chat_id=user_id, text=message)
    return msg.message_id