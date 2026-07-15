# Order & eMOL — Data Flow, Schema, dan SAP Sync

*Last updated: 2026-07-10*

---

**Feature:** Inspection & Order (Digiman+)
**Services terlibat:** `maintenance-execution` (Inspection, PM Shutdown, BD Corrective), `maintenance-order` (Order/eMOL, SAP sync middleware)
**Related doc:** [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md), [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) *(enhancement yang men-supersede Bagian 4.2 di bawah — lihat catatan di bagian tsb)*, [../dplan/digital-planning.md](../dplan/digital-planning.md), [../pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md](../pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md), [../database/sap-material-integration.md](../database/sap-material-integration.md) *(arah integrasi sebaliknya — SAP → Digiman+ material master, bukan flow ini)*

---

## 1. Overview Flow

Flow ini berbentuk **siklus** — Order/eMOL yang dikirim ke SAP akan kembali lagi ke Digiman+ sebagai backlog untuk dieksekusi:

```
1. User melakukan Inspection (input finding) — service maintenance-execution
2. User submit Inspection → data masuk ke Order — service maintenance-order
3. User edit eMOL — input material (pilih Order Type, add material) ATAU declare "tidak butuh material"
4. User submit Order → masuk ke Approver
5. Approver approve (bisa juga edit/update data Order-eMOL saat approval, bukan approve-only)
6. Setelah approve:
   a. Update tabel-tabel terkait Order-eMOL
   b. Build & publish data sync ke SAP (lihat Bagian 5)
   c. Service Bus lanjutkan proses sync ke SAP (call BAPI, create MO di SAP)
7. SAP memproses MO tersebut
8. MO yang sudah diproses SAP masuk kembali ke Digiman+ sebagai MO Backlog (lihat Bagian 9)
9. MO Backlog dieksekusi lewat salah satu dari 3 jalur (lihat Bagian 9.2), lalu Digiman+ kirim TECO MO ke SAP
```

> Inspection berada di service yang **sama** dengan PM Shutdown & BD Corrective (`maintenance-execution`) — bukan service terpisah.

---

## 2. Grain & Relasi Data

```
1 Inspection (WO)        = N Findings              = 1 Order
1 Finding                 = 1 eMOL
1 Order                   = 1 WorkflowTransaction   (approval, lihat gap-analysis.md)
```

- **Order** direpresentasikan oleh tabel header `MechanicOrderSummary`.
- **eMOL** direpresentasikan oleh tabel `MechanicOrderList` — satu baris = satu eMOL/finding.
- MOL (eMOL) berasal dari **dua sumber**:
  1. **Inspeksi** — `Type='Inspection'`, terhubung ke `WorkOrderId` (WO inspeksi) dan `TaskPersonalizedFindingId` (finding-nya).
  2. **Additional Order** — `Type='Additional'`, tanpa `WorkOrderId`/`TaskPersonalizedFindingId`, terhubung langsung ke `MechanicOrderSummaryId` (Order header) — dibuat user tanpa berasal dari finding inspeksi.

*(Detail cross-reference: lihat juga `gap-analysis.md` bagian "Business Rules Confirmed" — MOL berasal dari `summaryreference=0` (Inspeksi, punya `workorderid`) atau `summaryreference=1` (Additional Order, tanpa WO); `PriorityName` NULL untuk Additional Order karena tidak ada finding sebagai sumber priority.)*

---

## 3. Schema

### 3.1 `maintenance-order.MechanicOrderSummary` (header **Order**)

