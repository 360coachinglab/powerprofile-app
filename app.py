
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
import os

st.set_page_config(page_title="Trainierbares VO₂max-Modell", layout="wide")
st.title("🧠 VO₂max-ML-Modell: Training & Anwendung")

MODEL_PATH = "vo2_model.joblib"
DATA_PATH = "vo2_training_data.csv"

# Daten anzeigen oder hochladen
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
    st.subheader("📊 Aktuelle Trainingsdatenbank")
    st.dataframe(df)
else:
    df = pd.DataFrame()

st.subheader("➕ Neue Athleten-Daten hinzufügen")
with st.form("neuer_athlet"):
    col1, col2, col3 = st.columns(3)
    with col1:
        gewicht = st.number_input("Gewicht (kg)", 40.0, 120.0, 70.0)
        fett = st.number_input("Körperfett (%)", 5.0, 40.0, 15.0)
        vlamax = st.number_input("VLamax", 0.2, 1.0, 0.45)
    with col2:
        mmp1s = st.number_input("MMP 1s (W)", 500, 2000, 1100)
        mmp20s = st.number_input("MMP 20s (W)", 300, 1500, 800)
        mmp1min = st.number_input("MMP 1min (W)", 250, 1000, 550)
    with col3:
        mmp2min = st.number_input("MMP 2min (W)", 250, 900, 500)
        mmp3min = st.number_input("MMP 3min (W)", 250, 850, 480)
        mmp5min = st.number_input("MMP 5min (W)", 250, 800, 460)

    mmp10 = st.number_input("MMP 10min (W)", 200, 700, 410)
    mmp20 = st.number_input("MMP 20min (W)", 150, 600, 360)
    vo2 = st.number_input("VO₂max Zielwert (ml/min/kg)", 40.0, 90.0, 65.0)

    submitted = st.form_submit_button("Hinzufügen & Trainieren")
    if submitted:
        neue_daten = pd.DataFrame([{
            "Gewicht": gewicht,
            "Körperfett": fett,
            "VLamax": vlamax,
            "MMP_1s": mmp1s,
            "MMP_20s": mmp20s,
            "MMP_1min": mmp1min,
            "MMP_2min": mmp2min,
            "MMP_3min": mmp3min,
            "MMP_5min": mmp5min,
            "MMP_10min": mmp10,
            "MMP_20min": mmp20,
            "VO2max": vo2
        }])
        if not df.empty:
            df = pd.concat([df, neue_daten], ignore_index=True)
        else:
            df = neue_daten
        df.to_csv(DATA_PATH, index=False)
        st.success("✅ Neue Daten gespeichert!")

# Training starten
if not df.empty:
    df["FFM"] = df["Gewicht"] * (1 - df["Körperfett"] / 100)
    X = df[["MMP_1s", "MMP_20s", "MMP_1min", "MMP_2min", "MMP_3min", "MMP_5min", "MMP_10min", "MMP_20min", "FFM", "VLamax"]]
    y = df["VO2max"]

    modell = RandomForestRegressor(n_estimators=200, random_state=42)
    modell.fit(X, y)
    joblib.dump(modell, MODEL_PATH)
    y_pred = modell.predict(X)
    st.subheader("📈 Modellgüte (Training)")
    st.write(f"R²: {r2_score(y, y_pred):.3f}")
    st.write(f"MAE: {mean_absolute_error(y, y_pred):.2f} ml/kg/min")

    st.subheader("🎯 Anwendung des trainierten Modells")
    with st.form("anwendung"):
        col1, col2 = st.columns(2)
        with col1:
            g = st.number_input("Gewicht (kg)", 40.0, 120.0, 70.0, key="ag")
            kf = st.number_input("Körperfett (%)", 5.0, 40.0, 15.0, key="akf")
            vl = st.number_input("VLamax", 0.2, 1.0, 0.45, key="avl")
        with col2:
            ffm = g * (1 - kf / 100)
            mmp_values = []
            for label in ["1s", "20s", "1min", "2min", "3min", "5min", "10min", "20min"]:
                mmp = st.number_input(f"MMP {label} (W)", 100, 1500, 400, key=f"mmp{label}")
                mmp_values.append(mmp)

        predict_btn = st.form_submit_button("VO₂max schätzen")
        if predict_btn:
            input_data = np.array(mmp_values + [ffm, vl]).reshape(1, -1)
            prediction = modell.predict(input_data)[0]
            st.success(f"💨 Geschätzte VO₂max: {prediction:.1f} ml/min/kg")
