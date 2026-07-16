# Effort Summary — Maintenance Activity Type & Rapikan Integrasi Inspection→Order

*Last updated: 2026-07-16*

---

Dokumen ini merangkum estimasi effort untuk [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) — redesign sourcing PM Activity Type → "Maintenance Activity Type" (Bagian 2.1–2.8) plus rapikan integrasi Inspection→Order (Bagian 2.9–2.11). Metodologi kalibrasi SP & mandays memakai **baseline tim BUMA ID** yang sama dengan [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) — tidak diulang detailnya di sini, hanya dipakai hasilnya.

## Metodologi (ringkas, lihat detail di area-of-unit-man-power-effort-summary.md)

- **SP dikalibrasi ke skala Fibonacci `[1, 2, 3, 5, 8]`** per komponen kerja, berdasarkan label kompleksitas kualitatif:

| Label Kompleksitas | SP |
|---|---|
| Kecil | 1 |
| Kecil–Sedang | 2 |
| Sedang | 3 |
| Sedang–Besar | 5 |
| Besar | 8 |

- **Mandays = SP × ~0.98** — rasio throughput riil tim BUMA ID (312 SP ÷ 305 person-days, basis 5 sprint terakhir).
- **Kapasitas efektif sprint = ~43.7 SP/sprint** — velocity rata-rata 5 sprint terakhir (62.4 SP/sprint) × 70% (30% sisanya dialokasikan ke production support).

---

## Rekap Estimasi

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| Master Data UI baru: `MaintenanceActivityType` (CRUD `Id`/`Code`/`Description`/`IsActive`) | Sedang | 3 | 2.9 | CRUD standar + validasi unique `Code` & constraint ≤5 karakter ([maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) 2.9, batasan `PoolingMOItem.PMActType varchar(5)`) |
| Master Data UI baru: `MaterialCostTypeActivityTypeMapping` (M:N Order Type ↔ Activity Type) | Sedang–Besar | 5 | 4.9 | CRUD + validasi M:N — pola sama dengan Master Data Area↔Component-SubComponent di [area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md) Bagian 3 |
| Permission code baru untuk maintain kedua Master Data di atas | Kecil | 1 | 1.0 | Setup permission code + assign ke role |
| Data seeder `MaintenanceActivityType` — mekanisme seeder (bukan isi data, isi dari tim Product) | Kecil–Sedang | 2 | 2.0 | Script/mekanisme untuk deploy awal PRD |
| Additional Order Screen 1: hapus field "Activity Type" | Kecil | 1 | 1.0 | Remove field dari UI + stop populate `MechanicOrderSummary.MaintenanceCategoryCode` lewat UI |
| Additional Order Screen 2 ("Order #N"): tambah dropdown Maintenance Activity Type (dependent ke Order Type, disabled state, validasi wajib-isi) | Kecil–Sedang | 2 | 2.0 | Dropdown filtered by Order Type + disabled/enabled state + error message (2.3) |
| Screen "Order Details" (create/complete eMOL dari Inspection): tambah dropdown Maintenance Activity Type | Kecil | 1 | 1.0 | Field & logic sama dengan baris di atas, reuse komponen — screen berbeda |
| Order Approval: tambah edit Maintenance Activity Type | Kecil | 1 | 1.0 | Reuse validasi & dropdown yang sama, field baru di layar approval (2.8) |
| `MechanicOrderList`: tambah kolom `MaintenanceActivityTypeCode` (migration + wiring insert/update kedua flow) | Kecil | 1 | 1.0 | Kolom baru, populate saat submit eMOL (Inspection & Additional) |
| `PoolingMOItem`: sederhanakan populate `PMActType` (langsung dari `mol.MaintenanceActivityTypeCode`, hapus percabangan lama) | Kecil | 1 | 1.0 | Simplifikasi query 5.2 [order-emol-sap-sync.md](order-emol-sap-sync.md) |
| Extend proses submit Inspection ("Sign and Finish"): copy `SourceWorkOrderId`/`SourceWorkOrderNumber`/`HourMeter` ke `MechanicOrderSummary`, `InspectorCode`/`InspectorName` ke `MechanicOrderList` (+ migration kolom di 2 tabel) | Sedang–Besar | 5 | 4.9 | Menjangkau 3 level entity (`WorkOrder`/`TaskPersonalized`/`TaskPersonalizedFinding`), termasuk logic "`HourMeter` dari submit mechanic pertama" (2.9) |
| Resolusi `InspectorName` dari `InspectorCode` (lookup master data User saat submit) | Kecil–Sedang | 2 | 2.0 | Detail sumber & mekanisme resolve belum final (5.1 dokumen enhancement) — estimasi asumsi lookup sederhana |
| Endpoint `order-detail`: hapus live call, baca dari `MechanicOrderDetail` snapshot (2.11.D) | Kecil | 1 | 1.0 | Redundant call cleanup |
| Endpoint dropdown `assetnumber`/`assetmodel`: hapus live call, baca dari `MechanicOrderSummary` (2.11.D) | Kecil | 1 | 1.0 | Redundant call cleanup, sama sifatnya |
| Endpoint `approve`: API baru baca snapshot Order DB (2.11.E) | Sedang | 3 | 2.9 | Endpoint baru, tidak ubah in-place (backward-compat) — **di luar effort ini**: handling service bus, lihat baris terpisah di bawah |
| Deprecate endpoint dropdown `maintenancecategory` (2.11.A) — cek tidak ada consumer lain, hapus/deprecate | Kecil | 1 | 1.0 | Verifikasi consumer + cleanup endpoint lama |
| Testing end-to-end (Additional Order + Inspection Order: create → approve → SAP sync, regresi ke fitur existing) | Besar | 8 | 7.8 | Banyak titik integrasi (`maintenance-order`, `maintenance-execution`, SAP sync, approval workflow) |
| **Total** | | **39** | **~38** | 1 angka pasti (bukan range) — hasil kalibrasi Fibonacci per baris |

