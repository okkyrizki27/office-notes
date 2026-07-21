# Effort Summary — Storage Location & Planner Group (Gabungan)

*Last updated: 2026-07-21*

---

Dokumen ini merangkum estimasi effort **gabungan** untuk dua enhancement kecil di alur Order Digiman+ (**keduanya request MKP**) yang sengaja dibundel jadi **satu rilis / satu sprint** karena masing-masing di bawah kapasitas 1 sprint:

1. **Storage Location pada Create Order** — [storage-location-planner-group-enhancement.md](storage-location-planner-group-enhancement.md) Bagian A — tampilkan & simpan Storage Location (Sloc) saat pilih material ("Add Part"), menggantikan auto-resolve yang ambigu. *(Divalidasi ke UI & data nyata, 21 Jul 2026.)*
2. **Planner Group pada Order Approval** — [storage-location-planner-group-enhancement.md](storage-location-planner-group-enhancement.md) Bagian B, **Opsi 2** (input eksplisit saat approval).

Metodologi kalibrasi SP & mandays memakai **baseline tim BUMA ID** yang sama dengan [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) dan [maintenance-activity-type-effort-summary.md](maintenance-activity-type-effort-summary.md) — tidak diulang detailnya di sini, hanya dipakai hasilnya.

## Metodologi (ringkas — detail di area-of-unit-man-power-effort-summary.md bagian A–C)

- **SP dikalibrasi ke Fibonacci `[1, 2, 3, 5, 8]`** per komponen kerja, dari label kompleksitas kualitatif:

| Label Kompleksitas | SP |
|---|---|
| Kecil | 1 |
| Kecil–Sedang | 2 |
| Sedang | 3 |
| Sedang–Besar | 5 |
| Besar | 8 |

- **Mandays = SP × ~1.17** — throughput riil tim BUMA ID (312 SP ÷ 366 person-days, basis 5 sprint terakhir, 6 orang: 2 BE, 1 FE Web, 1 FE Mobile, 2 QA).
- **Kapasitas efektif = ~43.7 SP/sprint** — velocity rata-rata 5 sprint terakhir (62.4 SP/sprint) × 70% (30% sisanya production support).

---

## 1. Storage Location pada Create Order

### Scope (dikonfirmasi dari UI & data nyata, 21 Jul 2026)

