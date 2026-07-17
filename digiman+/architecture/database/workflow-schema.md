# Database Schema — `workflow`

*Sumber: DDL script asli (`workflow.sql`), schema `dbo`, script date 15/07/2026 2:11 PM — skema real, bukan document-derived.*
*Disimpan: 16 Jul 2026.*
*DB: `mkp_workflow` (nama generik per konvensi — lihat [[project_db_naming_convention]]) — lihat [`workflow.md`](../workflow.md) untuk narasi/business logic.*

---

Dokumen ini referensi mentah struktur tabel `workflow`. Untuk narasi/business logic (state machine, level approval, dst), lihat [`workflow.md`](../workflow.md) — dokumen itu ditulis dari hasil diskusi/konfirmasi bisnis-teknis, **bukan** dari DDL real seperti dokumen ini. Ada beberapa tabel & detail di bawah yang **belum pernah disebut** di `workflow.md` — lihat catatan ⚠️ di tiap section dan ringkasan di "Observasi Belum Dibahas".

---

## Workflow Definition (Master)

### `Workflow`
```
Id             PK, bigint, identity
Code           varchar(64), not null
TriggerName    varchar(128), null
Description    varchar(512), null
Version        int, not null
EffectiveDate  datetime, null
IsActive       bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **⚠️ Tabel ini belum pernah disebut di [`workflow.md`](../workflow.md) sama sekali.** Ini master definisi workflow tingkat atas — **versioned** (`Version`, `EffectiveDate`) dan **trigger-based** (`TriggerName`). `workflow.md` langsung mulai dari `WorkflowStep`/`WorkflowSite` seolah itu titik teratas, padahal `WorkflowSite.WorkflowId` (lihat di bawah) menunjukkan `Workflow` ini adalah root-nya. Implikasi: satu `TriggerName`/`Code` bisa punya multiple `Version` — perlu diklarifikasi versi mana yang "aktif"/dipakai (kemungkinan kombinasi `IsActive` + `EffectiveDate`, belum dikonfirmasi).

### `WorkflowSite`
```
Id           PK, bigint, identity
WorkflowId   bigint, null   ← FK ke Workflow.Id
SiteCode     varchar(64), null
IsActive     bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **⚠️ Koreksi penting ke [`workflow.md`](../workflow.md)**: dokumen itu men-deskripsikan `WorkflowStep.WorkflowSiteId` seolah `WorkflowSiteId` adalah representasi langsung "Site/tenant context". **Realitanya `WorkflowSite` adalah tabel mapping tersendiri** (`Id` PK sendiri) yang menghubungkan `Workflow` (master, versioned) ↔ `SiteCode`. Konsekuensi: `WorkflowStep.WorkflowSiteId` sebenarnya FK ke **baris mapping ini**, bukan ke site code secara langsung — dan karena `Workflow` itu versioned, kemungkinan ada **lebih dari satu `WorkflowSite` row untuk `SiteCode` yang sama** (beda `WorkflowId`/versi/trigger). Ini butuh diklarifikasi ke engineer sebelum narasi "jumlah level bisa berbeda per site" di `workflow.md` dianggap lengkap — kemungkinan lebih tepatnya "berbeda per kombinasi Workflow+Site".

### `WorkflowStep` (master)
```
Id               PK, bigint, identity
WorkflowSiteId   bigint, null   ← FK ke WorkflowSite.Id (lihat koreksi di atas)
Name             varchar(128), null
StepOrder        int, null
MinApprover      int, not null
IsActive         bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **Konfirmasi** — struktur & kolom (`Name`, `StepOrder`, `MinApprover`) cocok dengan yang sudah didokumentasikan di `workflow.md`. Catatan baru: `WorkflowSiteId` dan `StepOrder` sama-sama **nullable** di skema real (bukan implisit NOT NULL seperti kesan di narasi doc).

### `WorkflowStepApprover`
```
Id               PK, bigint, identity
WorkflowStepId   bigint, null
ApproverType     varchar(10), null
ApproverCode     varchar(128), null
IsActive         bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **⚠️ Belum disebut di `workflow.md`**, tapi **mengkonfirmasi langsung** klaim di sana: *"satu level bisa punya lebih dari satu user eligible"* — ini tabelnya, 1 baris per approver eligible per `WorkflowStepId` (bukan kolom array/CSV). `ApproverType` (varchar(10)) mengindikasikan ada **lebih dari satu cara** menentukan approver (mis. user spesifik vs role/group) — nilai yang mungkin belum diketahui, perlu dicek ke data real atau engineer.

