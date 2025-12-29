# DankY 🤖

## What is this project?

If you're a language learner and a programmer, and you use Anki every day to study your flashcards, you've surely experienced how much time you waste creating them. Gathering definitions, examples, IPA, and translations over and over can turn into a boring and repetitive chore.

DankY was created to simplify that process — so you can spend less time building cards and more time actually learning.

DankY is an automated Telegram bot that generates flashcards using open-source dictionaries.  
It currently supports **English** and **German**, with more languages coming soon.

## Dictionaries Supported

- 🇬🇧 **English**: Flashcards based on the [Free Dictionary API](https://dictionaryapi.dev/)
- 🇩🇪 **German**: Flashcards using the [Duden](https://www.duden.de/) dictionary via the ['duden' library developed by radomirbosak](https://github.com/radomirbosak/duden)

Currently, the bot fetches data directly from online dictionaries.
Some words may not have examples or other fields. In the future, optional AI integration (Gemini AI) will fill missing definitions and fields.

### Language Support Policy

At this time, we are focusing on maintaining and improving support for English and German. This bot was created to fulfill my personal language learning needs, and I am not actively adding new languages to the core project.

However, we welcome community contributions! If you would like to add support for a new language:

1. **Fork the repository** and implement the language support following the existing architecture
2. **Create a pull request** with your implementation
3. **Include documentation** explaining:
   - The dictionary/API used
   - Any additional dependencies required
   - Testing examples
   - How to configure the new language

We will review community-submitted language support implementations and may merge them if they meet our quality standards and maintain the project's architecture. Please ensure your implementation follows the existing code patterns and includes proper error handling.

## ✨ Features

🗂️ Each card includes up to **15 definition–example pairs**, plus:

- **IPA** (International Phonetic Alphabet)
- **Translations** into your native language
- **Synonyms**
- 📝 **Part of Speech (POS)** tagging for accurate grammar
- 🎯 **German-specific features**:
  - Grammatical articles (der/die/das)
  - Plural forms for nouns
- 🌍 **Multilingual interface**: Bot messages in English, German, French, Italian, and more
- 🔄 **Language selection**: Switch between learning English or German vocabulary
- 📁 **Bulk import**: Upload Excel, CSV, TSV, or TXT files to create multiple cards at once

---

## 📦 Installation

Follow these steps carefully — skipping any step might prevent the bot from working correctly.

### 1. Clone the repository

```bash
git clone https://github.com/aldomelpignano/DankY.git
cd DankY
```

### 2. Install dependencies

```bash
pip install -r requirments.txt
```

⚠️ **Make sure you are using the correct Python version (>=3.10 recommended).**

### 3. Set up TreeTagger (mandatory before starting the bot)

TreeTagger is used for processing German grammar and generating extra linguistic info. It's not just for Anki — the bot needs it to lemmatize the word, generating correct POS tags.

Run:

```bash
bash setup_TreeTagger.sh
```

At the end, you should see a completion message: **"TreeTagger setup completed! ✅"**


### 4. Install AnkiConnect

AnkiConnect is required for the bot to communicate with Anki. To install it:

1. Open Anki
2. Go to **Tools** → **Add-ons** → **Get Add-ons**
3. Enter the code: `2055492159`
4. Click **OK** and restart Anki

Alternatively, you can download it manually from the [AnkiConnect GitHub repository](https://github.com/amikey/anki-connect).

### 5. Make sure Anki is running

- Open Anki on your computer
- Make sure **AnkiConnect** is installed and enabled
- The bot communicates with Anki using this endpoint:

```bash
http://localhost:8765
```

You can change this in `config.json` if needed.

### 6. Import the DankY Note Type

Before you can use the bot, you must import the custom note type:

1. Open Anki
2. Locate the file in the project folder:

   ```bash
   NoteType.apkg
   ```

3. Import it in Anki. The deck name will be:

   ```bash
   DELETE_ME
   ```

4. After importing, you can **delete the DELETE_ME deck** — the custom note type remains available for DankY.

✅ **Make sure you run TreeTagger first, otherwise the note type may not work properly for German cards.**

**Optional:** Customize the note type if you want. Fields like IPA, definitions, examples, and translations are already set up.

---

## ▶️ Running the Bot

1. Configure your Telegram bot token in `config.json`:

   ```json
   {
     "TELEGRAM_BOT_API": "YOUR_TELEGRAM_BOT_API"
   }
   ```

2. Start the bot:

   ```bash
   python main.py
   ```

3. If everything is correct, you will see:

   ```bash
   Bot is running...
   ```

4. **Recommended next steps:**
   - Set your preferred bot language using `/lang`
   - Select your Anki deck using `/deck [DeckName]`

5. Now you can interact with the bot on Telegram and start generating flashcards!

---

## 🆕 Recent Updates

### Version 1.1 (Latest)

- ✅ **German language support**: Full Duden integration for German words
- ✅ **POS tagging**: Correctly displayed on all cards
- ✅ **German grammar features**: Articles and plural forms automatically extracted
- ✅ **Multilingual interface**: Messages available in multiple languages
- ✅ **Language selection**: Switch between English or German via `/lang`
- ✅ **Improved error handling**: Validates fields, prevents creation of cards for non-existent words
- ✅ **Bulk import**: Supports Excel, CSV, TSV, and TXT files
- ✅ **Better logging**: Full debug logging for troubleshooting

### Changes

- Added Duden support for German words
- Cards only created if mandatory fields exist
- Real-time updates when processing messages
- Full localization, changeable via `/lang` command
