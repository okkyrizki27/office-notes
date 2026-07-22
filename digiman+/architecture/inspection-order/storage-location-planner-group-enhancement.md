# Enhancement: Storage Location & Planner Group

*Last updated: 2026-07-22*

---

**Feature:** Order (Digiman+) — **Create Order** (Storage Location) & **Order Approval** (Planner Group)
**Client:** **MKP** (kedua enhancement) — Storage Location diimplementasi **tanpa toggle per-tenant** (keputusan teknis), sehingga berlaku untuk semua tenant
**Related doc:** [order-emol-sap-sync.md](order-emol-sap-sync.md), [maintenance-order-schema.md](../database/maintenance-order-schema.md)
**Effort:** [storage-location-planner-group-effort-summary.md](storage-location-planner-group-effort-summary.md) — gabungan **25 SP / ~29 mandays / 1 sprint** (baseline BUMA ID)

---

Dokumen ini mencakup **dua enhancement kecil** di alur Order yang dibundel jadi **satu rilis** karena masing-masing di bawah kapasitas 1 sprint:

- **Bagian A — Storage Location pada Create Order** (request MKP; tanpa toggle → berlaku semua tenant)
- **Bagian B — Planner Group pada Order Approval** (request MKP, 2 opsi)

Keduanya berasal dari **request MKP**.

---

# Bagian A — Storage Location pada Create Order

## A.1 Latar Belakang

