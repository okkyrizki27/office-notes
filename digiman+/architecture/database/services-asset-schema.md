# Database Schema — `services-asset`

*Sumber: DDL script asli (`asset.sql`), schema `dbo`, script date 15/07/2026 1:58 PM — skema real, bukan document-derived.*
*Disimpan: 15 Jul 2026.*
*DB: `cst-iams-sqldb-services-asset`, alias `asset` — lihat [`user-asset-relation.md`](user-asset-relation.md) dan [`new-model-checklist.md`](new-model-checklist.md).*

---

Dokumen ini referensi mentah struktur tabel `services-asset`. Untuk narasi/business logic, lihat [`user-asset-relation.md`](user-asset-relation.md) (relasi User→Section→Asset, hierarki Model→Component→SubComponent→DamageCode), [`new-model-checklist.md`](new-model-checklist.md) (checklist onboarding model baru), dan [`area-of-unit-man-power-enhancement.md`](../inspection-order/area-of-unit-man-power-enhancement.md) (enhancement Master Data mapping Area of Unit, dikembangkan di service ini).

---

## Asset Attribute Master Data

Master data kecil, pola seragam (`Code` PK varchar(64), `Name` varchar(200), `IsActive`, audit) kecuali disebutkan lain:

```
AssetType         Code PK, Name
AssetClass        Code PK, Name
AssetVariant      Code PK, Name
AssetModel        Code PK, Name
AssetBrand        Code PK, Name
AssetCategory     Code PK, Name
AssetSection      Code PK, Name                                          ← audit varchar(128), bukan (200); belum jelas beda konsep dari tenant.SectionType — lihat Observasi
AssetOwnership    Code PK, Name, Description varchar(200) not null
UnitOfMeasurement Code PK, Name, Description varchar(200) not null
```

---

## Asset Core

