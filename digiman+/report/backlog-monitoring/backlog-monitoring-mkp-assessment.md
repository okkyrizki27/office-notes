# Backlog Monitoring — MKP Implementation Assessment

Gap Analysis & Recommendations: BUMA ID → MKP

| | |
|---|---|
| **Document** | Technical Assessment Report |
| **Scope** | SP `usp_iams_backlog_monitoring` — Multi-tenant Readiness |
| **Current Tenant** | BUMA ID |
| **Target Tenant** | MKP |
| **Date** | 05 Juni 2026 |
| **Prepared by** | Okky Rizki R |

> **Status per dokumen ini:** Ini adalah gap analysis point-in-time (05 Jun, updated 09 Jun 2026). Sebagian besar item di bawah **sudah punya keputusan final** — lihat kolom "Status" di tiap tabel dan [backlog-monitoring-mkp-implementation.md](backlog-monitoring-mkp-implementation.md) untuk detail keputusannya. Item yang masih **OPEN** belum dikonfirmasi/diputuskan.

## Executive Summary

> Logic Backlog Monitoring yang ada saat ini **sepenuhnya hardcode untuk BUMA ID** dan **tidak dapat langsung dijalankan untuk MKP** tanpa perubahan. Terdapat **6 blocking issue** yang harus diselesaikan sebelum go-live, serta sejumlah konfigurasi yang perlu dieksternalisasi agar sistem dapat mendukung multi-tenant secara berkelanjutan.

Arsitektur saat ini: **API mentrigger save ke semua DB (ADM, d-inspect, d-execute, d-order) secara bersamaan**. Masing-masing client (BUMA ID dan MKP) memiliki DB terpisah. Perubahan SP harus mempertimbangkan bahwa satu SP akan digunakan untuk dua tenant dengan konfigurasi berbeda.

## 1. Inventory Hardcode di SP Saat Ini

### 1.1 ADLS2 Paths — 14 Path Semua Hardcode `/buma/`

```sql
-- Semua path di bawah ini mengandung '/buma/' yang perlu diganti per tenant
'assetmanagement/buma/digiman_dexecute/mobacklog/'
'assetmanagement/buma/digiman_dorder/lookup/'
'assetmanagement/buma/digiman_dplan/digitalplanning/'
'assetmanagement/buma/digiman_dplan/dpcolumn/'
'assetmanagement/buma/digiman_dplan/dpvalue/'
'assetmanagement/buma/iams_maintenance_execution/workorder/'
'assetmanagement/buma/iams_maintenance_execution/task/'
'assetmanagement/buma/iams_maintenance_execution/taskpersonalized/'
'assetmanagement/buma/iams_maintenance_execution/taskpersonalizedfinding/'
'assetmanagement/buma/iams_maintenance_order/mechanicorderlist/'
'assetmanagement/buma/iams_maintenance_order/...'  -- (dan 4 path lainnya)
'assetmanagement/buma/shared_tenant/sectiontype/'
'assetmanagement/buma/shared_tenant/site/'
'assetmanagement/buma/mapping/config_mapping_mol_status.csv'
'assetmanagement/buma/reports/digiman/dim_equipment_mobacklog/*.parquet'
'assetmanagement/buma/reports/digiman/dim_date/*.parquet'
```

