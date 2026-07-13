# Form Submission — Data Structure & Flow

*Last updated: 2026-06-23*

---

**Service:** `maintenance-execution`
**SQL DB:** `cst-iams-sqldb-maintenance-execution`
**Cosmos DB:** `MaintenanceExecution`

---

## Data Structure

### SQL (`cst-iams-sqldb-maintenance-execution`)

```
Workorder
  └── Task
        ├── FormSubmission  (TaskId → Task.Id)
        │     └── FormSubmissionTab
        └── TaskPersonalized  (TaskId → Task.Id)
              ├── TaskPersonalizedLog
              ├── TaskPersonalizedFinding
              │     └── TaskPersonalizedEvidence
```

#### Schema Tabel `WorkOrder`

```
Id
TypeCode
PriorityCode
Number
PlanId                  ← FK ke DigitalPlanning.Id (dplan)
Description             ← DigitalPlanning.PlanName
ScheduleStartDate       ← DigitalPlanning.ProjectStart
DueDate
WorkType
Source                  ← "Digiplan" jika berasal dari Digiplan (default)
Status
StartDate
EndDate
AssetNumber             ← DPEquipment.Equipment
AssetModelCode          ← cst-iams-sqldb-services-asset.Asset.AssetModelCode
AssetModelName          ← cst-iams-sqldb-services-asset.AssetModel.Name
MaintenanceCategoryCode
MaintenanceCategoryName
SectionTypeCode         ← cst-iams-sqldb-services-asset.Asset.SectionTypeCode
SiteCode                ← DigitalPlanning.SiteId
Notes
TotalOSBacklog
IsActive
CreatedBy, CreatedAt
ModifiedBy, ModifiedAt
ReferenceId
LastSyncedAt, LastSyncedBy
LastSyncedModifiedAt, LastSyncedModifiedBy
```

#### Schema Tabel `Task`

```
Id
WorkOrderId
Name
Type
Status
Notes
IsActive
ReferenceId
LastSyncedAt, LastSyncedBy
LastSyncedModifiedAt, LastSyncedModifiedBy
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

#### Schema Tabel `FormSubmission`

```
Id
TaskId              ← FK ke Task.Id
FormId              ← cross-service reference ke Form.Id (cst-iams-sqldb-maintenance-strategy) — menunjuk template form versi mana yang dipakai, bisa dijoinkan jika diperlukan
FormCode
Version
AssetTypeCode
AssetBrandCode
AssetVariantCode    ← hanya 3 dimensi (tidak ada AssetModelCode)
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

**Known gap:** `FormSubmission` (`cst-iams-sqldb-maintenance-execution`) hanya menyimpan 3 dimensi asset (`AssetTypeCode`, `AssetBrandCode`, `AssetVariantCode`), sedangkan `FormAssetAssignment` (`cst-iams-sqldb-maintenance-strategy`) menggunakan 4 dimensi (termasuk `AssetModelCode`). `AssetModelCode` tidak ada di tabel ini.

#### Schema Tabel `FormSubmissionTab`

```
Id
FormSubmissionId    ← FK ke FormSubmission.Id
Name
Sequence
TotalParentTask
IsCompleted
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

#### Schema Tabel `TaskPersonalized`

```
Id (PK, bigint)
TaskId              ← FK ke Task.Id
UserCode            ← identitas mechanic
IsPrecautionConfirmed
MachineSMUValue
MachineSMUAddress
Status
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
ReferenceId
LastSyncedAt, LastSyncedBy
LastSyncedModifiedAt, LastSyncedModifiedBy
```

Kardinalitas: 1 Task → N TaskPersonalized (1 record per mechanic per task)

#### Schema Tabel `TaskPersonalizedLog`

```
Id
TaskPersonalizedId  ← FK ke TaskPersonalized.Id
StartDate           ← device timestamp saat klik Start/Mulai
EndDate             ← device timestamp saat klik Finish/Close, nullable
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
LastSyncedAt
```

#### Schema Tabel `TaskPersonalizedFinding`

```
Id
TaskPersonalizedId      ← FK ke TaskPersonalized.Id
FormSubmissionTabId     ← FK ke FormSubmissionTab.Id
FormTaskCode
FormTaskNumber
ComponentCode
SubComponentCode
OtherSubComponentName
DamageCode
CauseCode
RatingCode
ActionRemedyCode
IsImmediateExecutable
PriorityCode
DefectNotes
DeleteNotes
RepairDuration
RepairInstruction
IsActive
ReferenceId
LastSyncedAt, LastSyncedBy
LastSyncedModifiedAt, LastSyncedModifiedBy
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

