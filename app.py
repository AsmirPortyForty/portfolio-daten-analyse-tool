# ==========================================
# IMPORT-BEREICH
# Hier laden wir alle benötigten "Werkzeuge"
# ==========================================
import streamlit as st          # Das Web-Framework für das Dashboard
import pandas as pd             # Das Herzstück für Tabellen und Datenverarbeitung
import matplotlib.pyplot as plt # Grundbibliothek zum Zeichnen von Diagrammen
import seaborn as sns           # Baut auf Matplotlib auf, macht hübschere Heatmaps
import json                     # Zum Lesen von verschachtelten JSON-Dateien
import io                       # Erlaubt uns, Dateien im Arbeitsspeicher zu bauen (für Excel-Export)

# ==========================================
# 1. SEITEN-KONFIGURATION & DESIGN
# Definiert den Tab-Namen im Browser und das Layout
# ==========================================
st.set_page_config(page_title="Data Discovery Tool", layout="wide")

# Ein bisschen Custom-CSS, um den Hintergrund leicht gräulich/professionell zu machen
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)

st.title(" Professionelles Datenanalyse-Tool")
st.write("Ein Portfolio-Projekt zur interaktiven Exploration und statistischen Prüfung.")

# ==========================================
# 2. SIDEBAR: DATEN-IMPORT
# ==========================================
with st.sidebar:
    st.header("1. Daten-Import")
    # File-Uploader, der nur bestimmte Formate zulässt
    uploaded_file = st.file_uploader("Datei hochladen", type=["csv", "xlsx", "json"])
    st.info("Unterstützte Formate: CSV, Excel, JSON")

