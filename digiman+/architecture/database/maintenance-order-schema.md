# Database Schema — `maintenance-order`

*Sumber: DDL script asli (`order-script.sql`), schema `dbo`, script date 15/07/2026 — skema real.*
*Disimpan: 15 Jul 2026.*

---

Dokumen ini referensi mentah struktur tabel `maintenance-order`. Untuk narasi/business logic, lihat [`order-emol-sap-sync.md`](../inspection-order/order-emol-sap-sync.md) dan [`maintenance-activity-type-enhancement.md`](../inspection-order/maintenance-activity-type-enhancement.md).

---

## Order / eMOL Core

### `MechanicOrderSummary` (header Order)
```
Id                       PK, bigint, identity
Status                   varchar(200), null
AssetNumber              varchar(200), null
AssetModelCode           varchar(200), null
AssetModelName           varchar(200), null
MaintenanceCategoryCode  varchar(64), null    ← "Activity Type" LAMA untuk Additional (lihat enhancement doc 2.6)
MaintenanceCategoryName  varchar(256), null
SectionTypeCode          varchar(200), null
SiteCode                 varchar(64), null
Number                   varchar(200), null
IsActive                 bit, not null (default 1)
CreatedAt                datetime, not null (default getutcdate())
CreatedBy                varchar(128), null
ModifiedAt               datetime, null
ModifiedBy               varchar(128), null
```
> ✅ Cocok hampir persis dengan versi document-derived di [order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) 3.1 — sekarang **terkonfirmasi real**.

### `MechanicOrderList` (eMOL)
```
Id                          PK, bigint, identity
CostTypeCode                varchar(64), null
WorkOrderId                 bigint, null
TaskPersonalizedFindingId   bigint, null
MechanicOrderSummaryId      bigint, null
Number                      varchar(200), not null
EDD                         datetime, not null
Status                      varchar(200), null
Type                        varchar(200), null
DeleteReason                varchar(max), null
NoPartsRequired             bit, not null (default 0)
CompletedBy                 varchar(200), null
CompletedDate               datetime, null
IsActive                    bit, not null (default 1)
CreatedBy                   varchar(128), not null
CreatedAt                   datetime, not null (default getutcdate())
ModifiedBy                  varchar(128), null
ModifiedAt                  datetime, null
```

### `MechanicOrderDetail`
```
Id                       PK, bigint, identity
MechanicOrderListId      bigint, not null
ComponentCode            varchar(64), null
SubComponentCode         varchar(64), null
OtherSubComponentName    varchar(512), null
DamageCode               varchar(64), null
CauseCode                varchar(64), null
RatingCode               varchar(64), null
ActionRemedyCode         varchar(64), null
PriorityCode             varchar(64), null
DefectNotes              varchar(1024), null
RepairDuration           float, null
RepairInstruction        varchar(200), null
IsActive                 bit, not null (default 1)
CreatedAt                datetime, not null (default getutcdate())
CreatedBy, ModifiedBy    varchar(128), null
ModifiedAt               datetime, null
```
> Snapshot-copy dari `maintenance-execution.TaskPersonalizedFinding` — dikonfirmasi 15 Jul 2026 (kolom identik).

### `MechanicOrderEvidence`
```
Id                     PK, bigint, identity
MechanicOrderListId    bigint, not null
Name                   varchar(256), null
ContentAddress         varchar(256), null
IsActive               bit, not null (default 1)
CreatedAt              datetime, not null (default getutcdate())
CreatedBy              varchar(128), null
ModifiedAt             datetime, null
ModifiedBy             varchar(128), null
```
> **Konfirmasi (15 Jul 2026)**: snapshot-copy dari `maintenance-execution.TaskPersonalizedEvidence` — sama pola dengan `MechanicOrderDetail`. Ini yang jadi jawaban fungsi `MechanicOrderEvidence` yang sebelumnya open item di [order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) 5.5/Bagian 10 (di-LEFT JOIN tapi tidak muncul di SELECT) — evidence **sudah** ter-copy ke sini saat eMOL dibuat, tidak perlu perubahan.

