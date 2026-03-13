from __future__ import annotations

import pandas as pd
import streamlit as st

from config import CONFIG
from dashboard_tabs import TabDefinition
from dashboard_view_shared import build_area_line_figure, component_color_map, render_plotly_chart
from live_data import RenderContext, build_render_context, drain_receiver_queue
from snapshot_schema import COMPONENT_KEYS, get_component_display_name
from utils import build_component_history_df


def build_component_figure(
    component_df: pd.DataFrame,
    component_key: str,
    context: RenderContext,
    show_x_tick_labels: bool = True,
):
    if component_df.empty or component_key not in component_df.columns:
        return None

    plot_df = component_df[["ts", component_key]].dropna(subset=[component_key]).copy()
    if plot_df.empty:
        return None

    color = component_color_map()[component_key]
    return build_area_line_figure(
        plot_df,
        x_col="ts",
        y_col=component_key,
        line_color=color,
        fill_rgba=CONFIG["COMPONENT_FILL_RGBA"],
        latest_marker_color=color,
        y_title=CONFIG["Y_COMPONENT_TITLE"],
        now_dt=context.now_dt,
        start_dt=context.window_start_dt,
        y_min=0,
        height_px=int(CONFIG["COMPONENT_PLOT_HEIGHT_PX"]),
        chart_uirevision=f"component-{component_key}",
        show_x_tick_labels=show_x_tick_labels,
        y_unit="W",
    )


def render_component_chart(
    component_df: pd.DataFrame,
    component_key: str,
    context: RenderContext,
    show_x_tick_labels: bool = True,
) -> None:
    display_name = get_component_display_name(component_key)
    with st.container(border=True, key=f"component-panel-{component_key}"):
        st.subheader(display_name)
        fig = build_component_figure(
            component_df,
            component_key,
            context,
            show_x_tick_labels=show_x_tick_labels,
        )
        if fig is None:
            st.info("Keine Daten fuer das Diagramm.")
            return

        render_plotly_chart(fig, key=f"plotly_{component_key}")


def render_component_showcase_view(context: RenderContext) -> None:
    if not isinstance(context.latest, dict):
        st.info("Warte auf Daten...")
        return

    component_df = build_component_history_df(context.window_history, window_seconds=context.window_seconds)
    for row_start in range(0, 6, 2):
        show_x_tick_labels = row_start >= 4
        left_col, right_col = st.columns(2)
        with left_col:
            render_component_chart(
                component_df,
                COMPONENT_KEYS[row_start],
                context,
                show_x_tick_labels=show_x_tick_labels,
            )
        with right_col:
            render_component_chart(
                component_df,
                COMPONENT_KEYS[row_start + 1],
                context,
                show_x_tick_labels=show_x_tick_labels,
            )

    render_component_chart(
        component_df,
        COMPONENT_KEYS[-1],
        context,
        show_x_tick_labels=True,
    )


@st.fragment(run_every="5s")
def _render_live_components_tab() -> None:
    drain_receiver_queue(st.session_state)
    context = build_render_context(st.session_state)
    render_component_showcase_view(context)


def render_components_tab() -> None:
    _render_live_components_tab()


def get_optional_tab_definition() -> TabDefinition:
    return TabDefinition(id="components", title="Komponenten", render=render_components_tab)
