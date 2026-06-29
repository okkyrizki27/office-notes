# Inspection Compliance Report

**Page:** INSPECTION COMPLIANCE
**Views:**
- `am.vw_report_iams_get_molist` — [SQL](vw_report_iams_get_molist.sql)
- `am.vw_report_iams_get_assignment` — [SQL](vw_report_iams_get_assignment.sql)

**Config Dependencies:**
- [config_mapping_wo_status.csv](config_mapping_wo_status.csv)
- [config_wicope_manual.csv](config_wicope_manual.csv) *(tidak dipakai di kedua view ini — kemungkinan di layer PBI)*

---

## Business Question

Apakah setiap MO Inspection sudah dikerjakan oleh inspector yang ditugaskan, kapan dikerjakan, dan apa status aktualnya? Report ini menjawab kepatuhan eksekusi inspeksi per unit, per site, dan per inspector.

**Pembagian peran kedua view:**
| View | Fokus | Granularitas |
|------|-------|-------------|
| `get_molist` | Dimensi MO — equipment, section, status display, DateCompletion | Per WO per taskpersonalized |
| `get_assignment` | Dimensi Personel — inspector, SPV, waktu mulai/submit (local time) | Per WO per taskpersonalized |

Consumer (Power BI / view downstream) meng-join keduanya via `MOId` = `Id`.

---

## Data Sources

| Source | Table/Path | `get_molist` | `get_assignment` | Catatan |
|--------|------------|:---:|:---:|---------|
| `mkp_maintenance_execution` | `workorder` | ✅ | ✅ | `get_molist` ambil lebih banyak kolom |
| `mkp_maintenance_execution` | `task` | ✅ | ✅ | Filter sama: `type='FlexiInspection'` |
| `mkp_maintenance_execution` | `taskpersonalized` | ✅ | ✅ | Filter sama: `isactive=1` |
| `mkp_maintenance_execution` | `taskpersonalizedlog` | ❌ | ✅ | Hanya di `get_assignment` — untuk `SubmittedUtcDate` |
| `mkp_services_asset` | `asset`, `assetmodel` | ✅ | ❌ | Lookup unit & model |
| `shared_tenant` | `sectiontype` | ✅ | ❌ | Lookup nama area |
| `shared_tenant` | `site` | ✅ *(dead)* | ✅ *(aktif)* | `get_molist` ambil tapi tidak pakai; `get_assignment` pakai untuk konversi timezone |
| `shared_user` | `user`, `useremploymentprofile` | ✅ (1×) | ✅ (2×) | `get_assignment` join dua kali: inspector `d` + SPV `g` |
| `mapping` | `config_mapping_wo_status.csv` | ✅ | ✅ | Mesin status resolusi — shared |

---

## Transformation Logic

### Status Resolusi — Shared Logic (kedua view)

Kedua view menggunakan mekanisme yang identik:

1. **LEFT JOIN** `workorder` ke `mapping_wo_status` via `wo.status = mws.wo_status`
2. Hitung `correct_status`:
   - `wo.status = 'Cancelled'` → `correct_status = 1` (override semua)
   - `check_taskpersonalized = 0` → `correct_status = 1` (status WO saja sudah cukup, contoh: INE=Completed)
   - `check_taskpersonalized = 1` → harus match **dua kondisi**: `tp.status = mws.taskpersonalized_status` **DAN** kondisi overdue
3. `WHERE correct_status = 1`
4. `first_value(status_code) over(partition by MOId/Id, TaskId, TaskPersonalizedId order by status_code asc)` — safeguard jika >1 config row lolos

**Tabel Status Code:**
| Code | Label | wo_status | Overdue | TP Status |
|------|-------|-----------|---------|-----------|
| `INA` | Open | Open | Tidak | Tidak ada / Close / Cancelled |
| `INB` | Assigned | Open / In Progress / Pending | Tidak | Complete / In Progress / Open / Pending |
| `INE` | Completed | Complete | — | (tidak dicek) |
| `INF` | Overdue Open | Open | **Ya** | Tidak ada / Close / Cancelled |
| `ING` | Overdue Assigned | Open / In Progress / Pending | **Ya** | Complete / In Progress / Open / Pending |
| `INI` | Closed | Close | — | (tidak dicek) |
| `Cancelled` | Cancelled | Cancelled | — | (override semua) |

