"""Tests for the plain-code checks: quotes, totals, bands, and the three tasks with a fake AI."""

import engine
from fake_ai import PracticeClient
from models import DIMENSIONS, DimensionScore, Message, Offer, ScoreResult

OFFER = Offer(
    business_name="Maya Coaching", closer_name="Jordan", offer_name="Test Program",
    included=["Weekly call"], price="$3,000", length="90 days",
)
MESSAGES = [
    Message(role="ai", text="What made you book a call now?"),
    Message(role="lead", text="I lost two big clients this spring and my income is all over the place."),
    Message(role="ai", text="What have you tried?"),
    Message(role="lead", text="I paid for an online course last year, but I never finished it. It is just me deciding."),
]


def make_score(points: int, enough: bool = True) -> ScoreResult:
    dimensions = [DimensionScore(name=n, score=points, reason="r", quote="") for n in DIMENSIONS]
    return ScoreResult(enough_information=enough, dimensions=dimensions)


def test_real_quote_is_accepted_even_with_different_capitals_and_spacing():
    assert engine.quote_is_real("I LOST two   big clients this spring", MESSAGES)


def test_invented_quote_is_rejected():
    assert not engine.quote_is_real("I have a huge budget ready", MESSAGES)


def test_quote_from_the_ai_side_does_not_count():
    assert not engine.quote_is_real("What made you book a call now?", MESSAGES)


def test_check_quotes_removes_invented_quotes_and_keeps_real_ones():
    score = make_score(3)
    score.dimensions[0].quote = "my income is all over the place"
    score.dimensions[1].quote = "I need this fixed by Friday"  # the lead never said this
    engine.check_quotes(score, MESSAGES)
    assert score.dimensions[0].quote_verified and score.dimensions[0].quote
    assert not score.dimensions[1].quote_verified and score.dimensions[1].quote == ""


def test_total_is_out_of_100():
    assert engine.total_score(make_score(5)) == 100
    assert engine.total_score(make_score(0)) == 0
    assert engine.total_score(make_score(3)) == 60


def test_bands():
    assert engine.band(make_score(5)) == "Strong lead (80+)"
    assert engine.band(make_score(3)) == "Good lead (60-79)"
    assert engine.band(make_score(2)) == "Needs discovery (40-59)"
    assert engine.band(make_score(1)) == "Low priority (under 40)"
    assert engine.band(make_score(5, enough=False)) == "Not enough information"


def test_missing_dimensions_are_filled_with_zero_in_the_fixed_order():
    only_one = [DimensionScore(name="Urgency", score=4, reason="r", quote="")]
    tidy = engine.tidy_dimensions(only_one)
    assert [d.name for d in tidy][:2] == ["pain", "urgency"]
    assert tidy[0].score == 0 and tidy[1].score == 4 and len(tidy) == 6


def test_dimension_names_written_with_underscores_still_match():
    odd_names = [DimensionScore(name="Decision_Authority", score=5, reason="r", quote=""),
                 DimensionScore(name="fit-with-the-offer", score=3, reason="r", quote="")]
    tidy = {d.name: d.score for d in engine.tidy_dimensions(odd_names)}
    assert tidy["decision authority"] == 5 and tidy["fit with the offer"] == 3


def test_opening_message_says_it_is_an_ai():
    text = engine.opening_message(OFFER, "Sam Rivera").text
    assert "AI assistant" in text and "Jordan" in text and "Sam" in text


def test_chat_turn_with_fake_ai():
    turn = engine.next_chat_turn(OFFER, MESSAGES[:2], client=PracticeClient())
    assert turn.reply and not turn.done


def test_chat_is_forced_to_finish_at_the_question_limit():
    class NeverDoneClient:
        def generate(self, model, system, prompt, schema):
            return '{"reply": "One more question?", "done": false}'

    long_chat = [Message(role="ai", text="q"), Message(role="lead", text="a")] * engine.MAX_QUESTIONS
    assert engine.next_chat_turn(OFFER, long_chat, client=NeverDoneClient()).done


def test_score_with_fake_ai_has_six_verified_dimensions():
    score = engine.score_conversation(OFFER, MESSAGES, client=PracticeClient())
    assert len(score.dimensions) == 6
    assert all(d.quote_verified for d in score.dimensions)
    assert score.enough_information


def test_too_short_conversation_is_not_enough_information():
    short = [Message(role="ai", text="Why now?"), Message(role="lead", text="Not sure.")]
    score = engine.score_conversation(OFFER, short, client=PracticeClient())
    assert not score.enough_information
    assert engine.band(score) == "Not enough information"


def test_brief_with_fake_ai_only_keeps_real_quotes():
    score = engine.score_conversation(OFFER, MESSAGES, client=PracticeClient())
    brief = engine.write_brief(OFFER, MESSAGES, score, client=PracticeClient())
    assert len(brief.summary_lines) == 3
    assert brief.key_quotes and all(engine.quote_is_real(q, MESSAGES) for q in brief.key_quotes)
