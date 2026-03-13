from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import CONFIG
from live_data import RenderContext
from plotting import LinePlotSpec, build_line_plot_figure
from snapshot_schema import COMPONENT_KEYS


PLOTLY_CHART_CONFIG = {
    "displaylogo": False,
    "responsive": True,
}


def format_integer_de(value: float | int) -> str:
    return f"{float(value):,.0f}".replace(",", ".")


def format_power_value(value: float | None, unit: str = "W") -> str:
    if isinstance(value, (int, float)):
        return f"{format_integer_de(float(value))} {unit}"
    return f"-- {unit}" if unit else "--"


def render_plotly_chart(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, key=key, config=PLOTLY_CHART_CONFIG)


def component_color_map() -> dict[str, str]:
    mono_color = CONFIG["COMPONENT_MONO_HEX"]
    return {key: mono_color for key in COMPONENT_KEYS}


def machine_status_color_map() -> dict[str, str]:
    return {
        "Processing": CONFIG["ELECTRICAL_PRIMARY_HEX"],
        "Non-Processing": CONFIG["ELECTRICAL_SOFT_HEX"],
        "Off": "#9e9e9e",
        "E-Stop/Warning": "#f44336",
    }


def machine_status_legend_labels() -> dict[str, str]:
    return {
        "Processing": "Processing",
        "Non-Processing": "Non-Processing",
        "Off": "Off",
        "E-Stop/Warning": "E-Stop",
    }


def render_machine_status_legend() -> None:
    legend_labels = machine_status_legend_labels()
    legend_html = "".join(
        (
            "<span class='machine-status-pill'>"
            f"<span class='machine-status-dot' style='background:{color};'></span>"
            f"{legend_labels[status_name]}"
            "</span>"
        )
        for status_name, color in machine_status_color_map().items()
    )
    st.markdown(f"<div class='machine-status-legend'>{legend_html}</div>", unsafe_allow_html=True)


def build_area_line_figure(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    line_color: str,
    fill_rgba: str,
    latest_marker_color: str,
    y_title: str,
    now_dt: datetime,
    start_dt: datetime,
    y_min: float | None = None,
    y_max: float | None = None,
    height_px: int | None = None,
    chart_uirevision: str = "stable-live-chart",
    background_color: str | None = None,
    show_x_tick_labels: bool = True,
    y_unit: str | None = "W",
) -> go.Figure:
    return build_line_plot_figure(
        df,
        LinePlotSpec(
            x_col=x_col,
            y_col=y_col,
            line_color=line_color,
            fill_rgba=fill_rgba,
            marker_color=latest_marker_color,
            y_title=y_title,
            now_dt=now_dt,
            start_dt=start_dt,
            y_min=y_min,
            y_max=y_max,
            height_px=height_px,
            chart_uirevision=chart_uirevision,
            show_x_tick_labels=show_x_tick_labels,
            background_color=background_color,
            y_unit=y_unit,
        ),
    )


def build_status_timeline_figure(df: pd.DataFrame, now_dt: datetime, start_dt: datetime) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            height=156,
            margin=dict(
                l=CONFIG["PLOTLY_MARGIN_L"],
                r=CONFIG["PLOTLY_MARGIN_R"],
                t=30,
                b=CONFIG["PLOTLY_MARGIN_B"],
            ),
            paper_bgcolor=CONFIG["CHART_PANEL_BG"],
            plot_bgcolor=CONFIG["CHART_PANEL_BG"],
            showlegend=False,
            font=dict(family=CONFIG["PLOTLY_FONT_FAMILY"], size=CONFIG["PLOTLY_TICK_FONT_SIZE"]),
            hoverlabel=dict(font=dict(family=CONFIG["PLOTLY_FONT_FAMILY"], size=CONFIG["PLOTLY_TICK_FONT_SIZE"])),
            separators=",.",
            uirevision="stable-timeline-chart",
        )
        fig.update_xaxes(
            range=[start_dt, now_dt],
            title_text=None,
            tickfont=dict(
                family=CONFIG["PLOTLY_FONT_FAMILY"],
                size=CONFIG["PLOTLY_TICK_FONT_SIZE"],
            ),
            tickformat="%H:%M",
            showticklabels=True,
            showgrid=True,
            gridcolor=CONFIG["CHART_GRID_COLOR"],
        )
        fig.update_yaxes(visible=False)
        return fig

    fig = px.timeline(
        df,
        x_start="start",
        x_end="end",
        y="row",
        color="cls",
        color_discrete_map=machine_status_color_map(),
    )
    fig.update_traces(showlegend=False)
    fig.update_yaxes(visible=False, showticklabels=False)
    fig.update_xaxes(
        range=[start_dt, now_dt],
        title_text=None,
        tickfont=dict(
            family=CONFIG["PLOTLY_FONT_FAMILY"],
            size=CONFIG["PLOTLY_TICK_FONT_SIZE"],
        ),
        tickformat="%H:%M",
        showticklabels=True,
        showgrid=True,
        gridcolor=CONFIG["CHART_GRID_COLOR"],
        gridwidth=CONFIG["PLOTLY_GRID_WIDTH"],
    )
    fig.update_layout(
        height=156,
        margin=dict(
            l=CONFIG["PLOTLY_MARGIN_L"],
            r=CONFIG["PLOTLY_MARGIN_R"],
            t=30,
            b=CONFIG["PLOTLY_MARGIN_B"],
        ),
        paper_bgcolor=CONFIG["CHART_PANEL_BG"],
        plot_bgcolor=CONFIG["CHART_PANEL_BG"],
        showlegend=False,
        font=dict(family=CONFIG["PLOTLY_FONT_FAMILY"], size=CONFIG["PLOTLY_TICK_FONT_SIZE"]),
        hoverlabel=dict(font=dict(family=CONFIG["PLOTLY_FONT_FAMILY"], size=CONFIG["PLOTLY_TICK_FONT_SIZE"])),
        separators=",.",
        uirevision="stable-timeline-chart",
    )
    return fig


def build_status_caption_from_context(context: RenderContext) -> str:
    state = "verbunden" if context.status["connected"] else "getrennt"
    error_text = f" | Fehler: {context.status['last_error']}" if context.status["last_error"] else ""
    return f"Status: {state} | Datenpunkte: {len(context.history)}/{context.history_capacity}{error_text}"


def coerce_timestamp_for_display(latest_snapshot: dict[str, Any]) -> dict[str, Any]:
    display_dict = latest_snapshot.copy()
    if "timestamp" in display_dict and isinstance(display_dict["timestamp"], float):
        display_dict["timestamp"] = round(display_dict["timestamp"], 2)
    return display_dict
