# Database Schema — `tenant`

*Sumber: DDL script asli (`DB Tenant.sql`), schema `dbo`, script date 05/08/2026 09:04:05 — skema real, bukan document-derived.*
*Disimpan: 05 Aug 2026.*

---

Dokumen ini referensi mentah struktur tabel `tenant`. Untuk narasi/business logic relasi User→Section→Asset, lihat [`user-asset-relation.md`](user-asset-relation.md).

> ✅ **Konfirmasi terhadap `user-asset-relation.md`**: relasi `tenant.SectionType.Code = tenant.OrganizationUnit.SectionTypeCode` (Bagian 1 doc tsb) **cocok dengan skema real di sini** — FK eksplisit `OrganizationUnit.SectionTypeCode` → `SectionType(Code, TenantCode)` ada di DDL. Relasi `User→OrganizationUnit` (via `UserEmploymentProfile`) masih belum bisa dikonfirmasi dari file ini — tabel itu tidak ada di DB `tenant` maupun di `usermanagement` ([`user-management-schema.md`](user-management-schema.md)).
>
> ⚠️ **Sebagian koreksi terhadap `user-management-schema.md`** baris 140: dokumen itu menduga tabel master `Role`/`Shift` (yang tidak ada FK-nya di `usermanagement`) "kemungkinan ada di DB `tenant`".
> - **Shift — dugaan itu benar**: `SiteShift.Id` (bigint identity) adalah tabel master Shift yang direferensikan `usermanagement.EmployeeShiftLog.ShiftId` (dikonfirmasi user 05 Aug 2026).
> - **Role — dikonfirmasi belum dipakai** (bukan master data yang hilang): Digiman+ saat ini belum punya konsep Role — permission di-mapping **langsung ke user** lewat `usermanagement.UserPermission` (dikonfirmasi user 05 Aug 2026). `RoleCode` di `usermanagement.UserRoleMapping` dan `tenant.MenuRole.RoleCode` kemungkinan kolom/tabel yang disiapkan untuk fitur Role di masa depan tapi belum aktif.

---

## Tenant / Site / Organization

### `Tenant`
```
Code           PK, varchar(64)
Name           varchar(64), not null
Description    varchar(128), not null
BusinessType   varchar(128), not null (default 'UNCATEGORIZED')
IsActive       bit, not null
CreatedBy      varchar(1000), not null
CreatedAt      datetime, not null
ModifiedBy     varchar(1000), not null
ModifiedAt     datetime, not null
```
Master tenant. Root dari semua tabel yang di-scope `TenantCode` di skema ini.

### `Site`
```
Code               PK (composite w/ TenantCode), varchar(64)
TenantCode         PK (composite), varchar(64), not null   FK → Tenant.Code
Name               varchar(100), not null
NameShort          varchar(10), not null
UtcOffset          int, not null
StartMorningShift  varchar(16), not null
StartNightShift    varchar(16), not null
IsHeadOffice       bit, not null (default 0)
IsActive           bit, not null
CreatedBy, ModifiedBy   varchar(1000)
CreatedAt, ModifiedAt   datetime
```

### `SiteShift`
```
Id             PK, bigint, identity
TenantCode     varchar(64), not null
SiteCode       varchar(64), not null
Name           varchar(128), not null
StartShift     varchar(8), not null
EndShift       varchar(8), not null (default '00:00:00')
IsActive       bit, not null (default 1)
CreatedBy      varchar(1000), not null
CreatedAt      datetime, not null
ModifiedBy     varchar(1000), null
ModifiedAt     datetime, null
```
FK `(SiteCode, TenantCode) → Site(Code, TenantCode)`. Jadwal shift per site — **ini tabel master Shift yang direferensikan `usermanagement.EmployeeShiftLog.ShiftId`** (dikonfirmasi user 05 Aug 2026; tidak ada FK eksplisit di DDL `usermanagement` karena lintas-DB, tapi `Id` bigint identity di sini cocok dengan tipe `ShiftId`).

### `SectionType`
```
Code           PK (composite w/ TenantCode), varchar(64)
TenantCode     PK (composite), varchar(64), not null   FK → Tenant.Code
Name           varchar(200), not null
IsActive       bit, not null (default 1)
CreatedBy      varchar(1000), not null
CreatedAt      datetime, not null
ModifiedBy     varchar(1000), null
ModifiedAt     datetime, null
```

### `OrganizationUnit`
```
Code               PK (composite w/ TenantCode), varchar(64)
TenantCode         PK (composite), varchar(64), not null   FK → Tenant.Code
ParentCode         varchar(64), null   FK (ParentCode, TenantCode) → OrganizationUnit(Code, TenantCode)  [self-referencing]
SectionTypeCode    varchar(64), null   FK (SectionTypeCode, TenantCode) → SectionType(Code, TenantCode)
UnitIdentifier     varchar(200), not null
Name               varchar(200), not null
Type               varchar(200), not null
IsActive           bit, not null (default 1)
CreatedBy          varchar(1000), not null
CreatedAt          datetime, not null
ModifiedBy         varchar(1000), null
ModifiedAt         datetime, null
```
Hierarki unit organisasi self-referencing (`ParentCode`) per tenant. Jembatan mapping User→Asset via `SectionTypeCode` (lihat [`user-asset-relation.md`](user-asset-relation.md) Bagian 1).

