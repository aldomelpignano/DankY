# src/LanguageManager.py

import json
import yaml
import os
from logger import log

class LanguageManager:
    def __init__(self):
        self.config_path = os.path.abspath(os.path.join(__file__, "../../config.json"))
        self.locales_dir = os.path.join(os.path.dirname(__file__), "../locales")

        # Load configuration
        self.config = self._load_config()

        # set languages from config or defaults
        self.bot_language = self.config.get("BOT_LANGUAGE", "en")
        self.target_language = self.config.get("TARGET_LANGUAGE", "en")
        self.translation_language = self.config.get("TRANSLATION_LANGUAGE", None)

        log(f"LanguageManager initialized: bot={self.bot_language}, target={self.target_language}, translation={self.translation_language}", level="DEBUG")

    # ------------------------- CONFIG -------------------------
    def _load_config(self):
        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = json.load(f)
                log(f"Config loaded from {self.config_path}", level="DEBUG")
                return config
        except FileNotFoundError:
            log(f"Config file not found, creating default config", level="WARNING")
            default_config = {
                "BOT_LANGUAGE": "en",
                "TARGET_LANGUAGE": "en",
                "TRANSLATION_LANGUAGE": None,
                "SELECTED_DECK": None
            }
            self._save_config(default_config)
            return default_config
        except json.JSONDecodeError as e:
            log(f"Error decoding JSON config: {e}", level="ERROR")
            return {}

    def _save_config(self, config):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        log(f"Config saved to {self.config_path}", level="DEBUG")

    # ------------------------- GETTER / SETTER -------------------------
    def get_bot_language(self):
        return self.bot_language

    def get_target_language(self):
        return self.target_language

    def get_translation_language(self):
        return self.translation_language

    #set_languages
    def set_languages(self, bot_lang: str = None, target_lang: str = None, translation_lang: str = None):
        if bot_lang:
            self.bot_language = bot_lang
            self.config["BOT_LANGUAGE"] = bot_lang
        if target_lang:
            self.target_language = target_lang
            self.config["TARGET_LANGUAGE"] = target_lang
        if translation_lang:
            self.translation_language = translation_lang
            self.config["TRANSLATION_LANGUAGE"] = translation_lang

        self._save_config(self.config)
        log(f"Languages updated: bot={self.bot_language}, target={self.target_language}, translation={self.translation_language}", level="DEBUG")

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
            log(f"Locale loaded for '{lang_code}': {list(data.keys())[:5]}...", level="DEBUG")
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
        log(f"Available languages found: {langs}", level="DEBUG")
        return langs