# Wenn eine Datei hochgeladen wurde, startet die eigentliche App-Logik
if uploaded_file is not None:
    
    # ------------------------------------------
    # 2.1 JSON-Sonderbehandlung
    # Streamlit hat einen tollen Tree-Viewer, aber der braucht die reinen JSON-Daten.
    # ------------------------------------------
    raw_json = None
    if uploaded_file.name.endswith('.json'):
        raw_json = json.load(uploaded_file)
        # Setzt den Lese-Zeiger der Datei wieder auf Anfang, damit Pandas sie gleich noch lesen kann
        uploaded_file.seek(0)

    # ------------------------------------------
    # 2.2 Daten laden (mit Cache für Performance)
    # @st.cache_data sorgt dafür, dass die Datei bei einem Klick nicht jedes Mal neu geladen wird
    # ------------------------------------------
    @st.cache_data
    def load_data(file):
        if file.name.endswith('.csv'): 
            return pd.read_csv(file)
        elif file.name.endswith('.xlsx'): 
            return pd.read_excel(file)
        else: 
            return pd.read_json(file)
            
    # Lade die Daten in einen Pandas DataFrame (die Standard-Tabelle in Python)
    df = load_data(uploaded_file)
    
    # ==========================================
    # 3. FILTER-ENGINE (Dynamisch je nach Datentyp)
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Daten filtern")
    
    # Wir arbeiten mit einer Kopie, damit die Originaldaten unberührt bleiben
    filtered_df = df.copy()

    # 3.1 Globale Textsuche (sucht über alle Spalten hinweg)
    search_term = st.sidebar.text_input("Globale Textsuche...")
    if search_term:
        # Wandelt alle Zeilen in Text um und filtert die, die den Suchbegriff enthalten
        filtered_df = filtered_df[filtered_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

    # 3.2 Spaltenspezifische Filter
    filter_columns = st.sidebar.multiselect("Spalten für Filter auswählen:", df.columns)
    
    for col in filter_columns:
        # Wenn die Spalte Zahlen enthält -> Baue einen Schieberegler (Slider)
        if pd.api.types.is_numeric_dtype(filtered_df[col]):
            _min, _max = float(df[col].min()), float(df[col].max())
            if _min != _max: # Verhindert Fehler, wenn alle Zahlen gleich sind
                step = (_max - _min) / 100
                user_num_input = st.sidebar.slider(f"Wertebereich {col}", min_value=_min, max_value=_max, value=(_min, _max), step=step)
                # Filtere den DataFrame anhand der Slider-Werte
                filtered_df = filtered_df[filtered_df[col].between(*user_num_input)]
                
        # Wenn die Spalte Text/Kategorien enthält -> Baue ein Dropdown-Menü (Multiselect)
        elif pd.api.types.is_object_dtype(filtered_df[col]) or pd.api.types.is_categorical_dtype(filtered_df[col]):
            unique_values = df[col].dropna().unique()
            user_cat_input = st.sidebar.multiselect(f"Kategorien {col}", unique_values, default=unique_values)
            filtered_df = filtered_df[filtered_df[col].isin(user_cat_input)]

    # Hilfs-Variable: Ein DataFrame, der NUR numerische Spalten enthält (wichtig für Mathe/Korrelation)
    numeric_df = filtered_df.select_dtypes(include=['number'])

    # ==========================================
    # 4. DAS TAB-SYSTEM (Die Hauptansicht)
    # ==========================================
    tab1, tab2, tab3, tab4 = st.tabs([" Datenansicht & Export", "🔍 Ausreißer (IQR)", " Korrelationen", " Daten-Qualität"])

    # ------------------------------------------
    # TAB 1: DATENANSICHT & EXPORT
    # ------------------------------------------
    with tab1:
        st.subheader("Interaktive Datenvorschau & Auswahl")
        
        # Zeigt, wie Pandas die hochgeladenen Spalten interpretiert hat (Zahl, Text etc.)
        with st.expander(" Erkannte Spaltentypen"):
            type_df = pd.DataFrame(df.dtypes.astype(str), columns=['Datentyp']).reset_index().rename(columns={'index': 'Spalte'})
            st.dataframe(type_df, use_container_width=True)

        # Wenn es eine JSON war, zeige den aufklappbaren Baum an
        if raw_json is not None:
            with st.expander(" JSON Tree-Ansicht (Hierarchische Navigation)", expanded=True):
                st.json(raw_json)
                
        st.write(f"Angezeigt: {filtered_df.shape[0]} von {df.shape[0]} Zeilen.")
        
        # Interaktive Tabelle: Nutzer können Checkboxen anklicken, um Zeilen auszuwählen
        event = st.dataframe(filtered_df, use_container_width=True, on_select="rerun", selection_mode="multi-row")
        selected_indices = event.selection.rows
        
        # Wenn Zeilen markiert wurden, exportiere nur diese. Sonst alle gefilterten.
        final_selection_df = filtered_df.iloc[selected_indices] if selected_indices else filtered_df
        if selected_indices: 
            st.success(f"{len(selected_indices)} Zeilen ausgewählt.")
            
        st.markdown("---")
        st.subheader("💾 Export & Reports")
        
        # Bereite die Datenformate für den Download vor
        csv_data = final_selection_df.to_csv(index=False).encode('utf-8')
        json_data = final_selection_df.to_json(orient="records", force_ascii=False).encode('utf-8')
        
        # Excel-Export braucht einen virtuellen Puffer (BytesIO), da wir keine Datei auf der Festplatte speichern wollen
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            final_selection_df.to_excel(writer, index=False, sheet_name='Daten')
        excel_data = excel_buffer.getvalue()

        # Download-Buttons nebeneinander anordnen
        col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
        with col_ex1: st.download_button(" CSV Export", data=csv_data, file_name='daten.csv', mime='text/csv')
        with col_ex2: st.download_button(" Excel Export", data=excel_data, file_name='daten.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        with col_ex3: st.download_button(" JSON Export", data=json_data, file_name='daten.json', mime='application/json')
        with col_ex4:
            # Generator-Funktion für den Markdown-Report
            def generate_md_report(data):
                md = "# Automatischer Daten-Report\n\n"
                md += f"**Analysierte Zeilen:** {data.shape[0]}  \n**Analysierte Spalten:** {data.shape[1]}  \n\n"
                md += "## 1. Fehlende Werte\n"
                missing = data.isnull().sum()
                md += missing[missing > 0].to_markdown() if missing.sum() > 0 else "Keine fehlenden Werte.\n"
                md += "\n\n## 2. Deskriptive Statistik\n"
                num_data = data.select_dtypes(include=['number'])
                md += num_data.describe().to_markdown() + "\n\n" if not num_data.empty else "Keine numerischen Spalten.\n\n"
                md += "## 3. Duplikate\n"
                md += f"Es wurden **{data.astype(str).duplicated().sum()}** doppelte Zeilen gefunden.\n"
                return md
            st.download_button(" Markdown Report", data=generate_md_report(final_selection_df).encode('utf-8'), file_name='report.md', mime='text/markdown')

    # ------------------------------------------
    # TAB 2: AUSREISSER (Interquartilsabstand / IQR-Regel)
    # ------------------------------------------
    with tab2:
        st.subheader("Mathematische Ausreißer-Erkennung")
        if not numeric_df.empty:
            outlier_report = []
            outlier_data_dict = {} # Speichert die echten Ausreißer-Zeilen ab
            
            for col in numeric_df.columns:
                # Berechne Q1 (25%), Q3 (75%) und den IQR, um logische Ober- und Untergrenzen zu setzen
                Q1 = numeric_df[col].quantile(0.25)
                Q3 = numeric_df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
                
                # Finde alle Zeilen, die außerhalb dieser Grenzen liegen
                outliers = filtered_df[(filtered_df[col] < lower) | (filtered_df[col] > upper)]
                outlier_report.append({"Spalte": col, "Q1": Q1, "Q3": Q3, "IQR": IQR, "Unten": lower, "Oben": upper, "Anzahl": len(outliers)})
                
                # Wenn es Ausreißer gibt, packen wir sie in unser "Wörterbuch" für die Detailansicht
                if len(outliers) > 0:
                    outlier_data_dict[col] = outliers
            
            # Zeige die Übersichtstabelle sauber formatiert (2 Nachkommastellen) an
            st.dataframe(pd.DataFrame(outlier_report).style.format(precision=2), use_container_width=True)
            
            # Die elegante Detailansicht
            if outlier_data_dict:
                st.markdown("---")
                st.subheader(" Detailansicht: Die echten Datensätze")
                
                # Dropdown-Menü, das nur Spalten mit Ausreißern anzeigt
                selected_outlier_col = st.selectbox(
                    "Wähle eine Spalte, um die exakten Ausreißer-Zeilen zu analysieren:", 
                    list(outlier_data_dict.keys())
                )
                
                if selected_outlier_col:
                    st.write(f"Zeige {len(outlier_data_dict[selected_outlier_col])} gefundene Ausreißer in der Spalte **'{selected_outlier_col}'**:")
                    # Zeigt die tatsächlichen Zeilen aus dem Original-Datensatz
                    st.dataframe(outlier_data_dict[selected_outlier_col], use_container_width=True)
            else:
                st.success("Perfekt! Es wurden keine Ausreißer in den aktuellen Daten gefunden.")
                
        else:
            st.warning("Keine numerischen Spalten vorhanden.")

   
    # TAB 3: KORRELATION & SMART ENCODE
    
    with tab3:
        st.subheader("Zusammenhänge visualisieren")
        corr_df = numeric_df.copy()
        
        # Option: Wandelt Text-Spalten mit nur 2 Werten (z.B. yes/no) in 1 und 0 um, damit sie in der Matrix auftauchen
        smart_encode = st.checkbox(" Smart Encode (Binäre Text-Spalten intelligent in 1/0 umwandeln)")
        
        if smart_encode:
            cat_cols = filtered_df.select_dtypes(include=['object', 'category']).columns
            encoded_cols = []
            
            # Signalwörter definieren, um logisch sinnvoll 1 und 0 zuzuweisen
            pos_terms = ['yes', 'ja', 'true', 'wahr', 'm', 'male']
            neg_terms = ['no', 'nein', 'false', 'f', 'female']

            for col in cat_cols:
                unique_vals = filtered_df[col].dropna().unique()
                if len(unique_vals) == 2:
                    val1, val2 = unique_vals[0], unique_vals[1]
                    str1, str2 = str(val1).lower(), str(val2).lower()
                    
                    # Zuweisungs-Logik
                    if str1 in pos_terms or str2 in neg_terms:
                        mapping = {val1: 1, val2: 0}
                    elif str2 in pos_terms or str1 in neg_terms:
                        mapping = {val1: 0, val2: 1}
                    else:
                        # Fallback: Alphabetische Zuweisung, falls die Wörter unbekannt sind
                        sorted_vals = sorted([val1, val2])
                        mapping = {sorted_vals[0]: 0, sorted_vals[1]: 1}
                        
                    corr_df[col] = filtered_df[col].map(mapping)
                    val_for_1 = val1 if mapping[val1] == 1 else val2
                    encoded_cols.append(f"'{col}' ({val_for_1} = 1)")
            
            if encoded_cols:
                st.success(f"Erfolgreich codiert: {', '.join(encoded_cols)}")
            else:
                st.info("Keine passenden binären Text-Spalten gefunden.")

        # Heatmap zeichnen, wenn es genug Zahlen-Spalten gibt
        if len(corr_df.columns) > 1:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.heatmap(corr_df.corr(), annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
            st.pyplot(fig)
        else:
            st.warning("Mindestens zwei numerische (oder codierte) Spalten benötigt.")

    
    # TAB 4: DATEN-QUALITÄT (Prüf-Bausteine)
   
    with tab4:
        st.subheader(" Berechnungsbausteine & Qualitäts-Checks")
        
        col1, col2, col3 = st.columns(3)
        
        # Check 1: Min, Max, Mean, Std (Standardstatistik)
        with col1:
            if st.button(" Deskriptive Statistik"):
                if not numeric_df.empty:
                    st.write("**Statistische Kennzahlen:**")
                    st.dataframe(numeric_df.describe(), use_container_width=True)
                else:
                    st.info("Keine numerischen Daten.")
                    
        # Check 2: Fehlende Werte & Heatmap
        with col2:
            if st.button(" Missing-Value-Report"):
                missing = filtered_df.isnull().sum()
                if missing.sum() > 0:
                    st.dataframe(missing[missing > 0].rename("Anzahl fehlend"))
                    # Zeichnet eine Heatmap der Löcher im Datensatz
                    fig, ax = plt.subplots(figsize=(6, 4))
                    sns.heatmap(filtered_df.isnull(), cbar=False, cmap="viridis", yticklabels=False, ax=ax)
                    st.pyplot(fig)
                    
                    # Berechnet zusätzlich die prozentuale Fehlerrate pro Gruppe (z.B. fehlen Daten öfter bei "Männern"?)
                    cat_cols = filtered_df.select_dtypes(include=['object', 'category']).columns
                    if len(cat_cols) > 0:
                        group_col = cat_cols[0]
                        st.write(f"**Missing-Rate (%) gruppiert nach '{group_col}':**")
                        missing_rates = filtered_df.groupby(group_col).apply(lambda x: (x.isnull().mean() * 100))
                        st.dataframe(missing_rates[missing[missing > 0].index].style.format("{:.1f}%"), use_container_width=True)
                else:
                    st.success("Keine fehlenden Werte gefunden.")
                    
        # Check 3: Doppelte Zeilen (Duplikate)
        with col3:
            if st.button("👯 Duplikat-Check"):
                # .sum() zählt weiterhin die reinen "Kopien" (also 1 Duplikat = 1 gefundener Fehler)
                dups = filtered_df.astype(str).duplicated().sum()
                if dups > 0:
                    st.warning(f"{dups} doppelte Zeilen gefunden! Hier sind alle Einträge dazu:")
                    # keep=False zwingt Pandas, ALLE Einträge (Original + Kopien) anzuzeigen
                    duplicate_mask = filtered_df.astype(str).duplicated(keep=False)
                    st.dataframe(filtered_df[duplicate_mask], use_container_width=True)
                else:
                    st.success("Keine Duplikate gefunden!")

        st.markdown("---")
        col4, col5, col6 = st.columns(3)
        
        # Check 4: Die häufigsten Kategorien anzeigen
        with col4:
            if st.button("Value Counts"):
                cat_cols = filtered_df.select_dtypes(include=['object', 'category']).columns
                if len(cat_cols) > 0:
                    for col in cat_cols:
                        st.write(f"**Top Werte in '{col}':**")
                        try: st.dataframe(filtered_df[col].value_counts().head(5))
                        except TypeError: st.dataframe(filtered_df[col].astype(str).value_counts().head(5))
                else: st.info("Keine Text-Spalten vorhanden.")
        
        # Check 5: Quasi-konstante Spalten (Spalten, die keinen Informationswert bieten, da fast alles gleich ist)
        with col5:
            variance_threshold = st.slider("Schwellenwert (%) für konstante Werte", min_value=50, max_value=100, value=95)
            if st.button("Konstante Spalten (Variance Check)"):
                quasi_constant_cols = []
                total_rows = len(filtered_df)
                if total_rows > 0:
                    for col in filtered_df.columns:
                        # Berechnet die Häufigkeit des meistgenutzten Wertes in der Spalte
                        try: max_freq = filtered_df[col].value_counts(dropna=False).max()
                        except TypeError: max_freq = filtered_df[col].astype(str).value_counts(dropna=False).max()
                        
                        # Wenn der häufigste Wert den Schwellenwert überschreitet -> Alarm
                        if (max_freq / total_rows) * 100 >= variance_threshold:
                            quasi_constant_cols.append(col)
                
                if quasi_constant_cols: st.warning(f"Quasi-konstant (≥{variance_threshold}% gleicher Wert): {', '.join(quasi_constant_cols)}")
                else: st.success(f"Alle Spalten haben genug Varianz (<{variance_threshold}% gleiche Werte).")

        # Check 6: Typkonflikte (Findet Spalten, die als Text markiert sind, aber heimlich Zahlen enthalten)
        with col6:
            if st.button("Typenkonflikte"):
                conflicts = []
                for col in filtered_df.columns:
                    if pd.api.types.is_object_dtype(filtered_df[col]):
                        valid_vals = filtered_df[col].dropna()
                        if not valid_vals.empty:
                            # Testet, ob sich die Texte in Zahlen umwandeln lassen
                            num_test = pd.to_numeric(valid_vals, errors='coerce')
                            # Wenn mehr als 80% eigentlich Zahlen sind -> Typkonflikt
                            if num_test.notna().sum() / len(valid_vals) > 0.8:
                                conflicts.append(col)
                
                if conflicts: st.warning(f" Typkonflikt (Text enthält heimlich Zahlen):\n**{', '.join(conflicts)}**")
                else: st.success("Sauber! Keine Zahlen als Text getarnt.")

# Fallback, wenn noch keine Datei hochgeladen wurde
else:
    st.info(" Bitte lade zuerst eine Datei hoch.")