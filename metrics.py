"""The numbers on the dashboards, worked out in plain Python from the list of leads.

Nothing here talks to the AI or the screen: each function takes leads in and
gives numbers back, which makes them easy to test.
"""

from dataclasses import dataclass
from datetime import date, timedelta

import engine
from models import Lead

BANDS = ["Strong lead (80+)", "Good lead (60-79)", "Needs discovery (40-59)",
         "Low priority (under 40)", "Not enough information"]


@dataclass
class Stage:
    """One level of the funnel: how many got here, out of how many who could have."""

    name: str
    count: int
    out_of: int  # how many could have reached this level
    out_of_what: str = "from the level above"
    note: str = ""

    @property
    def rate(self) -> float | None:
        """The share that made it to this level, from 0 to 1 (None if nobody could)."""
        return self.count / self.out_of if self.out_of else None


def has_started(lead: Lead) -> bool:
    return any(message.role == "lead" for message in lead.messages)


def showed_up(lead: Lead) -> bool:
    return lead.outcome in ("closed", "not_closed")


def call_day(lead: Lead) -> date | None:
    return date.fromisoformat(lead.call_time[:10]) if lead.call_time else None


def funnel(leads: list[Lead], clicks: int) -> list[Stage]:
    """The five levels: link clicks, chat started, chat finished, showed up, closed."""
    started = [lead for lead in leads if has_started(lead)]
    finished = [lead for lead in started if lead.chat_done]
    held = [lead for lead in finished if lead.outcome != "pending"]  # calls with a recorded result
    showed = [lead for lead in held if showed_up(lead)]
    closed = [lead for lead in showed if lead.outcome == "closed"]
    clicks = max(clicks, len(started))  # everyone who chatted must have clicked
    waiting = len(finished) - len(held)
    return [
        Stage("Clicked the link", clicks, clicks),
        Stage("Started the chat", len(started), clicks),
        Stage("Finished the chat", len(finished), len(started)),
        Stage("Showed up to the call", len(showed), len(held), "calls that have a recorded result",
              f"{waiting} booked calls have not happened yet, so they are not counted here."),
        Stage("Closed", len(closed), len(showed)),
    ]


def biggest_leak(stages: list[Stage]) -> Stage | None:
    """The level where the largest share of people is lost."""
    measured = [stage for stage in stages[1:] if stage.rate is not None]
    return min(measured, key=lambda stage: stage.rate) if measured else None


def show_rate(leads: list[Lead]) -> float | None:
    """Of the calls with a recorded result, the share where the lead showed up."""
    held = [lead for lead in leads if lead.outcome != "pending"]
    return sum(showed_up(lead) for lead in held) / len(held) if held else None


def close_rate(leads: list[Lead]) -> float | None:
    """Of the leads who showed up, the share who bought."""
    showed = [lead for lead in leads if showed_up(lead)]
    return sum(lead.outcome == "closed" for lead in showed) / len(showed) if showed else None


def rates_by_band(leads: list[Lead]) -> list[dict]:
    """Show rate and close rate for each score band. This is the check on whether the score means anything."""
    rows = []
    for band in BANDS:
        in_band = [lead for lead in leads if lead.score and engine.band(lead.score) == band]
        held = [lead for lead in in_band if lead.outcome != "pending"]
        rows.append({"band": band, "leads": len(in_band), "calls_held": len(held),
                     "show_rate": show_rate(in_band), "close_rate": close_rate(in_band)})
    return rows


def upcoming_calls(leads: list[Lead], today: date) -> list[Lead]:
    """Calls from today onwards with no result recorded yet, soonest first."""
    waiting = [lead for lead in leads if lead.call_time and lead.outcome == "pending" and call_day(lead) >= today]
    return sorted(waiting, key=lambda lead: lead.call_time)


def past_calls(leads: list[Lead], today: date) -> list[Lead]:
    """Calls that have a result, or whose day has passed, most recent first."""
    done = [lead for lead in leads if lead.call_time and (lead.outcome != "pending" or call_day(lead) < today)]
    return sorted(done, key=lambda lead: lead.call_time, reverse=True)


def needs_attention(leads: list[Lead], today: date) -> list[tuple[Lead, str]]:
    """Leads the closer should look at, each with the reason."""
    items = []
    for lead in past_calls(leads, today):
        if lead.outcome == "pending":
            items.append((lead, "The call day has passed. Record what happened."))
    for lead in upcoming_calls(leads, today):
        if lead.score is None or lead.brief is None:
            items.append((lead, "The score and brief have not been generated yet."))
        elif not lead.score.enough_information:
            items.append((lead, "The lead said too little in the chat to score. Plan extra discovery."))
    return items


def closer_numbers(leads: list[Lead], today: date) -> dict:
    """The closer's at-a-glance numbers."""
    upcoming = upcoming_calls(leads, today)
    scored = [engine.total_score(lead.score) for lead in upcoming if lead.score and lead.score.enough_information]
    return {
        "calls_today": sum(call_day(lead) == today for lead in upcoming),
        "calls_next_7_days": sum(call_day(lead) < today + timedelta(days=7) for lead in upcoming),
        "show_rate": show_rate(leads),
        "close_rate": close_rate(leads),
        "average_upcoming_score": round(sum(scored) / len(scored)) if scored else None,
    }
