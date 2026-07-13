# Effort Summary — Area of Unit & Man Power Enhancement (Lintas Fitur)

*Last updated: 2026-07-10*

---

Dokumen ini merangkum total estimasi effort dari inisiatif **Area of Unit & Man Power** yang tersebar di 3 dokumen enhancement (Inspection & Order, Digiplan, PM Shutdown & BD Corrective) plus 1 dokumen arsitektur pendukung. Tidak menduplikasi detail — hanya merujuk dan menjumlahkan.

## Dokumen Sumber

| Dokumen | Fitur/Service | Isi |
|---|---|---|
| [inspection-order/area-of-unit-man-power-enhancement.md](inspection-order/area-of-unit-man-power-enhancement.md) | Inspection, Additional Order, Order Approval, Master Data | Field baru Area/Man Power di Inspection & Additional Order, Master Data mapping M:N, validasi di Order Approval, gap kirim data ke SAP |
| [dplan/man-power-man-hours-excel-enhancement.md](dplan/man-power-man-hours-excel-enhancement.md) | Digiplan | Man Power/Man Hours + Component/Sub Component/Area di grid & Excel template |
| [pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md](pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md) | PM Shutdown, BD Corrective | Visibility Duration/Man Power/Man Hours di card task, assignment mechanic |
| [inspection-order/order-emol-sap-sync.md](inspection-order/order-emol-sap-sync.md) | `maintenance-order`, SAP middleware | Referensi teknis (bukan dokumen enhancement) — schema & flow existing yang jadi dasar assessment SAP |

---

## Metodologi Estimasi SP & Mandays (Tim BUMA ID)

*(Permintaan client: hitung mandays lebih akurat kalau dikerjakan tim BUMA ID, dan pakai standar kompleksitas riil tim untuk menentukan SP.)*

### A. Kalibrasi SP ke Skala Fibonacci

Awalnya setiap baris di tabel effort diberi **range SP** (mis. "3–5") berdasarkan label kompleksitas kualitatif (Kecil/Sedang/Besar) — ini murni judgment, **bukan** hasil planning poker atau perbandingan ke tiket historis. Setelah dicek, konvensi SP riil tim BUMA ID (dari `end_of_sprint_report.py`/`ORR_sprint_report.py`) memakai **skala Fibonacci `[1, 2, 3, 5, 8]` per tiket** — 1 angka pasti, bukan range.

Untuk menyelaraskan, setiap baris **dikalibrasi ulang ke 1 angka Fibonacci** pakai konvensi standar:

| Label Kompleksitas | SP |
|---|---|
| Kecil | 1 |
| Kecil–Sedang | 2 |
| Sedang | 3 |
| Sedang–Besar | 5 |
| Besar | 8 |

Sebagai konteks pembanding (bukan dasar perhitungan mandays — lihat bagian B), berikut **baseline cycle-time riil tim BUMA ID** (rata-rata waktu To Do → DEV DONE, dari `ORR_sprint_report.py`, 5 sprint closed terakhir):

| Story Point | Baseline Tim BUMA ID (hari kerja) |
|---|---|
| 1 | 1.09 |
| 2 | 2.36 |
| 3 | 8.25 ⚠️ *(anomali — lebih besar dari SP 5, kemungkinan sample size kecil di sprint-sprint ini; tidak dianggap kebenaran mutlak)* |
| 5 | 9.76 |
| 8 | 21.63 |

**Catatan penting**: baseline ini mengukur *cycle time* (elapsed calendar days, termasuk waktu tunggu/context-switching) — **bukan** *effort murni*. Karena itu, baseline ini **tidak** dipakai langsung sebagai mandays (akan overstate effort) — hanya dipakai sebagai konteks pembanding relatif kompleksitas.

### B. Rasio Mandays/SP (Basis Throughput)

Basis mandays memakai rasio **throughput** tim (bukan cycle-time), dari data Jira riil.

*Revisi 11 Jul 2026*: sebelumnya rasio ini dihitung dari 2 sprint terakhir saja (~0.68 mandays/SP), sementara estimasi jumlah sprint (bagian C) dihitung dari velocity **5 sprint terakhir** — 2 basis waktu yang berbeda untuk 2 perhitungan yang seharusnya konsisten. Client meminta keduanya disamakan, jadi rasio mandays/SP di bawah ini sekarang **juga dihitung dari 5 sprint terakhir**, sama seperti basis velocity di bagian C.

