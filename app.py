import streamlit as st
import pandas as pd
import numpy as np
from fitparse import FitFile
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d

st.title("🚴 Kombiniertes Power Profile (1s – 4h)")
st.write("Lade mehrere FIT-Dateien hoch – die Power Curve wird daraus erstellt.")

uploaded_files = st.file_uploader("FIT-Dateien hochladen", type=["fit"], accept_multiple_files=True)

# Ziel-Dauern in Sekunden: logarithmisch abgestuft von 1s bis 4h (14400s)
durations = sorted(set([
    int(x) for x in np.geomspace(1, 14400, num=100).round()
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

        st.subheader("📊 Kombinierte Power Curve (1s – 4h)")
        df_result = pd.DataFrame({
            "Dauer (s)": combined_profile.index.astype(int),
            "Bestleistung (W)": combined_profile.values
        }).sort_values("Dauer (s)")

        # Glätten
        df_result["Bestleistung (W)"] = gaussian_filter1d(df_result["Bestleistung (W)"], sigma=2)

        st.line_chart(df_result.set_index("Dauer (s)"))

        # Export
        csv = df_result.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV herunterladen", csv, "power_curve_1s_4h.csv", "text/csv")
