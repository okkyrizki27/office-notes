# Backlog Monitoring — MKP Implementation Guide

Adaptasi SP `usp_iams_backlog_monitoring` ke tenant MKP

| | |
|---|---|
| **SP Target** | `usp_iams_backlog_monitoring` |
| **Tenant Asal** | BUMA ID |
| **Tenant Target** | MKP |
| **Prepared by** | Okky Rizki R |
| **Terakhir diupdate** | 10 Juni 2026 |

---

## Keputusan 1 — Hapus Dead Code: Join `#lookup`

> **Tanggal:** 09 Jun 2026
> **Temuan:** Isi tabel `digiman_dorder/lookup` (lookupcategory = `MOL_LAST_STATUS`) identik dengan `config_mapping_mol_status.csv`. Hasil join (`lookupname as status_desc`) tidak dipakai di manapun dalam output maupun logic `correct_status`. Join ini murni dead code dan sekaligus menjadi sumber error di MKP karena tabel `lookup` tidak tersedia di sana. Dikonfirmasi juga bahwa `lookup` tidak dipakai sebagai filter dropdown di PBI — sehingga tidak perlu dibuat di datamart MKP.

#### Hapus blok fetch `#lookup`:

**HAPUS**
```sql
drop table if exists #lookup
create table #lookup
(
    [lookupcode] varchar(32),
    [lookupname] varchar(128),
)

declare @query_lookup nvarchar(4000)
set @query_lookup =
'select lookupcode, lookupname from openrowset
(
    bulk ''assetmanagement/buma/digiman_dorder/lookup/'',
    data_source = ''curated_dfs_core_windows_net'',
    format = ''delta''
) a
where isactive = 1 and lookupcategory = ''MOL_LAST_STATUS''
'
insert into #lookup exec(@query_lookup)
```

#### Sederhanakan join di `maintenance_order_transformation`:

**SEBELUM**
```sql
left join
(
    select mms.*, l.lookupname as status_desc
    from #mapping_mol_status mms
    left join #lookup l
    on mms.[status] = l.lookupcode
) mmls
on mol.[status] = mmls.mol_status
```

**SESUDAH**
```sql
left join #mapping_mol_status mmls
on mol.[status] = mmls.mol_status
```

---

## Keputusan 2 — `dim_date`: Buat Pipeline Generate Parquet untuk MKP

> **Tanggal:** 09 Jun 2026
> **Keputusan:** SP tidak diubah — tetap baca `dim_date` parquet dari datamart seperti BUMA ID. Karena MKP tidak punya `dim_date` di datamart dan BUMA ID tidak punya pipeline untuk generate-nya, maka dibuat **pipeline baru** khusus untuk generate `dim_date` parquet ke datamart MKP menggunakan auto-generate SQL.

#### Kolom yang Diperlukan

SP butuh 2 kolom, PBI filter butuh 4 kolom. Pipeline harus generate keempat-empatnya:

| Kolom | Format | Dipakai SP | Dipakai PBI Filter |
|---|---|---|---|
| `date_id` | date | Ya (join key) | Ya |
| `week_id` | YYYYWW (int) | Ya (output kolom [week]) | Ya |
| `year` | int | Tidak | Ya |
| `month_id` | YYYYMM (int) | Tidak | Ya |

#### Logic Generate

Semua kolom di-generate murni dari SQL date functions — tidak butuh source data dari MKP. Konvensi hari pertama minggu dikontrol via parameter `@first_day_of_week`.

| @first_day_of_week | Hari Pertama | Offset | week_id untuk 8 Agt 2026 |
|---|---|---|---|
| 1 | Senin | 0 | 202633 |
| 4 | Kamis | -3 | 202633 |
| **6** | **Sabtu (BUMA ID)** | **-5** | **202632** |