---

## RBAC / Navigasi

### `Menu`
```
Code           PK, varchar(64)
ParentCode     varchar(64), null   ← tidak ada FK eksplisit ke Menu.Code sendiri di DDL, meski nama menyiratkan hierarki
Name           varchar(64), not null
Path           varchar(128), not null
Icon           varchar(256), not null
Sequence       bigint, not null
IsActive       bit, not null
CreatedBy      varchar(1000), not null
CreatedAt      datetime, not null
ModifiedBy     varchar(1000), not null
ModifiedAt     datetime, not null
```

### `Module`
```
Code           PK, varchar(64)
Name           varchar(64), not null
IsActive       bit, not null
CreatedBy      varchar(1000), not null
CreatedAt      datetime, not null
ModifiedBy     varchar(1000), not null
ModifiedAt     datetime, not null
```

### `ModuleMenu`
```
ModuleCode     PK (composite), varchar(64), not null   FK → Module.Code
MenuCode       PK (composite), varchar(64), not null   FK → Menu.Code
IsActive       bit, not null
CreatedBy, ModifiedBy   varchar(1000)
CreatedAt, ModifiedAt   datetime
```

### `Permission`
```
Code           PK, varchar(64)
MenuCode       varchar(64), null   FK → Menu.Code
Name           varchar(64), null
ParentCode     varchar(64), null   FK (self) → Permission.Code
IsActive       bit, not null
CreatedBy      varchar(1000), not null
CreatedAt      datetime, not null
ModifiedBy     varchar(1000), not null
ModifiedAt     datetime, not null
```
Kandidat sumber `PermissionCode`/`ParentPermissionCode` yang direferensikan `usermanagement.UserPermission` ([`user-management-schema.md`](user-management-schema.md) — `Permission.Code` self-referencing via `ParentCode`, sama pola dengan `UserPermission.ParentPermissionCode`). Belum ada FK lintas-DB eksplisit (tidak mungkin lintas database di SQL Server tanpa linked server) — perlu dikonfirmasi ke tim codebase.

### `MenuRole`
```
MenuCode       PK (composite), varchar(64), not null   FK → Menu.Code
RoleCode       PK (composite), varchar(64), not null   ← tidak ada tabel Role master di skema ini
IsActive       bit, not null
CreatedBy, ModifiedBy   varchar(1000)
CreatedAt, ModifiedAt   datetime
```
`RoleCode` free-form tanpa FK. Tabel ini kemungkinan belum aktif dipakai — Digiman+ saat ini mapping permission langsung ke user via `usermanagement.UserPermission`, bukan lewat Role (dikonfirmasi user 05 Aug 2026, lihat catatan di atas).

---

## Tenant Config / Integrasi

### `TenantModule`
```
TenantCode     PK (composite), varchar(64), not null   FK → Tenant.Code
ModuleCode     PK (composite), varchar(64), not null   FK → Module.Code
ThemeId        bigint, not null
IsActive       bit, not null
CreatedBy, ModifiedBy   varchar(1000)
CreatedAt, ModifiedAt   datetime
```

### `TenantModuleConfig`
```
Id             PK, bigint, identity
TenantCode     varchar(64), not null   FK → Tenant.Code
ModuleCode     varchar(64), not null   FK → Module.Code
Name           varchar(64), not null
Value          varchar(128), not null
IsActive       bit, not null
CreatedBy, ModifiedBy   varchar(1000)
CreatedAt, ModifiedAt   datetime
```

### `TenantAzureAuthConfig`
```
Id                   PK, bigint, identity
TenantCode           varchar(64), not null   FK → Tenant.Code
ExtAuthPlatform      varchar(24), not null
AzureTenantId        varchar(200), not null
AzureClientId        varchar(200), not null
AzureClientConfig    varchar(200), null
IsActive             bit, not null
CreatedBy, ModifiedBy   varchar(1000)
CreatedAt, ModifiedAt   datetime
```
Config Azure B2C per tenant — sumber auth yang dipakai `usermanagement.AuthenticationLog`/JWT flow.

### `TenantPbiConfig`
```
Id             PK, int, identity
TenantCode     varchar(64), not null
ProfileId      varchar(100), not null
WorkspaceId    varchar(100), not null
WorkspaceName  varchar(200), not null
ReportName     varchar(100), not null
ReportId       varchar(100), not null
DatasetId      varchar(100), not null
IsActive       bit, not null (default 1)
CreatedBy      varchar(1000), not null (default 'system')
CreatedAt      datetime, not null (default getutcdate())
ModifiedBy     varchar(1000), not null (default 'system')
ModifiedAt     datetime, not null (default getutcdate())
```
UNIQUE `(TenantCode, ReportName)`. Config embed Power BI report per tenant. Tidak ada FK eksplisit ke `Tenant.Code` di DDL (beda dari tabel `Tenant*Config` lain yang semua FK).

