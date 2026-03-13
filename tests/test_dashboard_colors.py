from __future__ import annotations

import unittest
from datetime import datetime, timedelta

import pandas as pd

from config import CONFIG
from dashboard_view_shared import build_status_timeline_figure, component_color_map, machine_status_color_map
from dashboard_views import _build_dashboard_air_figure, _build_dashboard_electrical_figure
from live_data import RenderContext
from plotting import LinePlotSpec, build_line_plot_figure
from snapshot_schema import COMPONENT_KEYS
from tab_components_optional import build_component_figure


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
        component_df = pd.DataFrame(
            {
                "ts": [context.now_dt - timedelta(seconds=10), context.now_dt - timedelta(seconds=5)],
                COMPONENT_KEYS[0]: [1100, 1200],
            }
        )

        color_map = component_color_map()
        fig = build_component_figure(component_df, COMPONENT_KEYS[0], context)

        self.assertTrue(all(color == CONFIG["COMPONENT_MONO_HEX"] for color in color_map.values()))
        self.assertIsNotNone(fig)

        assert fig is not None

        self.assertEqual(fig.data[0].line.color, CONFIG["COMPONENT_MONO_HEX"])
        self.assertEqual(fig.data[1].fillcolor, CONFIG["COMPONENT_FILL_RGBA"])
        self.assertEqual(fig.data[2].marker.color, CONFIG["COMPONENT_MONO_HEX"])
        self.assertEqual(fig.layout.xaxis.tickformat, "%H:%M")
        self.assertTrue(fig.layout.yaxis.automargin)
        self.assertEqual(fig.layout.yaxis.ticklabeloverflow, "allow")

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


if __name__ == "__main__":
    unittest.main()
