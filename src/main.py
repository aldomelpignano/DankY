# src/main.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters, MessageHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from Word import Word
from AnkiLoader import AnkiLoader
from DeckManager import DeckManager
from LanguageManager import LanguageManager
import json
import os
import csv
import tempfile
import openpyxl
from logger import log  # import the logger wrapper

# #################################################
#                 CONFIGURATION                  #
# #################################################

# Determine absolute path to the config.json file (two levels above this script)
config_path = os.path.abspath(os.path.join(__file__, "../../config.json"))

# If config.json does not exist, create it with default values
if not os.path.exists(config_path):
    default_config = {
        "TELEGRAM_BOT_API": "YOUR_TELEGRAM_BOT_API",
        "ANKI_ENDPOINT": "http://localhost:8765",
        "BOT_LANGUAGE": "en",
        "TARGET_LANGUAGE": "en",
        "TRANSLATION_LANGUAGE": None,
        "SELECTED_DECK": None
    }
    with open(config_path, "w") as config_file:
        json.dump(default_config, config_file, indent=4)

# Load configuration from config.json
with open(config_path) as config_file:
    config = json.load(config_file)

TELEGRAM_TOKEN = config["TELEGRAM_BOT_API"]
ANKI_ENDPOINT = config["ANKI_ENDPOINT"]

# Check that Telegram token is valid
if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_API":
    raise ValueError("TELEGRAM_BOT_API is not set or invalid. Please configure it in config.json.")

# #################################################
#                  CONSTANTS                     #
# #################################################

# Initialize DeckManager and load default deck if selected
deck_manager = DeckManager()
try:
    DECK_NAME = deck_manager.get_loaded_deck()
except ValueError:
    DECK_NAME = None  # fallback if no deck selected

MODEL_NAME = "DankY"  # default Anki model

## language manager and LOCALE loading
lang_manager = LanguageManager()  # handle localization and translation

LOCALE = lang_manager.load_locale()  # load messages in selected bot language
TARGET_LANGUAGE = lang_manager.get_target_language()
TRANSLATION_LANGUAGE = lang_manager.get_translation_language()


# #################################################
#                  BOT COMMANDS                  #
# #################################################

# /start command: sends greeting message
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LOCALE["start"], parse_mode=ParseMode.MARKDOWN)

# /help command: sends instructions/help text
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(LOCALE["help"], parse_mode=ParseMode.MARKDOWN)

# /about command: shows bot info and GitHub link
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        LOCALE["about"],
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(LOCALE.get("about_github_button", "GitHub"), url="https://github.com/aldomelpignano/DankY")]]
        )
    )

# /lang command: allow user to select bot language
async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    available_languages = lang_manager.get_available_languages()  # get supported languages
    languages_list = list(available_languages.items())
    buttons_per_row = 2

    # Create inline keyboard for language selection
    keyboard = [
        [
            InlineKeyboardButton(name_flag, callback_data=f"set_lang:{code}")
            for code, name_flag in languages_list[i:i + buttons_per_row]
        ]
        for i in range(0, len(languages_list), buttons_per_row)
    ]
    
    await update.message.reply_text(LOCALE.get("BOT_select_language"), reply_markup=InlineKeyboardMarkup(keyboard))

# Callback handler for inline language buttons
async def lang_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LOCALE
    query = update.callback_query
    await query.answer()  # acknowledge the button press

    data = query.data
    if data.startswith("set_lang:"):
        lang_code = data.split(":")[1]

        # Update bot language in LanguageManager and save in config.json
        lang_manager.set_languages(
            bot_lang=lang_code,
            target_lang=lang_manager.target_language,
            translation_lang=lang_manager.translation_language
        )
        
        # Reload localized messages
        LOCALE = lang_manager.load_locale()

        # Notify user of successful language change
        await query.edit_message_text(LOCALE.get("BOT_changed_language"))

# /deck command: set the deck to be used
async def deck_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text(LOCALE.get("no_deck_name_provided"), parse_mode=ParseMode.MARKDOWN)
        return

    deck_name = " ".join(context.args)
    manager = DeckManager()

    # Check if deck exists in Anki
    if not manager.check_deck_existence(deck_name):
        await update.message.reply_text(LOCALE.get("deck_not_found").format(deck=deck_name), parse_mode=ParseMode.MARKDOWN)
        return

    # Set selected deck in config
    manager.set_deck(deck_name)
    global DECK_NAME
    DECK_NAME = deck_name
    await update.message.reply_text(LOCALE.get("deck_set_success").format(deck=deck_name), parse_mode=ParseMode.MARKDOWN)

# #################################################
#                WORD HANDLER                     #
# #################################################

