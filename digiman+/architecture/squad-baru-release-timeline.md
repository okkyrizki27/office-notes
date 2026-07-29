# Timeline & Skenario Delivery — Squad Baru (3 Proposal Digiman+)

*Last updated: 2026-07-29*

---

Dokumen ini merinci skenario delivery untuk **squad baru** yang mengerjakan ketiga proposal enhancement Digiman+ — [Man Power, Duration & Man Hours](man-power-duration-enhancement-proposal.html), [Area of Unit, Component & Sub Component](area-of-unit-enhancement-proposal.html), dan [Maintenance Activity Type & Integrasi Inspection→Order](inspection-order/maintenance-activity-type-effort-proposal.html) — setelah disepakati komitmen komersial **8 sprint** dengan squad baru (lihat [effort-recap-3-proposals.html](effort-recap-3-proposals.html) untuk estimasi awal per-proposal). Dokumen ini **turunan perencanaan**, bukan revisi proposal aslinya — angka SP tetap merujuk ke ketiga proposal sumber.

## Ringkasan Skenario

| | |
|---|---|
| **Komitmen komersial** | 8 sprint (16 minggu) kerja dev+QA, ditambah 1 minggu Release Preparation per rilis (3×1 minggu) = **19 minggu total** |
| **Squad** | 4 orang, tetap (tidak ada penambahan headcount): **2 Backend, 1 Frontend Fullstack (Web+Mobile), 1 QA** |
| **Velocity** | Sprint 1–2 (ramp-up, dengan Knowledge Transfer dari tim BUMA ID): 0.81 SP/hari/orang. Sprint 3 dst (full speed, setara tim BUMA ID veteran): 0.85 SP/hari/orang |
| **Urutan prioritas rilis** | Disepakati bersama stakeholder: **1) Man Power & Man Hours → 2) Area of Unit → 3) Maintenance Activity Type** |
| **Release Preparation** | 1 minggu per rilis: deployment plan, release notes, rollback plan (**tanpa UAT sign-off**) |

## Kenapa 2 Backend

Dari analisis awal (1 BE saja per skenario "Tim Baru" di tiap proposal), Backend konsisten jadi bottleneck tunggal — 57–65% dari total SP tiap proposal. Simulasi kapasitas dengan 1 BE untuk ketiga proposal sekaligus (bahkan dengan opsi Man Power "Tanpa" rollup penuh, dan defer item `ReferenceTransactionId`) hanya pas-pasan di ~9 sprint, melebihi budget 8 sprint.

Dengan **2 BE**, kapasitas pool BE (2 orang × ~67 SP/8 sprint = ~134 SP) jauh melebihi kebutuhan total (~65 SP dev BE di ketiga rilis, direvisi 30 Jul 2026 — koreksi role split Rilis 2 + penghapusan scope SAP Sync di Rilis 1 & 2) — cukup longgar untuk:
- Mengembalikan item `ReferenceTransactionId` (5 SP) yang sempat direncanakan di-defer.
- Menyisakan buffer ~1 sprint sebagai **kontingensi** (bukan dialokasikan ke scope tambahan — keputusan 29 Jul 2026).

FE Fullstack dan QA (masing-masing 1 orang) tidak pernah jadi bottleneck di skenario manapun — kapasitas mereka jauh di atas kebutuhan (~25–27 SP vs ~67 SP kapasitas/8 sprint).

## Metodologi Estimasi

SP & mandays memakai metodologi yang sama dengan ketiga proposal sumber — kalibrasi Fibonacci `[1,2,3,5,8]` per komponen kerja, lihat detail di [effort-recap-3-proposals.html](effort-recap-3-proposals.html) dan proposal masing-masing. Yang berbeda di dokumen ini: skenario **squad baru 4 orang** (bukan tim BUMA ID existing), dan **velocity 2 fase** (ramp-up Sprint 1–2, full speed Sprint 3 dst) — bukan velocity konstan seperti asumsi awal di proposal.

---

## Master Timeline (19 Minggu)

| Minggu | Rilis | Fase |
|---|---|---|
| 1–6 | Rilis 1 | Dev + QA |
| **7** | Rilis 1 | **Release Preparation** |
| — | | **🚀 Rilis 1 ship — akhir Minggu 7** |
| 8–11 | Rilis 2 | Dev + QA |
| **12** | Rilis 2 | **Release Preparation** |
| — | | **🚀 Rilis 2 ship — akhir Minggu 12** |
| 13–18 | Rilis 3 | Dev + QA |
| **19** | Rilis 3 | **Release Preparation** |
| — | | **🚀 Rilis 3 ship — akhir Minggu 19** |

