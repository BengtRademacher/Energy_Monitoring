from __future__ import annotations

import streamlit as st

from config import CONFIG
from dashboard_styles import inject_global_styles, inject_metric_styles, render_app_header
from dashboard_views import render_tabs_view
from live_data import drain_receiver_queue, ensure_state


def main() -> None:
    st.set_page_config(page_title=CONFIG["TITLE_TEXT"], layout="wide")

    ensure_state(st.session_state)
    drain_receiver_queue(st.session_state)
    inject_global_styles(CONFIG)
    inject_metric_styles(CONFIG)
    render_app_header(CONFIG)
    render_tabs_view()