```
Id                        ← PK, bigint
Status
AssetNumber
AssetModelCode
AssetModelName
MaintenanceCategoryCode   ← "Activity Type" untuk Order tipe Additional (lihat 4.2)
MaintenanceCategoryName
SectionTypeCode
SiteCode
Number
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

> Order (baik dari Inspeksi maupun Additional) menyimpan info asset sendiri (`AssetNumber`, `AssetModelCode`/`Name`, `SiteCode`, `SectionTypeCode`) — Additional Order punya alur pemilihan asset independen, tidak bergantung ke data WorkOrder inspeksi.

### 3.2 `maintenance-order.MechanicOrderList` (**eMOL** — satu baris per finding/Additional Order line)

```
Id                        ← PK, bigint
CostTypeCode              ← "Order Type"/MOType — lihat Bagian 4.1
WorkOrderId                ← FK ke WorkOrder inspeksi (hanya diisi jika Type='Inspection')
TaskPersonalizedFindingId  ← FK ke finding (hanya diisi jika Type='Inspection')
MechanicOrderSummaryId     ← FK ke Order header
Number                     ← nomor eMOL (mis. "AMO-2607000196")
EDD
Status
Type                        ← 'Inspection' | 'Additional'
DeleteReason
NoPartsRequired            ← bit — flag "declare eMOL tidak butuh material" (lihat 4.3)
CompletedBy, CompletedDate
IsActive
CreatedBy, CreatedAt
ModifiedBy, ModifiedAt
```
> ✅ Struktur di atas **dikonfirmasi cocok dengan skema real** (screenshot table structure, 15 Jul 2026) — beda dari 3.1 (`MechanicOrderSummary`) yang masih document-derived, belum di-screenshot-verify.

### 3.3 `maintenance-order.MechanicOrderDetail` (detail defect per eMOL — struktur real, dikonfirmasi 15 Jul 2026)

Direferensikan lewat `LEFT JOIN MechanicOrderDetail mod ON mol.Id = mod.MechanicOrderListId` di query build `PoolingMOItem` (Bagian 5.2), tapi belum pernah didokumentasikan skemanya sampai sekarang.

```
Id                       ← PK, bigint
MechanicOrderListId       ← FK ke MechanicOrderList (nullable di skema real — longgar, bukan strict NOT NULL)
ComponentCode
SubComponentCode
OtherSubComponentName     ← "Other, please specify" kalau SubComponent tidak ada di dropdown
DamageCode
CauseCode
RatingCode                 ← ikut ter-copy dari sumbernya (lihat catatan di bawah), tidak berarti aktif dipakai di UI Order
ActionRemedyCode
PriorityCode
DefectNotes
RepairDuration             ← float — field "How Long Will This Defect Repair Take?" (Duration)
RepairInstruction          ← ikut ter-copy dari sumbernya (lihat catatan di bawah), tidak berarti aktif dipakai di UI Order
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```
> **Konfirmasi pasti (15 Jul 2026)**: tabel ini adalah snapshot-copy dari `maintenance-execution.TaskPersonalizedFinding` ("Finding") saat eMOL dibuat — dikonfirmasi lewat perbandingan skema real, kolomnya **hampir identik**: `ComponentCode`/`SubComponentCode`/`OtherSubComponentName`/`DamageCode`/`CauseCode`/`RatingCode`/`ActionRemedyCode`/`PriorityCode`/`DefectNotes`/`RepairDuration`/`RepairInstruction` sama persis di kedua tabel (lihat [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) 2.9 untuk skema `TaskPersonalizedFinding` lengkap). Bukan live-query ke Finding tiap dibutuhkan — meski `insert list` query 5.2 sendiri menunjukkan sebagian value datang lewat `VALUES` clause dari BE saat proses copy itu terjadi (lihat catatan di 5.2). Field `IsImmediateExecutable`/`DeleteNotes` ada di `TaskPersonalizedFinding` tapi **tidak** ikut ter-copy ke sini.

---

## 4. Business Logic per Field

### 4.1 `CostTypeCode` (Order Type / MOType)
- **Input manual oleh user** di kedua flow — saat edit eMOL (create order dari inspection) **dan** saat create Additional Order. Tidak pernah auto-derive dari header manapun.
- Karena disimpan di `MechanicOrderList` (level eMOL/finding, bukan di `MechanicOrderSummary`/header), **tiap eMOL di bawah Order/Inspection yang sama bisa punya Order Type berbeda-beda** satu sama lain — tidak seragam di level header.

### 4.2 `PMActType` (Activity Type)

> ⚠️ **Bagian ini mendokumentasikan kondisi SAAT INI (sebelum enhancement).** Sourcing `PMActType` yang campuran per tipe eMOL di bawah ini teridentifikasi sebagai **konflasi dua konsep bisnis berbeda** (jenis pekerjaan eksekusi vs klasifikasi order berdasarkan severity finding) — sedang di-redesign, lihat [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) untuk model baru (generic naming "Maintenance Activity Type", seragam per-eMOL untuk kedua tipe, wajib isi manual tanpa default).

Sourcing-nya **berbeda tergantung tipe eMOL**:

| Tipe eMOL | Sumber `PMActType` |
|---|---|
| **Inspection** (`WorkOrderId` ada) | Cross-service call `GetWorkOrderById` (BE `maintenance-order` → service `maintenance-execution`) → `WorkOrder.MaintenanceCategory.Code`. Seragam per-WO karena diambil dari header inspeksi. |
| **Additional** (tanpa `WorkOrderId`) | Lokal — `MechanicOrderSummary.MaintenanceCategoryCode`, diisi user langsung saat create Additional Order (field "Activity Type"). Levelnya di header Order, bukan per-eMOL. |

> Beda level ini penting: `CostTypeCode` levelnya selalu per-eMOL (4.1), sedangkan `PMActType` levelnya campuran — per-WO (Inspection) atau per-header-Order (Additional).

### 4.3 Material — Opsional per eMOL
- Saat edit eMOL, user bisa **input material** (pilih Order Type, add material item) **atau declare eMOL tidak butuh material** — flag `MechanicOrderList.NoPartsRequired` (bit).
- Konsekuensi ke sync SAP: lihat gate konsistensi Material di Bagian 5.5.

### 4.4 Approval
- Order-eMOL yang sudah di-submit masuk ke **Approver**.
- Saat ini aksi approval **bukan approve-only** — approver **bisa edit/update data Order-eMOL** langsung di titik approval (termasuk validasi Man Power & Duration, lihat [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) 2.6).

---

## 5. Alur Sync ke SAP (Post-Approval)

Setelah Order di-approve:

1. **Update tabel-tabel terkait Order-eMOL.**
2. **Build data untuk sync ke SAP** — langkah a–g di bawah.
3. **Service Bus melanjutkan proses sync ke SAP** (call BAPI) — lihat Bagian 6.

### 5.1 (a) Lookup `PoolingId` existing

```sql
;WITH CTE_EmolNumber AS
(
    SELECT mol.Number, mom.MaterialNumber
    FROM MechanicOrderList mol
    INNER JOIN MechanicOrderMaterial mom ON mol.Id = mom.MechanicOrderListId
    INNER JOIN @Ids AS idt ON mol.Id = idt.Id
    WHERE mol.IsActive = 1
)
SELECT pmi.PoolingId as Id
FROM PoolingMOItem pmi
INNER JOIN CTE_EmolNumber cen
    ON pmi.EMOLNumber = cen.Number
    AND pmi.MaterialNumber = cen.MaterialNumber
