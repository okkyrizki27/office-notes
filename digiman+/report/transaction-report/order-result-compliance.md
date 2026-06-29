# `am.vw_report_iams_f_am_digiman_dorder`

**Page:** D'ORDER RESULT & ORDERING COMPLIANCE
**File:** [vw_report_iams_f_am_digiman_dorder.sql](vw_report_iams_f_am_digiman_dorder.sql)

## Business Question

Apa status spare part order (eMOL) yang dibuat dari temuan inspeksi maupun additional order, mulai dari submission hingga approval, SAP push, dan GR/GI? Setiap baris mewakili satu eMOL beserta material-nya, dilengkapi hasil validasi pooling dari SAP.

---

## Data Sources

| Source | Table/Path | Filter |
|--------|------------|--------|
| `mkp_dexecute` | `moapproval` | Tidak ada filter |
| `mkp_maintenance_execution` | `workorder` | `isactive = 1`, `typecode = 'Inspection'` |
| `mkp_maintenance_execution` | `task` | `isactive = 1`, `type = 'FlexiInspection'` |
| `mkp_maintenance_execution` | `taskpersonalized` | `isactive = 1` |
| `mkp_maintenance_execution` | `taskpersonalizedfinding` | `isactive = 1` |
| `mkp_maintenance_order` | `checkpartorder` | `isactive = 1` |
| `mkp_maintenance_order` | `material` | `isactive = 1` |
| `mkp_maintenance_order` | `mechanicorderdetail` | `isactive = 1` |
| `mkp_maintenance_order` | `mechanicorderlist` | **Filter `isactive` dikomentari — semua baris diambil** |
| `mkp_maintenance_order` | `mechanicordermaterial` | `isactive = 1` |
| `mkp_maintenance_order` | `mechanicordersummary` | `isactive = 1` |
| `mkp_maintenance_order` | `poolingmoitem` | `isactive = 1` |
| `mkp_maintenance_order` | `sapmosyncorder` | Tidak ada filter |
| `mkp_workflow` | `workflowtransaction` | `isactive = 1` |
| `mkp_services_asset` | `actionremedy`, `asset`, `assetmodel`, `component`, `damagecode`, `damagegroup`, `priority`, `subcomponent` | `isactive = 1` |
| `shared_tenant` | `sectiontype` | `isactive = 1`, `tenantcode = 'MKP'` |
| `shared_tenant` | `site` | `isactive = 1` |
| `shared_user` | `user` | `isactive = 1` ← **inkonsisten** dengan `vw_report_iams_inspection_results` yang tidak filter isactive |
| `mapping` | `config_mapping_mol_status.csv` | — |
| `mapping` | `config_mapping_pooling_validation.csv` | — |

---

## Transformation Logic

**CTE Chain:**
1. **26 Raw CTEs** — masing-masing baca satu tabel Delta Lake atau CSV
2. **`maintenance_execution_transformation`** — join WO → task → taskpersonalized → finding; menghasilkan data finding per inspector per unit
3. **`maintenance_order_transformation`** — CTE terkompleks; join `mechanicorderlist` ke semua tabel order, hitung `materialstatus` dan `correct_status`; filter `WHERE correct_status = 1`
4. **`sap_material_info`** — bandingkan material eMOL vs SAP (`checkpartorder`); hasilkan boolean flags: equipment, material number, ranking A-E, MO tracking CRTD/REL/TECO/CLSD, GR/GI partial/full
5. **`pooling_validation_result`** — join `sap_material_info` dengan truth table `config_mapping_pooling_validation`; hasilkan `colorcategory`, `canactiondigimandelete`, `cancreatemo`, `remark`
6. **`base_form`** — merge `maintenance_order_transformation` + `maintenance_execution_transformation`; untuk MOL tanpa summary (`summaryreference = 0`), field kosong diisi dari inspection via `COALESCE`
7. **Final SELECT** — enrich dengan master data, konversi UTC → local time, susun kolom display

