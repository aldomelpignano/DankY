###############################################################################
# src/dictionaries/dictionaries_manager.py
#
# Unified interface for multiple dictionary implementations.
# Provides access to word data (definitions, examples, synonyms, IPA, etc.)
# from different language dictionaries (English, German).
# Handles translation services and IPA fallback mechanisms.
###############################################################################

from src.dictionaries.dicts.english_dict import English_dict
from src.dictionaries.dicts.german_dict import German_dict

from src.utils.logging_utils import log
from deep_translator import GoogleTranslator, MyMemoryTranslator, LingueeTranslator, PonsTranslator

        # Try to import epitran for IPA fallback (optional)
try:
    import epitran
    EPITRAN_AVAILABLE = True
except ImportError:
    EPITRAN_AVAILABLE = False

class DictionariesManager:
    """
    Unified interface for multiple dictionaries.
    Provides access to lemma, part of speech, definitions, examples,
    synonyms, IPA, articles, URLs, and optional translation for a word.
    """

    # Map language codes to dictionary classes
    DICTS = {
        "en": English_dict,
        "de": German_dict
    }

    def __init__(self, word, selected_dictionary="en", max_items=15, translation_language=None):
        self.word = word
        self.lang = selected_dictionary
        self.max_items = max_items
        self.translation_language = translation_language

        log(f"Initializing DictionariesManager for word='{self.word}', lang='{self.lang}'")

        if self.lang not in self.DICTS:
            log(f"Invalid dictionary code: {self.lang}")
            raise ValueError(f"You must enter a valid dictionary: {list(self.DICTS.keys())}")

        try:
            self.dictionary = self.DICTS[self.lang](self.word)
            log(f"Dictionary '{self.lang}' initialized successfully for word '{self.word}'")
        except Exception as e:
            log(f"Failed to initialize dictionary: {e}")
            raise RuntimeError(f"Failed to initialize dictionary for '{self.word}' in {self.lang}: {e}")

    # -----------------------
    # Public getter methods
    # -----------------------
    def get_lemma(self):
        log(f"Getting lemma for '{self.word}'")
        try:
            return self.dictionary.get_lemma()
        except Exception as e:
            log(f"Error getting lemma: {e}")
            raise RuntimeError(f"Error getting lemma for '{self.word}' in {self.lang}: {e}")

    def get_POS(self):
        log(f"Getting POS for '{self.word}'")
        try:
            return self.dictionary.get_POS()
        except Exception as e:
            log(f"Error getting POS: {e}")
            return ""

    def get_url(self):
        log(f"Getting URL for '{self.word}'")
        try:
            return self.dictionary.get_url()
        except Exception as e:
            log(f"Error getting URL: {e}")
            return ""

    def get_article(self):
        log(f"Getting article for '{self.word}'")
        try:
            return self.dictionary.get_article()
        except Exception as e:
            log(f"Error getting article: {e}")
            return ""

    def get_plural(self):
        log(f"Getting plural for '{self.word}'")
        try:
            # Check if dictionary has get_plural method (only German_dict has it)
            if hasattr(self.dictionary, 'get_plural'):
                return self.dictionary.get_plural()
            else:
                log(f"get_plural not available for dictionary type '{type(self.dictionary).__name__}'")
                return ""
        except Exception as e:
            log(f"Error getting plural: {e}")
            return ""

    def get_definition(self):
        log(f"Getting definitions for '{self.word}'")
        try:
            definitions = self.dictionary.get_definition()
            if isinstance(definitions, list):
                return definitions[:self.max_items]
            return definitions
        except Exception as e:
            log(f"Error getting definitions: {e}")
            raise RuntimeError(f"Error getting definitions for '{self.word}' in {self.lang}: {e}")

    def get_examples(self):
        log(f"Getting examples for '{self.word}'")
        try:
            examples = self.dictionary.get_examples()
            if isinstance(examples, list):
                return examples[:self.max_items]
            return examples
        except Exception as e:
            log(f"Error getting examples: {e}")
            return []

    def get_synonyms(self):
        log(f"Getting synonyms for '{self.word}'")
        try:
            return self.dictionary.get_synonyms()
        except Exception as e:
            log(f"Error getting synonyms: {e}")
            return []

    def get_IPA(self):
        ipa = ""
        lemma = self.get_lemma()
        
        # Try to get IPA from dictionary
        try:
            ipa = self.dictionary.get_IPA()
            if ipa is None or not ipa.strip():
                ipa = ""
        except Exception as e:
            log(f"Error getting IPA from dictionary for '{lemma}': {e}", level="WARNING")
            ipa = ""
        
        # Fallback to epitran if IPA is still empty and language is German
        if not ipa and self.lang == "de" and EPITRAN_AVAILABLE:
            try:
                ep = epitran.Epitran("deu-Latn")
                ipa = ep.transliterate(lemma)
                if not ipa or not ipa.strip():
                    ipa = ""
            except Exception as e:
                log(f"Error getting IPA from epitran for '{lemma}': {e}", level="WARNING")
                ipa = ""
        
        return ipa if ipa and ipa.strip() else ""

    # -----------------------
    #       translation
    # -----------------------
    def get_translation(self):
        log(f"Getting translation for '{self.word}' to '{self.translation_language}'")
        if not self.translation_language:
            log("No translation language set")
            return ""

        # Use lemma instead of original word for better translation accuracy
        lemma = self.get_lemma()
        
        # List of translators to try in order (all free, no API key required)
        translators = [
            ("GoogleTranslator", GoogleTranslator),
            ("MyMemoryTranslator", MyMemoryTranslator),
            ("LingueeTranslator", LingueeTranslator),
            ("PonsTranslator", PonsTranslator),
        ]
        
        # Try each translator in order until one succeeds
        for translator_name, translator_class in translators:
            try:
                log(f"Attempting translation with {translator_name} for '{lemma}' (source: {self.lang}, target: {self.translation_language})")
                translator = translator_class(source=self.lang, target=self.translation_language)
                translated = translator.translate(lemma)
                
                if translated and translated.strip():
                    result = translated.capitalize()
                    log(f"Translation successful with {translator_name}: '{translated}' -> '{result}'")
                    return result
                else:
                    log(f"{translator_name} returned empty translation, trying next translator")
                    
            except Exception as e:
                log(f"{translator_name} failed for '{lemma}': {e}")
                continue
        
        # All translators failed
        log(f"All translators failed for '{lemma}' (source: {self.lang}, target: {self.translation_language})")
        return ""
