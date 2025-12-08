import simplemma
import requests
import os

class Word:

    def __init__(self, word='none'):
        # Raise error if no word is provided
        if word == 'none':
            raise ValueError("You must provide a word.")
        
        # Store the word in lowercase and stripped of spaces
        self.word = word.lower().strip()
        # Cache for JSON data from the dictionary API
        self.rawJson = []
        # URL for the dictionary API
        self.dictionary = f"https://api.dictionaryapi.dev/api/v2/entries/en/{self.word}"

    def _get_json(self):
        # Only fetch JSON if we haven't already
        if not self.rawJson:
            try:
                response = requests.get(self.dictionary)
                self.rawJson = response.json()
            
            except requests.RequestException:
                raise SystemError("Failed to contact the dictionary API.")
            except ValueError:
                raise SystemError("Invalid JSON received (HTML error?).")
    
    def _try_connection(self):
        # Check if the word exists in the dictionary
        self._get_json() 

        # If response is a non-empty list, the word exists
        if isinstance(self.rawJson, list) and len(self.rawJson) > 0:
            return True
        # If API says "No Definitions Found", raise an error
        if isinstance(self.rawJson, dict) and self.rawJson.get("title") == "No Definitions Found":
            raise SystemError(f"The word '{self.word}' was not found in the dictionary.")
        
        # Otherwise, the response is unexpected
        raise SystemError("Unexpected response from the dictionary API.")

    def lemmatize(self, checkExistence=True):
        ARTICLES_LIST = ["the", "a", "an", "to"]

        # Remove leading articles from the word
        for art in ARTICLES_LIST:
            if self.word.startswith(art + " "):
                self.word = self.word[len(art):].strip()
                break
        
        # Only allow single words, not phrases
        if " " in self.word:
            raise ValueError("Only one word is allowed, not a phrase.")

        # Lemmatize the word using simplemma
        self.word = simplemma.lemmatize(self.word, 'en')

        # Optionally check if the word exists in the dictionary
        if checkExistence:
            self._try_connection()
        return self.word

    def get_source_url(self):
        # Fetch JSON if needed
        self._get_json()
        
        # Return the first source URL, if any
        urls = self.rawJson[0].get("sourceUrls", [])
        if urls:
            return urls[0]
        return ""  # Return empty string if no URLs found
    
    def get_definition(self, max_definitions=15):
        self._get_json()
        definitions = []

        meanings = self.rawJson[0].get("meanings", [])
        for meaning in meanings:
            defs = meaning.get("definitions", [])

            for d in defs:
                definition = d.get("definition")
                example = d.get("example")

                # Skip definitions without examples
                if not example:
                    continue

                # Add definition and example to the list
                definitions.append({
                    f"def{len(definitions)+1}": definition,
                    f"ex{len(definitions)+1}": example
                })

                # Stop if maximum definitions reached
                if len(definitions) >= max_definitions:
                    return definitions

        # Return whatever definitions we have
        return definitions

    def get_synonyms(self):
        """Collects all synonyms of the word."""
        self._get_json()
        synonyms = set()  # Use a set to avoid duplicates

        for meaning in self.rawJson[0].get("meanings", []):
            # Synonyms at the meaning level
            synonyms.update(meaning.get("synonyms", []))
            # Synonyms at the definition level
            for d in meaning.get("definitions", []):
                synonyms.update(d.get("synonyms", []))

        return list(synonyms)

    def get_antonyms(self):
        """Collects all antonyms of the word."""
        self._get_json()
        antonyms = set()

        for meaning in self.rawJson[0].get("meanings", []):
            # Antonyms at the meaning level
            antonyms.update(meaning.get("antonyms", []))
            # Antonyms at the definition level
            for d in meaning.get("definitions", []):
                antonyms.update(d.get("antonyms", []))

        return list(antonyms)

    def get_POS(self):
        # Return the part of speech of the first meaning
        self._get_json()
        return self.rawJson[0].get("meanings", [])[0].get("partOfSpeech", "")

    def get_IPA(self):
        # Return the phonetic transcription (IPA)
        self._get_json()
        return self.rawJson[0].get("phonetic", "")
    
    def get_audio(self):
        # Download pronunciation audio
        self._get_json()

        us_audio = ""
        uk_audio = ""

        # Look for US and UK audio
        for p in self.rawJson[0].get("phonetics", []):
            audio = p.get("audio", "")
            if not audio:
                continue
            if "-us." in audio and not us_audio:
                us_audio = audio
            elif "-uk." in audio and not uk_audio:
                uk_audio = audio

        # Choose which audio to download
        audio_url = us_audio if us_audio else uk_audio
        if not audio_url:
            print(f"No audio available for '{self.word}'")
            return

        # Create folder for temporary audio files
        folder = os.path.join(os.path.dirname(__file__), ".temp_audio")
        os.makedirs(folder, exist_ok=True)

        filename = os.path.join(folder, f"{self.word}.mp3")

        try:
            r = requests.get(audio_url, stream=True)
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            print(f"Audio downloaded for '{self.word}' as {filename}")
        except requests.RequestException as e:
            print(f"Failed to download audio for '{self.word}': {e}")

    def get_translation(self, target_lang):
        # Translate the word to the target language using Lingva API
        url = f"https://lingva.ml/api/v1/en/{target_lang}/{self.word}"

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()

            translated = data.get("translation")
            if not translated:
                raise ValueError("No translation found.")

            return translated.capitalize()

        except Exception as e:
            raise ValueError(f"Translation error: {e}")
