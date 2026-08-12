# Order Integration di Form

Dokumen ini merekam diskusi phase 2: bagaimana Form (task di dalamnya) terintegrasi dengan Order — trigger create Order saat jawaban suatu task mengindikasikan defect, mekanisme capture data finding, sampai timing & flow create Order-nya.

Struktur dokumen ini mengikuti urutan 6 fase di [order-integration-checklist.md](order-integration-checklist.md) supaya progress diskusi mudah ditelusuri.

*Last updated: 2026-08-12*

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

**Sudah dikonfirmasi user:**
- Defect **selalu tercatat** (Finding tetap dipersist ke `TaskPersonalizedFinding`) terlepas dieksekusi sekarang atau nanti — berlaku untuk kedua skenario.
- `PriorityCode` **tidak bisa dipakai** sebagai pengganti/pelengkap gate ini — kegunaannya beda: menentukan **expected delivery date** (kapan defect harus dieksekusi dalam siklus penjadwalan normal), bukan penentu "eksekusi instan di lapangan sekarang".
- Untuk Skenario 2 (critical), **Order yang relevan bisa jadi sudah ada sebelumnya** — dari finding sebelumnya yang levelnya lebih rendah lalu eskalasi. Pola ini sama dengan [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack) (reuse Order yang masih open, bukan buat baru) — indikasi pola reuse-Order **tidak eksklusif untuk Crack**, berlaku juga untuk Defect biasa yang eskalasi jadi critical.

**Masih open (lanjut 2026-08-13):**
- Mekanisme correlation "Order sudah ada sebelumnya" — detail di [Poin 6](#poin-6-duplicate-atau-correlation-handling).
- Urutan eksekusi fisik vs approval Planner untuk Skenario 2 — apakah Order/approval harus selesai dulu sebelum mechanic boleh eksekusi (expedited approval), atau eksekusi fisik bisa duluan (material sudah di tangan) dan Order dibuat sebagai dokumentasi retroactive. Lihat juga [Poin 9](#poin-9-approval-flow).
- 4 TaskKit di luar scope (`Not Comply`/`Not Ok`/`Dirty`) — final by design, atau bisa diperluas nanti?
- Scope kerja "sambungkan backend" — breakdown detail: persist `TaskPersonalizedFinding`/`CrackIdentified` saja, atau juga trigger create `MechanicOrderList`/`MechanicOrderSummary`?

~~Crack Defect punya 2 opsi "Identified" (`Monitor` vs `Repair Required`) — apakah keduanya sama treatment?~~ — **resolved**: sudah dijawab di [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack) — keduanya sama-sama trigger Order, bedanya cuma priority.

---

### Poin 2: Defect di Luar Pertanyaan Form (Additional Defect saat Eksekusi)

Skenario: mechanic ketemu defect yang tidak ada pertanyaan relevannya di form yang sedang dikerjakan (mis. sedang inspeksi engine, nemu retak di frame yang bukan bagian checklist hari itu). Baseline flow existing untuk kasus ini adalah **Additional Order** (lihat [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) — `Type='Additional'`, tanpa `WorkOrderId`/`TaskPersonalizedFindingId`, semua field diisi manual).

**Dua opsi:**

- **Opsi A — Reuse Additional Order existing.** Fully decoupled dari WorkOrder/Task, tidak ada perubahan skema. Trade-off: hilang traceability ke WorkOrder asal ditemukannya defect, mechanic harus re-entry manual data asset/context yang sebenarnya sudah dia pegang saat itu.
- **Opsi B — Mekanisme baru "Add Finding" di dalam form berjalan**, tetap link ke WorkOrder/Task aktif. Trade-off: konsisten dengan prinsip [form-centric](#order-integration-bersifat-form-centric-bukan-per-fitur) yang sudah ditetapkan, tapi menyentuh data model — hierarki `WorkOrder → Task → TaskPersonalized → TaskPersonalizedFinding` mengharuskan Finding nempel ke satu Task/Question. Kalau defect tidak berasal dari Question manapun di form berjalan, perlu diputuskan: nempel ke Task "catch-all" generic yang selalu ada di tiap Form, atau perubahan skema supaya Finding bisa nempel langsung ke WorkOrder tanpa lewat Task.

**Status:** belum diputuskan — menunggu arah user.

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

Correlation key untuk "temuan yang sama" — dugaan awal: Asset + Component + SubComponent. Foundational untuk keputusan reuse-Order di [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack), dan sekarang juga relevan untuk skenario Defect critical-escalation ([Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)).

**Masih open (lanjut 2026-08-13):**
- Apakah correlation key sama (Asset + Component + SubComponent), atau ada elemen tambahan khusus buat kasus eskalasi Defect critical?
- Pencarian Order yang sudah ada ini **otomatis oleh sistem** (saat submit Finding baru, sistem cari match & langsung link), atau **manual** (Planner mencocokkan saat review, atau mechanic pilih sendiri)?
- Kalau ketemu Order lama yang masih open, apa yang berubah — cuma priority naik, atau ada field lain (mis. `ExecutionType`) yang ikut berubah?

---

## Fase D — Proses/Workflow

### Poin 9: Approval Flow

#### Form Approval — sampai Foreman/Supervisor

Form (termasuk Finding/Defect di dalamnya) melalui approval berjenjang sampai level **Foreman/Supervisor**.

#### Defect Biasa — Lanjut Jadi Order di SAP Tergantung Planner

Defect dibuat oleh **mechanic**, termasuk pengisian **material**. Apakah defect ini **dilanjutkan jadi Order di SAP** ditentukan oleh **Planner** — Planner adalah gate approval Order sebelum push ke SAP.

> Open (lanjut 2026-08-13): untuk Skenario 2 critical di [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack), apakah gate Planner ini tetap berlaku (cuma dipercepat) atau ada jalur bypass saat eksekusi tidak bisa menunggu approval.

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
- [maintenance-execution-schema.md](../../architecture/database/maintenance-execution-schema.md) — DDL real `TaskPersonalizedFinding`, `CrackIdentified`
- [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) — flow Order/eMOL existing
