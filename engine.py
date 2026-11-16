"""The three AI tasks (chat, score, brief), their prompts, and the checks in plain code.

Each task builds a prompt, calls llm.ask_ai(), and then checks the answer with
ordinary Python. The AI does the judging and writing; the code does the
arithmetic and makes sure every quote really came from the lead.
"""

import json
import re

import llm
from models import DIMENSIONS, Brief, ChatTurn, DimensionScore, Message, Offer, ScoreResult

MIN_QUESTIONS = 5
MAX_QUESTIONS = 7
MIN_LEAD_WORDS = 25  # fewer words than this from the lead = not enough to score

GUARDRAILS = """Rules you must always follow:
- Never ask about income, salary, savings, debt, credit or whether the lead can afford it.
  Talk about money only as "have you invested in solving this before" or "what would make this worth it".
- Never ask about or use age, gender, race, religion, health, disability, family status or nationality.
- Use only what is written in the conversation and in the offer. Never invent facts, prices or promises.
- Write plain text with no markdown."""


def opening_message(offer: Offer, lead_name: str) -> Message:
    """The first chat message. Written in code (not by the AI) so the AI disclosure is always there."""
    first_name = lead_name.split()[0]
    return Message(
        role="ai",
        text=(
            f"Hi {first_name}! I'm an AI assistant working with {offer.closer_name} at {offer.business_name}. "
            f"I'm not a person. I'll ask a few short questions so {offer.closer_name} can prepare for your call, "
            "and you can ask me anything about the program. To start: what made you book a call now?"
        ),
    )


def transcript(messages: list[Message]) -> str:
    """The conversation as plain text, one line per message, for the prompts."""
    return "\n".join(f"{m.role.upper()}: {' '.join(m.text.split())}" for m in messages)


# ---------- Task 1: the chat ----------

def next_chat_turn(offer: Offer, messages: list[Message], client=None) -> ChatTurn:
    """Ask the AI for its next chat message, given everything said so far."""
    asked = sum(1 for m in messages if m.role == "ai")
    must_finish = asked >= MAX_QUESTIONS
    if must_finish:
        progress = "You have asked all your questions. This message must be the goodbye: set done to true."
    elif asked >= MIN_QUESTIONS:
        progress = f"You have asked {asked} questions. Finish now unless one important thing is still missing."
    else:
        progress = f"You have asked {asked} questions so far. Ask {MIN_QUESTIONS} to {MAX_QUESTIONS} in total."

    system = f"""You are an AI assistant for {offer.business_name}. You are chatting by text with a lead
before their sales call with {offer.closer_name} (the closer). Never claim to be human.

Your goal is to learn what {offer.closer_name} needs to prepare: the problem the lead wants solved and
why now, what they have already tried, who else is part of the decision, what result would make this
worth it, and how ready they are to start.

How to chat:
- Read the whole conversation first. Choose the next question yourself, based on what is still missing.
- Never ask for something the lead has already told you. Briefly react to what they just said.
- One short question per message, at most three sentences in total.
- If the lead asks a question, answer it using ONLY the offer below. Give a price only if it is in the offer.
  If the offer does not answer it, say that {offer.closer_name} will cover it on the call.
- {progress}
- When you finish, set done to true and reply with a short thank-you saying {offer.closer_name}
  will read a summary before the call.

{GUARDRAILS}

THE OFFER:
{offer.model_dump_json(indent=2)}"""
    turn = llm.ask_ai(system, "THE CONVERSATION SO FAR:\n" + transcript(messages), ChatTurn, client)
    if must_finish:
        turn.done = True  # the code enforces the limit even if the AI forgets
    return turn


# ---------- Task 2: the score ----------

