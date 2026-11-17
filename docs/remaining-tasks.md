# Remaining tasks for the final demonstration

An honest list. "Built" means it works today in this repo.

## Built now (Milestone II)

- **Three separate views:** the lead sees only the chat; the closer and the owner each get their own pages
- **Lead chat** where the AI chooses each question, answers only from the offer file, and then lets the lead pick their own call time
- **AI scoring** on six dimensions with reasons and quotes, returned as validated JSON, produced automatically when a chat ends
- **Code checks:** quote verification, total out of 100, bands, "not enough information"
- **Closer dashboard:** numbers at a glance, upcoming calls with links to brief, score and chat log, and a "needs attention" list
- **Call calendar:** upcoming calls by day, call history, and recording the result of each call
- **Owner funnel:** link clicks → chat started → chat finished → call booked → showed up → closed, with the biggest leak marked, plus results by score band
- **Leads and chat logs, offer file, settings** for the owner
- One AI call with a time limit, retries, a fallback model and a Try again button
- Leads, link clicks and call results saved to SQLite; sample data so the dashboards are never empty
- A **Demo view** switch on every page, so one person can present all three roles
- The Sunsettr look: cream and ink, DM Sans, square corners, the rounded chat card
- Automated tests (pytest)

## Not built yet

| Gap | Why it matters | Size |
|---|---|---|
| **No real sign-in.** The start screen lets anyone pick the closer or owner view; there are no passwords. | In a real product only Jordan and the owner could reach those pages. | Medium |
| **The numbers are mostly sample data.** Call results (showed up, closed) and most link clicks are invented so the dashboards have something to show. | The funnel proves the screens work, not that the product works. | Needs real use |
| **The score is not validated.** The six dimensions and the bands are my own design. | "Results by score band" is the right check, but with a handful of invented results it proves nothing yet. | Ongoing |
| **No real calendar.** Leads pick from slots in my own database (four per weekday); nothing connects to Google Calendar or Calendly, and there are no time zones. | A real closer already has a calendar. | Medium |
| **The brief is not sent anywhere.** It only appears in the app. | Closers live in email and on their phone. | Small to medium |
| **One closer, one offer.** | A real business may have several of each. | Medium |
| **Runs only on my laptop.** The lead link starts with `localhost`. | A real lead could not open it; it needs hosting. | Medium |
| **Click counting is simple.** Every opening of the link counts, including the same person twice. | Inflates the top of the funnel. | Small |
| **Only tested with invented leads.** | Rude, confused or very short leads may get odd questions. | Small |
| **Evidence quotes are long.** The AI tends to copy the lead's whole message as its quote. | Shorter quotes would be easier to scan. | Small |
| **Free-tier AI.** It can be slow or busy, and Google may use free-tier content, so only invented data is allowed. | Fine for class; real leads would need a paid tier and a privacy review. | Out of scope for class |

## Plan for the final demonstration (in priority order)

1. **Host it** on a free service so a classmate can open the lead link on their phone during the demo while I watch the closer dashboard update.
2. **Real sign-in** for the closer and the owner (Streamlit has built-in login), so the start screen goes away.
3. **Send the brief** to the closer by email shortly before the call, or at least a "Download brief" button.
4. **Trends over time** on the owner's page: the funnel by week, so a leak that is getting worse is visible.
5. **Collect real results.** Have classmates play leads, record real show and close results, and see whether higher scores really do better.
6. **Stretch:** connect a real calendar; more than one closer and offer.

## Risks I am watching

- The free AI tier answering slowly during a demo. Mitigation: the dashboards and saved leads never need the AI.
- Scope creep: sign-in and calendar integrations are the easiest places to lose a week. Items 1 and 5 give the most value for the least code.
