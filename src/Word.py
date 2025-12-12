# src/Word.py

import simplemma
import requests
import os
from logger import log

class Word:
    def __init__(self, word='none', source_language="en", target_language=None):
        if word == 'none':
            raise ValueError("You must provide a word.")
        
        self.word = word.lower().strip()
        self.rawJson = []
        self.dictionary = f"https://api.dictionaryapi.dev/api/v2/entries/en/{self.word}"
        self.source_language = source_language
        self.target_language = target_language
        log(f"Word object created: '{self.word}', source_lang={source_language}, target_lang={target_language}", level="DEBUG")

    def _get_json(self):
        if not self.rawJson:
            try:
                log(f"Fetching JSON for '{self.word}' from {self.dictionary}", level="DEBUG")
                response = requests.get(self.dictionary)
                self.rawJson = response.json()
                log(f"JSON fetched successfully for '{self.word}'", level="DEBUG")
            except requests.RequestException as e:
                log(f"RequestException: {e}", level="ERROR")
                raise SystemError("Failed to contact the dictionary API.")
            except ValueError as e:
                log(f"JSON parse error: {e}", level="ERROR")
                raise SystemError("Invalid JSON received.")

    def _try_connection(self):
        self._get_json()
        if isinstance(self.rawJson, list) and len(self.rawJson) > 0:
            log(f"Word '{self.word}' exists in dictionary", level="DEBUG")
            return True
        if isinstance(self.rawJson, dict) and self.rawJson.get("title") == "No Definitions Found":
            log(f"Word '{self.word}' not found in dictionary", level="DEBUG")
            raise SystemError(f"The word '{self.word}' was not found in the dictionary.")
        raise SystemError("Unexpected response from the dictionary API.")

    def lemmatize(self, checkExistence=True):
        ARTICLES_LIST = ["the", "a", "an", "to"]
        for art in ARTICLES_LIST:
            if self.word.startswith(art + " "):
                self.word = self.word[len(art):].strip()
                break
        if " " in self.word:
            raise ValueError("Only one word is allowed, not a phrase.")

        self.word = simplemma.lemmatize(self.word, 'en')
        log(f"Lemmatized word: '{self.word}'", level="DEBUG")

        if checkExistence:
            self._try_connection()
        return self.word

    def get_source_url(self):
        self._get_json()
        urls = self.rawJson[0].get("sourceUrls", [])
        result = urls[0] if urls else ""
        log(f"Source URL for '{self.word}': {result}", level="DEBUG")
        return result

    def get_definition(self, max_definitions=15):
        self._get_json()
        definitions = []
        meanings = self.rawJson[0].get("meanings", [])
        for meaning in meanings:
            defs = meaning.get("definitions", [])
            for d in defs:
                definitions.append({
                    f"def{len(definitions)+1}": d.get("definition", ""),
                    f"ex{len(definitions)+1}": d.get("example", "")
                })
                if len(definitions) >= max_definitions:
                    log(f"Collected {len(definitions)} definitions for '{self.word}'", level="DEBUG")
                    return definitions
        log(f"Collected {len(definitions)} definitions for '{self.word}'", level="DEBUG")
        return definitions

    def get_synonyms(self):
        self._get_json()
        synonyms = set()
        for meaning in self.rawJson[0].get("meanings", []):
            synonyms.update(meaning.get("synonyms", []))
            for d in meaning.get("definitions", []):
                synonyms.update(d.get("synonyms", []))
        result = list(synonyms)
        log(f"Synonyms for '{self.word}': {result}", level="DEBUG")
        return result

    def get_antonyms(self):
        self._get_json()
        antonyms = set()
        for meaning in self.rawJson[0].get("meanings", []):
            antonyms.update(meaning.get("antonyms", []))
            for d in meaning.get("definitions", []):
                antonyms.update(d.get("antonyms", []))
        result = list(antonyms)
        log(f"Antonyms for '{self.word}': {result}", level="DEBUG")
        return result

    def get_POS(self):
        self._get_json()
        pos = self.rawJson[0].get("meanings", [{}])[0].get("partOfSpeech", "")
        log(f"Part of Speech for '{self.word}': {pos}", level="DEBUG")
        return pos

    def get_IPA(self):
        self._get_json()
        ipa = self.rawJson[0].get("phonetic", "")
        log(f"IPA for '{self.word}': {ipa}", level="DEBUG")
        return ipa

    def get_audio(self):
        self._get_json()
        us_audio, uk_audio = "", ""
        for p in self.rawJson[0].get("phonetics", []):
            audio = p.get("audio", "")
            if not audio: continue
            if "-us." in audio and not us_audio: us_audio = audio
            elif "-uk." in audio and not uk_audio: uk_audio = audio
        audio_url = us_audio if us_audio else uk_audio
        if not audio_url:
            log(f"No audio available for '{self.word}'", level="DEBUG")
            return
        folder = os.path.join(os.path.dirname(__file__), ".temp_audio")
        os.makedirs(folder, exist_ok=True)
        filename = os.path.join(folder, f"{self.word}.mp3")
        try:
            r = requests.get(audio_url, stream=True)
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            log(f"Audio downloaded for '{self.word}' as {filename}", level="DEBUG")
        except requests.RequestException as e:
            log(f"Failed to download audio for '{self.word}': {e}", level="ERROR")

    def get_translation(self):
        if self.target_language is None:
            return ""
        url = f"https://lingva.ml/api/v1/{self.source_language}/{self.target_language}/{self.word}"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            translated = data.get("translation")
            if not translated:
                raise ValueError("No translation found.")
            log(f"Translation for '{self.word}': {translated}", level="DEBUG")
            return translated.capitalize()
        except Exception as e:
            log(f"Translation error for '{self.word}': {e}", level="ERROR")
            return ""
