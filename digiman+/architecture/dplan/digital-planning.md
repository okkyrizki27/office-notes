# dplan — DigitalPlanning Table

*Last updated: 2026-07-10*

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

---

## Schema Tabel `DPTask`

Detail task per plan — hierarkis (task bisa punya sub-task).

```
TaskId                    ← PK
PlanId                    ← FK ke DigitalPlanning.PlanId
ParentId                  ← FK ke DPTask.TaskId (self-reference) — null jika task level teratas
Description
Sequence                  ← urutan tampil task dalam plan
ImportParent
SourceTask
SourceType
JobPercentage
TemplateJobPercentage
CreatedBy, CreatedUtcDate
ModifiedBy, ModifiedUtcDate
```

## Schema Tabel `DPPredecessor`

**Ditambahkan 10 Jul 2026** — model relasi dependency antar task, sudah ada saat ini (bukan konsep baru). Ini yang jadi dasar konsep **Sequence, Serial, Paralel** di Digiplan.

```
PredecessorId             ← PK, bigint
PlanId                    ← FK ke DigitalPlanning.PlanId
FromTask                  ← FK ke DPTask.TaskId
ToTask                    ← FK ke DPTask.TaskId
Type                      ← varchar(50) — tipe dependency (kemungkinan pola standar seperti FS/SS/FF/SF)
Lag                       ← int — jeda waktu antar task (lead/lag)
CreatedBy, CreatedUtcDate
ModifiedBy, ModifiedUtcDate
Active                    ← bit
```

> **Implikasi penting untuk rollup Man Power/Man Hours di level parent** (lihat [man-power-man-hours-excel-enhancement.md](man-power-man-hours-excel-enhancement.md) 3.3/4.0.1): konsep serial/paralel antar child task **sudah dimodelkan** lewat tabel ini (via `Type` + graph `FromTask`→`ToTask`), bukan sesuatu yang perlu dibangun dari nol. Assessment yang tersisa jadi lebih ke **finalisasi formula perhitungan** (bagaimana `Type`/`Lag` diterjemahkan ke rumus rollup Man Power/Man Hours), bukan riset ulang bagaimana menangkap struktur predecessor-nya — data modelnya sudah matang.

## Schema Tabel `DPColumn`

Definisi **kolom dinamis** — kolom yang muncul di grid Daily Plan (Duration, Start, Finish, MO Number, Job Risk, Part Readiness, Mechanic PIC, Mechanic Name, dst) tidak hardcode di skema tabel, melainkan didefinisikan di sini **per Plan**.

> ⚠️ **Koreksi (10 Jul 2026)**: kolom "Predecessor" yang tampil di grid **bukan** murni dynamic column EAV seperti kolom lain — nilainya didukung oleh tabel relasional tersendiri, `DPPredecessor` (lihat di bawah). Kolom grid ini kemungkinan hanya representasi tampilan dari data `DPPredecessor`, bukan disimpan sebagai `DPValue` biasa.

```
ColumnId                  ← PK
PlanId                    ← FK ke DigitalPlanning.PlanId
Name                      ← nama kolom (mis. "Duration", "Man Power", "Man Hours")
DataType
MaxCharacter
IsMandatory
IsShow                    ← toggle tampil/sembunyi di grid
Sequence                  ← urutan tampil kolom
AllowDelete
IsCustomColumn
CreatedBy, CreatedUtcDate
ModifiedBy, ModifiedUtcDate
```

**Penting:** `DPColumn` untuk sebuah plan **di-snapshot saat plan dibuat**, disalin dari definisi kolom Template yang dipilih user (lihat "Mekanisme Pembuatan Daily Plan" di bawah). Kolom-kolom ini dikelola lewat halaman **Config → Custom Column** di Template (tombol "Add Column"), bukan lewat perubahan skema database.

## Schema Tabel `DPValue`

Penyimpanan **value** dari kolom dinamis — pola EAV (Entity-Attribute-Value): satu baris = satu nilai untuk satu task pada satu kolom.

```
ValueId                   ← PK
TaskId                    ← FK ke DPTask.TaskId
ColumnId                  ← FK ke DPColumn.ColumnId
Value                     ← nvarchar(1000), semua tipe data disimpan sebagai string
CreatedBy, CreatedUtcDate
ModifiedBy, ModifiedUtcDate
```

## Relasi Antar Tabel

```
DigitalPlanning (header, 1 row per plan)
  └─ TemplateId → menentukan set kolom awal saat plan dibuat

DPTask (detail task per plan, hierarkis via ParentId)
  ├─ PlanId (FK)
  ├─ ParentId → hierarki task (parent/child)
  └─ Sequence

DPColumn (definisi kolom dinamis, per Plan — snapshot dari Template)
  ├─ PlanId (FK)
  └─ Name, DataType, MaxCharacter, IsMandatory, IsShow, Sequence, AllowDelete, IsCustomColumn

DPValue (EAV — isi value dinamis per task per kolom)
  ├─ TaskId (FK)
  ├─ ColumnId (FK)
  └─ Value (nvarchar(1000))
```

## Mekanisme Pembuatan Daily Plan

