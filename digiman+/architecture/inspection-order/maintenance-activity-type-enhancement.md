# Enhancement: Maintenance Activity Type & Rapikan Integrasi Inspection→Order

*Last updated: 2026-07-15*

---

**Feature:** Inspection & Order (Digiman+)
**Related doc:** [order-emol-sap-sync.md](order-emol-sap-sync.md) *(schema & flow existing yang jadi dasar enhancement ini — Bagian 4.2 khususnya)*, [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) *(enhancement lain yang menyentuh layar sama persis — lihat Bagian 6)*

> **Scope dokumen ini (dikonfirmasi 15 Jul 2026)**: sengaja digabung jadi **satu dokumen**, dua tujuan sekaligus — (1) redesign sourcing PM Activity Type → "Maintenance Activity Type" (Bagian 2.1–2.8), dan (2) **merapikan integrasi Inspection→Order secara umum** (Bagian 2.9: relasi `WorkOrder`/`TaskPersonalized`↔`MechanicOrderSummary`/`MechanicOrderList`, hapus ketergantungan cross-service call yang tidak perlu). Kedua tujuan ini saling terkait erat (ditemukan saat menganalisa yang pertama), jadi tidak dipisah jadi dokumen lain.

> Dokumen ini hasil **diskusi desain internal** (14–15 Jul 2026), bukan hasil meeting business yang sudah final seperti [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md). Beberapa keputusan di sini (skema, penamaan) sudah cukup matang untuk didokumentasikan, tapi **belum divalidasi ke tim technical/engineer** yang pegang codebase `maintenance-order`, dan **belum dikonfirmasi ke business/client** — lihat Bagian 5 Open Items.

---

## 1. Latar Belakang

Saat menganalisa alur sync Order-eMOL ke SAP ([order-emol-sap-sync.md](order-emol-sap-sync.md) Bagian 4.2), ditemukan bahwa sumber data **`PMActType`** (PM Activity Type) punya dua masalah:

1. **Konflasi dua konsep bisnis yang berbeda** — untuk eMOL tipe Inspection, `PMActType` saat ini **auto-derive** dari `WorkOrder.MaintenanceCategory.Code` (cross-service call BE `maintenance-order` → `maintenance-execution`). Tapi `WorkOrder.MaintenanceCategoryCode` (mis. `INP`, `IH04`, `SCH`) merepresentasikan **jenis pekerjaan yang sedang dieksekusi** (Inspection, Scheduled Service, dst) — konsep yang **tidak wajib terkait SAP/ERP sama sekali**, scope-nya luas (`maintenance-execution` = tempat eksekusi apapun jenis pekerjaannya). Sementara PM Activity Type seharusnya adalah **keputusan yang diambil di titik Order**, ditentukan dari **severity/kriteria finding** (minor/major, dst) — bukan diturunkan dari jenis job eksekusinya. Desain lama men-treat dua axis ini seolah sama, padahal secara bisnis keduanya independen.
2. **Grain tidak konsisten** — untuk eMOL tipe Additional, `PMActType` disimpan di **level header** (`MechanicOrderSummary.MaintenanceCategoryCode`, field "Activity Type" di screen 1 Asset Details), sementara untuk tipe Inspection levelnya per-WO (lewat cross-service call). Keduanya beda level dari `CostTypeCode` (Order Type) yang **konsisten selalu per-eMOL**.
3. **Penamaan terlalu SAP-minded** — `PMActType`/"PM Activity Type" adalah istilah SAP Plant Maintenance. Kalau Digiman+ diimplementasi ke client non-mining/non-SAP, istilah ini tidak applicable secara langsung.

Enhancement ini membetulkan ketiga hal di atas sekaligus: **memisahkan** axis eksekusi (`WorkOrder`, tetap di `maintenance-execution`, ERP-agnostic) dari axis order (`maintenance-order`, spesifik untuk artifact yang dibuat ke ERP/SAP), **menyeragamkan grain** ke per-eMOL, dan **menggeneralisasi penamaan**.

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

