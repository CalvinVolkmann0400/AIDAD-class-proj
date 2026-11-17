"""Owner: the lead chat link, the AI connection, and the sample data."""

from datetime import date
from urllib.parse import urlparse

import streamlit as st

import llm
import storage

leads = storage.list_leads()
samples = sum(lead.is_sample for lead in leads)

# ----- The link that is sent to leads -----
st.subheader("Lead chat link")
st.write("Send this link to a lead. They see only the chat. Every time it is opened, "
         "one click is counted at the top of the funnel.")
address = urlparse(st.context.url)  # where this app is running right now
link = f"{address.scheme}://{address.netloc}/?lead=new"
st.code(link, language=None)
st.link_button("Open the lead chat in a new tab", link, icon=":material/open_in_new:")
st.caption("The address starts with localhost because the app runs on this computer only. "
           "A hosted version would have a public address here.")

# ----- The AI -----
st.subheader("AI connection")
if llm.has_api_key():
    st.write(f"Live AI. Main model `{llm.MODEL}`, fallback `{llm.FALLBACK_MODEL}`. "
             f"Each call gets {llm.TIMEOUT_SECONDS} seconds and up to {llm.MAX_ATTEMPTS} tries.")
    if st.button("Test the AI connection", key="test_ai", icon=":material/wifi:"):
        with st.spinner("Contacting the AI…"):
            result = llm.test_connection()
        (st.success if result == "success" else st.error)(f"Connection test: {result}")
else:
    st.warning("No API key found, so the app is in practice mode (fixed scripted answers). "
               "Add GEMINI_API_KEY to the .env file and restart the app.")

# ----- Sample data -----
st.subheader("Sample data")
st.write(f"The database holds **{len(leads) - samples} real leads** and **{samples} invented sample leads**, "
         f"and **{storage.count_clicks()} link clicks** in total. Sample call dates are re-set around today's "
         "date each day.")
with st.form("reset_form", border=False):
    sure = st.checkbox("I understand this deletes every lead and click, including real ones")
    if st.form_submit_button("Reset to the sample data", icon=":material/restart_alt:") and sure:
        storage.reset_to_sample_data(date.today())
        st.toast("Reset done. The dashboards now show only the sample data.")
        st.rerun()

# ----- What is not here yet -----
st.subheader("Not built yet")
st.caption("Real sign-in with passwords, a connection to a real calendar, emailing the brief, "
           "and more than one closer or offer. See docs/remaining-tasks.md.")
