import streamlit as st
import pandas as pd
import numpy as np
from fitparse import FitFile
from sklearn.linear_model import LinearRegression

st.title("🚴 Erweiterte Leistungsanalyse aus FIT-Dateien")

uploaded_files = st.file_uploader("FIT-Dateien hochladen", type=["fit"], accept_multiple_files=True)

gewicht = st.number_input("Körpergewicht (kg)", min_value=30.0, max_value=120.0, value=70.0, step=0.1)
koerperfett = st.number_input("Körperfett (%)", min_value=5.0, max_value=50.0, value=15.0, step=0.1)
geschlecht = st.selectbox("Geschlecht", ["Mann", "Frau"])

# Feature Engineering
ffm = gewicht * (1 - koerperfett / 100)
geschlecht_code = 1 if geschlecht.lower() == "frau" else 0

durations = [20, 30, 60, 180, 240, 300, 600, 720, 900, 1200, 1800]

def extract_series(fitfile):
    power_data = []
    for record in fitfile.get_messages("record"):
        power = record.get_value("power")
        if power is not None:
            power_data.append(power)
    return power_data

def best_avg(series, duration):
    if len(series) >= duration:
        rolling = np.convolve(series, np.ones(duration), 'valid') / duration
        return max(rolling)
    return np.nan

def estimate_cp_model(power_dict):
    durations_min = []
    power_values = []
    for d, p in power_dict.items():
        if not np.isnan(p) and d >= 180:  # nur ab 3min sinnvoll für CP
            durations_min.append(d / 60)
            power_values.append(p)
    if len(durations_min) < 2:
        return np.nan  # nicht genug Daten
    inv_t = 1 / np.array(durations_min)
    P = np.array(power_values)
    model = LinearRegression().fit(inv_t.reshape(-1,1), P)
    cp = model.intercept_
    return cp

def estimate_vo2max_5min(power_300, weight):
    # VO2max (absolut): VO2 [L/min] ≈ 0.01141 × P5min + 0.435
    if np.isnan(power_300): return np.nan, np.nan
    vo2_abs = 0.01141 * power_300 + 0.435
    vo2_rel = vo2_abs * 1000 / weight
    return vo2_abs, vo2_rel

def estimate_vlamax(ffm, duration, avg, peak, geschlecht_code):
    # Regression basierend auf deiner letzten Formel
    return (
        0.004385289349914 * ffm +
        0.002030356114603 * duration +
        0.000413636126981 * avg +
        -0.000192203134232 * peak +
        0.055897283917473 * geschlecht_code +
        -0.141169048396927
    )

