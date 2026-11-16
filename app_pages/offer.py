"""Page 4: view and edit the offer file (offer.json) that the AI answers from."""

import streamlit as st

import storage
from models import Offer

offer = storage.load_offer()

st.caption(
    "The AI may only answer the lead's questions from this file. If the answer is not here, "
    f"it says {offer.closer_name} will cover it on the call. Change the file and the AI's answers change."
)

left, right = st.columns(2)

with left, st.form("offer_form"):
    business_name = st.text_input("Business name", offer.business_name)
    closer_name = st.text_input("Closer name", offer.closer_name)
    offer_name = st.text_input("Offer name", offer.offer_name)
    who_it_is_for = st.text_input("Who it is for", offer.who_it_is_for)
    included = st.text_area("What is included (one item per line)", "\n".join(offer.included), height=140)
    price = st.text_input("Price", offer.price)
    length = st.text_input("Length", offer.length)
    if st.form_submit_button("Save offer", type="primary", icon=":material/save:"):
        storage.save_offer(
            Offer(
                business_name=business_name, closer_name=closer_name, offer_name=offer_name,
                who_it_is_for=who_it_is_for, price=price, length=length,
                included=[line.strip() for line in included.splitlines() if line.strip()],
            )
        )
        st.toast("Offer saved. New AI answers will use it.")
        st.rerun()

with right:
    st.markdown("**The file the AI reads: `offer.json`**")
    st.json(offer.model_dump())
