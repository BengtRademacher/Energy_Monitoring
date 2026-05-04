from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from dashboard_tabs import TabDefinition
from utils import find_image_path


def _find_dmp70_logo_path() -> str | None:
    return find_image_path("logo_dmp70")


def _find_iso_logo_path() -> str | None:
    return find_image_path("logo_ISO")


def _image_to_data_uri(image_path: str) -> str:
    suffix = Path(image_path).suffix.lower()
    mime_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
    }.get(suffix, "application/octet-stream")
    encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _render_machine_logo_pair(left_image_path: str, right_image_path: str) -> None:
    left_data_uri = _image_to_data_uri(left_image_path)
    right_data_uri = _image_to_data_uri(right_image_path)
    st.markdown(
        f"""
<div class="additional-machine-logo-pair">
  <img src="{left_data_uri}" alt="" class="additional-machine-logo-left" />
  <img src="{right_data_uri}" alt="" class="additional-machine-logo-right" />
</div>
""",
        unsafe_allow_html=True,
    )


def render_additional_info_tab() -> None:
    link_col1, link_col2 = st.columns(2)
    with link_col1:
        with st.container(border=True, key="additional-ifw-link"):
            st.link_button("Link zum IFW Hannover", "https://www.ifw.uni-hannover.de", width="stretch", type="primary")
    with link_col2:
        with st.container(border=True, key="additional-export-link"):
            st.button("Export", width="stretch", type="primary", disabled=True)

    logo_dmp70 = _find_dmp70_logo_path()
    logo_iso = _find_iso_logo_path()
    if logo_dmp70 and logo_iso:
        with st.container(border=True, key="additional-boxplot-panel"):
            _render_machine_logo_pair(logo_dmp70, logo_iso)

    info_col1, info_col2 = st.columns(2)
    with info_col1:
        with st.container(border=True, key="additional-ifw-panel"):
            logo_ifw = find_image_path("logo_fx")
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
