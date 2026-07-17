# Enhancement: Maintenance Activity Type & Rapikan Integrasi Inspection→Order

*Last updated: 2026-07-17*

---

**Feature:** Inspection & Order (Digiman+)
**Related doc:** [order-emol-sap-sync.md](order-emol-sap-sync.md) *(schema & flow existing yang jadi dasar enhancement ini — Bagian 4.2 khususnya)*, [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) *(enhancement lain yang menyentuh layar sama persis — lihat Bagian 6)*

> **Scope dokumen ini (dikonfirmasi 15 Jul 2026)**: sengaja digabung jadi **satu dokumen**, dua tujuan sekaligus — (1) redesign sourcing PM Activity Type → "Maintenance Activity Type" (Bagian 2.1–2.8), dan (2) **merapikan integrasi Inspection→Order secara umum** (Bagian 2.9: relasi `WorkOrder`/`TaskPersonalized`↔`MechanicOrderSummary`/`MechanicOrderList`, hapus ketergantungan cross-service call yang tidak perlu). Kedua tujuan ini saling terkait erat (ditemukan saat menganalisa yang pertama), jadi tidak dipisah jadi dokumen lain.

> Dokumen ini hasil **diskusi desain internal** (14–15 Jul 2026), bukan hasil meeting business yang sudah final seperti [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md). Beberapa keputusan di sini (skema, penamaan) sudah cukup matang untuk didokumentasikan, tapi **belum divalidasi ke tim technical/engineer** yang pegang codebase `maintenance-order`, dan **belum dikonfirmasi ke business/client** — lihat Bagian 5 Open Items.

---

## 1. Latar Belakang

Saat menganalisa alur sync Order-eMOL ke SAP ([order-emol-sap-sync.md](order-emol-sap-sync.md) Bagian 4.2), ditemukan bahwa sumber data **`PMActType`** (PM Activity Type) punya dua masalah:

1. **Konflasi dua konsep bisnis yang berbeda** — untuk eMOL tipe Inspection, `PMActType` saat ini **auto-derive** dari `WorkOrder.MaintenanceCategory.Code` (cross-service call BE `maintenance-order` → `maintenance-execution`). Tapi `WorkOrder.MaintenanceCategoryCode` (mis. `INP`, `IH04`, `SCH`) merepresentasikan **jenis pekerjaan yang sedang dieksekusi** (Inspection, Scheduled Service, dst) — konsep yang **tidak wajib terkait SAP/ERP sama sekali**, scope-nya luas (`maintenance-execution` = tempat eksekusi apapun jenis pekerjaannya). Sementara PM Activity Type seharusnya adalah **keputusan yang diambil di titik Order**, ditentukan dari **severity/kriteria finding** (minor/major, dst) — bukan diturunkan dari jenis job eksekusinya. Desain lama men-treat dua axis ini seolah sama, padahal secara bisnis keduanya independen.
   - **⚠️ Dampak nyata (dikonfirmasi user, 17 Jul 2026)**: karena salah-derive ini, kombinasi **Order Type** (`CostTypeCode`) + **PM Activity Type** yang terkirim ke SAP bisa jadi **kombinasi yang tidak valid** (SAP/BAPI reject kombinasi tsb) — akibatnya **integrasi create MO ke SAP gagal**. Ini bukan cuma masalah fleksibilitas/desain, tapi **root cause kegagalan integrasi produksi** — jadi motivasi bisnis utama enhancement ini, bukan sekadar generalisasi penamaan (poin 3).
2. **Grain tidak konsisten** — untuk eMOL tipe Additional, `PMActType` disimpan di **level header** (`MechanicOrderSummary.MaintenanceCategoryCode`, field "Activity Type" di screen 1 Asset Details), sementara untuk tipe Inspection levelnya per-WO (lewat cross-service call). Keduanya beda level dari `CostTypeCode` (Order Type) yang **konsisten selalu per-eMOL**.
3. **Penamaan terlalu SAP-minded** — `PMActType`/"PM Activity Type" adalah istilah SAP Plant Maintenance. Kalau Digiman+ diimplementasi ke client non-mining/non-SAP, istilah ini tidak applicable secara langsung.

Enhancement ini membetulkan ketiga hal di atas sekaligus: **memisahkan** axis eksekusi (`WorkOrder`, tetap di `maintenance-execution`, ERP-agnostic) dari axis order (`maintenance-order`, spesifik untuk artifact yang dibuat ke ERP/SAP), **menyeragamkan grain** ke per-eMOL, dan **menggeneralisasi penamaan** — dengan motivasi utama **menghentikan kegagalan create MO ke SAP** akibat kombinasi Order Type/Activity Type yang salah (poin 1 di atas), bukan sekadar rapi-rapi arsitektur.

---

## 2. Keputusan & Scope

### 2.1 Penamaan: "Maintenance Activity Type"

- Field **`PMActType`/"PM Activity Type"** diganti istilah generik **"Maintenance Activity Type"** — drop prefix "PM" (SAP Plant Maintenance) supaya tidak SAP-minded, tapi tetap jelas maksudnya (aktivitas maintenance apa yang perlu dilakukan).
- **Istilah yang dipertimbangkan tapi ditolak** (dicatat supaya tidak dibahas ulang):
  - **"Work Order"** — ditolak. Sudah dipakai untuk entity berbeda (`WorkOrder` di `maintenance-execution`, scope eksekusi luas & ERP-agnostic) — beda scope dari Order/`maintenance-order` yang spesifik untuk artifact ke ERP/SAP (lihat Bagian 1).
  - **"eMOL"** — ditolak untuk penamaan field baru ini (meski istilah itu sendiri tetap valid untuk entity `MechanicOrderList`). "Mechanic" di eMOL juga istilah sempit (mining/heavy-equipment-minded), sama masalahnya dengan "PM".

### 2.2 Level Data: Per-eMOL, Seragam untuk Inspection & Additional

- `Maintenance Activity Type` dipilih **manual oleh user, per eMOL**, tepat setelah memilih **Order Type** — berlaku **sama** untuk eMOL tipe Inspection maupun Additional. Ini menghapus percabangan logic yang didokumentasikan di [order-emol-sap-sync.md](order-emol-sap-sync.md) 4.2 (tabel "Sourcing berbeda tergantung tipe eMOL").
- **Inspection**: **tidak ada default/pre-fill** dari `WorkOrder.MaintenanceCategory.Code`. Cross-service call `GetWorkOrderById` kemungkinan masih dipakai untuk field lain (mis. Equipment) — perlu dicek, tapi **tidak lagi** jadi sumber `Maintenance Activity Type` (lihat Bagian 5 Open Items).
- **Additional**: field lama di screen 1 Asset Details ("Activity Type", backed oleh `MechanicOrderSummary.MaintenanceCategoryCode`) **dihapus total** dari screen tersebut. Kolom `MaintenanceCategoryCode`/`MaintenanceCategoryName` di `MechanicOrderSummary` dibiarkan ada di DB (forward-only, lihat 2.6) tapi tidak lagi diisi lewat UI.
  - **Dikonfirmasi (15 Jul 2026)**: dropdown "Activity Type" ini sumbernya endpoint `GET /api/workorder/inspection/offline/dropdown/maintenancecategory` (memanggil `MaintenanceExecAPI.GetWorkOrderAsync`) — lihat audit dampak endpoint lengkap di 2.11.
- **Wajib isi (mandatory)** sebelum submit — untuk kedua tipe eMOL.

### 2.3 Opsi Dropdown: Dependent terhadap Order Type

- Opsi `Maintenance Activity Type` yang ditampilkan **difilter berdasarkan Order Type** (`CostTypeCode`/`MaterialCostType`) yang sudah dipilih user — bukan daftar independen. Butuh mapping **many-to-many** baru: 1 Order Type bisa punya beberapa Activity Type valid, dan 1 Activity Type bisa berlaku untuk beberapa Order Type.
- **Alasan M:N (bukan 1:N)**: fleksibilitas untuk client yang konvensi Order Type/Activity Type-nya belum diketahui, dan **belum tentu semua target SAP** — mapping ini murni data Digiman+ (per-tenant, lihat 2.4), independen dari BAPI/ERP spesifik manapun.
- **UX saat Order Type belum dipilih — diputuskan (15 Jul 2026): dropdown `Maintenance Activity Type` disabled.** User harus pilih Order Type dulu baru bisa membuka dropdown Activity Type — konsisten dengan sifatnya yang dependent/filtered (2.3).
- **Validasi wajib-isi saat submit — diputuskan (15 Jul 2026)**: divalidasi, dengan rekomendasi copy (English, konsisten Bahasa Inggris seperti field lain di layar yang sudah direview — "Order Type", "Part", dst):
  - **Error message (field kosong saat submit)**: `"Maintenance Activity Type is required."`
  - **Helper text saat dropdown disabled** (Order Type belum dipilih) — mengikuti pola placeholder existing di layar yang sama (mis. Order Type sendiri pakai "Choose material based on order type"): `"Select Order Type first"`
  - **Helper text saat dropdown enabled** (siap dipilih): `"Choose Maintenance Activity Type based on Order Type"`

### 2.4 Skema Data Baru

**`MaintenanceActivityType`** (master baru)
```
Id            ← PK, int identity
Code          ← unique constraint (BUKAN PK — beda dari MaterialCostType existing yang PK-nya Code/varchar)
Description
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```
- Per-tenant secara implisit — mengikuti arsitektur DB existing yang sudah isolated-per-tenant (sama seperti `MaterialCostType`, tidak perlu kolom `TenantCode` eksplisit).
- **Independen dari data master "maintenance activity" yang sudah ada di service `maintenance-strategy`** *(dikonfirmasi 14 Jul 2026)* — meski kemungkinan besar isinya overlap (contoh data BUMA ID yang dibahas berisi code seperti `INP`, `SCH`, `BEX` yang juga dipakai di `WorkOrder.MaintenanceCategoryCode`/`maintenance-execution`, sumber aslinya di `maintenance-strategy`), tabel ini **sengaja dibuat baru & lokal** di `maintenance-order`, bukan referensi cross-service. Konsekuensi: kalau data master di `maintenance-strategy` berubah, **tidak otomatis ter-reflect** di sini — perlu proses/governance terpisah untuk menjaga kedua list tetap selaras kalau memang harus (lihat Open Items).
- Kolom `TypeCode`/`IsPeriodicalService` yang ada di data master `maintenance-strategy` **sengaja tidak dibawa** ke tabel baru ini — di luar scope enhancement ini, mungkin dibahas terpisah nanti.

**`MaterialCostTypeActivityTypeMapping`** (junction M:N, nama sementara)
```
MaterialCostTypeCode       ← FK varchar → MaterialCostType.Code (PK asli tabel legacy tsb)
MaintenanceActivityTypeId  ← FK int → MaintenanceActivityType.Id
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```
> Tipe FK asimetris (varchar vs int) murni cerminan bahwa `MaterialCostType` (legacy) pakai Code sebagai PK, sementara `MaintenanceActivityType` (baru) pakai Id — bukan inkonsistensi baru yang diperkenalkan enhancement ini.

**Perubahan ke `MechanicOrderList`** (existing table — struktur real dikonfirmasi 15 Jul 2026)
```
Id                          PK, bigint, not null
CostTypeCode                varchar(64), null
WorkOrderId                 bigint, null            ← TETAP diisi seperti sekarang (2.9, additive — tidak di-drop)
TaskPersonalizedFindingId   bigint, null            ← TETAP diisi seperti sekarang (2.9, additive — tidak di-drop, sama seperti WorkOrderId)
MechanicOrderSummaryId      bigint, null
Number                      varchar(200), not null
EDD                         datetime, not null
Status                      varchar(200), null
Type                        varchar(200), null       ← 'Inspection' | 'Additional'
DeleteReason                varchar(max), null
NoPartsRequired             bit, not null
CompletedBy                 varchar(200), null
CompletedDate                datetime, null
IsActive                    bit, not null
CreatedBy/CreatedAt, ModifiedBy/ModifiedAt

+ MaintenanceActivityTypeCode   ← BARU, varchar(64) (samakan tipe dgn CostTypeCode), wajib diisi sebelum submit
```
- **Menyimpan value (Code), bukan FK Id** — sejajar pola `CostTypeCode` yang sudah ada di tabel yang sama, dan konsisten dengan prinsip "data transaksi disimpan by value, bukan by ID reference" yang sudah ditetapkan di [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) 2.2 untuk Component/Sub Component/Area. Konsekuensinya sama: kalau master data `MaintenanceActivityType` berubah/dihapus di kemudian hari, eMOL historis tidak terpengaruh.

