"""The start screen: choose which of the three people you are."""

import streamlit as st

import storage
import ui

offer = storage.load_offer()

st.title("Sunsettr")
st.write("A lead chats with an AI, the AI scores the lead, and the closer gets a brief before the call. "
         "Three people use it, and each one sees something different.")

lead, closer, owner = st.columns(3)

with lead.container(border=True, height="stretch"):
    st.subheader(":material/chat: Lead")
    st.write("Someone thinking of buying. They get a link and see **only the chat**: no menu, no score, no brief.")
    st.button("Open the lead's chat link", key="role_lead", type="primary", on_click=ui.set_role, args=("lead",))

with closer.container(border=True, height="stretch"):
    st.subheader(":material/support_agent: Closer")
    st.write(f"{offer.closer_name}, who takes the sales calls. Sees their numbers, upcoming calls with each "
             "brief, the call calendar and every lead's file.")
    st.button(f"Continue as {offer.closer_name}", key="role_closer", type="primary",
              on_click=ui.set_role, args=("closer",))

with owner.container(border=True, height="stretch"):
    st.subheader(":material/storefront: Owner")
    st.write(f"The owner of {offer.business_name}. Sees the whole funnel from link clicks to closed deals, "
             "all chat logs, the offer file and the settings.")
    st.button("Continue as the owner", key="role_owner", type="primary", on_click=ui.set_role, args=("owner",))

st.caption("Demo access: there is no real sign-in yet, so anyone can pick a role here. In a real version the "
           "closer and the owner would log in, and a lead would only ever receive the chat link.")
