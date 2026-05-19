# FlashMind

An AI-powered study tool that generates flashcards, quizzes, and adaptive
practice sessions from your notes. Built with Flask and the OpenAI API.

## Features

- **Flashcard generation** — paste notes and get 8–15 flashcards via OpenAI function calling
- **Flip-card viewer** — browse cards with a click-to-flip animation
- **Quiz mode** — mark each card correct or incorrect, see your score
- **Adaptive review** — after a quiz, generates new cards targeting your weak areas
- **Study chat** — multi-turn Q&A tutor grounded in your uploaded notes

## Setup

1. **Clone the repo**
   ```bash
   git clone git clone https://github.com/dariusmajd11/FlashMind.git
   cd flashmind
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # macOS / Linux
   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API key**
   ```bash
   cp .env.example .env
   # Open .env and replace  your_openai_api_key_here  with your actual key
   ```

5. **Run the app**
   ```bash
   python app.py
   ```

6. **Open in your browser**
   ```
   http://localhost:5000
   ```

## How to use

1. Go to the **Input** tab and paste study notes (up to 10,000 characters)
2. Click **✨ Generate Flashcards** and wait a few seconds
3. Browse cards in the **Flashcards** tab — click any card to flip it
4. Click **Start Quiz** to test yourself
5. Mark each answer correct or incorrect; after the quiz see your score
6. If you missed topics, click **🎯 Practice Weak Areas** for targeted cards
7. Use the **Chat** tab to ask follow-up questions about your material

## Running the eval

```bash
python eval/eval.py
```

This tests the flashcard generator against 10 labeled passages and prints a
**Concept Coverage Rate (CCR)** for each. Results are saved to `eval/results.json`.

The eval calls the OpenAI API directly (the server does not need to be running).

## Project structure

```
flashmind/
├── app.py              # Flask backend — /api/generate, /api/adaptive, /api/chat
├── static/
│   └── index.html      # Single-page UI (HTML + CSS + JS, no build step)
├── eval/
│   ├── eval.py         # Evaluation script
│   └── test_cases.json # 10 labeled test cases
├── requirements.txt
├── .env.example
├── README.md
└── REPORT.md
```
