# Backlog Monitoring — Dokumentasi

Dokumentasi adaptasi SP `usp_iams_backlog_monitoring` dari tenant BUMA ID ke tenant MKP. Baca berurutan sesuai alur di bawah — masing-masing dokumen adalah tahap berbeda, bukan versi duplikat.

## Urutan Baca

1. **[backlog-monitoring-analysis.md](backlog-monitoring-analysis.md)** — *26 Mei 2026.* Referensi arsitektur & business logic Backlog Monitoring sebagaimana berjalan di BUMA ID (data source, status MO, aging, dimension tables, config files). Snapshot yang tidak berubah — baca ini dulu kalau belum familiar dengan sistemnya sama sekali.
2. **[backlog-monitoring-mkp-assessment.md](backlog-monitoring-mkp-assessment.md)** — *05 Jun, updated 09 Jun 2026.* Gap analysis: bagian mana dari sistem BUMA ID yang hardcode/tidak kompatibel dengan MKP, risk & mitigasi, roadmap. Tiap item punya kolom **Status** yang menunjuk ke keputusan final di dokumen #3 — dokumen ini sendiri sudah tidak diupdate lagi, statusnya historical gap analysis.
3. **[backlog-monitoring-mkp-implementation.md](backlog-monitoring-mkp-implementation.md)** — *Living document, mulai 09 Jun 2026.* Keputusan final & implementasi per item (6 keputusan sejauh ini). **Ini yang terus diupdate** — setiap ada kesimpulan baru dari diskusi implementasi MKP, tambahkan sebagai section baru di sini.

## Kenapa 3 file terpisah, bukan 1?

- **analysis** = fakta tentang sistem existing (BUMA ID), jarang berubah.
- **assessment** = snapshot penilaian gap pada satu titik waktu — berguna sebagai jejak (kenapa keputusan diambil, apa saja yang tadinya jadi concern) tapi tidak dimaksudkan untuk terus diedit.
- **implementation** = satu-satunya dokumen yang jadi *source of truth* keputusan final dan terus tumbuh. Kalau assessment & implementation digabung, riwayat gap analysis akan tercampur dengan keputusan final dan sulit dibedakan mana yang masih rencana vs. yang sudah fix.

Setiap file `.md` punya pasangan `.html`/`.pdf` dengan nama sama — versi HTML/PDF dipakai untuk dibagikan sebagai laporan berformat (styling, badge, dsb.), versi `.md` untuk dibaca/di-diff langsung di editor atau git.

## File Pendukung Lain di Folder Ini

| File | Isi |
|---|---|
| `Backlog Monitoring.sql` | SP `usp_iams_backlog_monitoring` (BUMA ID) |
| `vw_dim_equipment.sql`, `vw_dim_site.sql`, `sp_dim_date.sql` | Dimension views/SP terkait |
| `*.csv` | Config mapping & data reference (mol_status, aging_category, config_image, dorder lookup) — ingat, delimiter CSV pakai `;` |
| `backlog-monitoring-mkp-konfirmasi.pptx`, `generate_mkp_confirmation_ppt.py` | Materi & script untuk sesi konfirmasi dengan tim MKP |
