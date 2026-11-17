"""Closer: numbers at a glance, upcoming calls with links to each brief, and what needs attention."""

from datetime import date

import streamlit as st

import metrics
import storage
import ui

leads = storage.list_leads()
today = date.today()
numbers = metrics.closer_numbers(leads, today)
ui.sample_note(leads)

# ----- The closer's numbers, in one cluster -----
with st.container(border=True):
    cells = st.columns(5)
    cells[0].metric("Calls today", numbers["calls_today"])
    cells[1].metric("Calls in the next 7 days", numbers["calls_next_7_days"])
    cells[2].metric("Show rate", ui.percent(numbers["show_rate"]), help="Of calls with a recorded result, the share where the lead showed up.")
    cells[3].metric("Close rate", ui.percent(numbers["close_rate"]), help="Of leads who showed up, the share who bought.")
    average = numbers["average_upcoming_score"]
    cells[4].metric("Average score, upcoming", "–" if average is None else f"{average} / 100")

# ----- Upcoming calls, soonest first, each with links into the lead's file -----
st.subheader("Upcoming calls")
upcoming = metrics.upcoming_calls(leads, today)
if not upcoming:
    st.info("No upcoming calls. A call appears here when a lead finishes the chat.")
for lead in upcoming:
    with st.container(border=True):
        when, who, links = st.columns([2, 5, 4], vertical_alignment="center")
        when.markdown(f"**{ui.nice_time(lead.call_time)}**")
        if metrics.call_day(lead) == today:
            when.badge("Today", color="green")
        who.markdown(f"**{lead.name}** · {ui.score_label(lead)}")
        if lead.brief:
            who.caption(lead.brief.summary_lines[0].replace("$", "\\$"))
        with links.container(horizontal=True):
            if st.button("Brief", key=f"brief_{lead.id}", icon=":material/description:"):
                ui.open_lead(lead.id, "Brief")
            if st.button("Score", key=f"score_{lead.id}", icon=":material/speed:"):
                ui.open_lead(lead.id, "Score")
            if st.button("Chat log", key=f"chat_{lead.id}", icon=":material/chat:"):
                ui.open_lead(lead.id, "Chat log")

# ----- Anything the closer should not miss -----
st.subheader("Needs attention")
attention = metrics.needs_attention(leads, today)
if not attention:
    st.success("Nothing needs attention right now.", icon=":material/check_circle:")
for lead, reason in attention:
    with st.container(border=True):
        text, action = st.columns([7, 3], vertical_alignment="center")
        text.markdown(f"**{lead.name}** · {ui.nice_time(lead.call_time)}")
        text.caption(reason)
        if action.button("Open lead file", key=f"attention_{lead.id}", icon=":material/person:"):
            ui.open_lead(lead.id, "Brief")