**Di luar total di atas (belum bisa diestimasi / di luar scope):**

| Item | Status | Catatan |
|---|---|---|
| Endpoint `approve`: cek & handle dependency **service bus** (2.11.E) | Belum bisa diestimasi | Tergantung hasil cek developer — detail dependency service bus ke `maintenance-execution` belum diketahui |
| Dampak ke report (`order-result-compliance.md`, `inspection-result.md`, `Backlog Monitoring.sql`, dst) | Di luar scope | Dikonfirmasi ada dampak, dibahas di sesi & dokumen terpisah — tidak termasuk total di atas |

*Catatan: estimasi berdasarkan deskripsi arsitektur dari diskusi desain, tanpa akses langsung ke source code — perlu divalidasi oleh engineer yang pegang codebase `maintenance-order`/`maintenance-execution`. Item terbesar (Master Data Mapping M:N, extend submit Inspection, testing e2e) adalah sumber ketidakpastian paling besar.*

---

## Estimasi Jumlah Sprint

Pakai kapasitas efektif tim BUMA ID yang sama dengan [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) (~43.7 SP/sprint, basis velocity 5 sprint terakhir, alokasi 70% enhancement + 30% production support):

**39 SP ÷ 43.7 SP/sprint = 0.89 → 1 sprint** (~89% kapasitas efektif sprint tsb — nyaris penuh, sisa ruang kecil untuk item lain di sprint yang sama).

### Kalau dikerjakan bersamaan dengan Area of Unit & Man Power

Kedua enhancement menyentuh layar **persis sama** (Additional Order Screen 1 & 2, screen "Order Details" Inspection — lihat [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) header dokumen & Bagian 5.2). Kalau dikerjakan tim yang sama di periode yang sama, total kombinasi SP:

| Skenario | SP Area/Man Power | SP Activity Type | Total SP | ÷ 43.7 SP/sprint | Sprint |
|---|---|---|---|---|---|
| **Tanpa** logic predecessor penuh | 85 | 39 | **124** | 2.84 | **≈3 sprint** (kapasitas 3 sprint ~131 SP, masih muat) |
| **Dengan** logic predecessor penuh | 93 | 39 | **132** | 3.02 | **≈3 sprint**, mepet ke batas (kapasitas 3 sprint ~131 SP — selisih ~1 SP, dalam margin ketidakpastian estimasi) |

Bukan hasil jumlah linear dari estimasi sprint masing-masing dokumen (2+1) — dihitung ulang dari total SP gabungan. Perlu dikoordinasikan sprint planning-nya bareng jika dua enhancement ini dikerjakan berdekatan — dicatat sebagai open item di [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) Bagian 5.2 (user yang atur langsung).

---

## Referensi
- [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) — dokumen sumber, seluruh keputusan scope yang jadi dasar breakdown ini
- [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) — metodologi kalibrasi SP/mandays/sprint lengkap, dan estimasi enhancement lain di layar yang sama
- [order-emol-sap-sync.md](order-emol-sap-sync.md) — schema & flow existing yang jadi dasar sebagian komponen di atas
