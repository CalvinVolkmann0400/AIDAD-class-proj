"""Tests for saving and loading (uses a temporary folder, never the real database)."""

import storage
from models import Brief, DimensionScore, Message, Offer, SavedRun, ScoreResult


def make_run() -> SavedRun:
    return SavedRun(
        lead_name="Sam Rivera", created_at="2026-11-16 18:00", source="test",
        messages=[Message(role="ai", text="Hi"), Message(role="lead", text="Hello there")],
    )


def test_run_round_trip(tmp_path):
    db = tmp_path / "test.db"
    run = make_run()
    run_id = storage.save_run(run, db_file=db)
    assert storage.load_run(run_id, db_file=db) == run


def test_saving_again_updates_the_same_row(tmp_path):
    db = tmp_path / "test.db"
    run = make_run()
    run_id = storage.save_run(run, db_file=db)
    run.score = ScoreResult(
        enough_information=True,
        dimensions=[DimensionScore(name="pain", score=4, reason="r", quote="Hello there", quote_verified=True)],
    )
    run.brief = Brief(summary_lines=["a", "b", "c"], key_quotes=["Hello there"], unknowns=["x"], opening_line="Hi Sam")
    assert storage.save_run(run, run_id, db_file=db) == run_id
    assert storage.count_runs(db_file=db) == 1
    assert storage.load_run(run_id, db_file=db) == run


def test_missing_run_returns_none(tmp_path):
    assert storage.load_run(99, db_file=tmp_path / "test.db") is None


def test_offer_and_replay_files_round_trip(tmp_path):
    offer = Offer(business_name="B", closer_name="C", offer_name="O", included=["x"], price="$1", length="1 day")
    storage.save_offer(offer, tmp_path / "offer.json")
    assert storage.load_offer(tmp_path / "offer.json") == offer
    storage.save_replay(make_run(), tmp_path / "replay" / "saved_run.json")
    assert storage.load_replay(tmp_path / "replay" / "saved_run.json") == make_run()
    assert storage.load_replay(tmp_path / "nothing.json") is None


def test_real_offer_file_is_valid():
    assert storage.load_offer().business_name == "Maya Coaching"
