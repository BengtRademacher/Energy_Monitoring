from __future__ import annotations

import asyncio
from dataclasses import dataclass
import os
import socket
import threading
import time
from typing import Any, Dict
from urllib.parse import urlparse
from urllib.request import urlopen

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from demo_data import _PNEUMATIC_MAIN_RANGE, build_snapshot


def create_app() -> FastAPI:
    app = FastAPI(title="Factory-X Dummy Data Server", version="1.0.0")

    @app.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok", "service": "data_server"}

    @app.get("/api/emo/snapshot")
    async def snapshot() -> Dict[str, Any]:
        return build_snapshot()

    @app.get("/data")
    async def data_alias() -> Dict[str, Any]:
        return build_snapshot()

    @app.websocket("/ws")
    async def websocket_snapshot_stream(websocket: WebSocket) -> None:
        """Pusht jede Sekunde einen neuen Snapshot an verbundene Clients."""
        await websocket.accept()
        try:
            while True:
                await websocket.send_json(build_snapshot())
                await asyncio.sleep(1.0)
        except WebSocketDisconnect:
            return

    return app


app = create_app()


@dataclass
class _EmbeddedServerState:
    server: uvicorn.Server | None = None
    thread: threading.Thread | None = None
    base_url: str | None = None
    startup_error: Exception | None = None


class _ThreadedUvicornServer(uvicorn.Server):
    def install_signal_handlers(self) -> None:  # pragma: no cover - required for threaded startup only
        return


_STATE_LOCK = threading.Lock()
_EMBEDDED_SERVER_STATE = _EmbeddedServerState()


def _normalize_api_base(api_base: str | None = None) -> str:
    raw_base = str(api_base or os.getenv("DATA_SERVER_URL") or "http://127.0.0.1:8000").strip()
    if not raw_base:
        return "http://127.0.0.1:8000"
    parsed = urlparse(raw_base)
    if parsed.scheme and parsed.netloc:
        return raw_base.rstrip("/")
    return f"http://{raw_base.lstrip('/')}".rstrip("/")


def _parsed_host_port(api_base: str | None = None) -> tuple[str, int]:
    parsed = urlparse(_normalize_api_base(api_base))
    host = parsed.hostname or "127.0.0.1"
    if parsed.port is not None:
        return host, parsed.port
    return host, 443 if parsed.scheme == "https" else 80


def _is_local_api_base(api_base: str | None = None) -> bool:
    host, _ = _parsed_host_port(api_base)
    return host in {"127.0.0.1", "localhost"}


def _health_url(api_base: str | None = None) -> str:
    return f"{_normalize_api_base(api_base)}/health"


def _is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _healthcheck_ok(api_base: str | None = None, timeout_s: float = 0.5) -> bool:
    try:
        with urlopen(_health_url(api_base), timeout=timeout_s) as response:
            return response.status == 200
    except Exception:
        return False


def _run_embedded_server(host: str, port: int) -> None:
    config = uvicorn.Config(
        app=create_app(),
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )
    server = _ThreadedUvicornServer(config)
    with _STATE_LOCK:
        _EMBEDDED_SERVER_STATE.server = server
        _EMBEDDED_SERVER_STATE.startup_error = None
    try:
        server.run()
    except Exception as exc:  # pragma: no cover - protective branch
        with _STATE_LOCK:
            _EMBEDDED_SERVER_STATE.startup_error = exc
        raise


def ensure_local_data_server_running(api_base: str | None = None, timeout_s: float = 5.0) -> str:
    normalized_base = _normalize_api_base(api_base)
    if not _is_local_api_base(normalized_base):
        return normalized_base

    host, port = _parsed_host_port(normalized_base)
    startup_deadline = time.monotonic() + timeout_s
    should_wait_for_health = False

    with _STATE_LOCK:
        state = _EMBEDDED_SERVER_STATE
        if state.base_url == normalized_base and state.thread is not None and state.thread.is_alive():
            return normalized_base
        elif _healthcheck_ok(normalized_base):
            state.base_url = normalized_base
            return normalized_base
        elif _is_port_open(host, port):
            raise RuntimeError(
                f"Port {port} auf {host} ist bereits belegt, aber {normalized_base}/health antwortet nicht."
            )
        else:
            state.base_url = normalized_base
            state.startup_error = None
            thread = threading.Thread(
                target=_run_embedded_server,
                args=(host, port),
                name=f"embedded-data-server-{port}",
                daemon=True,
            )
            state.thread = thread
            thread.start()
            should_wait_for_health = True

    if not should_wait_for_health:
        return normalized_base

    while time.monotonic() < startup_deadline:
        if _healthcheck_ok(normalized_base):
            return normalized_base
        with _STATE_LOCK:
            state = _EMBEDDED_SERVER_STATE
            startup_error = state.startup_error
            active_thread = state.thread
        if startup_error is not None:
            raise RuntimeError(f"Eingebetteter Data-Server konnte nicht starten: {startup_error}") from startup_error
        if active_thread is None or not active_thread.is_alive():
            raise RuntimeError("Eingebetteter Data-Server wurde beendet, bevor /health erreichbar war.")
        time.sleep(0.05)

    raise RuntimeError(f"Eingebetteter Data-Server wurde innerhalb von {timeout_s:.1f}s nicht erreichbar.")


def stop_local_data_server(timeout_s: float = 2.0) -> None:
    with _STATE_LOCK:
        server = _EMBEDDED_SERVER_STATE.server
        thread = _EMBEDDED_SERVER_STATE.thread

    if server is not None:
        server.should_exit = True

    if thread is not None and thread.is_alive():
        thread.join(timeout=timeout_s)

    with _STATE_LOCK:
        _EMBEDDED_SERVER_STATE.server = None
        _EMBEDDED_SERVER_STATE.thread = None
        _EMBEDDED_SERVER_STATE.base_url = None
        _EMBEDDED_SERVER_STATE.startup_error = None


def get_local_server_status() -> Dict[str, Any]:
    with _STATE_LOCK:
        thread = _EMBEDDED_SERVER_STATE.thread
        return {
            "managed": thread is not None,
            "running": bool(thread and thread.is_alive()),
            "base_url": _EMBEDDED_SERVER_STATE.base_url,
            "thread_ident": thread.ident if thread is not None else None,
            "startup_error": str(_EMBEDDED_SERVER_STATE.startup_error or ""),
        }


def main() -> None:
    port = int(os.getenv("DATA_SERVER_PORT", "8000"))
    host = os.getenv("DATA_SERVER_HOST", "127.0.0.1")
    print(f"data_server laeuft auf http://{host}:{port}")
    print("Endpunkte: /ws, /api/emo/snapshot, /data, /health")
    uvicorn.run(app, host=host, port=port, log_level="info", access_log=False)


if __name__ == "__main__":
    main()
