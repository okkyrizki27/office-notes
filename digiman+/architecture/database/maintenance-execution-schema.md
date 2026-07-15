# Database Schema — `maintenance-execution`

*Sumber: DDL script asli (`maintenance-execution-script.sql`), schema `dbo`, script date 15/07/2026 — skema real, bukan document-derived.*
*Disimpan: 15 Jul 2026.*

---

Dokumen ini referensi mentah struktur tabel `maintenance-execution`. Untuk narasi/business logic, lihat [`form-submission.md`](../form/form-submission.md) (hierarki WorkOrder→Task→TaskPersonalized→TaskPersonalizedFinding) dan [`maintenance-activity-type-enhancement.md`](../inspection-order/maintenance-activity-type-enhancement.md) 2.9 (pemakaian di enhancement Order).

---

## Hierarki Eksekusi (Inspection/PM Shutdown/BD Corrective/Form Submission — 1 service, 1 skema)

```
WorkOrder (1)
  └── Task (N)                          ← Task.WorkOrderId
        ├── FormSubmission (N)          ← FormSubmission.TaskId
        │     └── FormSubmissionTab (N) ← FormSubmissionTab.FormSubmissionId
        └── TaskPersonalized (N)        ← TaskPersonalized.TaskId (1 per mechanic per Task)
              ├── TaskPersonalizedLog (N)       ← .TaskPersonalizedId
              ├── TaskPersonalizedFinding (N)   ← .TaskPersonalizedId ("Finding")
              │     ├── TaskPersonalizedEvidence (N) ← .TaskPersonalizedFindingId
              │     └── CrackIdentified (N)          ← .TaskPersonalizedFindingId
              └── TaskPersonalizedEvidence (N)  ← juga bisa langsung ke TaskPersonalizedId (evidence umum, bukan per-finding)
```

### `WorkOrder`
```
Id                          PK, bigint, identity
TypeCode                    varchar(200), null
PriorityCode                varchar(200), null
Number                      varchar(16), null
PlanId                      bigint, null            ← FK ke DigitalPlanning.Id (dplan)
Description                 varchar(512), null
ScheduleStartDate           datetime, null
DueDate                     datetime, null
WorkType                    varchar(200), null
Source                      varchar(200), null       ← "Digiplan" jika dari Digiplan
Status                      varchar(200), null
StartDate                   datetime, null
EndDate                     datetime, null
AssetNumber                 varchar(200), null
AssetModelCode              varchar(200), null
AssetModelName               varchar(200), null
MaintenanceCategoryCode     varchar(200), null
MaintenanceCategoryName     varchar(512), null
SectionTypeCode             varchar(200), null
SiteCode                    varchar(64), null
Notes                       varchar(1024), null
TotalOSBacklog              int, null
IsActive                    bit, not null (default 1)
CreatedBy                   varchar(200), null
ModifiedBy                  varchar(200), null
CreatedAt                   datetime, null (default getutcdate())
ModifiedAt                  datetime, null
ReferenceId                 varchar(50), null
LastSyncedAt, LastSyncedBy               varchar(50)/datetime, null
LastSyncedModifiedAt, LastSyncedModifiedBy  varchar(50)/datetime, null
```
*(PK constraint bernama `PK_TempWorkOrder` — nama legacy, tabelnya sendiri sudah `WorkOrder`.)*

### `Task`
```
Id             PK, bigint, identity
WorkOrderId    bigint, not null
Name           varchar(200), not null
Type           varchar(200), not null (default 'UNDEFINED')
Status         varchar(200), not null (default 'Open')
Notes          varchar(1024), null
IsActive       bit, not null (default 1)
CreatedBy, ModifiedBy    varchar(200), null
CreatedAt, ModifiedAt    datetime, null
ReferenceId              varchar(50), null
LastSyncedAt/By, LastSyncedModifiedAt/By   datetime/varchar(50), null
```

### `TaskPersonalized`
```
Id                       PK, bigint, identity
TaskId                   bigint, not null
UserCode                 varchar(128), not null   ← identitas mechanic ("Inspector")
Status                   varchar(200), not null
MachineSMUValue          varchar(128), null       ← "HourMeter"
MachineSMUAddress        varchar(128), null
IsPrecautionConfirmed    bit, not null (default 0)
IsActive                 bit, not null (default 1)
CreatedBy, ModifiedBy    varchar(200), null
CreatedAt, ModifiedAt    datetime, null
ReferenceId              varchar(50), null
LastSyncedAt/By, LastSyncedModifiedAt/By   datetime/varchar(50), null
```

