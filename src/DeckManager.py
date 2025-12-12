# src/DeckManager.py

import json
import os
from AnkiLoader import AnkiLoader
from logger import log  # import your logger wrapper

class DeckManager:
    def __init__(self, deckname=None, anki_endpoint="http://localhost:8765", model_name="DankY"):
        self.config_path = os.path.abspath(os.path.join(__file__, "../../config.json"))
        self.deckname = deckname
        self.anki_endpoint = anki_endpoint
        self.model_name = model_name
        log(f"DeckManager initialized with endpoint='{anki_endpoint}', model='{model_name}'", level="DEBUG")

    def get_loaded_deck(self):
        with open(self.config_path, encoding="utf-8") as f:
            deck = json.load(f).get("SELECTED_DECK", "")
        
        if not deck:
            log("No deck selected in config.json", level="DEBUG")
            raise ValueError("No deck selected. Use /deck [DeckName] to select one.")
        
        self.deckname = deck
        log(f"Loaded deck from config.json: '{deck}'", level="DEBUG")
        return deck

    def set_deck(self, deckname: str):
        with open(self.config_path, encoding="utf-8") as f:
            config = json.load(f)

        config["SELECTED_DECK"] = deckname

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        self.deckname = deckname
        log(f"Set deck in config.json: '{deckname}'", level="DEBUG")

    def get_available_decks(self) -> list:
        try:
            anki = AnkiLoader(deck_name=None, endpoint=self.anki_endpoint, model_name=self.model_name)
            log("Checking available decks from Anki...", level="DEBUG")
            anki._tryConnectionToAnki()
            payload = anki._setPayload(action="deckNames")
            response = anki._executePayload(payload)
            decks = response.get("result", [])
            log(f"Available decks: {decks}", level="DEBUG")
            return decks
        except Exception as e:
            log(f"Error retrieving available decks: {e}", level="DEBUG")
            raise ConnectionError("Cannot contact Anki. Make sure Anki is running.") from e

    def check_deck_existence(self, deckname=None) -> bool:
        deck_to_check = deckname if deckname else self.get_loaded_deck()
        exists = deck_to_check in self.get_available_decks()
        log(f"Deck '{deck_to_check}' existence check: {exists}", level="DEBUG")
        return exists
