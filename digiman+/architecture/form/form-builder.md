# Form Builder — Data Structure

*Last updated: 2026-06-28*

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
 └── FormPSAssignment          ← ⚠ kemungkinan deprecated, lihat catatan di bawah
```

Tabel assignment (form di-assign ke mana):
| Tabel | Makna |
|-------|-------|
| `FormAssetAssignment` | Form di-assign ke asset tertentu (khusus `FT_MaintenanceForm`) |
| `FormSiteAssignment` | Form di-assign ke site tertentu — *tabel kosong, belum dipakai* |
| `FormPSAssignment` | Form di-assign ke Planning Schedule / PM Shutdown — ⚠ *kemungkinan deprecated* |

### Schema Tabel `FormPSAssignment`

```
Id
FormId                      ← FK ke Form.Id (per versi)
PeriodicalServiceTypeCode   ← tipe PM/Planning Schedule yang di-assign
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

> **⚠ Flag — kemungkinan tidak dipakai lagi.** [PRD PM Shutdown Phase 1](../../roadmap/phase1-service-package/PRD-PM-Shutdown-Phase1.html) (section T1 — Perubahan Data Model) memperkenalkan tabel baru `PlanForm` di `DPlanDB` (service `dplan`) sebagai mekanisme form assignment ke Plan — form di-assign Planner per plan selama status DRAFT, lalu di-resolve ke `FormSubmission`/`Task` di `maintenance-execution` saat plan SUBMIT (via event `PlanSubmitted`). Data model baru ini sama sekali tidak mereferensikan `FormPSAssignment`. Perlu dikonfirmasi ke tim apakah `FormPSAssignment` resmi digantikan oleh alur `PlanForm`, atau masih dipakai untuk kasus lain di luar scope Phase 1 ini.

