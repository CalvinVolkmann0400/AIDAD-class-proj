# Sunsettr (class version) — OIM 3641 project

A small Python app that shows one idea: **a sales lead chats with an AI, the AI scores the
lead, and the salesperson (the "closer") gets a one-page brief before the call.**

It is the class-sized version of a startup idea. Everything in it is invented: the business
("Maya Coaching"), the closer ("Jordan") and the lead ("Sam Rivera").

## What it does

| Page | What happens | Who does the work |
|---|---|---|
| **Lead chat** | The lead is told up front they are talking to an AI. The AI asks 5 to 7 questions, choosing each one from what the lead already said, and answers the lead's questions only from the offer file. | AI |
| **Score** | The AI scores the chat on six dimensions (0 to 5 each) with a reason and a quote. The code checks every quote really appears in the lead's messages, then shows a total out of 100 and a band. | AI + code checks |
| **Closer's brief** | The AI writes a three-line summary, key quotes, what is still unknown, and a suggested opening line. The score is shown beside it. | AI |
| **Offer file** | Shows and edits `offer.json`, the only source the AI may answer from. | You |

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

**No key? The app still runs.**

- **Replay saved run** (sidebar button, or open `http://localhost:8501/?replay=1`) loads a
  conversation, score and brief that the real AI produced earlier. It is labelled on screen as a saved run.
- **Practice mode** uses a fixed script instead of the AI, and says so in a yellow banner on every page.

## Architecture

```
            Browser
               |
   app.py  +  app_pages/          the screens (Streamlit)
   chat | score | brief | offer   ui.py = shared on-screen helpers
               |
           engine.py              the 3 AI tasks: prompts + checks in plain code
           /        \             (quote check, total out of 100, band)
      llm.py        storage.py
   the ONE AI call   offer.json   what the AI may answer from
   timeout, retries  sunsettr.db  SQLite: conversations, scores, briefs
        |            replay/saved_run.json   saved real-AI run for the demo
   Google Gemini
   (free tier)

   models.py   the data shapes (Pydantic) used by every file above
   fake_ai.py  scripted stand-in for the AI (practice mode and tests)
```

In a few sentences:

- **Screens** (`app.py`, `app_pages/`) only show things and collect clicks. They never talk to the AI directly.
- **`engine.py`** holds the three AI tasks. Each one builds a prompt, asks the AI through `llm.py`,
  then checks the answer with ordinary Python.
- **`llm.py`** is the only file that calls Google. One function, `ask_ai()`, adds a time limit,
  three tries with pauses in between, a lighter fallback model on the last try, and a clear error
  instead of a crash.
- **`models.py`** describes the data with Pydantic. The AI must answer in JSON that fits these shapes,
  so a badly formed answer is caught straight away.
- **`storage.py`** reads and writes the offer file, the SQLite database and the replay file.

## How the AI is used

- **Provider:** Google Gemini on the free tier, through Google's `google-genai` Python SDK
  (model name is one constant, `MODEL`, at the top of `llm.py`).
- **Structured output:** every AI call asks for JSON matching a Pydantic class (`ChatTurn`,
  `ScoreResult`, `Brief`), and Pydantic validates the reply.
- **The AI decides:** which question to ask next, when the chat is finished, the six scores with
  reasons, and the wording of the brief.
- **The code decides:** the total and the band (simple arithmetic), whether a quote is real
  (it must appear in the lead's own messages, otherwise it is removed and flagged), whether the lead
  said enough to score at all, and a hard stop after seven questions.
- **Guardrails in the prompts:** the first message says it is an AI; prices come only from the
  offer file; anything not in the offer file is "Jordan will cover that on the call"; no questions
  about income, ability to pay, or protected characteristics.
- **When the AI fails:** the app shows an honest error and a **Try again** button. It never
  fills the gap with made-up content.

## Folder guide

```
app.py               entry point: sidebar, page menu, shared state
app_pages/           one file per page (chat, score, brief, offer)
ui.py                shared on-screen helpers (spinner, error + Try again, score display)
engine.py            prompts, the three AI tasks, quote check, total and band
llm.py               the single AI call (timeout, retries, errors)
models.py            Pydantic data shapes
storage.py           offer file, SQLite database, replay file
fake_ai.py           scripted "practice mode" AI
offer.json           the invented offer
replay/              the saved real-AI run used by Replay
tests/               pytest tests
docs/                presentation notes, demo script, code walkthrough, screenshots
```