### `TaskPersonalizedFinding` ("Finding")
```
Id                        PK, bigint, identity
TaskPersonalizedId        bigint, not null
FormSubmissionTabId       uniqueidentifier, null
FormTaskCode              varchar(64), null
FormTaskNumber            varchar(16), null
ComponentCode             varchar(64), null
SubComponentCode          varchar(64), null
OtherSubComponentName     varchar(512), null
DamageCode                varchar(64), null
CauseCode                 varchar(64), null
RatingCode                varchar(64), null
ActionRemedyCode          varchar(64), null
IsImmediateExecutable     bit, not null (default 0)
PriorityCode              varchar(64), null
DefectNotes               varchar(1024), null
DeleteNotes               varchar(1024), null
RepairDuration            float, null (default 0)
RepairInstruction         varchar(200), null
IsActive                  bit, not null (default 1)
CreatedBy                 varchar(200), not null
CreatedAt                 datetime, not null (default getutcdate())
ModifiedBy                varchar(200), null
ModifiedAt                datetime, null
ReferenceId               varchar(50), null
LastSyncedAt/By, LastSyncedModifiedAt/By   datetime/varchar(50), null
```
> Dikonfirmasi: `maintenance-order.MechanicOrderDetail` snapshot-copy dari sini (lihat [order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) 3.3). `IsImmediateExecutable`/`DeleteNotes` **tidak** ikut ter-copy.

### `TaskPersonalizedEvidence`
```
Id                          PK, bigint, identity
TaskPersonalizedId          bigint, not null
TaskPersonalizedFindingId   bigint, null   ← nullable, jadi evidence bisa terikat langsung ke TaskPersonalized (bukan cuma ke Finding)
Name                        varchar(256), not null
ContentAddress              varchar(256), not null
IsActive                    bit, not null (default 1)
createdBy                   varchar(200), not null
createdAt                   datetime, not null (default getutcdate())
ModifiedBy, ModifiedAt      varchar(200)/datetime, null
ReferenceId                 varchar(50), null
LastSyncedAt/By, LastSyncedModifiedAt/By   datetime/varchar(50), null
```

### `TaskPersonalizedLog`
```
Id                    PK, bigint, identity
TaskPersonalizedId    bigint, not null
StartDate             datetime, null   ← device timestamp saat klik Start
EndDate               datetime, null   ← saat klik Finish, nullable
IsActive              bit, not null (default 1)
createdBy, createdAt  varchar(200)/datetime, not null (default getutcdate())
ModifiedBy, ModifiedAt varchar(200)/datetime, null
LastSyncedAt/By, LastSyncedModifiedAt/By   datetime/varchar(50), null
```

### `CrackIdentified`
```
Id                          PK, bigint, identity
TaskPersonalizedFindingId   bigint, not null
CrackDescription            varchar(1024), null
CrackLength                 float, null (default 0)
PrevCrackLength              float, null
IsActive                    bit, not null (default 1)
CreatedBy, CreatedAt        varchar(200)/datetime, not null (default getutcdate())
ModifiedBy, ModifiedAt       varchar(200)/datetime, null
```

---

## Form Submission

### `FormSubmission`
```
Id               PK, uniqueidentifier
TaskId           bigint, not null
FormId           uniqueidentifier, not null   ← cross-service ref ke Form.Id (maintenance-strategy)
FormCode         varchar(64), not null
Version          int, not null
AssetTypeCode    varchar(64), null
AssetBrandCode   varchar(64), null
AssetVariantCode varchar(64), null   ← 3 dimensi (tidak ada AssetModelCode — known gap, lihat form-submission.md)
IsActive         bit, not null (default 1)
CreatedAt        datetime, not null (default getutcdate())
CreatedBy        varchar(256), not null
ModifiedAt, ModifiedBy   datetime/varchar(256), null
```

### `FormSubmissionTab`
```
Id                  PK, uniqueidentifier
FormSubmissionId    uniqueidentifier, not null
Name                varchar(256), null
Sequence            int, not null
TotalParentTask     int, not null (default 0)
IsCompleted         bit, not null (default 0)
IsActive            bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(256), not null (default getutcdate())
ModifiedAt, ModifiedBy datetime/varchar(256), null
```

### `TaskResponseLog`
```
Id                     PK, bigint, identity
TaskId                 bigint, null
FormSubmissionTabId    uniqueidentifier, null
FormTaskCode           varchar(64), null
Response               varchar(128), null
Reason                 varchar(500), null
CreatedAt, CreatedBy   datetime/varchar(128), null
```

### `TaskKitResponse` (master data)
```
Code                        PK, varchar(64)
Name                        varchar(256), not null
IsDefectIdentified          bit, not null (default 0)
IsNotApplicable             bit, not null (default 0)
GroupDefectSummaryFormCode  varchar(64), not null
ElementCode                 varchar(64), null
RatingCode                  varchar(64), null
IsActive                    bit, not null (default 1)
CreatedAt, CreatedBy        datetime/varchar(256), not null (default getutcdate())
ModifiedAt, ModifiedBy      datetime/varchar(256), null
```

