"""Tests for saving and loading (uses a temporary folder, never the real database)."""

import json
from datetime import date

import storage
from models import Brief, DimensionScore, Lead, Message, Offer, ScoreResult

TODAY = date(2026, 11, 17)


def make_lead(token: str = "abc", **changes) -> Lead:
    lead = Lead(
        token=token, name="Sam Rivera", created_at="2026-11-16 18:00", source="test", call_time="",
        messages=[Message(role="ai", text="Hi"), Message(role="lead", text="Hello there")],
    )
    return lead.model_copy(update=changes)


def test_lead_round_trip(tmp_path):
    db = tmp_path / "test.db"
    lead = storage.save_lead(make_lead(), db)
    assert lead.id is not None
    assert storage.get_lead(lead.id, db) == lead
    assert storage.get_lead_by_token("abc", db) == lead


def test_saving_again_updates_the_same_row(tmp_path):
    db = tmp_path / "test.db"
    lead = storage.save_lead(make_lead(), db)
    lead.chat_done = True
    lead.outcome = "closed"
    lead.score = ScoreResult(
        enough_information=True,
        dimensions=[DimensionScore(name="pain", score=4, reason="r", quote="Hello there", quote_verified=True)],
    )
    lead.brief = Brief(summary_lines=["a", "b", "c"], key_quotes=["Hello there"], unknowns=["x"], opening_line="Hi Sam")
    storage.save_lead(lead, db)
    assert len(storage.list_leads(db)) == 1
    assert storage.get_lead(lead.id, db) == lead


def test_missing_lead_returns_none(tmp_path):
    db = tmp_path / "test.db"
    assert storage.get_lead(99, db) is None
    assert storage.get_lead_by_token("nobody", db) is None


def test_clicks_are_counted(tmp_path):
    db = tmp_path / "test.db"
    assert storage.count_clicks(db) == 0
    storage.add_click(db)
    storage.add_click(db)
    assert storage.count_clicks(db) == 2


def test_free_slots_skip_taken_times_and_weekends():
    taken = [make_lead(call_time="2026-11-18 10:00"), make_lead(call_time="2026-11-18 11:30")]
    slots = storage.free_slots(taken, TODAY)  # TODAY is Tuesday 17 November 2026
    assert slots["2026-11-18"] == ["14:00", "15:30"]
    assert list(slots) == ["2026-11-18", "2026-11-19", "2026-11-20", "2026-11-23", "2026-11-24"]  # no weekend
    assert slots["2026-11-19"] == storage.CALL_SLOTS


def test_a_fully_booked_day_is_not_offered():
    taken = [make_lead(call_time=f"2026-11-18 {slot}") for slot in storage.CALL_SLOTS]
    assert "2026-11-18" not in storage.free_slots(taken, TODAY)


def write_sample_file(path):
    record = {"name": "Priya Nair", "source": "test", "chat_done": True, "call_in_days": -1, "call_at": "10:00",
              "outcome": "closed", "messages": [{"role": "ai", "text": "Hi"}, {"role": "lead", "text": "Hello"}],
              "score": None, "brief": None}
    abandoned = dict(record, name="Leo Park", chat_done=False, call_in_days=None, call_at=None, outcome="pending")
    path.write_text(json.dumps({"clicks_only": 3, "leads": [record, abandoned]}), encoding="utf-8")


def test_sample_data_loads_once_with_dates_around_today(tmp_path):
    db, sample = tmp_path / "test.db", tmp_path / "sample.json"
    write_sample_file(sample)
    storage.ensure_sample_data(TODAY, db, sample)
    storage.ensure_sample_data(TODAY, db, sample)  # a second call on the same day changes nothing
    leads = {lead.name: lead for lead in storage.list_leads(db)}
    assert len(leads) == 2 and all(lead.is_sample for lead in leads.values())
    assert leads["Priya Nair"].call_time == "2026-11-16 10:00"  # one day before "today"
    assert leads["Leo Park"].call_time == ""  # never finished the chat, so no call
    assert storage.count_clicks(db) == 5  # 3 click-only visitors plus the 2 leads


def test_reset_removes_real_leads_and_reloads_samples(tmp_path):
    db, sample = tmp_path / "test.db", tmp_path / "sample.json"
    write_sample_file(sample)
    storage.save_lead(make_lead("real-lead"), db)
    storage.add_click(db)
    storage.reset_to_sample_data(TODAY, db, sample)
    assert storage.get_lead_by_token("real-lead", db) is None
    assert len(storage.list_leads(db)) == 2 and storage.count_clicks(db) == 5


def test_a_new_day_reloads_samples_but_keeps_real_leads(tmp_path):
    db, sample = tmp_path / "test.db", tmp_path / "sample.json"
    write_sample_file(sample)
    storage.ensure_sample_data(TODAY, db, sample)
    storage.save_lead(make_lead("real-lead"), db)
    storage.ensure_sample_data(date(2026, 11, 18), db, sample)
    leads = {lead.name: lead for lead in storage.list_leads(db)}
    assert leads["Priya Nair"].call_time == "2026-11-17 10:00"
    assert "Sam Rivera" in leads and len(leads) == 3


def test_offer_file_round_trip(tmp_path):
    offer = Offer(business_name="B", closer_name="C", offer_name="O", included=["x"], price="$1", length="1 day")
    storage.save_offer(offer, tmp_path / "offer.json")
    assert storage.load_offer(tmp_path / "offer.json") == offer


def test_real_offer_file_is_valid():
    assert storage.load_offer().business_name == "Maya Coaching"
