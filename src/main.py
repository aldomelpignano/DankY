from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters, MessageHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from Word import Word
from AnkiLoader import AnkiLoader
from DeckManager import DeckManager
from lang import LanguageManager
import json
import os

############################################
#           Configuration Loading          #
############################################

# Determine absolute path to the config.json file (two levels up from this script)
config_path = os.path.abspath(os.path.join(__file__, "../../config.json"))

# Check if config.json exists; if not, create it with default values
if not os.path.exists(config_path):
    default_config = {
        "TELEGRAM_BOT_API": "YOUR_TELEGRAM_BOT_API",
        "ANKI_ENDPOINT": "http://localhost:8765"
    }
    with open(config_path, "w") as config_file:
        json.dump(default_config, config_file, indent=4)

# Load configuration from config.json
with open(config_path) as config_file:
    config = json.load(config_file)

TELEGRAM_TOKEN = config["TELEGRAM_BOT_API"]  # Telegram Bot API token
ANKI_ENDPOINT = config["ANKI_ENDPOINT"]      # AnkiConnect endpoint

# Ensure TELEGRAM_TOKEN is set correctly
if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_API":
    raise ValueError("TELEGRAM_BOT_API is not set or invalid. Please configure it in config.json.")

## --- + Constants +--- ##
# Initialize DeckManager and load default deck safely
deck_manager = DeckManager()
try:
    DECK_NAME = deck_manager.get_loaded_deck()
except ValueError:
    DECK_NAME = None  # fallback if no deck selected

MODEL_NAME = "DankY"  # Anki model used for notes

# Initialize LanguageManager instance to handle localization and translations
lang_manager = LanguageManager()

# Load localized messages
locale = lang_manager.load_locale()

############################################
#               BOT COMMANDS               #
############################################

# /start command: sends a greeting message
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(locale["start"], parse_mode=ParseMode.MARKDOWN)

# /help command: provides instructions or help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(locale["help"], parse_mode=ParseMode.MARKDOWN)

# /about command: shows info about the bot, including a GitHub link
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        locale["about"],
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(locale.get("about_github_button", "GitHub"), url="https://github.com/aldomelpignano/DankY")]]
        )
    )

# /lang command: lets user select bot language
async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    available_languages = lang_manager.get_available_languages()  # Fetch supported languages
    languages_list = list(available_languages.items())
    buttons_per_row = 2  # Number of language buttons per row

    # Create inline keyboard for language selection
    keyboard = [
        [
            InlineKeyboardButton(name_flag, callback_data=f"set_lang:{code}")
            for code, name_flag in languages_list[i:i + buttons_per_row]
        ]
        for i in range(0, len(languages_list), buttons_per_row)
    ]
    
    await update.message.reply_text(locale.get("BOT_select_language"), reply_markup=InlineKeyboardMarkup(keyboard))

# Callback handler for inline language buttons
async def lang_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global locale
    query = update.callback_query
    await query.answer()  # Acknowledge button press

    data = query.data
    if data.startswith("set_lang:"):
        lang_code = data.split(":")[1]  # Extract language code from callback data

        # Update language settings in LanguageManager and config.json
        lang_manager.set_languages(
            bot_lang=lang_code,
            target_lang=lang_manager.target_language,         # Keep current target language
            translation_lang=lang_manager.translation_language  # Keep current translation language
        )
        
        # Reload localized messages for the new language
        locale = lang_manager.load_locale()

        # Notify user that language has changed
        await query.edit_message_text(locale.get("BOT_changed_language"))

# /deck command: user specifies which deck to use
async def deck_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the user provided a deck name
    if len(context.args) == 0:
        await update.message.reply_text(locale.get("no_deck_name_provided"), parse_mode=ParseMode.MARKDOWN)
        return

    deck_name = " ".join(context.args) # Combine args in case deck name has spaces

    # Initialize DeckManager
    manager = DeckManager()

    # Check if the specified deck exists
    if not manager.check_deck_existence(deck_name):
        await update.message.reply_text(locale.get("deck_not_found").format(deck=deck_name), parse_mode=ParseMode.MARKDOWN)
        return

    # Set the selected deck
    manager.set_deck(deck_name)
    global DECK_NAME
    DECK_NAME = deck_name  # update global variable for use in handle_word
    await update.message.reply_text(locale.get("deck_set_success").format(deck=deck_name), parse_mode=ParseMode.MARKDOWN)

# Handle incoming words sent by user (non-command messages)
async def handle_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if DECK_NAME is None:
        await update.message.reply_text(locale.get("no_deck_selected"), parse_mode=ParseMode.MARKDOWN)
        return

    raw_text = update.message.text.strip()  # Clean extra whitespace
    words = [w.strip() for w in raw_text.split(",") if w.strip()]  # Split comma-separated words

    # Initialize AnkiLoader with deck and model information
    anki = AnkiLoader(deck_name=DECK_NAME, endpoint=ANKI_ENDPOINT, model_name=MODEL_NAME)

    # Try connecting to Anki
    try:
        anki._tryConnectionToAnki()
    except Exception as e:
        await update.message.reply_text(locale["anki_connection_error"].format(error=str(e)))
        return

    # Process each word
    for word in words:
        try:
            word_obj = Word(word)         # Create Word object
            lemma = word_obj.lemmatize()  # Lemmatize the word

            msg = await update.message.reply_text(locale["processing"].format(word=lemma))

            anki.addNotes(word_obj)  # Add note to Anki

            # Confirm success to the user
            await msg.edit_text(locale["success"].format(word=lemma))

        except Exception as e:
            await update.message.reply_text(locale["error"].format(word=word, error=str(e)))

############################################
#                   MAIN                   #
############################################

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add handlers for commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("deck", deck_command))
    app.add_handler(CommandHandler("lang", lang_command))

    # Handle inline button callbacks
    app.add_handler(CallbackQueryHandler(lang_button_callback, pattern=r"^set_lang:"))

    # Handle regular text messages (treated as words to add to Anki)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_word))

    print("Bot is running...")
    app.run_polling()
