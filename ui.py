"""Small on-screen helpers shared by the pages."""

from datetime import datetime

import streamlit as st

import engine
import llm
import storage
from models import Lead, Message, Offer, ScoreResult

OUTCOME_LABELS = {"pending": "No result yet", "closed": "Showed and closed",
                  "not_closed": "Showed, did not close", "no_show": "No-show"}


# ---------- Small formatting helpers ----------

def plain(text: str) -> None:
    """Show text as written. (Streamlit treats $...$ as maths, so dollar signs are escaped.)"""
    st.markdown(text.replace("$", "\\$"))


def percent(rate: float | None) -> str:
    """0.75 becomes "75%"; nothing to measure yet becomes a dash."""
    return "–" if rate is None else f"{rate:.0%}"


def nice_time(call_time: str) -> str:
    """ "2026-11-17 10:00" becomes "Tue 17 Nov, 10:00"."""
    if not call_time:
        return "No call booked"
    return datetime.strptime(call_time, "%Y-%m-%d %H:%M").strftime("%a %d %b, %H:%M")


def score_label(lead: Lead) -> str:
    """One short line describing a lead's score."""
    if lead.score is None:
        return "Not scored yet" if lead.chat_done else "Chat not finished"
    if not lead.score.enough_information:
        return "Not enough information"
    return f"{engine.total_score(lead.score)} · {engine.band(lead.score)}"


# ---------- Banners ----------

def practice_banner() -> None:
    """Say clearly when answers come from the fixed script instead of the real AI."""
    if not llm.has_api_key():
        st.warning("No API key was found, so new AI answers come from a fixed script, not from a real AI.",
                   title="Practice mode", icon=":material/science:")


def sample_note(leads: list[Lead]) -> None:
    """Say clearly when the numbers on a dashboard include the invented sample leads."""
    samples = sum(lead.is_sample for lead in leads)
    if samples:
        st.caption(f":material/info: Includes sample data: {samples} invented leads with invented call results, "
                   "so the dashboards have something to show. Their chats, scores and briefs came from the real AI.")


# ---------- Running AI steps safely ----------

def ask_for_retry(flag: str) -> None:
    """Remember that the user pressed Try again, so the page reruns that AI step."""
    st.session_state[flag] = True


def run_ai_step(label: str, work, retry_flag: str):
    """Run one AI task with an "AI is thinking" spinner.

    Returns the result, or None if the AI failed. On failure it shows an honest
    error and a Try again button. It never crashes and never invents content.
    """
    try:
        with st.spinner(label, show_time=True):
            return work()
    except llm.AIError as error:
        st.error(str(error), title="The AI could not finish this step", icon=":material/error:")
        st.button("Try again", key=f"button_{retry_flag}", icon=":material/refresh:",
                  on_click=ask_for_retry, args=(retry_flag,))
        return None


def generate_missing(lead: Lead, offer: Offer) -> bool:
    """Ask the AI for the score and the brief if this lead does not have them yet, and save them."""
    if lead.score is None:
        lead.score = engine.score_conversation(offer, lead.messages)
        storage.save_lead(lead)
    if lead.brief is None:
        lead.brief = engine.write_brief(offer, lead.messages, lead.score)
        storage.save_lead(lead)
    return True


# ---------- Moving between pages ----------

def set_role(role: str | None) -> None:
    """Choose who is using the app: "lead", "closer", "owner", or None for the start screen."""
    st.session_state.role = role
    st.session_state.lead_token = "new"
    st.session_state.pop("click_counted", None)


def open_lead(lead_id: int, view: str = "Brief") -> None:
    """Jump to the lead file page for one lead, showing the brief, the score or the chat log."""
    st.session_state.selected_lead = lead_id
    st.session_state.lead_view = view
    st.switch_page("app_pages/lead_file.py")


# ---------- Showing a lead's chat, score and brief ----------

def show_chat(messages: list[Message]) -> None:
    for message in messages:
        with st.chat_message("assistant" if message.role == "ai" else "user"):
            plain(message.text)


def show_score_header(score: ScoreResult) -> None:
    """The big number, the band, and a warning when the lead said too little."""
    label = engine.band(score)
    total = engine.total_score(score)
    if not score.enough_information:
        st.metric("Lead score", "No score")
        st.badge(label, icon=":material/help:", color="gray")
        st.warning("The lead said too little to score fairly, so no total is shown.")
        return
    st.metric("Lead score", f"{total} / 100")
    color = "green" if total >= 80 else "blue" if total >= 60 else "orange" if total >= 40 else "gray"
    st.badge(label, color=color)


def show_score_cards(score: ScoreResult) -> None:
    """Six cards in two rows of three: score, reason and checked quote for each dimension."""
    for row in (score.dimensions[:3], score.dimensions[3:]):
        for column, dimension in zip(st.columns(3), row):
            with column.container(border=True, height="stretch"):
                st.markdown(f"**{dimension.name.capitalize()}** · {dimension.score}/5")
                st.progress(dimension.score / 5)
                plain(dimension.reason)
                if dimension.quote_verified:
                    plain(f"> “{dimension.quote}”")
                    st.caption(":material/check_circle: Quote found in the lead's messages")
                elif dimension.score > 0:
                    st.caption(":material/warning: No verified quote. The AI's quote was not in the lead's "
                               "messages, so it was removed.")
                else:
                    st.caption("No evidence in the conversation.")


def show_score_compact(score: ScoreResult) -> None:
    """The score in a narrow column: header plus one bar per dimension."""
    show_score_header(score)
    for dimension in score.dimensions:
        st.progress(dimension.score / 5, text=f"{dimension.name.capitalize()} · {dimension.score}/5")


def show_brief(lead: Lead, offer: Offer) -> None:
    """The one-page brief on the left and the score beside it."""
    left, right = st.columns([2, 1])
    with left.container(border=True):
        st.subheader(f"Pre-call brief: {lead.name}")
        st.caption(f"For {offer.closer_name} · {offer.business_name} · {offer.offer_name}")
        st.markdown("**Summary**")
        for line in lead.brief.summary_lines:
            plain(f"- {line}")
        st.markdown("**Key quotes from the lead**")
        for quote in lead.brief.key_quotes:
            plain(f"> “{quote}”")
        st.markdown("**Still unknown (ask on the call)**")
        for item in lead.brief.unknowns:
            plain(f"- {item}")
        st.markdown("**Suggested opening line**")
        st.info(lead.brief.opening_line.replace("$", "\\$"), icon=":material/record_voice_over:")
    with right.container(border=True):
        show_score_compact(lead.score)
