# User → Asset Data Relation

Dokumen ini menjelaskan relasi antar entitas lintas database yang menentukan bagaimana user mendapatkan hak akses terhadap data asset (equipment) dan turunannya.

## Database Overview

| Alias | Database Name | Konten |
|-------|--------------|--------|
| `tenant` | cst-shared-sqldb-tenant | Data organisasi, section type, unit organisasi |
| `user` | cst-shared-sqldb-user | Data user, employment profile |
| `asset` | cst-iams-sqldb-services-asset | Data asset/equipment, model, component |

> Notasi: `db.table.column` — contoh: `asset.Asset.AssetModelCode` berarti DB asset, tabel Asset, kolom AssetModelCode.

---

## Relasi: User → Section → Asset

### 1. Section Type → Organization Unit
```
tenant.SectionType.Code = tenant.OrganizationUnit.SectionTypeCode
```

### 2. User → Organization Unit (Section)
```
user.UserEmploymentProfile.SectionId = tenant.OrganizationUnit.Code
user.UserEmploymentProfile.SectionId = tenant.OrganizationUnit.UnitIdentifier
```
> User dapat direlasikan ke OrganizationUnit melalui salah satu dari dua kolom di atas.

### 3. Asset → Organization Unit (via Model)
```
asset.Asset.AssetModelCode = tenant.OrganizationUnit.SectionTypeCode
```

### 4. Asset → Asset Model
```
asset.Asset.AssetModelCode = asset.AssetModel.Code
```

---

## Diagram Relasi

```
[user.UserEmploymentProfile]
        │ SectionId
        ▼
[tenant.OrganizationUnit]  ◄──── SectionTypeCode ────  [tenant.SectionType]
        │ SectionTypeCode
        ▼
[asset.Asset]  ──── AssetModelCode ────►  [asset.AssetModel]
```

---

## Model → Component → SubComponent → Damage Code

Mapping dari model asset ke komponen, sub-komponen, dan damage code dilakukan melalui tabel `ModelComponentSubComponent` dengan join chain berikut:

```sql
SELECT
     b.AssetModelCode
     ,c.Name as [Model]
     ,a.[ComponentCode]
     ,d.Name as [Component]
     ,a.[SubComponentCode]
     ,e.Name [SubComponent]
     ,g.Name as [DamageCode]
     ,a.[IsActive]
     ,a.[CreatedAt]
     ,a.[CreatedBy]
     ,a.[ModifiedAt]
     ,a.[ModifiedBy]
 FROM [dbo].[ModelComponentSubComponent] a
 LEFT JOIN [dbo].[AssetModelMapping] b ON a.AssetModelMappingCode = b.Code
 LEFT JOIN [dbo].[AssetModel] c ON b.AssetModelCode = c.Code
 LEFT JOIN [dbo].[Component] d ON a.ComponentCode = d.Code
 LEFT JOIN [dbo].[SubComponent] e ON a.SubComponentCode = e.Code
 LEFT JOIN [dbo].[SubComponentDamage] f ON a.SubComponentCode = f.SubComponentCode
 LEFT JOIN [dbo].[DamageCode] g ON f.DamageCode = g.Code
```

### Tabel yang Terlibat (DB: asset)

| Tabel | Peran |
|-------|-------|
| `ModelComponentSubComponent` | Mapping utama model → component → subcomponent |
| `AssetModelMapping` | Bridge antara model mapping ke AssetModel |
| `AssetModel` | Master data model asset |
| `Component` | Master data component |
| `SubComponent` | Master data sub-component |
| `SubComponentDamage` | Mapping subcomponent → damage code |
| `DamageCode` | Master data damage code |

### Hierarki

```
AssetModel
  └── Component
        └── SubComponent
              └── DamageCode
```

---

*Last updated: 2026-06-18*
