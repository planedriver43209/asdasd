import asyncio
import os
from bot import initialize_bot

# Entry point of the application
if __name__ == "__main__":
    # Start the bot
    bot = initialize_bot()
    asyncio.run(bot.start_bot())
