# Database Schema — `maintenance-strategy`

*Sumber: DDL script asli (`maintenance-stretegy.sql`), schema `dbo`, script date 15/07/2026 — skema real.*
*Disimpan: 15 Jul 2026.*

---

Dokumen ini referensi mentah struktur tabel `maintenance-strategy` — service yang mendefinisikan **Form/FormTask** (template inspeksi/PM) dan **CBM Config** (standar Condition-Based Monitoring). Keduanya di-refer via `Code` oleh service lain saat runtime, mis. `FormTask.Code` ↔ [`maintenance-execution.TaskPersonalizedFinding.FormTaskCode`](maintenance-execution-schema.md).

---

## Form / FormTask — Template Definisi Form Inspeksi/PM

### `Form` (header + versi)
```
Id                          PK, uniqueidentifier
FormCode                    varchar(64), not null   ← 1 FormCode bisa punya banyak Version (row)
Version                     int, not null
Status                      varchar(32), null        ← draft/published (asumsi)
Type                        varchar(64), null
MaintenanceCategoryCode     varchar(64), null
OperationalEnvironmentCode  varchar(64), null
Name                        varchar(256), null
Description                 varchar(max), null
ReleaseNote                 varchar(max), null
ReleaseDate                 datetime, null
IsActive                    bit, not null
CreatedAt, CreatedBy        datetime/varchar(256), not null
ModifiedAt, ModifiedBy      datetime/varchar(256), null
```

### `FormTab`
```
Id                PK, uniqueidentifier
FormId            uniqueidentifier, not null
Name              varchar(256), null
Sequence          int, not null
TotalParentTask   int, not null
IsActive          bit, not null
CreatedAt, CreatedBy    datetime/varchar(256), not null
ModifiedAt, ModifiedBy  datetime/varchar(256), null
```

### `FormTask` (task bank, reusable — bukan child langsung `FormTab`)
```
Id                     PK, bigint, identity
Code                   varchar(64), null    ← inilah yang dirujuk sebagai FormTaskCode di service lain
FormTaskCategoryCode   varchar(64), null
Description            varchar(max), null
DescriptionHTML        varchar(max), null
Tab                    varchar(max), null   ← kemungkinan JSON, penempatan ke FormTab (denormalized)
SectionTask            varchar(max), null   ← kemungkinan JSON, grouping section dalam tab
IsActive               bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **Catatan struktur**: `FormTask` tidak punya kolom FK langsung ke `FormId`/`FormTabId` — relasi ke Form/Tab kemungkinan disimpan sebagai data di kolom `Tab`/`SectionTask` (varchar(max), kemungkinan JSON), bukan relational FK biasa. Perlu klarifikasi lebih lanjut kalau mau trace "task mana ada di form/tab mana" secara query SQL langsung.

### `FormTaskAsset`, `FormTaskAssetMaintenanceCategory` (scoping FormTask ke asset)
```
FormTaskAsset:
Id             PK, bigint, identity
FormTaskId     bigint, not null
FormTaskCode   varchar(64), null
AssetTypeCode, AssetBrandCode, AssetModelCode, AssetVariantCode   varchar(64), null
IsActive, audit   standard

FormTaskAssetMaintenanceCategory:
Id                       PK, bigint, identity
FormTaskAssetId          bigint, not null
FormTaskCode             varchar(64), null
MaintenanceCategoryCode  varchar(64), not null
IsActive, audit   standard
```

### `FormTaskCategory`
```
Code   PK, varchar(64)
Name   varchar(200), null
IsActive, audit   standard
```

### `FormAssetAssignment`, `FormPSAssignment`, `FormSiteAssignment` (scoping Form ke asset/periodical-service-type/site)
```
FormAssetAssignment:
Id      PK, bigint, identity
FormId  uniqueidentifier, not null
AssetTypeCode, AssetBrandCode, AssetModelCode, AssetVariantCode   varchar(64), null
IsActive, audit   standard

FormPSAssignment:
Id                          PK, bigint, identity
FormId                      uniqueidentifier, not null
PeriodicalServiceTypeCode   varchar(64), not null   ← "PS" = Periodical Service, lihat MaintenanceCategory.IsPeriodicalService
IsActive, audit   standard

FormSiteAssignment:
Id      PK, bigint, identity
FormId  uniqueidentifier, not null
SiteCode  varchar(64), not null
IsActive, audit   standard
```

---

## CBM Config — Condition-Based Monitoring

### `CBMConfig` (header standar CBM per component)
```
Id                     PK, bigint, identity
TaskKey                varchar(64), null
Code                   varchar(64), not null
Version                bigint, null
Description            varchar(max), null
AssetTypeCode, AssetBrandCode, AssetModelCode, AssetVariantCode   varchar(64), null
ComponentCode          varchar(64), not null
SubComponentCode       varchar(64), null
CBMMainCategoryCode    varchar(64), not null
CBMGroupCode           varchar(64), not null
CBMTypeCode            varchar(64), not null
RatingCategoryCode     varchar(64), not null
MaintenanceToolCode    varchar(64), null
ConditionTestingCode   varchar(64), null
UoMCode                varchar(64), null
OEMStandardMin         float, null
OEMStandardMax         float, null
OEMOperatorMin         varchar(4), null
OEMOperatorMax         varchar(4), null
IsActive, audit   standard
```

### `CBMConfigRating`, `CBMConfigMaintenanceCategory` (child assignment per `CBMConfig`)
```
CBMConfigRating:
Id             PK, bigint, identity
CBMConfigId    bigint, not null
CBMConfigCode  varchar(64), null
RatingCode     varchar(64), not null
Version        int, not null
ValueMin, ValueMax        float, null
OperatorMin, OperatorMax  varchar(4), null
IsActive, audit   standard