### `GroupTaskKitResponse` (master data)
```
Code                PK, varchar(64)
Name                varchar(256), not null
Type                varchar(64), not null
Description         varchar(512), not null (default '')
Icon                varchar(128), not null (default '')
BackgroundColor     varchar(16), not null (default '')
TextColor           varchar(16), not null (default '')
Sequence            int, not null (default 0)
IsActive            bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(256), not null (default getutcdate())
ModifiedAt, ModifiedBy datetime/varchar(256), null
```

### `BusinessOperationalForm` (master data)
```
Code            PK, varchar(64)
Icon            varchar(512), null
Name            varchar(128), null
FormCode        varchar(64), not null
Sequence        int, null
Group           varchar(128), null
SubGroup        varchar(128), null
WorkflowCode    varchar(64), null
IsActive        bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(256), not null (default getutcdate())
ModifiedAt, ModifiedBy datetime/varchar(256), null
```
*(PK constraint bernama `PK_WicopeLookUp` — nama legacy.)*

### `CBMTaskResponseValue`
```
Id                          PK, bigint, identity
TaskId                      bigint, not null
FormSubmissionTabId         uniqueidentifier, not null
CBMConfigCode               varchar(64), not null
CBMConfigVersion            int, not null (default 1)
PrevMeasurementValue        float, null
MeasurementValue            float, not null (default 0)
AdjustmentMeasurementValue  float, null
IsActive                    bit, not null (default 1)
CreatedBy, CreatedAt        varchar(200)/datetime, not null (default getutcdate())
ModifiedBy, ModifiedAt      varchar(200)/datetime, null
```

---

## SAP Sync & Integration (paralel dengan family `maintenance-order`, module tag "DInspect")

### `SAPMOSyncInspection`
```
Id               PK, bigint, identity
SiteId           varchar(64), null
MOId             int, null
MONo             varchar(32), null
MOStatus         varchar(6), null
ModuleName       varchar(64), null
SpvNIK           varchar(32), null
SAPStatus        smallint, null
SAPText          varchar(1024), null
CreatedUtcDate   datetime, null (default getutcdate())
ModifiedUtcDate  datetime, null (default getutcdate())
```
*(PK constraint `PK_SAPMOSynchronization`.)* Ini **konfirmasi** referensi "family `SAPMOSync*` untuk modul lain, mis. `DInspect`" yang disebut di [order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) 5.4 — jadi ada jalur sync MO paralel khusus Inspection, terpisah dari `maintenance-order.SAPMOSyncOrder` (`DOrder`).

### `SapIntegrationLog`
```
Id              PK, bigint, identity
RequestType     varchar(200), not null
RequestMessage, ResponseMessage, ErrorMessage, StackTrace   varchar(max), null
RetryCount      int, not null (default 0)
TenantCode      varchar(200), null
IsSuccess       bit, not null (default 0)
CreatedAt       datetime, not null (default getutcdate())
```
Sama struktur dengan `maintenance-order.SapIntegrationLog` — pola log audit BAPI call direplikasi per-service, bukan tabel bersama.

### `TopicPublishLog`
```
Id              PK, bigint, identity
TopicName       varchar(200), not null
MessagePayload  varchar(max), not null
TenantCode      varchar(200), null
Type            varchar(200), null
IsPublished     bit, not null (default 0)
PublishedAt     datetime, null
CreatedAt       datetime, not null (default getutcdate())
RetryCount      int, not null (default 0)
ErrorMessage    varchar(max), null
TraceId         varchar(100), null
ParentSpanId    varchar(100), null
```
Sama pola outbox dengan `maintenance-order.TopicPublishLog`.

### `LogSync`
```
ID            PK, bigint, identity
MONo          varchar(100), null
SAPStatus     varchar(10), null
SAPText       varchar(max), null
CreatedDate   datetime, null
```
*(PK constraint `LogSyncMo_PK`.)*

### `DeadLetterLog`
```
Id                 PK, bigint, identity
TopicName          varchar(200), not null
SubscriptionName   varchar(200), null
TenantCode         varchar(50), not null
MessageId          varchar(200), null
SessionId          varchar(200), null
MessagePayload, ErrorMessage   nvarchar(max), null
DeliveryCount      int, not null (default 0)
TraceId, ParentSpanId   varchar(500), null
FailedAt           datetime, not null (default getutcdate())
IsResolved         bit, not null (default 0)
```

---

## Config, Backlog, Auto-Generation

### `BacklogExecutionList`
```
Id              PK, bigint, identity
WorkOrderId     bigint, not null
MONumber        varchar(256), not null
MODescription   varchar(256), not null
CreatedAt, CreatedBy   datetime/varchar(128), not null
ModifiedAt, ModifiedBy datetime/varchar(128), null
IsActive        bit, not null (default 1)
```
Relevan langsung ke topik "MO Backlog" ([order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) Bagian 9) — tabel ini yang kemungkinan jadi tempat MO Backlog di-track di sisi `maintenance-execution`, terhubung ke `WorkOrderId`.

