# Checklist: Onboarding Model Baru

Gunakan checklist ini setiap kali ada model asset baru yang perlu dikonfigurasi agar user dapat mengakses data dengan benar.

Urutan mengikuti dependency chain: Tenant → Asset → User.

---

## 1. Tenant DB (`cst-shared-sqldb-tenant`)

### Section Type
- [ ] `tenant.SectionType` — pastikan SectionType untuk model ini sudah ada
  - Jika belum: tambahkan record baru di tabel `SectionType`

### Organization Unit
- [ ] `tenant.OrganizationUnit.SectionTypeCode` — pastikan ada OrganizationUnit yang memiliki `SectionTypeCode` sesuai dengan model baru
  - Verifikasi: `SELECT * FROM OrganizationUnit WHERE SectionTypeCode = '<model_code>'`
- [ ] Pastikan `OrganizationUnit.Code` dan `OrganizationUnit.UnitIdentifier` sudah terisi dengan benar (keduanya digunakan sebagai referensi dari user)

---

## 2. Asset DB (`cst-iams-sqldb-services-asset`)

### Asset Model Master
- [ ] `asset.AssetModel` — record model sudah ada
  - Verifikasi: `SELECT * FROM AssetModel WHERE Code = '<model_code>'`
  - Jika belum: tambahkan record baru

### Asset Model Mapping (Bridge)
- [ ] `asset.AssetModelMapping` — record mapping sudah ada untuk model ini
  - Verifikasi: `SELECT * FROM AssetModelMapping WHERE AssetModelCode = '<model_code>'`
  - Jika belum: tambahkan record baru (diperlukan sebagai bridge ke `ModelComponentSubComponent`)

### Component & SubComponent Master
- [ ] `asset.Component` — semua component yang akan dipakai model ini sudah ada di master
- [ ] `asset.SubComponent` — semua sub-component yang akan dipakai sudah ada di master

### Model → Component → SubComponent Mapping
- [ ] `asset.ModelComponentSubComponent` — mapping sudah dibuat untuk model ini
  - Verifikasi:
    ```sql
    SELECT b.AssetModelCode, a.ComponentCode, a.SubComponentCode
    FROM ModelComponentSubComponent a
    JOIN AssetModelMapping b ON a.AssetModelMappingCode = b.Code
    WHERE b.AssetModelCode = '<model_code>'
    ```
  - Jika belum: tambahkan record untuk setiap kombinasi Component + SubComponent

### Area of Unit Mapping *(ditambahkan 16 Jul 2026 — lihat [`area-of-unit-man-power-enhancement.md`](../inspection-order/area-of-unit-man-power-enhancement.md) 2.2)*
- [ ] `asset.Area` — Area yang relevan untuk model ini sudah ada di master
- [ ] `asset.ModelComponentSubComponent.AreaCode` — setiap baris mapping Component+SubComponent milik model ini sudah di-assign `AreaCode`-nya
  - Verifikasi:
    ```sql
    SELECT b.AssetModelCode, a.ComponentCode, a.SubComponentCode, a.AreaCode
    FROM ModelComponentSubComponent a
    JOIN AssetModelMapping b ON a.AssetModelMappingCode = b.Code
    WHERE b.AssetModelCode = '<model_code>'
    ```
  - Jika `AreaCode` NULL untuk sebagian/semua baris: lengkapi lewat Master Data UI (assign Area per baris) — **1 baris = maksimal 1 Area** (bukan M:N, lihat catatan desain di dokumen enhancement)
  - Catatan: Area di-assign **per baris per model** — tidak otomatis ke-reuse dari model lain meski Component+SubComponent-nya sama (lihat konsekuensi maintenance data di dokumen enhancement)

### Damage Code Mapping
- [ ] `asset.DamageCode` — damage code yang relevan sudah ada di master
- [ ] `asset.SubComponentDamage` — setiap SubComponent sudah di-mapping ke DamageCode yang sesuai
  - Verifikasi: `SELECT * FROM SubComponentDamage WHERE SubComponentCode IN ('<list_subcomponent>')`

