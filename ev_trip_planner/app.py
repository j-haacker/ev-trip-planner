"""Streamlit webapp"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import ev_models


def build_page():
    st.title("EV Trip Planner")
    st.badge("version 66", icon="✨", color="blue")
    with st.container(border=True):
        _c = st.tabs(["Select model", "Efficiency", "Charging"])
        _c[0].segmented_control(
            "EV model",
            [
                "Tesla Y",
            ],
            selection_mode="single",
            default=["Tesla Y"],
            key="model",
        )
        with _c[0].popover("Set properties"):
            global c_rates_df
            if st.session_state["model"] == "Tesla Y":
                model = ev_models.tesla_y_long()
            else:
                # st.title("fail")
                # Exception("Model not yet implemented")
                pass
            if st.session_state["model"] is None:
                st.number_input("Battery capacity", 1, 250, 50, key="capa")
                c_rates_df = st.data_editor(
                    pd.DataFrame(
                        [[10 * i, 15 - i] for i in range(11)],
                        columns=["Percentage", "Rate"],
                    ),
                    num_rows="dynamic",
                    hide_index=True,
                )
            else:
                st.number_input(
                    "Battery capacity", 1, 250, model.battery.capa, key="capa"
                )
                c_rates_df = st.data_editor(
                    pd.DataFrame(
                        [
                            [i, model.battery.charging_rate(i)]
                            for i in range(10, 91, 10)
                        ],
                        columns=["Percentage", "Rate"],
                    ),
                    num_rows="dynamic",
                    hide_index=True,
                )
        if st.session_state["model"] is not None:
            with _c[1].container():
                fig, ax = plt.subplots(figsize=(6, 2))
                _x = np.linspace(30, 160, 50)
                ax.plot(_x, [model.power_consumption(x) for x in _x])
                ax.set_xlabel("Speed, km/h")
                ax.set_ylabel("Power demand\nkWh per 100 km")
                st.pyplot(fig)
            with _c[2].container():
                fig, ax = plt.subplots(figsize=(6, 2))
                _x = np.linspace(10, 90, 50)
                ax.plot(_x, [model.battery.charging_rate(x) for x in _x])
                ax.set_xlabel("Battery state, %")
                ax.set_ylabel("Charging rate, kW")
                st.pyplot(fig)
    st.slider("Trip distance", 0, 2000, 600, 1, key="distance")
    st.slider("Start battery state (%)", 0, 100, 90, 1, key="start_state")
    st.slider("End battery state (%)", 0, 100, 10, 1, key="end_state")
    _left, _right = st.columns(2, gap="small", vertical_alignment="top", border=True)
    _left.slider("Travel speed", 30, 180, 130, 1, key="speed")
    _right.number_input("Number of breaks", 0, 10, 1, 1, key="n_breaks")
    _right.slider("Break duration", 3, 60, 25, 1, key="break_duration")
    _right.badge(
        "Traveling speed {:.0f} km/h".format(
            model.max_trip_speed(
                st.session_state["distance"],
                st.session_state["n_breaks"],
                st.session_state["break_duration"],
                st.session_state["end_state"],
                st.session_state["start_state"],
            )
        ),
        icon="🚀",
        color="green",
    )
    break_list = model.min_break_duration(
                    st.session_state["distance"],
                    st.session_state["speed"],
                    st.session_state["end_state"],
                    st.session_state["start_state"],
                )
    _left.badge(
        (f"{len(break_list)}x " if len(break_list) > 2 else "")
        + f"{break_list[0]:.0f} + {break_list[-1]:.0f} min",
        icon="🔌",
        color="orange",
    )
    st.markdown("Gute Fahrt, Mast- und Schotbruch!")


if __name__ == "__main__":
    build_page()
