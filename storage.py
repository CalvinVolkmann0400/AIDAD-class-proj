"""Saving and loading: the offer file, the SQLite database, and the sample data.

SQLite is a small database that lives in one file (sunsettr.db) and ships with Python.
There are three tables:
  leads   one row per lead: their chat, score, brief, call time and call outcome
  clicks  one row each time somebody opens the lead chat link
  notes   small remembered facts (for example the day the sample data was loaded)
"""

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from models import Lead, Offer

FOLDER = Path(__file__).parent
OFFER_FILE = FOLDER / "offer.json"
SAMPLE_FILE = FOLDER / "sample_data.json"
DB_FILE = FOLDER / "sunsettr.db"

CALL_SLOTS = ["10:00", "11:30", "14:00", "15:30"]  # the closer's daily call times
COLUMNS = ("token, name, created_at, source, call_time, messages_json, chat_done,"
           " score_json, brief_json, outcome, is_sample")


# ---------- The offer file ----------

def load_offer(path: Path = OFFER_FILE) -> Offer:
    return Offer.model_validate_json(path.read_text(encoding="utf-8"))


def save_offer(offer: Offer, path: Path = OFFER_FILE) -> None:
    path.write_text(offer.model_dump_json(indent=2), encoding="utf-8")


# ---------- The database ----------

def _connect(db_file: Path) -> sqlite3.Connection:
    """Open the database and create the tables the first time."""
    connection = sqlite3.connect(db_file)
    connection.executescript(
        """CREATE TABLE IF NOT EXISTS leads (
               id INTEGER PRIMARY KEY AUTOINCREMENT, token TEXT UNIQUE, name TEXT, created_at TEXT,
               source TEXT, call_time TEXT, messages_json TEXT, chat_done INTEGER,
               score_json TEXT, brief_json TEXT, outcome TEXT, is_sample INTEGER);
           CREATE TABLE IF NOT EXISTS clicks (
               id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, is_sample INTEGER);
           CREATE TABLE IF NOT EXISTS notes (name TEXT PRIMARY KEY, value TEXT);"""
    )
    return connection


def save_lead(lead: Lead, db_file: Path = DB_FILE) -> Lead:
    """Save a lead. A lead with no id is added as a new row; otherwise its row is updated."""
    values = (
        lead.token, lead.name, lead.created_at, lead.source, lead.call_time,
        json.dumps([m.model_dump() for m in lead.messages]), int(lead.chat_done),
        lead.score.model_dump_json() if lead.score else None,
        lead.brief.model_dump_json() if lead.brief else None,
        lead.outcome, int(lead.is_sample),
    )
    connection = _connect(db_file)
    with connection:  # "with" commits the change, or undoes it if something fails
        if lead.id is None:
            marks = ", ".join("?" * len(values))  # the ? marks keep data separate from the SQL
            lead.id = connection.execute(f"INSERT INTO leads ({COLUMNS}) VALUES ({marks})", values).lastrowid
        else:
            settings = ", ".join(f"{column.strip()}=?" for column in COLUMNS.split(","))
            connection.execute(f"UPDATE leads SET {settings} WHERE id=?", values + (lead.id,))
    connection.close()
    return lead


def _to_lead(row) -> Lead:
    """Turn one database row back into a Lead object."""
    return Lead.model_validate(
        {
            "id": row[0], "token": row[1], "name": row[2], "created_at": row[3], "source": row[4],
            "call_time": row[5], "messages": json.loads(row[6]), "chat_done": bool(row[7]),
            "score": json.loads(row[8]) if row[8] else None,
            "brief": json.loads(row[9]) if row[9] else None,
            "outcome": row[10], "is_sample": bool(row[11]),
        }
    )


def list_leads(db_file: Path = DB_FILE) -> list[Lead]:
    """Every lead, newest first."""
    connection = _connect(db_file)
    rows = connection.execute(f"SELECT id, {COLUMNS} FROM leads ORDER BY created_at DESC, id DESC").fetchall()
    connection.close()
    return [_to_lead(row) for row in rows]