**Request dari MKP** (konteks material master data — [MOM 09-Jul](../../../MKP-Project/2026-07-09-meeting-notes.md#L56)). Saat create order (eMOL), user memilih material lewat aksi **"Add Part"** — baik dari layar **"Order Details"** (Inspection) maupun block **"Order #N"** (Additional Order). Satu material bisa tersedia di **banyak Storage Location (Sloc)** — 9–11 Sloc per material menurut [MOM 09-Jul](../../../MKP-Project/2026-07-09-meeting-notes.md#L56).

**Kondisi sekarang (dikonfirmasi dari UI & data nyata, 21 Jul 2026):**

- Master `Material` (data dari SAP) sudah **multi-row per Sloc** — material yang sama muncul **berkali-kali** kalau ada di >1 Sloc. Kolom `StorageLocation` sudah ada di [maintenance-order-schema.md](../database/maintenance-order-schema.md#L140).
- Material list picker **sudah menampilkan duplikat per-baris** (tanpa dedup), tapi **tidak melabeli Sloc**. Akibatnya user melihat card yang tampak identik (Number/Description sama, hanya `Stock` yang beda) dan **tidak tahu material di Sloc mana** yang akan dipakai. Card sudah melabeli dimensi **Batch/valuation type** (mis. `NEW`/`REPAIRED`), tapi **Sloc belum**.
- **Endpoint list BE belum membawa** field Sloc (tidak diproyeksikan ke DTO).
- Transaksi `MechanicOrderMaterial` **tidak menyimpan** Sloc — field-nya cuma `MaterialNumber`/`Quantity`/`BatchCode`/dll ([maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md#L405-L421)). Sloc baru di-resolve otomatis saat insert `PoolingMOItem` (Step 2, match `Number+Description+BatchCode+SiteId+SectionTypeCode`) di [order-emol-sap-sync.md](order-emol-sap-sync.md#L186-L200). Karena 1 material bisa punya banyak Sloc, resolve ini **ambigu** dan berpotensi mengirim **Sloc arbitrer** ke SAP (bug data laten).

## A.2 Keputusan & Scope

| Aspek | Keputusan |
|---|---|
| Titik input | Saat **"Add Part"** di create order (per baris material), 2 jalur: "Order Details" (Inspection) & "Order #N" (Additional Order) |
| Perubahan UI | **Labeli Sloc** di tiap card material list — pola sama dengan label Batch (`NEW`/`REPAIRED`) yang sudah ada. Selection membawa Sloc baris terpilih |
| Platform | **Create order ada di Web & Mobile** (dikonfirmasi 22 Jul 2026) → picker material dikerjakan di **dua platform** (FE Web + FE Mobile) |
| Simpan di transaksi | **Kolom `StorageLocation` baru di `MechanicOrderMaterial`** — pola sama dengan `BatchCode` yang sudah tersimpan hari ini |
| Outbound ke SAP | Ganti auto-resolve Step 2 `PoolingMOItem` → pakai `MechanicOrderMaterial.StorageLocation` (pilihan user). Field `SLoc` & jalur ke SAP **tidak berubah** — cuma sumbernya. Sekaligus memperbaiki bug data laten (kirim Sloc arbitrer) |
| Toggle per tenant | **Tidak ada** — walau request dari MKP, ini perbaikan data/UX yang aman untuk semua tenant, jadi tidak di-gate per-tenant (keputusan user 21 Jul 2026) |
| Migrasi | **Forward-only** — order/eMOL lama tetap apa adanya (Sloc lama hasil auto-resolve) |
| Tidak perlu | Master data baru, permission baru, integrasi/sync material SAP baru (data Sloc sudah lengkap multi-row di Digiman+), field outbound baru |

## A.3 Open Items

**Tidak ada open item teknis tersisa** — status data (multi-row per Sloc) & grain list (sudah per-Sloc, tanpa dedup) sudah dikonfirmasi dari UI & DB. Sloc-sync SAP→Digiman **tidak perlu**.

---

# Bagian B — Planner Group pada Order Approval

**Related doc:** [order-emol-sap-sync.md](order-emol-sap-sync.md) *(Bagian 6.2 — mapping BAPI `GI_HEADER` existing, dasar analisa bagian ini)*

## B.1 Latar Belakang

Request berasal dari client **MKP**, dicatat di [MOM 01-Jul-2026](../../../MKP-Project/2026-07-01-meeting-notes.md) poin #34–35: saat create Maintenance Order (MO) ke SAP, ada field **Planner Group** yang perlu diisi. Saat ini **Digiman+ sama sekali tidak mengirim field ini** — dikonfirmasi dari review mapping BAPI `GI_HEADER` existing di [order-emol-sap-sync.md](order-emol-sap-sync.md#62-mapping-ke-bapi-sap-dilakukan-oleh-middleware) (`ORDER_TYPE`, `PLANT`, `EQUIPMENT`, `START_DATE`, `SHORT_TEXT`, `LONG_TEXT`, `ORDERID`, `PMACTTYPE`, `SYSTCOND` — Planner Group tidak ada di daftar ini).

### Konteks Teknis SAP (Referensi Umum)

- Planner Group di SAP PM adalah master data (tabel `T024I`), **di-scope per Maintenance Planning Plant** (site) — bukan kode global lintas plant.
- Secara standar, Planner Group **auto-derive dari Equipment** (yang biasanya inherit dari Functional Location) saat order dibuat. Field ini tetap **editable di order header** — override manual adalah behavior standar SAP, bukan workaround.
- **Dikonfirmasi user (21 Jul 2026):** di SAP BUMA ID, Planner Group memang auto-derive dari mapping Equipment, dan override manual aman dilakukan (tidak harus sama dengan hasil mapping).
- SAP **tidak punya validasi bawaan** yang mengaitkan Planner Group tertentu dengan pembatasan material/komponen. Kalau ada aturan seperti itu, itu di luar standar SAP (custom validation atau murni SOP).
- Planner Group di SAP juga lazim dipakai untuk **otorisasi** (authorization object `I_INGRP`) — assignment ke user lewat role (`PFCG`), bukan lewat field default di user master. Karena itu, "planner group milik user" secara SAP artinya "grup yang boleh dia kerjakan" (authorization), bukan identitas/default tunggal.

### Kebutuhan Bisnis MKP

- Planner Group **K01** adalah milik **dispatcher** — order dengan Planner Group ini **tidak boleh pakai material** (aturan bisnis MKP, lihat B.2 Opsi 2).
- Planner (user) bisa punya lebih dari satu Planner Group.

### Catatan Penting

Digiman+ adalah platform yang dipakai lintas client — **enhancement apapun di sini berdampak ke semua tenant**, bukan cuma MKP. Desain di bawah ini disusun supaya tenant yang tidak butuh fitur ini (mis. BUMA) tidak terdampak sama sekali.

## B.2 Keputusan & Scope

Ada dua opsi yang akan dipresentasikan ke client sebagai pilihan (lihat catatan penting di 2.3 sebelum menganggap keduanya setara/interchangeable).

### 2.1 Opsi 1 — Auto-Derive dari Equipment (SAP/Interface Side)

- **Effort Digiman+: 0** — tidak ada perubahan apapun di Digiman+. Field Planner Group tetap tidak dikirim (behavior sekarang), dan SAP yang menentukan nilainya dari mapping Equipment.
- **Konsekuensi:** Planner Group order 100% mengikuti hasil mapping Equipment di SAP, terlepas dari siapa atau proses apa yang membuat order tersebut. Skenario planner dengan >1 Planner Group jadi tidak relevan — identitas/pilihan planner tidak pernah dipakai untuk menentukan nilai ini.
- **Open item — perlu dikonfirmasi tim SAP MKP:**
  1. Apakah semua Equipment sudah termap ke Planner Group (tidak ada Equipment yang belum termap)?
  2. Apakah kode **K01** termap ke Equipment tertentu, atau tidak ada mapping Equipment untuk itu sama sekali?

### 2.2 Opsi 2 — Input Eksplisit di Digiman+ (Approval Planner)

| Aspek | Keputusan |
|---|---|
| Titik input | Saat **approval oleh Planner** (bukan saat create eMOL/order) |
| Platform | Master Data Planner Group = **Web admin saja**; **Order Approval ada di Web & Mobile** (dikonfirmasi 22 Jul 2026) → dropdown approval dikerjakan di **dua platform** |
| Wajib/opsional | **Mandatory** — approval tidak bisa lanjut tanpa mengisi Planner Group |
| Visibility fitur | **Toggle on/off per tenant** — satu flag, berlaku sama untuk semua site di bawah tenant tsb (bukan per site) |
| Master data Planner Group | Entity baru, **di-scope per Site**, **maintain manual lewat UI Admin** — bukan sync API dari SAP (eksplisit di luar scope saat ini) |
| Filtering dropdown | Difilter berdasarkan **Site user yang sedang login**. Aman dipakai karena approval order saat ini sudah dibatasi **per site per section** — tidak ada skenario approval lintas-site (dikonfirmasi user 21 Jul 2026) |
| Filtering tambahan by planner | **Tidak ada** — dropdown menampilkan semua Planner Group untuk site tsb, tidak dibatasi ke grup yang jadi hak planner yang approve |
| Enforcement rule K01/material | **Tidak dibangun di Digiman+** — tetap ditangani lewat SOP manual, di luar scope sistem |
| Outbound ke SAP | Digiman+ publish field baru **`PlannerGroup`** di payload outbound (message bus). Mapping ke field BAPI SAP aktual (`GI_HEADER`) jadi tanggung jawab middleware — di luar scope dokumen ini, konsisten dengan pola field lain yang sudah publish-only di [order-emol-sap-sync.md](order-emol-sap-sync.md#62-mapping-ke-bapi-sap-dilakukan-oleh-middleware) |

### 2.3 Catatan: Dua Opsi Ini Tidak Serta-Merta Saling Menggantikan

Opsi 1 dan Opsi 2 berpotensi menjawab kebutuhan yang berbeda, tergantung jawaban open item 2.1:

- Kalau K01 **memang murni atribut Equipment** (equipment tertentu selalu default ke K01, apapun proses pembuatan order-nya), Opsi 1 sudah cukup — tidak perlu Opsi 2 sama sekali.
- Kalau K01 **terkait proses pembuatan order** (mis. khusus order dari jalur dispatcher/SEMAR unscheduled, bukan equipment-nya), Opsi 1 tidak akan bisa membedakan itu — order untuk equipment yang sama akan selalu dapat Planner Group yang sama, siapapun/proses apapun yang membuatnya. Opsi 2 diperlukan untuk kasus ini.

Keputusan final antara "pilih salah satu" vs "kombinasi keduanya" diserahkan ke client MKP setelah open item 2.1 terjawab.

## B.3 Open Items

| # | Item | Terkait |
|---|---|---|
| 1 | Kelengkapan mapping Equipment → Planner Group di SAP MKP (apakah ada yang belum termap) | Opsi 1 |
| 2 | Status mapping Equipment untuk kode K01 (termap ke equipment tertentu atau tidak sama sekali) | Opsi 1, juga menentukan relevansi Opsi 2 (lihat 2.3) |

---

## Effort & Tim Eksekusi

Estimasi effort (baseline tim BUMA ID + skenario tim baru "BUMA ID Modified") ada di **[storage-location-planner-group-effort-summary.md](storage-location-planner-group-effort-summary.md)**. Ringkas:

- **Storage Location:** 10 SP / ~12 mandays
- **Planner Group:** Opsi 1 = **0 SP**; Opsi 2 = **15 SP / ~18 mandays**
- **Gabungan (Storage Location + Planner Group Opsi 2):** **25 SP / ~29 mandays** → **1 sprint** (baseline BUMA ID); **~3 sprint** kalau tim baru "BUMA ID Modified" (lihat effort summary).

**Catatan tim eksekusi:** tim technical yang akan mengeksekusi (baik di sisi MKP maupun BTech) **belum ditentukan** (lihat [MOM 01-Jul-2026](../../../MKP-Project/2026-07-01-meeting-notes.md) poin #10) — baseline BUMA ID dipakai sebagai **referensi** estimasi, bukan commitment tim. **Mapping BAPI** (agar `PlannerGroup` sampai ke field SAP aktual) tetap di luar scope, tanggung jawab middleware.

---

## Referensi

- [storage-location-planner-group-effort-summary.md](storage-location-planner-group-effort-summary.md) — estimasi effort gabungan (metodologi BUMA ID + skenario tim baru)
- [order-emol-sap-sync.md](order-emol-sap-sync.md) — flow eMOL→SAP, insert `PoolingMOItem` (Step 5.2, resolve SLoc), mapping BAPI `GI_HEADER` existing (Bagian 6.2)
- [maintenance-order-schema.md](../database/maintenance-order-schema.md) — schema `Material` (`StorageLocation`), `MechanicOrderMaterial`, `PoolingMOItem`
- [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) — layar create order ("Order #N" / "Order Details", "Add Part"), mapping `MechanicOrderMaterial`
- [MOM 2026-07-09](../../../MKP-Project/2026-07-09-meeting-notes.md) — poin #7 (struktur material: 5 Batch/valuation type, 9–11 Sloc)
- [MOM 2026-07-01](../../../MKP-Project/2026-07-01-meeting-notes.md) — asal request Planner Group (#34–35), status tim technical (#10)