### CTE Khusus `get_molist`

- **`unit`** — join `asset` + `assetmodel`: lookup `assetcategorycode` (EQTYP) dan `assetmodelname`
- **`sectiontype`** — lookup nama section (ATWRT / SectionTypeName)
- **`mincreatedat`** — window function di CTE `taskpersonalized`:
  ```sql
  min(case when status not in ('Closed','Cancelled') then createdat end)
  over(partition by taskid)
  ```
  → earliest createdat TP aktif per task, dipakai di `DateCompletion`
- **`DateCompletion`** (derived):
  | TP Status | Nilai |
  |-----------|-------|
  | `'Complete'` | `tp.modifiedat` |
  | `'Open'`, `'In Progress'`, `'Pending'` | `mincreatedat` (earliest assignment) |
  | Lainnya | `wo.duedate` |

### CTE Khusus `get_assignment`

- **`taskpersonalizedlog`** — audit log waktu penyelesaian TP:
  ```sql
  max(enddate) per taskpersonalizedid
  WHERE tpl.isactive = 1 AND tp.status = 'Complete'
  ```
  → hanya TP Complete yang punya log; hasilnya jadi `SubmittedUtcDate`
- **`userinformation` dipakai 2×:**
  - `d` via `tp.usercode` → inspector
  - `g` via `tp.createdby` → SPV (yang membuat TP assignment)
- **`site`** → join via `d.siteid` (site inspector, bukan site WO) → `utcoffset` untuk konversi semua datetime ke local time

---

## Output Columns

### `get_molist` — Dimensi MO

**Identity & Equipment:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `Id` | `int` | ID work order — join key ke `get_assignment`.`MOId` |
| `MONo` | `varchar(16)` | Nomor WO |
| `MOName` | `varchar(512)` | Deskripsi WO |
| `Equipment` | `varchar(64)` | Nomor asset/unit |
| `SiteId` | `varchar(10)` | Kode site dari WO |
| `ILART` | `varchar(6)` | `maintenancecategorycode` |
| `ILARTText` | `varchar(512)` | `maintenancecategoryname` |
| `EQTYP` | `varchar(3)` | `assetcategorycode` |
| `ModelName` | `varchar(50)` | Nama model asset |
| `ATWRT` | `varchar(64)` | Nama section type — **duplikat `SectionTypeName`** |
| `SectionTypeName` | `varchar(512)` | Nama section type |
| `IsActive` | `bit` | Flag isactive WO |

**Dates (UTC — tidak dikonversi):**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `ScheduleDate` | `date` | `wo.schedulestartdate` |
| `MOUtcDate` | `date` | **Duplikat `ScheduleDate`** — sama-sama `wo.schedulestartdate` |
| `CreatedUtcDate` | `datetime` | Tanggal WO dibuat |
| `ModifiedUtcDate` | `datetime` | Tanggal WO terakhir dimodifikasi |
| `DateCompletion` | `datetime` | Derived — lihat logika di atas |

**Status:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `InspectionStatus` | `varchar(8)` | Kode status (INA/INB/INE/INF/ING/INI) |
| `StatusName` | `varchar(512)` | Label status |
| `AssignedBy` | `varchar(255)` | `employeeid` inspector — **nama misleading**, ini orang yang *di-assign*, bukan yang assign |

**SAP Placeholder (semua NULL):** `WorkCenter`, `AUART`, `TXT04`, `ARBPL`, `WeekAge`, `QMNUM`, `QMTXT`, `HDDTL`

---

### `get_assignment` — Dimensi Personel

**Identity:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `MOId` | `int` | ID work order — join key ke `get_molist`.`Id` |
| `MONo` | `varchar(16)` | Nomor WO |

**Personnel:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `InspectorId` | `varchar(255)` | `employeeid` inspector |
| `InspectorName` | `varchar(1000)` | Nama inspector |
| `SPVid` | `varchar(255)` | `employeeid` supervisor (`tp.createdby`) |
| `SPVName` | `varchar(1000)` | Nama supervisor |

