# Two-minute live demo script

The path: **start screen → lead chat (two answers, live) → closer dashboard → one lead's brief → owner funnel.**

Typing two answers shows the AI really choosing its questions. Everything after that reads
saved leads from the database, so it cannot stall.

## Before class (five minutes)

1. Open a terminal in the project folder and start the app:

   ```bash
   uv run streamlit run app.py
   ```

2. The browser opens at `http://localhost:8501` on the **start screen** with three cards: Lead, Closer, Owner.
3. Click **Continue as the owner**, open **Settings**, and click **Test the AI connection**.
   - "success" means the live chat is safe to try.
   - If it fails or takes more than about 10 seconds, skip Step 1 below and start at Step 2.
4. Click **Switch role** in the sidebar to get back to the start screen.
5. Make the browser text bigger (Ctrl and +) so the back row can read it.

## The demo

### Step 1 — the lead's view, live (about 45 seconds)

On the start screen click **Open the lead's chat link**.

**Say:** "This is all a lead ever sees: one chat, no menu. Notice the first message says it's an AI."

Type a name (for example `Alex Morgan`) and click **Start the chat**. Click in the reply box
before typing each answer (it loses focus while the AI is replying). Then type:

> I lost two big clients this spring and my income has been up and down ever since.

Wait for the reply (the spinner says "AI is thinking"). Replies usually take 2 to 5 seconds.
Keep talking while it thinks.

**Say:** "I didn't script that question. The AI chose it from what I just said."

Type the second answer, which includes a question back to the AI:

> I tried an online course last year but never finished it. How much does your program cost?

**Say:** "It may only answer from the offer file, so the price is the one in the file. When the
chat ends, the lead gets a call time, and the AI scores the chat and writes a brief for the closer."

### Step 2 — the closer's view (about 40 seconds)

Open a **new browser tab** at `http://localhost:8501` and click **Continue as Jordan**.

**Say:** "This is Jordan, the closer. Numbers at the top, then today's and upcoming calls. Each
call has the lead's score and one line about them."

Click **Brief** on **Sam Rivera**.

**Say:** "This is what Jordan reads a minute before the call: three lines of summary, the lead's
own words, what's still unknown, and a suggested opening line. The AI gave six scores with a
quote for each, and my code checked every quote really appears in the chat."

(If you have time: click **Score** to show the six cards with the green ticks.)

### Step 3 — the owner's view (about 35 seconds)

Click **Switch role**, then **Continue as the owner**.

**Say:** "And this is the owner. The funnel goes level by level: who clicked the link, who started
the chat, who finished, who showed up to the call, who bought. The app marks the biggest leak."

Point at the yellow **Biggest leak** box, then scroll to **Results by score band**.

**Say:** "This last table is the honest test of the idea: do higher scores show up and close more?
Right now it's sample data, so it's an illustration. Collecting real results is my next step."

## If something goes wrong

| What you see | What to do | What to say |
|---|---|---|
| The spinner runs longer than about 10 seconds | Leave that tab, go to Step 2 | "The free AI tier is busy, so let me show what the closer sees for leads who already finished." |
| A red box: "The AI could not finish this step" | Click **Try again** once; if it fails again, go to Step 2 | "This is the failure handling: it tells me honestly instead of making something up." |
| Orange **Practice mode** banner | Skip Step 1's typing; start at Step 2 | "I'll show leads that already went through the real AI." |
| The app will not start at all | Use the screenshots in `docs/screenshots/` on the slides | "Here are screenshots from last night's run." |

A red error box is not a disaster. It is one of the features: a time limit, three tries, and an
honest message.

## Good to know

- The free AI tier allows only a limited number of requests a day. One practice chat is fine; do not run five in a row right before class.

- The closer and owner pages never call the AI, so Steps 2 and 3 always work.
- Refreshing a closer or owner page sends you back to the start screen (there is no real sign-in). Just pick the role again.
- The lead's chat survives a refresh, because its link contains that lead's personal code.
- Dashboards say "Includes sample data" at the top. If asked: the sample leads' chats, scores and briefs came from the real AI; their call results are invented.

## Rehearse

- Run the whole path twice with a timer. Aim for two minutes.
- Practise the two sentences about the quote check in Step 2. They are the most important part.
- Practise skipping Step 1 once, so it feels normal if the AI is slow.
