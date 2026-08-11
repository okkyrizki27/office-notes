# Order Integration di Form

Dokumen ini merekam diskusi phase 2: bagaimana Form (task di dalamnya) terintegrasi dengan Order — trigger create Order saat jawaban suatu task mengindikasikan defect, mekanisme capture data finding, sampai timing & flow create Order-nya.

*Last updated: 2026-08-11*

---

## Konteks

Phase 1 ([pm-shutdown-service-package.md](../phase1-service-package/pm-shutdown-service-package.md)) men-defer item **"Skenario field team menemukan pekerjaan tak terduga"** ke next MVP. Phase 2 ini membahas spesifik itu.

**Sifat enhancement ini (dikonfirmasi user):** UI Finding creation **sudah dibangun** di mobile app (lihat [Current State — Mobile App UI](#current-state--mobile-app-ui-v400) di bawah) tapi **belum functional** — form sudah ada dan fieldnya sudah match skema `TaskPersonalizedFinding`/`CrackIdentified`, tapi belum tersambung ke backend (persist data & trigger create Order). Jadi scope Phase 2 ini lebih ke **"aktifkan & sambungkan"** UI yang sudah ada, bukan desain UI dari nol.

Fakta current-state TaskKit General Check (7 tipe, opsi dropdown per tipe, struktur row) sudah didokumentasikan di [form-builder.md](../../architecture/form/form-builder.md#taskkit) — tidak diulang di sini, dokumen ini fokus ke keputusan & open items khusus Order Integration.

Baseline schema lain yang relevan:
- [form-submission.md](../../architecture/form/form-submission.md) — schema `TaskPersonalizedFinding`, `TaskResponseLog`
- [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) — flow Order/eMOL existing (sumber saat ini: Inspection & Additional Order saja)

---

## Order Integration Bersifat Form-Centric, Bukan Per-Fitur

Penting supaya scope tidak salah paham: integrasi Order ini **hook di level Form/Question**, bukan diimplementasikan terpisah per fitur pemanggil (Inspection/PM Shutdown/BD Corrective/pemanggil lain di masa depan). 1 Form terdiri dari N Question, tiap Question punya TaskKit type (lihat [Scope Trigger Order](#scope-trigger-order--keputusan-awal-dari-user) di bawah). Selama Question itu termasuk TaskKit yang punya opsi "Identified", integrasi Order terjadi **di manapun Form itu dipanggil** — karena mekanismenya menempel ke `TaskPersonalizedFinding` (layer Form, shared lintas fitur, lihat hierarki di [maintenance-execution-schema.md](../../architecture/database/maintenance-execution-schema.md)), bukan logic khusus per fitur.

Konsekuensinya: begitu PM Shutdown/BD Corrective memakai mekanisme Form standar dari Phase 1 (lihat [pm-shutdown-service-package.md](../phase1-service-package/pm-shutdown-service-package.md#apa-yang-migrasi-ke-maintenance-execution-apa-yang-tetap-di-dplandb) — Task/Backlog Execution di level Daily Plan tetap di `DPlanDB`, cuma Form yang migrasi ke `maintenance-execution`), Order Integration otomatis berlaku untuk mereka juga — **tidak perlu development terpisah per fitur**.

**Multi-mechanic per Form**: 1 Form bisa dikerjakan >1 mechanic (via "Assign to Me"/Supervisor assign) → membentuk multiple `TaskPersonalized` (1 per mechanic). Mechanic yang menjawab defect/crack found mengisi Finding + Order data di `TaskPersonalized` miliknya sendiri.

---

## Scope Trigger Order — Keputusan Awal (dari User)

TaskKit yang akan terintegrasi dengan Order (create Order saat jawaban = defect):

- **Crack Defect**
- **Data Input**
- **Defect Check**

Dasar pemilihan: opsi dropdown-nya mengandung kata **"Identified"** (`Crack Identified: ...`, `Defect Identified`) — berbeda dari 4 TaskKit lain (Action Task, Assessment Check, Condition Check, Washing) yang **tidak** masuk scope meski opsinya juga bisa berarti "ada masalah" (`Not Comply`, `Not Ok`, `Dirty`).

---

## Current State — Mobile App UI (v4.0.0)

Diverifikasi langsung dari screenshot app **Digiman+ mobile v4.0.0** (2026-08-06). **UI sudah ada tapi belum functional** — Save belum tentu persist data / trigger apapun ke backend.

### Trigger

Di row Bank Task (task list dalam tab form), begitu user pilih opsi dropdown yang termasuk kategori "defect" (`Defect Identified` untuk Defect Check/Data Input, `Crack Identified: Monitor`/`Crack Identified: Repair Required` untuk Crack Defect), app navigasi ke screen terpisah berjudul **"Defect Identified"** — judul ini generic/shared, dipakai untuk ketiga TaskKit (termasuk Crack Defect, bukan "Crack Identified").

### Struktur Screen "Defect Identified"

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

---

## Open Items / Belum Diputuskan

- **Apakah "Immediate Execute Declaration" jadi gate Order?** Teks checkbox eksplisit bilang *"by checking this, your finding won't be processed into backlog"* — dugaan: `IsImmediateExecutable=1` berarti finding **dikecualikan** dari pipeline Order/eMOL (mechanic langsung fix di lapangan, tidak butuh Order). Kalau benar, ini bisa jadi jawaban tunggal untuk pertanyaan "opsi dropdown mana yang trigger Order" — **belum dikonfirmasi user**.
- **Crack Defect punya 2 opsi "Identified"** (`Monitor` vs `Repair Required`) — apakah keduanya buka screen Finding yang sama & keduanya berpotensi jadi Order (tergantung `IsImmediateExecutable`), atau `Monitor` punya treatment berbeda?
- **4 TaskKit di luar scope** (`Not Comply`/`Not Ok`/`Dirty`) — final by design, atau bisa diperluas nanti?
- **Scope kerja "sambungkan backend"** — apa saja persisnya yang belum jalan: persist `TaskPersonalizedFinding`/`CrackIdentified` saja, atau juga trigger create `MechanicOrderList`/`MechanicOrderSummary`? Perlu breakdown lebih detail begitu bagian trigger (poin 1 & 2 di atas) sudah diputuskan.

---

## Related Docs

- [order-integration-checklist.md](order-integration-checklist.md) — kerangka kerja & progress diskusi Phase 2 (5 topik: UI, Data Flow, Approval, SAP/ERP, Dampak Report)
- [pm-shutdown-service-package.md](../phase1-service-package/pm-shutdown-service-package.md) — phase 1, sumber deferred item yang jadi latar belakang phase 2 ini
- [form-builder.md](../../architecture/form/form-builder.md) — struktur TaskKit & Bank Task row (fakta current-state lengkap)
- [form-submission.md](../../architecture/form/form-submission.md) — schema `TaskPersonalizedFinding`, `TaskResponseLog`
- [maintenance-execution-schema.md](../../architecture/database/maintenance-execution-schema.md) — DDL real `TaskPersonalizedFinding`, `CrackIdentified`
- [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) — flow Order/eMOL existing
