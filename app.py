import streamlit as st
import pandas as pd
import numpy as np
from fitparse import FitFile
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

st.title("🚴 Kombinierte Power Curve (1s – 2h)")
st.write("Lade mehrere FIT-Dateien hoch – die Power Curve wird daraus erstellt.")

uploaded_files = st.file_uploader("FIT-Dateien hochladen", type=["fit"], accept_multiple_files=True)

# Ziel-Dauern in Sekunden: logarithmisch abgestuft bis 2h
durations = sorted(set([
    int(x) for x in np.geomspace(1, 7200, num=100).round()
]))

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

if uploaded_files:
    all_power_values = []

    for file in uploaded_files:
        fitfile = FitFile(file)
        power_series = extract_power_series(fitfile)

        if len(power_series) == 0:
            st.warning(f"⚠️ Keine Leistungsdaten in {file.name}")
            continue

        single_file_result = {
            d: best_avg_power(power_series, d) for d in durations
        }
        all_power_values.append(single_file_result)

    if all_power_values:
        df_all = pd.DataFrame(all_power_values)
        combined_profile = df_all.max(axis=0).dropna()

        st.subheader("📊 Kombinierte Power Curve (1s – 2h)")
        df_result = pd.DataFrame({
            "Dauer (s)": combined_profile.index.astype(int),
            "Bestleistung (W)": combined_profile.values
        }).sort_values("Dauer (s)")

        # Glätten
        df_result["Bestleistung (W)"] = gaussian_filter1d(df_result["Bestleistung (W)"], sigma=2)

        # Benutzerdefinierte X-Achsenbeschriftung
        xticks = {
            1: "1s", 30: "30s", 60: "1min", 180: "3min", 300: "5min", 600: "10min",
            1200: "20min", 3600: "1h", 7200: "2h"
        }

        fig, ax = plt.subplots()
        ax.plot(df_result["Dauer (s)"], df_result["Bestleistung (W)"], color="blue")
        ax.set_xlabel("Dauer")
        ax.set_ylabel("Watt")
        ax.set_title("Kombinierte Power Curve")
        ax.set_xscale("log")
        ax.set_xticks(list(xticks.keys()))
        ax.set_xticklabels(list(xticks.values()))
        ax.grid(True, which="both", linestyle="--", linewidth=0.5)
        st.pyplot(fig)

        # Export
        csv = df_result.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV herunterladen", csv, "power_curve_1s_2h.csv", "text/csv")
