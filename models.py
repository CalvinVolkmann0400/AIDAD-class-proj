"""Data shapes used across the app.

Each class below describes one kind of data (an offer, a chat message, a score...).
Pydantic checks that data really has the right fields and types, which matters most
for the JSON the AI sends back: if the AI's answer has the wrong shape, we find out
immediately instead of crashing later.
"""

from typing import Literal

from pydantic import BaseModel, Field

# The six things a lead is scored on. Each one is scored 0 to 5.
DIMENSIONS = [
    "pain",
    "urgency",
    "decision authority",
    "fit with the offer",
    "investment readiness",
    "commitment",
]


class Offer(BaseModel):
    """What the business sells. Loaded from offer.json."""

    business_name: str
    closer_name: str
    offer_name: str
    who_it_is_for: str = ""
    included: list[str]
    price: str
    length: str


class Message(BaseModel):
    """One chat message. role is "ai" or "lead"."""

    role: Literal["ai", "lead"]
    text: str


class ChatTurn(BaseModel):
    """What the AI returns for each step of the chat."""

    reply: str = Field(description="The next message to send to the lead.")
    done: bool = Field(description="True when the chat is finished and this reply is the goodbye.")


class DimensionScore(BaseModel):
    """The score for one dimension, with the AI's reason and its evidence."""

    name: str = Field(description="One of the six dimension names.")
    score: int = Field(ge=0, le=5, description="0 = no sign of it, 5 = very strong.")
    reason: str = Field(description="One short sentence explaining the score.")
    quote: str = Field(description="Exact words copied from one lead message, or empty if none.")
    # Filled in by our own code (not the AI) after checking the quote is real.
    quote_verified: bool = False


class ScoreResult(BaseModel):
    """What the AI returns when it scores a conversation."""

    enough_information: bool = Field(description="False if the lead said too little to score fairly.")
    dimensions: list[DimensionScore]


class Brief(BaseModel):
    """The one-page brief the closer reads before the call."""

    summary_lines: list[str] = Field(description="Exactly three short lines summarising the lead.")
    key_quotes: list[str] = Field(description="Up to four exact quotes from the lead.")
    unknowns: list[str] = Field(description="What the closer still does not know.")
    opening_line: str = Field(description="A suggested first sentence for the call.")


class SavedRun(BaseModel):
    """One whole run: the conversation plus (when ready) its score and brief."""

    lead_name: str
    created_at: str
    source: str  # which AI produced it, for example "gemini-3.6-flash" or "practice"
    messages: list[Message]
    score: ScoreResult | None = None
    brief: Brief | None = None
