# Remaining tasks for the final demonstration

An honest list. "Built" means it works today in this repo.

## Built now (Milestone II)

- Lead chat where the AI chooses each question and answers only from the offer file
- AI scoring on six dimensions with reasons and quotes, returned as validated JSON
- Code checks: quote verification, total out of 100, bands, "not enough information"
- Closer's brief with the score beside it
- Offer file page (view and edit `offer.json`)
- One AI call with a time limit, retries, a fallback model and a Try again button
- Replay of a saved real-AI run, and a labelled practice mode with no key
- Conversations, scores and briefs saved to SQLite
- Automated tests (pytest)

## Not built yet

| Gap | Why it matters | Size |
|---|---|---|
| **No sign-in.** Anyone who opens the app sees everything, and the lead and the closer share one screen. | A real lead should only see the chat; only the closer should see scores and briefs. | Medium |
| **No list of past leads.** Runs are saved to SQLite but there is no page to browse or reopen them. | The closer needs to pick a lead before a call. | Small |
| **One lead, one offer.** The lead's name is fixed in the code and there is a single `offer.json`. | A real closer has many leads and maybe several offers. | Small |
| **No calendar connection.** The app does not know when the call is. | The brief should arrive shortly before the call. | Medium |
| **The brief is not sent anywhere.** It only appears on screen. | Closers live in email, not in a dashboard. | Small to medium |
| **No outcomes tracking.** Nothing records whether the lead showed up or bought. | Without outcomes we cannot tell if a high score really means a good lead. | Medium |
| **The score is not validated.** The six dimensions and the bands are my own design. | The numbers look precise but have not been checked against real results. | Ongoing |
| **Refreshing the browser starts a new chat.** The current conversation lives in the browser tab's memory. | Easy to lose a chat by accident. | Small |
| **Only tested with one invented lead.** | Rude, confused or very short leads may get odd questions. | Small |
| **Free-tier AI.** It can be slow or busy, and Google may use free-tier content, so only invented data is allowed. | Fine for class; real leads would need a paid tier and a privacy review. | Out of scope for class |

## Plan for the final demonstration (in priority order)

1. **Leads page.** A table of saved runs from SQLite (name, date, score, band) that reopens any run. Small, and it makes the database visible in the demo.
2. **Outcomes page.** Buttons on each run for "showed up" and "closed", then show-rate and close-rate by score band in a chart. This is the part that proves whether the score is useful.
3. **Two views.** A simple role switch (lead view shows only the chat; closer view shows score, brief, leads). A stand-in for real sign-in.
4. **Send the brief by email**, or at least a "Download brief" button (text or PDF).
5. **Second example lead** with weak answers, to show a low score and the "not enough information" case live.
6. **Stretch:** real sign-in, a calendar connection so the brief is timed to the call, more than one offer.

## Risks I am watching

- The free AI tier answering slowly during the final demo (mitigation: Replay, already built).
- Scope creep: sign-in and calendar are the easiest places to lose a week. Items 1, 2 and 5 give the most demo value for the least code.
