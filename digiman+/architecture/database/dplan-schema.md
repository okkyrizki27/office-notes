# Database Schema — `dplan`

*Sumber: DDL script asli (`dplan.sql`), schema `dbo`, script date 15/07/2026 1:53 PM — skema real, bukan document-derived.*
*Disimpan: 15 Jul 2026.*
*DB: `DPlanDB`, alias `dplan` — lihat [`digital-planning.md`](../dplan/digital-planning.md) dan [`man-power-man-hours-excel-enhancement.md`](../dplan/man-power-man-hours-excel-enhancement.md).*

---

Dokumen ini referensi mentah struktur tabel `DPlanDB`. Untuk narasi/business logic Daily Plan (lifecycle, hierarki task, dynamic column, predecessor), lihat [`digital-planning.md`](../dplan/digital-planning.md). Skema real ini jauh lebih luas dari yang sudah didokumentasikan — narasi yang ada baru cover hierarki inti (`DigitalPlanning`/`DPTask`/`DPPredecessor`/`DPColumn`/`DPValue`); DB ini ternyata juga menyimpan modul **Weekly Schedule/Backlog** (budget & approval Planner↔PSCM), **sinkronisasi SAP MO** sendiri (terpisah dari `maintenance-order`), dan replikasi **User/Site/Equipment** master data.

---

## Hierarki Inti Digital Planning

### `DigitalPlanning`, `DPTask`, `DPPredecessor`, `DPColumn`, `DPValue`
> ✅ **Kelima tabel ini cocok persis (field-for-field)** dengan versi document-derived di [`digital-planning.md`](../dplan/digital-planning.md) — terkonfirmasi real, tidak ada perbedaan. Tidak diulang di sini; lihat dokumen tersebut untuk skema lengkap + narasi lifecycle/EAV/predecessor.
>
> Satu detail konstruksi FK yang belum disebut di narasi: `DPPredecessor.FromTask` punya FK formal ke `DPTask.TaskId` (`ON DELETE CASCADE`), tapi **`ToTask` tidak punya FK constraint sama sekali** — asimetris. Kemungkinan disengaja (hapus task sumber otomatis hapus predecessor-nya, tapi hapus task tujuan tidak), atau oversight saat desain.

### `DPActivity` (extension 1:1 dari `DigitalPlanning` — audit lifecycle)
```
PlanId              FK → DigitalPlanning.PlanId (tanpa constraint formal), tanpa PK sendiri
CreatedBy, CreatedName, CreatedUtcDate
SubmittedBy, SubmittedName, SubmittedUtcDate
StartedBy, StartedName, StartedUtcDate
FinishedBy, FinishedName, FinishedUtcDate
CanceledBy, CanceledName, CanceledUtcDate
BDSyncResult        int, null
BDSyncUtcDate       datetime, null
```
Snapshot nama+waktu untuk tiap transisi status (`DRAFT→SUBMIT→INPROGRESS→FINISH`/`CANCEL`, lihat lifecycle di narasi) — satu row per Plan, di-update in-place per transisi (bukan log/history). `BDSyncResult`/`BDSyncUtcDate` belum pernah dibahas — kemungkinan hasil sinkronisasi ke Breakdown/BD Corrective saat plan berasal dari breakdown (`DigitalPlanning.StartBreakdown`/`FinishBreakdown`).

### `DPTaskOverview` (cache progress 1:1 dari `DigitalPlanning`)
```
PlanId              FK → DigitalPlanning.PlanId, tanpa PK sendiri
TaskAll             int, not null
TaskDone            int, not null
RemarkDone          int, not null
MainTaskProgress    decimal(18,2), null
ModifiedBy, ModifiedUtcDate   not null
```
Rollup progress plan (jumlah task selesai / total, dsb) — kemungkinan dipakai untuk progress bar di listing plan, di-maintain lewat trigger/proc tiap ada perubahan `DPTask`.

### `DPEquipment`
```
PlanId              FK → DigitalPlanning.PlanId
Equipment           varchar(100), not null
CreatedUtcDate       datetime, null
ModifiedUtcDate      datetime, not null
```
Tanpa PK sendiri (heap, N Equipment per Plan) — daftar equipment yang terkait plan (multi-equipment per plan dimungkinkan).

### `DPRemarkOverduration`
```
Id                  PK, bigint, identity
PlanId              FK → DigitalPlanning.PlanId
RemarkOverduration  varchar(300), null
CreatedBy, CreatedUtcDate   not null
ModifiedBy, ModifiedUtcDate null
```
Remark wajib kemungkinan saat durasi aktual plan melebihi plan duration — relevan untuk diskusi rollup Duration di [`man-power-man-hours-excel-enhancement.md`](../dplan/man-power-man-hours-excel-enhancement.md) (siapa yang harus kasih justifikasi kalau parent Duration/Man Hours melenceng dari plan).

---

## Comment, Notification & Change Log

### `DPComment` / `DPNotification`
```
DPComment:
CommentId    PK, bigint, identity
PlanId       FK → DigitalPlanning.PlanId
Comment      varchar(max), not null
CreatedBy, CreatedUtcDate   not null
ModifiedBy, ModifiedUtcDate null

DPNotification:
NotificationId  PK, bigint, identity
CommentId       FK → DPComment.CommentId, ON DELETE CASCADE
UserId          bigint, not null
IsRead          bit, not null (default 0)
IsSend          bit, not null (default 0)
ReadUtcDate     datetime, null
CreatedBy, CreatedUtcDate   not null
```
Comment thread per plan + fan-out notifikasi per user (`IsRead`/`IsSend` terpisah — kemungkinan `IsSend` untuk push/email, `IsRead` untuk status baca di UI).

