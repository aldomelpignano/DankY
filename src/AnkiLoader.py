import requests
import json

from Word import Word

class AnkiLoader:
    
    def __init__ (self, deck_name: str, endpoint: str = "http://127.0.0.1:8765", model_name: str = "DankY"):
        
        #declaration of attributes
        self.deck_name = deck_name
        self.endpoint = endpoint
        self.model_name = model_name
    
    def _setPayload(self, action: str, lemma: str = None, version: int = 6):
        payload = {
            "action": action,
            "version": version,
        }

        if action == "findnotes":
            payload["params"] = {
                "query": f"deck:{self.deck_name} lemma:{lemma}"
            }

        return payload
    
    def _executePayload(self, payload)-> dict:
        try:
            tryConnection = requests.post(self.endpoint, json=payload, timeout=10)

            tryConnection.raise_for_status() #Raise an HTTP error, if occurred

            return tryConnection.json()

        except requests.exceptions.RequestException:
            raise ConnectionError("Connection with Anki failed, make sure you have opened anki with ankiconnect installed.")
        except json.JSONDecodeError:
            raise ConnectionError("Anki returned invalid data. Check AnkiConnect.")

    def _tryConnectionToAnki(self):
        payload = self._setPayload("version")
        return self._executePayload(payload)
        
    def _prepareFields(self, word_obj: Word):
        fields = {
            "url": word_obj.get_source_url(),
            "lemma": word_obj.lemmatize(),
            "IPA": word_obj.get_IPA(),
            "POS": word_obj.get_POS(),
            "translated_lemma": word_obj.get_translation("it"),
            "synonyms": word_obj.get_synonyms(),
            "antonyms": word_obj.get_antonyms(),
        }

        definitions = word_obj.get_definition()

        for d in definitions[:15]:
            for key, value in d.items():
                fields[key] = value

        return fields

    def checkExistence(self, lemma) -> bool:

        """Check if a card already exists in the deck, avoiding duplicates"""

        payload = self._setPayload("findnotes", lemma)
        response = self._executePayload(payload)

        return bool(response.get("result"))  # True if the note exist

    def addNotes(self, word_obj: Word):
        

        fields = self._prepareFields(word_obj)

        required_fields = ["lemma", "def1", "ex1"] #these are the required fields for the note existence

        check_missing = [f for f in required_fields if not fields.get(f)]
        if check_missing:
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

        return self._executePayload(payload)