from __future__ import annotations

import random
import threading
import time
from typing import Any, Dict


def _randi(low: int, high: int) -> int:
    return random.randint(low, high)


_STATUS_OPTIONS = ["Processing", "Non-Processing", "Off", "E-Stop/Warning"]
_STATUS_WEIGHTS = {
    "Non-Processing": 0.5,
    "Processing": 0.3,
    "Off": 0.1,
    "E-Stop/Warning": 0.1,
}
_PNEUMATIC_MAIN_RANGE = (1700, 2300)
_status_lock = threading.Lock()
_current_status = random.choices(
    population=_STATUS_OPTIONS,
    weights=[_STATUS_WEIGHTS[status] for status in _STATUS_OPTIONS],
    k=1,
)[0]
_status_until_ts = 0.0


def _choose_next_status(current_status: str) -> str:
    next_options = [status for status in _STATUS_OPTIONS if status != current_status]
    next_weights = [_STATUS_WEIGHTS[status] for status in next_options]
    return random.choices(population=next_options, weights=next_weights, k=1)[0]


def _get_machine_status() -> str:
    global _current_status, _status_until_ts
    now = time.time()
    with _status_lock:
        if now >= _status_until_ts:
            _current_status = _choose_next_status(_current_status)
            _status_until_ts = now + random.uniform(5.0, 12.0)
        return _current_status


def build_snapshot() -> Dict[str, Any]:
    """Erzeugt Dummy-Daten im bestehenden Snapshot-Schema."""
    comp1 = _randi(3500, 4200)
    comp2 = _randi(300, 1500)
    comp3 = _randi(800, 3000)
    comp4 = _randi(1800, 1900)
    comp5 = _randi(100, 800)
    comp6 = _randi(220, 224)
    comp7 = _randi(50, 400)

    main_electrical = comp1 + comp2 + comp3 + comp4 + comp5 + comp6 + comp7
    main_pneumatic = _randi(*_PNEUMATIC_MAIN_RANGE)
    machine_status = _get_machine_status()

    return {
        "timestamp": time.time(),
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
