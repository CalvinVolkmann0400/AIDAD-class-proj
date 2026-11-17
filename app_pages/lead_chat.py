"""The only page a lead ever sees: a short welcome, then the chat with the AI assistant."""

import secrets
from datetime import date, datetime

import streamlit as st

import engine
import llm
import storage
import ui
from models import Lead, Message

offer = storage.load_offer()
lead = storage.get_lead_by_token(st.session_state.lead_token)

st.title(offer.business_name)
ui.practice_banner()

# ----- Step 1: a new visitor. Count the click, ask their name, then start the chat. -----
if lead is None:
    if not st.session_state.get("click_counted"):
        storage.add_click()  # the top of the owner's funnel: somebody opened the link
        st.session_state.click_counted = True
    st.write(f"Before your call with {offer.closer_name}, our AI assistant has a few short questions. "
             "It takes about three minutes.")
    with st.form("welcome", width=420):
        name = st.text_input("Your first and last name", max_chars=60)
        if st.form_submit_button("Start the chat", type="primary") and name.strip():
            lead = storage.save_lead(
                Lead(
                    token=secrets.token_urlsafe(6),  # a random code that becomes this lead's personal link
                    name=name.strip(), source=llm.ai_source(), call_time="",
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    messages=[engine.opening_message(offer, name.strip())],
                )
            )
            st.session_state.lead_token = lead.token
            st.query_params["lead"] = lead.token  # so refreshing the page keeps the same chat
            st.rerun()
    st.stop()

# ----- Step 2: the chat. -----
text = st.chat_input("Type your reply", key="lead_reply", disabled=lead.chat_done, submit_mode="disable")
if text:
    lead.messages.append(Message(role="lead", text=text))
    storage.save_lead(lead)
    st.session_state.retry_chat = True  # tells the code below to ask the AI for a reply

ui.show_chat(lead.messages)

waiting_for_ai = lead.messages[-1].role == "lead"
if waiting_for_ai and st.session_state.pop("retry_chat", False):
    with st.chat_message("assistant"):
        turn = ui.run_ai_step("AI is thinking…", lambda: engine.next_chat_turn(offer, lead.messages), "retry_chat")
    if turn:
        lead.messages.append(Message(role="ai", text=turn.reply))
        if turn.done:  # the chat is over: book the call
            lead.chat_done = True
            lead.call_time = storage.next_free_slot(storage.list_leads(), date.today())
        storage.save_lead(lead)
        st.rerun()  # redraw the page with the new message in place
elif waiting_for_ai:
    st.warning("The assistant has not replied to your last message yet.")
    st.button("Get the reply", icon=":material/refresh:", on_click=ui.ask_for_retry, args=("retry_chat",))

# ----- Step 3: finished. Confirm the call, then prepare the score and brief for the closer. -----
if lead.chat_done:
    first_name = lead.name.split()[0]
    st.success(f"You're all set, {first_name}. Your call with {offer.closer_name} is confirmed for "
               f"{ui.nice_time(lead.call_time)}.", icon=":material/event_available:")
    if (lead.score is None or lead.brief is None) and not st.session_state.get("wrap_up_tried"):
        st.session_state.wrap_up_tried = True
        try:  # the lead never sees the score or brief; if the AI fails here, the closer can generate them
            with st.spinner("Saving your answers…"):
                ui.generate_missing(lead, offer)
        except llm.AIError:
            pass
