# Sunsettr (class version) — OIM 3641 project

A small Python app that shows one idea: **a sales lead chats with an AI, the AI scores the
lead, and the salesperson (the "closer") gets a one-page brief before the call.** The business
owner sees the whole funnel, from link clicks to closed deals.

It is the class-sized version of a startup idea. Everything in it is invented: the business
("Maya Coaching"), the closer ("Jordan") and every lead.

## Three people, three views

| Who | How they get in | What they see |
|---|---|---|
| **Lead** | The lead chat link (`…/?lead=new`) | Only the chat. No menu, no score, no brief. The AI says it is an AI, asks 5 to 7 questions, answers questions only from the offer file, and confirms the call time at the end. |
| **Closer** | "Continue as Jordan" on the start screen | **Dashboard** (their numbers, upcoming calls with links to each brief, score and chat log, and what needs attention), **Call calendar** (upcoming calls by day, history, recording call results), **Lead file** (brief, score, chat log for one lead). |
| **Owner** | "Continue as the owner" on the start screen | **Funnel** (link clicks → chat started → chat finished → showed up → closed, with the biggest leak marked, plus results by score band), **Leads and chat logs**, **Lead file**, **Offer file**, **Settings**. |

There is no real sign-in yet: the start screen is demo access, and it says so on screen.

## How to run it

You need [uv](https://docs.astral.sh/uv/) (it installs Python and the packages for you).

```bash
uv sync
```

```bash
uv run streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

Run the tests:

```bash
uv run pytest
```

### The API key (for live AI)

The app reads one environment variable, **`GEMINI_API_KEY`**, from a file named `.env` in this
folder. The file holds a single line:

```
GEMINI_API_KEY=your-key-from-Google-AI-Studio
```

`.env` is listed in `.gitignore`, so the key is never committed. Use a free-tier key from
Google AI Studio. Check that it works with:

```bash
uv run python llm.py
```

It prints `success` or a short reason. It never prints the key.

**No key? The app still runs.** The dashboards, the calendar and every saved lead work without
the AI, because they read from the database. New chats then use **practice mode**: a fixed
script instead of the AI, with a yellow banner saying so.

### Sample data

The first time the app starts it loads `sample_data.json` into the database: invented leads
with different strengths, some who left mid-chat, and invented call results. Their chats,
scores and briefs were produced by the real AI (`seed.py` is the script that made them). The
dashboards label this as sample data. Real chats you run are added on top. The owner's
Settings page can reset everything back to the sample data.

## Architecture

```
            Browser
               |
   app.py                         decides the role (lead, closer, owner) and that role's pages
   app_pages/                     one small file per page
   ui.py                          shared on-screen helpers
               |
      +--------+---------+
      |                  |
  engine.py          metrics.py   funnel, show rate, close rate, upcoming calls (plain Python)
  the 3 AI tasks:
  chat, score, brief
  + quote check, total, band
      |                  |
   llm.py            storage.py
  the ONE AI call     offer.json        what the AI may answer from
  timeout, retries    sunsettr.db       SQLite: leads, link clicks
      |               sample_data.json  invented sample leads
  Google Gemini
  (free tier)

   models.py   the data shapes (Pydantic) used by every file above
   fake_ai.py  scripted stand-in for the AI (practice mode and tests)
   seed.py     the script that made sample_data.json with the real AI
```

In a few sentences:

- **`app.py`** works out who is using the app and gives Streamlit only that role's pages, so a
  lead cannot open the closer's or owner's pages.
- **Screens** (`app_pages/`) only show things and collect clicks. They never talk to the AI directly.
- **`engine.py`** holds the three AI tasks. Each one builds a prompt, asks the AI through `llm.py`,
  then checks the answer with ordinary Python.
- **`llm.py`** is the only file that calls Google. One function, `ask_ai()`, adds a time limit,
  three tries with pauses in between that alternate between two models, and a clear error
  instead of a crash.
- **`metrics.py`** turns the list of leads into the dashboard numbers. No AI, no screen code.
- **`models.py`** describes the data with Pydantic. The AI must answer in JSON that fits these shapes.
- **`storage.py`** reads and writes the offer file and the SQLite database.

## How the AI is used

- **Provider:** Google Gemini on the free tier, through Google's `google-genai` Python SDK. The
  free tier allows only a small number of requests per day for each model (20 a day for
  `gemini-3.6-flash`), so the app uses two light, fast models, `MODEL` and `FALLBACK_MODEL` at the
  top of `llm.py`, and switches between them when one is busy or out of free requests.
- **Structured output:** every AI call asks for JSON matching a Pydantic class (`ChatTurn`,
  `ScoreResult`, `Brief`), and Pydantic validates the reply.
- **The AI decides:** which question to ask next, when the chat is finished, the six scores with
  reasons, and the wording of the brief.
- **The code decides:** the total and the band (simple arithmetic), whether a quote is real
  (it must appear in the lead's own messages, otherwise it is removed and flagged), whether the lead
  said enough to score at all, a hard stop after seven questions, and every number on the dashboards.
- **Guardrails in the prompts:** the first message says it is an AI; prices come only from the
  offer file; anything not in the offer file is "Jordan will cover that on the call"; no questions
  about income, ability to pay, or protected characteristics.
- **When the AI fails:** the app shows an honest error and a **Try again** button. It never
  fills the gap with made-up content. If scoring fails right after a chat, the closer gets a
  "Generate now" button on that lead's file.

## Folder guide

```
app.py               entry point: works out the role and shows that role's pages
app_pages/           start, lead_chat, closer_dashboard, closer_calendar, lead_file,
                     owner_funnel, owner_leads, offer, settings
ui.py                shared on-screen helpers (spinner, error + Try again, score and brief display)
engine.py            prompts, the three AI tasks, quote check, total and band
metrics.py           funnel and dashboard numbers
llm.py               the single AI call (timeout, retries, errors)
models.py            Pydantic data shapes
storage.py           offer file, SQLite database, sample data loading
fake_ai.py           scripted "practice mode" AI
seed.py              made sample_data.json with the real AI
offer.json           the invented offer
sample_data.json     the invented sample leads
tests/               pytest tests
docs/                presentation notes, demo script, code walkthrough, screenshots
```
