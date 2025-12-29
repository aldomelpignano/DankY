###############################################################################
# src/dictionaries/dicts/german_dict.py
#
# German dictionary implementation using Duden.
# Retrieves word data including definitions, articles, plural forms,
# synonyms, and IPA from the Duden dictionary via the duden library.
# Uses TreeTagger for lemmatization and POS tagging.
###############################################################################

from src.dictionaries.tree_tagger import TreeTagger as Tagger  # import TreeTagger
from src.utils.logging_utils import log
import duden

class German_dict:
    def __init__(self, word: str):
        """
        Initialize a German_dict instance for the given word.
        Performs lemmatization via TreeTagger and retrieves dictionary data from Duden.
        """
        log(f"Initializing German_dict for word='{word}'")
        self.word = word

        # Initialize TreeTagger for German
        self.tagger = Tagger(word, lang="de")

        # Extract lemma and part of speech
        self.lemma = self.tagger.get_lemma()
        self.pos = self.tagger.get_pos()
        log(f"Lemma='{self.lemma}', POS='{self.pos}'")

        # Get Duden entry for the lemma
        try:
            self.duden_result = duden.get(self.lemma)
            log(f"Duden entry fetched successfully for '{self.lemma}'")
        except Exception as e:
            log(f"Failed to fetch Duden entry for '{self.lemma}': {e}")
            self.duden_result = None

    # -----------------------
    #        Utility
    # -----------------------
    def _clean_text(self, text: str) -> str:
        """
        Clean the input text by removing unwanted characters and normalizing whitespace.
        - Non-breaking spaces (\xa0)
        - Zero-width spaces (\u200b)
        - Newlines (\n), carriage returns (\r), tabs (\t)
        - Multiple spaces replaced with a single space
        - Leading/trailing whitespace removed
        """
        if not isinstance(text, str):
            return ""
        text = text.replace('\xa0', ' ').replace('\u200b', '')
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        text = ' '.join(text.split())
        return text

    # -----------------------
    #        Getters
    # -----------------------
    def get_lemma(self):
        """Return the lemma (base form) of the word."""
        return self.lemma

    def get_POS(self):
        """Return the part of speech (POS) of the word."""
        return self.pos

    def get_url(self):
        """Return the URL to the Duden entry for the lemma."""
        url = f"https://www.duden.de/rechtschreibung/{self.get_lemma()}"
        return url

    def get_article(self):
        """Return the grammatical article (if available) from Duden."""
        article = self.duden_result.article if self.duden_result else ""
        return article

    def get_definition(self):
        """
        Return definitions for the word as a clean, flat list.
        
        Handles three cases:
        1. Already flat list of definitions -> clean each definition.
        2. Nested lists -> flatten and clean.
        3. List of single characters (parsing error) -> join into one string and clean.
        """
        if not self.duden_result:
            return []

        definitions = self.duden_result.meaning_overview
        if not definitions:
            return []

        # Case 3: list of single characters (likely a parsing error)
        if all(isinstance(d, str) and len(d) <= 2 for d in definitions):
            joined = ''.join(definitions)
            cleaned = self._clean_text(joined)
            return [cleaned]

        # Case 1 & 2: flatten if nested
        flat_defs = []
        for d in definitions:
            if isinstance(d, list):
                flat_defs.extend(d)
            else:
                flat_defs.append(d)

        # Clean each definition individually
        cleaned_defs = []
        for d in flat_defs:
            cleaned = self._clean_text(d)
            cleaned_defs.append(cleaned)

        return cleaned_defs

    def get_examples(self):
        """
        Currently not implemented.
        In a future update, optional examples could be generated automatically
        using Gemini AI based on the definitions.
        """
        return ""

    def get_synonyms(self):
        """Return a list of synonyms from Duden."""
        synonyms = self.duden_result.synonyms if self.duden_result else []
        return synonyms

    def get_IPA(self):
        """Return the pronunciation (IPA) from Duden."""
        ipa = self.duden_result.phonetic if self.duden_result else ""
        return ipa

    def get_plural(self):
        """
        Return the plural form of the word (if available) from Duden.
        Extracts plural from grammar_overview which can have different formats:
        - "das Haus; Genitiv: des Hauses, Häuser" -> "Häuser"
        - "die Frau; Genitiv: der Frau, Plural: die Frauen" -> "Frauen"
        - "das Kind; Genitiv: des Kind[e]s, Plural: die Kinder" -> "Kinder"
        Returns empty string if not available or not a noun.
        """
        if not self.duden_result:
            return ""
        
        try:
            grammar_overview = self.duden_result.grammar_overview
            if not grammar_overview:
                return ""
            
            # Try to find "Plural: die X" pattern first
            if "Plural:" in grammar_overview:
                # Extract the part after "Plural:"
                plural_part = grammar_overview.split("Plural:")[-1].strip()
                # Remove article (der/die/das) if present and take the first word
                plural_words = plural_part.split()
                # Skip article if present (der, die, das)
                plural = plural_words[-1] if plural_words else ""
                # Clean the plural (remove any trailing punctuation)
                plural = plural.strip('.,;:')
                if plural:
                    return plural
            
            # Fallback: try to extract from comma-separated format
            # Format: "das Haus; Genitiv: des Hauses, Häuser"
            if ',' in grammar_overview:
                # Extract the part after the last comma
                after_comma = grammar_overview.split(',')[-1].strip()
                # Take the last word (the plural form)
                plural = after_comma.split()[-1] if after_comma else ""
                # Clean the plural (remove any trailing punctuation)
                plural = plural.strip('.,;:')
                if plural:
                    return plural
            
            return ""
        except Exception as e:
            log(f"Error getting plural for '{self.word}': {e}", level="WARNING")
            return ""