# Digiman+ — System Architecture Overview

*Last updated: 2026-08-04*

**Audiens:** Engineer baru (BE/FE/QA) yang butuh gambaran besar sistem Digiman+ sebelum masuk ke detail per-modul.

**Cara pakai dokumen ini:** Ini adalah **sintesis** dari dokumen-dokumen lain di folder `digiman+/architecture/` — bukan sumber baru. Setiap section punya link ke dokumen sumber untuk detail teknis lengkap (skema kolom, query, open items). Kalau ada perbedaan antara dokumen ini dan dokumen sumber yang di-link, **dokumen sumber yang benar** — sintesis ini bisa basi lebih cepat daripada dokumen per-modul yang lebih sering diupdate.

Beberapa bagian di bawah eksplisit ditandai **belum terverifikasi** — itu bukan kelalaian, tapi cerminan status pengetahuan yang sebenarnya (banyak bagian sistem ini didokumentasikan dari diskusi/DDL real secara bertahap, dan beberapa area masih punya open question yang dicatat di dokumen sumber).

---

## 1. Apa itu Digiman+

Digiman+ adalah platform pengelolaan maintenance alat berat (heavy equipment) untuk klien tambang (BUMA, MKP, dll). Cakupannya: inspeksi kondisi unit, perencanaan servis (Digiplan), eksekusi pekerjaan di lapangan (PM Shutdown, BD Corrective, Form Submission), sampai pembuatan order/permintaan material (eMOL) — yang kemudian terintegrasi dengan **SAP** sebagai ERP existing milik klien untuk procurement & work order resmi.

Sistem ini **multi-tenant** (BUMA ID, MKP, BUMA AU, dst — lihat [[project_digiman_teams]]) dan berjalan di **Web** (Planner, Admin HO, Approver) dan **Mobile** (Inspector, Mechanic, Supervisor/Foreman — **offline-first**).

---

## 2. Peta Layanan (Service Map)

| Service | Tanggung Jawab | Platform Utama | Database | Skema Terverifikasi? |
|---|---|---|---|---|
| `dplan` | Digital Planning: Daily Plan, Weekly Schedule/Backlog (Planner↔PSCM), sync MO sisi Digiplan sendiri, replikasi lokal User/Site/Equipment | Web | `DPlanDB` (SQL only, ~80 tabel) | ✅ DDL real (15 Jul 2026) |
| `maintenance-execution` | Eksekusi lapangan: **Inspection**, **PM Shutdown** (proxy), **BD Corrective**, **Form Submission** — hierarki `WorkOrder→Task→TaskPersonalized→TaskPersonalizedFinding` | Mobile (+sebagian Web) | SQL `cst-iams-sqldb-maintenance-execution` + Cosmos `MaintenanceExecution` | ✅ DDL real |
| `maintenance-strategy` | **Form Builder** (template form inspeksi/PM, versioned) + **CBM Config** (standar Condition-Based Monitoring) | Web | SQL `cst-iams-sqldb-maintenance-strategy` + Cosmos `MaintenanceStrategy` | ✅ DDL real |
| `maintenance-order` | **Order/eMOL** (permintaan material dari finding), middleware sync ke SAP (BAPI), inbound MO Backlog dari SAP | Web + Mobile | SQL (`order-script`) | ✅ DDL real |
| `services-asset` | Master data Asset/Equipment + taksonomi `Model→Component→SubComponent→DamageCode/CauseCode` | - (dikonsumsi service lain) | SQL `cst-iams-sqldb-services-asset` | ✅ DDL real |
| `usermanagement` | Auth, device/session, group, permission (access control) | - | SQL `usermanagement` | ✅ DDL real — **tapi lihat catatan §7**, DB ini murni auth, bukan employment profile |
| `workflow` | Engine approval multi-level generic, dipakai lintas-modul (`TransactionType` polymorphic) | - | SQL `mkp_workflow` (nama generik per [[project_db_naming_convention]]) | ✅ DDL real |
| `tenant` *(alias, belum ada dokumen schema sendiri)* | Master organisasi: Site, SectionType, OrganizationUnit | - | `cst-shared-sqldb-tenant` | ⚠️ Belum ada DDL real — hanya document-derived dari [`user-asset-relation.md`](user-asset-relation.md) |
| `user` *(alias, status dipertanyakan)* | Employment profile (SectionId, dept, dst) | - | `cst-shared-sqldb-user` | ⚠️ **Belum dikonfirmasi apakah DB ini benar-benar ada terpisah dari `usermanagement`** — lihat §7 |

---

## 3. Pola Arsitektur Lintas-Service

