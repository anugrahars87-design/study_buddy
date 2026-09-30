# 📚 Study Buddy

An AI-powered study assistant built with [Streamlit](https://streamlit.io) and [Claude](https://www.anthropic.com).

## Features

| Feature | Description |
|---|---|
| 💡 **Topic Explainer** | Explain any concept at a chosen level (beginner → expert) |
| 📝 **Notes Summariser** | Paste text or upload a PDF and get a structured summary |
| 🧠 **MCQ Quiz** | Generate a scored multiple-choice quiz on any topic |
| 🗂️ **Flashcards** | Create interactive flip-card flashcards from a topic or notes |

## Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd study-buddy
```

### 2. Create and activate a virtual environment

```bash
# macOS / Linux
python -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

```bash
cp .env.example .env
# Open .env and set ANTHROPIC_API_KEY=your-key-here
```

### 5. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Project structure

```
study-buddy/
├── app.py              # All application code (single-file)
├── requirements.txt    # Python dependencies
├── .env.example        # API key template (safe to commit)
├── .env                # Your actual secrets (git-ignored)
├── .gitignore
└── README.md
```

## Stack

- **[Streamlit](https://streamlit.io)** — UI framework
- **[Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)** — LLM API (`claude-3-5-haiku`)
- **[pypdf](https://github.com/py-pdf/pypdf)** — PDF text extraction
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — `.env` loading

## Notes

- The API key is loaded from `.env` and never hard-coded.
- Quiz and flashcard data are requested as JSON from the model and validated before use.
- All features live in a single `app.py` file as specified.
