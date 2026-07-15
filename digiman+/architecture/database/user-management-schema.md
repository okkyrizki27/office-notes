# Database Schema — `usermanagement`

*Sumber: DDL script asli (`usermanagement.sql`), schema `dbo`, script date 15/07/2026 1:56 PM — skema real, bukan document-derived.*
*Disimpan: 15 Jul 2026.*

---

Dokumen ini referensi mentah struktur tabel `usermanagement`. Untuk narasi/business logic terkait user↔asset↔organization, lihat [`user-asset-relation.md`](user-asset-relation.md).

> ⚠️ **Perlu diklarifikasi**: [`user-asset-relation.md`](user-asset-relation.md) mendaftar DB alias `user` = `cst-shared-sqldb-user` ("Data user, employment profile"), berisi tabel `UserEmploymentProfile` yang jadi kunci relasi User→OrganizationUnit (`user.UserEmploymentProfile.SectionId`). Skema real di file ini (`usermanagement.sql`) **tidak punya tabel `UserEmploymentProfile`** — isinya murni auth/access-control (login, device, grup, permission, role). Kemungkinan `usermanagement` adalah **database terpisah** dari `cst-shared-sqldb-user`, atau nama alias yang sama merujuk ke DB yang salah di dokumen lama. Perlu dikonfirmasi ke tim yang pegang codebase sebelum relasi di `user-asset-relation.md` dianggap valid terhadap skema ini.

---

## Auth & Access Log

### `AuthenticationLog`
```
Id             PK, bigint, identity
UserCode       varchar(128), MASKED (default()), null
Type           varchar(200), null
Date           datetime, null
Device         varchar(200), null
Platform       varchar(200), null
IsSuccess      bit, not null (default 1)
IsActive       bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
Log setiap percobaan login (`IsSuccess`), per device/platform. `UserCode` di-mask (Dynamic Data Masking, default()) — kemungkinan PII (email).

### `BlockedUser`
```
Id             PK, bigint, identity
UserCode       varchar(128), MASKED (default()), null
IsActive       bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
Daftar user yang diblokir. Tidak ada kolom alasan/durasi blokir — kemungkinan block bersifat permanen sampai row di-set `IsActive = 0`, atau alasan disimpan di `AuditLog`.

### `AuditLog`
```
Id             PK, bigint, identity
TableName      varchar(200), null
DataId         bigint, not null
Action         varchar(200), null
PreviousData   varchar(max), MASKED (default()), null
IsActive       bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
Sama pola nama dengan `services-asset.AuditLog` ([`services-asset-schema.md`](services-asset-schema.md)) tapi shape beda: versi ini `PreviousData` di-mask dan semua kolom (`TableName`/`Action`/dst.) nullable, versi asset semua `not null` — tabel `AuditLog` direplikasi per-service dengan variasi shape, sama seperti `Configuration`/`Feature`/`TopicPublishLog` di service lain.

---

## Device & Session

### `Device`
```
Id                     PK, bigint, identity
UserCode               varchar(64),  MASKED (default()), null
DeviceRegistrationId   varchar(200), MASKED (default()), null
DeviceId               datetime,     MASKED (default()), null   ← tipe kolom aneh, lihat catatan
AppVersion             varchar(200), null
SystemVersion          varchar(200), null
SystemBuildId          varchar(200), null
BrandName              varchar(200), null
DeviceModel            varchar(200), null
IsActive               bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> `DeviceId` bertipe **`datetime`**, bukan `varchar`/`uniqueidentifier` seperti biasanya untuk kolom "Id" — kemungkinan salah desain di DB asli (typo tipe kolom saat migration) atau nama menyesatkan (isinya sebenarnya timestamp registrasi, bukan identifier). Perlu diverifikasi ke tim codebase sebelum diasumsikan sebagai bug.

### `EmployeeShiftLog`
```
Id             PK, bigint, identity
UserCode       varchar(128), MASKED (default()), null
ShiftId        bigint, null
IsActive       bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
Constraint default bernama `DF_TempMOList_IsActive` — nama menyebut `TempMOList`, tidak match nama tabel `EmployeeShiftLog`. Kemungkinan tabel ini rename dari nama sebelumnya (`TempMOList`) tanpa update nama constraint. `ShiftId` tidak punya FK eksplisit ke tabel Shift manapun di skema ini — tabel `Shift` kemungkinan ada di DB lain atau belum di-generate di script ini.

---

## Group / Role / Permission

### `UserGroup`
```
Code           PK (composite w/ TenantCode), varchar(64), not null
TenantCode     PK (composite), varchar(64), not null
Name           varchar(32), null
Description    varchar(512), null
IsActive       bit, not null
CreatedBy      varchar(1000), not null
CreatedAt      datetime, not null
ModifiedBy     varchar(1000), null
ModifiedAt     datetime, null
```
PK komposit `(Code, TenantCode)` — beda pola dari `UserPermission`/`UserRoleMapping` di bawah yang pakai `Id` surrogate. `TenantCode` di sini eksplisit bagian dari identity grup (scoped per tenant), konsisten dengan pola multi-tenant (`Configuration.TenantCode`, dst. di service lain).

### `UserGroupMember`
```
Id             PK, bigint, identity
UserCode       varchar(128), not null   ← tidak di-mask, beda dari UserCode di tabel lain
GroupCode      varchar(64), not null
TenantCode     varchar(64), not null
IsActive       bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
FK `(GroupCode, TenantCode) → UserGroup(Code, TenantCode)`. Menghubungkan user ke `UserGroup` dalam scope tenant tertentu.
> **Observasi**: `UserCode` di tabel ini **tidak** kena Dynamic Data Masking, sedangkan di `UserPermission`/`AuthenticationLog`/`BlockedUser`/`Device`/`EmployeeShiftLog` kena mask. Inkonsistensi kebijakan masking — mungkin oversight, mungkin disengaja karena `UserGroupMember` dianggap lebih rendah sensitivitasnya.