**`MechanicOrderDetail`** (existing table — struktur real dikonfirmasi 15 Jul 2026, **tidak diubah** oleh enhancement ini, dicatat sebagai referensi)
```
Id                       PK, bigint, not null
MechanicOrderListId      bigint, null
ComponentCode            varchar(64), null
SubComponentCode         varchar(64), null
OtherSubComponentName    varchar(512), null
DamageCode               varchar(64), null
CauseCode                varchar(64), null
RatingCode               varchar(64), null
ActionRemedyCode         varchar(64), null
PriorityCode             varchar(64), null
DefectNotes              varchar(1024), null
RepairDuration           float, null              ← field "How Long Will This Defect Repair Take?" (Duration, lihat 2.5)
RepairInstruction        varchar(200), null
IsActive, CreatedAt/By, ModifiedAt/By
```
- **Temuan penting**: kolom defect info (Component/SubComponent/DamageCode/CauseCode/ActionRemedy/Priority/DefectNotes/RepairDuration) **sudah tersedia** di sini, terlepas dari `Type` eMOL-nya. Ini menjawab pertanyaan terbuka soal "apakah data Finding perlu di-copy juga seperti WorkOrder" (lihat 2.9) — kemungkinan besar **sudah** dilakukan lewat tabel ini (snapshot, bukan live-query ke Finding), jadi bukan scope baru.
- **`RatingCode`, `OtherSubComponentName`, `RepairInstruction`** — belum pernah muncul di screenshot/diskusi manapun sejauh ini. Dicatat sebagai observasi, fungsinya belum diketahui, di luar scope enhancement ini.

**`PoolingMOItem`** (existing table, [order-emol-sap-sync.md](order-emol-sap-sync.md) 5.2) — **tidak di-rename**
```
PMActType   ← tetap nama ini, sekarang diisi langsung dari mol.MaintenanceActivityTypeCode
```
- **Prinsip**: generic naming di layer bisnis (`MechanicOrderList`, master data baru), nama SAP-spesifik tetap dipertahankan di *boundary* integrasi (`PoolingMOItem`, mapping BAPI). `PoolingMOItem` memang staging table khusus SAP sync — wajar "berbicara bahasa SAP" di titik itu. Kalau nanti ada client non-SAP, cukup tambah *boundary* integrasi baru tanpa sentuh model bisnis inti (`MechanicOrderList`/`MaintenanceActivityType`).
- Populate logic jadi lebih simpel: copy langsung `mol.MaintenanceActivityTypeCode`, sama pola dengan `MOType` yang sudah copy langsung dari `mol.CostTypeCode` hari ini — tidak perlu lagi resolve `@MaintenanceCategoryCode` lewat percabangan logic (4.2 lama).

### 2.5 UI Changes

**Screen 1 — Additional Order, "Assets Details"**

| Sebelum | Sesudah |
|---|---|
| Asset Model*, Asset Number*, **Activity Type*** (3 field) | Asset Model*, Asset Number* (Activity Type dihapus total) |

**Screen 2 — per block "Order #N"** *(rename dari "Material Order #N", lihat Bagian 3)*

Urutan field per block (Additional Order), field baru **ditebalkan**:

```
Evidence (photo upload)
Defect Information: Component & Sub Component*, Damage Code*, Cause Code,
                     Action Remedy*, Priority*, Defect Notes,
                     How Long Will This Defect Repair Take?*
No Parts Required declaration (checkbox)
Order Type*
→ Maintenance Activity Type* (BARU — di bawah Order Type, opsi filtered by Order Type)
Part* (Add Part)
```

> `"How Long Will This Defect Repair Take?"` di atas **sudah dikonfirmasi** adalah field **Duration** dari [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) — sudah **live** (bukan rencana). Untuk Inspection, Duration **sudah direcord sejak create finding** (konsisten dengan [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) 2.3: "Saat create finding (Inspection), saat ini sudah ada field Component, Sub Component, dan Duration"). Dicatat di sini sebagai cross-reference, bukan scope enhancement ini.

**Screen "Order Details" — create/complete eMOL dari Inspection** *(direview 14 Jul 2026)*

Strukturnya **beda dari Additional Order** dalam satu hal penting: `Defect Information` (Component & Sub Component, Damage Group & Damage Code, Cause Group & Cause Code, Action Remedy, Finding Images, Defect Notes) tampil **terpisah dan read-only** di atas — datanya carry-forward dari Finding yang sudah direkam saat Inspection, bukan input baru. Section di bawahnya (yang menampung Order Type + Part) **cuma berisi Order Type + Part** — tidak digabung dengan defect info seperti block "Order #N" Additional Order, karena tidak perlu (Finding sudah ada duluan).

Tidak ada penomoran `#1`/`#2` di screen ini — tiap finding sudah punya screen "Order Details" sendiri-sendiri (diakses lewat tombol "Order" per finding card di list WorkOrder Inspection), jadi konteksnya otomatis 1 finding = 1 screen.

```
[Read-only] Defect Information: Component & Sub Component, Damage Group & Damage Code,
            Cause Group & Cause Code, Action Remedy, Finding Images, Defect Notes
No Parts Required declaration (checkbox)
Order Type*
→ Maintenance Activity Type* (BARU — di bawah Order Type, opsi filtered by Order Type)
Part*
```

- Section header **"Material Order" → "Order"** (rename, tanpa `#N` karena singular/konteksnya sudah 1 finding) — alasan sama dengan Bagian 3: "Material" terlalu sempit, apalagi setelah `Maintenance Activity Type` masuk ke section ini.
- Tombol submit di screen ini berlabel **"Complete Order"** (beda label dari "Preview"/"Create" di Additional Order) — dikonfirmasi ini **flow yang sama**, cuma beda label saja, bukan state/behavior berbeda. **Dibiarkan as-is** — bukan bagian dari scope enhancement ini untuk diseragamkan.

### 2.6 Migrasi: Forward-Only

- **Tidak ada backfill** untuk eMOL/Order yang sudah ada. Order lama (sudah pakai `MechanicOrderSummary.MaintenanceCategoryCode` untuk Additional, atau sudah sync pakai nilai dari WO untuk Inspection) **tetap apa adanya** — enhancement ini hanya berlaku untuk Order/eMOL baru yang dibuat setelah rilis.
- Kolom `MechanicOrderSummary.MaintenanceCategoryCode`/`MaintenanceCategoryName` **tidak di-drop** — dibiarkan ada untuk histori, cuma berhenti diisi lewat UI baru.

### 2.7 Scope Terpisah dari MO Backlog Filter

[order-emol-sap-sync.md](order-emol-sap-sync.md) 9.1 menyebut MO Backlog filter (menentukan MO mana yang ditarik balik dari SAP jadi backlog) juga berbasis "Order Type tertentu + PM Activity Type tertentu" per-client — ini **sengaja dibuat tetap sebagai konfigurasi terpisah**, bukan digabung dengan mapping M:N di Bagian 2.4, karena tujuannya beda:

| | Mapping M:N (2.3–2.4, enhancement ini) | MO Backlog Filter (9.1, existing) |
|---|---|---|
| Tujuan | Filter opsi yang **boleh dipilih user** saat create eMOL | Filter MO mana yang **ditarik balik** jadi backlog dari SAP |
| Titik pakai | Data-entry (create Order/eMOL) | Inbound sync (SAP → Digiman+) |

Kalau di masa depan mau digabung (mis. tambah kolom flag `IsEligibleForBacklogPull` di `MaterialCostTypeActivityTypeMapping`), itu **keputusan terpisah** yang perlu didiskusikan ulang — dicatat di sini supaya tidak digabung tanpa sadar.

### 2.8 Order Approval Checkpoint

- **`Maintenance Activity Type` tetap bisa diedit oleh SPV saat Order Approval** *(dikonfirmasi 14 Jul 2026)* — perlakuan **sama seperti Order Type** yang sudah editable di titik approval. Konsisten dengan pola Component/Sub Component/Area/Duration/Man Power yang juga validated & editable di checkpoint yang sama ([area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) 2.6) — SPV jadi checkpoint terakhir sebelum data dikirim ke SAP untuk field ini juga.
- Aturan wajib-isi (2.3) & dependent-terhadap-Order-Type (2.4) berlaku sama di titik approval ini — bukan form terpisah yang lebih longgar.

### 2.9 Relasi WorkOrder → Order Disederhanakan

*(Muncul saat membahas Open Item "cross-service call `GetWorkOrderById`" — scope-nya lebih luas dari sekadar Activity Type, jadi bagian resmi dari dokumen ini setelah scope diperluas 15 Jul 2026, lihat header dokumen.)*

**Trigger persis (dikonfirmasi 15 Jul 2026)**: integrasi Inspection→Order **sudah ada** hari ini, terjadi saat **masing-masing mechanic** menekan **"Sign and Finish" (Submit)** pada inspeksinya — bukan 1 aksi submit tunggal di level WorkOrder. Karena `TaskPersonalized` levelnya **per-mechanic** (1 Task = N `TaskPersonalized`, lihat kardinalitas di skema bawah), tiap kali 1 mechanic Sign and Finish, itu men-submit **`TaskPersonalized` milik mechanic itu sendiri** — dan proses itulah yang membentuk `MechanicOrderList`/`MechanicOrderDetail`/`MechanicOrderEvidence` dari `TaskPersonalizedFinding`-nya. Ini menegaskan kenapa data `TaskPersonalized.UserCode`/`MachineSMUValue` (calon `InspectorCode`/`HourMeter`) **pasti tersedia** di titik itu — proses submit itu sendiri **adalah** proses per-`TaskPersonalized`, jadi tidak butuh lookup/call tambahan ke entity lain.

**Kualifikasi trigger (dikonfirmasi 15 Jul 2026)**: proses copy per-Finding di atas **tidak berlaku untuk semua Finding** — kalau `TaskPersonalizedFinding.IsImmediateExecutable = True` (defect sudah diperbaiki langsung saat inspeksi, quick fix), Finding tsb **tidak menghasilkan eMOL/Order sama sekali**. Jadi "Sign and Finish" membentuk eMOL **per-Finding yang butuh Order** (immediately-executable dikecualikan), bukan otomatis 1:1 untuk semua Finding di `TaskPersonalized` itu.

**Implikasi ke resolusi `HourMeter` (2.10 tabel field)**: karena tiap mechanic submit di waktu yang bisa berbeda-beda (async, tidak barengan), dan `MechanicOrderSummary` (header, 1 per WorkOrder) kemungkinan **sudah dibuat** oleh submit mechanic pertama sebelum mechanic kedua/ketiga submit — aturan **"ambil dari yang pertama kali diinput"** yang sudah diputuskan sebelumnya secara konkret berarti: **`HourMeter` di header diisi sekali, dari submit mechanic PERTAMA yang membuat `MechanicOrderSummary`-nya** — submit mechanic berikutnya (kalau `MechanicOrderSummary` sudah ada) **tidak menimpa** nilai itu, walau `MachineSMUValue` di `TaskPersonalized` mereka beda.

**✅ `MechanicOrderSummary.CreatedBy` — terjawab (17 Jul 2026)**: pola sama persis dengan `HourMeter` di atas — diambil dari mechanic yang **pertama kali** Sign and Finish (yang membuat `MechanicOrderSummary`-nya). Mechanic berikutnya yang Sign and Finish untuk `WorkOrder` yang sama **tidak** mengubah `CreatedBy` header (karena baris `MechanicOrderSummary`-nya sudah ada, cuma nambah baris `MechanicOrderList` baru di bawahnya).