**Reframing (15 Jul 2026, setelah skema real `PoolingMOItem` dikonfirmasi & diklarifikasi lebih lanjut)**: `PoolingMOItem` — tabel staging SAP di `maintenance-order` — **sudah punya** kolom `HourMeter` (varchar(128)), `InspectorCode` (varchar(200)), `InspectorName` (varchar(100)), tapi **dikonfirmasi (15 Jul 2026): kolom-kolom ini saat ini tidak dipakai, masih NULL**. Jadi bukan "mekanisme existing yang perlu diganti sumbernya" seperti dugaan awal — kolomnya sudah ada di skema tapi memang belum pernah diaktifkan/diisi. Enhancement ini yang **pertama kali mengisi kolom-kolom tsb**, lewat snapshot yang disiapkan di `MechanicOrderSummary`/`MechanicOrderList` saat Order dibuat.

**Konfirmasi alur (15 Jul 2026)**: **tidak perlu cross-service call baru**. `MechanicOrderList` (dan `MechanicOrderSummary`/`MechanicOrderDetail`/`MechanicOrderEvidence`) **sudah terbentuk langsung** begitu mechanic submit Inspection — artinya proses yang menangani submit itu **sudah** punya akses ke data `WorkOrder`/`TaskPersonalized`/`TaskPersonalizedFinding` di context yang sama saat itu juga (bukti: `MechanicOrderDetail`/`MechanicOrderEvidence` sudah snapshot-copy dari `TaskPersonalizedFinding`/`TaskPersonalizedEvidence` hari ini — proses copy itu sudah jalan). Jadi menambahkan `SourceWorkOrderId`/`SourceWorkOrderNumber`/`HourMeter`/`InspectorCode`/`InspectorName` tinggal **memperluas proses submit yang sudah ada** supaya ikut menyalin field-field itu juga — bukan membangun integrasi cross-service baru.

**Koreksi (15 Jul 2026): `Inspector` jadi 2 kolom terpisah** — `InspectorCode` dan `InspectorName`, menyamai struktur target `PoolingMOItem` yang sudah ada. Alasan: `TaskPersonalized.UserCode` cuma kode, nama perlu di-resolve terpisah (mis. dari master data User) — kalau cuma simpan Code, `InspectorName` di `PoolingMOItem` nanti butuh resolve ulang saat sync (balik ke masalah live-lookup yang mau kita hindari). Simpan keduanya sebagai snapshot sekaligus di titik Order dibuat.

Lengkap skema real `PoolingMOItem`: lihat [maintenance-order-schema.md](../database/maintenance-order-schema.md). ⚠️ **`PoolingMOItem.PMActType` cuma `varchar(5)`** — constraint penting: `MaintenanceActivityType.Code` (2.4) harus dijaga ≤5 karakter supaya tidak terpotong saat sync. Sample data BUMA ID yang sudah diterima (35 code, semua 3 karakter) aman terhadap constraint ini.

**Field yang diusulkan, dengan level yang benar**:

| Kolom baru | Ditambah ke | Sumber | Catatan |
|---|---|---|---|
| `SourceWorkOrderId` | `MechanicOrderSummary` (header) | `WorkOrder.Id` | 1:1 dengan Order — snapshot, dipakai buat `WorkOrderId` di payload SAP & `AttachmentUrl` ([order-emol-sap-sync.md](order-emol-sap-sync.md) 6.1) |
| `SourceWorkOrderNumber` | `MechanicOrderSummary` (header) | `WorkOrder.Number` — **confirmed ada**, bukan asumsi lagi | Untuk display "Order ini asal dari WO mana" |
| `HourMeter` | `MechanicOrderSummary` (header) | **Dua fase (dikonfirmasi 15 Jul 2026)**: (1) **Sekarang - sampai Phase 1 live**: `TaskPersonalized.MachineSMUValue`, ambil dari record **yang pertama kali diinput** (paling awal `CreatedAt`/nilai SMU-nya diisi) — resolusi untuk kasus 1 Task punya N `TaskPersonalized` dengan nilai berbeda. (2) **Setelah Phase 1 live**: `Task.MachineSMUValue` — 1 nilai per Task, ambiguitas otomatis hilang, tidak perlu logic "ambil yang pertama" lagi. | 1 nilai representatif untuk Order, bukan per-eMOL — lihat rationale di atas. Implementasi perlu switch sumber saat Phase 1 rilis. |
| `InspectorCode` | **`MechanicOrderList`** (per-eMOL) | `TaskPersonalized.UserCode` | Bisa beda per eMOL — siapa yang mencatat finding tsb |
| `InspectorName` | **`MechanicOrderList`** (per-eMOL) | Resolve dari `InspectorCode` (mis. master data User) saat Order dibuat | Disimpan sebagai snapshot terpisah, bukan di-resolve ulang saat sync — sejalan prinsip "value bukan reference" |