Pola-pola berikut berulang di banyak service — penting dipahami di awal karena tidak selalu terlihat jelas hanya dari baca satu skema service saja.

### a. Dual database per service (SQL + Cosmos DB)
`maintenance-execution` dan `maintenance-strategy` sama-sama pakai dua jenis DB: **SQL** untuk data terstruktur/relasional/metadata, **Cosmos DB** untuk dokumen JSON fleksibel (form template & form submission per tab). Form itu sendiri terlalu dinamis strukturnya (tab, section, element bertingkat) untuk dipetakan bersih ke tabel relasional, jadi kontennya di Cosmos; metadata (versi, status, assignment) tetap di SQL.

### b. Async messaging — outbox pattern via Service Bus
Pola yang konsisten di hampir semua service: publish → `TopicPublishLog` (outbox lokal) → Azure Service Bus → consumer service baca dari topic → `TopicConsumeLog` (kalau tercatat) → kalau gagal setelah retry, masuk `DeadLetterLog`. Dipakai untuk:
- `dplan` publish event `PlanSubmitted` ke `maintenance-execution` saat plan di-SUBMIT
- `maintenance-order` publish payload Order/eMOL ke consumer yang memanggil BAPI SAP (lihat §5)
- Beberapa service juga jadi **consumer**, bukan cuma publisher (mis. `dplan.TopicConsumeLog` — arah pesan masuknya belum terdokumentasi)

### c. SAP integration — payload message bus ≠ payload BAPI
**Temuan penting** (dikonfirmasi 16 Jul 2026): payload yang disimpan di `TopicPublishLog.MessagePayload` adalah **superset** — berisi banyak field (`HourMeter`, `Inspector`, `EquipmentModel`, dst). Tapi middleware yang memanggil BAPI SAP hanya mapping **subset** field tertentu ke `GI_HEADER`/`GI_OPER`/`GI_COMP`. **Field yang "ada di tabel" atau "ada di payload message bus" tidak otomatis berarti "terkirim ke SAP"** — selalu cek mapping BAPI aktual sebelum mengasumsikan sebuah field sampai ke SAP. Detail: [`order-emol-sap-sync.md`](inspection-order/order-emol-sap-sync.md) §6.

### d. Snapshot-copy-at-creation (pola immutability)
Dipakai luas untuk menjaga histori data tetap stabil meski master/template berubah belakangan:
- **Form template** → di-copy dari `FormStructure` (Cosmos, `maintenance-strategy`) ke `FormSubmissionStructure` (Cosmos, `maintenance-execution`) saat transaksi form dibuat — form yang sudah diisi user tidak berubah meski template di-update ke versi baru.
- **Finding → eMOL Detail** — `maintenance-execution.TaskPersonalizedFinding` di-snapshot-copy ke `maintenance-order.MechanicOrderDetail` saat eMOL dibuat (field `IsImmediateExecutable`/`DeleteNotes` sengaja **tidak** ikut ter-copy).
- **Finding Evidence → eMOL Evidence** — pola sama, `TaskPersonalizedEvidence` → `MechanicOrderEvidence`.

Konsekuensi: **data di sisi eMOL/Order tidak live-sync ke sumber aslinya** — begitu di-copy, dua sisi bisa divergen tanpa mekanisme sinkron balik.

### e. Offline-first mobile
Tabel-tabel eksekusi (`Task`, `TaskPersonalized`, `TaskPersonalizedFinding`, dst.) punya kolom `LastSyncedAt`/`LastSyncedBy`/`LastSyncedModifiedAt`/`LastSyncedModifiedBy`, plus tabel `OfflineLog` (di `dplan`) untuk mencatat API call yang terjadi saat device offline. Mobile app bisa bekerja tanpa koneksi dan sync belakangan — ini **capability yang sudah ada**, bukan rencana, dan harus dipertimbangkan di setiap desain fitur baru untuk mobile.

### f. Multi-tenant via `TenantCode` — enforcement tidak konsisten
Banyak tabel infrastruktur (`Configuration`, `DeadLetterLog`, `TopicPublishLog`) punya kolom `TenantCode`, tapi:
- Ada yang `NOT NULL` (`services-asset.Configuration`), ada yang nullable (`usermanagement.Configuration`, `workflow.Configuration`)
- Ada tabel yang **secara konsep** per-client tapi **tidak punya kolom `TenantCode` sama sekali** (mis. `services-asset.ClientAssetMapping`) — mekanisme isolasi datanya belum jelas
- `usermanagement.UserPermission.TenantCode` bahkan hardcode default `'BUMAID'`

**Jangan asumsikan semua tabel otomatis terisolasi per tenant** — cek kolom & constraint aktualnya per tabel.