### `DPCancel`
```
CancelId       PK, bigint, identity
PlanId         FK → DigitalPlanning.PlanId
Action         varchar(50), not null
Reason         varchar(1000), not null
CreatedBy, CreatedUtcDate   not null
PlanningType   varchar(10), null
```
`PlanningType` belum jelas nilai apa saja (kemungkinan membedakan cancel di level `DigitalPlanning` vs `WeeklySchedule`, karena dua modul planning ini hidup di DB yang sama — lihat bagian Weekly Schedule).

### `DPChangeLog`
```
LogId        PK, bigint, identity
TableName    varchar(1000), not null
ColumnName   varchar(1000), not null
TableId      bigint, not null
OldValue, NewValue   nvarchar(1000), null
CreatedBy, CreatedUtcDate   not null
```
Audit **per kolom** (bukan per row seperti `AuditLog` di service lain yang simpan satu blob `PreviousData`) — polymorphic lewat `TableName`+`TableId`, tanpa FK (di luar jangkauan constraint DB, wajar untuk pola generic audit).

---

## Delay & Activity Breakdown

### `DelayType`, `DelayDescription`
```
DelayType:
DelayTypeId   PK, bigint, identity
DelayName     varchar(100), not null
IconURL       varchar(500), null
Sequence      int, null
IsActive, audit(100)   standard

DelayDescription:
DelayDescriptionId  PK, bigint, identity
DelayTypeId         bigint, not null (tanpa FK formal ke DelayType)
Description         varchar(100), not null
ActivityCode        varchar(10), null   ← lihat ActivityBreakdown di bawah
IsActive, audit(100)   standard
```

### `DPDelay`
```
DelayId              PK, bigint, identity
DelayTypeId          bigint, not null
PlanId               bigint, not null
TaskId               bigint, null
DelayDescriptionId   bigint, not null
DelayType            varchar(100), null   ← denormalized snapshot nama
DelayDescription     varchar(100), null   ← denormalized snapshot nama
Remark               varchar(500), null
Other                varchar(500), null
StartDate, FinishDate   datetime, not null
Duration             decimal(18,2), null
IsActive             bit, not null (default 1)
CreatedBy, CreatedUtcDate   not null
ModifiedBy, ModifiedUtcDate null
ReferenceId          varchar(50), null
```
> Belum pernah dibahas di dokumen manapun. **Tidak ada satupun FK formal** untuk `DPDelay` (`PlanId`/`TaskId`/`DelayTypeId`/`DelayDescriptionId` semua tanpa constraint) — beda dari pola tabel lain di DB ini yang setidaknya FK ke `DigitalPlanning`. Menyimpan alasan keterlambatan per task/plan, dengan `DelayType`/`DelayDescription` di-snapshot sebagai teks (bukan cuma FK Id) — pola sama seperti `DPPareto` di bawah (denormalized Code+Name).

### `ActivityBreakdown`
```
ActivityBreakdownId   PK, int, identity
PlanId                bigint, not null (tanpa FK formal)
ActivityCode          varchar(10), null
ActivityDescription   varchar(100), null
StartDatetime, FinishDatetime   datetime, null
Duration              decimal(18,2), null
IsActive, audit(100)   standard
```
`ActivityCode` sama persis namanya dengan `DelayDescription.ActivityCode` — kemungkinan taxonomy fase breakdown bersama (mis. "diagnose", "order part", "repair", "test") yang dipakai untuk mapping delay per fase breakdown. Relasinya berupa kode yang sama, bukan FK formal — perlu klarifikasi ke tim codebase.

---

## Evidence & Mechanic

### `DPEvidence`
```
EvidenceId   PK, bigint, identity
PlanId       FK → DigitalPlanning.PlanId, ON DELETE CASCADE
TaskId       FK → DPTask.TaskId, ON DELETE CASCADE
Url          varchar(255), not null
CreatedBy, CreatedUtcDate   not null
```

### `DPMechanic`
```
MechanicId    PK, bigint, identity
PlanId        FK → DigitalPlanning.PlanId, ON DELETE CASCADE
TaskId        FK → DPTask.TaskId, ON DELETE CASCADE
UserId        bigint, not null
MechanicType  varchar(10), null   ← kemungkinan PIC vs regular, nilai belum dikonfirmasi
CreatedBy, CreatedUtcDate   not null
ModifiedBy, ModifiedUtcDate not null
```
Assignment mechanic per task (N mechanic per task, beda dari `TemplateTask`/`DPColumn` yang expose "Mechanic Name" sebagai dynamic column tampilan — tabel relasional ini kemungkinan source-of-truth-nya, mirip pola `DPPredecessor` vs kolom "Predecessor" yang sudah dicatat di narasi).

---

## Finding / Pareto Taxonomy

### `DPPareto`
```
DPParetoId            PK, int, identity
PlanId                FK → DigitalPlanning.PlanId, ON DELETE CASCADE
TaskId                bigint, null
ComponentId           int, not null
ComponentCode         varchar(10), null
ComponentName         varchar(512), not null
SubcomponentId        int, not null
SubcomponentCode      varchar(10), null
SubcomponentName      varchar(512), not null
DamageGroupId         int, not null
DamageGroupCode       varchar(10), null
DamageGroupName       varchar(512), not null
DamageCodeId          int, not null
DamageCode            varchar(10), null
DamageCodeName        varchar(512), not null
CauseGroupCode        varchar(100), null
CauseGroupName        varchar(100), null
CauseGroupDefinition  varchar(max), null
CreatedBy, CreatedUtcDate   not null
ModifiedBy, ModifiedUtcDate not null
```
Taxonomy Component/SubComponent/DamageGroup/DamageCode/CauseGroup ini adalah **replika ketiga** dari shape yang sama — muncul juga di `services-asset` ([`Component`/`SubComponent`/`DamageCode`/`DamageGroup`/`CauseCode`/`CauseGroup`](services-asset-schema.md)) dan `maintenance-order.PoolingMOItem` (lihat [`order-emol-sap-sync.md`](../inspection-order/order-emol-sap-sync.md) §5.2). Versi ini **paling terdenormalisasi**: simpan `Id` numerik + `Code` + `Name` sekaligus untuk tiap level (bukan cuma `Code`), plus `CauseGroupDefinition` (deskripsi panjang) yang belum pernah muncul di versi lain. Constraint FK-nya diberi nama `pk_fk_PlanId` — penamaan aneh (prefix `pk_` untuk sebuah FK), kemungkinan sisa copy-paste.

