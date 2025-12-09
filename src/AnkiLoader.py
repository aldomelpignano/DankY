import requests
import json

from Word import Word

class AnkiLoader:
    
    def __init__ (self, deck_name: str, endpoint: str = "http://127.0.0.1:8765", model_name: str = "DankY"):
        
        # Basic initialization of Anki loader attributes
        self.deck_name = deck_name
        self.endpoint = endpoint
        self.model_name = model_name
    
    def _setPayload(self, action: str, lemma: str = None, version: int = 6):
        # Prepares a payload dictionary for AnkiConnect API
        payload = {
            "action": action,
            "version": version,
        }

        # When searching for notes, include query with deck and lemma
        if action == "findNotes":
            payload["params"] = {
                "query": f"deck:{self.deck_name} lemma:{lemma}"
            }

        return payload
    
    def _executePayload(self, payload) -> dict:
        # Sends the prepared payload to AnkiConnect and safely handles errors
        try:
            response = requests.post(self.endpoint, json=payload, timeout=10)
            response.raise_for_status()  # Raises HTTP error if one occurred

            return response.json()  # May raise ValueError if invalid JSON

        except requests.exceptions.RequestException:
            # Handles connection issues (Anki not running, API unreachable, etc.)
            raise ConnectionError("Connection with Anki failed, make sure you have opened Anki with AnkiConnect installed.")

        except ValueError:
            # Triggered when AnkiConnect returns invalid JSON
            raise ConnectionError("Anki returned invalid JSON data. Check AnkiConnect.")
    
    def _tryConnectionToAnki(self):
        # Basic version check to confirm AnkiConnect is available
        payload = self._setPayload("version")
        return self._executePayload(payload)
        
    def _prepareFields(self, word_obj: Word):
        # Builds the dictionary of fields used to populate an Anki note
        fields = {
            "url": word_obj.get_source_url(),
            "lemma": word_obj.lemmatize(),
            "IPA": word_obj.get_IPA(),
            "POS": word_obj.get_POS(),
            "translated_lemma": word_obj.get_translation(),
            "synonyms": word_obj.get_synonyms(),
            "antonyms": word_obj.get_antonyms(),
        }

        # Retrieves definitions and maps the first 15 entries into fields
        definitions = word_obj.get_definition()

        for i, d in enumerate(definitions[:15]):
            for key, value in d.items():
                fields[key] = value if value else ""  # trasforma None in stringa vuota


        return fields

    def checkExistence(self, lemma) -> bool:
        """Check if a card already exists in the deck, avoiding duplicates"""

        payload = self._setPayload("findNotes", lemma)
        response = self._executePayload(payload)

        return bool(response.get("result"))  # Returns True if one or more notes exist

    def addNotes(self, word_obj: Word):
        
        # Prepares all fields required for the note
        fields = self._prepareFields(word_obj)

        # Required fields that must be present in order to create a note
        required_fields = ["lemma", "def1"]

        # Checks if any required field is missing
        check_missing = [f for f in required_fields if not fields.get(f)]
        if check_missing:
            raise ValueError(f"Cannot create note: missing fields {check_missing}")

        # Payload for adding a note through AnkiConnect
        payload = {
            "action": "addNote",
            "version": 6,
            "params": {
                "note": {
                    "deckName": self.deck_name,
                    "modelName": self.model_name,
                    "fields": fields,
                    "tags": []
                }
            }
        }

        # Retrieves lemma once to avoid recomputing it
        lemma = word_obj.lemmatize()

        # Adds note only if it does not already exist
        if not self.checkExistence(lemma):
            self._executePayload(payload)
        else:
            raise ValueError(f"The word '{lemma}' already exists in the deck '{self.deck_name}'.")
