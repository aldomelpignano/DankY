# deckmanager.py

import json
import os
from AnkiLoader import AnkiLoader

class DeckManager:
    def __init__(self, deckname=None, anki_endpoint="http://localhost:8765", model_name="DankY"):
        # Absolute path to config.json
        self.config_path = os.path.abspath(os.path.join(__file__, "../../config.json"))
        self.deckname = deckname
        self.anki_endpoint = anki_endpoint
        self.model_name = model_name

    def get_loaded_deck(self):
        """
        Return the currently selected deck from config.json.
        Raises an error if no deck is selected.
        """
        with open(self.config_path, encoding="utf-8") as f:
            deck = json.load(f).get("SELECTED_DECK", "")
        
        if not deck:
            raise ValueError("No deck selected. Use /deck [DeckName] to select one.")
        
        self.deckname = deck
        return deck

    def set_deck(self, deckname: str):
        """
        Set the selected deck in config.json.
        """
        with open(self.config_path, encoding="utf-8") as f:
            config = json.load(f)

        config["SELECTED_DECK"] = deckname

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        self.deckname = deckname

    def get_available_decks(self) -> list:
        """
        Return a list of available decks in Anki.
        """
        try:
            # Create AnkiLoader instance to interact with AnkiConnect
            anki = AnkiLoader(deck_name=None, endpoint=self.anki_endpoint, model_name=self.model_name)
            anki._tryConnectionToAnki()
            payload = anki._setPayload(action="deckNames")
            response = anki._executePayload(payload)
            decks = response.get("result", [])
            return decks
        except Exception as e:
            raise ConnectionError("Cannot contact Anki. Make sure Anki is running.") from e

    def check_deck_existence(self, deckname=None) -> bool:
        """
        Check if a deck exists in Anki.
        """
        deck_to_check = deckname if deckname else self.get_loaded_deck()
        return deck_to_check in self.get_available_decks()