---

## Template — Sumber Snapshot Daily Plan

### `Template`, `TemplateColumn`, `TemplateTask`
```
Template:
TemplateId     PK, bigint, identity
Name           varchar(1000), not null
IsBMP          bit, null (default 0)
ExecutionType  varchar(15), null
SiteId         int, null
IsActive, audit(100)   standard

TemplateColumn:
ColumnId           PK, bigint, identity
TemplateId         FK → Template.TemplateId
ColumnName         varchar(1000), null
CustomColumnName   varchar(1000), null   ← belum ada versi ini di DPColumn (custom-label utk kolom custom?)
DataType           varchar(100), not null
MaxCharacter       int, null
IsMandatory, IsShow   bit, not null
Sequence           int, not null
AllowDelete        bit, not null
CreatedBy, CreatedUtcDate   not null
ModifiedBy, ModifiedUtcDate not null

TemplateTask:
TaskId         PK, bigint, identity
TemplateId     FK → Template.TemplateId
ParentId       FK → TemplateTask.TaskId (self-ref, WITH NOCHECK), default 0
Description    varchar(1000), not null
Sequence       int, not null
ImportParent   bit, not null                      ← DPTask versinya nullable, ini not null
Duration       decimal(18,1), not null (default 0)
JobPercentage  bit, null
Predecessor    varchar(200), null                 ← teks bebas, BUKAN relasional
CreatedBy, CreatedUtcDate   not null
ModifiedBy, ModifiedUtcDate not null
```
> **Konfirmasi & detail baru** untuk "Mekanisme Pembuatan Daily Plan" langkah 3 di [`digital-planning.md`](../dplan/digital-planning.md): `DPColumn`/`DPTask` memang di-snapshot dari `TemplateColumn`/`TemplateTask` saat plan dibuat — sekarang terlihat sumbernya persis. Satu detail penting: `TemplateTask.Predecessor` disimpan sebagai **teks bebas** (`varchar(200)`, kemungkinan format list seperti MS Project, mis. `"3FS+1"`), sedangkan runtime-nya (`DPPredecessor`) sudah jadi **tabel relasional penuh** (`FromTask`/`ToTask`/`Type`/`Lag`) — berarti ada proses parsing teks→relasional saat plan dibuat dari Template. Proses parsing ini belum didokumentasikan di manapun.

---

## Weekly Schedule / Backlog Module (Planner ↔ PSCM)

Modul terpisah dari hierarki `DigitalPlanning` di atas — workflow approval sendiri (`Submitted*`/`Approved*`), kemungkinan ini backing table untuk feature **Backlog Monitoring/MKP** (lihat [`backlog-monitoring-mkp-assessment.md`](../../report/backlog-monitoring/backlog-monitoring-mkp-assessment.md) dkk.) meski penamaan tabel tidak match persis — **belum dikonfirmasi**, lihat Observasi.

### `WeeklySchedule` (header, approval workflow sendiri)
```
ID              PK, bigint, identity
PlanName        varchar(100), not null
Status          varchar(100), not null
SiteId          varchar(10), not null
IsActive        bit, not null (default 1)
CreatedBy, CreatedByName, CreatedUtcDate   not null/null/not null
SubmittedBy, SubmittedByName, SubmittedUtcDate   null
ApprovedBy, ApprovedByName, ApprovedUtcDate   null
ModifiedBy, ModifiedByName   not null/null
ModifiedUtcDate  not null (default getutcdate())
```
Lifecycle `DRAFT→SUBMIT→APPROVE` (via kolom `Submitted*`/`Approved*`) — **berbeda** dari lifecycle `DigitalPlanning` (`DRAFT→SUBMIT→INPROGRESS→FINISH→CANCEL`, tanpa tahap approval). Dua modul planning paralel dalam satu DB, disambungkan lewat `DPMappingWSSummary`.

### `WSSummary`, `WSOutstandingMO` (detail per equipment/MO)
```
WSSummary:
ID                    PK, bigint, identity
WeeklyScheduleID      bigint, not null (tanpa FK formal)
SiteId, SectionTypeName, ModelName, EquipmentName
PSType                varchar(100), not null
MONo, MODescription   not null
Duration              decimal(13,2), not null
TotalCounterReading   decimal(13,2), not null
ScheduleDateService   date, not null
ScheduleMTRDue        decimal(13,2), not null
WeekPlan              varchar(100), not null
DetailType            varchar(100), not null
IsActive, audit(CreatedByName/ModifiedByName nullable)   not null

WSOutstandingMO:
ID                          PK, bigint, identity
WSSummaryID                 bigint, not null (tanpa FK formal)
SiteId, SectionTypeName, ModelName, EquipmentName
ScheduleDate                date, not null
PSType                      varchar(100), not null
MONo, MODescription         not null
ReservationNo, ReservationQty   int, null
MaterialNo, MaterialDesc    varchar, null
ExecutionConfirmPlanner     bit, null (default 0)   ← konfirmasi sisi Planner
ContinueOrderPlanner        bit, null (default 0)
InfoStockPSCM, ETASupplyPSCM, NoteFullfillPSCM   varchar(100), null   ← input sisi PSCM
DurationPlan                int, null
MoreRemarkPlant, MoreRemarkPSCM   varchar(255), null
CreateDateMo                date, null
CurrentWeek, HistoryDraft   varchar(100), null
StatusMO, UserStatus, GIStatus   varchar(100), null
EstCost                     decimal(18,2), null
GIQty                       int, null
OrderType                   varchar(20), null
```
`WSOutstandingMO` punya pasangan kolom eksplisit **Planner ↔ PSCM** (`ExecutionConfirmPlanner`/`ContinueOrderPlanner` vs `InfoStockPSCM`/`ETASupplyPSCM`/`NoteFullfillPSCM`, plus `MoreRemarkPlant`/`MoreRemarkPSCM`) — pola dialog dua pihak soal ketersediaan part untuk MO backlog, sangat mirip tema di dokumen Backlog Monitoring MKP (assessment/implementation) meski belum dicek apakah ini tabel yang sama persis dipakai fitur itu.

