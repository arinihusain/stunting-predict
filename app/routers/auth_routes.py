from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from app.forms.login_form import LoginForm
from app.models.user_model import User

auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        form = request.form

        valid, message = LoginForm.validate(form)

        if not valid:
            flash(message, "error")
            return redirect(url_for("auth.login"))

        username = form["username"]
        password = form["password"]

        user = User.query.filter_by(
            username=username
        ).first()

        if not user or not user.check_password(password):

            flash(
                "Username atau password salah",
                "error"
            )

            return redirect(url_for("auth.login"))

        # SAVE SESSION
        session["user_id"] = user.id
        session["fullname"] = user.fullname

        return redirect(url_for("main.summary"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))