async def handle_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ensure a deck is selected
    if DECK_NAME is None:
        await update.message.reply_text(LOCALE.get("no_deck_selected"), parse_mode=ParseMode.MARKDOWN)
        return

    # Clean input text
    raw_text = update.message.text.replace("\u200b", "").replace("\r", "").strip()
    words = [w.strip().lower() for w in raw_text.replace("\n", " ").replace(",", " ").split() if w.strip()]

    log(f"Raw input: {update.message.text}", level="DEBUG")
    log(f"Cleaned words list: {words}", level="DEBUG")

    # Initialize Anki loader
    anki = AnkiLoader(deck_name=DECK_NAME, endpoint=ANKI_ENDPOINT, model_name=MODEL_NAME)

    # Attempt connection to Anki
    try:
        log("Trying to connect to Anki...", level="DEBUG")
        anki._tryConnectionToAnki()
        log("Connected to Anki successfully!", level="DEBUG")
    except Exception as e:
        log(f"Anki connection failed: {e}", level="ERROR")
        await update.message.reply_text(f"Anki connection failed: {str(e)}")
        return

    # Process each word
    for word in words:
        try:
            log(f"Processing word: {word}", level="DEBUG")
            word_obj = Word(word, learning_language=TARGET_LANGUAGE, translation_language=TRANSLATION_LANGUAGE)
            lemma = word_obj.lemmatize()
            log(f"Lemmatized word: {lemma}", level="DEBUG")

            msg = await update.message.reply_text(LOCALE["processing"].format(word=lemma))

            # Add note to Anki
            log(f"Adding note for: {lemma}", level="DEBUG")
            anki.addNotes(word_obj)
            log(f"Note added successfully for: {lemma}", level="DEBUG")

            # Notify user of success
            await msg.edit_text(LOCALE["success"].format(word=lemma))

        except Exception as e:
            log(f"Error processing word '{word}': {e}", level="ERROR")
            msg = await update.message.reply_text(LOCALE["error_processing_word"].format(word=lemma, error=str(e)))


# file import handler
async def handle_import_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ensure a deck is selected
    deck_name = deck_manager.get_loaded_deck()
    if deck_name is None:
        await update.message.reply_text(LOCALE.get("no_deck_selected"), parse_mode=ParseMode.MARKDOWN)
        return

    file_doc = update.message.document
    filename = file_doc.file_name.lower()

    allowed_ext = (".xlsx", ".csv", ".tsv", ".txt")
    if not filename.endswith(allowed_ext):
        await update.message.reply_text(LOCALE.get("file_unsupported_format"), parse_mode=ParseMode.MARKDOWN)
        return

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
    file_bytes = await file_doc.get_file()
    await file_bytes.download_to_drive(temp.name)

    words = []

    # Parse file depending on format
    try:
        if filename.endswith(".xlsx"):
            wb = openpyxl.load_workbook(temp.name)
            sheet = wb.active
            for row in sheet.iter_rows(values_only=True):
                if row[0] is not None:
                    words.append(str(row[0]).strip())
        elif filename.endswith(".csv"):
            with open(temp.name, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0].strip():
                        words.append(row[0].strip())
        elif filename.endswith(".tsv"):
            with open(temp.name, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter="\t")
                for row in reader:
                    if row and row[0].strip():
                        words.append(row[0].strip())
        elif filename.endswith(".txt"):
            with open(temp.name, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        words.append(line)
    except Exception as e:
        log(f"Error reading file '{filename}': {e}", level="ERROR")
        await update.message.reply_text(LOCALE.get("file_read_error").format(filename=filename, error=str(e)))
        return

    if not words:
        await update.message.reply_text(LOCALE.get("file_empty"), parse_mode=ParseMode.MARKDOWN)
        return

    anki = AnkiLoader(deck_name=deck_name, endpoint=ANKI_ENDPOINT, model_name=MODEL_NAME)

    try:
        anki._tryConnectionToAnki()
    except Exception as e:
        await update.message.reply_text(LOCALE.get("anki_connection_error").format(error=str(e)))
        return

    await update.message.reply_text(LOCALE.get("file_import_started").format(num_words=len(words)), parse_mode=ParseMode.MARKDOWN)

    imported = 0
    errors = 0

    for word in words:
        try:
            word_obj = Word(word, learning_language=TARGET_LANGUAGE, translation_language=TRANSLATION_LANGUAGE)
            lemma = word_obj.lemmatize()
            anki.addNotes(word_obj)
            imported += 1
        except Exception:
            errors += 1

    await update.message.reply_text(
        LOCALE.get("file_import_completed").format(imported=imported, errors=errors),
        parse_mode=ParseMode.MARKDOWN,
    )

# #################################################
#                       MAIN                      #
# #################################################

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("deck", deck_command))
    app.add_handler(CommandHandler("lang", lang_command))
    app.add_handler(CallbackQueryHandler(lang_button_callback, pattern=r"^set_lang:"))

    # Handle text messages and file uploads
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_word))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_import_file))

    log("Bot is running...", level="DEBUG")
    app.run_polling()