### `WSProjectionPA`, `WSProjectionPAAdditional` (proyeksi Physical Availability)
```
ID                  PK, bigint, identity
WeeklyScheduleID    bigint, not null (tanpa FK formal)
SectionTypeName, ModelName, EquipmentName
MOHH                int, null
PlanScheduled       int, null
BudgetUnscheduled   decimal(18,2), null
PlanDowntime        int, null
OperatingHoursPlan  int, null
BudgetPA, ProjectionPA   decimal(18,2), null
CreatedBy, CreatedByName, CreatedUtcDate   not null/null/not null
ModifiedBy, ModifiedByName, ModifiedUtcDate   not null/null/not null
```
Dua tabel shape identik (`WSProjectionPA` vs `...Additional`) — beda fungsinya belum jelas (kemungkinan proyeksi utama vs entri tambahan/susulan).

### `DPMappingWSSummary` (bridge Weekly Schedule ↔ Digital Plan)
```
ID           PK, bigint, identity
PlanId       FK → DigitalPlanning.PlanId
WSSummaryID  bigint, not null (tanpa FK formal ke WSSummary)
IsActive     bit, not null (default 1)
CreatedBy, CreatedUtcDate   not null
ModifiedBy, ModifiedUtcDate null
```
Konfirmasi eksplisit: **satu `WSSummary` (item backlog/weekly schedule) bisa dipetakan ke satu `DigitalPlanning` (Daily Plan)** — inilah mekanisme "Add Backlog dari SAP" yang disebut di [`digital-planning.md`](../dplan/digital-planning.md) ("Add Backlog dari SAP (Current State)"), meski nama tabel di dokumen itu belum disebut. Table ini kemungkinan yang jadi jembatan MO Backlog → sub-task Plan.

### `DPWeeklyData`, `GanttChartConfiguration`, `HeaderConfiguration`, `WeeklyActivityLog`, `WeeklyMonitoring`
```
DPWeeklyData:
WeeklyId          PK, bigint, identity
SiteId            int, not null
SectionTypeName, ModelName, EquipmentNo   varchar, not null
WeekId            varchar(6), null
LastShutdownDate  datetime, null
LastExecutionType varchar(10), null
LastDuration      decimal(18,1), null
NextPlanDate      datetime, not null
NextPlanDuration  decimal(18,1), not null
MainCriticalJob   varchar(1000), null
PartReadiness     varchar(20), not null
Priority          int, null
CreatedBy, CreatedUtcDate, ModifiedBy, ModifiedUtcDate   varchar(20)/datetime, not null

GanttChartConfiguration:  PlanId, UserId, SettingId (bigint, not null), Value varchar(100) not null — per-user Gantt UI setting per plan
HeaderConfiguration:      PlanId, UserId, Type varchar(50), ReferenceId bigint, IsShow bit, Sequence int — per-user grid column show/order per plan
WeeklyActivityLog:        Action, OldValue/NewValue varchar(max) not null, IsActive bit DEFAULT ((11)) [⚠ lihat catatan], CreatedBy, CreatedByName, CreatedUtcDate
WeeklyMonitoring:         SiteId, SectionTypeName, ModelName, EquipmentName, EquipmentStatus, HourMeter numeric(18,10) [⚠ presisi tidak lazim], IsActive, audit(100)
```
> ⚠️ `WeeklyActivityLog.IsActive` (tipe `bit`) punya default constraint `DEFAULT ((11))` — nilai non-0/1 untuk kolom `bit` akan otomatis dikonversi SQL Server jadi `1`, tapi angka `11` di source-nya mencurigakan (kemungkinan typo/copy-paste dari tabel lain, harusnya `1`). Dampak fungsional kemungkinan tidak terasa (tetap jadi `1`), tapi penanda kualitas script.

---

## Meter/Service Forecast & Standard Cost Master

### `WMSummary`, `WorkHourPerDay` (forecast servis berbasis hour meter)
```
WMSummary (tanpa PK):
EquipmentName          varchar(100), not null
HMDisplay, CurrentHM, HourMeter, Deviation, TotalCounterReading   decimal(13,2)
DateHM                 date, null
WorkHourperDay         decimal(13,2), not null
OilChangeType          int, not null
LastServiceType        varchar(100), null
LastServiceHM          decimal(13,2), not null
LastServiceDate        date, null
NextServiceType        varchar(100), not null
MONo, MODescription    varchar, not null
ForecastMeterService, MetertoRun   decimal(13,2), not null
ForecastDate           date, not null
WeekPlan               varchar(100), not null
IsUpload               bit, not null (default 0)
CreatedBy, CreatedByName, CreatedUtcDate, ModifiedBy, ModifiedByName, ModifiedUtcDate

WorkHourPerDay (tanpa PK):
ModelUnit   varchar(100), not null
Hour        int, not null
IsActive, audit(100)   standard
```
Forecast kapan servis berikutnya jatuh tempo berdasar hour-meter run-rate (`WorkHourperDay` × sisa hari → `ForecastDate`), menghasilkan entri `WeekPlan` — kemungkinan inilah sumber `DPWeeklyData`/`WeeklySchedule`. `OilChangeType`/`WorkHourperDay` nama kolomnya cermin persis nama tabel master `ms_oil_eg_change_type`/`ms_workhour_day` di bawah.