| Sprint | Completed SP | Hari Kerja (business days) |
|---|---|---|
| Release 3.1.0 (Sprint 2) | 73 | 17 |
| Release 4.0.0 - S1 | 35 | 15 |
| Release 4.0.0 - S2 | 63 | 10 |
| Release 4.0.0 - S3 | 60 | 9 |
| 4.1.0 - Improve and Fix | 81 | 10 |
| **Total** | **312 SP** | **61 hari** |

**Perhitungan:** 312 SP ÷ (5 developer × 61 hari = 305 person-days) = ~1.02 SP per person-day → **~0.98 mandays per SP**.

*Catatan: rasio 2-sprint sebelumnya (~0.68 mandays/SP) tetap valid sebagai data point, tapi tidak dipakai lagi supaya konsisten dengan basis velocity 5 sprint di bagian C. Rasio ~0.98 ini yang sekarang dipakai konsisten di seluruh estimasi mandays pada dokumen ini dan 3 dokumen sumbernya.*

### C. Efek Kalibrasi: Bottom-Up vs Top-Down

Setelah dikalibrasi per-baris ke Fibonacci lalu dijumlahkan (bottom-up), totalnya **sedikit lebih tinggi** dari estimasi range top-down sebelumnya di beberapa bagian (mis. subtotal Man Power/Man Hours Digiplan naik dari 8–13 SP menjadi 23 SP setelah dijumlah per-baris). Ini pola umum dalam estimasi: menjumlahkan estimasi per-komponen kecil cenderung menghasilkan total lebih besar dibanding estimasi holistik top-down, karena tiap baris "dibulatkan ke atas" ke angka Fibonacci terdekat dan overhead integrasi antar-baris terhitung berulang. Angka final di bawah adalah hasil bottom-up (per-baris Fibonacci), **dianggap lebih andal** karena granular per komponen, meski totalnya naik dari estimasi awal.

---

## Rekap Estimasi

*(SP 1 angka pasti hasil kalibrasi Fibonacci — bukan range. Mandays = SP × 0.98, basis 5 sprint terakhir — konsisten dengan basis velocity sprint di bagian C.)*

