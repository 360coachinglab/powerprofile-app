

# ---- VLamax berechnen aus Power-Daten ----
from vlamax_formula import berechne_vlamax

st.subheader("⚡ Geschätzte VLamax")
if gewicht and koerperfett and dauer and watt_avg and watt_peak is not None:
    ffm = gewicht * (1 - koerperfett / 100)
    geschlecht_code = 1 if geschlecht.lower() == "frau" else 0
    vlamax = berechne_vlamax(ffm, dauer, watt_avg, watt_peak, geschlecht_code)
    st.success(f"VLamax: {vlamax:.3f} mmol/l/s")
