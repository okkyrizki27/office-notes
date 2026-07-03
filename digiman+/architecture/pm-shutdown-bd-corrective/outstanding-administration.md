# Outstanding Administration — Current State

Fitur **Outstanding Administration** menampilkan daftar task maintenance yang masih berjalan (status `INPROGRESS`) di aplikasi Mobile Digiman+. Data diambil dari database **DPlanDB** via service `dplan`.

*Last updated: 2026-07-03*

---

## Dua Kategori

### 1. PM Shutdown

| Field | Nilai |
|-------|-------|
| `Status` | `= 'INPROGRESS'` |
| `ExecutionType` | `IN ('Schedule', 'Other')` |
| `IsActive` | `= 1` |
| `NotifNoStatus` | `= 'NOCO'` |

### 2. BD Corrective

| Field | Nilai |
|-------|-------|
| `Status` | `= 'INPROGRESS'` |
| `ExecutionType` | `IN ('Unschedule')` |
| `IsActive` | `= 1` |
| `NotifNoStatus` | `= 'NOCO'` |

---

## Nilai Filter dari Settings (DPlanDB)

Filter `NotifNoStatus` dan `UnitStatus` dibaca secara dinamis dari table `Setting` di **DPlanDB**:

| SettingCategory | SettingCode | Nilai saat ini | Status implementasi |
|-----------------|-------------|----------------|---------------------|
| `EXECUTION_NOTIFSTATUS` | `NOTIF_STATUS_EXCLUDED_FROM_INPROGRESS` | `["NOCO"]` | Implemented |
| `EXECUTION_UNITSTATUS` | `UNIT_INPROGRESS` | `["IDWP", "INPR"]` | **Deferred — belum diimplementasi** |

> Filter `UnitStatus` di-defer, artinya saat ini data tidak difilter berdasarkan `UnitStatus` meskipun nilai sudah terdefinisi di Settings.

---

## Data Scope (Permission-based)

Scope data ditentukan berdasarkan permission user:

| Permission | Perilaku |
|------------|----------|
| Basic (bukan All Site) — Section ID ter-mapping ke Section Type | Hanya tampilkan task dari section yang sesuai |
| Basic (bukan All Site) — Section ID tidak ter-mapping | Tampilkan semua section |
| All Site | Tampilkan task dari semua site |

Mapping dilakukan melalui `OrganizationUnit` sebagai jembatan antara `User.SectionId` dan `Asset.SectionTypeCode`. Lihat [User → Asset Section Hierarchy](../../architecture/database/user-asset-relation.md).

---

## Fitur Pendukung

- **Detail Workcard:** sama seperti detail workcard PM Shutdown / BD Corrective (tidak ada tampilan khusus)
- **Search by:** Model name, Equipment Number, Plan Name

---

## API

Outstanding Administration **tidak memiliki API tersendiri** — menggunakan API yang sama dengan halaman PM Shutdown (untuk kategori PM Shutdown) dan API yang sama dengan halaman BD Corrective (untuk kategori BD Corrective). Pembedaan dilakukan di sisi client berdasarkan filter `NotifNoStatus`.

---

## Referensi Jira

- [IAMS30-3597](https://bukittechnology.atlassian.net/browse/IAMS30-3597) — Story implementasi fitur ini (Status: Done, Sprint: Release 4.0.0)