```

- Key lookup ke `PoolingMOItem` adalah **composite: `EMOLNumber` + `MaterialNumber`** (bukan `EMOLNumber` saja).
- ⚠️ Karena key butuh `MaterialNumber`, eMOL tanpa material (`NoPartsRequired=1`) **tidak akan pernah match** lewat query ini — perlu diperhatikan bagaimana kasus ini ditangani di step (b)/(c) berikutnya (kemungkinan selalu masuk jalur "create" di 5.2 karena tidak pernah ketemu existing row).

### 5.2 (b)/(c) Update jika ada, create jika tidak ada — insert ke `PoolingMOItem`

Insert (jika belum ada) menggunakan `OUTPUT Inserted.PoolingId`:

```sql
-- Step 1: temp table material keys, dari MechanicOrderMaterial + MechanicOrderList
--   (filter mol.IsActive=1, match by WorkOrderId+Type='Inspection' ATAU MechanicOrderSummaryId+Type='Additional')
-- Step 2: resolve StorageLocation dari tabel Material (match Number+Description+BatchCode+SiteId+SectionTypeCode)
-- Step 3: INSERT INTO PoolingMOItem (...)
--   SELECT ... FROM MechanicOrderList mol
--   JOIN (VALUES (@MolId1, @SubComponentName1, @ComponentName1, @DamageName1, @DamageGroupName1, @DefectNotes1), ...) dmol
--       ON (mol.TaskPersonalizedFindingId = dmol.MolId AND mol.Type='Inspection')
--        OR (mol.Id = dmol.MolId AND mol.Type='Additional')
--   LEFT JOIN MechanicOrderDetail mod ON mol.Id = mod.MechanicOrderListId AND mod.IsActive=1
--   LEFT JOIN MechanicOrderMaterial mom ON mom.MechanicOrderListId = mol.Id AND mom.IsActive=1
--   LEFT JOIN MechanicOrderSummary mos ON mol.MechanicOrderSummaryId = mos.Id
--   LEFT JOIN #MaterialTemp mt ON (match Number+Description+BatchCode+Ranking)
```

Kolom target `PoolingMOItem` (dari insert list): `MODetailMaterialId`, `MOType` (dari `mol.CostTypeCode`), `MONo` (NULL saat insert), `PMActType` (`@MaintenanceCategoryCode`), `SupervisorId`, `Equipment`, `BasicStartDate` (dari `mol.EDD`), `MaterialNumber`, `MaterialQuantity`, `Batch`, `Plant`, `MOCreatedBy`, `MOAttachment`, `EMOLNumber` (dari `mol.Number`), `Component`/`DamageGroup`/`SubComponent`/`DamageCode`/`MODescription`/`Notes` (dari `dmol`, hanya kalau `Mols.Count > 0` — di-passing dari BE lewat VALUES clause, bukan hasil join langsung ke tabel finding), `SiteId`, `SLoc` (dari `#MaterialTemp.StorageLocation`), `IsActive`, `CreatedUtcDate`, `ModifiedUtcDate`.