CBMConfigMaintenanceCategory:
Id                       PK, bigint, identity
CBMConfigId              bigint, not null
CBMConfigCode            varchar(64), null
MaintenanceCategoryCode  varchar(64), not null
Version                  int, not null
IsActive, audit   standard
```

### `CBMGroup`, `CBMType`, `CBMMainCategory`, `CBMParameter` (master data taxonomy CBM)
```
CBMGroup:        Code PK, Name, IsActive, audit
CBMType:         Code PK, Name, IsActive, audit
CBMMainCategory: Code PK, Name, Description, IsActive, audit
CBMParameter:    Code PK, Name, IsActive, audit
```

### `CBMGroupTypeParameter` (mapping 3-arah Group×Type×Parameter)
```
CBMGroupCode      PK(1), varchar(64)
CBMTypeCode       PK(2), varchar(64)
CBMParameterCode  PK(3), varchar(64)   ← composite PK, tanpa surrogate Id
Description       varchar(max), null
IsActive, audit   standard
```

### `ConditionTesting`, `MaintenanceTool` (master data pendukung CBM)
```
ConditionTesting: Code PK, Name (null), Description, IsActive, audit
MaintenanceTool:  Code PK, Name (null), Description, IsActive, audit
```

---

## Master Data Umum

### `MaintenanceCategory`
```
Code                  PK, varchar(64)
Name                  varchar(256), not null
TypeCode              varchar(256), not null
IsPeriodicalService   bit, null   ← flag dasar untuk klasifikasi "PS" (lihat FormPSAssignment)
IsActive, audit   standard
```

### `Element`, `GroupElement`
```
Element:
GroupElementCode  varchar(64), not null   ← BUKAN bagian PK, meski selalu diisi
Code              PK, varchar(64)
Name              varchar(256), null
Type              varchar(64), not null
ReferenceId       uniqueidentifier, null
Description       varchar(max), null
IconUrl           varchar(256), null
IsShow            bit, not null
IsActive, audit   standard

GroupElement: Code PK, Name, IsActive, audit
```
> **Catatan struktur**: PK `Element` cuma `Code` (bukan composite dengan `GroupElementCode`) — artinya `Code` harus unik global lintas group, bukan unik per-group.

### `LookupMasterData` (generic lookup/enum table)
```
Code    PK, varchar(64)
Name    varchar(256), not null
Group   varchar(128), not null   ← pengelompokan enum; Code tetap harus unik global (PK cuma Code)
IsActive, audit   standard
```

### `OperationalEnvironment`
```
Code   PK, varchar(64)
Name   varchar(256), not null
IsActive, audit   standard
```

### `Configuration`
```
Id            PK, bigint, identity
Key           varchar(128), null
Description   varchar(1024), null
Value         varchar(max), null
IsActive      bit, not null
CreatedAt     datetime, null
CreatedBy     varchar(200), null
ModifiedAt    datetime, null
ModifiedBy    varchar(200), null
```
*(Sama pola dengan versi `maintenance-order` — audit kolom nullable, beda dari `maintenance-execution` yang punya `TenantCode`.)*

---

## System

### `AuditLog`
```
Id             PK, bigint, identity
TableName      nvarchar(256), not null
DataId         bigint, not null
Action         nvarchar(256), not null
PreviousData   nvarchar(max), not null
IsActive       bit, not null
CreatedAt      datetime, not null
CreatedBy      varchar(256), not null
```
Sama pola dengan versi `maintenance-execution`/`maintenance-order` (lihat [maintenance-execution-schema.md](maintenance-execution-schema.md)) — direplikasi per-service.

### `RevertTable`
Boilerplate default SSMS (`nchar(10)`, PK tanpa nama constraint) — bukan tabel bisnis, diabaikan.

---

## Observasi Belum Dibahas
- **`FormTask` tidak punya FK relational ke `Form`/`FormTab`** — relasi kemungkinan disimpan sebagai data (JSON?) di kolom `Tab`/`SectionTask`. Perlu klarifikasi kalau butuh query langsung "task apa saja ada di form/tab X".
- **`Element`/`LookupMasterData`**: PK hanya `Code` walau ada kolom pengelompokan (`GroupElementCode`/`Group`) — perlu diperhatikan saat seed data supaya tidak bentrok kode antar-group.
- Titik sambung ke service lain belum ditelusuri lebih jauh: `FormTask.Code` → `maintenance-execution.TaskPersonalizedFinding.FormTaskCode`, dan `MaintenanceCategory.Code` di sini kemungkinan jadi source-of-truth untuk `MaintenanceCategoryCode` yang dipakai berulang di `maintenance-order`/`maintenance-execution`.

---

## Referensi
- [maintenance-execution-schema.md](maintenance-execution-schema.md)
- [maintenance-order-schema.md](maintenance-order-schema.md)
