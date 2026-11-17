"""Small on-screen helpers shared by the pages."""

import streamlit as st

import engine
import llm
import storage
from models import ScoreResult


def plain(text: str) -> None:
    """Show text as written. (Streamlit treats $...$ as maths, so dollar signs are escaped.)"""
    st.markdown(text.replace("$", "\\$"))


def show_mode_banner() -> None:
    """Say clearly, at the top of every page, when the content is not live real-AI output."""
    run = st.session_state.run
    if st.session_state.is_replay:
        st.info(
            f"A real conversation, score and brief that Google Gemini (main model: {run.source}) produced "
            f"earlier, on {run.created_at}. Nothing on this screen is being generated right now.",
            title="Saved run (replay)", icon=":material/history:",
        )
    elif run.source == "practice":
        st.warning(
            "No API key was found, so the answers come from a fixed script, not from a real AI.",
            title="Practice mode", icon=":material/science:",
        )


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


def save_current_run() -> None:
    """Save the current run to the SQLite database (replays are already saved, so skip them)."""
    if not st.session_state.is_replay:
        st.session_state.run_id = storage.save_run(st.session_state.run, st.session_state.run_id)


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


def show_score_compact(score: ScoreResult) -> None:
    """The score in a narrow column: header plus one bar per dimension."""
    show_score_header(score)
    for dimension in score.dimensions:
        st.progress(dimension.score / 5, text=f"{dimension.name.capitalize()} · {dimension.score}/5")
