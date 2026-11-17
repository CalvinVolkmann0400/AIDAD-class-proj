# Two-minute live demo script

The path: **type two answers live → Replay → Score → Brief → Offer file.**
Typing two answers shows the AI really choosing its questions. Replay then shows a finished
run without waiting, so the demo cannot stall.

## Before class (five minutes)

1. Open a terminal in the project folder and start the app:

   ```bash
   uv run streamlit run app.py
   ```

2. The browser opens at `http://localhost:8501`. Check the sidebar badge:
   - green **Live AI** = the key works and the AI is live
   - orange **Practice mode** = no key found (Replay still works; skip the live typing)
3. Click **Test the AI connection** in the sidebar. "success" means the live part is safe to try.
4. Click **Replay saved run** once to confirm it loads, then **New conversation** to reset.
5. Make the browser text bigger (Ctrl and +) so the back row can read it.
6. Leave the app on the **Lead chat** page with a fresh conversation.

Do not refresh the browser (F5) during the demo. A refresh starts a new conversation.

## The demo

### Step 1 — the chat, live (about 45 seconds)

**Say:** "This is what the lead sees. Notice the first message says it's an AI, not a person."

Type this as the lead and press Enter:

> I lost two big clients this spring and my income has been up and down ever since.

Wait for the reply (the spinner says "AI is thinking"). In testing a reply usually took 5 to 10
seconds, and once about 25 seconds. Keep talking while it thinks.

**Say:** "I didn't script that question. The AI chose it from what I just said."

Type the second answer, which includes a question back to the AI:

> I tried an online course last year but never finished it. How much does your program cost?

**Say:** "Now I asked it a question. It may only answer from the offer file, so the price it
gives is the one in the file, and then it carries on with its own questions."

### Step 2 — switch to the saved run (about 10 seconds)

Click **Replay saved run** in the sidebar.

**Say:** "To save time I'll load a full conversation the same AI produced earlier. The blue
banner says it's a saved run." Scroll the chat once so they see it is a whole conversation.
Point at the refund question: the offer file says nothing about refunds, so the AI answered
"Jordan will cover refund policies directly with you on the call" instead of inventing a policy.

### Step 3 — the score (about 30 seconds)

Click **Score** in the sidebar.

**Say:** "The AI scores six things from zero to five and has to give a reason and a quote for
each. My code then checks every quote really appears in what the lead typed. That's the green
tick. The total out of 100 and the band are plain Python, not the AI."

Point at one card: the score, the reason, the quote.

### Step 4 — the closer's brief (about 25 seconds)

Click **Closer's brief** in the sidebar.

**Say:** "This is what Jordan, the closer, reads one minute before the call: three lines of
summary, the lead's own words, what's still unknown, and a suggested opening line. The score
sits beside it."

### Step 5 — the offer file (about 10 seconds, skip if short on time)

Click **Offer file**.

**Say:** "And this is the only thing the AI is allowed to answer from. Change the price here
and the AI's answer changes."

## If something goes wrong

| What you see | What to do | What to say |
|---|---|---|
| The spinner runs longer than about 15 seconds | Click **Replay saved run** straight away | "The free AI tier is busy, so here is a saved run from the same AI." |
| A red box: "The AI could not finish this step" | Click **Try again** once; if it fails again, click **Replay saved run** | "This is the failure handling: it tells me honestly instead of making something up." |
| Orange **Practice mode** badge at the start | Skip Step 1's typing. Start at Step 2 (Replay) | "I'll show a saved run from the real AI." |
| The app will not start at all | Use the screenshots in `docs/screenshots/` on the slides | "Here are screenshots from this morning's run." |
| You clicked **New conversation** by accident | Click **Replay saved run** | (nothing; keep going) |

A red error box is not a disaster. It is one of the features: a time limit, three tries, and an
honest message.

## Shortcut link

Opening `http://localhost:8501/?replay=1` loads the saved run immediately. Keep it in a second
browser tab as the emergency backup.

## Rehearse

- Run the whole path twice with a timer. Aim for two minutes.
- Practise the two sentences in Step 3. They are the most important part of the demo.
- Practise the "AI is busy" switch to Replay once, so it feels normal.
