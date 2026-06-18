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

## Summary Dependency

```
[1] tenant.SectionType           → harus ada dulu
[2] tenant.OrganizationUnit      → SectionTypeCode = model_code
[3] asset.AssetModel             → Code = model_code
[4] asset.AssetModelMapping      → AssetModelCode = model_code
[5] asset.Component              → master component tersedia
[6] asset.SubComponent           → master subcomponent tersedia
[7] asset.ModelComponentSubComponent → mapping model ke component & subcomponent
[8] asset.DamageCode             → master damage code tersedia
[9] asset.SubComponentDamage     → mapping subcomponent ke damage code
[10] asset.Asset                 → AssetModelCode terisi benar
[11] user.UserEmploymentProfile  → SectionId sesuai OrganizationUnit
```

Jika salah satu step terlewat, user tidak akan bisa melihat data asset/component/damage untuk model tersebut.

---

*Last updated: 2026-06-18*
