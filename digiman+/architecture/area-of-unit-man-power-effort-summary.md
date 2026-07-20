# Effort Summary — Area of Unit & Man Power Enhancement (Lintas Fitur)

*Last updated: 2026-07-20*

---

Dokumen ini merangkum total estimasi effort dari inisiatif **Area of Unit & Man Power** yang tersebar di 3 dokumen enhancement (Inspection & Order, Digiplan, PM Shutdown & BD Corrective) plus 1 dokumen arsitektur pendukung. **Seluruh detail breakdown SP/mandays per komponen ada di dokumen ini** (dipisah dari masing-masing dokumen enhancement, 20 Jul 2026 — pola yang sama dengan [inspection-order/maintenance-activity-type-enhancement.md](inspection-order/maintenance-activity-type-enhancement.md) + [inspection-order/maintenance-activity-type-effort-summary.md](inspection-order/maintenance-activity-type-effort-summary.md)). Dokumen enhancement sumber cukup berisi keputusan & scope produk, tidak lagi menduplikasi tabel effort.

## Dokumen Sumber

| Dokumen | Fitur/Service | Isi |
|---|---|---|
| [inspection-order/area-of-unit-man-power-enhancement.md](inspection-order/area-of-unit-man-power-enhancement.md) | Inspection, Additional Order, Order Approval, Master Data | Field baru Area/Man Power di Inspection & Additional Order, enhance UI existing "Equipment Mapping" untuk assign `AreaCode` (1:N per `ModelComponentSubComponent`), validasi di Order Approval, gap kirim data ke SAP |
| [dplan/man-power-man-hours-excel-enhancement.md](dplan/man-power-man-hours-excel-enhancement.md) | Digiplan | Man Power/Man Hours + Component/Sub Component/Area di grid & Excel template |
| [pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md](pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md) | PM Shutdown, BD Corrective | Visibility Duration/Man Power/Man Hours di card task, assignment mechanic |
| [inspection-order/order-emol-sap-sync.md](inspection-order/order-emol-sap-sync.md) | `maintenance-order`, SAP middleware | Referensi teknis (bukan dokumen enhancement) — schema & flow existing yang jadi dasar assessment SAP |

> **Belum termasuk di rekap ini**: [inspection-order/maintenance-activity-type-enhancement.md](inspection-order/maintenance-activity-type-enhancement.md) — enhancement terpisah (redesign sourcing PM/Maintenance Activity Type), menyentuh layar sama persis dengan `area-of-unit-man-power-enhancement.md` (Additional Order screen 1 & 2). Estimasi SP/mandays/sprint-nya sendiri **sudah ada** di [inspection-order/maintenance-activity-type-effort-summary.md](inspection-order/maintenance-activity-type-effort-summary.md) — **43 SP, ~50 mandays**, 3 skenario sprint tergantung tim (BUMA ID baseline ~1 sprint sangat mepet; BUMA ID Modified tim baru ~5 sprint dengan atau tanpa Knowledge Transfer) — cuma belum digabung ke rekap total di dokumen ini.

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

**⚠️ Dikoreksi (16 Jul 2026)**: sebelumnya dipakai "5 developer" — **salah**. Roster riil tim BUMA ID (`BUMA_ID_MEMBERS` di `Jira/sprint-report/ORR_sprint_report.py`, dikonfirmasi user) adalah **6 orang**: 4 Dev (2 BE, 1 FE Web, 1 FE Mobile — dilabeli "Dev" generik di script, tidak dipecah sub-role di situ) + 2 QA. Velocity tim seharusnya menghitung **seluruh anggota termasuk QA** (kapasitas QA juga "terpakai" untuk menyelesaikan SP, bukan cuma Dev) — dikonfirmasi user, standar Scrum.

**Perhitungan (dikoreksi):** 312 SP ÷ (6 orang × 61 hari = 366 person-days) = **~0.85 SP per person-day** → **~1.17 mandays per SP** (naik dari 0.98 — tim sebenarnya butuh mandays lebih banyak per SP dari yang sebelumnya dihitung, karena headcount asli lebih besar dari asumsi awal).

*Catatan: rasio 2-sprint sebelumnya (~0.68 mandays/SP) tetap valid sebagai data point historis, tapi tidak dipakai. Rasio **~1.17** ini yang sekarang jadi basis mandays konsisten di seluruh dokumen — SP/sprint capacity (bagian C, 62.4 SP/sprint) **tidak berubah** karena itu murni SP-selesai-per-sprint riil, tidak bergantung ke headcount.*

**✅ Sinkronisasi 20 Jul 2026**: rasio 1.17 ini sekarang benar-benar konsisten diterapkan ke seluruh tabel per-baris di bawah (sebelumnya sempat ada 3 dokumen sumber yang masih memakai rasio lama ~0.98 secara internal meski rekap ini sudah pakai 1.17 — sudah disinkronkan).

### C. Efek Kalibrasi: Bottom-Up vs Top-Down

Setelah dikalibrasi per-baris ke Fibonacci lalu dijumlahkan (bottom-up), totalnya **sedikit lebih tinggi** dari estimasi range top-down sebelumnya di beberapa bagian (mis. subtotal Man Power/Man Hours Digiplan naik dari 8–13 SP menjadi 23 SP setelah dijumlah per-baris). Ini pola umum dalam estimasi: menjumlahkan estimasi per-komponen kecil cenderung menghasilkan total lebih besar dibanding estimasi holistik top-down, karena tiap baris "dibulatkan ke atas" ke angka Fibonacci terdekat dan overhead integrasi antar-baris terhitung berulang. Angka final di bawah adalah hasil bottom-up (per-baris Fibonacci), **dianggap lebih andal** karena granular per komponen, meski totalnya naik dari estimasi awal.

---

## Detail Effort per Dokumen

### 1. `area-of-unit-man-power-enhancement.md` — Inspection, Additional Order, Order Approval, Master Data