### `WorkflowActionProcess`
```
Code             PK, varchar(64)
Name             varchar(128), null
EndpointAPI      varchar(512), null
ServiceName      varchar(64), null
ActionMethod     varchar(10), null
IsActive         bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **⚠️ Belum disebut di `workflow.md`.** Tabel ini mendefinisikan **automated action** yang bisa dipanggil workflow — `EndpointAPI` + `ServiceName` + `ActionMethod` (kemungkinan `GET`/`POST`/dst, `varchar(10)` cukup untuk itu) terlihat seperti konfigurasi **webhook/callback ke service lain** saat suatu step tercapai. Constraint PK-nya bernama `PK_WorkflowStepProcess` — **tidak cocok** dengan nama tabel `WorkflowActionProcess`, indikasi tabel ini pernah di-rename tapi nama constraint lama tidak ikut diupdate (cosmetic, tidak mempengaruhi fungsi).

### `WorkflowStepAction`
```
Id                          PK, bigint, identity
WorkflowStepId              bigint, null
WorkflowActionProcessCode   varchar(64), null   ← FK ke WorkflowActionProcess.Code
ActionType                  varchar(32), null
IsActive                    bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **⚠️ Belum disebut di `workflow.md`.** Junction: menghubungkan `WorkflowStep` ke `WorkflowActionProcess` — jadi tiap step bisa trigger 0/lebih automated action. `ActionType` belum jelas bedanya dengan `ActionMethod` di tabel `WorkflowActionProcess` (nama mirip, tabel beda) — kemungkinan `ActionType` di sini semacam "kapan" (mis. `OnEnter`/`OnApprove`) vs `ActionMethod` yang HTTP method. Belum dikonfirmasi.

### `WorkflowStepActionTransition`
```
Id                       PK, bigint, identity
WorkflowStepActionId     bigint, null
NextWorkflowStepId       bigint, null
PriorityCondition        int, null
Condition                varchar(max), null
IsActive                 bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **⚠️⚠️ Temuan paling signifikan — berpotensi mengoreksi bagian "State Machine (Confirmed)" di `workflow.md`.** `workflow.md` menyatakan alur approval **linear murni** berdasarkan `StepOrder` ("alur hanya maju. Tidak ada percabangan mundur ke step sebelumnya"). Tapi tabel ini punya `Condition` (varchar(max), kemungkinan ekspresi) + `PriorityCondition` (urutan evaluasi) + `NextWorkflowStepId` — struktur ini adalah pola **conditional/dynamic step routing** (step berikutnya ditentukan oleh kondisi, bukan cuma `StepOrder + 1`). Ini **tidak berarti otomatis kontradiksi** dengan narasi existing (bisa saja saat ini semua `Condition`-nya trivial/selalu true, jadi efeknya tetap linear) — tapi kapabilitas conditional branching **ada** di skema, belum tercermin di narasi state machine manapun. **Perlu dikonfirmasi ke engineer**: apakah fitur ini aktif dipakai (ada `Condition` non-trivial di data real), atau murni skema yang disiapkan untuk masa depan tapi belum dipakai.

---

## Workflow Execution (Transactional)

### `WorkflowTransaction` (header)
```
Id                       PK, bigint, identity
WorkflowSiteId           bigint, not null
ReferenceTransactionId   bigint, null
TransactionType          varchar(32), null
CurrentWorkflowStepId    bigint, null
Name                     varchar(200), null
Payload                  varchar(max), null
Status                   varchar(32), null
LastAction               varchar(32), null
IsActive                 bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **Konfirmasi** — cocok persis dengan yang sudah didokumentasikan di `workflow.md` (termasuk risk `TransactionType` yang sudah dicatat di sana). Catatan tambahan: `ReferenceTransactionId` **nullable** (bukan implisit NOT NULL).

