class PredictionForm:

    @staticmethod
    def validate(form):

        required_fields = [
            'nama_anak',
            'jenis_kelamin',
            'bb_lahir',
            'umur',
            'berat_badan',
            'tinggi_badan',
            'tb_ibu'
        ]

        for field in required_fields:
            if field not in form or form[field] == "":
                return False, f"{field} wajib diisi"

        return True, "Valid"