Tabel Element registry: `GroupElement`, `Element` (lihat section [GroupElement](#groupelement) dan [Element](#element))

Tabel Bank Task: `FormTask`, `FormTaskCategory` (lihat section [Bank Task](#bank-task))

Tabel lain: `FormTaskAsset`, `FormTaskAssetMaintenanceCategory`, `LookupMasterData`, `MaintenanceCategory`, `MaintenanceTool`, `AuditLog`, `RevertTable`

Tabel CBM (cluster tersendiri): `CBMConfig`, `CBMConfigMaintenanceCategory`, `CBMConfigRating`, `CBMGroup`, `CBMGroupTypeParameter`, `CBMMainCategory`, `CBMParameter`, `CBMType`, `ConditionTesting` (lihat section [CBM](#cbm))

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
| `FormStructure` | Full JSON definition form template. Setiap dokumen = 1 tab |
| `TaskKit` | Template struktur row per task type. Direferensikan oleh `Element.ReferenceId` |
| `ContentKit` | Konten guideline (rich text + gambar). Direferensikan oleh `Element.ReferenceId` untuk group `GUIDELINE` |

### Relasi SQL ↔ Cosmos

| SQL | Field | Cosmos Container | Catatan |
|-----|-------|-----------------|---------|
| `Form.Id` | `formId` | `FormStructure` | wajib di-lowercase saat mapping SQL → Cosmos |
| `FormTab.Id` | `formTabId` | `FormStructure` | wajib di-lowercase saat mapping SQL → Cosmos |
| `Element.ReferenceId` (Type=`TaskKit`) | `id` | `TaskKit` | pointer ke template task type |
| `Element.ReferenceId` (Group=`GUIDELINE`) | `id` | `ContentKit` | pointer ke konten guideline |

Kardinalitas:
- 1 Form → N dokumen di `FormStructure` (N = jumlah tab)
- 1 FormTab → 1 dokumen di `FormStructure`
- 1 Element (TaskKit) → 1 dokumen di `TaskKit`
- 1 Element (Guideline) → 1 dokumen di `ContentKit`

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

---

## Bank Task

Bank Task adalah master data task yang dapat di-reuse lintas form. Terdiri dari dua tabel: `FormTaskCategory` dan `FormTask`.

### Schema Tabel `FormTaskCategory`

```
Code (PK, varchar(64))   ← natural key; digunakan sebagai FK dari FormTask
Name (varchar(200))
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

Fungsi: grouping/kategorisasi task di UI Bank Task. Tidak ada behavior khusus per kategori.

### Schema Tabel `FormTask`

```
Id (PK, bigint)                    ← auto-increment integer, bukan GUID
Code (varchar(64))                 ← business key; yang disimpan di Cosmos sebagai taskCode
FormTaskCategoryCode (varchar(64)) ← FK ke FormTaskCategory.Code
Description (varchar(max))         ← plain text; yang di-copy ke Cosmos saat task dipilih
DescriptionHTML (varchar(max))     ← rich text version; tidak dipakai di Cosmos
Tab (varchar(max))                 ← belum berfungsi, masih null
SectionTask (varchar(max))         ← belum berfungsi, masih null
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

**Catatan:** `FormTask.Id` adalah `bigint` (auto-increment), berbeda dengan `Form.Id` yang GUID. `Code` adalah business key yang dipakai di seluruh sistem termasuk Cosmos.

---

### Bank Task di Cosmos (`FormStructure`)

Saat task dari Bank Task dipilih ke dalam form, data yang di-embed ke dokumen `FormStructure` di Cosmos adalah:

```json
{
    "elementCode": "BANKTASK",
    "value": "S1",
    "label": "Description",
    "placeholder": "Select",
    "valueCaption": "Pekerja sudah paham tugas dan bahaya terkait?"
}
```

| Field | Sumber | Keterangan |
|-------|--------|------------|
| `value` | `FormTask.Code` | taskCode — identifier task |
| `valueCaption` | `FormTask.Description` | Snapshot plain text saat form di-publish |

`valueCaption` adalah **snapshot** — jika `FormTask.Description` diubah setelah form dipublish, form yang sudah ada tidak ikut berubah.

---

### Struktur Row Bank Task dalam ASSESSMENTCHECK

Bank Task selalu ditempatkan di dalam sebuah **task type** (misalnya `ASSESSMENTCHECK`). Satu row task dalam `ASSESSMENTCHECK` terdiri dari 4 elemen:

```
[ NUMBERINGTEXT ]   → nomor urut task (display only)
[ BANKTASK      ]   → value = taskCode, valueCaption = description snapshot
[ DROPDOWN      ]   → jawaban utama task, taskCode = sama, responseKey = "1"
[ INLINE        ]   → layout wrapper untuk additional fields:
    ├─ TAKEPHOTO           → taskCode = sama, responseKey = "2"
    └─ ADDITIONALINFORMATION → taskCode = sama, responseKey = "3"
```

`taskCode` yang sama diulang di setiap elemen dalam satu row. `responseKey` membedakan field mana yang diisi user dalam satu task — kombinasi `taskCode` + `responseKey` adalah unique key untuk satu nilai response.

`INLINE` bukan field data — hanya layout wrapper untuk mengelompokkan additional fields secara visual di UI.

---

### Dua Jenis `taskCode` di Cosmos

| Jenis | Contoh | Sumber |
|-------|--------|--------|
| Short code | `"S1"`, `"C1"` | Dari Bank Task (`FormTask.Code`) |
| UUID | `"8b3841fc-d9ad-4124-be78-5ca5d7bc5386"` | Task custom/sistem — bukan dari Bank Task |

---

### Struktur Tab di FormStructure

Setiap form di Cosmos minimal terdiri dari **2 dokumen** (2 tab):

| Tab | Karakteristik |
|-----|--------------|
| **General** | `sectionId` hardcoded (`00000000-0000-0000-0000-000000000001` dst.), beberapa section `isImmutable: true`. Berisi elemen sistem: `LABOURPERSONNEL`, `SITE`, `ASSETNUMBER`, `WORKORDER`, dll. |
| **Specific tab(s)** | `sectionId` berupa GUID dinamis, `isImmutable: false`. Berisi konten form termasuk Bank Task. Bisa lebih dari satu (CBM, Safety, dll.) |

---

### Known Gap — Bank Task tidak terikat task type

Satu `FormTask` dapat digunakan dengan task type berbeda di form yang berbeda. Tidak ada field di tabel `FormTask` yang mengunci task type. Implikasi: response structure untuk task yang sama (`taskCode` sama) bisa berbeda antar form, menyulitkan agregasi atau komparasi data response lintas form.

---

## TaskKit

TaskKit adalah definisi task type yang disimpan di Cosmos DB container `TaskKit`. Setiap dokumen mendefinisikan struktur kolom (header) dan behavior satu task type.

### Referensi di FormStructure

Element `ASSESSMENTCHECK` di `FormStructure` me-reference TaskKit via field `category`:

```json
{
    "elementCode": "ASSESSMENTCHECK",
    "type": "TaskKit",
    "category": "ASSESSMENT",
    ...
}
```

### Daftar TaskKit

**General Check:**

| Category | Name | Jumlah Kolom |
|----------|------|-------------|
| `ASSESSMENT` | General Check - Assessment Check | 4 |
| `WASHING` | General Check - Washing | 4 |
| `ACTION` | General Check - Action Task | 4 |
| `DEFECT` | General Check - Defect Check | 4 |
| `CRACK` | General Check - Crack Defect | 4 |
| `CONDITION_CHECK` | General Check - Condition Check | 4 |
| `DATAINPUT` | General Check - Data Input | 6 |

**CBM:**

| Category | Rating | Name | Jumlah Kolom |
|----------|--------|------|-------------|
| `CBMMC1` | `ABC` | CBM - Sense Rating | 6 |
| `CBMMC2` | `ABC` | CBM - OEM Standard Rating (ABC Rating) | 11 |
| `CBMMC2` | `INOUTSPEC` | CBM - OEM Standard Rating (In Spec Rating) | 11 |
| `CBMMC3` | `ABC` | CBM - Tool-Based Rating | 12 |
| `CBMMC4` | `INOUTSPEC` | CBM - Condition Test Rating | 12 |

### Catatan Penting

- **Kolom terakhir selalu `''`** — slot INLINE (action column: photo + additional information).
- **`category` tidak selalu unik** — `CBMMC2` muncul dua kali dengan `rating` berbeda (`ABC` vs `INOUTSPEC`). Untuk identify task type CBM secara unik diperlukan kombinasi `category` + `rating`.
- **Jumlah kolom = jumlah responseKey per task row** — General Check umumnya 4 responseKey, CBM bisa sampai 12.

Data lengkap TaskKit: [taskkit-all.json](examples/taskkit-all.json)

### Contoh Data Cosmos FormStructure

Form: **WICOPE CBM** (`FORM3`, version 4). Terdiri dari 3 dokumen (3 tab):

| File | Tab | Keterangan |
|------|-----|------------|
| [wicope-cbm-general-tab.json](examples/wicope-cbm-general-tab.json) | General | Tab sistem dengan immutable sections (Nama Observer, Asset Information) + section custom WICOPE Quality Check |
| [wicope-cbm-cbm-tab.json](examples/wicope-cbm-cbm-tab.json) | CBM | Tab spesifik dengan ASSESSMENTCHECK (category: ASSESSMENT) berisi Bank Task C1–C11 |
| [wicope-cbm-safety-tab.json](examples/wicope-cbm-safety-tab.json) | Safety | Tab spesifik dengan ASSESSMENTCHECK (category: ASSESSMENT) berisi Bank Task S1–S12 |

---

## CBM

> **Status:** Diskusi berlangsung — bagian ini akan dilanjutkan/dikoreksi di sesi berikutnya. Beberapa relasi masih perlu dikonfirmasi (lihat "Open Questions" di bawah).

CBM (Condition Based Monitoring) task type di Task Kit hanya muncul saat membuat form `FT_MaintenanceForm` — di-exclude untuk `FT_BusinessOperationalForm` via `Configuration.ExcludedFormElement_BusinessOperational` (lihat section [Configuration](#configuration)).

### Mapping Task Kit CBM → kolom form builder

Lima task type CBM di palette Task Kit (lihat juga section [TaskKit](#taskkit)), berurutan sesuai tampilan UI, dengan kolom yang muncul saat task ditambahkan ke form:

| Urutan UI | Task Kit | `category`/`rating` | Kolom di Form Builder |
|---|---|---|---|
| 1 | Condition Test Rating | `CBMMC4` / `INOUTSPEC` | Task, Measurement Location, CBM Type, Condition, OEM Spec, Respond, Measurement Value, Status |
| 2 | ABC Rating | `CBMMC2` / `ABC` | Task, Measurement Location, CBM Type, OEM Spec, Respond, Measurement Value, Rating |
| 3 | In Spec Rating | `CBMMC2` / `INOUTSPEC` | Task, Measurement Location, CBM Type, OEM Spec, Respond, Measurement Value, Status |
| 4 | Sense Rating | `CBMMC1` / `ABC` | Task, Measurement Location, CBM Type, Rating, Response |
| 5 | Tool Based Rating | `CBMMC3` / `ABC` | Task, Measurement Location, CBM Type, Tools, OEM Spec, Respond, Measurement Value, Rating |

Kolom **Measurement Location** = pilihan component/sub-component dari asset (relevan dengan catatan MOM EHMS: "Area diisi dengan Sub Component dari Digiman+ jika ada" — lihat [cbm-integration-ehms.md](../../mom/cbm-integration-ehms.md)).

Jumlah kolom di atas lebih sedikit dari jumlah kolom TaskKit yang tercatat (`CBMMC1`=6, `CBMMC2`=11, `CBMMC3`=12, `CBMMC4`=12) — selisihnya kemungkinan dari kolom INLINE (action: photo + additional information) yang tidak tampak sebagai header terpisah di UI.

### Schema Tabel Master CBM (`cst-iams-sqldb-maintenance-strategy`)

**`CBMMainCategory`** — lookup
```
Code (PK, varchar(64))
Name (varchar(256))
Description (varchar(max), null)
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

**`CBMParameter`** — lookup
```
Code (PK, varchar(64))
Name (varchar(256))
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

**`CBMType`** — lookup
```
Code (PK, varchar(64))
Name (varchar(256))
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

**`CBMGroup`** — lookup
```
Code (PK, varchar(64))
Name (varchar(256))
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

**`CBMGroupTypeParameter`** — junction 3-way, mendefinisikan kombinasi valid Group × Type × Parameter
```
CBMGroupCode (PK, FK → CBMGroup.Code, varchar(64))
CBMTypeCode (PK, FK → CBMType.Code, varchar(64))
CBMParameterCode (PK, FK → CBMParameter.Code, varchar(64))
Description (varchar(max), null)
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

**`CBMConfig`** — tabel pusat: master measurement point per kombinasi asset + component
```
Id (PK, bigint)
TaskKey (varchar(64), null)
Code (varchar(64), null)
Version (bigint, null)
Description (varchar(max), null)
AssetTypeCode (varchar(64), null)
AssetBrandCode (varchar(64), null)
AssetModelCode (varchar(64), null)
AssetVariantCode (varchar(64), null)   ← kombinasi 4 kolom ini = scope asset
ComponentCode (varchar(64), null)
SubComponentCode (varchar(64), null)
CBMMainCategoryCode (FK → CBMMainCategory.Code, varchar(64))
CBMGroupCode (FK → CBMGroup.Code, varchar(64))
CBMTypeCode (FK → CBMType.Code, varchar(64))
RatingCategoryCode (varchar(64), null)
MaintenanceToolCode (FK → MaintenanceTool.Code, varchar(64))
ConditionTestingCode (FK → ConditionTesting.Code, varchar(64))
UoMCode (varchar(64), null)
OEMStandardMin (float, null)
OEMStandardMax (float, null)
OEMOperatorMin (varchar(4), null)
OEMOperatorMax (varchar(4), null)
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

**`CBMConfigRating`** — threshold rating (1-to-many dari `CBMConfig`)
```
Id (PK, bigint)
CBMConfigId (FK → CBMConfig.Id, bigint)
CBMConfigCode (varchar(64), null)
RatingCode (varchar(64), null)         ← mis. A / B / C / X
Version (int)
ValueMin (float, null)
ValueMax (float, null)
OperatorMin (varchar(4), null)
OperatorMax (varchar(4), null)
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

**`CBMConfigMaintenanceCategory`** — scope maintenance category (1-to-many dari `CBMConfig`)
```
Id (PK, bigint)
CBMConfigId (FK → CBMConfig.Id, bigint)
CBMConfigCode (varchar(64), null)
MaintenanceCategoryCode (FK → MaintenanceCategory.Code, varchar(64))
Version (int)
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

**`ConditionTesting`** — belum dibahas, schema belum dicatat.

### Open Questions

1. `CBMConfig.TaskKey` — relasinya ke apa? Apakah ini Task Key yang dipakai untuk mapping ke EHMS (`external_code`)?
2. `CBMConfig.RatingCategoryCode` vs `CBMConfigRating.RatingCode` — apa beda fungsinya?
3. `ConditionTestingCode` mengarah ke tabel `ConditionTesting` — belum dibahas schema-nya.

---

## GroupElement

Tabel `GroupElement` adalah parent/kategori dari tabel `Element`. Mengelompokkan element type berdasarkan fungsinya di Form Builder.

### Schema Tabel `GroupElement`

```
Code (PK, varchar(64))   ← natural key; = Element.GroupElementCode
Name (varchar(256))
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

### Data

| Code | Name | Keterangan |
|------|------|------------|
| `GENERALCHECK` | General Check | Task type untuk pengecekan umum (defect, crack, assessment, dll) |
| `CBM` | CBM | Task type untuk Condition Based Monitoring |
| `INPUTLAYOUT` | Input | Elemen input standar (dropdown, datetime, text, dll) |
| `GUIDELINE` | Guideline | Konten referensi visual (A/B/C/X rating guide) |

---

## Element

Tabel `Element` adalah **registry semua element type** yang tersedia di Form Builder. Setiap elemen yang bisa dipakai di form (baik di UI palette maupun secara internal) terdaftar di sini.

Data lengkap: [element-all.csv](examples/element-all.csv)

### Schema Tabel `Element`

```
GroupElementCode (FK, varchar(64))  ← FK ke GroupElement.Code; menentukan kelompok elemen
Code (PK, varchar(64))              ← business key; = elementCode di Cosmos FormStructure
Name (varchar(256))
Type (varchar(64))                  ← TaskKit | InputLayout
ReferenceId (uniqueidentifier)      ← pointer ke Cosmos (TaskKit atau ContentKit); NULL jika tidak ada counterpart
Description (varchar(max))
IconUrl (varchar(256))
IsShow (bit)                        ← apakah muncul di UI palette
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

**Catatan penting:** `Element.Code` = `elementCode` yang dipakai di dokumen Cosmos `FormStructure`. Ini adalah identifier yang menghubungkan SQL ↔ Cosmos pada level element.

### Tiga Kelompok Element

| GroupElementCode | Type | ReferenceId | Cosmos Counterpart | Keterangan |
|---|---|---|---|---|
| `GENERALCHECK`, `CBM` | `TaskKit` | Ada | → `TaskKit` | Task type yang merender sebagai task table di form |
| `GUIDELINE` | `InputLayout` | Ada | → `ContentKit` | Konten referensi/guideline visual |
| `INPUTLAYOUT` | `InputLayout` | NULL | — | Elemen input standar; definisi ada di SQL saja |

### Daftar Element per Kelompok

**GENERALCHECK (TaskKit):**

| Code | Name |
|------|------|
| `ASSESSMENTCHECK` | Assessment Check |
| `WASHING` | Washing |
| `ACTIONTASK` | Action Task |
| `DEFECTCHECK` | Defect Check |
| `CRACKDEFECT` | Crack Defect |
| `CONDITION_CHECK` | Condition Check |
| `DATAINPUT` | Data Input |

**CBM (TaskKit):**

| Code | Name |
|------|------|
| `SENSERATING` | Sense Rating |
| `OEMSTD_ABCRATING` | ABC Rating (OEM Standard) |
| `OEMSTD_INOUTSPECRATING` | In Spec Rating (OEM Standard) |
| `TOOLBASEDRATING` | Tool Based Rating |
| `CONDITIONTESTRATING` | Condition Test Rating |

**GUIDELINE (InputLayout → ContentKit):**

| Code | Name |
|------|------|
| `LEAKS` | Leaks |
| `MAGNETIC_SCREENS` | Magnetic Screens |
| `MAGNETIC_PLUG` | Magnetic Plug |
| `FILTER_CUTS` | Filter Cuts |
| `CYLINDER_LEAKS` | Cylinder Leaks |
| `CONTAMINATIONS_OIL_SENSOR` | Contaminations Oil Sensor |

**INPUTLAYOUT (InputLayout, no Cosmos counterpart):**

`INPUT`, `DROPDOWN`, `MULTIPLECHOICE`, `SINGLECHOICE`, `DATETIME`, `NUMBER`, `LABEL`, `CUSTOMCONTENT`, `PHOTOLIST`, `SIGNATUREGROUP`, `CHECKBOXWITHREASON`, `ASSESSMENTSCORE`

---

## ContentKit

Container Cosmos `ContentKit` menyimpan konten guideline — material referensi visual yang ditampilkan kepada technician saat mengisi form.

### Struktur Dokumen ContentKit

```json
{
    "id": "...",                    ← = Element.ReferenceId untuk group GUIDELINE
    "type": "Guideline",           ← satu-satunya type yang ada saat ini
    "content": {
        "name": "Leaks",
        "elements": [
            {
                "groupElementCode": "GUIDELINE",
                "elementCode": "CUSTOMCONTENT",
                "label": "",
                "value": "<HTML konten CKEditor>",
                "customValidation": "[]"
            }
        ]
    },
    "activeFlag": true
}
```

### Karakteristik

- Konten disimpan sebagai **CKEditor HTML** — bisa berisi tabel, gambar, teks formatting
- Gambar-gambar guideline di-host di **Azure Blob Storage** (`cstbumaiddevsta001.blob.core.windows.net`)
- Semua dokumen saat ini bertipe `"Guideline"` — menampilkan visual rating criteria (A/B/C/X) per kondisi
- `ContentKit.id` = `Element.ReferenceId` untuk group `GUIDELINE`

Data lengkap: [contentkit-all.json](examples/contentkit-all.json) — field `value` berisi CKEditor HTML, disimpan sebagai ringkasan deskriptif.

### Daftar ContentKit (Guideline) Saat Ini

| id (= Element.ReferenceId) | Nama | Konten |
|---|---|---|
| `c0577cd8-...` | Leaks | Rating A/B/C/X untuk kondisi kebocoran |
| `d44f1a2c-...` | Magnetic Screens | Rating A/B/C/X untuk partikel di magnetic screen |
| `ede39cb5-...` | Magnetic Plug | Rating A/B/C/X untuk partikel di magnetic plug |
| `1a11f013-...` | Filter Cuts | Rating A/B/C/X untuk kondisi filter cuts |
| `60264385-...` | Cylinder Leaks | Rating A/B/C/X untuk kebocoran silinder |
| `5bc03ce0-...` | Contaminations Oil Sensor | Rating A/B/C/X untuk kontaminasi oil sensor |

---

## Configuration

Tabel `Configuration` adalah key-value store untuk konfigurasi sistem Form Builder. Mengontrol behavior yang berbeda antar form type tanpa perlu code change.

### Schema Tabel `Configuration`

```
Id (PK, bigint)           ← auto-increment
Key (varchar(128))        ← nama konfigurasi
Description (varchar(1024))
Value (varchar(max))      ← plain string atau JSON array as string
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

### Data Konfigurasi Saat Ini

| Key | Value | Keterangan |
|-----|-------|------------|
| `ExcludedFormElement_BusinessOperational` | `["CONDITIONTESTRATING","TOOLBASEDRATING","SENSERATING","OEMSTD_ABCRATING","OEMSTD_INOUTSPECRATING"]` | Element yang disembunyikan di Form Builder saat membuat `FT_BusinessOperationalForm` — semua CBM task type |
| `GeneralTab_Form_Maintenance` | `general_template` | `FormStructure.id` template General tab untuk `FT_MaintenanceForm` |
| `GeneralTab_Form_BusinessOperational` | `general_template_businessoperational` | `FormStructure.id` template General tab untuk `FT_BusinessOperationalForm` |
| `FormType_AdditionalWorkOrder` | `["FT_MaintenanceForm"]` | Form type yang eligible untuk Additional Work Order |

### Mekanisme General Tab Template

`GeneralTab_Form_*` mereferensikan dokumen khusus di Cosmos `FormStructure` yang berfungsi sebagai **base template** untuk General tab. Dokumen ini memiliki all-zero GUID sebagai identifier — bukan form nyata:

| Config Value | `FormStructure.id` | `formId` | `formTabId` | `version` |
|---|---|---|---|---|
| `general_template` | `general_template` | `00000000-...-000000000000` | `00000000-...-000000000000` | 0 |
| `general_template_businessoperational` | `general_template_businessoperational` | `00000000-...-000000000001` | `00000000-...-000000000001` | 1 |

Saat form baru dibuat, sistem membaca template ini dan **meng-copy** dokumennya sebagai General tab form tersebut. Perubahan pada template tidak propagate ke form yang sudah ada.

**Struktur General tab template (keduanya saat ini identik kontennya):**

| Section | `sectionId` | `isImmutable` | Elements |
|---------|-------------|---------------|----------|
| Service Labour Personnel | `00000000-...-000000000001` | `true` | `LABOURPERSONNEL`, `ACTUALSERVICESTART`, `SHIFT` |
| Asset Information | `00000000-...-000000000002` | `true` | `SITE`, `SECTION`, `ASSETNUMBER`, `WORKORDER`, `TEXTFIELD` (SMU), `CAMERACAPTURE`, `TEXTFIELD` (Hour Meter) |
| Safety Precautions | `00000000-...-000000000003` | `false` | `CUSTOMCONTENT`, `MULTIPLECHOICE`, `PHOTOLIST`, `CHECKBOXWITHREASON` |

Section "Safety Precautions" sengaja `isImmutable: false` — bisa dikustomisasi per form. Dua section pertama tidak bisa diubah.

Referensi template lengkap:
- [general-template-maintenance.json](examples/general-template-maintenance.json)
- [general-template-businessoperational.json](examples/general-template-businessoperational.json)

### `ExcludedFormElement_BusinessOperational`

CBM element types di-exclude dari palette Form Builder saat membuat `FT_BusinessOperationalForm` karena form jenis ini tidak untuk maintenance execution (tidak butuh pengukuran CBM):

| Element.Code yang di-exclude | TaskKit Name |
|---|---|
| `CONDITIONTESTRATING` | CBM - Condition Test Rating |
| `TOOLBASEDRATING` | CBM - Tool-Based Rating |
| `SENSERATING` | CBM - Sense Rating |
| `OEMSTD_ABCRATING` | CBM - OEM Standard Rating (ABC) |
| `OEMSTD_INOUTSPECRATING` | CBM - OEM Standard Rating (In Spec) |

---

## OperationalEnvironment

> **Status:** Fungsi belum dikonfirmasi. Schema dan data disimpan sebagai referensi.

Kemungkinan dipakai sebagai scope form ke area operasional tertentu — terkait field `Form.OperationalEnvironmentCode` di tabel `Form`.

### Schema Tabel `OperationalEnvironment`

```
Code (PK, varchar(64))
Name (varchar(256))
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

Data lengkap: [operational-environment-all.csv](examples/operational-environment-all.csv)

---

## MaintenanceTool

Sumber data dropdown untuk element `CHECKINGTOOL` di TaskKit `CBMMC3` (CBM - Tool-Based Rating). Field `dropdownData` di element tersebut di-populate dari tabel ini saat runtime.

### Schema Tabel `MaintenanceTool`

```
Code (PK, varchar(64))
Name (varchar(256))
Description (varchar(max))
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

### Data

| Code | Name | Description |
|------|------|-------------|
| `TOOL1` | Birrana | Birrana |
| `TOOL2` | CAT Gauge | CAT Gauge |

---

## MaintenanceCategory

Dipakai saat membuat `FT_MaintenanceForm` — user memilih maintenance category yang menjadi scope form. Tersimpan di `Form.MaintenanceCategoryCode`.

### Schema Tabel `MaintenanceCategory`

```
Code (PK, varchar(64))
Name (varchar(256))
TypeCode (varchar(64))        ← enum string, tidak ada tabel referensi
IsPeriodicalService (bit)     ← 1 jika terkait PM Shutdown / Planning Schedule
IsActive (bit)
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

Data lengkap: [maintenance-category-all.csv](examples/maintenance-category-all.csv)

### TypeCode

| TypeCode | Kelompok | `IsPeriodicalService` |
|----------|----------|-----------------------|
| `MCT_C` | Corrective | 0 |
| `MCT_GIC` | General Inspection/Check | 0 |
| `MCT_PI` | Periodical Inspection | 1 |
| `MCT_PS` | Periodical Service (PM Shutdown) | 1 |
