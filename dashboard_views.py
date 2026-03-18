from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from config import CONFIG
from dashboard_tabs import build_tab_definitions
from dashboard_view_shared import (
    build_area_line_figure,
    format_integer_de,
    format_power_value,
    render_machine_status_panel,
    render_plotly_chart,
)
from live_data import RenderContext, build_render_context, drain_receiver_queue
from snapshot_schema import get_main_electrical, get_main_pneumatic
from utils import build_generic_line_df, build_line_df


def _render_layer_metric_card(title: str, value: str, accent_color: str, container_key: str) -> None:
    with st.container(border=True, key=container_key):
        st.markdown(
            (
                "<div class='layer-kpi-card'>"
                f"<div class='layer-kpi-label'>{title}</div>"
                f"<div class='layer-kpi-value' style='color:{accent_color};'>{value}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )


def _render_summary_metric_card(title: str, value: str, container_key: str) -> None:
    with st.container(border=True, key=container_key):
        st.markdown(
            (
                "<div class='layer-kpi-card'>"
                f"<div class='layer-kpi-label'>{title}</div>"
                f"<div class='layer-kpi-value' style='color:#111827;'>{value}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )


def render_summary_cards(current: Dict[str, Any] | None) -> None:
    left_col, right_col = st.columns([1, 1])
    with left_col:
        total_power = None
        if isinstance(current, dict):
            electrical_power = get_main_electrical(current)
            pneumatic_power = get_main_pneumatic(current)
            if electrical_power is not None and pneumatic_power is not None:
                total_power = electrical_power + pneumatic_power
        _render_summary_metric_card(
            "Gesamte Leistungsaufnahme der Werkzeugmaschine",
            format_power_value(total_power) if total_power is not None else "--",
            "dashboard-summary-card-total",
        )

    with right_col:
        yearly_demand = None
        if isinstance(current, dict):
            electrical_power = get_main_electrical(current)
            pneumatic_power = get_main_pneumatic(current)
            if electrical_power is not None and pneumatic_power is not None:
                yearly_demand = (electrical_power + pneumatic_power) * 8 * 2 * 220 / 1000.0
        _render_summary_metric_card(
            "Jährlicher Energieverbrauch",
            f"{format_integer_de(yearly_demand)} kWh" if yearly_demand is not None else "--",
            "dashboard-summary-card-yearly",
        )


def _build_dashboard_electrical_figure(context: RenderContext):
    line_df = build_line_df(context.window_history, window_seconds=context.window_seconds)
    if line_df.empty:
        return None
    return build_area_line_figure(
        line_df,
        x_col="ts",
        y_col="electric_w",
        line_color=CONFIG["ELECTRICAL_PRIMARY_HEX"],
        fill_rgba=CONFIG["ELECTRICAL_FILL_RGBA"],
        latest_marker_color=CONFIG["ELECTRICAL_PRIMARY_HEX"],
        y_title=CONFIG["Y_POWER_TITLE"],
        now_dt=context.now_dt,
        start_dt=context.window_start_dt,
        y_min=0,
        chart_uirevision="dashboard-power",
        background_color=CONFIG["PANEL_BG_INNER"],
        y_unit="W",
    )


def _build_dashboard_air_figure(context: RenderContext):
    air_df = build_generic_line_df(
        context.window_history,
        "airpower_main",
        value_col="value",
        window_seconds=context.window_seconds,
    )
    if air_df.empty:
        return None
    return build_area_line_figure(
        air_df,
        x_col="ts",
        y_col="value",
        line_color=CONFIG["PNEUMATIC_PRIMARY_HEX"],
        fill_rgba=CONFIG["PNEUMATIC_FILL_RGBA"],
        latest_marker_color=CONFIG["PNEUMATIC_PRIMARY_HEX"],
        y_title=CONFIG["Y_POWER_TITLE"],
        now_dt=context.now_dt,
        start_dt=context.window_start_dt,
        y_min=0,
        chart_uirevision="dashboard-air",
        background_color=CONFIG["PANEL_BG_INNER"],
        y_unit="W",
    )


def _render_dashboard_group_panel(
    *,
    group_key: str,
    metric_title: str,
    metric_value: str,
    metric_color: str,
    metric_key: str,
    chart_title: str | None,
    chart_key: str,
    figure,
) -> None:
    with st.container(border=True, key=group_key):
        _render_layer_metric_card(metric_title, metric_value, metric_color, metric_key)
        with st.container(border=True, key=chart_key):
            if chart_title:
                st.subheader(chart_title)
            if figure is None:
                st.info("Keine Daten fuer das Diagramm.")
            else:
                render_plotly_chart(figure, key=f"plotly_{chart_key}")


def _render_dashboard_view(context: RenderContext) -> None:
    render_summary_cards(context.latest)

    left_col, right_col = st.columns([1, 1])
    with left_col:
        _render_dashboard_group_panel(
            group_key="dashboard-electrical-group",
            metric_title="Elektrische Hauptversorgung",
            metric_value=format_power_value(get_main_electrical(context.latest or {})),
            metric_color=CONFIG["ELECTRICAL_PRIMARY_HEX"],
            metric_key="dashboard-electrical-card",
            chart_title=None,
            chart_key="dashboard-electrical-chart",
            figure=_build_dashboard_electrical_figure(context),
        )

    with right_col:
        _render_dashboard_group_panel(
            group_key="dashboard-air-group",
            metric_title="Pneumatische Hauptversorgung Leistungsäquivalent",
            metric_value=format_power_value(get_main_pneumatic(context.latest or {})),
            metric_color=CONFIG["PNEUMATIC_PRIMARY_HEX"],
            metric_key="dashboard-air-card",
            chart_title=None,
            chart_key="dashboard-air-chart",
            figure=_build_dashboard_air_figure(context),
        )

    render_machine_status_panel(
        context,
        container_key="dashboard-status-panel",
        chart_key="plotly_timeline",
    )


@st.fragment(run_every="5s")
def _render_live_dashboard_tab() -> None:
    drain_receiver_queue(st.session_state)
    context = build_render_context(st.session_state)
    _render_dashboard_view(context)


def render_dashboard_tab() -> None:
    _render_live_dashboard_tab()


def render_tabs_view() -> None:
    tab_definitions = build_tab_definitions(render_dashboard_tab)
    tabs = st.tabs([tab_definition.title for tab_definition in tab_definitions])
    for tab_definition, tab in zip(tab_definitions, tabs, strict=False):
        with tab:
            tab_definition.render()