#### Schema Tabel `TaskPersonalizedEvidence`

```
Id
TaskPersonalizedId          ← FK ke TaskPersonalized.Id
TaskPersonalizedFindingId   ← FK ke TaskPersonalizedFinding.Id
Name
ContentAddress
IsActive
OfflineModeId
ReferenceId
LastSyncedAt, LastSyncedBy
LastSyncedModifiedAt, LastSyncedModifiedBy
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
```

---

#### Schema Tabel `TaskResponseLog`

```
Id
TaskId
FormSubmissionTabId     ← FK ke FormSubmissionTab.Id
FormTaskCode            ← identitas pertanyaan/task dalam form
Response                ← jawaban user (misal: Good, Defect Found, dll)
Reason
CreatedAt, CreatedBy
```

Tabel ini bersifat append-only (tidak ada `ModifiedAt`/`IsActive`). Digunakan sebagai basis agregasi summary di form — misalnya menghitung berapa mechanic menjawab "Good" vs "Defect Found" untuk satu task tertentu. Data response utama tetap disimpan di `FormSubmissionStructure` (Cosmos), tabel ini khusus untuk kebutuhan query/reporting SQL.

---

### Cosmos DB (`MaintenanceExecution`)

| Container | Fungsi |
|-----------|--------|
| `FormSubmissionStructure` | Satu-satunya container di `MaintenanceExecution`. Berisi salinan penuh form template yang di-copy dari `FormStructure` (`MaintenanceStrategy`) pada saat transaksi dibuat, beserta data submission per tab. Setiap dokumen (1 dokumen = 1 tab) mengandung field antara lain: `formSubmissionId`, `formSubmissionTabId`, `formId`, `formCode`, `version`, `title`, dll |

**Mekanisme copy:** Setiap kali transaksi dibuat, sistem meng-copy form template dari `MaintenanceStrategy` Cosmos ke `MaintenanceExecution` Cosmos sebagai form execution. Tujuannya agar data submission selalu merujuk ke struktur form yang tepat pada saat transaksi terjadi, meskipun template form sudah diupdate ke versi baru.

### Relasi SQL ↔ Cosmos

| SQL | Field | Cosmos Container | Catatan |
|-----|-------|-----------------|---------|
| `FormSubmission.Id` | `formSubmissionId` | `FormSubmissionStructure` | wajib di-lowercase saat mapping SQL → Cosmos |
| `FormSubmission.FormId` | `formId` | `FormSubmissionStructure` | wajib di-lowercase saat mapping SQL → Cosmos |
| `FormSubmissionTab.Id` | `formSubmissionTabId` | `FormSubmissionStructure` | wajib di-lowercase saat mapping SQL → Cosmos |

Kardinalitas:
- 1 Task → 1 FormSubmission
- 1 FormSubmission → N FormSubmissionTab (N = jumlah tab di form)
- 1 FormSubmissionTab → 1 file JSON di `FormSubmissionStructure` (`MaintenanceExecution` Cosmos)

---

## Contoh Query — Ambil Jawaban User dari FormSubmissionStructure