Alokasi minggu dev+QA proporsional ke beban BE tiap rilis (23/14/28 SP dari total 65 SP) terhadap budget 16 minggu — Rilis 1 & 2 kini punya buffer lebih longgar dari perkiraan awal setelah koreksi role split + penghapusan scope SAP Sync (30 Jul 2026); rentang minggu tiap rilis dipertahankan apa adanya (tidak dikompres lebih lanjut) sebagai kontingensi tambahan.

Alokasi BE: kedua BE all-hands di Rilis 1 (prioritas tertinggi). Setelah itu, BE tidak dikunci kaku 1 orang per rilis — begitu salah satu rilis (Area, lebih kecil) selesai duluan, BE yang lowong gabung membantu rilis berikutnya, bukan menganggu.

---

## Rilis 1 — Man Power, Man Hours (Minggu 1–7)

**Kategori | Task | Role | SP**

| Kategori | Task | Role | SP | Mandays |
|---|---|---|---|---|
| Inspection & Additional Order | Field Man Power (Inspection/Add. Inspection), Duration+Man Power (Additional Order) | BE | 2 | 2.5 |
| Inspection & Additional Order | Field Man Power/Duration UI (Inspection, Additional Order) | FE | 4 | 4.9 |
| Order Approval & Workflow | Edit eMOL carry-forward, validasi & edit Man Power/Duration di Approval | BE | 4 | 4.9 |
| Order Approval & Workflow | Edit Man Power/Duration UI di Order Approval | FE | 2 | 2.5 |
| Digiplan | Grid recalculate, Excel export/import, auto-recalculate struktur, assessment formula rollup — **termasuk** logic PM Shutdown & BD Corrective (assignment warning, `ManPowerVarianceReason`, 2 skenario mandatory), tidak ada baris SP terpisah untuk itu | BE | 17 | 21.0 |
| Digiplan | Guardrail Template Config UI, grid Man Hours read-only | FE | 3 | 3.7 |
| PM Shutdown & BD Corrective | Card visibility (UI) | FE | (dalam 9) | (dalam 11.1) |
| QA / Testing | Testing end-to-end + Digiplan + PM/BD | QA | 12 | 14.0 |
| Dashboard | Digiman Transaction Dashboard (D'Inspect/D'Order — Man Power/Duration/Man Hours) + Power BI | DE/DA (paralel) | 9.75 | 11.4 |

**Total BE: 23 SP / 28.4 mandays · FE: 9 SP / 11.1 mandays · QA: 12 SP / 14.0 mandays · DE/DA (paralel, di luar kapasitas squad): 9.75 SP / 11.4 mandays**

*Catatan rasio: baris BE & FE di Rilis 1 pakai **1/0.81 ≈ 1.235 mandays/SP** (bukan 1.17) — seluruh kerjaan BE+FE rilis ini selesai dalam periode ramp-up Sprint 1–2 (Minggu 1–4), belum masuk fase full speed. QA & Dashboard tetap 1.17 karena baru mulai di Minggu 4–6 (sudah full speed). Rilis 2 & 3 memakai 1.17 penuh — keduanya di luar periode ramp-up.*

*Catatan koreksi scope (30 Jul 2026): baris **SAP Sync** (`PoolingMOItem`/MO Backlog, 5.2 SP BE) dihapus dari rilis ini — per arahan user, SAP Sync hanya di-scope di Rilis 3 (Maintenance Activity Type). Lihat catatan #8 di Risiko & Catatan Terbuka soal implikasinya ke baris QA/Testing.*

**Scope note**: memakai opsi **"Tanpa" rollup** (parent Man Power/Man Hours dikosongkan dulu) — bukan logic penuh predecessor/serial/paralel. Opsi "Dengan" (+8 SP) di-defer, bisa disusulkan di rilis berikutnya.

**Benefit ke customer**: SPV bisa estimasi kebutuhan tenaga kerja (Man Power) sejak Order dibuat, Man Hours terhitung otomatis (`Duration × Man Power`) di Digiplan. Supervisor dapat visibility rencana-vs-aktual di eksekusi PM Shutdown/BD Corrective dengan audit trail kalau ada selisih.

---

## Rilis 2 — Area of Unit, Component & Sub Component (Minggu 8–12)