*(Scope keputusan lengkap ada di dokumen sumber, Bagian 2. SP dikalibrasi Fibonacci, mandays = SP × 1.17.)*

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| ~~Master Data UI baru~~ — Enhance UI existing `Equipment Mapping` (modal `Add New Component`): tambah field `AreaCode` | Kecil–Sedang | 2 | 2.3 | **Direvisi 20 Jul 2026** — turun dari 5 SP: dikoreksi dari "bangun UI baru" jadi "enhance modal existing + 1 field dropdown Area (posisi field pertama, tanpa filtering ke Component/Sub Component)". Scope jauh lebih kecil karena modal & list-nya sudah ada, tinggal 1 field + wiring simpan `AreaCode`. *(Desain skema 1 kolom `AreaCode` di `ModelComponentSubComponent` — 16 Jul 2026 — dan asumsi 1:N-nya — divalidasi ke data real/mechanical SME 20 Jul 2026 — tidak berubah.)* Regression scope tetap lebih lebar karena tabel yang di-ALTER dipakai fitur lain (Rating, DamageCode) |
| Equipment Mapping: tambah **Edit action baru** (assign/ubah Area untuk row existing) | Kecil–Sedang | 2 | 2.3 | *(Baris baru, 20 Jul 2026)* List "Equipment Mapping" saat ini cuma punya Action `View`/`Delete` — perlu `Edit` baru supaya admin HO bisa ubah Area row yang sudah ada tanpa hapus row |
| Data migration awal (BE): backfill `AreaCode` ke row `ModelComponentSubComponent` existing | Kecil–Sedang | 2 | 2.3 | *(Baris baru, 20 Jul 2026)* Mekanisme migrasi/script sekali jalan untuk rollout awal (volume row existing besar — 81 row untuk 1 kombinasi Model saja di contoh yang direview, dikali jumlah Model lain) — bukan isi datanya, isi Area per baris tetap disiapkan tim Product/HO, pola sama dengan seeder `MaintenanceActivityType` di [inspection-order/maintenance-activity-type-effort-summary.md](inspection-order/maintenance-activity-type-effort-summary.md) |
| Master data `Area` (Code/Name): UI maintain baru (CRUD standalone) | Sedang | 3 | 3.5 | *(Baris baru, 20 Jul 2026)* Terpisah dari modal "Add New Component" (yang cuma assign `AreaCode` ke row existing) — ini layar untuk **mendefinisikan** daftar Area itu sendiri, reference class: CRUD standar + validasi unique Code, pola sama dengan Master Data UI `MaintenanceActivityType` di [inspection-order/maintenance-activity-type-effort-summary.md](inspection-order/maintenance-activity-type-effort-summary.md) |
| Permission code baru untuk maintain Master Data (admin HO) | Kecil | 1 | 1.2 | Setup permission code + assign ke role |
| Inspection & Additional Inspection: tambah field Man Power di create finding | Kecil–Sedang | 2 | 2.3 | *(Direvisi 16 Jul 2026 — Area bukan field UI, cukup derive+simpan backend)* Component/Sub Component sudah ada (cascading 2 level tidak berubah), tinggal extend +1 field Man Power + logic backend lookup `AreaCode` — 1 form yang sama berlaku untuk Inspection maupun Additional Inspection, tidak perlu effort terpisah |
| Additional Order: tambah field Component, Sub Component, Duration, Man Power di create screen | Sedang | 2 | 2.3 | *(Direvisi 16 Jul 2026 — Area dikeluarkan dari field UI)* Field baru di layar ini (belum ada sebelumnya, layar terpisah dari Inspection) + cascading dropdown 2 level (Component→Sub Component, sama pola dengan Inspection) + validasi + backend derive Area |
| Edit eMOL: carry-forward nilai dari Finding/Additional Order (auto-fill, tetap editable) | Kecil–Sedang | 2 | 2.3 | Passing value ke layar edit eMOL, bukan re-input |
| Order Approval: tambah validasi & edit Man Power, Duration | Kecil–Sedang | 2 | 2.3 | *(Direvisi 20 Jul 2026 — Component/Sub Component diralat, diabaikan dulu dari scope layar ini; tetap tidak bisa diedit di approval seperti behavior sekarang. Sebelumnya 16 Jul 2026 Area juga sudah dikeluarkan.)* Scope sekarang cuma 2 field numerik (Man Power, Duration) — tidak perlu reuse dropdown Master Data lagi di layar ini. UI baru di layar approval (edit mode + save) + validasi Man Power integer >0 |
| `PoolingMOItem`/payload: tambah kolom Area, Duration, Man Power (Component/Sub Component sudah ada) | Sedang | 3 | 3.5 | Extend insert query & payload di [inspection-order/order-emol-sap-sync.md](inspection-order/order-emol-sap-sync.md) |
| Mapping BAPI: kirim Component, Sub Component, Area, Duration, Man Power ke SAP | **Belum bisa diestimasi** | — | — | Tergantung hasil assessment client dengan tim SAP mereka — bisa kecil (numpang field text) atau besar/multi-sprint (custom Z-field, butuh kerja sisi SAP client di luar kontrol estimasi tim Digiman+) |
| MO Backlog inbound: parse balik Component, Sub Component, Area, Duration, Man Power dari SAP response | Sedang | 3 | 3.5 | Extend parsing/mapping saat pull MO Backlog |
| ~~MO Backlog filter jadi konfigurasi per-client (bukan hardcode)~~ | — | **0** | **0** | **✅ Diputuskan (17 Jul 2026): bukan lagi item dev Digiman+.** Tanggung jawab filtering dipindah ke **sisi tenant/middleware** — client yang menentukan MO mana yang dikirim ke Digiman+ lewat konfigurasi middleware/SAP mereka sendiri, bukan Digiman+ yang filter dari MO yang sudah diterima. Alasan: fleksibilitas per-client tanpa Digiman+ perlu bangun & maintain config UI/logic filter |
| Testing end-to-end (Finding/Additional Order → eMOL → Approval → SAP → MO Backlog → Digiplan) | Besar | 8 | 9.4 | Banyak titik integrasi lintas service (`maintenance-execution`, `maintenance-order`, `dplan`), perlu test tiap checkpoint + regresi |
| **[DE]** Digiman Transaction Report — D'INSPECT RESULT: tambah `Area`/`Man Power`/`Duration`/`Man Hours` ke `vw_report_iams_inspection_results` (2.7) | Kecil–Sedang | 2 | 2.3 | *(Baris baru, 20 Jul 2026)* 1 jalur sumber, 3 titik CTE (lihat [inspection-result.md](../report/transaction-report/inspection-result.md) Planned Changes) |
| **[DE]** Digiman Transaction Report — D'ORDER RESULT & ORDERING COMPLIANCE: tambah 4 kolom yang sama ke `vw_report_iams_f_am_digiman_dorder` (2.7) | Sedang | 3 | 3.5 | *(Baris baru, 20 Jul 2026)* Lebih kompleks dari `Maint. Act. Type` — 2 jalur sumber (Inspection + Additional Order) di-`COALESCE`, 7 titik CTE (lihat [order-result-compliance.md](../report/transaction-report/order-result-compliance.md) Planned Changes). Reference class riil (Jira, dicek 20 Jul 2026): [IAMS30-3946](https://bukittechnology.atlassian.net/browse/IAMS30-3946) (Varian/DE, 3 SP — "Enhance `vw_report_iams_f_am_digiman_dorder`", tambah 1 kolom + 1 tabel baru ke **view yang sama persis**) — 3 SP di sini konsisten dengan preseden itu meski scope kita lebih besar (4 kolom, 2 jalur sumber vs 1 kolom 1 jalur) |
| **[DA]** Update dataset/report Power BI — tampilkan `Area`/`Man Power`/`Duration`/`Man Hours` di D'Inspect Result & D'Order Result/Ordering Compliance (2 halaman) | Besar | 8 | 9.4 | *(Baris baru, 20 Jul 2026, direvisi setelah cek Jira langsung)* Reference class riil: subtask [IAMS30-3946](https://bukittechnology.atlassian.net/browse/IAMS30-3946) — [IAMS30-3950](https://bukittechnology.atlassian.net/browse/IAMS30-3950) (Herianto/DA, 2 SP, "Adjust PBI based on WorkflowTransaction status") + [IAMS30-3980](https://bukittechnology.atlassian.net/browse/IAMS30-3980) (Herianto/DA, 3 SP, "Add Last Sync in Dashboard") = **5 SP untuk scope lebih kecil** (1 view, ~1 metrik + 1 tabel baru) dari punya kita (4 kolom × 2 halaman) — diskalakan naik ke 8 SP. **Bukti nyata risiko stabilisasi** dari fitur yang sama persis: 3 bug reopen pasca-rilis — [IAMS30-4012](https://bukittechnology.atlassian.net/browse/IAMS30-4012) (DE, 2 SP), [IAMS30-4013](https://bukittechnology.atlassian.net/browse/IAMS30-4013) (DE, 1 SP), [IAMS30-4015](https://bukittechnology.atlassian.net/browse/IAMS30-4015) (DA, unpointed) — **bukan hipotetis, ini pola nyata yang sudah terjadi 2×** untuk perubahan sejenis di view yang sama, pertimbangkan serius buffer stabilisasi pasca-rilis (di luar 8 SP ini) |
| **Total (di luar mapping BAPI)** | | **45** | **~52** | *(Naik dari 32 SP, 20 Jul 2026 — tambah 3 baris dampak report: 2 SQL view [DE] + 1 Power BI [DA], +13 SP, direvisi dari +10 SP setelah cek reference class Jira riil)* 1 angka pasti (bukan range) — hasil kalibrasi Fibonacci per baris |
| **⚠️ Catatan role [DE]/[DA]** | | | | **BUMA ID roster (6 orang) tidak punya DE/DA** (`Jira/sprint-report/ORR_sprint_report.py` — cuma 2 BE/1 FE Web/1 FE Mobile/2 QA) — DE/DA riil di project ini adalah **Varian Aditya Iryanto** (DE) & **Herianto Salim** (DA), dikonfirmasi lewat histori Jira 20 Jul 2026. SP di atas **sudah** pakai reference class SP riil dari kerja mereka (bukan lagi placeholder murni). **Rasio mandays 1.17 tetap placeholder** — histori timestamp Jira mereka (`resolutiondate`) banyak mengelompok di tanggal yang sama (batch-close), jadi tidak bisa dipakai hitung throughput SP/hari riil tanpa analisis changelog/transisi status lebih dalam (di luar scope pengecekan cepat ini) — rasio BUMA ID (1.17) dipakai sebagai pendekatan terbaik yang tersedia sekarang. Implikasi lain: karena DE/DA di luar 6 orang BUMA ID, effort ini **kemungkinan tidak memperebutkan kapasitas 43.7 SP/sprint** tim BUMA ID — bisa jalan paralel, bukan otomatis nambah durasi sprint BUMA ID. Lihat Estimasi Jumlah Sprint di bawah untuk implikasinya. |

*Catatan: estimasi berdasarkan deskripsi arsitektur dari pemilik produk, tanpa akses langsung ke source code — perlu divalidasi oleh engineer yang pegang codebase `maintenance-execution`/`maintenance-order`. Skema mapping Area sudah final secara desain (16 Jul 2026: 1 kolom `AreaCode` di `ModelComponentSubComponent`) dan asumsi 1:N-nya sudah divalidasi ke data real/mechanical SME (20 Jul 2026). Mapping BAPI tetap sumber ketidakpastian terbesar lainnya.*

---

### 2. `dplan/man-power-man-hours-excel-enhancement.md` — Digiplan (Man Power/Man Hours + Component/Sub Component/Area)

*(Scope keputusan lengkap ada di dokumen sumber, Bagian 3. SP dikalibrasi Fibonacci, mandays = SP × 1.17.)*

**Baseline Man Power/Man Hours:**

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| Template Config UI: guardrail Man Power & Man Hours tidak bisa di-disable/dihapus | Kecil–Sedang | 2 | 2.3 | Nonaktifkan toggle *Is Shown* & tombol delete khusus 2 baris ini di layar Config → Custom Column |
| Grid UI: cell Man Hours read-only (tidak bisa diedit langsung) | Kecil–Sedang | 2 | 2.3 | Beda perlakuan dari kolom dinamis lain yang semuanya editable; perlu flag khusus di level UI/`DPColumn` |
| Grid: edit Duration/Man Power → trigger recalculate & save Man Hours | Sedang | 3 | 3.5 | Titik sentuh baru di endpoint save/update task grid |
| Excel export: tampilkan Man Power & Man Hours | Kecil–Sedang | 2 | 2.3 | Karena mandatory di semua template baru (dan tidak retroactive), resolve `ColumnId` konsisten selalu ada untuk plan baru — plan lama tetap pakai template lama tanpa kolom ini |
| Excel import: parse & validasi Man Power, upsert ke `DPValue` | Sedang | 3 | 3.5 | Validasi tipe/`IsMandatory` dari metadata `DPColumn` |
| Excel import: hitung & upsert Man Hours setelah Man Power tersimpan | Sedang | 3 | 3.5 | Reuse shared service yang sama dengan grid-save |
| Auto-recalculate saat struktur task berubah (add/delete child, re-parenting) | Sedang | 3 | 3.5 | Trigger rollup parent (Duration/Man Power/Man Hours) otomatis; urutan proses harus dijaga — rollup Duration parent selesai dulu, baru Man Hours parent dihitung ulang |
| Testing Man Power/Man Hours (grid edit, excel upload, kombinasi ada/tidaknya kolom, hierarki parent-child, bulk) | Sedang–Besar | 5 | 5.9 | Dua entry point (grid + excel) harus konsisten hasil kalkulasinya |
| **Subtotal Man Power/Man Hours (baseline)** | | **23** | **~27** | ⚠️ Lebih tinggi dari estimasi top-down sebelumnya (8–13 SP) — penjumlahan Fibonacci per baris (bottom-up) cenderung menghasilkan total lebih besar dibanding estimasi top-down holistik; lihat catatan metodologi bagian C |

**Perbandingan Effort: Rollup Man Power/Man Hours di Level Parent — "Dengan" vs "Tanpa" Predecessor/Serial/Paralel**

*(Permintaan client: estimasi effort untuk 2 skenario — logic predecessor/serial/paralel diimplementasikan penuh, vs parent dikosongkan dulu. Revisi 10 Jul 2026: estimasi diturunkan signifikan dari perkiraan awal setelah dikonfirmasi tabel `DPPredecessor` — `FromTask`/`ToTask`/`Type`/`Lag` — sudah ada dan memodelkan konsep Sequence/Serial/Paralel dengan baik. Risiko terbesar sebelumnya, harus membangun/menangkap struktur predecessor dari nol, tidak berlaku — yang tersisa murni soal formula & implementasi traversal-nya.)*

| Skenario | SP | Mandays | Penjelasan |
|---|---|---|---|
| **Tanpa** — parent dikosongkan dulu (opsi interim) | **1** | **1.2** | Ini sudah jadi asumsi baseline di subtotal di atas — effort tambahannya minimal, cuma perlu pastikan UI grid & Excel menampilkan kosong/dash (bukan error atau `0`) di baris parent untuk Man Power & Man Hours, dan Man Hours parent otomatis ikut kosong (karena butuh Man Power). Tidak butuh assessment lanjutan untuk opsi ini. |
| **Dengan** — logic penuh predecessor/serial/paralel (menggunakan `DPPredecessor` existing) | **8** (di luar 3 SP assessment/finalisasi formula) | **9.4** (di luar ~3.5 mandays assessment) | Effort utamanya: (1) traversal graph `DPPredecessor` (`FromTask`→`ToTask` per `Type`/`Lag`) untuk tentukan jalur serial vs cabang paralel per parent task; (2) implementasi formula rollup (mis. serial dijumlahkan, paralel diambil terbesar — final ditentukan saat assessment); (3) integrasi ke shared service `RecalculateManHours`/rollup existing; (4) edge case (predecessor tidak lengkap, referensi melingkar); (5) testing. Lebih kecil dari estimasi awal karena data model dependency-nya sudah ada, bukan perlu dibangun. |

**Rekomendasi ke client**: opsi "Tanpa" (interim) hampir tidak menambah cost dan bisa dirilis bersamaan dengan Man Power/Man Hours utama; opsi "Dengan" logic penuh sekarang jauh lebih terjangkau dari perkiraan sebelumnya (karena `DPPredecessor` sudah ada) — bisa dipertimbangkan untuk masuk rilis pertama sekalian, tidak harus ditunda ke fase terpisah, tergantung urgensi bisnisnya.

**+ 3 SP (~3.5 mandays) untuk assessment/finalisasi formula predecessor/serial/paralel** (menentukan rumus rollup berdasarkan `Type`/`Lag` di `DPPredecessor`, terlepas dari opsi mana yang akhirnya dipilih untuk rilis pertama).

**Tambahan: Component, Sub Component, Area** *(10 Jul 2026)*

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| `DPColumn`: tambah 3 kolom baru (Component, Sub Component, Area) sebagai custom column | Kecil | 1 | 1.2 | Tidak mandatory/non-disable seperti Man Power/Man Hours — custom column biasa, lebih simpel |
| Grid UI: 3 dropdown baru dengan cascading Component→Sub Component→Area dari Master Data | Sedang | 3 | 3.5 | Butuh komponen cascading-dropdown baru, fetch dari API Master Data ([inspection-order/area-of-unit-man-power-enhancement.md](inspection-order/area-of-unit-man-power-enhancement.md) 2.2) |
| Auto-fill saat user pilih MO Backlog: isi Component/Sub Component/Area/Duration/Man Power | Sedang | 3 | 3.5 | Termasuk graceful handling kalau kolom tidak ada di Plan (skip field yang tidak ada `DPColumn`-nya) |
| Excel export: tampilkan 3 kolom baru | Kecil | 1 | 1.2 | Kolom text biasa (bukan dropdown Excel), sama pola dengan Man Power |
| Excel import: parse & validasi kombinasi terhadap Master Data (reject + warning kalau tidak match) | Sedang | 3 | 3.5 | Beda dari Man Hours (silent-overwrite) — di sini baris ditolak dengan warning jelas |
| Testing Component/Sub Component/Area (grid, excel, MO Backlog auto-fill, graceful-handling kolom hilang) | Sedang | 3 | 3.5 | |
| **Subtotal Component/Sub Component/Area** | | **14** | **~16** | |

**Total Bagian Digiplan:**

| Skenario Rilis | Total (SP) | Total (Mandays) |
|---|---|---|
| **Tanpa** logic penuh (parent dikosongkan dulu) — Man Power/Man Hours baseline (23) + assessment (3) + Component/Sub Component/Area (14) | **40 SP** | **~47 mandays** |
| **Dengan** logic penuh predecessor/serial/paralel (pakai `DPPredecessor` existing) — baseline (23) + assessment (3) + implementasi penuh (8) + Component/Sub Component/Area (14) | **48 SP** | **~56 mandays** |

**Selisih "Dengan" vs "Tanpa": 8 SP (~9 mandays) tambahan** kalau business memilih implementasi logic predecessor/serial/paralel penuh sejak rilis pertama, dibanding opsi interim (parent kosong). Selisih ini jauh lebih kecil dari perkiraan awal karena data model dependency (`DPPredecessor`) sudah ada, bukan perlu dibangun dari nol.

*Catatan: estimasi berdasarkan deskripsi arsitektur dari pemilik produk, tanpa akses langsung ke source code — perlu divalidasi oleh engineer yang pegang codebase `dplan`, terutama soal performa batch-upsert `DPValue` untuk plan dengan jumlah task besar.*

---

### 3. `pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md` — PM Shutdown & BD Corrective

*(Scope keputusan lengkap ada di dokumen sumber, Bagian 2. SP dikalibrasi Fibonacci, mandays = SP × 1.17.)*

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| Card task: tampilkan Duration, Man Power, Man Hours | Kecil | 1 | 1.2 | Read-only display, data sudah tersedia dari Digiplan |
| Assignment mechanic: hitung selisih vs Man Power plan, tampilkan warning | Kecil–Sedang | 2 | 2.3 | *(Direvisi 20 Jul 2026, turun dari 3 SP — dikonfirmasi validasi cukup 1 titik di endpoint finish, bukan real-time/reaktif tiap assign-unassign)* Logic compare assigned count vs plan, dijalankan sebagai validasi gate saat finish task |
| Assignment mechanic: wajib isi notes kalau ada selisih | Kecil–Sedang | 2 | 2.3 | Field notes + validasi wajib-isi kondisional; disimpan di service `dplan`/`DPlanDB` (20 Jul 2026) |
| 2 skenario mandatory assignment (umum vs backlog-with-MO) | Sedang | 3 | 3.5 | Conditional validation berdasarkan ada/tidaknya MO reference di task |
| Testing (card visibility, warning selisih, notes wajib, 2 skenario mandatory) | Sedang | 3 | 3.5 | |
| **Total** | | **11** | **~13** | *(Turun dari 12 SP, 20 Jul 2026)* 1 angka pasti (bukan range) — hasil kalibrasi Fibonacci per baris |

*Catatan: estimasi berdasarkan deskripsi arsitektur dari pemilik produk, tanpa akses langsung ke source code — perlu divalidasi oleh engineer yang pegang codebase `maintenance-execution`/`dplan`. Sisa open item: apakah field notes terpisah atau reuse existing remark field.*

**Perbandingan Effort: Validasi Assignment saat Finish Execution — 1 Skenario Seragam vs 2 Skenario (Differensiasi Backlog-with-MO)**

*(Permintaan client: estimasi effort untuk 2 pendekatan — 1 aturan seragam untuk semua task, vs 2 skenario berbeda tergantung ada/tidaknya MO reference.)*

| Pendekatan | SP | Mandays | Penjelasan |
|---|---|---|---|
| **1 skenario seragam** — semua task diperlakukan sama (misal selalu warning-only, tidak pernah mandatory) | **1** | **1.2** | Satu jalur validasi saja di Finish Execution — cek assignment kosong → tampilkan warning. Tidak perlu deteksi apakah task backlog execution/punya MO reference. |
| **2 skenario (differensiasi backlog-with-MO)** — keputusan final: warning-only untuk task umum, mandatory untuk task ber-MO reference | **3** (baris "2 skenario mandatory assignment" di tabel atas) | **3.5** | Effort tambahan dari deteksi apakah task itu backlog execution/punya MO reference, lalu branch ke 2 jalur validasi berbeda (non-blocking vs blocking), plus testing kedua jalur. |

**Selisih: 2 SP (~2.3 mandays)** untuk mengimplementasikan differensiasi 2 skenario dibanding kalau cukup 1 aturan seragam untuk semua task. Karena selisihnya kecil dan 2 skenario ini sudah jadi keputusan final business, langsung diimplementasikan sekaligus — tidak ada penghematan berarti kalau ditunda/disederhanakan ke 1 skenario dulu. **Keputusan client (10 Jul 2026): setuju langsung implementasikan 2 skenario sekaligus.**

---

## Rekap Estimasi

*(SP 1 angka pasti hasil kalibrasi Fibonacci — bukan range. Mandays = SP × 1.17, basis 5 sprint terakhir — konsisten dengan basis velocity sprint di bagian C.)*

| # | Sumber | Scope | SP | Mandays |
|---|---|---|---|---|
| 1 | area-of-unit-man-power-enhancement.md (tim BUMA ID) | Master Data (enhance UI existing + UI maintain `Area` baru), permission, Inspection, Additional Order, edit eMOL, Order Approval, `PoolingMOItem`/payload, MO Backlog inbound, testing e2e | **32** | **~37** |
| 1-DE/DA | area-of-unit-man-power-enhancement.md 2.7 (tim **DE/DA**: Varian & Herianto Salim, di luar BUMA ID) | Dampak ke Digiman Transaction Report — 2 SQL view + Power BI (lihat tabel di atas, baris `[DE]`/`[DA]`) | **13** | **~15** *(SP dari reference class Jira riil; mandays masih placeholder rasio BUMA ID, lihat catatan role di atas)* |
| 2a | man-power-man-hours-excel-enhancement.md ("Tanpa" logic penuh) | Man Power/Man Hours (23) + assessment predecessor/serial/paralel (3) + Component/Sub Component/Area (14) — parent Man Power/Man Hours **dikosongkan dulu** (interim) | **40** | **~47** |
| 2b | man-power-man-hours-excel-enhancement.md (tambahan kalau **"Dengan"** logic penuh, pakai `DPPredecessor` existing) | Implementasi penuh rollup Man Power/Man Hours parent dengan kondisi predecessor/serial/paralel | **+8** (di atas 2a) | **+~9** (di atas 2a) |
| 3 | man-power-duration-visibility-enhancement.md | Visibility card task, assignment mechanic warning/notes, 2 skenario mandatory (PM Shutdown/BD Corrective) | **11** | **~13** |
| — | Mapping BAPI ke SAP (bagian dari #1, assessment tim client dengan SAP mereka) | Kirim Component/Sub Component/Area/Duration/Man Power lewat BAPI | **Belum bisa diestimasi** | **Belum bisa diestimasi** |

**Catatan penting (revisi 20 Jul 2026 — DE/DA tidak lagi dibuat track terpisah, per arahan user)**: baris **1-DE/DA (13 SP / ~15 mandays)** sekarang **dihitung masuk ke total effort** (bukan lagi track terpisah, pola sama dengan [inspection-order/maintenance-activity-type-effort-summary.md](inspection-order/maintenance-activity-type-effort-summary.md)). Tapi pekerjaannya dikerjakan resource DE/DA (Varian/Herianto) yang **berbeda dari 6 orang tim BUMA ID** — jadi **berjalan paralel** dengan dev dan muat di dalam durasi dev, **tidak menambah sprint count**. Karena itu: **total effort headline** sudah termasuk 13 SP report (96/104 SP di bawah), sementara **jumlah sprint** tetap dihitung dari SP **dev** (83/91) yang memperebutkan kapasitas 43.7 SP/sprint.

### Total Estimasi — 2 Skenario (termasuk dampak report DE/DA, di luar mapping BAPI ke SAP)

*(Permintaan client: perbandingan effort dengan vs tanpa logic predecessor/serial/paralel di rollup parent Man Power/Man Hours. Total effort termasuk dampak report DE/DA — SP-nya masuk total, tapi karena dikerjakan resource DE/DA secara paralel, tidak menambah sprint; lihat Estimasi Jumlah Sprint.)*

| Skenario | SP dev (1/2a/2b/3) | + Report DE/DA | **Total SP** | **Total Mandays** |
|---|---|---|---|---|
| **Tanpa** logic penuh — parent Man Power/Man Hours dikosongkan dulu (1 + 2a + 3) | 83 | 13 | **96 SP** | **~112 mandays** |
| **Dengan** logic penuh predecessor/serial/paralel (1 + 2a + 2b + 3) | 91 | 13 | **104 SP** | **~122 mandays** |

**Selisih: 8 SP (~9 mandays)** kalau business memilih implementasi logic predecessor/serial/paralel penuh sejak rilis pertama, dibanding opsi interim (parent kosong dulu, bisa direvisit belakangan). Selisih ini jauh lebih kecil dari perkiraan awal karena data model dependency (`DPPredecessor` — `FromTask`/`ToTask`/`Type`/`Lag`) sudah ada, bukan perlu dibangun dari nol — sehingga opsi "Dengan" logic penuh cukup layak dipertimbangkan untuk rilis pertama sekalian.

Asumsi: 1 developer per work-item, dikerjakan berurutan — bisa lebih cepat kalau dikerjakan paralel oleh beberapa developer lintas service, belum termasuk waktu review/QA terpisah. Mandays dihitung dengan rasio tim BUMA ID (~1.17 mandays/SP, basis 5 sprint, 6 orang termasuk QA) — kalau dikerjakan tim lain dengan velocity berbeda, rasio ini perlu disesuaikan.

### Estimasi Jumlah Sprint — Tim BUMA ID (baseline)

*(Permintaan client: berapa sprint dibutuhkan berdasarkan rata-rata kecepatan 5 sprint terakhir tim BUMA ID.)*

Rata-rata velocity 5 sprint terakhir tim BUMA ID (Release 3.1.0-Sprint2: 73 SP, Release 4.0.0-S1: 35 SP, S2: 63 SP, S3: 60 SP, 4.1.0: 81 SP) = **312 SP ÷ 5 = 62.4 SP/sprint** (kapasitas penuh tim).

Karena tim juga menangani **support issue Production** di sela sprint (pola yang konsisten terlihat di sprint report — selalu ada delayed/reopened ticket, adhoc testing, dst), kapasitas yang bisa didedikasikan murni untuk enhancement ini diasumsikan **70%**, sisanya **30% untuk production support**:

**Kapasitas efektif = 62.4 × 70% = ~43.7 SP/sprint**

*(Jumlah sprint dihitung dari **SP dev** — 83/91 — bukan total SP, karena report/PBI DE/DA berjalan paralel di resource terpisah dan tidak memperebutkan kapasitas 43.7 SP/sprint tim dev. Total effort termasuk report = 96/104 SP, lihat kolom di Total Estimasi.)*

| Skenario | SP dev | ÷ Kapasitas Efektif (43.7 SP/sprint) | Kebutuhan Sprint |
|---|---|---|---|
| **Tanpa** logic penuh | 83 SP | 83 ÷ 43.7 = 1.90 | **2 sprint** |
| **Dengan** logic penuh | 91 SP | 91 ÷ 43.7 = 2.08 | **3 sprint** (2 sprint hanya cukup ~87.4 SP, sisa ~3.6 SP masuk ke sprint ke-3) |

*Catatan: ini asumsi kasar mengabaikan panjang sprint yang sebenarnya bervariasi (9–17 hari kerja per sprint pada data historis) dan mengasumsikan alokasi 70/30 konsisten sepanjang durasi pengerjaan. Angka riil bisa berubah tergantung prioritas production issue yang muncul saat itu.*

**Report & Power BI — DE/DA (dampak report, 2.7)**: 13 SP / ~15 mandays *(SP dari reference class Jira riil — Varian/Herianto Salim; mandays masih placeholder rasio BUMA ID, lihat catatan role)*, **sudah termasuk di total effort** (96/104 SP) tapi dikerjakan resource DE/DA yang berbeda dari tim dev — **berjalan paralel** dan muat di dalam durasi sprint dev, jadi **tidak menambah jumlah sprint**. Durasi absolut track DE/DA sendiri belum bisa dihitung dengan metodologi sprint yang sama — histori `resolutiondate` Varian/Herianto di Jira banyak mengelompok di tanggal yang sama (batch-close), jadi throughput SP/hari riil mereka belum bisa dihitung tanpa analisis changelog/transisi status lebih dalam.

---

### Skenario Alternatif: Tim Baru Terpisah ("BUMA ID Modified")

*(20 Jul 2026 — permintaan: hitung juga effort kalau dikerjakan **tim baru terpisah**, pola sama dengan skenario "BUMA ID Modified" di [inspection-order/maintenance-activity-type-effort-summary.md](inspection-order/maintenance-activity-type-effort-summary.md). Ini **bukan** penambahan orang ke tim BUMA ID — ini tim Scrum lain yang berdiri sendiri, sprint & kapasitas independen. Terdiri dari **1 BE, 1 FE Web, 1 FE Mobile, 1 QA** — 4 orang, semuanya baru di codebase & domain ini. Report/PBI DE/DA (13 SP, Varian/Herianto) **sudah termasuk di total effort** tapi dikerjakan resource DE/DA terpisah yang **berjalan paralel** — jadi tidak masuk 4 orang tim baru ini & tidak masuk critical path di bawah (muat di dalam durasi dev), sama seperti skenario baseline. Mapping BAPI juga tetap di luar, belum bisa diestimasi.)*

**Kenapa cara hitungnya beda dari baseline**: skenario BUMA ID baseline pakai **kapasitas SP/sprint riil tim** (43.7 SP/sprint — data historis yang sudah mencakup semua orang bekerja paralel), jadi tidak perlu breakdown role/dependency. Tim baru **belum punya data historis**, jadi jumlah sprint dihitung dari **critical path per-role** (BE jadi bottleneck) — pendekatan bottom-up yang sama persis dengan maint activity type.

#### Breakdown SP per role

Setiap baris effort di dokumen ini dipetakan ke role pakai asumsi platform yang sama dengan maint activity type: **Master Data admin & Order Approval = Web; layar Inspection / Additional Order / eMOL & card execution mechanic = Mobile; schema/API/migration/SAP-sync/kalkulasi/Excel = BE; testing = QA.** Digiplan diasumsikan seluruhnya Web (grid + Excel, tidak ada layar mobile).

| Sumber | BE | FE Web | FE Mobile | QA | Total |
|---|---|---|---|---|---|
| #1 Area of Unit core (32 SP) | 17.5 | 4.5 | 2 | 8 | 32 |
| #2a Digiplan "Tanpa" logic penuh (40 SP) | 25 | 7 | 0 | 8 | 40 |
| #3 PM Shutdown & BD Corrective (11 SP) | 6 | 0 | 2 | 3 | 11 |
| **Subtotal "Tanpa" logic penuh (83 SP)** | **48.5** | **11.5** | **4** | **19** | **83** |
| #2b Tambahan "Dengan" logic penuh predecessor/serial/paralel (+8 SP) | +8 | 0 | 0 | 0 | +8 |
| **Subtotal "Dengan" logic penuh (91 SP)** | **56.5** | **11.5** | **4** | **19** | **91** |

> Asumsi platform (Web vs Mobile) belum dikonfirmasi ke tim aktual — kalau ternyata beda, breakdown per role perlu disesuaikan. Baris "campur" (field UI + logic backend) dipecah proporsional; angka pecahan (mis. 17.5) berasal dari split baris Master Data schema-vs-UI — pola sama dengan maint activity type. **Report/PBI DE/DA (13 SP) tidak masuk breakdown role ini** — sudah termasuk di total effort tapi dikerjakan resource DE/DA paralel (di luar 4 orang tim baru), jadi tidak menambah critical path. Tambahan "Dengan" logic penuh (2b, +8 SP) murni kerja BE (traversal graph `DPPredecessor` + formula rollup), tidak menyentuh FE/QA di luar regresi yang sudah tercakup baris QA.

#### Velocity: 2 skenario (tanpa vs dengan Knowledge Transfer)

Sama persis dengan asumsi di [inspection-order/maintenance-activity-type-effort-summary.md](inspection-order/maintenance-activity-type-effort-summary.md): tim yang benar-benar baru di domain & codebase ini tidak bisa langsung secepat tim BUMA ID veteran (~0.85 SP/person-day riil).

| | Tanpa KT | Dengan KT |
|---|---|---|
| Velocity | **0.7 SP/hari/orang** (asumsi) | **0.81 SP/hari/orang** — menutup 75% jarak dari 0.7 menuju ceiling riil BUMA ID (0.85): `0.7 + 0.75 × (0.85 − 0.7) ≈ 0.81` |

#### Critical path & jumlah sprint

Critical path = **BE + QA** (serial), karena FE (Web 11.5 + Mobile 4 = 15.5 SP gabungan) jauh lebih kecil dari BE (48.5–56.5 SP) → FE selalu selesai duluan lalu menganggur menunggu BE, tidak menambah durasi. QA baru bisa mulai penuh setelah BE selesai (butuh endpoint, SAP-sync, & integrasi lintas service kelar untuk test e2e). Sprint = 10 hari kerja / 2 minggu, dibulatkan ke atas.

| Skenario Logic | Team | Critical Path (BE+QA) | ÷ Velocity → Hari | Sprint | Total Mandays (SP ÷ velocity) |
|---|---|---|---|---|---|
| **Tanpa** (83 SP) | Modified — dengan KT | 48.5 + 19 = 67.5 SP | ÷ 0.81 = 83.3 hari | **~9 sprint** | ~103 |
| **Tanpa** (83 SP) | Modified — tanpa KT | 67.5 SP | ÷ 0.7 = 96.4 hari | **~10 sprint** | ~119 |
| **Dengan** (91 SP) | Modified — dengan KT | 56.5 + 19 = 75.5 SP | ÷ 0.81 = 93.3 hari | **~10 sprint** | ~112 |
| **Dengan** (91 SP) | Modified — tanpa KT | 75.5 SP | ÷ 0.7 = 107.9 hari | **~11 sprint** | ~130 |

#### Perbandingan lintas tim (konsolidasi)

| Skenario Logic | SP dev | BUMA ID baseline (43.7 SP/sprint, tim 6 orang) | Modified — dengan KT | Modified — tanpa KT |
|---|---|---|---|---|
| **Tanpa** logic penuh | 83 | **2 sprint** | **~9 sprint** | **~10 sprint** |
| **Dengan** logic penuh | 91 | **3 sprint** | **~10 sprint** | **~11 sprint** |

*(SP dev; report/PBI DE/DA 13 SP paralel, tidak masuk critical path — total effort 96/104 SP. Sprint tim baru tidak berubah oleh fold ini.)*

**Temuan penting** (senada tapi lebih tajam dari maint activity type): BE mendominasi **~58–62% total SP** (48.5/83 sampai 56.5/91), jadi **1 BE tunggal di tim baru adalah bottleneck mutlak** — FE Web+Mobile (15.5 SP gabungan) selalu selesai jauh sebelum BE dan sebagian besar durasi menganggur. Menambah **BE ke-2** akan memangkas critical path jauh lebih efektif daripada menambah FE/QA. **KT menghemat ~1 sprint** di kedua skenario logic (Tanpa: 10→9; Dengan: 11→10). Gap besar vs BUMA ID baseline (2–3 sprint) wajar dan bukan kontradiksi: baseline pakai throughput 6 orang paralel yang riil-terukur, sedangkan tim baru dihitung dari critical path 1 BE + 1 QA serial dengan velocity per-orang yang lebih rendah — persis dinamika yang sama seperti di maint activity type, hanya berlipat karena inisiatif ini ~2× lebih besar (83–91 SP vs 48 SP).

---

## Sumber Ketidakpastian Terbesar

1. **Mapping BAPI ke SAP** (di luar total di atas) — feasibility & effort di sisi SAP belum diketahui sampai assessment client dengan tim SAP mereka selesai. Bisa kecil (numpang field text existing) atau besar/multi-sprint (custom Z-field, di luar kontrol tim Digiman+).
2. ~~Skema Master Data Area↔Component-SubComponent — apakah 3 dimensi atau 4 dimensi~~ — **✅ resolved 20 Jul 2026**: final di 1:N per baris `ModelComponentSubComponent` (1 kolom `AreaCode`), asumsi 1:N-nya sudah divalidasi ke data real/mechanical SME. Bukan lagi sumber ketidakpastian besar — lihat detail effort di atas.
3. **Rollup Man Power/Man Hours di level parent task** — sudah ada estimasi untuk 2 skenario (lihat tabel di atas), turun signifikan dari perkiraan awal setelah dikonfirmasi tabel `DPPredecessor` (`FromTask`/`ToTask`/`Type`/`Lag`) **sudah ada** — jadi bukan riset struktur data dari nol, cuma finalisasi formula rollup. Angka "Dengan" logic penuh (2b) masih perkiraan sampai formula final diputuskan business.
4. Estimasi ini disusun dari deskripsi arsitektur pemilik produk tanpa akses source code — perlu divalidasi oleh engineer yang pegang codebase `maintenance-execution`, `maintenance-order`, dan `dplan` masing-masing.

---

## Referensi
- [inspection-order/area-of-unit-man-power-enhancement.md](inspection-order/area-of-unit-man-power-enhancement.md)
- [dplan/man-power-man-hours-excel-enhancement.md](dplan/man-power-man-hours-excel-enhancement.md)
- [pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md](pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md)
- [inspection-order/order-emol-sap-sync.md](inspection-order/order-emol-sap-sync.md)
- [dplan/digital-planning.md](dplan/digital-planning.md)
- [inspection-order/maintenance-activity-type-effort-summary.md](inspection-order/maintenance-activity-type-effort-summary.md) — enhancement terpisah, belum digabung ke rekap ini
- [IAMS30-3946](https://bukittechnology.atlassian.net/browse/IAMS30-3946), [IAMS30-3950](https://bukittechnology.atlassian.net/browse/IAMS30-3950), [IAMS30-3980](https://bukittechnology.atlassian.net/browse/IAMS30-3980) — reference class Jira **[DE]/[DA]** untuk baris dampak report (2.7), dicek 20 Jul 2026