**Poin penting:**
- **Material `LEFT JOIN`** — eMOL tanpa material (`NoPartsRequired=1`) tetap dapat 1 row di `PoolingMOItem`, dengan field material-nya NULL. Ini mengakomodasi kasus "declare tidak butuh material" (4.3).
- **`PoolingMOItem` sudah punya kolom `Component`/`SubComponent`/`DamageGroup`/`DamageCode`** hari ini — relevan untuk assessment enhancement **Area of Unit** (lihat [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) 2.5): kalau `Area` ditambahkan, tabel ini & alur insert-nya perlu kolom baru juga.
- `MOType` di `PoolingMOItem` diisi dari `mol.CostTypeCode` (Order Type per-eMOL, lihat 4.1). `PMActType` di sini diisi dari parameter `@MaintenanceCategoryCode` yang di-resolve BE sebelumnya sesuai logic Bagian 4.2.

### 5.3 (d) Cek existing `SAPMOSyncOrder`

```sql
SELECT smo.Id
FROM SAPMOSyncOrder smo
INNER JOIN @Ids AS idt ON smo.PoolingId = idt.PoolingId
```

Existence-check berbasis `PoolingId` hasil 5.1/5.2, untuk decide create-or-skip di 5.4.

### 5.4 (e) Create `SAPMOSyncOrder` (placeholder tracking record)

```sql
INSERT INTO [dbo].[SAPMOSyncOrder]
    ([SiteId],[PoolingId],[MONo],[PoolingStatus],[ModuleName],[SAPStatus],
     [SAPText],[ParentNotifId],[MODescription],[AttachmentUrl],
     [IsDigimanProcessed],[CreatedUtcDate],[ModifiedUtcDate])
OUTPUT Inserted.Id
SELECT
    pmoi.SiteId, pmoi.PoolingId,
    NULL,        -- MONo (populated after SAP sync)
    'MOB',       -- PoolingStatus
    'DOrder',    -- ModuleName
    NULL,        -- SAPStatus (populated after SAP sync)
    NULL,        -- SAPText (populated after SAP sync)
    pmoi.NotifId,-- ParentNotifId — ⚠ asal kolom ini belum jelas di insert PoolingMOItem 5.2, lihat Bagian 7
    pmoi.MODescription,
    NULL,        -- AttachmentUrl (populated later)
    NULL,        -- IsDigimanProcessed
    @UtcNow, @UtcNow
FROM [dbo].[PoolingMOItem] pmoi
LEFT JOIN [dbo].[MechanicOrderMaterial] mom ON pmoi.MODetailMaterialId = mom.Id AND mom.IsActive = 1
JOIN [dbo].[MechanicOrderList] mol ON pmoi.EMOLNumber = mol.Number AND mol.IsActive = 1
WHERE (
    (mol.WorkOrderId = @MechanicOrderSummaryId AND mol.[Type] = 'Inspection')
    OR (mol.MechanicOrderSummaryId = @MechanicOrderSummaryId AND mol.[Type] = 'Additional')
) AND pmoi.IsActive = 1
```

- Kolom hasil sync (`MONo`, `SAPStatus`, `SAPText`, `AttachmentUrl`, `IsDigimanProcessed`) sengaja NULL saat insert — di-populate belakangan (async, setelah SAP merespons).
- `PoolingStatus='MOB'`, `ModuleName='DOrder'` — tag pembeda modul asal (pola serupa sudah dikenal dari `SAPMOSync*` family untuk modul lain, mis. DInspect).

### 5.5 Populate Data untuk Dikirim ke SAP