| Kategori | Task | Role | SP | Mandays |
|---|---|---|---|---|
| Master Data | Master data `Area` CRUD (UI maintain baru), enhance modal Equipment Mapping (`AreaCode` field) + Edit action baru | FE | 7 | 8.2 |
| Master Data | Data migration backfill `AreaCode` + permission code | BE | 3 | 3.5 |
| Inspection & Additional Order | Backend derive + snapshot `AreaCode`/`AreaName` — Inspection & Additional Order (dropdown Component/SubComponent sudah ada di kedua layar, tidak perlu dibangun UI baru) | BE | 2 | 2.3 |
| Order Approval & Workflow | Edit eMOL: carry-forward Component/SubComponent | BE | 1 | 1.2 |
| Digiplan | Grid UI: 3 dropdown cascading Area→Component→SubComponent | FE | 3 | 3.5 |
| Digiplan | `DPColumn` 3 kolom baru, auto-fill dari MO Backlog, Excel export/import+validasi | BE | 8 | 9.4 |
| QA / Testing | Testing end-to-end + Digiplan | QA | 7 | 8.2 |
| Dashboard | Digiman Transaction Dashboard (D'Inspect/D'Order — Area) + Power BI | DE/DA (paralel) | 3.25 | 3.8 |

**Total BE: 14 SP / 16.4 mandays · FE: 10 SP / 11.7 mandays · QA: 7 SP / 8.2 mandays · DE/DA (paralel): 3.25 SP / 3.8 mandays**

*Rasio mandays 1.17 (1/0.85, full speed) — Rilis 2 (Minggu 8–12) sepenuhnya di luar periode ramp-up Sprint 1–2.*

*Catatan koreksi (30 Jul 2026): (1) Master Data (10 SP) yang sebelumnya ter-duplikasi ke BE dan FE sekaligus sudah dipecah benar (FE 7, BE 3). (2) Grid UI dropdown cascading Digiplan (3 SP, jelas FE) dipindah dari BE. (3) "Edit eMOL carry-forward" disamakan ke **BE** (konsisten dengan baris yang sama di Rilis 1 Man Power — carry-forward adalah soal wiring data mengalir, bukan UI baru). (4) Baris **SAP Sync** (`PoolingMOItem`/MO Backlog, 2.8 SP BE) dihapus — per arahan user, SAP Sync hanya di-scope di Rilis 3.*

**Dependency**: Master Data Area (Equipment Mapping enhance) harus selesai lebih dulu sebelum kolom Area di Digiplan bisa dikembangkan penuh.

**Benefit ke customer**: Planner/SPV bisa mencatat & memfilter pekerjaan berdasarkan lokasi kerja (Area, Component, Sub Component) — konsisten di semua jalur order (Inspection maupun Additional Order), dan bisa dilihat per-Area di Digiplan & Dashboard.

---

## Rilis 3 — Maintenance Activity Type & Integrasi Inspection→Order (Minggu 13–19)

| Kategori | Task | Role | SP | Mandays |
|---|---|---|---|---|
| Master Data | `MaintenanceActivityType` schema/API + mapping M:N + permission + seeder | BE | 7 | 8.2 |
| Master Data | Master Data CRUD UI + Mapping UI | FE | 4 | 4.7 |
| Inspection & Additional Order | Extend submit Inspection (snapshot) + resolusi InspectorName | BE | 7 | 8.2 |
| Inspection & Additional Order | Additional Order Screen 1&2, Order Details — dropdown Activity Type | FE | 4 | 4.7 |
| Order Approval & Workflow | Order Approval — dropdown Activity Type | FE | 1 | 1.2 |
| Order Approval & Workflow | Standardisasi `ReferenceTransactionId` + dual-lookup 3 endpoint | BE | 5 | 5.9 |
| SAP Sync | `MechanicOrderList` kolom baru + extend `PoolingMOItem` | BE | 3 | 3.5 |
| SAP Sync | 4 endpoint cleanup (order-detail/assetnumber/approve/deprecate) | BE | 6 | 7.0 |
| QA / Testing | Testing end-to-end (create → approve → SAP sync + regresi) | QA | 8 | 9.4 |
| Dashboard | Digiman Transaction Dashboard (Maint. Act. Type) + Power BI | DE/DA (paralel) | 3 | 3.5 |

**Total BE: 28 SP / 32.8 mandays · FE: 9 SP / 10.5 mandays · QA: 8 SP / 9.4 mandays · DE/DA (paralel): 3 SP / 3.5 mandays**

*Rasio mandays 1.17 (1/0.85, full speed) — Rilis 3 (Minggu 13–19) sepenuhnya di luar periode ramp-up Sprint 1–2.*

