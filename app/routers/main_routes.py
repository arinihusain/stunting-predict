from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session
)
from io import BytesIO
from flask import send_file
import openpyxl
from openpyxl.styles import Font

from datetime import datetime
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


@main_bp.route("/prediksi")
@login_required
def index():
    return render_template("prediksi.html", fullname=session.get('fullname'))


@main_bp.route("/predict", methods=["POST"])
def predict():

    form_data = request.form

    valid, message = PredictionForm.validate(form_data)

    if not valid:
        return jsonify({
            "success": False,
            "message": message
        }), 400

    data = {
        "jenis_kelamin": int(form_data["jenis_kelamin"]),
        "bb_lahir": float(form_data["bb_lahir"]),
        "umur": float(form_data["umur"]),
        "berat_badan": float(form_data["berat_badan"]),
        "tinggi_badan": float(form_data["tinggi_badan"]),
        "lila": float(form_data["lila"]),
        "tb_ibu": float(form_data["tb_ibu"])
    }

    result = predict_stunting(data)

    history = Prediction(
        user_id=session['user_id'],
        nama_anak=form_data['nama_anak'],
        jenis_kelamin=data['jenis_kelamin'],
        bb_lahir=data['bb_lahir'],
        umur=data['umur'],
        berat_badan=data['berat_badan'],
        tinggi_badan=data['tinggi_badan'],
        lila=data['lila'],
        tb_ibu=data['tb_ibu'],
        prediction=result['prediction'],
        probability=result['probability']
    )

    try:
        db.session.add(history)
        db.session.commit()
    except:
        print("Gagal menyimpan data predict")
        db.session.rollback()

    return jsonify({
        "success": True,
        "result": result
    })


@main_bp.route('/history')
@login_required
def history():

    histories = Prediction.query.filter_by(user_id=session['user_id']).order_by(Prediction.created_at.desc()).all()
    return render_template('history.html', histories=histories, fullname=session.get('fullname'))


@main_bp.route('/')
@login_required
def summary():

    total_predictions = Prediction.query.count()

    total_stunting = Prediction.query.filter_by(
        prediction='Stunting'
    ).count()

    total_normal = Prediction.query.filter_by(
        prediction='Normal'
    ).count()

    today = datetime.utcnow().date()

    daily_predictions = Prediction.query.filter(
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

        normal_percentage = round(
            (total_normal / total_predictions) * 100,
            1
        )

    else:

        stunting_percentage = 0
        normal_percentage = 0

    # =========================
    # GRAFIK BULANAN
    # =========================

    monthly_data = db.session.query(
        extract('month', Prediction.created_at),
        func.count(Prediction.id)
    ).group_by(
        extract('month', Prediction.created_at)
    ).all()

    month_names = [
        'Jan', 'Feb', 'Mar', 'Apr',
        'Mei', 'Jun', 'Jul', 'Agu',
        'Sep', 'Okt', 'Nov', 'Des'
    ]

    monthly_labels = []
    monthly_totals = []

    for month, total in monthly_data:

        monthly_labels.append(
            month_names[int(month)-1]
        )

        monthly_totals.append(total)

    return render_template(

        'dashboard.html',

        fullname=session.get('fullname'),

        total_predictions=total_predictions,
        total_stunting=total_stunting,
        total_normal=total_normal,
        daily_predictions=daily_predictions,

        stunting_percentage=stunting_percentage,
        normal_percentage=normal_percentage,

        monthly_labels=monthly_labels,
        monthly_totals=monthly_totals
    )


@main_bp.route('/tentang')
@login_required
def tentang():
    return render_template("tentang.html", fullname=session.get('fullname'))


# =========================================
# DELETE HISTORY
# =========================================
@main_bp.route('/history/delete/<int:id>', methods=['POST'])
@login_required
def delete_history(id):

    history = Prediction.query.get_or_404(id)

    try:
        db.session.delete(history)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Riwayat berhasil dihapus"
        })
    except:
        return jsonify({
            "success": False,
            "message": "Riwayat gagal dihapus"
        })
    

@main_bp.route('/history/export')
@login_required
def export_history():

    histories = Prediction.query.order_by(
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
        "LILA",
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
            item.lila,
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