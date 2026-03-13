from __future__ import annotations

import unittest

from live_data import derive_websocket_url, filter_history_window
from snapshot_schema import get_component_display_name, get_machine_status


class LiveDataTests(unittest.TestCase):
    def test_derive_websocket_url_from_http(self) -> None:
        self.assertEqual(derive_websocket_url("http://localhost:8000"), "ws://127.0.0.1:8000/ws")
        self.assertEqual(derive_websocket_url("http://example.com/api"), "ws://example.com/api/ws")

    def test_derive_websocket_url_from_https(self) -> None:
        self.assertEqual(derive_websocket_url("https://factory-x.example"), "wss://factory-x.example/ws")

    def test_filter_history_window_keeps_recent_points(self) -> None:
        history = [
            {"timestamp": 10.0, "value": 1},
            {"timestamp": 15.0, "value": 2},
            {"timestamp": 19.5, "value": 3},
            {"timestamp": "invalid", "value": 4},
        ]
        self.assertEqual(
            filter_history_window(history, window_seconds=5, now_ts=20.0),
            [{"timestamp": 15.0, "value": 2}, {"timestamp": 19.5, "value": 3}],
        )


class SnapshotSchemaTests(unittest.TestCase):
    def test_machine_status_maps_unknown_values(self) -> None:
        self.assertEqual(get_machine_status({"machine_status": "Processing"}), "Processing")
        self.assertEqual(get_machine_status({"machine_status": "weird"}), "Non-Processing")
        self.assertEqual(get_machine_status({"machine_status": ""}), "Off")

    def test_component_display_name_mapping(self) -> None:
        self.assertEqual(get_component_display_name("component1_Heizstation"), "Heizstation")


if __name__ == "__main__":
    unittest.main()
