# Homepage Revamp — Current State

Dokumen ini mendeskripsikan kondisi halaman **Homepage** di Mobile Digiman+ pasca revamp (Release 4.0.0).

*Last updated: 2026-07-03*
*Referensi Jira: [IAMS30-3596](https://bukittechnology.atlassian.net/browse/IAMS30-3596)*

---

## Sections di Homepage

| Section | Permission | Redirect ke |
|---------|------------|-------------|
| Needs Attention | — (semua user) | Tidak redirect |
| Tasks – Inspection | `IAMS_Mobile_Inspection_View` | Inspection Page |
| Tasks – PM Shutdown | `IAMS_Mobile_Shutdown_View` | PM Shutdown Page |
| Tasks – BD Corrective | `IAMS_Mobile_Shutdown_View` | BD Corrective Page |
| Tasks – Order Parts | `IAMS_Mobile_Order_Page` | Order Page (no count) |

---

## Needs Attention (Agregat)

| Metric | Formula |
|--------|---------|
| Past Due | Past Due Inspection + Past Due PM Shutdown + Past Due BD Corrective |
| Due Today | Due Today Inspection + Due Today PM Shutdown + Due Today BD Corrective |

---

## Kriteria Count per Section

### Inspection
- **Source:** `Services.MaintenanceExec`
- **Kolom tanggal:** `ScheduleStartDate`
- **"Open" di UI** = status `Open` di database

| Metric | Kriteria |
|--------|---------|
| Past Due | `Status = 'Open'` AND `ScheduleStartDate < Today` |
| Due Today | `Status = 'Open'` AND `ScheduleStartDate = Today` |
| In Progress | `Status IN ('In Progress', 'Pending')` |

### PM Shutdown
- **Source:** `Services.Plan`
- **Kolom tanggal:** `ProjectStart`
- **"Open" di UI** = status `SUBMIT` di database

| Metric | Kriteria |
|--------|---------|
| Past Due | `Status = 'SUBMIT'` AND `ProjectStart < Today` AND `ExecutionType IN ('Schedule', 'Other')` AND `UnitStatus` contains `UNIT_INPROGRESS` |
| Due Today | `Status = 'SUBMIT'` AND `ProjectStart = Today` AND `ExecutionType IN ('Schedule', 'Other')` AND `UnitStatus` contains `UNIT_INPROGRESS` |
| In Progress | `Status = 'INPROGRESS'` AND `ExecutionType IN ('Schedule', 'Other')` AND `NotifNoStatus` NOT contains `NOTIF_STATUS_EXCLUDED_FROM_INPROGRESS` AND `UnitStatus` contains `UNIT_INPROGRESS` |

### BD Corrective
- **Source:** `Services.Plan`
- **Kolom tanggal:** `ProjectStart`
- **"Open" di UI** = status `SUBMIT` di database

| Metric | Kriteria |
|--------|---------|
| Past Due | `Status = 'SUBMIT'` AND `ProjectStart < Today` AND `ExecutionType IN ('Unschedule')` AND `UnitStatus` contains `UNIT_INPROGRESS` |
| Due Today | `Status = 'SUBMIT'` AND `ProjectStart = Today` AND `ExecutionType IN ('Unschedule')` AND `UnitStatus` contains `UNIT_INPROGRESS` |
| In Progress | `Status = 'INPROGRESS'` AND `ExecutionType IN ('Unschedule')` AND `NotifNoStatus` NOT contains `NOTIF_STATUS_EXCLUDED_FROM_INPROGRESS` AND `UnitStatus` contains `UNIT_INPROGRESS` |

---

## Settings yang Digunakan (DPlanDB)

Filter `UnitStatus` dan `NotifNoStatus` dibaca secara dinamis dari table `Setting` di **DPlanDB**:

| SettingCategory | SettingCode | Nilai saat ini |
|-----------------|-------------|----------------|
| `EXECUTION_UNITSTATUS` | `UNIT_INPROGRESS` | `["IDWP", "INPR"]` |
| `EXECUTION_NOTIFSTATUS` | `NOTIF_STATUS_EXCLUDED_FROM_INPROGRESS` | `["NOCO"]` |

---

## Data Scope (Permission-based)

Berlaku untuk semua section (Inspection, PM Shutdown, BD Corrective):

| Permission | Perilaku |
|------------|----------|
| Basic — Section ID ter-mapping ke Section Type | Hanya tampilkan task dari section yang sesuai |
| Basic — Section ID tidak ter-mapping | Tampilkan semua section |
| All Site | Tampilkan task dari semua site |

Permission code:

| Fitur | Basic | All Site |
|-------|-------|----------|
| Inspection | `IAMS_Mobile_Inspection_View` | `IAMS_Mobile_Inspection_View_All_Site` |
| PM Shutdown & BD Corrective | `IAMS_Mobile_Shutdown_View` | `IAMS_Mobile_Shutdown_View_All_Site` |

All Site permission memiliki Basic permission sebagai parent-nya.

---

## Catatan Penting

- **Count di Homepage dihitung dari server** (real-time via API), tidak bergantung data lokal di device.
- **Count di Detail Page** bergantung dari data lokal offline di device → bisa berbeda dengan count di Homepage.
- Past Due dan Due Today hanya menghitung status **Open (SUBMIT)**, bukan INPROGRESS.
- Setting data seeder berada di `Database.Plan`.

---

## API

- **Endpoint:** `GET /maintenance-execution/api/homepage/counts?ver=v1`
- **Response:** count per metric untuk inspection, pmShutdown, bdCorrective
