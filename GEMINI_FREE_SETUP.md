# Gemini Free AI Setup

This version replaces the Anthropic SDK with the Google Gemini Developer API.
The AI uses the Gemini REST API directly, so there is no `anthropic` package dependency.

## 1) Create your Gemini API key
Create a key in Google AI Studio. Do not paste the key into chat or commit it to Git.

## 2) Update `.env`
Copy `.env.example` to `.env`, then set:

```env
GEMINI_API_KEY=YOUR_REAL_GEMINI_KEY
AI_MODEL=gemini-2.5-flash
```

`gemini-2.5-flash` currently has a Free Tier, subject to Google's rate/usage limits.

## 3) Install dependencies

```powershell
pip install -r requirements.txt
```

## 4) Database
If you are using a fresh checkout and migration files are not present yet:

```powershell
python manage.py makemigrations
python manage.py migrate
```

If you already generated migrations in your existing working copy, keep those migration files.

## 5) Run

```powershell
python manage.py check
python manage.py runserver
```

Open `http://127.0.0.1:8000/` and test the AI page.

## Important
- The API key is required for real Gemini responses.
- The key is read only from the `.env` environment variable.
- If the key is missing, the UI receives a clear configuration message instead of a generic failure.
- Tool internals are no longer displayed to end users in the chat UI.
