# Milestone II check-in — slide outline

Eight slides, about five minutes plus a two-minute demo. The order follows the four points
in the assignment. Text under **Say** is written the way I would say it; shorten freely.

---

## Part 1 — Project summary

### Slide 1 — Title

- **Sunsettr: an AI that gets a salesperson ready for the call**
- Calvin Volkmann · OIM 3641 · Milestone II
- *Screenshot:* `docs/screenshots/3-brief.png` (small, on the right)

**Say:** "My project is a small Python app. A sales lead chats with an AI, the AI scores the
lead, and the salesperson gets a one-page brief before the call."

### Slide 2 — The problem and the idea

- People who sell expensive services by phone (coaches, consultants) take many calls with people
  who were never going to buy
- The salesperson, called the **closer**, walks into most calls knowing nothing about the lead
- Idea: before the call, an AI has a short chat with the lead, then tells the closer
  **who this is, how serious they are, and how to open**
- Everything in the demo is invented: Maya Coaching, Jordan the closer, Sam Rivera the lead

**Say:** "The closer's time is the expensive part. If the AI does the first five minutes of
discovery, the closer can skip the weak calls and start the good ones already knowing the story."

### Slide 3 — What the app does today

Three steps, one line each, with a small screenshot per step:

1. **Chat** — the AI says it is an AI, then picks each question from what the lead already said (`1-chat.png`)
2. **Score** — six dimensions, 0 to 5 each, with a reason and a quote as evidence; total out of 100 (`2-score.png`)
3. **Brief** — three-line summary, key quotes, what is still unknown, a suggested opening line (`3-brief.png`)

**Say:** "The AI does the judgement on all three pages. My code does the checking."

---

## Part 2 — Codebase and architecture

### Slide 4 — Architecture

- *Picture:* the diagram from `README.md` (screens → engine → llm → Gemini; models and storage on the side)
- Python, managed with **uv**
- **Streamlit** for the screens · **Pydantic** for data shapes · **SQLite** for saving · **pytest** for tests
- **Google Gemini** (free tier) for the AI
- About 950 lines of Python in 11 small files, plus tests

**Say:** "The screens never talk to the AI directly. They call the engine, the engine builds a
prompt, and exactly one function in `llm.py` makes the call. That one function has the time
limit and the retries, so every AI feature gets them for free."

### Slide 5 — How I keep the AI honest

- **Structured output:** the AI must answer in JSON that fits a Pydantic class; a wrong shape is rejected
- **Quote check in code:** every evidence quote must appear in the lead's own messages, or it is removed and flagged
- **Arithmetic in code:** the AI gives six small scores; the total and the band are plain Python
- **Offer file:** the AI may only answer from `offer.json` (`4-offer.png`); anything else is "Jordan will cover that on the call"
- **Guardrails:** says it is an AI in the first message; no questions about income or protected characteristics
- **Failure:** time limit, three tries, then an honest error and a Try again button. Never made-up content

**Say:** "The main thing I learned: don't trust the AI's output, check it. The AI writes a quote
as evidence, and my code checks that the lead really said it."

*Optional code snippet for this slide (from `engine.py`):*

```python
def quote_is_real(quote, messages):
    """True only if the quote appears inside one of the lead's own messages."""
    wanted = _simplify(quote)
    if not wanted:
        return False
    return any(wanted in _simplify(m.text) for m in messages if m.role == "lead")
```

---

## Part 3 — Demo of the current UI and functionality

### Slide 6 — Live demo

- One line on the slide: **Chat → Score → Brief**
- Then switch to the browser and follow `docs/demo-script.md` (two minutes)
- Backup: the four screenshots on slide 3 and slide 5, and the Replay button

**Say:** "I'll type two answers as the lead so you can see the AI choose its questions, then
load a saved run to show the score and the brief."

---

## Part 4 — Remaining tasks for the final demonstration

### Slide 7 — What is not built yet

- No sign-in: the lead and the closer share one screen
- No page to browse past leads (they are saved in SQLite, but not shown)
- The brief is only on screen: no email, no calendar
- No outcomes: nothing records whether the lead showed up or bought
- The score is my own design and is **not validated** against real results

**Say:** "The honest gap is the last one. The score looks precise, but until I track outcomes I
can't claim an 80 is really better than a 60."

### Slide 8 — Plan for the final demo

1. **Leads page** — a table of saved runs that reopens any of them
2. **Outcomes page** — mark "showed up" and "closed", then show-rate and close-rate by score band
3. **Two views** — lead sees only the chat; closer sees score, brief and leads
4. **Send or download the brief**
5. A second, weaker example lead to show a low score live
6. Stretch: real sign-in and a calendar connection

**Say:** "Items one and two are the priority, because together they turn this from a demo into
something that can show whether the score works."

---

## Likely questions, with short answers

- **Why Gemini?** Free tier, and its SDK supports structured JSON output. The model name is one constant, so switching is a one-line change.
- **What if the AI makes something up?** Quotes are checked against the chat in code; prices only come from the offer file; malformed answers are rejected by Pydantic.
- **What if the AI is down?** Time limit, three tries with pauses, a lighter fallback model, then an error with Try again. For demos there is a saved Replay.
- **Did you write all the code?** I built it with heavy AI assistance and I am working through it file by file (`docs/code-walkthrough.md`). I can explain what each file does.
- **Is real data used?** No. Every person and business is invented, because free-tier content may be used by Google.
- **How is it tested?** pytest: quote checking, totals and bands, saving and loading, and the AI call with a fake client (retries, fallback, timeout).
