"""Owner: the whole sales funnel, level by level, so the biggest leak is easy to see."""

import streamlit as st

import metrics
import storage
import ui

leads = storage.list_leads()
stages = metrics.funnel(leads, storage.count_clicks())
leak = metrics.biggest_leak(stages)
clicks, closed = stages[0].count, stages[-1].count
ui.sample_note(leads)

# ----- The headline numbers -----
with st.container(border=True):
    cells = st.columns(5)
    cells[0].metric("Link clicks", clicks)
    cells[1].metric("Chats finished", stages[2].count)
    cells[2].metric("Show rate", ui.percent(metrics.show_rate(leads)))
    cells[3].metric("Close rate", ui.percent(metrics.close_rate(leads)))
    cells[4].metric("Clicks that became sales", ui.percent(closed / clicks if clicks else None))

# ----- One row per level of the funnel -----
st.subheader("The funnel, level by level")
if leak:
    st.warning(f"**{leak.name}** is the biggest leak: only {ui.percent(leak.rate)} made it "
               f"({leak.count} of {leak.out_of} {leak.out_of_what}).", title="Biggest leak", icon=":material/water_drop:")
for number, stage in enumerate(stages, start=1):
    with st.container(border=True):
        name, bar, rate = st.columns([3, 5, 4], vertical_alignment="center")
        name.markdown(f"**{number}. {stage.name}**")
        name.markdown(f"### {stage.count}")
        bar.progress(stage.count / clicks if clicks else 0.0)  # bar length = share of all link clicks
        if number == 1:
            rate.caption("Everyone who opened the lead chat link.")
        else:
            lost = stage.out_of - stage.count
            rate.markdown(f"**{ui.percent(stage.rate)}** made it · {stage.count} of {stage.out_of} "
                          f"{stage.out_of_what} · {lost} lost")
            if stage.note:
                rate.caption(stage.note)
            if stage is leak:
                rate.badge("Biggest leak", icon=":material/water_drop:", color="red")

# ----- Does the AI's score predict anything? -----
st.subheader("Results by score band")
st.caption("If the score is useful, higher bands should show up and close more often. "
           "With this few calls it is an illustration, not proof.")
st.dataframe(
    [{"Score band": row["band"], "Leads": row["leads"], "Calls with a result": row["calls_held"],
      "Show rate": ui.percent(row["show_rate"]), "Close rate": ui.percent(row["close_rate"])}
     for row in metrics.rates_by_band(leads)],
    hide_index=True, alt="Show rate and close rate for each score band",
)
