from __future__ import annotations

from datetime import datetime
import re
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import CONFIG
from live_data import RenderContext
from plotting import LinePlotSpec, build_line_plot_figure
from snapshot_schema import COMPONENT_KEYS, get_component_value, get_machine_status
from utils import build_status_timeline_df


PLOTLY_CHART_CONFIG = {
    "displaylogo": False,
    "responsive": True,
}


def _status_timeline_margins(height_px: int) -> dict[str, int]:
    if height_px < 120:
        return {
            "l": CONFIG["PLOTLY_MARGIN_L"],
            "r": CONFIG["PLOTLY_MARGIN_R"],
            "t": 8,
            "b": max(int(CONFIG["PLOTLY_MARGIN_B"]), int(CONFIG["PLOTLY_TICK_FONT_SIZE"]) + 12),
        }
    return {
        "l": CONFIG["PLOTLY_MARGIN_L"],
        "r": CONFIG["PLOTLY_MARGIN_R"],
        "t": 30,
        "b": CONFIG["PLOTLY_MARGIN_B"],
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


def _coerce_color_to_rgba(color: str, alpha: float) -> str | None:
    normalized = color.strip()
    if not normalized:
        return None

    if normalized.startswith("#"):
        hex_value = normalized[1:]
        if len(hex_value) == 3:
            hex_value = "".join(char * 2 for char in hex_value)
        if len(hex_value) != 6:
            return None
        try:
            red = int(hex_value[0:2], 16)
            green = int(hex_value[2:4], 16)
            blue = int(hex_value[4:6], 16)
        except ValueError:
            return None
        return f"rgba({red},{green},{blue},{alpha:.2f})"

    rgb_match = re.fullmatch(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", normalized)
    if rgb_match:
        red, green, blue = rgb_match.groups()
        return f"rgba({red},{green},{blue},{alpha:.2f})"

    rgba_match = re.fullmatch(
        r"rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([0-9]*\.?[0-9]+)\s*\)",
        normalized,
    )
    if rgba_match:
        red, green, blue, _ = rgba_match.groups()
        return f"rgba({red},{green},{blue},{alpha:.2f})"

    return None


def machine_status_background_color(status_name: str, alpha: float = 0.35) -> str | None:
    base_color = machine_status_color_map().get(status_name)
    if base_color is None:
        return None
    return _coerce_color_to_rgba(base_color, alpha)


def _build_component_status_history_df(component_key: str, context: RenderContext) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for point in context.window_history:
        ts = point.get("timestamp")
        if not isinstance(ts, (int, float)):
            continue

        value = get_component_value(point, component_key)
        if value is None:
            continue

        rows.append(
            {
                "ts": datetime.fromtimestamp(float(ts)),
                "value": float(value),
                "status": get_machine_status(point),
            }
        )

    return pd.DataFrame(rows, columns=["ts", "value", "status"])


def _build_status_overlay_trace(
    segment_x: list[object],
    segment_y: list[float],
    status_name: str,
    y_top: float,
) -> go.Scatter | None:
    fill_color = machine_status_background_color(status_name)
    if fill_color is None or len(segment_x) < 2:
        return None

    return go.Scatter(
        x=[*segment_x, *reversed(segment_x)],
        y=([y_top] * len(segment_x)) + list(reversed(segment_y)),
        mode="lines",
        line=dict(color="rgba(0,0,0,0)", width=0),
        fill="toself",
        fillcolor=fill_color,
        showlegend=False,
        hoverinfo="skip",
    )


def build_component_status_overlay_traces(
    *,
    component_key: str,
    context: RenderContext,
    y_top: float,
) -> list[go.Scatter]:
    status_df = _build_component_status_history_df(component_key, context)
    if len(status_df.index) < 2 or y_top <= 0:
        return []

    status_df = status_df.sort_values("ts").reset_index(drop=True)
    x_values = status_df["ts"].tolist()
    y_values = pd.to_numeric(status_df["value"], errors="coerce").tolist()
    statuses = status_df["status"].tolist()

    overlay_traces: list[go.Scatter] = []
    current_status = str(statuses[0])
    current_x = [x_values[0], x_values[1]]
    current_y = [float(y_values[0]), float(y_values[1])]

    for index in range(1, len(x_values) - 1):
        interval_status = str(statuses[index])
        next_x = x_values[index + 1]
        next_y = float(y_values[index + 1])
        if interval_status == current_status:
            current_x.append(next_x)
            current_y.append(next_y)
            continue

        trace = _build_status_overlay_trace(current_x, current_y, current_status, y_top)
        if trace is not None:
            overlay_traces.append(trace)

        current_status = interval_status
        current_x = [x_values[index], next_x]
        current_y = [float(y_values[index]), next_y]

    trace = _build_status_overlay_trace(current_x, current_y, current_status, y_top)
    if trace is not None:
        overlay_traces.append(trace)

    return overlay_traces


def apply_status_overlay_above_line(
    fig: go.Figure,
    *,
    component_key: str,
    context: RenderContext,
) -> go.Figure:
    try:
        y_axis_range = list(fig.layout.yaxis.range) if fig.layout.yaxis.range is not None else []
        y_top = float(y_axis_range[1]) if len(y_axis_range) >= 2 else 0.0
    except (TypeError, ValueError):
        y_top = 0.0

    overlay_traces = build_component_status_overlay_traces(
        component_key=component_key,
        context=context,
        y_top=y_top,
    )
    if not overlay_traces:
        return fig

    layered_fig = go.Figure()
    layered_fig.update_layout(fig.layout)
    for trace in overlay_traces:
        layered_fig.add_trace(trace)
    for trace in fig.data:
        layered_fig.add_trace(trace)
    return layered_fig


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
    plot_background_color: str | None = None,
    paper_background_color: str | None = None,
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
            plot_background_color=plot_background_color,
            paper_background_color=paper_background_color,
            y_unit=y_unit,
        ),
    )


