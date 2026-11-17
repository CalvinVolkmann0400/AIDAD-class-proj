"""Creates sample_data.json: invented leads for the dashboards.

Run once with:  uv run python seed.py

Every lead here is made up. Their typed answers are scripted below, but the AI's
questions, the scores and the briefs are produced by the real AI, exactly as in
the app. Call outcomes (showed up, closed) are invented too, so the dashboards
have something to show; the app labels all of this as sample data.

The script saves after every lead and skips leads it has already done, so it
can simply be run again if the AI service stops answering part-way.
"""

import json
import time
from pathlib import Path

import engine
import llm
import storage
from models import Message

SAMPLE_FILE = Path(__file__).parent / "sample_data.json"
PAUSE_SECONDS = 1  # a short gap between requests, to stay under the free tier's per-minute limit
# Use one model for the whole run, so every sample lead can be labelled with the model that made it.
llm.FALLBACK_MODEL = llm.MODEL
WAIT_AFTER_FAILURE = 30  # if the AI fails, wait this long and try the same step again
PATIENT_TRIES = 4
CLICKS_ONLY = 22  # invented: people who opened the chat link and never typed anything

# Words in the AI's question that tell us which scripted answer fits.
TOPIC_WORDS = {
    "tried": ["tried", "already", "so far", "in the past", "before"],
    "decision": ["decision", "decide", "anyone else", "involved", "partner"],
    "worth_it": ["worth", "result", "outcome", "success", "goal"],
    "start": ["start", "soon", "ready", "begin", "timeline", "when"],
}

# outcome: "pending" (call not held yet), "closed", "not_closed" or "no_show".
# stop_after: the lead leaves after this many messages (an abandoned chat).
SCRIPTS = [
    dict(name="Priya Nair", call_in_days=-1, call_at="10:00", outcome="closed", answers=dict(
        why_now="My anchor client ended our contract last month and it was 60% of my design income. I need a real system for finding clients instead of hoping.",
        tried="I worked with a business coach two years ago and it paid for itself, and I've been posting on LinkedIn every week, but nothing consistent comes from it.",
        decision="It's my decision. I'm a one-person studio.",
        worth_it="Two new retainer clients in the next three months would make it clearly worth it. What exactly is included in the program?",
        start="Next week if possible. I've already blocked out Friday mornings for this.")),
    dict(name="Marcus Bell", call_in_days=-2, call_at="14:00", outcome="closed", answers=dict(
        why_now="I went independent as an IT consultant in January and I have about two months of runway left. I need paying clients fast.",
        tried="Cold emails, around 200 of them, and I paid for a lead list that went nowhere. I got one small project out of all that.",
        decision="Just me, I make the calls for my business.",
        worth_it="If I could sign three clients on monthly support contracts I'd be stable. That is the whole goal.",
        start="Immediately. I can give this ten hours a week right now.")),
    dict(name="Hannah Weiss", call_in_days=-3, call_at="11:30", outcome="closed", answers=dict(
        why_now="My bookkeeping practice has been stuck at the same six clients for a year. I want to grow but I don't know what to do differently.",
        tried="I joined a networking group and I redid my website last spring. The website looks nice but nobody finds it.",
        decision="I decide on my own, although I usually talk big purchases through with my husband first.",
        worth_it="Getting to ten clients by the summer. How long is the program?",
        start="I could start at the beginning of next month, once tax season calms down.")),
    dict(name="Elena Kowalski", call_in_days=-3, call_at="15:30", outcome="not_closed", answers=dict(
        why_now="I'm a freelance copywriter and my income is fine, but it has been flat for two years and I'm getting bored of chasing one-off jobs.",
        tried="Mostly word of mouth. I read a couple of books about pricing but didn't change much.",
        decision="My partner and I share finances, so I would want to discuss it with her before committing to anything.",
        worth_it="I suppose moving from one-off jobs to a few monthly retainers. I'm not sure what number would feel worth it yet.",
        start="Maybe next month or the one after. There is no rush on my side.")),
    dict(name="Aisha Karim", call_in_days=-5, call_at="10:00", outcome="not_closed", answers=dict(
        why_now="A friend recommended Maya Coaching. My translation business is okay, I'm mostly curious what coaching could add.",
        tried="Nothing really, clients have always just come through an agency I work with.",
        decision="I run it with a business partner and she handles the money side, so she would have the final say.",
        worth_it="Honestly I don't know. Maybe having direct clients instead of going through the agency.",
        start="Not sure. We would have to talk about it first. Is there a guarantee?")),
    dict(name="Diego Santos", call_in_days=-6, call_at="14:00", outcome="no_show", answers=dict(
        why_now="I saw an ad and thought I'd take a look. I do some freelance video editing on the side of my job.",
        tried="Not much. I have a profile on a freelancer site.",
        decision="It would be up to me.",
        worth_it="More side income I guess. I haven't thought about a number.",
        start="Probably not this year. Maybe next year when work is quieter.")),
    dict(name="Ben Lindqvist", call_in_days=-7, call_at="11:30", outcome="no_show", answers=dict(
        why_now="Just browsing really. I'm thinking about freelancing someday.",
        tried="Nothing yet, I haven't started.",
        decision="Me.",
        worth_it="No idea. Do you have any free tips or a free version?",
        start="No plans yet.")),
    dict(name="Chloe Martin", call_in_days=0, call_at="16:30", outcome="pending", answers=dict(
        why_now="Not sure.", tried="No.", decision="Me.", worth_it="Don't know.", start="Maybe.")),
    dict(name="Tom Okafor", call_in_days=1, call_at="10:00", outcome="pending", answers=dict(
        why_now="I'm a wedding photographer and bookings for next season are way down. I want corporate clients so I'm not relying on weddings.",
        tried="I ran Instagram ads for two months and spent about $800. I got likes but only one enquiry.",
        decision="It's my business, so it's my decision.",
        worth_it="Two corporate clients who book me every quarter would make this worth it.",
        start="In about six weeks, when wedding season ends. I can't take on anything before that.")),
    dict(name="Ravi Menon", call_in_days=2, call_at="11:30", outcome="pending", answers=dict(
        why_now="I left my agency job to consult on marketing analytics, and my first contract ends in five weeks with nothing lined up after it.",
        tried="I've asked former colleagues for introductions and written a few articles. I got two coffee chats, no work yet.",
        decision="I make the decision myself. How much does the program cost?",
        worth_it="One signed contract before the current one ends, and a pipeline so I'm never in this spot again.",
        start="Within two weeks. I can do evenings and Saturday mornings.")),
    # Abandoned chats: these leads typed one or two messages and then left.
    dict(name="Nora Jensen", stop_after=1, answers=dict(why_now="I want more clients for my illustration work.")),
    dict(name="Leo Park", stop_after=1, answers=dict(why_now="Someone sent me this link, what is this exactly?")),
    dict(name="Omar Haddad", stop_after=2, answers=dict(
        why_now="My consulting income dropped a lot this year.", tried="I tried a few webinars. How much is it?")),
    dict(name="Jess Turner", stop_after=1, answers=dict(why_now="Just checking this out before I book anything.")),
    dict(name="Kai Brooks", stop_after=2, answers=dict(
        why_now="I'm a freelance developer and I want steadier work.", tried="Job boards mostly.")),
]
# Run the upcoming leads and the short abandoned chats first, so a cut-short run is still useful.
FIRST = ["Tom Okafor", "Chloe Martin", "Priya Nair", "Ben Lindqvist", "Nora Jensen", "Leo Park",
         "Omar Haddad", "Jess Turner", "Kai Brooks", "Ravi Menon"]