```sql
DECLARE @server VARCHAR(100) = @@SERVERNAME;
DECLARE @url VARCHAR(100) = (SELECT TOP 1 [Value] FROM [Configuration] WHERE [Key] = @server);

SELECT
    a.Id, a.SiteId, a.PoolingStatus,
    b.MOType, b.MODescription, b.MONo as MONoPrev, b.PMActType,
    b.Equipment, b.BasicStartDate, b.MaterialNumber, b.MaterialQuantity,
    b.Batch, b.MOCreatedBy,
    @url AS AttachmentUrl,   -- base URL dari Configuration, digabung query params di BE jadi deep link (lihat Bagian 6)
    c.TaskPersonalizedFindingId,
    b.SLoc, b.SupervisorId AS SupervisorId, b.EMOLNumber AS EMolNumber,
    a.PoolingId, c.WorkOrderId, c.MechanicOrderSummaryId
FROM dbo.SAPMOSyncOrder a WITH(NOLOCK)
INNER JOIN @SapIds tvp ON a.Id = tvp.Id
INNER JOIN dbo.PoolingMOItem b WITH(NOLOCK) ON a.PoolingId = b.PoolingId
INNER JOIN dbo.MechanicOrderList c WITH(NOLOCK) ON b.EMOLNumber = c.Number
LEFT JOIN dbo.MechanicOrderEvidence d WITH(NOLOCK) ON c.Id = d.MechanicOrderListId
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.PoolingMOItem
    WHERE SupervisorId = b.SupervisorId
      AND EMOLNumber = b.EMOLNumber
      AND (
            (COALESCE(MaterialNumber, '') != '' AND COALESCE(MaterialQuantity, '') = '')
         OR (COALESCE(MaterialNumber, '') = '' AND COALESCE(MaterialQuantity, '') != '')
      )
);
```

**⚠️ Gate konsistensi Material (`WHERE NOT EXISTS`)**: baris di-exclude dari pengiriman ke SAP kalau kombinasi `SupervisorId`+`EMOLNumber` di `PoolingMOItem` punya Material yang **tidak konsisten** — `MaterialNumber` terisi tapi `MaterialQuantity` kosong, atau sebaliknya. Rule-nya: Material harus **fully filled atau fully empty** (pasangan lengkap) baru boleh sync ke SAP.
- Kasus "declare tidak butuh material" (4.3, keduanya kosong) → **valid**, lolos gate ini.
- Kasus user salah isi (misal pilih material tapi lupa isi quantity) → **diblokir di sini tanpa tanda error eksplisit** di titik ini. Kemungkinan butuh validasi tambahan di layer sebelumnya (FE/BE saat submit eMOL) supaya kasus ini tidak silently stuck tidak ter-sync. **Ini finding yang perlu dikonfirmasi ke tim technical**, belum tentu bug — lihat Bagian 10.

### 5.6 (f) Publish ke `TopicPublishLog` (outbox)

```sql
INSERT INTO [dbo].[TopicPublishLog]
    ([TopicName],[MessagePayload],[TenantCode],[Type],[IsPublished],
     [CreatedAt],[RetryCount],[TraceId],[ParentSpanId])
VALUES (@TopicName, @MessagePayload, @TenantCode, @Type, @IsPublished,
        @CreatedAt, @RetryCount, @TraceId, @ParentSpanId);
```

Pola outbox standar — `MessagePayload` berisi hasil serialize dari query 5.5 (lihat contoh payload di Bagian 6.1). `TraceId`/`ParentSpanId` untuk distributed tracing.

### 5.7 `SapIntegrationLog` (audit log pemanggilan BAPI)

```sql
INSERT INTO [dbo].[SapIntegrationLog]
    ([RequestType],[RequestMessage],[ResponseMessage],[ErrorMessage],
     [StackTrace],[RetryCount],[TenantCode],[IsSuccess],[CreatedAt])
OUTPUT Inserted.Id
VALUES (@RequestType, @RequestMessage, @ResponseMessage, @ErrorMessage,
        @StackTrace, @RetryCount, @TenantCode, @IsSuccess, @CreatedAt);
```

Beda fungsi dari `TopicPublishLog` (antrian pesan yang mau dikirim/outbox) — `SapIntegrationLog` adalah audit trail **hasil aktual** tiap kali BAPI call dieksekusi oleh consumer Service Bus, termasuk kalau gagal (`ErrorMessage`, `StackTrace`).

**Fungsi konkret** *(dikonfirmasi 11 Jul 2026)*: tabel ini dipakai untuk **log payload yang dikirim** (`RequestMessage`) dan **cek status apakah call BAPI ke SAP berhasil atau tidak** (`IsSuccess`, `ResponseMessage`) — jadi titik acuan utama untuk troubleshooting/monitoring kalau ada Order/eMOL yang gagal sync ke SAP.

---

## 6. Payload & BAPI Mapping

### 6.1 Contoh `TopicPublishLog.MessagePayload`

