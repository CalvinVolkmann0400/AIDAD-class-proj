# Milestone II check-in — slide outline

Nine slides, about five minutes plus a two-minute demo. The order follows the four points
in the assignment. Text under **Say** is written the way I would say it; shorten freely.
Screenshots are in `docs/screenshots/` (they are tall, so crop them to fit).

---

## Part 1 — Project summary

### Slide 1 — Title

- **Sunsettr: an AI that gets a salesperson ready for the call**
- Calvin Volkmann · OIM 3641 · Milestone II
- *Screenshot:* `4-lead-brief.png` (small, on the right)

**Say:** "My project is a Python app. A sales lead chats with an AI, the AI scores the lead, and
the salesperson gets a one-page brief before the call."

### Slide 2 — The problem and the idea

- People who sell expensive services by phone (coaches, consultants) take many calls with people
  who were never going to buy
- The salesperson, called the **closer**, walks into most calls knowing nothing about the lead
- The **owner** cannot see where leads drop out between the first click and the sale
- Idea: before the call, an AI has a short chat with the lead, then tells the closer
  **who this is, how serious they are, and how to open**
- Everything in the demo is invented: Maya Coaching, Jordan the closer, every lead

**Say:** "The closer's time is the expensive part. If the AI does the first five minutes of
discovery, the closer starts the good calls already knowing the story, and the owner can see
where the funnel leaks."

### Slide 3 — Three people, three views

| | Sees | Screenshot |
|---|---|---|
| **Lead** | Only the chat | `1-lead-chat.png` |
| **Closer** | Dashboard, call calendar, each lead's brief and score | `2-closer-dashboard.png` |
| **Owner** | The funnel, all chat logs, the offer file, settings | `6-owner-funnel.png` |

**Say:** "Three people use it and each one sees something different. The lead only ever gets a
chat link. The AI does the judgement; my code does the checking and the numbers."

---

## Part 2 — Codebase and architecture

### Slide 4 — Architecture

- *Picture:* the diagram from `README.md`
- Python, managed with **uv**
- **Streamlit** for the screens · **Pydantic** for data shapes · **SQLite** for saving · **pytest** for tests
- **Google Gemini** (free tier) for the AI
- About 1,600 lines of Python in small files (comments and prompts included), plus 38 tests

**Say:** "`app.py` works out who you are and only loads that person's pages. The pages never
talk to the AI directly. They call the engine, and exactly one function in `llm.py` makes the
call. That one function has the time limit and the retries, so every AI feature gets them.
The dashboard numbers come from a separate file of plain Python with no AI in it."

### Slide 5 — How I keep the AI honest

- **Structured output:** the AI must answer in JSON that fits a Pydantic class; a wrong shape is rejected
- **Quote check in code:** every evidence quote must appear in the lead's own messages, or it is removed and flagged (`5-lead-score.png`)
- **Arithmetic in code:** the AI gives six small scores; the total, the band and the whole funnel are plain Python
- **Offer file:** the AI may only answer from `offer.json` (`8-offer-file.png`); anything else is "Jordan will cover that on the call"
- **Guardrails:** says it is an AI in the first message; no questions about income or protected characteristics
- **Failure:** time limit, three tries across two models, then an honest error and a Try again button. Never made-up content

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

### Slide 6 — Two things that broke, and what I changed

- **The free AI tier allows 20 requests a day on the better model.** A single lead chat uses about
  seven. I switched to two lighter models that answer in about a second and take turns when one is busy.
- **The AI sometimes renamed a score** ("decision_authority" for "decision authority"), and my code
  silently gave that dimension a zero. Now names are matched loosely, and there is a test for it.

**Say:** "Both of these only showed up when I ran real conversations, not in my tests. That's why
there is now a test for the second one."

---

## Part 3 — Demo of the current UI and functionality

### Slide 7 — Live demo

- One line on the slide: **Lead chat → Closer dashboard → Owner funnel**
- Then switch to the browser and follow `docs/demo-script.md` (two minutes)
- Backup: the screenshots on slides 3 and 5

**Say:** "I'll type two answers as a lead so you can see the AI choose its questions, then show
what the closer and the owner see."

---

## Part 4 — Remaining tasks for the final demonstration

### Slide 8 — What is not built yet

- **No real sign-in:** anyone can pick the closer or owner view on the start screen
- **The numbers are mostly sample data:** call results and most clicks are invented so the dashboards are not empty
- **The score is not validated** against real results
- No real calendar, the brief is not emailed, and it only runs on my laptop

**Say:** "The honest gap is the middle one. The funnel and the score-band table are the right
screens, but they're showing sample data. Until real people go through it, I can't claim an
80 is better than a 60."

### Slide 9 — Plan for the final demo

1. **Host it** so a classmate can open the lead link on their phone while I watch the closer dashboard
2. **Real sign-in** for the closer and the owner
3. **Send the brief** by email before the call
4. **Funnel by week**, so a leak that is getting worse is visible
5. **Collect real results** from classmates playing leads, and check the score against them

**Say:** "Items one and five are the priority, because together they turn sample numbers into
real ones."

---

## Likely questions, with short answers

- **Why Gemini?** Free tier, and its SDK supports structured JSON output. The model names are two constants at the top of `llm.py`.
- **What if the AI makes something up?** Quotes are checked against the chat in code; prices only come from the offer file; malformed answers are rejected by Pydantic.
- **What if the AI is down?** Time limit, three tries across two models, then an error with Try again. The dashboards and saved leads never need the AI.
- **Is the dashboard data real?** No, and the screen says so. The sample leads' chats, scores and briefs came from the real AI; their call results and most clicks are invented.
- **How do you stop a lead from seeing the closer's pages?** The lead's link only loads the chat page; the other pages are not in that session's page list. But there is no password on the closer and owner views yet. That is first on my list.
- **Did you write all the code?** I built it with heavy AI assistance and I am working through it file by file (`docs/code-walkthrough.md`). I can explain what each file does.
- **Is real personal data used?** No. Every person and business is invented, because free-tier content may be used by Google.
- **How is it tested?** pytest, 38 tests: quote checking, totals and bands, the funnel numbers, saving and loading, and the AI call with a fake client (retries, fallback model, timeout).
