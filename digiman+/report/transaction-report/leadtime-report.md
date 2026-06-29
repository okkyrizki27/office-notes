# `am.vw_report_iams_f_am_digiman_leadtime`

**Page:** LEAD TIME REPORT
**File:** [vw_report_iams_f_am_digiman_leadtime.sql](vw_report_iams_f_am_digiman_leadtime.sql)

## Business Question

Berapa lama waktu yang dibutuhkan dari penugasan inspector hingga spare part order (eMOL) disetujui? Report ini mengukur **full cycle lead time** inspeksi per tahapan — assignment → submit inspeksi → buat eMOL → approval — per MO, per unit, per site. Hanya WO yang sudah menyelesaikan full cycle (approved) yang masuk laporan.

---

## Data Sources

| Source | Table/Path | Filter |
|--------|------------|--------|
| `mkp_maintenance_execution` | `workorder` | `isactive = 1`, `typecode = 'Inspection'` |
| `mkp_maintenance_execution` | `task` | `isactive = 1`, `type = 'FlexiInspection'` |
| `mkp_maintenance_execution` | `taskpersonalized` | `isactive = 1` |
| `mkp_maintenance_execution` | `taskpersonalizedfinding` | `isactive = 1` |
| `mkp_maintenance_execution` | `taskpersonalizedlog` | `isactive = 1`; inner join ke TP dengan `status = 'Complete'`; ambil `rank = 1` (`enddate` terbaru per TP) |
| `mkp_maintenance_order` | `mechanicorderlist` | `isactive = 1` |
| `mkp_workflow` | `workflowtransaction` | `status = 'Complete'`, `isactive = 1` |
| `mkp_services_asset` | `assetmodel` | Tidak ada filter |
| `shared_tenant` | `sectiontype` | `isactive = 1`, `tenantcode = 'MKP'` — hardcoded |
| `shared_user` | `user` | **Tidak ada filter** (termasuk user nonaktif) |
| `mapping` | `config_mapping_wo_status.csv` | — |
| `mapping` | `config_wicope_manual.csv` | `name_id = 'TARGET_FULL_CYCLE'`, `type_id = 'TFC'` |

---

## Transformation Logic

**CTE Chain:**

1. **`workorder`** → WO aktif tipe Inspection; field kunci: id, number, schedulestartdate, duedate, status, sitecode, sectiontypecode, assetnumber, assetmodelcode
2. **`task`** → task aktif tipe FlexiInspection; link ke WO via `workorderid`
3. **`taskpersonalized`** → semua TP aktif; field kunci: id, taskid, usercode, status, createdat, createdby, modifiedat. Satu task bisa punya beberapa TP (satu per inspector)
4. **`taskpersonalizedfinding`** → semua finding/defect aktif; link ke TP via `taskpersonalizedid`
5. **`taskpersonalizedlog`** → audit log waktu penyelesaian per TP, diambil tiga lapis:
   - Raw Delta: `taskpersonalizedid`, `enddate` (tanpa `usercode`)
   - INNER JOIN ke `taskpersonalized` di mana `status = 'Complete'` → `usercode` diambil dari `taskpersonalized`, bukan dari log
   - `ROW_NUMBER() OVER(PARTITION BY taskpersonalizedid ORDER BY enddate DESC)` → `WHERE rank = 1` → log terbaru per TP
6. **`mechanicorderlist`** → spare part order (eMOL); field kunci: workorderid, taskpersonalizedfindingid, number, completeddate, completedby
7. **`workflowtransaction`** → approval workflow; hanya `status = 'Complete'`; field kunci: referencetransactionid, modifiedat, modifiedby
8. **`assetmodel`**, **`sectiontype`** → master data lookup nama model dan section
9. **`user`** dipakai 3×: `usr1` (inspector via `tp.usercode`), `usr2` (eMOL creator via `mol.completedby`), `usr3` (approver via `wft.modifiedby`)
10. **`mapping_wo_status`** → status resolusi display (INA/INB/INE/INF/ING/INI)
11. **`config_wicope_manual`** → target SLA per site × jenis unit; filter `TARGET_FULL_CYCLE / TFC`; `type_desc` = target jam (nilai: `'24'`)

**Key JOINs:**

