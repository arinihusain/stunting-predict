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

    def z_score(self):
        """TB/U z-score from the WHO LMS reference.

        Delegates to the same function the prediction endpoint uses, so the value
        shown in the history table, the detail modal and the Excel export matches
        the one shown on the result card. Returns None when the age falls outside
        the 0-60 month reference or the row is incomplete.
        """
        from app.models.predictor import calculate_z_score

        try:
            # The reference table is keyed by whole months, 0-60.
            months = int(round(self.umur))
            if months < 0 or months > 60:
                return None
            return calculate_z_score(int(self.jenis_kelamin), self.tinggi_badan, months)
        except (TypeError, ValueError, KeyError, ZeroDivisionError):
            return None