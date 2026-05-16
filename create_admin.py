from app import create_app
from app.models.database import db
from app.models.user_model import User

app = create_app()

with app.app_context():

    username = "arini1"

    existing = User.query.filter_by(
        username=username
    ).first()

    if existing:
        print("Admin sudah ada")
    else:

        admin = User(
            username=username,
            fullname="Arini"
        )

        admin.set_password("arini123")

        db.session.add(admin)
        db.session.commit()

        print("Admin berhasil dibuat")