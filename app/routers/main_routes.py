from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    jsonify,
    session
)
from io import BytesIO
from flask import send_file
import openpyxl
from openpyxl.styles import Font

from datetime import datetime, timedelta
from sqlalchemy import extract, func

from app.models.predictor import predict_stunting
from app.models.prediction_model import Prediction
from app.models.database import db
from app.forms.prediction_form import PredictionForm
from app.utils.auth_helper import login_required

main_bp = Blueprint(
    "main",
    __name__
)


def rekomendasi_for(prediction):
    """Advice text for a result. Shared by /predict and the history detail so the
    two never drift apart."""

    if prediction == 'Stunting':
        return (
            "Anak terindikasi stunting. Segera konsultasi ke tenaga kesehatan, "
            "tingkatkan asupan protein hewani (telur/ikan), dan perbaiki pola asuh makan."
        )

    return (
        "Pertumbuhan anak normal. Pertahankan asupan gizi seimbang "
        "dan rutin timbang berat badan di Posyandu setiap bulan."
    )


@main_bp.route("/prediksi")
@login_required
def index():
    return render_template("prediksi.html")


@main_bp.route("/predict", methods=["POST"])
@login_required
def predict():

    form_data = request.form

    valid, message = PredictionForm.validate(form_data)

    if not valid:
        return jsonify({
            "success": False,
            "message": message
        }), 400

    data = {
        "JK": int(form_data["jenis_kelamin"]),
        "bb_lahir": float(form_data["bb_lahir"]),
        "Usia": float(form_data["umur"]),
        "Berat": float(form_data["berat_badan"]),
        "Tinggi": float(form_data["tinggi_badan"]),
        "tb_ibu": float(form_data["tb_ibu"])
    }
    print("Data yang diterima:", data)  # Debugging line

    result = predict_stunting(data)

    history = Prediction(
        user_id=session['user_id'],
        nama_anak=form_data['nama_anak'],
        jenis_kelamin=data['JK'],
        bb_lahir=data['bb_lahir'],
        umur=data['Usia'],
        berat_badan=data['Berat'],
        tinggi_badan=data['Tinggi'],
        # The form never collects LILA and the model does not use it. An empty
        # string here raised "could not convert string to float" on every insert,
        # which the bare except below used to swallow — so nothing was saved.
        lila=None,
        tb_ibu=data['tb_ibu'],
        prediction=result['prediction'],
        probability=result['probability']
    )

    result['rekomendasi'] = rekomendasi_for(result['prediction'])

    saved = True

    try:
        db.session.add(history)
        db.session.commit()
    except Exception:
        db.session.rollback()
        saved = False
        current_app.logger.exception("Gagal menyimpan hasil prediksi")

    return jsonify({
        "success": True,
        "saved": saved,
        "result": result
    })


@main_bp.route('/history')
@login_required
def history():

    histories = Prediction.query.filter_by(
        user_id=session['user_id']
    ).order_by(Prediction.created_at.desc()).all()

    # Plain dicts for the JSON data island the detail modal reads. Passing the
    # values through markup instead (the old inline onclick) broke on any name
    # containing an apostrophe, and executed anything that looked like code.
    history_rows = [
        {
            'id': item.id,
            'nama': item.nama_anak,
            'jk': 'Laki-laki' if item.jenis_kelamin == 1 else 'Perempuan',
            'bbLahir': item.bb_lahir,
            'umur': item.umur,
            'berat': item.berat_badan,
            'tinggi': item.tinggi_badan,
            'tbIbu': item.tb_ibu,
            'prediction': item.prediction,
            'probability': item.probability,
            'z': item.z_score(),
            'created': item.created_at.strftime('%d %B %Y, %H:%M'),
            'rekomendasi': rekomendasi_for(item.prediction),
        }
        for item in histories
    ]

    return render_template(
        'history.html',
        histories=histories,
        history_rows=history_rows
    )


MONTHS_SHORT = [
    'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
    'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'
]

MONTHS_LONG = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]

DAYS_SHORT = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']