- `WorkOrder.MaintenanceCategory.Code` **sengaja tidak** diusulkan sebagai field yang di-copy untuk drive nilai apapun — itu sumber masalah yang enhancement ini hilangkan (2.2).
- **Konsekuensi struktural — disederhanakan (15 Jul 2026)**: proses "copy saat Order dibuat" menjangkau **3 level entity** di `maintenance-execution` (`WorkOrder` → header, `TaskPersonalized` → header `HourMeter` + per-eMOL `InspectorCode`/`InspectorName`, `TaskPersonalizedFinding` → per-eMOL/`MechanicOrderDetail` yang sudah ada) — tapi **tidak perlu cross-service call baru**, karena proses submit Inspection yang sudah ada hari ini **sudah** membentuk `MechanicOrderList`/`Summary`/`Detail`/`Evidence` langsung, dengan akses ke data 3 level itu di context yang sama. Tinggal perluas proses existing untuk ikut menyalin field tambahan ini.
- **`TaskPersonalizedFindingId` tetap diisi seperti sekarang, sama prinsipnya dengan `WorkOrderId`** — additive, tidak di-drop (lihat keputusan `WorkOrderId` di atas). Tetap dipakai untuk trace ke `TaskPersonalizedFinding`/`TaskPersonalized` asalnya kalau suatu saat perlu re-verify, meski data operasionalnya sudah snapshot ke `MechanicOrderDetail`.

> **Scope dokumen (15 Jul 2026)**: perubahan relasi WorkOrder↔Order ini memang lebih luas dari sekadar Activity Type (menyentuh `AttachmentUrl` deep link, payload SAP `WorkOrderId`, query 5.2/5.4 di [order-emol-sap-sync.md](order-emol-sap-sync.md)) — **sengaja tetap di dokumen ini**, bukan dipisah, karena tujuan dokumen ini memang sudah diperluas mencakup "merapikan integrasi Inspection→Order" (lihat header dokumen).

### 2.10 Mapping Lengkap: Sumber → Order Tables

Merangkum seluruh keputusan 2.2–2.9 jadi satu gambaran: prinsipnya **target schema seragam** (`MechanicOrderSummary`/`MechanicOrderList`/`MechanicOrderDetail` sama untuk kedua tipe eMOL), **mekanisme pengisian yang beda** tergantung sumber (copy-at-creation dari Inspection, vs manual input untuk Additional yang tidak punya WorkOrder/Finding asal). Ini bentuk "standard"-nya — bukan skema terpisah per tipe, tapi 1 skema dengan 2 jalur populate.

**`MechanicOrderSummary` (header, 1:1 dengan Order/batch)**

| Field | Sumber — Inspection | Sumber — Additional |
|---|---|---|
| `AssetNumber`/`AssetModelCode`/`AssetModelName`/`SectionTypeCode`/`SiteCode` | Copy dari `WorkOrder` saat Order dibuat (existing behavior) | Manual input user (screen 1 Asset Details) |
| `SourceWorkOrderId`/`SourceWorkOrderNumber` (baru) | Copy dari `WorkOrder.Id`/`Number` | NULL — tidak ada WorkOrder asal |
| `HourMeter` (baru) | Copy dari `TaskPersonalized.MachineSMUValue` (ambil pertama diinput; pasca Phase 1: `Task.MachineSMUValue`) | **⚠️ Belum diputuskan** — lihat di bawah |
| `MaintenanceCategoryCode`/`Name` (legacy) | Tidak pernah dipakai untuk tipe Inspection | Tidak dipakai lagi (2.6) — kolom dibiarkan untuk histori |

**`MechanicOrderList` (per-eMOL)**