1. User buka halaman Daily Plan
2. Create Planning
3. Pilih Template → set kolom (`DPColumn`) untuk plan ini di-snapshot dari Template terpilih
4. Isi informasi asset dan plan eksekusi (data header `DigitalPlanning`)
5. Next
6. Data Planning terbentuk — hierarki `DPTask` + kolom sesuai Template
7. User melengkapi data — **input langsung di grid**, atau **lewat template Excel** (download template tersedia)
8. Excel template upload saat ini **hardcode ke kolom fixed saja** — belum mengakomodasi kolom dinamis dari `DPColumn`/`DPValue`

> Karena `DPColumn` di-snapshot saat plan dibuat (bukan dibaca live dari Template), plan yang sudah terlanjur dibuat sebelum Template diupdate (misal ditambah kolom baru) **tidak otomatis ikut berubah**.

## Business Logic Khusus per Kolom (Precedent)

Meski kolom di `DPColumn` bersifat dinamis/generic secara skema, beberapa kolom sudah punya business logic khusus yang tidak generic:

- **Duration** — nilai di level *parent* task dihitung sebagai **MAX** (nilai Duration terbesar) dari semua *children*-nya — bukan sum/total, dan bukan input independen. Kemungkinan logic ini merefleksikan bahwa child task berjalan paralel, jadi durasi parent mengikuti child yang paling lama selesai. Ini precedent bahwa "kolom dinamis" di sistem ini boleh punya logic spesial per-nama-kolom, bukan murni data generic.
  - Di level task (leaf), Duration **otomatis terisi default `1`** saat user create planning dan menambahkan task baru — bukan kosong/null di awal.
  - **Satuan Duration adalah jam (Hours)**.
  - Nilai Duration **dibulatkan ke 1 angka desimal** (konsisten dengan tipe kolom `decimal(18,1)`).
  - **Precedence saat task berasal dari MO Backlog** *(dikonfirmasi 10 Jul 2026)*: kalau task dibuat dari MO Backlog yang membawa nilai Duration plan sendiri (lihat [../inspection-order/area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md) 2.5), **nilai dari MO Backlog yang menang** — bukan default `1`. Default `1` hanya berlaku untuk task yang dibuat manual (tanpa MO Backlog).
  - **Auto-fill dari MO Backlog tetap editable** — nilai Duration (juga Component/Sub Component/Area/Man Power) yang auto-fill dari MO Backlog **bukan read-only/lock**; user (planner) tetap bisa mengubahnya sesuai analisa & kondisi terkini saat membuat Plan.

*(Lihat [man-power-man-hours-excel-enhancement.md](man-power-man-hours-excel-enhancement.md) untuk rencana penambahan kolom Man Power & Man Hours yang mengikuti pola serupa.)*

## Add Backlog dari SAP (Current State)

- Digiplan **saat ini sudah bisa** menambahkan backlog dari SAP ke dalam Daily Plan (sebagai sub-task).
- **Scope saat ini terbatas**: khusus untuk **order type tertentu** dengan **PM Activity Backlog** — belum mencakup semua jenis order/backlog dari SAP.
- **Filter ini bersifat konfigurasi per client** *(dikonfirmasi 10 Jul 2026)* — Order Type/PM Activity Type yang jadi kriteria bisa berbeda antar client (menyesuaikan konvensi SAP masing-masing), bukan nilai yang di-hardcode global. Lihat [../inspection-order/order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) Bagian 9.1.
- Backlog ini disebut **MO Backlog** — hasil MO yang sudah dibuat & diproses di SAP (lewat flow Order/eMOL → SAP), lalu masuk kembali ke Digiman+. Setelah ditambahkan ke sub-task Plan, eksekusinya terjadi di PM Shutdown atau BD Corrective (atau, di luar Digiplan, bisa juga langsung dieksekusi saat Inspection). Detail lengkap flow ini (termasuk kirim TECO ke SAP setelah eksekusi) ada di [../inspection-order/order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) Bagian 9.

## Prinsip Arsitektur

- **Hindari integrasi langsung dengan Order** — hasil meeting business (10 Jul 2026): **saat ini Digiplan belum punya integrasi apapun dengan Order**, dan prinsipnya adalah **sebisa mungkin integrasi ini tidak perlu dibuat** — bukan soal decoupling dari sesuatu yang sudah ada.
  - **Alasan konkretnya**: kebutuhan agar Component, Sub Component, Area, Duration, Man Power (nilai **plan**, bukan actual) tersedia otomatis di Digiplan **tidak perlu** dipenuhi lewat integrasi baru Digiplan↔Order. Cukup dengan memastikan data-data itu **ikut dikirim ke SAP saat create Order** (perluasan pipeline Order/eMOL → SAP yang sudah ada, lihat [area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md) 2.5 dan [order-emol-sap-sync.md](../inspection-order/order-emol-sap-sync.md) Bagian 5–6) — data itu akan otomatis ikut kembali saat MO tersebut ditarik lagi ke Digiman+ sebagai **MO Backlog** (lihat "Add Backlog dari SAP" di atas). Saat user pilih MO Backlog di Digiplan, field-field itu langsung terisi dari data MO Backlog, tanpa Digiplan perlu tahu atau bicara langsung ke Order/SAP sama sekali.
  - Kalau Digiplan sampai dibuat terintegrasi langsung ke Order untuk tujuan yang sama, itu jadi jalur ketiga yang redundan (selain jalur create-Order→SAP dan jalur SAP→MO-Backlog yang sudah ada) — menambah kompleksitas tanpa manfaat tambahan.
  - *(Lihat juga [area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md) untuk konteks enhancement Component/Sub-Component/Area yang berjalan bersamaan dengan keputusan ini.)*
