# Code walkthrough (for learning the code after the build)

Read the files in this order. Each section says what the file is for, the few ideas worth
understanding, and one thing to try.

A 30-second map first: **screens → engine → llm → Google**, with **models** describing the
data and **storage** saving it. A click on a screen calls a function in `engine.py`; that function
builds a prompt and calls `ask_ai()` in `llm.py`; the answer comes back as a checked Python object
and the screen shows it.

---

## 1. `models.py` — the shapes of the data

**What it is.** A list of small classes: `Offer`, `Message`, `ChatTurn`, `DimensionScore`,
`ScoreResult`, `Brief`, `SavedRun`. Each class says "this kind of data has these fields, of these types".

**Ideas to understand.**

- `class Offer(BaseModel)` — `BaseModel` comes from **Pydantic**. Giving a class fields like
  `price: str` means Pydantic will refuse data where `price` is missing or is not text.
- `Field(ge=0, le=5)` on `score` means "greater or equal 0, less or equal 5". If the AI ever
  returned a score of 9, Pydantic would reject it.
- The `description=` texts are sent to the AI as part of the JSON schema, so they double as
  instructions.
- `quote_verified` is set by our own code, not by the AI.

**Try it.** In a terminal: `uv run python`, then
`from models import DimensionScore` and `DimensionScore(name="pain", score=9, reason="x", quote="")`.
Read the error. That error is the safety net.

---

## 2. `offer.json` and `storage.py` — files and the database

**What it is.** `offer.json` is the invented offer. `storage.py` has the functions that read and
write three things: the offer file, the SQLite database (`sunsettr.db`), and the replay file.

**Ideas to understand.**

- `Offer.model_validate_json(text)` turns JSON text into a checked `Offer` object;
  `offer.model_dump_json()` goes the other way.
- **SQLite** is a database in a single file, built into Python (`import sqlite3`). The table is
  called `runs`; each row is one conversation. Messages, score and brief are stored as JSON text in columns.
- `save_run(run, run_id)` — with no `run_id` it adds a new row (`INSERT`); with one it changes that
  row (`UPDATE`). That is how the same conversation gets its score added later.
- The `?` marks in the SQL are placeholders. Values are passed separately, which is the safe way
  to put data into SQL.
- `sunsettr.db` is git-ignored: it is created the first time the app saves something.

**Try it.** After a chat in the app, run
`uv run python -c "import storage; print(storage.count_runs())"`.

---

## 3. `llm.py` — the single AI call

**What it is.** The only file that talks to Google. Everything else calls `ask_ai()`.

**Ideas to understand.**

- The settings at the top (`MODEL`, `FALLBACK_MODEL`, `TIMEOUT_SECONDS`, `MAX_ATTEMPTS`) are
  constants: change the model in one place.
- `load_dotenv()` reads the `.env` file and puts `GEMINI_API_KEY` where the program can find it
  (`os.environ`). The key never appears in the code.
- `GeminiClient.generate()` is the actual request. `response_format={... "schema": schema}` is
  **structured output**: we hand Google the JSON schema of a Pydantic class and it answers in that shape.
- `ask_ai()` is a loop of up to three tries:
  1. call the AI (with a time limit),
  2. check the answer with Pydantic (`model_validate_json`),
  3. if the service was busy or the answer was malformed, wait and try again; the last try uses the lighter fallback model,
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
  `tidy_dimensions()` (six dimensions, fixed order), `check_quotes()` (remove quotes the lead never
  said), and `lead_said_enough()` (fewer than 25 words from the lead means "not enough information").
- `quote_is_real()` is the heart of the honesty check: simplify both texts (lower-case, tidy
  spaces and quote marks) and test whether the quote is **inside** one of the lead's messages.
- `total_score()` is arithmetic: points out of 30, shown out of 100. `band()` turns the total
  into a label.
- `write_brief()` asks for a `Brief` and applies the same quote check to its key quotes.

**Try it.** Change `MIN_QUESTIONS` and `MAX_QUESTIONS` to 3 and 4 and chat again.