### `UserPermission`
```
Id                       PK, bigint, identity
TenantCode               varchar(64), not null (default 'BUMAID')
UserCode                 varchar(128), MASKED (default()), null
ParentPermissionCode     varchar(64), null
PermissionCode           varchar(64), null
IsActive                 bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
`ParentPermissionCode` menunjukkan `PermissionCode` bersifat **hierarkis** (parent-child, kemungkinan untuk grouping menu/fitur bertingkat). Default `TenantCode = 'BUMAID'` — hardcoded ke satu tenant spesifik, kemungkinan tenant awal/default sebelum multi-tenant lain onboard.
> **Cross-reference**: `PermissionCode` di sini kemungkinan yang direferensikan oleh `maintenance-execution.Feature.PermissionCode` (lihat [`maintenance-execution-schema.md`](maintenance-execution-schema.md)) — `Feature` di service `maintenance-execution` menyimpan `PermissionCode` untuk menentukan akses fitur per permission. Relasi lintas-DB ini belum pernah didokumentasikan sebelumnya, perlu dikonfirmasi.

### `UserRoleMapping`
```
Id             PK, bigint, identity
UserCode       varchar(128), MASKED (default()), null
RoleCode       varchar(64), null
IsActive       bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
Tidak ada tabel `Role` master di skema ini — `RoleCode` free-form tanpa FK, sama seperti `EmployeeShiftLog.ShiftId` tanpa FK ke `Shift`. Kemungkinan tabel master `Role`/`Shift` ada di DB lain (misalnya `tenant`) yang tidak tercakup di script ini.

---

## Config

### `Configuration`
```
Id             PK, bigint, identity
TenantCode     varchar(200), null
Key            varchar(200), null
Description    varchar(200), null
Value          varchar(max), null
IsActive       bit, not null (default 1)
CreatedAt, CreatedBy   datetime/varchar(200), null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
Pola sama dengan `Configuration` di service lain ([`services-asset-schema.md`](services-asset-schema.md), [`maintenance-execution-schema.md`](maintenance-execution-schema.md)) — direplikasi per-service, tapi di sini semua kolom nullable (termasuk `TenantCode`/`Key`/`Value`), beda dari versi `services-asset` yang `not null`.

---

## Observasi Belum Dibahas
- **DB `usermanagement` vs alias `user` (`cst-shared-sqldb-user`)** — lihat catatan di atas, kemungkinan dua DB berbeda; `UserEmploymentProfile` (kunci relasi ke `OrganizationUnit` di [`user-asset-relation.md`](user-asset-relation.md)) tidak ada di skema ini. **Perlu klarifikasi paling prioritas** sebelum dokumen relasi lain dianggap konsisten dengan skema real ini.
- **`Device.DeviceId` bertipe `datetime`** — kemungkinan bug desain, perlu verifikasi.
- **`EmployeeShiftLog`** constraint bernama `DF_TempMOList_IsActive` — sisa nama tabel lama (`TempMOList`), tidak match nama tabel saat ini.
- **`UserGroupMember.UserCode` tidak di-mask** sementara kolom `UserCode` di tabel lain (`UserPermission`, `AuthenticationLog`, `BlockedUser`, `Device`, `EmployeeShiftLog`) di-mask — inkonsistensi kebijakan masking, belum jelas disengaja atau oversight.
- **`RoleCode` (UserRoleMapping) dan `ShiftId` (EmployeeShiftLog)** — tidak ada tabel master `Role`/`Shift` di skema ini, tidak ada FK. Master data-nya kemungkinan di DB lain.
- **`UserPermission.PermissionCode` ↔ `maintenance-execution.Feature.PermissionCode`** — kemungkinan relasi lintas-DB yang belum pernah dibahas, relevan untuk memahami bagaimana akses fitur ditentukan lintas service.

---

## Referensi
- [`user-asset-relation.md`](user-asset-relation.md) — narasi relasi User→Section→Asset (perlu ditinjau ulang terhadap skema ini, lihat peringatan di atas)
- [`services-asset-schema.md`](services-asset-schema.md), [`maintenance-order-schema.md`](maintenance-order-schema.md), [`maintenance-execution-schema.md`](maintenance-execution-schema.md) — skema service lain untuk perbandingan pola (`Configuration`, `AuditLog` direplikasi per-service dengan variasi shape)