*Verifikasi ulang (30 Jul 2026): dicek baris-per-baris ke `maintenance-activity-type-effort-summary.md` — role breakdown BE 28/FE 9/QA 8 rekonsiliasi persis ke sumber resmi (dokumen ini satu-satunya dari 3 proposal yang memang sudah punya breakdown role resmi, jadi tidak perlu direkonstruksi seperti Rilis 2). **SAP Sync** (9 SP: `MechanicOrderList`/`PoolingMOItem` 3 + 4 endpoint cleanup 6) dikonfirmasi tetap di sini — satu-satunya rilis yang menyimpan scope SAP Sync. Timing Gantt diperbaiki: BE (2 orang, full speed) selesai ~Minggu 16, bukan menyebar sampai Minggu 17 seperti versi sebelumnya.*

**Benefit ke customer**: Kegagalan create MO ke SAP akibat kombinasi Order Type+Activity Type yang salah-derive **berhenti** — Activity Type sekarang bisa dikonfigurasi fleksibel per Order Type oleh client sendiri. Sistem lebih robust (kurang dependency live-call antar service).

---

## Risiko & Catatan Terbuka

1. **Maintenance Activity Type diprioritaskan terakhir (Rilis 3, ~Minggu 19)** meski proposal sumbernya menyebut ini "menghentikan kegagalan integrasi create MO ke SAP yang sedang terjadi di server Production" — bukan sekadar enhancement. Urutan ini sudah disepakati bersama stakeholder (29 Jul 2026); dicatat di sini supaya risikonya eksplisit, bukan untuk didebat ulang.
2. **Item belum bisa diestimasi** di Rilis 3: mekanisme deteksi "submit mechanic terakhir" (trigger `ReferenceTransactionId`) — berpotensi menambah scope di luar 5 SP yang sudah dialokasikan, tergantung hasil investigasi engineer.
3. **Re-touch layar**: karena Man Power, Area, dan Maintenance Activity Type dikerjakan sebagai 3 rilis terpisah (bukan digabung sesuai rekomendasi awal proposal), layar **Additional Order** dan **Order Approval** dibuka ulang di ketiga rilis — konsekuensi dari urutan prioritas bisnis, bukan inefisiensi teknis yang terlewat.
4. **Man Power rollup "Dengan" logic penuh** (predecessor/serial/paralel, +8 SP) di-defer ke rilis berikutnya di luar 19 minggu ini — Rilis 1 memakai opsi interim ("Tanpa", parent dikosongkan dulu).
5. **Buffer ~1 sprint** dari kapasitas 2 BE disimpan sebagai kontingensi murni (risiko estimasi belum divalidasi engineer, mapping BAPI ke SAP di luar kontrol tim Digiman+) — tidak dialokasikan ke scope tambahan.
6. **Mapping BAPI ke SAP** tetap di luar seluruh estimasi ini di ketiga rilis — assessment kelayakan teknis dikoordinasikan client (PIC: Faiza) dengan tim SAP internal mereka.
7. **Koreksi scope (29 Jul 2026)**: proposal [Area of Unit](area-of-unit-enhancement-proposal.html) berasumsi Additional Order "belum punya field Component/Sub Component sama sekali" — dikonfirmasi user, asumsi ini **salah**. Dropdown Component/SubComponent sudah ada di Inspection, Additional Inspection, **dan** Additional Order. Scope yang tersisa untuk Rilis 2 bukan membangun UI, melainkan **BE derive + snapshot `AreaCode`/`AreaName`** dari pilihan itu (backend-only, sama pola dengan Inspection) — berlaku juga untuk Additional Order, bukan cuma Inspection. Proposal HTML sumber **belum diubah** (perlu persetujuan terpisah sebelum revisi dokumen client-facing).
8. **Keputusan scope (30 Jul 2026)**: SAP Sync (`PoolingMOItem`/payload, MO Backlog inbound parse) dihapus dari Rilis 1 (Man Power, 5.2 SP) dan Rilis 2 (Area, 2.8 SP) — per arahan user, hanya di-scope di Rilis 3 (Maintenance Activity Type). **Belum diklarifikasi**: apakah baris QA/Testing di Rilis 1 (12 SP) & Rilis 2 (7 SP) — yang tadinya mencakup pengujian alur "→ SAP → MO Backlog →" sebagai bagian dari testing e2e — perlu ikut dikurangi, atau tetap sama karena testing tetap mencakup titik-titik lain di alur yang sama. Belum dikurangi di dokumen ini sampai ada arahan lebih lanjut.

---

## Referensi

- [effort-recap-3-proposals.html](effort-recap-3-proposals.html) — rekap effort awal ketiga proposal (tim BUMA ID vs tim baru)
- [man-power-duration-enhancement-proposal.html](man-power-duration-enhancement-proposal.html)
- [area-of-unit-enhancement-proposal.html](area-of-unit-enhancement-proposal.html)
- [inspection-order/maintenance-activity-type-effort-proposal.html](inspection-order/maintenance-activity-type-effort-proposal.html)
