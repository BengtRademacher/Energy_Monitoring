"""
Zentralisierte Laufzeitkonfiguration fuer Dashboard und Daten-Server.

Alle Werte sind per Umgebungsvariablen ueberschreibbar. Sinnvolle Defaults
ermoeglichen einen sofortigen Start ohne zusaetzliche Parametrierung.
"""

from __future__ import annotations

import os
from typing import Any, Dict


def _get_env_str(name: str, default: str) -> str:
    return os.getenv(name, str(default))


def _get_first_env_str(names: tuple[str, ...], default: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()
    return str(default)


def _get_env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _get_env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def _get_env_bool(name: str, default: bool) -> bool:
    try:
        value = os.getenv(name)
        if value is None:
            return bool(default)
        normalized = value.strip().lower()
        if normalized in ("1", "true", "t", "yes", "y", "on"):
            return True
        if normalized in ("0", "false", "f", "no", "n", "off"):
            return False
        return bool(default)
    except Exception:
        return bool(default)


def _get_sensor_names() -> list[str]:
    csv = os.getenv("SENSOR_NAMES_CSV", "").strip()
    if csv:
        names = [part.strip() for part in csv.split(",") if part.strip()]
        if len(names) >= 7:
            return names[:7]
    return [
        "Heizstation",
        "Siegelstation",
        "Kompaktstation",
        "Formstation",
        "Komponente eines Drittanbieters",
        "Zusatzkomponente 1",
        "Zusatzkomponente 2",
    ]


def _resolve_data_source_mode() -> str:
    configured_mode = os.getenv("DATA_SOURCE_MODE", "").strip().lower()
    if configured_mode in {"demo", "external"}:
        return configured_mode

    configured_api_base = os.getenv("DATA_SERVER_URL", "").strip()
    return "external" if configured_api_base else "demo"


_default_api_base = _get_env_str("DATA_SERVER_URL", "").rstrip("/")
_data_source_mode = _resolve_data_source_mode()

_accent_tier1 = _get_env_str("ACCENT_TIER1", "#88b9dc")
_accent_tier2 = _get_env_str("ACCENT_TIER2", "#d0e487")
_title_text = _get_env_str("EMO_TITLE", "Energy Monitoring")
_ifw_brand_blue = _get_env_str("IFW_BRAND_BLUE", "#1f4e79")
_electrical_primary_hex = _get_env_str("ELECTRICAL_PRIMARY_HEX", "#1A75B8")
_electrical_soft_hex = _get_env_str("ELECTRICAL_SOFT_HEX", "#87BBE0")
_electrical_fill_rgba = _get_env_str("ELECTRICAL_FILL_RGBA", "rgba(26,117,184,0.14)")
_pneumatic_primary_hex = _get_env_str("PNEUMATIC_PRIMARY_HEX", "#B1CB21")
_pneumatic_fill_rgba = _get_env_str("PNEUMATIC_FILL_RGBA", "rgba(177,203,33,0.16)")
_component_mono_hex = _get_env_str("COMPONENT_MONO_HEX", "#000000")
_component_fill_rgba = _get_env_str("COMPONENT_FILL_RGBA", "rgba(0,0,0,0.08)")

_live_window_seconds = _get_env_int("LIVE_WINDOW_SECONDS", 600)
_websocket_rate_hz = max(1, _get_env_int("WEBSOCKET_RATE_HZ", 1))
_demo_refresh_seconds = 1.0 / float(_websocket_rate_hz)
_history_max_points_override = _get_env_int("EMO_HISTORY_MAX_POINTS", 0)
_history_max_points = (
    _history_max_points_override
    if _history_max_points_override > 0
    else max(2, _live_window_seconds * _websocket_rate_hz + 1)
)

_sensor_names = _get_sensor_names()

_widget_border_width_px = _get_env_int("WIDGET_BORDER_WIDTH_PX", 8)
_widget_border_radius_px = _get_env_int("WIDGET_BORDER_RADIUS_PX", 8)
_widget_padding_rem = _get_env_float("WIDGET_PADDING_REM", 0.75)
_top_padding_rem = _get_env_float("TOP_PADDING_REM", 0.0)
_card_surface_bg = _get_env_str("CARD_SURFACE_BG", "rgba(243, 244, 246, 0.92)")
_card_surface_border = _get_env_str("CARD_SURFACE_BORDER", "rgba(156, 163, 175, 0.24)")
_panel_bg_outer = _get_env_str("PANEL_BG_OUTER", "rgba(242,242,242,0.95)")
_panel_border_outer = _get_env_str("PANEL_BORDER_OUTER", "rgba(190,190,190,0.80)")
_panel_bg_inner = _get_env_str("PANEL_BG_INNER", "rgba(222,226,232,0.96)")
_panel_border_inner = _get_env_str("PANEL_BORDER_INNER", "rgba(160,168,180,0.95)")
_chart_panel_bg = _get_env_str("CHART_PANEL_BG", "rgba(234,238,243,0.92)")
_chart_grid_color = _get_env_str("CHART_GRID_COLOR", "rgba(160,168,180,0.35)")
_ui_font_family = _get_env_str("UI_FONT_FAMILY", 'Aptos, "Segoe UI", Arial, sans-serif')
_font_weight_regular = _get_env_int("FONT_WEIGHT_REGULAR", 400)
_font_weight_semibold = _get_env_int("FONT_WEIGHT_SEMIBOLD", 600)
_font_weight_bold = _get_env_int("FONT_WEIGHT_BOLD", 700)

_logo_ifw = _get_env_str("LOGO_IFW_BASENAME", "logo_firma")
_logo_fx = _get_env_str("LOGO_FX_BASENAME", "logo_f\u00f6rderung")
_logo_meta = _get_env_str("LOGO_META_BASENAME", "logo_dmp70")

_tab_titles = {
    "components": _get_first_env_str(("TAB_COMPONENTS_TITLE", "TAB_2_TITLE", "TAB_3_TITLE"), "Komponenten"),
    "info": _get_first_env_str(("TAB_ADDITIONAL_INFO_TITLE", "TAB_3_TITLE", "TAB_4_TITLE"), "Zusatzinformationen"),
    "json": _get_first_env_str(("TAB_JSON_EXPLORER_TITLE", "TAB_4_TITLE", "TAB_5_TITLE"), "JSON-Explorer"),
}

_plotly_default_height_px = _get_env_int("PLOTLY_DEFAULT_HEIGHT_PX", 300)
_component_plot_height_px = _get_env_int("COMPONENT_PLOT_HEIGHT_PX", 260)
_plotly_margin_l = _get_env_int("PLOTLY_MARGIN_L", 10)
_plotly_margin_r = _get_env_int("PLOTLY_MARGIN_R", 10)
_plotly_margin_t = _get_env_int("PLOTLY_MARGIN_T", 10)
_plotly_margin_b = _get_env_int("PLOTLY_MARGIN_B", 10)
_plotly_font_family = _get_env_str("PLOTLY_FONT_FAMILY", _ui_font_family)
_plotly_title_font_size = _get_env_int("PLOTLY_TITLE_FONT_SIZE", 18)
_plotly_axis_title_font_size = _get_env_int("PLOTLY_AXIS_TITLE_FONT_SIZE", 20)
_plotly_tick_font_size = _get_env_int("PLOTLY_TICK_FONT_SIZE", 20)
_plotly_legend_font_size = _get_env_int("PLOTLY_LEGEND_FONT_SIZE", 14)
_plotly_line_width = _get_env_float("PLOTLY_LINE_WIDTH", 2.0)
_plotly_marker_size = _get_env_int("PLOTLY_MARKER_SIZE", 15)
_plotly_showgrid = _get_env_bool("PLOTLY_SHOWGRID", True)
_plotly_grid_color = _get_env_str("PLOTLY_GRID_COLOR", "#e0e0e0")
_plotly_grid_width = _get_env_float("PLOTLY_GRID_WIDTH", 1.0)
_plotly_time_range_step_s = _get_env_int("PLOTLY_TIME_RANGE_STEP_S", 5)

_x_axis_title = _get_env_str("X_AXIS_TITLE", "Zeit")
_y_power_title = _get_env_str("Y_POWER_TITLE", "Leistung in W")
_y_component_title = _get_env_str("Y_COMPONENT_TITLE", "Leistung in W")
_x_component_title = _get_env_str("X_COMPONENT_TITLE", "Komponente")
_plot_cache_ttl_s = _get_env_int("PLOT_CACHE_TTL_S", 15)
_bus_poll_fail_backoff_max_s = _get_env_int("BUS_POLL_FAIL_BACKOFF_MAX_S", 8)
_component_plot_colors = [
    "#4f83cc",
    "#2a9d8f",
    "#f4a261",
    "#e76f51",
    "#6d597a",
    "#8ab17d",
    "#577590",
]

CONFIG: Dict[str, Any] = {
    "API_BASE": _default_api_base,
    "DATA_SOURCE_MODE": _data_source_mode,
    "DEMO_REFRESH_SECONDS": _demo_refresh_seconds,
    "TITLE_TEXT": _title_text,
    "ACCENT_TIER1": _accent_tier1,
    "ACCENT_TIER2": _accent_tier2,
    "IFW_BRAND_BLUE": _ifw_brand_blue,
    "ELECTRICAL_PRIMARY_HEX": _electrical_primary_hex,
    "ELECTRICAL_SOFT_HEX": _electrical_soft_hex,
    "ELECTRICAL_FILL_RGBA": _electrical_fill_rgba,
    "PNEUMATIC_PRIMARY_HEX": _pneumatic_primary_hex,
    "PNEUMATIC_FILL_RGBA": _pneumatic_fill_rgba,
    "COMPONENT_MONO_HEX": _component_mono_hex,
    "COMPONENT_FILL_RGBA": _component_fill_rgba,
    "TAB_TITLES": _tab_titles,
    "TABS": ["Dashboard", _tab_titles["components"], _tab_titles["info"]],
    "LEGACY_TABS": [_tab_titles["json"]],
    "HISTORY_MAX_POINTS": _history_max_points,
    "LIVE_WINDOW_SECONDS": _live_window_seconds,
    "WEBSOCKET_RATE_HZ": _websocket_rate_hz,
    "WIDGET_BORDER_WIDTH_PX": _widget_border_width_px,
    "WIDGET_BORDER_RADIUS_PX": _widget_border_radius_px,
    "WIDGET_PADDING_REM": _widget_padding_rem,
    "TOP_PADDING_REM": _top_padding_rem,
    "CARD_SURFACE_BG": _card_surface_bg,
    "CARD_SURFACE_BORDER": _card_surface_border,
    "PANEL_BG_OUTER": _panel_bg_outer,
    "PANEL_BORDER_OUTER": _panel_border_outer,
    "PANEL_BG_INNER": _panel_bg_inner,
    "PANEL_BORDER_INNER": _panel_border_inner,
    "CHART_PANEL_BG": _chart_panel_bg,
    "CHART_GRID_COLOR": _chart_grid_color,
    "UI_FONT_FAMILY": _ui_font_family,
    "FONT_WEIGHT_REGULAR": _font_weight_regular,
    "FONT_WEIGHT_SEMIBOLD": _font_weight_semibold,
    "FONT_WEIGHT_BOLD": _font_weight_bold,
    "LOGO_IFW_BASENAME": _logo_ifw,
    "LOGO_FX_BASENAME": _logo_fx,
    "LOGO_META_BASENAME": _logo_meta,
    "SENSOR_NAMES": _sensor_names,
    "PLOTLY_DEFAULT_HEIGHT_PX": _plotly_default_height_px,
    "COMPONENT_PLOT_HEIGHT_PX": _component_plot_height_px,
    "PLOTLY_MARGIN_L": _plotly_margin_l,
    "PLOTLY_MARGIN_R": _plotly_margin_r,
    "PLOTLY_MARGIN_T": _plotly_margin_t,
    "PLOTLY_MARGIN_B": _plotly_margin_b,
    "PLOTLY_FONT_FAMILY": _plotly_font_family,
    "PLOTLY_TITLE_FONT_SIZE": _plotly_title_font_size,
    "PLOTLY_AXIS_TITLE_FONT_SIZE": _plotly_axis_title_font_size,
    "PLOTLY_TICK_FONT_SIZE": _plotly_tick_font_size,
    "PLOTLY_LEGEND_FONT_SIZE": _plotly_legend_font_size,
    "PLOTLY_LINE_WIDTH": _plotly_line_width,
    "PLOTLY_MARKER_SIZE": _plotly_marker_size,
    "PLOTLY_SHOWGRID": _plotly_showgrid,
    "PLOTLY_GRID_COLOR": _plotly_grid_color,
    "PLOTLY_GRID_WIDTH": _plotly_grid_width,
    "PLOTLY_TIME_RANGE_STEP_S": _plotly_time_range_step_s,
    "X_AXIS_TITLE": _x_axis_title,
    "Y_POWER_TITLE": _y_power_title,
    "Y_COMPONENT_TITLE": _y_component_title,
    "X_COMPONENT_TITLE": _x_component_title,
    "PLOT_CACHE_TTL_S": _plot_cache_ttl_s,
    "BUS_POLL_FAIL_BACKOFF_MAX_S": _bus_poll_fail_backoff_max_s,
    "COMPONENT_PLOT_COLORS": _component_plot_colors,
}
