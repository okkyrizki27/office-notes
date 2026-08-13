# Timeline & Skenario Delivery — FINAL (Squad Diperkuat, 2 Rilis)

*Last updated: 2026-08-03*

---

Dokumen ini adalah **skenario final** hasil diskusi bertahap dari [squad-baru-release-timeline.md](squad-baru-release-timeline.md) (Skenario A — 4 orang, 3 rilis sequential). Dua skenario antara sempat dibuat sebagai file terpisah selama diskusi — Skenario B (gabung Rilis 1+2, squad tetap 4 orang) dan Skenario C (eksplorasi opsi headcount 5/6 orang) — keduanya sudah dihapus setelah keputusan final ini diambil (sudah digantikan, bukan referensi aktif lagi).

**Gantt chart interaktif**: [claude.ai/code/artifact/15a73a97-b0f1-431a-8c67-6fb5966c2204](https://claude.ai/code/artifact/15a73a97-b0f1-431a-8c67-6fb5966c2204) — 2 panel Rilis 1 & Rilis 2, hover/focus per task untuk detail, toggle tabel breakdown SP.

**Keputusan final (2026-08-03)**:
- **Squad diperkuat dari 4 → 7 orang**: 2→**3 Backend**, 1→**2 Frontend Fullstack** (Web+Mobile, tugas dibagi bebas — bukan dipisah per platform), 1→**2 QA**.
- **2 rilis** (bukan 3): **Rilis 1** = Man Power, Duration & Man Hours + Area of Unit, Component & Sub Component (digabung). **Rilis 2** = Maintenance Activity Type & Integrasi Inspection→Order (scope sama persis dengan Rilis 3 Skenario A) + **My Work & eMAR** (ditambahkan 2026-08-13, lihat bawah).
- **Freeze code penuh antar rilis** — Rilis 2 tidak dimulai sebelum Rilis 1 ship (tidak ada BE yang nyicil kerjaan Rilis 2 selama Rilis 1 masih berjalan).

**Revisi scope (2026-08-13)**: Rilis 2 sekarang juga mencakup **My Work** & **eMAR** (*Electronic Mechanic Activity Report*) — dua fitur baru yang ship bersamaan dengan Maintenance Activity Type, bukan rilis terpisah. Total SP Rilis 2 naik dari 48 → **161 SP**. Ship awalnya diperkirakan Minggu 18, lalu **direvisi ke Minggu 19** (lihat "Revisi Capacity Check" di bawah) — total proyek: 12 → **19 minggu**. Rilis 1 tidak berubah. Breakdown lengkap ada di bagian "Dasar Perhitungan" dan di Gantt chart artifact (link di atas, sudah diupdate).

---

## Ringkasan Skenario

| | |
|---|---|
| **Squad** | 7 orang: **3 Backend, 2 Frontend Fullstack (Web+Mobile), 2 QA** |
| **Velocity** | Sama seperti skenario sebelumnya: ramp-up 0.81 SP/hari/orang (Sprint 1–2, Minggu 1–4), full speed 0.85 SP/hari/orang (Sprint 3 dst, Minggu 5+) |
| **Antar-rilis** | Freeze code penuh — tidak ada overlap/cicil kerjaan Rilis 2 selama Rilis 1 berjalan |
| **Release Preparation** | 1 minggu per rilis (2×1 minggu = 2 minggu total) |
| **QA** | Mulai bertahap (shift-left) — testing modul yang sudah selesai duluan, bukan nunggu 100% dev rilis selesai. Rilis 1 pakai +1 minggu buffer QA (keputusan 2026-08-03); Rilis 2 tetap tanpa buffer tambahan di luar perpanjangan akibat scope baru |
| **Total estimasi** | **~19 minggu** (naik dari ~12 minggu setelah My Work & eMAR ditambahkan ke Rilis 2, 2026-08-13 — direvisi dari estimasi awal 18 minggu setelah capacity check per-orang, lihat bawah). Perbandingan langsung ke 19 minggu Skenario A **tidak lagi apple-to-apple** — Skenario A tidak pernah mencakup My Work/eMAR, tidak direcompute di sini. Tapi angkanya kini **kebetulan sama persis**: Squad Diperkuat + My Work/eMAR = 19 minggu = Skenario A (4 orang, 3 rilis). Bukan berarti squad diperkuat sia-sia (Skenario A akan lebih lambat lagi kalau My Work/eMAR ditambahkan ke dalamnya juga) — tapi benefit "lebih cepat dari Skenario A" yang jadi justifikasi awal keputusan 7 orang praktis hilang begitu Rilis 2 diperluas |

---

## Master Timeline (~19 Minggu, direvisi 2026-08-13)

| Minggu | Rilis | Fase |
|---|---|---|
| 1–6 | Rilis 1 (Man Power + Area) | Dev + QA (QA mulai bertahap dari Minggu 2, +1 minggu buffer) |
| **7** | Rilis 1 | **Release Preparation** |
| — | | **🚀 Rilis 1 ship — akhir Minggu 7** |
| 8–18 | Rilis 2 (Maintenance Activity Type + My Work + eMAR) | Dev + QA (QA mulai paralel dari Minggu 8 — test case design sejak hari pertama; My Work BE baru mulai penuh Minggu 11 menunggu Activity Type melepas kapasitas — lihat capacity check di bawah; fase end-to-end diperpanjang ke Minggu 15–18) |
| **19** | Rilis 2 | **Release Preparation** |
| — | | **🚀 Rilis 2 ship — akhir Minggu 19** |

**Catatan (2026-08-03)**: Rilis 1 dikembalikan ke **Minggu 7** (bukan Minggu 6 di versi sebelumnya) — 1 minggu buffer ditambahkan kembali ke fase QA end-to-end sebagai margin keamanan, keputusan sadar untuk mengurangi risiko jadwal terlalu ketat (lihat Risiko #7). Hasilnya persis sama dengan tanggal ship Man Power *standalone* di Skenario A (Minggu 7, yang cuma bawa 1 fitur dengan tim 4 orang) — trade-off "Man Power mundur" dari Skenario B/C tetap hilang (tidak mundur), meski sekarang tidak lebih cepat juga. Rilis 2 (scope awal) tidak diberi buffer tambahan, hanya bergeser +1 minggu mengikuti mundurnya Rilis 1 (mulai Minggu 8, bukan Minggu 7).

**Catatan (2026-08-13, revisi pertama)**: Rilis 2 diperluas mencakup My Work & eMAR (lihat bagian "Dasar Perhitungan" untuk breakdown SP lengkap). Estimasi awal: durasi dev+QA naik dari 4 → 10 minggu (ship Minggu 12 → Minggu 18).

**Catatan (2026-08-13, revisi kedua — capacity check)**: Estimasi revisi pertama menggambar bar Gantt per-kategori tanpa cross-check jumlah thread konkuren terhadap headcount riil — hasilnya di Minggu 8–10 ada sampai 4 thread BE/FE "paralel" sekaligus, padahal cuma ada 3 BE/2 FE. Setelah dijadwal ulang mengikuti kapasitas nyata (lihat tabel alokasi per-orang di bagian "Dasar Perhitungan"), BE & FE baru benar-benar selesai ~Minggu 15 (bukan 13–14), QA end-to-end mundur ke Minggu 15–18, ship bergeser dari Minggu 18 → **Minggu 19**. Total SP tidak berubah (161 SP) — murni koreksi timing.

---

## Dasar Perhitungan

**Rilis 1** (43 SP BE / 19 SP FE / 17 SP QA — tabel gabungan lengkap & breakdown per task ada di Gantt chart artifact di atas):
- BE (3 orang): Inspection & Additional Order, Order Approval, Master Data selesai ~Minggu 2; Digiplan + Integrasi `PoolingMOItem` (bagian terbesar, 25+6 SP) selesai ~Minggu 3
- FE (2 orang): mayoritas kerjaan selesai ~Minggu 2–3, beriringan dengan BE
- QA (2 orang) **mulai bertahap, bukan nunggu 100% dev selesai**:
  - Minggu 2: functional testing modul yang sudah code-complete (Inspection, Order Approval, Master Data) — ~5 SP
  - Minggu 3–6: testing end-to-end (baru bisa jalan setelah Digiplan siap) — ~12 SP sisanya, **+1 minggu buffer** ditambahkan di sini (kerja sebenarnya ~3 minggu, dibulatkan jadi 4 minggu kalender sebagai margin keamanan)
- Dev+QA: **6 minggu**, Release Prep: 1 minggu → **ship Minggu 7**

**Rilis 2 — scope awal, Maintenance Activity Type** (28 SP BE / 9 SP FE / 8 SP QA — tabel lengkap = Rilis 3 [Skenario A](squad-baru-release-timeline.md)):
- BE/FE (3+2 orang): Master Data + Inspection & Additional Order selesai ~Minggu 9; SAP Sync + Order Approval (`ReferenceTransactionId`) selesai ~Minggu 10
- QA (2 orang) mulai bertahap, tanpa buffer tambahan:
  - Minggu 9: testing modul awal (Master Data, Inspection & Additional Order) — ~2 SP
  - Minggu 10–11: testing end-to-end create→approve→SAP sync (baru bisa jalan setelah SAP Sync + Order Approval siap) — ~6 SP sisanya
- Dev+QA: 4 minggu, Release Prep: 1 minggu → ship Minggu 12 *(angka scope-awal ini sudah digantikan oleh revisi gabungan di bawah — dipertahankan sebagai basis perbandingan)*

---

### Revisi Scope Rilis 2 (2026-08-13) — Tambahan My Work & eMAR

My Work & eMAR (lihat [my-work.md](../my-work-and-emar/my-work.md), [mechanic-activity-report.md](../my-work-and-emar/mechanic-activity-report.md), [mechanic-productivity-management.md](../my-work-and-emar/mechanic-productivity-management.md)) ditambahkan ke Rilis 2, ship bersamaan dengan Maintenance Activity Type. Estimasi di bawah **confidence-nya lebih rendah** dari estimasi Maintenance Activity Type — tidak ada reference class Jira (fitur belum pernah dibangun sama sekali), dan beberapa keputusan desain masih terbuka saat estimasi ini dibuat (lihat catatan di bawah tabel).

**My Work — 27 SP BE / 18 SP FE:**

| Item | Role | SP |
|---|---|---|
| `UserActivityLog` schema + migration (aktivitas manual) | BE | 3 |
| API unified feed `GET /my-work` (gabung `TaskPersonalized`/`TaskPersonalizedLog` + `UserActivityLog`) | BE | 5 |
| API CRUD manual activity | BE | 3 |
| API confirm actual start/done | BE | 2 |
| Fit to Work — reuse `FormSubmission` + gating-check endpoint | BE | 2 |
| Unit/WorkOrder search endpoint (asumsi belum ada reuse) | BE | 3 |
| Auto-match engine (event listener Inspection/Form Submission) | BE | 8 |
| Permission + integrasi Homepage | BE | 1 |
| Home hari ini + navigasi tanggal | FE | 4 |
| Detail assignment | FE | 2 |
| Form tambah non-maintenance | FE | 2 |
| Form tambah maintenance ad-hoc + unit picker | FE | 3 |
| Edit/delete manual | FE | 1 |
| Layar Fit to Work + blocked state | FE | 2 |
| Konfirmasi actual start/done | FE | 1 |
| Prompt auto-match | FE | 2 |
| Empty state + blocking state (no connection) | FE | 1 |

**eMAR — 20 SP BE / 20 SP FE:**

| Item | Role | SP |
|---|---|---|
| Entity report envelope (`McActivityReport`: Status/Period/audit) + migration | BE | 3 |
| API Submit (lock entries, hitung summary, notify) | BE | 5 |
| API Approve/Reject (comment, notify) | BE | 2 |
| Baseline hours config — tabel + CRUD API | BE | 2 |
| Integrasi DWS (`dplan.Dws`) — gap-detection + denominator Utilization | BE | 5 |
| API approver queue (pending reports) | BE | 2 |
| API riwayat report (periode lampau) | BE | 1 |
| Mobile — list bulanan | FE | 3 |
| Mobile — day detail (add/edit/delete manual) | FE | 3 |
| Mobile — ganti periode | FE | 2 |
| Mobile — riwayat report | FE | 2 |
| Mobile — state rejected + edit-resubmit | FE | 2 |
| Mobile — submit confirmation | FE | 1 |
| Web — approver detail + approve/reject | FE | 3 |
| Web — approver inbox/queue | FE | 2 |
| Web — admin baseline hours config | FE | 2 |

**QA (20 SP baru) & Dashboard (8 SP baru):**

| Item | Role | SP |
|---|---|---|
| Testing My Work — self-capture, fit to work, manual entry, auto-match | QA | 8 |
| Testing eMAR — submit→approve→reject end-to-end (mobile+web) | QA | 5 |
| Testing integrasi DWS + kalkulasi Utilization Rate | QA | 3 |
| Testing Mechanic Productivity Dashboard (Power BI) | QA | 2 |
| Regresi ke Maintenance Activity Type (rilis bersamaan) | QA | 2 |
| Mechanic Productivity Dashboard (Site Manager & HO, drilldown) — Power BI, report baru | DE/DA | 8 |

Mandays pakai rasio ×1.17 yang sama dengan estimasi lain di dokumen ini.

**Di luar 113 SP di atas** (belum diestimasi / di luar scope Rilis 2 ini): push-assignment Foreman→Mechanic (My Work saat ini pull/self-assign — lihat gap di [my-work.md](../my-work-and-emar/my-work.md)), split Man Power/Man Hours per-individu mechanic (tergantung enhancement lain), notification service (dependency platform belum dikonfirmasi ada), export PDF/Excel eMAR, GPS/location My Work. Kalau salah satu ini masuk scope belakangan, 161 SP di bawah perlu direvisi naik.

**Rilis 2 — Gabungan (revisi 2026-08-13): 75 SP BE / 47 SP FE / 28 SP QA / 11 SP DE-DA = 161 SP total**, mulai Minggu 8 (langsung setelah Rilis 1 ship):
- QA (2 orang, 28 SP: 8 existing + 20 baru) mulai bertahap **dari Minggu 8**:
  - Minggu 8–13: test case design/test plan + functional testing modul code-complete duluan (Master Data/Inspection Activity Type existing, ditambah eMAR mobile UI & layar My Work non-integrasi begitu siap — FE-nya tetap selesai on-time meski BE My Work mundur, lihat tabel alokasi di bawah) — ~10 SP
  - Minggu 15–18: testing end-to-end — create→approve→SAP sync (Activity Type) **+** self-capture→confirm→auto-match (My Work) **+** submit→approve→reject (eMAR) **+** validasi Utilization Rate via DWS — ~18 SP sisanya. Mulai Minggu 15 (bukan 14), menunggu BE My Work & eMAR FE benar-benar selesai
- Dev+QA: **11 minggu**, Release Prep: 1 minggu → **ship Minggu 19**

### Revisi Capacity Check (2026-08-13, revisi kedua)

Estimasi BE/FE di atas awalnya digambar per-kategori (Master Data, Inspection, My Work, eMAR, dst.) dengan tanggal mulai/selesai dihitung independen dari SP÷velocity masing-masing kategori — **tanpa cross-check berapa kategori yang berjalan bersamaan pada minggu yang sama terhadap headcount riil**. Hasilnya: di Minggu 8–10 ada sampai **4 thread BE dan 4 thread FE "paralel"**, padahal squad cuma py 3 BE / 2 FE. Tidak bisa dieksekusi seperti itu.

Jadwal ulang di bawah mengasumsikan **reallocation aktif** — begitu satu thread selesai, orangnya pindah bantu thread lain yang masih jalan (bukan silo tetap 1 orang 1 fitur untuk seluruh Rilis 2):

**Alokasi BE (3 orang):**

| Lane | Thread | SP | Minggu | Catatan |
|---|---|---|---|---|
| BE-1 | Activity Type (Master Data 7 + Inspection 7 + SAP Sync 9 + Order Approval 5) | 28 | 8–10 | Dibantu ~2 BE lain sebentar di Minggu 8–9 (Master Data+Inspection) supaya tetap selesai secepat rencana awal |
| BE-2 | eMAR (Report envelope, Submit/Approve API, baseline config, DWS, approver queue, riwayat) | 20 | 9–14 | Mulai Minggu 9 — Activity Type belum butuh 3 BE penuh saat itu, 1 BE bebas |
| BE-3 | My Work (schema, feed API, CRUD, confirm, Fit to Work, unit/WO search, permission, auto-match) | 27 | **11–15** | **Baru mulai penuh Minggu 11** — menunggu Activity Type (selesai ~Mgg 10) melepas 2 BE untuk bantu; auto-match (8 SP) juga butuh Inspection Activity Type stabil dulu (selesai ~Mgg 9, jadi bukan bottleneck tambahan). Dengan bantuan BE-1/BE-2 begitu bebas, selesai ~Minggu 15, bukan solo ~Minggu 16 |

Maks 3 BE konkuren di setiap minggu ✓. **BE selesai ~Minggu 15** (naik dari estimasi awal Minggu 14).

**Alokasi FE (2 orang):**

| Lane | Thread | SP | Minggu | Catatan |
|---|---|---|---|---|
| FE-1 | Activity Type FE (9) → lanjut eMAR FE (20) | 9 + 20 | 8–9, lalu 9–15 | 1 lane berkelanjutan (bukan 2 orang beda) — Activity Type FE kecil & cepat, begitu selesai langsung lanjut eMAR FE |
| FE-2 | My Work FE (Home, navigasi tanggal, detail assignment, form manual, Fit to Work, dst.) | 18 | 8–13 | Dedicated solo dari Minggu 8 |

Maks 2 FE konkuren ✓. **FE selesai ~Minggu 15** (eMAR FE, naik dari estimasi awal Minggu 13) — meski My Work FE sendiri tetap selesai ~Minggu 13 seperti rencana awal (tidak terdampak, karena FE-2 dedicated sejak awal).

**Dampak ke jadwal**: karena BE & FE baru benar-benar selesai ~Minggu 15 (bukan 13–14), QA end-to-end mundur ke **Minggu 15–18** (dari rencana awal Minggu 14–17), Release Prep mundur ke **Minggu 19**, ship **Minggu 19** (dari estimasi awal Minggu 18). **Total SP tidak berubah (161 SP)** — murni koreksi timing supaya konsisten dengan kapasitas riil.

## Kenapa 3 BE — Bukan Cukup Nambah FE/QA Saja

Dari eksplorasi Skenario C: menambah FE dan QA saja (tanpa nambah BE) tidak cukup untuk kompresi signifikan **selama freeze code diberlakukan** (tidak ada cicil antar rilis) — karena BE (2 orang) selalu jadi *critical path* di tiap rilis, FE/QA ekstra cuma menunggu BE selesai duluan. BE harus ikut ditambah supaya benar-benar berhenti jadi bottleneck di kedua rilis.

## Kenapa ~12 → 19 Minggu — Perjalanan Angkanya

Estimasi awal skenario final (13 minggu) mengasumsikan QA baru mulai setelah **100% dev rilis selesai** ("big bang" testing). Realistisnya, task-task dalam satu rilis tidak semua selesai di hari yang sama — beberapa modul (Inspection, Order Approval, Master Data) code-complete lebih dulu daripada modul terbesar (Digiplan/SAP Sync). QA tidak perlu menunggu modul terakhir selesai untuk mulai testing modul yang sudah jadi — testing bertahap (shift-left) ini awalnya memangkas ~1 minggu di tiap rilis (13→11 minggu), tanpa perlu freeze code dilonggarkan dan tanpa nambah orang lagi.

**Revisi 2026-08-03**: setelah dipikir ulang, 1 minggu buffer dikembalikan **khusus ke Rilis 1** — QA end-to-end tetap mulai bertahap (shift-left, mulai Minggu 2), tapi durasi kalendernya dilonggarkan lagi supaya Rilis 1 ship di Minggu 7 (bukan Minggu 6), sama seperti tanggal ship Man Power standalone di Skenario A. Rilis 2 **tidak** diberi buffer tambahan — tetap dev-QA 4 minggu penuh dengan shift-left, cuma bergeser mengikuti mundurnya Rilis 1. Hasilnya: **~12 minggu total** (13→11→12), tetap hemat 7 minggu dari Skenario A, dengan Rilis 1 punya margin keamanan lebih besar dibanding Rilis 2.

**Revisi 2026-08-13 (pertama)**: My Work & eMAR ditambahkan ke Rilis 2 (161 SP total gabungan). Estimasi awal: dev+QA Rilis 2 naik dari 4 → 10 minggu, ship Minggu 12 → **Minggu 18**.

**Revisi 2026-08-13 (kedua — capacity check)**: estimasi revisi pertama menggambar bar per-kategori tanpa cross-check jumlah thread konkuren terhadap headcount riil (3 BE, 2 FE) — Minggu 8–10 sempat menuntut sampai 4 thread BE/FE sekaligus. Setelah dijadwal ulang mengikuti kapasitas riil (tabel alokasi per-orang di "Dasar Perhitungan"), BE & FE baru benar-benar selesai ~Minggu 15 (bukan 13–14), QA end-to-end mundur ke Minggu 15–18, ship mundur dari Minggu 18 → **Minggu 19**. Total SP tidak berubah (161 SP) — murni koreksi timing. Hasil akhir: **~19 minggu total**, kebetulan sama persis dengan Skenario A.

---

## Risiko & Catatan Terbuka

1. **Headcount naik 75% (4→7 orang)** — keputusan komersial, biaya squad naik signifikan dari baseline 4 orang. Perlu persetujuan budget terpisah dari komitmen awal (8 sprint, tim 4 orang).
2. **Velocity ramp-up (0.81→0.85 SP/hari/orang) belum tervalidasi untuk kohort 7 orang baru sekaligus.** Angka ini dikalibrasi untuk skenario 4 orang menerima Knowledge Transfer dari tim BUMA ID veteran. Menaikkan jadi 7 orang berarti bandwidth KT tim veteran juga perlu di-scale — **risiko ini diketahui dan sengaja dikesampingkan** dalam pemodelan ini (keputusan 2026-08-03), bukan tervalidasi tidak berdampak.
3. **Hiring lead time** untuk net tambahan +1 BE, +1 FE, +1 QA (di luar 4 orang existing) **di luar estimasi 19 minggu ini** — waktu rekrutmen/interview/notice period akan mengulur tanggal mulai Sprint 1.
4. **Risiko koordinasi/merge-conflict lebih tinggi** di 4 titik shared-screen Rilis 1 (eMOL carry-forward, `PoolingMOItem`, Digiplan grid/export, MO Backlog JOIN) karena sekarang dikerjakan 3 BE, bukan 2 — perlu pembagian task/branch yang jelas.
5. **Dependency yang tetap berlaku**: Master Data Area (Equipment Mapping enhance) tetap harus selesai lebih dulu sebelum kolom Area di Digiplan bisa dikembangkan penuh (sequencing internal Rilis 1, bukan lagi soal urutan rilis).
6. Item lain yang masih berlaku dari Skenario A (belum berubah): mekanisme deteksi `ReferenceTransactionId` di Rilis 2 belum bisa diestimasi penuh (lihat Risiko Skenario A #2); mapping BAPI ke SAP tetap di luar seluruh estimasi ini (dikoordinasikan client, PIC Faiza).
7. **Jadwal Rilis 2 tetap lebih ketat dari Rilis 1** — buffer 1 minggu (2026-08-03) cuma ditambahkan ke Rilis 1. Rilis 2 pakai estimasi shift-left + capacity check (2026-08-13) tanpa margin ekstra tambahan di luar itu; kalau reallocation antar-thread (Risiko #9) atau shift-left QA sulit dieksekusi rapi (misal environment testing belum siap sebelum dev selesai penuh), realistanya jadwal Rilis 2 bisa mundur lagi dari Minggu 19 (total >19 minggu).
8. **Risiko retest** kalau BE menyentuh ulang kode shared-screen (eMOL carry-forward, `PoolingMOItem`) **setelah** QA sudah mulai testing modul terkait duluan (Minggu 2 di Rilis 1, Minggu 9 di Rilis 2) — retest tambahan akibat perubahan itu belum terhitung eksplisit di estimasi ini.
9. **(Baru, 2026-08-13, dikuantifikasi di revisi kedua) Tiga thread fitur bersamaan dengan hanya 3 BE.** Rilis 2 sekarang menjalankan Maintenance Activity Type + My Work + eMAR sekaligus. Jadwal yang tercantum di dokumen ini **sudah mengasumsikan reallocation aktif** (orang pindah bantu thread lain begitu thread-nya sendiri selesai — lihat tabel alokasi per-orang di "Dasar Perhitungan"), bukan silo 1 orang per fitur. Kalau reallocation ini tidak dikelola rapi di eksekusi riil (mis. karena hand-off/komunikasi antar-thread lambat), jadwal bisa mundur lagi dari Minggu 19.
10. **(Baru, 2026-08-13) Confidence estimasi My Work & eMAR (113 SP) lebih rendah** dari Maintenance Activity Type. Maintenance Activity Type tervalidasi reference class Jira riil ([maintenance-activity-type-effort-summary.md](inspection-order/maintenance-activity-type-effort-summary.md)); My Work & eMAR murni estimasi dari desain di atas kertas, belum ada kode/mockup backend sama sekali. Beberapa keputusan yang bisa geser SP signifikan kalau berubah: push vs pull assignment dari Digiplan, arsitektur Management Dashboard (Power BI vs halaman app baru dengan RBAC), mekanisme reopen-editing setelah Reject di eMAR.
11. **(Baru, 2026-08-13) Rilis 1 punya gap serupa (kecil) — bukan buatan sesi ini.** Kroscek kapasitas yang sama, diterapkan ke Rilis 1 (bagian dari rencana asli 3 Agustus 2026, bukan revisi baru): BE 43 SP diklaim selesai Minggu 3, tapi kapasitas riil 3 BE di ramp-up (0.81 SP/hari) untuk Minggu 1–3 cuma ~36.5 SP — realistanya BE selesai lebih dekat ke Minggu 4. Beda dengan Rilis 2: gap-nya kecil (~1 minggu) dan Rilis 1 sudah punya buffer 3 minggu QA sebelum ship (Minggu 4→7) yang kemungkinan besar menyerap slip ini. **Ship Minggu 7 tetap dipertahankan, tidak direvisi** — dicatat di sini untuk transparansi metodologi, bukan karena mengubah kesimpulan Rilis 1.

---

## Referensi

- [squad-baru-release-timeline.md](squad-baru-release-timeline.md) — Skenario A (4 orang, 3 rilis sequential, 19 minggu) — **tidak mencakup My Work/eMAR**, tidak direcompute untuk scope baru
- Gantt chart interaktif (final, direvisi 2026-08-13): [claude.ai/code/artifact/15a73a97-b0f1-431a-8c67-6fb5966c2204](https://claude.ai/code/artifact/15a73a97-b0f1-431a-8c67-6fb5966c2204)
- [effort-recap-3-proposals.html](effort-recap-3-proposals.html)
- [man-power-duration-enhancement-proposal.html](man-power-duration-enhancement-proposal.html)
- [area-of-unit-enhancement-proposal.html](area-of-unit-enhancement-proposal.html)
- [inspection-order/maintenance-activity-type-effort-proposal.html](inspection-order/maintenance-activity-type-effort-proposal.html)
- [../my-work-and-emar/my-work.md](../my-work-and-emar/my-work.md) — requirement, gap analisis, dan kebutuhan UI/BE My Work
- [../my-work-and-emar/mechanic-activity-report.md](../my-work-and-emar/mechanic-activity-report.md) — requirement & kebutuhan UI/BE eMAR (mechanic + approver)
- [../my-work-and-emar/mechanic-productivity-management.md](../my-work-and-emar/mechanic-productivity-management.md) — requirement & kebutuhan UI/BE eMAR (management dashboard)