**Key JOINs:**
- `mechanicorderlist` LEFT JOIN `mechanicordersummary` → MOL bisa standalone (`summaryreference=0`) atau via summary (`summaryreference=1`)
- Dual workflow: `wft1` by `workorderid`, `wft2` by `mechanicordersummaryid` → `COALESCE(wft1.status, wft2.status)`. Keduanya mutually exclusive karena **additional order tidak memiliki workorder** — MOL dari inspeksi hanya punya `wft1`, MOL dari additional order hanya punya `wft2`
- `pooling_validation_result` di-join dua kali karena MOL bisa punya atau tidak punya material: `pvr1` by `mechanicordermaterialid` (MOL dengan spare part), `pvr2` by `mechanicorderdetailid` (MOL tanpa material). `COALESCE(pvr1, pvr2)` → validasi material lebih spesifik dan diutamakan; fallback ke validasi detail jika tidak ada material
- `moapproval` via `concat('00', sso.mono) = moa.monumber`

**Key Derived Columns:**
- `InspectDescription` = `ComponentName + SubComponent/Other + DamageCodeName + (DamageGroupName)`
- `SubComponentName` = jika `subcomponentcode` null → `'Others; ' + othersubcomponentname`, else `sc.name`
- `PriorityName` = `concat(priority.code, ' - ', priority.description)`
- `materialstatus` = setelah workflow Complete: `isactive=0` → `'Delete'`; `createdby=modifiedby` → `'Add'`; lainnya → `'Ok'`
- `Activity` = `'CreateSAP'` jika `sapstatus = 1`, else null
- `moapprovaldate` = max(`approval1date`, `approval2date`) dari string `YYYYMMDD`; `'00000000'` = null
- `Aging` = `DATEDIFF(day, mol.createdat, GETUTCDATE())` — real-time, dihitung ulang setiap query
- Semua kolom tanggal di-`DATEADD(hour, utcoffset, ...)` → **local time** (termasuk yang namanya "UTC")

---

## Output Columns

**Identity:**
`MONo`, `InspectionType`, `UnitCode`, `ModelName`, `InspectorName`, `Section`, `SiteId`, `SiteName`

**Dates (semua sudah local time):**
`Date_Id`, `SubmittedUtcDateUTC`*, `SubmittedUtcDate`, `SubmitDate`, `SubmitDateCompliance`, `ApprovalDateUTC`*, `ModifiedUtdDate`, `EDDMOL`, `EDDValidation`, `eMOLOrderDate`, `SAPSyncStartDate`, `SAPSyncCompletedDate`, `MOApprovalDate`
*nama mengandung "UTC" tapi sudah dikonversi ke local time

**Component & Finding:**
`InspectDescription`, `ComponentName`, `SubComponentId`*, `SubComponentName`, `ActionName`, `PriorityName`, `DamageCodeName`
*menyimpan `componentcode`, bukan subcomponent ID — naming bug

**eMOL & Material:**
`EMOLNo`, `DetailId`, `MaterialNumber`, `MaterialDescription`, `Quantity`, `Unit`, `MaterialRanking`, `Batch`, `Amount`, `MOType`, `DeleteReason`

**Status & Workflow:**
`EMOLStatus`, `StatusDescription`, `MaterialStatus`†, `ApprovalName`, `ValidationBy`, `ValidationDate`

**SAP & Pooling:**
`SAPMONo`, `PoolingStatus`, `SAPStatus`, `SAPText`, `SAPSyncStartDate`, `SAPSyncCompletedDate`, `MOStatus`, `MOApprovalDate`, `Category`, `Remark`, `QuantityValidation`, `BatchValidation`

**Lain-lain:**
`Aging`, `Activity`, `Notes` (selalu null)

---

## Business Rules (Confirmed)

- **MOL bisa berasal dari dua sumber:**
  - **Inspeksi** (`summaryreference = 0`, punya `workorderid`) → data finding diambil dari `maintenance_execution_transformation`; filter `typecode = 'Inspection'` dan `type = 'FlexiInspection'` berlaku di path ini
  - **Additional Order** (`summaryreference = 1`, tidak punya workorder) → tidak melewati path inspeksi; filter WO tidak berlaku
- **`correct_status = 1`** adalah gating filter utama — eMOL hanya tampil jika kombinasi statusnya valid di `config_mapping_mol_status.csv`:

| Display | mol_status | isactive | workflow_status | require_mono |
|---------|-----------|----------|-----------------|--------------|
| Open | Open | 1 | (kosong) | — |
| Submitted | Complete | 1 | In Progress | — |
| Submitted | Complete | 1 | (kosong) | — |
| Approved | Complete | 1 | Complete | 0 |
| Deleted | Open/Complete | 0 | (kosong) | — |
| Completed | Complete | 1 | Complete | 1 |

