###############################################################################
# src/utils/deck_utils.py
#
# Anki deck management utility.
# Handles deck selection, deck existence checking, and deck persistence.
# Manages communication with AnkiConnect for deck operations.
###############################################################################

from src.utils.config_utils import ConfigManager
from src.bot.send_to_anki import SendToAnki
from src.utils.logging_utils import log

class DeckUtils:
    def __init__(self, anki_endpoint="http://localhost:8765", model_name="DankY"):
        self.config_manager = ConfigManager()
        self.deckname = None
        self.anki_endpoint = anki_endpoint
        self.model_name = model_name

    def get_loaded_deck(self):
        deck = self.config_manager.get("SELECTED_DECK")
        if not deck:
            raise ValueError("No deck selected. Use /deck [DeckName] to select one.")
        self.deckname = deck
        return deck

    def set_deck(self, deckname: str):
        self.config_manager.set("SELECTED_DECK", deckname)
        self.deckname = deckname

    def get_available_decks(self) -> list:
        try:
            anki = SendToAnki(deck_name=None, endpoint=self.anki_endpoint, model_name=self.model_name)
            anki._tryConnectionToAnki()
            payload = anki._setPayload(action="deckNames")
            response = anki._executePayload(payload)
            decks = response.get("result", [])
            return decks
        except Exception as e:
            log(f"Error retrieving available decks: {e}", level="WARNING")
            raise ConnectionError("Cannot contact Anki. Make sure Anki is running.") from e

    def check_deck_existence(self, deckname=None) -> bool:
        deck_to_check = deckname if deckname else self.get_loaded_deck()
        exists = deck_to_check in self.get_available_decks()
        return exists
