# PM Shutdown — Data Model Changes

Dokumen ini merangkum perubahan data model yang dibutuhkan untuk mendukung fitur service package dan multi-mechanic form execution di PM Shutdown.

*Last updated: 2026-06-22*

---

## Ringkasan Perubahan

| Table | Service | Perubahan |
|-------|---------|-----------|
| `PlanForm` | `dplan` | **Tabel baru** — menyimpan form assignment per plan selama status DRAFT |
| `DigitalPlanning` | `dplan` | Fix: simpan `MaintenanceCategoryName` saat plan dibuat (join dari `MaintenanceCategory`) |
| `Task` | `maintenance-execution` | Tambah kolom SMU; `Name` diisi FormName dari maintenance-strategy saat consumer process event |
| `TaskPersonalized` | `maintenance-execution` | Hapus kolom SMU, tambah `StartedAt`, support N records per Task |
| `FormSubmission` | `maintenance-execution` | Tambah `FormName` dan `IsMandatory` |
| `TaskMechanic` | `maintenance-execution` | ~~Tidak jadi~~ — TaskPersonalized sudah support N records |

---

## PlanForm (Tabel Baru — dplan)

Tabel ini menyimpan form assignment yang dilakukan Planner selama plan masih berstatus `DRAFT`. Data di sini menjadi sumber saat plan di-SUBMIT untuk generate Task + FormSubmission + Cosmos snapshot di `maintenance-execution`.

### Schema

| Kolom | Tipe | Nullable | Default | Keterangan |
|-------|------|----------|---------|------------|
| `Id` | GUID | No | — | PK |
| `PlanId` | GUID | No | — | FK ke Plan |
| `FormCode` | NVARCHAR | No | — | Identitas form lintas versi — versi aktif di-resolve saat SUBMIT |
| `FormName` | NVARCHAR | No | — | Snapshot nama form — di-set saat assign (DRAFT) dan di-refresh saat SUBMIT dari `maintenance-strategy` |
| `IsMandatory` | BIT | No | 0 | Ditentukan Planner, default OFF |
| `IsDeleted` | BIT | No | 0 | Soft delete saat Planner unassign form di DRAFT |
| `CreatedAt` | DateTime | No | — | |
| `CreatedBy` | NVARCHAR | No | — | |
| `ModifiedAt` | DateTime | Yes | NULL | |
| `ModifiedBy` | NVARCHAR | Yes | NULL | |

### Lifecycle

- **DRAFT** — Planner bebas tambah/unassign form. Unassign menggunakan soft delete (`IsDeleted = 1`), bukan hard delete.
- **SUBMIT** — Form assignment terkunci. dplan melakukan:
  1. Resolve `FormCode` → `maintenance-strategy.Form` (where `IsActive = 1`) untuk mendapat `FormName` terbaru
  2. UPDATE `PlanForm.FormName` dengan nama terbaru
  3. Publish event `PlanSubmitted { PlanId, PlanForms: [{ FormCode, IsMandatory }] }` ke Service Bus
  > Downstream processing (Task, FormSubmission, Cosmos snapshot) ditangani oleh maintenance-execution consumer — lihat section **SUBMIT Flow — Service Bus**.
- **SUBMIT ke atas** — `PlanForm` tidak bisa diubah.

### Catatan

- `FormCode` digunakan (bukan `FormId`) karena Planner tidak peduli versi — versi aktif di-resolve saat SUBMIT. Jika form mendapat versi baru antara DRAFT dan SUBMIT, snapshot akan menggunakan versi terbaru. Ini adalah **intended behavior**.
- `FormName` di-set saat assign (DRAFT) untuk keperluan pre-populate modal "Choose Form" saat planner buka kembali draft. Saat SUBMIT, `FormName` di-refresh dari `maintenance-strategy` sebelum dipakai untuk membuat `Task` dan `FormSubmission` — memastikan nama yang tersimpan adalah nama terbaru dari versi aktif.

---

## DigitalPlanning — Fix (dplan)

