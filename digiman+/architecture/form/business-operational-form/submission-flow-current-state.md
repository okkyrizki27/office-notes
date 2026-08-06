# Business Operational Form — Mobile Submission Flow (Current State)

*Last updated: 2026-08-06*

---

**Service:** `maintenance-execution`
**Platform:** Mobile
**Actor:** User Site / Supervisor / Foreman / Mechanic
**Sumber:** HTTP capture (Alice HTTP Inspector) dari app `Digiman+ Dev` (`com.bukitteknologi.iamsmobile.dev`), tanggal 2026-08-06
**Contoh form:** `boFormCode: WICOPECHECK_WASHING` (`FT_BusinessOperationalForm`, lihat [form-builder.md](../form-builder.md))

Dokumen ini merekam **flow API riil** saat user mengisi Business Operational Form di mobile, sebagai pelengkap struktur data yang sudah didokumentasikan di [form-submission.md](../form-submission.md) dan [form-builder.md](../form-builder.md). Auth pakai Bearer JWT (Azure AD B2C) — token diredact di seluruh dokumen ini; klaim yang relevan ke flow ini: `extension_Site`, `extension_Section`, `extension_Cst`, `extension_Roles`.

> ⚠️ **Contoh request/response di tiap step adalah capture terpisah** (masing-masing mengilustrasikan pola API untuk step tersebut), **bukan jaminan satu transaksi yang sama end-to-end.** GUID/ID di satu step bisa saja tidak match dengan step lain kalau capture-nya diambil dari sesi/percobaan berbeda — jangan asumsikan chaining literal antar-step kecuali dicek ulang match ID-nya (lihat catatan spesifik di step 2.2).

---

## Ringkasan Flow

