# Code walkthrough (for learning the code after the build)

Read the files in this order. Each section says what the file is for, the few ideas worth
understanding, and one thing to try.

A 30-second map first:

- **`app.py`** decides who you are (lead, closer, owner) and loads only that person's pages.
- A page calls **`engine.py`** when it needs the AI (chat, score, brief), and **`metrics.py`** when it
  needs numbers (funnel, rates, upcoming calls).
- `engine.py` builds a prompt and calls **`ask_ai()` in `llm.py`**, the only place that talks to Google.
- **`models.py`** describes the data and **`storage.py`** saves it in a SQLite database.

---

## 1. `models.py` — the shapes of the data

**What it is.** A list of small classes: `Offer`, `Message`, `ChatTurn`, `DimensionScore`,
`ScoreResult`, `Brief`, `Lead`. Each class says "this kind of data has these fields, of these types".

**Ideas to understand.**

- `class Offer(BaseModel)` — `BaseModel` comes from **Pydantic**. Giving a class fields like
  `price: str` means Pydantic will refuse data where `price` is missing or is not text.
- `Field(ge=0, le=5)` on `score` means "greater or equal 0, less or equal 5". If the AI ever
  returned a score of 9, Pydantic would reject it.
- The `description=` texts are sent to the AI as part of the JSON schema, so they double as instructions.
- `Lead` is the main record: the lead's name, their personal link code (`token`), the chat
  messages, whether the chat is finished, the score, the brief, the call time, and the call
  `outcome` (`pending`, `closed`, `not_closed` or `no_show`). `Literal[...]` means "only these exact words are allowed".
- `quote_verified` and `is_sample` are set by our own code, never by the AI.

**Try it.** In a terminal: `uv run python`, then
`from models import DimensionScore` and `DimensionScore(name="pain", score=9, reason="x", quote="")`.
Read the error. That error is the safety net.

---

## 2. `offer.json` and `storage.py` — files and the database

**What it is.** `offer.json` is the invented offer. `storage.py` reads and writes the offer file
and the SQLite database (`sunsettr.db`).

**Ideas to understand.**

- **SQLite** is a database in a single file, built into Python (`import sqlite3`). There are three tables:
  `leads` (one row per lead), `clicks` (one row each time the lead link is opened) and `notes`
  (small remembered facts).
- `save_lead(lead)` — a lead with no `id` is added as a new row (`INSERT`); a lead that already has
  an `id` has its row changed (`UPDATE`). The messages, score and brief are stored as JSON text.
- The `?` marks in the SQL are placeholders. Values are passed separately, which is the safe way
  to put data into SQL.
- `list_leads()`, `get_lead()`, `get_lead_by_token()` read leads back as `Lead` objects.
- `add_click()` and `count_clicks()` feed the top of the owner's funnel.
- `next_free_slot()` finds the first call time (four slots a day, starting tomorrow) nobody has yet.
- `ensure_sample_data()` loads `sample_data.json` once a day. The file stores each call as "so many
  days from today", so the dashboards always have some upcoming calls and some past ones.
- `sunsettr.db` is git-ignored: it is created the first time the app runs.

**Try it.** `uv run python -c "import storage; print(len(storage.list_leads()), storage.count_clicks())"`.

---

## 3. `llm.py` — the single AI call

**What it is.** The only file that talks to Google. Everything else calls `ask_ai()`.

**Ideas to understand.**

- The settings at the top (`MODEL`, `FALLBACK_MODEL`, `TIMEOUT_SECONDS`, `MAX_ATTEMPTS`) are
  constants: change the model in one place. The comment there explains why two light models are
  used: the free tier allows only a small number of requests per day per model.
- `load_dotenv()` reads the `.env` file and puts `GEMINI_API_KEY` where the program can find it
  (`os.environ`). The key never appears in the code.
- `GeminiClient.generate()` is the actual request. `response_mime_type="application/json"` plus
  `response_json_schema=schema` is **structured output**: we hand Google the JSON schema of a
  Pydantic class and it answers in that shape.
- `ask_ai()` is a loop of up to three tries:
  1. call the AI (with a time limit); tries go main model, fallback model, main model,
  2. check the answer with Pydantic (`model_validate_json`),
  3. if the service was busy, out of free requests, or the answer was malformed, wait and try again,
  4. if the request itself is wrong (for example a bad key), stop at once,
  5. if all tries fail, raise `AIError` with a message that is safe to show on screen.
