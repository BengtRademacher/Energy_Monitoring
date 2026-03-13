from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard_tabs import TabDefinition
from dashboard_view_shared import build_status_caption_from_context, coerce_timestamp_for_display
from live_data import RenderContext, build_render_context, drain_receiver_queue


def render_json_explorer_view(context: RenderContext) -> None:
    with st.container(border=True, key="json-header-panel"):
        st.caption(build_status_caption_from_context(context))
        st.caption("Basis: 2 Schichten, 8h/Tag, 220 Tage/Jahr")
        st.caption(f"Letztes Update: {context.now_dt.strftime('%H:%M:%S')}")

    with st.container(border=True, key="json-body-panel"):
        if isinstance(context.latest, dict):
            display_dict: dict[str, Any] = coerce_timestamp_for_display(context.latest)
            st.json(display_dict)
        else:
            st.info("Warte auf Live-Daten vom WebSocket...")


@st.fragment(run_every="1s")
def _render_live_json_explorer_tab() -> None:
    drain_receiver_queue(st.session_state)
    context = build_render_context(st.session_state)
    render_json_explorer_view(context)


def render_json_explorer_tab() -> None:
    _render_live_json_explorer_tab()


def get_optional_tab_definition() -> TabDefinition:
    return TabDefinition(id="json", title="JSON-Explorer", render=render_json_explorer_tab)