### g. Nama tabel yang sama ≠ tabel yang shared
`Configuration`, `Feature`, `AuditLog`, `TopicPublishLog` muncul dengan nama identik di hampir semua service — tapi masing-masing adalah **tabel terpisah dengan shape yang bisa berbeda** (kolom beda, constraint beda, nullable beda). Contoh: `maintenance-execution.Feature` punya `PermissionCode`, sementara `services-asset.Feature` punya `Description`/`Status` — bukan tabel yang sama direplikasi identik. **Jangan asumsikan skema salah satu versi berlaku untuk service lain.**

---

## 4. Alur Inti: Inspection → Order → SAP → MO Backlog → Eksekusi

Ini adalah siklus data paling sentral di Digiman+ — melibatkan 3 service (`maintenance-execution`, `maintenance-order`, `dplan`) dan SAP sebagai sistem eksternal. Detail lengkap: [`order-emol-sap-sync.md`](inspection-order/order-emol-sap-sync.md).

```
┌──────────────────┐
│ 1. Inspection      │  maintenance-execution
│    (input Finding) │  WorkOrder → Task → TaskPersonalized → TaskPersonalizedFinding
└─────────┬──────────┘
          │  submit
          ▼
┌──────────────────┐
│ 2. Order / eMOL    │  maintenance-order
│    (edit material,│  MechanicOrderSummary → MechanicOrderList (eMOL)
│    atau declare    │  Finding di-snapshot-copy ke MechanicOrderDetail
│    "no parts")     │
└─────────┬──────────┘
          │  submit → masuk Approver
          ▼
┌──────────────────┐
│ 3. Approval        │  workflow (generic engine, lihat §6)
│    (bisa edit saat │  Approver bisa ubah data, bukan approve-only
│    approve)        │
└─────────┬──────────┘
          │  approved
          ▼
┌──────────────────┐
│ 4. Build & publish  │  maintenance-order: PoolingMOItem (staging) →
│    payload SAP      │  SAPMOSyncOrder (tracking) → TopicPublishLog (outbox)
└─────────┬──────────┘
          │  Service Bus → BAPI call
          ▼
┌──────────────────┐
│ 5. SAP memproses MO │  BAPI: GI_HEADER / GI_OPER / GI_COMP (subset field, lihat §3c)
└─────────┬──────────┘
          │  MO selesai diproses SAP
          ▼
┌──────────────────┐
│ 6. MO Backlog       │  Balik ke Digiman+ via MOOpen (maintenance-order)
│    (inbound)        │  Filter Order Type/PM Activity Type — per 17 Jul 2026,
│                     │  filtering dipindah ke sisi tenant/middleware, bukan lagi
│                     │  konfigurasi Digiman+
└─────────┬──────────┘
          │  dieksekusi lewat salah satu dari 3 jalur:
          ├──► sub-task di Digiplan → PM Shutdown
          ├──► sub-task di Digiplan → BD Corrective
          └──► langsung saat Inspection (pekerjaan ringan/cepat)
          │
          ▼
┌──────────────────┐
│ 7. TECO ke SAP      │  Setelah eksekusi selesai, kirim Technical Completion
└──────────────────┘
```

**Catatan arsitektur penting:**
- **Dua/tiga jalur sync SAP paralel yang independen**: `maintenance-order.SAPMOSyncOrder` (tag `DOrder`), `dplan.SAPMOSynchronization` (MO dieksekusi lewat Digiplan langsung, jalur sendiri), `maintenance-execution.SAPMOSyncInspection` (tag `DInspect`). **Belum dikonfirmasi apakah ketiganya saling overlap atau benar-benar independen** — jangan asumsikan salah satu tahu soal state yang lain.
- Prinsip arsitektur eksplisit dari business (10 Jul 2026): **Digiplan sengaja tidak dibuat terintegrasi langsung ke Order** — data plan (Component/SubComponent/Area/Duration/Man Power) dialirkan lewat SAP (create Order → SAP → balik sebagai MO Backlog), bukan lewat integrasi langsung Digiplan↔Order, supaya tidak ada jalur ketiga yang redundan.
- Gap yang sudah diketahui: `Component`/`SubComponent` sudah tersimpan di `PoolingMOItem` tapi **belum ada mapping-nya ke BAPI** — belum benar-benar terkirim ke SAP hari ini.

---

## 5. Form Architecture: Builder → Submission

Dua service kerjasama untuk seluruh fitur berbasis form (Inspection, PM Shutdown, BD Corrective, Form Submission self-service):

