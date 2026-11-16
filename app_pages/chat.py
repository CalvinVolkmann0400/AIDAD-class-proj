"""Page 1: the lead chats with the AI assistant."""

import streamlit as st

import engine
import storage
import ui
from models import Message

run = st.session_state.run
offer = storage.load_offer()
locked = st.session_state.is_replay or st.session_state.chat_done

st.caption(
    f"This is what the lead ({run.lead_name}) sees. The AI chooses each next question from what was "
    "said so far, and answers the lead's questions only from the offer file."
)

# The box at the bottom where the lead's reply is typed.
text = st.chat_input("Type the lead's reply", key="lead_reply", disabled=locked, submit_mode="disable")
if text:
    run.messages.append(Message(role="lead", text=text))
    st.session_state.retry_chat = True  # tells the code below to ask the AI for a reply

for message in run.messages:
    with st.chat_message("assistant" if message.role == "ai" else "user"):
        ui.plain(message.text)

waiting_for_ai = run.messages[-1].role == "lead"
if waiting_for_ai and st.session_state.pop("retry_chat", False):
    with st.chat_message("assistant"):
        turn = ui.run_ai_step("AI is thinking…", lambda: engine.next_chat_turn(offer, run.messages), "retry_chat")
    if turn:
        run.messages.append(Message(role="ai", text=turn.reply))
        st.session_state.chat_done = turn.done
        ui.save_current_run()
        st.rerun()  # redraw the page with the new message in place
elif waiting_for_ai:
    st.warning("The AI has not replied to the last message yet.")
    st.button("Get the AI's reply", icon=":material/refresh:", on_click=ui.ask_for_retry, args=("retry_chat",))

if st.session_state.chat_done:
    st.success("The chat is finished. Next: see how the AI scores this lead.", icon=":material/check_circle:")
    st.page_link("app_pages/score.py", label="Go to the score", icon=":material/speed:")