> ✅ **Resolved** — semua path diganti `+ @tenantPath +` — lihat [Keputusan 4](backlog-monitoring-mkp-implementation.md#keputusan-4--parameterisasi-business-logic-filter).

### 1.2 Business Logic Filter — Hardcode

```sql
-- Filter MO (di query mobacklog)
WHERE mocreatedby = 'DATACOM'            -- source MO dari SAP
  AND replacementstatuslvl1 = 'BEX'      -- activity type
  AND motype = 'MT01'                    -- tipe MO

-- Tenant filter (di sectiontype & site)
WHERE tenantcode = 'BUMAID'

-- Status MO mapping (SAP user status codes)
WHEN lower(user_status) = 'comp'  → Closed
WHEN lower(user_status) IN ('init','wapv','inpv','nrev') → Waiting Approval
WHEN lower(user_status) = 'appv'  → (kondisional)

-- Priority group filter
WHERE [group] = 'Inspection'
```

> ✅ **Resolved** — dijadikan parameter SP (`@tenantCode`, `@moCreatedBy`, `@replacementStatusLvl1`, `@moType`) — lihat [Keputusan 4](backlog-monitoring-mkp-implementation.md#keputusan-4--parameterisasi-business-logic-filter). SAP user status mapping → [Keputusan 5](backlog-monitoring-mkp-implementation.md#keputusan-5--sap-user-status-config-mapping-file). `[group] = 'Inspection'` sengaja **tidak diubah** (master data Digiman+, sama untuk semua client).

### 1.3 Dimension Tables — Tidak Tersedia di MKP

| Table | Source | Status MKP | Impact jika Missing | Status Resolusi |
|---|---|---|---|---|
| `dim_equipment` | Parquet di datamart BUMA ID | Tidak Ada | INNER JOIN → output **0 rows** | ✅ [Keputusan 3](backlog-monitoring-mkp-implementation.md#keputusan-3--dim_equipment-buat-pipeline-generate-parquet-untuk-mkp-desain-universal) |
| `dim_date` | Parquet di datamart BUMA ID | Tidak Ada | `week_id` semua NULL | ✅ [Keputusan 2](backlog-monitoring-mkp-implementation.md#keputusan-2--dim_date-buat-pipeline-generate-parquet-untuk-mkp) |
| `lookup` MOL_LAST_STATUS | digiman_dorder/lookup | Tidak Ada | Risk SP error / `status_desc` NULL | ✅ [Keputusan 1](backlog-monitoring-mkp-implementation.md#keputusan-1--hapus-dead-code-join-lookup) — dihapus sepenuhnya (bukan sekadar TRY/CATCH, lihat §7) |

### 1.4 Config Files — BUMA ID Specific

| File | Konten (BUMA ID) | Risk di MKP | Status Resolusi |
|---|---|---|---|
| `config_mapping_mol_status.csv` | Status mapping MOL ke business status | MKP mungkin punya status berbeda | ✅ Copy as-is — [Keputusan 6](backlog-monitoring-mkp-implementation.md#keputusan-6--config-files-untuk-mkp) |
| `config_image.csv` | OB LOADER, OB HAULER, COAL HAULER, dll | Section MKP berbeda | 🟠 Buat baru, tunggu data MKP — [Keputusan 6](backlog-monitoring-mkp-implementation.md#keputusan-6--config-files-untuk-mkp) |
| `aging_category.csv` | 1–14, 15–45, >45 hari | Threshold MKP mungkin berbeda | 🟠 Struktur baru dibuat, tunggu threshold MKP — [Keputusan 6](backlog-monitoring-mkp-implementation.md#keputusan-6--config-files-untuk-mkp) |

## 2. Gap Analysis per Kategori

### Kategori A — BLOCKING (Harus diselesaikan sebelum go-live)

| # | Item | Masalah | Solusi | Status |
|---|---|---|---|---|
| **A1** | ADLS2 path `/buma/` | Path tidak exist di MKP container → semua query error | Parameterize: `@tenantPath` | ✅ Resolved — Keputusan 4 |
| **A2** | `dim_equipment` parquet | INNER JOIN → output 0 rows, dashboard kosong | Buat dim_equipment untuk MKP dari source DB MKP | ✅ Resolved — Keputusan 3 |
| **A3** | `dim_date` parquet | `week_id` semua NULL | Share parquet (data tidak tenant-specific) atau run `sp_dim_date` | ✅ Resolved — Keputusan 2 (pipeline generate baru, bukan share) |
| **A4** | `tenantcode = 'BUMAID'` | Filter salah, data sectiontype & site kosong | Parameterize: `@tenantCode` | ✅ Resolved — Keputusan 4 |
| **A5** | `createdby = 'DATACOM'` | MKP mungkin bukan DATACOM → mobacklog kosong | Config per tenant atau parameterize | 🟠 Diparameterkan (Keputusan 4), **nilai MKP masih open item** — kemungkinan multi-value |
| **A6** | `replacementstatuslvl1 = 'BEX'` | MKP mungkin punya activity type berbeda | Config per tenant atau parameterize | 🟠 Diparameterkan (Keputusan 4), **nilai MKP masih open item** — kemungkinan multi-value |

### Kategori B — SHOULD CHANGE (Data tidak akurat jika dibiarkan)

| # | Item | Masalah | Solusi | Status |
|---|---|---|---|---|
| **B1** | `motype = 'MT01'` | Tipe MO MKP belum dikonfirmasi | Config per tenant | ✅ Diparameterkan — Keputusan 4 |
| **B2** | SAP user status codes | MKP mungkin pakai kode berbeda di SAP | Config mapping status per tenant | 🟠 Desain config file selesai (Keputusan 5), **nilai MKP masih open item** |
| **B3** | `[group] = 'Inspection'` | Priority group MKP belum dikonfirmasi | Config per tenant | ✅ Diputuskan **tidak diubah** — master data Digiman+ (Keputusan 4) |
| **B4** | Section type exclusion (`OTHERS`, `LIGHTING TOWER`) | Mungkin bukan exclusion list MKP | Config per tenant | 🔴 **Belum dibahas** di implementation guide — masih perlu diputuskan |
| **B5** | `config_image.csv` | Section name MKP berbeda dari BUMA ID | Buat file config terpisah per tenant | 🟠 Struktur baru (base64 chunked) — Keputusan 6, tunggu data MKP |
| **B6** | `config_mapping_mol_status.csv` | MOL status MKP belum dikonfirmasi | Buat file config terpisah per tenant | ✅ Copy as-is dari BUMA ID — Keputusan 6 |
| **B7** | `lookup` MOL_LAST_STATUS | Tidak ada di MKP — risk SP error silent | Wrap query dalam TRY/CATCH (quick win) | ✅ **Superseded** — dihapus sepenuhnya, lihat §7 di bawah & Keputusan 1 |

### Kategori C — NICE TO HAVE (Improvement Arsitektur)

| # | Item | Rekomendasi | Status |
|---|---|---|---|
| **C1** | Aging range threshold | Buat config table per tenant (saat ini hardcode di SP) | ✅ Resolved — Keputusan 6 (`aging_category.csv` + `min_days`/`max_days`/`priority`) |
| **C2** | UTC offset | Sudah dynamic dari site table ✓ — tidak perlu diubah | ✅ No action needed |
| **C3** | `SELECT TOP 1` di validasi | Hanya validasi record pertama jika batch — perlu review jika batch dipakai | 🔴 Belum dibahas |
| **C4** | SP on-demand per bulan | Pertimbangkan scheduling otomatis jika volume meningkat | 🔴 Belum dibahas |

## 3. Rekomendasi Arsitektur

### Opsi 1 — SP Parameter (Jangka Pendek) ✅ Dipilih & Diimplementasi

Tambahkan parameter ke SP untuk menggantikan hardcode tenant-specific:

```sql
CREATE PROCEDURE [dbo].[usp_iams_backlog_monitoring]
(
    @yearmonth        VARCHAR(6),
    @tenantCode       VARCHAR(20) = 'BUMAID',   -- NEW
    @tenantPath       VARCHAR(100) = 'buma',    -- NEW: ADLS2 path segment
    @moCreatedBy      VARCHAR(50) = 'DATACOM', -- NEW
    @moType           VARCHAR(20) = 'MT01',    -- NEW
    @activityType     VARCHAR(20) = 'BEX',     -- NEW
    @priorityGroup    VARCHAR(50) = 'Inspection' -- NEW
)
```

Semua hardcode di-replace dengan parameter:

```sql
-- Sebelum
'assetmanagement/buma/digiman_dexecute/mobacklog/'
WHERE tenantcode = 'BUMAID'

-- Sesudah
'assetmanagement/' + @tenantPath + '/digiman_dexecute/mobacklog/'
WHERE tenantcode = @tenantCode
```

> **Pro:** Cepat diimplementasi, minimal perubahan, backward compatible (default value = BUMA ID).
> **Con:** Makin banyak parameter jika konfigurasi bertambah.

Opsi ini yang **dipilih dan sudah diimplementasi** — lihat parameter final di [Keputusan 4](backlog-monitoring-mkp-implementation.md#keputusan-4--parameterisasi-business-logic-filter) (bentuk final sedikit berbeda dari draft di atas, mis. `@replacementStatusLvl1` bukan `@activityType`).

### Opsi 2 — Tenant Config Table (Jangka Panjang) — Tidak Dipilih

Buat tabel konfigurasi yang dibaca SP saat runtime:

```sql
CREATE TABLE dbo.backlog_monitoring_config (
    tenant_code           VARCHAR(20)   PRIMARY KEY,
    tenant_path           VARCHAR(100),   -- ADLS2 path segment
    mo_created_by         VARCHAR(50),    -- filter createdby di mobacklog
    mo_type               VARCHAR(20),    -- filter motype
    activity_type         VARCHAR(20),    -- filter replacementstatuslvl1
    priority_group        VARCHAR(50),    -- filter [group] di priority
    section_type_exclude  VARCHAR(500),   -- comma-separated exclusion list
    aging_tier1_days      INT,            -- batas aging tier 1 (default 14)
    aging_tier2_days      INT,            -- batas aging tier 2 (default 45)
    is_active             BIT
)

-- BUMA ID (existing)
INSERT INTO backlog_monitoring_config VALUES
('BUMAID', 'buma', 'DATACOM', 'MT01', 'BEX', 'Inspection', 'OTHERS,LIGHTING TOWER', 14, 45, 1)

-- MKP (setelah dikonfirmasi)
INSERT INTO backlog_monitoring_config VALUES
('MKP', 'mkp', '???', '???', '???', '???', '???', 14, 45, 1)
```

> **Pro:** Scalable — tenant baru cukup tambah 1 row, tidak perlu ubah SP.
> **Con:** Effort lebih besar, perlu migration data, SP lebih kompleks.

> Belum dipilih — jadi kandidat jika jumlah tenant bertambah lagi setelah MKP dan jumlah parameter SP Opsi 1 mulai tidak terkelola.

## 4. Risk & Mitigasi

| Risk | Prob. | Impact | Mitigasi |
|---|---|---|---|
| `dim_equipment` MKP tidak tersedia → output kosong | Tinggi | Kritis | Buat SP/view `dim_equipment` untuk MKP sebelum go-live. Test dengan `SELECT COUNT(*)` dari source. |
| Filter `createdby=DATACOM` salah di MKP → mobacklog kosong | Tinggi | Kritis | Konfirmasi dengan tim MKP. Run: `SELECT DISTINCT createdby FROM mobacklog` |
| `replacementstatuslvl1=BEX` tidak match di MKP | Sedang | Tinggi | Run: `SELECT DISTINCT replacementstatuslvl1 FROM mobacklog` di MKP. |
| SAP user status codes berbeda → status MO salah semua | Sedang | Tinggi | Validasi dengan BPO MKP: apakah menggunakan kode SAP yang sama (`comp`, `appv`, dll). |
| `lookup MOL_LAST_STATUS` tidak ada → SP error silent | Tinggi | Sedang | Quick win: wrap query `#lookup` dalam TRY/CATCH. Sudah ada pattern di query `#mobacklog`. *(Superseded — lihat §7, join dihapus sepenuhnya)* |
| Section type exclusion berbeda → dim_equipment filter salah | Sedang | Sedang | Konfirmasi daftar section type MKP dengan BPO. Update config exclusion list. |
| Config files (image, aging) tidak di-update → UI tidak sesuai MKP | Rendah | Rendah | Buat file config baru per tenant di ADLS2 sebelum go-live. |
| `dim_date` tidak tersedia → `week_id` NULL | Tinggi | Rendah | `dim_date` tidak tenant-specific — share parquet yang sama atau run `sp_dim_date`. |

## 5. Quick Wins (Bisa Dilakukan Sekarang)

| # | Action | Effort | Impact |
|---|---|---|---|
| 1 | ~~Wrap `#lookup` query dalam TRY/CATCH~~ → digantikan hapus total join (§7) | 5 menit | Hilangkan risk SP error di MKP |
| 2 | Run query validasi berikut di MKP DB | 30 menit | Konfirmasi semua nilai filter yang benar |
| 3 | Cek apakah `dim_date` parquet bisa di-share antar tenant | 1 jam | Resolve 1 dari 3 blocking dim tables |
| 4 | Tambahkan parameter `@tenantCode` & `@tenantPath` ke SP | 2–3 jam | SP bisa dijalankan untuk MKP dengan path yang benar |

#### Query Validasi untuk Dijalankan di MKP:

```sql
-- 1. Cek nilai filter MO
SELECT DISTINCT createdby, replacementstatuslvl1, motype
FROM mobacklog

-- 2. Cek SAP user status codes
SELECT DISTINCT user_status FROM mechanicorderlist

-- 3. Cek priority group
SELECT DISTINCT [group] FROM priority

-- 4. Cek section type yang ada di MKP
SELECT DISTINCT sectiontypecode, sectiontypename FROM sectiontype
WHERE tenantcode = 'MKP'  -- ganti dengan tenant code MKP yang benar
```

## 6. Implementation Roadmap

1. **Assessment & Konfirmasi** — Jalankan query validasi di MKP. Konfirmasi nilai filter (createdby, motype, activity type, SAP status codes, section types) dengan BPO MKP.
2. **Resolve Blockers** — Buat `dim_equipment` untuk MKP. Handle atau share `dim_date`. Wrap `lookup` dalam TRY/CATCH.
3. **Refactor SP** — Tambah parameter tenant ke SP. Replace semua 14 hardcode ADLS2 path. Externalize filter values.
4. **Buat Config Files MKP** — `config_image.csv`, `aging_category.csv`, `config_mapping_mol_status.csv` untuk MKP di ADLS2.
5. **Testing** — Run SP untuk MKP `@yearmonth` bulan berjalan. Validasi output vs data di aplikasi Digiman+ MKP. Sign-off BPO MKP.
6. **Go-live & Monitoring** — Deploy ke production. Monitor jumlah record output antar tenant setiap run.

> **Estimasi effort total:** ~3–5 hari engineering (tergantung kecepatan konfirmasi data dari BPO MKP dan ketersediaan dim_equipment).

## 7. Temuan dari Analisis Mendalam (09 Juni 2026)

> Temuan ini (join `#lookup` redundant, bisa dihapus sepenuhnya) sudah dipindahkan menjadi keputusan final di **[Keputusan 1 — Hapus Dead Code: Join `#lookup`](backlog-monitoring-mkp-implementation.md#keputusan-1--hapus-dead-code-join-lookup)**, termasuk detail perbandingan data dan diff SQL. Lihat dokumen tersebut untuk isi lengkapnya — tidak diduplikasi di sini agar tidak ada dua sumber kebenaran yang bisa saling tidak sinkron.
>
> Ringkasan: hasil perbandingan data `digiman_dorder/lookup` vs `config_mapping_mol_status.csv` identik, dan kolom hasil join (`status_desc`) tidak dipakai di final SELECT maupun logic `correct_status`. Update terhadap item **B7** dan **Quick Win #1** di atas: rekomendasi awal (wrap TRY/CATCH) digantikan dengan **hapus join sepenuhnya**.

---

*Backlog Monitoring — MKP Implementation Assessment | Prepared by Okky Rizki R | 05 Juni 2026 | Updated 09 Juni 2026 | Confidential — Internal Use Only*