```
maintenance-strategy (authoring)              maintenance-execution (execution)
┌─────────────────────────────┐               ┌─────────────────────────────┐
│ Form (SQL, versioned,        │   di-copy     │ FormSubmission (SQL)         │
│ immutable — FormCode tetap,  │   saat        │  └─ FormSubmissionTab        │
│ Id berubah tiap versi)       │   transaksi   │                              │
│  └─ FormTab                  │   dibuat  ──► │ FormSubmissionStructure      │
│                               │               │ (Cosmos — full copy struktur │
│ FormStructure (Cosmos)        │               │  form + jawaban user)        │
│ TaskKit / ContentKit (Cosmos) │               │                              │
└─────────────────────────────┘               └─────────────────────────────┘
```

- **Dua Form Type**: `FT_MaintenanceForm` (wajib asset mapping — dipakai PM Shutdown/BD Corrective/Inspection) vs `FT_BusinessOperationalForm` (tanpa asset mapping — dipakai Form Submission self-service, tampil di mobile lewat konfigurasi `BusinessOperationalForm` di `maintenance-execution`).
- **Versioning immutable**: update form = row baru di SQL+Cosmos, bukan update in-place. `FormCode` tetap, `Id`/`Version` berubah.
- **Kenapa di-copy, bukan di-reference live**: supaya form yang sudah diisi user tetap merujuk struktur form pada saat transaksi terjadi — kalau cuma reference, form lama akan "rusak" tampilannya kalau template diupdate.

Detail lengkap: [`form-builder.md`](form/form-builder.md), [`form-submission.md`](form/form-submission.md).

---

## 6. Approval Workflow Engine (shared, generic)

Satu service (`workflow`) menyediakan **engine approval generic** yang dipakai lintas-modul — bukan logic approval terpisah per fitur.

```
Workflow (master, versioned, root)
  └─ WorkflowSite (mapping Workflow ↔ SiteCode)
        └─ WorkflowStep (level approval, StepOrder, MinApprover)
              ├─ WorkflowStepApprover (siapa eligible per level)
              └─ WorkflowStepAction → WorkflowActionProcess (automated action/webhook per step)

WorkflowTransaction (header, 1 per transaksi yang butuh approval)
  └─ WorkflowTransactionStep (1 per level, Status: Submitted → In Progress → Approved)
        └─ WorkflowTransactionUser (resolusi konkret "siapa eligible" untuk instance ini)
```

- **Polymorphic** lewat kolom `TransactionType` — satu tabel dipakai lintas jenis transaksi (Order approval = `'Mechanic Order'`, Form Submission approval jenis lain). **Semua join ke `WorkflowTransaction` harus filter `TransactionType`** — beberapa SQL report existing pernah ketemu tanpa filter ini (risk false-positive match).
- **Jumlah level bisa berbeda per site** (lewat `WorkflowStep.WorkflowSiteId`) — tapi karena `Workflow` itu sendiri versioned, kemungkinan lebih tepatnya "berbeda per kombinasi Workflow+Site", bukan per site murni.
- ⚠️ **Belum dikonfirmasi**: skema punya `WorkflowStepActionTransition` (`Condition` + `PriorityCondition` + `NextWorkflowStepId`) yang mengindikasikan kapabilitas **conditional/dynamic routing** — tapi narasi bisnis yang ada bilang alur "hanya maju secara linear". Belum jelas mana yang aktif dipakai di production. **Jangan asumsikan alur approval pasti linear** sampai ini diklarifikasi ke engineer.
- Delegasi approval (`Delegation`/`DelegationTransactionType`) — skemanya ada tapi **dikonfirmasi belum pernah dibuild fiturnya**, aman diabaikan dari logic manapun untuk saat ini.

Detail lengkap: [`workflow.md`](workflow.md), [`database/workflow-schema.md`](database/workflow-schema.md).

---

## 7. Identity, Tenant & Asset Access Model

Model yang **dimaksudkan** (document-derived, belum 100% terverifikasi ke DDL real semua sisinya):

```
[user employment profile]
        │ SectionId
        ▼
[tenant.OrganizationUnit]  ◄──── SectionTypeCode ────  [tenant.SectionType]
        │ SectionTypeCode
        ▼
[services-asset.Asset]  ──── AssetModelCode ────►  [services-asset.AssetModel]
```

⚠️ **Dua ketidakpastian yang perlu diketahui sebelum bekerja dengan area ini:**