**⚠️ Timing trigger Workflow Approval — temuan baru (17 Jul 2026), belum pernah tercatat sebelumnya**: contoh skenario konkret dari user — 1 `WorkOrder` di-assign ke 3 mechanic (A, B, C). Mechanic A Sign and Finish paling pertama, lalu **langsung bisa create Order** dari finding-nya sendiri (hari yang sama). Mechanic B dan C baru Sign and Finish keesokan harinya, lalu masing-masing create Order dari finding mereka sendiri (B duluan, baru C). **Workflow approval baru ter-trigger saat mechanic C submit Order-nya — yaitu submit Order yang PALING TERAKHIR dari ketiga mechanic**, bukan saat Order pertama (milik A) dibuat. Jadi:
- `MechanicOrderList` bertambah **incremental** seiring tiap mechanic submit Order-nya sendiri (async, bisa beda hari) — konsisten dengan `MechanicOrderSummary` yang sudah dibuat lebih dulu oleh mechanic pertama (A).
- `WorkflowTransaction` (approval) **tidak** dibuat/di-trigger saat Order pertama submit — baru muncul setelah **submit Order terakhir** dari seluruh mechanic yang di-assign ke `WorkOrder` tersebut.
- **⚠️ Mekanisme deteksi "submit Order terakhir" — dibuka lagi (17 Jul 2026), sempat ditandai terjawab tapi dikoreksi user sendiri**: sempat disimpulkan cukup cek **`MechanicOrderList.Status`** — kalau seluruh baris existing dengan `WorkOrderId`/`MechanicOrderSummaryId` yang sama sudah `Complete`, trigger `WorkflowTransaction`. **Ini tidak cukup** — ada celah waktu (gap) di mana sebagian mechanic yang di-assign ke `WorkOrder` yang sama **belum Sign and Finish sama sekali** (belum submit inspeksinya), sementara mechanic lain sudah submit Order duluan. Kalau logic cuma cek "baris `MechanicOrderList` yang **sudah ada** semuanya `Complete`", itu bisa salah trigger prematur — karena mechanic yang belum Sign and Finish **belum punya baris `MechanicOrderList` sama sekali** untuk dicek, bukan baris dengan status lain (`Pending`/`In Progress`). Kemungkinan logic sebenarnya perlu juga mempertimbangkan status `TaskPersonalized` (siapa saja yang sudah Sign and Finish) dari seluruh mechanic yang di-assign, bukan cuma `MechanicOrderList.Status` dari baris yang kebetulan sudah terbentuk.
  > **Tambahan nuance (17 Jul 2026)**: `TaskPersonalized` juga punya kolom `IsActive` — assignment ke seorang mechanic bisa **di-cancel/dihapus** (`IsActive=0`). Kalau logic penghitungan "berapa mechanic yang di-assign, sudah berapa yang submit" tidak filter `IsActive=1`, assignment yang sudah di-cancel bisa membuat perhitungan **macet permanen** (nunggu submit dari mechanic yang assignment-nya sudah tidak berlaku, tidak akan pernah submit). Jadi logic yang benar kemungkinan perlu: `TaskPersonalized WHERE IsActive=1` sebagai basis "siapa saja yang masih valid harus submit", bukan seluruh histori assignment.
  >
  > **Belum ada jawaban final** untuk keseluruhan mekanisme ini — perlu dicek ke engineer, dicatat ulang sebagai open item (5.1).
  > Submitter yang tercatat di `WorkflowTransaction` (calon sumber `CreatedBy`/aktor pemicu saat trigger) tetap dipahami sebagai **user yang submit Order terakhir** — bagian ini belum dikoreksi, cuma mekanisme deteksi "terakhir"-nya yang masih perlu diperjelas.

**⚠️ Implikasi arsitektur penting (17 Jul 2026)**: kalau logic deteksi "submit terakhir" di atas memang perlu cek status `TaskPersonalized` (bukan cuma `MechanicOrderList.Status`), **ini jadi satu-satunya titik yang belum bisa 100% menghilangkan cross-service call ke `maintenance-execution` saat proses Order** — berbeda dari semangat "additive, snapshot cukup" yang jadi prinsip di seluruh 2.9/2.11. Alasannya: data status mechanic yang **belum** Sign and Finish (masih pending) **tidak pernah ter-snapshot** ke Order DB — snapshot (`MechanicOrderList`/`MechanicOrderSummary`) cuma terbentuk **setelah** mechanic submit, jadi tidak ada cara untuk tahu "masih ada berapa mechanic yang belum submit" tanpa nanya balik ke `maintenance-execution` (baca `TaskPersonalized.Status` untuk seluruh mechanic yang di-assign ke `WorkOrder`/`Task` itu). Ini beda karakter dari temuan di 2.11 poin D (yang murni redundan, bisa dihapus) — cross-service call di sini **struktural diperlukan**, bukan sekadar optimisasi yang belum dilakukan. Perlu dikonfirmasi ke engineer apakah pemahaman ini benar, dan kalau ya, dicatat sebagai pengecualian eksplisit dari prinsip audit di 2.11.

**Konteks penting**: Inspection, PM Shutdown, BD Corrective, dan Form Submission adalah **fitur berbeda tapi satu service** (`maintenance-execution`), dan datanya tersimpan di **tabel-tabel yang sama** dengan pola yang sama — bukan struktur terpisah per fitur. Jadi skema di bawah (dari [`form-submission.md`](../form/form-submission.md), `cst-iams-sqldb-maintenance-execution`) berlaku langsung untuk konteks Inspection yang dibahas di dokumen ini juga.

**Hierarki real (dikonfirmasi 15 Jul 2026)**:
```
WorkOrder (1)
  └── Task (N)                       ← Task.WorkOrderId
        └── TaskPersonalized (N)     ← 1 record per mechanic per Task (TaskPersonalized.TaskId)
              └── TaskPersonalizedFinding (N)  ← "Finding" (TaskPersonalizedFinding.TaskPersonalizedId)
                    └── eMOL (1)      ← MechanicOrderList, 1 Finding = 1 eMOL
```

**Skema real (`maintenance-execution`)**:
```
WorkOrder: Id, TypeCode, PriorityCode, Number, PlanId, Description, ScheduleStartDate, DueDate,
           WorkType, Source, Status, StartDate, EndDate, AssetNumber, AssetModelCode, AssetModelName,
           MaintenanceCategoryCode, MaintenanceCategoryName, SectionTypeCode, SiteCode, Notes,
           TotalOSBacklog, IsActive, CreatedBy/At, ModifiedBy/At, ReferenceId, LastSyncedAt/By,
           LastSyncedModifiedAt/By

Task: Id, WorkOrderId, Name, Type, Status, Notes, IsActive, ReferenceId,
      LastSyncedAt/By, LastSyncedModifiedAt/By, CreatedAt/By, ModifiedAt/By

TaskPersonalized: Id, TaskId, UserCode, IsPrecautionConfirmed, MachineSMUValue, MachineSMUAddress,
                  Status, IsActive, CreatedAt/By, ModifiedAt/By, ReferenceId, LastSyncedAt/By,
                  LastSyncedModifiedAt/By

TaskPersonalizedFinding: Id, TaskPersonalizedId, FormSubmissionTabId, FormTaskCode, FormTaskNumber,
                          ComponentCode, SubComponentCode, OtherSubComponentName, DamageCode, CauseCode,
                          RatingCode, ActionRemedyCode, IsImmediateExecutable, PriorityCode, DefectNotes,
                          DeleteNotes, RepairDuration, RepairInstruction, IsActive, ReferenceId,
                          LastSyncedAt/By, LastSyncedModifiedAt/By, CreatedAt/By, ModifiedAt/By
```

> **Konfirmasi silang penting**: `TaskPersonalizedFinding` di atas **hampir identik kolom-per-kolom** dengan `MechanicOrderDetail` (3.3, [order-emol-sap-sync.md](order-emol-sap-sync.md)) — `ComponentCode`/`SubComponentCode`/`OtherSubComponentName`/`DamageCode`/`CauseCode`/`RatingCode`/`ActionRemedyCode`/`PriorityCode`/`DefectNotes`/`RepairDuration`/`RepairInstruction` semuanya sama persis. Ini **mengkonfirmasi pasti** (bukan lagi dugaan) bahwa `MechanicOrderDetail` adalah snapshot-copy dari `TaskPersonalizedFinding` saat eMOL dibuat — pola yang persis sama dengan yang diusulkan di bagian ini untuk WorkOrder/TaskPersonalized. `RatingCode`/`OtherSubComponentName`/`RepairInstruction` yang tadinya "belum diketahui fungsinya" sekarang jelas: cuma ikut ter-copy dari `TaskPersonalizedFinding`, tidak berarti dipakai aktif di UI Order. (`IsImmediateExecutable` dan `DeleteNotes` ada di `TaskPersonalizedFinding` tapi **tidak** ikut ter-copy ke `MechanicOrderDetail`.)

**Keputusan (15 Jul 2026, direvisi — additive, bukan replacement)**: awalnya diputuskan `WorkOrderId` dihapus sebagai FK aktif (forward-only, NULL untuk eMOL baru). **Ini dibatalkan** — arahan final: **`WorkOrderId` TETAP diisi seperti sekarang, tanpa perubahan apapun ke behavior insert existing.** Alasannya: kita tidak tahu API/service lain apa saja yang mungkin masih bergantung ke `MechanicOrderList.WorkOrderId` (lalu melakukan call sendiri ke `maintenance-execution` untuk ambil data WorkOrder) — men-drop insert behavior itu berisiko mem-break konsumen yang tidak kita ketahui. Field baru (`SourceWorkOrderId`/`SourceWorkOrderNumber`/`HourMeter`/`InspectorCode`/`InspectorName`) ditambahkan **murni additive** — mendampingi `WorkOrderId` yang sudah ada, bukan menggantikannya. `MechanicOrderList` tetap relasi lewat `WorkOrderId` **dan** `MechanicOrderSummaryId` seperti sekarang; tidak ada percabangan/kondisi yang dihapus dari query existing manapun.

**⚠️ Koreksi level data (15 Jul 2026, direvisi)** — usulan awal saya (copy `Inspector`/`HourMeter` ke `MechanicOrderSummary`, level header) sempat saya turunkan semua ke `MechanicOrderList` (per-eMOL) karena sumbernya `TaskPersonalized` (1 Task bisa N record, 1 per mechanic). Tapi ini **dikoreksi lagi**: `Inspector` dan `HourMeter` **beda karakter data**, meski sama-sama bersumber dari `TaskPersonalized` hari ini:
- **`Inspector`** — atribut *siapa yang mencatat finding ini*, secara alami bisa beda per finding/mechanic → tetap di `MechanicOrderList` (per-eMOL).
- **`HourMeter`** — atribut *state mesin* (pembacaan hour meter), dimaksudkan **1 nilai representatif untuk keseluruhan Order**, bukan atribut per-pencatat. Ini juga konsisten dengan arah desain Phase 1 (`TaskPersonalized`→`Task`, "1 nilai per service execution") — produk sendiri sudah menganggap grain per-mechanic untuk SMU itu yang perlu diperbaiki, bukan grain yang dituju. Jadi **`HourMeter` kembali ke `MechanicOrderSummary`** (header).

