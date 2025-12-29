###############################################################################
# src/dictionaries/dicts/english_dict.py
#
# English dictionary implementation using Free Dictionary API.
# Retrieves word data including definitions, examples, synonyms,
# antonyms, and IPA from dictionaryapi.dev.
# Uses TreeTagger for lemmatization and POS tagging.
###############################################################################

from src.dictionaries.tree_tagger import TreeTagger as Tagger  # import TreeTagger
from src.utils.logging_utils import log
import requests

class English_dict:
    """
    Wrapper for English word data.
    Uses TreeTagger for lemmatization and POS tagging,
    and dictionaryapi.dev for definitions, examples, synonyms, and IPA.
    """

    def __init__(self, word: str):
        """
        Initialize the English_dict instance.
        - Lemmatize and get POS via TreeTagger
        - Fetch dictionary data from dictionaryapi.dev
        """
        log(f"Initializing English_dict for word='{word}'")
        self.word = word
        self.tagger = Tagger(word, lang="en")

        # Linguistic data
        self.lemma = self.tagger.get_lemma()
        self.pos = self.tagger.get_pos()
        log(f"Lemma='{self.lemma}', POS='{self.pos}'")

        # Dictionary lookup URL
        self.api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{self.lemma}"
        self.data = self._fetch_data()

    # -----------------------#
    #      Private helpers   #
    # -----------------------#
    def _fetch_data(self):
        """
        Fetch JSON data from the dictionary API.
        Returns an empty dict if fetch fails or response is invalid.
        """
        try:
            log(f"Fetching data from API: {self.api_url}")
            response = requests.get(self.api_url, timeout=5)
            response.raise_for_status()
            json_data = response.json()
            # pick the first entry if multiple
            if isinstance(json_data, list) and json_data:
                log(f"Data fetched successfully for '{self.lemma}'")
                return json_data[0]
            return {}
        except Exception as e:
            log(f"Failed to fetch data for '{self.lemma}': {e}")
            return {}

    # -----------------------#
    #         Getters        #
    # -----------------------#
    def get_lemma(self):
        """Return the lemma (base form) of the word."""
        log(f"get_lemma called for '{self.word}' -> '{self.lemma}'")
        return self.lemma

    def get_POS(self):
        """Return the part of speech (noun, verb, etc.) of the word."""
        log(f"get_POS called for '{self.word}' -> '{self.pos}'")
        return self.pos

    def get_url(self):
        """Return the source URL of the dictionary entry."""
        try:
            urls = self.data.get("sourceUrls", [])
            url = urls[0] if urls else ""
            log(f"get_url for '{self.word}' -> '{url}'")
            return url
        except Exception as e:
            log(f"Error in get_url for '{self.word}': {e}")
            return ""

    def get_article(self):
        """
        Return the definite article if available.
        English words generally do not have grammatical articles,
        so this always returns an empty string.
        """
        log(f"get_article called for '{self.word}' -> ''")
        return ""

    def get_definition(self):
        """
        Return a list of definitions for the word.
        Iterates over meanings and definitions in the API response.
        Returns an empty list if no definitions are found.
        """
        definitions = []
        try:
            meanings = self.data.get("meanings", [])
            for meaning in meanings:
                defs = meaning.get("definitions", [])
                for d in defs:
                    definitions.append(d.get("definition", ""))
            log(f"get_definition for '{self.word}' -> {len(definitions)} definitions")
        except Exception as e:
            log(f"Error in get_definition for '{self.word}': {e}")
        return definitions

    def get_examples(self):
        """
        Return example sentences for the word.
        Returns an empty list if none are found or on error.
        """
        examples = []
        try:
            meanings = self.data.get("meanings", [])
            for meaning in meanings:
                defs = meaning.get("definitions", [])
                for d in defs:
                    ex = d.get("example")
                    if ex:
                        examples.append(ex)
            log(f"get_examples for '{self.word}' -> {len(examples)} examples")
        except Exception as e:
            log(f"Error in get_examples for '{self.word}': {e}")
        return examples

    def get_synonyms(self):
        """
        Return a set of synonyms for the word.
        Aggregates synonyms from meanings and individual definitions.
        Returns an empty set if none are found or on error.
        """
        synonyms = set()
        try:
            meanings = self.data.get("meanings", [])
            for meaning in meanings:
                synonyms.update(meaning.get("synonyms", []))
                for d in meaning.get("definitions", []):
                    synonyms.update(d.get("synonyms", []))
            log(f"get_synonyms for '{self.word}' -> {len(synonyms)} synonyms")
        except Exception as e:
            log(f"Error in get_synonyms for '{self.word}': {e}")
        return synonyms

    def get_IPA(self):
        """
        Return the pronunciation in IPA format.
        Returns an empty string if not available or on error.
        """
        try:
            ipa = self.data.get("phonetic", "")
            log(f"get_IPA for '{self.word}' -> '{ipa}'")
            return ipa
        except Exception as e:
            log(f"Error in get_IPA for '{self.word}': {e}")
            return ""
