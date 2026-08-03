# Timeline & Skenario Delivery — FINAL (Squad Diperkuat, 2 Rilis)

*Last updated: 2026-08-03*

---

Dokumen ini adalah **skenario final** hasil diskusi bertahap dari [squad-baru-release-timeline.md](squad-baru-release-timeline.md) (Skenario A — 4 orang, 3 rilis sequential). Dua skenario antara sempat dibuat sebagai file terpisah selama diskusi — Skenario B (gabung Rilis 1+2, squad tetap 4 orang) dan Skenario C (eksplorasi opsi headcount 5/6 orang) — keduanya sudah dihapus setelah keputusan final ini diambil (sudah digantikan, bukan referensi aktif lagi).

**Gantt chart interaktif**: [claude.ai/code/artifact/15a73a97-b0f1-431a-8c67-6fb5966c2204](https://claude.ai/code/artifact/15a73a97-b0f1-431a-8c67-6fb5966c2204) — 2 panel Rilis 1 & Rilis 2, hover/focus per task untuk detail, toggle tabel breakdown SP.

**Keputusan final (2026-08-03)**:
- **Squad diperkuat dari 4 → 7 orang**: 2→**3 Backend**, 1→**2 Frontend Fullstack** (Web+Mobile, tugas dibagi bebas — bukan dipisah per platform), 1→**2 QA**.
- **2 rilis** (bukan 3): **Rilis 1** = Man Power, Duration & Man Hours + Area of Unit, Component & Sub Component (digabung). **Rilis 2** = Maintenance Activity Type & Integrasi Inspection→Order (scope sama persis dengan Rilis 3 Skenario A, tidak berubah).
- **Freeze code penuh antar rilis** — Rilis 2 tidak dimulai sebelum Rilis 1 ship (tidak ada BE yang nyicil kerjaan Rilis 2 selama Rilis 1 masih berjalan).

---

## Ringkasan Skenario

| | |
|---|---|
| **Squad** | 7 orang: **3 Backend, 2 Frontend Fullstack (Web+Mobile), 2 QA** |
| **Velocity** | Sama seperti skenario sebelumnya: ramp-up 0.81 SP/hari/orang (Sprint 1–2, Minggu 1–4), full speed 0.85 SP/hari/orang (Sprint 3 dst, Minggu 5+) |
| **Antar-rilis** | Freeze code penuh — tidak ada overlap/cicil kerjaan Rilis 2 selama Rilis 1 berjalan |
| **Release Preparation** | 1 minggu per rilis (2×1 minggu = 2 minggu total) |
| **QA** | Mulai bertahap (shift-left) — testing modul yang sudah selesai duluan, bukan nunggu 100% dev rilis selesai. Rilis 1 pakai +1 minggu buffer QA (keputusan 2026-08-03); Rilis 2 tetap tanpa buffer tambahan |
| **Total estimasi** | **~12 minggu** (turun dari 19 minggu Skenario A) — hemat **~7 minggu (~3.5 sprint)** |

---

## Master Timeline (~12 Minggu)

| Minggu | Rilis | Fase |
|---|---|---|
| 1–6 | Rilis 1 (Man Power + Area) | Dev + QA (QA mulai bertahap dari Minggu 2, +1 minggu buffer) |
| **7** | Rilis 1 | **Release Preparation** |
| — | | **🚀 Rilis 1 ship — akhir Minggu 7** |
| 8–11 | Rilis 2 (Maintenance Activity Type) | Dev + QA (QA mulai bertahap dari Minggu 9) |
| **12** | Rilis 2 | **Release Preparation** |
| — | | **🚀 Rilis 2 ship — akhir Minggu 12** |

**Catatan (2026-08-03)**: Rilis 1 dikembalikan ke **Minggu 7** (bukan Minggu 6 di versi sebelumnya) — 1 minggu buffer ditambahkan kembali ke fase QA end-to-end sebagai margin keamanan, keputusan sadar untuk mengurangi risiko jadwal terlalu ketat (lihat Risiko #7). Hasilnya persis sama dengan tanggal ship Man Power *standalone* di Skenario A (Minggu 7, yang cuma bawa 1 fitur dengan tim 4 orang) — trade-off "Man Power mundur" dari Skenario B/C tetap hilang (tidak mundur), meski sekarang tidak lebih cepat juga. Rilis 2 tidak diberi buffer tambahan, hanya bergeser +1 minggu mengikuti mundurnya Rilis 1 (mulai Minggu 8, bukan Minggu 7).

---

## Dasar Perhitungan

**Rilis 1** (43 SP BE / 19 SP FE / 17 SP QA — tabel gabungan lengkap & breakdown per task ada di Gantt chart artifact di atas):
- BE (3 orang): Inspection & Additional Order, Order Approval, Master Data selesai ~Minggu 2; Digiplan + Integrasi `PoolingMOItem` (bagian terbesar, 25+6 SP) selesai ~Minggu 3
- FE (2 orang): mayoritas kerjaan selesai ~Minggu 2–3, beriringan dengan BE
- QA (2 orang) **mulai bertahap, bukan nunggu 100% dev selesai**:
  - Minggu 2: functional testing modul yang sudah code-complete (Inspection, Order Approval, Master Data) — ~5 SP
  - Minggu 3–6: testing end-to-end (baru bisa jalan setelah Digiplan siap) — ~12 SP sisanya, **+1 minggu buffer** ditambahkan di sini (kerja sebenarnya ~3 minggu, dibulatkan jadi 4 minggu kalender sebagai margin keamanan)
- Dev+QA: **6 minggu**, Release Prep: 1 minggu → **ship Minggu 7**

**Rilis 2** (28 SP BE / 9 SP FE / 8 SP QA — tabel lengkap = Rilis 3 [Skenario A](squad-baru-release-timeline.md)), mulai Minggu 8 (langsung setelah Rilis 1 ship):
- BE/FE (3+2 orang): Master Data + Inspection & Additional Order selesai ~Minggu 9; SAP Sync + Order Approval (`ReferenceTransactionId`) selesai ~Minggu 10
- QA (2 orang) mulai bertahap, **tanpa buffer tambahan**:
  - Minggu 9: testing modul awal (Master Data, Inspection & Additional Order) — ~2 SP
  - Minggu 10–11: testing end-to-end create→approve→SAP sync (baru bisa jalan setelah SAP Sync + Order Approval siap) — ~6 SP sisanya
- Dev+QA: **4 minggu**, Release Prep: 1 minggu → **ship Minggu 12**

## Kenapa 3 BE — Bukan Cukup Nambah FE/QA Saja

Dari eksplorasi Skenario C: menambah FE dan QA saja (tanpa nambah BE) tidak cukup untuk kompresi signifikan **selama freeze code diberlakukan** (tidak ada cicil antar rilis) — karena BE (2 orang) selalu jadi *critical path* di tiap rilis, FE/QA ekstra cuma menunggu BE selesai duluan. BE harus ikut ditambah supaya benar-benar berhenti jadi bottleneck di kedua rilis.

## Kenapa ~12 Minggu — Perjalanan Angkanya

Estimasi awal skenario final (13 minggu) mengasumsikan QA baru mulai setelah **100% dev rilis selesai** ("big bang" testing). Realistisnya, task-task dalam satu rilis tidak semua selesai di hari yang sama — beberapa modul (Inspection, Order Approval, Master Data) code-complete lebih dulu daripada modul terbesar (Digiplan/SAP Sync). QA tidak perlu menunggu modul terakhir selesai untuk mulai testing modul yang sudah jadi — testing bertahap (shift-left) ini awalnya memangkas ~1 minggu di tiap rilis (13→11 minggu), tanpa perlu freeze code dilonggarkan dan tanpa nambah orang lagi.

**Revisi 2026-08-03**: setelah dipikir ulang, 1 minggu buffer dikembalikan **khusus ke Rilis 1** — QA end-to-end tetap mulai bertahap (shift-left, mulai Minggu 2), tapi durasi kalendernya dilonggarkan lagi supaya Rilis 1 ship di Minggu 7 (bukan Minggu 6), sama seperti tanggal ship Man Power standalone di Skenario A. Rilis 2 **tidak** diberi buffer tambahan — tetap dev-QA 4 minggu penuh dengan shift-left, cuma bergeser mengikuti mundurnya Rilis 1. Hasilnya: **~12 minggu total** (13→11→12), tetap hemat 7 minggu dari Skenario A, dengan Rilis 1 punya margin keamanan lebih besar dibanding Rilis 2.

---

## Risiko & Catatan Terbuka

1. **Headcount naik 75% (4→7 orang)** — keputusan komersial, biaya squad naik signifikan dari baseline 4 orang. Perlu persetujuan budget terpisah dari komitmen awal (8 sprint, tim 4 orang).
2. **Velocity ramp-up (0.81→0.85 SP/hari/orang) belum tervalidasi untuk kohort 7 orang baru sekaligus.** Angka ini dikalibrasi untuk skenario 4 orang menerima Knowledge Transfer dari tim BUMA ID veteran. Menaikkan jadi 7 orang berarti bandwidth KT tim veteran juga perlu di-scale — **risiko ini diketahui dan sengaja dikesampingkan** dalam pemodelan ini (keputusan 2026-08-03), bukan tervalidasi tidak berdampak.
3. **Hiring lead time** untuk net tambahan +1 BE, +1 FE, +1 QA (di luar 4 orang existing) **di luar estimasi 12 minggu ini** — waktu rekrutmen/interview/notice period akan mengulur tanggal mulai Sprint 1.
4. **Risiko koordinasi/merge-conflict lebih tinggi** di 4 titik shared-screen Rilis 1 (eMOL carry-forward, `PoolingMOItem`, Digiplan grid/export, MO Backlog JOIN) karena sekarang dikerjakan 3 BE, bukan 2 — perlu pembagian task/branch yang jelas.
5. **Dependency yang tetap berlaku**: Master Data Area (Equipment Mapping enhance) tetap harus selesai lebih dulu sebelum kolom Area di Digiplan bisa dikembangkan penuh (sequencing internal Rilis 1, bukan lagi soal urutan rilis).
6. Item lain yang masih berlaku dari Skenario A (belum berubah): mekanisme deteksi `ReferenceTransactionId` di Rilis 2 belum bisa diestimasi penuh (lihat Risiko Skenario A #2); mapping BAPI ke SAP tetap di luar seluruh estimasi ini (dikoordinasikan client, PIC Faiza).
7. **Jadwal Rilis 2 tetap lebih ketat dari Rilis 1** — buffer 1 minggu (2026-08-03) cuma ditambahkan ke Rilis 1. Rilis 2 masih pakai estimasi shift-left tanpa margin ekstra (dev-QA 4 minggu penuh); kalau shift-left QA di Rilis 2 sulit dieksekusi rapi (misal environment testing belum siap sebelum dev selesai penuh), realistanya jadwal Rilis 2 bisa mundur ~1 minggu lagi (total ~13 minggu).
8. **Risiko retest** kalau BE menyentuh ulang kode shared-screen (eMOL carry-forward, `PoolingMOItem`) **setelah** QA sudah mulai testing modul terkait duluan (Minggu 2 di Rilis 1, Minggu 9 di Rilis 2) — retest tambahan akibat perubahan itu belum terhitung eksplisit di estimasi ini.

---

## Referensi

- [squad-baru-release-timeline.md](squad-baru-release-timeline.md) — Skenario A (4 orang, 3 rilis sequential, 19 minggu)
- Gantt chart interaktif (final): [claude.ai/code/artifact/15a73a97-b0f1-431a-8c67-6fb5966c2204](https://claude.ai/code/artifact/15a73a97-b0f1-431a-8c67-6fb5966c2204)
- [effort-recap-3-proposals.html](effort-recap-3-proposals.html)
- [man-power-duration-enhancement-proposal.html](man-power-duration-enhancement-proposal.html)
- [area-of-unit-enhancement-proposal.html](area-of-unit-enhancement-proposal.html)
- [inspection-order/maintenance-activity-type-effort-proposal.html](inspection-order/maintenance-activity-type-effort-proposal.html)
