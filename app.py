import streamlit as st
import pandas as pd
import numpy as np
from fitparse import FitFile
import io
import matplotlib.pyplot as plt

st.title("🚴 Power Profile Analyse")
st.write("Lade eine .fit-Datei hoch, um Bestwerte über verschiedene Zeiträume zu berechnen.")

uploaded_file = st.file_uploader("FIT-Datei hochladen", type=["fit"])

def extract_power_series(fitfile):
    power_data = []
    for record in fitfile.get_messages("record"):
        power = record.get_value("power")
        if power is not None:
            power_data.append(power)
    return power_data

def best_avg_power(power_series, duration_seconds):
    return max(
        np.convolve(power_series, np.ones(duration_seconds), 'valid') / duration_seconds
    ) if len(power_series) >= duration_seconds else 0

if uploaded_file:
    fitfile = FitFile(uploaded_file)
    power_series = extract_power_series(fitfile)

    if len(power_series) == 0:
        st.error("Keine Leistungsdaten gefunden.")
    else:
        st.success(f"{len(power_series)} Leistungsdatenpunkte geladen.")

        durations = [20, 30, 60, 180, 240, 300, 600, 720, 900, 1200, 1800]
        results = {
            f"{d}s": round(best_avg_power(power_series, d), 1) for d in durations
        }

        df = pd.DataFrame(list(results.items()), columns=["Dauer", "Bestleistung (W)"])
        st.dataframe(df)

        # Plot
        fig, ax = plt.subplots()
        ax.plot(df["Dauer"], df["Bestleistung (W)"], marker='o')
        ax.set_xlabel("Dauer")
        ax.set_ylabel("Watt")
        ax.set_title("Power Curve")
        st.pyplot(fig)

        # Platzhalter für VO2max, FTP, VLamax (später erweiterbar)
        st.header("📈 Schätzungen (Beta)")
        ftp = round(results.get("300s", 0) * 0.95, 1)
        vo2max = round(results.get("300s", 0) / 0.072, 1) if results.get("300s", 0) else 0
        vlamax = round(results.get("30s", 0) / 1000, 2)

        st.markdown(f"**FTP (geschätzt):** {ftp} W")
        st.markdown(f"**VO₂max (geschätzt):** {vo2max} ml/min/kg (Platzhalter)")
        st.markdown(f"**VLamax (grob geschätzt):** {vlamax} mmol/l/s")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV herunterladen", csv, "powerprofile.csv", "text/csv")
