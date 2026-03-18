from __future__ import annotations

from typing import Any, Mapping

import streamlit as st


def inject_global_styles(config: Mapping[str, Any]) -> None:
    try:
        top_pad = float(config.get("TOP_PADDING_REM", 0.0))
    except Exception:
        top_pad = 0.0

    st.markdown(
        f"""
<style>
:root {{
  --fx-font-family: {config["UI_FONT_FAMILY"]};
  --fx-font-weight-regular: {config["FONT_WEIGHT_REGULAR"]};
  --fx-font-weight-semibold: {config["FONT_WEIGHT_SEMIBOLD"]};
  --fx-font-weight-bold: {config["FONT_WEIGHT_BOLD"]};
  --fx-min-font-size: {config["PLOTLY_TICK_FONT_SIZE"]}px;
}}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .block-container {{
  font-family: var(--fx-font-family) !important;
  font-weight: var(--fx-font-weight-regular);
}}
div[data-testid="stMarkdownContainer"],
div[data-testid="stText"],
div[data-testid="stCaptionContainer"],
div[data-testid="stMetricLabel"],
div[data-testid="stMetricValue"],
div[data-testid="stAlertContainer"],
label,
p,
span {{
  font-family: var(--fx-font-family) !important;
  font-size: var(--fx-min-font-size) !important;
}}
div[data-testid="stHeading"] h1,
div[data-testid="stHeading"] h2,
div[data-testid="stHeading"] h3,
div[data-testid="stHeading"] h4,
div[data-testid="stHeading"] h5,
div[data-testid="stHeading"] h6 {{
  font-family: var(--fx-font-family) !important;
  font-weight: var(--fx-font-weight-semibold) !important;
}}
div[data-testid="stCaptionContainer"],
div[data-testid="stCaptionContainer"] p {{
  font-weight: var(--fx-font-weight-regular) !important;
}}
.block-container {{
  padding-top: {top_pad}rem !important;
}}
.app-title {{
  font-family: var(--fx-font-family) !important;
  color: {config["ACCENT_TIER1"]};
  margin: 0 0 0.25rem 0;
  font-size: 2.8rem;
  font-weight: var(--fx-font-weight-bold);
}}
[class*="st-key-dashboard-"],
[class*="st-key-component-"],
[class*="st-key-additional-"]:not(.st-key-additional-logo-row),
[class*="st-key-json-"] {{
  border: 1px solid transparent !important;
  border-radius: {config["WIDGET_BORDER_RADIUS_PX"]}px !important;
  box-shadow: none !important;
  padding: {config["WIDGET_PADDING_REM"]}rem !important;
  margin-top: 0.5rem !important;
  margin-bottom: 0.5rem !important;
}}
.st-key-dashboard-electrical-card,
.st-key-dashboard-air-card,
.st-key-dashboard-electrical-chart,
.st-key-dashboard-air-chart,
.st-key-component-kpi-panel {{
  background-color: {config["PANEL_BG_INNER"]} !important;
}}
.st-key-dashboard-status-panel,
.st-key-component-status-panel,
[class*="st-key-component-panel-"],
.st-key-json-body-panel {{
  background-color: {config["CHART_PANEL_BG"]} !important;
}}
.st-key-additional-uhlmann-link,
.st-key-additional-festo-link,
.st-key-additional-export-link,
.st-key-additional-ifw-panel,
.st-key-additional-fx-panel,
.st-key-additional-iso-panel,
.st-key-additional-boxplot-panel,
.st-key-json-header-panel,
.st-key-json-body-panel,
.st-key-dashboard-summary-card-total,
.st-key-dashboard-summary-card-yearly,
.st-key-dashboard-electrical-group,
.st-key-dashboard-air-group {{
  background-color: {config["PANEL_BG_OUTER"]} !important;
}}
.st-key-dashboard-electrical-group > div,
.st-key-dashboard-air-group > div {{
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}}
.st-key-additional-logo-row div[data-testid="stHorizontalBlock"] {{
  align-items: stretch;
}}
.st-key-additional-logo-row div[data-testid="column"] {{
  display: flex;
}}
.st-key-additional-logo-row div[data-testid="column"] > div {{
  display: flex;
  width: 100%;
}}
.st-key-additional-export-link button {{
  background: #000000 !important;
  color: #ffffff !important;
  border: 1px solid #000000 !important;
  opacity: 1 !important;
  cursor: default !important;
}}
.st-key-additional-export-link button:hover,
.st-key-additional-export-link button:focus,
.st-key-additional-export-link button:active {{
  background: #000000 !important;
  color: #ffffff !important;
  border: 1px solid #000000 !important;
  box-shadow: none !important;
}}
.st-key-additional-export-link button p,
.st-key-additional-export-link button span {{
  color: #ffffff !important;
  font-size: inherit !important;
  font-weight: var(--fx-font-weight-semibold) !important;
}}
.st-key-additional-ifw-panel,
.st-key-additional-fx-panel {{
  display: flex;
  flex: 1 1 auto;
  min-height: 10.75rem;
  width: 100%;
}}
.st-key-additional-ifw-panel > div,
.st-key-additional-fx-panel > div {{
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  justify-content: flex-start;
  width: 100%;
}}
.st-key-additional-ifw-panel div[data-testid="stImage"],
.st-key-additional-fx-panel div[data-testid="stImage"] {{
  display: flex;
  align-items: flex-start;
  min-height: 5rem;
}}
.st-key-additional-ifw-panel div[data-testid="stImage"] img,
.st-key-additional-fx-panel div[data-testid="stImage"] img {{
  height: 4.5rem;
  width: auto !important;
  object-fit: contain;
}}
.st-key-additional-iso-panel div[data-testid="stImage"],
.st-key-additional-boxplot-panel div[data-testid="stImage"] {{
  display: flex;
  justify-content: center;
}}
.st-key-additional-iso-panel div[data-testid="stImage"] img,
.st-key-additional-boxplot-panel div[data-testid="stImage"] img {{
  display: block;
  margin: 0 auto;
  max-width: 100%;
  height: auto;
  object-fit: contain;
}}
.additional-machine-image {{
  display: flex;
  justify-content: center;
  width: 100%;
}}
.additional-machine-image img {{
  display: block;
  max-width: 100%;
  height: auto;
  object-fit: contain;
}}
div[data-testid="stTabs"] button[data-baseweb="tab"] {{
  gap: 0.45rem;
}}
div[data-testid="stTabs"] button[data-baseweb="tab"]::before {{
  content: "";
  display: inline-block;
  width: 1.2rem;
  height: 1.2rem;
  flex: 0 0 1.2rem;
  background-position: center;
  background-repeat: no-repeat;
  background-size: contain;
}}
div[data-testid="stTabs"] button[data-baseweb="tab"]:nth-of-type(1)::before {{
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23111827' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='7' height='7' rx='1.5'/><rect x='14' y='3' width='7' height='5' rx='1.5'/><rect x='14' y='10' width='7' height='11' rx='1.5'/><rect x='3' y='14' width='7' height='7' rx='1.5'/></svg>");
}}
div[data-testid="stTabs"] button[data-baseweb="tab"]:nth-of-type(2)::before {{
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23111827' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2 19 6 12 10 5 6 12 2Z'/><path d='M5 6v6l7 4 7-4V6'/><path d='M12 10v6'/><path d='M5 12l7 4 7-4'/></svg>");
  transform: translateY(4px);
}}
div[data-testid="stTabs"] button[data-baseweb="tab"]:nth-of-type(3)::before {{
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23111827' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='9'/><path d='M12 10v6'/><path d='M12 7h.01'/></svg>");
  transform: translateY(1px);
}}
div[data-testid="stTabs"] button[data-baseweb="tab"]:nth-of-type(4)::before {{
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23111827' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M9 4H8a2 2 0 0 0-2 2v3a2 2 0 0 1-2 2 2 2 0 0 1 2 2v3a2 2 0 0 0 2 2h1'/><path d='M15 4h1a2 2 0 0 1 2 2v3a2 2 0 0 0 2 2 2 2 0 0 0-2 2v3a2 2 0 0 1-2 2h-1'/></svg>");
  transform: translateY(2px);
}}
div[data-testid="stTabs"] button[data-baseweb="tab"] p,
div[data-testid="stTabs"] button[data-baseweb="tab"] span {{
  font-size: max(1.25rem, var(--fx-min-font-size)) !important;
  font-weight: var(--fx-font-weight-semibold) !important;
}}
.layer-kpi-card {{
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  column-gap: 1.25rem;
  min-height: 5.5rem;
  font-family: var(--fx-font-family) !important;
}}
.layer-kpi-label {{
  font-size: max(0.95rem, var(--fx-min-font-size));
  font-weight: var(--fx-font-weight-semibold);
  color: #4b5563;
  line-height: 1.2;
  min-width: 0;
}}
.layer-kpi-value {{
  font-size: 1.95rem;
  font-weight: var(--fx-font-weight-bold);
  line-height: 1.1;
  text-align: right;
  white-space: nowrap;
}}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] p {{
  font-size: max(0.95rem, var(--fx-min-font-size)) !important;
  font-weight: var(--fx-font-weight-semibold) !important;
  color: #4b5563 !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"],
div[data-testid="metric-container"] [data-testid="stMetricValue"] > div,
div[data-testid="metric-container"] [data-testid="stMetricValue"] p {{
  font-size: 1.95rem !important;
  font-weight: var(--fx-font-weight-bold) !important;
  line-height: 1.1 !important;
  color: #111827 !important;
}}
.st-key-json-body-panel div[data-testid="stJson"] {{
  background: rgba(255, 255, 255, 0.36);
  border-radius: {config["WIDGET_BORDER_RADIUS_PX"]}px;
  padding: 0.35rem;
}}
.machine-status-legend {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0.1rem 0 0.8rem 0;
}}
.machine-status-pill {{
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.3rem 0.7rem;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid {config["PANEL_BORDER_OUTER"]};
  border-radius: 999px;
  font-size: max(0.92rem, var(--fx-min-font-size));
  font-family: var(--fx-font-family) !important;
  font-weight: var(--fx-font-weight-semibold);
  color: #1f2937;
}}
.machine-status-dot {{
  width: 0.8rem;
  height: 0.8rem;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.7);
  flex: 0 0 auto;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def inject_metric_styles(config: Mapping[str, Any]) -> None:
    st.markdown(
        f"""
<style>
div[data-testid="metric-container"] {{
  background-color: rgba(255,255,255,0.72);
  border: 1px solid {config["PANEL_BORDER_OUTER"]};
  padding: 4% 5% 4% 8%;
  border-radius: 5px;
  border-left: 0.5rem solid {config["ACCENT_TIER1"]} !important;
  font-family: {config["UI_FONT_FAMILY"]} !important;
  box-shadow: none !important;
}}
div[data-testid="metric-container"] * {{
  font-family: {config["UI_FONT_FAMILY"]} !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] p {{
  font-weight: {config["FONT_WEIGHT_SEMIBOLD"]} !important;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"],
div[data-testid="metric-container"] [data-testid="stMetricValue"] > div,
div[data-testid="metric-container"] [data-testid="stMetricValue"] p {{
  font-weight: {config["FONT_WEIGHT_BOLD"]} !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def render_app_header(config: Mapping[str, Any]) -> None:
    st.markdown(f"<h1 class='app-title'>{config['TITLE_TEXT']}</h1>", unsafe_allow_html=True)