**Reframing (15 Jul 2026, setelah skema real `PoolingMOItem` dikonfirmasi & diklarifikasi lebih lanjut)**: `PoolingMOItem` — tabel staging SAP di `maintenance-order` — **sudah punya** kolom `HourMeter` (varchar(128)), `InspectorCode` (varchar(200)), `InspectorName` (varchar(100)), **dan `EquipmentModel`** (varchar(200)), tapi **dikonfirmasi (15 Jul 2026): kolom-kolom ini saat ini tidak dipakai, masih NULL**. Jadi bukan "mekanisme existing yang perlu diganti sumbernya" seperti dugaan awal — kolomnya sudah ada di skema tapi memang belum pernah diaktifkan/diisi. Enhancement ini yang **pertama kali mengisi kolom-kolom tsb**, lewat snapshot yang disiapkan di `MechanicOrderSummary`/`MechanicOrderList` saat Order dibuat. **`EquipmentModel` diputuskan ikut diisi juga (16 Jul 2026), meski tidak dikirim ke SAP** (6.2, sama seperti `HourMeter`/`Inspector`) — sumbernya lebih sederhana dari yang lain: `MechanicOrderSummary.AssetModelName` **sudah ada & sudah terisi** (existing behavior, 2.10), jadi cukup extend query insert 5.2 untuk ikut SELECT `mos.AssetModelName`, tidak perlu kolom snapshot baru.

**Konfirmasi alur (15 Jul 2026)**: **tidak perlu cross-service call baru**. `MechanicOrderList` (dan `MechanicOrderSummary`/`MechanicOrderDetail`/`MechanicOrderEvidence`) **sudah terbentuk langsung** begitu mechanic submit Inspection — artinya proses yang menangani submit itu **sudah** punya akses ke data `WorkOrder`/`TaskPersonalized`/`TaskPersonalizedFinding` di context yang sama saat itu juga (bukti: `MechanicOrderDetail`/`MechanicOrderEvidence` sudah snapshot-copy dari `TaskPersonalizedFinding`/`TaskPersonalizedEvidence` hari ini — proses copy itu sudah jalan). Jadi menambahkan `SourceWorkOrderId`/`SourceWorkOrderNumber`/`HourMeter`/`InspectorCode`/`InspectorName` tinggal **memperluas proses submit yang sudah ada** supaya ikut menyalin field-field itu juga — bukan membangun integrasi cross-service baru.

**Koreksi (15 Jul 2026): `Inspector` jadi 2 kolom terpisah** — `InspectorCode` dan `InspectorName`, menyamai struktur target `PoolingMOItem` yang sudah ada. Alasan: `TaskPersonalized.UserCode` cuma kode, nama perlu di-resolve terpisah (mis. dari master data User) — kalau cuma simpan Code, `InspectorName` di `PoolingMOItem` nanti butuh resolve ulang saat sync (balik ke masalah live-lookup yang mau kita hindari). Simpan keduanya sebagai snapshot sekaligus di titik Order dibuat.

Lengkap skema real `PoolingMOItem`: lihat [maintenance-order-schema.md](../database/maintenance-order-schema.md). ⚠️ **`PoolingMOItem.PMActType` cuma `varchar(5)`** — constraint penting: `MaintenanceActivityType.Code` (2.4) harus dijaga ≤5 karakter supaya tidak terpotong saat sync. Sample data BUMA ID yang sudah diterima (35 code, semua 3 karakter) aman terhadap constraint ini.

**⚠️ Koreksi (16 Jul 2026)**: sempat disimpulkan `HourMeter`/`InspectorCode`/`InspectorName` juga perlu ditambahkan ke payload SAP (query 5.5) — **ini salah, dikoreksi user**. Mapping BAPI SAP real yang dikonfirmasi user ([order-emol-sap-sync.md](order-emol-sap-sync.md) 6.2 — `GI_HEADER`/`GI_OPER`/`GI_COMP`) **tidak punya field `HourMeter`/`Inspector` sama sekali** — payload di 6.1 (`TopicPublishLog.MessagePayload`) itu superset yang dikonsumsi message bus, middleware cuma mapping subset field ke BAPI SAP (lihat catatan baru di 6.2). Kesalahan sebelumnya: menyimpulkan dari contoh payload 6.1 tanpa cross-check ke mapping BAPI 6.2 yang **sudah terdokumentasi** — pelajaran: field yang ada di payload message bus tidak otomatis berarti field itu sampai ke SAP.

Jadi mengisi `PoolingMOItem.HourMeter`/`InspectorCode`/`InspectorName` (di atas) **tetap valid sebagai scope** — kolomnya memang ada tapi belum pernah diisi, dan mengaktifkannya berguna untuk kelengkapan record staging `PoolingMOItem` itu sendiri — tapi **bukan** karena SAP butuh datanya. Hubungan field ini dengan mekanisme "BE enrichment" existing yang mengisi `Inspector`/`HourMeter` di payload message bus (6.1, sudah berjalan hari ini untuk `Inspector` — terlihat di contoh payload, `HourMeter` kebetulan kosong di contoh itu) **belum jelas** — apakah enrichment itu nanti perlu diubah untuk baca dari `PoolingMOItem` (konsisten dengan prinsip snapshot), atau tetap independen. **Perlu dicek developer**, dicatat sebagai open item (5.1).

**Field yang diusulkan, dengan level yang benar**:

| Kolom baru | Tipe *(dikonfirmasi 17 Jul 2026)* | Ditambah ke | Sumber | Catatan |
|---|---|---|---|---|
| `Source` | varchar(128) | `MechanicOrderSummary` (header) | Label asal Order — **3 nilai (direvisi 17 Jul 2026)**: `'Scheduled Inspection'` (Inspection reguler lewat jadwal), `'Additional Inspection'` (Inspection ad-hoc), `'Additional Order'` (bukan NULL lagi — punya nilai sendiri) | **Baru ditambahkan 17 Jul 2026**, di luar 5 field yang tadinya diusulkan. Didesain **extensible**: fitur lain yang nanti integrate ke Order (PM Shutdown, BD Corrective, Form Submission — lihat "Konteks penting" 2.9 di atas) kemungkinan pakai nama fitur masing-masing sebagai value. Melengkapi `SourceWorkOrderId`/`SourceWorkOrderNumber` di bawah — field itu nunjuk ID/Number WO asal, tapi tidak bilang WO itu dari jalur mana; `Source` yang menjawab itu. **✅ Cara membedakan `Scheduled Inspection` vs `Additional Inspection` — terjawab (17 Jul 2026)**: dari kolom **`WorkOrder.WorkType`** (kolom existing, lihat skema real 2.9) — nilainya `'Scheduled'` untuk Inspection reguler, `'Additional'` untuk Inspection ad-hoc. Ini yang dipakai untuk derive `MechanicOrderSummary.Source` (map ke `'Scheduled Inspection'`/`'Additional Inspection'`). *(Dua kandidat sebelumnya — `WorkOrder.Source` dan `WorkOrder.PlanId` — sama-sama salah/dugaan, dikoreksi user; `WorkType` adalah kolom yang benar.)* |
| `SourceWorkOrderId` | varchar(128) | `MechanicOrderSummary` (header) | `WorkOrder.Id` | 1:1 dengan Order — snapshot, dipakai buat field `WorkOrderId` di payload message bus (`TopicPublishLog.MessagePayload`, **bukan** payload BAPI SAP — lihat koreksi di atas) & `AttachmentUrl` deep link ([order-emol-sap-sync.md](order-emol-sap-sync.md) 6.1). **NULL untuk Additional Order.** *(Tipe varchar meski `WorkOrder.Id` aslinya numerik — konsisten pola snapshot-by-value, bukan FK aktif.)* |
| `SourceWorkOrderNumber` | varchar(128) | `MechanicOrderSummary` (header) | `WorkOrder.Number` — **confirmed ada**, bukan asumsi lagi | Untuk display "Order ini asal dari WO mana". **NULL untuk Additional Order.** |
| `HourMeter` | bigint | `MechanicOrderSummary` (header) | **Dua fase (dikonfirmasi 15 Jul 2026)**: (1) **Sekarang - sampai Phase 1 live**: `TaskPersonalized.MachineSMUValue`, ambil dari record **yang pertama kali diinput** (paling awal `CreatedAt`/nilai SMU-nya diisi) — resolusi untuk kasus 1 Task punya N `TaskPersonalized` dengan nilai berbeda. (2) **Setelah Phase 1 live**: `Task.MachineSMUValue` — 1 nilai per Task, ambiguitas otomatis hilang, tidak perlu logic "ambil yang pertama" lagi. | 1 nilai representatif untuk Order, bukan per-eMOL — lihat rationale di atas. Implementasi perlu switch sumber saat Phase 1 rilis. **NULL untuk Additional Order.** |
| `InspectorCode` | — *(tipe belum dikonfirmasi)* | **`MechanicOrderList`** (per-eMOL) | `TaskPersonalized.UserCode` | Bisa beda per eMOL — siapa yang mencatat finding tsb |
| `InspectorName` | — *(tipe belum dikonfirmasi)* | **`MechanicOrderList`** (per-eMOL) | Resolve dari `InspectorCode` (mis. master data User) saat Order dibuat | Disimpan sebagai snapshot terpisah, bukan di-resolve ulang saat sync — sejalan prinsip "value bukan reference" |

> **`PoolingMOItem.EquipmentModel`** (diputuskan 16 Jul 2026) — **bukan** kolom baru di `MechanicOrderSummary`/`MechanicOrderList` seperti 4 baris di atas. Sumbernya `MechanicOrderSummary.AssetModelName`, kolom yang **sudah ada & sudah terisi** hari ini (existing behavior, 2.10) — jadi cukup extend query insert `PoolingMOItem` (5.2, [order-emol-sap-sync.md](order-emol-sap-sync.md)) untuk ikut SELECT `mos.AssetModelName` → `EquipmentModel`, sama seperti aktivasi `HourMeter`/`InspectorCode`/`InspectorName`, tidak dikirim ke SAP (6.2) tapi diisi untuk kelengkapan record staging.

- `WorkOrder.MaintenanceCategory.Code` **sengaja tidak** diusulkan sebagai field yang di-copy untuk drive nilai apapun — itu sumber masalah yang enhancement ini hilangkan (2.2).
- **Konsekuensi struktural — disederhanakan (15 Jul 2026)**: proses "copy saat Order dibuat" menjangkau **3 level entity** di `maintenance-execution` (`WorkOrder` → header, `TaskPersonalized` → header `HourMeter` + per-eMOL `InspectorCode`/`InspectorName`, `TaskPersonalizedFinding` → per-eMOL/`MechanicOrderDetail` yang sudah ada) — tapi **tidak perlu cross-service call baru**, karena proses submit Inspection yang sudah ada hari ini **sudah** membentuk `MechanicOrderList`/`Summary`/`Detail`/`Evidence` langsung, dengan akses ke data 3 level itu di context yang sama. Tinggal perluas proses existing untuk ikut menyalin field tambahan ini.
- **`TaskPersonalizedFindingId` tetap diisi seperti sekarang, sama prinsipnya dengan `WorkOrderId`** — additive, tidak di-drop (lihat keputusan `WorkOrderId` di atas). Tetap dipakai untuk trace ke `TaskPersonalizedFinding`/`TaskPersonalized` asalnya kalau suatu saat perlu re-verify, meski data operasionalnya sudah snapshot ke `MechanicOrderDetail`.

> **Scope dokumen (15 Jul 2026)**: perubahan relasi WorkOrder↔Order ini memang lebih luas dari sekadar Activity Type (menyentuh `AttachmentUrl` deep link, payload SAP `WorkOrderId`, query 5.2/5.4 di [order-emol-sap-sync.md](order-emol-sap-sync.md)) — **sengaja tetap di dokumen ini**, bukan dipisah, karena tujuan dokumen ini memang sudah diperluas mencakup "merapikan integrasi Inspection→Order" (lihat header dokumen).

### 2.9a Standardisasi `WorkflowTransaction.ReferenceTransactionId` ke `MechanicOrderSummaryId`

*(Dibahas 17 Jul 2026 — muncul dari analisa SQL report `vw_report_iams_f_am_digiman_dorder.sql`, diperluas jadi bagian resmi "merapikan integrasi Inspection→Order".)*