### Master Data Budget/Standar per Site+Model (pola `ms_*`, seragam)
Semua: `id_xxx` PK bigint **identity**, `xxx_name` varchar(30) not null, `is_active` bit not null, `site_id` int not null, ...dimensi..., `created_by` bigint not null, `created_utc_date`/`changed_utc_date` datetime not null.
```
ms_bays                 bays_location varchar(10), description varchar(20)
ms_cost_RM              unit_code varchar(20), category varchar(20), attachment_type varchar(10), material_type varchar(10), mo_type varchar(5), description varchar(15), budget decimal(18,0)
ms_duration              ⚠ is_active bertipe varchar(1), BUKAN bit — beda dari semua ms_* lain. model_code varchar(10), mo_type varchar(5), material_activity_type/material_description varchar(10), object_type/object_type_description varchar(10), risk varchar(10), std_leadtime int
ms_equipment_support     support_tool varchar(15), description varchar(20), capacity int, unit_of_measure varchar(4)
ms_oil_eg_change_type    model varchar(5), workhour_day int, engine_change_type varchar(10)
ms_quantity_breakdown    model_code varchar(10), category/attachment_type/material_type varchar(10), target int, qty_pop int, budget_unit_rfu/budget_unit_breakdown decimal(18,0)
ms_tools                 description varchar(20), capacity int, unit_of_measure varchar(4)
ms_weekly_calendar       id_weekly_calendar PK bigint (BUKAN identity — caller-supplied), start_date date, weekly_range int, id_customer bigint
ms_weekly_calendar_details  id_weekly_calendar_details PK identity, id_weekly_calendar (FK implisit), week_number varchar(50), status varchar(50), start_date/finish_date date, id_customer bigint
ms_workhour_day          model_code varchar(10), workhour_day int, engine_oil_eg_change_type varchar(10)
```
Master data budget/standar leadtime/cost per kombinasi `site_id`+`model_code`+dimensi lain — dipakai untuk hitung target/benchmark di modul Weekly Schedule/Backlog. Belum ada dokumen narasi yang membahas tabel-tabel ini.

---

## SAP / MO Integration (jalur milik `dplan`, terpisah dari `maintenance-order`)

### `SAPMOSynchronization`
```
Id                PK, bigint, identity
TaskId, NotifId   bigint, null
NotifNo           varchar(50), null
Component, SubComponent, DamageGroup, DamageCode, CauseGroup, CauseCode   varchar(128), null
MONo              varchar(32), null
PartNumber        varchar(32), null
PartDescription   varchar(126), null
QTYSAP, QTYGI, QTYUse   float, null
SiteId            int, null
ExecutionStatus   varchar(32), null
ModuleName        varchar(32), null
SAPStatus         smallint, null
SAPText           varchar(1024), null
CreatedBy, CreatedUtcDate, ModifiedUtcDate   null
```
> **Jalur sinkronisasi SAP kedua** yang belum pernah dibahas — [`order-emol-sap-sync.md`](../inspection-order/order-emol-sap-sync.md) mendokumentasikan sync SAP dari sisi `maintenance-order` (eMOL→`PoolingMOItem`→`SAPMOSyncOrder`). Tabel ini adalah outbox/log sync SAP milik **`dplan` sendiri** — kemungkinan untuk MO yang dieksekusi lewat task Digiplan (PM Shutdown/BD Corrective) langsung, bukan lewat alur eMOL. Field taxonomy (`Component`/`SubComponent`/`DamageGroup`/`DamageCode`/`CauseGroup`/`CauseCode`) sama pola dengan `DPPareto` di atas — kemungkinan sumbernya dari situ. Belum dikonfirmasi apakah dua jalur sync SAP ini (`maintenance-order` vs `dplan`) saling independen atau ada overlap/urutan tertentu.

### `CloseMO`
```
CloseMOId    PK, bigint, identity
PlanId, TaskId   bigint, not null (tanpa FK formal)
MONo         varchar(20), not null
PushToSAP    bit, not null
CreatedBy, CreatedUtcDate   not null
```
Penanda MO ditutup dari sisi Digiplan + apakah sudah di-push ke SAP.

### `MOOpen` / `StageMOOpen`, `CheckPartOrder` / `StageCheckPartOrder` (mirror SAP, pola staging)
```
MOOpen/StageMOOpen: TANPA PK constraint sama sekali (heap murni) — kolom SAP mentah
  AUFNR, KTEXT, TXT04, ILART, ILATX, IWERK, AUART, QMNUM, QMART, EQUNR, ATWRT,
  EQART, ANLZU, NODUR, ACDUR, EST_COST, NEXT_PS, SystemStatus, CreateDateMO, ReleaseDate, ...
  (MOOpen tambahan: IsDeleted, CreatedUtcDate, ModifiedUtcDate — StageMOOpen tidak punya ini)

CheckPartOrder/StageCheckPartOrder: PK `ID` (int) — field SAP reservasi/PR/PO/GR/GI mentah
  EQUNR, ATWRT, ARBPL, WERKS, RSNUM, RSPOS, MATNR, BNFPO, MAKTX, LGORT, BDMNG, CHARG,
  BUDAT, AUFNR, KTEXT, GSTRP, AUART, ILART, DSTAT, GR_STATUS, GI_STATUS, GR_QTY, GI_QTY,
  PR_STATUS, BANFN, EBELN, LOEKZ, QMNUM, GR_Number, GI_Number, IsActive, CreatedUtcDate, ModifiedUtcDate
```
Pola **stage→merge** (`Stage*` tanpa PK/audit lengkap → tabel final dengan PK/`IsActive`/audit) — kemungkinan hasil pull batch dari SAP (truncate-and-reload ke Stage, lalu upsert ke tabel final). Field-field ini murni kode SAP (EQUNR/MATNR/AUFNR/dst.), tidak didetailkan lebih jauh di sini karena maknanya spesifik SAP, bukan skema aplikasi.

