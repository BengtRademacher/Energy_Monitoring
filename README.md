# Factory-X Dashboard

Streamlit-Dashboard mit integriertem Mock-Data-Server und Live-Daten per WebSocket.

## Schnellstart

```bash
pip install -r requirements.txt
streamlit run app.py
```

Im Standardbetrieb startet die App den lokalen Data-Server automatisch und verbindet sich danach per WebSocket mit `ws://127.0.0.1:8000/ws`.

## Projektstruktur

- `app.py`: kanonischer Streamlit-Einstiegspunkt
- `dashboard_app.py`: App-Initialisierung und Start des lokalen Data-Servers
- `dashboard_views.py`: Kernansicht mit Tab 1 (`Dashboard`)
- `dashboard_tabs.py`: Tab-Registry und defensiver Loader fuer optionale Tabs
- `tab_components_optional.py`: optionaler Tab fuer Komponenten
- `tab_additional_info_optional.py`: optionaler Tab fuer Zusatzinformationen
- `tab_json_explorer_optional.py`: optionaler Tab fuer den JSON-Explorer
- `data_server.py`: eingebetteter Mock-Server fuer HTTP- und WebSocket-Daten
- `tests/`: automatisierte Tests

## Optionale Tabs entfernen

Tab 1 (`Dashboard`) ist fest eingebaut. Alle weiteren Tabs sind absichtlich als separate Dateien ausgelagert, damit sie auch von Nicht-Programmierern leicht entfernt werden koennen.

Wenn eine der folgenden Dateien geloescht wird, verschwindet der zugehoerige Tab automatisch beim naechsten Start:

- `tab_components_optional.py`
- `tab_additional_info_optional.py`
- `tab_json_explorer_optional.py`

Die App ist so aufgebaut, dass fehlende optionale Dateien keinen Fehler ausloesen. Die verbleibenden Tabs ruecken einfach auf.

## Pflichtdateien und optionale Dateien

Pflichtbestandteile fuer den normalen Betrieb sind unter anderem:

- `app.py`
- `dashboard_app.py`
- `dashboard_views.py`
- `dashboard_tabs.py`
- `config.py`
- `live_data.py`
- `data_server.py`
- `requirements.txt`

Optional sind nur die drei oben genannten `tab_*_optional.py`-Dateien.

## Externer Data-Server

Wenn bereits ein externer Dienst existiert, kann die App ohne eingebetteten Server betrieben werden:

```bash
DATA_SERVER_URL=https://example.com streamlit run app.py
```

Sobald `DATA_SERVER_URL` nicht auf `localhost` oder `127.0.0.1` zeigt, startet die App keinen lokalen FastAPI/Uvicorn-Server.

## API- und WebSocket-Endpunkte

Der interne oder externe Data-Server verwendet dieselben Schnittstellen:

- `GET /health`
- `GET /api/emo/snapshot`
- `GET /data`
- `WS /ws`

## Vor dem ersten Git-Push

Dieses Projekt sollte als eigenes Git-Repository direkt in diesem Ordner liegen. Aktuell zeigt das uebergeordnete Git-Root auf `C:\Users\rademacher`; dadurch wuerden beim Committen auch fremde Dateien ausserhalb des Projekts auftauchen.

Empfohlene Schritte:

1. Im Projektordner ein eigenes Repository initialisieren oder das Projekt in ein eigenes Repo verschieben.
2. Pruefen, dass `git rev-parse --show-toplevel` auf diesen Ordner zeigt.
3. Danach `git status` kontrollieren und nur Projektdateien committen.

Beispiel:

```bash
cd C:\Users\rademacher\Desktop\Factory-X_Dashboard_Uhlmann
git init
git add .
git commit -m "Initial commit"
```

## Tests

```bash
pytest -q
```
