import pickle
import numpy as np
from flask import current_app

# Cache model agar tidak reload terus
model = None
scaler = None


def load_artifacts():

    global model, scaler

    if model is None:
        with open(current_app.config['MODEL_PATH'], 'rb') as f:
            model = pickle.load(f)

    if scaler is None:
        with open(current_app.config['SCALER_PATH'], 'rb') as f:
            scaler = pickle.load(f)


def calculate_z_score(tinggi_badan, umur):
    """
    Simulasi sederhana Z-Score TB/U
    (dapat disesuaikan dengan standar WHO sebenarnya)
    """

    # Rumus pendekatan sederhana
    median_tb = 49 + (umur * 1.5)

    sd = 3.5

    z_score = (tinggi_badan - median_tb) / sd

    return round(z_score, 2)


def interpret_z_score(z_score):
    """
    Interpretasi status WHO berdasarkan Z-Score
    """

    if z_score < -3:
        return "Sangat Pendek"

    elif z_score < -2:
        return "Pendek (Stunting)"

    elif z_score <= 2:
        return "Normal"

    else:
        return "Tinggi"


def predict_stunting(data):

    load_artifacts()

    # =========================
    # FEATURE ARRAY
    # =========================

    features = np.array([[

        data['jenis_kelamin'],
        data['bb_lahir'],
        data['umur'],
        data['berat_badan'],
        data['tinggi_badan'],
        data['lila'],
        data['tb_ibu']

    ]])

    # =========================
    # SCALING
    # =========================

    scaled = scaler.transform(features)

    # =========================
    # PREDICTION
    # =========================

    prediction = model.predict(scaled)[0]

    probability = model.predict_proba(scaled)[0][1]

    label = "Stunting" if prediction == 1 else "Normal"

    # =========================
    # Z-SCORE
    # =========================

    z_score = calculate_z_score(
        data['tinggi_badan'],
        data['umur']
    )

    z_status = interpret_z_score(z_score)

    # =========================
    # RETURN
    # =========================

    return {

        "prediction": label,

        "probability": round(probability * 100, 2),

        "z_score": z_score,

        "z_status": z_status

    }