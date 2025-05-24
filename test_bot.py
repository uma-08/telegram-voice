import asyncio
from telegram import Bot
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get the token
token = os.getenv('TELEGRAM_BOT_TOKEN')

async def main():
    bot = Bot(token=token)
    try:
        bot_info = await bot.get_me()
        print("✅ Bot token is valid!")
        print(f"Bot username: @{bot_info.username}")
        print(f"Bot name: {bot_info.first_name}")
    except Exception as e:
        print("❌ Error: Invalid bot token or connection issue")
        print(f"Error details: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 