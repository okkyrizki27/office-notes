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
Id
TaskId              ← FK ke Task.Id
UserCode            ← identitas mechanic
IsPrecautionConfirmed
MachineSMUValue
MachineSMUAddress
Status
IsActive
CreatedAt, CreatedBy
ModifiedAt, ModifiedBy
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

## Flow — Form Submission & Approval

1. Admin HO membuat form di **Form Builder** (web)
2. Form dikonfigurasi agar muncul di menu **Form Submission** (mobile)
3. User yang memiliki akses memilih form dari list (self-service , pooling)
4. User mengisi form dan submit — support **offline-first**
5. Satu form diisi oleh **satu user** dari awal sampai submit (single-user, linear)
6. Setelah submit → masuk ke **Approval Workflow**
7. Jumlah step approval ditentukan oleh konfigurasi workflow
8. Setelah semua step selesai → **Fully Approved**
