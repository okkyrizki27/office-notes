# Order Integration di Form

Dokumen ini merekam diskusi phase 2: bagaimana Form (task di dalamnya) terintegrasi dengan Order — trigger create Order saat jawaban suatu task mengindikasikan defect, mekanisme capture data finding, sampai timing & flow create Order-nya.

Struktur dokumen ini mengikuti urutan 6 fase di [order-integration-checklist.md](order-integration-checklist.md) supaya progress diskusi mudah ditelusuri.

*Last updated: 2026-08-13*

---

## Konteks

Phase 1 ([pm-shutdown-service-package.md](../phase1-service-package/pm-shutdown-service-package.md)) men-defer item **"Skenario field team menemukan pekerjaan tak terduga"** ke next MVP. Phase 2 ini membahas spesifik itu.

**Sifat enhancement ini (dikonfirmasi user):** UI Finding creation **sudah dibangun** di mobile app (lihat [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack) di bawah) tapi **belum functional** — form sudah ada dan fieldnya sudah match skema `TaskPersonalizedFinding`/`CrackIdentified`, tapi belum tersambung ke backend (persist data & trigger create Order). Jadi scope Phase 2 ini lebih ke **"aktifkan & sambungkan"** UI yang sudah ada, bukan desain UI dari nol.

