# Form Builder — Data Structure

*Last updated: 2026-06-23*

---

**Service:** `maintenance-strategy`
**SQL DB:** `cst-iams-sqldb-maintenance-strategy`
**Cosmos DB:** `MaintenanceStrategy`

---

## Tabel SQL (`cst-iams-sqldb-maintenance-strategy`)

Tabel utama Form Builder:
```
Form
 ├── FormTab
 ├── FormAssetAssignment   ← khusus FT_MaintenanceForm
 ├── FormSiteAssignment        ← tabel kosong, belum dipakai
 └── FormPSAssignment
```

Tabel assignment (form di-assign ke mana):
| Tabel | Makna |
|-------|-------|
| `FormAssetAssignment` | Form di-assign ke asset tertentu (khusus `FT_MaintenanceForm`) |
| `FormSiteAssignment` | Form di-assign ke site tertentu — *tabel kosong, belum dipakai* |
| `FormPSAssignment` | Form di-assign ke Planning Schedule / PM Shutdown |

### Schema Tabel `FormPSAssignment`

```
Id
FormId                      ← FK ke Form.Id (per versi)
PeriodicalServiceTypeCode   ← tipe PM/Planning Schedule yang di-assign
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

Tabel lain: `FormTask`, `FormTaskAsset`, `FormTaskAssetMaintenanceCategory`, `FormTaskCategory`, `Element`, `GroupElement`, `LookupMasterData`, `MaintenanceCategory`, `MaintenanceTool`, `OperationalEnvironment`, `Configuration`, `AuditLog`, `RevertTable`

Tabel CBM (cluster tersendiri): `CBMConfig`, `CBMConfigMaintenanceCategory`, `CBMConfigRating`, `CBMGroup`, `CBMGroupTypeParameter`, `CBMMMainCategory`, `CBMParameter`, `CBMType`, `ConditionTesting`

---

## Schema Tabel `Form`

```
Id                        ← PK, FK ke Cosmos FormStructure.formId (harus di-lowercase saat mapping)
FormCode                  ← identitas tetap form lintas versi
Version                   ← versi form
Status                    ← lifecycle state (Draft, Published, Archived, dll)
Type                      ← FT_MaintenanceForm | FT_BusinessOperationalForm
MaintenanceCategoryCode   ← scope form ke maintenance category
OperationalEnvironmentCode← scope form ke operational environment
Name
Description
ReleaseNote
ReleaseDate
IsActive                  ← soft delete; hanya versi terbaru yang IsActive=1
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

---

## Versioning — Immutable Pattern

Setiap update form → data baru dibuat di SQL dan Cosmos, bukan update in-place:
- `FormCode` tetap sama lintas versi (identitas permanen form)
- `Id` berubah setiap versi (identitas per versi)
- Versi terbaru: `IsActive = 1`, versi lama: `IsActive = 0`
- Dokumen Cosmos lama tidak dihapus → selalu bisa di-fetch berdasarkan versi lama

**Catatan penting:** `Form.Id` di SQL adalah GUID uppercase. Saat mapping ke Cosmos `formId`, wajib di-lowercase terlebih dahulu.

---

## Cosmos DB (`MaintenanceStrategy`)

| Container | Fungsi |
|-----------|--------|
| `FormStructure` | Full JSON definition form template. Setiap dokumen = 1 tab, field utama: `formId`, `formTabId`, `formCode`, `version`, `title`, dll |
| `ContentKit` | Konten/aset pendukung form |
| `TaskKit` | Tipe task khusus dengan behavior khusus |

### Relasi SQL ↔ Cosmos

| SQL | Field | Cosmos Container | Catatan |
|-----|-------|-----------------|---------|
| `Form.Id` | `formId` | `FormStructure` | wajib di-lowercase saat mapping SQL → Cosmos |
| `FormTab.Id` | `formTabId` | `FormStructure` | wajib di-lowercase saat mapping SQL → Cosmos |

Kardinalitas:
- 1 Form → N dokumen di `FormStructure` (N = jumlah tab)
- 1 FormTab → 1 dokumen di `FormStructure`

---

## Form Type

| Type | Peruntukan |
|------|------------|
| `FT_MaintenanceForm` | Form untuk maintenance execution (PM Shutdown, BD Corrective, Inspection) |
| `FT_BusinessOperationalForm` | Form untuk Form Submission self-service (menu Form Submission mobile) |

**Perbedaan saat pembuatan form di UI:**

| Field / Behavior | `FT_MaintenanceForm` | `FT_BusinessOperationalForm` |
|---|---|---|
| Form Name | Wajib | Wajib |
| Form Description | Ada | Ada |
| Release Notes | Ada | Ada |
| Asset mapping (AssetType + Brand + Model + Variant) | **Wajib** | Tidak ada (tidak tersedia di UI) |

Agar form bertipe `FT_BusinessOperationalForm` muncul di halaman Form Submission (mobile) dan bisa dipilih oleh user, form tersebut perlu dikonfigurasi di tabel `BusinessOperationalForm` di `cst-iams-sqldb-maintenance-execution`.

---

## Schema Tabel `FormAssetAssignment`

```
Id
FormId                ← FK ke Form.Id (per versi, bukan per FormCode)
AssetTypeCode
AssetBrandCode
AssetModelCode
AssetVariantCode      ← kombinasi 4 kolom ini = scope asset untuk form ini
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

Hanya `FT_MaintenanceForm` yang mengisi tabel ini. `FT_BusinessOperationalForm` tidak membentuk data di `FormAssetAssignment` sama sekali. Setiap kali form diupdate (versi baru, `FormId` baru), baris baru dibuat di tabel ini untuk `FormId` yang baru — mengikuti pola immutable yang sama dengan tabel `Form`.

**Known gap:** `FormAssetAssignment.IsActive` tidak otomatis mengikuti `Form.IsActive`. Secara teknis, saat form versi lama di-archive, baris assignment lama tidak di-set `IsActive = 0`. Namun karena `FormId` selalu baru di setiap versi, row lama terisolir secara natural dan tidak ter-query dalam konteks form aktif. Gap ini hanya berpotensi masalah jika ada query yang filter langsung ke `FormAssetAssignment.IsActive` tanpa join ke `Form`.