1. User buka form di mobile → create transaksi (identitas WorkOrder/Task/TaskPersonalized/FormSubmission/tab di-generate client-side)
2. User isi tab **General** → 2 API terpisah: SQL (`save/offline`) + Cosmos (`form-submission/structure/tab`)
3. User isi tab selain General (mis. Washing, Safety) → **belum ada trace, lihat [Open Questions](#open-questions--belum-dikonfirmasi)**
4. User submit form setelah semua tab selesai diisi → **belum ada trace, lihat [Open Questions](#open-questions--belum-dikonfirmasi)**

---

## Step 1 — Buka Form → Create Transaksi

**Endpoint:** `POST /maintenance-execution/api/workorder/additional/business-operational/{boFormCode}?ver=v1`

Request body:

```json
{
  "boFormCode": "WICOPECHECK_WASHING",
  "userCode": "2009OBH.supervisor02@protonmail.com",
  "siteId": "2009",
  "sectionId": "S095",
  "workOrderId": "59592612-7134-48c4-bf28-ecf04f96e596",
  "taskId": "9a846def-ccc8-442b-875a-b923cddf5784",
  "taskPersonalizedId": "0430063c-e99a-40cf-8497-73e5ab6cfefb",
  "formSubmissionId": "894157e5-7f78-4435-865b-80f1aaa51cc4",
  "formSubmissionTab": [
    { "FormSubmissionTabId": "6fa4a1d1-a00a-41e7-8695-2eeec73ec8ad", "FormTabName": "General" },
    { "FormSubmissionTabId": "dca8738e-765e-4bc6-a73c-db2884a57485", "FormTabName": "Washing" },
    { "FormSubmissionTabId": "0fe554a6-761b-4b9d-aedc-948e6f53a56c", "FormTabName": "Safety" }
  ]
}
```

Response (ringkas):

```json
{
  "result": {
    "workOrderId": 66579,
    "taskId": 65733,
    "taskPersonalizedId": 10652,
    "formSubmissionId": "894157e5-7f78-4435-865b-80f1aaa51cc4",
    "formTab": {
      "isCompleted": false,
      "tabs": [
        { "submissionTabId": "6fa4a1d1-a00a-41e7-8695-2eeec73ec8ad", "tabName": "General", "sequence": 1, "isCompleted": false },
        { "submissionTabId": "dca8738e-765e-4bc6-a73c-db2884a57485", "tabName": "Washing", "sequence": 2, "isCompleted": false },
        { "submissionTabId": "0fe554a6-761b-4b9d-aedc-948e6f53a56c", "tabName": "Safety", "sequence": 3, "isCompleted": false }
      ],
      "id": "894157e5-7f78-4435-865b-80f1aaa51cc4",
      "formId": "c3cd54dd-0cad-47e3-b986-3382b2e4c939",
      "title": "Washing",
      "formCode": "FORM7",
      "version": 7
    },
    "message": "WorkOrder saved successfully"
  }
}
```

### Observasi

- **Client generate semua GUID identitas transaksi** (`workOrderId`, `taskId`, `taskPersonalizedId`, `formSubmissionId`, tiap `FormSubmissionTabId`) — bukan server yang generate. Ini konsisten dengan desain **offline-first** (client harus bisa buat transaksi tanpa round-trip ke server dulu).
- **Server assign numeric ID** untuk `workOrderId` (66579), `taskId` (65733), `taskPersonalizedId` (10652) di response — sementara `formSubmissionId` dan `FormSubmissionTabId` **tetap dalam bentuk GUID** apa adanya (tidak dikonversi ke ID numerik). **Dikonfirmasi dari source code:** `WorkOrder`/`Task`/`TaskPersonalized` punya numeric `Id` internal (auto-generated saat create) + GUID dari client disimpan di kolom `ReferenceId`, sedangkan **`FormSubmission.Id` dan `FormSubmissionTab.Id` = GUID dari client langsung sebagai PK** (`Id = request.FormSubmissionId == Guid.Empty ? Guid.NewGuid() : request.FormSubmissionId`, pola sama persis untuk tab) — tidak ada numeric `Id` terpisah untuk 2 entity ini.
- **`boFormCode` (request) ≠ `formCode` (response)**: `boFormCode: "WICOPECHECK_WASHING"` adalah kode konfigurasi di tabel `BusinessOperationalForm` (yang membuat form ini muncul di menu mobile — lihat [form-builder.md](../form-builder.md)), sedangkan `formCode: "FORM7"` adalah kode form template sebenarnya (`Form.FormCode`) yang di-reference lewat `formId`. **Dikonfirmasi dari source code:** resolusinya lewat `BusinessOperationalFormRepository.GetFormCodeAsync(request.BoFormCode, ...)` → dapat `formCode` → dipakai untuk fetch definisi form lengkap (`GetFormSubmissionDataAsync`, external call ke service `maintenance-strategy`). Kalau form belum di-publish, external call ini gagal dan endpoint return error `FormNotPublished`.
- Response `formTab.tabs[].isCompleted` semuanya `false` di titik ini — form baru dibuat, belum ada data.

#### Server-side logic (Step 1) — `CreateBoAdditionalWoDataCommandHandler`

Satu transaction SQL yang create 4 entity berantai (`WorkOrder` → `Task` → `TaskPersonalized` → `FormSubmission` + `FormSubmissionTab`), plus copy form template dari Cosmos `MaintenanceStrategy` ke Cosmos `MaintenanceExecution` per tab — semuanya bisa gagal & rollback bareng kalau ada error di tengah (kecuali Cosmos copy, lihat catatan di bawah).

1. **Resolusi `SectionTypeCode` dari `SectionId` (organisasi), bukan dikirim client:** sebelum transaction dimulai, handler panggil `GetSectionTypeAsync(..., request.SectionId, ...)` (external call) untuk resolve `sectionId` user (`"S095"`) → `sectionType.Code`, yang lalu dipakai sebagai `WorkOrder.SectionTypeCode` awal. Ini konfirmasi langsung mekanisme `User.SectionId → OrganizationUnit → Asset.SectionTypeCode` — nilai awal `SectionTypeCode` di-derive dari section organisasi user, **bukan** dari asset yang dipilih (asset baru dipilih belakangan di tab General → lihat step 2.1, yang meng-overwrite `SectionTypeCode` ini dengan `sectionTypeCode` dari asset yang benar-benar dipilih user, mis. `"OBH"`).
2. **Idempotency check — cegah duplicate create kalau client retry:** sebelum create apa pun, handler cek `WorkOrderRepository.GetByReferenceIdAsync(request.WorkOrderId, ...)`. Kalau `WorkOrder` dengan `ReferenceId` itu **sudah ada**, handler **tidak create ulang** — masuk ke `ValidateExistingData()` yang cuma re-fetch identifier existing (`Task`, `TaskPersonalized`, `FormSubmission`, tab dari Cosmos by title) dan return response yang sama bentuknya tapi dengan message **`"Data already existed"`** (bukan `"WorkOrder saved successfully"`). Ini safety net penting untuk skenario **offline-first**: kalau mobile retry request create (mis. karena response timeout padahal server sudah sukses proses), tidak akan kebentuk WorkOrder/Task/dst duplikat.
   - ⚠️ Di `ValidateExistingData()`, ada 2 hal yang berpotensi tidak akurat: (a) loop `foreach (var formDetail in forms) { formStructures = await ...GetByFormSubmissionIdAsync(...) }` **menimpa** `formStructures` tiap iterasi alih-alih akumulasi (`Add`/`AddRange`) — kalau suatu saat 1 WorkOrder punya lebih dari 1 `FormSubmission`, cuma `FormSubmission` terakhir yang ke-return; aman selama asumsi 1 WorkOrder BO form = 1 `FormSubmission` selalu benar. (b) `IsCompleted` di response `ValidateExistingData` **selalu di-hardcode `false`** untuk tiap tab, walau sebenarnya beberapa tab sudah completed di percobaan sebelumnya — jadi kalau client retry-fetch data yang sudah ada, dia tidak dapat info progress completion yang akurat dari response ini.
3. **`WorkOrder`, `Task`, `TaskPersonalized` dibuat berurutan**, masing-masing `ReferenceId = request.<x>Id` (atau `Guid.NewGuid()` kalau kosong dari client). Khusus `TaskPersonalized`: setelah dibuat, handler **otomatis create 1 `TaskPersonalizedLog`** dengan `StartDate = DateTime.UtcNow` (server time saat create transaksi) — untuk Business Operational Form, log "start" ini **dibuat otomatis saat transaksi dibuat**, bukan dari device timestamp saat user klik tombol Start terpisah (beda dari deskripsi umum `TaskPersonalizedLog.StartDate` di [form-submission.md](../form-submission.md#schema-tabel-taskpersonalizedlog) yang bilang "device timestamp saat klik Start/Mulai").
4. **`FormSubmission` + `FormSubmissionTab`** dibuat dengan `Id` = GUID dari client (lihat poin numeric ID di atas). Untuk tiap tab (`form.Tabs`, urut `Sequence`), handler match ke `request.FormSubmissionTab` by `FormTabName` untuk ambil GUID yang dikirim client.
   - **`firstNumber` di response = running counter lintas tab**, bukan reset per tab: mulai dari 1, lalu tiap tab selesai diproses, `currentFirstNumber += tab.TotalParentTask`. General tab punya `TotalParentTask = 0` (tidak ada elemen bernomor / BANKTASK — flat form, lihat [struktur tab General](../form-builder.md#struktur-tab-di-formstructure)), makanya Washing tetap mulai dari `firstNumber = 1`; Safety lanjut dari situ (`firstNumber = 12` di response step 1 berarti Washing tab punya 11 parent task). Ini penjelasan konkret dari nilai `firstNumber` yang sudah kelihatan di response step 1.
5. **Copy form template ke Cosmos, per tab:** untuk tiap tab, handler panggil `GetFormStructureByTabIdAsync` (external call, service `maintenance-strategy`) untuk ambil struktur template, lalu di-map jadi dokumen `FormSubmissionStructure` baru dan `CreateAsync` ke Cosmos `MaintenanceExecution`. Ini implementasi literal dari mekanisme copy yang sudah didokumentasikan di [form-builder.md](../form-builder.md#dua-form-type). Detail baru: **hanya section dengan `IsSectionActive = true`** di template yang ikut di-copy (`tabStructure.Sections.Where(p => p.IsSectionActive)`) — section yang di-nonaktifkan di template tidak akan muncul di form submission baru.
   - **Cosmos document `id` (PK internal Cosmos) = GUID baru random** (`Guid.NewGuid().ToString()`), **bukan** sama dengan `FormSubmissionTabId`. Field `FormSubmissionTabId`/`FormSubmissionId` disimpan terpisah sebagai atribut dokumen untuk keperluan query (`GetByFormSubmissionTabIdAsync`) — bukan dipakai sebagai Cosmos document id itu sendiri.
   - ⚠️ **Cosmos create ini terjadi *di dalam* SQL transaction scope (secara kode), tapi Cosmos sendiri tidak ikut ke rollback SQL** — kalau SQL transaction di-rollback setelah sebagian dokumen Cosmos sudah ter-create (mis. tab ke-2 dari 3 gagal insert SQL-nya), dokumen Cosmos tab ke-1 yang sudah kepalang dibuat **tidak ikut di-rollback**. Sama seperti catatan konsistensi di step 2.2 — dua database ini memang tidak bisa 1 atomic transaction.

---

## Step 2 — Isi Tab General (2 API Terpisah)

Saat user mengisi tab General, mobile mengirim **2 request terpisah** ke 2 database berbeda (SQL dan Cosmos), tidak digabung jadi satu call.

### 2.1 — SQL: `save/offline`

**Endpoint:** `POST /maintenance-execution/api/workorder/additional/business-operational/{workOrderId}/save/offline?ver=v1`

`{workOrderId}` di URL = **GUID asli** yang dikirim client di step 1 (`59592612-7134-48c4-bf28-ecf04f96e596`), bukan numeric ID (`66579`) dari response step 1.

Request body:

```json
{
  "laborPersonnelCode": "2009OBH.supervisor02@protonmail.com",
  "siteCode": "2009",
  "sectionTypeCode": "OBH",
  "assetNumber": "HDCT78003",
  "assetTypeCode": "AT0007",
  "assetBrandCode": "AB0003",
  "assetModelCode": "AM0037",
  "assetModelName": "785C",
  "assetVariantCode": "AV0007",
  "SectionId": "S095"
}
```

Response:

```json
{ "result": { "message": "WorkOrder saved successfully" } }
```

#### Server-side logic (2.1) — `SaveBoAdditionalWoDataOfflineCommandHandler`

Satu handler ini menyentuh **3 tabel sekaligus**, dalam **1 DB transaction** (rollback total kalau ada error di tengah), plus audit log per entity yang diupdate:

1. **`WorkOrder`** — di-lookup via `GetByReferenceIdAsync(request.WorkOrderId, ...)`, yaitu **`WorkOrder.ReferenceId` = GUID `workOrderId` di URL** (bukan numeric `Id`). Field yang diupdate: `AssetModelCode`, `AssetModelName`, `AssetNumber`, `SiteCode`, `SectionTypeCode`.
   - **Auto-resolve `AssetModelName`**: kalau `AssetModelName` kosong tapi `AssetModelCode` ada, handler panggil `AssetAPI.GetAssetModelByCodesAsync` (external call ke service `asset`) untuk ambil nama model sebelum disimpan.
2. **`TaskPersonalized`** — **semua** record di bawah `WorkOrder` ini (`GetByReferenceIdWithTaskAsync(request.WorkOrderId, ...)`, join ke `Task`) di-update `UserCode = request.Request.LaborPersonnelCode`. ⚠️ Ini blanket-update ke **seluruh** `TaskPersonalized` milik WorkOrder tsb, tidak discope ke satu `TaskPersonalizedId` tertentu — aman selama asumsi "1 WorkOrder Business Operational Form = 1 `TaskPersonalized`" (single-user, linear — lihat [flow submission](../form-submission.md#flow--form-submission--approval)) selalu benar. Kalau suatu saat ada multi-`TaskPersonalized` per WorkOrder BO form, semua record akan ketiban `UserCode` yang sama.
3. **`FormSubmission`** — kalau ada `TaskPersonalized` (langkah 2), ambil semua `FormSubmission` lewat `TaskId` dari `TaskPersonalized` tsb, lalu update **3-dimensi asset**: `AssetBrandCode`, `AssetTypeCode`, `AssetVariantCode`. Ini mengonfirmasi dugaan sebelumnya soal [known gap 4-dimensi vs 3-dimensi](../form-submission.md#schema-tabel-formsubmission) — `AssetModelCode` memang tidak ditulis ke `FormSubmission` (cuma ke `WorkOrder`).

**Field yang dikirim tapi tidak dipakai:** `SectionId` (`"S095"`, section organisasi user) ada di request body tapi **tidak direferensikan sama sekali** di handler ini — tidak ditulis ke `WorkOrder`, `TaskPersonalized`, maupun `FormSubmission`. Kemungkinan cuma dipakai di layer lain (mis. otorisasi) atau memang dead field untuk endpoint ini.

Endpoint `/save/offline` ini **belum pernah didokumentasikan** sebelumnya di [form-submission.md](../form-submission.md) — baru muncul di trace ini.

### 2.2 — Cosmos: `form-submission/structure/tab`

**Endpoint:** `POST /maintenance-execution/api/form-submission/structure/tab?submissionTabId={FormSubmissionTabId}&ver=v1`

> ⚠️ **Catatan:** `submissionTabId` pada trace ini (`06505bf6-5488-4e12-a3ff-12824e324c50`) **tidak match** dengan GUID tab General dari response step 1 (`6fa4a1d1-a00a-41e7-8695-2eeec73ec8ad`), dan request time-nya juga terpaut ~28 menit dari step 2.1. Kemungkinan trace ini diambil dari sesi/transaksi percobaan yang berbeda (form yang sama — `WICOPECHECK_WASHING` — tapi instance berbeda), bukan chaining langsung dari step 1. Pola API-nya tetap representatif, tapi jangan asumsikan ID-nya berantai satu sama lain.

Request body (disingkat — body asli mengirim **seluruh isi tab**, bukan cuma field yang baru diisi):

```json
{
  "id": "",
  "sections": [
    {
      "sectionId": "00000000-0000-0000-0000-000000000001",
      "title": "Nama Observer",
      "elements": [
        {
          "elementCode": "LABOURPERSONNEL",
          "value": "{'userCode': '2009OBH.supervisor02@protonmail.com', 'siteId': '2009', ...}",
          "valueCaption": "2009OBH.supervisor02",
          "isShow": true
        },
        { "elementCode": "ACTUALSERVICESTART", "value": "2026-08-06T08:32:49.903067", "isShow": false },
        { "elementCode": "SHIFT", "value": "", "isShow": false }
      ]
    },
    {
      "sectionId": "00000000-0000-0000-0000-000000000002",
      "title": "Asset Information",
      "elements": [
        { "elementCode": "SITE", "value": "2009", "valueCaption": "IPR", "isShow": true },
        {
          "elementCode": "ASSETNUMBER",
          "value": "{'assetNumber': 'HDCT78003', 'assetTypeCode': 'AT0007', ...}",
          "valueCaption": "HDCT78003",
          "isShow": true
        },
        { "elementCode": "SECTION", "value": "OBH", "valueCaption": "OB HAULER", "isShow": true },
        { "elementCode": "WORKORDER", "value": "", "isShow": false },
        { "elementCode": "TEXTFIELD", "label": "Machine SMU Value", "value": "", "isShow": false },
        { "elementCode": "CAMERACAPTURE", "label": "Photo Machine SMU", "value": "", "isShow": false },
        { "elementCode": "TEXTFIELD", "label": "Hour Meter Offset", "value": "", "isShow": false }
      ]
    },
    {
      "sectionId": "00000000-0000-0000-0000-000000000003",
      "title": "WICOPE Quality Check",
      "elements": [
        { "elementCode": "CUSTOMCONTENT", "value": "<p>...instruksi WICOPE Quality Check...</p>" },
        { "elementCode": "DATETIME", "label": "Tanggal", "value": "", "valueType": "DATE_ONLY" },
        { "elementCode": "CUSTOMCONTENT", "value": "<p>...BMP &gt; 24HRS masuk kategori Scheduled Maintenance...</p>" },
        {
          "elementCode": "DROPDOWN",
          "label": "Breakdown Category",
          "caption": "['SCHEDULED MAINTENANCE']",
          "itemValue": "[1]",
          "value": ""
        }
      ]
    }
  ]
}
```

Response:

```json
{
  "result": {
    "isFormCompleted": false,
    "lastModifiedAt": "2026-08-06T01:34:47.9318926Z",
    "message": "FormSubmissionStructure saved successfully"
  }
}
```

**Observasi:**

- **Save-nya full overwrite per tab**, bukan delta per-field — seluruh section+elemen tab dikirim ulang tiap kali ada perubahan. **Dikonfirmasi dari source code:** `formStructure.Sections = request.Request.Sections` — seluruh `Sections` di Cosmos ditimpa langsung dari body request, tidak ada merge/diff.
- Field `id` di body kosong (`""`) — identifier tab ditentukan lewat query param `submissionTabId`, bukan body.
- Konfirmasi ulang known gotcha yang sudah dicatat di [form-submission.md](../form-submission.md#query--tab-general-flat-elements): `LABOURPERSONNEL.value` dan `ASSETNUMBER.value` berupa **object-literal string Python/JS-style** (single-quote, bukan JSON valid) — `StringToObject()` di Cosmos SQL API akan gagal parse ini. `DROPDOWN.caption` juga single-quote list string (`"['SCHEDULED MAINTENANCE']"`), pola yang sama dengan `PHOTOLIST.caption`.
- Field yang belum pernah disentuh user (`ACTUALSERVICESTART`, `SHIFT`, `WORKORDER`, `TEXTFIELD` Machine SMU, `CAMERACAPTURE`, `TEXTFIELD` Hour Meter Offset) semua `isShow: false` — konsisten dengan conditional visibility yang sudah didokumentasikan.
- Section **General tab form ini bukan cuma template shared** (`Nama Observer` + `Asset Information`, yang match [general-template-businessoperational.json](../examples/general-template-businessoperational.json)) — ada section tambahan **"WICOPE Quality Check"** yang spesifik ke form ini. Konsisten dengan catatan di [form-builder.md](../form-builder.md#mekanisme-general-tab-template) bahwa General tab adalah template shared yang isinya bisa beda-beda per form.

#### Server-side logic (2.2) — `SaveFormSubmissionStructureCommandHandler`

Handler ini menulis ke **SQL dan Cosmos secara berurutan, dalam 2 transaksi terpisah** (bukan 1 atomic transaction lintas database — wajar karena SQL dan Cosmos DB memang tidak bisa di-commit dalam 1 distributed transaction):

1. **Lookup paralel** (`Task.WhenAll`): `FormSubmissionTab` dari SQL via `GetByIdAsyncConn(request.FormSubmissionTabId, ...)` — **`FormSubmissionTabId` dipakai langsung sebagai PK (`Id`)**, bukan `ReferenceId` seperti `WorkOrder`. Kalau tidak ketemu → `DataNotFoundException`. Bersamaan, lookup dokumen `FormSubmissionStructure` existing di Cosmos via `GetByFormSubmissionTabIdAsync` — kalau belum ada (tab baru pertama kali disave), fallback ke `new()` (upsert-style).
2. **SQL transaction (terpisah, commit duluan):** update `FormSubmissionTab.IsCompleted` (dari `request.Request.IsCompleted` — field ini **tidak terlihat** di raw body trace step 2.2 yang sudah dicatat, kemungkinan optional/default `false`) + `ModifiedAt`/`ModifiedBy`, plus 1 audit log entry. Setelah commit, baca `FormSubmissionRepository.IsCompletedAsyncConn(formTab.FormSubmissionId, ...)` — **ini yang jadi nilai `isFormCompleted` di response**, dan itu status **level FormSubmission (seluruh form, semua tab)**, bukan status tab yang baru disave.
3. **Cosmos upsert (setelah SQL transaction sudah commit):** set `FormSubmissionId`, `FormSubmissionTabId`, `Title` (dari `formTab.Name`), `Sections` (full overwrite dari request), `ActiveFlag = true`. `CreatedBy`/`CreatedDate` cuma diisi kalau belum ada nilai sebelumnya (`??=` / `== default`) — dipertahankan across update. `LastUpdatedBy`/`LastUpdatedDate` selalu diupdate.

⚠️ **Catatan konsistensi:** Karena SQL (`FormSubmissionTab.IsCompleted`) commit duluan lalu baru Cosmos upsert (bukan 1 transaksi gabungan), ada window dimana **SQL sudah ter-update tapi Cosmos upsert gagal** (mis. network error/timeout ke Cosmos) — state jadi tidak konsisten (`IsCompleted` bilang selesai tapi jawaban form di Cosmos belum ter-simpan/masih versi lama). Belum ada retry/compensating-transaction yang terlihat di handler ini untuk kasus ini.

---

## Step 3 — Isi Tab Selain General (Washing, Safety)

User mengisi data di tab selain General (mis. Washing, Safety). **Belum ada trace API untuk step ini** — lihat [Open Questions](#open-questions--belum-dikonfirmasi).

---

## Step 4 — Submit Form

Setelah semua tab selesai diisi, user submit form. **Belum ada trace API untuk step ini** — lihat [Open Questions](#open-questions--belum-dikonfirmasi).

---

## Open Questions / Belum Dikonfirmasi

- **Step 3:** Apakah tab non-General (Washing, Safety) juga memicu SQL `save/offline` seperti General, atau cuma Cosmos `form-submission/structure/tab` saja (karena tab non-General kemungkinan tidak bawa field WorkOrder-level seperti asset/personnel)?
- **Step 4:** Endpoint submit form belum diketahui — apakah API terpisah (mis. `.../submit`), atau form otomatis dianggap complete saat semua `FormSubmissionTab.IsCompleted = true` (lihat `IsCompletedAsyncConn` di step 2.2)?
- Field request `IsCompleted` di endpoint `form-submission/structure/tab` (step 2.2) — tidak muncul di raw body trace yang sudah dicatat sebelumnya (cuma ada `id` dan `sections`), jadi belum jelas apakah field ini memang optional/default `false`, atau trace-nya kebetulan tidak menangkap field ini.
- Siapa/apa yang memakai field `SectionId` di request body step 2.1 — dikirim client tapi tidak direferensikan sama sekali di `SaveBoAdditionalWoDataOfflineCommandHandler` (beda dari step 1 dimana `SectionId` justru dipakai untuk resolve `SectionTypeCode` awal lewat `GetSectionTypeAsync`).

---

## Related Docs

- [Form Submission — Data Structure & Flow](../form-submission.md)
- [Form Builder](../form-builder.md)
- [SQL/Cosmos Data Consistency Issue (Step 2)](sql-cosmos-consistency-issue.md) — known issue soal 3 unit commit independen di step 2 (save/offline + form-submission/structure/tab) yang tidak terkoordinasi
