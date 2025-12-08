from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters, MessageHandler
from telegram.constants import ParseMode
from Word import Word
from AnkiLoader import AnkiLoader
import json
import os

############################################
#           Configuration Loading          #
############################################

"""
This section of the code is responsible for loading configuration settings from the `config.json` file.
If the file does not exist, it is created with default values for the Telegram Bot API key and the Anki endpoint.

Before running the bot, ensure that:
1. You have configured your `TELEGRAM_BOT_API` key.
2. You have set the `ANKI_ENDPOINT` (if necessary).

Default values:
- `TELEGRAM_BOT_API`: Placeholder for your Telegram Bot API key.
- `ANKI_ENDPOINT`: Defaults to `http://localhost:8765` (AnkiConnect default endpoint).
"""

config_path = os.path.abspath(os.path.join(__file__, "../../config.json"))

# Check if config.json exists, if not, create it with default values
if not os.path.exists(config_path):
    default_config = {
        "TELEGRAM_BOT_API": "YOUR_TELEGRAM_BOT_API",
        "ANKI_ENDPOINT": "http://localhost:8765" # as default value
    }
    with open(config_path, "w") as config_file:
        json.dump(default_config, config_file, indent=4)

# Load configuration from config.json
with open(config_path) as config_file:
    config = json.load(config_file)

TELEGRAM_TOKEN = config["TELEGRAM_BOT_API"] 
ANKI_ENDPOINT = config["ANKI_ENDPOINT"] # default http://localhost:8765

# Check if TELEGRAM_TOKEN is set
if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_API":
    raise ValueError("TELEGRAM_BOT_API is not set or invalid. Please configure it in config.json.")

## --- + Constants +--- ##
DECK_NAME = "EnglishWords"
MODEL_NAME = "DankY"

############################################
#               BOT COMMANDS               #
############################################

# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Welcome to your DankY assistant for Anki!*\n\n"

        "If you're a language learner and you use Anki every day, "
        "you probably know how tedious it is to create flashcards manually. "
        "Collecting *definitions*, *examples*, *IPA*, *translations*, *synonyms*, and *antonyms* over and over can get boring fast.\n\n"

        "🤖 *What is DankY?*\n"
        "DankY is *an automated Telegram bot that generates flashcards for you using open-source dictionaries.* "
        "Currently it supports English vocabulary, with more languages like German coming soon!\n\n"

        "✨ *Features*\n"
        "🇬🇧 Generates English flashcards based on the Free Dictionary API\n"
        "🗂️ Includes up to 15 definition–example pairs, plus IPA, translations, synonyms, and antonyms\n\n"

        "⚙️ *How to use DankY?*\n"
        "1. Make sure Anki is running with AnkiConnect enabled\n"
        "2. Send me a word in English (German support coming soon!)\n"
        "3. Wait a few seconds ⏳\n"
        "4. Receive confirmation when the flashcard is added\n\n"

        "🧠 *Goal*\n"
        "Automate sentence mining: you study, DankY does the hard work.\n\n"

        "🚧 *Note:* DankY is still in development, but it’s already usable.\n"
        "🧪 *Version:* 1.0 (beta)\n\n"

        "💻 *Developer:* @zTamiel\n\n"
        "✍️ *Send me a word to get started!*",
        parse_mode=ParseMode.MARKDOWN
    )

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 How it works:\n"
        "• Send a single English word\n"
        "• The bot fetches definitions, examples, synonyms, antonyms, IPA, and Italian translation\n"
        "• The flashcard is added to your Anki deck automatically\n\n"
        "Commands available:\n"
        "• /start — Welcome message\n"
        "• /help — Show this help message\n"
        "• /about — Links to the github of this bot"
    )

# /about command
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hey there! *Want to supercharge your language learning journey*?\n\n"
        "📚 This bot instantly creates Anki flashcards for any English word — _definitions_, _examples_, _IPA_, and even _translations_ included!\n\n"
        "💻 Check out the source code and updates on *GitHub*.\n\n"
        "👤 _ - Built with ❤️ by *@zTamiel*, a passionate coder and language lover_",
        parse_mode=ParseMode.MARKDOWN,

        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Visit GitHub", url="https://github.com/aldomelpignano/DankY")]])
    )

# Handle incoming words
async def handle_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.strip()
    words = [w.strip() for w in raw_text.split(",") if w.strip()]

    anki = AnkiLoader(deck_name=DECK_NAME, endpoint=ANKI_ENDPOINT, model_name=MODEL_NAME)

    try:
        # Test connection to Anki
        anki._tryConnectionToAnki()
    except Exception as e:
        await update.message.reply_text(f"⚠️ Cannot connect to Anki: {e}")
        return

    for word in words:
        try:
            word_obj = Word(word)
            lemma = word_obj.lemmatize()

            msg = await update.message.reply_text(f"🔍 Processing '{lemma}'...")

            # Let AnkiLoader handle duplicates and errors
            anki.addNotes(word_obj)

            await msg.edit_text(f"✅ '{lemma}' added successfully to Anki!")

        except Exception as e:
            await update.message.edit_text(f"🚫 Error processing '{word}': {str(e)}")


# MAIN
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_word))

    print("Bot is running...")
    app.run_polling()