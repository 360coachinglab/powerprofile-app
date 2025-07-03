
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

# Lade Beispieldaten
df = pd.read_csv("vo2_training_data.csv")  # Diese Datei musst du vorbereiten

# Feature Engineering
df["FFM"] = df["Gewicht"] * (1 - df["Körperfett"] / 100)

features = [
    "MMP_1s", "MMP_20s", "MMP_1min", "MMP_2min", "MMP_3min", "MMP_5min", "MMP_10min", "MMP_20min", "FFM", "VLamax"
]

X = df[features]
y = df["VO2max"]

# Train/Test-Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ML-Modell: Random Forest
modell = RandomForestRegressor(n_estimators=200, random_state=42)
modell.fit(X_train, y_train)

# Evaluation
y_pred = modell.predict(X_test)
print("R²:", r2_score(y_test, y_pred))
print("MAE:", mean_absolute_error(y_test, y_pred))

# Speichern
joblib.dump(modell, "vo2_model.joblib")
print("✅ Modell gespeichert als vo2_model.joblib")