| Field | Sumber — Inspection | Sumber — Additional |
|---|---|---|
| `MechanicOrderSummaryId` | FK ke header (seragam, 2.9) | FK ke header (seragam) |
| `WorkOrderId` | Tetap diisi seperti sekarang, tidak berubah (additive, 2.9) | Selalu NULL (tidak ada WorkOrder asal — sudah sifat aslinya, bukan hal baru) |
| `TaskPersonalizedFindingId` | Tetap diisi seperti sekarang, tidak berubah (additive, sama prinsipnya dengan `WorkOrderId`, 2.9) | NULL — tidak ada Finding (sudah sifat aslinya, bukan hal baru) |
| `CostTypeCode` (Order Type) | Manual input user saat create eMOL | Manual input user |
| `MaintenanceActivityTypeCode` (baru, 2.2–2.3) | Manual input user, **tanpa default** dari WorkOrder | Manual input user |
| `InspectorCode`/`InspectorName` (baru) | Copy dari `TaskPersonalized.UserCode` (+ resolve Name) | **⚠️ Belum diputuskan** — lihat di bawah |
| `Number`, `EDD`, `Status`, `Type`, `NoPartsRequired`, dst | Business logic biasa (tidak berubah) | Business logic biasa |

**`MechanicOrderDetail` (1:1 per eMOL)**

| Field | Sumber — Inspection | Sumber — Additional |
|---|---|---|
| `ComponentCode`/`SubComponentCode`/`OtherSubComponentName`/`DamageCode`/`CauseCode`/`RatingCode`/`ActionRemedyCode`/`PriorityCode`/`DefectNotes`/`RepairDuration`/`RepairInstruction` | Copy dari `TaskPersonalizedFinding` (sudah snapshot, existing behavior — dikonfirmasi 2.9) | Manual input user (screen 2, block "Order #N" — Defect Information) |

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
| `POST /api/inspection/approval/approve` | `GetWorkOrderByIdAsync` | **Logic diubah**: baca dari snapshot `MechanicOrderSummary`/`MechanicOrderList` (field baru, 2.9) — tidak perlu lagi call `maintenance-execution`. **Rekomendasi: buat API baru**, bukan ubah endpoint existing in-place — konsisten prinsip additive/backward-compat (2.9), supaya app version lama yang mungkin masih panggil endpoint existing tidak break. **⚠️ Perlu dicek developer**: endpoint ini juga melibatkan **service bus** (integrasi async, belum diketahui detailnya) — belum jelas apakah service bus itu juga bergantung ke data WorkOrder live dari `maintenance-execution`. Jangan diasumsikan aman sampai dikonfirmasi developer.

**Method `IMaintenanceExecAPI` yang belum dipanggil di endpoint manapun saat ini** (dicatat developer, informational): `GetWorkOrderDescriptionAsync`, `GetFindingByParam`, `GetTaskPersonalizedEvidenceByFindingIdsAsync`.

> **Prinsip audit ini**: perubahan skema/schema di enhancement ini sendiri **tidak mengubah/menghapus** call ke `maintenance-execution` manapun di luar dropdown Activity Type (poin A) — konsisten dengan keputusan additive-only di 2.9. Poin D adalah temuan optimisasi terpisah yang boleh dikerjakan kapan saja (independen dari rilis enhancement ini), bukan prasyarat.

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
- **`MechanicOrderSummary`** (3.1) — tambah kolom `SourceWorkOrderId`, `SourceWorkOrderNumber`, `HourMeter` (lihat 2.9–2.10).
- **`MechanicOrderList`** — tambah kolom `Inspector` (lihat 2.9–2.10), selain `MaintenanceActivityTypeCode` yang sudah dicatat di atas.

---

## 5. Open Items / Belum Dibahas

### 5.1 Masih Perlu Jawaban/Aksi

