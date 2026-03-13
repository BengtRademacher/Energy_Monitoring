from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from config import CONFIG
from snapshot_schema import (
    COMPONENT_KEYS,
    get_component_display_name,
    get_component_value,
    get_machine_status,
    get_main_electrical,
    get_main_pneumatic,
)


def initialize_state(session_state: Any) -> None:
    """Initialisiert den Session-State fuer den Zeitverlauf."""
    if "history" not in session_state:
        session_state["history"] = []


def append_to_history(
    session_state: Any,
    point: Dict[str, Any],
    max_points: int = CONFIG["HISTORY_MAX_POINTS"],
) -> None:
    """Haengt einen Messpunkt an und begrenzt die Historie."""
    session_state["history"].append(point)
    if len(session_state["history"]) > max_points:
        session_state["history"] = session_state["history"][-max_points:]


def _history_signature(history: List[Dict[str, Any]]) -> tuple[int, float | None]:
    if not history:
        return (0, None)
    last_ts = history[-1].get("timestamp") if isinstance(history[-1], dict) else None
    last_ts_f = float(last_ts) if isinstance(last_ts, (int, float)) else None
    return (len(history), last_ts_f)


def _window_cutoff(window_seconds: int | None = None) -> float:
    effective_window_seconds = window_seconds or int(CONFIG["LIVE_WINDOW_SECONDS"])
    return time.time() - effective_window_seconds


@st.cache_data(ttl=CONFIG["PLOT_CACHE_TTL_S"])
def build_line_df_cached(
    sig: tuple[int, float | None],
    history: List[Dict[str, Any]],
    window_seconds: int,
) -> pd.DataFrame:
    """Cached version of build_line_df."""
    if not history:
        return pd.DataFrame(columns=["time", "ts", "electric_w"])

    cutoff_ts = _window_cutoff(window_seconds)
    pc_offset = 0.0
    try:
        pc_offset = float(st.session_state.get("process_cooling", 0.0))
    except Exception:
        pc_offset = 0.0

    rows: List[Dict[str, Any]] = []
    for point in history:
        ts = point.get("timestamp")
        if ts is None or ts < cutoff_ts:
            continue

        value = get_main_electrical(point)
        if value is not None:
            value += pc_offset
        rows.append(
            {
                "time": datetime.fromtimestamp(ts).strftime("%H:%M:%S"),
                "ts": datetime.fromtimestamp(ts),
                "electric_w": value,
            }
        )
    return pd.DataFrame(rows)


def build_line_df(history: List[Dict[str, Any]], window_seconds: int | None = None) -> pd.DataFrame:
    signature = _history_signature(history)
    effective_window_seconds = window_seconds or int(CONFIG["LIVE_WINDOW_SECONDS"])
    return build_line_df_cached(signature, history, effective_window_seconds)


def translate_component_name(signal_key: str) -> str:
    return get_component_display_name(signal_key)


def build_bar_df(point: Dict[str, Any]) -> pd.DataFrame:
    """Erzeugt ein DataFrame fuer den Balken-Chart der Komponenten."""
    variables: List[str] = []
    values: List[float | None] = []

    for key in COMPONENT_KEYS:
        variables.append(key)
        values.append(get_component_value(point, key))

    df = pd.DataFrame({"variable": variables, "value": values})
    if not df.empty:
        df["variable_display"] = df["variable"].apply(translate_component_name)
        df["variable"] = df["variable"].astype("string")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def _extract_generic_value(point: Dict[str, Any], extractor_key: str) -> Any:
    if extractor_key == "airpower_main":
        return get_main_pneumatic(point)
    raise ValueError(f"Unknown extractor_key: {extractor_key}")


@st.cache_data(ttl=CONFIG["PLOT_CACHE_TTL_S"])
def build_generic_line_df_cached(
    sig: tuple[int, float | None],
    history: List[Dict[str, Any]],
    extractor_key: str,
    value_col: str,
    window_seconds: int,
) -> pd.DataFrame:
    if not history:
        return pd.DataFrame(columns=["time", "ts", value_col])

    cutoff_ts = _window_cutoff(window_seconds)
    rows: List[Dict[str, Any]] = []
    for point in history:
        ts = point.get("timestamp")
        if ts is None or ts < cutoff_ts:
            continue
        try:
            value = _extract_generic_value(point, extractor_key)
        except Exception:
            value = None
        rows.append(
            {
                "time": datetime.fromtimestamp(ts).strftime("%H:%M:%S"),
                "ts": datetime.fromtimestamp(ts),
                value_col: value,
            }
        )
    return pd.DataFrame(rows)