### `Asset`
```
Id                    PK, bigint, identity
BlobPath              varchar(200), null
AssetNumber           varchar(200), not null
SiteCode              varchar(64), not null
AssetTypeCode         varchar(64), null
AssetClassCode        varchar(64), null
AssetVariantCode      varchar(64), null
AssetModelCode        varchar(64), not null
BrandCode             varchar(64), null
AssetCategoryCode     varchar(64), null
SectionTypeCode       varchar(64), not null   ← kolom langsung di Asset, lihat catatan di bawah
AssetOwnershipCode    varchar(64), null
UoMCode               varchar(64), null
TargetLife            varchar(200), null
AssetSerialNumber     varchar(200), null
AssetDealer           varchar(200), null
Status                varchar(200), null
IsActive              bit, not null (default 1)
CreatedAt, CreatedBy  datetime/varchar(200), not null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **⚠️ Kemungkinan perlu koreksi di [`user-asset-relation.md`](user-asset-relation.md) poin 3**: dokumen itu mengklaim relasi Asset → OrganizationUnit lewat `asset.Asset.AssetModelCode = tenant.OrganizationUnit.SectionTypeCode`. Skema real menunjukkan `Asset` punya kolom **`SectionTypeCode` sendiri** (NOT NULL, langsung di tabel, bukan cuma lewat `AssetModelCode`). Kemungkinan relasi yang benar adalah `asset.Asset.SectionTypeCode = tenant.OrganizationUnit.SectionTypeCode` — perlu diverifikasi ke tim yang pegang codebase sebelum dokumen lama diperbaiki, karena ini bagian penting dari alur akses data user→asset.
>
> Field lain (`AssetTypeCode`, `AssetClassCode`, `AssetVariantCode`, `BrandCode`, `AssetCategoryCode`, `AssetOwnershipCode`, `UoMCode`, `TargetLife`, `AssetSerialNumber`, `AssetDealer`, `Status`) belum pernah didetailkan di dokumen manapun sebelumnya — baru terlihat di sini.

### `AssetStatus`
```
Id             PK, int, identity
TrDate         datetime, not null
AssetNumber    varchar(50), not null
Status         varchar(20), not null
CreatedAt      datetime, not null (default getutcdate())
```
Log histori perubahan status asset (tanpa `CreatedBy`/`ModifiedAt`/`IsActive` — beda pola dari tabel lain, kemungkinan pure event log).

### `AssetModelMapping` (bridge)
```
Id                PK, bigint, identity
Code              varchar(64), not null, UNIQUE
AssetTypeCode     varchar(64), null
AssetBrandCode    varchar(64), not null
AssetModelCode    varchar(64), not null
AssetVariantCode  varchar(64), null
AssetClassCode    varchar(64), null
IsActive          bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(256), not null
ModifiedAt, ModifiedBy datetime/varchar(256), null
```
> **Konfirmasi** struktur yang sudah disebut di [`user-asset-relation.md`](user-asset-relation.md) dan [`new-model-checklist.md`](new-model-checklist.md) — tapi detail baru: bridge ini sebenarnya **5 dimensi** (`AssetType`, `AssetBrand`, `AssetModel`, `AssetVariant`, `AssetClass`), bukan cuma `AssetModelCode`. Hanya `AssetBrandCode`/`AssetModelCode` yang `NOT NULL`; `AssetTypeCode`/`AssetVariantCode`/`AssetClassCode` nullable. **Relevan untuk open item di [`area-of-unit-man-power-enhancement.md`](../inspection-order/area-of-unit-man-power-enhancement.md) Bagian 4** ("apakah mapping Area↔Component-SubComponent scoped per Asset Model, mengikuti pola existing?") — pola existing yang dimaksud (`ModelComponentSubComponent`, lihat di bawah) ternyata scoped lewat `AssetModelMappingCode` (5 dimensi), **bukan** `AssetModelCode` polos. Kalau mapping Area baru mengikuti pola yang sama persis, dependency-nya bukan cuma ke `AssetModel`, tapi ke kombinasi 5 dimensi `AssetModelMapping` — perlu diperhitungkan saat desain skema mapping baru.

### `ClientAssetMapping`
```
Id                PK, bigint, identity
AssetModelCode    varchar(64), not null
AssetTypeCode     varchar(64), null
SectionTypeCode   varchar(64), not null
IsActive          bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(256), not null
ModifiedAt, ModifiedBy datetime/varchar(256), null
```
> Belum pernah dibahas di dokumen manapun. Tampaknya mapping per-client: `AssetModel` (+ opsional `AssetType`) ke `SectionType`. **Tidak ada kolom `TenantCode`** di tabel ini — beda dari `Configuration`/`DeadLetterLog`/`TopicPublishLog` di service yang sama yang eksplisit multi-tenant lewat `TenantCode`. Perlu diklarifikasi bagaimana isolasi per-client dilakukan di sini (row-level lewat kolom lain yang tidak terlihat dari nama tabel, atau DB terpisah per client).

### `SectionUserEquipmentMapping`
```
Id               PK, bigint, identity
SectionId        varchar(64), not null
SectionName      varchar(64), not null
SectionTypeCode  varchar(64), not null
SectionTypeName  varchar(200), null
IsActive         bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(128), not null
ModifiedAt, ModifiedBy datetime/varchar(128), null
```
UNIQUE `(SectionId, SectionTypeCode)`. Kemungkinan snapshot/cache dari `tenant.OrganizationUnit` di sisi service asset (nama kolom `SectionId`/`SectionName`/`SectionTypeCode`/`SectionTypeName` mirip persis field yang direlasikan di [`user-asset-relation.md`](user-asset-relation.md)) — belum dikonfirmasi.

---

## Component / Damage / Rating

### `Component`, `SubComponent`
```
Code PK varchar(64), Name varchar(200) not null, IsActive, audit(200)
```
> **Sudah didokumentasikan** di [`user-asset-relation.md`](user-asset-relation.md) — konsisten dengan skema real ini.

### `SubComponentDamage`
```
Id                 PK, bigint, identity
SubComponentCode   varchar(64), not null
DamageCode         varchar(64), not null
IsActive           bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), not null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **Sudah didokumentasikan** di [`user-asset-relation.md`](user-asset-relation.md) (mapping SubComponent → DamageCode) — konsisten.

### `DamageCode`
```
Code             PK, varchar(64)
DamageGroupCode  varchar(64), not null
Name             varchar(200), not null
Description      varchar(max), not null (default '')
IsActive         bit, not null
CreatedAt, CreatedBy   datetime/varchar(128), not null
ModifiedAt, ModifiedBy datetime/varchar(128), null
```
> `DamageGroupCode` belum disebut sebelumnya — DamageCode ternyata punya grouping sendiri (`DamageGroup`), mirip pola `CauseCode`/`CauseGroup` di bawah.

