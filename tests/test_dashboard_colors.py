from __future__ import annotations

import unittest
from contextlib import nullcontext
from datetime import datetime, timedelta
from unittest.mock import patch

import pandas as pd

from config import CONFIG
from dashboard_view_shared import (
    apply_status_overlay_above_line,
    build_status_timeline_figure,
    build_component_status_overlay_traces,
    component_color_map,
    machine_status_background_color,
    machine_status_color_map,
)
from dashboard_views import _build_dashboard_air_figure, _build_dashboard_electrical_figure
from live_data import RenderContext
from plotting import LinePlotSpec, build_line_plot_figure
from snapshot_schema import COMPONENT_KEYS
from tab_components_optional import build_component_figure, render_component_showcase_view


def _build_context() -> RenderContext:
    now_dt = datetime.now()
    now_ts = now_dt.timestamp()
    history = [
        {
            "timestamp": now_ts - 10,
            "data_mains": {
                "electrical_Hauptversorgung": 4200,
                "pneumatic_Hauptversorgung": 800,
            },
            "data_components": {
                COMPONENT_KEYS[0]: 1100,
                COMPONENT_KEYS[1]: 900,
            },
            "machine_status": "Processing",
        },
        {
            "timestamp": now_ts - 5,
            "data_mains": {
                "electrical_Hauptversorgung": 4600,
                "pneumatic_Hauptversorgung": 900,
            },
            "data_components": {
                COMPONENT_KEYS[0]: 1200,
                COMPONENT_KEYS[1]: 950,
            },
            "machine_status": "Non-Processing",
        },
    ]
    return RenderContext(
        latest=history[-1],
        history=history,
        window_history=history,
        status={"connected": True, "last_error": "", "ws_url": "ws://test/ws"},
        now_dt=now_dt,
        window_start_dt=now_dt - timedelta(seconds=600),
        window_seconds=600,
        history_capacity=601,
    )


