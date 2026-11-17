"""Closer and owner: everything about one lead (brief, score, chat log, and the call result)."""

import streamlit as st

import metrics
import storage
import ui

offer = storage.load_offer()
leads = [lead for lead in storage.list_leads() if metrics.has_started(lead)]
if not leads:
    st.info("No lead has chatted yet. Leads appear here after they send their first message.")
    st.stop()

# ----- Choose the lead (the dashboards jump here with one already chosen) -----
ids = [lead.id for lead in leads]
if st.session_state.get("selected_lead") not in ids:
    st.session_state.selected_lead = ids[0]
names = {lead.id: f"{lead.name} · {ui.nice_time(lead.call_time)} · {ui.score_label(lead)}" for lead in leads}
lead_id = st.selectbox("Lead", ids, format_func=names.get, key="selected_lead")
lead = next(lead for lead in leads if lead.id == lead_id)

with st.container(horizontal=True):
    st.badge(ui.nice_time(lead.call_time), icon=":material/event:", color="blue")
    st.badge(ui.OUTCOME_LABELS[lead.outcome], color="green" if lead.outcome == "closed" else "gray")
    if lead.is_sample:
        st.badge("Sample lead (invented)", icon=":material/info:", color="orange")

# ----- The result of the call (only for leads who have a call) -----
if lead.call_time:
    options = list(ui.OUTCOME_LABELS)
    chosen = st.segmented_control("Result of the call", options, format_func=ui.OUTCOME_LABELS.get,
                                  default=lead.outcome, key=f"outcome_{lead.id}")
    if chosen and chosen != lead.outcome:
        lead.outcome = chosen
        storage.save_lead(lead)
        st.rerun()

# ----- If the AI has not produced the score and brief yet, do it here -----
if lead.chat_done and (lead.score is None or lead.brief is None):
    st.warning("The score and brief have not been generated for this lead yet.")
    clicked = st.button("Generate now", key="generate_button", type="primary", icon=":material/bolt:")
    if clicked or st.session_state.pop("retry_generate", False):
        if ui.run_ai_step("AI is thinking: scoring the chat and writing the brief…",
                          lambda: ui.generate_missing(lead, offer), "retry_generate"):
            st.rerun()

# ----- Brief, score or chat log -----
if st.session_state.get("lead_view") is None:
    st.session_state.lead_view = "Brief"
view = st.segmented_control("Show", ["Brief", "Score", "Chat log"], key="lead_view", label_visibility="collapsed")
if view == "Chat log" or not lead.chat_done:
    if not lead.chat_done:
        st.info("This lead left before finishing the chat, so there is no score, brief or call.")
    ui.show_chat(lead.messages)
elif lead.score is None or lead.brief is None:
    st.info("Nothing to show yet. Generate the score and brief above.")
elif view == "Score":
    ui.show_score_header(lead.score)
    st.caption("Six dimensions, 0 to 5 each. The total is the sum out of 30, shown as a number out of 100.")
    ui.show_score_cards(lead.score)
else:
    ui.show_brief(lead, offer)
