"""Tests for the dashboard numbers."""

from datetime import date

import metrics
from models import DIMENSIONS, Brief, DimensionScore, Lead, Message, ScoreResult

TODAY = date(2026, 11, 17)
CHAT = [Message(role="ai", text="Hi"), Message(role="lead", text="Hello")]
BRIEF = Brief(summary_lines=["a", "b", "c"], key_quotes=["Hello"], unknowns=["x"], opening_line="Hi")


def score(points: int, enough: bool = True) -> ScoreResult:
    return ScoreResult(enough_information=enough,
                       dimensions=[DimensionScore(name=n, score=points, reason="r", quote="") for n in DIMENSIONS])


def lead(name: str, call_time: str = "", outcome: str = "pending", done: bool = True, points: int | None = 4) -> Lead:
    return Lead(token=name, name=name, created_at="2026-11-10 09:00", source="test", call_time=call_time,
                messages=CHAT, chat_done=done, outcome=outcome,
                score=score(points) if points is not None else None, brief=BRIEF if points is not None else None)


LEADS = [
    lead("closed-strong", "2026-11-14 10:00", "closed", points=5),
    lead("not-closed", "2026-11-15 10:00", "not_closed", points=3),
    lead("no-show-low", "2026-11-16 10:00", "no_show", points=1),
    lead("today", "2026-11-17 14:00"),
    lead("next-week", "2026-11-25 10:00"),
    lead("abandoned", done=False, points=None),
    Lead(token="never-typed", name="never-typed", created_at="2026-11-10 09:00", source="test", call_time="",
         messages=CHAT[:1]),
]


def test_funnel_counts_each_level():
    stages = metrics.funnel(LEADS, clicks=20)
    assert [stage.count for stage in stages] == [20, 6, 5, 5, 2, 1]
    assert [stage.out_of for stage in stages] == [20, 20, 6, 5, 3, 2]  # showed is out of the 3 calls with a result
    assert stages[1].rate == 0.3


def test_funnel_never_shows_fewer_clicks_than_chats():
    assert metrics.funnel(LEADS, clicks=0)[0].count == 6


def test_biggest_leak_is_the_level_with_the_lowest_rate():
    assert metrics.biggest_leak(metrics.funnel(LEADS, clicks=20)).name == "Started the chat"
    assert metrics.biggest_leak(metrics.funnel([], clicks=0)) is None


def test_show_rate_and_close_rate():
    assert metrics.show_rate(LEADS) == 2 / 3
    assert metrics.close_rate(LEADS) == 1 / 2
    assert metrics.show_rate([]) is None and metrics.close_rate([]) is None


def test_rates_by_band():
    rows = {row["band"]: row for row in metrics.rates_by_band(LEADS)}
    assert rows["Strong lead (80+)"]["calls_held"] == 1 and rows["Strong lead (80+)"]["close_rate"] == 1
    assert rows["Low priority (under 40)"]["show_rate"] == 0
    assert rows["Not enough information"]["leads"] == 0


def test_upcoming_and_past_calls():
    assert [l.name for l in metrics.upcoming_calls(LEADS, TODAY)] == ["today", "next-week"]
    assert [l.name for l in metrics.past_calls(LEADS, TODAY)] == ["no-show-low", "not-closed", "closed-strong"]


def test_needs_attention_flags_missing_outcomes_and_thin_chats():
    overdue = lead("overdue", "2026-11-12 10:00")
    thin = lead("thin", "2026-11-18 10:00")
    thin.score = score(0, enough=False)
    unscored = lead("unscored", "2026-11-19 10:00", points=None)
    not_booked = lead("not-booked")  # finished the chat, never picked a time
    extra = [overdue, thin, unscored, not_booked]
    reasons = {l.name: reason for l, reason in metrics.needs_attention(LEADS + extra, TODAY)}
    assert set(reasons) == {"overdue", "thin", "unscored", "not-booked"}
    assert metrics.funnel(LEADS + extra, clicks=30)[3].count == 8  # booked: not-booked is left out
    assert "Record" in reasons["overdue"] and "too little" in reasons["thin"]


def test_closer_numbers():
    numbers = metrics.closer_numbers(LEADS, TODAY)
    assert numbers["calls_today"] == 1
    assert numbers["calls_next_7_days"] == 1
    assert numbers["average_upcoming_score"] == 80