| Join | Tipe | Implikasi |
|------|------|-----------|
| `workorder → task` | **INNER** | Hanya WO dengan FlexiInspection task |
| `task → taskpersonalized` | LEFT | WO tanpa inspector tetap masuk (leadtime NULL) |
| `taskpersonalized → taskpersonalizedfinding` | LEFT | TP tanpa finding tetap masuk |
| `taskpersonalized → taskpersonalizedlog` | LEFT | TP belum Complete → tpl NULL → `inspection_submitted_date` NULL |
| `workorder + tpf → mechanicorderlist` | LEFT | Dual kondisi: `wo.id = mol.workorderid AND tpf.id = mol.taskpersonalizedfindingid` |
| `workorder → workflowtransaction` | **INNER** | **Filter utama** — hanya WO yang sudah ada Complete workflow approval (by design) |
| `workorder + sectiontype → config_wicope_manual` | LEFT | `wo.sitecode = cwm.site_id AND lower(st.name) = lower(cwm.type_status)` |

**Leadtime Calculations (satuan: jam, dibulatkan 2 desimal):**

```
schedulestartdate → tp.createdat       = leadtime_assignment
tp.createdat      → tpl.enddate        = leadtime_inspection
tpl.enddate       → mol.completeddate  = leadtime_create_emol
mol.completeddate → wft.modifiedat     = leadtime_approval
tpl.enddate       → wft.modifiedat     = leadtime_ordering    (create_emol + approval)
tp.createdat      → wft.modifiedat     = fullcycle_leadtime   (end-to-end)
```

Rumus: `round(datediff(second, [start], [end]) / 3600.0, 2)`

**Status Resolusi (window function, outer layer):**
```sql
first_value(status_name) over(partition by Id, TaskId, TaskPersonalizedId order by status_code asc)
```

---

## Output Columns

**Identity & Equipment:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `date_id` | `date` | `wo.schedulestartdate` — **duplikat `schedule_date`** |
| `mo_number` | `varchar(25)` | Nomor work order |
| `emol_number` | `varchar(25)` | Nomor eMOL (`mol.number`); NULL jika TP tidak punya finding |
| `maintenance_type` | `varchar(512)` | `wo.maintenancecategoryname` |
| `site_id` | `varchar(10)` | Kode site WO |
| `section_name` | `varchar(512)` | Nama section type |
| `model_unit` | `varchar(50)` | Nama model asset |
| `equipment` | `varchar(64)` | Nomor asset/unit |
| `status` | `varchar(50)` | Status display (Open/Assigned/Completed/dll) |
| `schedule_date` | `date` | `wo.schedulestartdate` — **duplikat `date_id`** |

**Timeline & Personel:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `assignment_date` | `datetime` | `tp.createdat` — kapan TP dibuat (inspector ditugaskan) |
| `assignmentby` | `varchar(4000)` | Nama inspector (`tp.usercode → user.fullname`) |
| `inspection_submitted_date` | `datetime` | `tpl.enddate` — waktu TP diselesaikan (log terbaru, UTC) |
| `inspection_submittedby` | `varchar(4000)` | **Usercode** inspector (`tpl.usercode = tp.usercode`) — bukan fullname; sama orang dengan `assignmentby` dalam satu baris, berbeda per baris jika beda TP |
| `submitted_emoldate` | `datetime` | `mol.completeddate` — tanggal eMOL selesai dibuat |
| `submitted_emolby` | `varchar(255)` | Nama pembuat eMOL (`mol.completedby → user.fullname`) |
| `approved_date` | `datetime` | `wft.modifiedat` — tanggal workflow diapprove |
| `approvedby` | `varchar(4000)` | Nama approver (`wft.modifiedby → user.fullname`) |

**Lead Time (jam):**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `leadtime_assignment` | `numeric` | schedulestartdate → assignment; bisa negatif |
| `leadtime_inspection` | `numeric` | assignment → submit inspeksi |
| `leadtime_create_emol` | `numeric` | submit inspeksi → buat eMOL; NULL jika tidak ada finding |
| `leadtime_approval` | `numeric` | buat eMOL → approved; NULL jika tidak ada eMOL |
| `leadtime_ordering` | `numeric` | submit inspeksi → approved (combined) |
| `fullcycle_leadtime` | `numeric` | assignment → approved (end-to-end) |
| `fullcycle_leadtime_target` | `varchar(255)` | Target SLA dari config (nilai: `'24'`); NULL jika section name tidak match config |