**Dates (local time kecuali suffix `2`/`22`):**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `CreatedUtcDate` | `datetime` | Waktu TP dibuat — **local time** (nama misleading) |
| `CreatedUtcDate22` | `datetime` | Waktu TP dibuat — raw UTC |
| `SubmittedUtcDate` | `datetime` | Waktu TP selesai dari `taskpersonalizedlog` — **local time** |
| `SubmittedUtcDate2` | `datetime` | Waktu TP selesai dari log — raw UTC |
| `CompletedUtcDate` | `datetime` | **Selalu NULL** — placeholder |
| `CompletedUtcDate22` | `datetime` | **Selalu NULL** — placeholder |

**Status:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `Status` | `varchar(8)` | Kode status (INA/INB/INE/INF/ING/INI) |
| `StatusName` | `varchar(512)` | Label status |
| `Notes` | `varchar(5000)` | **Selalu NULL** — placeholder |

---

## Gap Analysis — Inkonsistensi Lintas View

### 1. Timezone: Overdue Check Berbeda

| | `get_molist` | `get_assignment` |
|---|---|---|
| `duedate` untuk overdue check | `cast(wo.duedate as date)` — UTC murni | `cast(dateadd(hour, utcoffset, wo.duedate) as date)` — local time |
| `today` untuk overdue check | `cast(getutcdate() as date)` — UTC | `cast(dateadd(hour, utcoffset, getutcdate()) as date)` — local time |
| `site.utcoffset` | Diambil, **tidak dipakai** | Dipakai untuk semua datetime |

**Dampak:** Untuk site UTC+7 (WITA) atau UTC+8 (WIT), batas tengah malam lokal berbeda 7–8 jam dari UTC. WO yang duedate-nya hari ini pukul 23:00 UTC → sudah overdue dalam local time tapi belum overdue dalam UTC. Satu WO yang sama bisa mendapat status berbeda di kedua view: `INF/ING` di `get_assignment` tapi masih `INA/INB` di `get_molist`.

**Rekomendasi:** Samakan ke salah satu. Jika timezone perlu konsisten → `get_molist` perlu pakai utcoffset juga. Jika UTC sudah cukup → `get_assignment` perlu dihapus konversinya dari logika overdue.

---

### 2. Sumber Waktu "Selesai" Berbeda

| | `get_molist` | `get_assignment` |
|---|---|---|
| Kolom | `DateCompletion` | `SubmittedUtcDate` |
| Sumber | `tp.modifiedat` (ketika TP status = Complete) | `max(tpl.enddate)` dari `taskpersonalizedlog` |
| Satuan | UTC | Local time |

**Dampak:** `tp.modifiedat` bisa berubah jika ada operasi update pada record TP setelah status Complete. `tpl.enddate` adalah audit log yang lebih stabil. Jika keduanya dipakai bersama di PBI, angka lead time / compliance bisa tidak konsisten untuk WO yang sama.

**Rekomendasi:** Tentukan satu sumber canonical untuk "waktu TP selesai". Jika `tpl.enddate` dianggap lebih akurat, `get_molist` perlu ditambah CTE `taskpersonalizedlog`.

---

### 3. Join Key Tidak Lengkap di `get_assignment`

`get_assignment` tidak mengekspos `TaskId` maupun `TaskPersonalizedId` di output-nya. Hanya `MOId` yang tersedia sebagai join key ke `get_molist`.

**Dampak:** Satu MO bisa punya N inspector (N baris di kedua view). Join via `MOId` saja menghasilkan **cartesian product**: N baris `get_molist` × N baris `get_assignment` = N² baris. Jika PBI tidak handle ini dengan benar, angka bisa double-count.

**Rekomendasi:** Tambahkan `TaskPersonalizedId` ke output `get_assignment` sehingga join bisa tepat per assignment.

---

### 4. Kolom Personel Tidak Setara

| Aspek | `get_molist` | `get_assignment` |
|-------|-------------|-----------------|
| ID inspector | `AssignedBy` = `employeeid` | `InspectorId` = `employeeid` |
| Nama inspector | ❌ tidak ada | `InspectorName` |
| ID SPV | ❌ tidak ada | `SPVid` |
| Nama SPV | ❌ tidak ada | `SPVName` |

Naming `AssignedBy` di `get_molist` ambigu — secara semantik bermakna "yang assign", tapi isinya adalah `employeeid` orang yang *di-assign*. `get_assignment` menggunakan `InspectorId` yang lebih jelas.

