/* Prediction form. The result markup lives in <template> elements in the page,
   so this file only clones one and fills [data-slot] nodes with textContent —
   no HTML is built from strings, and every style comes from theme.css. */

(function () {
    'use strict';

    var form = document.getElementById('predictionForm');
    var resultArea = document.getElementById('resultArea');
    if (!form || !resultArea) return;

    var button = document.getElementById('predictButton');
    var buttonText = button.querySelector('[data-slot="button-text"]');

    function render(templateId) {
        var tpl = document.getElementById(templateId);
        var node = tpl.content.cloneNode(true);
        var root = node.firstElementChild;
        resultArea.replaceChildren(node);
        return root;
    }

    function setSlot(root, slot, text) {
        var el = root.querySelector('[data-slot="' + slot + '"]');
        if (el) el.textContent = text;
    }

    function busy(state) {
        button.setAttribute('aria-busy', String(state));
        buttonText.textContent = state ? 'Memproses…' : 'Jalankan prediksi';
    }

    function showError(title, message) {
        var root = render('tpl-error');
        setSlot(root, 'title', title);
        setSlot(root, 'message', message);
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();

        /* app.js validates on submit first and stops the event when a field is
           invalid, so reaching here means the form is complete. */
        busy(true);
        render('tpl-loading');

        try {
            var response = await fetch('/predict', {
                method: 'POST',
                body: new FormData(form)
            });

            var payload = await response.json();

            if (!payload.success) {
                showError('Prediksi gagal', payload.message || 'Data belum bisa diproses.');
                return;
            }

            var data = payload.result;
            var root = render('tpl-result');

            root.dataset.tone = data.prediction === 'Stunting' ? 'risk' : 'safe';

            var ring = root.querySelector('.progress-ring');
            ring.style.setProperty('--pct', data.probability);
            ring.setAttribute('aria-label', 'Probabilitas: ' + data.probability + '%');
            root.querySelector('[data-slot="ring-value"]').textContent = data.probability + '%';

            setSlot(root, 'zscore', data.z_score);
            setSlot(root, 'zstatus', data.z_status);
            setSlot(root, 'rekomendasi', data.rekomendasi);

            /* The page promises the result is saved automatically, so say so when
               it was not, rather than showing a clean card over a failed write. */
            if (payload.saved === false) {
                var warning = root.querySelector('[data-slot="save-warning"]');
                warning.textContent =
                    'Hasil ini tidak tersimpan ke riwayat. Coba lagi, atau hubungi administrator.';
                warning.hidden = false;
            }
        } catch (error) {
            showError('Koneksi bermasalah', 'Tidak dapat terhubung ke server prediksi.');
        } finally {
            busy(false);
        }
    });
})();