### `MechanicOrderMaterial`
```
Id                     PK, bigint, identity
MechanicOrderListId    bigint, not null
BatchCode              varchar(64), null
Quantity               decimal(18,2), not null (default 1)
UoMCode                varchar(64), null
Cost                   decimal(18,2), null
TotalCost              decimal(18,2), null
MaterialDescription    varchar(200), null
MaterialNumber         varchar(200), null
MaterialRanking        varchar(64), null
Currency               varchar(5), null
IsActive               bit, not null (default 1)
CreatedBy              varchar(128), not null
CreatedAt              datetime, not null (default getutcdate())
ModifiedBy             varchar(128), null
ModifiedAt             datetime, null
```

---

## Master Data

### `MaterialCostType` (Order Type)
```
Code           PK, varchar(64)
Description    varchar(512), null
IsActive       bit, not null
CreatedAt, CreatedBy   datetime/varchar(128), not null
ModifiedAt, ModifiedBy datetime/varchar(128), null
```
*(Match dengan sample data BUMA ID yang sudah dibahas — MT01-MT06.)*

### `Material`
```
Id                PK, bigint, identity
Description       varchar(200), not null
Number            varchar(200), not null
MAP               float, null    ← Moving Average Price (asumsi)
MAPLocalCurr      float, null
Stock             float, null
Ranking           varchar(64), null
BatchCode         varchar(64), null
UoMCode           varchar(64), null
SiteId            varchar(64), not null
AssetModelCode    varchar(64), null
SectionTypeCode   varchar(64), null
StorageLocation   varchar(64), null
Currency          varchar(5), null
IsActive          bit, not null
CreatedAt, CreatedBy   datetime/varchar(128), not null
ModifiedAt, ModifiedBy datetime/varchar(128), null
```

### `MaterialBatchCode`, `MaterialRanking` (master data kecil)
```
MaterialBatchCode: Name (PK, varchar(64)), Description, IsActive, audit
MaterialRanking:   Code (PK, varchar(64)), Description, TextColor, BackgroundColor, IsActive, audit
```

### `Configuration`
```
Id             PK, bigint, identity
Key            varchar(128), null
Description    varchar(200), null
Value          varchar(max), null
IsActive       bit, not null
CreatedAt, CreatedBy   datetime/varchar(128), not null
ModifiedAt, ModifiedBy datetime/varchar(128), null
```
*(Beda dari versi `maintenance-execution` — tidak ada kolom `TenantCode` di sini.)*

---

## SAP Sync

### `PoolingMOItem` (staging sebelum sync SAP)
```
PoolingId          PK, bigint, identity
MODetailMaterialId bigint, null
MOType             varchar(50), null
MODescription      varchar(500), null
MONo               varchar(50), null
PMActType          varchar(5), null   ← ⚠️ DILEBARKAN (keputusan final 24 Jul 2026) — lihat catatan bawah
NotifId            bigint, null
SupervisorId       int, null
Equipment          varchar(50), null
BasicStartDate     datetime, null
MaterialNumber     varchar(50), null
MaterialQuantity   varchar(50), null
Batch              varchar(20), null
Plant              varchar(50), null
MOCreatedBy        varchar(50), null
MOAttachment       varchar(200), null
EMOLNumber         varchar(50), null
Component          varchar(50), null
DamageGroup        varchar(50), null
SubComponent       varchar(128), null
DamageCode         varchar(50), null
SiteId             varchar(64), null
Notes              varchar(5000), null
SLoc               varchar(10), null
IsActive           bit, null
CreatedUtcDate     datetime, null
ModifiedUtcDate    datetime, null
EquipmentModel     varchar(200), null
HourMeter          varchar(128), null   ← SUDAH ADA (lihat catatan penting di bawah)
InspectorCode      varchar(200), null   ← SUDAH ADA
InspectorName      varchar(100), null   ← SUDAH ADA
```
> **⚠️ Temuan (15 Jul 2026), dikoreksi (16 Jul 2026)**: `HourMeter`, `InspectorCode`, `InspectorName`, dan `EquipmentModel` **sudah ada** di tabel ini, tapi **saat ini tidak pernah diisi (NULL)**. **Dikonfirmasi user (16 Jul 2026)**: field-field ini **TIDAK masuk payload SAP** — mapping BAPI real ([order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) 6.2, `GI_HEADER`/`GI_OPER`/`GI_COMP`) tidak punya field ini sama sekali. Klaim sebelumnya ("sudah masuk payload SAP hari ini") **salah** — keliru menyamakan payload `TopicPublishLog.MessagePayload` (6.1, superset message bus) dengan payload BAPI SAP yang sebenarnya (6.2, subset). Jadi mengisi kolom-kolom ini di [maintenance-activity-type-enhancement.md](../inspection-order/maintenance-activity-type-enhancement.md) 2.9 murni untuk kelengkapan record staging `PoolingMOItem` itu sendiri, bukan kebutuhan SAP.

