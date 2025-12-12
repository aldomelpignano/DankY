# src/lang.py

import json
import yaml
import os
from logger import log

class LanguageManager:
    def __init__(self):
        self.config_path = os.path.abspath(os.path.join(__file__, "../../config.json"))
        self.locales_dir = os.path.join(os.path.dirname(__file__), "../locales")
        self.bot_language = "en"
        self.target_language = "en"
        self.translation_language = None
        self.get_languages()
        log(f"LanguageManager initialized: bot={self.bot_language}, target={self.target_language}, translation={self.translation_language}", level="DEBUG")

    def get_languages(self):
        with open(self.config_path, encoding="utf-8") as config_file:
            config = json.load(config_file)

        self.bot_language = config.get("BOT_LANGUAGE", "en")
        self.target_language = config.get("TARGET_LANGUAGE", "en")
        self.translation_language = config.get("TRANSLATION_LANGUAGE", "en")
        log(f"Loaded languages from config.json: bot={self.bot_language}, target={self.target_language}, translation={self.translation_language}", level="DEBUG")

    def set_languages(self, bot_lang: str, target_lang: str, translation_lang: str):
        with open(self.config_path, encoding="utf-8") as config_file:
            config = json.load(config_file)

        config["BOT_LANGUAGE"] = bot_lang
        config["TARGET_LANGUAGE"] = target_lang
        config["TRANSLATION_LANGUAGE"] = translation_lang

        with open(self.config_path, "w", encoding="utf-8") as config_file:
            json.dump(config, config_file, indent=4, ensure_ascii=False)

        self.bot_language = bot_lang
        self.target_language = target_lang
        self.translation_language = translation_lang
        log(f"Languages updated: bot={bot_lang}, target={target_lang}, translation={translation_lang}", level="DEBUG")

    def load_locale(self):
        path = os.path.join(self.locales_dir, f"{self.bot_language}.yaml")
        if not os.path.exists(path):
            path = os.path.join(self.locales_dir, "en.yaml")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            log(f"Locale loaded for '{self.bot_language}': {list(data.keys())[:5]}...", level="DEBUG")  # show first 5 keys
            return data

    def set_locale(self, lang_code: str):
        path = os.path.join(self.locales_dir, f"{lang_code}.yaml")
        if not os.path.exists(path):
            path = os.path.join(self.locales_dir, "en.yaml")

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            log(f"Locale preview loaded for '{lang_code}': {list(data.keys())[:5]}...", level="DEBUG")
            return data

    def get_available_languages(self):
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
