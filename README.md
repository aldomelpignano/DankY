# DankY 🤖

## What this project is?

If you're a language learner as well as a programmer like me, and you use Anki every day to study your flashcards, you've surely experienced how much time you waste creating them. Gathering definitions, examples, IPA, and translations over and over can turn into a boring and repetitive chore.  
DankY was created exactly to simplify that process — so you can spend less time building cards and more time actually learning.

DankY (my first real project) is an automated Telegram bot that generates flashcards using open-source dictionaries.  
It currently supports English, with more languages — like German — coming soon.

---

## ✨ Features

- 🇬🇧 English vocabulary flashcard generation based on the [Free Dictionary API](https://dictionaryapi.dev/)  
- 🗂️ Each card includes up to **15 definition–example pairs**, plus **IPA**, **translations into your native language**, **synonyms**, and **antonyms**.

---

## 🚧 Upcoming Features (In Development)

- 🌍 Support for more languages (German, Italian, etc.)  
- 🔊 Built-in pronunciation audio  
- 🔄 Improved dictionary fallback system  
- 👤 User profiles with saved preferences  

---

## 📦 Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/aldomelpignano/DankY.git
    cd DankY
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Make sure Anki is running with AnkiConnect installed.  
    The bot communicates by default with Anki through:  
    ```bash
    http://localhost:8765
    ```
    (You can configure this in `config.json` if necessary.)

---

## ▶️ Running the Bot

1. Configure the bot token in the `config.json` file:

     ```bash
     TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_API"
     ```

2. Start the bot with:

     ```bash
     python main.py
     ```

3. If everything is correct, you will see:

     ```bash
     Bot is running...
     ```

4. Good luck and happy learning!