```json
[{
  "SupervisorId": 10002390,
  "EMolNumber": "AMO-2607000196",
  "TenantCode": "BUMAID",
  "Body": [{
    "Id": 1052,
    "SiteId": 2009,
    "MOType": "MT02",
    "MODescription": "P1-Recondition Atlb Tank Broken",
    "PMActType": "FSI",
    "Equipment": "HDCT78077",
    "BasicStartDate": "2026-07-24T17:13:02.323",
    "MaterialNumber": "17262260",
    "MaterialQuantity": "1.00",
    "Batch": "REPAIRED",
    "MOCreatedBy": "2009OBH.supervisor01@protonmail.com",
    "AttachmentUrl": "https://digiman-uat.bukittechnology.com/order-list/material-order?workOrderId=220&assetNumber=HDCT78077&taskPersonalizedFindingId=&molNumber=AMO-2607000196",
    "TaskPersonalizedFindingId": null,
    "SLoc": "WH01",
    "PoolingId": 1167,
    "WorkOrderId": null,
    "MechanicOrderSummaryId": 220,
    "EquipmentModel": "785D",
    "HourMeter": "",
    "Inspector": "2009OBH.supervisor01",
    "DamageGroup": "Damaged",
    "DamageCode": "Broken",
    "MoDescriptionLong": "Model Unit : 785D\nKode Unit  : HDCT78077\nDamage     : Damaged-Broken\nInspector  : 2009OBH.supervisor01"
  }]
}]
```

- **Grouping**: array top-level di-grup per `SupervisorId` + `EMolNumber` — key yang sama dengan gate konsistensi Material di 5.5. `Body` bisa berisi >1 item kalau 1 eMOL punya beberapa baris `PoolingMOItem`/material.
- **Field hasil enrichment BE** (tidak ada di query 5.5, berarti di-enrich terpisah sebelum payload dibentuk): `EquipmentModel`, `HourMeter`, `Inspector`, `MoDescriptionLong`.
- **`AttachmentUrl` adalah deep link lengkap** ke halaman Digiman (`/order-list/material-order?workOrderId=...&assetNumber=...&taskPersonalizedFindingId=...&molNumber=...`) — base URL dari `Configuration` (5.5) digabung query params di BE.
- Contoh di atas adalah **Additional Order** (`WorkOrderId: null`, `TaskPersonalizedFindingId: null`, ada `MechanicOrderSummaryId`), tapi tetap punya `DamageGroup`/`DamageCode` terisi — observasi: untuk Additional Order, `DamageGroup`/`DamageCode` kemungkinan bisa diisi manual oleh user (belum dikonfirmasi sebagai aturan final).
- `Component`/`SubComponent` tidak muncul di contoh payload ini meski kolomnya ada di `PoolingMOItem` — kemungkinan null/di-omit pada contoh ini, bukan kesimpulan aturan umum.

### 6.2 Mapping ke BAPI SAP (dilakukan oleh middleware)

**Header (`GI_HEADER`)**

| SAP Field | Source |
|---|---|
| `ORDER_TYPE` | `moType` |
| `PLANT` | `siteId` |
| `EQUIPMENT` | `equipment` |
| `START_DATE` | `basicStartDate` → format `yyyyMMdd` |
| `SHORT_TEXT` | `moDescription` |
| `LONG_TEXT` | `moDescriptionLong` |
| `ORDERID` | fixed `%00000000001` |
| `PMACTTYPE` | **dinamis dari `PmActType` payload** (bukan fixed value — lihat Bagian 4.2 untuk asal `PmActType`) |
| `SYSTCOND` | fixed `0` |

**Operation (`GI_OPER`)** — semua fixed: `ACTIVITY=0010`, `CONTROL_KEY=PM01`, `PLANT` ← `siteId`.

**Component (`GI_COMP`)**

| SAP Field | Source |
|---|---|
| `MATERIAL` | `materialNumber` (jika ≤18 char) |
| `MATERIAL_LONG` | `materialNumber` (jika >18 char) |
| `PLANT` | `siteId` |
| `STGE_LOC` | `sLoc` |
| `BATCH` | `batch` |
| `GR_RCPT` | `moCreatedBy` (NIK) |
| `REQUIREMENT_QUANTITY` | `materialQuantity` |

---

## 9. MO Backlog — Inbound Flow (SAP → Digiman+)

Setelah MO diproses di SAP (Bagian 5–6), data MO tersebut **masuk kembali ke Digiman+ sebagai MO Backlog** — sisi kebalikan dari flow outbound yang didokumentasikan di atas.

### 9.1 Filter MO Backlog
- Secara teknis **semua MO SAP bisa saja diambil** ke Digiman+, tapi **saat ini sengaja difilter**: hanya MO dengan **Order Type tertentu** dan **PM Activity Type tertentu** yang masuk sebagai MO Backlog.
- **Filter ini bersifat konfigurasi per client** *(dikonfirmasi 10 Jul 2026)* — Order Type dan PM Activity Type yang jadi kriteria filter **bisa berbeda antar client/tenant** (tergantung konvensi Order Type/PM Activity Type di SAP masing-masing client), sehingga **tidak boleh di-hardcode** secara global. Harus disimpan sebagai konfigurasi per-tenant.
- *(Detail nilai Order Type/PM Activity Type spesifik untuk tiap client — belum didokumentasikan, lihat Bagian 10 Open Items.)*
- Ini konsisten dengan catatan "Add Backlog dari SAP" di [digital-planning.md](../dplan/digital-planning.md) — Digiplan mengambil data backlog full dari SAP (bukan dari Order Digiman+ langsung), dan scope-nya saat ini juga terbatas ke order type tertentu dengan PM Activity Backlog (per konfigurasi masing-masing client).

