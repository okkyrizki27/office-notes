# Digiman Transaction Report

Report transaksi Digiman yang terdiri dari 5 halaman. Semua view dibuat di schema `[am]` di Synapse/SQL serverless.

**Gap Analysis & Discussion Document:** [gap-analysis/Digiman_Transaction_Report_Gap_Analysis.pdf](gap-analysis/Digiman_Transaction_Report_Gap_Analysis.pdf) — dokumen rangkuman gap, usulan solusi, dan konfirmasi yang dibutuhkan dari business stakeholder lintas 5 halaman report. Sumber: [gap-analysis/gap-analysis.md](gap-analysis/gap-analysis.md), regenerate via `python gap-analysis/generate_pdf.py`.

**Improvement Design — Multi-Level Approval:** [gap-analysis/multi-level-approval-design.md](gap-analysis/multi-level-approval-design.md) — desain perubahan D'Order Result & Ordering Compliance untuk mendukung approval berjenjang (`WorkflowTransactionStep` + `WorkflowStep`).

---

## Mapping Report → View

| Page | View | File | Doc |
|------|------|------|-----|
| D'INSPECT RESULT | `am.vw_report_iams_inspection_results` | [vw_report_iams_inspection_results.sql](vw_report_iams_inspection_results.sql) | [doc](inspection-result.md) |
| D'ORDER RESULT | `am.vw_report_iams_f_am_digiman_dorder` | [vw_report_iams_f_am_digiman_dorder.sql](vw_report_iams_f_am_digiman_dorder.sql) | [doc](order-result-compliance.md) |
| INSPECTION COMPLIANCE | `am.vw_report_iams_get_molist` + `am.vw_report_iams_get_assignment` | [molist](vw_report_iams_get_molist.sql) · [assignment](vw_report_iams_get_assignment.sql) | [doc](inspection-compliance.md) |
| ORDERING COMPLIANCE | `am.vw_report_iams_f_am_digiman_dorder` | sama dengan D'ORDER RESULT | [doc](order-result-compliance.md) |
| LEAD TIME REPORT | `am.vw_report_iams_f_am_digiman_leadtime` | [vw_report_iams_f_am_digiman_leadtime.sql](vw_report_iams_f_am_digiman_leadtime.sql) | [doc](leadtime-report.md) |

---

## Data Sources per View

### `vw_report_iams_inspection_results`
| Source | Table/Path | Keterangan |
|--------|------------|------------|
| `mkp_maintenance_execution` | `workorder` | Filter: `typecode = 'Inspection'`, status bukan Close/Cancelled |
| `mkp_maintenance_execution` | `task` | Filter: `type = 'FlexiInspection'`, status bukan Close/Cancelled |
| `mkp_maintenance_execution` | `taskpersonalized` | Filter: `status = 'Complete'` |
| `mkp_maintenance_execution` | `taskpersonalizedfinding` | Hasil temuan inspeksi |
| `shared_user` | `user` | Nama inspector |
| `shared_tenant` | `site` | Nama site + UTC offset |
| `mkp_services_asset` | `assetmodel`, `component`, `subcomponent`, `damagecode`, `damagegroup`, `actionremedy`, `priority` | Master data asset |
| `shared_tenant` | `sectiontype` | Nama section type |

### `vw_report_iams_get_molist`
| Source | Table/Path | Keterangan |
|--------|------------|------------|
| `mkp_maintenance_execution` | `workorder`, `task`, `taskpersonalized` | MO list inspection |
| `mkp_services_asset` | `asset`, `assetmodel` | Data unit |
| `shared_tenant` | `sectiontype`, `site` | Referensi lokasi |
| `shared_user` | `user`, `useremploymentprofile` | Data inspector + employee ID |
| `mapping` | `config_mapping_wo_status.csv` | Mapping status WO → display status |

### `vw_report_iams_get_assignment`
| Source | Table/Path | Keterangan |
|--------|------------|------------|
| `mkp_maintenance_execution` | `workorder`, `task`, `taskpersonalized`, `taskpersonalizedlog` | Assignment & status |
| `shared_user` | `user`, `useremploymentprofile` | Inspector + SPV |
| `shared_tenant` | `site` | UTC offset |
| `mapping` | `config_mapping_wo_status.csv` | Mapping status |

### `vw_report_iams_f_am_digiman_dorder`
| Source | Table/Path | Keterangan |
|--------|------------|------------|
| `mkp_dexecute` | `moapproval` | Status approval MO dari SAP |
| `mkp_maintenance_execution` | `workorder`, `task`, `taskpersonalized`, `taskpersonalizedfinding` | Data inspection |
| `mkp_maintenance_order` | `mechanicorderlist`, `mechanicorderdetail`, `mechanicordermaterial`, `mechanicordersummary`, `poolingmoitem`, `sapmosyncorder`, `checkpartorder`, `material` | Data eMOL / spare part order |
| `mkp_workflow` | `workflowtransaction` | Status approval workflow |
| `mkp_services_asset` | `asset`, `assetmodel`, `component`, `subcomponent`, `damagecode`, `damagegroup`, `actionremedy`, `priority` | Master data |
| `shared_tenant` | `sectiontype`, `site` | Referensi lokasi |
| `shared_user` | `user` | Nama inspector & approver |
| `mapping` | `config_mapping_mol_status.csv`, `config_mapping_pooling_validation.csv` | Mapping status eMOL & validasi pooling |

---

## Additional Datasets (Required by PBI)

Dataset tambahan yang harus ada agar Power BI report bisa load, meskipun sebagian tidak digunakan secara aktif.

| Dataset | Notes |
|---------|-------|
| `vw_report_iams_assignment_compliance` | Not Used — empty table, must exist for PBI |
| `vw_report_iams_breakdown_monitoring` | Not Used — empty table, must exist for PBI |
| `vw_report_iams_calendar` | Same as Backlog Monitoring |
| `vw_report_iams_completion_compliance_persona` | Not Used — empty table, must exist for PBI |
| `vw_report_iams_dim_date` | Same as Backlog Monitoring |
| `vw_report_iams_execute_compliance_persona_open` | Not Used — empty table, must exist for PBI |
| `vw_report_iams_execution_compliance_persona` | Not Used — empty table, must exist for PBI |
| `vw_report_iams_leadtime_inspection` | Not Used — empty table, must exist for PBI |
| `vw_report_iams_leadtime_ordering` | Not Used — empty table, must exist for PBI |
| `vw_report_iams_monitoring_mapping_equipment` | [vw_monitoring_mapping_equipment.sql](vw_monitoring_mapping_equipment.sql) |
| `vw_report_iams_supervisor_compliance_persona` | Not Used — empty table, must exist for PBI |
| `mapping_pooling_validation` | Last discussion: will not be used |
| `mapping_wo_status` | `config_mapping_wo_status.csv` |
| `config_wicope_manual` | `config_wicope_manual.csv` |
| `mapping_mol_status` | `config_mapping_mol_status.csv` |

---

## Config Files

| File | Dipakai di View |
|------|----------------|
| [config_mapping_wo_status.csv](config_mapping_wo_status.csv) | `vw_report_iams_get_molist`, `vw_report_iams_get_assignment`, `vw_report_iams_f_am_digiman_leadtime` |
| `config_mapping_mol_status.csv` | `vw_report_iams_f_am_digiman_dorder` |
| `config_mapping_pooling_validation.csv` | `vw_report_iams_f_am_digiman_dorder` |
| `config_wicope_manual.csv` | `vw_report_iams_f_am_digiman_leadtime` |