### `WorkflowTransactionStep`
```
Id                      PK, bigint, identity
WorkflowTransactionId   bigint, not null
WorkflowStepId          bigint, null
Status                  varchar(32), null
IsActive                bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **Konfirmasi** — cocok dengan `workflow.md`.

### `WorkflowTransactionUser`
```
Id                          PK, bigint, identity
WorkflowTransactionStepId   bigint, null
UserCode                    varchar(128), null
IsActive                    bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> **⚠️ Belum disebut di `workflow.md` — tapi kemungkinan besar inilah data "target approver" yang menurut doc itu "sengaja tidak ditampilkan ke user/report".** Beda dari `WorkflowStepApprover` (master, definisi siapa yang *eligible* di level step manapun secara umum), tabel ini per-**transaksi** (`WorkflowTransactionStepId`) — kemungkinan snapshot resolusi aktual "siapa saja yang eligible approve instance transaksi ini" (hasil ekspansi dari `ApproverType`/`ApproverCode` master jadi daftar `UserCode` konkret). Perlu dikonfirmasi ke engineer, tapi ini titik data yang relevan kalau suatu saat business berubah pikiran mau menampilkan target approver di report.

### `WorkflowExecutionLog`
```
Id                      PK, bigint, identity
WorkflowTransactionId   bigint, not null
WorkflowStepId          bigint, null
Type                    varchar(32), null
Message                 varchar(max), null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
```
> **⚠️ Belum disebut di `workflow.md`.** Pure log (tanpa `IsActive`/`ModifiedAt`/`ModifiedBy`) — kemungkinan log teknis/debug (`Type` + `Message` bebas) untuk troubleshooting eksekusi workflow, bukan audit trail bisnis (beda dari `WorkflowHistory` di bawah).

### `WorkflowHistory`
```
Id                          PK, bigint, identity
WorkflowTransactionStepId   bigint, not null
ActionBy                    varchar(128), null
ActionAt                    datetime, null
ActionType                  varchar(32), null
Remarks                     varchar(1024), null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
```
> **⚠️ Belum disebut di `workflow.md` — kemungkinan sumber audit-trail yang lebih lengkap daripada yang diasumsikan doc itu.** `workflow.md` bilang "siapa & kapan approve" cukup dibaca dari `WorkflowTransactionStep.ModifiedBy`/`ModifiedAt` — tapi itu cuma **1 nilai terakhir per step** (di-overwrite tiap perubahan status). Tabel `WorkflowHistory` ini punya `ActionBy`/`ActionAt`/`ActionType`/`Remarks` per baris — kemungkinan **1 baris per aksi** (bukan overwrite), jadi bisa merekam **riwayat lengkap** (mis. kalau ada multiple `MinApprover` di 1 step, tiap approver yang approve tercatat baris sendiri, bukan cuma yang terakhir). Ini lebih relevan untuk kebutuhan audit trail/report dibanding cuma baca `ModifiedBy` — perlu dicek apakah tabel ini sudah dipakai di SQL report manapun.

---

## Delegation