Saat ini kolom `MaintenanceCategoryName` di `DPlanDB.DigitalPlanning` selalu kosong — hanya `MaintenanceCategoryCode` yang terisi. Sebagai bagian dari Phase 1, dplan perlu menyimpan name-nya saat plan dibuat.

### Yang Perlu Difix

Saat `DigitalPlanning` record dibuat atau diupdate, lakukan join ke `DPlanDB.MaintenanceCategory` berdasarkan `MaintenanceCategoryCode` dan simpan hasilnya ke `DigitalPlanning.MaintenanceCategoryName`.

```sql
-- Contoh logic saat insert/update DigitalPlanning:
SELECT Name FROM DPlanDB.MaintenanceCategory
WHERE MaintenanceCategoryCode = @MaintenanceCategoryCode
```

Ini dibutuhkan agar `PlanSubmitted` event bisa menyertakan `MaintenanceCategoryName` yang valid tanpa harus join di sisi publisher setiap kali event dikirim.

---

## WorkOrder

### Column Mapping — Sumber Data saat Consumer Process Event

| Kolom WorkOrder | Sumber | Keterangan |
|-----------------|--------|------------|
| `PlanId` | `DPlanDB.DigitalPlanning.PlanId` | FK ke plan |
| `Description` | `DPlanDB.DigitalPlanning.PlanName` | |
| `ScheduleStartDate` | `DPlanDB.DigitalPlanning.ProjectStart` | |
| `SiteCode` | `DPlanDB.DigitalPlanning.SiteId` | |
| `AssetNumber` | `DPlanDB.DPEquipment.Equipment` | |
| `AssetModelCode` | `cst-iams-sqldb-services-asset` — `Asset.AssetModelCode` | |
| `AssetModelName` | `cst-iams-sqldb-services-asset` — `AssetModel.Name` | |
| `SectionTypeCode` | `cst-iams-sqldb-services-asset` — `Asset.SectionTypeCode` | |
| `MaintenanceCategoryCode` | `DPlanDB.DigitalPlanning.MaintenanceCategoryCode` | |
| `MaintenanceCategoryName` | `DPlanDB.MaintenanceCategory.MaintenanceCategoryName` | |
| `Source` | Hardcoded `"Digiplan"` | Default untuk semua WorkOrder dari Digiplan |

### Status Flow
```
Open → In Progress → Complete
```

| Status | Trigger |
|--------|---------|
| `Open` | WorkOrder dibuat saat consumer process event `PlanSubmitted` |
| `In Progress` | Mechanic pertama klik "Start" pada form apapun dalam package |
| `Complete` | Finish Execution dilakukan oleh Supervisor/Foreman/Mechanic |

---

## Task

### Kolom Baru
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `MachineSMUValue` | - | Dipindah dari TaskPersonalized — 1 nilai per service execution |
| `MachineSMUAddress` | - | Dipindah dari TaskPersonalized |

### Kolom Existing yang Dipakai
| Kolom | Keterangan |
|-------|------------|
| `Name` | Diisi dengan `FormName` yang di-resolve dari `maintenance-strategy` saat consumer process event — tidak perlu kolom baru |

### Status Flow
```
Open → In Progress → Complete → Approved
```

| Status | Trigger |
|--------|---------|
| `Open` | Task dibuat saat plan berpindah ke status SUBMIT |
| `In Progress` | Saat sync: server hitung ulang MIN(StartedAt) dari semua TaskPersonalized yang ada — termasuk yang sync belakangan |
| `Complete` | Saat satu mechanic submit form |
| `Approved` | Setelah approval workflow selesai |

> **Catatan:** Jika Task dibuat offline dan sync belakangan, `In Progress` menggunakan `StartedAt` terkecil dari semua TaskPersonalized yang ada — bukan berdasarkan urutan sync.

---

## TaskPersonalized

### 1 Task = N TaskPersonalized
Setiap mechanic yang mengerjakan form memiliki record TaskPersonalized sendiri. Dibuat saat mechanic tap **"Assign to Me"** di 3-dot menu form card — bukan saat tap "Start".

### Kolom Dihapus
| Kolom | Keterangan |
|-------|------------|
| `MachineSMUValue` | Dipindah ke Task |
| `MachineSMUAddress` | Dipindah ke Task |

