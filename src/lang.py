import json
import yaml
import os

class LanguageManager:
    """
    Class to manage the bot's languages.
    Responsibilities:
    - Read/write language settings from config.json
    - Load YAML locale files
    - Allow changing language on the fly
    """

    def __init__(self):
        # Path to the configuration file
        self.config_path = os.path.abspath(os.path.join(__file__, "../../config.json"))

        # Folder containing YAML locale files
        self.locales_dir = os.path.join(os.path.dirname(__file__), "../locales")

        # Default languages (used if config doesn't specify them)
        self.bot_language = "en"          # language used by the bot interface
        self.target_language = "en"       # language for output/content
        self.translation_language = None  # source language for translations

        # Load current languages from config
        self.get_languages()

    def get_languages(self):
        """
        Load current language settings from config.json.
        Updates the instance variables with the loaded values.
        """
        with open(self.config_path, encoding="utf-8") as config_file:
            config = json.load(config_file)

        self.bot_language = config.get("BOT_LANGUAGE", "en")
        self.target_language = config.get("TARGET_LANGUAGE", "en")
        self.translation_language = config.get("TRANSLATION_LANGUAGE", "en")

    def set_languages(self, bot_lang: str, target_lang: str, translation_lang: str):
        """
        Update the bot's languages.
        - Writes the new settings to config.json
        - Updates the current in-memory instance
        """
        # Read current config
        with open(self.config_path, encoding="utf-8") as config_file:
            config = json.load(config_file)

        # Update values
        config["BOT_LANGUAGE"] = bot_lang
        config["TARGET_LANGUAGE"] = target_lang
        config["TRANSLATION_LANGUAGE"] = translation_lang

        # Save back to file
        with open(self.config_path, "w", encoding="utf-8") as config_file:
            json.dump(config, config_file, indent=4, ensure_ascii=False)

        # Update the current instance so changes take effect immediately
        self.bot_language = bot_lang
        self.target_language = target_lang
        self.translation_language = translation_lang

    def load_locale(self):
        """
        Load the YAML file for the current bot language.
        If the file doesn't exist, fallback to en.yaml.
        Returns a Python dictionary containing all text strings.
        """
        path = os.path.join(self.locales_dir, f"{self.bot_language}.yaml")
        if not os.path.exists(path):
            # fallback to English
            path = os.path.join(self.locales_dir, "en.yaml")

        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def set_locale(self, lang_code: str):
        """
        Load a YAML file for a specific language without changing bot_language.
        Useful for previewing or testing other languages.
        """
        path = os.path.join(self.locales_dir, f"{lang_code}.yaml")
        if not os.path.exists(path):
            path = os.path.join(self.locales_dir, "en.yaml")

        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_available_languages(self):
        """
        Return a dictionary of available languages.
        Key: language code (fr, en, de, ...)
        Value: single string with native name + flag (e.g., "Deutsch 🇩🇪")
        """
        # Map of language codes to "name + flag"
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

        # Filter only the languages for which a YAML file exists
        available_codes = [f.split(".")[0] for f in os.listdir(self.locales_dir) if f.endswith(".yaml")]

        # Build the dictionary: code -> "Name + Flag"
        return {code: language_info.get(code, "Unknown 🏳️") for code in available_codes}
