
import streamlit as st
import pandas as pd
import numpy as np
import io
from fitparse import FitFile
from vlamax_formula import predict_vlamax
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Leistungsprofil Analyse", layout="wide")

st.title("🚴 Leistungsprofil Analyse & Physiologie")

uploaded_files = st.file_uploader("Wähle FIT-Dateien", type=["fit"], accept_multiple_files=True)

power_data = []

if uploaded_files:
    for file in uploaded_files:
        if file is not None:
            try:
                fitfile = FitFile(io.BytesIO(file.read()))
                records = [r.get_values() for r in fitfile.get_messages("record")]
                df = pd.DataFrame(records)
                if "power" in df.columns and "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df.set_index("timestamp", inplace=True)
                    df = df.resample("1s").mean().interpolate()

                    for dur in [1, 5, 20, 30, 60, 120, 180, 300, 600, 900, 1200, 1800, 2400, 3600, 7200]:
                        window = df["power"].rolling(f"{dur}s").mean()
                        if not window.empty:
                            max_power = window.max()
                            power_data.append((dur, max_power))
            except Exception as e:
                st.error(f"Fehler beim Verarbeiten von {file.name}: {e}")

if power_data:
    df_power = pd.DataFrame(power_data, columns=["Dauer (s)", "Bestleistung (W)"])
    df_power = df_power.drop_duplicates(subset=["Dauer (s)"])
    st.subheader("📈 Power-Daten aus FIT-Dateien")
    st.dataframe(df_power)

    st.subheader("🧠 Eingabe für VO2max, VLamax & FTP")
    gewicht = st.number_input("Gewicht (kg)", 30.0, 120.0, 70.0, 0.1)
    fett = st.number_input("Körperfett (%)", 5.0, 50.0, 15.0, 0.1)
    geschlecht = st.selectbox("Geschlecht", ["Mann", "Frau"])
    geschlecht_code = 1 if geschlecht == "Frau" else 0

    ffm = gewicht * (1 - fett / 100)
    avg20 = df_power[df_power["Dauer (s)"] == 20]["Bestleistung (W)"].values[0] if 20 in df_power["Dauer (s)"].values else 0
    peak = df_power["Bestleistung (W)"].max()

    vlamax = predict_vlamax(ffm, 20, avg20, peak, geschlecht_code)
    st.success(f"🔬 Geschätzte VLamax: {vlamax:.3f} mmol/l/s")

    ftp = df_power[df_power["Dauer (s)"] == 1200]["Bestleistung (W)"].values[0] if 1200 in df_power["Dauer (s)"].values else 0.95 * avg20
    ftp_wkg = ftp / gewicht
    st.success(f"🚀 Geschätzte FTP: {ftp:.0f} W ({ftp_wkg:.2f} W/kg)")

    vo2abs = (ftp * 10.8 + 7) / 1000
    vo2rel = vo2abs * 1000 / gewicht
    st.success(f"💨 VO2max: {vo2abs:.2f} l/min ({vo2rel:.1f} ml/min/kg)")

    st.subheader("📋 Trainingszonen nach FTP")
    zonen = {
        "Zone 1 (Regeneration)": (0, 0.55),
        "Zone 2 (Grundlage)": (0.56, 0.75),
        "Zone 3 (Tempo)": (0.76, 0.90),
        "Zone 4 (Schwelle)": (0.91, 1.05),
        "Zone 5 (VO2max)": (1.06, 1.20),
        "Zone 6 (Anaerob)": (1.21, 1.50),
        "Zone 7 (Neuromuskulär)": (1.51, 2.50)
    }

    for zone, (low, high) in zonen.items():
        st.write(f"{zone}: {low*ftp:.0f} – {high*ftp:.0f} W")
