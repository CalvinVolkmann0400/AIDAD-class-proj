"""The entry point of the app. Start it with:  uv run streamlit run app.py

This file sets up what every page shares: the current "run" (one conversation
with its score and brief), the sidebar buttons, and the menu of four pages.
The pages themselves live in the app_pages/ folder, one small file each.
"""

from datetime import datetime

import streamlit as st

import engine
import llm
import storage
import ui
from models import SavedRun

LEAD_NAME = "Sam Rivera"  # an invented lead; only made-up people are sent to the AI

st.set_page_config(page_title="Sunsettr class project", page_icon=":material/wb_twilight:", layout="wide")


def start_new_conversation():
    """Begin a fresh run that holds only the AI's opening message."""
    offer = storage.load_offer()
    st.session_state.run = SavedRun(
        lead_name=LEAD_NAME,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        source=llm.ai_source(),
        messages=[engine.opening_message(offer, LEAD_NAME)],
    )
    st.session_state.run_id = None  # its row in the database (none until first save)
    st.session_state.chat_done = False
    st.session_state.is_replay = False


def load_replay():
    """Load the saved real-AI run from the replay file, so nothing has to be generated live."""
    saved = storage.load_replay()
    if saved is None:
        return
    st.session_state.run = saved
    st.session_state.run_id = None
    st.session_state.chat_done = True
    st.session_state.is_replay = True


# st.session_state is Streamlit's memory between clicks. Set it up once per browser tab.
if "run" not in st.session_state:
    start_new_conversation()
    if st.query_params.get("replay") == "1":  # a link ending in ?replay=1 opens the saved run
        load_replay()

page = st.navigation(
    [
        st.Page("app_pages/chat.py", title="Lead chat", icon=":material/chat:", default=True,
                help="The lead chats with the AI assistant, which chooses each question itself."),
        st.Page("app_pages/score.py", title="Score", icon=":material/speed:",
                help="The AI scores the finished chat on six dimensions, with quotes as evidence."),
        st.Page("app_pages/brief.py", title="Closer's brief", icon=":material/description:",
                help="The one-page brief the closer reads before the call, with the score beside it."),
        st.Page("app_pages/offer.py", title="Offer file", icon=":material/sell:",
                help="The offer details the AI is allowed to answer from. Edit and save them here."),
    ]
)

with st.sidebar:
    st.caption("Sunsettr · OIM 3641 class project. All people and businesses are invented.")
    if st.session_state.is_replay:
        st.badge("Saved run (replay)", icon=":material/history:", color="blue")
    elif llm.has_api_key():
        st.badge(f"Live AI: {llm.MODEL}", icon=":material/bolt:", color="green")
    else:
        st.badge("Practice mode (no API key)", icon=":material/science:", color="orange")

    st.button("New conversation", key="new_button", icon=":material/add:", on_click=start_new_conversation, width="stretch")
    st.button("Replay saved run", key="replay_button", icon=":material/history:", on_click=load_replay, width="stretch",
              disabled=not storage.REPLAY_FILE.exists(),
              help="Loads a conversation, score and brief the real AI produced earlier.")
    if llm.has_api_key() and st.button("Test the AI connection", icon=":material/wifi:", width="stretch"):
        with st.spinner("Contacting the AI…"):
            result = llm.test_connection()
        (st.success if result == "success" else st.error)(f"Connection test: {result}")

st.title(page.title)
ui.show_mode_banner()
page.run()