### Kolom Baru
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `StartedAt` | DateTime | Device timestamp saat mechanic pertama kali tap "Start" pada form ini |

### Deduplication
Server melakukan **upsert** berdasarkan `TaskId + UserCode` — mencegah duplikasi jika mechanic assign di lebih dari satu device.

### "Start" Button
Tombol "Start" muncul ketika mechanic yang sudah ter-assign membuka form, baik untuk pertama kali maupun melanjutkan. Tap "Start" membuat **TaskPersonalizedLog** (activity record) — bukan TaskPersonalized.

**Yang terjadi saat mechanic tap "Start":**

**TaskPersonalizedLog** (setiap tap "Start" di shift baru):
1. Jika tidak ada open session di shift yang sama → buat TaskPersonalizedLog record baru (StartDate = device timestamp, ShiftName = shift saat ini)
2. Jika ada open session di shift sebelumnya → client auto-close session tersebut (set EndDate = shift end time), lalu buat TaskPersonalizedLog baru
3. Jika sudah ada open session di shift yang sama → tidak buat record baru, langsung masuk form

Semua operasi di-queue dalam satu batch sync — tidak ada sync terpisah per operasi.

### Status per TaskPersonalized
| Kondisi | Status |
|---------|--------|
| Mechanic membuka form dan mulai mengisi | `In Progress` |
| Form disubmit (oleh siapapun) | `Complete` — semua TaskPersonalized pada Task tersebut diupdate |

### Offline Behavior
- Tapping "Start" while offline → record dibuat lokal, di-queue untuk sync
- Saat sync: server upsert berdasarkan `TaskId + UserCode`
- `Task.Status → In Progress` menggunakan MIN(StartedAt) dari semua TaskPersonalized yang ada — server selalu hitung ulang termasuk jika ada record yang sync belakangan dengan StartedAt lebih kecil

---

## FormSubmission

### Kolom Baru
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `FormName` | NVARCHAR | Snapshot nama form saat plan di-SUBMIT — disimpan di dua tempat: `Task.Name` dan di sini |
| `IsMandatory` | BIT | Disalin dari `PlanForm.IsMandatory` saat plan di-SUBMIT. Default 0 untuk existing records |

---

## SUBMIT Flow — Service Bus

Proses saat plan di-SUBMIT melibatkan 3 database lintas service. Untuk menghindari partial failure yang sulit di-rollback, downstream processing ke `maintenance-execution` dilakukan async via **Azure Service Bus**.

### Atomicity: Outbox Pattern

> **Catatan untuk developer:** Pendekatan di bawah ini adalah suggestion menggunakan Outbox Pattern untuk menjamin atomicity antara SUBMIT status change dan event publish. Jika ada pendekatan lain yang lebih sesuai dengan kondisi infrastruktur dan tim, dipersilakan untuk menyesuaikan.

Risiko tanpa Outbox Pattern:
```
1. COMMIT status SUBMIT ke DPlanDB  → sukses
2. Publish event ke Service Bus     → GAGAL
→ Status = SUBMIT, consumer tidak pernah jalan, maintenance-execution tidak tahu
```

Solusi — Outbox Pattern:
```
Dalam satu DB transaction di DPlanDB:
  1. UPDATE DigitalPlanning.Status = 'SUBMIT'
  2. INSERT Outbox { EventType='PlanSubmitted', Payload=..., Status='Pending' }
  → COMMIT

Background relay job (dplan):
  - Poll Outbox WHERE Status='Pending'
  - Publish ke Azure Service Bus
  - UPDATE Outbox.Status = 'Published'
  → Jika publish gagal: retry via relay job (bukan via Service Bus retry)
  → Atomicity terjamin: jika DB commit sukses, event PASTI eventually ter-publish
```

### Flow Lengkap

