"""Page 2: the AI scores the finished conversation."""

import streamlit as st

import engine
import storage
import ui

run = st.session_state.run

if not st.session_state.chat_done:
    st.info("Finish the chat first (or press Replay saved run in the sidebar). Then the AI can score it.")
    st.stop()

if run.score is None:
    st.write(
        "The AI reads the whole conversation and scores six dimensions from 0 to 5, each with a reason "
        "and a quote from the lead. The code then checks that every quote really appears in the chat."
    )
    clicked = st.button("Score this conversation", key="score_button", type="primary", icon=":material/speed:")
    if clicked or st.session_state.pop("retry_score", False):
        offer = storage.load_offer()
        result = ui.run_ai_step(
            "AI is thinking: scoring the conversation…",
            lambda: engine.score_conversation(offer, run.messages),
            "retry_score",
        )
        if result:
            run.score = result
            ui.save_current_run()
            st.rerun()
    st.stop()

ui.show_score_header(run.score)
st.caption("Six dimensions, 0 to 5 each. The total is the sum out of 30, shown as a number out of 100.")

# Six cards in two rows of three.
dimensions = run.score.dimensions
for row in (dimensions[:3], dimensions[3:]):
    for column, dimension in zip(st.columns(3), row):
        with column.container(border=True, height="stretch"):
            st.markdown(f"**{dimension.name.capitalize()}** · {dimension.score}/5")
            st.progress(dimension.score / 5)
            ui.plain(dimension.reason)
            if dimension.quote_verified:
                ui.plain(f"> “{dimension.quote}”")
                st.caption(":material/check_circle: Quote found in the lead's messages")
            elif dimension.score > 0:
                st.caption(":material/warning: No verified quote. The AI's quote was not in the lead's messages, so it was removed.")
            else:
                st.caption("No evidence in the conversation.")

st.page_link("app_pages/brief.py", label="Go to the closer's brief", icon=":material/description:")