### Asset Data
- [ ] `asset.Asset.AssetModelCode` — asset (equipment) sudah memiliki `AssetModelCode` yang benar
  - Verifikasi: `SELECT AssetNumber, AssetModelCode FROM Asset WHERE AssetModelCode = '<model_code>'`

---

## 3. User DB (`cst-shared-sqldb-user`)

### User Employment Profile
- [ ] `user.UserEmploymentProfile.SectionId` — user yang perlu akses ke model ini sudah memiliki `SectionId` yang cocok dengan `OrganizationUnit.Code` atau `OrganizationUnit.UnitIdentifier`
  - Verifikasi:
    ```sql
    SELECT u.UserId, u.SectionId, o.Code, o.UnitIdentifier, o.SectionTypeCode
    FROM UserEmploymentProfile u
    JOIN [tenant].[dbo].[OrganizationUnit] o
      ON u.SectionId = o.Code OR u.SectionId = o.UnitIdentifier
    WHERE o.SectionTypeCode = '<model_code>'
    ```
  - Jika user belum ter-assign: update `SectionId` di `UserEmploymentProfile`

---

## 4. Permission & Group (`cst-shared-sqldb-user` / User Management)

> Detail sistem permission dan group: lihat [permission.md](../permission.md)

### Permission Code — Akses Fitur
- [ ] User sudah di-mapping ke **permission code** yang sesuai agar fitur dapat diakses
  - Verifikasi di User Management: pastikan role/permission user sudah include permission code yang diperlukan
  - Jika belum: assign permission code yang sesuai ke role user tersebut

### Group: BUMA ID Inspector — Muncul di List Assign to Inspection
- [ ] User yang perlu muncul di list **"Assign to Inspector"** sudah ditambahkan ke group **`BUMA ID Inspector`**
  - Verifikasi: cek group membership user di User Management
  - Jika belum: tambahkan user ke group `BUMA ID Inspector`
  - Tanpa ini: nama user tidak akan muncul sebagai pilihan saat assign inspection ke inspector

### Group: BUMA ID Approver — Mendapatkan Data Approval di Workflow
- [ ] User yang berperan sebagai Approver sudah ditambahkan ke group **`BUMA ID Approver`**
  - Verifikasi: cek group membership user di User Management
  - Jika belum: tambahkan user ke group `BUMA ID Approver`
  - Tanpa ini: user tidak akan mendapatkan notifikasi/data approval di Workflow
  - Detail konfigurasi workflow: lihat [workflow.md](../workflow.md)

---

## Summary Dependency

```
[1] tenant.SectionType           → harus ada dulu
[2] tenant.OrganizationUnit      → SectionTypeCode = model_code
[3] asset.AssetModel             → Code = model_code
[4] asset.AssetModelMapping      → AssetModelCode = model_code
[5] asset.Component              → master component tersedia
[6] asset.SubComponent           → master subcomponent tersedia
[7] asset.ModelComponentSubComponent → mapping model ke component & subcomponent
[8] asset.Area                   → master Area tersedia (baru, 16 Jul 2026)
[9] asset.ModelComponentSubComponent.AreaCode → Area di-assign per baris mapping (baru, 16 Jul 2026)
[10] asset.DamageCode            → master damage code tersedia
[11] asset.SubComponentDamage    → mapping subcomponent ke damage code
[12] asset.Asset                 → AssetModelCode terisi benar
[13] user.UserEmploymentProfile  → SectionId sesuai OrganizationUnit
[14] Permission Code             → user di-assign ke permission code yang sesuai
[15] Group BUMA ID Inspector     → user muncul di list assign to inspection
[16] Group BUMA ID Approver      → approver mendapatkan data approval di Workflow
```

Jika salah satu step terlewat, user tidak akan bisa melihat data asset/component/damage untuk model tersebut, atau tidak muncul di list yang seharusnya.

---

*Last updated: 2026-07-16*