Fakta current-state TaskKit General Check (7 tipe, opsi dropdown per tipe, struktur row) sudah didokumentasikan di [form-builder.md](../../architecture/form/form-builder.md#taskkit) — tidak diulang di sini, dokumen ini fokus ke keputusan & open items khusus Order Integration.

Baseline schema lain yang relevan:
- [form-submission.md](../../architecture/form/form-submission.md) — schema `TaskPersonalizedFinding`, `TaskResponseLog`
- [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) — flow Order/eMOL existing (sumber saat ini: Inspection & Additional Order saja)

---

## Order Integration Bersifat Form-Centric, Bukan Per-Fitur

Penting supaya scope tidak salah paham: integrasi Order ini **hook di level Form/Question**, bukan diimplementasikan terpisah per fitur pemanggil (Inspection/PM Shutdown/BD Corrective/pemanggil lain di masa depan). 1 Form terdiri dari N Question, tiap Question punya TaskKit type (lihat [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack) di bawah). Selama Question itu termasuk TaskKit yang punya opsi "Identified", integrasi Order terjadi **di manapun Form itu dipanggil** — karena mekanismenya menempel ke `TaskPersonalizedFinding` (layer Form, shared lintas fitur, lihat hierarki di [maintenance-execution-schema.md](../../architecture/database/maintenance-execution-schema.md)), bukan logic khusus per fitur.

Konsekuensinya: begitu PM Shutdown/BD Corrective memakai mekanisme Form standar dari Phase 1 (lihat [pm-shutdown-service-package.md](../phase1-service-package/pm-shutdown-service-package.md#apa-yang-migrasi-ke-maintenance-execution-apa-yang-tetap-di-dplandb) — Task/Backlog Execution di level Daily Plan tetap di `DPlanDB`, cuma Form yang migrasi ke `maintenance-execution`), Order Integration otomatis berlaku untuk mereka juga — **tidak perlu development terpisah per fitur**.

**Multi-mechanic per Form**: 1 Form bisa dikerjakan >1 mechanic (via "Assign to Me"/Supervisor assign) → membentuk multiple `TaskPersonalized` (1 per mechanic). Mechanic yang menjawab defect/crack found mengisi Finding + Order data di `TaskPersonalized` miliknya sendiri.

---

## Fase A — Scope & Trigger

*Apa saja yang bisa memicu Finding*

### Poin 1: Trigger dan UI Create Defect atau Crack

#### Scope Trigger Order — Keputusan Awal (dari User)

TaskKit yang akan terintegrasi dengan Order (create Order saat jawaban = defect):

- **Crack Defect**
- **Data Input**
- **Defect Check**

Dasar pemilihan: opsi dropdown-nya mengandung kata **"Identified"** (`Crack Identified: ...`, `Defect Identified`) — berbeda dari 4 TaskKit lain (Action Task, Assessment Check, Condition Check, Washing) yang **tidak** masuk scope meski opsinya juga bisa berarti "ada masalah" (`Not Comply`, `Not Ok`, `Dirty`).

#### Current State — Mobile App UI (v4.0.0)

Diverifikasi langsung dari screenshot app **Digiman+ mobile v4.0.0** (2026-08-06). **UI sudah ada tapi belum functional** — Save belum tentu persist data / trigger apapun ke backend.

**Trigger**

Di row Bank Task (task list dalam tab form), begitu user pilih opsi dropdown yang termasuk kategori "defect" (`Defect Identified` untuk Defect Check/Data Input, `Crack Identified: Monitor`/`Crack Identified: Repair Required` untuk Crack Defect), app navigasi ke screen terpisah berjudul **"Defect Identified"** — judul ini generic/shared, dipakai untuk ketiga TaskKit (termasuk Crack Defect, bukan "Crack Identified").

**Struktur Screen "Defect Identified"**

Screen ini adalah **satu form Finding shared**, dengan field tambahan khusus Crack Defect di bagian atas. Urutan top-to-bottom:

1. **Tab Finding #1 / Finding 2 / ...** — satu task row (satu `FormTaskCode`) bisa punya **lebih dari satu Finding** (tombol "+" untuk tambah Finding baru)
2. **Identitas user** (mis. `2009OBH.supervisor01`) + **evidence/foto** — "Add evidence through the camera or browse the taken image", 3 slot + tombol "Add More"
3. *(khusus Crack Defect)* **Crack Identified Description** — textarea, 0/500 char → `CrackIdentified.CrackDescription`
4. *(khusus Crack Defect)* **Crack Length** table — kolom Location (auto dari task description) / Previous / Current* (mm) → `CrackIdentified.PrevCrackLength` / `CrackLength`
5. **Defect Detail** — "Fill out this form with defect details":
   - **Component & Sub Component\*** → `TaskPersonalizedFinding.ComponentCode`/`SubComponentCode`
   - **Damage Code\*** → `DamageCode`
   - **Cause Code** (tidak wajib) → `CauseCode`
   - **Action Remedy\*** → `ActionRemedyCode`
6. **Immediate Execute Declaration** — checkbox: *"I confirm this inspection finding executable now. By checking this, your finding won't be processed into backlog."* → `IsImmediateExecutable`
7. **Priority\*** dropdown → `PriorityCode`
8. **Defect Notes** textarea, 0/100 → `DefectNotes`
9. **How Long Will This Defect Repair Take?\*** dropdown → `RepairDuration`
10. **Defect Repair Instructions / Actions** textarea, 0/200 → `RepairInstruction`
11. **Save**

Field di step 5 & 7–10 match 1:1 ke schema `TaskPersonalizedFinding` yang sudah terdokumentasi ([maintenance-execution-schema.md](../../architecture/database/maintenance-execution-schema.md)); step 3–4 match `CrackIdentified`. Defect Check (Task 25, diverifikasi terpisah) pakai form identik **tanpa** step 3–4 — mengonfirmasi field Crack itu addon khusus TaskKit, bukan form yang beda total per TaskKit.

#### Diskusi: Immediate Execute Declaration sebagai Gate Order

Konteks bisnis (dari user, 2026-08-12): teks checkbox *"By checking this, your finding won't be processed into backlog"* dinilai **kurang tepat** kalau dipakai sebagai satu-satunya gate penentu Order. Ada 2 makna "bisa dieksekusi sekarang" yang konsekuensinya beda:

1. **Defect kecil** — perbaikan mudah, mungkin tanpa material tertentu, waktu pengerjaan singkat.
2. **Defect critical** — harus diperbaiki saat itu juga karena kalau tidak bisa mengganggu performa unit atau menyebabkan unscheduled breakdown. Skenario ini **bisa tetap butuh material dan Order/WorkOrder SAP.**

**Analisis — 2 sumbu yang tercampur dalam 1 checkbox:**

| | Butuh Order? | Kapan dieksekusi? |
|---|---|---|
| Skenario 1 (kecil, no material) | Tidak | Sekarang |
| Skenario 2 (critical, butuh material/SAP WO) | Ya | Sekarang (tidak bisa tunggu) |

Teks checkbox saat ini cuma valid untuk Skenario 1. Untuk Skenario 2, Order tetap harus dibuat — bukan "tidak diproses", cuma tidak masuk antrian backlog normal.

**Sudah dikonfirmasi user (2026-08-12):**
- Defect **selalu tercatat** (Finding tetap dipersist ke `TaskPersonalizedFinding`) terlepas dieksekusi sekarang atau nanti — berlaku untuk kedua skenario.
- `PriorityCode` **tidak bisa dipakai** sebagai pengganti/pelengkap gate ini — kegunaannya beda: menentukan **expected delivery date** (kapan defect harus dieksekusi dalam siklus penjadwalan normal), bukan penentu "eksekusi instan di lapangan sekarang".

**Skenario 2 (critical) — detail per sub-kasus (2026-08-13):**

Skenario 2 ternyata perlu dipecah lebih lanjut tergantung apakah ada Order lama yang bisa di-reuse:

- **Sub-kasus A — Order lama sudah ada**, dari finding sebelumnya yang levelnya lebih rendah lalu eskalasi (pola sama dengan [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack); mekanisme correlation-nya di [Poin 6](#poin-6-duplicate-atau-correlation-handling)). Eksekusi fisik **non-blocking** (mechanic tidak perlu nunggu approval untuk mulai kerja) — tapi **trigger close/TECO Order ke SAP menunggu approval SPV/Planner selesai** dulu, bukan langsung setelah mechanic submit. Karena Order lama ini sudah pernah lolos approval saat pertama kali dibuat, tidak ada bypass approval yang dibutuhkan — functionally sama dengan backlog execution biasa, cuma dieksekusi lebih cepat dari jadwal aslinya.
- **Sub-kasus B — tidak ada Order lama**, dipecah lagi berdasarkan kebutuhan material:
  - **B1 (tidak butuh material)** — pola sama seperti Sub-kasus A: Order dibuat, mechanic eksekusi sekarang (non-blocking), masuk approval SPV/Planner post-hoc, begitu approved sistem create+close (TECO) ke SAP sekaligus.
  - **B2 (butuh material)** — **tidak bisa** pakai pola non-blocking di atas, karena keluarnya material dari logistic mensyaratkan Order/Reservasi SAP sudah ada & di-print duluan (proses fisik: Planner request ke logistic → print MO dari SAP → SPV/Foreman ambil material — proses ini **di luar sistem**). Arahnya: **tetap pakai flow Order → Approval → SAP standar** (tidak bikin jalur baru, supaya mudah dimaintain), cuma **dipercepat prioritasnya** (expedited) dibanding Order biasa. **Open item** — mekanisme percepatan/prioritas belum didesain, kemungkinan terkait visibility/sorting di [Fase F — Dashboard](#fase-f--dashboard).

**Masih open:**
- 4 TaskKit di luar scope (`Not Comply`/`Not Ok`/`Dirty`) — final by design, atau bisa diperluas nanti?
- Scope kerja "sambungkan backend" — breakdown detail: persist `TaskPersonalizedFinding`/`CrackIdentified` saja, atau juga trigger create `MechanicOrderList`/`MechanicOrderSummary`?
- Mekanisme percepatan/prioritas untuk Sub-kasus B2 (lihat di atas).
- **UI View detail (2026-08-13)** — journey/flow sudah disepakati, tapi tampilan layarnya sendiri belum dibahas: bentuk list suggestion Order lama (info apa yang ditampilkan supaya user yakin pilih yang benar), screen "Add Material" baru, **dan tampilan form setelah defect disubmit** (bagaimana defect yang sudah disubmit ditampilkan balik di form).

~~Crack Defect punya 2 opsi "Identified" (`Monitor` vs `Repair Required`) — apakah keduanya sama treatment?~~ — **resolved**: sudah dijawab di [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack) — keduanya sama-sama trigger Order, bedanya cuma priority.

#### User Journey — Defect (2026-08-13)

Scope: **Defect saja** — Crack dibahas terpisah nanti (skenarionya beda, lihat open item di bawah).

1. User find defect.
2. User jawab pertanyaan "Defect Identified".
3. Form defect muncul, diisi seperti [Current State — Mobile App UI](#current-state--mobile-app-ui-v400) (Component/SubComponent/DamageCode/dst, termasuk `IsImmediateExecutable`).
4. **Kalau `IsImmediateExecutable=Yes`** → sistem cari & tampilkan suggestion Order lama ([Poin 6](#poin-6-duplicate-atau-correlation-handling)) **duluan**, sebelum material:
   - **Ketemu & dipilih** → material **derived, read-only** dari Order lama (tidak bisa diedit — lihat catatan di bawah), user langsung submit.
   - **Tidak ketemu Order lama** (atau `IsImmediateExecutable=No`) → lanjut ke input material **manual/editable** seperti biasa, submit sebagai Order baru.
5. **Kalau `IsImmediateExecutable=No`** → submit seperti flow existing (skip correlation check), cuma ditambah step material.

**Material — UI baru dibutuhkan:** belum ada di current-state UI, perlu ditambah ("Add Material"). User journey untuk "butuh material" vs "tidak butuh" **dibuat sama** — reuse pola `NoPartsRequired` yang sudah ada di eMOL (declare "tidak butuh material" itu sendiri sudah opsi existing).

**Material saat reuse Order lama — read-only, edit di-defer:** kalau Order lama ke-pilih, material-nya **diderive dari Order lama** (bukan dari input user di Finding baru), dan **untuk sekarang tidak bisa diedit** — alasan: kalau dikasih ability edit, butuh jalur khusus baru untuk propagate perubahan itu ke SAP/ERP. Di-defer.

**Skenario "tidak ada Order lama" — dikonfirmasi bisa terjadi:** defect yang sama bisa saja pernah ditemukan di pekerjaan sebelumnya tapi **di-decline approver** (kapabilitas existing — approver sudah bisa decline defect) — sehingga tidak ada Order yang "masih open" untuk di-correlate meski defect-nya bukan baru pertama kali ketemu. Fallback: user submit sebagai Order baru (poin 4 di atas, cabang "tidak ketemu").

**Open item:** scope correlation untuk **Crack** tidak bisa dibatasi cuma jalan saat `IsImmediateExecutable=Yes` seperti Defect (beda dinamika — lihat [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack), Order tetap dibuat sejak level monitoring/rendah) — dibahas detail nanti pas sesi Crack.

---

### Poin 2: Defect di Luar Pertanyaan Form (Additional Defect saat Eksekusi)

Skenario: mechanic ketemu defect yang tidak ada pertanyaan relevannya di form yang sedang dikerjakan (mis. sedang inspeksi engine, nemu retak di frame yang bukan bagian checklist hari itu). Baseline flow existing untuk kasus ini adalah **Additional Order** (lihat [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) — `Type='Additional'`, tanpa `WorkOrderId`/`TaskPersonalizedFindingId`, semua field diisi manual).

**Dua opsi:**

- **Opsi A — Reuse Additional Order existing.** Fully decoupled dari WorkOrder/Task, tidak ada perubahan skema. Trade-off: hilang traceability ke WorkOrder asal ditemukannya defect, mechanic harus re-entry manual data asset/context yang sebenarnya sudah dia pegang saat itu.
- **Opsi B — Mekanisme baru "Add Finding" di dalam form berjalan**, tetap link ke WorkOrder/Task aktif. Trade-off: konsisten dengan prinsip [form-centric](#order-integration-bersifat-form-centric-bukan-per-fitur) yang sudah ditetapkan.

**Resolved (2026-08-13) — blocker data model Opsi B ternyata sudah tidak ada:** `TaskPersonalizedFinding.FormSubmissionTabId`/`FormTaskCode`/`FormTaskNumber` (field yang menunjuk ke Question/Tab spesifik) **ternyata nullable, dan bisa NULL ketiganya sekaligus** — skema **sudah mendukung** Finding yang tidak nempel ke Question manapun. `TaskPersonalized` (parent wajib, FK tidak nullable) tetap harus ada — jadi Finding baru nempel ke `TaskPersonalized` yang **sedang aktif dikerjakan** (WorkOrder/Task konteks berjalan), cuma 3 field penunjuk Question itu dibiarkan NULL. Relasi ke Form tetap bisa di-derive lewat `TaskPersonalized → Task → FormSubmission`, jadi tidak ada informasi yang hilang. **Tidak perlu Task "catch-all" baru, tidak perlu perubahan skema.**

Dengan blocker ini hilang, **Opsi B jadi arah yang jelas lebih unggul** (traceability terjaga, tanpa cost skema) dibanding Opsi A (Additional Order, decoupled).

**Status: Final — Opsi B.** Open item: butuh **UI/entry-point khusus** buat trigger "Add Finding" saat eksekusi form — beda dari trigger existing yang nempel di dropdown per-Question ([Current State UI](#current-state--mobile-app-ui-v400)), karena defect di poin ini justru **tidak** berasal dari Question manapun. Masuk ke daftar "UI View detail" yang sudah dicatat di [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack).

---

## Fase B — Aktor

*Belum dibahas — lihat [checklist](order-integration-checklist.md#fase-b--aktor).*

---

## Fase C — Data Model

*Jantung diskusi, paling banyak keputusan*

### Poin 5: Data Flow Defect dan Crack

#### Crack Order Lifecycle

**Crack — Order dibuat sejak tahap monitoring**

Crack yang terdeteksi sejak monitoring (crack masih sangat kecil) tetap **dibuatkan Order**, hanya saja dengan **priority rendah**.

**Crack — eskalasi ke critical saat inspeksi berikutnya**

Saat inspeksi berikutnya, crack yang sama bisa naik status jadi **critical**. Eksekusinya:

- Kalau Order dari temuan sebelumnya **masih open** → eksekusi pakai Order itu (bukan bikin baru).
- Kalau Order sebelumnya **sudah tidak open** → tetap push Order baru ke SAP.

> Catatan (2026-08-12): pola reuse-Order ini kemungkinan **generalisasi ke Defect biasa juga**, tidak eksklusif Crack — lihat diskusi Skenario 2 di [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack).

### Poin 6: Duplicate atau Correlation Handling

Foundational untuk keputusan reuse-Order di [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack), dan juga relevan untuk skenario Defect critical-escalation ([Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)).

**Correlation key (2026-08-13):** Asset + Component + SubComponent + **DamageCode**. DamageCode ditambahkan ke key karena relasi `SubComponent ↔ DamageCode` di master data bersifat **many-to-many** (lihat [query_mapping_damage_code.sql](../../query/query_mapping_damage_code.sql) & [master data Damage](../../../BUMA-ID-project/master-data/damage-code-all.csv)) — 1 SubComponent yang sama bisa punya beberapa DamageCode valid berbeda (mis. "Crack" dan "Corroded" di lokasi fisik yang sama), jadi Asset+Component+SubComponent saja berisiko salah gabung dua temuan yang sebenarnya tidak related.

**Mekanisme pencarian (2026-08-13):** bukan auto-match, bukan full-manual — **sistem (FE mobile) search & suggest** kandidat Order relevan, lalu **manusia yang pilih & validasi final** dari suggestion itu (mengingat bisa ada >1 Order open yang match). Yang bisa melakukan pemilihan: **siapapun yang sedang mengerjakan form tersebut** (mechanic/foreman/supervisor/dst), mengikuti permission yang sudah ada — tidak perlu permission baru (lihat [Fase B](#fase-b--aktor)).

**Yang berubah di Order lama kalau ketemu match (2026-08-13):** **tidak ada field yang diubah** — Order lama cukup **di-close**, dan closure ini wajib sync ke SAP/ERP. Detail timing & konsekuensi lengkap ada di [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack) (Sub-kasus A).

**Gap teknis — DamageCode tidak sampai ke SAP, MO Backlog tidak ter-link ke source (2026-08-13):**

Concern besar: `DamageCode` (dan ternyata juga `Component`/`SubComponent`) **tidak dikirim ke SAP** — sudah teridentifikasi sebagai gap di [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) (Bagian 4/§204, Open Items §428): field ini tersimpan di `PoolingMOItem` tapi tidak ada mapping ke BAPI (`GI_HEADER`/`GI_OPER`/`GI_COMP`). Ditambah, data "MO Backlog" (outstanding Order yang dipakai user sehari-hari) **murni berasal dari SAP** (§436) dan tidak terlihat ada join-back terdokumentasi ke row `MechanicOrderList` asal.

**Current state — mekanisme Outstanding Backlog yang sudah ada (2026-08-13):** ternyata sebagian besar dari yang dibutuhkan correlation **sudah jalan hari ini**, dipakai fitur "backlog execution" di layar Inspection (inspector pilih & eksekusi MO Backlog langsung saat inspeksi):

- **`MOOpen`** (service `maintenance-order`, pure data SAP) = source list outstanding backlog.
- **`BacklogExecutionList`** (service `maintenance-execution`) = record completion; begitu ada row aktif untuk `MONumber` tertentu, MO itu hilang dari list outstanding.
- Filter **"`MOOpen` minus `BacklogExecutionList`"** ini **sudah ada & jalan** (lintas service `maintenance-order` ↔ `maintenance-execution`) — bukan sesuatu yang perlu dibangun baru untuk correlation kita.
- `MOOpen` dan `PoolingMOItem` **sama-sama di service `maintenance-order`** — jadi join di antara keduanya **same-service**, bukan cross-service.
- Mekanisme ini secara natural **cuma mempertimbangkan record yang sudah punya `MONo`** (masuk akal — `MOOpen` diisi dari SAP, jadi mustahil punya entri untuk Order yang belum pernah di-push).

**Resolusi (2026-08-13):** correlation ternyata tidak butuh DamageCode sampai ke SAP sama sekali, dan tidak perlu bangun pathway baru — cukup:

1. Tambah kolom **Name** (bukan cuma Code) di `maintenance-order.MechanicOrderDetail`: `ComponentName`, `SubComponentName`, `DamageName`, `CauseName`, `ActionRemedyName`.
2. Propagate seluruh field Code+Name (poin 1) ke `PoolingMOItem` — saat ini `PoolingMOItem` cuma punya sebagian (Component/SubComponent/DamageGroup/DamageCode berisi Name, tanpa Cause/ActionRemedy sama sekali).
3. **Join `MOOpen` ↔ `PoolingMOItem`** by `MONumber`/`MONo` (same-service, `maintenance-order`) — begitu ini ada, list outstanding backlog yang sudah ada otomatis bisa dipakai untuk correlation matching by DamageCode dkk, numpang ke filter `MOOpen`-minus-`BacklogExecutionList` yang sudah jalan.

Rantai lengkap correlation "apakah Order masih open":

```
MechanicOrderList (Finding/Order asal, + DamageCode dkk via MechanicOrderDetail)
   → PoolingMOItem.PoolingId
      → SAPMOSyncOrder.MONo  (nomor MO dari SAP, NULL kalau belum sync)
         ≈ MOOpen.MONumber  (kalau masih ada di sini = masih outstanding, minus yang sudah di BacklogExecutionList)
```

- **`MONo` NULL** → belum sync ke SAP, masih di pipeline lokal Digiman+ → default **open**, kecuali ada state semacam Rejected/Cancelled di `MechanicOrderList` yang bikin dia mati meski `MONo` tidak pernah terisi. Ini satu-satunya bagian yang **genuinely baru** (tidak tercover mekanisme Outstanding Backlog existing, karena SAP tidak tahu apa-apa soal Order yang belum di-push).
- **`MONo` terisi** → status open/closed-nya **tinggal numpang** ke mekanisme Outstanding Backlog existing (`MOOpen` minus `BacklogExecutionList`) — tidak perlu logic baru sama sekali di sisi ini, cuma butuh join `PoolingMOItem` (poin 3 di atas) untuk dapat DamageCode dkk-nya.

**Open item:** apakah `MechanicOrderList` punya state Rejected/Cancelled yang perlu dikecualikan dari "open" saat `MONo` masih NULL, atau row yang ada (`IsActive=1`) otomatis selalu valid/in-progress tanpa perlu logic tambahan.

---

## Fase D — Proses/Workflow

### Poin 9: Approval Flow

#### Form Approval — sampai Foreman/Supervisor

Form (termasuk Finding/Defect di dalamnya) melalui approval berjenjang sampai level **Foreman/Supervisor**.

#### Defect Biasa — Lanjut Jadi Order di SAP Tergantung Planner

Defect dibuat oleh **mechanic**, termasuk pengisian **material**. Apakah defect ini **dilanjutkan jadi Order di SAP** ditentukan oleh **Planner** — Planner adalah gate approval Order sebelum push ke SAP.

> **Resolved (2026-08-13):** untuk Skenario 2 critical di [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack), gate Planner **tetap berlaku, tidak ada bypass** — approval cuma didekopel dari eksekusi fisik (non-blocking), bukan dihilangkan. Detail per sub-kasus (Order lama ada / tidak ada, butuh material atau tidak) ada di Poin 1.

**Masih open (2026-08-13):** UI approval — bagaimana SPV/Planner **melihat & bertindak** atas Order yang statusnya "sudah dieksekusi, approval post-hoc" (Sub-kasus A/B1 di Poin 1) — apakah perlu indikator visual yang beda dari Order normal yang belum dieksekusi, supaya approver sadar ini bukan approval blocking biasa.

---

## Fase E — Integrasi

*Belum dibahas — lihat [checklist](order-integration-checklist.md#fase-e--integrasi).*

## Fase F — Dashboard

*Belum dibahas — lihat [checklist](order-integration-checklist.md#fase-f--dashboard).*

---

## Related Docs

- [order-integration-checklist.md](order-integration-checklist.md) — kerangka kerja & progress diskusi Phase 2 (14 poin, 6 fase)
- [pm-shutdown-service-package.md](../phase1-service-package/pm-shutdown-service-package.md) — phase 1, sumber deferred item yang jadi latar belakang phase 2 ini
- [form-builder.md](../../architecture/form/form-builder.md) — struktur TaskKit & Bank Task row (fakta current-state lengkap)
- [form-submission.md](../../architecture/form/form-submission.md) — schema `TaskPersonalizedFinding`, `TaskResponseLog`
- [maintenance-execution-schema.md](../../architecture/database/maintenance-execution-schema.md) — DDL real `TaskPersonalizedFinding`, `CrackIdentified`, `BacklogExecutionList`
- [maintenance-order-schema.md](../../architecture/database/maintenance-order-schema.md) — DDL real `MechanicOrderList`, `SAPMOSyncOrder`, `PoolingMOItem`, dll
- [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) — flow Order/eMOL existing, gap DamageCode/Component tidak sampai ke SAP
