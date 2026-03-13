from __future__ import annotations

import time
import unittest

from live_data import DemoReceiver, derive_websocket_url, filter_history_window, resolve_data_source_mode
from snapshot_schema import get_component_display_name, get_machine_status


class LiveDataTests(unittest.TestCase):
    def test_derive_websocket_url_from_http(self) -> None:
        self.assertEqual(derive_websocket_url("http://localhost:8000"), "ws://127.0.0.1:8000/ws")
        self.assertEqual(derive_websocket_url("http://example.com/api"), "ws://example.com/api/ws")

    def test_derive_websocket_url_from_https(self) -> None:
        self.assertEqual(derive_websocket_url("https://factory-x.example"), "wss://factory-x.example/ws")

    def test_resolve_data_source_mode_defaults_to_demo_without_url(self) -> None:
        self.assertEqual(resolve_data_source_mode(source_mode="", api_base=""), "demo")

    def test_resolve_data_source_mode_prefers_external_when_url_exists(self) -> None:
        self.assertEqual(resolve_data_source_mode(source_mode="", api_base="https://factory-x.example"), "external")

    def test_resolve_data_source_mode_honors_explicit_demo(self) -> None:
        self.assertEqual(resolve_data_source_mode(source_mode="demo", api_base="https://factory-x.example"), "demo")

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

    def test_demo_receiver_emits_valid_snapshot_payloads(self) -> None:
        receiver = DemoReceiver(refresh_interval_s=0.01)
        try:
            receiver.start()
            deadline = time.time() + 1.0
            while receiver.message_queue.empty() and time.time() < deadline:
                time.sleep(0.02)

            payload, raw_text = receiver.message_queue.get_nowait()
        finally:
            receiver.stop()

        self.assertIn("timestamp", payload)
        self.assertIn("machine_status", payload)
        self.assertTrue(raw_text)


class SnapshotSchemaTests(unittest.TestCase):
    def test_machine_status_maps_unknown_values(self) -> None:
        self.assertEqual(get_machine_status({"machine_status": "Processing"}), "Processing")
        self.assertEqual(get_machine_status({"machine_status": "weird"}), "Non-Processing")
        self.assertEqual(get_machine_status({"machine_status": ""}), "Off")

    def test_component_display_name_mapping(self) -> None:
        self.assertEqual(get_component_display_name("component1_Heizstation"), "Heizstation")


if __name__ == "__main__":
    unittest.main()
