"""Streamlit webapp"""

import pandas as pd
import streamlit as st
import ev_models


def build_page():
    st.title("EV Trip Planner")
    with st.container(border=True):
        st.segmented_control("EV model", ["Tesla Y", ], selection_mode="single", default=["Tesla Y"], key="model")
        with st.popover("Set properties"):
            global c_rates_df
            if st.session_state["model"] == "Tesla Y":
                model = ev_models.tesla_y_long()
            else:
                # st.title("fail")
                # Exception("Model not yet implemented")
                pass
            if st.session_state["model"] is None:
                st.number_input("Battery capacity", 1, 250, 50, key="capa")
                c_rates_df = st.data_editor(pd.DataFrame([[10 * i, 15 - i] for i in range(11)], columns=["Percentage", "Rate"]), num_rows="dynamic", hide_index=True)
            else:
                st.number_input("Battery capacity", 1, 250, model.battery.capa, key="capa")
                c_rates_df = st.data_editor(pd.DataFrame([[i, model.battery.charging_rate(i)] for i in range(10, 91, 10)], columns=["Percentage", "Rate"]), num_rows="dynamic", hide_index=True)
    st.slider("Trip distance", 0, 3000, 100, 1, key="distance")
    st.slider("Start battery state (%)", 0, 100, 90, 1, key="start_state")
    st.slider("End battery state (%)", 0, 100, 10, 1, key="end_state")
    _left, _right = st.columns(2, gap="small", vertical_alignment="center", border=True)
    _left.slider("Travel speed", 30, 180, 130, 1, key="speed")
    _right.number_input("Number of breaks", 0, 10, 1, 1, key="n_breaks")
    _right.slider("Break duration", 3, 60, 15, 1, key="break_duration")
    _right.badge(f"Traveling speed {model.max_trip_speed(st.session_state["distance"], st.session_state["n_breaks"], st.session_state["break_duration"], st.session_state["end_state"], st.session_state["start_state"]):.0f} km/h", icon="🚀", color="green")
    _left.badge("Breaks (min):  " + ", ".join([f"{i + 1}.  {t:.0f}" for i, t in enumerate(model.min_break_duration(st.session_state["distance"], st.session_state["speed"], st.session_state["end_state"], st.session_state["start_state"]))]), icon="⏳", color="orange")


if __name__ == "__main__":
    build_page()
