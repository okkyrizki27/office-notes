# `am.vw_report_iams_inspection_results`

**Page:** D'INSPECT RESULT
**File:** [vw_report_iams_inspection_results.sql](vw_report_iams_inspection_results.sql)

## Business Question

Apa saja temuan defect/kerusakan dari hasil inspeksi unit yang sudah diselesaikan inspector? Setiap baris mewakili satu finding dari satu work order inspeksi. Digunakan untuk monitoring hasil inspeksi per unit, komponen, dan tipe kerusakan.

---

## Data Sources

| Source | Table/Path | Filter |
|--------|------------|--------|
| `mkp_maintenance_execution` | `workorder` | `isactive = 1`, `typecode = 'Inspection'`, `status NOT IN ('Close', 'Cancelled')` |
| `mkp_maintenance_execution` | `task` | `isactive = 1`, `type = 'FlexiInspection'`, `status NOT IN ('Close', 'Cancelled')` |
| `mkp_maintenance_execution` | `taskpersonalized` | `isactive = 1`, `status = 'Complete'` |
| `mkp_maintenance_execution` | `taskpersonalizedfinding` | `isactive = 1` |
| `shared_user` | `user` | Tidak ada filter (termasuk user nonaktif) |
| `shared_tenant` | `site` | `isactive = 1`, `tenantcode = 'MKP'` |
| `shared_tenant` | `sectiontype` | `isactive = 1`, `tenantcode = 'MKP'` |
| `mkp_services_asset` | `assetmodel`, `component`, `subcomponent`, `damagecode`, `damagegroup`, `actionremedy` | Tidak ada filter tambahan |
| `mkp_services_asset` | `priority` | `group = 'Inspection'` |

---

## Transformation Logic

**CTE Chain:**
- `workorder` → WO aktif tipe Inspection, belum Close/Cancelled
- `task` → task aktif tipe FlexiInspection, belum Close/Cancelled
- `taskpersonalized` → assignment inspector yang sudah Complete
- `taskpersonalizedfinding` → semua finding/defect aktif
- `user` → lookup nama inspector
- `site` → lookup nama site + UTC offset
- `assetmodel`, `component`, `subcomponent`, `actionremedy` → master data lookup
- `damagecode`, `damagegroup` → digabung di CTE `damagecodegroup` via INNER JOIN on `damagegroupcode`
- `priority` → hanya group `'Inspection'`

**Key JOINs:**
- `workorder` **INNER JOIN** `task` → hanya WO yang punya FlexiInspection task
- `task` **LEFT JOIN** `taskpersonalized` → task bisa belum punya assignment
- `taskpersonalized` **LEFT JOIN** `taskpersonalizedfinding` → assignment bisa tanpa finding
- Semua master data → **LEFT JOIN**
- `damagecode` **INNER JOIN** `damagegroup` di CTE `damagecodegroup` → finding tanpa damagecode yang match akan hilang (silent drop)

**Derived Columns:**
- `Date` = `DATEADD(hour, site.utcoffset, wo.enddate)` → konversi UTC ke local time site
- `PriorityId`, `PriorityName` → jika `isimmediateexecutable = 1` AND `prioritycode` kosong/NULL → override jadi `'CLOSE'`
- `Notes` → jika kondisi CLOSE di atas → prefix `'CLOSE - '` + defectnotes
- `priorityname` di CTE priority = `CONCAT(name, ' ', description)`

**Filter akhir:** `WHERE tpf.id IS NOT NULL` → hanya baris yang punya finding

**Deduplication:** `SELECT DISTINCT` di inner query

---

## Output Columns

**Identity:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `MONo` | `varchar(16)` | Nomor work order |
| `Equipment` | `varchar(64)` | Nomor asset/unit |
| `ResultId` | `int` | ID finding (`tpf.id`) — primary key |
| `InspectorName` | `varchar(1000)` | Nama inspector |
| `ModelName` | `varchar(512)` | Nama model asset |
| `SiteName` | `varchar(1000)` | Nama site |
| `SectionTypeName` | `varchar(512)` | Nama section type |
| `SourceCode` | `varchar(8)` | Source WO |
| `InspectionType` | `varchar(512)` | Nama maintenance category |