- **`summaryreference`**: `0` = MOL dari inspeksi (`workorderid` ada, `mechanicordersummaryid` null), `1` = MOL dari additional order (`mechanicordersummaryid` ada, **tidak ada workorder**)
- **`user` filter `isactive = 1`** — **inkonsisten dengan `vw_report_iams_inspection_results`** yang tidak filter isactive. Di D'INSPECT inspector nonaktif tetap muncul (historis), tapi di D'ORDER tidak. Perlu dikonfirmasi apakah ini disengaja atau bug
- **SAP MO number lookup**: `concat('00', sso.mono)` untuk match ke `moapproval.monumber`. **Risk:** prefix `'00'` hardcoded — mengasumsikan semua tenant pakai SAP dengan format nomor MO berawalan `'00'`. Tenant yang tidak pakai SAP atau format berbeda → join selalu gagal → `MOStatus` dan `MOApprovalDate` selalu NULL tanpa error (silent)
- **Pooling validation**: truth table multi-kondisi (16+ boolean flag) → warna category + allowed actions
- **MOL bisa tanpa material** — ada dua jenis MOL detail: dengan spare part (punya `mechanicordermaterial`) dan tanpa spare part (hanya `mechanicorderdetail`). Pooling validation berlaku untuk keduanya dengan fallback: material-level (`pvr1`) diutamakan, detail-level (`pvr2`) sebagai fallback
- **Special case AR0010**: jika `actionremedycode = 'AR0010'` dan tidak ada material → `canactiondigimandelete` di-override jadi `1`

---

## Pending Confirmation

- **`MaterialStatus` (`'Add'`/`'Ok'`/`'Delete'`)** — kolom ini hanya output, tidak mempengaruhi logika lain di view. Tujuan bisnis di PBI belum dikonfirmasi. `'Add'` = workflow Complete, dibuat & dimodifikasi orang yang sama. `'Ok'` = dimodifikasi orang berbeda (kemungkinan supervisor). Perlu dikonfirmasi dipakai untuk apa di report.

---

## Known Issues (Accepted / To Investigate)

- **`mechanicorderlist` isactive dikomentari** — semua MOL masuk, disaring via `correct_status`. Berisiko jika ada kombinasi status baru yang belum ada di config → silent drop.
- **`SubComponentId` menyimpan `componentcode`** — naming bug.
- **Kolom "UTC" sudah local time** — `SubmittedUtcDateUTC`, `ApprovalDateUTC` sudah di-convert ke local time.
- **`Notes` selalu NULL** — placeholder.
- **Dual workflow COALESCE(wft1, wft2)** — aman, mutually exclusive by design. MOL inspeksi hanya match `wft1`, MOL additional order hanya match `wft2`.
- **`pvr1` vs `pvr2` COALESCE** — jika keduanya non-null tapi berbeda value, `pvr1` (material-level) menang. Ini disengaja karena validasi material lebih spesifik dari validasi detail.
- **`canactiondigimandelete`, `canactionsappushdelete`, `cancreatemo`, `cancreatemowithnote`** — dihitung di `pooling_validation_result` tapi **tidak masuk output view**. Kemungkinan dead code atau dipakai di layer lain (aplikasi Digiman+). Belum dikonfirmasi.
- **`poolingstatus NOT IN ('MOJ','MOK')`** — magic string, arti kedua status ini belum didokumentasikan.
- **`Aging` real-time** — laporan historis akan selalu menunjukkan aging terbaru.
- **`moapproval` tanpa filter isactive** — bisa ambil approval yang sudah tidak valid.
- **`sectiontype` hardcoded `tenantcode = 'MKP'`** — multi-tenant risk, sama seperti di `vw_report_iams_inspection_results`.
- **`sapmosyncorder` tanpa filter isactive** — bisa ambil SAP sync record yang sudah stale atau cancelled.
- **`moapprovaldate` string comparison** — `approval2date >= approval1date` adalah perbandingan varchar `YYYYMMDD`. Fragile jika ada format tidak konsisten di data SAP.
- **`PriorityName` NULL untuk additional order** — expected behavior; additional order tidak punya finding sehingga tidak ada priority.