### 9.2 Cara MO Backlog Dieksekusi
MO Backlog bisa dieksekusi lewat **3 jalur**:

1. **Ditambahkan ke sub-task di Digiplan** — MO Backlog dimasukkan sebagai sub-task dalam suatu Plan, lalu dieksekusi lewat:
   - **PM Shutdown**, atau
   - **BD Corrective**
   (lihat [man-power-duration-visibility-enhancement.md](../pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md) untuk detail visibility & assignment mechanic di eksekusi ini.)
2. **Eksekusi langsung saat Inspection** — inspector bisa langsung mengeksekusi MO Backlog di saat yang sama dengan melakukan inspeksi (tidak lewat Digiplan/PM Shutdown/BD Corrective sama sekali). Biasanya untuk **pekerjaan ringan/cepat** yang tidak butuh waktu lama.

### 9.3 TECO ke SAP (Setelah Eksekusi)
- Setelah MO Backlog selesai dieksekusi (dari jalur manapun di 9.2), Digiman+ mengirim data untuk **TECO** (Technical Completion) MO tersebut ke SAP.
- *(Struktur data TECO yang dikirim — belum didokumentasikan, lihat Bagian 10 Open Items.)*

### 9.4 Sync Status Cancel MO
- **Diduga sudah ada mekanisme existing** *(disebutkan 10 Jul 2026, tapi belum dikonfirmasi solid)*: kalau MO di SAP di-**cancel**, MO Backlog yang sudah masuk ke Digiman+ **ikut ter-update/terhapus** secara otomatis.
- ⚠️ **Perlu dicek ulang di level code** — user sendiri belum yakin pasti soal ini. Jangan dianggap sebagai fakta final sebelum diverifikasi ke codebase/engineer yang pegang `maintenance-order`/`dplan`. Lihat Bagian 10 Open Items.
- Kalau ini benar ada, sifatnya beda dari edit **value** (Component/Sub Component/Area/Duration/Man Power) yang murni satu arah dan tidak sync balik (lihat [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) 2.5) — sync di sini khusus untuk **status/lifecycle MO** (cancel), bukan untuk value plan-nya.

---

## 10. Open Items / Belum Jelas