### `DamageGroup`
```
Code PK varchar(64), Name varchar(200) not null, Description varchar(max) not null (default ''), IsActive, audit(128)
```

### `CauseCode`
```
Code             PK, varchar(64)
CauseGroupCode   varchar(64), not null
Name             varchar(200), not null
Description      varchar(max), not null (default '')
IsActive         bit, not null
CreatedAt, CreatedBy   datetime/varchar(128), not null
ModifiedAt, ModifiedBy datetime/varchar(128), null
```

### `CauseGroup`
```
Code PK varchar(64), Name varchar(200) not null, Description varchar(max) not null (default ''), IsActive, audit(128)
```

### `ActionRemedy`
```
Code             PK, varchar(64)
Name             varchar(200), not null
Description      varchar(max), not null (default '')
IsActive         bit, not null
CreatedAt, CreatedBy   datetime/varchar(128), not null
ModifiedAt, ModifiedBy datetime/varchar(128), null
```

### `Priority`
```
Code, Group        PK (composite), varchar(64) each
Name               varchar(15), not null
Description        varchar(max), not null (default '')
EDD                int, not null                    ← Estimated Delivery/Duration Days (asumsi)
TextColor          varchar(15), null
BackgroundColor    varchar(15), null
IsActive           bit, not null
CreatedAt, CreatedBy   datetime/varchar(128), not null
ModifiedAt, ModifiedBy datetime/varchar(128), null
```
PK komposit `(Code, Group)` — satu `Code` bisa berulang lintas `Group` berbeda, belum jelas apa signifikansi `Group` ini (per-tenant? per-module?).

### `RatingCategory`
```
Code PK varchar(64), Name varchar(200) not null, IsActive, audit(200)
```

### `Rating`
```
Code                PK, varchar(64)
RatingCategoryCode  varchar(64), not null
Sequence            int, not null (default 0)
Name                varchar(200), not null
TextColor           varchar(15), null
BackgroundColor     varchar(15), null
Note                varchar(max), not null (default '')
ImageUrl            varchar(max), not null (default '')
IsActive            bit, not null
CreatedAt, CreatedBy   datetime/varchar(128), not null
ModifiedAt, ModifiedBy datetime/varchar(128), null
```

### `ModelComponentSubComponent` (mapping utama Model → Component → SubComponent)
```
Id                     PK, bigint, identity
AssetModelMappingCode  varchar(64), not null
ComponentCode          varchar(64), not null
SubComponentCode       varchar(64), not null
RatingCategoryCode     varchar(64), null   ← belum pernah dibahas sebelumnya
IsActive               bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), not null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **Sudah didokumentasikan** di [`user-asset-relation.md`](user-asset-relation.md) dan [`new-model-checklist.md`](new-model-checklist.md) — join chain via `AssetModelMappingCode` terkonfirmasi persis. **Temuan baru**: kolom **`RatingCategoryCode`** — tiap kombinasi Model-Component-SubComponent punya `RatingCategory` sendiri, kemungkinan menentukan pilihan `Rating` mana yang tampil saat inspeksi untuk kombinasi tersebut (lihat `Rating`/`RatingCategory` di atas). Belum pernah disinggung di dokumen manapun — relevan untuk narasi cascading dropdown di [`area-of-unit-man-power-enhancement.md`](../inspection-order/area-of-unit-man-power-enhancement.md) 2.2/2.4 kalau Rating juga ikut ditentukan oleh kombinasi ini.

---

## Config & Feature

### `Configuration`
```
Id             PK, bigint, identity
TenantCode     nvarchar(200), not null
Key            nvarchar(200), not null
Description    nvarchar(max), not null
Value          nvarchar(max), not null
IsActive       bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
Punya `TenantCode` — beda dari `maintenance-order.Configuration` yang menurut catatan di [`maintenance-order-schema.md`](maintenance-order-schema.md) **tidak** punya kolom ini.

