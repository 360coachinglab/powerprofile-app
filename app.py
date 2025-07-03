import streamlit as st
import pandas as pd
import numpy as np
from fitparse import FitFile

st.title("🚴 Leistungsanalyse aus FIT-Dateien")
st.write("Lade eine oder mehrere FIT-Dateien hoch – die App zeigt die Bestwerte und leitet physiologische Parameter ab.")

uploaded_files = st.file_uploader("FIT-Dateien hochladen", type=["fit"], accept_multiple_files=True)

# Ziel-Dauern in Sekunden
durations = [20, 30, 60, 180, 240, 300, 600, 720, 900, 1200, 1800]

def extract_series(fitfile):
    power_data = []
    hr_data = []
    for record in fitfile.get_messages("record"):
        power = record.get_value("power")
        hr = record.get_value("heart_rate")
        if power is not None:
            power_data.append(power)
        if hr is not None:
            hr_data.append(hr)
    return power_data, hr_data

def best_avg(series, duration):
    if len(series) >= duration:
        rolling = np.convolve(series, np.ones(duration), 'valid') / duration
        return max(rolling)
    return np.nan

def estimate_metrics(best_powers):
    ftp = best_powers.get(1200, np.nan)  # 20min
    vo2max = best_powers.get(300, np.nan) / 0.85 if not np.isnan(best_powers.get(300, np.nan)) else np.nan
    vlamax = best_powers.get(20, np.nan) / 1000 if not np.isnan(best_powers.get(20, np.nan)) else np.nan
    fatmax = 0.65 * ftp if not np.isnan(ftp) else np.nan
    return ftp, vo2max, vlamax, fatmax

if uploaded_files:
    all_best = []
    for file in uploaded_files:
        fitfile = FitFile(file)
        power_series, hr_series = extract_series(fitfile)
        best = {dur: best_avg(power_series, dur) for dur in durations}
        all_best.append(best)

    if all_best:
        df = pd.DataFrame(all_best)
        combined = df.max(axis=0).to_dict()

        # Metriken berechnen
        ftp, vo2max, vlamax, fatmax = estimate_metrics(combined)

        # Anzeige der Ergebnisse
        st.subheader("📊 Bestwerte aus allen Dateien")
        st.dataframe(pd.DataFrame(combined.items(), columns=["Dauer (s)", "Bestleistung (W)"]))

        st.subheader("📈 Abgeleitete Parameter")
        st.markdown(f"- **FTP**: {ftp:.0f} W")
        st.markdown(f"- **VO2max**: {vo2max:.0f} W")
        st.markdown(f"- **VLamax**: {vlamax:.2f} mmol/l/s")
        st.markdown(f"- **FatMax-Zone (Schätzung)**: {fatmax:.0f} W")

        if not np.isnan(ftp):
            st.subheader("📐 Trainingszonen (Leistung in Watt)")
            zones = {
                "Zone 1 (Regeneration)": (0, 0.55 * ftp),
                "Zone 2 (Grundlage)": (0.56 * ftp, 0.75 * ftp),
                "Zone 3 (Tempo)": (0.76 * ftp, 0.9 * ftp),
                "Zone 4 (Laktatschwelle)": (0.91 * ftp, 1.05 * ftp),
                "Zone 5 (VO2max)": (1.06 * ftp, 1.20 * ftp),
                "Zone 6 (Anaerob)": (1.21 * ftp, 1.50 * ftp),
                "Zone 7 (Neuromuskulär)": (1.51 * ftp, np.nan)
            }
            df_zones = pd.DataFrame([
                {"Zone": z, "Wattbereich": f"{int(low)}–{int(high) if not np.isnan(high) else '∞'}"}
                for z, (low, high) in zones.items()
            ])
            st.dataframe(df_zones)

        # Pulsdaten
        if any(len(FitFile(f).get_messages("record")) > 0 for f in uploaded_files):
            avg_hr = np.mean([np.mean(extract_series(FitFile(f))[1]) for f in uploaded_files if len(extract_series(FitFile(f))[1]) > 0])
            st.subheader("❤️ Durchschnittlicher Puls")
            st.write(f"{avg_hr:.0f} bpm") if not np.isnan(avg_hr) else st.write("Keine Pulsdaten gefunden.")
