
def berechne_vlamax(ffm, dauer, watt_avg, watt_peak, geschlecht_code):
    # Regressionsformel aus deinem vlamax-app-Modell
    # Du kannst die Koeffizienten direkt durch die finalen aus deinem Modell ersetzen
    return (
        0.1032
        + 0.00487 * ffm
        - 0.00614 * dauer
        + 0.00063 * watt_avg
        + 0.00048 * watt_peak
        + 0.0329 * geschlecht_code
    )