def get_lead(lead_id: int, db_file: Path = DB_FILE) -> Lead | None:
    return next((lead for lead in list_leads(db_file) if lead.id == lead_id), None)


def get_lead_by_token(token: str, db_file: Path = DB_FILE) -> Lead | None:
    return next((lead for lead in list_leads(db_file) if lead.token == token), None)


def add_click(db_file: Path = DB_FILE, is_sample: bool = False) -> None:
    """Record that somebody opened the lead chat link (the top of the funnel)."""
    connection = _connect(db_file)
    with connection:
        connection.execute("INSERT INTO clicks (created_at, is_sample) VALUES (?, ?)",
                           (datetime.now().strftime("%Y-%m-%d %H:%M"), int(is_sample)))
    connection.close()


def count_clicks(db_file: Path = DB_FILE) -> int:
    connection = _connect(db_file)
    total = connection.execute("SELECT COUNT(*) FROM clicks").fetchone()[0]
    connection.close()
    return total


def free_slots(leads: list[Lead], today: date, days: int = 5) -> dict[str, list[str]]:
    """The call times a lead can still choose: the next few weekdays, minus times already taken.

    Returns a dictionary like {"2026-11-18": ["10:00", "14:00"], ...}.
    """
    taken = {lead.call_time for lead in leads}
    slots: dict[str, list[str]] = {}
    day = today
    while len(slots) < days:
        day += timedelta(days=1)
        if day.weekday() >= 5:  # 5 and 6 are Saturday and Sunday
            continue
        free = [slot for slot in CALL_SLOTS if f"{day} {slot}" not in taken]
        if free:
            slots[str(day)] = free
    return slots


# ---------- Sample data (invented leads that fill the dashboards) ----------

def ensure_sample_data(today: date, db_file: Path = DB_FILE, sample_file: Path = SAMPLE_FILE) -> None:
    """Load the sample leads once per day, with call dates placed around today.

    The sample file stores each call as "so many days from today", so the
    dashboards always show some upcoming calls and some past ones.
    """
    connection = _connect(db_file)
    loaded_on = connection.execute("SELECT value FROM notes WHERE name='sample_loaded_on'").fetchone()
    connection.close()
    if not sample_file.exists() or (loaded_on and loaded_on[0] == str(today)):
        return
    _delete(db_file, only_samples=True)
    data = json.loads(sample_file.read_text(encoding="utf-8"))
    for number, record in enumerate(data["leads"], start=1):
        has_call = record.get("call_in_days") is not None
        call_day = today + timedelta(days=record["call_in_days"]) if has_call else today
        chatted_on = call_day - timedelta(days=2 if has_call else number % 6)
        save_lead(
            Lead(
                token=f"sample-{number}", name=record["name"], source=record["source"],
                created_at=f"{chatted_on} 09:{number:02d}",
                call_time=f"{call_day} {record['call_at']}" if has_call else "",
                messages=record["messages"], chat_done=record["chat_done"],
                score=record["score"], brief=record["brief"],
                outcome=record["outcome"], is_sample=True,
            ),
            db_file,
        )
    for _ in range(data["clicks_only"] + len(data["leads"])):  # every sample lead clicked the link too
        add_click(db_file, is_sample=True)
    connection = _connect(db_file)
    with connection:
        connection.execute("INSERT OR REPLACE INTO notes VALUES ('sample_loaded_on', ?)", (str(today),))
    connection.close()


def reset_to_sample_data(today: date, db_file: Path = DB_FILE, sample_file: Path = SAMPLE_FILE) -> None:
    """Wipe every lead and click, then load the sample data fresh."""
    _delete(db_file, only_samples=False)
    ensure_sample_data(today, db_file, sample_file)


def _delete(db_file: Path, only_samples: bool) -> None:
    where = " WHERE is_sample=1" if only_samples else ""
    connection = _connect(db_file)
    with connection:
        connection.execute("DELETE FROM leads" + where)
        connection.execute("DELETE FROM clicks" + where)
        connection.execute("DELETE FROM notes")
    connection.close()