**Audit:**
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `load_date` | `datetime` | `dateadd(hour, 7, getutcdate())` — UTC+7 hardcoded |

---

## Business Rules (Confirmed)

- **Hanya WO yang sudah approved:** INNER JOIN ke `workflowtransaction WHERE status='Complete'` adalah by design — report ini hanya mengukur WO yang sudah menyelesaikan full cycle (inspection → eMOL → approval). WO yang masih berjalan tidak masuk dan tidak seharusnya masuk.
- **Granularitas per WO per TP per finding:** Satu WO bisa punya beberapa inspector (beberapa TP) dan beberapa finding per TP → beberapa baris per WO adalah expected behavior.
- **eMOL hanya linked via finding:** `mol.taskpersonalizedfindingid = tpf.id` — setiap eMOL berasal dari satu finding spesifik. WO tanpa finding tidak akan punya data eMOL.
- **`taskpersonalizedlog` hanya untuk Complete TP:** Log hanya ada jika TP sudah Complete; TP yang masih aktif tidak punya `inspection_submitted_date`.
- **Target SLA (`fullcycle_leadtime_target`):** Semua kombinasi yang match di config memiliki target 24 jam (`TFC`). Baris `TFCx3 = 72 jam` tidak dipakai di view ini (filter `type_id = 'TFC'`) — kemungkinan dead configuration, dapat dievaluasi untuk dihapus dari CSV.
- **Status resolusi overdue:** `wo.duedate vs getutcdate()` — UTC murni, tidak ada konversi timezone.
- **`user` tanpa filter `isactive`:** Disengaja — report historis, inspector/approver yang sudah nonaktif tetap harus tampil.

---

## Known Issues (Accepted / To Investigate)

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1 | `inspection_submittedby` menyimpan **usercode** (bukan fullname) sementara kolom lain menyimpan fullname; dalam satu baris selalu orang yang sama dengan `assignmentby` — hanya representasi berbeda | Low | Accepted — by design karena tiap baris adalah satu TP, `submittedby` = inspector TP tersebut |
| 2 | TP tanpa finding → `tpf.id = NULL` → join ke MOL tidak pernah match → `emol_number`, `leadtime_create_emol`, `leadtime_approval`, `fullcycle_leadtime` semua NULL | Medium | Accepted — WO tanpa finding memang tidak punya eMOL |
| 3 | Multiple `workflowtransaction Complete` per WO → baris ganda per siklus re-approval | Medium | To Investigate — apakah bisa terjadi di data aktual |
| 4 | `SELECT DISTINCT` sebagai safeguard duplikasi — tidak efektif jika baris hanya berbeda di nilai numerik leadtime | Medium | To Investigate |
| 5 | `fullcycle_leadtime_target` sering NULL — join via `lower(st.name) = lower(cwm.type_status)` bergantung pada kesamaan persis nama section type dengan nilai di CSV (`OB LOADER`, `OB HAULER`, `SGE`); beda tenant bisa beda nama | Medium | Accepted — nama section type bisa berbeda per tenant; perlu validasi per site |
| 6 | `leadtime_assignment` bisa negatif jika inspector ditugaskan sebelum `schedulestartdate` | Low | Accepted — tidak ada guard; consumer harus handle |
| 7 | `load_date = dateadd(hour, 7, getutcdate())` — UTC+7 hardcoded; site di WITA (UTC+8) atau WIT (UTC+9) mendapat nilai yang tidak tepat | Low | To Investigate — apakah semua site memang UTC+7 |
| 8 | `date_id` = duplikat `schedule_date` — keduanya `wo.schedulestartdate` | Low | Accepted — naming redundan, tidak berdampak fungsional |
| 9 | `workflowtransaction` join hanya via `referencetransactionid` tanpa filter tipe referensi — risiko false match jika ID WO dipakai juga oleh entitas lain | Low | To Investigate |
| 10 | `TFCx3 = 72 jam` di `config_wicope_manual.csv` tidak dipakai — kemungkinan dead configuration | Low | Accepted — akan dievaluasi untuk dihapus dari CSV di masa depan |