- **Resolusi `InspectorName` dari `InspectorCode`** — lewat master data apa persis (User service?), dan siapa yang melakukan resolve-nya (BE saat proses submit Inspection, atau lookup terpisah)? Belum didesain detail.
- **Data seeder untuk `MaintenanceActivityType`** *(diputuskan 15 Jul 2026)* — perlu dibuatkan **mekanisme seeder** untuk implementasi pertama kali di PRD; isi datanya **akan diprovide tim Product kemudian** (bukan otomatis pakai 35 code BUMA ID yang sudah diterima — itu boleh dipakai sebagai referensi/contoh, tapi bukan berarti final). Seeder-nya sendiri (script/mekanisme) perlu didesain — belum dibahas detail formatnya.
- **Governance data master ganda** — karena `MaintenanceActivityType` (baru, lokal `maintenance-order`) sengaja dibuat independen dari data master `maintenance-strategy` (2.4), perlu diputuskan siapa yang jaga kedua list ini tetap selaras (kalau memang harus), supaya tidak drift diam-diam dari waktu ke waktu.
- Belum divalidasi ke tim technical/engineer `maintenance-order` — seluruh desain di dokumen ini berdasarkan diskusi arsitektur, belum ada pengecekan ke source code aktual.
- **1 endpoint API perlu klarifikasi dev** (lihat 2.11.C): purpose `GetWorkOrderAsync` di section `orderinformation` — apakah field yang dibaca sudah tercakup snapshot `MechanicOrderSummary`.
- **Endpoint `approve` — API baru & cek service bus** (2.11.E, diputuskan 15 Jul 2026): logic ganti ke baca snapshot Order DB, rekomendasi dibuat sebagai API baru (bukan ubah in-place). **Wajib dicek developer**: ada service bus yang terlibat di endpoint ini, belum jelas dependency-nya ke `maintenance-execution` — jangan implementasi sebelum ini dikonfirmasi.
- **2 endpoint punya live call redundan, dikonfirmasi (15 Jul 2026)** (2.11.D): `GET /api/mol/{molId}/order-detail` (data finding sudah ada di `MechanicOrderDetail`) dan `.../offline/dropdown/assetnumber`/`assetmodel` (data asset sudah ada di `MechanicOrderSummary`). Bukan aksi wajib enhancement ini, tapi rekomendasi simplifikasi yang bisa diajukan ke tim engineer kapan saja.
- ~~`MechanicOrderList.Number` prefix convention~~ — **terjawab (15 Jul 2026)**: `EXO-` adalah prefix **`MechanicOrderSummary.Number`** (bukan `MechanicOrderList.Number`) untuk order selain Additional (Inspection). Lihat implikasi penting di 5.2 — ini justru mengonfirmasi `MechanicOrderSummary` **memang ada** untuk Inspection-type (bertentangan dengan business rule report yang bilang "standalone tanpa summary").

### 5.2 Sengaja Ditunda / Di Luar Scope Sekarang

- **`HourMeter` — pantau rilis [`pm-shutdown-data-model.md`](../../roadmap/phase1-service-package/pm-shutdown-data-model.md) Phase 1** (2.9) — sumbernya `TaskPersonalized.MachineSMUValue` (ambil dari record pertama kali diinput) cuma berlaku **sampai** Phase 1 live; setelah itu pindah ke `Task.MachineSMUValue`. *(Noted 15 Jul 2026 — tinggal pantau timing rilis, tidak butuh keputusan lagi sekarang.)*
- **`TypeCode`/`IsPeriodicalService`** — kolom di data master `maintenance-strategy` yang sengaja diabaikan di enhancement ini (2.4) — **dikonfirmasi dibahas terpisah nanti** (15 Jul 2026), di luar scope ini.
- **Koordinasi timing dengan [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md)** — dua enhancement ini menyentuh layar **persis sama**. *(Diputuskan 15 Jul 2026: user yang atur langsung, tidak perlu didesain di dokumen ini.)*
- **Dampak ke report — dikonfirmasi ada, dibahas terpisah** *(diputuskan 15 Jul 2026)*: enhancement ini **akan berdampak** ke report existing (mis. [`order-result-compliance.md`](../../report/transaction-report/order-result-compliance.md)/`vw_report_iams_f_am_digiman_dorder.sql`, `inspection-result.md`, `Backlog Monitoring.sql` — semua yang query `MechanicOrderSummary`/`MechanicOrderList`/`MechanicOrderDetail`). **Tidak dibahas/diselesaikan di dokumen ini** — akan dibahas di **sesi & file terpisah**, khusus report impact. Termasuk potensi ketidaksesuaian business rule report (`summaryreference=0`/`MechanicOrderSummaryId` NULL untuk Inspection) yang kemungkinan sudah outdated (lihat 5.1 — prefix `MechanicOrderSummary.Number` `EXO-` untuk Inspection justru menyiratkan `MechanicOrderSummary` memang dibuat untuk Inspection-type) — jadi dasar diskusi di file terpisah nanti, bukan diselesaikan di sini.

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