**Temuan awal**: SQL report existing (`dorder.sql`, baris 709-712) join ke `workflowtransaction` lewat **2 jalur sekaligus**, di-`coalesce`:
```sql
left join workflowtransaction wft1 on mol.workorderid = wft1.referencetransactionid
left join workflowtransaction wft2 on mol.mechanicordersummaryid = wft2.referencetransactionid
```
Ini mengindikasikan `ReferenceTransactionId` **tidak konsisten 1 kolom** — kemungkinan besar `WorkOrderId` untuk Inspection-origin, `MechanicOrderSummaryId` untuk Additional Order (yang tidak punya `WorkOrderId` sama sekali).

**Keputusan standardisasi (17 Jul 2026)**: `ReferenceTransactionId` **selalu** pakai `MechanicOrderSummaryId` ke depannya — untuk Inspection **maupun** Additional Order. Dimungkinkan karena `MechanicOrderSummaryId` **terkonfirmasi selalu ada** di `MechanicOrderList` untuk kedua tipe (2.10, "FK ke header, seragam") — beda dengan `WorkOrderId` yang NULL untuk Additional. Manfaat: 1 join konsisten (report tidak perlu dual-join lagi), semantik lebih tepat (approval itu approve **Order**, bukan `WorkOrder`).

**✅ Konfirmasi (17 Jul 2026)**:
1. **Ini task BE** — mengubah logic yang men-set `ReferenceTransactionId` saat `WorkflowTransaction` dibuat/di-trigger (2.9, poin "Mekanisme deteksi submit terakhir" — masih open item terpisah soal *kapan* trigger-nya, ini soal *field apa* yang dipakai).
2. **Forward-only, TAPI ada nuance penting yang beda dari pola forward-only lain di dokumen ini** (mis. `MaintenanceCategoryCode` di 2.6, yang cukup "data lama dibiarkan, tidak dibaca lagi"): API **get approval list** dan **get approval detail** — dua endpoint yang **membaca** `WorkflowTransaction` untuk ditampilkan ke user (SPV approval list, dsb) — **logic lama-nya pasti pakai `WorkOrderId` untuk Inspection-origin dan `MechanicOrderSummaryId` untuk Additional**. Perubahan ini **harus tetap bisa menampilkan Order lama yang approval-nya belum selesai** (`WorkflowTransaction.Status` masih `In Progress`, dibuat sebelum perubahan ini live) — bukan cuma soal data baru ke depan, tapi soal **approval yang sedang berjalan** saat rilis terjadi. Kalau read-API cuma dirombak untuk baca `MechanicOrderSummaryId` saja, Order lama yang masih pending approval-nya akan **hilang dari list**/tidak ke-load detail-nya — regresi fungsional, bukan cuma soal data historis yang aman diabaikan. *(Lihat poin 3 — ternyata bukan cuma 2 endpoint ini yang kena, endpoint approve juga.)*
3. **⚠️ Koreksi (17 Jul 2026) — Endpoint approve (2.11.E) TERNYATA juga kena dual-lookup, bukan "write-side yang otomatis aman"**: sempat disimpulkan endpoint approve murni sisi write (bikin `WorkflowTransaction` baru). **Ini salah** — endpoint approve tidak membuat `WorkflowTransaction` baru, dia **mencari & meng-update** `WorkflowTransaction`/`WorkflowTransactionStep` yang **sudah ada** (langkah 1 dari 5 langkah di 2.11.E: "update status workflow jadi approved"). Untuk menemukan baris yang tepat, endpoint ini **juga butuh dual-lookup** yang sama seperti get approval list/detail — kalau Order yang di-approve itu lama (`ReferenceTransactionId` masih `WorkOrderId`), endpoint approve tetap harus bisa menemukannya. Jadi **3 titik** (get list, get detail, **dan** langkah 1 endpoint approve) sama-sama butuh dual-lookup transisi — bukan cuma 2. Yang **benar-benar** murni write-side/pakai standar baru langsung tanpa dual-lookup: titik **pembuatan awal** `WorkflowTransaction` itu sendiri (trigger "submit mechanic terakhir", 2.9) — proses yang beda dari endpoint approve ini.

**✅ Arah jawaban (17 Jul 2026)**: dual-lookup di read-API aman dihapus **setelah semua `WorkflowTransaction` lama (`ReferenceTransactionId = WorkOrderId`) tidak ada yang menggantung** — semua sudah `Complete`. **Belum ada mekanisme otomatis** untuk verifikasi titik itu — perlu **dimonitor manual** pasca rilis. Penghapusan dual-lookup-nya sendiri **pending item untuk rilis berikutnya**, bukan bagian rilis enhancement ini. Detail di open item 5.1.

### 2.10 Mapping Lengkap: Sumber → Order Tables

Merangkum seluruh keputusan 2.2–2.9 jadi satu gambaran: prinsipnya **target schema seragam** (`MechanicOrderSummary`/`MechanicOrderList`/`MechanicOrderDetail` sama untuk kedua tipe eMOL), **mekanisme pengisian yang beda** tergantung sumber (copy-at-creation dari Inspection, vs manual input untuk Additional yang tidak punya WorkOrder/Finding asal). Ini bentuk "standard"-nya — bukan skema terpisah per tipe, tapi 1 skema dengan 2 jalur populate.

**`MechanicOrderSummary` (header, 1:1 dengan Order/batch) — mapping lengkap seluruh kolom, direvisi 17 Jul 2026**

| Field | Tipe | Sumber — Inspection | Sumber — Additional |
|---|---|---|---|
| `Id` | PK, bigint, identity | — (generated) | — (generated) |
| `AssetNumber` | varchar(200) | Copy dari `WorkOrder.AssetNumber` saat Order dibuat (existing behavior) | Manual input user (screen 1 Asset Details) |
| `AssetModelCode` | varchar(200) | Copy dari `WorkOrder.AssetModelCode` | Manual input user |
| `AssetModelName` | varchar(200) | Copy dari `WorkOrder.AssetModelName` | Manual input user |
| `SectionTypeCode` | varchar(200) | Copy dari `WorkOrder.SectionTypeCode` | Manual input user |
| `SiteCode` | varchar(64) | Copy dari `WorkOrder.SiteCode` | Manual input user |
| `Source` **(baru)** | varchar(128) | **Direvisi 17 Jul 2026 — 2 sub-kasus, bukan 1 nilai tunggal**: `'Scheduled Inspection'` untuk Inspection reguler lewat jadwal, `'Additional Inspection'` untuk Inspection ad-hoc — keduanya sama-sama lewat `WorkOrder` (layar sama persis, area-of-unit-man-power-enhancement.md 2.3), dibedakan dari `WorkOrder.WorkType` (`'Scheduled'`/`'Additional'`) — **terjawab 17 Jul 2026**, lihat tabel field 2.9 | `'Additional Order'` — **bukan NULL lagi** (direvisi 17 Jul 2026), literal tetap menandakan Order dibuat langsung tanpa fitur asal |
| `SourceWorkOrderId` **(baru)** | varchar(128) | Copy dari `WorkOrder.Id` — snapshot, dipakai untuk payload message bus & `AttachmentUrl` deep link | NULL — tidak ada WorkOrder asal |
| `SourceWorkOrderNumber` **(baru)** | varchar(128) | Copy dari `WorkOrder.Number` | NULL — tidak ada WorkOrder asal |
| `HourMeter` **(baru)** | bigint | Copy dari `TaskPersonalized.MachineSMUValue` (ambil record pertama diinput; pasca Phase 1: `Task.MachineSMUValue`) — beda entity sumber (`TaskPersonalized`/`Task`, bukan `WorkOrder`) | **⚠️ Belum diputuskan** — lihat di bawah |
| `MaintenanceCategoryCode` | varchar(64) | Tidak pernah dipakai untuk tipe Inspection — bukan gap, memang tidak applicable | Tidak dipakai lagi (2.6) — kolom dibiarkan untuk histori |
| `MaintenanceCategoryName` | varchar(256) | Sama seperti `MaintenanceCategoryCode` | Sama seperti `MaintenanceCategoryCode` |
| `Status` | varchar(200) | Business logic Order — bukan copy dari `WorkOrder` | Business logic Order |
| `Number` | varchar(200) | Nomor Order sendiri (bukan `WorkOrder.Number` — itu di `SourceWorkOrderNumber`), prefix `EXO-` (5.1) | Nomor Order sendiri, generate biasa |
| `IsActive` | bit | — (default 1) | — (default 1) |
| `CreatedAt` | datetime | — (waktu Order dibuat) | — (waktu Order dibuat) |
| `CreatedBy` | varchar(128) | **✅ Terjawab (17 Jul 2026)** — mechanic yang **pertama kali** Sign and Finish (sama pola dengan `HourMeter`), lihat detail skenario di 2.9. **Beda dengan `MechanicOrderList.CreatedBy`** (per-eMOL) yang bisa beda-beda per baris sesuai mechanic pemiliknya | User yang create Additional Order |
| `ModifiedAt` | datetime | — | — |
| `ModifiedBy` | varchar(128) | — | — |

**`MechanicOrderList` (per-eMOL) — mapping lengkap seluruh kolom, direvisi 17 Jul 2026**

| Field | Tipe | Sumber — Inspection | Sumber — Additional |
|---|---|---|---|
| `Id` | PK, bigint, identity | — (generated) | — (generated) |
| `MechanicOrderSummaryId` | bigint, null | FK ke header (seragam, 2.9) | FK ke header (seragam) |
| `WorkOrderId` | bigint, null | Tetap diisi seperti sekarang, tidak berubah (additive, 2.9) | Selalu NULL (tidak ada WorkOrder asal — sudah sifat aslinya, bukan hal baru) |
| `TaskPersonalizedFindingId` | bigint, null | Tetap diisi seperti sekarang, tidak berubah (additive, sama prinsipnya dengan `WorkOrderId`, 2.9) | NULL — tidak ada Finding (sudah sifat aslinya, bukan hal baru) |
| `CostTypeCode` (Order Type) | varchar(64), null | Manual input user saat create eMOL | Manual input user |
| `MaintenanceActivityTypeCode` **(baru, 2.2–2.3)** | varchar(64), null | Manual input user, **tanpa default** dari WorkOrder | Manual input user |
| `InspectorCode` **(baru)** | — *(tipe belum dikonfirmasi)* | Copy dari `TaskPersonalized.UserCode` — **per-eMOL, bisa beda mechanic** (beda dengan `MechanicOrderSummary.CreatedBy` yang cuma dari mechanic pertama) | **NULL** — diputuskan 15 Jul 2026, lihat catatan di bawah |
| `InspectorName` **(baru)** | — *(tipe belum dikonfirmasi)* | Resolve dari `InspectorCode` (master data User) saat Order dibuat | **NULL** |
| `Number` | varchar(200), not null | Business logic (generate nomor eMOL) — **tanpa prefix `EXO-`**, itu khusus `MechanicOrderSummary.Number` (5.1) | Business logic biasa |
| `EDD` | datetime, not null | Existing logic kalkulasi otomatis saat Sign and Finish — **dibiarkan as-is, tidak disentuh enhancement ini** (diputuskan 17 Jul 2026) | Sama, existing behavior |
| `Status` | varchar(200), null | Business logic (lifecycle Order) | Business logic |
| `Type` | varchar(200), null | **`'Inspection'`** — kolom existing, **dibiarkan as-is, tidak disentuh enhancement ini** (diputuskan 17 Jul 2026). Cuma 2 nilai (`Inspection`/`Additional`), beda granularity dari `MechanicOrderSummary.Source` yang baru (3 nilai) — **disengaja**, bukan gap yang perlu diselaraskan | **`'Additional'`** |
| `DeleteReason` | varchar(max), null | User input kalau di-delete (existing behavior) | Sama |
| `NoPartsRequired` | bit, not null (default 0) | User input (checkbox declaration, 2.5) | Sama |
| `CompletedBy` | varchar(200), null | **Diturunkan dari kesetaraan `MechanicOrderList` ↔ `TaskPersonalizedFinding` (1:1, 2.9)** — mechanic pemilik eMOL ini sendiri, sama dengan `CreatedBy`/`InspectorCode` (per-baris, bukan pola "mechanic pertama" seperti di header `MechanicOrderSummary`) | Mechanic/user yang complete Additional Order-nya sendiri, sama dengan `CreatedBy` |
| `CompletedDate` | datetime, null | Sama logikanya dengan `CompletedBy` — timestamp aksi complete oleh mechanic pemilik eMOL ini | Sama, timestamp complete Additional Order |
| `IsActive` | bit, not null (default 1) | — | — |
| `CreatedBy` | varchar(128), not null | Mechanic pemilik eMOL **spesifik ini** (per-baris) — **beda dari `MechanicOrderSummary.CreatedBy`** yang cuma dari mechanic pertama di level header; di sini tiap baris `MechanicOrderList` `CreatedBy`-nya bisa A, B, atau C sesuai siapa yang submit eMOL itu | User yang create Additional Order |
| `CreatedAt` | datetime, not null | Waktu eMOL ini dibuat (per-baris, async — lihat skenario 2.9) | Waktu Additional Order dibuat |
| `ModifiedBy`/`ModifiedAt` | varchar(128)/datetime, null | — | — |