### `TenantTelemeteryConfig` *(typo — perhatikan ejaan)*
```
Id             PK, bigint, identity
TenantCode     varchar(64), not null   FK → Tenant.Code
ProductCode    varchar(100), not null
Type           varchar(100), not null
Configuration  varchar(max), null
IsActive       bit, not null
CreatedBy      varchar(1000), not null
CreatedAt      datetime, not null
ModifiedBy     varchar(1000), not null
ModifiedAt     datetime, not null
```

### `TenantTelemetryConfig` *(ejaan benar — tabel terpisah, bukan typo yang sama)*
```
Id             PK, bigint, identity
TenantCode     varchar(64), not null   FK (named constraint FK_TenantTelemetryConfig_Tenant) → Tenant.Code
ProductCode    varchar(100), not null
Type           varchar(100), not null
Configuration  nvarchar(max), not null
IsActive       bit, not null
CreatedBy      varchar(255), not null
CreatedAt      datetimeoffset(7), not null
ModifiedBy     varchar(255), not null
ModifiedAt     datetimeoffset(7), not null
```
Dua tabel nyaris identik hanya beda 1 huruf ejaan (`Telemetery` vs `Telemetry`). Versi ini lebih baru — `Configuration` jadi `nvarchar` `not null` (bukan `varchar` nullable), audit kolom pakai `datetimeoffset` (bukan `datetime`), constraint FK diberi nama eksplisit. Kemungkinan migrasi rename yang belum cleanup tabel lama (`TenantTelemeteryConfig` kemungkinan bisa di-drop setelah dikonfirmasi tidak dipakai lagi) — perlu dikonfirmasi ke tim codebase, bukan diasumsikan aman untuk dihapus.

---

## Legacy / Tidak Jelas Statusnya

### `Tenants` *(plural — tabel terpisah dari `Tenant`)*
```
TenantId               PK, int, identity
Name                   nvarchar(100), not null
ProfileName            nvarchar(100), not null
StartDate              datetime, null
EndDate                datetime, null
WorkspaceId            nvarchar(1000), null
WorkspaceUrl           nvarchar(1000), null
DatabaseServer         nvarchar(1000), null
DatabaseName           nvarchar(1000), null
DatabaseUserName       nvarchar(1000), null
DatabaseUserPassword   nvarchar(1000), null
Created                datetime, null
```
> ⚠️ Tabel provisioning tenant model lama (per-tenant database terpisah — `DatabaseServer`/`DatabaseName`/`DatabaseUserName`/`DatabaseUserPassword` eksplisit per row), tidak nyambung ke `Tenant.Code` (PK `TenantId int`, bukan `Code varchar`). Kemungkinan sisa dari arsitektur multi-tenant generasi sebelumnya (single-tenant-per-DB) sebelum pindah ke model shared-DB + `TenantCode` scoping yang dipakai tabel lain di skema ini. **`DatabaseUserPassword` disimpan sebagai kolom biasa (tidak ada indikasi encryption/masking di DDL)** — perlu dikonfirmasi ke tim codebase apakah tabel ini masih live/dipakai, karena kalau ya ini risiko keamanan (password DB tersimpan plain di kolom `nvarchar`).

### `Profiles`
```
ProfileId      PK, nvarchar(50), not null
ProfileName    nvarchar(100), not null
Exclusive      bit, not null
Created        datetime, null
```
Tidak ada `TenantCode`/audit kolom standar (`CreatedBy`/`IsActive`) seperti tabel lain di skema ini — pola beda, kemungkinan tabel lama juga (sepasang dengan `Tenants` di atas, bukan dengan `Tenant`/`TenantPbiConfig` yang polanya konsisten).

### `MaintivaPOCMenu`
```
MenuId         PK?, int, not null   ← tidak ada constraint PRIMARY KEY eksplisit di DDL meski NOT NULL
MenuName       varchar(300), null
SubMenuName    varchar(300), null
WorkspaceId    varchar(2000), null
ReportId       varchar(2000), null
DatasetId      varchar(2000), null
CreatedDate    datetime2(7), null (default getutcdate())
```
Nama `POC` (proof of concept) — kemungkinan tabel eksperimen, prekursor `TenantPbiConfig`/`Menu` sebelum jadi tabel resmi. Tidak ada `TenantCode` scoping maupun audit kolom standar.

### `deleteme_equipment`
```
site_id                nvarchar(10), null
site_description       nvarchar(100), null
equipment_hierarchy    nvarchar(200), null
model_unit             nvarchar(200), null
equipment_id           int, null
equipment              nvarchar(20), null
```
Nama tabel eksplisit menandakan scratch/temp (`deleteme_*`) — bukan bagian schema resmi, kemungkinan aman diabaikan dari dokumentasi ke depannya kalau memang sudah dihapus dari DB.

---

## Referensi
- [`user-asset-relation.md`](user-asset-relation.md) — narasi relasi User→Section(OrganizationUnit)→Asset, sebagian terkonfirmasi lewat skema ini
- [`user-management-schema.md`](user-management-schema.md) — skema `usermanagement` (auth/access-control), beberapa referensi silang ke `Role`/`Permission` yang belum bisa dikonfirmasi lintas-DB