```sql
-- Query generate dim_date untuk pipeline MKP
-- @offset = -(@first_day_of_week - 1)
-- @first_date_of_date_generation = tanggal awal generate dim_date (parameter, default '2020-01-01')
select
    d.date_id,
    cast(year(dateadd(day, @offset, d.date_id)) as varchar)
        + right('0' + cast(datepart(iso_week, dateadd(day, @offset, d.date_id)) as varchar), 2) as week_id,
    year(d.date_id) as [year],
    cast(year(d.date_id) as varchar)
        + right('0' + cast(month(d.date_id) as varchar), 2) as month_id
from (
    select cast(dateadd(day, n, @first_date_of_date_generation) as date) as date_id
    from (
        select top 3650 row_number() over (order by (select null)) - 1 as n
        from sys.objects s1 cross join sys.objects s2
    ) nums
) d
```

> **Prerequisite:** Konfirmasi 2 hal ke tim MKP sebelum pipeline dijalankan:
> - Konvensi hari pertama minggu (`@first_day_of_week`), agar `week_id` yang dihasilkan konsisten dengan kalender yang dipakai di dashboard mereka.
> - Tanggal awal generate `dim_date` (`@first_date_of_date_generation`) — sebelumnya hardcode `'2020-01-01'`, sekarang dijadikan parameter.

---

## Keputusan 3 — `dim_equipment`: Buat Pipeline Generate Parquet untuk MKP (Desain Universal)

> **Tanggal:** 09 Jun 2026, direvisi 10 Jun 2026
> **Keputusan:** SP tidak diubah — tetap baca `dim_equipment` parquet dari datamart seperti BUMA ID. Karena MKP tidak punya `dim_equipment` di datamart, dibuat **pipeline baru** yang generate `dim_equipment` parquet ke datamart MKP dengan menjoin tabel-tabel yang sudah ada di curated layer.

