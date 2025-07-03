
def predict_vlamax(ffm, dauer, watt_avg, watt_peak, geschlecht_code):
    return 0.441300174112809 + (
        -0.002047883679573 * ffm +
        -0.001519866112106 * dauer +
        0.000343276543089 * watt_avg +
        0.000142497280620 * watt_peak +
        0.024103129674314 * geschlecht_code
    )
