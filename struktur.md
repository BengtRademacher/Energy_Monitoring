# Factory-X Dashboard Struktur

## Zweck
- Streamlit-Dashboard mit Live-Daten aus einem WebSocket-Stream.
- Integrierter lokaler Mock-Server (`data_server.py`) liefert Testdaten.
- Fokus: schnelle Anzeige von Energie-/Luftverbrauch und JSON-Inspektion der Maschinendaten.

## Snapshot-Vertrag
Die App arbeitet mit folgender JSON-Struktur:

```json
{
  "timestamp": 1710000000.0,
  "data_mains": {
    "electrical_Hauptversorgung": 3500.0,
    "pneumatic_Hauptversorgung": 1200.0
  },
  "data_components": {
    "component1_Heizstation": 500.0,
    "component2_Siegelstation": 300.0,
    "component3_Kompaktstation": 800.0,
    "component4_Formstation": 600.0,
    "component5_3rd_party_component": 100.0,
    "component6_additional1": 50.0,
    "component7_additional2": 50.0
  },
  "machine_status": "Processing"
}
```

## Datenfluss
1. `app.py` startet bei lokaler Ziel-URL den eingebetteten FastAPI/Uvicorn-Data-Server.
2. `live_data.py` baut die WebSocket-URL aus `DATA_SERVER_URL` ab und startet einen Hintergrund-Receiver.
3. Neue Snapshots werden validiert, gepuffert und in `st.session_state["history"]` uebernommen.
4. `dashboard_views.py` rendert den verpflichtenden Dashboard-Tab.
5. `dashboard_tabs.py` laedt zusaetzlich optionale Tab-Dateien nur dann, wenn sie vorhanden und importierbar sind.
6. Die verbleibenden Tabs werden in stabiler Reihenfolge angezeigt; fehlt eine optionale Datei, ruecken die anderen automatisch auf.
7. `utils.py` erzeugt DataFrames fuer Zeitreihen und Statussegmente.

## Hauptdateien
- `app.py`: kanonischer Einstieg fuer Streamlit und Community Cloud.
- `dashboard.py`: Kompatibilitaets-Wrapper fuer den bisherigen Einstieg.
- `live_data.py`: WebSocket-Empfang, Session-State und Render-Kontext.
- `dashboard_views.py`: Kern-Tab `Dashboard`.
- `dashboard_tabs.py`: Registry und Loader fuer optionale Tabs.
- `tab_components_optional.py`: optionaler Komponenten-Tab.
- `tab_additional_info_optional.py`: optionaler Tab fuer Zusatzinformationen.
- `tab_json_explorer_optional.py`: optionaler JSON-Explorer-Tab.
- `dashboard_view_shared.py`: gemeinsam genutzte Plot- und Anzeigehelfer.
- `dashboard_styles.py`: globale CSS-Injektion und Header-Ausgabe.
- `utils.py`: reine History-, DataFrame- und Asset-Helfer.
- `snapshot_schema.py`: Snapshot-Vertrag, Validierung und Getter.
- `plotting.py`: gemeinsame Plotly-Figure-Builder.
- `data_server.py`: eingebetteter oder standalone nutzbarer Mock-Server mit `/ws`, `/api/emo/snapshot`, `/data` und `/health`.

## Optionale Tabs
- Tab 1 (`Dashboard`) ist verpflichtend.
- Tab 2 bis Tab 4 liegen absichtlich in separaten Skripten.
- Wer einen optionalen Tab nicht moechte, kann die zugehoerige Datei loeschen.
- Fehlende optionale Dateien fuehren nicht zu einem Absturz; der Tab wird einfach nicht angezeigt.

## Betrieb
- Standard: `streamlit run app.py`
- Optional externes Backend: `DATA_SERVER_URL=https://example.com streamlit run app.py`

Im Standardbetrieb startet die App den lokalen Mock-Server einmalig selbst und verbindet sich anschliessend per WebSocket.
