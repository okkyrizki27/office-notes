# Effort Summary — Maintenance Activity Type & Rapikan Integrasi Inspection→Order

*Last updated: 2026-07-17*

---

Dokumen ini merangkum estimasi effort untuk [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) — redesign sourcing PM Activity Type → "Maintenance Activity Type" (Bagian 2.1–2.8), rapikan integrasi Inspection→Order termasuk standardisasi `WorkflowTransaction.ReferenceTransactionId` (Bagian 2.9–2.11), dan dampak ke Digiman Transaction Report (Bagian 2.12). Metodologi kalibrasi SP & mandays memakai **baseline tim BUMA ID** yang sama dengan [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) — tidak diulang detailnya di sini, hanya dipakai hasilnya. **Satu estimasi gabungan** (48 SP, direvisi 17 Jul 2026 dari 43 SP setelah scope 2.9a ditambahkan) — dampak ke report tidak dipisah jadi track/timeline tersendiri, per arahan user 17 Jul 2026.

## Metodologi (ringkas, lihat detail di area-of-unit-man-power-effort-summary.md)

- **SP dikalibrasi ke skala Fibonacci `[1, 2, 3, 5, 8]`** per komponen kerja, berdasarkan label kompleksitas kualitatif:

| Label Kompleksitas | SP |
|---|---|
| Kecil | 1 |
| Kecil–Sedang | 2 |
| Sedang | 3 |
| Sedang–Besar | 5 |
| Besar | 8 |

- **Mandays = SP × ~1.17** — rasio throughput riil tim BUMA ID (312 SP ÷ 366 person-days, basis 5 sprint terakhir). **Dikoreksi 16 Jul 2026**: headcount tim BUMA ID yang benar adalah **6 orang** (2 BE, 1 FE Web, 1 FE Mobile, 2 QA — dikonfirmasi dari roster `BUMA_ID_MEMBERS` di `Jira/sprint-report/ORR_sprint_report.py`), bukan 5 seperti yang dipakai sebelumnya. Lihat [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) bagian B untuk detail koreksi.
- **Kapasitas efektif sprint = ~43.7 SP/sprint** — velocity rata-rata 5 sprint terakhir (62.4 SP/sprint) × 70% (30% sisanya dialokasikan ke production support). *(Tidak terpengaruh koreksi headcount — ini murni SP selesai per sprint riil, bukan dihitung dari jumlah orang.)*

---

