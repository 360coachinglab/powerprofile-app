
import streamlit as st
from vlamax_model_predict import vlamax_prediction
import numpy as np

st.title("🚴 Leistungsprofil-Analyse – Manuelle Eingabe")

# --- Eingabegrunddaten ---
st.header("🧍 Athletenprofil")
col1, col2 = st.columns(2)
with col1:
    gewicht = st.number_input("Gewicht (kg)", 40.0, 120.0, 70.0, 0.1)
    koerperfett = st.number_input("Körperfett (%)", 5.0, 40.0, 15.0, 0.1)
    geschlecht = st.selectbox("Geschlecht", ["Mann", "Frau"])
    geschlecht_code = 1 if geschlecht == "Frau" else 0
with col2:
    fahrertyp = st.selectbox("Geplantes Zielprofil", ["XCO", "Marathon", "Strasse", "Kriterium", "Bergfahrer", "Sprinter", "Zeitfahrer"])

ffm = gewicht * (1 - koerperfett / 100)

# --- Leistungseingaben ---
st.header("⚡ Peak-Leistungswerte eingeben")
col1, col2, col3 = st.columns(3)
with col1:
    w5s = st.number_input("5s Peak (W)", 200, 2000, 1100, 10)
    w20s = st.number_input("20s Peak (W)", 200, 1500, 900, 10)
with col2:
    w1m = st.number_input("1min Peak (W)", 200, 1200, 700, 10)
    w3m = st.number_input("3min Peak (W)", 200, 1000, 600, 10)
with col3:
    w5m = st.number_input("5min Peak (W)", 200, 1000, 550, 10)
    w20m = st.number_input("20min Peak (W)", 100, 600, 300, 10)

# --- Analyse starten ---
if st.button("🔍 Analyse starten"):
    cp = (w3m + w20m) / 2  # simple CP-Schätzung
    vo2_rel = 16.6 + 8.87 * (w5m / gewicht)
    vo2_cp_rel = 10.8 * (cp / gewicht) + 7
    vlamax = vlamax_prediction(ffm, 20, w20s, w5s, geschlecht_code)

    st.success(f"📈 FTP (CP-basiert): {cp:.0f} W")
    st.success(f"🫁 VO₂max (5min MMP): {vo2_rel:.1f} ml/min/kg")
    st.success(f"🫁 VO₂max (CP-basiert): {vo2_cp_rel:.1f} ml/min/kg")
    st.success(f"⚡ VLamax: {vlamax:.3f} mmol/l/s")

    # --- Vergleich mit Referenzprofilen (statisch als Beispiel) ---
    st.header("📊 Vergleich mit Typ-Profilen")
    st.markdown("""
    | Typ         | 5s   | 1min | 5min | 20min |
    |-------------|------|------|------|--------|
    | Sprinter    | 18 W/kg | 10 W/kg | 6 W/kg | 4 W/kg |
    | Kriterium   | 15 W/kg | 8 W/kg | 5.5 W/kg | 4.5 W/kg |
    | XCO         | 14 W/kg | 7.5 W/kg | 5.8 W/kg | 4.6 W/kg |
    | Marathon    | 12 W/kg | 6 W/kg | 5.2 W/kg | 4.4 W/kg |
    | Bergfahrer  | 10 W/kg | 6 W/kg | 6 W/kg | 5 W/kg |
    """)

    # --- Empfehlungen je nach Ziel ---
    st.header("📌 Trainings-Empfehlung")
    if fahrertyp == "XCO":
        st.markdown("- 2× pro Woche VO₂max-Intervalle: 4x4min @ 110–120% FTP
- 1× Sprinttraining (8× 20s all-out)
- 1× Sweetspot-Session (3× 12min @ 88–94% FTP)")
    elif fahrertyp == "Sprinter":
        st.markdown("- Anaerobes Intervalltraining 10× 30/30s @ 150% FTP
- Maximalkrafttraining am Berg (6–8 Wiederholungen)
- Sprintstarts mit >1300 W")
    elif fahrertyp == "Bergfahrer":
        st.markdown("- Schwellenintervalle: 3× 20min @ 100–105% FTP
- lange Grundlageneinheiten (3–5h) bei 65–70% HFmax")

