"""Saving and loading: the offer file, the SQLite database, and the replay file.

SQLite is a small database that lives in one file (sunsettr.db) and ships with Python,
so there is nothing to install. We keep one table, "runs": one row per conversation.
The messages, score and brief are stored as JSON text in that row.
"""

import json
import sqlite3
from pathlib import Path

from models import Offer, SavedRun

FOLDER = Path(__file__).parent
OFFER_FILE = FOLDER / "offer.json"
REPLAY_FILE = FOLDER / "replay" / "saved_run.json"
DB_FILE = FOLDER / "sunsettr.db"


# ---------- The offer file ----------

def load_offer(path: Path = OFFER_FILE) -> Offer:
    return Offer.model_validate_json(path.read_text(encoding="utf-8"))


def save_offer(offer: Offer, path: Path = OFFER_FILE) -> None:
    path.write_text(offer.model_dump_json(indent=2), encoding="utf-8")


# ---------- The database ----------

def _connect(db_file: Path) -> sqlite3.Connection:
    """Open the database and create the table the first time."""
    connection = sqlite3.connect(db_file)
    connection.execute(
        """CREATE TABLE IF NOT EXISTS runs (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               lead_name TEXT, created_at TEXT, source TEXT,
               messages_json TEXT, score_json TEXT, brief_json TEXT)"""
    )
    return connection


def save_run(run: SavedRun, run_id: int | None = None, db_file: Path = DB_FILE) -> int:
    """Save a run. With no run_id a new row is added; with one, that row is updated.

    Returns the row's id so the app can update the same row later
    (for example when the score is added to a saved conversation).
    """
    values = (
        run.lead_name,
        run.created_at,
        run.source,
        json.dumps([m.model_dump() for m in run.messages]),
        run.score.model_dump_json() if run.score else None,
        run.brief.model_dump_json() if run.brief else None,
    )
    connection = _connect(db_file)
    with connection:  # "with" commits the change, or undoes it if something fails
        if run_id is None:
            cursor = connection.execute(
                "INSERT INTO runs (lead_name, created_at, source, messages_json, score_json, brief_json)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                values,
            )
            run_id = cursor.lastrowid
        else:
            connection.execute(
                "UPDATE runs SET lead_name=?, created_at=?, source=?, messages_json=?,"
                " score_json=?, brief_json=? WHERE id=?",
                values + (run_id,),
            )
    connection.close()
    return run_id


def load_run(run_id: int, db_file: Path = DB_FILE) -> SavedRun | None:
    """Read one run back from the database, or None if that id does not exist."""
    connection = _connect(db_file)
    row = connection.execute(
        "SELECT lead_name, created_at, source, messages_json, score_json, brief_json"
        " FROM runs WHERE id=?",
        (run_id,),
    ).fetchone()
    connection.close()
    if row is None:
        return None
    return SavedRun.model_validate(
        {
            "lead_name": row[0],
            "created_at": row[1],
            "source": row[2],
            "messages": json.loads(row[3]),
            "score": json.loads(row[4]) if row[4] else None,
            "brief": json.loads(row[5]) if row[5] else None,
        }
    )


def count_runs(db_file: Path = DB_FILE) -> int:
    connection = _connect(db_file)
    total = connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    connection.close()
    return total


# ---------- The replay file (a saved real-AI run for the demo) ----------

def load_replay(path: Path = REPLAY_FILE) -> SavedRun | None:
    if not path.exists():
        return None
    return SavedRun.model_validate_json(path.read_text(encoding="utf-8"))


def save_replay(run: SavedRun, path: Path = REPLAY_FILE) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(run.model_dump_json(indent=2), encoding="utf-8")
