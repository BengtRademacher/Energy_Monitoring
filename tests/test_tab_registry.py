from __future__ import annotations

import unittest
from types import ModuleType
from unittest.mock import patch

from dashboard_tabs import (
    LEGACY_TAB_SPECS,
    OptionalTabSpec,
    TabDefinition,
    build_tab_definitions,
    load_legacy_tab_definitions,
    load_optional_tab_definitions,
)


def _render_stub() -> None:
    return None


class TabRegistryTests(unittest.TestCase):
    def test_build_tab_definitions_includes_dashboard_first(self) -> None:
        tab_definitions = build_tab_definitions(_render_stub)

        self.assertGreaterEqual(len(tab_definitions), 1)
        self.assertEqual(tab_definitions[0].id, "dashboard")
        self.assertEqual(tab_definitions[0].title, "Dashboard")

    def test_missing_optional_module_is_skipped(self) -> None:
        missing_spec = OptionalTabSpec("components", "Komponenten", "definitely_missing_optional_tab.py")

        with patch("dashboard_tabs.VISIBLE_OPTIONAL_TAB_SPECS", (missing_spec,)):
            tab_definitions = load_optional_tab_definitions()

        self.assertEqual(tab_definitions, [])

    def test_invalid_optional_module_is_skipped(self) -> None:
        broken_spec = OptionalTabSpec("components", "Komponenten", "tab_components_optional.py")
        with patch("dashboard_tabs.VISIBLE_OPTIONAL_TAB_SPECS", (broken_spec,)):
            with patch("dashboard_tabs._load_module_from_path", side_effect=RuntimeError("boom")):
                tab_definitions = load_optional_tab_definitions()

        self.assertEqual(tab_definitions, [])

    def test_valid_optional_module_is_loaded(self) -> None:
        custom_spec = OptionalTabSpec("components", "Komponenten", "tab_components_optional.py")
        mock_module = ModuleType("mock_optional_module")

        def _factory() -> TabDefinition:
            return TabDefinition(id="custom", title="Custom", render=_render_stub)

        mock_module.get_optional_tab_definition = _factory

        with patch("dashboard_tabs.VISIBLE_OPTIONAL_TAB_SPECS", (custom_spec,)):
            with patch("dashboard_tabs._load_module_from_path", return_value=mock_module):
                tab_definitions = load_optional_tab_definitions()

        self.assertEqual(len(tab_definitions), 1)
        self.assertIsInstance(tab_definitions[0], TabDefinition)
        self.assertEqual(tab_definitions[0].id, "custom")
        self.assertEqual(tab_definitions[0].title, "Custom")

    def test_build_tab_definitions_excludes_legacy_tabs(self) -> None:
        tab_definitions = build_tab_definitions(_render_stub)

        self.assertTrue(tab_definitions)
        self.assertNotIn("json", [tab_definition.id for tab_definition in tab_definitions])

    def test_legacy_tab_remains_loadable(self) -> None:
        legacy_spec = LEGACY_TAB_SPECS[0]
        mock_module = ModuleType("mock_legacy_module")

        def _factory() -> TabDefinition:
            return TabDefinition(id=legacy_spec.id, title="Legacy JSON", render=_render_stub)

        mock_module.get_optional_tab_definition = _factory

        with patch("dashboard_tabs.LEGACY_TAB_SPECS", (legacy_spec,)):
            with patch("dashboard_tabs._load_module_from_path", return_value=mock_module):
                tab_definitions = load_legacy_tab_definitions()

        self.assertEqual(len(tab_definitions), 1)
        self.assertEqual(tab_definitions[0].id, "json")
        self.assertEqual(tab_definitions[0].title, "JSON-Explorer")


if __name__ == "__main__":
    unittest.main()
