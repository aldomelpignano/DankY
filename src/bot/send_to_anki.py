###############################################################################
# src/bot/send_to_anki.py
#
# Handles communication with Anki via AnkiConnect API.
# Prepares flashcard fields and sends them to Anki for note creation.
# Validates mandatory fields before creating cards.
###############################################################################

import requests
from src.dictionaries.dictionaries_manager import DictionariesManager
from src.utils.logging_utils import log
from src.utils.language_utils import LanguageUtils as LangU


class MissingMandatoryFieldError(Exception):
    """Exception raised when a mandatory field is missing or empty."""
    def __init__(self, missing_fields, word=None):
        self.missing_fields = missing_fields
        self.word = word
        if word:
            message = f"Cannot create note for '{word}': missing mandatory fields: {', '.join(missing_fields)}"
        else:
            message = f"Cannot create note: missing mandatory fields: {', '.join(missing_fields)}"
        super().__init__(message)

class SendToAnki:
    
    def __init__(self, deck_name: str, endpoint: str = "http://127.0.0.1:8765", model_name: str = "DankY"):
        self.deck_name = deck_name
        self.endpoint = endpoint
        self.model_name = model_name

        lang_utils = LangU()
        self.lang_code = lang_utils.get_target_language()
        self.translation_language = lang_utils.get_translation_language()

    # -----------------------
    #      Anki Payloads
    # -----------------------
    def _setPayload(self, action: str, lemma: str = None, version: int = 6):
        payload = {"action": action, "version": version}
        if action == "findNotes":
            payload["params"] = {"query": f"deck:{self.deck_name} lemma:{lemma}"}
        return payload

    def _executePayload(self, payload) -> dict:
        try:
            response = requests.post(self.endpoint, json=payload, timeout=10)
            response.raise_for_status()
            json_response = response.json()
            return json_response
        except requests.exceptions.RequestException as e:
            log(f"Anki connection error: {e}", level="ERROR")
            raise ConnectionError("Connection with Anki failed, make sure Anki and AnkiConnect are running.")
        except ValueError as e:
            log(f"Anki returned invalid JSON: {e}", level="ERROR")
            raise ConnectionError("Anki returned invalid JSON data.")

    def _tryConnectionToAnki(self):
        payload = self._setPayload("version")
        return self._executePayload(payload)

    # -----------------------
    #    Prepare Fields
    # -----------------------
    def _prepareFields(self, word_str):
        if isinstance(word_str, DictionariesManager):
            word_obj = word_str
        else:
            word_obj = DictionariesManager(word_str, selected_dictionary=self.lang_code, translation_language=self.translation_language)

        url = word_obj.get_url()
        lemma = word_obj.get_lemma()
        
        # Get IPA (fallback logic is handled in DictionariesManager)
        try:
            ipa = word_obj.get_IPA()
            if ipa is None:
                ipa = ""
        except Exception as e:
            log(f"Error getting IPA for '{lemma}': {e}", level="WARNING")
            ipa = ""
        
        # Get POS
        try:
            pos = word_obj.get_POS()
            if pos is None:
                pos = ""
            elif not isinstance(pos, str):
                pos = str(pos) if pos else ""
            else:
                pos = pos.strip() if pos.strip() else ""
        except Exception as e:
            log(f"Error getting POS for '{lemma}': {e}", level="WARNING")
            pos = ""
        
        # Final validation: ensure pos is a string (never None)
        pos = pos if pos is not None else ""
        
        # Get article
        try:
            article = word_obj.get_article()
            if article is None:
                article = ""
            elif not isinstance(article, str):
                article = str(article) if article else ""
            else:
                article = article.strip() if article.strip() else ""
        except Exception as e:
            log(f"Error getting article for '{lemma}': {e}", level="WARNING")
            article = ""
        
        # Final validation: ensure article is a string (never None)
        article = article if article is not None else ""
        
        # Get plural
        try:
            plural = word_obj.get_plural()
            if plural is None:
                plural = ""
            elif not isinstance(plural, str):
                plural = str(plural) if plural else ""
            else:
                plural = plural.strip() if plural.strip() else ""
        except Exception as e:
            log(f"Error getting plural for '{lemma}': {e}", level="WARNING")
            plural = ""
        
        # Final validation: ensure plural is a string (never None)
        plural = plural if plural is not None else ""
        
        # Get translation
        try:
            translation = word_obj.get_translation()
        except AttributeError:
            translation = ""
        except Exception as e:
            log(f"Error getting translation for '{lemma}': {e}", level="WARNING")
            translation = ""
        
        # Get synonyms with None handling
        synonyms = []
        try:
            synonyms = word_obj.get_synonyms()
            if synonyms is None:
                synonyms = []
            elif not isinstance(synonyms, (list, set, tuple)):
                log(f"Synonyms returned unexpected type for '{lemma}': {type(synonyms)}", level="WARNING")
                synonyms = []
        except (AttributeError, Exception) as e:
            log(f"Error getting synonyms for '{lemma}': {e}", level="WARNING")
            synonyms = []

        # Ensure all fields are strings (no None values)
        fields = {
            "url": url if url is not None else "",
            "lemma": lemma if lemma is not None else "",
            "IPA": ipa if ipa is not None else "",
            "POS": pos if pos is not None else "",
            "article": article if article is not None else "",
            "plural": plural if plural is not None else "",
            "translated_lemma": translation if translation is not None else "",
            "synonyms": ", ".join(synonyms) if synonyms else "",
        }

        # Get definitions - do not use fallback, let it be empty if no definitions found
        definitions = word_obj.get_definition() or []
        for i, d in enumerate(definitions[:15], start=1):
            fields[f"def{i}"] = d or ""

        examples = word_obj.get_examples() or []
        for i, ex in enumerate(examples[:15], start=1):
            fields[f"ex{i}"] = ex or ""

        return fields

    # -----------------------
    #    Check & Add Notes
    # -----------------------
    def checkExistence(self, lemma: str) -> bool:
        payload = self._setPayload("findNotes", lemma)
        response = self._executePayload(payload)
        exists = bool(response.get("result"))
        return exists

    def addNotes(self, word_str: str):
        fields = self._prepareFields(word_str)

        # Define mandatory fields that must be present and non-empty
        mandatory_fields = ["def1"]
        missing_fields = []
        
        # Check each mandatory field
        for field_name in mandatory_fields:
            field_value = fields.get(field_name)
            # Check if field is missing, None, or empty string (after stripping whitespace)
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                missing_fields.append(field_name)
        
        # If any mandatory fields are missing, raise exception with details
        if missing_fields:
            log(f"Missing mandatory fields for '{word_str}': {missing_fields}", level="ERROR")
            raise MissingMandatoryFieldError(missing_fields, word=word_str)

        # Also check that lemma exists (required for Anki operations)
        lemma = fields.get("lemma")
        if not lemma or (isinstance(lemma, str) and not lemma.strip()):
            log(f"Lemma field missing for '{word_str}'", level="ERROR")
            raise MissingMandatoryFieldError(["lemma"], word=word_str)

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

        if not self.checkExistence(lemma):
            log(f"Adding note for '{lemma}'", level="INFO")
            response = self._executePayload(payload)
        else:
            raise ValueError(f"The word '{lemma}' already exists in the deck '{self.deck_name}'.")
