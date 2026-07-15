import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:

    SECRET_KEY = "stunting-secret-key"

    SQLALCHEMY_DATABASE_URI = \
        "sqlite:///" + os.path.join(BASE_DIR, "instance/stunting.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MODEL_PATH = os.path.join(
        BASE_DIR,
        "app/models/model_stunting859.pkl"
    )

    SCALER_PATH = os.path.join(
        BASE_DIR,
        "app/models/scaler859.pkl"
    )