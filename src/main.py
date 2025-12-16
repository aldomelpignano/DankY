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

########################################################
#                   Language Manager                   #
########################################################
# /lang command: allow user to select bot language
async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display language selection menu: BOT_language, Translation_language, Target_language"""

    keyboard = [
        [InlineKeyboardButton(LOCALE.get("inline_bot_language"), callback_data="lang_select:bot")],
        [InlineKeyboardButton(LOCALE.get("inline_target_language"), callback_data="lang_select:target")],
        [InlineKeyboardButton(LOCALE.get("inline_translation_language"), callback_data="lang_select:translation")]
    ]

    await update.message.reply_text(LOCALE.get("select_language"), reply_markup=InlineKeyboardMarkup(keyboard))


# Callback handler for multi-level language selection
async def lang_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle multi-level language selection menus"""
    global LOCALE

    query = update.callback_query
    await query.answer()
    data = query.data

    # #################################################
    #                    Back button                  #
    # #################################################
    if data == "lang_back":
        # go back to main language menu
        keyboard = [
            [InlineKeyboardButton(LOCALE.get("inline_bot_language"), callback_data="lang_select:bot")],
            [InlineKeyboardButton(LOCALE.get("inline_target_language"), callback_data="lang_select:target")],
            [InlineKeyboardButton(LOCALE.get("inline_translation_language"), callback_data="lang_select:translation")]
        ]

        await query.edit_message_text(LOCALE.get("select_language"), reply_markup=InlineKeyboardMarkup(keyboard))
        return # end 

    # #################################################
    #              Level 1: Choose language type     #
    # #################################################
    if data.startswith("lang_select:"):
        lang_type = data.split(":")[1]

        if lang_type == "bot":
            # show available bot languages from locales/yaml
            languages_list = list(lang_manager.get_available_languages().items())
            buttons_per_row = 2  # number of buttons per row
            keyboard = []
    
            # create buttons in rows
            for i in range(0, len(languages_list), buttons_per_row):
                row = []
                for code, name_flag in languages_list[i:i + buttons_per_row]:
                    row.append(InlineKeyboardButton(name_flag, callback_data=f"set_lang:bot:{code}"))
                keyboard.append(row)
            keyboard.append([InlineKeyboardButton(LOCALE.get("back"), callback_data="lang_back")])
            await query.edit_message_text(LOCALE.get("select_bot_language"), reply_markup=InlineKeyboardMarkup(keyboard))

        elif lang_type == "target":

            # show hardcoded target languages for simplicity
            target_langs = [("en", "English")]

            buttons_per_row = 2

            keyboard = []

            # create buttons in rows from target_langs
            for i in range(0, len(target_langs), buttons_per_row):
                row = []
                for code, name_flag in target_langs[i:i + buttons_per_row]:
                    row.append(InlineKeyboardButton(name_flag, callback_data=f"set_lang:target:{code}"))
                keyboard.append(row)
            keyboard.append([InlineKeyboardButton(LOCALE.get("back"), callback_data="lang_back")])
            await query.edit_message_text(LOCALE.get("select_target_language"), reply_markup=InlineKeyboardMarkup(keyboard))

        elif lang_type == "translation":
            # ask user to type translation language in chat
            context.user_data["awaiting_translation_lang"] = True

            # keyboard with only Back button
            keyboard = [
                [InlineKeyboardButton(LOCALE.get("back"), callback_data="lang_back")]
            ]
            await query.edit_message_text(
                LOCALE.get("enter_translation_language"),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    # #################################################
    #              Level 2: Set language             #
    # #################################################
    elif data.startswith("set_lang:"):
        parts = data.split(":")
        lang_scope = parts[1]
        lang_code = parts[2]

        # Update language depending on scope
        if lang_scope == "bot":
            lang_manager.set_languages(
                bot_lang=lang_code, 
                target_lang=lang_manager.target_language, 
                translation_lang=lang_manager.translation_language
            )
            if lang_scope == "bot":
                LOCALE = lang_manager.load_locale()  # reload locale if bot language changes

        elif lang_scope == "target":
            lang_manager.set_languages(
                bot_lang=lang_manager.bot_language, 
                target_lang=lang_code, 
                translation_lang=lang_manager.translation_language
            )

        # Send the same success message for both
        await query.edit_message_text(LOCALE.get("language_set_successfully"))


# #################################################
#              Handle translation input           #
# #################################################
async def handle_translation_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user input for translation language"""
    user_input = update.message.text.strip()
    if not user_input:
        await update.message.reply_text("Inserisci una lingua valida!")
        return

    # Update translation language only for this user
    lang_manager.set_languages(
        bot_lang=lang_manager.bot_language,
        target_lang=lang_manager.target_language,
        translation_lang=user_input
    )
    context.user_data["translation_language"] = user_input
    context.user_data["awaiting_translation_lang"] = False

    await update.message.reply_text(f"Translation language set to: {user_input}")

    # Return to main language menu
    keyboard = [
        [InlineKeyboardButton(LOCALE.get("inline_bot_language"), callback_data="lang_select:bot")],
        [InlineKeyboardButton(LOCALE.get("inline_target_language"), callback_data="lang_select:target")],
        [InlineKeyboardButton(LOCALE.get("inline_translation_language"), callback_data="lang_select:translation")]
    ]
    await update.message.reply_text(LOCALE.get("select_language"), reply_markup=InlineKeyboardMarkup(keyboard))


# #################################################
#                WORD HANDLER                     #
# #################################################
async def handle_word_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles word input and adds notes to Anki"""
    deck_name = deck_manager.get_loaded_deck()
    if deck_name is None:
        await update.message.reply_text(LOCALE.get("no_deck_selected"), parse_mode=ParseMode.MARKDOWN)
        return

    raw_text = update.message.text.replace("\u200b", "").replace("\r", "").strip()
    words = [w.strip().lower() for w in raw_text.replace("\n", " ").replace(",", " ").split() if w.strip()]

    if not words:
        await update.message.reply_text("Nessuna parola valida trovata nel testo.")
        return

    # Retrieve user's translation language or fallback global
    translation_lang = context.user_data.get("translation_language", TRANSLATION_LANGUAGE)
    target_lang = TARGET_LANGUAGE

    anki = AnkiLoader(deck_name=deck_name, endpoint=ANKI_ENDPOINT, model_name=MODEL_NAME)

    try:
        anki._tryConnectionToAnki()
    except Exception as e:
        await update.message.reply_text(f"Anki connection failed: {str(e)}")
        return

    for word in words:
        try:
            word_obj = Word(word, learning_language=target_lang, translation_language=translation_lang)
            lemma = word_obj.lemmatize()
            msg = await update.message.reply_text(LOCALE["processing"].format(word=lemma))

            anki.addNotes(word_obj)
            await msg.edit_text(LOCALE["success"].format(word=lemma))
        except Exception as e:
            log(f"Error processing word '{word}': {e}", level="ERROR")
            await update.message.reply_text(LOCALE["error_processing_word"].format(word=word, error=str(e)))


# #################################################
#              Handle text input                  #
# #################################################
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes the user input either to translation language handler or word handler"""
    if context.user_data.get("awaiting_translation_lang"):
        await handle_translation_input(update, context)
    else:
        await handle_word_input(update, context)


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
    app.add_handler(CallbackQueryHandler(lang_button_callback, pattern=r"^(lang_select:|set_lang:|lang_back)"))

    # Handle text messages and file uploads
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_input))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_import_file))

    log("Bot is running...", level="DEBUG")
    app.run_polling()