**Kondisi sekarang:**
- Master `Material` (data dari SAP) sudah **multi-row per Sloc** — material yang sama muncul berkali-kali kalau ada di >1 Sloc (dikonfirmasi dari UI & DB). Kolom `StorageLocation` sudah ada di [maintenance-order-schema.md](../database/maintenance-order-schema.md#L140).
- Material list picker ("Add Part" — layar "Order Details" dari Inspection & block "Order #N" Additional Order) **sudah menampilkan duplikat per-baris** (tanpa dedup), tapi **tidak melabeli Sloc**. User melihat card yang tampak identik (Number/Description sama, hanya `Stock` yang beda) dan tidak tahu Sloc mana yang akan dipakai. Card **sudah** melabeli dimensi **Batch/valuation type** (mis. `NEW`/`REPAIRED`), tapi **Sloc belum**.
- **Endpoint list BE belum membawa** field Sloc (proyeksi/DTO tidak menyertakannya).
- Transaksi `MechanicOrderMaterial` **tidak menyimpan** Sloc — field-nya cuma `MaterialNumber`/`Quantity`/`BatchCode`/dll ([maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md#L405-L421)). Sloc baru di-resolve otomatis saat insert `PoolingMOItem` (Step 2, match `Number+Description+BatchCode+SiteId+SectionTypeCode`) di [order-emol-sap-sync.md](order-emol-sap-sync.md#L186-L200). Karena 1 material bisa punya banyak Sloc, resolve ini **ambigu** dan berpotensi mengirim **Sloc arbitrer** ke SAP.

**Keputusan scope:**
- **Labeli Sloc** di tiap card material list — pola sama dengan label Batch yang sudah ada.
- **Simpan Sloc terpilih** di `MechanicOrderMaterial` — pola sama dengan `BatchCode` yang sudah tersimpan hari ini.
- **Pakai Sloc tersimpan** di outbound — ganti auto-resolve Step 2 → pakai `MechanicOrderMaterial.StorageLocation` (pilihan user), sekaligus **memperbaiki bug data laten** (kirim Sloc arbitrer).
- **Tanpa toggle per-tenant** — walau request dari MKP, ini perbaikan data/UX yang aman untuk semua tenant, jadi tidak di-gate per-tenant (keputusan user 21 Jul 2026). Beda dari Planner Group (yang tetap pakai toggle).
- **Tidak perlu**: master data baru, permission baru, integrasi/sync material SAP baru (data Sloc sudah lengkap multi-row di Digiman+), atau field outbound baru (`SLoc` & jalur ke SAP sudah ada).

### Effort

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| **BE**: material list endpoint bawa field `StorageLocation` (proyeksi + DTO) | Kecil | 1 | 1.2 | List sudah per-Sloc (tanpa dedup, dikonfirmasi UI) — tinggal surface kolom yang sudah ada di master `Material` |
| **FE**: labeli Sloc di tiap card material list + selection bawa Sloc terpilih — 2 jalur (Additional Order "Order #N" + Inspection "Order Details") | Kecil–Sedang | 2 | 2.3 | Membedakan card yang tadinya tampak identik; reuse komponen picker yang sama di kedua jalur; pola label sama dengan Batch (NEW/REPAIRED) yang sudah ada |
| `MechanicOrderMaterial`: kolom `StorageLocation` baru (migration) + capture Sloc baris terpilih saat "Save" | Kecil–Sedang | 2 | 2.3 | Transaksi belum simpan Sloc (dikonfirmasi schema) — pola sama dengan `BatchCode` yang sudah tersimpan |
| Outbound: ganti resolve SLoc Step 2 `PoolingMOItem` → pakai `MechanicOrderMaterial.StorageLocation` | Kecil | 1 | 1.2 | Menyederhanakan query existing + hilangkan ambiguitas/kirim Sloc arbitrer. Field `SLoc` & jalur ke SAP tidak berubah |
| Testing e2e: Sloc dari BE → tampil 2 jalur → tersimpan di transaksi → mengalir benar ke `PoolingMOItem.SLoc` → payload → SAP; regresi picker & pooling (termasuk material yang muncul di banyak Sloc) | Sedang | 3 | 3.5 | Termasuk regresi penghapusan auto-resolve lama |
| **Total (Storage Location)** | | **9** | **~10** | 1 angka pasti hasil kalibrasi Fibonacci per baris |

*Catatan: forward-only — order/eMOL lama tetap apa adanya (Sloc lama hasil auto-resolve), enhancement berlaku untuk Order baru. Tidak ada open item teknis tersisa — Sloc-sync tidak perlu (data sudah multi-row), grain list sudah per-Sloc.*

---

## 2. Planner Group pada Order Approval

Scope lengkap & keputusan di [storage-location-planner-group-enhancement.md](storage-location-planner-group-enhancement.md) Bagian B. Ada **2 opsi**:

- **Opsi 1 — Auto-derive dari Equipment (SAP side)**: **Effort Digiman+ = 0 SP** — tidak ada perubahan apapun di Digiman+ (field tetap tidak dikirim, SAP yang menentukan dari mapping Equipment).
- **Opsi 2 — Input eksplisit saat Approval (di bawah)**: **14 SP / ~16 mandays**.

Estimasi di bawah untuk **Opsi 2** (Opsi 1 tidak butuh baris effort). Planner Group **tetap pakai toggle on/off per-tenant** — itu bagian dari desain Opsi 2 (fitur MKP-specific), berbeda dari keputusan "tanpa toggle" untuk Storage Location.

### Effort (Opsi 2)

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| Master Data UI baru `PlannerGroup` (CRUD, di-scope per Site, maintain manual via UI Admin) | Sedang | 3 | 3.5 | Reference class: Master Data `MaintenanceActivityType`/`Area` CRUD standalone (Sedang, 3 SP). Dimensi Site = 1 FK + list difilter per site — masih CRUD standar |
| Permission code baru untuk maintain Master Data Planner Group | Kecil | 1 | 1.2 | Setup permission code + assign ke role |
| Toggle on/off per tenant (1 flag, gating show + enforce di approval) | Kecil–Sedang | 2 | 2.3 | Asumsi infra config per-tenant sudah ada — 1 flag + wiring conditional. Kalau infra flag belum ada, bisa naik |
| Order Approval: dropdown Planner Group **mandatory** + validasi gate approve | Kecil–Sedang | 2 | 2.3 | Field baru di layar approval + approve diblok kalau kosong. Sedikit di atas reuse murni (dropdown baru + gating) |
| Endpoint dropdown Planner Group difilter Site user login | Kecil | 1 | 1.2 | Aman krn approval sudah dibatasi per site per section — tidak ada skenario lintas-site (dikonfirmasi 21 Jul 2026) |
| Simpan `PlannerGroup` di order + publish field baru di payload outbound (message bus) | Kecil–Sedang | 2 | 2.3 | Migration kolom + wiring **publish-only**. Mapping ke field BAPI SAP = tanggung jawab middleware, **di luar scope** (konsisten pola field publish-only lain) |
| Testing e2e (CRUD master data, toggle on & off, mandatory gate, filter site, payload berisi `PlannerGroup`) | Sedang | 3 | 3.5 | Titik integrasi lebih sedikit — tanpa round-trip SAP (BAPI di middleware) & tanpa cross-service baru |
| **Total (Planner Group — Opsi 2)** | | **14** | **~16** | 1 angka pasti hasil kalibrasi Fibonacci per baris |

*Catatan: **Mapping BAPI ke SAP** (agar `PlannerGroup` sampai ke field SAP aktual) **di luar total ini** — tanggung jawab middleware, belum bisa diestimasi dari sisi Digiman+. Enforcement rule K01/material tetap SOP manual (0 SP). Seeder awal tidak perlu (data di-maintain manual, entity baru tanpa row existing).*

---

## Rekap Estimasi Gabungan

| # | Enhancement | SP | Mandays |
|---|---|---|---|
| 1 | Storage Location pada Create Order | **9** | ~10 |
| 2 | Planner Group pada Order Approval — **Opsi 2** *(Opsi 1 = 0 SP)* | **14** | ~16 |
| — | Mapping BAPI Planner Group → SAP *(middleware)* | **Belum bisa diestimasi** | **Belum bisa diestimasi** |
| | **Total gabungan** | **23** | **~27** |

*(SP 1 angka pasti hasil kalibrasi Fibonacci per baris — bukan range. Mandays = SP × 1.17, basis 5 sprint terakhir tim BUMA ID.)*

## Estimasi Jumlah Sprint — Tim BUMA ID (baseline)

Kapasitas efektif tim BUMA ID = **~43.7 SP/sprint** (velocity 62.4 SP/sprint × 70%).

| Skenario | SP | ÷ Kapasitas Efektif (43.7 SP/sprint) | Kebutuhan Sprint |
|---|---|---|---|
| Gabungan (Storage Location + Planner Group Opsi 2) | 23 | 23 ÷ 43.7 = 0.53 | **1 sprint** (~53% kapasitas efektif) |

Kedua enhancement muat nyaman dalam **1 sprint** dengan sisa kapasitas ~47% — inilah alasan keduanya digabung jadi satu rilis (masing-masing sendirian < 1 sprint: Storage Location ~0.21 sprint, Planner Group ~0.32 sprint).

---

## Skenario Alternatif: Tim Baru Terpisah ("BUMA ID Modified")

*(21 Jul 2026 — permintaan: hitung juga effort kalau dikerjakan **tim baru terpisah**, pola sama dengan skenario "BUMA ID Modified" di [maintenance-activity-type-effort-summary.md](maintenance-activity-type-effort-summary.md) & [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md). **Bukan** penambahan orang ke tim BUMA ID — tim Scrum lain yang berdiri sendiri, sprint & kapasitas independen. Terdiri dari **1 BE, 1 FE Web, 1 FE Mobile, 1 QA** — 4 orang, semuanya baru di codebase & domain ini.)*

**Kenapa cara hitungnya beda dari baseline**: baseline BUMA ID pakai **kapasitas SP/sprint riil tim** (43.7 SP/sprint — data historis, sudah mencakup semua orang bekerja paralel). Tim baru **belum punya data historis**, jadi jumlah sprint dihitung dari **critical path per-role** (BE jadi bottleneck) — pendekatan bottom-up.

### Breakdown SP per role

Asumsi platform: **Master Data admin & Order Approval = Web; layar create order (material picker "Add Part") = Mobile; schema/API/migration/outbound/kalkulasi = BE; testing = QA.**

| Sumber | BE | FE Web | FE Mobile | QA | Total |
|---|---|---|---|---|---|
| Storage Location (9 SP) | 4 | 0 | 2 | 3 | 9 |
| Planner Group Opsi 2 (14 SP) | 8.5 | 2.5 | 0 | 3 | 14 |
| **Total (23 SP)** | **12.5** | **2.5** | **2** | **6** | **23** |

> **Detail split**: Storage Location BE = endpoint Sloc (1) + `MechanicOrderMaterial` kolom+capture (2) + outbound Step 2 (1); FE Mobile = labeli Sloc + selection (2); QA = testing (3). Planner Group BE = Master Data schema/API (1.5) + permission (1) + toggle flag/gating (2) + approval gate (1) + dropdown API filter site (1) + simpan+publish outbound (2); FE Web = Master Data CRUD UI (1.5) + approval dropdown UI (1); QA = testing (3). Asumsi platform belum dikonfirmasi ke tim aktual. **Tidak ada track DE/DA** — kedua enhancement tidak menyentuh report/Power BI.

### Velocity, Critical Path & Jumlah Sprint

Velocity tim baru (asumsi sama dengan assessment sebelumnya): **Tanpa KT 0.7 SP/hari/orang**, **Dengan KT 0.81** (menutup 75% jarak dari 0.7 ke ceiling riil BUMA ID 0.85: `0.7 + 0.75 × (0.85 − 0.7) ≈ 0.81`).

Critical path = **BE + QA** (serial) — FE (Web 2.5 + Mobile 2 = 4.5 SP) jauh lebih kecil dari BE (12.5 SP), selalu selesai duluan lalu menganggur; QA fase terakhir serial setelah BE selesai (butuh endpoint, outbound, integrasi kelar untuk test e2e). Critical path = 12.5 + 6 = **18.5 SP**. Sprint = 10 hari kerja / 2 minggu, dibulatkan ke atas.

| Skenario | Critical Path (BE+QA) | ÷ Velocity → Hari | Sprint | Total Mandays (23 SP ÷ velocity) |
|---|---|---|---|---|
| Modified — dengan KT | 18.5 SP | ÷ 0.81 = 22.8 hari | **~3 sprint** | ~28 |
| Modified — tanpa KT | 18.5 SP | ÷ 0.7 = 26.4 hari | **~3 sprint** | ~33 |

### Perbandingan lintas tim (konsolidasi)

| Skenario | SP | BUMA ID baseline (43.7 SP/sprint, 6 orang) | Modified — dengan KT | Modified — tanpa KT |
|---|---|---|---|---|
| Gabungan (Storage Location + Planner Group Opsi 2) | 23 | **1 sprint** | **~3 sprint** | **~3 sprint** |

**Temuan penting**: BE mendominasi **~54% total SP** (12.5/23) — **1 BE tunggal di tim baru = bottleneck mutlak**. FE Web+Mobile (4.5 SP gabungan) selesai jauh sebelum BE. Menambah **BE ke-2** memangkas critical path jauh lebih efektif daripada menambah FE/QA. **KT menghemat ~5 mandays** (33→28) tapi **tidak menghemat sprint penuh di skala ini** — dua-duanya tetap ~3 sprint (beda dari inisiatif besar di mana KT bisa memangkas 1 sprint). Gap besar vs baseline (1 vs 3 sprint) wajar & bukan kontradiksi: baseline pakai throughput 6 orang paralel yang riil-terukur, sedangkan tim baru dihitung dari critical path 1 BE + 1 QA serial dengan velocity per-orang lebih rendah.

---

## Open Items

| # | Item | Terkait | Status |
|---|---|---|---|
| 1 | **Mapping BAPI** `PlannerGroup` → field SAP aktual | Planner Group Opsi 2 | Di luar scope (middleware) — belum bisa diestimasi, seperti pola field publish-only lain |
| 2 | Infra config/feature-flag per-tenant sudah ada atau belum | Planner Group Opsi 2 (toggle, 2 SP) | Kalau belum ada, baris toggle bisa naik |
| 3 | Kelengkapan mapping Equipment → Planner Group di SAP MKP (relevansi Opsi 1 vs Opsi 2) | Planner Group | Open item business, lihat [storage-location-planner-group-enhancement.md](storage-location-planner-group-enhancement.md) B.3 |
| 4 | Tim technical yang mengeksekusi belum ditentukan | Keduanya | Baseline BUMA ID dipakai sebagai **referensi** estimasi, **bukan** commitment tim ([MOM 01-Jul](../../../MKP-Project/2026-07-01-meeting-notes.md) poin #10) |

*Catatan umum: estimasi disusun dari deskripsi arsitektur + review UI/schema, tanpa akses langsung ke source code — perlu divalidasi engineer yang pegang codebase `maintenance-order`.*

---

## Referensi

- [storage-location-planner-group-enhancement.md](storage-location-planner-group-enhancement.md) — dokumen sumber (Storage Location Bagian A & Planner Group Bagian B — scope & keputusan)
- [order-emol-sap-sync.md](order-emol-sap-sync.md) — flow eMOL→SAP, insert `PoolingMOItem` (Step 5.2, resolve SLoc), payload
- [maintenance-order-schema.md](../database/maintenance-order-schema.md) — schema `Material` (`StorageLocation`), `MechanicOrderMaterial`, `PoolingMOItem`
- [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) — layar create order ("Order #N" / "Order Details", "Add Part"), mapping `MechanicOrderMaterial`
- [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) — metodologi kalibrasi SP/mandays/sprint lengkap (baseline BUMA ID)
- [maintenance-activity-type-effort-summary.md](maintenance-activity-type-effort-summary.md) — pola dokumen effort summary yang diikuti di sini
- [MOM 2026-07-09](../../../MKP-Project/2026-07-09-meeting-notes.md) — poin #7 (struktur material: 5 Batch/valuation type, 9–11 Sloc)
- [MOM 2026-07-01](../../../MKP-Project/2026-07-01-meeting-notes.md) — asal request Planner Group (#34–35), status tim technical (#10)