- `_call_with_time_limit()` runs the request in a background thread so a request that hangs
  cannot freeze the app.
- `client=None` in `ask_ai(...)`: tests pass in a fake client here. This is why the tests can
  check the retry logic without the internet.

**Try it.** `uv run python llm.py` prints whether your key works.

---

## 4. `engine.py` — prompts, the three AI tasks, and the checks

**What it is.** The "brain" of the app, in three parts.

**Ideas to understand.**

- `opening_message()` is written in code, not by the AI, so the "I'm an AI assistant" disclosure
  can never be skipped.
- `next_chat_turn()` builds a **system prompt** (the AI's role, rules, and the offer) and sends the
  conversation so far. The AI answers with a `ChatTurn`: its `reply` and whether it is `done`.
  The line `if must_finish: turn.done = True` is the code enforcing the seven-question limit even
  if the AI ignores it.
- `GUARDRAILS` is a block of rules added to every prompt (no income questions, no protected
  characteristics, no invented facts).
- `score_conversation()` asks for a `ScoreResult`, then runs three plain-code checks:
  `tidy_dimensions()` (six dimensions, fixed order, names matched loosely because the AI sometimes
  writes `decision_authority`), `check_quotes()` (remove quotes the lead never said), and
  `lead_said_enough()` (fewer than 25 words from the lead means "not enough information").
- `quote_is_real()` is the heart of the honesty check: simplify both texts (lower-case, tidy
  spaces and quote marks) and test whether the quote is **inside** one of the lead's messages.
- `total_score()` is arithmetic: points out of 30, shown out of 100. `band()` turns the total into a label.
- `write_brief()` asks for a `Brief` and applies the same quote check to its key quotes.

**Try it.** Change `MIN_QUESTIONS` and `MAX_QUESTIONS` to 3 and 4 and chat again.

---

## 5. `metrics.py` — the dashboard numbers

**What it is.** Plain functions that take the list of leads and return numbers. No AI, no screen code.

**Ideas to understand.**

- `funnel(leads, clicks)` returns five `Stage` objects: clicked the link, started the chat,
  finished the chat, showed up, closed. Each stage knows its `count` and what it is `out_of`,
  and `rate` is one divided by the other.
- "Showed up" is measured out of calls **that have a recorded result**, not all booked calls,
  because calls that have not happened yet cannot be a no-show.
- `biggest_leak()` is the stage with the lowest rate.
- `show_rate()`, `close_rate()` and `rates_by_band()` are a few lines each. `rates_by_band()` is
  the check on whether the AI's score means anything.
- `upcoming_calls()`, `past_calls()` and `needs_attention()` decide what the closer sees.
- `@dataclass` on `Stage` is a short way to make a class that just holds a few values.

**Try it.** Read `tests/test_metrics.py` next to this file. Each test is a tiny worked example.

---

## 6. `fake_ai.py` — the practice AI

**What it is.** A class with the same `generate()` method as `GeminiClient`, but it returns fixed
answers. Used when there is no key, and by the tests.

**Idea to understand.** Because `ask_ai()` only needs "something with a `generate()` method", the
real AI and the fake one are interchangeable. Programmers call this *dependency injection*; it is
just "pass in the thing you depend on, so you can swap it".

---

## 7. `app.py` — the entry point and the three roles

**What it is.** The file Streamlit runs. It decides the role and shows that role's pages.

**Ideas to understand.**

- **Streamlit reruns the whole script from top to bottom on every click.** Ordinary variables are
  forgotten between reruns. `st.session_state` is the memory that survives, one per browser tab.
- The role is worked out once per tab: a link with `?lead=...` means the lead; otherwise the start
  screen lets you choose closer or owner. It is kept in `st.session_state.role`.
- `PAGES` is a dictionary: for each role, the list of pages that role may open.
  `st.navigation(PAGES[role], ...)` registers only those pages, so a lead's session simply does
  not contain the closer's or owner's pages.
- The lead and the start screen get `position="hidden"` (no menu at all); the closer and the
  owner get a sidebar with a **Switch role** button.
- This is role separation, not security: there are no passwords yet. That is the first item in
  `docs/remaining-tasks.md`.

---

## 8. `ui.py` — shared on-screen helpers

- `run_ai_step(label, work, retry_flag)` is the demo-safety wrapper: it shows the spinner
  ("AI is thinking"), runs the AI task, and if `AIError` is raised it shows the error and a
  **Try again** button instead of crashing.
- `ask_for_retry()` sets a flag in `st.session_state`; on the next rerun the page sees the flag
  and runs the AI step again.
- `generate_missing()` asks the AI for a lead's score and brief if they are not there yet, and saves them.
- `set_role()` and `open_lead()` move between roles and pages.
- `plain()` escapes dollar signs, because Streamlit would otherwise read `$3,000 … $1,100` as a
  maths formula. `percent()` and `nice_time()` format numbers and dates.
- `show_chat()`, `show_score_cards()`, `show_score_compact()` and `show_brief()` draw a lead's
  chat, score and brief the same way wherever they appear.

---

## 9. `app_pages/` — one file per page

All of them follow the same pattern: read what is needed from the database, decide what to show, draw it.

| File | Who | What it does |
|---|---|---|
| `start.py` | everyone | Three cards for choosing a role |
| `lead_chat.py` | lead | Counts the link click, asks the name, runs the chat, books the call, then quietly asks the AI for the score and brief |
| `closer_dashboard.py` | closer | Five numbers, upcoming calls with Brief / Score / Chat log buttons, and "needs attention" |
| `closer_calendar.py` | closer | Upcoming calls by day with result buttons, and the history table |
| `lead_file.py` | closer, owner | One lead: call result, brief, score cards, chat log, and "Generate now" if the AI has not scored it |
| `owner_funnel.py` | owner | Headline numbers, one row per funnel level, the biggest leak, results by score band |
| `owner_leads.py` | owner | Every lead in a table; pick a row to open the lead file |
| `offer.py` | owner | A form whose Save button writes `offer.json`, with the raw file beside it |
| `settings.py` | owner | The lead chat link, the AI connection test, and resetting to the sample data |

Things worth noticing:

- In `lead_chat.py`, `st.query_params["lead"] = lead.token` puts the lead's personal code in the
  address bar, so refreshing the page keeps the same chat.
- In `closer_calendar.py`, `on_click=record, args=(lead, "closed")` means "when this button is
  clicked, call `record(lead, "closed")`".
- `st.stop()` ends a page early (for example when there are no leads yet).

---

## 10. `seed.py` and `sample_data.json` — the sample leads

`seed.py` is a one-off script, not part of the running app. It plays scripted invented leads
against the real AI (the lead's answers are scripted, the AI's questions, scores and briefs are
real) and writes `sample_data.json`. Call results and click counts in that file are invented.
You do not need to run it again.

---

## 11. `tests/` — proof that the checks work

Run `uv run pytest`. Each function starting with `test_` is one check.

- `test_engine.py` — real quotes pass, invented quotes are removed, totals and bands are right,
  odd dimension names still match, the chat is forced to end at the limit.
- `test_metrics.py` — the funnel counts, the biggest leak, show and close rates, upcoming and past calls.
- `test_llm.py` — busy errors are retried, the second try uses the fallback model, a bad key is not
  retried, a hanging call times out.
- `test_storage.py` — whatever is saved comes back the same ("round trip"), clicks are counted,
  sample data loads with dates around today. Uses a temporary folder so the real database is never touched.

**A good first exercise:** add a test to `test_metrics.py` with two leads who both closed, and
check that `close_rate` is 1.

---

## Words you will be asked about

| Word | Plain meaning |
|---|---|
| **Prompt** | The text we send to the AI: its instructions plus the material to work on |
| **System prompt** | The part of the prompt that sets the AI's role and rules |
| **Structured output** | Asking the AI to answer in JSON with fixed fields instead of free text |
| **Pydantic model** | A Python class that checks data has the right fields and types |
| **JSON schema** | A description of what a piece of JSON must look like; Pydantic generates it |
| **Session state** | Streamlit's memory between clicks, one per browser tab |
| **Retry with backoff** | Try again after a pause, with a longer pause each time |
| **Fallback model** | A second AI model used when the first is busy or out of free requests |
| **Guardrail** | A rule that limits what the AI may ask or say |
| **Fake / mock client** | A stand-in for the real AI, used for tests and practice |
| **Funnel** | The steps a lead passes through, with fewer people at each step |
| **Show rate / close rate** | Of calls held, how many leads showed up / of those, how many bought |
