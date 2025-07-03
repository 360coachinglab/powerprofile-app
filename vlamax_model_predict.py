
import joblib
import numpy as np
import os

# Lade das Modell beim ersten Import
model_path = "vlamax_model.joblib"
if os.path.exists(model_path):
    modell = joblib.load(model_path)
else:
    modell = None

def vlamax_prediction(ffm, dauer, watt_avg, watt_peak, geschlecht_code):
    if modell is None:
        raise ValueError("❌ VLamax-Modell nicht gefunden. Bitte 'vlamax_model.joblib' bereitstellen.")
    features = np.array([[ffm, dauer, watt_avg, watt_peak, geschlecht_code]])
    return modell.predict(features)[0]