### `Feature`
```
Id              PK, bigint, identity
FeatureName     nvarchar(200), not null
Description     nvarchar(200), not null
Type            nvarchar(200), not null
Platform        nvarchar(200), not null
Status          nvarchar(200), not null
IsActive        bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
Beda shape dari `maintenance-execution.Feature` ([`maintenance-execution-schema.md`](maintenance-execution-schema.md)) — versi itu punya `PermissionCode`, versi ini punya `Description`/`Status` — tampaknya tabel `Feature` direplikasi per-service dengan skema yang tidak identik (bukan shared table).

---

## Audit, Integration & System

### `AuditLog`
```
Id             PK, bigint, identity
TableName      nvarchar(200), not null
DataId         bigint, not null
Action         nvarchar(200), not null
PreviousData   nvarchar(max), not null
IsActive       bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```

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

### `TopicPublishLog`
```
Id              PK, bigint, identity
TopicName       varchar(200), not null
MessagePayload  nvarchar(max), not null
TenantCode      varchar(50), null
Type            varchar(100), null
SessionId       varchar(200), null
IsPublished     bit, not null (default 0)
PublishedAt     datetime, null
TraceId         varchar(500), null
CreatedAt       datetime, not null (default getutcdate())
RetryCount      int, not null (default 0)
ErrorMessage    nvarchar(max), null
```
Sama pola outbox dengan `maintenance-order.TopicPublishLog`/`maintenance-execution.TopicPublishLog` — direplikasi per-service.

*(`AzureSQLMaintenanceLog`, `AzureSQLMaintenanceOverride` — tabel sistem Azure SQL bawaan (index/statistics maintenance job), bukan business schema, tidak didetailkan di sini — sama seperti di `maintenance-execution-schema.md`.)*

---

## Observasi Belum Dibahas
- **`Asset.SectionTypeCode`** — kemungkinan koreksi ke [`user-asset-relation.md`](user-asset-relation.md) poin 3, lihat catatan di bawah tabel `Asset` di atas. Perlu diverifikasi ke engineer sebelum dokumen lama diedit.
- **`ModelComponentSubComponent.RatingCategoryCode`** — field baru, belum dibahas relasinya ke narasi Rating saat inspeksi/finding. Relevan untuk enhancement Area of Unit.
- **`AssetModelMapping` 5 dimensi** (bukan cuma `AssetModelCode`) — relevan untuk keputusan scoping mapping Area baru, lihat open item Bagian 4 [`area-of-unit-man-power-enhancement.md`](../inspection-order/area-of-unit-man-power-enhancement.md).
- **`ClientAssetMapping`** — tabel baru yang belum pernah dibahas, tidak punya `TenantCode` meski namanya menyiratkan konsep per-client. Perlu klarifikasi mekanisme isolasi datanya.
- **`AssetSection`** — belum jelas beda konsepnya dari `tenant.SectionType`; nama mirip tapi living di DB berbeda.
- **`Priority.Group`** (bagian dari PK komposit) — signifikansinya belum jelas (per-tenant/per-module/lainnya).
- **`AssetStatus`** — pure event log (tanpa audit `CreatedBy`/`IsActive`), pola beda dari tabel lain di service ini — belum dibahas siapa/apa yang menulis ke tabel ini dan kapan.

---

## Referensi
- [`user-asset-relation.md`](user-asset-relation.md) — narasi relasi User→Section→Asset dan Model→Component→SubComponent→DamageCode (document-derived, sekarang sebagian besar terkonfirmasi cocok dengan DDL real ini, kecuali catatan poin 3 di atas)
- [`new-model-checklist.md`](new-model-checklist.md) — checklist onboarding model baru, referensi tabel yang sama
- [`../inspection-order/area-of-unit-man-power-enhancement.md`](../inspection-order/area-of-unit-man-power-enhancement.md) — enhancement Master Data mapping Area of Unit ↔ Component/SubComponent, dikembangkan di service `services-asset`
- [`maintenance-order-schema.md`](maintenance-order-schema.md), [`maintenance-execution-schema.md`](maintenance-execution-schema.md), [`user-management-schema.md`](user-management-schema.md) — skema service lain untuk perbandingan pola (`Configuration`, `Feature`, `AuditLog`, `TopicPublishLog` direplikasi per-service dengan variasi shape)