if uploaded_files:
    all_best = []
    peak_watts = []
    for file in uploaded_files:
        fitfile = FitFile(file)
        power_series = extract_series(fitfile)
        peak_watts.append(max(power_series) if len(power_series) > 0 else np.nan)
        best = {dur: best_avg(power_series, dur) for dur in durations}
        all_best.append(best)

    if all_best:
        df = pd.DataFrame(all_best)
        combined = df.max(axis=0).to_dict()
        peak = np.nanmax(peak_watts)
        avg_20s = combined.get(20, np.nan)
        duration = 20  # fest für VLamax-Schätzung

        # FTP via CP-Modell
        ftp = estimate_cp_model(combined)

        # VO2max
        vo2_abs, vo2_rel = estimate_vo2max_5min(combined.get(300, np.nan), gewicht)

        # VLamax
        vlamax = estimate_vlamax(ffm, duration, avg_20s, peak, geschlecht_code)

        # Anzeige
        st.subheader("📊 Bestwerte")
        st.dataframe(pd.DataFrame(combined.items(), columns=["Dauer (s)", "Bestleistung (W)"]))

        st.subheader("📈 Abgeleitete Parameter")
        st.markdown(f"- **FTP (Critical Power)**: {ftp:.0f} W" if not np.isnan(ftp) else "- **FTP**: nicht berechenbar")
        st.markdown(f"- **VO₂max absolut**: {vo2_abs:.2f} L/min")
        st.markdown(f"- **VO₂max relativ**: {vo2_rel:.0f} ml/min/kg")
        st.markdown(f"- **VLamax**: {vlamax:.2f} mmol/l/s")

        st.subheader("📐 Trainingszonen basierend auf FTP")
        if not np.isnan(ftp):
            zones = {
                "Zone 1 (Aktive Erholung)": (0, 0.55 * ftp),
                "Zone 2 (Grundlagenausdauer)": (0.56 * ftp, 0.75 * ftp),
                "Zone 3 (Tempo)": (0.76 * ftp, 0.9 * ftp),
                "Zone 4 (Schwelle)": (0.91 * ftp, 1.05 * ftp),
                "Zone 5 (VO₂max)": (1.06 * ftp, 1.20 * ftp),
                "Zone 6 (Anaerob)": (1.21 * ftp, 1.50 * ftp),
                "Zone 7 (Neuromuskulär)": (1.51 * ftp, np.nan)
            }
            df_zones = pd.DataFrame([
                {"Zone": z, "Leistung (W)": f"{int(low)}–{int(high) if not np.isnan(high) else '∞'}"}
                for z, (low, high) in zones.items()
            ])
            st.dataframe(df_zones)

        st.subheader("❤️ Herzfrequenzbasierte Zonen (falls verfügbar)")
        hr_all = []
        hr_max = 0
        for file in uploaded_files:
            fitfile = FitFile(file)
            for record in fitfile.get_messages("record"):
                hr = record.get_value("heart_rate")
                if hr:
                    hr_all.append(hr)
                    if hr > hr_max:
                        hr_max = hr

        if hr_max > 0:
            hr_zones = {
                "Zone 1 (Regeneration)": (0, 0.6 * hr_max),
                "Zone 2 (Grundlage)": (0.61 * hr_max, 0.7 * hr_max),
                "Zone 3 (aerob)": (0.71 * hr_max, 0.8 * hr_max),
                "Zone 4 (Schwelle)": (0.81 * hr_max, 0.89 * hr_max),
                "Zone 5 (VO₂max)": (0.90 * hr_max, hr_max),
            }
            df_hr = pd.DataFrame([
                {"Zone": z, "Pulsbereich (bpm)": f"{int(low)}–{int(high)}"}
                for z, (low, high) in hr_zones.items()
            ])
            st.markdown(f"**Erkannte HFmax**: {hr_max} bpm")
            st.dataframe(df_hr)
        else:
            st.write("⚠️ Keine Herzfrequenzdaten gefunden.")

        from fpdf import FPDF
        import base64

        class PowerReportPDF(FPDF):
            def header(self):
                self.set_font("Arial", "B", 14)
                self.cell(0, 10, "Leistungsanalyse", ln=True, align="C")
                self.ln(5)

            def section_title(self, title):
                self.set_font("Arial", "B", 12)
                self.set_fill_color(240, 240, 240)
                self.cell(0, 10, title, ln=True, fill=True)
                self.ln(1)

            def print_parameter(self, label, value):
                self.set_font("Arial", "", 11)
                self.cell(0, 8, f"{label}: {value}", ln=True)

        pdf = PowerReportPDF()
        pdf.add_page()
        pdf.section_title("Erkannte Leistungsdaten")
        pdf.print_parameter("FTP", f"{ftp:.0f} W" if not np.isnan(ftp) else "nicht verfügbar")
        pdf.print_parameter("VO2max (absolut)", f"{vo2_abs:.2f} L/min")
        pdf.print_parameter("VO2max (relativ)", f"{vo2_rel:.0f} ml/min/kg")
        pdf.print_parameter("VLamax", f"{vlamax:.2f} mmol/l/s")

        if not np.isnan(ftp):
            pdf.section_title("Trainingszonen (Leistung)")
            for z, (low, high) in zones.items():
                high_str = f"{int(high)}" if not np.isnan(high) else "∞"
                pdf.print_parameter(z, f"{int(low)}-{high_str} W")

        if hr_max > 0:
            pdf.section_title("Herzfrequenz-Zonen")
            pdf.print_parameter("HFmax", f"{hr_max} bpm")
            for z, (low, high) in hr_zones.items():
                pdf.print_parameter(z, f"{int(low)}-{int(high)} bpm")

        pdf_path = "report.pdf"
        pdf.output(pdf_path)

        with open(pdf_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        href = f'<a href="data:application/octet-stream;base64,{b64}" download="leistungsreport.pdf">📄 PDF herunterladen</a>'
        st.markdown(href, unsafe_allow_html=True)

        st.subheader("🏁 Athletentyp & Renntyp-Vergleich")

        # Typzuordnung (basierend auf Werten)
        typ = "Allrounder"
        if vo2_rel >= 70 and vlamax <= 0.4 and ftp_wkg >= 4.8:
            typ = "Bergfahrer"
        elif vo2_rel >= 65 and vlamax <= 0.35:
            typ = "Zeitfahrer"
        elif vlamax >= 0.6 and ftp_wkg < 4.0:
            typ = "Sprinter"
        elif vo2_rel >= 65 and vlamax >= 0.5 and ftp_wkg >= 4.5:
            typ = "MTB XCO"
        elif vo2_rel >= 60 and vlamax <= 0.5 and ftp_wkg >= 4.2:
            typ = "Marathon MTB"
        elif vo2_rel >= 60 and vlamax >= 0.5:
            typ = "Kriterium"

        st.markdown(f"**Automatisch erkanntes Athletenprofil:** {typ}")

        # Zieltyp Auswahl
        renntyp = st.selectbox("🔧 Ziel-Renntyp auswählen", [
            "MTB XCO", "MTB Marathon", "Strassenrennen", "Zeitfahren", "Kriterium", "Sprintrennen"
        ])

        st.markdown(f"**Zieltyp laut Eingabe:** {renntyp}")

        # Vergleich und Empfehlungen
        if typ != renntyp:
            st.warning("⚠️ Profil stimmt nicht ganz mit dem Zieltyp überein.")
            if renntyp == "MTB Marathon" and vlamax > 0.5:
                st.info("➡️ VLamax senken durch extensive Schwellenintervalle (3x20', 4x15')")
            elif renntyp == "MTB XCO" and vlamax < 0.5:
                st.info("➡️ Glykolytische Leistung steigern mit 30/15s, VO₂max Intervallen")
            elif renntyp == "Sprintrennen" and vlamax < 0.6:
                st.info("➡️ Mehr Sprinttraining (z. B. 6x20s all-out mit voller Erholung)")
            else:
                st.info("➡️ Trainingsfokus je nach Differenz individuell anpassen")
        else:
            st.success("✅ Athlet ist gut auf den Zieltyp abgestimmt.")

        # Empfehlungen
        st.subheader("📋 Trainingsvorschläge")
        vorschlaege = {
            "Sprinter": ["8x20s all-out", "6x30s uphill sprint", "3x5min low cadence"],
            "Kriterium": ["4x3min VO₂max", "2x(5x1min/1min)", "Sprintwiederholungen"],
            "MTB XCO": ["30/15s x 12min", "4x4min VO₂max", "5x1min uphill burst"],
            "Marathon MTB": ["3x20min Schwelle", "2x12min sweetspot", "3x12min low cadence"],
            "Zeitfahrer": ["4x10min @ FTP", "5x5min @ 90% MAP", "Over/Under 2x15min"],
            "Bergfahrer": ["5x5min VO₂max", "3x8min Schwelle", "Laktatshuttle 4x3min"],
            "Allrounder": ["3x10min Tempo", "4x5min Schwelle", "2x8min Over/Under"]
        }

        for t, einheiten in vorschlaege.items():
            if t == typ:
                st.markdown(f"**Trainingsvorschläge für {t}:**")
                for e in einheiten:
                    st.markdown(f"- {e}")