Tab **General** dan tab **spesifik** (CBM/General Check dll.) punya struktur elemen berbeda di Cosmos (lihat [Struktur Tab di FormStructure](form-builder.md#struktur-tab-di-formstructure)), jadi butuh query terpisah — bukan satu query yang di-generalize untuk keduanya.

### Query — Tab Spesifik (Bank Task row, nested)

Query Cosmos DB (`MaintenanceExecution` → `FormSubmissionStructure`) untuk mengambil jawaban user dari satu row task (struktur `NUMBERINGTEXT` → `BANKTASK` → `DROPDOWN` → `INLINE[TAKEPHOTO, ADDITIONALINFORMATION]`, lihat [form-builder.md](form-builder.md#struktur-row-bank-task-dalam-assessmentcheck)):

```sql
SELECT 
c.formSubmissionId,
c.formSubmissionTabId,
c.formCode,
c.version,
c.title,
d.sectionId,
d.title as sectionTitle,
f[0]['value'] as number,
f[1].valueCaption as taskDesc,
f[2].valueCaption as taskValue,
f[2].taskCode,
f[2].lastUpdatedByUserCode,
(f[3].child[0]['value'] = "" ? [] : StringToArray(f[3].child[0]['value'])) as photoGuid,
f[3].child[1]['value'] as remark,
c.createdDate
FROM c
JOIN d IN c.sections
JOIN e IN d.elements
JOIN f IN e.elements
WHERE c.formSubmissionId= '4b604512-b409-4a19-ba79-9ac5ab68e16c'
```

**Catatan penting — `TAKEPHOTO.value` disimpan sebagai JSON-encoded string, bukan array native:**

```
"value": "[\"1ccac17f-f8aa-49fe-9c53-5cc4c30ae77d\",\"8ffc591c-8a6d-46e4-bfdb-d7a4d5590a47\"]"
```

Ambil apa adanya (`f[3].child[0]['value']`) akan menghasilkan string yang terlihat seperti array tapi tipenya tetap string — gunakan `StringToArray()` untuk parse jadi array beneran. Jika task tidak diisi foto, `value` kemungkinan `""` (empty string) — bukan JSON array valid, sehingga `StringToArray("")` menghasilkan `undefined` dan Cosmos akan **drop** field `photoGuid` dari hasil row tersebut (bukan error, tapi field-nya hilang). Query di atas sudah membungkus dengan ternary agar selalu dapat array (kosong jika tidak ada foto).

### Query — Tab General (flat elements)

Tab General **tidak** punya struktur row (`NUMBERINGTEXT`/`BANKTASK`/`INLINE`) — tiap section langsung berisi list elemen datar, jadi cukup 2 level join (`sections` → `elements`), tidak perlu join ketiga (`f`):

```sql
SELECT 
c.formSubmissionId,
c.formSubmissionTabId,
c.formCode,
c.version,
c.title,
d.sectionId,
d.title as sectionTitle,
'' as number,
e.label as taskDesc,
(e.valueCaption != null AND e.valueCaption != "" ? e.valueCaption : e['value']) as taskValue,
e.taskCode,
e.lastUpdatedByUserCode,
(e.elementCode = 'CAMERACAPTURE' ? [e['value']]
    : e.elementCode = 'PHOTOLIST' ? (e.valueCaption = "" ? [] : [
        {"label": StringToArray(REPLACE(e.caption, "'", '"'))[0], "value": StringToArray(e.valueCaption)[0][0]},
        {"label": StringToArray(REPLACE(e.caption, "'", '"'))[1], "value": StringToArray(e.valueCaption)[1][0]},
        {"label": StringToArray(REPLACE(e.caption, "'", '"'))[2], "value": StringToArray(e.valueCaption)[2][0]},
        {"label": StringToArray(REPLACE(e.caption, "'", '"'))[3], "value": StringToArray(e.valueCaption)[3][0]},
        {"label": StringToArray(REPLACE(e.caption, "'", '"'))[4], "value": StringToArray(e.valueCaption)[4][0]}
      ])
    : null) as photoGuid,
'' as remark
FROM c
JOIN d IN c.sections
JOIN e IN d.elements
WHERE c.formSubmissionId = '4b604512-b409-4a19-ba79-9ac5ab68e16c'
  AND c.title = 'General'
  AND (
        e.isShow = true
        OR e.elementCode = 'PHOTOLIST'
      )
```

Perbedaan penting dari query tab spesifik:

| Aspek | Tab Spesifik | Tab General |
|---|---|---|
| `taskCode` / `lastUpdatedByUserCode` | Hanya ada di sub-elemen tertentu dalam `INLINE` | Ada langsung di tiap elemen |
| `taskValue` | Selalu di `valueCaption` | `valueCaption` kadang kosong (mis. `ACTUALSERVICESTART`, `TEXTFIELD` Current SMU) — fallback ke `value` |
| Foto | `TAKEPHOTO.value` = JSON-encoded string, flat array of GUID (`["guid1","guid2"]`) | `CAMERACAPTURE.value` = GUID string langsung; `PHOTOLIST` = array of object `{label, value}` — keduanya tetap di `photoGuid` |
| Filter `isShow` | Elemen jawaban selalu punya `isShow` | `CUSTOMCONTENT` dan `PHOTOLIST` tidak punya key `isShow` sama sekali — filter default akan drop keduanya, makanya ada `OR e.elementCode = 'PHOTOLIST'` |

**Konfirmasi — `PHOTOLIST` field mapping-nya kebalik dari elemen lain:** label per slot foto ada di `caption` (bukan `label`), dan isi/path foto ada di `valueCaption` (bukan `value`). Field `value` (`"[[0], [0], [0], [0], [0]]"`) cuma placeholder index, bukan data foto yang sebenarnya — jangan dipakai. Bentuknya **nested array** — satu array per slot foto, cocok dengan jumlah label di `caption`:

```
"valueCaption": "[[\"path1.jpg\"], [\"path2.jpg\"], ...]"
```

`photoGuid` untuk `PHOTOLIST` berupa array of object `{label, value}` — label dari `caption`, value (path foto) dari `valueCaption`, dipasangkan per index slot foto dalam satu object supaya tidak perlu zip manual di aplikasi.

**Kenapa index-nya di-hardcode 0–4 (bukan loop/subquery):** Cosmos DB SQL API tidak mendukung iterasi dinamis untuk memasangkan `caption[i]` dengan `valueCaption[i][0]` — sudah dicoba dua cara (`FROM p IN StringToArray(...)` dan `JOIN idx IN [0,1,2,3,4]`), keduanya error **SC1001**, karena `JOIN`/`FROM ... IN ...` di Cosmos DB SQL API hanya menerima property path yang sudah ada di dokumen (mis. `c.sections`, `d.elements`) sebagai sumber array — bukan hasil function call maupun array literal. Karena itu query di atas hardcode 5 index (0–4) sesuai jumlah slot foto pada contoh form IIR (`FORM394`) ini.

**⚠ Known limitation — jumlah slot foto di-hardcode 5:** Kalau `PHOTOLIST` di form lain punya jumlah slot foto berbeda (caption/valueCaption count ≠ 5), query ini perlu disesuaikan jumlah entri object-nya secara manual. Index yang melebihi panjang array akan menghasilkan `undefined` (bukan error) untuk slot yang tidak ada — aman tapi elemen array-nya hilang dari output, bukan `null`.

**`caption` (label per slot) berformat Python/JS single-quote, bukan JSON valid:** `"['Foto Tampak Depan', 'Foto Tampak Samping Kanan', ...]"` — sama seperti kasus `LABOURPERSONNEL`/`ASSETNUMBER` di bawah, `StringToArray()` langsung akan gagal parse. Query di atas fix ini dengan `REPLACE(e.caption, "'", '"')` (ganti semua single quote jadi double quote) sebelum di-parse — asumsinya teks label tidak mengandung karakter apostrof (`'`) di dalamnya; kalau ada (mis. label "Driver's Seat"), replace ini akan merusak JSON-nya.

**Gotcha — `value` adalah reserved keyword di Cosmos DB SQL API.** Selalu akses field `value` pakai bracket notation (`e['value']`), **bukan** dot notation (`e.value`) — dot notation akan error karena bentrok dengan keyword `VALUE` yang dipakai di syntax `SELECT VALUE`. Field lain (`valueCaption`, `taskCode`, dll) aman pakai dot notation seperti biasa. Lihat juga query tab spesifik di atas — semua akses ke `value` konsisten pakai `['value']`.

**Query di atas contoh untuk form IIR** (`FORM394`). Section-nya cuma "Personnel Information", "Asset Information", dan satu section tanpa judul (`CUSTOMCONTENT` + `PHOTOLIST`) — tidak ada section "WICOPE Quality Check", jadi filter yang mengecualikan `WICOPE Quality Check`/`DATETIME`/`DROPDOWN` (pernah ada di draft sebelumnya) sudah dihapus dari query ini. General tab adalah **template shared** yang isinya (section + elemen) berbeda-beda antar form (lihat [Mekanisme General Tab Template](form-builder.md#mekanisme-general-tab-template)) — jadi kalau nanti query ini dipakai untuk form lain, cek dulu section apa saja yang benar-benar ada di form tersebut sebelum reuse filter `isShow`/`elementCode` di atas.

**Elemen dengan `value` berupa object-literal string (bukan valid JSON):** `LABOURPERSONNEL` dan `ASSETNUMBER` menyimpan `value` dalam format Python/JS-style single-quote (`"{'userCode': '...'}"`), bukan JSON valid — `StringToObject()` akan gagal di-parse. Query di atas menghindari ini dengan selalu prioritaskan `valueCaption` (yang terisi untuk kedua elemen ini) sebagai `taskValue`.

---

## Flow — Form Submission & Approval

1. Admin HO membuat form di **Form Builder** (web)
2. Form dikonfigurasi agar muncul di menu **Form Submission** (mobile)
3. User yang memiliki akses memilih form dari list (self-service , pooling)
4. User mengisi form dan submit — support **offline-first**
5. Satu form diisi oleh **satu user** dari awal sampai submit (single-user, linear)
6. Setelah submit → masuk ke **Approval Workflow**
7. Jumlah step approval ditentukan oleh konfigurasi workflow
8. Setelah semua step selesai → **Fully Approved**
