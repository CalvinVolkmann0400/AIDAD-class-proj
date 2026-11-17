"""The entry point of the app. Start it with:  uv run streamlit run app.py

This file decides WHO is using the app and shows only that person's pages:
  lead    only the chat (reached through the lead chat link, ...?lead=new)
  closer  dashboard, call calendar, lead files
  owner   funnel, all leads and chat logs, offer file, settings
The pages themselves live in the app_pages/ folder, one small file each.
"""

from datetime import date

import streamlit as st

import llm
import storage
import ui

# st.session_state is Streamlit's memory between clicks. Work out the role once per browser tab.
# A link ending in ?lead=new (or ?lead=<a lead's code>) opens the lead's chat directly.
if "role" not in st.session_state:
    ui.set_role(None)
    if st.query_params.get("lead"):
        ui.set_role("lead")
        st.session_state.lead_token = st.query_params["lead"]
    elif st.query_params.get("role") in ("closer", "owner"):
        ui.set_role(st.query_params["role"])
role = st.session_state.role

# The lead gets a narrow, centred chat; everyone else gets the full width for dashboards.
st.set_page_config(page_title="Sunsettr class project", page_icon=":material/wb_twilight:",
                   layout="centered" if role == "lead" else "wide")

# Make sure the invented sample leads are loaded, with call dates placed around today.
storage.ensure_sample_data(date.today())

# Each role gets its own list of pages. A page that is not in the list cannot be opened.
lead_file = st.Page("app_pages/lead_file.py", title="Lead file", icon=":material/person:",
                    help="One lead's brief, score and full chat log, and the result of their call.")
PAGES = {
    None: [st.Page("app_pages/start.py", title="Start")],
    "lead": [st.Page("app_pages/lead_chat.py", title="Chat")],
    "closer": [
        st.Page("app_pages/closer_dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True,
                help="The closer's numbers, upcoming calls with links to each brief, and leads needing attention."),
        st.Page("app_pages/closer_calendar.py", title="Call calendar", icon=":material/calendar_month:",
                help="Every upcoming call by day, the call history, and where call results are recorded."),
        lead_file,
    ],
    "owner": [
        st.Page("app_pages/owner_funnel.py", title="Funnel", icon=":material/filter_alt:", default=True,
                help="Each level of the sales funnel from link clicks to closed deals, with the biggest leak marked."),
        st.Page("app_pages/owner_leads.py", title="Leads and chat logs", icon=":material/group:",
                help="Every lead in one table. Open any of them to read the chat, score and brief."),
        lead_file,
        st.Page("app_pages/offer.py", title="Offer file", icon=":material/sell:",
                help="The offer details the AI is allowed to answer from. Edit and save them here."),
        st.Page("app_pages/settings.py", title="Settings", icon=":material/settings:",
                help="The lead chat link, the AI connection, and the sample data."),
    ],
}

# The lead and the start screen get no menu at all; the closer and the owner get a sidebar.
has_menu = role in ("closer", "owner")
page = st.navigation(PAGES[role], position="sidebar" if has_menu else "hidden")

if has_menu:
    offer = storage.load_offer()
    with st.sidebar:
        who = f"{offer.closer_name} · closer" if role == "closer" else f"{offer.business_name} · owner"
        st.caption(f"Signed in as **{who}** (demo access, no password). All people and businesses are invented.")
        if llm.has_api_key():
            st.badge(f"Live AI: {llm.MODEL}", icon=":material/bolt:", color="green")
        else:
            st.badge("Practice mode (no API key)", icon=":material/science:", color="orange")
        st.button("Switch role", key="switch_role", icon=":material/swap_horiz:", width="stretch",
                  on_click=ui.set_role, args=(None,))
    st.title(page.title)

page.run()
