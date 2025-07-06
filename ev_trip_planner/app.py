"""Streamlit webapp"""

from json import dumps as j_dumps
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from urllib.parse import quote
from webbrowser import open as w_open
import ev_models
import ev_trip_planner


def callback_end_state():
    if st.session_state.end_state < st.session_state.res_prc:
        st.warning(
            "End battery state cannot be lower than battery reserve. Adjust reserve "
            "setting if needed.",
            icon="❗",
        )
        st.session_state["end_state"] = st.session_state.res_prc


def callback_feedback():
    w_open(
        "&".join(
            [
                "mailto:?to=ev-trip-planner@riseup.net",
                "subject=[EVtp:data]",
                "body="
                + quote(
                    j_dumps(
                        {
                            k[:-8]: str(v)
                            for k, v in st.session_state.items()
                            if k.endswith("_fb_data")
                        }
                    )
                    + "\n-----\nLeave the above as is.",
                    safe="",
                ),
            ]
        )
    )


def callback_res_prc():
    st.session_state["res_km"] = (
        EV.battery.kWh(st.session_state.res_prc)
        / EV.power_consumption(st.session_state.res_sp)
        * 100
    )
    if st.session_state.end_state < st.session_state.res_prc:
        st.session_state["end_state"] = st.session_state.res_prc


def callback_res_km_sp():
    st.session_state["res_prc"] = (
        st.session_state.res_km
        * EV.power_consumption(st.session_state.res_sp)
        / EV.battery.capa
    )
    if st.session_state.end_state < st.session_state.res_prc:
        st.session_state["end_state"] = st.session_state.res_prc


def build_EV_section():
    global EV
    _c = st.container(border=True).tabs(["Select EV", "Efficiency", "Charging"])
    _c[0].segmented_control(
        "Vehicle",
        [
            "Tesla Y",
        ],
        selection_mode="single",
        default=["Tesla Y"],
        key="EV",
    )
    if st.session_state.EV == "Tesla Y":
        EV = ev_models.tesla_y_long()
    else:
        EV = ev_trip_planner.vehicle()
    with _c[0].popover("Set properties"):
        st.number_input("Battery capacity", 1, 250, EV.battery.capa, key="capa")
        st.data_editor(
            pd.DataFrame(
                [[i, EV.battery.charging_rate(i)] for i in range(10, 91, 10)],
                columns=["Percentage", "Rate"],
            ),
            num_rows="dynamic",
            hide_index=True,
        )

    fig, ax = plt.subplots(figsize=(6, 2))
    _x = np.linspace(30, 160, 50)
    ax.plot(_x, [EV.power_consumption(x) for x in _x])
    ax.set_xlabel("Speed, km/h")
    ax.set_ylabel("Power demand\nkWh per 100 km")
    _c[1].pyplot(fig)

    fig, ax = plt.subplots(figsize=(6, 2))
    _x = np.linspace(10, 90, 50)
    ax.plot(_x, [EV.battery.charging_rate(x) for x in _x])
    ax.set_xlabel("Battery state, %")
    ax.set_ylabel("Charging rate, kW")
    _c[2].pyplot(fig)


def build_feedback_section():
    st.link_button(
        "Wuensche/Ideen", "mailto:?to=ev-trip-planner@riseup.net&subject=[EVtp:fb]"
    )
    with st.popover("Send in trip details"):
        st.write(
            "Please submit value to preformat email, click the send link, and send "
            "from you email client."
        )
        with st.form(key="jouney_feedback", enter_to_submit=False):
            st.text_input(
                "EV model", st.session_state.EV, max_chars=80, key="EV_fb_data"
            )
            st.number_input(
                "Distance", 1, 9999, st.session_state.distance, key="dist_fb_data"
            )
            tmp = pd.Timedelta(
                st.session_state.distance / st.session_state.speed, "hours"
            ).components
            st.time_input(
                "Time w/out breaks",
                f"{tmp.hours:02d}:{tmp.minutes:02d}",
                key="time_fb_data",
            )
            st.number_input("Charged (kWh)", 0.0, 999.0, key="charged_fb_data")
            st.number_input(
                "Start battery state (%)",
                5,
                100,
                int(st.session_state.start_state),
                key="start_fb_data",
            )
            st.number_input(
                "End battery state (%)",
                0,
                100,
                int(st.session_state.end_state),
                key="end_fb_data",
            )
            st.text_area(
                "Notes",
                "zB starker Gegenwind, Hitze, Kaelte, nasse Bahn, etc",
                max_chars=250,
                key="notes_fb_data",
            )
            st.form_submit_button("Create email", on_click=callback_feedback)


def build_trip_section():
    global EV
    _c = st.container(border=True).tabs(["Trip", "Reserve"])
    _c[0].slider("Trip distance", 0, 2000, 600, 1, key="distance")
    _c[0].slider("Start battery state (%)", 0, 100, 90, 1, key="start_state")
    if "res_prc" not in st.session_state:
        st.session_state["res_prc"] = EV.batt_reserve
    if "end_state" not in st.session_state:
        st.session_state["end_state"] = st.session_state.res_prc
    _c[0].slider(
        "End battery state (%)",
        0.0,
        100.0,
        step=1.0,
        format="%.0f",
        key="end_state",
        on_change=callback_end_state,
    )
    _c1_prc = _c[1].container()
    _c1_km_sp = _c[1].columns(2, vertical_alignment="center")
    _c1_km_sp[1].slider(
        "at Speed", 70, 130, 110, 1, key="res_sp", on_change=callback_res_km_sp
    )
    if "res_km" not in st.session_state:
        st.session_state["res_km"] = (
            EV.battery.kWh(st.session_state.res_prc)
            / EV.power_consumption(st.session_state.res_sp)
            * 100
        )
    _c1_prc.slider(
        "Battery (%)",
        1.0,
        25.0,
        step=0.5,
        format="%.1f",
        key="res_prc",
        on_change=callback_res_prc,
    )
    _c1_km_sp[0].slider(
        "Distance",
        10.0,
        80.0,
        step=1.0,
        format="%.0f",
        key="res_km",
        on_change=callback_res_km_sp,
    )
    EV.batt_reserve = st.session_state.res_prc


def build_results_section():
    global EV
    _left, _right = st.columns(2, gap="small", vertical_alignment="top", border=True)
    _left.slider("Travel speed", 30, 180, 130, 1, key="speed")
    _right.number_input("Number of breaks", 0, 10, 1, 1, key="n_breaks")
    _right.slider("Break duration", 3, 60, 25, 1, key="break_duration")
    _right.badge(
        "Traveling speed {:.0f} km/h".format(
            EV.max_trip_speed(
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
    break_list = EV.min_break_duration(
        st.session_state["distance"],
        st.session_state["speed"],
        st.session_state["end_state"],
        st.session_state["start_state"],
    )
    _left.badge(
        (f"{len(break_list) - 1}x " if len(break_list) > 2 else "")
        + f"{break_list[0]:.0f} + {break_list[-1]:.0f} min",
        icon="🔌",
        color="orange",
    )


def build_page():
    st.title("EV Trip Planner")
    st.badge("version 66", icon="✨", color="blue")
    build_EV_section()
    build_trip_section()
    build_results_section()
    st.markdown("Gute Fahrt, Mast- und Schotbruch!")
    st.write("-----")
    build_feedback_section()


if __name__ == "__main__":
    build_page()
