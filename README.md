import streamlit as st


readme_content = """
#  Data Discovery Tool - Portfolio Projekt

Dieses Tool ist eine interaktive Web-Applikation zur Exploration, Bereinigung und statistischen Analyse von Datensätzen. Es wurde speziell entwickelt, um den Prozess der Datenvorbereitung (Data Profiling) für Machine-Learning-Aufgaben zu beschleunigen.

##  Live-Demo
Die App ist bereits in der Cloud deployed und kann hier getestet werden:
[ Zum Live-Tool](https://portfolio-daten-analyse-tool-c9bpqtcze48tgrr8zgbkvh.streamlit.app/)



##  Kernfunktionen

### 1. Daten-Import & Vorschau
* Unterstützung für **CSV, Excel (.xlsx)** und **JSON**.
* Dynamische Erkennung von Spaltentypen.
* Interaktive **JSON-Tree-Ansicht** für hierarchische Datenstrukturen.

### 2. Dynamische Filter-Engine
* Globale Textsuche über den gesamten Datensatz.
* Typ-spezifische Filter in der Sidebar (Range-Slider für Numerik, Multi-Select für Kategorien).
* Selektion einzelner Zeilen für gezielten Export.

### 3. Statistische Analysen (Berechnungsbausteine)
* **Ausreißer-Erkennung (IQR):** Mathematische Identifikation von Anomalien inkl. Detailansicht der betroffenen Zeilen.
* **Korrelations-Matrix:** Heatmap zur Identifikation von Feature-Abhängigkeiten (inkl. Smart-Encoding für binäre Text-Spalten).
* **Missing-Value-Report:** Analyse von Datenlücken inkl. gruppierter Fehlerraten.
* **Datenqualitäts-Checks:** Erkennung von Typkonflikten (Zahlen als Text) und quasi-konstanten Spalten.

### 4. Export & Reporting
* Export gefilterter Teilmengen als CSV, Excel oder JSON.
* Automatisierte Generierung eines Markdown-Analyse-Reports.

---

## Lokale Installation & Setup

Um das Tool lokal auf Ihrem System auszuführen, folgen Sie bitte diesen Schritten:

### 1. Voraussetzungen
* Installiertes **Python 3.11** oder höher.

### 2. Repository vorbereiten
Entpacken Sie die Projektdateien in einen Ordner Ihrer Wahl.

### 3. Virtuelle Umgebung erstellen (Empfohlen)
Öffnen Sie ein Terminal im Projektordner und führen Sie folgende Befehle aus:

```bash
# Erstellen der virtuellen Umgebung
python -m venv .venv

# Aktivieren (Windows)
.\\.venv\\Scripts\\activate

# Aktivieren (Mac/Linux)
source .venv/bin/activate