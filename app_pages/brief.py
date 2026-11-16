"""Page 3: the one-page brief for the closer, with the score beside it."""

import streamlit as st

import engine
import storage
import ui

run = st.session_state.run
offer = storage.load_offer()

if run.score is None:
    st.info("Score the conversation first. The brief is written from the conversation and the score.")
    st.stop()

if run.brief is None:
    st.write(f"The AI writes a one-page brief for {offer.closer_name} from the conversation and the score.")
    clicked = st.button("Write the closer's brief", key="brief_button", type="primary", icon=":material/description:")
    if clicked or st.session_state.pop("retry_brief", False):
        result = ui.run_ai_step(
            "AI is thinking: writing the brief…",
            lambda: engine.write_brief(offer, run.messages, run.score),
            "retry_brief",
        )
        if result:
            run.brief = result
            ui.save_current_run()
            st.rerun()
    st.stop()

brief = run.brief
left, right = st.columns([2, 1])

with left.container(border=True):
    st.subheader(f"Pre-call brief: {run.lead_name}")
    st.caption(f"For {offer.closer_name} · {offer.business_name} · {offer.offer_name}")
    st.markdown("**Summary**")
    for line in brief.summary_lines:
        ui.plain(f"- {line}")
    st.markdown("**Key quotes from the lead**")
    for quote in brief.key_quotes:
        ui.plain(f"> “{quote}”")
    st.markdown("**Still unknown (ask on the call)**")
    for item in brief.unknowns:
        ui.plain(f"- {item}")
    st.markdown("**Suggested opening line**")
    st.info(brief.opening_line.replace("$", "\\$"), icon=":material/record_voice_over:")

with right.container(border=True):
    ui.show_score_compact(run.score)

# Lets a good real-AI run be kept as the demo's replay file.
if not st.session_state.is_replay and run.source != "practice":
    if st.button("Save this run as the replay file", key="save_replay_button", icon=":material/save:",
                 help="Replaces replay/saved_run.json, which the Replay button loads."):
        storage.save_replay(run)
        st.toast("Saved. The Replay button now loads this run.")