class DashboardColorTests(unittest.TestCase):
    def _build_custom_line_figure(self, values: list[float]) -> object:
        now_dt = datetime.now()
        df = pd.DataFrame(
            {
                "ts": [now_dt - timedelta(seconds=5 * (len(values) - index)) for index in range(len(values))],
                "power": values,
            }
        )
        return build_line_plot_figure(
            df,
            LinePlotSpec(
                x_col="ts",
                y_col="power",
                line_color=CONFIG["ELECTRICAL_PRIMARY_HEX"],
                fill_rgba=CONFIG["ELECTRICAL_FILL_RGBA"],
                marker_color=CONFIG["ELECTRICAL_PRIMARY_HEX"],
                y_title=CONFIG["Y_POWER_TITLE"],
                now_dt=now_dt,
                start_dt=now_dt - timedelta(seconds=600),
                y_min=0,
                y_unit="W",
            ),
        )

    def test_machine_status_color_map_uses_new_blue_tokens(self) -> None:
        color_map = machine_status_color_map()

        self.assertEqual(color_map["Processing"], CONFIG["ELECTRICAL_PRIMARY_HEX"])
        self.assertEqual(color_map["Non-Processing"], CONFIG["ELECTRICAL_SOFT_HEX"])
        self.assertEqual(color_map["Off"], "#9e9e9e")
        self.assertEqual(color_map["E-Stop/Warning"], "#f44336")

    def test_dashboard_main_figures_use_semantic_colors(self) -> None:
        context = _build_context()

        electrical_fig = _build_dashboard_electrical_figure(context)
        pneumatic_fig = _build_dashboard_air_figure(context)

        self.assertIsNotNone(electrical_fig)
        self.assertIsNotNone(pneumatic_fig)

        assert electrical_fig is not None
        assert pneumatic_fig is not None

        self.assertEqual(electrical_fig.data[0].line.color, CONFIG["ELECTRICAL_PRIMARY_HEX"])
        self.assertEqual(electrical_fig.data[1].fillcolor, CONFIG["ELECTRICAL_FILL_RGBA"])
        self.assertEqual(electrical_fig.data[2].marker.color, CONFIG["ELECTRICAL_PRIMARY_HEX"])

        self.assertEqual(pneumatic_fig.data[0].line.color, CONFIG["PNEUMATIC_PRIMARY_HEX"])
        self.assertEqual(pneumatic_fig.data[1].fillcolor, CONFIG["PNEUMATIC_FILL_RGBA"])
        self.assertEqual(pneumatic_fig.data[2].marker.color, CONFIG["PNEUMATIC_PRIMARY_HEX"])
        self.assertEqual(electrical_fig.layout.xaxis.tickformat, "%H:%M")
        self.assertEqual(pneumatic_fig.layout.xaxis.tickformat, "%H:%M")
        self.assertTrue(electrical_fig.layout.yaxis.automargin)
        self.assertEqual(electrical_fig.layout.yaxis.ticklabeloverflow, "allow")
        self.assertTrue(pneumatic_fig.layout.yaxis.automargin)
        self.assertEqual(pneumatic_fig.layout.yaxis.ticklabeloverflow, "allow")

    def test_component_figures_use_monochrome_black(self) -> None:
        context = _build_context()
        component_key = COMPONENT_KEYS[1]
        component_df = pd.DataFrame(
            {
                "ts": [context.now_dt - timedelta(seconds=10), context.now_dt - timedelta(seconds=5)],
                component_key: [1100, 1200],
            }
        )

        color_map = component_color_map()
        fig = build_component_figure(component_df, component_key, context)

        self.assertTrue(all(color == CONFIG["COMPONENT_MONO_HEX"] for color in color_map.values()))
        self.assertIsNotNone(fig)

        assert fig is not None

        self.assertEqual(len(fig.data), 4)
        self.assertEqual(fig.data[0].fillcolor, machine_status_background_color("Processing"))
        self.assertEqual(fig.data[1].line.color, CONFIG["COMPONENT_MONO_HEX"])
        self.assertEqual(fig.data[2].fillcolor, CONFIG["COMPONENT_FILL_RGBA"])
        self.assertEqual(fig.data[3].marker.color, CONFIG["COMPONENT_MONO_HEX"])
        self.assertEqual(fig.layout.xaxis.tickformat, "%H:%M")
        self.assertTrue(fig.layout.yaxis.automargin)
        self.assertEqual(fig.layout.yaxis.ticklabeloverflow, "allow")

    def test_component_plots_use_transparent_current_status_overlays(self) -> None:
        now_dt = datetime.now()
        history = [
            {
                "timestamp": (now_dt - timedelta(seconds=15)).timestamp(),
                "data_mains": {},
                "data_components": {
                    COMPONENT_KEYS[0]: 1050,
                    COMPONENT_KEYS[1]: 850,
                },
                "machine_status": "Processing",
            },
            {
                "timestamp": (now_dt - timedelta(seconds=10)).timestamp(),
                "data_mains": {},
                "data_components": {
                    COMPONENT_KEYS[0]: 1100,
                    COMPONENT_KEYS[1]: 900,
                },
                "machine_status": "Non-Processing",
            },
            {
                "timestamp": (now_dt - timedelta(seconds=5)).timestamp(),
                "data_mains": {},
                "data_components": {
                    COMPONENT_KEYS[0]: 1200,
                    COMPONENT_KEYS[1]: 950,
                },
                "machine_status": "Off",
            },
        ]
        context = RenderContext(
            latest=history[-1],
            history=history,
            window_history=history,
            status={"connected": True, "last_error": "", "ws_url": "ws://test/ws"},
            now_dt=now_dt,
            window_start_dt=now_dt - timedelta(seconds=600),
            window_seconds=600,
            history_capacity=601,
        )
        component_df = pd.DataFrame(
            {
                "ts": [
                    context.now_dt - timedelta(seconds=15),
                    context.now_dt - timedelta(seconds=10),
                    context.now_dt - timedelta(seconds=5),
                ],
                COMPONENT_KEYS[1]: [850, 900, 950],
            }
        )

        fig = build_component_figure(component_df, COMPONENT_KEYS[1], context)

        self.assertIsNotNone(fig)

        assert fig is not None

        self.assertEqual(fig.layout.plot_bgcolor, CONFIG["CHART_PANEL_BG"])
        self.assertEqual(fig.layout.paper_bgcolor, CONFIG["CHART_PANEL_BG"])
        self.assertEqual(fig.data[0].fillcolor, machine_status_background_color("Processing"))
        self.assertEqual(fig.data[1].fillcolor, machine_status_background_color("Non-Processing"))
        self.assertEqual(fig.data[2].line.color, CONFIG["COMPONENT_MONO_HEX"])
        self.assertEqual(fig.data[3].fillcolor, CONFIG["COMPONENT_FILL_RGBA"])
        self.assertEqual(fig.data[4].marker.color, CONFIG["COMPONENT_MONO_HEX"])

    def test_all_component_plots_share_the_same_overlay_build_path(self) -> None:
        context = _build_context()
        first_component_df = pd.DataFrame(
            {
                "ts": [context.now_dt - timedelta(seconds=10), context.now_dt - timedelta(seconds=5)],
                COMPONENT_KEYS[0]: [1100, 1200],
            }
        )
        second_component_df = pd.DataFrame(
            {
                "ts": [context.now_dt - timedelta(seconds=10), context.now_dt - timedelta(seconds=5)],
                COMPONENT_KEYS[1]: [900, 950],
            }
        )

        first_fig = build_component_figure(first_component_df, COMPONENT_KEYS[0], context)
        second_fig = build_component_figure(second_component_df, COMPONENT_KEYS[1], context)

        self.assertIsNotNone(first_fig)
        self.assertIsNotNone(second_fig)

        assert first_fig is not None
        assert second_fig is not None

        self.assertEqual(len(first_fig.data), 4)
        self.assertEqual(len(second_fig.data), 4)
        self.assertEqual(first_fig.data[0].fillcolor, machine_status_background_color("Processing"))
        self.assertEqual(second_fig.data[0].fillcolor, machine_status_background_color("Processing"))
        self.assertEqual(first_fig.data[1].line.color, CONFIG["COMPONENT_MONO_HEX"])
        self.assertEqual(second_fig.data[1].line.color, CONFIG["COMPONENT_MONO_HEX"])

    def test_component_plot_overlay_applies_to_non_heizstation_with_available_history(self) -> None:
        context = _build_context()
        component_df = pd.DataFrame(
            {
                "ts": [context.now_dt - timedelta(seconds=10), context.now_dt - timedelta(seconds=5)],
                COMPONENT_KEYS[1]: [900, 950],
            }
        )

        fig = build_component_figure(component_df, COMPONENT_KEYS[1], context)

        self.assertIsNotNone(fig)

        assert fig is not None

        self.assertEqual(fig.layout.plot_bgcolor, CONFIG["CHART_PANEL_BG"])
        self.assertEqual(fig.layout.paper_bgcolor, CONFIG["CHART_PANEL_BG"])
        self.assertEqual(len(fig.data), 4)
        self.assertEqual(fig.data[0].fillcolor, machine_status_background_color("Processing"))
        self.assertEqual(fig.data[1].line.color, CONFIG["COMPONENT_MONO_HEX"])
        self.assertEqual(fig.data[2].fillcolor, CONFIG["COMPONENT_FILL_RGBA"])
        self.assertEqual(fig.data[3].marker.color, CONFIG["COMPONENT_MONO_HEX"])

    def test_status_overlay_helper_returns_base_figure_for_unknown_status(self) -> None:
        context = _build_context()
        base_fig = self._build_custom_line_figure([1100, 1200])

        with patch("dashboard_view_shared.get_machine_status", return_value="Unknown"):
            overlay_fig = apply_status_overlay_above_line(base_fig, component_key=COMPONENT_KEYS[0], context=context)

        self.assertIs(base_fig, overlay_fig)

    def test_status_overlay_helper_returns_no_traces_for_too_few_points(self) -> None:
        now_dt = datetime.now()
        history = [
            {
                "timestamp": (now_dt - timedelta(seconds=5)).timestamp(),
                "data_mains": {},
                "data_components": {
                    COMPONENT_KEYS[2]: 700,
                },
                "machine_status": "Processing",
            }
        ]
        context = RenderContext(
            latest=history[-1],
            history=history,
            window_history=history,
            status={"connected": True, "last_error": "", "ws_url": "ws://test/ws"},
            now_dt=now_dt,
            window_start_dt=now_dt - timedelta(seconds=600),
            window_seconds=600,
            history_capacity=601,
        )

        traces = build_component_status_overlay_traces(
            component_key=COMPONENT_KEYS[2],
            context=context,
            y_top=1000.0,
        )

        self.assertEqual(traces, [])

    def test_machine_status_timeline_shows_only_time_without_seconds(self) -> None:
        context = _build_context()
        timeline_df = pd.DataFrame(
            {
                "start": [context.now_dt - timedelta(seconds=30)],
                "end": [context.now_dt],
                "cls": ["Processing"],
                "row": ["status"],
            }
        )

        fig = build_status_timeline_figure(timeline_df, context.now_dt, context.window_start_dt)

        self.assertEqual(fig.layout.xaxis.tickformat, "%H:%M")
        self.assertEqual(fig.layout.xaxis.tickfont.size, CONFIG["PLOTLY_TICK_FONT_SIZE"])

    def test_machine_status_timeline_uses_default_and_custom_height(self) -> None:
        context = _build_context()
        timeline_df = pd.DataFrame(
            {
                "start": [context.now_dt - timedelta(seconds=30)],
                "end": [context.now_dt],
                "cls": ["Processing"],
                "row": ["status"],
            }
        )

        default_fig = build_status_timeline_figure(timeline_df, context.now_dt, context.window_start_dt)
        compact_fig = build_status_timeline_figure(
            timeline_df,
            context.now_dt,
            context.window_start_dt,
            height_px=78,
        )

        self.assertEqual(default_fig.layout.height, 156)
        self.assertEqual(compact_fig.layout.height, 78)
        self.assertEqual(default_fig.layout.margin.t, 30)
        self.assertEqual(default_fig.layout.margin.b, CONFIG["PLOTLY_MARGIN_B"])
        self.assertEqual(compact_fig.layout.margin.t, 8)
        self.assertEqual(compact_fig.layout.margin.b, CONFIG["PLOTLY_TICK_FONT_SIZE"] + 12)

    def test_dynamic_y_axis_uses_expected_ticks_for_10000_range(self) -> None:
        fig = self._build_custom_line_figure([0, 10000])

        self.assertEqual(list(fig.layout.yaxis.range), [0, 10000])
        self.assertEqual(list(fig.layout.yaxis.tickvals), [0, 2500, 5000, 7500, 10000])
        self.assertEqual(list(fig.layout.yaxis.ticktext), ["0", "2.500", "5.000", "W", "10.000"])

    def test_dynamic_y_axis_rounds_up_without_exceeding_five_labels(self) -> None:
        fig = self._build_custom_line_figure([0, 10001])

        self.assertEqual(list(fig.layout.yaxis.range), [0, 15000])
        self.assertEqual(list(fig.layout.yaxis.tickvals), [0, 5000, 10000, 15000])
        self.assertEqual(list(fig.layout.yaxis.ticktext), ["0", "5.000", "W", "15.000"])

    def test_dynamic_y_axis_chooses_smaller_nice_range_for_lower_values(self) -> None:
        fig = self._build_custom_line_figure([0, 1100])

        self.assertEqual(list(fig.layout.yaxis.range), [0, 1500])
        self.assertEqual(list(fig.layout.yaxis.tickvals), [0, 500, 1000, 1500])
        self.assertEqual(list(fig.layout.yaxis.ticktext), ["0", "500", "W", "1.500"])

    def test_dynamic_y_axis_uses_minimal_zero_fallback_without_unit_placeholder(self) -> None:
        fig = self._build_custom_line_figure([0, 0, 0])

        self.assertEqual(list(fig.layout.yaxis.range), [0, 1])
        self.assertEqual(list(fig.layout.yaxis.tickvals), [0, 1])
        self.assertEqual(list(fig.layout.yaxis.ticktext), ["0", "1"])

    def test_components_tab_renders_machine_status_panel_before_component_charts(self) -> None:
        context = _build_context()
        call_order: list[tuple[str, object]] = []

        def _record_status_panel(*args, **kwargs) -> None:
            call_order.append(("status", kwargs["height_px"]))

        def _record_component_chart(*args, **kwargs) -> None:
            call_order.append(("component", args[1]))

        with patch("tab_components_optional.render_machine_status_panel", side_effect=_record_status_panel) as status_mock:
            with patch(
                "tab_components_optional.build_component_history_df",
                return_value=pd.DataFrame({"ts": []}),
            ):
                with patch("tab_components_optional.render_component_chart", side_effect=_record_component_chart):
                    with patch("tab_components_optional.st.columns", return_value=(nullcontext(), nullcontext())):
                        render_component_showcase_view(context)

        status_mock.assert_called_once()
        self.assertEqual(call_order[0], ("status", 78))
        self.assertEqual(call_order[1][0], "component")


if __name__ == "__main__":
    unittest.main()
