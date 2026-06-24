# dplan — DigitalPlanning Table

*Last updated: 2026-06-24*

---

**Service:** `dplan`
**SQL DB:** `DPlanDB`

---

## Schema Tabel `DigitalPlanning`

```
PlanId                    ← PK
PlanName                  ← nama plan (→ WorkOrder.Description)
SiteId                    ← site lokasi (→ WorkOrder.SiteCode)
Location
Status                    ← lifecycle: DRAFT | SUBMIT | INPROGRESS | FINISH | CANCEL
ProjectStart              ← tanggal mulai (→ WorkOrder.ScheduleStartDate)
ProjectFinish
Priority
NotifNo
StartBreakdown
FinishBreakdown
HourMeter
EstimateRFU
TargetRFU
PlanDuration
ActualDuration
RevisionDuration
PIC
IsBMP
ExecutionType
SourcePlanning
MaintenanceCategoryCode   ← (→ WorkOrder.MaintenanceCategoryCode)
MaintenanceCategoryName   ← di-join dari DPlanDB.MaintenanceCategory.MaintenanceCategoryName (→ WorkOrder.MaintenanceCategoryName)
                            ⚠ Known gap: saat ini kolom ini kosong di data existing — hanya MaintenanceCategoryCode yang terisi.
                            Requirement: saat plan dibuat, MaintenanceCategoryName harus disimpan sekaligus
                            dengan cara join ke DPlanDB.MaintenanceCategory berdasarkan MaintenanceCategoryCode.
TemplateId
IsActive
CreatedBy
CreatedUtcDate
SubmittedUtcDate          ← timestamp saat plan di-SUBMIT — digunakan untuk hitung elapsed packageSyncStatus
ModifiedBy
ModifiedUtcDate
NotifNoStatus
FinishBreakdownExecution
```

## Planning Lifecycle

```
DRAFT → SUBMIT → INPROGRESS → FINISH
```

| Status | Keterangan |
|--------|------------|
| `DRAFT` | Plan dibuat, form assignment bisa dilakukan/diubah |
| `SUBMIT` | Plan dikonfirmasi Planner — form assignment terkunci, trigger Service Bus event ke maintenance-execution |
| `INPROGRESS` | Eksekusi sedang berjalan di lapangan |
| `FINISH` | Eksekusi selesai |
| `CANCEL` | Terminal state — plan dibatalkan |

> `SubmittedUtcDate` diisi saat status berubah ke `SUBMIT`. Digunakan oleh `GET /api/work-card/detail` untuk menghitung elapsed time guna menentukan `packageSyncStatus` (pending vs error setelah 10 menit).