### `Delegation`
```
Id               PK, bigint, identity
DelegatorCode    varchar(128), null
DelegateeCode    varchar(128), null
StartDate        datetime, null
EndDate          datetime, null
Status           varchar(32), null
IsActive         bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> Approver bisa **mendelegasikan** wewenang approval ke user lain untuk periode tertentu (`StartDate`/`EndDate`). **✅ Dikonfirmasi (16 Jul 2026): skema disiapkan untuk kebutuhan masa depan, fiturnya belum pernah dibuild.** Jadi delegasi **tidak aktif** — tidak memengaruhi resolusi approver saat ini, aman diabaikan dari logic/report manapun sampai fitur ini benar-benar diaktifkan.

### `DelegationTransactionType`
```
Id               PK, bigint, identity
DelegationId     bigint, not null
TransactionType  varchar(32), null
IsActive         bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> Scoping delegasi per `TransactionType` — 1 `Delegation` bisa berlaku untuk beberapa jenis transaksi (atau dibatasi ke jenis tertentu saja). Konsisten dengan `TransactionType` yang juga dipakai di `WorkflowTransaction` untuk membedakan jenis transaksi (Order/eMOL vs lainnya).

---

## Config & Misc

### `Configuration`
```
Id             PK, bigint, identity
TenantCode     varchar(200), null   ← nullable, beda dari asset.Configuration yang NOT NULL
Key            varchar(200), null
Description    varchar(200), null
Value          varchar(max), null
IsActive       bit, not null
CreatedAt, CreatedBy   datetime/varchar(200), not null/null
ModifiedAt, ModifiedBy datetime/varchar(200), null
```
> `TenantCode` **nullable** di sini — beda dari [`services-asset-schema.md`](services-asset-schema.md) `Configuration.TenantCode` yang **NOT NULL**. Pola replikasi-per-service dengan variasi shape (sama seperti temuan `Feature` sebelumnya) — konsisten dengan observasi bahwa tabel-tabel umum ini **tidak** benar-benar shared, tiap service punya versi sendiri yang bisa sedikit berbeda constraint-nya.

### `PredefinedParameter`
```
Code             PK, varchar(128)
Name             varchar(256), not null
WorkflowCode     varchar(64), not null   ← FK ke Workflow.Code
IsActive         bit, not null
CreatedAt, CreatedBy   datetime/varchar(128), not null/null
ModifiedAt, ModifiedBy datetime/varchar(128), null
```
> **⚠️ Belum disebut di `workflow.md`.** Scoped per `Workflow` (lewat `WorkflowCode`) — kemungkinan daftar parameter/variable yang tersedia untuk dipakai di `WorkflowStepActionTransition.Condition` (ekspresi kondisi) atau di `Payload` `WorkflowTransaction`. Fungsi persisnya belum dikonfirmasi.

### `WorkflowLogic`
```
Id             PK, bigint, identity
GroupCode      varchar(64), not null
LogicKey       varchar(128), not null
IsActive       bit, not null
CreatedAt, CreatedBy   datetime/varchar(128), not null/null
ModifiedAt, ModifiedBy datetime/varchar(128), null
```
> **⚠️ Belum disebut di `workflow.md`, fungsinya belum jelas.** Tidak ada kolom yang menjelaskan isi "logic"-nya (tidak ada `Value`/`Expression`) — kemungkinan cuma flag/registry (`GroupCode` + `LogicKey` sebagai identifier gabungan), dipakai di tempat lain (kode aplikasi) untuk lookup logic mana yang aktif per grup. Perlu dicek ke engineer.

---

## Audit & System

### `AuditLog`
```
Id             PK, bigint, identity
TableName      nvarchar(256), not null
DataId         bigint, not null
Action         nvarchar(256), not null
PreviousData   nvarchar(max), null
IsActive       bit, not null
CreatedAt, CreatedBy   datetime/varchar(256), null
```
Pola sama dengan `asset.AuditLog` ([`services-asset-schema.md`](services-asset-schema.md)) — tanpa `ModifiedAt`/`ModifiedBy` (event log, bukan entity biasa).