> **Revisi 10 Jun 2026 — Desain Universal:** `dim_equipment` harus berisi **SEMUA equipment** tanpa filter kategori. Tujuannya agar `dim_equipment` bisa direuse oleh dashboard lain (tidak hanya Backlog Monitoring). Filter spesifik per-dashboard dipindahkan ke config mapping `equipment_category` ↔ dashboard (lihat [Keputusan 6](#keputusan-6--config-files-untuk-mkp)), bukan baked-in di `dim_equipment` atau di SP.

#### Kolom yang Diperlukan

SP butuh `equipment` dan `status_unit`. PBI filter butuh 6 kolom (termasuk `equipment_category` baru):

| Kolom | Sumber | Catatan |
|---|---|---|
| `site_id` | `iams_services_asset/asset.sitecode` | Kolom sudah ada di tabel asset, belum di-select di SP |
| `equipment` | `iams_services_asset/asset.assetnumber` | Sudah ada di SP |
| `model_unit` | `iams_services_asset/assetmodel.name` | Join via `asset.assetmodelcode` |
| `section_type_code_name` | `iams_services_asset/sectiontype.name` | Join via `asset.sectiontypecode` — 🟠 **perlu direvisi/dicek ulang**, sebelumnya diasumsikan dari tabel `subcomponent` |
| `status_unit` | `iams_services_asset/assetstatus` | Ambil status terbaru per asset (ROW_NUMBER), **LEFT JOIN** |
| `equipment_category` | `iams_services_asset/asset.AssetCategoryCode` | 🟠 **Baru** — dipakai bersama config mapping `equipment_category` ↔ dashboard di Keputusan 6 |

#### Prerequisite — Sync `AssetStatus` ke Datamart

Tabel `AssetStatus` dari `cst-iams-sqldb-services-asset` belum ada di datamart. Perlu di-sync ke path:

```
assetmanagement/{tenantPath}/iams_services_asset/assetstatus/
```

#### Logic Ambil Status Terbaru

Tabel `AssetStatus` bersifat histori — ada multiple rows per asset. Pipeline harus ambil status terbaru per `AssetNumber`:

```sql
select AssetNumber, Status
from (
    select
        AssetNumber,
        Status,
        row_number() over (
            partition by AssetNumber
            order by TrDate desc, CreatedAt desc
        ) as rn
    from AssetStatus
) a
where rn = 1
```

> **Catatan:** Khusus join ke `AssetStatus` (untuk ambil `status_unit`) harus **LEFT JOIN**, supaya equipment yang belum punya record status tidak ter-exclude dari `dim_equipment` — `status_unit` hanya informasi tambahan, bukan filter. Join lainnya (model, section type, dst) ikuti pola yang sudah ada di SP saat ini. Pastikan pipeline generate `dim_equipment` MKP mencakup **semua** equipment yang ada (universal — lihat callout di atas), dan filter per-dashboard dilakukan lewat config mapping di Keputusan 6, bukan lewat INNER JOIN di SP.

---

## Keputusan 4 — Parameterisasi Business Logic Filter

> **Tanggal:** 09 Jun 2026
> **Keputusan:** Filter-filter yang hardcode di SP dijadikan parameter agar bisa dikonfigurasi per tenant. Nilai default diisi dengan nilai BUMA ID agar backward compatible.

#### Parameter Baru di SP

```sql
CREATE PROCEDURE [dbo].[usp_iams_backlog_monitoring]
(
    @yearmonth              VARCHAR(6),
    @tenantPath             VARCHAR(50)  = 'buma',        -- segment path ADLS2
    @tenantCode             VARCHAR(20)  = 'BUMAID',      -- filter tenantcode di sectiontype & site
    @moCreatedBy            VARCHAR(50)  = 'DATACOM',     -- filter createdby di mobacklog
    @replacementStatusLvl1  VARCHAR(20)  = 'BEX',         -- filter replacementstatuslvl1 di mobacklog
    @moType                 VARCHAR(20)  = 'MT01'         -- filter motype di mobacklog
)
```

| Filter | Lokasi di SP | Default (BUMA ID) | Action |
|---|---|---|---|
| `tenantcode` | sectiontype, site | BUMAID | Jadi `@tenantCode` |
| `mocreatedby` | mobacklog WHERE | DATACOM | Jadi `@moCreatedBy` — kemungkinan dihapus dari filter setelah konfirmasi MKP |
| `replacementstatuslvl1` | mobacklog WHERE | BEX | Jadi `@replacementStatusLvl1` — ini adalah **PM Activity Type** di SAP, 🟠 perlu konfirmasi nilai untuk MKP |
| `motype` | mobacklog WHERE | MT01 | Jadi `@moType` |
| `[group] = 'Inspection'` | priority WHERE | Inspection | 🟢 Tidak diubah — master data Digiman+, sama untuk semua client |

> **Open Item (10 Jun 2026):**
> - `@moCreatedBy` dan `@moType` mengasumsikan single value (mis. `'DATACOM'`, `'MT01'`). Di MKP kemungkinan ada **lebih dari satu value** untuk masing-masing filter ini — perlu desain parameter yang support multi-value (misal comma-separated string yang di-split, atau table-valued parameter). Teknis belum diputuskan.
> - Perlu konfirmasi ke MKP: apakah mereka oke **semua data backlog** diambil tanpa filter `created_by`, atau hanya subset tertentu — terkait volume data dan sensitivitas data.
> - `@replacementStatusLvl1` adalah **PM Activity Type** di SAP. BUMA ID memakai `'BEX'`; di MKP kemungkinan `'BKG'` saja, atau bisa jadi ada activity type lain yang juga relevan (multi-value, sama seperti `@moCreatedBy` dan `@moType`) — perlu konfirmasi ke tim MKP.

---

## Keputusan 5 — SAP User Status: Config Mapping File

> **Tanggal:** 09 Jun 2026
> **Keputusan:** SAP user status codes di MKP dipastikan berbeda dari BUMA ID. Pendekatan yang dipilih adalah **config mapping file** — mengikuti pola `config_mapping_mol_status.csv` yang sudah ada. SP membaca mapping dari file CSV sehingga tidak perlu ubah logic CASE WHEN saat ada client baru.

> **Revisi 10 Jun 2026:** Standar MO SAP **tidak punya step approval default** — workflow approval (*Waiting Approval*) adalah konfigurasi tambahan khusus BUMA ID. Step status MKP perlu dikonfirmasi satu per satu ke tim MKP (apa yang dianggap *Closed*, *In Progress*, *Waiting Approval*, dst — bisa jadi sebagian step ini tidak ada di MKP).

#### Kondisi Saat Ini (BUMA ID — Hardcode di SP)

```sql
case
    when lower(bb.user_status) = 'comp'                          then 'Closed'
    when lower(bb.user_status) in ('init','wapv','inpv','nrev')  then 'Waiting Approval'
    when lower(bb.user_status) = 'appv' and ...                  then 'Waiting Execution'
    when lower(bb.user_status) = 'appv' and ...                  then 'Waiting Planning'
    when lower(bb.user_status) = 'appv' and ...                  then 'Waiting Part'
end status_mo
```

#### Pendekatan Baru — Config Mapping File

Buat file `config_mapping_sap_user_status.csv` di ADLS2 path MKP yang memetakan SAP status code ke kategori status:

```
-- Struktur config_mapping_sap_user_status.csv
sap_status ; status_category
comp       ; closed
appv       ; approved
init       ; waiting_approval
wapv       ; waiting_approval
inpv       ; waiting_approval
nrev       ; waiting_approval
```

SP membaca file ini lalu CASE WHEN menggunakan `status_category` (nilai yang seragam) bukan hardcode SAP code. Saat ada client baru, cukup buat file config baru — SP tidak perlu diubah.

> **Open Item:** Nilai SAP user status codes untuk MKP belum dikonfirmasi. Perlu dicek ke tim MKP atau dari data aktual:
> ```sql
> SELECT DISTINCT [status] AS sap_status, COUNT(*) AS jumlah
> FROM mechanicorderlist
> GROUP BY [status]
> ORDER BY jumlah DESC
> ```
> Setelah nilai dikonfirmasi, isi `config_mapping_sap_user_status.csv` untuk MKP dan update logic SP untuk membaca dari config file.
>
> **Catatan penamaan (10 Jun 2026):** Apapun hasil konfirmasi step status MKP, nilai `status_category` di config tetap harus diselaraskan ke penamaan existing yang sudah dipakai (mis. *in progress* → `INPR`) — standardisasi penuh dilakukan di Digiman+ melalui `config_mapping_sap_user_status.csv`.

---

## Keputusan 6 — Config Files untuk MKP

> **Tanggal:** 09 Jun 2026, direvisi 10 Jun 2026
> **Keputusan:** Ada 5 config file yang perlu dipersiapkan untuk MKP. Satu bisa di-copy as-is, empat sisanya perlu dibuat baru setelah konfirmasi dengan tim MKP.

| File | Dipakai oleh | Aksi untuk MKP | Status |
|---|---|---|---|
| `config_mapping_mol_status.csv` | SP | Copy as-is dari BUMA ID | 🟢 Clear |
| `config_mapping_sap_user_status.csv` | SP | Buat baru — file ini belum ada di BUMA ID maupun MKP | 🟠 Tunggu konfirmasi SAP user status MKP |
| `config_image.csv` | PBI | Buat baru — section names disesuaikan dengan MKP, gambar disimpan sebagai base64 (chunked) bukan URL statis | 🟠 Tunggu section names & gambar dari MKP |
| `aging_category.csv` | PBI + SP | Buat baru — struktur CSV diperluas dengan kolom threshold & priority, SP diganti dari CASE WHEN ke range join | 🟠 Tunggu konfirmasi threshold MKP |
| `config_mapping_equipment_category_dashboard.csv` | PBI | 🟠 Baru — mapping `equipment_category` ↔ dashboard, bentuk baris per dashboard. Lihat [Keputusan 3](#keputusan-3--dim_equipment-buat-pipeline-generate-parquet-untuk-mkp-desain-universal) | 🟠 Desain awal, belum final |

#### Config Baru — `config_mapping_equipment_category_dashboard.csv`

Dipakai untuk filter per-dashboard di sisi PBI tanpa mengubah `dim_equipment` atau SP. Tidak perlu sampai level equipment — cukup level `equipment_category`. Setiap kombinasi kategori + dashboard yang ingin ditampilkan jadi satu baris (1 kategori bisa muncul di banyak dashboard):

| equipment_category | dashboard |
|---|---|
| AC | Backlog Monitoring |
| AC | EMS |
| OB | Backlog Monitoring |

PBI filter dashboard tertentu cukup join `dim_equipment.equipment_category` ke config ini lalu filter `dashboard = '...'` — tidak perlu logic filter terpisah per dashboard di SP/datamart.

#### Config Image — Mekanisme Base64 + Chunking

Gambar section/unit disimpan sebagai **base64** di config table (URL statis tidak diizinkan lagi). Karena base64 bisa melebihi limit ukuran kolom/storage, gambar dipecah jadi beberapa baris dengan kolom `sequence` dan di-assemble ulang saat dibaca:

| section | sequence | base64_chunk |
|---|---|---|
| OB | 1 | `iVBORw0KGgoAAAANS...` |
| OB | 2 | `UhEUgAAAyAAAAMg...` |

Akan dibuat program konversi gambar → base64 (chunked). Untuk MKP: minta gambar sesuai section/unit mereka, lalu dikonversi via program tersebut.

#### Perubahan Struktur `aging_category.csv`

Kolom `min_days` dan `max_days` ditambahkan agar threshold bisa dikonfigurasi per tenant tanpa ubah SP. `max_days` dikosongkan (NULL) untuk bucket terakhir, artinya tidak ada batas atas.

**Sebelum:**

| id | aging_category |
|---|---|
| 1 | 1-14 |
| 2 | 15-45 |
| 3 | >45 |

**Sesudah:**

| id | aging_category | min_days | max_days | priority |
|---|---|---|---|---|
| 1 | 1-14 | 0 | 14 | P1 |
| 2 | 15-45 | 15 | 45 | P2 |
| 3 | >45 | 46 | *null* | P3 |

> **Revisi 10 Jun 2026:** Aging range awalnya diasumsikan berbanding lurus langsung dengan priority (P1/P2/P3) dari tabel priority master — ternyata tidak, tabel priority punya range sendiri yang independen. Untuk sekarang, kolom `priority` ditambahkan eksplisit di `aging_category.csv` (P1 untuk 1-14, P2 untuk 15-45, P3 untuk >45) agar tidak ada asumsi proporsional. Long term: pertimbangkan ambil `aging_category` & `priority` langsung dari tabel priority master (diasumsikan universal antar tenant) begitu tabel itu tersedia di datamart.

#### Perubahan di SP — CASE WHEN diganti Range Join

**SEBELUM — hardcode CASE WHEN**
```sql
case
    when aging_days between 0  and 14 then '1-14'
    when aging_days between 15 and 45 then '15-45'
    when aging_days > 45              then '>45'
end as aging_range
```

**SESUDAH — range join ke #aging_category**
```sql
-- tambah temp table #aging_category, load dari CSV
drop table if exists #aging_category
create table #aging_category
(
    [aging_category] varchar(20),
    [min_days]       int,
    [max_days]       int,  -- null = tidak ada batas atas
    [priority]       varchar(10)
)
-- load dari: assetmanagement/{tenantPath}/mapping/aging_category.csv

-- lalu di CTE, ganti CASE WHEN dengan:
left join #aging_category ac
on aging_days >= ac.min_days
and (ac.max_days is null or aging_days <= ac.max_days)
-- select tambahan: ac.aging_category, ac.priority
```

---

*Backlog Monitoring — MKP Implementation Guide | Prepared by Okky Rizki R | 10 Juni 2026 | Confidential — Internal Use Only*
