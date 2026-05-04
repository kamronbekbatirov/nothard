import asyncio
import telegram
from config import BOT_TOKEN

async def main():
    bot = telegram.Bot(token=BOT_TOKEN)
    
    # Fetch updates from the bot
    updates = await bot.get_updates()

    for update in updates:
        if update.message and update.message.chat.type in ['group', 'supergroup']:
            print("Chat ID:", update.message.chat.id)
            break

if __name__ == '__main__':
    asyncio.run(main())