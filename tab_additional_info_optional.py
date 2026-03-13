from __future__ import annotations

import streamlit as st

from config import CONFIG
from dashboard_tabs import TabDefinition
from utils import find_image_path


def _find_iso_logo_path() -> str | None:
    return find_image_path("logo_ISO")


def _find_boxplot_logo_path() -> str | None:
    return find_image_path("logo_boxplot")


def render_additional_info_tab() -> None:
    link_col1, link_col2 = st.columns(2)
    with link_col1:
        with st.container(border=True, key="additional-uhlmann-link"):
            st.link_button("Link zu Uhlmann", "https://www.uhlmann.de/de", width="stretch", type="primary")
    with link_col2:
        with st.container(border=True, key="additional-festo-link"):
            st.link_button("Link zu Festo", "https://www.festo.com/de/de/", width="stretch", type="primary")

    logo_iso = _find_iso_logo_path()
    if logo_iso:
        with st.container(border=True, key="additional-iso-panel"):
            _, center_col, _ = st.columns([1, 2, 1])
            with center_col:
                st.image(logo_iso)

    logo_boxplot = _find_boxplot_logo_path()
    if logo_boxplot:
        with st.container(border=True, key="additional-boxplot-panel"):
            _, center_col, _ = st.columns([1, 2, 1])
            with center_col:
                st.image(logo_boxplot)

    info_col1, info_col2 = st.columns(2)
    with info_col1:
        with st.container(border=True, key="additional-ifw-panel"):
            logo_ifw = find_image_path(CONFIG["LOGO_IFW_BASENAME"])
            if logo_ifw:
                st.image(logo_ifw, width=180)
            st.markdown("**Institut fuer Fertigungstechnik und Werkzeugmaschinen (IFW)**")
            st.caption("Leibniz Universitaet Hannover")
    with info_col2:
        with st.container(border=True, key="additional-fx-panel"):
            logo_fx = find_image_path(CONFIG["LOGO_FX_BASENAME"])
            if logo_fx:
                st.image(logo_fx, width=180)
            st.markdown("**Factory-X 2026**")
            st.caption("Autoren: Bengt Rademacher und Alexander Boettcher")


def get_optional_tab_definition() -> TabDefinition:
    return TabDefinition(id="info", title="Zusatzinformationen", render=render_additional_info_tab)
