from __future__ import annotations

import random
import threading
import time
from typing import Any, Dict


def _randi(low: int, high: int) -> int:
    return random.randint(low, high)


_STATUS_OPTIONS = ["Processing", "Non-Processing", "Off", "E-Stop/Warning"]
_INITIAL_STATUS_WEIGHTS = {
    "Non-Processing": 0.5,
    "Processing": 0.3,
    "Off": 0.1,
    "E-Stop/Warning": 0.1,
}
_STATUS_DURATION_RANGES = {
    "Processing": (35, 45),
    "Non-Processing": (20, 25),
    "Off": (30, 40),
    "E-Stop/Warning": (10, 12),
}
_MAIN_ELECTRICAL_RANGES = {
    "Processing": (11750, 12250),
    "Non-Processing": (10000, 10250),
    "E-Stop/Warning": (10000, 10250),
}
_PNEUMATIC_MAIN_RANGE = (4750, 5250)
_HEIZSTATION_LOW_RANGE = (1200, 1250)
_HEIZSTATION_HIGH_RANGE = (4750, 5000)
_HEIZSTATION_CYCLE_SECONDS = 30
_HEIZSTATION_LOW_PHASE_SECONDS = 20
_GENERIC_COMPONENT_RANGES = {
    "component2_Siegelstation": (300, 1500),
    "component3_Kompaktstation": (800, 3000),
    "component4_Formstation": (1800, 1900),
    "component5_3rd_party_component": (100, 800),
    "component6_additional1": (220, 224),
    "component7_additional2": (50, 400),
}
_status_lock = threading.Lock()
_current_status = random.choices(
    population=_STATUS_OPTIONS,
    weights=[_INITIAL_STATUS_WEIGHTS[status] for status in _STATUS_OPTIONS],
    k=1,
)[0]
_status_until_ts = 0.0


def _get_status_duration_seconds(status: str) -> int:
    if status not in _STATUS_DURATION_RANGES:
        raise ValueError(f"Unknown machine status: {status}")

    low, high = _STATUS_DURATION_RANGES[status]
    return random.randint(low, high)


def _get_next_status_weights(current_status: str) -> Dict[str, float]:
    if current_status not in _STATUS_OPTIONS:
        raise ValueError(f"Unknown machine status: {current_status}")

    next_options = [status for status in _STATUS_OPTIONS if status != current_status]
    weights: Dict[str, float] = {}
    remaining_weight = 1.0

    if "Processing" in next_options:
        weights["Processing"] = 0.6
        remaining_weight -= 0.6

    if "E-Stop/Warning" in next_options:
        weights["E-Stop/Warning"] = 0.2
        remaining_weight -= 0.2

    other_options = [status for status in next_options if status not in weights]
    shared_weight = remaining_weight / len(other_options) if other_options else 0.0
    for status in other_options:
        weights[status] = shared_weight

    return {status: weights[status] for status in next_options}


def _choose_next_status(current_status: str) -> str:
    transition_weights = _get_next_status_weights(current_status)
    next_options = list(transition_weights.keys())
    next_weights = [transition_weights[status] for status in next_options]
    return random.choices(population=next_options, weights=next_weights, k=1)[0]


def _get_machine_status() -> str:
    global _current_status, _status_until_ts
    now = time.time()
    with _status_lock:
        if _status_until_ts <= 0.0:
            _status_until_ts = now + _get_status_duration_seconds(_current_status)
        elif now >= _status_until_ts:
            _current_status = _choose_next_status(_current_status)
            _status_until_ts = now + _get_status_duration_seconds(_current_status)
        return _current_status


def _build_main_electrical_value(machine_status: str) -> int:
    if machine_status == "Off":
        return 0
    if machine_status not in _MAIN_ELECTRICAL_RANGES:
        raise ValueError(f"Unknown machine status: {machine_status}")
    return _randi(*_MAIN_ELECTRICAL_RANGES[machine_status])


def _build_main_pneumatic_value() -> int:
    return _randi(*_PNEUMATIC_MAIN_RANGE)


def _build_heizstation_value(machine_status: str, now_ts: float | None = None) -> int:
    if machine_status == "Off":
        return 0
    if machine_status not in _STATUS_OPTIONS:
        raise ValueError(f"Unknown machine status: {machine_status}")

    cycle_second = int(time.time() if now_ts is None else now_ts) % _HEIZSTATION_CYCLE_SECONDS
    cycle_range = (
        _HEIZSTATION_LOW_RANGE
        if cycle_second < _HEIZSTATION_LOW_PHASE_SECONDS
        else _HEIZSTATION_HIGH_RANGE
    )
    return _randi(*cycle_range)


def _get_generic_component_range_for_status(base_range: tuple[int, int], machine_status: str) -> tuple[int, int]:
    low, high = base_range
    if machine_status == "Processing":
        return low, high
    if machine_status in {"Non-Processing", "E-Stop/Warning"}:
        return low // 2, high // 2
    if machine_status == "Off":
        return 0, 0
    raise ValueError(f"Unknown machine status: {machine_status}")


def _build_generic_component_value(base_range: tuple[int, int], machine_status: str) -> int:
    low, high = _get_generic_component_range_for_status(base_range, machine_status)
    if low == 0 and high == 0:
        return 0
    return _randi(low, high)


def build_snapshot() -> Dict[str, Any]:
    """Erzeugt Dummy-Daten im bestehenden Snapshot-Schema."""
    machine_status = _get_machine_status()
    now_ts = time.time()

    comp1 = _build_heizstation_value(machine_status, now_ts=now_ts)
    comp2 = _build_generic_component_value(_GENERIC_COMPONENT_RANGES["component2_Siegelstation"], machine_status)
    comp3 = _build_generic_component_value(_GENERIC_COMPONENT_RANGES["component3_Kompaktstation"], machine_status)
    comp4 = _build_generic_component_value(_GENERIC_COMPONENT_RANGES["component4_Formstation"], machine_status)
    comp5 = _build_generic_component_value(_GENERIC_COMPONENT_RANGES["component5_3rd_party_component"], machine_status)
    comp6 = _build_generic_component_value(_GENERIC_COMPONENT_RANGES["component6_additional1"], machine_status)
    comp7 = _build_generic_component_value(_GENERIC_COMPONENT_RANGES["component7_additional2"], machine_status)

    main_electrical = _build_main_electrical_value(machine_status)
    main_pneumatic = _build_main_pneumatic_value()

    return {
        "timestamp": now_ts,
        "data_mains": {
            "electrical_Hauptversorgung": float(main_electrical),
            "pneumatic_Hauptversorgung": float(main_pneumatic),
        },
        "data_components": {
            "component1_Heizstation": float(comp1),
            "component2_Siegelstation": float(comp2),
            "component3_Kompaktstation": float(comp3),
            "component4_Formstation": float(comp4),
            "component5_3rd_party_component": float(comp5),
            "component6_additional1": float(comp6),
            "component7_additional2": float(comp7),
        },
        "machine_status": machine_status,
    }
