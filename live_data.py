from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import queue
import threading
import time
from typing import Any, Dict, List

import orjson
import websockets

from config import CONFIG
from data_server import ensure_local_data_server_running
from snapshot_schema import is_valid_snapshot
from utils import append_to_history, initialize_state


LOGGER = logging.getLogger("factory_x_dashboard")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False


@dataclass(frozen=True)
class RenderContext:
    latest: Dict[str, Any] | None
    history: List[Dict[str, Any]]
    window_history: List[Dict[str, Any]]
    status: Dict[str, Any]
    now_dt: datetime
    window_start_dt: datetime
    window_seconds: int
    history_capacity: int


class WebSocketReceiver:
    """Liest den WebSocket-Stream im Hintergrund und puffert Nachrichten threadsicher."""

    def __init__(self, ws_url: str) -> None:
        self.ws_url = ws_url
        self.message_queue: queue.Queue[tuple[Dict[str, Any], str]] = queue.Queue(maxsize=256)
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self._status_lock = threading.Lock()
        self._connected = False
        self._last_error = ""

    def start(self) -> None:
        if self.thread is not None and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run, name="ws-receiver", daemon=True)
        self.thread.start()

    def status_snapshot(self) -> Dict[str, Any]:
        with self._status_lock:
            return {
                "connected": self._connected,
                "last_error": self._last_error,
                "ws_url": self.ws_url,
            }

    def _set_status(self, connected: bool, last_error: str = "") -> None:
        with self._status_lock:
            self._connected = connected
            self._last_error = last_error

    def _enqueue_snapshot(self, payload: Dict[str, Any], raw_text: str) -> None:
        try:
            self.message_queue.put_nowait((payload, raw_text))
        except queue.Full:
            try:
                self.message_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.message_queue.put_nowait((payload, raw_text))
            except queue.Full:
                pass

    def _run(self) -> None:
        asyncio.run(self._listen_forever())

    async def _listen_forever(self) -> None:
        backoff_seconds = 1
        max_backoff_seconds = max(1, int(CONFIG["BUS_POLL_FAIL_BACKOFF_MAX_S"]))
        while not self.stop_event.is_set():
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=1,
                    max_size=None,
                ) as websocket:
                    LOGGER.info("WebSocket verbunden: %s", self.ws_url)
                    self._set_status(True, "")
                    backoff_seconds = 1

                    while not self.stop_event.is_set():
                        raw_message = await websocket.recv()
                        raw_text = raw_message.decode("utf-8") if isinstance(raw_message, bytes) else str(raw_message)
                        payload = orjson.loads(raw_text)
                        if is_valid_snapshot(payload):
                            self._enqueue_snapshot(payload, raw_text)
            except Exception as exc:
                self._set_status(False, str(exc))
                LOGGER.warning("WebSocket getrennt (%s). Neuer Versuch in %ss.", exc, backoff_seconds)
                await asyncio.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, max_backoff_seconds)


def derive_websocket_url(api_base: str | None = None) -> str:
    """Leitet die WebSocket-URL aus der API-Basis ab."""
    base = str(api_base or CONFIG.get("API_BASE") or "http://127.0.0.1:8000").rstrip("/")
    if "localhost" in base:
        base = base.replace("localhost", "127.0.0.1")

    if base.startswith("https://"):
        ws_base = "wss://" + base[len("https://") :]
    elif base.startswith("http://"):
        ws_base = "ws://" + base[len("http://") :]
    else:
        ws_base = f"ws://{base.lstrip('/')}"
    return f"{ws_base}/ws"


def filter_history_window(
    history: List[Dict[str, Any]],
    window_seconds: int,
    now_ts: float,
) -> List[Dict[str, Any]]:
    cutoff_ts = now_ts - window_seconds
    return [
        point
        for point in history
        if isinstance(point, dict)
        and isinstance(point.get("timestamp"), (int, float))
        and float(point["timestamp"]) >= cutoff_ts
    ]


def ensure_state(session_state: Any) -> None:
    initialize_state(session_state)
    session_state.setdefault("latest_snapshot", None)
    session_state.setdefault("latest_raw_text", "")
    session_state.setdefault("_last_data_ts", None)
    session_state.setdefault("_ws_receiver", None)


def get_receiver(session_state: Any) -> WebSocketReceiver:
    ensure_local_data_server_running(CONFIG.get("API_BASE"))
    ws_url = derive_websocket_url()
    receiver = session_state.get("_ws_receiver")
    if not isinstance(receiver, WebSocketReceiver) or receiver.ws_url != ws_url:
        receiver = WebSocketReceiver(ws_url)
        receiver.start()
        session_state["_ws_receiver"] = receiver
    else:
        receiver.start()
    return receiver


def _get_history(session_state: Any) -> List[Dict[str, Any]]:
    history = session_state.get("history", [])
    return history if isinstance(history, list) else []


def _get_latest_snapshot(session_state: Any) -> Dict[str, Any] | None:
    latest = session_state.get("latest_snapshot")
    if isinstance(latest, dict):
        return latest
    history = _get_history(session_state)
    return history[-1] if history else None


def drain_receiver_queue(session_state: Any, max_items: int = 256) -> int:
    receiver = get_receiver(session_state)
    drained = 0
    while drained < max_items:
        try:
            payload, raw_text = receiver.message_queue.get_nowait()
        except queue.Empty:
            break

        append_to_history(session_state, payload, max_points=int(CONFIG["HISTORY_MAX_POINTS"]))
        session_state["latest_snapshot"] = payload
        session_state["latest_raw_text"] = raw_text
        session_state["_last_data_ts"] = payload.get("timestamp")
        drained += 1
    return drained


def build_render_context(session_state: Any) -> RenderContext:
    history = _get_history(session_state)
    latest = _get_latest_snapshot(session_state)
    status = get_receiver(session_state).status_snapshot()
    window_seconds = int(CONFIG["LIVE_WINDOW_SECONDS"])
    now_ts = time.time()
    now_dt = datetime.fromtimestamp(now_ts)
    return RenderContext(
        latest=latest,
        history=history,
        window_history=filter_history_window(history, window_seconds, now_ts),
        status=status,
        now_dt=now_dt,
        window_start_dt=now_dt - timedelta(seconds=window_seconds),
        window_seconds=window_seconds,
        history_capacity=int(CONFIG["HISTORY_MAX_POINTS"]),
    )