**`MechanicOrderDetail` (1:1 per eMOL) — mapping lengkap, direvisi 17 Jul 2026**

Snapshot-copy dari `TaskPersonalizedFinding` untuk Inspection (kolom identik, dikonfirmasi 2.9) — bukan bagian dari enhancement ini, existing behavior. Untuk Additional Order: manual input di screen 2 Defect Information.

| Field | Tipe | Sumber — Inspection | Sumber — Additional |
|---|---|---|---|
| `Id` | PK, bigint, identity | — (generated) | — (generated) |
| `MechanicOrderListId` | bigint, not null | FK 1:1 ke eMOL | FK 1:1 ke eMOL |
| `ComponentCode` | varchar(64), null | Copy dari `TaskPersonalizedFinding.ComponentCode` | Manual input ("Component & Sub Component*") |
| `SubComponentCode` | varchar(64), null | Copy | Manual input |
| `OtherSubComponentName` | varchar(512), null | Copy | Manual input (kalau SubComponent tidak ada di master) |
| `DamageCode` | varchar(64), null | Copy | Manual input ("Damage Code*") |
| `CauseCode` | varchar(64), null | Copy | Manual input ("Cause Code") |
| `RatingCode` | varchar(64), null | Copy | **✅ Ada, konditional (dikoreksi 17 Jul 2026)** — tidak disebut eksplisit di daftar field 2.5 karena field ini **cuma muncul untuk kombinasi Component-SubComponent tertentu**, bukan selalu ada. Konsisten dengan temuan `ModelComponentSubComponent.RatingCategoryCode` ([`services-asset-schema.md`](../database/services-asset-schema.md)) — tiap kombinasi Component-SubComponent punya `RatingCategory` sendiri yang menentukan apakah/opsi Rating apa yang muncul. Bukan gap. |
| `ActionRemedyCode` | varchar(64), null | Copy | Manual input ("Action Remedy*") |
| `PriorityCode` | varchar(64), null | Copy | Manual input ("Priority*") |
| `DefectNotes` | varchar(1024), null | Copy | Manual input ("Defect Notes") |
| `RepairDuration` | float, null | Copy — ini field **Duration** (area-of-unit-man-power-enhancement.md 2.3), sudah live sejak create finding | Manual input ("How Long Will This Defect Repair Take?*") |
| `RepairInstruction` | varchar(200), null | Copy | **✅ Ada, konditional (dikoreksi 17 Jul 2026)** — sama seperti `RatingCode`, cuma muncul untuk kombinasi Component-SubComponent tertentu, bukan selalu ada di semua kasus. Bukan gap. |
| `IsActive` | bit, not null (default 1) | — | — |
| `CreatedAt`/`CreatedBy` | datetime/varchar(128), null | Waktu & mechanic pemilik eMOL (sama pola dengan `MechanicOrderList`) | User yang create Additional Order |
| `ModifiedAt`/`ModifiedBy` | datetime/varchar(128), null | — | — |

**`MechanicOrderEvidence` (N per eMOL) — mapping lengkap, direvisi 17 Jul 2026**

Snapshot-copy dari `TaskPersonalizedEvidence` untuk Inspection (dikonfirmasi 15 Jul 2026, sama pola dengan `MechanicOrderDetail`). Untuk Additional Order: dari field "Evidence (photo upload)" di screen 2 (2.5).

| Field | Tipe | Sumber — Inspection | Sumber — Additional |
|---|---|---|---|
| `Id` | PK, bigint, identity | — (generated) | — (generated) |
| `MechanicOrderListId` | bigint, not null | FK ke eMOL (N evidence per eMOL) | FK ke eMOL |
| `Name` | varchar(256), null | Copy dari `TaskPersonalizedEvidence.Name` | Dari file yang di-upload user |
| `ContentAddress` | varchar(256), null | Copy dari `TaskPersonalizedEvidence.ContentAddress` (storage path/blob) | Dari hasil upload (storage path) |
| `IsActive` | bit, not null (default 1) | — | — |
| `CreatedAt`/`CreatedBy` | datetime/varchar(128), null | Sama pola dengan `MechanicOrderDetail` | User yang create Additional Order |
| `ModifiedAt`/`ModifiedBy` | datetime/varchar(128), null | — | — |

> **✅ Bukan gap (dikoreksi 17 Jul 2026)**: `TaskPersonalizedEvidence.TaskPersonalizedFindingId` memang **nullable** di skema real (`maintenance-execution`), tapi untuk masuk ke `MechanicOrderEvidence`, evidence **memang harus** punya relasi ke Finding — evidence yang tidak terikat ke Finding manapun **by design** tidak relevan untuk Order (bukan kelalaian/celah yang perlu ditangani).

**`MechanicOrderMaterial` (N per eMOL) — mapping lengkap, direvisi 17 Jul 2026**

**✅ Dikonfirmasi (17 Jul 2026) — beda pola dari `MechanicOrderDetail`/`MechanicOrderEvidence`**: bukan snapshot-copy dari entity Inspection manapun, murni bagian dari fitur **Order** itu sendiri — pengisian memang terjadi di Order, bukan di Inspection. Aksi **"Add Part"** yang user lakukan saat create Order (field "Part*" di 2.5) — berlaku **sama** untuk Inspection maupun Additional Order, karena user di kedua jalur sama-sama harus pilih Part secara manual. **Kolom turunan di bawah (`MaterialDescription`/`Cost`/dll) sudah punya logic existing yang handle auto-fill-nya — dibiarkan as-is, tidak disentuh/didesain ulang oleh enhancement ini.**

| Field | Tipe | Sumber — Inspection | Sumber — Additional |
|---|---|---|---|
| `Id` | PK, bigint, identity | — (generated) | — (generated) |
| `MechanicOrderListId` | bigint, not null | FK ke eMOL | FK ke eMOL |
| `MaterialNumber` | varchar(200), null | Manual input user (pilih Material via "Add Part") | Manual input user, sama |
| `Quantity` | decimal(18,2), not null (default 1) | Manual input user | Manual input user, sama |
| `MaterialDescription` | varchar(200), null | Existing logic, auto-fill dari master data Material — as-is | Sama |
| `MaterialRanking` | varchar(64), null | Existing logic — as-is | Sama |
| `UoMCode` | varchar(64), null | Existing logic — as-is | Sama |
| `Cost` | decimal(18,2), null | Existing logic — as-is | Sama |
| `TotalCost` | decimal(18,2), null | Existing logic — as-is | Sama |
| `Currency` | varchar(5), null | Existing logic — as-is | Sama |
| `BatchCode` | varchar(64), null | Existing logic (terkait pooling/SAP sync) — as-is | Sama |
| `IsActive` | bit, not null (default 1) | — | — |
| `CreatedBy` | varchar(128), not null | User yang tambah Part (mechanic pemilik eMOL) | User yang tambah Part |
| `CreatedAt` | datetime, not null | Waktu Part ditambahkan | Sama |
| `ModifiedBy`/`ModifiedAt` | varchar(128)/datetime, null | — | — |

**`InspectorCode`/`InspectorName`/`HourMeter` untuk Additional Order — diputuskan (15 Jul 2026): biarkan NULL.**
Additional Order tidak punya WorkOrder/TaskPersonalized asal, jadi tidak ada sumber copy untuk field-field ini, dan tidak ditambah input manual baru (tidak nambah scope UI di screen 1/2 Additional Order). `InspectorCode`/`InspectorName` tidak benar-benar hilang datanya — `MechanicOrderList.CreatedBy` (audit field existing) sudah cukup merepresentasikan "siapa yang buat eMOL ini" untuk kasus Additional. `HourMeter` memang murni tidak applicable untuk Additional Order (tidak ada konsep "state mesin saat inspeksi" di flow ini).

### 2.11 Dampak ke Endpoint API (`maintenance-order` → `maintenance-execution`)

Developer men-share daftar endpoint `Services.iAMS.MaintenanceOrder` yang handler-nya memanggil `IExternalAPIGateway.MaintenanceExecAPI` (15 Jul 2026) — dipakai untuk audit endpoint mana yang terdampak enhancement ini. Ini juga menjawab open item di 2.2 soal "cross-service call `GetWorkOrderById` kemungkinan masih dipakai untuk field lain".

**A. Jadi tidak terpakai lagi (dampak langsung enhancement ini)**

| Endpoint | Call | Status |
|---|---|---|
| `GET /api/workorder/inspection/offline/dropdown/maintenancecategory` | `GetWorkOrderAsync` | **Dikonfirmasi (15 Jul 2026)**: sumber dropdown "Activity Type" di screen 1 Additional Order — field ini dihapus total dari UI (2.2), jadi endpoint ini **tidak dipanggil lagi oleh FE**. Keputusan deprecate/hapus endpoint di sisi BE di luar scope dokumen ini (perlu keputusan tim engineer, mis. cek dulu tidak ada consumer lain). |

**B. Tetap dipakai, tidak terdampak** *(validasi konkret bahwa keputusan retain `WorkOrderId` di 2.9 sudah tepat — endpoint ini contoh nyata consumer yang bergantung ke relasi WorkOrder yang sudah ada)*

| Endpoint | Call |
|---|---|
| `GET`/`POST /api/workorder/tab/inspection` | `GetTaskPersonalizedFindingByListId` |
| `POST /api/mol/{mechanicOrderId}/complete` | `GetCountingUncompleteTaskPersonalize`, `GetTaskPersonalizedByWorkOrder` |
| `DELETE /api/mol/{mechanicOrderId}` | `GetTaskPersonalizedByWorkOrder`, `GetGetTaskPersonalizedFindingById` |
| `DELETE /api/mol/{mechanicOrderId}/approval/delete` | `GetTaskPersonalizedByWorkOrder`, `GetGetTaskPersonalizedFindingById` |
| `GET /api/inspection/approval/{section}` (`assigneduser`) | `GetTaskPersonalizedByWorkOrder` |
| `GET /api/inspection/approval/{section}` (`header`) | `GetInspectionApprovalByWorkOrderIdAsync` |
| `GET /api/inspection/approval/{section}` (default/`finding`), `.../by-finding`, `validation`, `GET /api/inspection/approval/validation` | `GetTaskPersonalizedFindingByListId` |

**C. Masih perlu klarifikasi** *(belum dikonfirmasi, jangan diasumsikan)*

| Endpoint | Call | Pertanyaan |
|---|---|---|
| `GET /api/inspection/approval/{section}` (`orderinformation`) | `GetWorkOrderAsync` | Field apa saja yang dibaca dari WorkOrder di sini? Kalau termasuk data yang sekarang mau di-snapshot ke `MechanicOrderSummary` (`SourceWorkOrderId`/`Number`, dst — 2.9), berpotensi endpoint ini bisa disederhanakan (baca dari snapshot, bukan live call) — tapi ini optimisasi terpisah, bukan wajib dilakukan sekarang. |

**D. Confirmed redundant — rekomendasi simplifikasi** *(dikonfirmasi 15 Jul 2026, temuan tambahan dari audit ini, bukan bagian scope asli enhancement)*