def score_conversation(offer: Offer, messages: list[Message], client=None) -> ScoreResult:
    """Ask the AI to score the finished conversation, then check its work in code."""
    system = f"""You score a finished chat between an AI assistant and a sales lead, to help the closer
prepare. Score each dimension from 0 (no sign of it) to 5 (very strong), using ONLY what the LEAD wrote.

The six dimensions, in this order and with exactly these names:
- pain: how serious and specific the lead's problem is
- urgency: how strong their reason is to act now
- decision authority: whether they can make this decision themselves
- fit with the offer: how well the offer below matches what they need
- investment readiness: whether they have invested in solving this before, or said what would make it
  worth it. Do not guess at income or wealth.
- commitment: how willing they are to do the work and to start

For each dimension give a one-sentence reason and a quote. The quote must be copied character for
character from ONE lead message: no rewording, no "...", no added words. If the lead said nothing
relevant, give score 0 and an empty quote. Set enough_information to false if the lead said too
little to score fairly.

{GUARDRAILS}

THE OFFER:
{offer.model_dump_json(indent=2)}"""
    result = llm.ask_ai(system, "THE CONVERSATION:\n" + transcript(messages), ScoreResult, client)
    result.dimensions = tidy_dimensions(result.dimensions)
    check_quotes(result, messages)
    if not lead_said_enough(messages):
        result.enough_information = False
    return result


def tidy_dimensions(found: list[DimensionScore]) -> list[DimensionScore]:
    """Put the six dimensions in our fixed order; any the AI left out gets an honest 0."""
    by_name = {d.name.strip().lower(): d for d in found}
    missing = "The AI did not score this dimension."
    return [by_name.get(name) or DimensionScore(name=name, score=0, reason=missing, quote="") for name in DIMENSIONS]


def _simplify(text: str) -> str:
    """Lower-case, straighten curly quotes and squeeze spaces, so tiny differences do not matter."""
    text = text.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip(" \"'.,!?")


def quote_is_real(quote: str, messages: list[Message]) -> bool:
    """True only if the quote appears inside one of the lead's own messages."""
    wanted = _simplify(quote)
    if not wanted:
        return False
    return any(wanted in _simplify(m.text) for m in messages if m.role == "lead")


def check_quotes(result: ScoreResult, messages: list[Message]) -> None:
    """Mark each evidence quote as verified, and remove any quote the lead never said."""
    for dimension in result.dimensions:
        dimension.quote_verified = quote_is_real(dimension.quote, messages)
        if not dimension.quote_verified:
            dimension.quote = ""


def lead_said_enough(messages: list[Message]) -> bool:
    words = sum(len(m.text.split()) for m in messages if m.role == "lead")
    return words >= MIN_LEAD_WORDS


def total_score(result: ScoreResult) -> int:
    """Turn six scores of 0-5 (30 points at most) into one number from 0 to 100."""
    points = sum(d.score for d in result.dimensions)
    return round(points / (5 * len(DIMENSIONS)) * 100)


def band(result: ScoreResult) -> str:
    """The label shown next to the total."""
    if not result.enough_information:
        return "Not enough information"
    total = total_score(result)
    if total >= 80:
        return "Strong lead (80+)"
    if total >= 60:
        return "Good lead (60-79)"
    if total >= 40:
        return "Needs discovery (40-59)"
    return "Low priority (under 40)"


# ---------- Task 3: the closer's brief ----------

def write_brief(offer: Offer, messages: list[Message], score: ScoreResult, client=None) -> Brief:
    """Ask the AI to write the closer's one-page brief from the conversation and the score."""
    system = f"""You write a short pre-call brief for {offer.closer_name}, the closer at {offer.business_name},
about a lead who just finished a chat with the AI assistant.

Write:
- summary_lines: exactly three short lines (who the lead is and what they want; why now; how ready they are)
- key_quotes: two to four quotes copied character for character from the LEAD's messages
- unknowns: the important things the lead did not say, which {offer.closer_name} should ask on the call
- opening_line: one natural sentence {offer.closer_name} could open the call with, built on the lead's own words

{GUARDRAILS}

THE OFFER:
{offer.model_dump_json(indent=2)}"""
    scores = json.dumps({d.name: d.score for d in score.dimensions})
    prompt = f"THE CONVERSATION:\n{transcript(messages)}\n\nTHE SCORES (0-5 each): {scores}"
    brief = llm.ask_ai(system, prompt, Brief, client)
    brief.key_quotes = [q for q in brief.key_quotes if quote_is_real(q, messages)]  # same quote check
    return brief