- **Asal kolom `PoolingMOItem.NotifId`** — dipakai di insert `SAPMOSyncOrder.ParentNotifId` (5.4), tapi tidak terlihat di list kolom insert `PoolingMOItem` (5.2). Belum dikonfirmasi apakah ada default/trigger, atau kolom lain yang belum ter-cover di dokumentasi step 5.2.
- **Gate konsistensi Material (5.5) tanpa notifikasi error** — baris dengan Material setengah-isi (`MaterialNumber` tanpa `MaterialQuantity` atau sebaliknya) diam-diam tidak pernah ter-sync ke SAP. Perlu dikonfirmasi ke tim technical apakah ada validasi FE/BE lain yang mencegah state ini terjadi di awal (saat submit eMOL), atau ini gap yang perlu ditindaklanjuti.
- **`DamageGroup`/`DamageCode` untuk Additional Order** — contoh payload (6.1) menunjukkan field ini terisi meski tanpa finding (`TaskPersonalizedFindingId: null`). Sudah dikonfirmasi (lihat [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) 2.3) bahwa Additional Order akan punya input manual untuk Component/Sub Component/Area/Duration/Man Power juga — konsisten dengan observasi ini.
- **Gap: `Component`/`Sub Component` belum dikirim ke SAP** — kedua field ini sudah ikut tersimpan di `PoolingMOItem` (5.2) dan payload (6.1), tapi **belum ada mapping-nya ke BAPI** (`GI_HEADER`/`GI_OPER`/`GI_COMP`, Bagian 6.2) — sehingga saat ini tidak benar-benar terkirim ke SAP saat create Order. `Area`, `Duration`, `Man Power` juga belum ada sama sekali di `PoolingMOItem`/payload/mapping BAPI. Ini persis scope assessment integrasi SAP (PIC Faiza) di [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md) 2.5 — tujuannya supaya kelima field ini (Component, Sub Component, Area, Duration, Man Power — versi **plan**, bukan actual) terkirim ke SAP saat create Order, sehingga saat MO kembali sebagai MO Backlog (Bagian 9), field-field itu bisa auto-fill di Digiplan saat user memilih MO Backlog.
- **Detail filter MO Backlog (9.1)** — Order Type dan PM Activity Type spesifik mana saja yang jadi kriteria filter belum didokumentasikan per client (baru diketahui bahwa filter itu ada dan bersifat konfigurasi per client, belum detail nilainya/struktur konfigurasinya).
- **Struktur data TECO (9.3)** — payload/mapping BAPI untuk kirim TECO ke SAP belum didokumentasikan (baru diketahui bahwa proses ini terjadi setelah eksekusi MO Backlog selesai).
- **Teknis "tambah MO Backlog ke sub-task Digiplan" (9.2)** — mekanisme detail bagaimana MO Backlog menjadi baris/task di `DPTask` belum dibahas.
- **Verifikasi mekanisme sync status cancel MO (9.4)** — perlu dicek ke codebase/engineer `maintenance-order`/`dplan` apakah benar ada mekanisme yang menghapus/update MO Backlog di Digiman+ saat MO terkait di-cancel di SAP. Disebutkan tapi belum solid dikonfirmasi.
- **Redesign sourcing `PMActType`/Activity Type (4.2)** — sudah ada rencana enhancement, lihat [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md): generic naming ("Maintenance Activity Type"), seragam per-eMOL (bukan campuran WO-derived/header-level), opsi dependent terhadap Order Type lewat mapping M:N baru. Belum divalidasi ke tim technical.
- **`PoolingMOItem` skema real (15 Jul 2026) ternyata sudah punya `HourMeter`, `InspectorCode`, `InspectorName`** — field ini tidak disebut di query 5.2 yang didokumentasikan di atas, berarti dokumentasi query 5.2 di bagian ini tidak lengkap/terpotong. Belum dikonfirmasi cara populate-nya hari ini. Lihat [maintenance-order-schema.md](../database/maintenance-order-schema.md) dan [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) 2.9.
- **`SAPMOSyncOrder` skema real jauh lebih kaya dari yang didokumentasikan di 5.4** — ada field `PlanDuration`, `Cost`, `Downtime`, `HM`, `Warranty`, `NextPSDate`, `ObjectPart`/`ObjectPartDesc`, `InspectionType`, `ModelUnit`, `UnitCode`, `NotifNo`/`NotifType` yang tidak disebut di dokumentasi query 5.4. **Diklarifikasi (15 Jul 2026)**: row-nya tetap dibuat lebih dulu sebagai placeholder (sesuai 5.4), tapi kolom-kolom ini ikut **di-update belakangan** setelah integrasi ke SAP selesai — sama pola dengan `MONo`/`SAPStatus`/`SAPText`/`AttachmentUrl`/`IsDigimanProcessed` yang sudah terdokumentasi, cuma jumlah kolomnya lebih banyak dari yang disebut di 5.4. Karena update-nya terjadi setelah BAPI call, bukan bagian proses build payload sebelum-nya, jadi terpisah dari flow `PoolingMOItem`/5.2 yang sudah didokumentasikan. Lihat [maintenance-order-schema.md](../database/maintenance-order-schema.md).
- ~~`MOOpen`/`StageMOOpen`~~ — **dikonfirmasi (15 Jul 2026)**: sumber data MO Backlog (Bagian 9) dari SAP.

---

## 11. Referensi
- [area-of-unit-man-power-enhancement.md](area-of-unit-man-power-enhancement.md)
- [maintenance-activity-type-enhancement.md](maintenance-activity-type-enhancement.md) — redesign sourcing PM Activity Type, superseded Bagian 4.2
- [../database/maintenance-execution-schema.md](../database/maintenance-execution-schema.md) — DDL real lengkap `maintenance-execution`
- [../database/maintenance-order-schema.md](../database/maintenance-order-schema.md) — DDL real lengkap `maintenance-order`
- [../dplan/digital-planning.md](../dplan/digital-planning.md) — mekanisme Digiplan, "Add Backlog dari SAP" (current state)
- [../pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md](../pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md) — eksekusi task (termasuk MO Backlog) di PM Shutdown/BD Corrective
- [../database/sap-material-integration.md](../database/sap-material-integration.md) — arah integrasi SAP → Digiman+ (material master), kebalikan dari flow ini
- `digiman+/report/transaction-report/gap-analysis/gap-analysis.md` — konteks report `dorder`, grain per-eMOL, business rules MOL (Inspeksi vs Additional Order)
