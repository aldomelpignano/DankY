# /TreeTagger/TreeTagger.py

"""
TreeTagger Python Wrapper
------------------------------------------

This module provides a high-level Python interface to the TreeTagger tool for German.
TreeTagger is a widely used part-of-speech (POS) tagger and lemmatizer developed by 
Helmut Schmid at the University of Stuttgart. It allows you to automatically annotate 
text with POS tags and lemmas (base forms of words).

Reference:
- Helmut Schmid (1995): Improvements in Part-of-Speech Tagging with an Application to German. ACL SIGDAT Workshop.
- Helmut Schmid (1994): Probabilistic Part-of-Speech Tagging Using Decision Trees. Conference on New Methods in Language Processing.

Official TreeTagger site: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/
Python wrapper documentation: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/python.html

Features of this wrapper:
- Automatically tags a single German word with its POS and lemma.
- Simplifies TreeTagger POS tags into readable English categories.
- Returns results as strings for easy use (instead of lists).
- Handles TreeTagger initialization errors with clear messages.
"""

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import treetaggerwrapper

class TreeTagger:

    TREETAGGER_DIRECTORY = './DankY/.TreeTagger'

    # Simplified POS mapping to readable names
    POS_MAP = {
        "NN": "Noun", "NE": "Noun",
        "VVINF": "Verb", "VVPP": "Verb", "VVFIN": "Verb",
        "VVIMP": "Verb", "VVP": "Verb",
        "VAFIN": "Verb", "VAINF": "Verb", "VAPP": "Verb",
        "VVIZU": "Verb",
        "ADJD": "Adjective", "ADJA": "Adjective",
        "ADV": "Adverb",
        "PPOSAT": "Pronoun", "PDAT": "Pronoun", "PIS": "Pronoun", "PIAT": "Pronoun",
        "PTKVZ": "Particle/Preposition",
        "KOUI": "Conjunction", "KOUS": "Conjunction", "KON": "Conjunction",
        "ART": "Article",
        "APPO": "Apposition",
        "FM": "Other", "ITJ": "Other",
        "CARD": "Numeral",
        "APPR": "Particle/Preposition", "APPRART": "Particle/Preposition"
    }

    def __init__(self, word: str, lang: str):
        self.word = word

        # Initialize TreeTagger for German
        try:
            self.tagger = treetaggerwrapper.TreeTagger(TAGLANG=lang, TAGDIR=self.TREETAGGER_DIRECTORY)
        except Exception as e:
            raise RuntimeError(
                f"TreeTagger not found in '{self.TREETAGGER_DIRECTORY}'.\n"
                "Please run 'setup_TreeTagger.sh' or download TreeTagger manually and place it correctly."
            )

        # Tag the word once and store parsed tags
        self.parsed_tags = treetaggerwrapper.make_tags(
            self.tagger.tag_text(self.word)
        )

    def get_pos(self) -> str:
        """Return the simplified POS of the word as a string."""
        pos_list = [self.POS_MAP.get(t.pos, t.pos) for t in self.parsed_tags if t is not None]
        return " ".join(pos_list)

    def get_lemma(self) -> str:
        """Return the lemma of the word as a string."""
        lemma_list = [t.lemma for t in self.parsed_tags if t is not None]
        return " ".join(lemma_list)

def main():
    word = input("Enter a German word to tag: ").strip()
    
    # Inizializza il wrapper
    try:
        tagger = TreeTagger(word, lang='de')  # 'de' per tedesco
    except RuntimeError as e:
        print(f"Error: {e}")
        return

    # Stampa POS semplificato e lemma
    print(f"Word: {word}")
    print(f"POS: {tagger.get_pos()}")
    print(f"Lemma: {tagger.get_lemma()}")

if __name__ == "__main__":
    main()