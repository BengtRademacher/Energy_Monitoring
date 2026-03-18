from __future__ import annotations

import socket
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from data_server import (
    _EMBEDDED_SERVER_STATE,
    _PNEUMATIC_MAIN_RANGE,
    build_snapshot,
    create_app,
    ensure_local_data_server_running,
    get_local_server_status,
    stop_local_data_server,
)
from demo_data import _MAIN_ELECTRICAL_RANGES
from snapshot_schema import is_valid_snapshot


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class DataServerTests(unittest.TestCase):
    def tearDown(self) -> None:
        stop_local_data_server()

    def test_pneumatic_main_supply_uses_requested_range(self) -> None:
        low, high = _PNEUMATIC_MAIN_RANGE

        for _ in range(50):
            snapshot = build_snapshot()
            pneumatic = snapshot["data_mains"]["pneumatic_Hauptversorgung"]
            self.assertGreaterEqual(pneumatic, low)
            self.assertLessEqual(pneumatic, high)

    def test_electrical_main_supply_uses_status_specific_ranges(self) -> None:
        for status, (low, high) in _MAIN_ELECTRICAL_RANGES.items():
            with self.subTest(status=status):
                with patch("demo_data._get_machine_status", return_value=status):
                    for _ in range(20):
                        snapshot = build_snapshot()
                        electrical = snapshot["data_mains"]["electrical_Hauptversorgung"]
                        self.assertGreaterEqual(electrical, low)
                        self.assertLessEqual(electrical, high)

    def test_off_status_zeroes_electrical_main_and_all_components(self) -> None:
        with patch("demo_data._get_machine_status", return_value="Off"):
            snapshot = build_snapshot()

        self.assertEqual(snapshot["data_mains"]["electrical_Hauptversorgung"], 0.0)
        self.assertEqual(
            snapshot["data_components"],
            {
                "component1_Heizstation": 0.0,
                "component2_Siegelstation": 0.0,
                "component3_Kompaktstation": 0.0,
                "component4_Formstation": 0.0,
                "component5_3rd_party_component": 0.0,
                "component6_additional1": 0.0,
                "component7_additional2": 0.0,
            },
        )

    def test_health_endpoint_reports_server_status(self) -> None:
        with TestClient(create_app()) as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "data_server"})

    def test_snapshot_endpoint_returns_valid_snapshot(self) -> None:
        with TestClient(create_app()) as client:
            response = client.get("/api/emo/snapshot")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(is_valid_snapshot(response.json()))

    def test_websocket_endpoint_streams_snapshots(self) -> None:
        with TestClient(create_app()) as client:
            with client.websocket_connect("/ws") as websocket:
                payload = websocket.receive_json()

        self.assertTrue(is_valid_snapshot(payload))

    def test_embedded_server_starts_only_once(self) -> None:
        port = _find_free_port()
        api_base = f"http://127.0.0.1:{port}"

        self.assertEqual(ensure_local_data_server_running(api_base), api_base)
        first_status = get_local_server_status()

        self.assertEqual(ensure_local_data_server_running(api_base), api_base)
        second_status = get_local_server_status()

        self.assertTrue(first_status["running"])
        self.assertEqual(first_status["thread_ident"], second_status["thread_ident"])

    def test_external_data_server_url_skips_embedded_server_start(self) -> None:
        api_base = "https://factory-x.example"

        self.assertEqual(ensure_local_data_server_running(api_base), api_base)
        status = get_local_server_status()

        self.assertFalse(status["managed"])
        self.assertFalse(status["running"])

    def test_embedded_server_is_healthy_before_returning(self) -> None:
        port = _find_free_port()
        api_base = f"http://127.0.0.1:{port}"

        self.assertEqual(ensure_local_data_server_running(api_base), api_base)
        status = get_local_server_status()

        self.assertTrue(status["running"])
        self.assertEqual(status["base_url"], api_base)

    def test_running_embedded_server_skips_repeated_healthchecks(self) -> None:
        api_base = "http://127.0.0.1:8000"

        class _AliveThread:
            ident = 123

            @staticmethod
            def is_alive() -> bool:
                return True

        with patch.object(_EMBEDDED_SERVER_STATE, "base_url", api_base):
            with patch.object(_EMBEDDED_SERVER_STATE, "thread", _AliveThread()):
                with patch("data_server._healthcheck_ok") as healthcheck_mock:
                    self.assertEqual(ensure_local_data_server_running(api_base), api_base)

        healthcheck_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