SCRIPTS.sort(key=lambda script: FIRST.index(script["name"]) if script["name"] in FIRST else len(FIRST))


def pick_answer(question: str, answers: dict, used: list[str]) -> str:
    """Choose the scripted answer that fits the AI's question, never repeating one."""
    question = question.lower()
    for topic, words in TOPIC_WORDS.items():
        if topic in answers and topic not in used and any(word in question for word in words):
            used.append(topic)
            return answers[topic]
    for topic in answers:  # nothing matched: use the next answer not given yet
        if topic not in used:
            used.append(topic)
            return answers[topic]
    return "I think that covers it."


def patient(work):
    """Run one AI step; if the service fails, wait and try again a few times before giving up."""
    for attempt in range(1, PATIENT_TRIES + 1):
        try:
            return work()
        except llm.AIError:
            if attempt == PATIENT_TRIES:
                raise
            print(f"  AI did not answer; waiting {WAIT_AFTER_FAILURE} seconds (try {attempt} of {PATIENT_TRIES})")
            time.sleep(WAIT_AFTER_FAILURE)


def run_lead(script: dict, offer) -> dict:
    """Play one scripted lead against the real AI and return the finished record."""
    messages = [engine.opening_message(offer, script["name"])]
    used = ["why_now"]
    answer = script["answers"]["why_now"]
    chat_done = False
    stop_after = script.get("stop_after")
    while not chat_done:
        messages.append(Message(role="lead", text=answer))
        time.sleep(PAUSE_SECONDS)
        turn = patient(lambda: engine.next_chat_turn(offer, messages))
        messages.append(Message(role="ai", text=turn.reply))
        chat_done = turn.done
        lead_messages = sum(1 for m in messages if m.role == "lead")
        if stop_after and lead_messages >= stop_after:
            break  # this lead walks away mid-chat
        answer = pick_answer(turn.reply, script["answers"], used)

    record = dict(
        name=script["name"], source=llm.MODEL, chat_done=chat_done,
        call_in_days=script.get("call_in_days"), call_at=script.get("call_at"),
        outcome=script.get("outcome", "pending"),
        messages=[m.model_dump() for m in messages], score=None, brief=None,
    )
    if chat_done:
        time.sleep(PAUSE_SECONDS)
        score = patient(lambda: engine.score_conversation(offer, messages))
        time.sleep(PAUSE_SECONDS)
        brief = patient(lambda: engine.write_brief(offer, messages, score))
        record["score"] = score.model_dump()
        record["brief"] = brief.model_dump()
    return record


def main() -> None:
    offer = storage.load_offer()
    data = json.loads(SAMPLE_FILE.read_text(encoding="utf-8")) if SAMPLE_FILE.exists() else {}
    data.setdefault("note", "Invented sample leads. Chats, scores and briefs by the real AI; outcomes and click counts invented.")
    data["clicks_only"] = CLICKS_ONLY
    data.setdefault("leads", [])
    done = {lead["name"] for lead in data["leads"]}
    for script in SCRIPTS:
        if script["name"] in done:
            continue
        try:
            record = run_lead(script, offer)
        except llm.AIError as error:
            print(f"Stopped at {script['name']}: {error}\nRun the script again later to continue.")
            break
        data["leads"].append(record)
        SAMPLE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        total = engine.total_score(engine.ScoreResult.model_validate(record["score"])) if record["score"] else "-"
        print(f"saved {record['name']}: {len(record['messages'])} messages, finished={record['chat_done']}, score={total}")
    print(f"{len(data['leads'])} of {len(SCRIPTS)} sample leads are in {SAMPLE_FILE.name}")


if __name__ == "__main__":
    main()