def build_generic_line_df(
    history: List[Dict[str, Any]],
    extractor_key: str,
    value_col: str = "value",
    window_seconds: int | None = None,
) -> pd.DataFrame:
    signature = _history_signature(history)
    effective_window_seconds = window_seconds or int(CONFIG["LIVE_WINDOW_SECONDS"])
    return build_generic_line_df_cached(
        signature,
        history,
        extractor_key,
        value_col,
        effective_window_seconds,
    )


@st.cache_data(ttl=CONFIG["PLOT_CACHE_TTL_S"])
def build_component_history_df_cached(
    sig: tuple[int, float | None],
    history: List[Dict[str, Any]],
    window_seconds: int,
) -> pd.DataFrame:
    columns = ["time", "ts", *COMPONENT_KEYS]
    if not history:
        return pd.DataFrame(columns=columns)

    cutoff_ts = _window_cutoff(window_seconds)
    rows: List[Dict[str, Any]] = []
    for point in history:
        ts = point.get("timestamp")
        if ts is None or ts < cutoff_ts:
            continue

        row: Dict[str, Any] = {
            "time": datetime.fromtimestamp(ts).strftime("%H:%M:%S"),
            "ts": datetime.fromtimestamp(ts),
        }
        for component_key in COMPONENT_KEYS:
            row[component_key] = get_component_value(point, component_key)
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns)


def build_component_history_df(
    history: List[Dict[str, Any]],
    window_seconds: int | None = None,
) -> pd.DataFrame:
    signature = _history_signature(history)
    effective_window_seconds = window_seconds or int(CONFIG["LIVE_WINDOW_SECONDS"])
    return build_component_history_df_cached(signature, history, effective_window_seconds)


@st.cache_data(ttl=CONFIG["PLOT_CACHE_TTL_S"])
def build_status_timeline_df_cached(
    sig: tuple[int, float | None],
    history: List[Dict[str, Any]],
    window_seconds: int,
) -> pd.DataFrame:
    if not history:
        return pd.DataFrame(columns=["start", "end", "cls", "row"])

    now_ts = time.time()
    cutoff_ts = now_ts - window_seconds
    points: List[Dict[str, Any]] = []
    for point in history:
        ts = point.get("timestamp")
        if ts is None or ts < cutoff_ts:
            continue
        points.append({"ts": float(ts), "cls": get_machine_status(point)})

    if not points:
        return pd.DataFrame(columns=["start", "end", "cls", "row"])

    points.sort(key=lambda entry: entry["ts"])
    segments: List[Dict[str, Any]] = []
    current_cls: str | None = None
    seg_start_ts: float | None = None

    for point in points:
        point_cls = point["cls"]
        if current_cls is None:
            current_cls = point_cls
            seg_start_ts = point["ts"]
            continue
        if point_cls != current_cls:
            segments.append({"start": seg_start_ts, "end": point["ts"], "cls": current_cls})
            current_cls = point_cls
            seg_start_ts = point["ts"]

    if current_cls is not None and seg_start_ts is not None:
        segments.append({"start": seg_start_ts, "end": now_ts, "cls": current_cls})

    clamped: List[Dict[str, Any]] = []
    for segment in segments:
        start = max(float(segment["start"]), cutoff_ts)
        end = min(float(segment["end"]), now_ts)
        if end <= start:
            continue
        clamped.append(
            {
                "start": datetime.fromtimestamp(start),
                "end": datetime.fromtimestamp(end),
                "cls": segment["cls"],
                "row": "status",
            }
        )

    return pd.DataFrame(clamped)


def build_status_timeline_df(history: List[Dict[str, Any]], window_seconds: int = 600) -> pd.DataFrame:
    signature = _history_signature(history)
    return build_status_timeline_df_cached(signature, history, window_seconds)


def find_image_path(basename_without_ext: str) -> str | None:
    """Sucht eine Bilddatei im Ordner 'logos' relativ zu Datei oder CWD."""
    candidates = [f"{basename_without_ext}{ext}" for ext in [".png", ".jpg", ".jpeg", ".svg"]]
    here = Path(__file__).resolve().parent
    cwd = Path.cwd()
    search_dirs = [here / "logos", cwd / "logos"]
    for candidate in candidates:
        for base in search_dirs:
            path = base / candidate
            if path.exists():
                return str(path)
    return None