### `SAPMOSyncOrder` (tracking sync + kemungkinan data inbound MO Backlog)
```
Id                 PK, bigint, identity
SiteId             varchar(64), null
PoolingId          bigint, null
MONo               varchar(32), null
PoolingStatus      varchar(6), null
ModuleName         varchar(64), null
SAPStatus          smallint, null
SAPText            varchar(1024), null
NotifNo            varchar(32), null
NotifType          varchar(32), null
MOType             varchar(50), null
InspectionType     varchar(50), null
ModelUnit          varchar(50), null
UnitCode           varchar(50), null
Description        varchar(500), null
PlanDuration       float, null    ← kemungkinan landing spot utk "Duration" round-trip SAP
Warranty           varchar(50), null
NextPSDate         varchar(50), null
Cost               float, null
Downtime           float, null
HM                 float, null    ← "Hour Meter" versi float, BEDA dari PoolingMOItem.HourMeter (varchar)
ObjectPart         varchar(50), null
ObjectPartDesc     varchar(1024), null
ParentNotifId      varchar(50), null
MODescription      varchar(1024), null
AttachmentUrl      varchar(1024), null
IsDigimanProcessed smallint, null (default 0)
CreatedUtcDate, ModifiedUtcDate   datetime, null (default getutcdate())
```
> **Klarifikasi (15 Jul 2026)**: skema lebih kaya dari yang didokumentasikan di [order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) 5.4. Row-nya **tetap dibuat lebih dulu sebagai placeholder** sebelum BAPI call (sesuai 5.4 — `MONo`/`SAPStatus`/`SAPText`/`AttachmentUrl`/`IsDigimanProcessed` juga NULL saat insert) — bedanya, ternyata **lebih banyak kolom** yang ikut di-**update belakangan** setelah integrasi ke SAP selesai: `PlanDuration`, `Cost`, `Downtime`, `HM`, `Warranty`, `NextPSDate`, `ObjectPart`/`ObjectPartDesc`, `InspectionType`, `ModelUnit`, `UnitCode`, `NotifNo`/`NotifType` — bukan cuma 5 kolom yang sudah terdokumentasi. Karena update-nya terjadi **setelah** BAPI call (bukan bagian proses build payload sebelum-nya), kolom-kolom ini **tidak relevan** untuk [maintenance-activity-type-enhancement.md](../inspection-order/maintenance-activity-type-enhancement.md) (fokusnya `PoolingMOItem`/pre-sync) — dicatat di sini murni sebagai referensi struktur, bukan open item aktif.

### `SapIntegrationLog`, `TopicPublishLog`, `TopicConsumeLog`, `DeadLetterLog`, `AuditLog`
Sama pola dengan versi `maintenance-execution` (lihat [maintenance-execution-schema.md](maintenance-execution-schema.md)) — direplikasi per-service. `TopicConsumeLog` (baru, counterpart inbound dari `TopicPublishLog`):
```
Id              PK, bigint, identity
TopicName       varchar(200), not null
MessagePayload  varchar(max), not null
TenantCode      varchar(200), null
IsProcessed     bit, not null (default 0)
ProcessedAt, CompleteAt   datetime, null
CreatedAt       datetime, not null
ErrorMessage, StackTrace  varchar(max), null
```

---

## MO Backlog / Open MO (kemungkinan sumber data "Add Backlog dari SAP")