---

## Master Data Umum (Equipment / Section / Reference)

### `Equipment`, `EquipmentModel`, `SectionEquipment`, `SectionType`, `SectionSubType`, `SectionUser`
```
Equipment:
Id    PK, int, identity
SiteId, EquipmentName, ModelUnit, EquipmentCategory, EquipmentCategoryDesc, EquipmentClass, Manufacturer, SectionTypeCode, LoadDate
IsActive, audit   standard

EquipmentModel:
ModelId   PK, int, identity
ModelCode varchar(6), ModelName varchar(512), SectionTypeCode int, SectionSubTypeCode varchar(100) → FK SectionSubType.SectionSubTypeCode (NOCHECK)
IsActive, audit   standard

SectionEquipment:
SectionEquipmentId  PK, int, identity
EquipmentName, ModelUnit, SectionTypeCode (not null)
CreatedBy default 'system', audit

SectionType:      SectionTypeId PK identity, SectionTypeCode int not null, SectionTypeName, SectionId, IsActive, audit
SectionSubType:   SectionSubTypeId PK identity, SectionSubTypeCode varchar(100) UNIQUE, SectionSubTypeName, Sequence, IsActive, audit
SectionUser:      SectionTypeCode int not null, SectionId varchar(20) not null, CreatedUtcDate — TANPA PK, TANPA kolom user apapun (nama tabel menyiratkan relasi ke User, tapi isinya cuma SectionTypeCode+SectionId)
```
> `SectionUser` namanya menyiratkan mapping user↔section, tapi **tidak punya kolom user sama sekali** — cuma `SectionTypeCode`+`SectionId`+`CreatedUtcDate`, tanpa PK. Kemungkinan nama menyesatkan (isinya sebenarnya master Section per type, bukan relasi ke User), atau tabel ini belum lengkap/sisa migrasi. Perlu diklarifikasi.

### `MaintenanceCategory` (local copy)
```
MaintenanceCategoryId    PK, bigint, identity
MaintenanceCategoryCode  varchar(10), not null
MaintenanceCategoryName  varchar(100), not null
MaintenanceCategoryType  varchar(100), null
IsActive, audit(100, nullable CreatedBy/ModifiedBy)
```
> **Konfirmasi langsung** untuk catatan di [`digital-planning.md`](../dplan/digital-planning.md) baris `MaintenanceCategoryName` ("di-join dari `DPlanDB.MaintenanceCategory.MaintenanceCategoryName`") — tabel ini memang ada persis di `DPlanDB`, terpisah dari `maintenance-strategy.MaintenanceCategory` ([`maintenance-strategy-schema.md`](maintenance-strategy-schema.md)) — direplikasi per-service seperti `Configuration`/`Feature`/`AuditLog` di service lain.

### `Site` / `StageSite`, `ImageMaster`, `Setting`
```
Site:       SiteId PK int, SiteName, SiteShortName, Timezone int, StartMorningShift/StartNightShift varchar(16), UpdatedUtcDate not null
            ⚠ default constraint bernama DF_Site_IsActive tapi target-nya kolom UpdatedUtcDate, default ((0)) — nama constraint menyebut "IsActive" (kolom yang bahkan tidak ada di tabel Site), dan default 0 untuk kolom datetime akan resolve ke 1900-01-01. Kemungkinan sisa copy-paste dari script tabel lain.
StageSite:  sama minus UpdatedUtcDate, plus IsActive bit not null (default 1)
ImageMaster: Id PK identity, Category/Type varchar(100) not null, Url varchar(500) not null, CreatedUtcDate — lookup icon/image generik (kemungkinan sumber DelayType.IconURL)
Setting:    SettingId PK bigint (BUKAN identity), SettingCategory/SettingCode/SettingName varchar(100) not null, IsActive, audit(nullable CreatedBy/ModifiedBy) — dipakai GanttChartConfiguration.SettingId
```

### Master Data Reference/KPI (id caller-supplied, bukan identity)
```
ms_attachment_type      id_attachment_type PK bigint, type_name varchar(50), description nvarchar(256)
ms_customer              id_customer PK bigint, site_id, site_shortname varchar(3), customer_name varchar(10)
ms_equipment_category    id_equipment_category PK bigint, category_name varchar(10), description nvarchar(256)
ms_equipment_kpi         id_equipment_kpi PK bigint, site_id, model_name, id_category/id_attachment_type/id_material_type/id_kpi bigint, target int, unit, description varchar(500)
ms_equipment_population  id_equipment_population PK bigint, site_id, model_name, unit_code, status, equip_engineering/application/manufacturer/axle_driveline_type/attachment_type varchar(50), category_1/2/3 varchar(50)
ms_kpi_item              id_kpi_item PK bigint, kpi_item_name varchar(50), unit, description varchar(500)
ms_material_type         id_material_type PK bigint, type_name varchar(50), description nvarchar(256)
```
Semua `is_active`(bit)/`created_by`/`created_utc_date`/`changed_utc_date` standar. Tidak satupun `IDENTITY` (beda dari mayoritas tabel lain di DB ini) — Id kemungkinan disuplai dari sumber eksternal (master data yang di-sync dari sistem lain), bukan dibuat lewat aplikasi ini.

---

## User / Employee