def build_status_timeline_figure(
    df: pd.DataFrame,
    now_dt: datetime,
    start_dt: datetime,
    height_px: int = 156,
) -> go.Figure:
    timeline_margins = _status_timeline_margins(height_px)
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            height=height_px,
            margin=timeline_margins,
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
            automargin=True,
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
        automargin=True,
    )
    fig.update_layout(
        height=height_px,
        margin=timeline_margins,
        paper_bgcolor=CONFIG["CHART_PANEL_BG"],
        plot_bgcolor=CONFIG["CHART_PANEL_BG"],
        showlegend=False,
        font=dict(family=CONFIG["PLOTLY_FONT_FAMILY"], size=CONFIG["PLOTLY_TICK_FONT_SIZE"]),
        hoverlabel=dict(font=dict(family=CONFIG["PLOTLY_FONT_FAMILY"], size=CONFIG["PLOTLY_TICK_FONT_SIZE"])),
        separators=",.",
        uirevision="stable-timeline-chart",
    )
    return fig


def render_machine_status_panel(
    context: RenderContext,
    *,
    container_key: str,
    chart_key: str,
    height_px: int = 156,
) -> None:
    with st.container(border=True, key=container_key):
        st.subheader("Maschinenstatus")
        render_machine_status_legend()
        timeline_df = build_status_timeline_df(context.window_history, window_seconds=context.window_seconds)
        timeline_fig = build_status_timeline_figure(
            timeline_df,
            context.now_dt,
            context.window_start_dt,
            height_px=height_px,
        )
        render_plotly_chart(timeline_fig, key=chart_key)


def build_status_caption_from_context(context: RenderContext) -> str:
    state = "verbunden" if context.status["connected"] else "getrennt"
    error_text = f" | Fehler: {context.status['last_error']}" if context.status["last_error"] else ""
    return f"Status: {state} | Datenpunkte: {len(context.history)}/{context.history_capacity}{error_text}"


def coerce_timestamp_for_display(latest_snapshot: dict[str, Any]) -> dict[str, Any]:
    display_dict = latest_snapshot.copy()
    if "timestamp" in display_dict and isinstance(display_dict["timestamp"], float):
        display_dict["timestamp"] = round(display_dict["timestamp"], 2)
    return display_dict
