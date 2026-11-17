"""Owner: every lead in one table, with a way into each lead's chat log, score and brief."""

import streamlit as st

import metrics
import storage
import ui

leads = [lead for lead in storage.list_leads() if metrics.has_started(lead)]
ui.sample_note(leads)

if not leads:
    st.info("No lead has chatted yet.")
    st.stop()

only = st.segmented_control("Show", ["All", "Finished the chat", "Left mid-chat"], default="All", key="leads_filter")
if only == "Finished the chat":
    leads = [lead for lead in leads if lead.chat_done]
elif only == "Left mid-chat":
    leads = [lead for lead in leads if not lead.chat_done]

st.caption("Click a row, then open that lead's file.")
table = st.dataframe(
    [{"Lead": lead.name,
      "Opened the chat": lead.created_at[:10],
      "Chat": "Finished" if lead.chat_done else "Left mid-chat",
      "Messages from lead": sum(message.role == "lead" for message in lead.messages),
      "Score": ui.score_label(lead),
      "Call": ui.nice_time(lead.call_time),
      "Result": ui.OUTCOME_LABELS[lead.outcome] if lead.call_time else "–",
      "Sample": "yes" if lead.is_sample else "no"} for lead in leads],
    hide_index=True, on_select="rerun", selection_mode="single-row", key="leads_table",
    alt="All leads with chat status, score, call time and call result",
)
if table.selection.rows:
    chosen = leads[table.selection.rows[0]]
    with st.container(horizontal=True):
        if st.button(f"Read {chosen.name}'s chat log", key="leads_chat", icon=":material/chat:"):
            ui.open_lead(chosen.id, "Chat log")
        if chosen.chat_done and st.button("Brief and score", key="leads_brief", icon=":material/description:"):
            ui.open_lead(chosen.id, "Brief")