### `User` / `StageUser`
```
UserId          PK, bigint (BUKAN identity)
EmployeeId      bigint, not null
FullName, Upn (nvarchar(128)), PositionId/PositionName, LevelId/LevelName
SiteId/SiteName, SupervisorId/SupervisorName, DepartmentId/DepartmentName, SectionId/SectionName
Mobile, ShiftId, PasswordExpireUtcDate
GenderCode/GenderName, BirthDate, Age, StartWorkingDate, AgeWorkingDate, LastPositionName, AgeLastPosition
Grade           varchar(6) (User) / varchar(64) (StageUser)
IsActive, audit   (hanya di User; StageUser tanpa IsActive/audit — pola stage→merge sama seperti MOOpen)
```
> **Temuan penting, lintas-DB**: [`user-management-schema.md`](user-management-schema.md) mencatat bahwa DB `usermanagement` **tidak punya** tabel `UserEmploymentProfile` yang menyimpan `SectionId` (kunci relasi User→OrganizationUnit di [`user-asset-relation.md`](user-asset-relation.md)), dan menandai ini sebagai gap prioritas tinggi. Tabel `dplan.User`/`StageUser` di sini **punya persis kolom yang dicari** — `SectionId`/`SectionName`, `DepartmentId`/`DepartmentName`, `SiteId`/`SiteName`, dst., shape-nya sangat mirip employee profile. Kemungkinan ini adalah **cache/replika lokal** dari data employment profile (disinkronkan via `StageUser`→`User`, sama pola `StageDws`→`Dws`/`StageSite`→`Site`/`StageMOOpen`→`MOOpen`), bukan source-of-truth-nya sendiri — tapi ini clue kuat untuk menjawab open question di `user-management-schema.md` tentang di mana data employment profile sebenarnya hidup. **Perlu dikonfirmasi ke tim codebase**: apakah `dplan.User` disinkronkan dari `cst-shared-sqldb-user` (alias `user` di `user-asset-relation.md`), dan kalau ya, `usermanagement` (auth-only) vs `user` (employment profile) benar-benar dua DB terpisah seperti dugaan di `user-management-schema.md`.

### `Dws` / `StageDws` (Daily Work Schedule — roster shift)
```
Dws:       Id PK identity int, DateId date not null, NIK bigint not null, DwsCode varchar(64) not null, ShiftId int null, UpdateDate datetime null, IsActive, audit
StageDws:  DwsDate date, NIK bigint, DwsCode varchar(64), ShiftId int — tanpa PK/IsActive/audit (staging)
```
Roster kerja harian per NIK (nomor induk karyawan) — kemungkinan sumber `ShiftId` yang dipakai `User.ShiftId`/`usermanagement.EmployeeShiftLog.ShiftId` (lihat [`user-management-schema.md`](user-management-schema.md), yang mencatat `ShiftId` di sana tanpa FK ke tabel `Shift` manapun — `Dws`/`StageDws` di sini kandidat kuat sumber datanya, meski bukan tabel master `Shift` itu sendiri, lebih ke tabel transaksi assignment).

### `UserMonitoring`
```
Id             PK, uniqueidentifier (default newid())
MenuName, UrlPath, TransactionId
NIK            bigint, not null
FullName, SiteId/SiteName, LevelId/LevelName, DepartmentId/DepartmentName, SectionId/SectionName
AccessDate     datetime, not null (default getutcdate())
CreatedUtcDate, ModifiedUtcDate   not null
```
Log akses per menu/halaman per user — snapshot profile (site/level/dept/section) di-denormalize per baris log (bukan FK ke `User`), pola audit trail generik.

---

## Vendor / Stock

```
VendorStock:
VendorStockID   PK, int
VendorCode      varchar(20), UNIQUE
VendorName      varchar(20), EmailDomain varchar(50)
IsActive, CreatedBy/ModifiedBy default 'system', audit

StockInventoryVendor:
StockInventoryVendorID  PK, int, identity
VendorCode              FK → VendorStock.VendorCode
VendorName, MaterialNumber, MaterialDescription, AvailableStock int, BaseUnitofMeasure, MaterialLocation
CreatedBy, CreatedUtcDate
```
Stok inventory per vendor per material — `VendorStock.EmailDomain` kemungkinan dipakai untuk validasi/routing notifikasi ke vendor portal (belum dikonfirmasi).

---

## Reporting & Historical

### `HistoricalPlannExecution`
Tabel flatten sangat lebar (43 kolom) — gabungan header Plan + Task + hasil eksekusi (`ActualStart`/`ActualFinish`/`TaskStatusDescription`/`Evidence`/`Remark`/dst.) dalam satu row per task. **Tidak ada FK constraint sama sekali** — murni tabel arsip/laporan, kemungkinan diisi lewat ETL/stored proc periodik dari `DigitalPlanning`+`DPTask`+data eksekusi, bukan ditulis langsung oleh aplikasi transaksional.

### `MonthlyReport`, `UnitStatus`
```
MonthlyReport: MonthlyReportId PK identity, EquipmentName, MonthId, SiteId varchar(10), TotalInprHour/TotalDownHour/PAMonthToDay decimal(18,2), CreatedUtcDate
UnitStatus:    Id PK identity int, TrDate, SiteId varchar(10), EquipmentName, StatusUnit, SourceEquipment, IsFis/IsFisHm bit, LoadDate, CreatedUtcDate
```
`IsFis`/`IsFisHm` — kemungkinan penanda sumber data dari sistem "FIS" eksternal (fleet/field information system, belum dikonfirmasi kepanjangannya) — dipakai juga sebagai flag kualitas data hour-meter.

---

## System & Ops Log

