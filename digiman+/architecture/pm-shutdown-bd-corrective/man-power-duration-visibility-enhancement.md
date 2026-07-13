# Enhancement: Visibility Duration/Man Power/Man Hours & Assignment Mechanic — PM Shutdown & BD Corrective

*Last updated: 2026-07-10*

---

**Feature:** PM Shutdown & BD Corrective (Digiman+)
**Related doc:** [../dplan/man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md), [../inspection-order/area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md)
**Effort summary lintas fitur:** [../area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md)

---

## 1. Latar Belakang

Hasil meeting dengan business (10 Jul 2026) terkait bagaimana kolom Duration/Man Power/Man Hours (dari Digiplan, lihat [man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md)) ditampilkan dan berinteraksi dengan proses assignment mechanic di eksekusi PM Shutdown & BD Corrective.

---

## 2. Keputusan yang Disepakati

### 2.1 Visibility di Card Task
- Duration, Man Power, **dan** Man Hours ketiga-tiganya ditampilkan di dalam card task PM Shutdown/BD Corrective — supaya pengawas (SPV) bisa langsung melihat visibility man power plan tanpa buka detail.

### 2.2 Assignment Mechanic Bebas Menyimpang dari Man Power Plan
- Assign-to tidak dibatasi harus persis sama dengan angka Man Power yang direncanakan — boleh lebih atau kurang.
- Kalau ada selisih antara jumlah mechanic yang di-assign vs Man Power plan, sistem **memberi warning**, dan user **wajib mengisi notes** alasan selisihnya sebelum lanjut.

### 2.3 Dua Skenario Mandatory-nya Assignment
Tergantung jenis eksekusi:
1. **Umum (non-backlog-with-MO)** — assignment mechanic boleh kosong; kalau kosong, sistem hanya kasih **warning untuk awareness**, tapi user tetap bisa finish execution meski assignment belum diisi.
2. **Backlog execution** (atau task yang punya MO reference) — assignment mechanic **mandatory**, minimal harus terisi 1 mechanic, sebelum task bisa di-finish.

Alasan pembedaan: assignment ke mechanic di mobile app saat ini memang tidak selalu jadi langkah wajib secara umum, tapi untuk task yang terhubung ke MO (backlog execution) assignment perlu lebih ketat karena terhubung ke tracking actual effort di SAP.

---

## 3. Scope Perubahan & Estimasi Effort

*(SP dikalibrasi ke skala Fibonacci `[1,2,3,5,8]` — konvensi tim BUMA ID, lihat metodologi kalibrasi di [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md). Mandays dihitung dari rasio throughput ~0.98 mandays/SP — basis 5 sprint terakhir, konsisten dengan basis velocity yang dipakai untuk estimasi jumlah sprint.)*

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| Card task: tampilkan Duration, Man Power, Man Hours | Kecil | 1 | 1.0 | Read-only display, data sudah tersedia dari Digiplan |
| Assignment mechanic: hitung selisih vs Man Power plan, tampilkan warning | Sedang | 3 | 2.9 | Perlu logic compare assigned count vs plan; lihat open item soal real-time vs saat-finish |
| Assignment mechanic: wajib isi notes kalau ada selisih | Kecil–Sedang | 2 | 2.0 | Field notes + validasi wajib-isi kondisional |
| 2 skenario mandatory assignment (umum vs backlog-with-MO) | Sedang | 3 | 2.9 | Conditional validation berdasarkan ada/tidaknya MO reference di task |
| Testing (card visibility, warning selisih, notes wajib, 2 skenario mandatory) | Sedang | 3 | 2.9 | |
| **Total** | | **12** | **~12** | 1 angka pasti (bukan range) — hasil kalibrasi Fibonacci per baris |

*Catatan: estimasi berdasarkan deskripsi arsitektur dari pemilik produk, tanpa akses langsung ke source code — perlu divalidasi oleh engineer yang pegang codebase `maintenance-execution`. Estimasi bisa berubah tergantung jawaban open item di Bagian 4 (real-time vs saat-finish, lokasi penyimpanan notes).*

### 3.1 Perbandingan Effort: Validasi Assignment saat Finish Execution — 1 Skenario Seragam vs 2 Skenario (Differensiasi Backlog-with-MO)

*(Permintaan client: estimasi effort untuk 2 pendekatan — 1 aturan seragam untuk semua task, vs 2 skenario berbeda tergantung ada/tidaknya MO reference, seperti yang sudah disepakati di 2.3.)*

| Pendekatan | SP | Mandays | Penjelasan |
|---|---|---|---|
| **1 skenario seragam** — semua task diperlakukan sama (misal selalu warning-only, tidak pernah mandatory) | **1** | **1.0** | Satu jalur validasi saja di Finish Execution — cek assignment kosong → tampilkan warning. Tidak perlu deteksi apakah task backlog execution/punya MO reference. |
| **2 skenario (differensiasi backlog-with-MO)** — keputusan final di 2.3: warning-only untuk task umum, mandatory untuk task ber-MO reference | **3** (baris "2 skenario mandatory assignment" di tabel atas) | **2.9** | Effort tambahan dari deteksi apakah task itu backlog execution/punya MO reference, lalu branch ke 2 jalur validasi berbeda (non-blocking vs blocking), plus testing kedua jalur. |

**Selisih: 2 SP (~2.0 mandays)** untuk mengimplementasikan differensiasi 2 skenario dibanding kalau cukup 1 aturan seragam untuk semua task. Karena selisihnya kecil dan 2 skenario ini sudah jadi keputusan final business (2.3, bukan lagi open question), **rekomendasi: langsung implementasikan 2 skenario sekaligus** — tidak ada penghematan berarti kalau ditunda/disederhanakan ke 1 skenario dulu.

**Keputusan client (10 Jul 2026): setuju langsung implementasikan 2 skenario sekaligus** — bukan disederhanakan ke 1 skenario dulu. Estimasi Bagian 3 (12 SP / ~12 mandays) sudah mencerminkan pilihan ini (baris "2 skenario mandatory assignment" sudah termasuk di total, bukan tambahan baru).

---

## 4. Open Items / Belum Dibahas

- Detail teknis flag "selisih Man Power vs assignment" — apakah dihitung real-time saat assign, atau divalidasi saat finish task.
- UI/UX detail warning + notes (2.2) — apakah notes ini disimpan sebagai field terpisah atau masuk ke existing notes/remark task.

---

## 5. Referensi
- [../dplan/man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md) — sumber Duration/Man Power/Man Hours (Digiplan)
- [../inspection-order/area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md)