### `TopicPublishLog`
```
Id               PK, bigint, identity
TopicName        varchar(200), not null
MessagePayload   varchar(max), not null
TenantCode       varchar(200), null
IsPublished      bit, not null
PublishedAt      datetime, null
CreatedAt        datetime, not null
RetryCount       int, not null
ErrorMessage     varchar(max), null
TraceId          varchar(100), null
ParentSpanId     varchar(100), null
```
> Pola outbox sama dengan service lain, tapi **shape lebih ramping** — tidak ada `CreatedBy`, `SessionId`, `Type` yang ada di versi `maintenance-order`/`maintenance-execution`/`asset`. Konsisten dengan temuan sebelumnya: tabel ini **direplikasi per-service dengan variasi shape**, bukan tabel shared.

*(Tidak ada tabel `Feature` di service ini — beda dari `asset`/`maintenance-execution`. Tidak dijelaskan apakah karena tidak dipakai atau sengaja tidak diadopsi service ini.)*

---

## Observasi Belum Dibahas

- **`Workflow` (master, versioned)** — root dari seluruh hierarki, tidak pernah disebut di `workflow.md`. Perlu diklarifikasi bagaimana versi aktif ditentukan.
- **`WorkflowSite` sebagai tabel mapping tersendiri** (bukan `WorkflowSiteId` = site code langsung) — berpotensi mengoreksi asumsi "level approval berbeda per site" di `workflow.md` jadi "per kombinasi Workflow+Site".
- **`WorkflowStepActionTransition.Condition`/`NextWorkflowStepId`** — indikasi kapabilitas conditional/dynamic step routing, berpotensi tidak selaras dengan narasi "alur hanya maju secara linear" di `workflow.md`. **Prioritas tinggi untuk diklarifikasi ke engineer.**
- ~~`Delegation`/`DelegationTransactionType` — kapabilitas delegasi approval~~ — **✅ dijawab (16 Jul 2026)**: skema disiapkan untuk masa depan, belum pernah dibuild fiturnya, tidak aktif.
- **`WorkflowTransactionUser`** — kemungkinan data konkret "target approver" yang menurut `workflow.md` sengaja tidak ditampilkan; sekarang jelas datanya memang ada, cuma tidak dipakai di UI/report.
- **`WorkflowHistory` vs `WorkflowTransactionStep.ModifiedBy`** — `WorkflowHistory` berpotensi audit trail yang lebih lengkap (multi-baris per step) dibanding cuma baca `ModifiedBy` (1 nilai, ke-overwrite). Perlu dicek dipakai atau tidak di SQL report existing.
- **`WorkflowActionProcess`/`WorkflowStepAction`** — kapabilitas trigger automated action (webhook/API call) per step, belum ada di narasi manapun.
- **`PredefinedParameter`/`WorkflowLogic`** — fungsi persisnya belum jelas, kemungkinan terkait evaluasi `Condition` di `WorkflowStepActionTransition`.
- **`PK_WorkflowStepProcess`** sebagai nama constraint di tabel `WorkflowActionProcess` — indikasi rename tabel yang tidak diikuti update nama constraint (cosmetic).

---

## Referensi
- [`workflow.md`](../workflow.md) — narasi/business logic state machine approval (document-derived dari diskusi, sekarang sebagian dikonfirmasi & sebagian perlu dikoreksi/diperluas berdasarkan DDL real ini)
- [`services-asset-schema.md`](services-asset-schema.md) — pola serupa (DDL real vs document-derived), termasuk temuan replikasi tabel umum (`Configuration`, `TopicPublishLog`) dengan shape berbeda per service
- [`vw_report_iams_f_am_digiman_dorder.sql`](../../report/transaction-report/vw_report_iams_f_am_digiman_dorder.sql), [`vw_report_iams_f_am_digiman_leadtime.sql`](../../report/transaction-report/vw_report_iams_f_am_digiman_leadtime.sql) — consumer SQL yang join ke `WorkflowTransaction` (lihat risk `TransactionType` di `workflow.md`)