1. **Status DB `usermanagement` vs `cst-shared-sqldb-user`** — [`user-asset-relation.md`](database/user-asset-relation.md) mengasumsikan tabel `UserEmploymentProfile` (kunci relasi User→OrganizationUnit) hidup di DB `cst-shared-sqldb-user`. Tapi DDL real `usermanagement` ([`user-management-schema.md`](database/user-management-schema.md)) **tidak punya tabel ini sama sekali** — isinya murni auth/access-control. Kandidat kuat: tabel `dplan.User`/`dplan.StageUser` (yang justru **punya** kolom `SectionId`/`DepartmentId`/dst persis seperti yang dicari) mungkin cache/replika dari sumber aslinya — tapi ini **belum dikonfirmasi ke tim codebase**.
2. **Asset → OrganizationUnit** — `user-asset-relation.md` awalnya mengklaim relasi lewat `Asset.AssetModelCode = OrganizationUnit.SectionTypeCode`. DDL real menunjukkan `Asset` punya kolom **`SectionTypeCode` sendiri** (langsung, bukan derive dari Model) — kemungkinan relasi yang benar berbeda dari yang terdokumentasi. Juga belum diverifikasi.

**Implikasi praktis**: kalau kerja di area akses data user→asset (mis. onboarding model baru, debug "kenapa user tidak lihat data ini"), pakai [`new-model-checklist.md`](database/new-model-checklist.md) sebagai checklist operasional (sudah battle-tested), tapi jangan asumsikan diagram relasi di atas 100% akurat tanpa verifikasi tambahan ke engineer yang pegang codebase `tenant`/`user`/`usermanagement`.

---

## 8. Known Architecture Debt & Gotchas

Hal-hal yang akan membingungkan kalau tidak tahu di awal:

- **PM Shutdown = pure proxy.** API PM Shutdown ada di `maintenance-execution`, tapi hanya membungkus API `dplan` — **tidak ada data PM Shutdown yang disimpan di DB `maintenance-execution`**. Semua data hidup di `dplan`. Ini historis: Digiplan awalnya dibangun sebagai aplikasi terpisah dari Digiman+, dan effort untuk memperbaiki ini dianggap terlalu besar sehingga dipertahankan.
- **Banyak relasi tanpa FK constraint formal**, terutama di `dplan` (~24 FK eksplisit untuk ~80 tabel). Integritas relasi banyak bergantung pada aplikasi, bukan DB — jangan asumsikan ON DELETE CASCADE atau integrity check otomatis ada kalau belum dicek langsung ke DDL.
- **Constraint `PMActType varchar(5)` sempat jadi keputusan yang dibalik** (24 Jul 2026) — awalnya field `MaintenanceCategory.Code` dibatasi ≤5 char supaya muat constraint SAP legacy, lalu dibalik: kolom `PMActType` yang dilebarkan, bukan core-nya yang dibatasi. Prinsipnya: **batasan SAP hanya berlaku di boundary integrasi SAP**, tidak di-back-propagate jadi constraint global — Digiman+ didesain sebagai produk standalone/ERP-agnostic.
- **"Sudah ada di tabel" ≠ "sudah terkirim ke SAP"** — lihat §3c. Field seperti `HourMeter`/`InspectorCode`/`Component`/`SubComponent` sudah ada di beberapa tabel staging tapi belum tentu ikut mapping BAPI.
- **Snapshot-copy pattern (§3d) berarti data lama bisa "membeku"** — kalau ada bug di source data sebelum snapshot terjadi, memperbaiki source tidak akan memperbaiki data yang sudah ter-copy.

---

## 9. Peta Dokumen Lebih Dalam

| Topik | Dokumen |
|---|---|
| Ringkasan fitur & status per modul | [`current-state.md`](current-state.md) |
| Katalog enhancement/proposal aktif | [`README.md`](README.md) |
| Skema DDL real per service | `database/dplan-schema.md`, `database/maintenance-execution-schema.md`, `database/maintenance-order-schema.md`, `database/maintenance-strategy-schema.md`, `database/services-asset-schema.md`, `database/user-management-schema.md`, `database/workflow-schema.md` |
| Form Builder & Form Submission | `form/form-builder.md`, `form/form-submission.md` |
| Digital Planning (Daily Plan) | `dplan/digital-planning.md` |
| Order/eMOL ↔ SAP sync | `inspection-order/order-emol-sap-sync.md` |
| SAP → Digiman+ material master | `database/sap-material-integration.md` |
| Approval Workflow | `workflow.md` |
| Permission & Group | `permission.md` *(status: belum lengkap, TBD)* |
| User→Asset access & onboarding model baru | `database/user-asset-relation.md`, `database/new-model-checklist.md` |
| Homepage | `homepage/homepage-current-state.md` |
| PM Shutdown / BD Corrective | `pm-shutdown-bd-corrective/*.md` |