| # | Sumber | Scope | SP | Mandays |
|---|---|---|---|---|
| 1 | area-of-unit-man-power-enhancement.md Bagian 3 | Master Data UI, permission, Inspection, Additional Order, edit eMOL, Order Approval, `PoolingMOItem`/payload, MO Backlog inbound + filter per-client, testing e2e | **33** | **~32** |
| 2a | man-power-man-hours-excel-enhancement.md Bagian 4 ("Tanpa" logic penuh) | Man Power/Man Hours (23) + assessment predecessor/serial/paralel (3) + Component/Sub Component/Area (14) — parent Man Power/Man Hours **dikosongkan dulu** (interim) | **40** | **~39** |
| 2b | man-power-man-hours-excel-enhancement.md Bagian 4.0.1 (tambahan kalau **"Dengan"** logic penuh, pakai `DPPredecessor` existing) | Implementasi penuh rollup Man Power/Man Hours parent dengan kondisi predecessor/serial/paralel | **+8** (di atas 2a) | **+~8** |
| 3 | man-power-duration-visibility-enhancement.md Bagian 3 | Visibility card task, assignment mechanic warning/notes, 2 skenario mandatory (PM Shutdown/BD Corrective) | **12** | **~12** |
| — | Mapping BAPI ke SAP (bagian dari #1, assessment tim client dengan SAP mereka) | Kirim Component/Sub Component/Area/Duration/Man Power lewat BAPI | **Belum bisa diestimasi** | **Belum bisa diestimasi** |

### Total Estimasi — 2 Skenario (di luar mapping BAPI ke SAP)

*(Permintaan client: perbandingan effort dengan vs tanpa logic predecessor/serial/paralel di rollup parent Man Power/Man Hours — detail di [dplan/man-power-man-hours-excel-enhancement.md](dplan/man-power-man-hours-excel-enhancement.md) 4.0.1. Direvisi 11 Jul 2026 — SP dikalibrasi ke Fibonacci, dan rasio mandays/SP disamakan basisnya (5 sprint) dengan basis velocity sprint.)*

| Skenario | Total SP | **Total Mandays** |
|---|---|---|
| **Tanpa** logic penuh — parent Man Power/Man Hours dikosongkan dulu (1 + 2a + 3) | **85 SP** | **~83 mandays** |
| **Dengan** logic penuh predecessor/serial/paralel (1 + 2a + 2b + 3) | **93 SP** | **~91 mandays** |

**Selisih: 8 SP (~8 mandays)** kalau business memilih implementasi logic predecessor/serial/paralel penuh sejak rilis pertama, dibanding opsi interim (parent kosong dulu, bisa direvisit belakangan). Selisih ini **jauh lebih kecil** dari perkiraan awal karena data model dependency (`DPPredecessor` — `FromTask`/`ToTask`/`Type`/`Lag`) **sudah ada**, bukan perlu dibangun dari nol — sehingga opsi "Dengan" logic penuh cukup layak dipertimbangkan untuk rilis pertama sekalian.

Asumsi: 1 developer per work-item, dikerjakan berurutan — bisa lebih cepat kalau dikerjakan paralel oleh beberapa developer lintas service, belum termasuk waktu review/QA terpisah. Mandays dihitung dengan rasio tim BUMA ID (~0.98 mandays/SP, basis 5 sprint) — kalau dikerjakan tim lain dengan velocity berbeda, rasio ini perlu disesuaikan.

### Estimasi Jumlah Sprint

*(Permintaan client: berapa sprint dibutuhkan berdasarkan rata-rata kecepatan 5 sprint terakhir tim BUMA ID.)*

Rata-rata velocity 5 sprint terakhir tim BUMA ID (Release 3.1.0-Sprint2: 73 SP, Release 4.0.0-S1: 35 SP, S2: 63 SP, S3: 60 SP, 4.1.0: 81 SP) = **312 SP ÷ 5 = 62.4 SP/sprint** (kapasitas penuh tim).

Karena tim juga menangani **support issue Production** di sela sprint (pola yang konsisten terlihat di sprint report — selalu ada delayed/reopened ticket, adhoc testing, dst), kapasitas yang bisa didedikasikan murni untuk enhancement ini diasumsikan **70%**, sisanya **30% untuk production support**:

**Kapasitas efektif = 62.4 × 70% = ~43.7 SP/sprint**

| Skenario | Total SP | ÷ Kapasitas Efektif (43.7 SP/sprint) | Kebutuhan Sprint |
|---|---|---|---|
| **Tanpa** logic penuh | 85 SP | 85 ÷ 43.7 = 1.95 | **2 sprint** |
| **Dengan** logic penuh | 93 SP | 93 ÷ 43.7 = 2.13 | **3 sprint** (2 sprint hanya cukup ~87.4 SP, sisa ~5.6 SP masuk ke sprint ke-3) |

*Catatan: ini asumsi kasar mengabaikan panjang sprint yang sebenarnya bervariasi (9–17 hari kerja per sprint pada data historis) dan mengasumsikan alokasi 70/30 konsisten sepanjang durasi pengerjaan. Angka riil bisa berubah tergantung prioritas production issue yang muncul saat itu.*

---

## Sumber Ketidakpastian Terbesar

1. **Mapping BAPI ke SAP** (di luar total di atas) — feasibility & effort di sisi SAP belum diketahui sampai assessment client dengan tim SAP mereka selesai. Bisa kecil (numpang field text existing) atau besar/multi-sprint (custom Z-field, di luar kontrol tim Digiman+).
2. **Skema Master Data Area↔Component-SubComponent** — apakah 3 dimensi atau 4 dimensi (scoped per Asset Model). Kalau 4 dimensi, estimasi Master Data UI di #1 bisa naik dari 5 SP ke 8 SP.
3. **Rollup Man Power/Man Hours di level parent task** — sudah ada estimasi untuk 2 skenario (lihat tabel di atas), turun signifikan dari perkiraan awal setelah dikonfirmasi tabel `DPPredecessor` (`FromTask`/`ToTask`/`Type`/`Lag`) **sudah ada** — jadi bukan riset struktur data dari nol, cuma finalisasi formula rollup. Angka "Dengan" logic penuh (2b) masih perkiraan sampai formula final diputuskan business.
4. Estimasi ini disusun dari deskripsi arsitektur pemilik produk tanpa akses source code — perlu divalidasi oleh engineer yang pegang codebase `maintenance-execution`, `maintenance-order`, dan `dplan` masing-masing.

---

## Referensi
- [inspection-order/area-of-unit-man-power-enhancement.md](inspection-order/area-of-unit-man-power-enhancement.md)
- [dplan/man-power-man-hours-excel-enhancement.md](dplan/man-power-man-hours-excel-enhancement.md)
- [pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md](pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md)
- [inspection-order/order-emol-sap-sync.md](inspection-order/order-emol-sap-sync.md)
- [dplan/digital-planning.md](dplan/digital-planning.md)
