/* History table: one delegated listener, and row data read from a JSON island
   rather than interpolated into onclick attributes. Modal content is built with
   textContent, so a name containing quotes or markup renders literally. */

(function () {
    'use strict';

    var table = document.querySelector('[data-history-table]');
    var island = document.getElementById('history-data');
    if (!table || !island) return;

    var rows = new Map(
        JSON.parse(island.textContent).map(function (row) {
            return [String(row.id), row];
        })
    );

    var detailModal = document.getElementById('detailModal');
    var deleteModal = document.getElementById('deleteModal');
    var confirmButton = document.getElementById('confirmDelete');
    var pendingId = null;

    function slot(modal, name) {
        return modal.querySelector('[data-slot="' + name + '"]');
    }

    function kvTile(label, value, tone) {
        var tile = document.createElement('div');
        tile.className = 'kv-tile' + (tone ? ' kv-tile--' + tone : '');

        var labelEl = document.createElement('p');
        labelEl.className = 'kv-label';
        labelEl.textContent = label;

        var valueEl = document.createElement('p');
        valueEl.className = 'kv-value';
        valueEl.textContent = value;

        tile.append(labelEl, valueEl);
        return tile;
    }

    function openDetail(row) {
        if (!row) return;

        slot(detailModal, 'nama').textContent = row.nama;
        slot(detailModal, 'created').textContent = row.created;
        slot(detailModal, 'rekomendasi').textContent = row.rekomendasi;

        var risky = row.prediction === 'Stunting';

        slot(detailModal, 'tiles').replaceChildren(
            kvTile('Hasil prediksi', row.prediction, risky ? 'risk' : 'safe'),
            kvTile('Probabilitas', row.probability + '%', risky ? 'risk' : 'safe'),
            kvTile('Z-Score (TB/U)', row.z === null ? '—' : row.z),
            kvTile('Jenis kelamin', row.jk),
            kvTile('Umur', row.umur + ' bulan'),
            kvTile('Berat badan lahir', row.bbLahir + ' kg'),
            kvTile('Berat badan', row.berat + ' kg'),
            kvTile('Tinggi badan', row.tinggi + ' cm'),
            kvTile('Tinggi badan ibu', row.tbIbu + ' cm')
        );

        window.SP.openModal(detailModal);
    }

    function askDelete(row) {
        if (!row) return;
        pendingId = row.id;
        slot(deleteModal, 'confirm').textContent =
            'Riwayat pemeriksaan ' + row.nama + ' (' + row.created + ') akan dihapus permanen.';
        window.SP.openModal(deleteModal);
    }

    table.addEventListener('click', function (event) {
        var button = event.target.closest('button[data-action]');
        if (!button) return;

        var row = button.closest('tr');
        if (!row) return;

        var data = rows.get(row.dataset.rowId);

        if (button.dataset.action === 'detail') openDetail(data);
        else if (button.dataset.action === 'delete') askDelete(data);
    });

    confirmButton.addEventListener('click', async function () {
        if (pendingId === null) return;

        confirmButton.setAttribute('aria-busy', 'true');

        try {
            var response = await fetch('/history/delete/' + pendingId, { method: 'POST' });
            var payload = await response.json();

            if (payload.success) {
                window.location.reload();
                return;
            }

            slot(deleteModal, 'confirm').textContent =
                payload.message || 'Riwayat gagal dihapus.';
        } catch (error) {
            slot(deleteModal, 'confirm').textContent =
                'Tidak dapat terhubung ke server. Coba lagi.';
        } finally {
            confirmButton.removeAttribute('aria-busy');
        }
    });
})();
