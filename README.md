# Stunting Predict

Aplikasi web Flask untuk prediksi risiko stunting pada anak.

## Persyaratan

- Python 3.12
- pip

## Cara Menjalankan (Development)

1. Clone repo ini, lalu masuk ke folder project:

   ```
   git clone <url-repo>
   cd stunting-predict
   ```

2. Buat virtual environment:

   ```
   python -m venv venv
   ```

3. Aktifkan virtual environment:

   - Windows (PowerShell):
     ```
     venv\Scripts\Activate.ps1
     ```
   - Windows (cmd):
     ```
     venv\Scripts\activate.bat
     ```
   - Linux/Mac:
     ```
     source venv/bin/activate
     ```

4. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

5. (Opsional, sekali saja) Buat akun admin default:

   ```
   python create_admin.py
   ```

   Ini akan membuat user admin dengan username `arini1` dan password `arini123`. Database SQLite (`instance/stunting.db`) akan otomatis dibuat saat aplikasi pertama kali dijalankan.

6. Jalankan aplikasi:

   ```
   python run.py
   ```

7. Buka browser ke:

   ```
   http://127.0.0.1:5001
   ```

   > Catatan: port default diubah ke `5001` karena port `5000` sering di-reserve oleh Windows (Hyper-V/WSL) sehingga menyebabkan error `An attempt was made to access a socket in a way forbidden by its access permissions`. Kalau di komputer kamu port `5000` bebas, boleh dikembalikan di `run.py`.

## Struktur Singkat

- `app/` - kode aplikasi (routes, forms, models, utils)
- `app/models/predictor.py` - logika prediksi stunting (pakai model `.pkl` di `app/models/`)
- `config.py` - konfigurasi (database, path model)
- `run.py` - entry point untuk menjalankan server
- `create_admin.py` - script untuk membuat akun admin awal
