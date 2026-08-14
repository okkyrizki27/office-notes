# Form Submission — External API Integration Design (awalnya "Form IIR")

*Last updated: 2026-08-14*

*Nama endpoint & dokumen digeneralisasi 2026-08-14 — awalnya khusus IIR (`/api/v1/iir-form-submissions`), sekarang lintas semua kategori `BusinessOperationalForm` (`/api/v1/form-submissions`), IIR jadi kasus pemakaian awal/pendorong desain. Lihat [Konteks](#konteks) dan Keputusan Desain #25.*

*Status: Draft — proposal, belum diimplementasi*

---

## Konteks

Rencana expose data form submission ke sistem eksternal via pull endpoint. Endpoint mengembalikan **banyak `formSubmission`** sekaligus, di-filter berdasarkan date range dengan **cap maksimal 7 hari**. Kasus pemakaian awal/pendorong desain ini adalah **IIR**, tapi endpoint-nya **digeneralisasi untuk seluruh kategori `BusinessOperationalForm`**, bukan di-hardcode cuma untuk IIR — lihat revisi di bawah.

**🚩 Direvisi (2026-08-14) — "IIR" bukan satu `formCode` tunggal, dan endpoint ini digeneralisasi jadi lintas-kategori.** Desain sebelumnya (dan seluruh contoh SQL/perhitungan di dokumen ini) diasumsikan cuma `FORM394`. Ternyata form dikategorikan di tabel `[cst-iams-sqldb-maintenance-execution].[BusinessOperationalForm]`, kolom `SubGroup` — **IIR cuma salah satu nilai `SubGroup`**, bukan satu-satunya. Dari 4 sample yang baru ditambahkan sudah ketemu minimal 2 formCode berbeda yang sama-sama `SubGroup = 'IIR'` (`FORM385` — varian "General", dan `FORM394` — varian "Grader"); kemungkinan ada lebih banyak lagi yang belum di-sample, dan kemungkinan ada `SubGroup` lain di luar IIR yang bisa dilayani endpoint yang sama.

**✅ Diputuskan (2026-08-14) — endpoint dibuat generik lintas `SubGroup`, bukan cuma IIR:**
- **Response** menyertakan field baru `formSubGroup` (dari `BusinessOperationalForm.SubGroup`) per submission — lihat [Skema Response](#skema-response).
- **Request WAJIB menyertakan `formSubGroup` dan `siteCode`, masing-masing satu nilai saja** (bukan opsional, bukan list/multi-value), sejajar dengan date range — lihat [HTTP Method & Endpoint](#http-method--endpoint). Endpoint **tidak** punya mode "semua kategori sekaligus" atau "semua site sekaligus" — tiap request harus eksplisit scope ke satu kategori & satu site.
- **`equipmentNumber` — satu-satunya yang opsional, dan boleh lebih dari satu nilai** (list, mis. `equipmentNumber=HDCT73112,HDCT73113`) — kosong/tidak diisi berarti **semua equipment** di site & kategori yang diminta, diisi berarti narrowing ke equipment-equipment tersebut saja (Keputusan #11 direvisi).
- **Tujuannya**: kalau ada kategori form baru ditambahkan ke `BusinessOperationalForm` di masa depan, sistem eksternal tinggal ganti nilai `formSubGroup=<kategori-baru>` di request mereka — **tidak perlu perubahan endpoint/kode apapun** di sisi Digiman+, karena filter-nya dinamis berdasarkan data (`SubGroup` di tabel), bukan whitelist yang di-hardcode.
- **Kenapa wajib & single-value (bukan opsional/multi)**: mencegah satu request tanpa sadar menarik campuran banyak kategori form sekaligus (yang secara struktur/konten bisa sangat berbeda antar kategori — tab/section/element per kategori form tidak dijamin sama), dan membuat tiap integrasi eksternal eksplisit scope ke kategori yang memang jadi tanggung jawabnya.
- **Batasan cakupan yang tetap berlaku**: endpoint ini tetap khusus form bertipe `FT_BusinessOperationalForm` (form self-service di menu Form Submission mobile, satu-satunya yang punya baris di `BusinessOperationalForm` — lihat [form-builder.md](form-builder.md#karakteristik)) — **bukan** generalisasi ke seluruh form Digiman+. Form bertipe `FT_MaintenanceForm` (Inspection, PM Shutdown, BD Corrective) pakai mekanisme Bank Task yang berbeda sama sekali dan **tidak** masuk cakupan endpoint ini, generik atau tidak.
- Perhitungan worst-case rate limit foto (lihat [Endpoint — Photo Download](#endpoint--photo-download)) idealnya berbasis jumlah task **terbanyak di antara semua varian form**, tapi endpoint ini **sengaja tidak meng-enumerasi/melacak daftar formCode per kategori** (lihat [Keputusan #26](#keputusan-desain-sudah-dikonfirmasi) dan [Open Item #6](#6--resolved--join-key-ke-businessoperationalform-terkonfirmasi-dan-daftar-lengkap-formcode-per-varian-sengaja-tidak-di-enumerasi)) — basis rate limit tetap dari sample yang tersedia sebagai estimasi guard rail, bukan hasil enumerasi lengkap.

Data source: Cosmos `MaintenanceExecution` → `FormSubmissionStructure`, hasil query di [form-submission.md](form-submission.md#contoh-query--ambil-jawaban-user-dari-formsubmissionstructure) (query tab spesifik + tab general), digabung dengan `formName` dari SQL `cst-iams-sqldb-maintenance-execution` (lihat [Sumber Data](#sumber-data--sql--cosmos) di bawah).

## HTTP Method & Endpoint

**✅ Dikonfirmasi — dua endpoint dengan peruntukan berbeda**, bukan digabung jadi satu:

| Endpoint | Method | Peruntukan |
|---|---|---|
| `/api/v1/form-submissions` | `GET` | **List/polling** — endpoint utama, filter date range + `formSubGroup` (satu nilai) + `siteCode` (satu nilai) — ketiganya **wajib** — + `equipmentNumber` (opsional, boleh banyak nilai) + pagination. Ini yang dipakai sistem eksternal untuk polling berkala |
| `/api/v1/form-submissions/{formSubmissionId}` | `GET` | **Single-fetch by ID** — ambil 1 submission spesifik. Peruntukannya beda dari list: dipakai untuk re-fetch detail setelah dapat `formSubmissionId` dari hasil list (mis. retry granular kalau 1 submission gagal diproses di sisi eksternal), atau lookup manual/support/debugging — bukan untuk polling |

**✅ Diputuskan (2026-08-14) — endpoint & naming digeneralisasi, tidak lagi IIR-spesifik.** Awalnya didesain khusus untuk IIR (`/api/v1/iir-form-submissions`), tapi karena IIR ternyata cuma satu dari beberapa kategori `BusinessOperationalForm` (lihat [Konteks](#konteks)), endpoint (termasuk endpoint foto) di-generalisasi jadi `/api/v1/form-submissions` — lintas kategori, dengan `formSubGroup` sebagai filter dinamis. Lihat Keputusan Desain #25.

**✅ Disetujui — Method: `GET` untuk keduanya** — kedua endpoint sifatnya *read-only* dan *idempotent* (tidak membuat/mengubah state), jadi `GET` adalah pilihan paling idiomatik. `POST` biasanya dipakai kalau body request kompleks/butuh disembunyikan dari log/URL (mis. mengandung data sensitif) atau melebihi batas panjang URL — tidak berlaku di sini karena filter cuma date range + 2 string opsional + pagination, semuanya aman sebagai query string. `GET` juga lebih gampang di-cache, di-bookmark, dan di-debug (bisa langsung dites lewat browser/curl tanpa body).

Contoh:
```
GET /api/v1/form-submissions?dateFrom=2026-07-01T00:00:00Z&dateTo=2026-07-07T23:59:59Z&formSubGroup=IIR&siteCode=LAT&page=1&pageSize=20   ← equipmentNumber kosong = semua equipment di site LAT
GET /api/v1/form-submissions?dateFrom=2026-07-01T00:00:00Z&dateTo=2026-07-07T23:59:59Z&formSubGroup=IIR&siteCode=LAT&equipmentNumber=HDCT73112,HDCT73113&page=1&pageSize=20   ← narrowing ke 2 equipment
GET /api/v1/form-submissions?dateFrom=2026-07-01T00:00:00Z&dateTo=2026-07-07T23:59:59Z&page=1&pageSize=20   ← ❌ invalid, formSubGroup & siteCode wajib diisi
GET /api/v1/form-submissions/4b604512-b409-4a19-ba79-9ac5ab68e16c
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

## Endpoint — Photo Download

**✅ Dikonfirmasi (2026-08-04)** — proxy endpoint terpisah untuk serve konten foto, bukan expose blob path langsung maupun SAS token. *(Menggantikan Open Item #4 lama — lihat riwayat diskusi di situ.)*

```
GET /api/v1/form-submissions/photos/{photoGuid}
X-Api-Key: <api_key>
```

Auth pakai API Key + IP whitelist yang sama dengan endpoint data (lihat [Autentikasi & Otorisasi](#autentikasi--otorisasi)) — tidak ada mekanisme auth kedua terpisah.

### Kenapa Proxy, Bukan SAS Token

Blob penyimpanan foto **tidak bisa diakses langsung dari luar Digiman+** (dikonfirmasi user, 2026-08-04) — akses hanya lewat sistem Digiman+ sendiri (web/mobile), konsisten dengan pola gambar guideline yang di-host di Azure Blob Storage privat ([`form-builder.md`](form-builder.md#karakteristik)). Dua opsi dipertimbangkan:

- **SAS token per-URL** — **ditolak**. Masalahnya soal timing: endpoint data didesain untuk polling async (Keputusan #1, bukan real-time), jadi sistem eksternal belum tentu langsung fetch foto begitu dapat response metadata (bisa jadi backfill/catch-up belakangan). SAS TTL pendek berisiko expired sebelum sempat dipakai; TTL panjang memperbesar window kebocoran kalau URL ter-log/screenshot di sisi eksternal.
- **Proxy endpoint (dipilih)** — reuse API Key + IP whitelist yang sama dengan endpoint data (satu mekanisme auth, satu titik revoke), blob tetap fully private (tidak ada perubahan access policy Azure sama sekali), dan tidak terikat masalah timing SAS.

### Response — Binary, Bukan Base64

```
200 OK
Content-Type: image/jpeg   (sesuai tipe file asli)
Content-Length: <ukuran file>
Cache-Control: private, max-age=31536000, immutable

<raw bytes>
```

Base64 sengaja tidak dipakai — base64 cuma masuk akal kalau foto harus nempel langsung di JSON response list/detail (menaikkan ukuran payload ~33%, bertentangan dengan alasan pagination endpoint list yang sudah ada di Keputusan #2). Karena ini endpoint terpisah, binary + `Content-Type` yang benar lebih efisien: bisa di-cache, mendukung `Range` request, dan langsung bisa dibuka/didownload tanpa decode di sisi eksternal.

Backend **stream** dari Blob Storage ke response (bukan buffer seluruh file ke memory) — penting untuk foto berukuran besar supaya tidak membebani memory service per-request.

`Cache-Control: private, max-age=31536000, immutable` (1 tahun) — foto evidence bersifat **immutable** (satu `photoGuid` = satu foto yang tidak pernah berubah isinya begitu dibuat), jadi aman TTL panjang tanpa perlu revalidasi (`ETag`). `private` karena response butuh auth — cache berlaku buat sistem eksternal itu sendiri, bukan shared cache/CDN publik.

### Resolusi `photoGuid`

Logic sama dengan yang sudah didokumentasikan di [Resolusi Blob URL untuk Foto](#resolusi-blob-url-untuk-foto) — backend coba resolve ke `TaskPersonalizedEvidence.ReferenceId` dulu, fallback ke `TaskPersonalized.ReferenceId`/`Task.ReferenceId` (Keputusan #5/#13, tergantung status rollout PM Shutdown Service Package Phase 1). Filter `IsActive = 1` tetap berlaku (Keputusan #14). Bedanya dari desain lama: hasil resolusi (`ContentAddress`) dipakai backend untuk fetch & stream isi file, **bukan** dikirim sebagai string ke response JSON endpoint data.

### Error

```json
404 Not Found
{ "error": { "code": "PHOTO_NOT_FOUND", "message": "...", "details": null } }
```

Tambahan baris di [Format Error Response](#format-error-response) — dipakai kalau `photoGuid` tidak match apapun di `TaskPersonalizedEvidence`/`TaskPersonalized`/`Task`. Beda dari fallback `url: null` di endpoint data (yang tetap `200`) — di endpoint proxy ini, foto yang benar-benar tidak ada memang harus `404` karena tidak ada isi untuk di-stream.

### Rate Limit — Terpisah dari Endpoint Data

**✅ Direvisi (2026-08-14) — 1.850 req/menit, 155.000 req/hari** (sliding window, algoritma sama dengan [Rate Limiting](#rate-limiting) endpoint data) — sengaja dibuat terpisah dari limit endpoint data (30/menit, 2.500/hari) karena karakteristik beban jauh beda: fetch foto adalah operasi ringan (resolve 1 `ReferenceId` + stream, bukan JOIN 4 tabel + aggregation), dan foto punya efek multiplier tinggi per submission — 1 request data bisa butuh puluhan-ratusan request foto susulan.

**Perhitungan awal (worst-case-literal, dikonfirmasi user 2026-08-04) — basis lama, sudah stale:**
- Tab spesifik "Inspection" form `FORM394` diasumsikan punya **113 form task** (`BANKTASK`, basis dari [`IIR-Grader.json`](examples/IIR-Grader.json) versi 6 — sample lama, sudah digantikan sample real terbaru).
- Asumsi worst-case: semua task punya evidence, evidence maksimal 3 foto → 113 × 3 = 339 foto.
- Ditambah 5 foto section `PHOTOLIST` (General tab) + 1 foto Machine SMU (`CAMERACAPTURE`) → total 345 foto/submission.
- Basis per-menit: pageSize *default* (20) × 345 = 6.900 foto/halaman, target waktu hydrate ~5 menit → 1.380/menit → dibulatkan 1.400/menit.
- Basis per-hari: rasio yang sama dengan endpoint data (2.500 ÷ 30 ≈ 83x) → 1.400 × 83 ≈ 116.200 → dibulatkan 120.000/hari.

**✅ Dihitung ulang (2026-08-14) — basis 113 diganti angka real + buffer 30% untuk varian belum diketahui:**
- Sample real menunjukkan `FORM394` versi 16 (varian "Grader") punya **116** `BANKTASK`/`TAKEPHOTO` — lebih tinggi dari `FORM385` (varian "General", **111**), jadi dipakai sebagai basis worst-case di antara 2 varian yang diketahui.
- 116 × 3 foto = 348 foto, + 5 foto `PHOTOLIST` (General tab) + 1 foto Machine SMU + **1 foto signature** ("Digital Signature by Inspector", sebelumnya belum terhitung — lihat [Open Item #5](#5--resolved--flat-photolist-di-tab-inspection-signature-ditangani-sama-seperti-flat-elements-tab-general)) → **355 foto/submission** (worst-case-literal dari data yang diketahui).
- **Buffer 30%** ditambahkan di atas 355 (355 × 1,3 ≈ 461,5) → dibulatkan ke **460 foto/submission** — bukan angka sembarangan, tujuannya nutup risiko dari [Keputusan #26](#keputusan-desain-sudah-dikonfirmasi)/[Open Item #6](#6--resolved--join-key-ke-businessoperationalform-terkonfirmasi-dan-daftar-lengkap-formcode-per-varian-sengaja-tidak-di-enumerasi): endpoint ini sengaja **tidak** meng-enumerasi semua formCode per `SubGroup`, jadi selalu ada kemungkinan varian lain (IIR yang belum di-sample, atau kategori `SubGroup` lain di masa depan) yang task-nya lebih banyak dari 116 — buffer lebih besar (30%, direvisi dari ~13% sebelumnya) dipilih supaya limit lebih longgar menghadapi varian baru yang cukup jauh lebih besar dari 116, bukan cuma sedikit lebih besar.
- Basis per-menit: pageSize *default* (20) × 460 = 9.200 foto/halaman, target waktu hydrate ~5 menit → 1.840/menit → dibulatkan **1.850/menit**.
- Basis per-hari: rasio yang sama (2.500 ÷ 30 ≈ 83x) → 1.850 × 83 ≈ 154.167 → dibulatkan **155.000/hari**.

**🚩 Catatan penting (tetap berlaku):** ini masih worst-case-literal + buffer, bukan angka dari volume real — kemungkinan besar volume real jauh lebih rendah (biasanya cuma item defect yang di-foto, item "OK" sering dilewat tanpa evidence). Limit ini fungsinya sebagai guard rail (konsisten dengan filosofi limit endpoint data di Keputusan #9), bukan target throughput yang harus selalu dikejar. **Perlu direvisit setelah ada data volume real pasca-launch.**

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
| `photos[].url` | Diisi URL ke [Endpoint — Photo Download](#endpoint--photo-download) (`.../photos/{photoGuid}`), **bukan** `ContentAddress` mentah. Resolusi `ContentAddress`/`MachineSMUAddress` tetap terjadi lewat query di bawah, tapi hasilnya dipakai backend untuk stream isi file di endpoint proxy — tidak pernah dikirim sebagai string ke response JSON | Lihat [Resolusi Blob URL untuk Foto](#resolusi-blob-url-untuk-foto) di bawah dan [Endpoint — Photo Download](#endpoint--photo-download) |

### Resolusi Blob URL untuk Foto

> ✅ **Resolved (2026-08-04)** — sebelumnya section ini flag risiko `ContentAddress` tidak bisa diakses langsung oleh sistem eksternal (dulu Open Item #4). Sudah diputuskan: nilai `ContentAddress`/`MachineSMUAddress` hasil query di bawah **tidak pernah dikirim langsung ke sistem eksternal** — dipakai backend secara internal untuk resolve & stream isi file lewat [Endpoint — Photo Download](#endpoint--photo-download) yang baru. Sistem eksternal cuma menerima URL ke endpoint proxy itu (berisi `photoGuid`), bukan path Blob Storage mentah.

`photoGuid` yang didapat dari Cosmos (dari `TAKEPHOTO`, `CAMERACAPTURE`, maupun `PHOTOLIST` — ketiganya dari field `value`, lihat koreksi di [Open Item #1](#1--belum-resolved-dibuka-ulang-2026-08-14--photolistvalue-di-data-real-masih-placeholder-bukan-guid)) **bukan URL langsung** — cuma GUID. Untuk resolve jadi blob URL, join ke SQL `[dbo].[TaskPersonalizedEvidence]` berdasarkan `ReferenceId = photoGuid`:

```sql
SELECT 
    tpe.ReferenceId AS photoGuid,
    tpe.ContentAddress AS url
FROM [dbo].[TaskPersonalizedEvidence] tpe
WHERE tpe.ReferenceId IN (@photoGuid1, @photoGuid2, ...)
  AND tpe.IsActive = 1
```

Batch semua `photoGuid` yang terkumpul dari satu halaman hasil Cosmos jadi satu query `IN (...)` — bukan N+1 per foto.

**🚩 Dibuka ulang (2026-08-14) — `PHOTOLIST.value` (target-nya tetap dibaca dari sini, bukan `valueCaption`) belum terbukti reliable berisi GUID di data real**, meski itu tetap arah desain yang benar begitu data matang — lihat status terbaru & evidence di [Open Item #1](#1--belum-resolved-dibuka-ulang-2026-08-14--photolistvalue-di-data-real-masih-placeholder-bukan-guid) di bawah. `valueCaption` yang berisi device file path adalah bug terpisah ([IAMS30-4485](https://bukittechnology.atlassian.net/browse/IAMS30-4485)), tetap tidak dipakai untuk resolusi foto di desain ini — cuma sekarang `value` juga belum bisa diandalkan sampai diverifikasi ulang.

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
    bof.SubGroup AS formSubGroup,
    wo.SiteCode AS siteCode,
    wo.AssetNumber AS equipmentNumber,
    MAX(tp.ModifiedAt) AS submittedAt,
    MAX(tp.LastSyncedModifiedAt) AS syncAt
FROM [dbo].[FormSubmission] fs
JOIN [dbo].[Task] t ON fs.TaskId = t.Id
JOIN [dbo].[WorkOrder] wo ON t.WorkOrderId = wo.Id
JOIN [dbo].[TaskPersonalized] tp ON tp.TaskId = t.Id
JOIN [dbo].[BusinessOperationalForm] bof ON bof.FormCode = fs.FormCode
WHERE fs.IsActive = 1
  AND t.IsActive = 1
  AND wo.IsActive = 1
  AND tp.IsActive = 1
  AND bof.IsActive = 1
  AND bof.SubGroup = @formSubGroup
  AND wo.SiteCode = @siteCode
  AND (@equipmentNumberList IS NULL OR wo.AssetNumber IN (SELECT value FROM STRING_SPLIT(@equipmentNumberList, ',')))
GROUP BY fs.Id, t.Name, bof.SubGroup, wo.SiteCode, wo.AssetNumber
HAVING MAX(tp.LastSyncedModifiedAt) >= @dateFrom
   AND MAX(tp.LastSyncedModifiedAt) < @dateTo
```

**✅ Diputuskan (2026-08-14) — `bof.SubGroup = 'IIR'` yang tadinya hardcode diganti jadi parameter wajib `@formSubGroup`** (satu nilai, bukan opsional, bukan list) supaya endpoint generik lintas `BusinessOperationalForm`, bukan cuma IIR — lihat [Konteks](#konteks) dan Keputusan Desain #25. `bof.SubGroup` juga di-`SELECT` sebagai `formSubGroup` untuk response payload (lihat [Skema Response](#skema-response)).

**✅ Direvisi (2026-08-14) — `@siteCode` juga jadi wajib, satu nilai** (`wo.SiteCode = @siteCode`, tanpa `IS NULL OR`), beda dari keputusan awal (Keputusan #11) yang tadinya opsional. `formSubGroup` dan `siteCode` sekarang berperilaku sama: keduanya wajib, keduanya cuma terima satu nilai.

**✅ Direvisi (2026-08-14) — `equipmentNumber` tetap opsional, tapi sekarang boleh lebih dari satu nilai** (list, `@equipmentNumberList` = string comma-separated dari request, mis. `"HDCT73112,HDCT73113"`, di-pecah pakai `STRING_SPLIT`). Kosong/`NULL` = tidak ada filter (semua equipment di site & kategori yang diminta); diisi = `IN (...)`, bukan cuma `=` satu nilai seperti sebelumnya. Beda perlakuan dari `formSubGroup`/`siteCode` yang wajib+single — `equipmentNumber` tetap murni narrowing filter opsional, cuma sekarang bisa narrowing ke beberapa equipment sekaligus dalam satu request (mis. caller mau backfill beberapa unit spesifik tanpa harus request terpisah per unit).

**Tidak perlu join lintas service ke `maintenance-strategy`** — join di atas pakai `bof.FormCode = fs.FormCode`, dan `FormSubmission.FormCode` (alias `fs`) sudah ada langsung sebagai kolom plain string di `maintenance-execution` (lihat [schema `FormSubmission`](form-submission.md#schema-tabel-formsubmission)), bukan cross-service reference. **Koreksi (2026-08-14):** draft sebelumnya sempat salah tulis kolom ini sebagai `t.FormCode` (di tabel `Task`) dan keliru mengaitkannya dengan `Task.FormId` yang cross-service ke `maintenance-strategy` — setelah dicek ulang ke schema, **`Task` sama sekali tidak punya kolom `FormId`/`FormCode`**; yang punya `FormId` (cross-service) *dan* `FormCode` (lokal, plain) itu `FormSubmission`, bukan `Task`. Karena join di sini pakai `FormCode` (bukan `FormId`), seluruh isu cross-service ke `maintenance-strategy` tidak relevan untuk endpoint ini — `maintenance-execution` saja cukup.

**✅ Join key & database sudah terkonfirmasi lewat DDL asli** — [`database/maintenance-execution-schema.md`](../database/maintenance-execution-schema.md#businessoperationalform-master-data) (*"Sumber: DDL script asli (`maintenance-execution-script.sql`)... skema real, bukan document-derived"*, disimpan 15 Jul 2026) mencantumkan `BusinessOperationalForm` lengkap dengan kolom `Code, Icon, Name, FormCode (varchar(64), not null), Sequence, Group, SubGroup, WorkflowCode, IsActive, ...` — **persis** dengan nama kolom yang dipakai di query (`FormCode`, `SubGroup`, `IsActive`), dan tabel ini memang bagian dari schema `maintenance-execution` (nama file dokumennya sendiri), jadi join lokal di atas valid, bukan cross-database. Tidak perlu tanya ulang ke tim backend untuk hal ini — sudah ada di DDL yang sudah didokumentasikan.

Filter date range pakai `HAVING` (bukan `WHERE`) karena kriterianya adalah hasil agregasi (`MAX(LastSyncedModifiedAt)`) per `formSubmissionId`, bukan per row mentah — `WHERE` akan filter row sebelum agregasi dan menghasilkan semantik yang salah (bisa exclude submission yang punya salah satu row TaskPersonalized di luar range padahal `MAX`-nya di dalam range). `siteCode`/`equipmentNumber` sebaliknya **bukan** hasil agregasi (nilainya konstan per `WorkOrder`, sama untuk semua row `TaskPersonalized` dalam grup yang sama) — jadi aman difilter di `WHERE`, tidak perlu `HAVING`.

`wo.SiteCode` dan `wo.AssetNumber` didapat dari join tambahan `Task.WorkOrderId → WorkOrder.Id` (lihat [schema WorkOrder](form-submission.md#schema-tabel-workorder)) — join path baru di luar yang sudah ada (`Task → TaskPersonalized`). Lihat [Filter Tambahan](#filter-tambahan--site-equipment-number--form-subgroup) untuk detail kenapa filter ini ditambahkan dan kenapa kedua kolom ini juga di-include di response payload, bukan cuma jadi parameter filter.

Query metadata single-submission di atas ([Resolusi Blob URL untuk Foto](#resolusi-blob-url-untuk-foto)) juga perlu update join `WorkOrder` yang sama kalau `siteCode`/`equipmentNumber` mau muncul di response single-fetch — lihat versi update di bawah:

```sql
SELECT 
    fs.Id AS formSubmissionId,
    t.Name AS formName,
    bof.SubGroup AS formSubGroup,
    wo.SiteCode AS siteCode,
    wo.AssetNumber AS equipmentNumber,
    MAX(tp.ModifiedAt) AS submittedAt,
    MAX(tp.LastSyncedModifiedAt) AS syncAt
FROM [dbo].[FormSubmission] fs
JOIN [dbo].[Task] t ON fs.TaskId = t.Id
JOIN [dbo].[WorkOrder] wo ON t.WorkOrderId = wo.Id
JOIN [dbo].[TaskPersonalized] tp ON tp.TaskId = t.Id
JOIN [dbo].[BusinessOperationalForm] bof ON bof.FormCode = fs.FormCode
WHERE fs.Id = @formSubmissionId
  AND fs.IsActive = 1
  AND t.IsActive = 1
  AND wo.IsActive = 1
  AND tp.IsActive = 1
  AND bof.IsActive = 1
GROUP BY fs.Id, t.Name, bof.SubGroup, wo.SiteCode, wo.AssetNumber
```

**Tidak ada filter `SubGroup` di query single-fetch** — beda dari query list, di sini caller sudah tahu `formSubmissionId` spesifik (dari hasil list sebelumnya atau lookup manual), jadi tidak perlu narrowing kategori lagi. Join ke `BusinessOperationalForm` tetap ada, cuma untuk populate `formSubGroup` di response, bukan untuk filtering.

### Filter `IsActive`

Semua query SQL di atas (resolusi foto maupun metadata) sudah ditambahkan filter `IsActive = 1` di tiap tabel yang dijoin (`FormSubmission`, `Task`, `WorkOrder`, `TaskPersonalized`, `TaskPersonalizedEvidence`, `BusinessOperationalForm`) — supaya record yang sudah di-soft-delete tidak ikut ter-expose ke sistem eksternal.

**🚩 Flag ke developer/tim backend — perlu dikonfirmasi apakah mekanisme `IsActive` ini benar-benar berjalan konsisten di live data saat ini**, sebelum filter ini diandalkan sebagai satu-satunya penjaga soft-delete. Yang perlu dicek:
- Apakah semua path soft-delete (UI, API internal, batch job, dll) benar-benar konsisten set `IsActive = 0`, atau ada jalur yang masih hard-delete/lupa update flag ini?
- Apakah ada kasus row dengan `IsActive = 0` yang justru **masih perlu muncul** di endpoint ini (mis. submission yang di-nonaktifkan tapi historinya tetap relevan buat pihak eksternal)? Kalau iya, filter ini perlu di-refine, bukan blanket `= 1` di semua tabel.
- Konsistensi antar tabel — kalau `FormSubmission.IsActive = 0` tapi `TaskPersonalized.IsActive = 1` (atau kombinasi tidak konsisten lainnya), row mana yang jadi acuan?

Kalau ternyata `IsActive` tidak reliable/tidak konsisten dijaga di seluruh alur, filter ini berisiko **exclude data yang seharusnya valid** (false negative) — jadi perlu divalidasi dulu, bukan diasumsikan aman cuma karena kolomnya ada di schema.

### Fallback Kalau Resolusi Foto Gagal

**✅ Disetujui — kalau `photoGuid` tidak match apapun** di `TaskPersonalizedEvidence`/`TaskPersonalized`/`Task` (mis. karena data korup, race condition, atau data lama dari sebelum [IAMS30-4485](https://bukittechnology.atlassian.net/browse/IAMS30-4485) — kasusnya soal `valueCaption`, bukan `value` yang dipakai resolusi — tapi tetap perlu fallback untuk kasus lain), entry foto **tetap muncul di `photos[]`, tapi `url: null`** — bukan di-drop diam-diam dari array.

Alasan:
- **Drop diam-diam menyembunyikan masalah** — caller tidak akan tahu ada foto yang seharusnya ada tapi hilang, jumlah `photos[]` jadi tidak match ekspektasi tanpa penjelasan
- **`url: null` konsisten dengan pola "jujur representasikan ketiadaan"** yang sudah dipakai di tempat lain di desain ini (mis. `title: null` untuk section tanpa judul)
- Memudahkan **observability** — endpoint bisa log/monitor berapa persen resolusi foto yang gagal per periode, sinyal awal kalau ada masalah data yang lebih luas

## Kenapa Perlu Skema Ter-normalisasi (Bukan Expose Hasil Query Mentah)

Hasil query Cosmos untuk tab **General** dan tab **Inspection/spesifik** punya struktur field yang berbeda secara internal (lihat [form-submission.md](form-submission.md)):

| Field hasil query | Tab General | Tab Spesifik |
|---|---|---|
| `taskCode` | GUID (element instance ID), **beda per submission** (dikonfirmasi 2026-08-14 — dibandingkan langsung dari 2 sample real, elemen yang sama punya `taskCode` berbeda antar form) — **tetap di-include di API**, lihat Keputusan Desain #7 (direvisi) | Business code (mis. `Task1252`), stabil lintas submission karena reuse Bank Task — di-include di API |
| `photoGuid` | 🚩 belum diverifikasi ulang — sebelumnya ditulis `null`/array of `{label, value}` (untuk `PHOTOLIST`, sumbernya diklaim `valueCaption`) atau array 1 GUID (untuk `CAMERACAPTURE`), tapi bentuk untuk `PHOTOLIST` perlu dikonfirmasi lagi karena sumbernya sekarang `value`, bukan `valueCaption` (lihat [Open Item #1](#1--belum-resolved-dibuka-ulang-2026-08-14--photolistvalue-di-data-real-masih-placeholder-bukan-guid)) | Array of GUID string, atau `[]` |
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
      formSubmissionId, formCode, formVersion, formName, formSubGroup,
      siteCode, equipmentNumber,
      submittedBy, submittedAt, syncAt,
      tabs: [
        {
          title,
          sections: [
            {
              title,
              answers: [
                { taskCode, label, value, lastUpdatedBy, lastUpdatedAt, photos: [{label, url}], number?, remark? }
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
| SQL `BusinessOperationalForm.SubGroup` (join by `FormCode`) | `formSubGroup` | **Field baru (2026-08-14)** — kategori form (mis. `"IIR"`). Selalu di-include di response, terlepas dari apakah caller filter pakai `formSubGroup` atau tidak — lihat [Filter Tambahan](#filter-tambahan--site-equipment-number--form-subgroup) dan Keputusan Desain #25 |
| SQL `WorkOrder.SiteCode` (join `Task.WorkOrderId → WorkOrder.Id`) | `siteCode` | **Field baru** — lihat [Filter Tambahan](#filter-tambahan--site-equipment-number--form-subgroup) |
| SQL `WorkOrder.AssetNumber` (join `Task.WorkOrderId → WorkOrder.Id`) | `equipmentNumber` | **Field baru** — sumber asli `DPEquipment.Equipment`, lihat [Filter Tambahan](#filter-tambahan--site-equipment-number--form-subgroup). Beda dengan jawaban "Kode Unit"/"Site" di tab General (isian inspector, bisa typo/beda) — field ini datang dari `WorkOrder`, jadi lebih reliable untuk filtering/correlation |
| SQL `TaskPersonalized.ModifiedAt` | `submittedAt` | Diganti dari sumber Cosmos ke SQL — lihat [Sumber Data](#sumber-data--sql--cosmos) |
| SQL `TaskPersonalized.LastSyncedModifiedAt` | `syncAt` | **Field baru** — perlu verifikasi kolom ini benar ada di live schema (lihat catatan ⚠ di atas) |
| `taskDesc` | `label` | Disamakan namanya lintas tab. **Untuk `PHOTOLIST`, `e.label` selalu `""`** (dikonfirmasi di semua kemunculan real: "Foto Kondisi Fisik Equipment" maupun "Digital Signature by Inspector") — lihat aturan derivasi label di Keputusan Desain #27, bukan dibiarkan kosong |
| `taskValue` | `value` | Disamakan namanya lintas tab. **Untuk elemen yang isinya murni foto** (`CAMERACAPTURE` mis. "Photo Machine SMU", dan `PHOTOLIST` mis. "Foto Kondisi Fisik Equipment"), `value` selalu **`null`** — terlepas dari jumlah foto (lihat Keputusan Desain #12). GUID tetap bisa didapat dari `photos[].url`. **`TAKEPHOTO` yang nempel di row checklist** (tab spesifik) tidak kena aturan ini — `value`-nya tetap jawaban `DROPDOWN` (mis. "Ok"), foto cuma lampiran tambahan |
| `taskCode` | `taskCode` | **Di-include untuk kedua tab** (direvisi 2026-08-14, lihat Keputusan Desain #7) — konsisten, tidak ada exception per tab. Semantiknya beda: tab spesifik = business code stabil (`Task1252`), tab General = GUID internal yang beda tiap submission (tidak berguna untuk korelasi lintas submission, tapi tidak masalah di-expose) |
| `lastUpdatedByUserCode` | `lastUpdatedBy` | Email user yang terakhir mengubah jawaban (bukan display name `lastUpdatedBy` di raw). PII — disetujui di-share, lihat Keputusan Desain #6 |
| `lastUpdatedDate` | `lastUpdatedAt` | Timestamp (ISO-8601 UTC) terakhir jawaban diubah. Diambil per-answer; kalau satu `taskCode` punya beberapa timestamp (mis. remark/foto di-update belakangan), pakai yang **paling akhir** (max) sebagai "kapan jawaban ini terakhir berubah" |
| `photoGuid` (bentuk tidak konsisten — lihat tabel di atas) | `photos: [{label, url}]` | **Selalu array**, `url` diisi link ke [Endpoint — Photo Download](#endpoint--photo-download) (`.../photos/{photoGuid}`) — bukan `ContentAddress` mentah (lihat [Resolusi Blob URL untuk Foto](#resolusi-blob-url-untuk-foto)) — konsumen API tidak perlu tahu/branch berdasarkan elementCode asal (`TAKEPHOTO`/`CAMERACAPTURE`/`PHOTOLIST`), cukup `GET` URL tersebut dengan API Key yang sama |
| `sectionTitle: ""` | `title: null` | `null` lebih jujur merepresentasikan "tidak ada judul" dibanding string kosong |
| `number` | `number` (nullable, hanya ada di tab spesifik) | Tidak dipaksakan ada di semua row |

## Keputusan Desain (Sudah Dikonfirmasi)

| # | Keputusan | Alasan |
|---|---|---|
| 1 | Date range filter berdasarkan **`syncAt`** (`TaskPersonalized.LastSyncedModifiedAt`) — **bukan** `submittedAt` maupun `createdDate` | Digiman+ **offline-first** — `submittedAt` adalah waktu aksi di device, bisa terjadi saat offline dan baru sync jauh belakangan. Kalau filter pakai `submittedAt`, submission yang selesai offline di hari-1 tapi baru sync di hari-10 berisiko **tidak pernah muncul** kalau sistem eksternal poll per window tanggal berurutan tanpa overlap (window hari 1-7 sudah lewat sebelum sync terjadi, window berikutnya filter dari hari-8 jadi tidak menangkapnya juga). Filter berdasarkan `syncAt` (kapan data benar-benar tersedia di server) menjamin record selalu ketangkap di window manapun yang mencakup waktu sync-nya |
| 2 | Endpoint **pakai pagination** (`page`/`pageSize`), default `pageSize` **20**, max **100** | Volume submission tetap bisa tinggi di periode sibuk (banyak site/banyak form/hari) — cap 7 hari tidak membatasi jumlah row, cuma membatasi rentang waktu. Batas max mencegah caller minta page size tak terbatas dan meniadakan tujuan pagination |
| 3 | `formName` diambil dari join `FormSubmission.TaskId → Task.Id → Task.Name`, **bukan** dari kolom `FormSubmission.FormName` | `FormSubmission.FormName` cuma ada di rencana **PM Shutdown Service Package Phase 1** ([pm-shutdown-data-model.md](../../roadmap/phase1-service-package/pm-shutdown-data-model.md)) — **Phase 1 (Service Package) tersebut belum go-live**, kolom itu belum ada di live schema. `Task.Name` sudah ada dan terisi sekarang |
| 4 | Query metadata (`formName`/`submittedAt`/`syncAt`/`siteCode`/`equipmentNumber`) selalu pakai `MAX()` + `GROUP BY`, **tidak** mengasumsikan 1 `TaskPersonalized` row per `formSubmissionId` | Form IIR secara bisnis memang cuma 1 orang yang submit — tapi query diperlakukan generik seolah bisa N mechanic (schema `TaskPersonalized` mendukung N per Task), supaya tidak perlu diubah kalau nanti form lain/perubahan bisnis membuat multi-mechanic jadi nyata. **`machineSMUPhotoUrl` dikecualikan dari daftar ini** — lihat #5 |
| 5 | ~~`machineSMUPhotoUrl`~~ (nama field draft lama, **sudah tidak ada** di skema final — lihat catatan di kolom Alasan) **tidak lagi** bagian dari query metadata `MAX()`/`GROUP BY` — di-resolve lewat batch query by `ReferenceId = photoGuid` (paralel dengan resolusi foto lain via `TaskPersonalizedEvidence`). **Sebelum PM Shutdown Service Package Phase 1 go-live**: join ke `TaskPersonalized.ReferenceId` + `TaskPersonalized.MachineSMUAddress`. **✅ Dikonfirmasi untuk pasca-rollout Phase 1 tersebut**: join key pindah ke `Task.ReferenceId` + `Task.MachineSMUAddress` — bukan cuma migrasi kolom, tapi migrasi tabel join juga | Revisi dari desain awal: `value` elemen "Photo Machine SMU" di Cosmos ternyata berupa GUID yang match `ReferenceId` — sama polanya dengan `photoGuid` elemen foto lain, bukan field yang butuh join+agregasi terpisah. Ini juga menghilangkan ambiguitas N-mechanic untuk field ini (resolusi by `ReferenceId` spesifik, bukan `MAX()` per `TaskId`). `pm-shutdown-data-model.md` mencantumkan kolom `MachineSMUAddress` pindah dari `TaskPersonalized` ke `Task` sebagai bagian dari PM Shutdown Service Package Phase 1, dan tim mengonfirmasi `Task.ReferenceId` yang jadi join key baru — lihat query pasca-Phase 1 di [Resolusi Blob URL untuk Foto](#resolusi-blob-url-untuk-foto). **Catatan (2026-08-14):** `machineSMUPhotoUrl` di sini nama field draft dari versi desain yang lebih lama, sebelum "Photo Machine SMU" digabung jadi jawaban `CAMERACAPTURE` biasa (`value: null` + `photos[]`, lihat Keputusan #12) — **tidak ada field bernama itu di [Skema Response](#skema-response) final**, disebut di sini murni untuk konteks historis keputusan |
| 6 | PII (`submittedBy`/`lastUpdatedBy` — email) **disetujui untuk di-share** ke sistem eksternal | Pihak eksternal seharusnya sudah tahu NIK dan data karyawan lain di database mereka sendiri — sharing email/identitas ini untuk keperluan reconciliation/matching record, bukan memperkenalkan informasi baru yang belum mereka punya |
| 7 | **✅ Direvisi (2026-08-14)** — `taskCode` **di-include untuk kedua tab**, General maupun spesifik, tanpa exception | Keputusan awal (exclude di tab General) berangkat dari asumsi `taskCode` General tab = GUID internal yang "tidak berguna" — **bukan** soal keamanan/larangan expose GUID (tidak pernah ada concern itu). Dikonfirmasi 2026-08-14 dari 2 sample real (`IIR-General-tab-general-sample.json` vs `IIR-Grader-tab-general-sample.json`): elemen yang identik (elementCode+label sama) punya `taskCode` **berbeda** antar form — jadi memang bukan business key yang stabil/reusable seperti tab spesifik (`Task1252`, hasil reuse Bank Task), cuma random GUID per submission. Tapi karena tidak ada alasan keamanan untuk exclude, dan supaya schema API konsisten (tidak ada field yang exception per tab), diputuskan tetap di-include di kedua tab — konsumen API cukup tahu semantiknya beda (stabil di tab spesifik, tidak stabil di tab General), bukan berarti fieldnya hilang |
| 8 | **✅ Direvisi (2026-08-14)** — Autentikasi pakai **API Key + IP whitelist**, bukan OAuth2 Client Credentials Grant seperti draft awal | Diminta eksplisit — disamakan dengan pola integrasi eksternal lain yang sudah berjalan (mis. SAP), supaya tim ops/support cukup punya satu playbook provisioning/rotasi/monitoring untuk semua integrasi B2B, bukan pola auth baru khusus endpoint ini. Ini juga menjawab open item lama soal identity platform (draft awal masih menimbang perlu-tidaknya bangun OAuth2 provider dari nol). Detail lihat [Autentikasi & Otorisasi](#autentikasi--otorisasi) |
| 9 | Rate limit **per API Key**, **disetujui** 30 req/menit + 2.500 req/hari (sliding window) | Endpoint didesain untuk polling berkala (bukan real-time), limit ini jadi guard rail terhadap bug/retry-loop, bukan pembatas kebutuhan wajar. Lihat [Rate Limiting](#rate-limiting) |
| 10 | Error response pakai envelope `{ error: { code, message, details } }` dengan `code` machine-readable, bukan cuma andalkan HTTP status | Konsumen API butuh cara program-friendly untuk branch per jenis error (mis. `DATE_RANGE_TOO_LARGE` vs `RATE_LIMITED`) tanpa parsing `message` yang human-readable. Lihat [Format Error Response](#format-error-response) |
| 11 | Filter tambahan **`siteCode`** (✅ direvisi 2026-08-14 — **wajib, satu nilai**, bukan opsional lagi) dan **`equipmentNumber`** (tetap opsional, combinable dengan date range; ✅ direvisi 2026-08-14 — sekarang boleh **lebih dari satu nilai**, kosong = semua equipment) ditambahkan; kedua field ini juga di-include di response payload (`equipmentNumber` tetap satu nilai per submission di response, cuma filter request-nya yang multi-value) | Diminta eksplisit. Karena tanpa filter ini response bisa berisi campuran banyak site/equipment, kedua field juga ditambahkan ke response supaya caller bisa correlate hasil tanpa query balik — lihat [Filter Tambahan](#filter-tambahan--site-equipment-number--form-subgroup) |
| 12 | **✅ Direvisi (2026-08-04)** — `value` untuk elemen yang **isinya murni foto** (`CAMERACAPTURE` mis. "Photo Machine SMU", dan `PHOTOLIST` mis. "Foto Kondisi Fisik Equipment") selalu **`null`**, terlepas dari jumlah foto (1 atau banyak). `TAKEPHOTO` yang nempel di row checklist (tab spesifik, mis. "Cat Walk") **tidak terpengaruh aturan ini** — `value`-nya tetap jawaban `DROPDOWN` (mis. "Ok"), karena foto di situ cuma lampiran tambahan, bukan keseluruhan jawaban | ~~Versi sebelumnya bikin `value` = GUID untuk 1 foto, `null` untuk >1 foto — inkonsisten, dibedakan cuma berdasarkan *jumlah* foto padahal semantiknya sama (foto = keseluruhan jawaban, tidak ada nilai lain).~~ Disederhanakan: GUID tetap bisa didapat dari `photos[].url` (nempel di path terakhir), jadi tidak ada informasi yang hilang dengan selalu `null`. `TAKEPHOTO`-dalam-row per desain bisa **maksimal 3 foto** — dipakai juga sebagai basis perhitungan rate limit di [Endpoint — Photo Download](#endpoint--photo-download) |
| 13 | Identifikasi elemen "Photo Machine SMU" (untuk percabangan resolusi foto ke `TaskPersonalized`/`Task`, bukan `TaskPersonalizedEvidence`) pakai **`elementCode = 'CAMERACAPTURE'`**, bukan `taskCode` atau `label` | Dikonfirmasi: di [General Tab Template](form-builder.md#mekanisme-general-tab-template) (varian `maintenance` maupun `businessoperational`), `CAMERACAPTURE` cuma dipakai untuk satu elemen — "Photo Machine SMU" — elemen foto lain di template ini pakai `PHOTOLIST`. Elemen foto di tab Inspection/spesifik pakai `TAKEPHOTO`, bukan `CAMERACAPTURE`. Jadi `elementCode` saja sudah cukup unik untuk identifikasi, tidak perlu matching `taskCode` (yang belum tentu stabil lintas form) atau `label` (rawan typo/translasi) |
| 14 | Semua query (resolusi foto & metadata) ditambahkan filter **`IsActive = 1`** di tiap tabel yang dijoin (`FormSubmission`, `Task`, `WorkOrder`, `TaskPersonalized`, `TaskPersonalizedEvidence`, `BusinessOperationalForm`) | Diminta eksplisit — supaya record yang sudah di-soft-delete tidak ikut ter-expose ke sistem eksternal. **🚩 Reliabilitas mekanisme `IsActive` di live data belum diverifikasi** — lihat [Filter IsActive](#filter-isactive) dan open item baru |
| 15 | **✅ Disetujui** — kalau resolusi `photoGuid` gagal (tidak match apapun), entry tetap muncul di `photos[]` dengan **`url: null`** — bukan di-drop dari array | Drop diam-diam menyembunyikan masalah dari caller. `url: null` konsisten dengan pola "jujur representasikan ketiadaan" (lihat `title: null`), dan memudahkan observability (bisa monitor rate kegagalan resolusi foto). Lihat [Fallback Kalau Resolusi Foto Gagal](#fallback-kalau-resolusi-foto-gagal) |
| 16 | **✅ Disetujui** — method **`GET`** untuk kedua endpoint (list maupun single-fetch) | Kedua endpoint read-only dan idempotent — `GET` paling idiomatik, gampang di-cache/bookmark/debug. Filter (date range + `siteCode`/`equipmentNumber` + pagination) semuanya aman sebagai query string, tidak ada alasan pakai `POST`. Lihat [HTTP Method & Endpoint](#http-method--endpoint) |
| 17 | **Dua endpoint terpisah** — `GET /api/v1/form-submissions` (list/polling) dan `GET /api/v1/form-submissions/{formSubmissionId}` (single-fetch by ID) | Diminta eksplisit — dua endpoint ini beda peruntukan (polling berkala vs re-fetch/lookup granular), tidak digabung jadi satu. Lihat [HTTP Method & Endpoint](#http-method--endpoint) |
| 18 | Versioning API pakai **URL path** (`/api/v1/...`) | Paling eksplisit untuk konsumen B2B eksternal, gampang didokumentasikan/dites tanpa header khusus. **🚩 Masih rekomendasi, perlu di-assess developer** sebelum dikunci — lihat [API Versioning](#api-versioning) |
| 19 | **Tidak ada pembatasan otorisasi granular per site** — 1 API Key valid otomatis akses semua site | Diminta eksplisit. Filter `siteCode`/`equipmentNumber` di request murni narrowing hasil pencarian, bukan enforcement keamanan. Lihat [Scope Otorisasi](#scope-otorisasi) |
| 20 | **Proxy endpoint** dipilih untuk serve foto (`GET /api/v1/form-submissions/photos/{photoGuid}`), **bukan** SAS token per-URL maupun expose `ContentAddress` mentah | Blob Storage tidak bisa diakses langsung dari luar Digiman+ (dikonfirmasi user). SAS token ditolak karena masalah timing TTL — endpoint ini didesain untuk polling async, sistem eksternal belum tentu langsung fetch foto begitu dapat response metadata. Proxy reuse auth API Key + IP whitelist yang sama (satu mekanisme, satu titik revoke), blob tetap fully private. Lihat [Endpoint — Photo Download](#endpoint--photo-download) |
| 21 | Response endpoint foto pakai **binary langsung + `Content-Type`**, **bukan base64** | Base64 nge-bloat payload ~33%, cuma masuk akal kalau foto harus nempel di JSON list/detail (bertentangan dengan alasan pagination di Keputusan #2). Endpoint terpisah membuat binary lebih efisien: cache-able, mendukung `Range` request, langsung bisa dibuka tanpa decode. Lihat [Endpoint — Photo Download](#endpoint--photo-download) |
| 22 | `Cache-Control: private, max-age=31536000, immutable` (1 tahun) untuk response foto | Foto evidence bersifat immutable per `photoGuid` — tidak perlu revalidasi (`ETag`) sama sekali. `private` karena response butuh auth, bukan buat shared cache/CDN publik |
| 23 | **✅ Direvisi (2026-08-14)** — Rate limit endpoint foto **terpisah** dari endpoint data: **1.850 req/menit, 155.000 req/hari** (sebelumnya 1.400/120.000, basisnya salah — lihat kolom Alasan) | Karakteristik beban beda jauh (fetch foto ringan vs query data yang JOIN+aggregate), dan foto punya multiplier tinggi per submission. Basis lama (345 foto/submission = 113 form task × 3 foto + 5 foto General tab + 1 SMU) pakai angka "113" yang ternyata stale — real: **116** `BANKTASK` varian Grader (lebih tinggi dari 111 varian General), +1 foto signature yang dulu belum terhitung → worst-case-literal jadi **355** foto/submission. Ditambah **buffer 30%** (355 × 1,3 ≈ 461,5, dibulatkan ke **460**) untuk jaga-jaga varian form IIR lain/kategori `SubGroup` baru yang belum di-sample (konsisten dengan Keputusan #26 — daftar formCode sengaja tidak di-enumerasi). Limit final diturunkan dari 460 foto/submission dengan formula yang sama seperti sebelumnya (pageSize default × foto/submission ÷ target hydrate 5 menit, lalu rasio 2.500:30 untuk basis harian). **🚩 Tetap worst-case-literal + buffer dari sisi kebutuhan client — belum diverifikasi terhadap kapasitas backend/DevOps** (lihat [Open Item #9](#9--rate-limit-endpoint-foto-1850-reqmenit-155000-reqhari-belum-diverifikasi-terhadap-kapasitas-backend)). Lihat [Endpoint — Photo Download](#endpoint--photo-download) |
| 24 | Naming endpoint: `GET /api/v1/form-submissions/photos/{photoGuid}` — **tidak** nested di bawah `{formSubmissionId}` | Tetap di namespace `form-submissions` untuk konsistensi/discoverability dengan 2 endpoint lain. `photoGuid` sudah cukup unik untuk resolve sendiri, tidak butuh `formSubmissionId` sebagai konteks — apalagi otorisasi juga tidak granular per-resource (Keputusan #19) |
| 25 | **✅ Diputuskan (2026-08-14)** — Endpoint (termasuk naming, `/api/v1/iir-form-submissions` → `/api/v1/form-submissions`, dan endpoint foto) **digeneralisasi lintas semua kategori `BusinessOperationalForm`**, bukan cuma IIR. Filter `bof.SubGroup = 'IIR'` yang tadinya hardcode diganti jadi parameter **wajib** `formSubGroup` di request (satu nilai, bukan list) — bukan opsional/default-ke-semua-kategori. `siteCode` juga direvisi jadi wajib di request yang sama (lihat Keputusan #11 revisi). `formSubGroup`/`siteCode`/`equipmentNumber` selalu di-include di response | Diminta eksplisit — supaya kalau ada kategori form baru ditambahkan ke `BusinessOperationalForm` di masa depan, sistem eksternal tinggal ganti nilai `formSubGroup=<kategori>` di request mereka tanpa perlu perubahan endpoint/kode di sisi Digiman+; wajib (bukan opsional) supaya tiap request eksplisit scope ke satu kategori, tidak ada request yang tanpa sadar menarik campuran banyak kategori sekaligus. Cakupan tetap terbatas ke form `FT_BusinessOperationalForm` (yang punya baris di `BusinessOperationalForm`) — form `FT_MaintenanceForm` (Inspection/PM Shutdown/BD Corrective) tetap di luar cakupan, generik atau tidak. Lihat [Konteks](#konteks), [HTTP Method & Endpoint](#http-method--endpoint), dan [Filter Tambahan](#filter-tambahan--site-equipment-number--form-subgroup) |
| 26 | **✅ Diputuskan (2026-08-14)** — **Tidak ada filter per-`formCode`** di dalam satu `formSubGroup`. Response untuk satu `formSubGroup` (mis. `IIR`) selalu mengembalikan **semua** formCode yang tergabung di kategori itu tercampur (mis. `FORM385` + `FORM394` bareng dalam satu response) — tidak ada mode "cuma varian X". Konsekuensinya, daftar lengkap formCode per `SubGroup` **tidak perlu di-enumerasi/di-maintain** sebagai bagian dari desain endpoint ini | Diminta eksplisit. Grouping sudah cukup terjadi di level `SubGroup` (Keputusan #25) — filter tambahan per-formCode di bawahnya cuma menambah kompleksitas tanpa manfaat, karena tujuan endpoint memang expose semua submission dalam satu kategori bisnis, bukan micro-manage per varian form. Endpoint jadi benar-benar generik: tidak perlu tahu/track formCode apa saja yang termasuk kategori tertentu, cukup andalkan kolom `SubGroup` di database sebagai source of truth. Lihat [Open Item #6](#6--resolved--join-key-ke-businessoperationalform-terkonfirmasi-dan-daftar-lengkap-formcode-per-varian-sengaja-tidak-di-enumerasi) |
| 27 | **✅ Diputuskan (2026-08-14)** — Untuk jawaban `PHOTOLIST` yang `e.label`-nya kosong (`""`, selalu begitu di data real), API **tidak membiarkan `label` kosong** — diisi dari konteks section: (a) kalau section punya elemen `CUSTOMCONTENT` sebelum `PHOTOLIST`-nya (mis. section "Asset Detail" → "Foto Kondisi Fisik Equipment", teks dari `<strong>FOTO KONDISI FISIK EQUIPMENT :</strong>` di-strip HTML & tanda baca penutup), pakai teks itu; (b) kalau section cuma berisi elemen `PHOTOLIST` itu sendiri tanpa `CUSTOMCONTENT` (mis. section "Digital Signature by Inspector"), pakai **`title` section itu sendiri** sebagai `label` | Diminta eksplisit — signature disamakan perlakuannya dengan "Foto Kondisi Fisik Equipment": sama-sama prinsip "ambil teks konteks terdekat", cuma sumbernya beda (sibling `CUSTOMCONTENT` vs `title` section) tergantung apa yang tersedia. Ini **beda** dari filosofi "honest null" yang dipakai untuk `title: null` section tanpa judul (Mapping Field) — di situ memang tidak ada teks apapun yang bisa diambil, sedangkan di sini source teksnya selalu ada (baik dari `CUSTOMCONTENT` maupun `title` section), jadi tidak ada alasan membiarkan `label` kosong. Per-foto tetap juga punya `label` sendiri dari `caption` (lihat [Skema Response](#skema-response)) — field ini di level jawaban cuma menjelaskan section-nya secara keseluruhan |

## Open Items — Perlu Diselesaikan Sebelum Implementasi

### 1. 🚩 Belum Resolved (dibuka ulang, 2026-08-14) — `PHOTOLIST.value` di data real masih placeholder, bukan GUID

**Ticket: [IAMS30-4485](https://bukittechnology.atlassian.net/browse/IAMS30-4485)**

**Dibuka ulang (2026-08-14):** kesimpulan "Resolved" tanggal 2026-08-04 di bawah ini ternyata **belum terbukti di data real**. 4 sample baru ([`IIR-General-tab-general-sample.json`](examples/IIR-General-tab-general-sample.json), [`IIR-Grader-tab-general-sample.json`](examples/IIR-Grader-tab-general-sample.json), dan section "Digital Signature by Inspector" di kedua sample tab Inspection) semuanya menunjukkan pola yang sama untuk `PHOTOLIST`:
- `value` = placeholder array, mis. `"[[0], [0], [0], [0], [0]]"` — **bukan GUID**.
- `valueCaption` masih berisi device file path asli (`/var/mobile/Containers/Data/Application/.../CAP_....jpg`) — persis pola bug yang sebelumnya dianggap sudah difix.

**Target/desain tetap benar, cuma belum live**: arah resolusi yang didokumentasikan di bawah (`value` berisi GUID foto, dibaca sama seperti `TAKEPHOTO`/`CAMERACAPTURE`) **tetap jadi tujuan akhir yang benar** — begitu data sudah matang, `value` memang seharusnya berisi GUID foto, bukan `valueCaption`. Yang berubah cuma status: ini **belum terjadi di data saat ini**, jadi belum bisa diasumsikan sebagai fakta yang sudah berlaku untuk implementasi.

**Caveat**: keempat sample di atas berasal dari 1 tester (`2009OBH.supervisor01@protonmail.com`), 1 sesi, hari yang sama (kemungkinan data test/UAT, bukan produksi) — belum tentu representatif. Tapi karena semua 4 kemunculan `PHOTOLIST` (General tab ×2 form, signature tab Inspection ×2 form) konsisten menunjukkan pola yang sama, ini cukup kuat untuk tidak lagi diasumsikan "Resolved" tanpa verifikasi tambahan dari data produksi atau konfirmasi ulang ke tim.

**Implikasi ke endpoint ini:** balik ke status semula — endpoint IIR external API **kemungkinan perlu menunggu** fix IAMS30-4485 (atau perbaikan setara yang membuat `value` benar-benar terisi GUID) sebelum resolusi foto `PHOTOLIST` bisa diandalkan dari `value`. Sampai dikonfirmasi ulang, treat sebagai **blocker parsial** — bukan hard blocker untuk seluruh endpoint, tapi mempengaruhi validitas foto General tab & signature secara spesifik. Fallback [`url: null`](#fallback-kalau-resolusi-foto-gagal) (Keputusan #15) akan sering terpakai untuk kasus ini kalau di-deploy sebelum data benar-benar matang.

**Masih perlu ditindaklanjuti:**
- Konfirmasi ke tim: apakah pola placeholder `[[0], ...]` ini memang representasi "belum di-upload/di-sync", atau regresi bug yang belum ke-tangkap.
- Ambil/uji dengan sample dari data produksi (bukan akun test) untuk memastikan pola ini bukan artifact environment test.
- Query di [Resolusi Blob URL untuk Foto](#resolusi-blob-url-untuk-foto)/[form-submission.md](form-submission.md#query--tab-general-flat-elements) yang membaca dari `e.valueCaption` untuk `PHOTOLIST` tetap perlu direvisi ke `e['value']` **begitu** `value` benar-benar reliable — tapi bentuk JSON pasti `value` (nested per-slot, terlihat dari sample sebagai `[[slot1], [slot2], ...]`) baru bisa dipastikan final setelah data sudah terisi GUID sungguhan, bukan placeholder `0`.

**✅ Dikonfirmasi (2026-08-14) — section "Digital Signature by Inspector" di tab Inspection memang sengaja pakai `elementCode = PHOTOLIST`** (bukan salah label/kebetulan) — sama dengan `PHOTOLIST` di General tab, cuma beda section/lokasi. Status `value`-nya **mengikuti item ini juga** (masih placeholder, akan dibetulkan bersamaan) — jadi tidak perlu dilacak sebagai bug terpisah, tapi lihat [Open Item #5](#5--resolved--flat-photolist-di-tab-inspection-signature-ditangani-sama-seperti-flat-elements-tab-general) untuk catatan structural terpisah (sudah resolved) yang ditemukan di lokasi yang sama.

### 2. 🚩 Reliabilitas mekanisme `IsActive` di live data belum diverifikasi

Query resolusi foto & metadata sekarang filter `IsActive = 1` di semua tabel yang dijoin (lihat [Filter IsActive](#filter-isactive) dan Keputusan Desain #14). Sebelum filter ini diandalkan sebagai satu-satunya penjaga soft-delete, **perlu dikonfirmasi ke developer/tim backend**:
- Apakah semua path soft-delete konsisten set `IsActive = 0`, atau ada jalur yang masih hard-delete/lupa update flag ini
- Apakah ada kasus row `IsActive = 0` yang justru masih perlu muncul di endpoint ini (mis. submission historis yang tetap relevan buat pihak eksternal)
- Konsistensi `IsActive` antar tabel yang di-join (mis. `FormSubmission.IsActive = 0` tapi `TaskPersonalized.IsActive = 1`) — row mana yang jadi acuan

Kalau ternyata tidak reliable, filter ini berisiko exclude data yang seharusnya valid (false negative).

### 3. 🚩 API Versioning — perlu di-assess developer

Rekomendasi versioning (`/api/v1/...` di URL path, kebijakan breaking-change/deprecation) di [API Versioning](#api-versioning) dan Keputusan Desain #18 **masih proposal, belum final**. Perlu dinilai developer: konsistensi dengan konvensi API/endpoint lain yang sudah ada di Digiman+, kesiapan infrastruktur routing/gateway untuk path-based versioning, dan realistis-tidaknya komitmen masa deprecation dari sisi effort maintain multi-versi.

### 4. ✅ Resolved — Aksesibilitas foto oleh sistem eksternal

**Dikonfirmasi user (2026-08-04):** blob penyimpanan foto **tidak bisa diakses langsung dari luar Digiman+** — akses hanya berlaku lewat sistem Digiman+ sendiri (web maupun mobile). Konsisten dengan pola gambar guideline yang di-host di Azure Blob Storage privat ([`form-builder.md`](form-builder.md#karakteristik)).

**Keputusan:** proxy endpoint (bukan SAS token) — lihat spec lengkap di [Endpoint — Photo Download](#endpoint--photo-download) dan Keputusan Desain #20–24. `photos[].url` sekarang mengarah ke endpoint proxy Digiman+ sendiri, bukan `ContentAddress` mentah.

### 5. ✅ Resolved — Flat `PHOTOLIST` di tab Inspection (signature) ditangani sama seperti flat elements tab General

**Ditemukan (2026-08-14)** dari [`IIR-General-tab-inspection-sample.json`](examples/IIR-General-tab-inspection-sample.json) dan [`IIR-Grader-tab-inspection-sample.json`](examples/IIR-Grader-tab-inspection-sample.json), section "Digital Signature by Inspector": elemen `PHOTOLIST` di situ duduk **flat** di `section.elements[]` (sejajar dengan `CUSTOMCONTENT`/`INPUT` "SUMMARY"), **bukan** nested di dalam container `BANKTASK`/`NUMBERINGTEXT` seperti pola checklist item lainnya di tab spesifik.

**Kenapa awalnya dikira masalah:** query tab spesifik yang didokumentasikan di [form-submission.md](form-submission.md#query--tab-spesifik-nested-elements) pakai 3-level `JOIN` (`c.sections → d.elements → e.elements`) — level ketiga (`e.elements`) mengasumsikan tiap `d.elements` (mis. `BANKTASK`) selalu punya array `elements` nested di dalamnya (`DROPDOWN`/`TAKEPHOTO`/`ADDITIONALINFORMATION`). Elemen flat seperti `PHOTOLIST`/`INPUT` "SUMMARY" **tidak punya properti `.elements`**, jadi kalau query 3-level ini dipaksa jalan apa adanya untuk seluruh tab, section signature (dan section "RESUME FINAL INSPECTION" yang berisi `INPUT` "SUMMARY") tidak akan ke-return.

**✅ Dikonfirmasi (2026-08-14) — bukan gap, section flat ini ditangani persis seperti flat elements tab General:** tab General sendiri sudah lebih dulu punya pola section flat (`CUSTOMCONTENT`/`PHOTOLIST` langsung di `section.elements[]`, tanpa nesting `BANKTASK`) dan sudah ada query khususnya — [Query — Tab General (flat elements)](form-submission.md#query--tab-general-flat-elements), 2-level `JOIN` (`c.sections → d.elements`, tanpa level ketiga). Section signature di tab Inspection strukturnya identik dengan pola itu, jadi query-nya tinggal reuse pattern yang sama (2-level JOIN, filter ke section/element yang bersangkutan), **bukan** perlu diakali dari 3-level JOIN yang memang didesain untuk `BANKTASK`-nested rows. Implementasi tab spesifik/Inspection jadinya **menggabungkan dua query**: 3-level JOIN untuk section berisi checklist `BANKTASK`, dan 2-level JOIN (pola tab General) untuk section flat seperti signature/summary — bukan satu query tunggal yang harus menangani keduanya sekaligus.

**Implikasi:** foto signature tetap ke-cover di `photos[]` selama implementasi memakai kedua pola query di atas untuk tab spesifik, bukan cuma 3-level JOIN saja. Rate limit di [Perhitungan worst-case](#endpoint--photo-download) tetap perlu +1 untuk foto signature ini (sudah dicatat di revisi 2026-08-14) — itu murni soal angka volume, bukan lagi soal risiko section-nya hilang dari response.

**✅ Diperbaiki (2026-08-14) — filter `isShow` di query flat (yang di-reuse dari tab General) sudah dilengkapi.** Waktu pattern 2-level JOIN ini benar-benar di-reuse untuk tab spesifik, ketahuan filter `WHERE (e.isShow = true OR e.elementCode = 'PHOTOLIST')` yang lama juga men-drop elemen `INPUT` (mis. "SUMMARY" di section "RESUME FINAL INSPECTION") — karena `INPUT` **juga** tidak punya key `isShow` sama sekali, sama seperti `PHOTOLIST`/`CUSTOMCONTENT`. Fix: `OR e.elementCode IN ('PHOTOLIST', 'INPUT')` — lihat query & penjelasan lengkap di [form-submission.md](form-submission.md#query--tab-general-flat-elements).

**Catatan tambahan — section instruksional murni tetap benar ter-exclude:** tab Inspection di sample terbaru juga punya section pembuka "CATATAN PENTING !" isinya cuma 2 elemen `CUSTOMCONTENT` (teks instruksi, bukan jawaban, tidak ada `taskCode`). Section ini **otomatis tidak ke-return** oleh kedua query di atas (3-level JOIN karena tidak ada `.elements` nested, 2-level JOIN karena `CUSTOMCONTENT` sengaja tidak masuk daftar `OR e.elementCode IN (...)`) — ini **behavior yang benar**, bukan bug, jadi tidak perlu penanganan tambahan. Dicatat di sini supaya tidak disangka gap kalau nanti section ini "hilang" dari response.

### 6. ✅ Resolved — Join key ke `BusinessOperationalForm` terkonfirmasi, dan daftar lengkap formCode per varian sengaja tidak di-enumerasi

**Ditemukan/dikonfirmasi (2026-08-14):** "form IIR" bukan satu `formCode` tunggal — dikonfirmasi user, kategorinya ada di tabel `[cst-iams-sqldb-maintenance-execution].[BusinessOperationalForm]`, kolom `SubGroup = 'IIR'`. Lihat revisi [Konteks](#konteks). Ini menggantikan asumsi lama di seluruh dokumen ini yang hardcode ke `FORM394`.

**✅ Resolved — join key & lokasi tabel**: `bof.FormCode = fs.FormCode`, dan `BusinessOperationalForm` memang di database `maintenance-execution` yang sama — dikonfirmasi langsung dari DDL asli di [`database/maintenance-execution-schema.md`](../database/maintenance-execution-schema.md#businessoperationalform-master-data) (bukan asumsi/perlu tanya backend lagi). Lihat detail koreksi di [Sumber Data](#sumber-data--sql--cosmos).

**✅ Resolved (2026-08-14) — tidak perlu filter per-varian, dan daftar lengkap formCode tidak perlu di-enumerasi/di-maintain di dokumen ini.** Diputuskan eksplisit: response untuk satu `formSubGroup` (mis. `IIR`) selalu berisi **semua** formCode yang tergabung di kategori itu tercampur (mis. `FORM385` + `FORM394` bareng dalam satu response) — **tidak** ada mode filter ke satu varian form tertentu (mis. cuma "Grader"). Karena grouping sudah cukup di level `SubGroup` (Keputusan #25/#26), endpoint tidak pernah butuh tahu formCode individual apa saja yang termasuk satu kategori — jadi butir "daftar lengkap formCode `SubGroup = 'IIR'`" yang sebelumnya dianggap perlu di-enumerasi **bukan lagi blocker desain**. (Tetap relevan sebagai info operasional kalau tim mau spot-check volume/rate-limit — lihat [Rate Limit](#rate-limit--terpisah-dari-endpoint-data) — tapi bukan sesuatu yang perlu dituntaskan sebelum implementasi.)

### 7. ✅ Resolved — `Task.WorkOrderId` selalu terisi, semua form submission generate data ke `WorkOrder`

**Ditemukan (2026-08-14, audit ulang design doc)**, lalu **langsung dikonfirmasi user 2026-08-14**: sempat dicurigai `Task.WorkOrderId` bisa `NULL` untuk task bertipe `FT_BusinessOperationalForm` (self-service, beda mekanisme dari `FT_MaintenanceForm` yang Bank-Task/WorkOrder-driven by design — lihat [Konteks](#konteks)), yang kalau benar akan bikin `INNER JOIN [dbo].[WorkOrder]` di query list & single-fetch (lihat [Sumber Data](#sumber-data--sql--cosmos)) diam-diam meng-exclude submission tanpa `WorkOrder` dari response — serius karena `siteCode` (bersumber dari `WorkOrder`) sekarang wajib sebagai filter (Keputusan #11/#25).

**✅ Dikonfirmasi user — kecurigaan ini tidak berlaku:** **semua form submission (termasuk `FT_BusinessOperationalForm`) generate data ke tabel `WorkOrder`**, jadi `Task.WorkOrderId` selalu terisi, `INNER JOIN` di kedua query aman, tidak ada submission yang diam-diam ke-drop. Petunjuk yang tadinya dicurigai (inspector tetap isi manual "Site"/"Kode Unit" di tab General meski `WorkOrder` juga selalu ada) ternyata bukan indikasi `WorkOrder`-nya tidak ada — dua sumber data ini memang sengaja tetap terpisah/redundant (isian form vs `WorkOrder.SiteCode`/`AssetNumber`), bukan karena salah satunya sering kosong.

**Tidak ada perubahan ke query/keputusan** — desain `siteCode` wajib + bersumber dari `WorkOrder` (Keputusan #11/#25) tetap valid apa adanya, tidak perlu `LEFT JOIN`/fallback tambahan.

### 8. ✅ Resolved — `BusinessOperationalForm.FormCode` selalu unique, tidak ada risiko fan-out

**Ditemukan (2026-08-14, audit ulang design doc)**, lalu **langsung dikonfirmasi user 2026-08-14**: DDL di [`database/maintenance-execution-schema.md`](../database/maintenance-execution-schema.md#businessoperationalform-master-data) cuma menandai `Code` sebagai **PK** — `FormCode` (kolom yang dipakai untuk join, `bof.FormCode = fs.FormCode`) tidak eksplisit didokumentasikan unique di DDL yang sudah dilihat, sempat dicurigai berisiko **fan-out**: kalau satu `FormCode` bisa dipakai lebih dari satu baris `BusinessOperationalForm`, join di kedua query (list & single-fetch) bisa menghasilkan duplikat row untuk submission yang sama.

**✅ Dikonfirmasi user — `FormCode` di `BusinessOperationalForm` selalu unique** (satu `FormCode` cuma pernah muncul di satu baris). Join `bof.FormCode = fs.FormCode` aman, tidak ada risiko fan-out/duplikat row. Tidak ada perubahan ke query — desain saat ini tetap valid apa adanya.

### 9. 🚩 Rate limit endpoint foto (1.850 req/menit, 155.000 req/hari) belum diverifikasi terhadap kapasitas backend

**Ditemukan (2026-08-14).** Angka rate limit endpoint foto di [Rate Limit — Terpisah dari Endpoint Data](#rate-limit--terpisah-dari-endpoint-data) dan Keputusan Desain #23 (**1.850 req/menit, 155.000 req/hari**, setelah revisi basis 116 BANKTASK + buffer 30%) murni diturunkan dari sudut pandang **"berapa request yang dibutuhkan client eksternal yang berperilaku wajar"** — sama sekali **belum dibandingkan dengan kapasitas riil backend** (throughput Blob Storage untuk serve foto, jumlah koneksi SQL concurrent ke `TaskPersonalizedEvidence`/`TaskPersonalized`, kapasitas service `maintenance-execution` secara umum).

**Kenapa ini perlu diperhatikan:** buffer 30% yang ditambahkan (Keputusan #23) sengaja **menaikkan** ceiling limit supaya client legit tidak keblokir kalau ada varian form dengan lebih banyak foto — tapi menaikkan ceiling client-side otomatis berarti **potensi beban puncak ke backend juga naik**, tanpa ada verifikasi apakah backend sanggup menyerap beban itu. Kedua pertanyaan ini ("berapa yang dibutuhkan client" vs "berapa yang sanggup ditangani server") tidak sama, dan saat ini cuma yang pertama yang dihitung.

**Perlu dikonfirmasi ke tim backend *dan* DevOps/infra** — dua sudut pandang yang beda:
- **Backend**: kapasitas service `maintenance-execution` sendiri — koneksi SQL concurrent ke `TaskPersonalizedEvidence`/`TaskPersonalized`, efisiensi query resolusi foto di titik beban puncak.
- **DevOps/infra**: kapasitas di luar kendali kode aplikasi — throughput/bandwidth Blob Storage, batas App Service Plan/container (CPU, memory, concurrent connection), rules di load balancer/API gateway/WAF (kalau ada rate limiting atau connection cap di layer itu juga), serta apakah autoscaling sudah dikonfigurasi untuk menyerap burst 1.850 req/menit (≈31 req/detik) di titik puncak.
- Kalau kapasitas dari **salah satu pihak** (backend maupun infra) ternyata lebih rendah dari angka yang dihitung dari sisi client, **rate limit final harus ikut angka yang paling ketat** di antara keduanya — bukan angka kebutuhan client begitu saja.

**Status:** angka 1.850/menit, 155.000/hari tetap dipakai sebagai estimasi sementara (belum final) sampai ada konfirmasi kapasitas dari backend **dan** DevOps/infra.

---

## Autentikasi & Otorisasi

**✅ Direvisi (2026-08-14) — API Key + IP whitelist**, bukan OAuth2 Client Credentials Grant seperti draft awal (lihat Keputusan Desain #8). Disamakan dengan pola integrasi eksternal lain yang sudah berjalan (mis. SAP) — diminta eksplisit, supaya tidak ada dua pola auth berbeda untuk hal yang sama (integrasi B2B server-to-server) dan tim ops/support cukup punya satu playbook provisioning/rotasi/monitoring untuk semua integrasi eksternal, bukan cuma endpoint ini.

**Mekanisme:**
1. Setiap konsumen eksternal dapat **1 API Key statis** (per konsumen, bukan per environment/per user).
2. Konsumen mendaftarkan **IP/CIDR range** dari mana request akan datang (whitelist) — sama seperti proses provisioning integrasi SAP.
3. Setiap request ke endpoint data maupun endpoint foto wajib menyertakan API Key di header, **dan** originate dari IP yang sudah di-whitelist untuk key tersebut:
   ```
   X-Api-Key: <api_key>
   ```
4. Request yang API Key-nya valid tapi datang dari IP di luar whitelist tetap **ditolak** (lihat [Format Error Response](#format-error-response), `403 FORBIDDEN`) — dua faktor ini (key + asal IP) dicek bersamaan, bukan salah satu saja.

**Kenapa dua faktor (API Key + IP whitelist), bukan API Key saja:**
- Konsisten dengan pola existing (SAP dkk) — bukan desain baru yang mesti didokumentasikan/dipelajari terpisah oleh tim ops maupun konsumen eksternal.
- IP whitelist jadi lapisan pertahanan tambahan di level jaringan — API Key yang bocor tidak otomatis bisa dipakai dari IP sembarangan.
- Tidak perlu bangun infrastruktur token-issuance (OAuth2 provider) baru dari nol — API Key statis + whitelist jauh lebih sederhana dioperasikan untuk jumlah konsumen eksternal yang relatif sedikit & dikenal (bukan API publik dengan konsumen tak terbatas).

**🚩 Perlu dikonfirmasi ke tim yang biasa provisioning integrasi SAP-style:**
- Detail teknis persis yang sudah dipakai (nama header, format API Key, mekanisme rotasi/revoke, di mana whitelist IP dikelola — API Gateway/WAF/App Service) — supaya endpoint ini benar-benar reuse infrastruktur yang sudah ada, bukan cuma meniru polanya secara konsep.
- Asumsi bahwa konsumen endpoint ini (sistem eksternal yang serupa dengan SAP-style integration) punya **egress IP yang statis/predictable** — kalau ada calon konsumen dengan infrastruktur cloud-based/IP dinamis, pola ini perlu pengecualian/penyesuaian.

### Scope Otorisasi

**✅ Dikonfirmasi — tidak ada pembatasan granular per site.** 1 API Key yang valid (lolos autentikasi, termasuk cek IP whitelist) otomatis punya akses ke **semua site**, bukan dibatasi ke site tertentu. Jadi tidak perlu ACL/mapping tambahan "API Key X cuma boleh lihat site LAT" — begitu autentikasi lolos, filter `siteCode`/`equipmentNumber` di request murni buat narrowing hasil pencarian caller sendiri, bukan enforcement keamanan.

## Rate Limiting

**✅ Dikonfirmasi — per API Key** (bukan per IP). Perlu dibedakan dari IP whitelist di [Autentikasi & Otorisasi](#autentikasi--otorisasi) — whitelist itu **gate** (boleh/tidak boleh akses sama sekali dari IP tersebut), bukan **unit hitungan kuota**. Kuota rate limit tetap dihitung per API Key, bukan per IP asal — supaya kalau di kemudian hari ada konsumen dengan beberapa IP dalam satu whitelist (mis. multi-server/load-balanced di sisi eksternal), kuotanya tetap satu bucket per konsumen, bukan pecah per IP.

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
| 400 | `MISSING_REQUIRED_PARAMETER` | **Baru (2026-08-14)** — `formSubGroup` atau `siteCode` tidak diisi (lihat Keputusan Desain #25 dan #11 revisi), atau salah satunya diisi lebih dari satu nilai (mis. dikirim sebagai list/array, bukan satu string) — beda dari `equipmentNumber` yang memang boleh multi-value. `details` isi `[{field, reason}]` kalau lebih dari satu parameter wajib yang bermasalah sekaligus |
| 401 | `UNAUTHORIZED` | **✅ Direvisi (2026-08-14)** — Header `X-Api-Key` tidak ada, atau API Key tidak valid (tidak terdaftar/sudah di-revoke) — lihat [Autentikasi & Otorisasi](#autentikasi--otorisasi) |
| 403 | `FORBIDDEN` | **✅ Direvisi (2026-08-14)** — API Key valid, tapi request datang dari IP di luar whitelist yang terdaftar untuk key tersebut — lihat [Autentikasi & Otorisasi](#autentikasi--otorisasi) |
| 429 | `RATE_LIMITED` | Lihat [Rate Limiting](#rate-limiting) |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

## Filter Tambahan — Site, Equipment Number & Form SubGroup

**`formSubGroup` & `siteCode` — WAJIB, tepat satu nilai masing-masing (bukan opsional, bukan list):**

| Parameter | Sumber SQL | Keterangan |
|---|---|---|
| `formSubGroup` | `BusinessOperationalForm.SubGroup` | **Baru (2026-08-14), wajib, satu nilai** — lihat [Konteks](#konteks) dan Keputusan Desain #25. Mis. `formSubGroup=IIR`; **tidak ada** mode "semua kategori" — request tanpa `formSubGroup`, atau dengan lebih dari satu nilai, invalid — lihat [Format Error Response](#format-error-response) |
| `siteCode` | `WorkOrder.SiteCode` | **✅ Direvisi (2026-08-14), wajib, satu nilai** (sebelumnya opsional — lihat Keputusan #11) — lihat [schema WorkOrder](form-submission.md#schema-tabel-workorder). Request tanpa `siteCode`, atau dengan lebih dari satu nilai, invalid |

Keduanya sejajar dengan date range (Keputusan #1) — sama-sama wajib & single-value, bukan filter narrowing seperti `equipmentNumber` di bawah.

**`equipmentNumber` — satu-satunya yang opsional, dan satu-satunya yang boleh multi-value:**

| Parameter | Sumber SQL | Keterangan |
|---|---|---|
| `equipmentNumber` | `WorkOrder.AssetNumber` | Sumber asli `DPEquipment.Equipment`. **✅ Direvisi (2026-08-14)** — boleh lebih dari satu nilai, comma-separated (mis. `equipmentNumber=HDCT73112,HDCT73113`), di-`IN (...)`-kan lewat `STRING_SPLIT` (lihat [Sumber Data](#sumber-data--sql--cosmos)). Kosong/tidak diisi = **semua equipment** di site & kategori yang diminta |

Join path baru: `FormSubmission.TaskId → Task.Id`, `Task.WorkOrderId → WorkOrder.Id` — tambahan dari join path yang sudah ada (`Task → TaskPersonalized`). Ketiga kolom **bukan** hasil agregasi (nilainya konstan per grup — `siteCode`/`equipmentNumber` konstan per `WorkOrder`, `formSubGroup` konstan per `formCode`), jadi difilter di `WHERE`, bukan `HAVING` — lihat query lengkap di [Sumber Data](#sumber-data--sql--cosmos).

**Ketiga field juga ditambahkan ke response payload** (`siteCode`, `equipmentNumber`, `formSubGroup` di level `submissions[]`, lihat [Skema Response](#skema-response) dan [Mapping Field](#mapping-field-raw-query-result--api-field)) — bukan cuma jadi parameter filter/request. Di response, `equipmentNumber` tetap **satu nilai per submission** (bukan array) — 1 submission memang cuma terkait 1 `WorkOrder`/1 equipment, multi-value cuma berlaku di sisi filter request, bukan di bentuk data submission itu sendiri. Tanpa filter `equipmentNumber` dipakai, satu response (dalam satu site+kategori yang sama) masih bisa berisi campuran banyak equipment, caller butuh cara correlate tiap submission tanpa query balik ke sistem lain — field ini juga lebih reliable dibanding jawaban "Kode Unit" di tab General (isian bebas/dropdown dari inspector, bisa typo/tidak sinkron; `equipmentNumber` level submission datang langsung dari `WorkOrder`). Untuk `formSubGroup`/`siteCode`: meski caller sudah wajib kirim nilai spesifik di request, tetap di-echo di tiap submission supaya bentuk response konsisten dan caller tidak perlu asumsi implisit dari parameter request-nya sendiri.
