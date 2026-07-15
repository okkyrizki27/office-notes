# Backlog Monitoring — Business Process & Configuration Analysis

Generated: 26 Mei 2026 | Author: Okky Rizki R | Scope: BUMA ID

> Dokumen ini adalah **referensi arsitektur & business logic** Backlog Monitoring sebagaimana berjalan saat ini di tenant BUMA ID. Snapshot per 26 Mei 2026 — untuk status adaptasi ke tenant MKP, lihat [backlog-monitoring-mkp-assessment.md](backlog-monitoring-mkp-assessment.md) (gap analysis) dan [backlog-monitoring-mkp-implementation.md](backlog-monitoring-mkp-implementation.md) (keputusan final, living document).

## 1. Overview

Backlog Monitoring adalah sistem pelaporan **Maintenance Order (MO) yang belum selesai (backlog)** di Digiman+ untuk tenant **BUMA ID**. SP utamanya adalah `usp_iams_backlog_monitoring` yang dijalankan per bulan dengan parameter `@yearmonth` format `YYYYMM`.

- Filter MO: `createdby = DATACOM`, `replacementstatuslvl1 = BEX`, `motype = MT01`
- Filter final: hanya MO yang memiliki `priority is not null` (sudah punya EMOL dengan data priority)
- Data di-adjust timezone berdasarkan UTC offset masing-masing site

## 2. Data Sources (ADLS2 via OPENROWSET)

| Source Group | Table | Keterangan |
|---|---|---|
| digiman_dexecute | mobacklog | MO backlog dari SAP. Filter: createdby=DATACOM, replacementstatuslvl1=BEX, motype=MT01 |
| digiman_dorder | lookup | Master status MOL (MOL_LAST_STATUS) — **tidak ada di MKP** |
| digiman_dplan | digitalplanning, dpcolumn, dpvalue | Cek apakah MO sudah masuk planning (status SUBMIT/INPROGRESS) |
| iams_maintenance_execution | workorder, task, taskpersonalized, taskpersonalizedfinding | Data inspeksi/eksekusi, join ke MO number |
| iams_maintenance_order | mechanicorderlist, mechanicorderdetail, mechanicordersummary, mechanicordermaterial, poolingmoitem, sapmosyncorder, checkpartorder | Data EMOL, part order, SAP sync |
| iams_services_asset | asset, assetmodel, component, subcomponent, actionremedy, priority | Master data equipment & komponen |
| iams_workflow | workflowtransaction | Status approval workflow |
| shared_tenant | sectiontype, site | Master site & section, filter tenantcode=BUMAID |
| shared_user | user | Master data user (code, fullname) |
| datamart (parquet) | dim_equipment_mobacklog, dim_date | Dimension equipment & tanggal — **tidak ada di MKP** |
| config (csv) | config_mapping_mol_status.csv | Mapping status MOL ke business status |

## 3. Business Logic Utama

### 3.1 Status MO

Ditentukan dari `user_status` (SAP) dan kondisi lainnya:

| User Status | Kondisi Tambahan | Status MO |
|---|---|---|
| `COMP` | — | **Closed** |
| `INIT, WAPV, INPV, NREV` | — | **Waiting Approval** |
| `APPV` | Ada di Digital Planning | **Waiting Execution** |
| `APPV` | Tidak di DP, ada SAP MO, GR/GI full atau partial | **Waiting Planning** |
| `APPV` | Tidak di DP, ada SAP MO, GR/GI kosong | **Waiting Part** |
| `APPV` | Tidak di DP, tidak ada SAP MO | **Waiting Planning** |
| Override: `Waiting Part` + `No Material` | | **→ Waiting Planning** |

**Priority rank** saat ada duplicate MO number:

Closed (1) → Waiting Approval (2) → Waiting Execution (3) → Waiting Planning (4) → Waiting Part (5)

### 3.2 Status Part

Diisi berdasarkan kombinasi GR/GI status dari `checkpartorder`. Hanya relevan untuk status Closed, Waiting Execution, Waiting Planning, Waiting Part. Nilai: *Completed: GR Full/GI Full/GI Partial*, *Not Completed*, atau `null`.

### 3.3 Aging Days & Aging Range

- **Aging Days** = selisih hari dari `mocreateddate` hingga sekarang (adjusted UTC offset per site), atau hingga `motecodate` jika sudah Closed.
- **Aging Range** (dari config CSV):

| Range | Keterangan |
|---|---|
| 1–14 hari | New/Recent |
| 15–45 hari | Medium |
| >45 hari | Critical |

### 3.4 Status Digital Planning

`Yes` / `No` — apakah MO number ditemukan di Digital Planning yang aktif (status SUBMIT/INPROGRESS) pada bulan tersebut.

### 3.5 MO Category

`Material` jika `plancost > 0`, `No Material` jika `plancost` adalah 0 atau null.

## 4. Dimension Tables

### vw_dim_equipment (app_wicope)

- Source: DB Digiman+ (`app_wicope`)
- Join: equipment → equipmentmodel → sectiontype → unitstatus (ambil status terbaru per equipment)
- Filter: `status_unit = 'INPR'`, section type bukan `OTHERS` atau `LIGHTING TOWER`
- Output: equipment, model_unit, section_type_code_name, status_unit

### vw_dim_site (app_opex)

- Source: `app_opex.dbo.vw_mcc_sap_mssite`
- Mapping site_id → site_code untuk 22 site BUMA (LAT, BIN, ADR, IPR, dll.)
- Beberapa site di-hardcode via UNION ALL (BSF, RO, INFRA, ADR CP, dll.)

### sp_dim_date

- Generate kalender dari **2019-01-01** s/d **2035-12-31**
- Week menggunakan custom logic: week start **Sabtu** (`DATEFIRST 5/6`)
- Output: date_id, week_id, month_id, quarter_id, semester_id, week_reset_desc, dll.

## 5. Configuration Files

### backlog_monitoring_config_image.csv

Mapping section ke URL gambar equipment untuk tampilan dashboard:

| Section | Image |
|---|---|
| OB LOADER | BIG DIGGER.png |
| OB HAULER | OB HAULER.png |
| SUPPORT GEAR EQUIPMENT | DOZZER.png |
| COAL HAULER | COAL HAULER.png |
| ALL | BUMA.png |

### backlog_monitoring_aging_category.csv

| ID | Aging Category |
|---|---|
| 1 | 1–14 hari |
| 2 | 15–45 hari |
| 3 | >45 hari |

## 6. Catatan Penting / Known Issues

> **1. dim_equipment & dim_date tidak tersedia di MKP**
> Kedua table ini diambil dari datamart parquet (bukan curated). Ada komentar eksplisit `GA ADA DI MKP` di stored procedure.

> **2. Lookup MOL status tidak tersedia di MKP**
> Table `#lookup` dari `digiman_dorder/lookup/` juga tidak ada di MKP.

> **3. SP berjalan per bulan (on-demand)**
> Tidak ada materialized view — SP ini menggunakan temp table dan harus dijalankan manual dengan parameter `@yearmonth`.

> **4. Filter MO ketat**
> Hanya MO dengan `createdby = DATACOM` (dari SAP), `replacementstatuslvl1 = BEX`, dan `motype = MT01` yang masuk ke backlog.

> **5. Priority null di-exclude dari output final**
> MO tanpa EMOL atau tanpa data priority tidak akan muncul di hasil akhir (`where [priority] is not null`).