| Endpoint | Call | Temuan |
|---|---|---|
| `GET /api/mol/{molId}/order-detail` | `GetTaskPersonalizedFindingByListId` | **Dikonfirmasi**: data finding yang diambil live call ini **sudah ada** di `MechanicOrderDetail` (snapshot-copy dari `TaskPersonalizedFinding`, lihat 2.9). Live call ini redundan. **Rekomendasi**: endpoint baca langsung dari `MechanicOrderDetail`, hapus dependency ke `MaintenanceExecAPI.GetTaskPersonalizedFindingByListId` di handler ini — mengurangi 1 cross-service call yang tidak perlu. |
| `.../offline/dropdown/assetnumber`, `.../offline/dropdown/assetmodel` | `GetWorkOrderAsync` | **Dikonfirmasi (15 Jul 2026)**: `AssetNumber`/`AssetModelCode`/`AssetModelName` **sudah ada** di `MechanicOrderSummary` (copy dari `WorkOrder` saat Order dibuat — existing behavior, lihat 2.10). Live call ke `GetWorkOrderAsync` redundan. **Rekomendasi**: endpoint baca dari `MechanicOrderSummary`, bukan live call. |

**`IsImmediateExecutable`/`DeleteNotes` — dikonfirmasi (15 Jul 2026), bukan gap** (relevan untuk rekomendasi `order-detail` di atas):
- **`IsImmediateExecutable = True` → finding tidak perlu di-copy ke Order sama sekali.** Ini bukan cuma soal 2 kolom yang tidak ikut ter-copy — kalau finding-nya immediately-executable, **tidak ada eMOL/Order yang dibuat untuk finding tsb**. Konsisten dengan business rule report [`inspection-result.md`](../../report/transaction-report/inspection-result.md) (`isimmediateexecutable=1` = defect sudah diperbaiki langsung saat inspeksi, quick fix). Lihat kualifikasi trigger di 2.9.
- **`DeleteNotes` tidak perlu di-copy** — `MechanicOrderList` **sudah punya kolom `DeleteReason` sendiri** (level Order/eMOL, independen — lihat 2.4). `TaskPersonalizedFinding.DeleteNotes` melacak deletion event Finding (beda entity, beda lifecycle), tidak relevan disalin ke Order.

Rekomendasi hapus live call di `order-detail` **berlaku tanpa syarat** — kedua field ini memang tidak pernah jadi bagian data Order. Kedua baris di tabel D di atas **opportunity terpisah**, bukan wajib dikerjakan bareng enhancement Activity Type, tapi dicatat di sini karena ditemukan lewat audit yang sama.

**E. Keputusan: ganti ke snapshot Order DB, rekomendasi API baru** *(diputuskan 15 Jul 2026)*

| Endpoint | Call | Keputusan |
|---|---|---|
| `POST /api/inspection/approval/approve` | `GetWorkOrderByIdAsync` | **Logic diubah**: baca dari snapshot `MechanicOrderSummary`/`MechanicOrderList` (field baru, 2.9) — tidak perlu lagi call `maintenance-execution`. **Rekomendasi: buat API baru**, bukan ubah endpoint existing in-place — konsisten prinsip additive/backward-compat (2.9), supaya app version lama yang mungkin masih panggil endpoint existing tidak break. **✅ Mekanisme lengkap dikonfirmasi user (16 Jul 2026)**, 5 langkah: (1) update status workflow jadi approved — tidak ada impact, (2) update `MechanicOrderSummary`/`MechanicOrderList`/`MechanicOrderDetail` di Order DB, (3) populate & insert ke `PoolingMOItem`/`SAPMOSyncOrder` (mekanisme existing, bukan baru), (4) generate payload SAP dari data `PoolingMOItem`, (5) publish payload ke topic (**service bus**). **Service bus di step 5 murni outbound publish ke SAP** — sumber datanya `PoolingMOItem` yang sudah di-snapshot di step 3, **bukan** live-call balik ke `maintenance-execution`. Caveat dependency service bus↔`maintenance-execution` di versi sebelumnya **terjawab: tidak ada** — tidak perlu dicek developer lagi. **⚠️ Langkah (1) terdampak standardisasi `ReferenceTransactionId` (2.9a, 17 Jul 2026)**: lookup `WorkflowTransaction` yang mau di-update statusnya butuh dual-lookup transisi (`WorkOrderId` lama / `MechanicOrderSummaryId` baru) — sama seperti get approval list/detail, bukan cuma sisi write yang otomatis aman pakai standar baru. |

**Method `IMaintenanceExecAPI` yang belum dipanggil di endpoint manapun saat ini** (dicatat developer, informational): `GetWorkOrderDescriptionAsync`, `GetFindingByParam`, `GetTaskPersonalizedEvidenceByFindingIdsAsync`.

> **Prinsip audit ini**: perubahan skema/schema di enhancement ini sendiri **tidak mengubah/menghapus** call ke `maintenance-execution` manapun di luar dropdown Activity Type (poin A) — konsisten dengan keputusan additive-only di 2.9. Poin D adalah temuan optimisasi terpisah yang boleh dikerjakan kapan saja (independen dari rilis enhancement ini), bukan prasyarat.
>
> **⚠️ Satu pengecualian yang mungkin struktural, bukan sekadar belum dioptimasi (17 Jul 2026)** — lihat 2.9: logic deteksi "apakah semua mechanic yang di-assign ke `WorkOrder` sudah submit Order" (dipakai untuk trigger `WorkflowTransaction`) kemungkinan **perlu** cek `TaskPersonalized.Status` langsung ke `maintenance-execution`, karena mechanic yang belum Sign and Finish **tidak punya jejak apapun** di Order DB untuk dicek (snapshot cuma terbentuk setelah submit). Kalau ini benar, **ini satu-satunya dependency ke `maintenance-execution` yang tidak bisa dihilangkan** oleh prinsip "snapshot cukup, tidak perlu live-call" yang berlaku di poin D/E — beda karakter, bukan temuan redundansi. Masih perlu dikonfirmasi ke engineer sebelum jadi kesimpulan final.

### 2.12 Dampak ke Report — In Scope (17 Jul 2026)

- **Diputuskan (17 Jul 2026)**: dampak ke report **dimasukkan ke scope** enhancement ini — merevisi keputusan sebelumnya (5.2, 15 Jul 2026) yang bilang ini akan "dibahas di sesi & file terpisah".
- **Report terdampak (utama)**: halaman **D'ORDER RESULT** dan **ORDERING COMPLIANCE** — keduanya di-backing view yang sama, `am.vw_report_iams_f_am_digiman_dorder` ([doc](../../report/transaction-report/order-result-compliance.md), [SQL](../../report/transaction-report/vw_report_iams_f_am_digiman_dorder.sql)).
  - Report lain yang juga query tabel `mkp_maintenance_order` (mis. `vw_report_iams_get_molist`, halaman INSPECTION COMPLIANCE — levelnya per-`mechanicorderlist`, sama seperti Activity Type) **berpotensi ikut terdampak**, tapi **belum dianalisa** — di luar scope pembahasan ini, dicatat sebagai pointer saja (lihat [README.md](../../report/transaction-report/README.md)).
- **Kolom baru di detail data**: **`Maint. Act. Type`** — ditambahkan ke output view, sejajar kolom `MOType` yang sudah ada (sama-sama level per-eMOL, sama-sama merepresentasikan pilihan dropdown user saat create Order).
  - **Sumber**: `mechanicorderlist.maintenanceactivitytypecode` (kolom baru, 2.4).
  - **Titik perubahan di SQL** (referensi untuk dev, bukan implementasi final di dokumen ini): kolom perlu ditambahkan di 4 titik CTE chain `vw_report_iams_f_am_digiman_dorder.sql` — (1) raw read `mechanicorderlist` (baris ~189/199), (2) `maintenance_order_transformation` (baris ~637, sejajar `mol.costtypecode as motype`), (3) `base_form` (baris ~893, sejajar `mot.motype`), (4) final SELECT (baris ~949/1010, sejajar `[MOType]`).
- **Belum diputuskan**: label final kolom di PBI ("Maint. Act. Type" working name dari diskusi ini, bisa beda dari label akhir di report) dan urutan tampil persis (asumsi sementara: bersebelahan dengan `MOType`).
- **Timing**: mengikuti rilis enhancement ini secara keseluruhan (satu deployment) — kolom sumbernya (`mechanicorderlist.maintenanceactivitytypecode`) baru ada setelah enhancement ini live, jadi tidak bisa dirilis lebih dulu.
- **Pertanyaan terbuka yang belum terjawab** (dipindah dari 5.2, masih relevan): ketidaksesuaian business rule report `summaryreference=0`/`MechanicOrderSummaryId` NULL untuk Inspection — kemungkinan sudah outdated (lihat 5.1, prefix `EXO-` di `MechanicOrderSummary.Number` justru menyiratkan `MechanicOrderSummary` memang dibuat untuk Inspection-type). Tetap perlu dicek terpisah saat implementasi, di luar scope penambahan kolom `Maint. Act. Type` itu sendiri.
- **✅ Keputusan (17 Jul 2026): UNION/dual-path query report DIBIARKAN PERMANEN, tidak disederhanakan** — beda arah dari standardisasi `ReferenceTransactionId` di sisi API/backend (2.9a) yang punya rencana dual-lookup **sementara** + sunset setelah data lama habis. Untuk report (`dorder.sql` — dual-join `workflowtransaction` wft1/wft2, **dan** pola dual-source `maintenance_order_transformation`/`maintenance_execution_transformation` via flag `summaryreference`; `vw_report_iams_f_am_digiman_leadtime.sql`; kemungkinan Backlog Monitoring — belum dicek SQL-nya), kompleksitas UNION/dual-path **dibiarkan seperti sekarang selamanya** — bukan disederhanakan meski data baru pasca-enhancement sudah konsisten `MechanicOrderSummaryId`. Ini secara efektif **menutup** pertanyaan terbuka di poin sebelumnya (`summaryreference=0` dst) — bukan karena terjawab, tapi karena diputuskan tidak perlu diubah. Cakupan report yang benar-benar terdampak (termasuk konfirmasi Backlog Monitoring) **belum dieksplorasi penuh** — keputusan ini soal *arah* (jangan disederhanakan), bukan hasil audit lengkap semua report.

---

## 3. Rename: "Material Order" → "Order"

Screen 2 Additional Order saat ini melabeli tiap block eMOL sebagai **"Material Order #1"**, **"Material Order #2"**, dst — diganti jadi **"Order #N"**. Screen "Order Details" (create/complete eMOL dari Inspection, lihat 2.5) juga punya section berlabel "Material Order" — diganti jadi **"Order"** (tanpa `#N`, karena screen tsb sudah scoped ke 1 finding, tidak ada multiplicity).

**Alasan:**
- Block ini bukan cuma soal material — isinya defect info (Component/SubComponent/Damage Code/dst), Order Type, **dan** Maintenance Activity Type (field baru) — "Material" terlalu sempit.
- **"Order Line"/"Order Item" juga ditolak** — istilah itu menyiratkan *containment* (beberapa line di dalam 1 order), padahal relasi sebenarnya **paralel**: tiap eMOL/block jadi **1 order independen** saat sync ke SAP (`1 finding = 1 order`, `MONo` di-populate per-`PoolingMOItem`/per-eMOL, bukan per-header `MechanicOrderSummary`). Header "Order" (screen "Add Order", `MechanicOrderSummary`) sebenarnya berperan sebagai **batch/wrapper pembuatan & approval** (1 Order = 1 `WorkflowTransaction`, lihat [order-emol-sap-sync.md](order-emol-sap-sync.md) Bagian 2) yang membungkus beberapa order independen — bukan 1 order yang berisi banyak line.
- **"Order #N"** paling jujur secara semantik: screen "Add Order" (aksi, kata kerja) menghasilkan block-block "Order #1", "Order #2", dst (instance, masing-masing order utuh) — analog batch-create PO, tiap hasil tetap disebut sendiri-sendiri.
- Mengganti nama header `MechanicOrderSummary`/screen "Add Order" itu sendiri (supaya konsisten penuh sebagai "batch/wrapper") **di luar scope enhancement ini** — dicatat sebagai observasi, bukan action item.