```
dplan — saat status DRAFT → SUBMIT:
  0. [Pre-SUBMIT Validation] Tampilkan confirmation popup berisi daftar form yang di-assign.
     Sekaligus cek ketersediaan setiap FormCode di maintenance-strategy:
     Form dianggap TIDAK available jika:
       - Tidak ditemukan sama sekali di maintenance-strategy (hard deleted), ATAU
       - IsActive = 0 (versi tidak aktif), ATAU
       - Status = 'Archived'
       - Jika semua form available → Planner bisa klik Confirm
       - Jika ada yang tidak available → Planner tidak bisa lanjut.
         Harus: (a) hapus form tersebut dari assignment, atau (b) aktifkan/un-archive form di Form Builder
  1. Resolve FormCode → maintenance-strategy.Form (IsActive=1) → dapat FormName terbaru
  2. UPDATE PlanForm.FormName
  3. Publish event → Azure Service Bus:
     PlanSubmitted {
       PlanId,
       PlanName,                ← DPlanDB.DigitalPlanning.PlanName
       ProjectStart,            ← DPlanDB.DigitalPlanning.ProjectStart
       SiteId,                  ← DPlanDB.DigitalPlanning.SiteId
       MaintenanceCategoryCode, ← DPlanDB.DigitalPlanning.MaintenanceCategoryCode
       MaintenanceCategoryName, ← DPlanDB.DigitalPlanning.MaintenanceCategoryName
                                   (diisi setelah fix — lihat section DigitalPlanning Fix)
       AssetNumber,             ← DPlanDB.DPEquipment.Equipment
       PlanForms: [{ FormCode, IsMandatory }]
     }
     ← Event hanya berisi data yang dplan tahu.
       FormId/FormName/Version dan asset detail di-resolve oleh consumer.

[Azure Service Bus]
  ↓ (async, retry-able)

maintenance-execution consumer:
  1. Fetch dari cst-iams-sqldb-services-asset: AssetModelCode, AssetModelName, SectionTypeCode
     berdasarkan AssetNumber dari event
  2. Fetch dari maintenance-strategy: FormId, FormName, Version per FormCode
  3. SQL upsert WorkOrder lengkap (idempotent by PlanId):
       PlanId, Description=PlanName, ScheduleStartDate=ProjectStart, SiteCode=SiteId,
       AssetNumber, AssetModelCode, AssetModelName, SectionTypeCode,
       MaintenanceCategoryCode, MaintenanceCategoryName, Source="Digiplan"
  4. SQL upsert Task + FormSubmission (idempotent by PlanId + FormCode)
  5. Per FormSubmission:
       - DELETE existing Cosmos docs (safety for retry)
       - Cosmos Transactional Batch (partition: FormSubmissionId):
           INSERT tab1_doc, tab2_doc, ... (all-or-nothing)

Jika consumer gagal → Service Bus retry otomatis
Jika irrecoverable (semua retry habis) → masuk Dead-Letter Queue untuk investigasi manual
Step 3-4 idempotent (upsert) → aman di-retry
Step 5 delete-then-reinsert → aman di-retry

### Retry Policy — Suggestion

> **Catatan untuk developer:** Ini adalah suggestion berdasarkan karakteristik operasi consumer. Jika ada pendekatan yang lebih baik sesuai kondisi infrastruktur dan kebutuhan aktual, dipersilakan untuk menyesuaikan.

| Parameter | Suggested Value | Alasan |
|-----------|----------------|--------|
| Max Delivery Count | 5 | Cukup untuk transient failure (network timeout, DB throttling). Lebih dari 5 biasanya indikasi bug permanen yang tidak akan sembuh dengan retry |
| Lock Duration | 5 menit | Cukup untuk menyelesaikan semua fetch + SQL write + Cosmos batch dalam satu attempt |
| Backoff | Exponential — 30s, 1m, 2m, 4m | Menghindari hammer ke downstream service yang sedang recover |
| Dead-Letter Queue | Setelah attempt ke-5 | Alert ke ops untuk investigasi manual — lebih baik cepat masuk DLQ daripada mechanic menunggu berjam-jam dengan status `pending` |

> **Catatan implementasi:** Exponential backoff tidak tersedia native di Azure Service Bus Standard tier — memerlukan Premium tier atau workaround via scheduled re-enqueue. Konfirmasi tier yang dipakai sebelum implementasi.

Edge case — Form di-archive setelah SUBMIT tapi sebelum consumer process event:
  - Consumer tetap buat Task + FormSubmission (menggunakan PlanForm.FormName sebagai fallback)
  - Cosmos snapshot TIDAK dibuat (form tidak available di maintenance-strategy)
  - Mechanic melihat form card di Tab Form tapi tidak bisa dibuka → tampilkan error state:
    "Form not available. Please contact your admin."
  - Solusi permanen (admin trigger re-copy Cosmos snapshot setelah form di-un-archive):
    DEFERRED to next MVP
```