```
DeadLetterLog:     pola sama dengan service lain (TopicName, SubscriptionName, TenantCode, MessageId, MessagePayload, ErrorMessage, DeliveryCount, TraceId/ParentSpanId, FailedAt, IsResolved)
TopicConsumeLog:   Id PK identity, TopicName, Subject, MessageId, MessagePayload varchar(max) not null, TenantCode, IsProcessed bit (default 0), ProcessedAt, RetryCount (default 0), ErrorMessage/StackTrace, CreatedAt
JobLog:            Id PK identity int, JobName, Description, FunctionName, Parameter varchar(max), TotalData int, IsSuccess bit, ErrorMessage, CreatedUtcDate — log job/ETL (kandidat penjadwal sync MOOpen/CheckPartOrder/Dws/dst.)
OfflineLog:        LogId PK identity, APIName/SPName, DeviceId, IsSuccess bit (default 1), ErrorMessage, CreatedBy, CreatedUtcDate — log API call dari mobile app saat mode offline-sync
PlanId_Temp:       PlanId PK identity bigint, ModifiedUtcDate — generator/reservasi batch PlanId sebelum bulk insert
TaskId_Temp:       TaskId bigint not null (BUKAN identity, beda dari PlanId_Temp), ModifiedUtcDate — sama fungsi, tapi TaskId harus disuplai manual
```
`TopicConsumeLog` menandakan `dplan` juga jadi **consumer** Service Bus (bukan cuma publisher) — arah pesan masuk yang mana belum dijelaskan di narasi manapun (`digital-planning.md` hanya menyebut `dplan` publish event ke `maintenance-execution` saat `SUBMIT`).

---

## Observasi Belum Dibahas
- **`dplan.User`/`StageUser` mirip employment-profile yang "hilang" di `usermanagement`** (lihat catatan di atas) — prioritas tinggi untuk diklarifikasi, langsung relevan ke gap yang sudah dicatat di [`user-management-schema.md`](user-management-schema.md).
- **Dua jalur sync SAP independen** (`maintenance-order.SAPMOSyncOrder` vs `dplan.SAPMOSynchronization`) — belum dikonfirmasi apakah overlap/berurutan atau benar-benar independen per modul (eMOL vs MO Backlog Digiplan).
- **`WSOutstandingMO`/`WSSummary`/`WeeklySchedule`** kemungkinan backing table fitur Backlog Monitoring/MKP ([`backlog-monitoring-mkp-assessment.md`](../../report/backlog-monitoring/backlog-monitoring-mkp-assessment.md) dkk.) berdasar kemiripan tema (Planner↔PSCM, ETA supply, budget PA) — **belum dikonfirmasi** nama tabel yang dipakai fitur itu sama persis dengan ini.
- **`DPPredecessor.ToTask` tanpa FK** (asimetris dengan `FromTask`) — perlu klarifikasi apakah disengaja.
- **`SectionUser` tanpa kolom user** — nama menyesatkan, isi sebenarnya cuma `SectionTypeCode`+`SectionId`.
- **Banyak relasi "soft" tanpa FK formal** — pola umum di DB ini: `DPDelay` (semua kolom relasinya), `CloseMO`, `GanttChartConfiguration`/`HeaderConfiguration` (`PlanId`), `DPMappingWSSummary`/`WSOutstandingMO` (`WSSummaryID`), `WSProjectionPA(Additional)` (`WeeklyScheduleID`), `SAPMOSynchronization` (`TaskId`), `ActivityBreakdown` (`PlanId`) — hanya ~24 FK constraint eksplisit untuk ~80 tabel. Integritas relasi banyak bergantung pada aplikasi, bukan DB.
- **`ms_duration.is_active` bertipe `varchar(1)`**, beda dari seluruh keluarga `ms_*` lain yang pakai `bit` — inkonsistensi tipe, berpotensi bug kalau ada query yang nganggap semua `ms_*.is_active` bertipe sama.
- **`WeeklyActivityLog.IsActive` default `((11))`** dan **`Site` punya default constraint bernama `DF_Site_IsActive` yang justru target `UpdatedUtcDate` ke `0`** — dua tanda kualitas script/migrasi yang perlu diwaspadai saat baca schema ini lebih jauh.
- **`ActivityBreakdown.ActivityCode` = `DelayDescription.ActivityCode`** — kemungkinan taxonomy fase breakdown bersama, relasinya lewat kode yang sama tanpa FK; belum dikonfirmasi ke tim codebase.

---

## Referensi
- [`digital-planning.md`](../dplan/digital-planning.md) — narasi lifecycle, hierarki task, dynamic column, predecessor, mekanisme Template→Plan (document-derived, sekarang terkonfirmasi cocok dengan DDL real untuk hierarki inti)
- [`man-power-man-hours-excel-enhancement.md`](../dplan/man-power-man-hours-excel-enhancement.md) — enhancement kolom Man Power/Man Hours, relevan ke `DPColumn`/`DPValue`/`TemplateColumn`
- [`order-emol-sap-sync.md`](../inspection-order/order-emol-sap-sync.md) — jalur sync SAP sisi `maintenance-order`, untuk dibandingkan dengan `SAPMOSynchronization`/`CloseMO` di sini
- [`user-management-schema.md`](user-management-schema.md) — gap `UserEmploymentProfile` yang kemungkinan terjawab sebagian oleh `dplan.User`/`StageUser`
- [`services-asset-schema.md`](services-asset-schema.md), [`maintenance-order-schema.md`](maintenance-order-schema.md), [`maintenance-execution-schema.md`](maintenance-execution-schema.md), [`maintenance-strategy-schema.md`](maintenance-strategy-schema.md) — skema service lain untuk perbandingan pola (`Configuration`/`AuditLog`/`MaintenanceCategory`/taxonomy Component-Damage-Cause direplikasi per-service dengan variasi shape)
- [`backlog-monitoring-mkp-assessment.md`](../../report/backlog-monitoring/backlog-monitoring-mkp-assessment.md) — kemungkinan konsumen modul Weekly Schedule/`WSOutstandingMO`, belum dikonfirmasi
