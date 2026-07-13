# Form IIR — External API Integration Design

*Last updated: 2026-07-13*

*Status: Draft — proposal, belum diimplementasi*

---

## Konteks

Rencana expose data form submission IIR (`FORM394`) ke sistem eksternal via pull endpoint. Endpoint mengembalikan **banyak `formSubmission`** sekaligus, di-filter berdasarkan date range dengan **cap maksimal 7 hari**.

Data source: Cosmos `MaintenanceExecution` → `FormSubmissionStructure`, hasil query di [form-submission.md](form-submission.md#contoh-query--ambil-jawaban-user-dari-formsubmissionstructure) (query tab spesifik + tab general), digabung dengan `formName` dari SQL `cst-iams-sqldb-maintenance-execution` (lihat [Sumber Data](#sumber-data--sql--cosmos) di bawah).

## HTTP Method & Endpoint

**✅ Dikonfirmasi — dua endpoint dengan peruntukan berbeda**, bukan digabung jadi satu:

| Endpoint | Method | Peruntukan |
|---|---|---|
| `/api/v1/iir-form-submissions` | `GET` | **List/polling** — endpoint utama, filter date range (wajib) + `siteCode`/`equipmentNumber` (opsional) + pagination. Ini yang dipakai sistem eksternal untuk polling berkala |
| `/api/v1/iir-form-submissions/{formSubmissionId}` | `GET` | **Single-fetch by ID** — ambil 1 submission spesifik. Peruntukannya beda dari list: dipakai untuk re-fetch detail setelah dapat `formSubmissionId` dari hasil list (mis. retry granular kalau 1 submission gagal diproses di sisi eksternal), atau lookup manual/support/debugging — bukan untuk polling |

**✅ Disetujui — Method: `GET` untuk keduanya** — kedua endpoint sifatnya *read-only* dan *idempotent* (tidak membuat/mengubah state), jadi `GET` adalah pilihan paling idiomatik. `POST` biasanya dipakai kalau body request kompleks/butuh disembunyikan dari log/URL (mis. mengandung data sensitif) atau melebihi batas panjang URL — tidak berlaku di sini karena filter cuma date range + 2 string opsional + pagination, semuanya aman sebagai query string. `GET` juga lebih gampang di-cache, di-bookmark, dan di-debug (bisa langsung dites lewat browser/curl tanpa body).

Contoh:
```
GET /api/v1/iir-form-submissions?dateFrom=2026-07-01T00:00:00Z&dateTo=2026-07-07T23:59:59Z&siteCode=LAT&page=1&pageSize=20
GET /api/v1/iir-form-submissions/4b604512-b409-4a19-ba79-9ac5ab68e16c
```

### API Versioning

**🚩 Perlu di-assess developer — belum final, ini masih rekomendasi.**

**Rekomendasi: version di URL path** (`/api/v1/...`, sudah dipakai di contoh di atas) — dibanding header-based versioning (mis. `Accept: application/vnd.digiman.v1+json`) atau query-param versioning (`?version=1`). Alasan: paling eksplisit dan gampang didokumentasikan/dites untuk konsumen eksternal (tinggal ganti `/v1/` → `/v2/` di URL, tidak perlu edit header khusus) — cocok untuk integrasi B2B dengan tim eksternal yang belum tentu familiar dengan konvensi REST yang lebih "murni".

Kebijakan versioning yang direkomendasikan:
- **Breaking change** (hapus/rename field, ubah tipe data, ubah semantik filter) → bump major version (`/v1` → `/v2`), versi lama tetap jalan selama masa deprecation
- **Non-breaking change** (tambah field baru yang opsional, tambah endpoint baru) → tidak perlu bump version
- **Masa deprecation**: karena ini integrasi B2B terkoordinasi (bukan API publik dengan konsumen tak dikenal), beri window waktu (mis. 3–6 bulan) + notifikasi langsung ke pihak eksternal sebelum versi lama di-sunset — bukan langsung dimatikan

**Yang perlu developer nilai sebelum ini dikunci:**
- Apakah pola versioning ini konsisten dengan endpoint/API lain yang sudah ada di Digiman+ (kalau ada konvensi existing, sebaiknya ikut itu, bukan bikin pola baru khusus endpoint ini)
- Apakah infrastruktur routing/gateway saat ini sudah mendukung path-based versioning dengan mudah (mis. API Management/reverse proxy), atau ada kendala teknis yang bikin opsi lain (header/query-param) lebih murah diimplementasikan
- Realistis atau tidak komitmen masa deprecation 3–6 bulan dari sisi effort maintain 2 versi berjalan bersamaan

## Sumber Data — SQL + Cosmos

`formSubmissionId`, `formCode`, `formVersion` (`version`) **sudah ada langsung di dokumen Cosmos** `FormSubmissionStructure` — ketiganya sudah di-select di query yang ada di [form-submission.md](form-submission.md) (`c.formSubmissionId`, `c.formCode`, `c.version`), tidak perlu round-trip tambahan ke SQL.

Satu-satunya field yang **genuinely butuh SQL** adalah `formName` — Cosmos tidak pernah menyimpan nama form yang human-readable, cuma `formCode`/`formId`/`version`.

| Field | Sumber | Detail |
|---|---|---|
| `formSubmissionId`, `formCode`, `formVersion` | Cosmos — `FormSubmissionStructure` | Sudah ada di hasil query yang sama dengan `tabs[].sections[].answers[]`, tidak perlu SQL |
| `formName` | SQL — `[dbo].[Task].Name` (join `FormSubmission.TaskId → Task.Id`) | Snapshot nama form dari `maintenance-strategy` — lihat catatan keputusan di bawah |
| `submittedAt` | SQL — `[dbo].[TaskPersonalized].ModifiedAt` (join `Task.Id → TaskPersonalized.TaskId`) | Waktu final submit di device — informational, **bukan** field filter (lihat `syncAt`) |
| `syncAt` | SQL — `[dbo].[TaskPersonalized].LastSyncedModifiedAt` | Waktu record sync ke server — **ini field filter date-range**, karena Digiman+ offline-first (lihat Keputusan Desain #1) |
| `tabs[].sections[].answers[]` (isi jawaban form) | Cosmos — `FormSubmissionStructure` | Hasil query di [form-submission.md](form-submission.md) |
| `photos[].url` | SQL — `[dbo].[TaskPersonalizedEvidence].ContentAddress` (join `ReferenceId = photoGuid`), **kecuali** "Photo Machine SMU" via `[dbo].[TaskPersonalized].MachineSMUAddress` (join `ReferenceId = photoGuid`) | Lihat [Resolusi Blob URL untuk Foto](#resolusi-blob-url-untuk-foto) di bawah |

### Resolusi Blob URL untuk Foto

`photoGuid` yang didapat dari Cosmos (baik dari `TAKEPHOTO`, `CAMERACAPTURE`, maupun `PHOTOLIST` setelah fix) **bukan URL langsung** — cuma GUID. Untuk resolve jadi blob URL, join ke SQL `[dbo].[TaskPersonalizedEvidence]` berdasarkan `ReferenceId = photoGuid`:

```sql
SELECT 
    tpe.ReferenceId AS photoGuid,
    tpe.ContentAddress AS url
FROM [dbo].[TaskPersonalizedEvidence] tpe
WHERE tpe.ReferenceId IN (@photoGuid1, @photoGuid2, ...)
  AND tpe.IsActive = 1
```

Batch semua `photoGuid` yang terkumpul dari satu halaman hasil Cosmos jadi satu query `IN (...)` — bukan N+1 per foto.

**✅ `PHOTOLIST.valueCaption` sedang diperbaiki tim** — akan berisi GUID (konsisten dengan elemen foto lainnya), bukan device file path. Lihat pembaruan di open item #1 di bawah.

**✅ Revisi — "Photo Machine SMU" TERNYATA sama polanya dengan foto lain, cuma beda tabel target.** Sebelumnya didokumentasikan seolah field ini butuh query metadata terpisah (`MAX(tp.MachineSMUAddress)` via `TaskId` join). **Ini salah** — dikonfirmasi dari data Cosmos nyata: `value` elemen `CAMERACAPTURE` berlabel "Photo Machine SMU" (tab General, section "Asset Information") berisi GUID biasa (contoh: `122362d1-5230-4d2a-9883-cdb57eb97820`), **persis seperti `photoGuid` elemen foto lainnya** — bedanya cuma GUID ini nunjuk ke `[dbo].[TaskPersonalized].ReferenceId`, bukan `[dbo].[TaskPersonalizedEvidence].ReferenceId`:

```sql
SELECT 
    tp.ReferenceId AS photoGuid,
    tp.MachineSMUAddress AS url
FROM [dbo].[TaskPersonalized] tp
WHERE tp.ReferenceId IN (@photoGuid1, @photoGuid2, ...)
  AND tp.IsActive = 1
```

Query ini **paralel** dengan query resolusi `TaskPersonalizedEvidence` di atas — sama-sama batch `IN (...)`, sama-sama dipanggil sekali per halaman hasil, cuma beda tabel target. Karena resolusinya langsung berdasarkan `ReferenceId` spesifik (bukan agregasi `MAX()` per `TaskId`), **tidak ada lagi ambiguitas N-mechanic untuk field ini** — row yang di-lookup sudah pasti tepat, tidak perlu `GROUP BY`/`MAX()` seperti `formName`/`submittedAt`/`syncAt`.

**Implikasi implementasi:** logic resolusi foto tetap perlu percabangan di layer aplikasi berdasarkan elemen mana yang sedang di-resolve — tapi percabangannya cuma soal **pilih tabel target** (`TaskPersonalizedEvidence` vs `TaskPersonalized`/`Task`) untuk batch resolve GUID yang sama-sama datang dari `value`/`photoGuid`, bukan soal "field ini datang dari query yang sama sekali berbeda". **✅ Dikonfirmasi — identifikasi elemen "Photo Machine SMU" pakai `elementCode = 'CAMERACAPTURE'`**, bukan `taskCode`/label (lihat Keputusan Desain #13).

**✅ Dikoordinasikan dengan tim — migrasi `MachineSMUAddress` masuk scope PM Shutdown Service Package Phase 1.** [pm-shutdown-data-model.md](../../roadmap/phase1-service-package/pm-shutdown-data-model.md) mencantumkan `MachineSMUValue`/`MachineSMUAddress` sebagai kolom yang dihapus dari `TaskPersonalized` dan dipindah ke `Task`, sebagai bagian dari **PM Shutdown Service Package Phase 1**. Query di atas (`tp.MachineSMUAddress`, join by `tp.ReferenceId`) valid untuk live schema **saat ini** (PM Shutdown Service Package Phase 1 belum go-live).

**✅ Dikonfirmasi — pasca-rollout PM Shutdown Service Package Phase 1, join key pindah ke `Task.ReferenceId`.** Setelah `MachineSMUAddress` pindah ke `Task`, `value` GUID dari elemen "Photo Machine SMU" di Cosmos akan di-resolve lewat `Task.ReferenceId`, bukan lagi `TaskPersonalized.ReferenceId`:

```sql
SELECT 
    t.ReferenceId AS photoGuid,
    t.MachineSMUAddress AS url
FROM [dbo].[Task] t
WHERE t.ReferenceId IN (@photoGuid1, @photoGuid2, ...)
  AND t.IsActive = 1
```

Endpoint versi awal tetap pakai query `TaskPersonalized.ReferenceId` (sesuai live schema saat ini) — query di atas cuma berlaku setelah PM Shutdown Service Package Phase 1 go-live, jadi implementasi endpoint perlu switch ke versi ini bersamaan dengan rollout Phase 1 tersebut, bukan sebelumnya.

Contoh query SQL untuk metadata (`formName`, `submittedAt`, `syncAt`) per `formSubmissionId` — pakai `MAX()` + `GROUP BY` (lihat Keputusan Desain #4 kenapa selalu agregasi, bukan asumsi 1 row). `machineSMUPhotoUrl` **tidak lagi** bagian dari query metadata ini — resolusinya lewat query batch `TaskPersonalized.ReferenceId` di atas, sejalan dengan foto lain. Query metadata lengkap (dengan join `WorkOrder` untuk `siteCode`/`equipmentNumber`) ada di bawah, setelah versi list/date-range.

**✅ Dikonfirmasi — pakai join ke `Task.Name`, bukan `FormSubmission.FormName`:** [pm-shutdown-data-model.md](../../roadmap/phase1-service-package/pm-shutdown-data-model.md) menyebut `FormSubmission` rencananya dapat kolom `FormName` langsung sebagai bagian dari **PM Shutdown Service Package Phase 1** — tapi **Phase 1 tersebut belum go-live**. Kolom itu belum ada di live schema `cst-iams-sqldb-maintenance-execution` saat ini. Jadi opsi `FormSubmission.FormName` **tidak dipilih** untuk desain ini — join ke `Task.Name` (yang sudah ada dan terisi sekarang) adalah satu-satunya jalur yang valid. Kalau Phase 1 (Service Package) nanti go-live dan kolom itu tersedia, bisa dipertimbangkan lagi sebagai simplifikasi (skip join), tapi bukan keputusan untuk saat ini.

**✅ Dikonfirmasi ke live schema — `TaskPersonalized.LastSyncedModifiedAt` memang ada.** Dokumentasi [form-submission.md](form-submission.md#schema-tabel-taskpersonalized) sebelumnya belum mencantumkan kolom ini (gap dokumentasi, bukan gap schema) — sudah diperbaiki. Live schema `TaskPersonalized` juga punya `ReferenceId`, `LastSyncedAt`, `LastSyncedBy`, `LastSyncedModifiedBy` yang sebelumnya tidak terdokumentasi.

**✅ Dikonfirmasi — kardinalitas `TaskPersonalized` diperlakukan generik (N mechanic), bukan diasumsikan 1:1:** [form-submission.md](form-submission.md#schema-tabel-taskpersonalized) mendokumentasikan **1 Task → N TaskPersonalized** (1 record per mechanic yang di-assign ke task tersebut). Untuk form IIR spesifik, secara bisnis cuma 1 orang yang submit per form — tapi query di desain ini **tetap** memperlakukannya seolah bisa N mechanic (pakai `MAX()`/`GROUP BY`, lihat query di bawah dan Keputusan Desain #4), bukan mengandalkan fakta bisnis IIR yang single-user. Kalau nanti IIR (atau form lain yang pakai endpoint ini) berubah jadi multi-mechanic, query tidak perlu diubah.

**Implikasi untuk endpoint list/date-range:** alur paling natural jadi **SQL dulu** — query `FormSubmission JOIN Task JOIN WorkOrder JOIN TaskPersonalized` filter by **`LastSyncedModifiedAt`** (`syncAt`) date range untuk dapat daftar `formSubmissionId` + `formName`/`siteCode`/`equipmentNumber`/`submittedAt`/`syncAt` sekaligus, lalu satu Cosmos query tambahan untuk ambil isi jawaban semua `formSubmissionId` dalam batch tersebut (`WHERE c.formSubmissionId IN (...)`), lalu batch resolve semua `photoGuid` yang terkumpul (termasuk "Photo Machine SMU") lewat query `TaskPersonalizedEvidence`/`TaskPersonalized` — bukan N+1 per submission di tiap langkah. Ini kebalikan dari alur "Cosmos dulu" yang didesain sebelumnya (saat kriteria filter masih dianggap field Cosmos).

```sql
SELECT 
    fs.Id AS formSubmissionId,
    t.Name AS formName,
    wo.SiteCode AS siteCode,
    wo.AssetNumber AS equipmentNumber,
    MAX(tp.ModifiedAt) AS submittedAt,
    MAX(tp.LastSyncedModifiedAt) AS syncAt
FROM [dbo].[FormSubmission] fs
JOIN [dbo].[Task] t ON fs.TaskId = t.Id
JOIN [dbo].[WorkOrder] wo ON t.WorkOrderId = wo.Id
JOIN [dbo].[TaskPersonalized] tp ON tp.TaskId = t.Id
WHERE fs.IsActive = 1
  AND t.IsActive = 1
  AND wo.IsActive = 1
  AND tp.IsActive = 1
  AND (@siteCode IS NULL OR wo.SiteCode = @siteCode)
  AND (@equipmentNumber IS NULL OR wo.AssetNumber = @equipmentNumber)
GROUP BY fs.Id, t.Name, wo.SiteCode, wo.AssetNumber
HAVING MAX(tp.LastSyncedModifiedAt) >= @dateFrom
   AND MAX(tp.LastSyncedModifiedAt) < @dateTo
```

Filter date range pakai `HAVING` (bukan `WHERE`) karena kriterianya adalah hasil agregasi (`MAX(LastSyncedModifiedAt)`) per `formSubmissionId`, bukan per row mentah — `WHERE` akan filter row sebelum agregasi dan menghasilkan semantik yang salah (bisa exclude submission yang punya salah satu row TaskPersonalized di luar range padahal `MAX`-nya di dalam range). `siteCode`/`equipmentNumber` sebaliknya **bukan** hasil agregasi (nilainya konstan per `WorkOrder`, sama untuk semua row `TaskPersonalized` dalam grup yang sama) — jadi aman difilter di `WHERE`, tidak perlu `HAVING`.

`wo.SiteCode` dan `wo.AssetNumber` didapat dari join tambahan `Task.WorkOrderId → WorkOrder.Id` (lihat [schema WorkOrder](form-submission.md#schema-tabel-workorder)) — join path baru di luar yang sudah ada (`Task → TaskPersonalized`). Lihat [Filter Tambahan — Site & Equipment Number](#filter-tambahan--site--equipment-number) untuk detail kenapa filter ini ditambahkan dan kenapa kedua kolom ini juga di-include di response payload, bukan cuma jadi parameter filter.

Query metadata single-submission di atas ([Resolusi Blob URL untuk Foto](#resolusi-blob-url-untuk-foto)) juga perlu update join `WorkOrder` yang sama kalau `siteCode`/`equipmentNumber` mau muncul di response single-fetch — lihat versi update di bawah:

```sql
SELECT 
    fs.Id AS formSubmissionId,
    t.Name AS formName,
    wo.SiteCode AS siteCode,
    wo.AssetNumber AS equipmentNumber,
    MAX(tp.ModifiedAt) AS submittedAt,
    MAX(tp.LastSyncedModifiedAt) AS syncAt
FROM [dbo].[FormSubmission] fs
JOIN [dbo].[Task] t ON fs.TaskId = t.Id
JOIN [dbo].[WorkOrder] wo ON t.WorkOrderId = wo.Id
JOIN [dbo].[TaskPersonalized] tp ON tp.TaskId = t.Id
WHERE fs.Id = @formSubmissionId
  AND fs.IsActive = 1
  AND t.IsActive = 1
  AND wo.IsActive = 1
  AND tp.IsActive = 1
GROUP BY fs.Id, t.Name, wo.SiteCode, wo.AssetNumber
```

### Filter `IsActive`

Semua query SQL di atas (resolusi foto maupun metadata) sudah ditambahkan filter `IsActive = 1` di tiap tabel yang dijoin (`FormSubmission`, `Task`, `WorkOrder`, `TaskPersonalized`, `TaskPersonalizedEvidence`) — supaya record yang sudah di-soft-delete tidak ikut ter-expose ke sistem eksternal.

**🚩 Flag ke developer/tim backend — perlu dikonfirmasi apakah mekanisme `IsActive` ini benar-benar berjalan konsisten di live data saat ini**, sebelum filter ini diandalkan sebagai satu-satunya penjaga soft-delete. Yang perlu dicek:
- Apakah semua path soft-delete (UI, API internal, batch job, dll) benar-benar konsisten set `IsActive = 0`, atau ada jalur yang masih hard-delete/lupa update flag ini?
- Apakah ada kasus row dengan `IsActive = 0` yang justru **masih perlu muncul** di endpoint ini (mis. submission yang di-nonaktifkan tapi historinya tetap relevan buat pihak eksternal)? Kalau iya, filter ini perlu di-refine, bukan blanket `= 1` di semua tabel.
- Konsistensi antar tabel — kalau `FormSubmission.IsActive = 0` tapi `TaskPersonalized.IsActive = 1` (atau kombinasi tidak konsisten lainnya), row mana yang jadi acuan?

Kalau ternyata `IsActive` tidak reliable/tidak konsisten dijaga di seluruh alur, filter ini berisiko **exclude data yang seharusnya valid** (false negative) — jadi perlu divalidasi dulu, bukan diasumsikan aman cuma karena kolomnya ada di schema.

### Fallback Kalau Resolusi Foto Gagal

**✅ Disetujui — kalau `photoGuid` tidak match apapun** di `TaskPersonalizedEvidence`/`TaskPersonalized`/`Task` (mis. karena bug `PHOTOLIST` yang masih in-progress, data korup, atau race condition), entry foto **tetap muncul di `photos[]`, tapi `url: null`** — bukan di-drop diam-diam dari array.

Alasan:
- **Drop diam-diam menyembunyikan masalah** — caller tidak akan tahu ada foto yang seharusnya ada tapi hilang, jumlah `photos[]` jadi tidak match ekspektasi tanpa penjelasan
- **`url: null` konsisten dengan pola "jujur representasikan ketiadaan"** yang sudah dipakai di tempat lain di desain ini (mis. `title: null` untuk section tanpa judul)
- Memudahkan **observability** — endpoint bisa log/monitor berapa persen resolusi foto yang gagal per periode, sinyal awal kalau ada masalah data yang lebih luas (mis. bug `PHOTOLIST` yang belum kelar)

## Kenapa Perlu Skema Ter-normalisasi (Bukan Expose Hasil Query Mentah)

Hasil query Cosmos untuk tab **General** dan tab **Inspection/spesifik** punya struktur field yang berbeda secara internal (lihat [form-submission.md](form-submission.md)):

| Field hasil query | Tab General | Tab Spesifik |
|---|---|---|
| `taskCode` | GUID (element instance ID) — **tidak di-include di API, lihat Keputusan Desain #7** | Business code (mis. `Task1252`) — di-include di API |
| `photoGuid` | `null`, atau array of `{label, value}` (untuk `PHOTOLIST`), atau array 1 GUID (untuk `CAMERACAPTURE`) | Array of GUID string, atau `[]` |
| `number` | Selalu `""` | Nomor urut task |

Kalau hasil query ini di-expose apa adanya ke sistem eksternal, konsumen API harus tahu detail internal Cosmos (dua struktur tab yang berbeda, bentuk `photoGuid` yang tidak konsisten) — rawan salah paham dan breaking change kalau struktur internal berubah. API contract sebaiknya **satu bentuk yang konsisten**, terlepas dari bagaimana data disimpan secara internal.

## Skema Response

Contoh lengkap: [form-iir-external-api-response.json](examples/form-iir-external-api-response.json)

```
{
  dateFrom, dateTo,          ← echo balik parameter request
  totalRecords, page, pageSize, hasMore,
  submissions: [
    {
      formSubmissionId, formCode, formVersion, formName,
      siteCode, equipmentNumber,
      submittedBy, submittedAt, syncAt,
      tabs: [
        {
          title,
          sections: [
            {
              title,
              answers: [
                { taskCode?, label, value, lastUpdatedBy, photos: [{label, url}], number?, remark? }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Mapping Field (raw query result → API field)

| Raw (query) | API | Keterangan |
|---|---|---|
| Cosmos `c.formSubmissionId` | `formSubmissionId` | Sudah ada di Cosmos (asalnya dari SQL `FormSubmission.Id`, di-lowercase saat mapping — lihat [Relasi SQL ↔ Cosmos](form-submission.md)), tapi untuk API ini diambil langsung dari hasil query Cosmos |
| SQL `Task.Name` (join by `TaskId`) | `formName` | Lihat [Sumber Data](#sumber-data--sql--cosmos). Bukan dari `Form.Name` langsung, lewat snapshot `Task.Name` |
| SQL `WorkOrder.SiteCode` (join `Task.WorkOrderId → WorkOrder.Id`) | `siteCode` | **Field baru** — lihat [Filter Tambahan](#filter-tambahan--site--equipment-number) |
| SQL `WorkOrder.AssetNumber` (join `Task.WorkOrderId → WorkOrder.Id`) | `equipmentNumber` | **Field baru** — sumber asli `DPEquipment.Equipment`, lihat [Filter Tambahan](#filter-tambahan--site--equipment-number). Beda dengan jawaban "Kode Unit"/"Site" di tab General (isian inspector, bisa typo/beda) — field ini datang dari `WorkOrder`, jadi lebih reliable untuk filtering/correlation |
| SQL `TaskPersonalized.ModifiedAt` | `submittedAt` | Diganti dari sumber Cosmos ke SQL — lihat [Sumber Data](#sumber-data--sql--cosmos) |
| SQL `TaskPersonalized.LastSyncedModifiedAt` | `syncAt` | **Field baru** — perlu verifikasi kolom ini benar ada di live schema (lihat catatan ⚠ di atas) |
| `taskDesc` | `label` | Disamakan namanya lintas tab |
| `taskValue` | `value` | Disamakan namanya lintas tab. **Untuk elemen foto single-photo** (`CAMERACAPTURE`/`TAKEPHOTO`, mis. "Photo Machine SMU"), `value` diisi raw GUID yang sama dengan yang dipakai untuk resolve `photos[].url` (bukan `null`) — supaya konsumen API bisa correlate balik ke `ReferenceId` sumbernya kalau perlu. **Untuk multi-photo** (`PHOTOLIST`, mis. "Foto Kondisi Fisik Equipment"), `value` tetap `null` karena ada N GUID (satu per foto), tidak bisa direduksi ke satu scalar — masing-masing GUID cuma tersimpan implisit di balik `photos[].url` |
| `taskCode` (tab spesifik saja) | `taskCode` | **Cuma di-include untuk jawaban tab spesifik** — lihat Keputusan Desain #7. Untuk tab General, field ini `null`/tidak ada di response |
| `photoGuid` (bentuk tidak konsisten — lihat tabel di atas) | `photos: [{label, url}]` | **Selalu array**, `url` di-resolve dari SQL `TaskPersonalizedEvidence.ContentAddress` (join `ReferenceId = photoGuid` — lihat [Resolusi Blob URL untuk Foto](#resolusi-blob-url-untuk-foto)) — konsumen API tidak perlu tahu/branch berdasarkan elementCode asal (`TAKEPHOTO`/`CAMERACAPTURE`/`PHOTOLIST`) |
| `sectionTitle: ""` | `title: null` | `null` lebih jujur merepresentasikan "tidak ada judul" dibanding string kosong |
| `number` | `number` (nullable, hanya ada di tab spesifik) | Tidak dipaksakan ada di semua row |

## Keputusan Desain (Sudah Dikonfirmasi)

| # | Keputusan | Alasan |
|---|---|---|
| 1 | Date range filter berdasarkan **`syncAt`** (`TaskPersonalized.LastSyncedModifiedAt`) — **bukan** `submittedAt` maupun `createdDate` | Digiman+ **offline-first** — `submittedAt` adalah waktu aksi di device, bisa terjadi saat offline dan baru sync jauh belakangan. Kalau filter pakai `submittedAt`, submission yang selesai offline di hari-1 tapi baru sync di hari-10 berisiko **tidak pernah muncul** kalau sistem eksternal poll per window tanggal berurutan tanpa overlap (window hari 1-7 sudah lewat sebelum sync terjadi, window berikutnya filter dari hari-8 jadi tidak menangkapnya juga). Filter berdasarkan `syncAt` (kapan data benar-benar tersedia di server) menjamin record selalu ketangkap di window manapun yang mencakup waktu sync-nya |
| 2 | Endpoint **pakai pagination** (`page`/`pageSize`), default `pageSize` **20**, max **100** | Volume submission tetap bisa tinggi di periode sibuk (banyak site/banyak form/hari) — cap 7 hari tidak membatasi jumlah row, cuma membatasi rentang waktu. Batas max mencegah caller minta page size tak terbatas dan meniadakan tujuan pagination |
| 3 | `formName` diambil dari join `FormSubmission.TaskId → Task.Id → Task.Name`, **bukan** dari kolom `FormSubmission.FormName` | `FormSubmission.FormName` cuma ada di rencana **PM Shutdown Service Package Phase 1** ([pm-shutdown-data-model.md](../../roadmap/phase1-service-package/pm-shutdown-data-model.md)) — **Phase 1 (Service Package) tersebut belum go-live**, kolom itu belum ada di live schema. `Task.Name` sudah ada dan terisi sekarang |
| 4 | Query metadata (`formName`/`submittedAt`/`syncAt`/`siteCode`/`equipmentNumber`) selalu pakai `MAX()` + `GROUP BY`, **tidak** mengasumsikan 1 `TaskPersonalized` row per `formSubmissionId` | Form IIR secara bisnis memang cuma 1 orang yang submit — tapi query diperlakukan generik seolah bisa N mechanic (schema `TaskPersonalized` mendukung N per Task), supaya tidak perlu diubah kalau nanti form lain/perubahan bisnis membuat multi-mechanic jadi nyata. **`machineSMUPhotoUrl` dikecualikan dari daftar ini** — lihat #5 |
| 5 | `machineSMUPhotoUrl` **tidak lagi** bagian dari query metadata `MAX()`/`GROUP BY` — di-resolve lewat batch query by `ReferenceId = photoGuid` (paralel dengan resolusi foto lain via `TaskPersonalizedEvidence`). **Sebelum PM Shutdown Service Package Phase 1 go-live**: join ke `TaskPersonalized.ReferenceId` + `TaskPersonalized.MachineSMUAddress`. **✅ Dikonfirmasi untuk pasca-rollout Phase 1 tersebut**: join key pindah ke `Task.ReferenceId` + `Task.MachineSMUAddress` — bukan cuma migrasi kolom, tapi migrasi tabel join juga | Revisi dari desain awal: `value` elemen "Photo Machine SMU" di Cosmos ternyata berupa GUID yang match `ReferenceId` — sama polanya dengan `photoGuid` elemen foto lain, bukan field yang butuh join+agregasi terpisah. Ini juga menghilangkan ambiguitas N-mechanic untuk field ini (resolusi by `ReferenceId` spesifik, bukan `MAX()` per `TaskId`). `pm-shutdown-data-model.md` mencantumkan kolom `MachineSMUAddress` pindah dari `TaskPersonalized` ke `Task` sebagai bagian dari PM Shutdown Service Package Phase 1, dan tim mengonfirmasi `Task.ReferenceId` yang jadi join key baru — lihat query pasca-Phase 1 di [Resolusi Blob URL untuk Foto](#resolusi-blob-url-untuk-foto) |
| 6 | PII (`submittedBy`/`lastUpdatedBy` — email) **disetujui untuk di-share** ke sistem eksternal | Pihak eksternal seharusnya sudah tahu NIK dan data karyawan lain di database mereka sendiri — sharing email/identitas ini untuk keperluan reconciliation/matching record, bukan memperkenalkan informasi baru yang belum mereka punya |
| 7 | `taskCode` **tidak di-include** untuk jawaban di tab General — cuma ada di jawaban tab spesifik | Tab General memang tidak butuh `taskCode` — nilainya di sana cuma GUID internal (element instance ID), bukan business key yang berguna bagi sistem eksternal (beda dengan tab spesifik yang `taskCode`-nya business code seperti `Task1252`) |
| 8 | Autentikasi pakai **Client ID + Secret Key**, di-exchange ke Bearer token (rekomendasi: OAuth2 Client Credentials Grant) — bukan secret dikirim langsung tiap request | Mekanisme dasar (Client ID + Secret) sudah ditentukan; pola exchange-ke-token direkomendasikan supaya secret jarang terekspos (cuma saat token exchange) dan token bisa di-revoke/rotate independen. Detail lihat [Autentikasi & Otorisasi](#autentikasi--otorisasi) — **exact flow masih perlu dikonfirmasi**, lihat open item |
| 9 | Rate limit **per Client ID**, **disetujui** 30 req/menit + 2.500 req/hari (sliding window) | Endpoint didesain untuk polling berkala (bukan real-time), limit ini jadi guard rail terhadap bug/retry-loop, bukan pembatas kebutuhan wajar. Lihat [Rate Limiting](#rate-limiting) |
| 10 | Error response pakai envelope `{ error: { code, message, details } }` dengan `code` machine-readable, bukan cuma andalkan HTTP status | Konsumen API butuh cara program-friendly untuk branch per jenis error (mis. `DATE_RANGE_TOO_LARGE` vs `RATE_LIMITED`) tanpa parsing `message` yang human-readable. Lihat [Format Error Response](#format-error-response) |
| 11 | Filter tambahan **`siteCode`** dan **`equipmentNumber`** (opsional, combinable dengan date range) ditambahkan; kedua field ini juga di-include di response payload | Diminta eksplisit. Karena tanpa filter ini response bisa berisi campuran banyak site/equipment, kedua field juga ditambahkan ke response supaya caller bisa correlate hasil tanpa query balik — lihat [Filter Tambahan](#filter-tambahan--site--equipment-number) |
| 12 | `value` untuk answer **single-photo** (`CAMERACAPTURE`/`TAKEPHOTO`, mis. "Photo Machine SMU") diisi raw GUID (sama dengan `ReferenceId` yang dipakai untuk resolve `photos[].url`), **bukan** `null`. Untuk **multi-photo** (`PHOTOLIST`), `value` tetap `null` | Diminta eksplisit. Raw GUID di `value` memberi konsumen API cara audit/correlate balik ke sumber foto tanpa parsing `photos[].url`. Untuk `PHOTOLIST` tidak diterapkan karena ada N GUID (satu per foto) — tidak bisa direduksi ke satu field scalar `value` |
| 13 | Identifikasi elemen "Photo Machine SMU" (untuk percabangan resolusi foto ke `TaskPersonalized`/`Task`, bukan `TaskPersonalizedEvidence`) pakai **`elementCode = 'CAMERACAPTURE'`**, bukan `taskCode` atau `label` | Dikonfirmasi: di [General Tab Template](form-builder.md#mekanisme-general-tab-template) (varian `maintenance` maupun `businessoperational`), `CAMERACAPTURE` cuma dipakai untuk satu elemen — "Photo Machine SMU" — elemen foto lain di template ini pakai `PHOTOLIST`. Elemen foto di tab Inspection/spesifik pakai `TAKEPHOTO`, bukan `CAMERACAPTURE`. Jadi `elementCode` saja sudah cukup unik untuk identifikasi, tidak perlu matching `taskCode` (yang belum tentu stabil lintas form) atau `label` (rawan typo/translasi) |
| 14 | Semua query (resolusi foto & metadata) ditambahkan filter **`IsActive = 1`** di tiap tabel yang dijoin (`FormSubmission`, `Task`, `WorkOrder`, `TaskPersonalized`, `TaskPersonalizedEvidence`) | Diminta eksplisit — supaya record yang sudah di-soft-delete tidak ikut ter-expose ke sistem eksternal. **🚩 Reliabilitas mekanisme `IsActive` di live data belum diverifikasi** — lihat [Filter IsActive](#filter-isactive) dan open item baru |
| 15 | **✅ Disetujui** — kalau resolusi `photoGuid` gagal (tidak match apapun), entry tetap muncul di `photos[]` dengan **`url: null`** — bukan di-drop dari array | Drop diam-diam menyembunyikan masalah dari caller. `url: null` konsisten dengan pola "jujur representasikan ketiadaan" (lihat `title: null`), dan memudahkan observability (bisa monitor rate kegagalan resolusi foto). Lihat [Fallback Kalau Resolusi Foto Gagal](#fallback-kalau-resolusi-foto-gagal) |
| 16 | **✅ Disetujui** — method **`GET`** untuk kedua endpoint (list maupun single-fetch) | Kedua endpoint read-only dan idempotent — `GET` paling idiomatik, gampang di-cache/bookmark/debug. Filter (date range + `siteCode`/`equipmentNumber` + pagination) semuanya aman sebagai query string, tidak ada alasan pakai `POST`. Lihat [HTTP Method & Endpoint](#http-method--endpoint) |
| 17 | **Dua endpoint terpisah** — `GET /api/v1/iir-form-submissions` (list/polling) dan `GET /api/v1/iir-form-submissions/{formSubmissionId}` (single-fetch by ID) | Diminta eksplisit — dua endpoint ini beda peruntukan (polling berkala vs re-fetch/lookup granular), tidak digabung jadi satu. Lihat [HTTP Method & Endpoint](#http-method--endpoint) |
| 18 | Versioning API pakai **URL path** (`/api/v1/...`) | Paling eksplisit untuk konsumen B2B eksternal, gampang didokumentasikan/dites tanpa header khusus. **🚩 Masih rekomendasi, perlu di-assess developer** sebelum dikunci — lihat [API Versioning](#api-versioning) |
| 19 | **Tidak ada pembatasan otorisasi granular per site** — 1 Client ID valid otomatis akses semua site | Diminta eksplisit. Filter `siteCode`/`equipmentNumber` di request murni narrowing hasil pencarian, bukan enforcement keamanan. Lihat [Scope Otorisasi](#scope-otorisasi) |

## Open Items — Perlu Diselesaikan Sebelum Implementasi

### 1. `PHOTOLIST.valueCaption` berisi device file path, bukan blob URL — 🔧 sedang diperbaiki tim

**Status: In progress, bukan lagi open blocker murni.** Pada contoh submission yang diperiksa (`FORM394`, section tanpa judul di tab General), `PHOTOLIST.valueCaption` berisi path lokal device (`/var/mobile/Containers/Data/Application/.../CAP_....jpg`), bukan GUID seperti elemen foto lain. **Dikonfirmasi ini adalah bug yang sedang diperbaiki tim** — setelah fix, `PHOTOLIST.valueCaption` akan berisi GUID, konsisten dengan `TAKEPHOTO`/`CAMERACAPTURE`, dan bisa di-resolve ke blob URL lewat mekanisme yang sama (lihat [Resolusi Blob URL untuk Foto](#resolusi-blob-url-untuk-foto)).

**Masih perlu ditindaklanjuti:** pastikan endpoint ini tidak diimplementasikan/di-rollout sebelum fix tersebut selesai — kalau tidak, `photos[].url` untuk `PHOTOLIST` akan berupa GUID yang tidak match apapun di `TaskPersonalizedEvidence` (bukan device path lagi, tapi data lama yang sudah terlanjur tersimpan dengan bug ini mungkin tetap butuh penanganan/backfill terpisah).

### 2. 🚩 Reliabilitas mekanisme `IsActive` di live data belum diverifikasi

Query resolusi foto & metadata sekarang filter `IsActive = 1` di semua tabel yang dijoin (lihat [Filter IsActive](#filter-isactive) dan Keputusan Desain #14). Sebelum filter ini diandalkan sebagai satu-satunya penjaga soft-delete, **perlu dikonfirmasi ke developer/tim backend**:
- Apakah semua path soft-delete konsisten set `IsActive = 0`, atau ada jalur yang masih hard-delete/lupa update flag ini
- Apakah ada kasus row `IsActive = 0` yang justru masih perlu muncul di endpoint ini (mis. submission historis yang tetap relevan buat pihak eksternal)
- Konsistensi `IsActive` antar tabel yang di-join (mis. `FormSubmission.IsActive = 0` tapi `TaskPersonalized.IsActive = 1`) — row mana yang jadi acuan

Kalau ternyata tidak reliable, filter ini berisiko exclude data yang seharusnya valid (false negative).

### 3. 🚩 API Versioning — perlu di-assess developer

Rekomendasi versioning (`/api/v1/...` di URL path, kebijakan breaking-change/deprecation) di [API Versioning](#api-versioning) dan Keputusan Desain #18 **masih proposal, belum final**. Perlu dinilai developer: konsistensi dengan konvensi API/endpoint lain yang sudah ada di Digiman+, kesiapan infrastruktur routing/gateway untuk path-based versioning, dan realistis-tidaknya komitmen masa deprecation dari sisi effort maintain multi-versi.

---

## Autentikasi & Otorisasi

Mekanisme dasar: **Client ID + Secret Key** per konsumen eksternal.

**Rekomendasi implementasi — OAuth2 Client Credentials Grant** (standar untuk server-to-server integration):

1. Sistem eksternal exchange `client_id` + `client_secret` ke token endpoint (mis. `POST /oauth/token`) → dapat `access_token` (Bearer) dengan TTL pendek (mis. 1 jam)
2. Setiap request ke endpoint data pakai header `Authorization: Bearer <access_token>`
3. Token expired → sistem eksternal re-exchange, **bukan** pakai ulang `client_secret` di setiap request data

Kenapa exchange-ke-token, bukan kirim `client_id`+`client_secret` langsung di header tiap request data:
- Secret cuma terekspos saat token exchange (frekuensi jauh lebih rendah dibanding tiap call data), mengurangi permukaan risiko kalau ada log/proxy yang tidak sengaja capture header
- Token bisa di-revoke/rotate tanpa perlu ganti `client_secret` utama
- Token exchange jadi titik audit terpisah dari data access log — lebih mudah bedakan "siapa yang login" vs "siapa yang narik data"

**⚠ Open item — exact flow perlu dikonfirmasi:** apakah tim sudah punya identity platform/OAuth2 provider existing (mis. Azure AD atau IdP yang dipakai layanan Digiman+ lain) yang bisa dipakai untuk endpoint ini, supaya tidak perlu bangun token-issuance sendiri dari nol. Kalau tidak ada, opsi fallback lebih sederhana: static API key (`client_id`+`client_secret` langsung di header, mis. `X-Client-Id`/`X-Client-Secret`) tanpa token exchange — lebih cepat diimplementasikan tapi kurang aman untuk jangka panjang.

### Scope Otorisasi

**✅ Dikonfirmasi — tidak ada pembatasan granular per site.** 1 Client ID yang valid (lolos autentikasi) otomatis punya akses ke **semua site**, bukan dibatasi ke site tertentu. Jadi tidak perlu ACL/mapping tambahan "Client ID X cuma boleh lihat site LAT" — begitu autentikasi lolos, filter `siteCode`/`equipmentNumber` di request murni buat narrowing hasil pencarian caller sendiri, bukan enforcement keamanan.

## Rate Limiting

**✅ Dikonfirmasi — per Client ID** (bukan per IP — ini integrasi server-to-server, IP caller eksternal bisa shared/NAT/berubah).

Algoritma: **sliding window** (lebih smooth dibanding fixed window, tidak ada burst-di-boundary problem saat window reset).

**✅ Dikonfirmasi** limit berikut:

| Window | Limit |
|---|---|
| Per menit | 30 request |
| Per hari | 2.500 request |

Angka per-hari diskalakan proporsional mengikuti angka per-menit (rasio yang sama dengan starting point awal 60/menit : 5.000/hari).

Alasan angka ini masuk akal: endpoint ini didesain untuk **polling berkala** (date-range pull, cap 7 hari, page size default 20/max 100), bukan akses real-time frekuensi tinggi. Kalau sistem eksternal poll tiap beberapa menit sekali, 30/menit jauh di atas kebutuhan wajar — limit ini fungsinya jadi guard rail terhadap bug (mis. retry loop tanpa backoff) atau penyalahgunaan, bukan pembatas kebutuhan bisnis normal.

**Catatan implikasi:** 30 req/menit berarti rata-rata 1 request tiap 2 detik. Kalau caller perlu paginasi banyak halaman untuk 1 date range (mis. hasil `hasMore: true` berkali-kali karena volume submission tinggi), ini jauh lebih longgar dibanding opsi 6/menit sebelumnya — 10 halaman ≈ 20 detik, cukup nyaman untuk bulk backfill/catch-up juga.

Response contract saat limit terlampaui:
- HTTP `429 Too Many Requests`
- Header `Retry-After: <detik>`
- Body pakai format error response standar (lihat [Format Error Response](#format-error-response)), `code: RATE_LIMITED`

Header informational di setiap response (termasuk yang sukses), best practice supaya caller bisa self-throttle sebelum kena limit:
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 22
X-RateLimit-Reset: 1720598400
```

## Format Error Response

Rekomendasi: envelope konsisten dengan `code` machine-readable (jangan cuma andalkan HTTP status untuk branching) + `message` human-readable untuk debugging:

```json
{
  "error": {
    "code": "DATE_RANGE_TOO_LARGE",
    "message": "Date range exceeds maximum of 7 days",
    "details": null
  }
}
```

`details` nullable — dipakai untuk kasus validasi dengan lebih dari satu field bermasalah, bentuknya array of `{field, reason}`.

| HTTP Status | `code` | Kapan |
|---|---|---|
| 400 | `INVALID_REQUEST` | Parameter malformed (mis. format tanggal salah, `siteCode` bukan string) |
| 400 | `DATE_RANGE_TOO_LARGE` | `dateTo - dateFrom` > 7 hari |
| 400 | `INVALID_PAGE_SIZE` | `pageSize` > 100 |
| 401 | `UNAUTHORIZED` | Token tidak ada / invalid / expired |
| 403 | `FORBIDDEN` | Client valid tapi tidak punya akses ke resource yang diminta |
| 429 | `RATE_LIMITED` | Lihat [Rate Limiting](#rate-limiting) |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

## Filter Tambahan — Site & Equipment Number

Selain date range (wajib), endpoint juga terima filter opsional, combinable, di-AND-kan dengan date range:

| Parameter | Sumber SQL | Keterangan |
|---|---|---|
| `siteCode` | `WorkOrder.SiteCode` | Lihat [schema WorkOrder](form-submission.md#schema-tabel-workorder) |
| `equipmentNumber` | `WorkOrder.AssetNumber` | Sumber asli `DPEquipment.Equipment` |

Join path baru: `FormSubmission.TaskId → Task.Id`, `Task.WorkOrderId → WorkOrder.Id` — tambahan dari join path yang sudah ada (`Task → TaskPersonalized`). Kedua kolom **bukan** hasil agregasi (nilainya konstan per `WorkOrder`, sama untuk semua row `TaskPersonalized` dalam grup yang sama), jadi difilter di `WHERE`, bukan `HAVING` — lihat query lengkap di [Sumber Data](#sumber-data--sql--cosmos).

**Kedua field juga ditambahkan ke response payload** (`siteCode`, `equipmentNumber` di level `submissions[]`, lihat [Skema Response](#skema-response) dan [Mapping Field](#mapping-field-raw-query-result--api-field)) — bukan cuma jadi parameter filter. Alasannya: tanpa filter dipakai, satu response bisa berisi campuran banyak site/equipment; caller butuh cara correlate tiap submission ke site/equipment-nya tanpa query balik ke sistem lain. Field ini juga lebih reliable dibanding jawaban "Site"/"Kode Unit" yang ada di tab General (nilai itu isian bebas/dropdown dari inspector di form, bisa typo atau tidak sinkron — `siteCode`/`equipmentNumber` di level submission datang langsung dari `WorkOrder`, sumber yang sama dipakai untuk penjadwalan kerja).