### packageSyncStatus

Mobile perlu membedakan dua kondisi yang tampak sama (Tab Form kosong):

| Kondisi | `packageSyncStatus` | UX Mobile |
|---------|---------------------|-----------|
| `PlanForm WHERE IsDeleted=0` count = 0 | `none` | Empty state biasa |
| `PlanForm WHERE IsDeleted=0` count > 0, `Task` count = 0 | `pending` | "Service package sync in progress, wait for a moment" |
| `Task` count > 0 | `ready` | Tampilkan list form |

Field `packageSyncStatus` di-derive oleh `GET /api/work-card/detail` — tidak perlu kolom status tambahan di DB. Gunakan `PlanForm WHERE IsDeleted = 0` — jangan hitung form yang sudah di-soft delete. Failure ditangani oleh Dead Letter Queue + monitoring operasional, tidak ditampilkan ke user mobile.

**Finish Execution gate** — jika `packageSyncStatus = pending`, Finish Execution di-block dengan hint: "⚠ Form package is not yet available. Please try again later or contact your admin."

---

## Breaking Changes & Migration

| Perubahan | Impact | Action |
|-----------|--------|--------|
| `MachineSMUValue` & `MachineSMUAddress` pindah dari TaskPersonalized → Task | Data existing di TaskPersonalized perlu dimigrate ke Task | Migration script diperlukan |
| TaskPersonalized: 1 Task bisa N records | Logic yang mengasumsikan 1 Task = 1 TaskPersonalized perlu direview | Audit existing queries & business logic |

---

## Keputusan Desain

1. **Device Spec** — Mechanic, Foreman, dan Supervisor menggunakan device pribadi masing-masing dengan spesifikasi beragam. Perlu ada minimum spec requirement yang dikomunikasikan ke user sebelum rollout.

2. **Planning Lifecycle & Form Assignment Lock** — ✅ Dikonfirmasi: Submit plan tanpa form assignment tetap dibolehkan. Setelah plan berstatus `SUBMIT` ke atas, form assignment tidak bisa ditambah atau diubah.

3. **Mechanic Identity** — ✅ Dikonfirmasi: **Individual account** — setiap mechanic, foreman, dan supervisor memiliki akun masing-masing.

4. **"Assign to Me" Flow** — ✅ Dikonfirmasi: `TaskPersonalized` dibuat saat mechanic melakukan "Assign to Me" via 3-dot menu di Form Tab workcard PM Shutdown. Flow: buka workcard PM Shutdown → Tab Form → klik ··· pada form card → klik "Assign to Me".

---

## Catatan Arsitektur

- `StartedAt` = device clock (bisa tidak akurat) — acceptable risk, konsisten dengan known limitation timestamp offline yang sudah didokumentasikan
- `CreatedAt` = server timestamp saat sync — berbeda dari `StartedAt` karena offline gap
- Submit form → masuk approval workflow (sama seperti Form Submission)
- **Finish Execution gate** — validasi dari dua sumber berbeda:
  1. **Backlog execution selesai** → query `dPlan` (existing, tidak berubah)
  2. **Semua mandatory form Complete** → query `maintenance-execution`: semua `Task` di WorkOrder tersebut dimana `FormSubmission.IsMandatory = true` harus memiliki `Task.Status = Complete`
- `FormSubmission` tidak memiliki kolom Status — status form execution direpresentasikan oleh `Task.Status`
- `FormName` disimpan di dua tempat: `Task.Name` (untuk keperluan task tracking) dan `FormSubmission.FormName` (untuk keperluan form execution & reporting)