## Rekap Estimasi

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| Master Data UI baru: `MaintenanceActivityType` (CRUD `Id`/`Code`/`Description`/`IsActive`) | Sedang | 3 | 3.5 | CRUD standar + validasi unique `Code` & constraint ≤5 karakter ([maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) 2.9, batasan `PoolingMOItem.PMActType varchar(5)`) |
| Master Data UI baru: `MaterialCostTypeActivityTypeMapping` (M:N Order Type ↔ Activity Type) | Sedang–Besar | 5 | 5.9 | CRUD + validasi M:N — pola sama dengan Master Data Area↔Component-SubComponent di [area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md) Bagian 3 |
| Permission code baru untuk maintain kedua Master Data di atas | Kecil | 1 | 1.2 | Setup permission code + assign ke role |
| Data seeder `MaintenanceActivityType` — mekanisme seeder (bukan isi data, isi dari tim Product) | Kecil–Sedang | 2 | 2.3 | Script/mekanisme untuk deploy awal PRD |
| Additional Order Screen 1: hapus field "Activity Type" | Kecil | 1 | 1.2 | Remove field dari UI + stop populate `MechanicOrderSummary.MaintenanceCategoryCode` lewat UI |
| Additional Order Screen 2 ("Order #N"): tambah dropdown Maintenance Activity Type (dependent ke Order Type, disabled state, validasi wajib-isi) | Kecil–Sedang | 2 | 2.3 | Dropdown filtered by Order Type + disabled/enabled state + error message (2.3) |
| Screen "Order Details" (create/complete eMOL dari Inspection): tambah dropdown Maintenance Activity Type | Kecil | 1 | 1.2 | Field & logic sama dengan baris di atas, reuse komponen — screen berbeda |
| Order Approval: tambah edit Maintenance Activity Type | Kecil | 1 | 1.2 | Reuse validasi & dropdown yang sama, field baru di layar approval (2.8) |
| `MechanicOrderList`: tambah kolom `MaintenanceActivityTypeCode` (migration + wiring insert/update kedua flow) | Kecil | 1 | 1.2 | Kolom baru, populate saat submit eMOL (Inspection & Additional) |
| `PoolingMOItem` insert (5.2): sederhanakan populate `PMActType` **+ tambah populate `HourMeter`/`InspectorCode`/`InspectorName`/`EquipmentModel`** (pertama kali diisi — kolomnya sudah ada, bukan untuk SAP, lihat catatan) | Kecil–Sedang | 2 | 2.3 | Extend query insert yang sama — `HourMeter`/`InspectorCode`/`InspectorName` dari snapshot baru di `MechanicOrderSummary`/`MechanicOrderList`, `EquipmentModel` dari `MechanicOrderSummary.AssetModelName` (sudah ada, tidak perlu kolom baru). **Dikoreksi 16 Jul 2026**: bukan untuk sampai ke payload SAP (mapping BAPI real dikonfirmasi user, tidak ada field-field ini) — murni kelengkapan record staging `PoolingMOItem` itu sendiri |
| Extend proses submit Inspection ("Sign and Finish"): copy `Source`/`SourceWorkOrderId`/`SourceWorkOrderNumber`/`HourMeter` ke `MechanicOrderSummary`, `InspectorCode`/`InspectorName` ke `MechanicOrderList` (+ migration kolom di 2 tabel) | Sedang–Besar | 5 | 5.9 | Menjangkau 3 level entity (`WorkOrder`/`TaskPersonalized`/`TaskPersonalizedFinding`), termasuk logic "`HourMeter` dari submit mechanic pertama" (2.9) dan derivasi `Source` (`'Scheduled Inspection'`/`'Additional Inspection'`) dari `WorkOrder.WorkType` (ditambahkan 17 Jul 2026, absorbed ke estimasi existing — perubahan kecil di scope yang sama) |
| Resolusi `InspectorName` dari `InspectorCode` (lookup master data User saat submit) | Kecil–Sedang | 2 | 2.3 | Detail sumber & mekanisme resolve belum final (5.1 dokumen enhancement) — estimasi asumsi lookup sederhana |
| Endpoint `order-detail`: hapus live call, baca dari `MechanicOrderDetail` snapshot (2.11.D) | Kecil | 1 | 1.2 | Redundant call cleanup |
| Endpoint dropdown `assetnumber`/`assetmodel`: hapus live call, baca dari `MechanicOrderSummary` (2.11.D) | Kecil | 1 | 1.2 | Redundant call cleanup, sama sifatnya |
| Endpoint `approve`: API baru baca snapshot Order DB (2.11.E) | Sedang | 3 | 3.5 | Endpoint baru, tidak ubah in-place (backward-compat). Mekanisme approve lengkap (5 langkah) dikonfirmasi 16 Jul 2026 — service bus di step publish SAP murni outbound existing, **tidak ada** dependency baru ke `maintenance-execution` (lihat enhancement doc 2.11.E) |
| Deprecate endpoint dropdown `maintenancecategory` (2.11.A) — cek tidak ada consumer lain, hapus/deprecate | Kecil | 1 | 1.2 | Verifikasi consumer + cleanup endpoint lama |
| **(Baru, 17 Jul 2026)** Standardisasi `WorkflowTransaction.ReferenceTransactionId` ke `MechanicOrderSummaryId` — titik pembuatan (trigger submit mechanic terakhir) + dual-lookup transisi di 3 endpoint (get approval list, get approval detail, approve langkah 1) | Sedang–Besar | 5 | 5.9 | [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) 2.9a. Dual-lookup sementara sampai data lama (`ReferenceTransactionId=WorkOrderId`) tidak ada yang menggantung — penghapusan dual-lookup jadi pending item rilis berikutnya, **di luar** SP ini |
| **(Baru, 17 Jul 2026) Belum bisa diestimasi**: Mekanisme deteksi "submit mechanic terakhir" — validasi ulang & kemungkinan tambah filter `TaskPersonalized.IsActive=1`, berpotensi butuh cross-service call baru ke `maintenance-execution` | **Belum bisa diestimasi** | — | — | [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) 2.9/2.11 — tergantung konfirmasi engineer, masih open item. Bisa kecil (tambah 1 filter ke query existing) atau besar (bangun cross-service call baru yang belum ada — kalau ini satu-satunya titik yang tidak bisa dihilangkan lewat snapshot, lihat prinsip audit 2.11) |
| Testing end-to-end (Additional Order + Inspection Order: create → approve → SAP sync, regresi ke fitur existing) | Besar | 8 | 9.4 | Banyak titik integrasi (`maintenance-order`, `maintenance-execution`, SAP sync, approval workflow) |
| Digiman Transaction Report: tambah kolom `Maint. Act. Type` ke view Synapse (`vw_report_iams_f_am_digiman_dorder`, 4 titik CTE) — [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) 2.12 | Kecil | 1 | 1.2 | Passthrough dari `mechanicorderlist.maintenanceactivitytypecode`, sejajar pola kolom `MOType` yang sudah ada di view yang sama |
| Update dataset/report Power BI — tampilkan kolom `Maint. Act. Type` baru | Kecil–Sedang | 2 | 2.3 | Reference class: preseden serupa [IAMS30-3946](https://bukittechnology.atlassian.net/browse/IAMS30-3946) (kolom lain di view yang sama, 2 SP untuk sisi PBI-nya) — preseden itu sempat *reopened* 1x pasca-rilis awal (3 bug: data null, presisi angka, field kosong), pertimbangkan buffer stabilisasi serupa |
| **Total** | | **48** | **~56** | 1 angka pasti (bukan range) — hasil kalibrasi Fibonacci per baris, termasuk dampak ke report ([maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) 2.12, dikonfirmasi in-scope 17 Jul 2026). **Mandays dikoreksi 16 Jul 2026** dari ~39→~47 (koreksi headcount tim BUMA ID 5→6 orang), **43 SP/~50 mandays (17 Jul 2026)** setelah 2 baris report/PBI digabung ke total, lalu **48 SP/~56 mandays (17 Jul 2026, revisi kedua)** setelah standardisasi `ReferenceTransactionId` (2.9a) ditambahkan sebagai scope baru. UNION/dual-path di query **report** (`dorder`/`leadtime`/dst) sengaja **tidak** ditambahkan ke SP — diputuskan dibiarkan permanen (2.12), beda arah dari sisi API yang di atas. Item "mekanisme deteksi submit terakhir" **di luar** total ini (belum bisa diestimasi) — sama perlakuannya dengan Mapping BAPI di [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md). |

*Catatan: estimasi berdasarkan deskripsi arsitektur dari diskusi desain, tanpa akses langsung ke source code — perlu divalidasi oleh engineer yang pegang codebase `maintenance-order`/`maintenance-execution`. Item terbesar (Master Data Mapping M:N, extend submit Inspection, testing e2e) adalah sumber ketidakpastian paling besar.*

---

## Estimasi Jumlah Sprint — 3 Skenario

*(Sprint = 10 hari kerja/2 minggu, kecuali skenario BUMA ID baseline yang pakai kapasitas SP/sprint riil-nya sendiri, bukan durasi kalender per-role — lihat catatan per baris.)*

| Skenario | Tim | Velocity | Mandays | Cara Hitung Sprint | Sprint |
|---|---|---|---|---|---|
| **BUMA ID (baseline)** | 6 orang, existing (2 BE, 1 FE Web, 1 FE Mobile, 2 QA) | ~0.85 SP/person-day (real) | ~56 | 48 SP ÷ 43.7 SP/sprint (kapasitas efektif tim, 70% dari velocity 62.4 SP/sprint) = 1.098 | **~2 sprint** (**melebihi kapasitas 1 sprint** — 110%, naik dari 98% sebelum standardisasi `ReferenceTransactionId` ditambahkan — kemungkinan meluber ke sprint ke-2) |
| **BUMA ID Modified — dengan KT** | 4 orang baru (1 BE, 1 FE Web, 1 FE Mobile, 1 QA) | 0.81 SP/hari/orang | ~59 | Critical path (BE+QA) 39 SP ÷ 0.81 ≈ 48 hari ÷ 10 hari/sprint | **~5 sprint** |
| **BUMA ID Modified — tanpa KT** | 4 orang baru, idem | 0.7 SP/hari/orang | ~69 | Critical path 39 SP ÷ 0.7 ≈ 56 hari ÷ 10 hari/sprint | **~6 sprint** |

**⚠️ Update 17 Jul 2026 (revisi pertama)**: setelah 3 SP report/PBI digabung ke total (43 SP, bukan 40), skenario "BUMA ID Modified — dengan KT" bergeser dari ~4 ke ~5 sprint — sempat sama dengan skenario tanpa KT (keduanya 5 sprint, critical path 34 SP).

**⚠️ Update 17 Jul 2026 (revisi kedua, setelah standardisasi `ReferenceTransactionId` ditambahkan, +5 SP ke BE)**: total naik ke 48 SP, critical path (BE+QA) naik ke 39 SP. Efeknya **2 skenario tim baru sekarang berbeda lagi** (tidak lagi sama-sama 5 sprint seperti revisi pertama): **dengan KT tetap ~5 sprint** (39÷0.81≈48 hari, masih di bawah batas 50 hari/5 sprint), tapi **tanpa KT naik jadi ~6 sprint** (39÷0.7≈56 hari, melewati batas 50 hari). KT sekarang kembali **menghemat 1 sprint penuh** (5 vs 6), bukan cuma menghemat mandays seperti kesimpulan revisi pertama. Skenario BUMA ID baseline juga berubah — dari "~1 sprint sangat mepet" jadi **"~2 sprint, melebihi kapasitas 1 sprint"** (lihat tabel di atas).

**Kenapa cara hitungnya beda antar skenario**: BUMA ID baseline pakai kapasitas SP/sprint riil tim (data historis, sudah mencakup 5 developer/6 orang bekerja paralel) — tidak perlu breakdown role/dependency karena itu sudah "given" dari data. BUMA ID Modified belum punya data historis, jadi dihitung dari critical path per-role (BE jadi bottleneck, lihat breakdown & dependency di bawah) — pendekatan bottom-up karena tidak ada shortcut data riil.

*(Detail breakdown per role, dependency, dan alasan critical path untuk BUMA ID Modified — lihat section di bawah.)*

---

## Skenario Alternatif: Tim Baru Terpisah ("BUMA ID Modified")

*(16 Jul 2026 — bukan penambahan orang ke tim BUMA ID, ini tim Scrum lain yang berdiri sendiri, sprint & kapasitas independen. Terdiri dari **1 BE, 1 FE Web, 1 FE Mobile, 1 QA** — 4 orang, semuanya baru di codebase & domain ini.)*

### Breakdown 48 SP per role

| Role | SP | Item |
|---|---|---|
| BE | 31 | Master Data schema/API (4), permission (1), seeder (2), `MechanicOrderList` kolom (1), `PoolingMOItem` (2), extend submit Inspection (5), resolusi InspectorName (2), 4 endpoint (order-detail/assetnumber-model/approve/deprecate) (6), report/PBI (3, digabung ke BE per arahan user 17 Jul 2026), **standardisasi `ReferenceTransactionId` + dual-lookup 3 endpoint (5, ditambahkan 17 Jul 2026 — 2.9a)** |
| FE Web | 5 | Master Data CRUD UI (1.5), Mapping UI (2.5), Order Approval edit (1) — asumsi Master Data admin & Approval itu layar Web |
| FE Mobile | 4 | Additional Order Screen 1 hapus field (1), Screen 2 dropdown (2), Order Details dropdown (1) — asumsi layar field/mechanic itu Mobile |
| QA | 8 | Testing end-to-end |

> Asumsi platform (Web vs Mobile) di atas belum dikonfirmasi ke tim aktual — kalau ternyata beda, breakdown SP per role perlu disesuaikan. **3 SP report/PBI** dimasukkan ke baris BE murni untuk kesederhanaan tabel (arahan user: estimasi jadi satu, tidak dipisah per-role/PIC) — secara teknis mencakup pekerjaan SQL view Synapse & dataset Power BI, bukan API backend biasa. **5 SP standardisasi `ReferenceTransactionId`** juga masuk BE murni — perubahan trigger workflow + 3 endpoint, tidak menyentuh FE/QA secara langsung (di luar regresi testing yang sudah tercakup baris QA). Item "mekanisme deteksi submit terakhir" (belum bisa diestimasi, lihat Rekap Estimasi) **tidak** dimasukkan ke breakdown role manapun di sini — masih open item, di luar 48 SP.

### Velocity: 2 skenario (tanpa vs dengan Knowledge Transfer)

Velocity awal 2 SP/hari/orang dianggap **terlalu optimis** untuk tim yang benar-benar baru di domain & codebase ini (baseline tim BUMA ID sendiri yang sudah berpengalaman cuma ~0.85 SP/person-day riil — lihat di atas). Dua skenario:

| | Tanpa KT | Dengan KT |
|---|---|---|
| Velocity | **0.7 SP/hari/orang** (asumsi user) | **0.81 SP/hari/orang** — dihitung menutup 75% jarak dari 0.7 menuju ceiling riil tim BUMA ID (0.85 SP/person-day, dikoreksi dari 1.02): `0.7 + 0.75 × (0.85 − 0.7) ≈ 0.81` |
| BE (31 SP) | 44.3 hari | 38.3 hari |
| FE Web (5 SP) | 7.1 hari | 6.1 hari |
| FE Mobile (4 SP) | 5.7 hari | 4.9 hari |
| QA (8 SP) | 11.4 hari | 9.8 hari |
| **Total mandays** (48 SP ÷ velocity) | **~69** | **~59** |
| **Critical path** — (BE SP + QA SP) ÷ velocity = 39 SP ÷ velocity, karena FE selalu selesai lebih cepat dari BE jadi tidak menambah durasi | **~56 hari kerja** | **~48 hari kerja** |
| **Sprint** (asumsi 2 minggu/10 hari kerja) | **~6 sprint** | **~5 sprint** |

**Dependency & urutan kerja** (kenapa critical path = BE + QA, bukan jumlah semua role):
1. BE kerjakan Master Data schema/API + kolom `MechanicOrderList` dulu (5 SP) — ini yang blocking FE mulai kerja.
2. FE Mobile bisa mulai item "hapus field" (1 SP, tanpa dependency) paralel dari hari pertama.
3. Begitu API dasar siap, FE Web & FE Mobile kerja paralel — tapi total kerja mereka (5+4=9 SP) jauh lebih kecil dari sisa kerja BE (**26 SP** backend-only lain: permission, seeder, `PoolingMOItem`, extend submit process, resolusi InspectorName, 4 endpoint, report/PBI, standardisasi `ReferenceTransactionId`) — jadi FE **selalu selesai duluan** dan menganggur menunggu BE.
4. QA baru bisa mulai testing end-to-end setelah BE benar-benar selesai (butuh endpoint `approve`, extend submit process, **dan sekarang juga standardisasi `ReferenceTransactionId`** yang baru kelar di akhir) — QA jadi fase terakhir yang murni serial setelah BE.

*(Perbandingan lintas 3 skenario — lihat tabel konsolidasi di "Estimasi Jumlah Sprint" di atas. Urutan masuk akal: tim baru, bahkan dengan KT, selalu butuh mandays lebih banyak dari tim veteran untuk scope yang sama — KT memperkecil gap-nya, tidak membalik urutannya.)*

**Temuan penting**: nambah role FE Web + FE Mobile terpisah untuk tim BUMA ID Modified kemungkinan **over-provisioned** untuk enhancement spesifik ini — **~65% dari total SP (31/48)** adalah kerja BE (naik dari 60%/26 SP sebelum standardisasi `ReferenceTransactionId` ditambahkan), sementara FE Web+Mobile cuma 9 SP gabungan dan selalu selesai jauh sebelum BE. BE jadi satu-satunya penentu durasi total, terlepas dari berapa banyak FE/QA yang di-staff — dan makin dominan setelah revisi ini.

---

## Referensi
- [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) — dokumen sumber, seluruh keputusan scope yang jadi dasar breakdown ini
- [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) — metodologi kalibrasi SP/mandays/sprint lengkap, dan estimasi enhancement lain di layar yang sama
- [order-emol-sap-sync.md](order-emol-sap-sync.md) — schema & flow existing yang jadi dasar sebagian komponen di atas
- [IAMS30-3946](https://bukittechnology.atlassian.net/browse/IAMS30-3946) — reference class Jira untuk estimasi baris "Update dataset/report Power BI" di atas, dicek 17 Jul 2026