---

### 5. `DateCompletion` vs `CompletedUtcDate` — Keduanya Tidak Kompatibel

`get_molist` punya `DateCompletion` (derived logic per TP status, UTC). `get_assignment` punya `CompletedUtcDate` tapi **selalu NULL**. Jika consumer ingin "kapan inspeksi selesai" dari `get_assignment`, tidak ada data yang bisa dipakai selain `SubmittedUtcDate` yang hanya ada jika TP = Complete.

---

### 6. `mincreatedat` — Logic Tidak Ada di `get_assignment`

`get_molist` menghitung `mincreatedat` (earliest assignment per task) untuk mengisi `DateCompletion` ketika TP masih aktif. `get_assignment` tidak punya logic ini. Jika consumer ingin tahu "kapan pertama kali WO ini diassign ke siapapun", harus ambil dari `get_molist`.

---

## Business Rules (Confirmed)

- Hanya WO aktif (`isactive=1`) bertipe `'Inspection'` dengan task `'FlexiInspection'` yang masuk ke kedua view
- Granularitas: **per WO per taskpersonalized** — satu WO dengan N inspector menghasilkan N baris di masing-masing view
- `tenantcode = 'MKP'` hardcoded di `sectiontype` dan `site`
- WO dengan `wo.status` yang tidak ada di `config_mapping_wo_status.csv` → silent drop (tidak error)
- SPV didefinisikan sebagai `tp.createdby` — asumsi: yang membuat record assignment adalah supervisor/dispatcher

---

## Known Issues (Accepted / To Investigate)

| # | Issue | View | Severity |
|---|-------|------|----------|
| 1 | Inkonsistensi timezone di overdue check | Lintas view | **Tinggi** — bisa beda status untuk WO yang sama |
| 2 | Sumber waktu "selesai" berbeda (`modifiedat` vs `tpl.enddate`) | Lintas view | **Tinggi** — bisa beda angka KPI |
| 3 | Tidak ada `TaskPersonalizedId` di output `get_assignment` | `get_assignment` | **Tinggi** — cartesian product jika join via `MOId` saja |
| 4 | `site` CTE dead di `get_molist` | `get_molist` | Medium — boros fetch, potensi bingung pembaca |
| 5 | `MOUtcDate` = duplikat `ScheduleDate` | `get_molist` | Medium — jika `MOUtcDate` seharusnya local time, ini bug |
| 6 | `ATWRT` = duplikat `SectionTypeName` | `get_molist` | Low — redundan, SAP naming legacy |
| 7 | `AssignedBy` naming misleading | `get_molist` | Low — semantik membingungkan |
| 8 | `CompletedUtcDate` selalu NULL | `get_assignment` | Medium — placeholder belum jelas kapan diisi |
| 9 | Kolom "Utc" di `get_assignment` sudah local time | `get_assignment` | Low — naming misleading |
| 10 | Site join via `d.siteid` (site inspector) → NULL risk | `get_assignment` | **Tinggi** — jika inspector tidak punya siteid, seluruh datetime NULL dan baris hilang |
| 11 | `SPVName` bisa akun sistem | `get_assignment` | Low — perlu validasi data aktual |
| 12 | 8 kolom SAP selalu NULL | `get_molist` | Low — placeholder integrasi SAP |
| 13 | `mincreatedat` shared across all TP in task | `get_molist` | Low — semua inspector dalam task berbagi nilai yang sama |

---

## Recommended Questions for Business

1. **Timezone mana yang jadi acuan overdue?** Harus disamakan antara `get_molist` dan `get_assignment` agar status konsisten.
2. **`SubmittedUtcDate` (dari log) atau `DateCompletion` (dari modifiedat) yang jadi acuan KPI compliance?** Pilih satu sumber canonical untuk waktu selesai TP.
3. **Bagaimana cara PBI join kedua view?** Jika hanya via `MOId`, perlu dipastikan logic di PBI handle cartesian untuk WO dengan banyak inspector.
4. **`CompletedUtcDate` di `get_assignment` — kapan akan diisi, atau bisa dihapus?**
5. **Apakah `config_wicope_manual.csv` dipakai di layer PBI secara langsung, atau harusnya masuk ke salah satu view ini?** Saat ini tidak direferensikan di kedua SQL view.
