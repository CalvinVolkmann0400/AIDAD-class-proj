"""The only page a lead ever sees: a short welcome, the chat with the AI, then picking a call time."""

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

# ----- The top of the page: the brand on the left, the presenter's demo switch on the right -----
brand_side, demo_side = st.columns([3, 2], vertical_alignment="center")
with brand_side:
    ui.eyebrow(f"Before your call with {offer.closer_name}")
with demo_side:
    ui.demo_switch("lead")  # for demos only; a real lead would not get this
st.title(offer.business_name)
ui.practice_banner()

# ----- Step 1: a new visitor. Count the click, ask their name, then start the chat. -----
if lead is None:
    if not st.session_state.get("click_counted"):
        storage.add_click()  # the top of the owner's funnel: somebody opened the link
        st.session_state.click_counted = True
    st.write(f"Our AI assistant has a few short questions so {offer.closer_name} can prepare. "
             "It takes about three minutes, and then you pick a time for your call.")
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
            st.rerun()
    st.stop()

st.query_params["lead"] = lead.token  # so refreshing the page keeps the same chat

# ----- Step 2: the chat, inside the rounded chat card. -----
card = st.container(key="chat_card")
bubbles = card.container()  # created first, so the messages sit above the reply box
text = None
if not lead.chat_done:
    text = card.chat_input("Type your reply", key="lead_reply", submit_mode="disable")
if text:
    lead.messages.append(Message(role="lead", text=text))
    storage.save_lead(lead)
    st.session_state.retry_chat = True  # tells the code below to ask the AI for a reply

with bubbles:
    ui.show_chat(lead.messages)
    waiting_for_ai = lead.messages[-1].role == "lead"
    if waiting_for_ai and st.session_state.pop("retry_chat", False):
        turn = ui.run_ai_step("AI is thinking…", lambda: engine.next_chat_turn(offer, lead.messages), "retry_chat")
        if turn:
            lead.messages.append(Message(role="ai", text=turn.reply))
            lead.chat_done = turn.done
            storage.save_lead(lead)
            if turn.done:
                try:  # prepare the score and brief for the closer; the lead never sees them
                    with st.spinner("Saving your answers…"):
                        ui.generate_missing(lead, offer)
                except llm.AIError:
                    pass  # if the AI fails here, the closer gets a "Generate now" button instead
            st.rerun()  # redraw the page with the new message in place
    elif waiting_for_ai:
        st.warning("The assistant has not replied to your last message yet.")
        st.button("Get the reply", icon=":material/refresh:", on_click=ui.ask_for_retry, args=("retry_chat",))

# ----- Step 3: the chat is finished. The lead picks their own call time. -----
if lead.chat_done and not lead.call_time:
    st.subheader("Pick a time for your call")
    slots = storage.free_slots(storage.list_leads(), date.today())
    day = st.pills("Day", list(slots), key="call_day", default=next(iter(slots)),
                   format_func=lambda d: date.fromisoformat(d).strftime("%a %d %b"))
    if day:
        time = st.pills("Time", slots[day], key=f"call_time_{day}")
        if st.button("Confirm my call", key="confirm_call", type="primary", disabled=not time):
            chosen = f"{day} {time}"
            if chosen in {other.call_time for other in storage.list_leads()}:
                st.warning("Someone just took that time. Please pick another.")
            else:
                lead.call_time = chosen
                storage.save_lead(lead)
                st.rerun()
elif lead.chat_done:
    first_name = lead.name.split()[0]
    st.success(f"You're all set, {first_name}. Your call with {offer.closer_name} is confirmed for "
               f"{ui.nice_time(lead.call_time)}.", icon=":material/event_available:")
    # For demos only: lets the presenter play another lead without leaving this page.
    st.button("Start another lead chat (demo)", key="another_lead", type="tertiary", icon=":material/restart_alt:",
              on_click=ui.set_role, args=("lead",))

st.caption("Powered by")
ui.wordmark()
