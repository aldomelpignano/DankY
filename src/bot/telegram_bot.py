###############################################################################
# src/bot/telegram_bot.py
#
# Main Telegram bot implementation.
# Handles user commands, word processing, file imports, and language settings.
# Manages bot interface localization and deck selection.
###############################################################################

import os
import csv
import tempfile
import openpyxl

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, filters, MessageHandler, CallbackQueryHandler
from telegram.constants import ParseMode

from src.bot.send_to_anki import SendToAnki as Anki, MissingMandatoryFieldError
from src.utils.deck_utils import DeckUtils as DeckManager
from src.utils.language_utils import LanguageUtils as LanguageManager
from src.utils.logging_utils import log
from src.dictionaries.dictionaries_manager import DictionariesManager as dictManager
from src.utils.config_utils import ConfigManager

class TelegramBot:

    def __init__(self, token=None):

        # #################################################
        #                 CONFIGURATION                  #
        # #################################################
        
        config_manager = ConfigManager()
        self.TELEGRAM_TOKEN = config_manager.get("TELEGRAM_BOT_API")
        self.ANKI_ENDPOINT = config_manager.get("ANKI_ENDPOINT")

        # Check that Telegram token is valid
        if not self.TELEGRAM_TOKEN or self.TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_API":
            raise ValueError("TELEGRAM_BOT_API is not set or invalid. Please configure it in config.json.")

        self.token = token or self.TELEGRAM_TOKEN
        self.app = ApplicationBuilder().token(self.token).build()

        # #################################################
        #                  CONSTANTS                     #
        # #################################################

        # Initialize DeckManager and load default deck if selected
        self.deck_manager = DeckManager()
        try:
            self.DECK_NAME = self.deck_manager.get_loaded_deck()
        except ValueError:
            self.DECK_NAME = None  # fallback if no deck selected

        self.MODEL_NAME = "DankY"  # default Anki model

        ## language manager and LOCALE loading
        self.lang_manager = LanguageManager()  # handle localization and translation

        self.LOCALE = self.lang_manager.load_locale()  # load messages in selected bot language
        self.TARGET_LANGUAGE = self.lang_manager.get_target_language()
        self.TRANSLATION_LANGUAGE = self.lang_manager.get_translation_language()

    # #################################################
    #                  BOT COMMANDS                  #
    # #################################################

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.LOCALE["start"], parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.LOCALE["help"], parse_mode=ParseMode.MARKDOWN)

    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            self.LOCALE["about"],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(self.LOCALE.get("about_github_button", "GitHub"), url="https://github.com/aldomelpignano/DankY")]]
            )
        )

    # #################################################
    #                   Language Manager             #
    # #################################################

    async def lang_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton(self.LOCALE.get("inline_bot_language"), callback_data="lang_select:bot")],
            [InlineKeyboardButton(self.LOCALE.get("inline_target_language"), callback_data="lang_select:target")],
            [InlineKeyboardButton(self.LOCALE.get("inline_translation_language"), callback_data="lang_select:translation")]
        ]
        await update.message.reply_text(self.LOCALE.get("select_language"), reply_markup=InlineKeyboardMarkup(keyboard))

    async def lang_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "lang_back":
            keyboard = [
                [InlineKeyboardButton(self.LOCALE.get("inline_bot_language"), callback_data="lang_select:bot")],
                [InlineKeyboardButton(self.LOCALE.get("inline_target_language"), callback_data="lang_select:target")],
                [InlineKeyboardButton(self.LOCALE.get("inline_translation_language"), callback_data="lang_select:translation")]
            ]
            await query.edit_message_text(self.LOCALE.get("select_language"), reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if data.startswith("lang_select:"):
            lang_type = data.split(":")[1]

            if lang_type == "bot":
                languages_list = list(self.lang_manager.get_available_languages().items())
                buttons_per_row = 2
                keyboard = []
                for i in range(0, len(languages_list), buttons_per_row):
                    row = []
                    for code, name_flag in languages_list[i:i + buttons_per_row]:
                        row.append(InlineKeyboardButton(name_flag, callback_data=f"set_lang:bot:{code}"))
                    keyboard.append(row)
                keyboard.append([InlineKeyboardButton(self.LOCALE.get("back"), callback_data="lang_back")])
                await query.edit_message_text(self.LOCALE.get("select_bot_language"), reply_markup=InlineKeyboardMarkup(keyboard))

            elif lang_type == "target":
                target_langs = [("en", "English 🇬🇧"), ("de", "Deutsch 🇩🇪")]
                buttons_per_row = 2
                keyboard = []
                for i in range(0, len(target_langs), buttons_per_row):
                    row = []
                    for code, name_flag in target_langs[i:i + buttons_per_row]:
                        row.append(InlineKeyboardButton(name_flag, callback_data=f"set_lang:target:{code}"))
                    keyboard.append(row)
                keyboard.append([InlineKeyboardButton(self.LOCALE.get("back"), callback_data="lang_back")])
                await query.edit_message_text(self.LOCALE.get("select_target_language"), reply_markup=InlineKeyboardMarkup(keyboard))

            elif lang_type == "translation":
                context.user_data["awaiting_translation_lang"] = True
                keyboard = [[InlineKeyboardButton(self.LOCALE.get("back"), callback_data="lang_back")]]
                await query.edit_message_text(self.LOCALE.get("enter_translation_language"), reply_markup=InlineKeyboardMarkup(keyboard))

        elif data.startswith("set_lang:"):
            parts = data.split(":")
            lang_scope = parts[1]
            lang_code = parts[2]

            if lang_scope == "bot":
                self.lang_manager.set_languages(
                    bot_lang=lang_code, 
                    target_lang=self.lang_manager.target_language, 
                    translation_lang=self.lang_manager.translation_language
                )
                self.LOCALE = self.lang_manager.load_locale()

            elif lang_scope == "target":
                self.lang_manager.set_languages(
                    bot_lang=self.lang_manager.bot_language, 
                    target_lang=lang_code, 
                    translation_lang=self.lang_manager.translation_language
                )
                # Update TARGET_LANGUAGE to reflect the change
                self.TARGET_LANGUAGE = self.lang_manager.get_target_language()
            await query.edit_message_text(self.LOCALE.get("language_set_successfully"))

    async def handle_translation_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text.strip()
        if not user_input:
            await update.message.reply_text(self.LOCALE.get("invalid_language_input"))
            return
        self.lang_manager.set_languages(
            bot_lang=self.lang_manager.bot_language,
            target_lang=self.lang_manager.target_language,
            translation_lang=user_input
        )
        context.user_data["translation_language"] = user_input
        context.user_data["awaiting_translation_lang"] = False
        await update.message.reply_text(self.LOCALE.get("translation_language_set").format(language=user_input))
        keyboard = [
            [InlineKeyboardButton(self.LOCALE.get("inline_bot_language"), callback_data="lang_select:bot")],
            [InlineKeyboardButton(self.LOCALE.get("inline_target_language"), callback_data="lang_select:target")],
            [InlineKeyboardButton(self.LOCALE.get("inline_translation_language"), callback_data="lang_select:translation")]
        ]
        await update.message.reply_text(self.LOCALE.get("select_language"), reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_word_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        deck_name = self.deck_manager.get_loaded_deck()
        if deck_name is None:
            await update.message.reply_text(self.LOCALE.get("no_deck_selected"), parse_mode=ParseMode.MARKDOWN)
            return
        raw_text = update.message.text.replace("\u200b", "").replace("\r", "").strip()
        words = [w.strip().lower() for w in raw_text.replace("\n", " ").replace(",", " ").split() if w.strip()]
        if not words:
            await update.message.reply_text(self.LOCALE.get("no_valid_words_found"))
            return
        translation_lang = context.user_data.get("translation_language", self.TRANSLATION_LANGUAGE)
        # Get target language from lang_manager to ensure it's up-to-date
        target_lang = self.lang_manager.get_target_language()
        anki = Anki(deck_name=deck_name, endpoint=self.ANKI_ENDPOINT, model_name=self.MODEL_NAME)
        try:
            anki._tryConnectionToAnki()
        except Exception as e:
            await update.message.reply_text(self.LOCALE.get("anki_connection_failed").format(error=str(e)))
            return
        for word in words:
            msg = None
            try:
                word_obj = dictManager(word, selected_dictionary=target_lang, translation_language=translation_lang)
                lemma = word_obj.get_lemma()
                msg = await update.message.reply_text(self.LOCALE["processing"].format(word=lemma))
                anki.addNotes(word_obj)
                await msg.edit_text(self.LOCALE["success"].format(word=lemma))
            except MissingMandatoryFieldError as e:
                log(f"Missing mandatory field error for word '{word}': {e.missing_fields}", level="ERROR")
                if msg:
                    await msg.edit_text(self.LOCALE.get("word_not_exists").format(word=word))
                else:
                    await update.message.reply_text(self.LOCALE.get("word_not_exists").format(word=word))
            except Exception as e:
                log(f"Error processing word '{word}': {e}", level="ERROR")
                if msg:
                    await msg.edit_text(self.LOCALE["error_processing_word"].format(word=word, error=str(e)))
                else:
                    await update.message.reply_text(self.LOCALE["error_processing_word"].format(word=word, error=str(e)))

    async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.user_data.get("awaiting_translation_lang"):
            await self.handle_translation_input(update, context)
        else:
            await self.handle_word_input(update, context)

    async def deck_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) == 0:
            await update.message.reply_text(self.LOCALE.get("no_deck_name_provided"), parse_mode=ParseMode.MARKDOWN)
            return
        deck_name = " ".join(context.args)
        manager = DeckManager()
        if not manager.check_deck_existence(deck_name):
            await update.message.reply_text(self.LOCALE.get("deck_not_found").format(deck=deck_name), parse_mode=ParseMode.MARKDOWN)
            return
        manager.set_deck(deck_name)
        self.DECK_NAME = deck_name
        await update.message.reply_text(self.LOCALE.get("deck_set_success").format(deck=deck_name), parse_mode=ParseMode.MARKDOWN)

    async def handle_import_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        deck_name = self.deck_manager.get_loaded_deck()
        if deck_name is None:
            await update.message.reply_text(self.LOCALE.get("no_deck_selected"), parse_mode=ParseMode.MARKDOWN)
            return
        file_doc = update.message.document
        filename = file_doc.file_name.lower()
        allowed_ext = (".xlsx", ".csv", ".tsv", ".txt")
        if not filename.endswith(allowed_ext):
            await update.message.reply_text(self.LOCALE.get("file_unsupported_format"), parse_mode=ParseMode.MARKDOWN)
            return
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1])
        file_bytes = await file_doc.get_file()
        await file_bytes.download_to_drive(temp.name)
        words = []
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
            await update.message.reply_text(self.LOCALE.get("file_read_error").format(filename=filename, error=str(e)))
            return
        if not words:
            await update.message.reply_text(self.LOCALE.get("file_empty"), parse_mode=ParseMode.MARKDOWN)
            return
        anki = Anki(deck_name=deck_name, endpoint=self.ANKI_ENDPOINT, model_name=self.MODEL_NAME)
        try:
            anki._tryConnectionToAnki()
        except Exception as e:
            await update.message.reply_text(self.LOCALE.get("anki_connection_error").format(error=str(e)))
            return
        await update.message.reply_text(self.LOCALE.get("file_import_started").format(num_words=len(words)), parse_mode=ParseMode.MARKDOWN)
        imported = 0
        errors = 0
        # Get target language from lang_manager to ensure it's up-to-date
        target_lang = self.lang_manager.get_target_language()
        for word in words:
            try:
                word_obj = dictManager(word, selected_dictionary=target_lang, translation_language=self.TRANSLATION_LANGUAGE)
                lemma = word_obj.get_lemma()
                anki.addNotes(word_obj)
                imported += 1
            except MissingMandatoryFieldError as e:
                log(f"Missing mandatory field error for word '{word}' in file import: {e.missing_fields}", level="ERROR")
                errors += 1
            except Exception as e:
                log(f"Error importing word '{word}': {e}", level="ERROR")
                errors += 1
        await update.message.reply_text(
            self.LOCALE.get("file_import_completed").format(imported=imported, errors=errors),
            parse_mode=ParseMode.MARKDOWN,
        )

    # #################################################
    #                 RUN BOT                         #
    # #################################################
    async def run(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("about", self.about_command))
        self.app.add_handler(CommandHandler("deck", self.deck_command))
        self.app.add_handler(CommandHandler("lang", self.lang_command))
        self.app.add_handler(CallbackQueryHandler(self.lang_button_callback, pattern=r"^(lang_select:|set_lang:|lang_back)"))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_text_input))
        self.app.add_handler(MessageHandler(filters.Document.ALL, self.handle_import_file))

        log("Bot is running...", level="INFO")
        await self.app.run_polling()