@main_bp.route('/')
@login_required
def summary():

    # Everything on this page is scoped to the signed-in user, matching /history
    # and the export. Mixing global totals with a personal recent-activity list
    # put two contradictory numbers side by side.
    uid = session['user_id']
    owned = Prediction.query.filter_by(user_id=uid)

    total_predictions = owned.count()
    total_stunting = owned.filter_by(prediction='Stunting').count()
    total_normal = owned.filter_by(prediction='Normal').count()

    today = datetime.utcnow().date()

    daily_predictions = owned.filter(
        func.date(Prediction.created_at) == today
    ).count()

    # =========================
    # PERSENTASE
    # =========================

    if total_predictions > 0:

        stunting_percentage = round(
            (total_stunting / total_predictions) * 100,
            1
        )

        # Derived from the other half so the two always total exactly 100 —
        # rounding each independently can produce 100.1 and overflow the bar.
        normal_percentage = round(100 - stunting_percentage, 1)

    else:

        stunting_percentage = 0
        normal_percentage = 0

    # =========================
    # GRAFIK BULANAN
    # =========================

    # A fixed twelve-month series: the chart highlights the current month, so it
    # needs every month present and in order, including the empty ones.
    monthly_counts = {
        int(month): int(total)
        for month, total in db.session.query(
            extract('month', Prediction.created_at),
            func.count(Prediction.id)
        ).filter(
            Prediction.user_id == uid
        ).group_by(
            extract('month', Prediction.created_at)
        ).all()
    }

    monthly_labels = MONTHS_SHORT
    monthly_totals = [monthly_counts.get(month, 0) for month in range(1, 13)]
    active_month_index = today.month - 1

    # =========================
    # RIWAYAT
    # =========================

    recent_predictions = owned.order_by(
        Prediction.created_at.desc()
    ).limit(5).all()

    latest = recent_predictions[0] if recent_predictions else None

    # Seven day columns ending today, for the activity card.
    week_start = today - timedelta(days=6)

    week_rows = owned.filter(
        func.date(Prediction.created_at) >= week_start
    ).order_by(Prediction.created_at.asc()).all()

    week_days = []

    for offset in range(7):

        day = week_start + timedelta(days=offset)

        week_days.append({
            'name': DAYS_SHORT[day.weekday()],
            'num': day.day,
            'is_today': day == today,
            'items': [row for row in week_rows if row.created_at.date() == day]
        })

    return render_template(

        'dashboard.html',

        total_predictions=total_predictions,
        total_stunting=total_stunting,
        total_normal=total_normal,
        daily_predictions=daily_predictions,

        stunting_percentage=stunting_percentage,
        normal_percentage=normal_percentage,

        monthly_labels=monthly_labels,
        monthly_totals=monthly_totals,
        active_month_index=active_month_index,

        recent_predictions=recent_predictions,
        latest=latest,

        week_days=week_days,
        week_total=len(week_rows),
        month_label=MONTHS_LONG[today.month - 1] + ' ' + str(today.year),
        prev_month_label=MONTHS_LONG[today.month - 2],
        next_month_label=MONTHS_LONG[today.month % 12]
    )


@main_bp.route('/tentang')
@login_required
def tentang():
    return render_template("tentang.html")


# =========================================
# DELETE HISTORY
# =========================================
@main_bp.route('/history/delete/<int:id>', methods=['POST'])
@login_required
def delete_history(id):

    # Scoped by owner: without the user_id filter any signed-in user could
    # delete any other user's row by guessing its id.
    history = Prediction.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first_or_404()

    try:
        db.session.delete(history)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Riwayat berhasil dihapus"
        })
    except Exception:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Riwayat gagal dihapus"
        }), 500
    

@main_bp.route('/history/export')
@login_required
def export_history():

    # Same scope as /history — the export used to include every user's rows.
    histories = Prediction.query.filter_by(
        user_id=session['user_id']
    ).order_by(
        Prediction.created_at.desc()
    ).all()

    # Workbook
    wb = openpyxl.Workbook()
    ws = wb.active

    ws.title = "Riwayat Prediksi"

    # HEADER
    headers = [
        "ID",
        "Nama Anak",
        "Jenis Kelamin",
        "BB Lahir",
        "Umur",
        "Berat Badan",
        "Tinggi Badan",
        "TB Ibu",
        "Hasil Prediksi",
        "Probabilitas (%)",
        "Z-Score",
        "Tanggal"
    ]

    ws.append(headers)

    # STYLE HEADER
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # DATA
    for item in histories:

        gender = (
            "Laki-laki"
            if item.jenis_kelamin == 1
            else "Perempuan"
        )

        ws.append([
            item.id,
            item.nama_anak,
            gender,
            item.bb_lahir,
            item.umur,
            item.berat_badan,
            item.tinggi_badan,
            item.tb_ibu,
            item.prediction,
            item.probability,
            item.z_score(),
            item.created_at.strftime('%d-%m-%Y %H:%M')
        ])

    # AUTO WIDTH
    for column_cells in ws.columns:

        length = max(
            len(str(cell.value))
            if cell.value else 0
            for cell in column_cells
        )

        ws.column_dimensions[
            column_cells[0].column_letter
        ].width = length + 5

    # SAVE MEMORY
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="riwayat_prediksi_stunting.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )