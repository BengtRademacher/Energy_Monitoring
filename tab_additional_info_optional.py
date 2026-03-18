from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from config import CONFIG
from dashboard_tabs import TabDefinition
from utils import find_image_path


def _find_boxplot_logo_path() -> str | None:
    return find_image_path("logo_b1770c")


def _render_centered_logo_image(image_path: str, width_px: int) -> None:
    suffix = Path(image_path).suffix.lower()
    mime_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
    }.get(suffix, "application/octet-stream")
    encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
    st.markdown(
        f"""
<div class="additional-machine-image">
  <img src="data:{mime_type};base64,{encoded}" alt="" style="width:{width_px}px;" />
</div>
""",
        unsafe_allow_html=True,
    )


def render_additional_info_tab() -> None:
    link_col1, link_col2 = st.columns(2)
    with link_col1:
        with st.container(border=True, key="additional-uhlmann-link"):
            st.link_button("Link zu Uhlmann", "https://www.uhlmann.de/de", width="stretch", type="primary")
    with link_col2:
        with st.container(border=True, key="additional-export-link"):
            st.button("Export", width="stretch", type="primary", disabled=True)

    logo_boxplot = _find_boxplot_logo_path()
    if logo_boxplot:
        with st.container(border=True, key="additional-boxplot-panel"):
            _render_centered_logo_image(logo_boxplot, width_px=760)

    info_col1, info_col2 = st.columns(2)
    with info_col1:
        with st.container(border=True, key="additional-ifw-panel"):
            logo_ifw = find_image_path(CONFIG["LOGO_IFW_BASENAME"])
            if logo_ifw:
                st.image(logo_ifw, width=180)
            st.markdown("**Uhlmann Pac-Systeme GmbH & Co. KG**")
            st.caption("In Kooperation mit der Leibniz Universität Hannover")
    with info_col2:
        with st.container(border=True, key="additional-fx-panel"):
            logo_fx = find_image_path(CONFIG["LOGO_FX_BASENAME"])
            if logo_fx:
                st.image(logo_fx, width=180)
            st.markdown("**Factory-X 2026**")
            st.caption("Autoren: Bengt Rademacher, Alexander Böttcher und Anna Hörner")


def get_optional_tab_definition() -> TabDefinition:
    return TabDefinition(id="info", title="Zusatzinformationen", render=render_additional_info_tab)
