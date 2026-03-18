from __future__ import annotations

import time
import unittest
from unittest.mock import patch

from demo_data import (
    _HEIZSTATION_HIGH_RANGE,
    _HEIZSTATION_LOW_RANGE,
    _build_generic_component_value,
    _build_heizstation_value,
    _build_main_electrical_value,
    _choose_next_status,
    _get_generic_component_range_for_status,
    _get_next_status_weights,
    _get_status_duration_seconds,
)
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


class DemoDataStatusTests(unittest.TestCase):
    def test_status_duration_ranges_are_used_per_status(self) -> None:
        duration_expectations = {
            "Processing": (35, 45, 40),
            "Non-Processing": (20, 25, 22),
            "Off": (30, 40, 35),
            "E-Stop/Warning": (10, 12, 11),
        }

        for status, (low, high, mocked_result) in duration_expectations.items():
            with self.subTest(status=status):
                with patch("demo_data.random.randint", return_value=mocked_result) as randint_mock:
                    self.assertEqual(_get_status_duration_seconds(status), mocked_result)
                randint_mock.assert_called_once_with(low, high)

    def test_transition_weights_from_processing_distribute_remaining_probability_evenly(self) -> None:
        self.assertEqual(
            _get_next_status_weights("Processing"),
            {
                "Non-Processing": 0.4,
                "Off": 0.4,
                "E-Stop/Warning": 0.2,
            },
        )

    def test_transition_weights_prioritize_processing_from_other_states(self) -> None:
        expected_weights = {
            "Non-Processing": {
                "Processing": 0.6,
                "Off": 0.2,
                "E-Stop/Warning": 0.2,
            },
            "Off": {
                "Processing": 0.6,
                "Non-Processing": 0.2,
                "E-Stop/Warning": 0.2,
            },
            "E-Stop/Warning": {
                "Processing": 0.6,
                "Non-Processing": 0.2,
                "Off": 0.2,
            },
        }

        for current_status, expected in expected_weights.items():
            with self.subTest(current_status=current_status):
                self.assertEqual(_get_next_status_weights(current_status), expected)

    def test_transition_weights_never_include_current_status(self) -> None:
        for current_status in ("Processing", "Non-Processing", "Off", "E-Stop/Warning"):
            with self.subTest(current_status=current_status):
                self.assertNotIn(current_status, _get_next_status_weights(current_status))

    def test_choose_next_status_uses_weighted_population_without_current_state(self) -> None:
        with patch("demo_data.random.choices", return_value=["Off"]) as choices_mock:
            self.assertEqual(_choose_next_status("Non-Processing"), "Off")

        choices_mock.assert_called_once_with(
            population=["Processing", "Off", "E-Stop/Warning"],
            weights=[0.6, 0.2, 0.2],
            k=1,
        )

    def test_main_electrical_value_uses_status_specific_ranges_and_off_zero(self) -> None:
        expectations = {
            "Processing": ((11750, 12250), 12010),
            "Non-Processing": ((10000, 10250), 10125),
            "E-Stop/Warning": ((10000, 10250), 10080),
        }

        for status, ((low, high), mocked_result) in expectations.items():
            with self.subTest(status=status):
                with patch("demo_data.random.randint", return_value=mocked_result) as randint_mock:
                    self.assertEqual(_build_main_electrical_value(status), mocked_result)
                randint_mock.assert_called_once_with(low, high)

        with patch("demo_data.random.randint") as randint_mock:
            self.assertEqual(_build_main_electrical_value("Off"), 0)
        randint_mock.assert_not_called()

    def test_generic_component_range_scales_for_non_processing_and_estop(self) -> None:
        base_range = (301, 1501)

        self.assertEqual(_get_generic_component_range_for_status(base_range, "Processing"), base_range)
        self.assertEqual(_get_generic_component_range_for_status(base_range, "Non-Processing"), (150, 750))
        self.assertEqual(_get_generic_component_range_for_status(base_range, "E-Stop/Warning"), (150, 750))
        self.assertEqual(_get_generic_component_range_for_status(base_range, "Off"), (0, 0))

    def test_generic_component_value_uses_scaled_ranges_and_off_zero(self) -> None:
        with patch("demo_data.random.randint", return_value=512) as randint_mock:
            self.assertEqual(_build_generic_component_value((300, 1500), "Processing"), 512)
        randint_mock.assert_called_once_with(300, 1500)

        with patch("demo_data.random.randint", return_value=333) as randint_mock:
            self.assertEqual(_build_generic_component_value((300, 1500), "Non-Processing"), 333)
        randint_mock.assert_called_once_with(150, 750)

        with patch("demo_data.random.randint", return_value=333) as randint_mock:
            self.assertEqual(_build_generic_component_value((300, 1500), "E-Stop/Warning"), 333)
        randint_mock.assert_called_once_with(150, 750)

        with patch("demo_data.random.randint") as randint_mock:
            self.assertEqual(_build_generic_component_value((300, 1500), "Off"), 0)
        randint_mock.assert_not_called()

    def test_heizstation_cycle_uses_low_range_for_first_twenty_seconds(self) -> None:
        with patch("demo_data.random.randint", return_value=1222) as randint_mock:
            self.assertEqual(_build_heizstation_value("Processing", now_ts=19.9), 1222)
        randint_mock.assert_called_once_with(*_HEIZSTATION_LOW_RANGE)

    def test_heizstation_cycle_uses_high_range_for_last_ten_seconds(self) -> None:
        with patch("demo_data.random.randint", return_value=4888) as randint_mock:
            self.assertEqual(_build_heizstation_value("Non-Processing", now_ts=29.1), 4888)
        randint_mock.assert_called_once_with(*_HEIZSTATION_HIGH_RANGE)

    def test_heizstation_value_is_zero_when_machine_is_off(self) -> None:
        with patch("demo_data.random.randint") as randint_mock:
            self.assertEqual(_build_heizstation_value("Off", now_ts=25.0), 0)
        randint_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