---

## 5. `fake_ai.py` — the practice AI

**What it is.** A class with the same `generate()` method as `GeminiClient`, but it returns fixed
answers. Used when there is no key, and by the tests.

**Idea to understand.** Because `ask_ai()` only needs "something with a `generate()` method", the
real AI and the fake one are interchangeable. Programmers call this *dependency injection*; it is
just "pass in the thing you depend on, so you can swap it".

---

## 6. `app.py` — the entry point

**What it is.** The file Streamlit runs. It sets up shared state, the sidebar and the page menu.

**Ideas to understand.**

- **Streamlit reruns the whole script from top to bottom on every click.** Ordinary variables are
  forgotten between reruns. `st.session_state` is the memory that survives.
- `st.session_state.run` holds the current `SavedRun` (messages, score, brief).
  `chat_done` and `is_replay` are simple True/False flags.
- `start_new_conversation()` and `load_replay()` replace that state; the sidebar buttons call
  them through `on_click=`.
- `st.navigation([...])` defines the four pages; `page.run()` at the bottom runs the chosen one.
- `st.query_params.get("replay") == "1"` makes the link `…/?replay=1` open the saved run directly.

---

## 7. `ui.py` — shared on-screen helpers

- `run_ai_step(label, work, retry_flag)` is the demo-safety wrapper: it shows the spinner
  ("AI is thinking"), runs the AI task, and if `AIError` is raised it shows the error and a
  **Try again** button instead of crashing.
- `ask_for_retry()` sets a flag in `st.session_state`; on the next rerun the page sees the flag
  and runs the AI step again. (`st.session_state.pop("retry_chat", False)` reads the flag and
  clears it in one move.)
- `plain()` escapes dollar signs, because Streamlit would otherwise read `$3,000 … $1,100` as a
  maths formula.
- `show_score_header()` and `show_score_compact()` draw the score, so the Score page and the
  Brief page look the same.

---

## 8. `app_pages/` — one file per page

All four follow the same pattern: read the state, decide what stage we are in, draw it.

- **`chat.py`** — `st.chat_input` returns the text the lead typed (or nothing). The lead's message
  is added to `run.messages`, all messages are drawn with `st.chat_message`, then the AI is asked
  for its reply and `st.rerun()` redraws the page with it.
- **`score.py`** — three stages: chat not finished → a hint; no score yet → the button; score
  ready → the big number, the band and six cards. `st.stop()` ends the page early in the first two stages.
- **`brief.py`** — same three stages, then two columns: the brief on the left, the score on the right.
- **`offer.py`** — a form whose Save button writes `offer.json`, and the raw file beside it.

---

## 9. `tests/` — proof that the checks work

Run `uv run pytest`. Each function starting with `test_` is one check.

- `test_engine.py` — real quotes pass, invented quotes are removed, totals and bands are right,
  the chat is forced to end at the limit.
- `test_llm.py` — busy errors are retried, the last try uses the fallback model, a bad key is not
  retried, a hanging call times out.
- `test_storage.py` — whatever is saved comes back the same ("round trip"), using a temporary
  folder so the real database is never touched.

**A good first exercise:** add a test to `test_engine.py` that checks a score of four on every
dimension gives a total of 80 and the band "Strong lead (80+)".

---

## Words you will be asked about

| Word | Plain meaning |
|---|---|
| **Prompt** | The text we send to the AI: its instructions plus the material to work on |
| **System prompt** | The part of the prompt that sets the AI's role and rules |
| **Structured output** | Asking the AI to answer in JSON with fixed fields instead of free text |
| **Pydantic model** | A Python class that checks data has the right fields and types |
| **JSON schema** | A description of what a piece of JSON must look like; Pydantic generates it |
| **Session state** | Streamlit's memory between clicks |
| **Retry with backoff** | Try again after a pause, with a longer pause each time |
| **Guardrail** | A rule that limits what the AI may ask or say |
| **Fake / mock client** | A stand-in for the real AI, used for tests and practice |