### `MOOpen`
```
Id                       PK, bigint, identity
MONumber                 varchar(256), null
MODescription            varchar(256), null
Status                   varchar(256), null
MaintenanceCategoryCode  varchar(256), null
MaintenanceCategoryName  varchar(256), null
SiteCode                 varchar(64), null
CostTypeCode             varchar(256), null
Notification             varchar(256), null
NotificationType         varchar(256), null
AssetNumber              varchar(200), null
AssetStatus              varchar(256), null
AssetModelCode           varchar(256), null
AssetBrandCode           varchar(256), null
EstCost                  varchar(50), null
ObjectPartName           varchar(50), null
SystemStatus             varchar(250), null
CreateDateMo             date, null
ReleaseDate              date, null
IsActive                 bit, null (default 1)
CreatedAt, ModifiedAt    datetime, null (default getutcdate())
```
**Dikonfirmasi (15 Jul 2026)**: ini tabel sumber MO Backlog yang ditarik dari SAP (lihat [order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) Bagian 9).

### `StageMOOpen`
Staging counterpart `MOOpen` (kolom sama, PK di `MONumber`, tanpa audit `CreatedBy`/`ModifiedBy`).

### `BacklogExecutionList` *(di `maintenance-execution`, bukan di sini — lihat [maintenance-execution-schema.md](maintenance-execution-schema.md))*

---

## Part/Material Order Tracking (SAP GR/GI/PR/PO — di luar scope Order/eMOL)

### `CheckPartOrder` / `StageCheckPartOrder`
```
Id, AssetNumber, AssetModelCode, SiteCode, ReservationNumber, ItemNumber, MaterialNumber,
MaterialDescription, StorageLocation, ReservationQuantity, Batch, UoM, GIDate, MONumber,
MODescription, BasicStartDate, MaterialCostType, MaintenanceCategoryCode, MaintenanceCategoryName,
Status, OrderStatus, GRStatus, GIStatus, GRQuantity, GIQuantity, PRStatus, PRNumber, PONumber,
NotificationNumber, PlanDuration, Warranty, Est_Cost, NextPSDate, ObjectPart, ObjectPartName,
GRNumber, GINumber, IsActive, CreatedAt, CreatedBy, ModifiedAt, ModifiedBy
```
Tracking status material order ke SAP (Goods Receipt/Issue, Purchase Requisition/Order) — concern terpisah dari eMOL/Order flow yang sudah dibahas.

---

## Observasi Belum Dibahas
- **`PoolingMOItem.HourMeter`/`InspectorCode`/`InspectorName` sudah ada** — perlu cek ke tim technical bagaimana nilainya di-populate hari ini (cross-service call apa, atau computed dari mana) sebelum finalisasi desain 2.9 di `maintenance-activity-type-enhancement.md`.
- **`SAPMOSyncOrder` sebenarnya jauh lebih kaya field-nya** (`PlanDuration`, `Cost`, `Downtime`, `HM`, dll) dari yang terdokumentasi — kemungkinan relevan untuk MO Backlog inbound dan assessment SAP di enhancement Area/Man Power. User sedang cek sendiri (15 Jul 2026), belum dibahas lebih lanjut di sini.
- ~~`MOOpen`/`StageMOOpen`~~ — **dikonfirmasi (15 Jul 2026)**: sumber MO Backlog dari SAP.
- **`PMActType varchar(5)` — DILEBARKAN (keputusan final 24 Jul 2026, membalik keputusan 15 Jul).** Sebelumnya diputuskan `MaintenanceCategory.Code` (Activity Type) harus dijaga ≤5 char supaya muat di kolom ini. Keputusan itu **dibatalkan**: kolom `PMActType` yang **dilebarkan** (disarankan ≥ `varchar(64)`, setara `MechanicOrderList.ActivityType`/`CostTypeCode` yang menjadi sumbernya), **bukan** membatasi panjang `MaintenanceCategory.Code` di core. Alasan: `varchar(5)` itu warisan constraint SAP, dan Digiman+ didesain sebagai produk standalone/ERP-agnostic — batasan SAP hanya berlaku di boundary integrasi SAP (mapping/publish ke BAPI `PMACTTYPE`, `order-emol-sap-sync.md` §6.2), tidak di-back-propagate jadi constraint global. Detail: `maintenance-activity-type-enhancement.md` §2.9.
- **`CheckPartOrder`/`StageCheckPartOrder`** — di luar scope Order/eMOL, tidak dibahas lebih lanjut.

---

## Referensi
- [maintenance-execution-schema.md](maintenance-execution-schema.md)
- [../inspection-order/order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md)
- [../inspection-order/maintenance-activity-type-enhancement.md](../inspection-order/maintenance-activity-type-enhancement.md)
