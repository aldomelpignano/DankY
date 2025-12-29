###############################################################################
# src/utils/language_utils.py
#
# Language and localization manager.
# Handles bot language, target language (English/German), and translation language.
# Loads locale files (YAML) for bot interface messages.
# Manages available languages and language switching.
###############################################################################

import yaml
import os
from src.utils.logging_utils import log
from src.utils.config_utils import ConfigManager

class LanguageUtils:
    def __init__(self):
        # Usa ConfigManager invece di leggere JSON direttamente
        self.config_manager = ConfigManager()
        self.locales_dir = os.path.join(os.path.dirname(__file__), "../../locales")

        # set languages from config o default
        self.bot_language = self.config_manager.get("BOT_LANGUAGE", "en")
        self.target_language = self.config_manager.get("TARGET_LANGUAGE", "en")
        self.translation_language = self.config_manager.get("TRANSLATION_LANGUAGE", None)


    # ------------------------- GETTER / SETTER -------------------------
    def get_bot_language(self):
        return self.bot_language

    def get_target_language(self):
        return self.target_language

    def get_translation_language(self):
        return self.translation_language

    def set_languages(self, bot_lang: str = None, target_lang: str = None, translation_lang: str = None):
        if bot_lang:
            self.bot_language = bot_lang
            self.config_manager.set("BOT_LANGUAGE", bot_lang)
        if target_lang:
            self.target_language = target_lang
            self.config_manager.set("TARGET_LANGUAGE", target_lang)
        if translation_lang:
            self.translation_language = translation_lang
            self.config_manager.set("TRANSLATION_LANGUAGE", translation_lang)


    # ------------------------- LOCALE -------------------------
    def load_locale(self, lang_code: str = None):
        """Loads the YAML locale file for the specified language code."""
        lang_code = lang_code or self.bot_language
        path = os.path.join(self.locales_dir, f"{lang_code}.yaml")
        if not os.path.exists(path):
            log(f"Locale file '{lang_code}.yaml' not found, fallback to 'en.yaml'", level="WARNING")
            path = os.path.join(self.locales_dir, "en.yaml")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data

    # ------------------------- UTILITY -------------------------
    def get_available_languages(self):
        """Returns a dictionary of available language codes and their display names."""
        language_info = {
            "en": "English 🇬🇧",
            "fr": "Français 🇫🇷",
            "de": "Deutsch 🇩🇪",
            "it": "Italiano 🇮🇹",
            "es": "Español 🇪🇸",
            "pt": "Português 🇵🇹",
            "ru": "Русский 🇷🇺",
            "zh": "中文 🇨🇳",
            "ja": "日本語 🇯🇵",
            "ko": "한국어 🇰🇷",
            "ar": "العربية 🇸🇦",
            "nl": "Nederlands 🇳🇱",
            "sv": "Svenska 🇸🇪",
            "no": "Norsk 🇳🇴",
            "fi": "Suomi 🇫🇮",
            "tr": "Türkçe 🇹🇷",
            "pl": "Polski 🇵🇱",
            "gr": "Ελληνικά 🇬🇷",
            "he": "עברית 🇮🇱",
            "hi": "हिन्दी 🇮🇳",
            "th": "ไทย 🇹🇭",
            "vi": "Tiếng Việt 🇻🇳",
            "id": "Bahasa Indonesia 🇮🇩",
        }

        available_codes = [f.split(".")[0] for f in os.listdir(self.locales_dir) if f.endswith(".yaml")]
        langs = {code: language_info.get(code, "Unknown 🏳️") for code in available_codes}
        return langs