**Dates:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `Date` | `datetime` | Tanggal selesai inspeksi (local time site) |
| `SubmittedUtcDate` | `datetime` | Tanggal selesai inspeksi (UTC) |
| `ScheduleDate` | `date` | Tanggal rencana inspeksi |

**Component & Finding:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `ComponentCode` | `varchar(4)` | Kode komponen |
| `ComponentName` | `varchar(512)` | Nama komponen |
| `SubcomponentCode` | `varchar(512)` | Kode subkomponen |
| `SubcomponentName` | `varchar(512)` | Nama subkomponen |
| `SubComponentOther` | `varchar(128)` | Nama subkomponen bebas (jika tidak ada di master) |
| `DamageGroupCode` | `varchar(16)` | Kode damage group |
| `DamageGroupName` | `varchar(512)` | Nama damage group |
| `DamageGroupDescription` | `varchar(512)` | Deskripsi damage group |
| `DamageCode` | `varchar(16)` | Kode damage |
| `DamageCodeName` | `varchar(512)` | Nama damage |
| `DamageCodeDescription` | `varchar(512)` | Deskripsi damage |

**Action & Priority:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `ActionName` | `varchar(128)` | Nama action remedy |
| `PriorityId` | `varchar(10)` | Kode priority (atau `'CLOSE'`) |
| `PriorityName` | `varchar(512)` | Nama priority (atau `'CLOSE'`) |
| `Notes` | `varchar(512)` | Catatan defect (atau `'CLOSE - <notes>'`) |

**Placeholder (selalu NULL — jangan dihapus dulu):**
`RouteId`, `RouteCode`, `RouteName`, `ComponentId`, `SubComponentId`, `DamageGroupId`, `DamageCodeId`, `ModelRouteText`, `Condition`, `ConditionName`, `ActionId`

---

## Business Rules (Confirmed)

- **WO lifecycle:** `Open → Pending → In Progress → Complete → Close`. Status `Close` = auto-close sistem karena inspector tidak mengeksekusi WO (bukan selesai). Filter `NOT IN ('Close', 'Cancelled')` benar — keduanya berarti WO tidak pernah diinspeksi.
- **Real-time findings:** View menampilkan findings dari WO `In Progress` maupun `Complete`. Disengaja — findings langsung tampil begitu inspector submit.
- **`isimmediateexecutable = 1` tanpa priority → label `CLOSE`:** Finding yang langsung diperbaiki saat inspeksi (quick fix, effort rendah). Bukan berarti WO-nya closed.
- **`ResultId` adalah primary key** — relasi `taskpersonalized → taskpersonalizedfinding` adalah 1-N.
- **Inspector nonaktif tetap diambil** — report historis, tidak ada filter `isactive` di `user`.
- **`tenantcode = 'MKP'` hardcoded** di site dan sectiontype.
- **Priority hanya group `'Inspection'`** — priority dari group lain tidak akan match.

---

## Known Issues (Accepted)

- **11 kolom placeholder selalu NULL** — dipertahankan sementara, belum ada rencana pengisian.
- **`user` tanpa filter `isactive`** — disengaja, report historis.
- **`damagecodegroup` pakai INNER JOIN** — finding dengan `damagecode` yang tidak ada di master akan hilang (silent drop). Belum divalidasi apakah ini terjadi di data aktual.
- **`SELECT DISTINCT` sebagai deduplication** — jika ada join fanout, bisa tetap menghasilkan duplikat. Belum ada laporan masalah.
- **`Date` bisa NULL** jika `sitecode` WO tidak match di tabel `site` (LEFT JOIN, utcoffset NULL → DATEADD NULL).
- **`taskpersonalized` filter hanya `Complete`** — task `In Progress` tidak akan punya findings yang tampil meski WO-nya aktif.