---

## 4. Dampak ke Dokumen Existing

[order-emol-sap-sync.md](order-emol-sap-sync.md) mendokumentasikan **kondisi saat ini** (sebelum enhancement ini) — bagian berikut akan superseded setelah enhancement ini dikerjakan (lihat catatan cross-reference yang ditambahkan di dokumen tsb):
- **Bagian 3.2** (`MechanicOrderList`) — tambah kolom `MaintenanceActivityTypeCode`, `InspectorCode`, `InspectorName`; `WorkOrderId` **tidak berubah**, tetap diisi seperti sekarang (additive, lihat 2.9).
- **Bagian 3.3** (`MechanicOrderDetail`, baru ditambahkan 15 Jul 2026) — sudah dikonfirmasi snapshot-copy dari `TaskPersonalizedFinding`, tidak berubah oleh enhancement ini.
- **Bagian 4.2** (`PMActType` sourcing table) — diganti logic seragam per-eMOL (Bagian 2.2 dokumen ini).
- **Bagian 5.2** (`PoolingMOItem` populate) — `PMActType` tidak lagi dari `@MaintenanceCategoryCode` hasil resolve BE, langsung dari `mol.MaintenanceActivityTypeCode`.
- **`MechanicOrderSummary`** (3.1) — tambah kolom `Source` (varchar(128)), `SourceWorkOrderId` (varchar(128)), `SourceWorkOrderNumber` (varchar(128)), `HourMeter` (bigint) — tipe dikonfirmasi 17 Jul 2026 (lihat 2.9–2.10).
- **`MechanicOrderList`** — tambah kolom `Inspector` (lihat 2.9–2.10), selain `MaintenanceActivityTypeCode` yang sudah dicatat di atas.

Selain itu, [order-result-compliance.md](../../report/transaction-report/order-result-compliance.md) (Digiman Transaction Report, halaman D'ORDER RESULT & ORDERING COMPLIANCE) juga terdampak — kolom baru `Maint. Act. Type`, detail di **2.12**.

---

## 5. Open Items / Belum Dibahas

### 5.1 Masih Perlu Jawaban/Aksi

- **✅ Durasi mempertahankan dual-lookup — arah jawaban ada (17 Jul 2026), lihat 2.9a**: berlaku untuk **3 titik** (bukan cuma get approval list/detail — endpoint approve langkah 1 juga terdampak, dikoreksi 17 Jul 2026). Dual-lookup aman dihapus **setelah semua data approval lama (`ReferenceTransactionId = WorkOrderId`) tidak ada yang menggantung** (semua sudah `Complete`, tidak ada lagi yang `In Progress`). **Belum ada mekanisme otomatis untuk itu** — perlu **dimonitor manual** pasca rilis, dan penghapusan dual-lookup-nya sendiri jadi **pending item untuk rilis berikutnya** (bukan bagian dari rilis enhancement ini). Dicatat di sini supaya tidak terlupa, bukan tugas yang perlu diselesaikan sekarang.
- **Resolusi `InspectorName` dari `InspectorCode`** — lewat master data apa persis (User service?), dan siapa yang melakukan resolve-nya (BE saat proses submit Inspection, atau lookup terpisah)? Belum didesain detail.
- ~~Cara teknis membedakan `Scheduled Inspection` vs `Additional Inspection` untuk kolom `Source`~~ — **✅ terjawab (17 Jul 2026)**: dari `WorkOrder.WorkType` (`'Scheduled'`/`'Additional'`). *(2 kandidat sebelumnya sempat salah/dugaan — `WorkOrder.Source` dan `WorkOrder.PlanId` — dikoreksi user, jawaban benar `WorkType`.)*
- ~~Sumber `MechanicOrderSummary.CreatedBy` untuk Inspection-origin~~ — **✅ terjawab (17 Jul 2026)**: mechanic yang **pertama kali** Sign and Finish (pola sama dengan resolusi `HourMeter`, lihat 2.9). Mechanic berikutnya tidak mengubah `CreatedBy` header.
- **Mekanisme deteksi "submit Order terakhir" untuk trigger Workflow Approval** *(dibuka lagi 17 Jul 2026 — sempat ditandai terjawab, dikoreksi user sendiri)* — cek `MechanicOrderList.Status` semua `Complete` **tidak cukup**, karena ada celah waktu: mechanic yang belum Sign and Finish sama sekali **belum punya baris `MechanicOrderList`** untuk dicek (bukan status lain, tapi tidak ada barisnya). Kemungkinan logic sebenarnya juga perlu cek status `TaskPersonalized` dari seluruh mechanic yang di-assign, bukan cuma baris eMOL yang kebetulan sudah terbentuk — dengan filter tambahan **`TaskPersonalized.IsActive=1`** (assignment yang sudah di-cancel/dihapus jangan ikut dihitung sebagai "masih harus submit", supaya tidak macet permanen). Perlu dicek ke engineer. Detail skenario di 2.9. Submitter yang tercatat di `WorkflowTransaction` (user submit terakhir) belum dikoreksi, cuma mekanisme deteksinya yang masih perlu diperjelas.
- **Data seeder untuk `MaintenanceActivityType`** *(diputuskan 15 Jul 2026)* — perlu dibuatkan **mekanisme seeder** untuk implementasi pertama kali di PRD; isi datanya **akan diprovide tim Product kemudian** (bukan otomatis pakai 35 code BUMA ID yang sudah diterima — itu boleh dipakai sebagai referensi/contoh, tapi bukan berarti final). Seeder-nya sendiri (script/mekanisme) perlu didesain — belum dibahas detail formatnya.
- **Governance data master ganda** — karena `MaintenanceActivityType` (baru, lokal `maintenance-order`) sengaja dibuat independen dari data master `maintenance-strategy` (2.4), perlu diputuskan siapa yang jaga kedua list ini tetap selaras (kalau memang harus), supaya tidak drift diam-diam dari waktu ke waktu.
- Belum divalidasi ke tim technical/engineer `maintenance-order` — seluruh desain di dokumen ini berdasarkan diskusi arsitektur, belum ada pengecekan ke source code aktual.
- **1 endpoint API perlu klarifikasi dev** (lihat 2.11.C): purpose `GetWorkOrderAsync` di section `orderinformation` — apakah field yang dibaca sudah tercakup snapshot `MechanicOrderSummary`.
- ~~**Endpoint `approve` — API baru & cek service bus**~~ (2.11.E) — **terjawab (16 Jul 2026)**: mekanisme approve dikonfirmasi user (5 langkah, lihat 2.11.E) — service bus yang dimaksud murni publish payload SAP outbound (step 5), sumbernya `PoolingMOItem` yang sudah snapshot (step 3), **bukan** dependency live-call ke `maintenance-execution`. Tidak perlu dicek developer lagi.
- **2 endpoint punya live call redundan, dikonfirmasi (15 Jul 2026)** (2.11.D): `GET /api/mol/{molId}/order-detail` (data finding sudah ada di `MechanicOrderDetail`) dan `.../offline/dropdown/assetnumber`/`assetmodel` (data asset sudah ada di `MechanicOrderSummary`). Bukan aksi wajib enhancement ini, tapi rekomendasi simplifikasi yang bisa diajukan ke tim engineer kapan saja.
- **Relasi `PoolingMOItem.HourMeter`/`InspectorCode`/`InspectorName` (baru diisi enhancement ini) dengan mekanisme "BE enrichment" existing** (2.9, 16 Jul 2026) — enrichment existing yang mengisi `Inspector`/`HourMeter` di payload message bus (6.1 [order-emol-sap-sync.md](order-emol-sap-sync.md)) sudah berjalan (untuk `Inspector`) secara independen dari `PoolingMOItem`. Apakah perlu diubah untuk baca dari `PoolingMOItem` yang baru diisi, atau dibiarkan terpisah? Belum dicek developer.
- ~~`MechanicOrderList.Number` prefix convention~~ — **terjawab (15 Jul 2026)**: `EXO-` adalah prefix **`MechanicOrderSummary.Number`** (bukan `MechanicOrderList.Number`) untuk order selain Additional (Inspection). Lihat implikasi penting di 5.2 — ini justru mengonfirmasi `MechanicOrderSummary` **memang ada** untuk Inspection-type (bertentangan dengan business rule report yang bilang "standalone tanpa summary").

### 5.2 Sengaja Ditunda / Di Luar Scope Sekarang

- **`HourMeter` — pantau rilis [`pm-shutdown-data-model.md`](../../roadmap/phase1-service-package/pm-shutdown-data-model.md) Phase 1** (2.9) — sumbernya `TaskPersonalized.MachineSMUValue` (ambil dari record pertama kali diinput) cuma berlaku **sampai** Phase 1 live; setelah itu pindah ke `Task.MachineSMUValue`. *(Noted 15 Jul 2026 — tinggal pantau timing rilis, tidak butuh keputusan lagi sekarang.)*
- **`TypeCode`/`IsPeriodicalService`** — kolom di data master `maintenance-strategy` yang sengaja diabaikan di enhancement ini (2.4) — **dikonfirmasi dibahas terpisah nanti** (15 Jul 2026), di luar scope ini.
- **Koordinasi timing dengan [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md)** — dua enhancement ini menyentuh layar **persis sama**. *(Diputuskan 15 Jul 2026: user yang atur langsung, tidak perlu didesain di dokumen ini.)*
- ~~**Dampak ke report — dikonfirmasi ada, dibahas terpisah**~~ *(diputuskan 15 Jul 2026)* — **direvisi (17 Jul 2026): dipromosikan jadi bagian resmi scope enhancement ini, bukan lagi ditunda.** Lihat **2.12** untuk keputusan konkret (kolom baru `Maint. Act. Type` di D'ORDER RESULT & ORDERING COMPLIANCE). Pertanyaan soal ketidaksesuaian business rule report (`summaryreference=0`/`MechanicOrderSummaryId` NULL untuk Inspection, lihat 5.1) **masih belum terjawab** — dicatat ulang di 2.12 sebagai open item, bukan otomatis ikut selesai oleh keputusan ini.

---

## 6. Referensi
- [maintenance-activity-type-effort-summary.md](maintenance-activity-type-effort-summary.md) — estimasi SP/mandays/sprint (baseline tim BUMA ID), ditambahkan 16 Jul 2026
- [order-emol-sap-sync.md](order-emol-sap-sync.md) — schema & flow existing, Bagian 4.2 jadi titik awal enhancement ini
- [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) — enhancement lain di layar yang sama, prinsip "by value bukan by ID" yang diikuti di Bagian 2.4
- [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) — effort summary lintas fitur inisiatif lain (belum mencakup enhancement ini)
- [../form/form-submission.md](../form/form-submission.md) — skema real `WorkOrder`/`Task`/`TaskPersonalized`/`TaskPersonalizedFinding` (`maintenance-execution`), dasar Bagian 2.9
- [../../roadmap/phase1-service-package/pm-shutdown-data-model.md](../../roadmap/phase1-service-package/pm-shutdown-data-model.md) — perubahan `TaskPersonalized`/`Task` (SMU) yang direncanakan, belum live per 15 Jul 2026, relevan untuk 2.9
- [../database/maintenance-execution-schema.md](../database/maintenance-execution-schema.md) — DDL real lengkap `maintenance-execution`
- [../database/maintenance-order-schema.md](../database/maintenance-order-schema.md) — DDL real lengkap `maintenance-order`, termasuk `PoolingMOItem`/`SAPMOSyncOrder` yang jadi dasar reframing 2.9
- [../../report/transaction-report/order-result-compliance.md](../../report/transaction-report/order-result-compliance.md) — report terdampak (D'ORDER RESULT & ORDERING COMPLIANCE), kolom baru `Maint. Act. Type` (2.12)
