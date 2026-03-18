# Energy Monitoring Dashboard

> Streamlit-Dashboard für Live-Monitoring von Energie- und Mediendaten mit integriertem Demo-Modus.

Dieses Projekt stellt eine kompakte Monitoring-Oberfläche für maschinenbezogene Energiedaten bereit. Es ist für einen schnellen lokalen Start, gut lesbare Visualisierungen und eine einfache Anpassung ausgelegt, wenn einzelne Dashboard-Bereiche nicht benötigt werden.

## Überblick

| Bereich | Beschreibung |
| --- | --- |
| Live-Monitoring | Zeigt aktuelle Maschinen- und Komponentenwerte aus einem fortlaufend aktualisierten Snapshot-Datenstrom an. |
| Schneller lokaler Start | Läuft als normale Streamlit-App und eignet sich gut für Demos und lokale Entwicklung. |
| Modulare UI | Zusätzliche Tabs sind bewusst getrennt aufgebaut, damit die Oberfläche ohne tiefgreifende Codeänderungen vereinfacht werden kann. |
| Fokus auf Visualisierung | Schwerpunkt auf gut lesbaren Statusanzeigen, Zeitreihenansichten und strukturierter Inspektion von Maschinendaten. |

## Schnellstart

```bash
pip install -r requirements.txt
streamlit run app.py
```

Nach dem Start öffnet sich das Dashboard im Browser und verbindet sich automatisch mit der konfigurierten Datenquelle. In der Standardkonfiguration läuft ein interner Demo-Modus direkt im Streamlit-Prozess, sodass die Anwendung sofort ausprobiert werden kann.

## Was Das Dashboard Bietet

- Ein zentrales Dashboard für Live-Monitoring von Energieverbrauch und Maschinenstatus
- Optionale Ansichten für Komponenten und Zusatzinformationen
- Einen ausgelagerten Legacy-Tab für JSON-Inspektion, der im Code erhalten bleibt
- Einen internen Demo-Datenmodus für Entwicklung und Demonstrationen
- Gemeinsame Plot-, Validierungs- und Transformationshelfer für eine konsistente Oberfläche

## Anwendungsfluss

```mermaid
flowchart LR
    A["Datenquelle"] --> B["Snapshot-Validierung"]
    B --> C["Session State / Historie"]
    C --> D["Dashboard-Tab"]
    C --> E["Optionale Tabs"]
    E --> F["Komponenten"]
    E --> G["Zusatzinfos"]
    E --> H["Legacy: JSON-Explorer"]
```

## Aufbau Der Oberfläche

Das Dashboard besteht aus einer zentralen Monitoring-Ansicht und optionalen Erweiterungen:

| Ansicht | Zweck |
| --- | --- |
| `Dashboard` | Zentrale Betriebsübersicht mit den wichtigsten Live-Werten und Statusinformationen |
| `Components` | Detaillierte Ansicht auf Komponentenebene |
| `Additional Info` | Ergänzende Maschineninformationen und zusätzliche Kontextdaten |
| `JSON Explorer (Legacy)` | Einblick in die rohen strukturierten Snapshots für Debugging und Validierung |

## Anpassung

Die Anwendung ist bewusst so aufgebaut, dass sie sich mit wenig Aufwand anpassen lässt.

### Sichtbare Und Legacy-Tabs

Standardmäßig zeigt die App drei Tabs an:

- `Dashboard`
- `Komponenten`
- `Zusatzinformationen`

Der `JSON-Explorer` bleibt als Legacy-Modul im Code erhalten, wird aber nicht mehr in der Standardnavigation angezeigt.

### Nicht Benötigte Tabs Entfernen

Wenn eine Ansicht nicht angezeigt werden soll, kann die zugehörige optionale Datei gelöscht werden:

- `tab_components_optional.py`
- `tab_additional_info_optional.py`
- `tab_json_explorer_optional.py`

Fehlende optionale Dateien werden sauber abgefangen. Die übrigen Tabs funktionieren weiter, ohne dass die Anwendung dadurch bricht.

### Externe Datenquelle Verwenden

Wenn das Dashboard statt des internen Demo-Modus mit einem bestehenden Backend verbunden werden soll, kann es so gestartet werden:

```bash
DATA_SOURCE_MODE=external DATA_SERVER_URL=https://example.com streamlit run app.py
```

## Projektstruktur

| Datei | Rolle |
| --- | --- |
| `app.py` | Zentraler Streamlit-Einstiegspunkt |
| `dashboard_app.py` | App-Startlogik und Laufzeit-Orchestrierung |
| `dashboard_views.py` | Rendering der Kernansicht |
| `dashboard_tabs.py` | Tab-Registry und Laden optionaler Tabs |
| `live_data.py` | Verarbeitung von Live-Daten und Historie |
| `data_server.py` | Optionales Standalone-Demo-Backend |
| `plotting.py` | Gemeinsame Erstellung von Plotly-Figuren |
| `snapshot_schema.py` | Hilfsfunktionen für Snapshot-Validierung |
| `utils.py` | Allgemeine Hilfsfunktionen |

## Leitgedanken

- Klare Betriebsübersicht statt unnötiger technischer Überladung
- Einfache lokale Demo ohne zusätzlichen Nebenserver
- Anpassbar mit wenig Aufwand, auch für Nicht-Programmierer
- Robustes Verhalten, wenn optionale UI-Module entfernt werden

## Hinweise

Weitere technische Details und Informationen zur internen Struktur stehen in [`struktur.md`](./struktur.md).
