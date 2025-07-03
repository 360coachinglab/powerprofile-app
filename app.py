import streamlit as st
import pandas as pd
import numpy as np
from fitparse import FitFile
import matplotlib.pyplot as plt

st.title("🚴 Kombiniertes Power Profile aus mehreren FIT-Dateien")
st.write("Lade mehrere FIT-Dateien hoch – das beste Power-Profil wird daraus generiert.")

uploaded_files = st.file_uploader("FIT-Dateien hochladen", type=["fit"], accept_multiple_files=True)

# Ziel-Dauern in Sekunden
durations = [20, 30, 60, 180, 240, 300, 600, 720, 900, 1200, 1800]

def extract_power_series(fitfile):
    power_data = []
    for record in fitfile.get_messages("record"):
        power = record.get_value("power")
        if power is not None:
            power_data.append(power)
    return power_data

def best_avg_power(power_series, duration_seconds):
    if len(power_series) >= duration_seconds:
        rolling = np.convolve(power_series, np.ones(duration_seconds), 'valid') / duration_seconds
        return max(rolling)
    else:
        return np.nan

# Ergebnisse pro Datei und kombiniert
if uploaded_files:
    all_power_values = []

    for file in uploaded_files:
        fitfile = FitFile(file)
        power_series = extract_power_series(fitfile)

        if len(power_series) == 0:
            st.warning(f"⚠️ Keine Leistungsdaten in {file.name}")
            continue

        single_file_result = {
            f"{d}s": best_avg_power(power_series, d) for d in durations
        }
        all_power_values.append(single_file_result)

    if all_power_values:
        df_all = pd.DataFrame(all_power_values)
        combined_profile = df_all.max(axis=0)

        st.subheader("📊 Kombiniertes Power-Profile (beste Werte aus allen Dateien)")
        df_result = combined_profile.reset_index()
        df_result.columns = ["Dauer", "Bestleistung (W)"]
        st.dataframe(df_result)

        # Plot
        fig, ax = plt.subplots()
        df_result["Dauer (s)"] = df_result["Dauer"].str.replace("s", "").astype(int)
        ax.plot(df_result["Dauer (s)"], df_result["Bestleistung (W)"], marker='o')
        ax.set_xlabel("Dauer (s)")
        ax.set_ylabel("Watt")
        ax.set_title("Kombinierte Power Curve")
        st.pyplot(fig)

        # Export
        csv = df_result.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV herunterladen", csv, "kombiniertes_power_profile.csv", "text/csv")
