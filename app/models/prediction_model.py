from datetime import datetime
from app.models.database import db

class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    nama_anak = db.Column(db.String(150))
    jenis_kelamin = db.Column(db.Integer)

    bb_lahir = db.Column(db.Float)
    umur = db.Column(db.Float)
    berat_badan = db.Column(db.Float)
    tinggi_badan = db.Column(db.Float)
    lila = db.Column(db.Float)
    tb_ibu = db.Column(db.Float)

    prediction = db.Column(db.String(50))
    probability = db.Column(db.Float)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )