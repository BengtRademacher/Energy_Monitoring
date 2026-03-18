from __future__ import annotations

import importlib.util
import logging
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable

from config import CONFIG


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class TabDefinition:
    id: str
    title: str
    render: Callable[[], None]


@dataclass(frozen=True)
class OptionalTabSpec:
    id: str
    default_title: str
    filename: str


VISIBLE_OPTIONAL_TAB_SPECS: tuple[OptionalTabSpec, ...] = (
    OptionalTabSpec(id="components", default_title="Komponenten", filename="tab_components_optional.py"),
    OptionalTabSpec(id="info", default_title="Zusatzinformationen", filename="tab_additional_info_optional.py"),
)


LEGACY_TAB_SPECS: tuple[OptionalTabSpec, ...] = (
    OptionalTabSpec(id="json", default_title="JSON-Explorer", filename="tab_json_explorer_optional.py"),
)


def resolve_tab_title(tab_id: str, default_title: str) -> str:
    if tab_id == "dashboard":
        return "Dashboard"

    configured_titles = CONFIG.get("TAB_TITLES")
    if isinstance(configured_titles, dict):
        configured_title = configured_titles.get(tab_id)
        if isinstance(configured_title, str) and configured_title.strip():
            return configured_title.strip()
    return default_title


def build_tab_definitions(core_render: Callable[[], None]) -> list[TabDefinition]:
    return [
        TabDefinition(id="dashboard", title="Dashboard", render=core_render),
        *load_optional_tab_definitions(),
    ]


def load_optional_tab_definitions() -> list[TabDefinition]:
    return _load_tab_definitions(VISIBLE_OPTIONAL_TAB_SPECS)


def load_legacy_tab_definitions() -> list[TabDefinition]:
    return _load_tab_definitions(LEGACY_TAB_SPECS)


def _load_tab_definitions(tab_specs: tuple[OptionalTabSpec, ...]) -> list[TabDefinition]:
    tab_definitions: list[TabDefinition] = []
    for spec in tab_specs:
        loaded_definition = _load_optional_tab_definition(spec)
        if loaded_definition is not None:
            tab_definitions.append(loaded_definition)
    return tab_definitions


def _load_optional_tab_definition(spec: OptionalTabSpec) -> TabDefinition | None:
    module_path = Path(__file__).resolve().with_name(spec.filename)
    if not module_path.exists():
        return None

    try:
        module = _load_module_from_path(module_path, spec.id)
        factory = getattr(module, "get_optional_tab_definition", None)
        if not callable(factory):
            LOGGER.warning("Optionales Tab-Modul %s exportiert keine Factory.", module_path.name)
            return None

        tab_definition = factory()
        if not _is_valid_tab_definition(tab_definition):
            LOGGER.warning("Optionales Tab-Modul %s liefert keine gueltige TabDefinition.", module_path.name)
            return None

        return TabDefinition(
            id=tab_definition.id,
            title=resolve_tab_title(tab_definition.id, tab_definition.title or spec.default_title),
            render=tab_definition.render,
        )
    except Exception:
        LOGGER.exception("Optionales Tab-Modul %s konnte nicht geladen werden.", module_path.name)
        return None


def _load_module_from_path(module_path: Path, module_id: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"factory_x_optional_tab_{module_id}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Kein Modul-Spec fuer {module_path.name} verfuegbar.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _is_valid_tab_definition(candidate: object) -> candidate is TabDefinition:
    return (
        isinstance(candidate, TabDefinition)
        and isinstance(candidate.id, str)
        and bool(candidate.id.strip())
        and isinstance(candidate.title, str)
        and bool(candidate.title.strip())
        and callable(candidate.render)
    )
