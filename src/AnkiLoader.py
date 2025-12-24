# src/AnkiLoader.py

import requests
import json
from Word import Word
from logger import log

class AnkiLoader:
    
    def __init__(self, deck_name: str, endpoint: str = "http://127.0.0.1:8765", model_name: str = "DankY"):
        self.deck_name = deck_name
        self.endpoint = endpoint
        self.model_name = model_name
        log(f"AnkiLoader initialized with deck='{deck_name}', model='{model_name}'", level="DEBUG")

    def _setPayload(self, action: str, lemma: str = None, version: int = 6):
        payload = {"action": action, "version": version}
        if action == "findNotes":
            payload["params"] = {"query": f"deck:{self.deck_name} lemma:{lemma}"}
            log(f"Payload for findNotes: {payload}", level="DEBUG")
        return payload
    
    def _executePayload(self, payload) -> dict:
        log(f"Sending payload to AnkiConnect: {payload}", level="DEBUG")
        try:
            response = requests.post(self.endpoint, json=payload, timeout=10)
            response.raise_for_status()
            json_response = response.json()
            log(f"AnkiConnect response: {json_response}", level="DEBUG")
            return json_response
        except requests.exceptions.RequestException as e:
            log(f"RequestException: {e}", level="DEBUG")
            raise ConnectionError("Connection with Anki failed, make sure Anki and AnkiConnect are running.")
        except ValueError as e:
            log(f"ValueError parsing JSON: {e}", level="DEBUG")
            raise ConnectionError("Anki returned invalid JSON data.")
    
    def _tryConnectionToAnki(self):
        payload = self._setPayload("version")
        return self._executePayload(payload)
        
    def _prepareFields(self, word_obj: Word):
        fields = {
            "url": word_obj.get_source_url(),
            "lemma": word_obj.lemmatize(),
            "IPA": word_obj.get_IPA(),
            "POS": word_obj.get_POS(),
            "translated_lemma": word_obj.get_translation(),
            "synonyms": ", ".join(word_obj.get_synonyms()) if word_obj.get_synonyms() else "",
            "antonyms": ", ".join(word_obj.get_antonyms()) if word_obj.get_antonyms() else "",
        }

        definitions = word_obj.get_definition()
        if not definitions:
            definitions = [{"def1": "Definition not found", "ex1": ""}]
        
        for i, d in enumerate(definitions[:15]):
            for key, value in d.items():
                fields[key] = value if value else ""
        
        log(f"Prepared fields: {fields}", level="DEBUG")
        return fields

    def checkExistence(self, lemma) -> bool:
        payload = self._setPayload("findNotes", lemma)
        response = self._executePayload(payload)
        exists = bool(response.get("result"))
        log(f"Check existence for '{lemma}': {exists}", level="DEBUG")
        return exists

    def addNotes(self, word_obj: Word):
        fields = self._prepareFields(word_obj)
        required_fields = ["lemma", "def1"]
        check_missing = [f for f in required_fields if not fields.get(f)]
        if check_missing:
            log(f"Missing required fields: {check_missing}", level="DEBUG")
            raise ValueError(f"Cannot create note: missing fields {check_missing}")

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

        lemma = word_obj.lemmatize()
        if not self.checkExistence(lemma):
            log(f"Adding note for '{lemma}'", level="DEBUG")
            response = self._executePayload(payload)
            log(f"Note added response: {response}", level="DEBUG")
        else:
            log(f"Word '{lemma}' already exists, skipping.", level="DEBUG")
            raise ValueError(f"The word '{lemma}' already exists in the deck '{self.deck_name}'.")