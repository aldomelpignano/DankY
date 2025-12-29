###############################################################################
# src/utils/config_utils.py
#
# Configuration file manager.
# Handles reading and writing to config.json.
# Provides get() and set() methods for configuration values.
###############################################################################

import json
import os
from src.utils.logging_utils import log

class ConfigManager:
    def __init__(self):
        # Determine absolute path to config.json (three levels up)
        self.config_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../config.json")
        )

        # Load existing config or create default if not exists
        self.config = self._load_or_create()

    def _load_or_create(self):
        """Load config.json if exists, otherwise create default config."""
        if not os.path.exists(self.config_path):
            log(f"ConfigManager: config not found, creating default at {self.config_path}", level="INFO")
            
            default_config = {
                "TELEGRAM_BOT_API": "YOUR_TELEGRAM_BOT_API",
                "ANKI_ENDPOINT": "http://localhost:8765",
                "BOT_LANGUAGE": "en",
                "TARGET_LANGUAGE": "en",
                "TRANSLATION_LANGUAGE": None,
                "SELECTED_DECK": None
            }
            
            # Write default config to file
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=4)
            
            return default_config
        else:
            # Load existing config
            with open(self.config_path) as f:
                config = json.load(f)
            return config

    def get(self, key, default=None):
        """Get a value from config with optional default."""
        value = self.config.get(key, default)
        return value

    def set(self, key, value):
        """Set a value in config and save to file."""
        self.config[key] = value
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)
        log(f"ConfigManager: set '{key}' -> {value}", level="INFO")
