from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

import pandas as pd
import plotly.graph_objects as go

from config import CONFIG


@dataclass(frozen=True)
class LinePlotSpec:
    x_col: str
    y_col: str
    line_color: str
    fill_rgba: str
    marker_color: str
    y_title: str
    now_dt: datetime
    start_dt: datetime
    y_min: float | None = None
    y_max: float | None = None
    height_px: int | None = None
    chart_uirevision: str = "stable-live-chart"
    show_x_tick_labels: bool = True
    background_color: str | None = None
    plot_background_color: str | None = None
    paper_background_color: str | None = None
    y_unit: str | None = None


_NICE_TICK_FACTORS = (1.0, 2.0, 2.5, 5.0)
_Y_AXIS_INTERVAL_CANDIDATES = (4, 3, 2)


def _format_tick_label_de(value: float) -> str:
    return f"{float(value):,.0f}".replace(",", ".")


def _nice_ceil(value: float) -> float:
    if value <= 0:
        return 1.0

    exponent = math.floor(math.log10(value))
    while True:
        magnitude = 10**exponent
        for factor in _NICE_TICK_FACTORS:
            candidate = factor * magnitude
            if candidate >= value:
                return candidate
        exponent += 1


def _build_dynamic_y_axis(max_value: float, unit: str | None) -> dict[str, list[float] | list[str] | list[int]]:
    if max_value <= 0:
        return {
            "range": [0, 1],
            "tickvals": [0, 1],
            "ticktext": ["0", "1"],
        }

    best_interval_count: int | None = None
    best_step: float | None = None
    best_top: float | None = None

    for interval_count in _Y_AXIS_INTERVAL_CANDIDATES:
        step = _nice_ceil(max_value / interval_count)
        top = step * interval_count
        if best_top is None or top < best_top or (math.isclose(top, best_top) and interval_count > (best_interval_count or 0)):
            best_interval_count = interval_count
            best_step = step
            best_top = top

    assert best_interval_count is not None
    assert best_step is not None
    assert best_top is not None

    tickvals = [round(best_step * index, 10) for index in range(best_interval_count + 1)]
    ticktext = [_format_tick_label_de(value) for value in tickvals]
    if unit and len(ticktext) >= 3:
        ticktext[-2] = unit

    return {
        "range": [0, int(round(best_top)) if math.isclose(best_top, round(best_top)) else best_top],
        "tickvals": [int(round(value)) if math.isclose(value, round(value)) else value for value in tickvals],
        "ticktext": ticktext,
    }


def build_line_plot_figure(df: pd.DataFrame, spec: LinePlotSpec) -> go.Figure:
    default_background_color = spec.background_color or CONFIG["CHART_PANEL_BG"]
    plot_background_color = spec.plot_background_color or default_background_color
    paper_background_color = spec.paper_background_color or default_background_color
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[spec.x_col],
            y=df[spec.y_col],
            mode="lines",
            line=dict(color=spec.line_color, width=CONFIG["PLOTLY_LINE_WIDTH"]),
            showlegend=False,
            hovertemplate="%{x|%d.%m.%Y %H:%M:%S}<br>%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df[spec.x_col],
            y=df[spec.y_col],
            mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            fill="tozeroy",
            fillcolor=spec.fill_rgba,
            showlegend=False,
            hoverinfo="skip",
        )
    )
    latest_point = df.tail(1)
    fig.add_trace(
        go.Scatter(
            x=latest_point[spec.x_col],
            y=latest_point[spec.y_col],
            mode="markers",
            marker=dict(size=CONFIG["PLOTLY_MARKER_SIZE"], color=spec.marker_color),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    bottom_margin = CONFIG["PLOTLY_MARGIN_B"] if spec.show_x_tick_labels else 6
    fig.update_layout(
        height=spec.height_px or int(CONFIG["PLOTLY_DEFAULT_HEIGHT_PX"]),
        margin=dict(
            l=CONFIG["PLOTLY_MARGIN_L"],
            r=CONFIG["PLOTLY_MARGIN_R"],
            t=CONFIG["PLOTLY_MARGIN_T"],
            b=bottom_margin,
        ),
        showlegend=False,
        font=dict(family=CONFIG["PLOTLY_FONT_FAMILY"], size=CONFIG["PLOTLY_TICK_FONT_SIZE"]),
        paper_bgcolor=paper_background_color,
        plot_bgcolor=plot_background_color,
        hovermode="x unified",
        hoverlabel=dict(
            font=dict(family=CONFIG["PLOTLY_FONT_FAMILY"], size=CONFIG["PLOTLY_TICK_FONT_SIZE"])
        ),
        separators=",.",
        uirevision=spec.chart_uirevision,
    )
    fig.update_xaxes(
        range=[spec.start_dt, spec.now_dt],
        title_text=None,
        tickfont=dict(
            family=CONFIG["PLOTLY_FONT_FAMILY"],
            size=CONFIG["PLOTLY_TICK_FONT_SIZE"],
        ),
        tickformat="%H:%M",
        showticklabels=spec.show_x_tick_labels,
        showgrid=CONFIG["PLOTLY_SHOWGRID"],
        gridcolor=CONFIG["CHART_GRID_COLOR"],
        gridwidth=CONFIG["PLOTLY_GRID_WIDTH"],
    )
    fig.update_yaxes(
        title_text=spec.y_title,
        title_font=dict(
            family=CONFIG["PLOTLY_FONT_FAMILY"],
            size=CONFIG["PLOTLY_AXIS_TITLE_FONT_SIZE"],
        ),
        tickfont=dict(
            family=CONFIG["PLOTLY_FONT_FAMILY"],
            size=CONFIG["PLOTLY_TICK_FONT_SIZE"],
        ),
        tickformat=",.0f",
        showgrid=CONFIG["PLOTLY_SHOWGRID"],
        gridcolor=CONFIG["CHART_GRID_COLOR"],
        gridwidth=CONFIG["PLOTLY_GRID_WIDTH"],
        ticklabeloverflow="allow",
        automargin=True,
    )

    if spec.y_min == 0 and spec.y_max is None:
        max_value = pd.to_numeric(df[spec.y_col], errors="coerce").dropna().max()
        dynamic_axis = _build_dynamic_y_axis(float(max_value) if pd.notna(max_value) else 0.0, spec.y_unit)
        fig.update_yaxes(
            range=dynamic_axis["range"],
            tickmode="array",
            tickvals=dynamic_axis["tickvals"],
            ticktext=dynamic_axis["ticktext"],
        )
    elif spec.y_min is not None or spec.y_max is not None:
        fig.update_yaxes(range=[spec.y_min, spec.y_max])

    return fig
