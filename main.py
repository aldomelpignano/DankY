###############################################################################
# main.py
#
# Main entry point for the DankY Telegram bot.
# Initializes the bot and starts the event loop.
###############################################################################

import asyncio
import nest_asyncio 
from src.bot.telegram_bot import TelegramBot

nest_asyncio.apply()

def main():
    bot = TelegramBot() 
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.run())

if __name__ == "__main__":
    main()
