import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

# Load env variables
load_dotenv(".env")

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def reset_webhook():
    if not TOKEN:
        print("Error: No TELEGRAM_TOKEN found in .env")
        return

    print(f"Connecting with token: {TOKEN[:5]}...{TOKEN[-5:]}")
    bot = Bot(TOKEN)
    
    # 1. Get current status
    print("Checking current Webhook status...")
    info = await bot.get_webhook_info()
    print(f"Current Webhook URL: {info.url}")
    print(f"Pending updates: {info.pending_update_count}")
    
    if info.url:
        print("⚠️ A webhook is currently set! This is likely n8n.")
        print("Attempting to delete webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook deleted successfully. Polling should work now.")
    else:
        print("✅ No webhook was set. You were already in polling mode.")
        print("If the bot wasn't working, it might be a local process conflict or logic error.")

if __name__ == "__main__":
    asyncio.run(reset_webhook())