### `Configuration`
```
Id            PK, bigint, identity
TenantCode    varchar(200), null
Key           varchar(200), null
Description   varchar(200), null
Value         varchar(max), null
IsActive      bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
Match dengan `Configuration` yang direferensikan di [order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) 5.5 (base URL untuk `AttachmentUrl`).

### `Feature`
```
Id              PK, bigint, identity
FeatureName     varchar(200), null
Type            varchar(200), null
Platform        varchar(200), null
PermissionCode  varchar(64), null
IsActive        bit, not null
CreatedBy, ModifiedBy   varchar(200), null
CreatedAt, ModifiedAt   datetime, null
```
*(PK constraint `PK_TempFeature`.)*
> **Cross-reference (belum dikonfirmasi)**: `PermissionCode` kemungkinan merujuk ke `usermanagement.UserPermission.PermissionCode` (lihat [`user-management-schema.md`](user-management-schema.md)), yang bersifat hierarkis lewat `ParentPermissionCode`. Relasi lintas-DB ini belum pernah didokumentasikan sebelumnya.

### `WOGenerationConfig`
```
Id             PK, bigint, identity
AssetNumber    varchar(200), null
IntervalDays   int, null
IsActive       bit, not null (default 1)
CreatedBy, ModifiedBy   varchar(128), null
CreatedAt, ModifiedAt   datetime, null
AgingDays      int, not null (default 30)
InitialDate    datetime, not null (default getdate())
```
*(PK constraint `PK_AutoScheduleWorkOrder`.)* Config auto-generate WorkOrder terjadwal per asset.

### `StageWorkOrder` (staging, tanpa PK)
```
TypeCode                 varchar(200), null (default 'Inspection')
Number                   varchar(16), null
Description              varchar(512), null
DueDate                  datetime, null
WorkType                 varchar(200), null (default 'Scheduled')
Status                   varchar(200), null (default 'Open')
AssetNumber              varchar(200), null
AssetModelCode           varchar(200), null
AssetModelName           varchar(200), null
MaintenanceCategoryCode  varchar(200), null
MaintenanceCategoryName  varchar(512), null
SectionTypeCode          varchar(200), null
SiteCode                 varchar(64), null
IsActive                 bit, null (default 1)
CreatedAt, ModifiedAt    datetime, null (default getutcdate())
```
Tabel staging (tidak ada PK) — kemungkinan tempat sementara sebelum batch-insert ke `WorkOrder`.

### `MaterialBatch`
```
Id            PK, bigint, identity
MaterialId    bigint, not null
BatchCode     varchar(64), not null
IsActive      bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), not null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```

### `AuditLog`
```
Id             PK, bigint, identity
TableName      varchar(200), null
DataId         bigint, not null
Action         varchar(200), null
PreviousData   varchar(max), null
IsActive       bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```

*(`AzureSQLMaintenanceLog`, `AzureSQLMaintenanceOverride` — tabel sistem Azure SQL bawaan, bukan business schema, tidak didetailkan di sini.)*

---

## Observasi Belum Dibahas
- `SAPMOSyncInspection` — jalur sync SAP paralel khusus modul Inspection (`DInspect`), belum pernah dibahas detail flow-nya (beda dari `maintenance-order.SAPMOSyncOrder`/`DOrder` yang sudah didokumentasikan lengkap di order-emol-sap-sync.md).
- `BacklogExecutionList` — kemungkinan counterpart di `maintenance-execution` untuk MO Backlog, belum dibahas relasinya ke `PoolingMOItem`/`SAPMOSyncOrder` di `maintenance-order`.
- `StageWorkOrder`, `WOGenerationConfig` — mekanisme auto-generate/staging WorkOrder, belum pernah dibahas.
- `CBMTaskResponseValue`, `CrackIdentified`, `TaskKitResponse`, `GroupTaskKitResponse`, `BusinessOperationalForm` — tampaknya terkait modul CBM (Condition-Based Monitoring)/Wicope inspection form, di luar scope diskusi Order/eMOL sejauh ini.

---

## Referensi
- [../form/form-submission.md](../form/form-submission.md) — narasi hierarki WorkOrder→Task→TaskPersonalized (document-derived, sekarang terkonfirmasi cocok dengan DDL real ini)
- [../inspection-order/order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) — flow Order↔SAP di `maintenance-order`, referensi `SAPMOSync*` family
- [../inspection-order/maintenance-activity-type-enhancement.md](../inspection-order/maintenance-activity-type-enhancement.md) 2.9 — pemakaian skema ini untuk desain copy WorkOrder/TaskPersonalized ke `maintenance-order`
