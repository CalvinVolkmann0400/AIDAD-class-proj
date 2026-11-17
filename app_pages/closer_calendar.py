"""Closer: every upcoming call by day, the call history, and where call results are recorded."""

from datetime import date

import streamlit as st

import metrics
import storage
import ui

leads = storage.list_leads()
today = date.today()
ui.sample_note(leads)


def record(lead, outcome: str) -> None:
    """Save what happened on a call (runs when one of the result buttons is clicked)."""
    lead.outcome = outcome
    storage.save_lead(lead)


# ----- Upcoming calls, grouped by day -----
st.subheader("Upcoming")
upcoming = metrics.upcoming_calls(leads, today)
if not upcoming:
    st.info("No upcoming calls.")
for day in sorted({metrics.call_day(lead) for lead in upcoming}):
    label = day.strftime("%A %d %B") + (" · today" if day == today else "")
    st.markdown(f"**{label}**")
    for lead in [l for l in upcoming if metrics.call_day(l) == day]:
        with st.container(border=True):
            when, who, result, link = st.columns([1, 4, 5, 2], vertical_alignment="center")
            when.markdown(f"**{lead.call_time[11:]}**")
            who.markdown(f"**{lead.name}** · {ui.score_label(lead)}")
            with result.container(horizontal=True):  # record the result once the call has happened
                st.button("Closed", key=f"closed_{lead.id}", icon=":material/check:", on_click=record, args=(lead, "closed"))
                st.button("Did not close", key=f"open_{lead.id}", on_click=record, args=(lead, "not_closed"))
                st.button("No-show", key=f"noshow_{lead.id}", on_click=record, args=(lead, "no_show"))
            if link.button("Lead file", key=f"file_{lead.id}", icon=":material/person:"):
                ui.open_lead(lead.id, "Brief")

# ----- History: calls that already have a result (or whose day has passed) -----
st.subheader("History")
history = metrics.past_calls(leads, today)
if not history:
    st.info("No past calls yet.")
else:
    st.caption("Click a row, then open that lead's file to read the brief or change the result.")
    table = st.dataframe(
        [{"Call": ui.nice_time(lead.call_time), "Lead": lead.name, "Score": ui.score_label(lead),
          "Result": ui.OUTCOME_LABELS[lead.outcome]} for lead in history],
        hide_index=True, on_select="rerun", selection_mode="single-row", key="history_table",
        alt="Past calls with each lead's score and the result of the call",
    )
    if table.selection.rows:
        chosen = history[table.selection.rows[0]]
        if st.button(f"Open {chosen.name}'s file", key="history_open", icon=":material/person:"):
            ui.open_lead(chosen.id, "Brief")
