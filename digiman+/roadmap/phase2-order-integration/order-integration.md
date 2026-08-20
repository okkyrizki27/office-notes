# Order Integration di Form

Dokumen ini merekam diskusi phase 2: bagaimana Form (task di dalamnya) terintegrasi dengan Order — trigger create Order saat jawaban suatu task mengindikasikan defect, mekanisme capture data finding, sampai timing & flow create Order-nya.

Struktur dokumen ini mengikuti urutan 6 fase di [order-integration-checklist.md](order-integration-checklist.md) supaya progress diskusi mudah ditelusuri.

*Last updated: 2026-08-17*

---

## Konteks

Phase 1 ([pm-shutdown-service-package.md](../phase1-service-package/pm-shutdown-service-package.md)) men-defer skenario mechanic yang sedang melakukan service rutin dan menggunakan form menemukan finding — defect atau crack — ke next MVP. Phase 2 ini membahas spesifik itu.

**Sifat enhancement ini (dikonfirmasi user):** UI Finding creation **sudah dibangun** di mobile app (lihat [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack) di bawah) tapi **belum functional** — form sudah ada dan fieldnya sudah match skema `TaskPersonalizedFinding`/`CrackIdentified`, tapi belum tersambung ke backend (menyimpan data & trigger create Order). Jadi scope Phase 2 ini lebih ke **"aktifkan & sambungkan"** UI yang sudah ada, bukan desain UI dari nol.

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

## Catatan untuk QA — Scope Testing End-to-End (2026-08-17)

**Enhancement ini menyentuh tabel shared** (`TaskPersonalizedFinding`, `MechanicOrderList`, `MechanicOrderDetail`, dkk — kolom Name baru, `NoPartsRequired`, dll, [lihat Data Propagation Mapping](#poin-5-data-flow-defect-dan-crack)) yang **dipakai juga oleh flow existing**, bukan eksklusif ke flow Form/defect baru. Testing **wajib end-to-end** mencakup:
- **Finding & Additional Finding dari Inspection** (scheduled inspection maupun additional inspection) — flow existing, bukan bagian yang didesain baru di dokumen ini, tapi berpotensi terdampak karena skema shared.
- **Additional Order dari Maintenance Order** — flow existing (`Type='Additional'`), sama alasannya.
- **Finding/defect/crack dari Form** (Inspection/PM Shutdown/BD Corrective, [form-centric](#order-integration-bersifat-form-centric-bukan-per-fitur)) — ini yang didesain baru di dokumen ini.

Jangan asumsikan testing cukup di jalur Form baru saja — regresi ke flow existing (Inspection/Additional Order) perlu dicek eksplisit.

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

**Resolved (2026-08-15): exclude 4 TaskKit ini bersifat final, bukan sekadar scope MVP** — bukan "dipersempit dulu, nanti diperluas", tapi keputusan permanen bahwa temuan dari 4 TaskKit itu memang di luar cakupan Order Integration.

#### Current State — Mobile App UI (v4.0.0)

Diverifikasi langsung dari screenshot app **Digiman+ mobile v4.0.0** (2026-08-06). **UI sudah ada tapi belum functional** — Save belum tentu menyimpan data / trigger apapun ke backend.

**Trigger**

Di row **Form Task** (list dalam tab form — **koreksi terminologi 2026-08-17, revisi ke-2**: bukan "Bank Task" — itu istilah untuk **master task** reusable lewat `TaskCode` yang sama di banyak form; juga bukan sekadar "Task" — itu entity DB tersendiri di `maintenance-execution` (`Task: Id, WorkOrderId, ...`), beda dari row form ini. Row form ini pakai istilah **"Form Task"**, konsisten dengan field schema yang sudah ada `TaskPersonalizedFinding.FormTaskCode`/`FormTaskNumber` — dipilih "Form Task" bukan "Question"/"Pertanyaan" karena kalimatnya tidak selalu berupa pertanyaan, kadang perintah kerja/instruksi), begitu user pilih opsi dropdown yang termasuk kategori "defect" (`Defect Identified` untuk Defect Check/Data Input, `Crack Identified: Monitor`/`Crack Identified: Repair Required` untuk Crack Defect), app navigasi ke screen terpisah berjudul **"Defect Identified"** — judul ini generic/shared, dipakai untuk ketiga TaskKit (termasuk Crack Defect, bukan "Crack Identified").

**Indikator post-submit — sebagian existing, sebagian masih ekspektasi (2026-08-15):** ada icon (rounded-square outline, isinya glyph dokumen+kaca pembesar) di sebelah kanan dropdown "Condition" pada tiap row Form Task — **abu-abu** saat Condition belum dijawab (dikonfirmasi dari screenshot: row dengan dropdown masih "Select" → icon abu-abu). **State setelah diisi (warna/tampilan) belum eksis di app hari ini — masih ekspektasi/diskusi, bukan fakta existing** (belum ada screenshot dengan row yang sudah "Defect Identified").

**Warna icon ikut warna Condition (2026-08-15, resolved — koreksi tag 2026-08-17, ini bukan lagi diskusi terbuka, sudah jadi dasar keputusan lain di bawah)** — karena opsi dropdown Condition sendiri **color-coded** — dikonfirmasi visual dari screenshot: **hijau** untuk "Normal, system working", **merah** untuk "Defect Identified", **oranye** untuk "Not Applicable" — usulan icon-nya **ikut warna Condition yang dipilih** (jadi merah kalau Defect Identified), bukan hijau generik seperti asumsi awal saya. Lebih konsisten secara visual.

**Scope icon lebih luas dari dugaan awal — juga dipakai untuk "Not Applicable" (2026-08-15):** icon ini **bukan eksklusif untuk Defect** — dipakai juga untuk nyimpen **reason/alasan "Not Applicable"**. Jadi fungsinya lebih tepat "entry-point buka detail tambahan untuk jawaban Condition yang butuh info lebih" — beda perilaku tergantung opsi yang dipilih: `Defect Identified` → buka screen "Defect Identified", `Not Applicable` → buka input reason N/A, `Normal` → kemungkinan tidak butuh detail tambahan (icon tetap abu-abu/inactive). **Reason N/A ini di luar scope Order Integration** (tidak trigger Order), dicatat di sini murni supaya konteks icon-nya lengkap.

**Model 3-state untuk icon (2026-08-15, resolved — koreksi tag 2026-08-17) — gap validasi yang perlu ditutup:** kalau Condition dijawab `Defect Identified`/`Not Applicable` tapi Finding/reason-nya **belum ada sama sekali** (user keluar dari screen pengisian tanpa save as draft/submit) **atau masih draft** ([Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15)) — Form jadi tidak bisa diselesaikan (submit) padahal tidak ada indikator yang bikin user aware. Usulan 3 state icon:

1. **Abu-abu** — Condition belum dijawab.
2. **Warning/incomplete** (state baru, mis. icon pudar + badge tanda seru) — Condition sudah dijawab `Defect Identified`/`Not Applicable`, tapi Finding/reason **belum ada** ATAU **masih draft** — 2 kondisi ini **digabung jadi 1 tampilan yang sama** (keduanya sama-sama blocking submit, user cukup tahu "belum selesai" tanpa perlu tahu penyebab persisnya). **Perluasan (2026-08-17):** "belum ada" **mencakup juga** kasus semua Finding di row itu sudah **di-delete** ([Poin 8](#poin-8-cancel-atau-delete-finding)) — meski sempat pernah ada & submitted, begitu semuanya `IsActive=0`, row ini balik ke state #2 (bukan balik abu-abu — Condition-nya tetap tercatat sudah dijawab, cuma Finding di baliknya sekarang kosong).
3. **Merah/oranye solid** (sesuai warna Condition) — Finding/reason sudah **submitted** (`IsDraft=0`), Form boleh dilanjutkan submit.

**Deferred (2026-08-17) — state icon untuk "Rejected":** belum ada state ke-4 untuk kondisi Finding/Order-nya ditolak approver — **sengaja di-defer** sampai Poin 10 (Reject/rework flow, masih sepenuhnya belum dibahas) benar-benar didesain. Jangan desain state icon ini sekarang, tunggu Poin 10.

**Resolved (2026-08-17) — icon TIDAK bedakan "pending review" vs "locked/approved":** state #3 (merah/oranye solid) tetap **1 tampilan** untuk semua kondisi submitted, tidak dipecah lagi. Alasan: distingsi pending vs locked cuma actionable pas user mau edit (bukan info yang perlu diketahui sekilas dari list row), dan detail-nya sudah tersedia on-demand begitu user buka drill-down ([status chip + tombol Edit/Delete muncul/hilang, lihat Poin 7](#poin-7-editability-window-sebelum-approval)) — konsisten prinsip "icon/badge ringkas di level list, detail di drill-down" yang sudah dipakai di keputusan count badge.

**Validasi submit di level Form (baru, konsekuensi dari model di atas):** sebelum Form bisa disubmit, sistem cek semua row Form Task yang Condition-nya `Defect Identified`/`Not Applicable` — kalau ada yang masih di state #2 (incomplete/draft), submit Form **di-block** dengan pesan yang jelas menunjuk row mana yang belum selesai.

**Perluasan — highlight card pertanyaan saat try-submit (2026-08-15, dipertimbangkan):** validasi di atas diperluas jadi visual di level **card pertanyaan** (bukan cuma icon Condition) — begitu user coba submit Form, card pertanyaan yang masih "belum selesai" diberi **background merah muda**. Definisi "belum selesai" meliputi:

1. Belum dijawab (Condition masih "Select")
2. Ada field input mandatory yang belum diisi
3. Photo evidence mandatory yang belum dilengkapi
4. Remark mandatory yang belum dilengkapi
5. Defect/Crack Identified tapi Finding-nya belum diisi atau masih draft (state #2 icon di atas)
6. ~~Not Applicable belum ada reason~~ — **tidak mungkin terjadi**: `Not Applicable` cuma bisa disimpan **atomic bareng reason-nya** (1 aksi save, beda dari Defect yang bisa draft/multi-step) — jadi tidak ada state "N/A tanpa reason" yang perlu divalidasi.

**Catatan (2026-08-17) — state #2/#3 & card highlight butuh UI designer:** beda dari state #1 (abu-abu) yang sudah confirmed existing di app hari ini ([lihat screenshot v4.0.0](#current-state--mobile-app-ui-v400)), **state #2 (warning/incomplete) dan visual persis state #3** (warna solid, exact icon asset) **belum eksis** — konsepnya sudah didefine lengkap di atas (kapan trigger, kondisi apa saja), tapi **butuh UI designer** untuk styling final (bentuk badge tanda seru, shade warna solid, dkk). Sama untuk **card highlight merah muda** — konsep & kondisi trigger-nya sudah jelas, visual-nya belum ada.

**Icon Condition (state #2) tetap wajib ada, bukan opsional** — ini yang mencegah user bingung: kalau cuma ada card highlight merah muda tanpa icon warning, user yang **sudah menjawab** Condition-nya (`Defect Identified`) tapi card-nya tetap merah muda bisa salah paham "jawaban saya kenapa tidak kesimpan?". Icon di sebelah kanan Condition itu yang kasih tahu **alasan spesifiknya** — bukan jawabannya yang bermasalah, tapi ada Finding di baliknya yang belum diisi/masih draft. Jadi hubungannya: card highlight = sinyal "ada yang belum beres di pertanyaan ini" (level tinggi), icon = alasan persisnya (level detail) — dua-duanya perlu tampil bareng, bukan salah satu saja.

**Icon camera & pencil — konfirmasi terpisah, tidak terkait status Condition:** 2 icon hijau (camera+ untuk Add Evidence, pencil untuk input Remark) di bawah dropdown Condition **hijau sejak awal**, tidak berubah berdasarkan status Condition — generic action button yang selalu aktif, tidak ada hubungannya dengan icon indikator dokumen+kaca-pembesar di atas.

**Header "Work Detail" ada status "Syncing.../Not Synced"** — indikasi mekanisme offline-sync **sudah ada** di level screen ini hari ini, relevan buat [Poin 4 (Offline Behavior/Draft State)](#poin-4-offline-behavior--draft-state-2026-08-15) — kemungkinan bisa jadi referensi pola existing yang bisa di-reuse/diselaraskan, tapi belum dikonfirmasi hubungannya dengan draft state yang kita desain.

**Confirmed (2026-08-15) — icon ini adalah entry-point buka balik screen "Defect Identified":** tap icon ini navigasi balik ke screen yang sama (Tab Finding #1/#2/... dkk, lihat [Struktur Screen "Defect Identified"](#struktur-screen-defect-identified) di bawah), berfungsi ganda: **(a)** lihat/edit Finding yang sudah pernah diisi, dan **(b)** entry-point untuk **tambah Finding baru** lewat tombol "+" di Tab Finding yang sudah terdokumentasi — jadi icon ini bukan cuma indikator pasif, tapi jadi jawaban utama untuk "tampilan form setelah defect disubmit". **Belum bisa ditest end-to-end** — konsisten tema "UI sudah ada tapi belum functional", create defect sendiri belum berfungsi saat ini. **Default behavior (resolved 2026-08-15):** kalau ada >1 Finding, buka ke **Tab Finding #1** (bukan tab terakhir yang diisi) — keputusan desain, verifikasi implementasi aktualnya baru bisa dilakukan setelah backend jalan.

**Usulan tambahan (2026-08-15, resolved 2026-08-17) — count badge, cuma relevan untuk `Defect Identified`:** karena 1 row bisa punya >1 Finding (Tab Finding #1/#2/...), usulan nambah **badge angka** di icon ini (jumlah Finding yang sudah diisi untuk row itu) supaya user bisa lihat sekilas tanpa tap masuk. **Tidak berlaku untuk `Not Applicable`** — reason N/A selalu cuma 1 (tidak ada konsep "banyak reason" seperti Finding), jadi count badge tidak relevan di kasus itu, cukup indikator status biasa (state #2/#3 dari model di atas). **Resolved** — badge cuma hitung Finding **submitted** (`IsDraft=0`), draft tidak ikut dihitung (alasan & detail di [Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15)). **Diperketat (2026-08-17):** juga cuma yang **aktif** (`IsActive=1`) — Finding yang sudah di-delete ([Poin 8](#poin-8-cancel-atau-delete-finding)) otomatis tidak ikut dihitung lagi meski sempat pernah submitted. **Visual badge-nya sendiri belum eksis di app, butuh UI designer** (sama seperti state #2/#3, [lihat catatan di bawah](#current-state--mobile-app-ui-v400)) — behavior/kriteria hitungnya sudah didefine lengkap di atas.

**Resolved (2026-08-17) — Finding yang di-delete hilang dari tampilan form:** begitu di-delete ([Poin 8](#poin-8-cancel-atau-delete-finding)), Finding itu **tidak lagi ditampilkan** di Tab Finding list layar "Defect Identified" — tab-nya **difilter keluar** (cuma tampilkan yang `IsActive=1`) dan sisanya **di-renumber sequential** (mis. Finding #1 di-delete, sisa Finding #2 jadi tampil sebagai "Tab Finding #1", bukan tetap "#2" dengan gap) — supaya user tidak bingung lihat nomor yang hilang. User tetap bisa tambah Finding baru lewat tombol "+" seperti biasa setelah ini.

#### Struktur Screen "Defect Identified"

Screen ini adalah **satu form Finding shared**, dengan field tambahan khusus Crack Defect di bagian atas. Urutan top-to-bottom:

1. **Tab Finding #1 / Finding 2 / ...** — satu task row (satu `FormTaskCode`) bisa punya **lebih dari satu Finding** (tombol "+" untuk tambah Finding baru). **Tidak ada batas maksimum jumlah Finding per row (2026-08-17, resolved)** — sengaja tidak dibatasi.
2. **Identitas user** (mis. `2009OBH.supervisor01`) + **evidence/foto** — "Add evidence through the camera or browse the taken image", 3 slot + tombol "Add More". **Hapus foto saat edit (2026-08-17):** bisa terjadi, sifatnya sama dengan mekanisme edit lain ([Poin 7](#poin-7-editability-window-sebelum-approval)) — perlu dicek dulu apakah pola hapus-foto-yang-sudah-diupload ini **sudah ada** di mekanisme evidence existing (mis. di Inspection); kalau belum ada, **butuh UI designer** untuk desain baru.
3. *(khusus Crack Defect)* **Crack Identified Description** — textarea, 0/500 char → `CrackIdentified.CrackDescription`
4. *(khusus Crack Defect)* **Crack Length** table — kolom Location (auto dari task description) / Previous / Current* (mm) → `CrackIdentified.PrevCrackLength` / `CrackLength`
5. **Defect Detail** — "Fill out this form with defect details":
   - **Component & Sub Component\*** → `TaskPersonalizedFinding.ComponentCode`/`SubComponentCode`
   - **Damage Code\*** → `DamageCode`
   - **Cause Code** (tidak wajib) → `CauseCode`
   - **Action Remedy\*** → `ActionRemedyCode`
6. **Immediate Execute Declaration** — checkbox: *"I confirm this inspection finding executable now. By checking this, your finding won't be processed into backlog."* → `IsImmediateExecutable`. **Copy revisi (2026-08-17, resolved)** — teks existing keliru di 2 hal: (a) "won't be processed into backlog" tidak selalu benar (Sub-kasus B2 tetap bikin Order, cuma diprioritaskan), (b) framing-nya "future intent" padahal maknanya "fakta eksekusi sekarang" (lihat [klarifikasi semantik](#poin-1-trigger-dan-ui-create-defect-atau-crack)). **Teks baru:** label checkbox *"I confirm I am fixing/repairing this right now."*, sub-text *"Use this only if the repair is happening now, at the time of this report."* — berlaku sama untuk layar Crack (title screen generic "Defect Identified" juga untuk Crack, tidak perlu versi terpisah).
7. **Priority\*** dropdown → `PriorityCode`
8. **Defect Notes** textarea, 0/100 → `DefectNotes`
9. **Estimated Repair Duration\*** dropdown → `RepairDuration`. **Copy revisi (2026-08-17, resolved)** — label lama *"How Long Will This Defect Repair Take?"* ambigu buat kasus `IsImmediateExecutable=Yes` ("will take" kesannya forward-looking/scheduling, aneh kalau perbaikannya sedang berlangsung sekarang). **Teks baru "Estimated Repair Duration"** — netral, tidak terikat tense/waktu tertentu, konsisten dengan pola penamaan field tetangga (*Defect Notes*, *Defect Repair Instructions*), enak dibaca untuk kedua kondisi `IsImmediateExecutable`.
10. **Defect Repair Instructions / Actions** textarea, 0/200 → `RepairInstruction`

**Gap ditemukan & resolved (2026-08-17, dari screenshot user) — step 9 & 10 (Repair Duration, Repair Instructions) TIDAK boleh conditional ke `IsImmediateExecutable`:** dikonfirmasi dari screenshot app existing (Task 23) — hari ini kedua field ini **hilang dari tampilan** begitu checkbox `IsImmediateExecutable` dicentang (`Yes`). Ini konsisten dengan premis lama yang **sudah dikoreksi** ([lihat semantik checkbox](#diskusi-immediate-execute-declaration-sebagai-gate-order)) — asumsi lama "checked = tidak diproses ke backlog, jadi field terkait backlog tidak relevan" itu **tidak selalu benar** (Sub-kasus B2 tetap bikin Order meski `Yes`). **Keputusan: kedua field ini SELALU muncul, tidak dipengaruhi nilai `IsImmediateExecutable` sama sekali** — Repair Duration & Repair Instructions mendeskripsikan **sifat perbaikannya sendiri** (relevan dipakai Planner/approver terlepas eksekusinya sekarang atau nanti), bukan atribut yang terikat ke keputusan backlog routing. **Ini koreksi ke behavior existing** (bukan fitur baru) — perlu perbaikan logic conditional-visibility yang sudah ada, ditandai **butuh UI designer + dev** untuk eksekusinya.
11. **Save** — **Resolved (2026-08-17) — validasi field-level saat tap "Submit" dengan mandatory field kosong:** **inline merah** di bawah tiap field yang bermasalah (bukan banner ringkasan terpisah) — lebih mudah dideteksi user langsung di titik field-nya. Berlaku untuk semua field bertanda `*` di step 5 & 7–10 (Component/SubComponent/Damage Code/Action Remedy/Priority/Repair Duration), termasuk validasi mutual-exclusivity Material/`NoPartsRequired` ([lihat di bawah](#poin-5-data-flow-defect-dan-crack)). **Revisi (2026-08-17, resolved):** jadi **2 tombol terpisah**, bukan 1 "Save" generik lagi — konsekuensi dari draft state yang masuk di [Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15) (model lama "1 Save button = langsung submit final" sudah [direvisi](#poin-4-offline-behavior--draft-state-2026-08-15), tapi trigger button-nya baru diputuskan sekarang):
    - **"Save as Draft"** — **tidak validasi field mandatory** sama sekali, bisa save meski banyak field masih kosong (`IsDraft=1`, tidak publish ke topic, [lihat Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15)).
    - **"Submit"** — validasi field mandatory (field bertanda `*` di atas) seperti biasa, baru berhasil kalau lengkap (`IsDraft=0`, publish ke topic).
    - **Catatan — butuh UI designer** untuk layout persis 2 tombol ini (posisi, hierarchy visual mana yang primary/secondary).

Field di step 5 & 7–10 match 1:1 ke schema `TaskPersonalizedFinding` yang sudah terdokumentasi ([maintenance-execution-schema.md](../../architecture/database/maintenance-execution-schema.md)); step 3–4 match `CrackIdentified`. Defect Check (Task 25, diverifikasi terpisah) pakai form identik **tanpa** step 3–4 — mengonfirmasi field Crack itu addon khusus TaskKit, bukan form yang beda total per TaskKit.

**Resolved (2026-08-17) — prompt "unsaved changes" saat keluar tanpa save:** kalau user isi sebagian field lalu navigasi keluar (back/exit) **tanpa** tap salah satu dari 2 tombol di atas, dan ada perubahan yang belum tersimpan — tampilkan **confirmation dialog**, bukan biarkan data hilang diam-diam:
- Title: *"Save your changes?"*
- Body: *"You have unsaved changes. Do you want to save this as a draft before leaving?"*
- Buttons: **Discard** / **Save as Draft**

**Catatan — butuh UI designer** untuk visual dialog ini (mengikuti existing design system Digiman+, [sama seperti dialog delete](#poin-8-cancel-atau-delete-finding)).

**`CrackIdentified` — tabel sudah ada, tidak perlu skema baru (confirmed 2026-08-15):**
```
Id                          PK, bigint, identity
TaskPersonalizedFindingId   bigint, not null   ← FK wajib, 1-to-many
CrackDescription            varchar(1024), null
CrackLength                 float, null (default 0)
PrevCrackLength             float, null
IsActive, CreatedBy/At, ModifiedBy/At
```
FK-nya `TaskPersonalizedFindingId` (**not null**, 1-to-many) — pola sama dengan `TaskPersonalizedFindingMaterial` yang kita desain baru ([Poin 5](#poin-5-data-flow-defect-dan-crack)). Jadi field khusus Crack (Crack Description, Crack Length Previous/Current) tinggal pakai tabel existing ini di sisi `maintenance-execution` — **tapi ini cuma separuh cerita, lihat gap di sisi `maintenance-order` yang baru ditemukan & resolved 2026-08-17 di bawah.**

**Gap ditemukan & resolved (2026-08-17) — `CrackIdentified` tidak punya tujuan di `maintenance-order`, padahal approval terjadi di sana:** dicek ke [maintenance-order-schema.md](../../architecture/database/maintenance-order-schema.md) — tidak ada tabel/kolom Crack apapun di sana. Konsekuensinya: Planner yang approve eMOL untuk Crack finding tidak akan bisa lihat Crack Description/Length sama sekali, karena datanya cuma ada di `maintenance-execution`. **Fix:** tabel baru `MechanicOrderCrackIdentified` di `maintenance-order` — mirror `CrackIdentified` persis (`CrackDescription`/`CrackLength`/`PrevCrackLength`), FK `MechanicOrderListId` (not null, 1-to-many, pola sama `MechanicOrderMaterial`). Diisi lewat publish/consume yang sama saat eMOL dibuat (create-baru **maupun** reuse-vehicle — snapshot-copy, konsisten prinsip yang sudah dipakai di semua field lain). Skema lengkap: [maintenance-order-schema.md](../../architecture/database/maintenance-order-schema.md).

**Backfill — TIDAK perlu (2026-08-17, confirmed user):** beda dari 6 field Name/`NoPartsRequired` sebelumnya, `MechanicOrderCrackIdentified` **tidak di-backfill sama sekali** — dikonfirmasi tidak ada eMOL historis yang berasal dari Crack finding (flow Crack→Order belum pernah functional sebelum Phase 2, tidak ada jalur lain seperti Additional Order manual yang menghasilkan data Crack). Genuinely skip, bukan cuma di-defer.

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

**Resolved (2026-08-17) — copy checkbox direvisi**, sudah tidak mengklaim "won't be processed into backlog" (yang cuma valid Skenario 1) — [lihat teks baru & detail di Struktur Screen "Defect Identified"](#struktur-screen-defect-identified) step 6.

**Sudah dikonfirmasi user (2026-08-12):**
- Defect **selalu tercatat** (Finding tetap disimpan ke `TaskPersonalizedFinding`) terlepas dieksekusi sekarang atau nanti — berlaku untuk kedua skenario.
- `PriorityCode` **tidak bisa dipakai** sebagai pengganti/pelengkap gate ini — kegunaannya beda: menentukan **expected delivery date** (kapan defect harus dieksekusi dalam siklus penjadwalan normal), bukan penentu "eksekusi instan di lapangan sekarang".

**⚠️ Klarifikasi semantik penting (2026-08-16) — `IsImmediateExecutable` itu pernyataan FAKTA, bukan permintaan/rencana:** nama kolom ini secara ideal harusnya lebih dekat ke `IsImmediateExecuted` — mechanic menyatakan perbaikan ini **sudah/sedang dikerjakan saat itu juga**, simultan dengan pengisian form, bukan janji/permintaan untuk dikerjakan segera nanti (juga bukan permintaan prioritas). Konsisten dengan alasan asal Skenario 2 critical di atas ("harus diperbaiki saat itu juga karena kalau tidak bisa mengganggu performa unit/unscheduled breakdown") — ini kejadian eksekusi yang terjadi bersamaan dengan pelaporan. **Nama kolom `IsImmediateExecutable` TETAP dipakai apa adanya, TIDAK di-rename** — ini murni klarifikasi pemahaman/semantik, bukan proposal perubahan nama; sudah terlanjur dipakai di schema/logic existing, rename cuma akan bikin breaking changes tanpa manfaat. **Implikasi dari klarifikasi ini:** field ini otomatis berfungsi ganda sebagai **sinyal status eksekusi**, bukan cuma trigger routing Order — relevan langsung ke gap visibility approver ([lihat Poin 9](#poin-9-approval-flow)).

**Skenario 2 (critical) — detail per sub-kasus (2026-08-13):**

Skenario 2 ternyata perlu dipecah lebih lanjut tergantung apakah ada Order lama yang bisa di-reuse:

- **Sub-kasus A — Order lama sudah ada**, dari finding sebelumnya yang levelnya lebih rendah lalu eskalasi (pola sama dengan [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack); mekanisme correlation-nya di [Poin 6](#poin-6-duplicate-atau-correlation-handling)). Eksekusi fisik **non-blocking** (mechanic tidak perlu nunggu approval untuk mulai kerja) — tapi **trigger `BacklogExecutionList`/TECO ke SAP menunggu approval SPV/Planner selesai** dulu, bukan langsung setelah mechanic submit (koreksi mekanisme 2026-08-15: bukan "close" field di `MechanicOrderList`, lihat [Poin 5](#poin-5-data-flow-defect-dan-crack)). ~~Karena Order lama ini sudah pernah lolos approval saat pertama kali dibuat, tidak ada bypass approval yang dibutuhkan~~ — functionally sama dengan backlog execution biasa, cuma dieksekusi lebih cepat dari jadwal aslinya. **Resolved (2026-08-19) — Sub-kasus A dipecah jadi A1 / A2 / A-manual** (definisi lengkap di **Kondisi data** di bawah): kedua jenis kandidat sudah sah sebelum masuk ke sini — **A1** lewat Planner approval di Digiman+, **A2** lewat proses approval di SAP. Yang di-approve di eMOL vehicle ini bukan Order-nya, melainkan **keputusan reuse mechanic**.
- **Sub-kasus B — tidak ada Order lama**, dipecah lagi berdasarkan kebutuhan material:
  - **B1 (tidak butuh material)** — pola sama seperti Sub-kasus A: Order dibuat, mechanic eksekusi sekarang (non-blocking), masuk approval SPV/Planner post-hoc, begitu approved sistem create+close (TECO) ke SAP sekaligus. **Tetap aman**. Tetap perlu konfirmasi ke BPO (Business Process Owner) client (2026-08-15) sebagai validasi rutin, bukan karena ada flaw yang diketahui.
  - **B2 (butuh material)** — **tidak bisa** pakai pola non-blocking di atas, karena keluarnya material dari logistic mensyaratkan Order/Reservasi SAP sudah ada & di-print duluan (proses fisik: Planner request ke logistic → print MO dari SAP → SPV/Foreman ambil material — proses ini **di luar sistem**). Arahnya: **tetap pakai flow Order → Approval → SAP standar** (tidak bikin jalur baru, supaya mudah dimaintain), cuma **dipercepat prioritasnya** (expedited) dibanding Order biasa. **Open item** — mekanisme percepatan/prioritas belum didesain, kemungkinan terkait visibility/sorting di [Fase F — Dashboard](#fase-f--dashboard). **Ini yang paling kena concern GI di bawah** (butuh material by definition).
    - **Alur yang sudah jelas (2026-08-15):** submit → sync ke `maintenance-order` → eMOL terbentuk → trigger approval workflow → approver bisa langsung approve sampai **fully approved** → data sync ke SAP membentuk MO. Follow-up setelah itu (approval fisik lain, print MO, ambil ke logistic, dst) **di luar sistem**, sudah dijelaskan di atas.

**Resolved (2026-08-19) — Kondisi data (mengganti kolom `Jalur` di matrix):** kolom `Jalur` lama mencampur **cara menemukan** dengan **kondisi data**. Yang menentukan outcome hanya kondisi datanya.

| Kode | Kondisi | `ReuseOrderNumber` | `ReuseSAPOrderNumber` | Provenance approval |
|---|---|---|---|---|
| **A1** | Ada row `PoolingMOItem` — **dengan atau tanpa** row `MOOpen` | Dari `PoolingMOItem` | Auto dari `SAPMOSyncOrder.MONo` (atau `MOOpen.MONumber` kalau row-nya sudah ada). **NULL selama `MONo` belum kembali** — inilah baris 3–4 di matrix di bawah | Planner approval Digiman+ |
| **A2** | Ada row `MOOpen`, **tidak ada** row `PoolingMOItem` | NULL | Auto-derive `MOOpen.MONumber` | Proses approval di SAP |
| **A-manual** | Auto-detection gagal total | NULL | **Manual** — diinput user | Tidak terverifikasi |
| **B1** | Order baru, tidak butuh material | NULL | NULL | — (Order belum ada) |
| **B2** | Order baru, butuh material | NULL | NULL | — (Order belum ada) |

Pembeda A1 vs A2 adalah **asal-usul Order**, bukan ada-tidaknya row `MOOpen`: A1 lahir di Digiman+ (karena itu punya row `PoolingMOItem`), A2 dibuat langsung di ERP. A1 yang sudah sync akan punya row di **kedua** tabel — itu kondisi paling umum, bukan pengecualian.

Hanya **B1/B2** yang menghasilkan row `PoolingMOItem` baru; seluruh jalur reuse (A1/A2/A-manual) tidak, karena Order-nya sudah ada di SAP.

**Escape hatch tidak muncul di sumbu ini** — ia pintu masuk, bukan kondisi data. Sistem tetap coba lookup `MOOpen` + `CheckPartOrder` pakai MO Number yang diinput; ketemu → jatuh ke A1/A2, tidak ketemu → A-manual. Detail lookup & perilaku offline ada di [Poin 6](#poin-6-duplicate-atau-correlation-handling).

**⚠️ Konteks SAP real (BUMA ID) — concern TECO cuma relevan kalau MO butuh material (2026-08-15, disempitkan & dikoreksi):** MO yang **butuh material** dari Digiman+ **tidak langsung siap dieksekusi/TECO** — statusnya awal **"belum release"**/**"waiting approval"** di SAP sendiri (proses approval SAP sendiri, terpisah dari approval Planner di Digiman+ — approver-nya **bukan** procurement/logistic). **Setelah** MO itu approved/release, **baru** lanjut ke proses di sisi **procurement/logistic** (durasinya tergantung ketersediaan material) — 2 tahap berurutan, bukan 1 tahap yang sama. Jadi dapat nomor MO balik dari sync **bukan berarti** MO itu siap di-TECO — bisa jadi masih belum release/approved, atau sudah release tapi proses procurement/logistic-nya masih berjalan. **MO tanpa material (`NoPartsRequired=1`) tidak kena concern ini** — tidak ada GI yang perlu ditunggu, aman TECO langsung.

Sempat dipikirkan solusi "tunggu MO muncul di `MOOpen` dulu baru eksekusi lewat Backlog Execution existing" — **tapi ini juga bermasalah**: inbound sync SAP→`MOOpen` **tidak real-time**, jadi nunggu situ bisa lama/tidak reliable sebagai sinyal.

**Resolved (2026-08-19) — TECO tidak lagi digantungkan ke status GI:** TECO **selalu** dicoba di titik yang sama, SAP yang menolak kalau Order belum eligible, dan retry existing yang menyelesaikan konvergensinya.

**Resolved (2026-08-18, final — supersede 3 draft sebelumnya) — determinan sebenarnya "apakah `MONo` sudah diketahui/predictable", bukan cuma "butuh material atau tidak":**

3 draft sebelumnya berturut-turut dikoreksi: (1) defensive-retry generik untuk semua kasus, (2) eager-vs-manual berdasar butuh-material-atau-tidak semata, (3) baru disadari reuse dan Order baru punya karakteristik `MONo` yang beda total, jadi mekanismenya juga harus beda — bukan cuma soal butuh material atau tidak.

**Mekanisme final, dipecah per situasi:**

1. **Reuse (Sub-kasus A), `MONo` sudah diketahui** (terlepas Order lama itu butuh material atau tidak) → **eager-trigger** `BacklogExecutionList` langsung di titik **final Order Approval** (tier terakhir, beda dari trigger edit-lock yang di tier pertama — [lihat Poin 7](#poin-7-editability-window-sebelum-approval)). Aman karena `MONo` yang diketahui berarti Order itu sudah confirmed real di SAP.
2. **Reuse (Sub-kasus A), butuh material, `MONo` masih NULL** → ~~**submit di-block** sebelum sempat masuk Order Approval sama sekali (detail & pesan di bawah)~~ — **Resolved (2026-08-19): submit tidak pernah di-block, yang di-block adalah final approval** ([matrix baris 3](#poin-1-trigger-dan-ui-create-defect-atau-crack)). Determinannya juga bukan lagi butuh-material, melainkan ketersediaan `MONo` semata. Alasan kenapa `MONo` Order lama tidak bisa ditunggu lewat scheduler seperti B2 **tetap berlaku**: `MONo` Order lama ini **statusnya independen**, tidak terikat ke event apa pun dari Finding baru ini — bisa jadi sudah lama ada, bisa juga genuinely stuck, tidak ada pipeline baru yang predictable untuk ditunggu. Yang berubah cuma **siapa yang menanggung tunggu itu**: dulu mechanic di depan, sekarang approver di belakang (alasan lengkap di [Poin 7](#poin-7-editability-window-sebelum-approval)).
3. **Reuse (Sub-kasus A), tidak butuh material** → **eager-trigger**, sama seperti poin 1 (tidak ada dependency fisik apa pun yang perlu dicek).
4. **B1 (Order baru, tidak butuh material)** → **eager-trigger** (create+close TECO sekaligus) begitu Planner approve + sync SAP — desain awal tetap valid.
5. **B2 (Order baru, butuh material)** → **submit tetap jalan normal, tidak di-block** (beda dari reuse — `MONo` Order baru **memang selalu** NULL di titik submit, itu bukan sinyal masalah, cuma pipeline yang belum jalan). Order Approval selesai seperti biasa → **scheduler** yang urus triggernya (detail di bawah) — **bukan** mekanisme "3 jalur eksekusi MO Backlog" manual (itu tetap ada tapi untuk backlog **biasa**, bukan buat Finding `IsImmediateExecutable=Yes` Phase 2 ini).

**Kenapa reuse dan B2 beda perlakuan meski sama-sama "butuh material + `MONo` belum diketahui":** untuk **B2**, Order Approval **memicu langsung** pipeline baru yang predictable — create `PoolingMOItem` → sync SAP → `MONo` terbentuk → response balik ke `SAPMOSyncOrder`. Ini kejadian **fresh**, terikat ke approval Finding ini, jadi masuk akal ditunggu/di-schedule. Untuk **reuse**, `MONo` yang ditunggu adalah status Order **lama** yang independen dari submission ini (eMOL vehicle-approval untuk reuse **skip total** sync SAP — [lihat Poin 5](#poin-5-data-flow-defect-dan-crack)) — tidak ada pipeline baru yang predictable untuk dijadikan patokan, jadi block di depan lebih tepat daripada menunggu tanpa kepastian.

**~~Blocking untuk reuse + butuh material + `MONo` NULL — pesan validasi (di titik Submit)~~ — dicabut (2026-08-19):** mechanic **tidak pernah** di-block terkait `MONo`. Yang ada di sisi mechanic hanya peringatan **non-blocking**:

> *"Order ini belum confirmed ready — eksekusinya tetap tercatat, tapi penutupannya menunggu approval."*

~~User punya 2 jalan keluar: **uncheck `IsImmediateExecutable`**, atau **skip/back** dari kandidat ini.~~ Dua jalan keluar itu ikut dicabut. "Uncheck" justru menyuruh mechanic mencatat bahwa ia **tidak** mengerjakan pekerjaan yang sudah ia kerjakan — `IsImmediateExecutable` adalah pernyataan fakta, bukan permintaan (alasan lengkap di [Poin 7](#poin-7-editability-window-sebelum-approval)). Block-nya pindah ke **final approval**, dan di sana approver punya remedy yang sebenarnya: menunggu `MONo` datang, atau memakai escape valve ber-pop-up secara sadar.

**Scheduler untuk B2 (Order baru, butuh material, `IsImmediateExecutable=Yes`) — mekanisme baru (2026-08-18):** job terjadwal **2x/hari, 1 jam sebelum shift berakhir** (jam shift persis perlu dikonfirmasi ke BPO client — placeholder dulu, mis. kalau shift 06:00–18:00/18:00–06:00 berarti jalan ~17:00 & ~05:00). Kandidat yang diproses tiap run:
- `IsImmediateExecutable=Yes`
- Order butuh material (`NoPartsRequired=0`)
- Order Approval sudah **fully approved** (final, bukan tier pertama)
- **Genuine Order baru** (bukan reuse — `ReuseOrderNumber`/`ReuseSAPOrderNumber` NULL di titik ini)
- `SAPMOSyncOrder.MONo` **sudah terisi** (response dari SAP sudah diterima)
- `BacklogExecutionList` **belum pernah** dibuat untuk Order ini

Aksinya: create `BacklogExecutionList` (`WorkOrderId` dari konteks Finding, `MONumber` dari `SAPMOSyncOrder.MONo` yang sudah diketahui) → TECO jalan lewat mekanisme **§9.3 existing**, tidak perlu mekanisme baru untuk pengiriman TECO-nya sendiri. Kandidat yang `MONo`-nya **masih** belum terisi saat scheduler jalan → **di-skip**, dicek lagi di run berikutnya (~12 jam kemudian). **Residual/belum didesain:** ada batas maksimum berapa kali di-skip sebelum butuh eskalasi/notifikasi manual (kalau sync SAP-nya genuinely stuck lama) — dicatat sebagai open item implementasi, bukan blocker desain.

**Konsekuensi ke skema — field manual `ReuseSAPOrderNumber` cuma dibutuhkan untuk escape hatch:** untuk reuse dengan `PoolingMOItem`, field ini **tidak pernah** diisi manual — kalau `MONo` sudah diketahui, otomatis lengkap; kalau belum, field **tetap kosong** dan yang di-block adalah **final approval**, bukan submit (revisi 2026-08-19 — sebelumnya alasannya "submit di-block duluan"). State "submit lolos tapi field-nya kosong" memang terjadi, dan itu **disengaja**: pengisian manual bukan jawabannya, menunggu `MONo` atau escape valve approver yang jadi jawabannya. Manual input **cuma** dibutuhkan untuk **escape hatch** (Order yang genuinely tidak pernah masuk Digiman+, tidak ada mekanisme sync/scheduler apa pun yang bisa diandalkan di situ).

**Resolved (2026-08-19) — matrix turun dari 20 baris jadi 10 baris, tanpa kehilangan satu kasus pun:**

**Status SAP bukan lagi dimensi gate.** Yang tersisa hanya `MONo` — terisi atau NULL. Status REL/CRTD tidak diperiksa Digiman+ sama sekali; SAP yang menolak TECO kalau belum eligible, dan retry existing yang menyelesaikan begitu Order jadi REL. Status **terminal (TECO/CLSD) ditangani lebih awal** — Order seperti itu di-exclude dari candidate scope ([Poin 6](#poin-6-duplicate-atau-correlation-handling)), jadi tidak pernah sampai ke titik ini.

`MONo` NULL hanya mungkin di **A1 yang belum pernah sync** (`PoolingMOItem` ada, `MOOpen` belum ada). A2 selalu punya `MONumber` dari `MOOpen`; A-manual selalu punya dari input user (tidak terverifikasi — accepted risk).

`ButuhMaterial` **gugur sebagai dimensi outcome untuk reuse** — setelah GI resolved, material tidak lagi mengubah timing TECO di jalur reuse; ia hanya relevan sebagai validasi tulis ([Poin 7](#poin-7-editability-window-sebelum-approval)) dan sebagai pembeda B1/B2. Kolom `Submit` juga gugur: **tidak ada satu pun kondisi reuse yang di-block di sisi mechanic**.

**Tabel — 10 baris, tiap kolom selalu diisi nilai konkret (tidak ada "N/A"/"tidak relevan" untuk dimensi yang sebenarnya punya nilai):**

| # | Kondisi | `MONo` | `IsImmediateExecutable` | Final Approval | Create `PoolingMOItem` → Sync SAP | TECO ke SAP |
|---|---|---|---|---|---|---|
| 1 | A1 / A2 | Terisi | Yes | Lolos | Tidak pernah | Immediate — final Order Approval |
| 2 | A1 / A2 | Terisi | No | Lolos | Tidak pernah | Tidak ada |
| 3 | A1 (belum sync) | NULL | Yes | **Blocked** — sampai `MONo` confirmed. Escape valve: turunkan ke `No` (pop-up warning) → jadi baris 4 | Tidak pernah | Immediate — begitu approval lolos |
| 4 | A1 (belum sync) | NULL | No | Lolos | Tidak pernah | Tidak ada |
| 5 | A-manual | Manual ⚠ | Yes | Lolos | Tidak pernah | Immediate — final Order Approval |
| 6 | A-manual | Manual ⚠ | No | Lolos | Tidak pernah | Tidak ada |
| 7 | B1 | — | Yes | Lolos | Final Order Approval | Immediate — begitu `MONo` confirmed dari create-response |
| 8 | B1 | — | No | Lolos | Final Order Approval | Tidak ada |
| 9 | B2 | — | Yes | Lolos | Final Order Approval | **Scheduler — 2x/hari dekat shift-end** |
| 10 | B2 | — | No | Lolos | Final Order Approval | Tidak ada |

**Legend:**
- Baris 1–6 = disebut **Sub-kasus A** di bagian lain dokumen ini (A1/A2/A-manual); baris 7–8 = **B1**, baris 9–10 = **B2**.
- **Baris 3 = satu-satunya block di seluruh matrix, dan letaknya di sisi approver.** Sebabnya bukan kesiapan SAP, melainkan `BacklogExecutionList.MONumber` yang **NOT NULL** — tanpa `MONo`, insert-nya tidak bisa terjadi dan tidak ada apa pun yang bisa dikirim ke SAP untuk ditolak. **Remedy utama: menunggu `MONo` datang.** Approver tetap punya escape valve (turunkan ke `No`) supaya approval tidak pernah buntu total — tapi ada konsekuensi data, lihat [Poin 7](#poin-7-editability-window-sebelum-approval).
- **Status REL tidak diperiksa di mana pun.** MO berstatus CRTD tetap muncul sebagai kandidat, tetap bisa disubmit, tetap bisa di-approve — TECO ditembak, SAP menolak, retry existing berhasil sendiri begitu Order jadi REL. Konsisten dengan keputusan GI yang sudah ada.
- **Status terminal (TECO/CLSD) tidak pernah sampai ke matrix ini** — di-exclude di candidate scope ([Poin 6](#poin-6-duplicate-atau-correlation-handling)). Alasannya beda dari CRTD: Order terminal **tidak akan pernah** jadi REL, jadi retry akan gagal selamanya, sementara row `BacklogExecutionList` sudah terlanjur ter-insert dan tidak ada yang membersihkannya.
- **Mechanic tidak pernah kena block terkait `MONo`.** Di sisi mechanic hanya ada peringatan non-blocking: *"Order ini belum confirmed ready — eksekusinya tetap tercatat, tapi penutupannya menunggu approval."* Alasan pemindahan ada di [Poin 7](#poin-7-editability-window-sebelum-approval).
- **⚠ (baris 5–6) = Accepted Risk, status SAP A-manual tidak terverifikasi.** MO Number diinput manual dan tidak ketemu di `MOOpen`, jadi tidak bisa dicek apakah terminal. Ini satu-satunya jalan Order terminal bisa lolos ke TECO — dan itu diterima, karena SAP tetap menolak.
- **Marker ⚠ material dihapus.** Ketiga arah risikonya sudah tertutup (lihat tangga **Sumber Data Order** di [User Journey — Defect](#user-journey--defect-2026-08-13)), jadi tidak ada baris yang perlu ditandai.
- **Kolom Create/Sync = satu pipeline, dua langkah.** `PoolingMOItem` adalah **staging table** untuk sync SAP, bukan tujuan terpisah: Order Approval → insert `PoolingMOItem` → publish ke SAP → `MONo` terbentuk → balik ke `SAPMOSyncOrder`. Nilai `Final Order Approval` di kolom ini berarti **kedua langkah** dipicu di titik itu.
- **"Tidak pernah" berarti tidak pernah untuk dua-duanya.** Jalur reuse (baris 1–6) tidak insert `PoolingMOItem` dan tidak publish ke SAP — Order-nya sudah ada di ERP (untuk A-manual: diklaim ada, tidak terverifikasi). Konsekuensi yang perlu disadari: **eMOL reuse tidak pernah menjadi kandidat baru** di kemudian hari, karena kandidat di-drive dari union `PoolingMOItem` ∪ `MOOpen` (lihat **Kondisi data** di atas dan [Poin 6](#poin-6-duplicate-atau-correlation-handling)) dan eMOL reuse tidak masuk keduanya. Yang tetap jadi kandidat adalah Order lama yang direuse — dan itu memang benar, kalau tidak akan muncul dua kandidat untuk satu MO yang sama.
- **Baris 7 vs 9:** B1 menunggu event create-response, B2 pakai scheduler karena harus menunggu GI selesai — satu-satunya baris yang pakai scheduler di seluruh matrix.

**Resolved:**
- ~~Scope kerja "sambungkan backend"~~ — **terjawab lengkap** lewat mekanisme di [Poin 5](#poin-5-data-flow-defect-dan-crack): menyimpan `TaskPersonalizedFinding`/`TaskPersonalizedFindingMaterial`/`CrackIdentified`, publish ke topic, DAN trigger create `MechanicOrderSummary`/`MechanicOrderList` (baik create-baru maupun reuse-vehicle) — bukan cuma menyimpan Finding saja. **Koreksi (2026-08-17):** klaim "lengkap" ini sebelumnya cuma benar untuk sisi `maintenance-execution` — `CrackIdentified` ternyata tidak punya tujuan di `maintenance-order` sama sekali (gap, [lihat detail di Poin 5](#poin-5-data-flow-defect-dan-crack)), baru resolved sekarang dengan tabel baru `MechanicOrderCrackIdentified`.
- ~~UI View detail~~ — **selesai**: List Suggestion Order Lama, View Detail Order, Order Type/Activity Type/Material digabung ke 1 layar, dan tampilan post-submit (icon kaca pembesar → model 3-state: abu-abu/warning-incomplete/merah-oranye-solid sesuai warna Condition — [detail lengkap](#current-state--mobile-app-ui-v400); entry-point buka balik/tambah Finding, default buka ke Tab Finding #1 kalau >1) semua sudah didesain. Lihat [List Suggestion Order Lama](#ui-view-detail--list-suggestion-order-lama-2026-08-14), [View Detail Order](#ui-view-detail--view-detail-order-2026-08-14), [User Journey — Defect](#user-journey--defect-2026-08-13), [Current State UI](#current-state--mobile-app-ui-v400). Verifikasi implementasi aktual baru bisa dilakukan setelah backend jalan — bukan blocker diskusi, cuma blocker testing.
- ~~Konsekuensi consumer untuk escape hatch~~ — **resolved**: mekanisme sama persis dengan eMOL vehicle-approval Sub-kasus A ([Poin 5](#poin-5-data-flow-defect-dan-crack)), bedanya `MONumber` selalu dari input manual (lihat detail di atas).
- ~~Timing TECO untuk kasus butuh material (B2, dan Sub-kasus A kalau `NoPartsRequired=0`)~~ — **resolved (2026-08-18)**: tidak perlu tahu status GI duluan — tetap trigger TECO di titik yang sama seperti B1/tanpa-material, biarkan SAP validasi & tolak kalau belum siap, retry mechanism existing yang tangani konvergensinya. [Detail & residual monitoring concern di atas](#poin-1-trigger-dan-ui-create-defect-atau-crack).

**Masih open:**
- **Mekanisme percepatan/prioritas untuk Sub-kasus B2** (lihat di atas) — belum didesain sama sekali.
- **B1 perlu konfirmasi ke BPO client** sebelum dianggap final — sebagai validasi rutin.

~~Crack Defect punya 2 opsi "Identified" (`Monitor` vs `Repair Required`) — apakah keduanya sama treatment?~~ — **resolved**: sudah dijawab di [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack) — keduanya sama-sama trigger Order, bedanya cuma priority.

#### User Journey — Defect (2026-08-13, konsolidasi 2026-08-15)

Scope: **Defect saja** — Crack dibahas terpisah nanti (skenarionya beda, lihat open item di bawah).

1. **Trigger** — user sedang mengerjakan Form apapun (Inspection/PM Shutdown/BD Corrective — [form-centric](#order-integration-bersifat-form-centric-bukan-per-fitur)), jawab pertanyaan dengan opsi "Identified" → navigasi ke layar **"Defect Identified"** (1 layar tunggal, lihat catatan di bawah kenapa bukan navigasi ke screen terpisah).
2. **Isi Form Defect** — Component & Sub Component, Damage Code, Cause Code, Action Remedy, Priority, Defect Notes, Repair Duration, Repair Instructions, evidence/foto ([Current State — Mobile App UI](#current-state--mobile-app-ui-v400)), dan checkbox **`IsImmediateExecutable`**.
3. **Correlation check ([Poin 6](#poin-6-duplicate-atau-correlation-handling)) — jalan di KEDUA kondisi `IsImmediateExecutable`** (bukan cuma saat `Yes` — masalah duplicate Order tidak eksklusif ke immediate execution, bisa terjadi kapan saja defect yang sama ke-record ulang). **Trigger-nya button eksplisit** — label **"Check Existing Defect"** (atau **"Check Existing Crack"** untuk TaskKit Crack Defect, dinamis sesuai konteks — bukan "Check Existing Order", supaya sesuai mental model user yang mikirnya "pernah lihat ini sebelumnya", bukan konsep Order yang levelnya lebih backend, 2026-08-15) — **enabled setelah Component/SubComponent/DamageCode terisi** (3 field correlation key), **bukan otomatis jalan sendiri**. User tap button ini → sistem search Order lama by Asset+Component+SubComponent+DamageCode (precise match) **+** Asset+Site Code saja untuk kandidat `MOOpen`-only (broader match, badge beda) → tampilkan **List Suggestion** (single-select, boleh skip/back kalau tidak relevan → diperlakukan sama seperti "tidak ketemu"). **Catatan (2026-08-17):** tampilan visual tombol ini (styling, posisi persis) **butuh UI designer** untuk finalisasi — label & behavior/objective-nya (kapan enabled, apa yang di-trigger) sudah didefine di dokumen ini, tinggal dieksekusi visualnya. **Ditambah (2026-08-17)** — state lain yang juga butuh UI designer: **loading state** selagi search berjalan, **error state** kalau search gagal (mis. network error di tengah proses meski device online), dan **"tidak ketemu"** (search selesai tapi kandidat kosong) — 3 state ini belum ada tampilannya, cuma behavior-nya yang sudah jelas ("tidak ketemu" diperlakukan sama seperti skip/back, [lihat poin 4 branch table](#user-journey--defect-2026-08-13)).
4. **Branch hasil correlation:**

| Kondisi | Hasil |
|---|---|
| **Ketemu & dipilih**, `IsImmediateExecutable=Yes` | Section Order Type/Activity Type/Part **muncul, read-only** di UI mobile (user tidak bisa edit), tapi **tetap ditulis penuh** ke eMOL baru yang dibentuk (snapshot-copy dari Order lama — lihat mekanisme "vehicle approval" di [Poin 5](#poin-5-data-flow-defect-dan-crack)). **Fallback (2026-08-15):** kalau Order lama **tidak punya** `ActivityType`/`ActivityTypeName` terisi (Order dibuat sebelum enhancement Activity Type dirilis, forward-only migration — lihat [Poin 5](#poin-5-data-flow-defect-dan-crack)) → field Order Type/Activity Type **jadi enabled**, user pilih manual (bukan stuck kosong read-only). eMOL baru ini **lewat Planner approval seperti biasa** (preventive check atas keputusan reuse), lalu post-approval **trigger `BacklogExecutionList`** ke Order lama (bukan sync SAP sebagai MO baru — detail di Poin 5). ~~Kalau `MONo` Order lama masih NULL **dan** butuh material → **wajib** input manual SAP MO Number dulu sebelum submit.~~ **Resolved (2026-08-19):** tidak ada input manual di sini — `ReuseSAPOrderNumber` selalu auto dari `SAPMOSyncOrder.MONo` ([Poin 6](#poin-6-duplicate-atau-correlation-handling)). Submit tetap lolos; kalau `MONo` masih NULL, **final approval** yang di-block. Syarat `BacklogExecutionList.MONumber` yang **not null** tetap jadi sebab teknisnya — itu sebabnya block-nya ada, cuma pindah titik. |
| **Ketemu & dipilih**, `IsImmediateExecutable=No` | **⚠️ Reversed total (2026-08-16) — lihat alasan lengkap di [Poin 9](#poin-9-approval-flow).** Section Order Type/Activity Type/Part **muncul, read-only**, dan **SEKARANG tetap ditulis penuh** ke eMOL baru (mekanisme "vehicle approval" yang **sama persis** dengan cabang `Yes` di atas — snapshot-copy dari Order lama, lewat Planner approval). Alasan: **semua** defect/crack yang dihasilkan mechanic/foreman — apapun hasil `IsImmediateExecutable`-nya — butuh validasi supervisor/planner atas 3 keputusan: benar reuse Order lama atau tidak, executed sekarang atau tidak, butuh material atau tidak; keputusan itu **tanggung jawab level supervisor/planner**, bukan cuma self-declared mechanic tanpa oversight. **Post-approval beda dari cabang `Yes`** — begitu Planner approve, **tidak ada aksi lanjutan** (tidak trigger `BacklogExecutionList`, karena belum dieksekusi) — eMOL ini murni jadi **record bahwa Planner sudah validasi & setuju** defect ini memang sama dengan Order lama dan belum perlu dieksekusi sekarang. Order lama **tetap open, tidak disentuh/di-close**, akan dieksekusi lewat jalur normalnya nanti. **Sama seperti cabang `Yes`, eMOL ini SKIP sync SAP & `PoolingMOItem`** (reuse, apapun `IsImmediateExecutable`-nya, tidak pernah sync SAP sebagai MO baru — mencegah duplicate, [lihat Poin 5](#poin-5-data-flow-defect-dan-crack)). ~~Field SAP MO Number manual (kalau `MONo` Order lama NULL) tetap **opsional**~~ — **direvisi 2026-08-19: tidak ada field manual di cabang manapun** untuk kandidat ber-`PoolingMOItem`, `ReuseSAPOrderNumber` selalu kosong atau auto ([Poin 6](#poin-6-duplicate-atau-correlation-handling)). Cabang `No` tidak pernah tertahan karena `MONo` — tidak ada TECO yang perlu dipicu, jadi tidak ada yang di-block di titik manapun. |
| **Tidak ketemu di Digiman+, tapi user tahu Order-nya ada di SAP** (escape hatch) | Opsi manual "saya tahu Order ini sudah ada di ERP" → input MO Number (mandatory), lalu **sistem lookup dulu** — ketemu → Order Type/Activity Type/Material **read-only derived** seperti A1/A2; tidak ketemu → **manual semua** ([revisi 2026-08-19, detail lookup di Poin 6](#poin-6-duplicate-atau-correlation-handling)). Defect nempel ke MO Number itu, tidak create Order baru di Digiman+. |
| **Tidak ketemu sama sekali** | Section Order Type/Activity Type/Part **manual/editable**, submit sebagai Order baru — Sub-kasus B1/B2 kalau `Yes`, flow backlog normal kalau `No`. |

5. **Material — tidak mandatory** di semua cabang yang section-nya muncul — bisa dibiarkan kosong, reuse pola `NoPartsRequired` existing.
6. **Submit — 1 aksi save ke `maintenance-execution` saja** (`TaskPersonalizedFinding` + kolom baru `OrderType`/`ActivityType`/`ReuseOrderNumber`/`ReuseSAPOrderNumber` + tabel baru `TaskPersonalizedFindingMaterial`) — hindari dual-service-call/race condition ([Poin 5](#poin-5-data-flow-defect-dan-crack)).
7. **Sync ke Order (async)** — publish ke topic → `maintenance-order` consume (polling, delay maks ~5 detik) → create `MechanicOrderSummary` (1:1 baru) + `MechanicOrderList` (`Type='Form'`) + `Detail`/`Material`/`Evidence`. **Reversed (2026-08-16):** ini sekarang berlaku untuk **SEMUA** cabang yang section-nya muncul, **termasuk "ketemu & dipilih, `No`"** (sebelumnya dikecualikan, sekarang juga bikin eMOL — [lihat Poin 9](#poin-9-approval-flow) untuk alasan lengkap). Tidak ada lagi cabang yang skip publish sama sekali kalau correlation sudah menghasilkan match yang dipilih.
8. **Approval** — tetap lewat gate Planner sebelum push SAP ([Poin 9](#poin-9-approval-flow)) untuk semua Order baru/di-close.

**Material/Order Type/Activity Type — digabung ke 1 layar "Defect Identified" (revisi 2026-08-14), BUKAN navigasi ke screen "Order Details"/Add Part terpisah:** sempat diputuskan "reuse screen Order Details/Add Part" (navigasi ke screen lain) — **direvisi setelah klarifikasi user**: konsep defect/crack di Form ini sengaja **disederhanakan jadi 1 layar tunggal literal**, beda dari Inspection existing yang emang 2 fitur/screen terpisah ("Inspection — Add Finding" lalu screen "Order" terpisah, lihat [Poin 5](#poin-5-data-flow-defect-dan-crack) untuk alasan lengkapnya). Jadi Order Type\*/Activity Type\*/Part\* **jadi section tambahan di dalam layar "Defect Identified" itu sendiri** — perilakunya beda tergantung kondisi hasil correlation (poin 4 di atas, **direvisi lagi 2026-08-16**): **editable** saat "tidak ketemu Order lama" (apapun `IsImmediateExecutable`), **read-only derived, ditulis ke Order** saat "ketemu & dipilih" — **berlaku sama untuk `Yes` maupun `No`** (sebelumnya `No` "murni display, tidak ditulis" — **dibalik**, sekarang kedua kondisi ini sama-sama menulis penuh ke eMOL vehicle-approval & lewat Planner approval, cuma beda di post-approval action-nya, [lihat Poin 9](#poin-9-approval-flow)) — section-nya **selalu muncul** di semua kondisi setelah correlation selesai, bedanya cuma editable/read-only, bukan lagi soal ditulis/tidak ditulis.

**Catatan (2026-08-17) — section Order Type/Activity Type/Part butuh UI designer:** ini section **baru**, bukan bagian dari screen "Defect Identified" yang sudah existing hari ini ([lihat Struktur Screen](#struktur-screen-defect-identified) — section ini tidak ada di 11 step yang sudah screenshot-verified). Pola field/logic-nya reuse dari screen "Order Details"/"Add Part" existing (lihat paragraf di bawah), tapi **assembly-nya ke dalam 1 layar baru ini belum ada visualnya** — behavior (editable/read-only per kondisi correlation) sudah didefine lengkap, tinggal dieksekusi UI designer.

**Yang tetap di-reuse: pola field & logic-nya, bukan navigasi screen-nya** — urutan `Order Type* → Activity Type* → Part*` (+ checkbox **"No parts required"** di section Part, elemen UI terpisah dari list material — [lihat skema & alasannya](#poin-5-data-flow-defect-dan-crack)), source dropdown (Order Type dari `MaterialCostType` — sudah ada di skema real; Activity Type dari `MaintenanceCategory`, difilter lewat `OrderTypeMaintenanceCategoryMapping` M:N — **✅ dikonfirmasi live (2026-08-16)**, tabel ini sudah rilis di skema real meski belum sempat masuk ke dokumen referensi kami saat itu; **beda dari `MechanicOrderList.ActivityType`/`ActivityTypeName`, yang dikonfirmasi masih belum live** — jadi cuma sebagian dari enhancement 2.2–2.5 yang sudah rilis, bukan semuanya, lihat [caveat lengkap di Poin 5](#poin-5-data-flow-defect-dan-crack)), dan pola pencarian/pilih material (`addedParts`/`partsToAdd`, konsep dari [material-list-api.md](../../architecture/inspection-order/material-list-api.md)/[material-save-api.md](../../architecture/inspection-order/material-save-api.md), keduanya dikonfirmasi ada di skema real) — semua ini jadi **acuan desain UI & logic**, dipasang inline di 1 layar, bukan navigasi ke screen terpisah. **API-nya sendiri tidak dipakai langsung** — sesuai keputusan [Poin 5](#poin-5-data-flow-defect-dan-crack) (1 save = 1 service), submit di layar ini tulis ke `maintenance-execution` (`TaskPersonalizedFinding`/`TaskPersonalizedFindingMaterial`), bukan panggil `SaveMolMaterialOrderCommand` (`maintenance-order`) langsung.

~~**Material tidak mandatory (2026-08-14):** user bisa biarkan section Part kosong dan tetap bisa submit — beda dari pola "Order Details" existing, yang memaksa user memilih salah satu (isi minimal 1 baris material, atau declare `NoPartsRequired`). Phase 2 sengaja lebih longgar: section Part optional total, tidak dipaksa pilih apapun.~~

**REVISED (2026-08-17) — balik ke mutual exclusivity, mandatory pilih salah satu:** keputusan "section Part optional total" di atas **dibalik**. Alasan (dari user): kalau checkbox "No parts required" **tidak** dicentang **dan** list Material **juga** dibiarkan kosong, itu jadi state ambigu — tidak jelas apakah mechanic memang belum tahu butuh part apa (niat isi belakangan) atau sekadar lupa declare. Checkbox "No parts required" kehilangan maknanya kalau boleh diabaikan begitu saja.

**Aturan baru:**
- Checkbox **dicentang** → section list Material **disembunyikan/disabled** (bukan cuma dibiarkan kosong — dihilangkan dari tampilan supaya jelas kalau ini pilihan sadar, bukan lupa isi).
- Checkbox **tidak dicentang** → list Material **wajib diisi minimal 1 baris** sebelum submit berhasil.
- **Validasi ini di titik Submit, bukan Save as Draft** ([konsisten dengan aturan 2 tombol & validasi inline merah](#struktur-screen-defect-identified) — draft tidak validasi mandatory apapun).
- **Scope: cuma berlaku di cabang editable/manual** (Order baru, tidak ketemu candidate reuse) — **tidak berlaku** saat reuse Order lama, karena section itu read-only-derived di sana, bukan input user ([lihat di bawah](#poin-5-data-flow-defect-dan-crack)).

**Gap yang ke-catch user (2026-08-16) — declare "No parts required" belum punya tempat penyimpanan di `maintenance-execution`:** checkbox "No parts required" **tetap ada** — sekarang malah **mandatory disentuh** (salah satu jalur di atas). Field penyimpanannya `TaskPersonalizedFinding.NoPartsRequired` (kolom baru, default `0`) — [lihat skema lengkap & alasan load-bearing-nya](#poin-5-data-flow-defect-dan-crack), propagate ke `MechanicOrderList.NoPartsRequired` yang sudah ada. **Catatan:** revisi mutual-exclusivity ini tidak mengubah keputusan backfill historis — row lama tetap `NULL`/tidak di-backfill ([lihat alasannya](#poin-6-duplicate-atau-correlation-handling)), aturan mandatory baru ini cuma berlaku untuk submission baru ke depan.

**Catatan bug existing yang berpotensi ikut kebawa (dari [material-list-api.md](../../architecture/inspection-order/material-list-api.md) Bagian 4–5):** logic picker material existing (yang jadi acuan) punya dedup yang salah dimensi (collapse Storage Location & Asset Model Code) dan tidak di-scope ke Asset yang sedang di-order. Karena kita **rewrite logic-nya di `maintenance-execution`** (bukan reuse API apa adanya seperti draft sebelumnya), bug ini **berpotensi tidak ikut kebawa** kalau logic baru didesain ulang dengan benar — tapi tetap dicatat sebagai referensi supaya tidak diulang.

**Material saat reuse Order lama — read-only, edit di-defer:** kalau Order lama ke-pilih, material-nya **diderive dari Order lama** (bukan dari input user di Finding baru), dan **untuk sekarang tidak bisa diedit** — alasan: kalau dikasih ability edit, butuh jalur khusus baru untuk propagate perubahan itu ke SAP/ERP. Di-defer.

**Gap yang ditemukan & resolved (2026-08-14) — kandidat reuse yang belum sync SAP tapi butuh material:** kandidat Order lama dengan `MONo` masih NULL (belum sync SAP, per [candidate scope Poin 6](#poin-6-duplicate-atau-correlation-handling)) **DAN** butuh material — secara fisik **tidak bisa langsung dieksekusi**, karena ambil material dari logistic mensyaratkan Order/Reservasi SAP sudah ada & di-print duluan (kendala fisik yang sama dengan [Sub-kasus B2](#poin-1-trigger-dan-ui-create-defect-atau-crack)). Ini bertentangan dengan tujuan `IsImmediateExecutable` kalau dibiarkan begitu saja.

**Keputusan:** kandidat ini **tetap muncul** di suggestion list (tidak di-exclude) — ~~tapi begitu dipilih **dan** `MONo`-nya masih NULL, field **input manual MO Number** jadi **mandatory** sebelum bisa submit (bukan sekadar opsional)~~. **Resolved (2026-08-19, supersede):** untuk kandidat ber-`PoolingMOItem`, `ReuseSAPOrderNumber` **selalu kosong dan tidak pernah diinput manual** — selalu auto dari `SAPMOSyncOrder.MONo` ([lihat Poin 6](#poin-6-duplicate-atau-correlation-handling)). Kalau `MONo` masih NULL dan `IsImmediateExecutable=Yes`, **final approval** yang di-block, bukan ditutup input manual. Alasan lama: kemungkinan SAP MO Number **sudah ada di sisi SAP** (sudah di-print, material sudah bisa diambil secara fisik) tapi **belum sempat sync balik ke Digiman+** (lag sinkronisasi) — user yang tahu di lapangan (mis. lihat langsung dokumen MO fisik) **wajib** input manual, karena tanpa nomor ini material tidak akan pernah bisa diambil (kendala fisik Sub-kasus B2).

**Konsekuensi ke skema:** ini mengkonfirmasi kita memang butuh **2 field baru** di `TaskPersonalizedFinding` untuk kasus reuse — (1) **`ReuseOrderNumber`** (reference ke `MechanicOrderList.Number` Order lama yang dipilih, selalu ada **kalau** kandidatnya punya row lokal di Digiman+) dan (2) **`ReuseSAPOrderNumber`** (nomor MO SAP — ~~**mandatory kalau `MONo` old order masih NULL** dan butuh material~~, **direvisi 2026-08-19:** tidak pernah diinput manual untuk kandidat ber-`PoolingMOItem`, auto dari `SAPMOSyncOrder.MONo`; input manual hanya di escape hatch yang lookup-nya gagal). Field kedua ini beda karakter dari draft awal (bukan "cached copy buat fallback lookup" yang sempat dipertimbangkan lalu ditolak — tapi genuinely **data baru dari user** yang belum ada di Digiman+ manapun sampai user input di titik ini). **Rasional lengkap kenapa 2 field terpisah (bukan 1 field serbaguna) & cakupan penuhnya lintas semua kondisi kandidat — [lihat Poin 6](#poin-6-duplicate-atau-correlation-handling).**

**~~Konsekuensi ke consumer `maintenance-order` — resolved (2026-08-15)~~ — tidak lagi punya pemicu (2026-08-19):** mekanisme ini mengisi `MONo` yang NULL di `PoolingMOItem`/`SAPMOSyncOrder` milik Order lama, memakai nilai manual yang di-supply user. **Nilai itu sudah tidak ada.** Input manual dihapus untuk kandidat ber-`PoolingMOItem` ([Poin 6](#poin-6-duplicate-atau-correlation-handling)), sementara kandidat yang **punya** nilai (A2 dan A-manual) justru **tidak punya row `PoolingMOItem`** untuk di-update. Irisan keduanya kosong, jadi tidak ada kondisi yang bisa menjalankannya — **jangan diimplementasikan sebagai cabang kode.** Konsekuensinya (sync tersendat tidak punya jalur perbaikan manual di dalam fitur ini) sudah dicatat sebagai open item visibilitas di [Poin 7](#poin-7-editability-window-sebelum-approval).

**Berlaku juga untuk cabang `IsImmediateExecutable=No` — disederhanakan (2026-08-16, reversed):** ~~field MO Number di cabang `No`+reuse tetap **opsional** (bukan mandatory, karena tidak ada eksekusi sekarang)~~ — **direvisi 2026-08-19: selalu kosong, tidak ada input manual di cabang manapun untuk kandidat ber-`PoolingMOItem`.** Yang tetap berlaku dari keputusan 2026-08-16: **tidak perlu lagi 2 jenis publish terpisah**. Sebelumnya cabang `No` dianggap "tidak memicu publish full Order", jadi update `MONo` ke Order lama butuh publish targeted sendiri — **itu sudah tidak berlaku**: cabang `No` sekarang **juga** memicu publish full eMOL vehicle-approval (sama seperti `Yes`, [lihat tabel branch](#user-journey--defect-2026-08-13)), jadi update `MONo` manual (kalau diisi) tinggal **ikut ke dalam payload publish penuh yang sama** — tidak ada lagi kebutuhan jalur publish terpisah/lebih ringan.

**Skenario "tidak ada Order lama" — dikonfirmasi bisa terjadi:** defect yang sama bisa saja pernah ditemukan di pekerjaan sebelumnya tapi **di-decline approver** (kapabilitas existing — approver sudah bisa decline defect) — sehingga tidak ada Order yang "masih open" untuk di-correlate meski defect-nya bukan baru pertama kali ketemu. Fallback: user submit sebagai Order baru (poin 4 di atas, cabang "tidak ketemu").

**Escape hatch — Order yang cuma ada di SAP, belum pernah masuk Digiman+ sama sekali (2026-08-14):** kasus beda dari di atas — correlation search kita cuma jalan di data Digiman+ (`MechanicOrderList`/`PoolingMOItem`/`MOOpen`), jadi kalau Order dibuat **manual langsung di SAP** (di luar Digiman+) dan belum sempat sync ke `MOOpen`, search kita otomatis kosong meski Order-nya nyata ada di SAP. Kalau dibiarkan lewat jalur "tidak ketemu" biasa (create Order baru), risikonya **duplicate MO di SAP** untuk 1 defect yang sama — masalah yang sama seperti yang Poin 6 coba hindari, cuma tidak tertangkap correlation karena sumbernya di luar Digiman+.

**Keputusan:** tambah opsi manual di cabang "tidak ketemu" — user bisa pilih **"saya tahu Order ini sudah ada di ERP"**, lalu input **MO Number manual** (mandatory saat opsi ini dipilih). ~~Karena Digiman+ tidak punya data apapun soal Order SAP itu (tidak pernah tersimpan di manapun), **Order Type/Activity Type/Material tetap diisi manual** oleh user (tidak ada yang bisa di-derive, beda dari cabang reuse-dari-suggestion yang materialnya read-only).~~ **Resolved (2026-08-19):** premisnya keliru — Order-nya bisa saja **ada** di `MOOpen`/`CheckPartOrder` tapi tidak lolos filter correlation. Sistem menjalankan lookup by `MONumber` dulu; manual hanya fallback kalau lookup gagal ([detail di Poin 6](#poin-6-duplicate-atau-correlation-handling)). Defect ini nempel/di-link ke SAP MO Number itu (lewat field manual yang sama dengan [gap-sync sebelumnya](#poin-1-trigger-dan-ui-create-defect-atau-crack)), bukan create Order baru di sisi Digiman+.

**Catatan (2026-08-17):** opsi/input manual ini **baru** (Phase 2, belum ada di app hari ini) — tampilan visualnya **butuh UI designer**, mekanisme/kapan mandatory-nya sudah didefine.

**Resolved (2026-08-18) — bentuk kontrol UI:** opsi "saya tahu Order ini sudah ada di ERP" pakai **checkbox**. ~~Karena Order Type/Activity Type/Material tidak bisa di-derive sama sekali di cabang ini~~ — **direvisi 2026-08-19:** bentuk section ditentukan **hasil lookup**, bukan otomatis manual. Kalau lookup gagal (A-manual), barulah ketiganya diisi manual oleh user — termasuk **Material**, yang mengikuti alur declaration yang sama dengan flow utama ([checkbox "No parts required" mutual-exclusive dengan list Material](#user-journey--defect-2026-08-13), divalidasi di titik Submit) — bukan mekanisme terpisah.

**Resolved (2026-08-18) — copy checkbox:** *"I confirm this Order already exists in the ERP."* — final wording pending review UI Designer/copywriter, tapi arah teksnya sudah disepakati.

**Resolved (2026-08-18) — reuse-dari-suggestion dan escape hatch checkbox saling mutually exclusive:** dua-duanya cuma 2 cara berbeda menuju hasil yang sama (link Finding ke Order existing), jadi tidak boleh aktif bersamaan — mencegah ambiguitas soal Order mana yang sebenarnya dituju kalau user sempat menyentuh keduanya.
- **Trigger disable di titik SELEKSI, bukan di titik menjalankan search:** sekadar tap "Check Existing" (menjalankan search, lihat List Suggestion) **belum** men-disable checkbox — user masih boleh eksplorasi dulu. Begitu user **benar-benar memilih** 1 kandidat dari List Suggestion → checkbox "I confirm..." jadi **disabled**. Sebaliknya, begitu checkbox dicentang → button "Check Existing"/hasil pilihan yang sudah ada jadi **disabled**.
- **Jalan balik eksplisit, bukan cuma disabled tanpa penjelasan:** kalau user sudah pilih kandidat lalu berubah pikiran mau pakai escape hatch (atau sebaliknya), sediakan aksi eksplisit untuk **clear pilihan yang aktif** (mis. tombol/link "Change" atau "×" di samping ringkasan kandidat yang sudah dipilih) — begitu di-clear, kontrol yang tadinya disabled ikut ter-enable lagi. Konsisten dengan mekanisme "bisa re-run Check Existing setelah pilih kandidat" yang sudah didesain — cuma sekarang eksplisit juga meng-cover arah sebaliknya (dari escape hatch balik ke reuse-dari-suggestion).
- **Butuh UI Designer** untuk visual persis disabled-state dan tombol "Change"/clear ini — behavior & trigger-nya sudah final di atas.

**Resolved (2026-08-18, final — supersede draft sebelumnya) — untuk escape hatch ini, `ReuseOrderNumber` dibiarkan NULL, `ReuseSAPOrderNumber` yang diisi dengan SAP MO Number manual.** Draft awal sempat mengusulkan `ReuseOrderNumber` dipakai ganda (menyimpan SAP MO Number kalau tidak ada row lokal) — **dibalik** setelah dipertimbangkan lebih lanjut: lebih baik tiap field punya 1 arti konsisten di semua kondisi (`ReuseOrderNumber` = selalu reference lokal Digiman+ atau NULL, tidak pernah diisi nilai lain) daripada menghemat 1 kolom tapi bikin logic baca-nya harus selalu cek "field ini isinya nomor lokal atau nomor SAP?". Detail lengkap mekanisme 2-field ini (berlaku untuk **semua** kondisi kandidat, bukan cuma escape hatch) ada di [Poin 6](#poin-6-duplicate-atau-correlation-handling).

**⚠️ Accepted Risk (2026-08-18, disempitkan setelah resolusi TECO/GI di atas) — declare `NoPartsRequired` di escape hatch ini murni self-declared, tidak terverifikasi ke SAP:** karena Order-nya dibuat di luar Digiman+, tidak ada cara sistem memvalidasi apakah declare user (termasuk `NoPartsRequired`) cocok dengan kondisi asli Order tersebut di SAP. **Konsekuensinya sekarang lebih ringan** dari draft awal — dengan resolusi TECO/GI ([lihat di atas](#poin-1-trigger-dan-ui-create-defect-atau-crack)), Digiman+ tidak lagi mencoba "menebak aman atau tidak" dari `NoPartsRequired` sebelum trigger TECO — TECO **selalu** dicoba di titik yang sama, SAP sendiri yang menolak kalau belum siap (GI belum ada), retry existing yang tangani. Jadi salah declare `NoPartsRequired` **tidak lagi** menyebabkan TECO premature ke SAP — paling jauh cuma bikin call itu gagal & retry sampai SAP benar-benar siap, bukan operasional yang salah.

**Resolved (2026-08-19) — Sumber Data Order (Order Type, Activity Type, Material), tangga 3 tingkat (menggantikan accepted risk material lama):** berurutan, berhenti di tingkat pertama yang menghasilkan data. Berlaku sama untuk ketiga field — **SAP tetap source of truth**, karena perubahan di SAP tidak terlihat dari sisi Digiman+.

| Tingkat | Order Type / Activity Type | Material |
|---|---|---|
| **1. Tabel hasil sync SAP** — otoritatif | `MOOpen.CostTypeCode` (Order Type), `MOOpen.MaintenanceCategoryCode`/`Name` (Activity Type) | `CheckPartOrder` (join `MONumber`). Kalau ada row, Material dari sini dan **`NoPartsRequired=Yes` gugur** |
| **2. Snapshot Order lama di service `maintenance-order`** — hanya kalau tingkat 1 kosong, hanya tersedia untuk **A1** | `PoolingMOItem.MOType` (Order Type), `PoolingMOItem.PMActType` (Activity Type) — **Code saja**, tabel ini tidak punya kolom Name | `MechanicOrderMaterial` |
| **3. Input user** — kalau tingkat 1 & 2 kosong | Manual/editable | Declare `NoPartsRequired`: `Yes` → **no issue**, sesuai ekspektasi, transaksi jalan. `No` → **blocking**, user wajib input material manual |

Alasan tangga ini: perubahan di SAP tidak terlihat dari sisi Digiman+, jadi snapshot di `maintenance-order` (`PoolingMOItem`, `MechanicOrderMaterial`) tidak boleh dipakai selama tabel hasil sync SAP (`MOOpen`, `CheckPartOrder`) punya jawaban.

**Tingkat 1 kosong itu normal, bukan error** — A1 yang belum pernah sync (`MONo` NULL, baris 3–4 matrix) memang belum punya row `MOOpen`/`CheckPartOrder`, jadi wajar jatuh ke tingkat 2.

**Kosong dievaluasi per field, bukan per tabel (2026-08-19, dicek ke data PRD).** Adanya row `MOOpen` **tidak menjamin** semua field-nya terisi — `MaintenanceCategoryCode`/`Name` (Activity Type) **bisa NULL** meski row-nya ada dan `CostTypeCode` terisi. NULL diperlakukan sama dengan "tidak ada row": field itu sendiri turun ke tingkat berikutnya, sementara field lain yang terisi tetap di tingkat 1. Jadi satu kandidat bisa mengambil Order Type dari tingkat 1 dan Activity Type dari tingkat 2 sekaligus.

**Kenapa tingkat 2 pakai `PoolingMOItem`, bukan `MechanicOrderList` (2026-08-19):** tiga alasan. **(1) Tidak perlu join** — kandidat sudah di-drive dari `PoolingMOItem` dan `ReuseOrderNumber` sudah dibaca dari `PoolingMOItem.EMOLNumber` ([Poin 6](#poin-6-duplicate-atau-correlation-handling)), jadi `MOType`/`PMActType` ada di row yang sama. **(2) Selalu tersedia untuk A1** — `PoolingMOItem` di-insert di titik Order Approval, sebelum sync SAP, jadi A1 yang belum sync (`MONo` NULL, baris 3–4 matrix) pun sudah punya row-nya. **(3) Lebih andal untuk Order historis** — `MechanicOrderList.ActivityTypeCode` adalah kolom **baru** Phase 2 ([lihat skema Poin 5](#poin-5-data-flow-defect-dan-crack)) dan **tidak masuk daftar backfill** ([lihat backfill Poin 6](#poin-6-duplicate-atau-correlation-handling)), jadi Order lama akan NULL di situ; `PoolingMOItem.PMActType` sudah ada sejak lama dan terisi.

**Yang tidak ada di `PoolingMOItem`: kolom Name.** `MOType`/`PMActType` menyimpan Code saja, jadi Name-nya di-resolve dari master data — atau diambil dari `MechanicOrderList.OrderTypeName`/`ActivityTypeName` kalau Order lama itu memang eMOL Phase 2 yang sudah punya kolom tersebut. Pola sama dengan `MONo` yang juga tidak disimpan di `PoolingMOItem` ([lihat E8 sourcing](#poin-6-duplicate-atau-correlation-handling)).

**Tangga ini soal seeding, bukan pembatalan prinsip snapshot-at-creation.** Nilai hasil derive tetap ditulis ke kolom milik eMOL/Finding baru itu sendiri — yang berubah cuma *dari mana* nilai awalnya diambil, bukan berubah jadi live-lookup tiap render.

**Accepted risk material lama dihapus, bukan ditulis ulang.** Rumusan "dua arah" sudah tidak akurat: arah *declare-tidak-butuh vs SAP-punya* selesai lewat tingkat 1 (`CheckPartOrder` menang, `NoPartsRequired=Yes` gugur), arah *declare-butuh vs tidak ada di mana pun* jadi **blocking** lewat tingkat 3.

**Catatan beda jenis blocking** — perlu ditulis supaya tidak disamakan:

| Blocking | Bisa diselesaikan user di tempat? |
|---|---|
| Material (tangga tingkat 3) | **Ya** — input material manual, submit lolos |
| `MONo` NULL | **Tidak oleh mechanic** — hanya approver, lewat menunggu atau escape valve ber-warning ([Poin 9](#poin-9-approval-flow)) |

**⚠️ Accepted Risk (2026-08-19) — status SAP A-manual tidak terverifikasi.** MO Number yang diinput manual dan tidak ketemu di `MOOpen` tidak bisa dicek statusnya. Yang penting di sini bukan CRTD (itu memang tidak di-block di mana pun), melainkan **status terminal**: kandidat A1/A2 yang sudah TECO/CLSD di-exclude di candidate scope ([Poin 6](#poin-6-duplicate-atau-correlation-handling)), sedangkan lewat A-manual Order terminal bisa lolos sampai TECO. Diterima — SAP tetap menolak, dan retry existing yang menangani.

**Resolved (2026-08-15):** mekanisme consumer-nya **sama persis** dengan "eMOL vehicle approval" untuk Sub-kasus A ([Poin 5](#poin-5-data-flow-defect-dan-crack)) — consumer create eMOL baru (full snapshot, isinya dari input manual user karena Digiman+ tidak punya data lain), lewat Planner approval seperti biasa, post-approval **skip sync SAP normal** (supaya tidak create MO baru yang duplicate dengan yang sudah ada di SAP), trigger `BacklogExecutionList` — bedanya cuma `MONumber`-nya **selalu** dari input manual (bukan kondisional seperti Sub-kasus A yang bisa derive dari `MONo` existing).

~~Open item: scope correlation untuk **Crack** tidak bisa dibatasi cuma jalan saat `IsImmediateExecutable=Yes` seperti Defect — dibahas detail nanti pas sesi Crack.~~ — **resolved (2026-08-15)**: sudah dijawab di [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack) — setelah revisi correlation jalan di kedua kondisi `IsImmediateExecutable`, open item ini otomatis resolved, Crack journey sama dengan Defect journey.

#### UI View Detail — List Suggestion Order Lama (2026-08-14)

Screen yang muncul saat correlation match ketemu ([Poin 6](#poin-6-duplicate-atau-correlation-handling)), sebelum user pilih mana yang mau di-reuse.

**Catatan (2026-08-17):** tampilan visual screen ini (layout, styling per baris kandidat, dkk) **butuh UI designer** untuk finalisasi — kolom/data/behavior (sourcing, selection, pengelompokan 2 section) sudah didefine lengkap di bawah, tinggal dieksekusi visualnya.

**Pengelompokan (2026-08-18, resolved):** kandidat ditampilkan dalam **2 section terpisah** (bukan 1 list digabung) — section **"Precise Match"** lalu section **"Broader Match"** di bawahnya — sesuai jalur search yang menemukan kandidat itu ([lihat fix di Poin 6](#poin-6-duplicate-atau-correlation-handling)). Layout persis 2 section ini (label, empty state per section) **butuh UI Designer**.

**Resolved (2026-08-18) — search/filter dalam list, dan MO Number tetap tampil setelah kandidat dipilih:**
- **Search/filter** — di dalam kandidat yang sudah ketemu (hasil precise/broader-match), user bisa ketik sebagian **Order Number** atau **MO Number** untuk mempersempit tampilan list. Ini murni filter client-side atas hasil yang sudah di-fetch — **bukan** lookup baru ke luar hasil correlation yang sudah ada (beda dari escape hatch, yang memang untuk kasus di luar hasil search).
- **Awareness setelah pilih** — begitu kandidat dipilih & user kembali ke layar "Defect Identified", **MO Number kandidat itu (kalau ada) tetap ditampilkan** di section Order Type/Activity Type/Material (bukan cuma sempat kelihatan di List Suggestion lalu hilang) — supaya user (dan approver nanti di View Detail Order) tetap aware Order SAP mana persisnya yang di-reuse, walau field-nya read-only.
- **Butuh UI Designer** untuk layout search box dan penempatan tampilan MO Number di layar utama.

**Kolom per baris kandidat (berlaku di kedua section):**

| Kolom | Sumber | Catatan |
|---|---|---|
| Order Number | `PoolingMOItem.EMOLNumber` | Sama value dengan `MechanicOrderList.Number` (join key existing, lihat [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md#52-bc-update-jika-ada-create-jika-tidak-ada--insert-ke-poolingmoitem)) — tidak perlu join balik ke `MechanicOrderList`. Kosong untuk kandidat di section Broader Match (`MOOpen`-only, lihat di bawah) karena `MOOpen` tidak punya field ini — terkait gap [Poin 13](order-integration-checklist.md#fase-e--integrasi). |
| MO Number | `MOOpen.MONumber` (join by `MONo`) | Kosong/dash kalau belum sync ke SAP. |
| Deskripsi Order | Lihat aturan sourcing Deskripsi di bawah | — |
| Status Order | Lihat aturan sourcing Status di bawah | — |
| — | Button **"View Detail Order"** | Isi/layout detail-nya belum dibahas. |

**Selection:** single-select (radio) — user cuma bisa pilih **satu** Order untuk direuse. Kalau ketemu kandidat tapi tidak ada yang relevan/mau di-reuse — **tidak ada tombol eksplisit "buat baru"**, user cukup **skip/back** dari screen ini, lanjut ke section Order Type/Activity Type/Part manual/editable seperti cabang "tidak ketemu" (2026-08-14). **Resolved (2026-08-17):** skip/back ini **andalkan back/close navigation device/app** — bukan tombol eksplisit "None of these match" terpisah.

**Resolved (2026-08-17) — bisa re-run "Check Existing" setelah sudah pilih 1 kandidat:** ya, boleh — user bisa ganti pikiran, buka lagi List Suggestion (via tombol "Check Existing Defect/Crack" yang sama) dan pilih kandidat lain atau batalkan pilihan sebelumnya, sebelum submit final.

**Aturan sourcing Deskripsi Order (2026-08-14)** — prioritas berdasarkan keberadaan row `PoolingMOItem`/`MOOpen`:

1. **`PoolingMOItem` match ke `MOOpen`** (sudah sync SAP & masih outstanding) → pakai `PoolingMOItem.MODescription`.
2. **`PoolingMOItem` ada, tapi tidak match ke `MOOpen`** (sudah lolos approval & masuk pipeline sync, tapi belum/tidak nongol di `MOOpen`) → tetap pakai `PoolingMOItem.MODescription`.
3. **`PoolingMOItem` tidak ada, tapi ada row di `MOOpen`** (kemungkinan skenario MO Backlog re-entry dari SAP, lihat [Poin 13](order-integration-checklist.md#fase-e--integrasi)) → fallback ke `MOOpen.MODescription`.
4. **Keduanya tidak ada** (Order belum lolos Planner approval) → **Order ini tidak muncul sebagai kandidat sama sekali** (lihat [candidate scope](#poin-6-duplicate-atau-correlation-handling) di atas), jadi kasus ini tidak pernah butuh fallback description.

**Aturan sourcing Status Order (2026-08-14)** — beda pola dari Deskripsi (cuma 2 kondisi, bukan prioritas 3 tingkat):

1. **Ada row di `MOOpen`** → pakai `MOOpen.Status` (status SAP asli, karena `MOOpen` adalah source backlog dari SAP).
2. **Selain itu** (tidak ada di `MOOpen`) → pakai `SAPMOSyncOrder.SAPStatus`, di-convert BE ke label:
   - `SAPStatus = 1` → **"Sync complete"**
   - `SAPStatus = 2` → tampilkan isi `SAPText` (pesan/error dari SAP)
   - Kalau `SAPStatus` masih NULL (row `SAPMOSyncOrder` masih placeholder, BAPI call belum selesai — lihat [5.4](../../architecture/inspection-order/order-emol-sap-sync.md#54-e-create-sapmosyncorder-placeholder-tracking-record)), Status Order tampil **kosong/dash** — tidak fallback ke `PoolingStatus`.

**Open item:** kandidat case 3 di Deskripsi (`PoolingMOItem` tidak ada, cuma ada di `MOOpen`) otomatis dapat status dari kondisi 1 di atas — konsisten, tidak butuh aturan tambahan.

**Material tetap seperti sudah disepakati** ([User Journey — Defect](#user-journey--defect-2026-08-13)): kalau kandidat ini dipilih, material auto-derive read-only dari Order lama, tidak bisa diedit (di-defer).

#### UI View Detail — View Detail Order (2026-08-14)

Screen drill-down dari button "View Detail Order" di [List Suggestion Order Lama](#ui-view-detail--list-suggestion-order-lama-2026-08-14) — bantu user yakin sebelum pilih kandidat untuk reuse. Sama field-nya dengan input form "Defect Identified" ([Current State UI](#current-state--mobile-app-ui-v400)), tapi ditampilkan **label + value read-only**, bukan disabled input field.

**Catatan (2026-08-17):** screen ini **baru** (drill-down Phase 2, tidak ada di app hari ini) — tampilan visualnya **butuh UI designer** untuk finalisasi, field/source data-nya sudah didefine lengkap di bawah.

**Source: `MechanicOrderDetail`/`MechanicOrderMaterial`/`MechanicOrderEvidence` (join dari `MechanicOrderListId`), bukan `PoolingMOItem`.**

Sempat dipertimbangkan pakai `PoolingMOItem` saja (supaya 1 tabel, tidak perlu join tambahan — toh row-nya sudah pasti ada berkat [candidate scope](#poin-6-duplicate-atau-correlation-handling)), tapi dicek lapangan: `PoolingMOItem` cuma staging table buat sync SAP, bukan tempat simpan record defect lengkap.

| Kolom `PoolingMOItem`? | Field |
|---|---|
| ✅ Ada (tapi isinya Name, bukan Code — lihat [Poin 6](#poin-6-duplicate-atau-correlation-handling)) | Component, Sub Component, Damage Code |
| ✅ Ada (kolom `Notes`, bukan `DefectNotes`) | Defect Notes |
| ✅ Ada (`MaterialNumber`/`MaterialQuantity`/`Batch`/`Plant`/`SLoc`) | Material Number, Qty, Batch, Plant, Storage Location |
| ❌ Tidak ada | Cause Code, Action Remedy, Priority, Repair Duration, Repair Instructions |
| ❌ Tidak ada | Material Description, UoM, Cost, Total Cost, Currency, Material Ranking |
| ⚠️ Tidak kompatibel struktur | Evidence — `MOAttachment` cuma 1 kolom varchar, sementara foto bisa >1 (3 slot + Add More di input form). Propagate ke sini butuh tabel child baru yang bakal duplikat `MechanicOrderEvidence` yang sudah ada. |

**Keputusan (2026-08-14):** tidak propagate field yang kurang ke `PoolingMOItem` — join langsung ke `MechanicOrderDetail`/`MechanicOrderMaterial`/`MechanicOrderEvidence`, yang sudah lengkap (snapshot-copy asli dari Finding) tanpa perlu perubahan skema. Pembagian source jadi jelas per concern: **List Suggestion** pakai `PoolingMOItem`/`MOOpen`/`SAPMOSyncOrder` (concern: status sync), **View Detail Order** pakai `MechanicOrderDetail`/`MechanicOrderMaterial`/`MechanicOrderEvidence` (concern: full record defect).

**Catatan (2026-08-16) — tabel di atas mengacu ke skema `PoolingMOItem` current state, bukan skema setelah enhancement manapun:** termasuk gap Cause Code/Action Remedy yang rencananya ditutup lewat [Resolusi Poin 6](#poin-6-duplicate-atau-correlation-handling) (2026-08-13) — belum tentu kapan itu rilis, jadi keputusan bypass `PoolingMOItem` di atas **sengaja tidak digantungkan** ke timeline enhancement itu (maupun ke [maintenance-activity-type-enhancement.md](../../architecture/inspection-order/maintenance-activity-type-enhancement.md) yang terpisah, juga belum diimplementasi). Robust terhadap timing: bahkan kalau Cause/Action Remedy sudah ditambahkan ke `PoolingMOItem`, gap lain (Priority, Repair Duration/Instructions, Material Description/UoM/Cost/Currency/Ranking, struktur Evidence) tetap bikin `PoolingMOItem` tidak cukup untuk full record — keputusan join langsung tidak berubah. **Prinsip umum:** kalau Phase 2 ini genuinely butuh field tambahan di suatu tabel, masukkan sebagai scope eksplisit sekarang (langsung dikerjakan), jangan digantungkan nunggu rilis enhancement terpisah yang timeline-nya tidak pasti.

**Field yang ditampilkan (label + value):**

| Label | Sumber |
|---|---|
| Evidence/Foto | `MechanicOrderEvidence` (list) |
| Component & Sub Component | `MechanicOrderDetail.ComponentName`/`SubComponentName` (2026-08-16: kolom Name baru, propagate dari `TaskPersonalizedFinding` — [lihat skema Poin 5](#poin-5-data-flow-defect-dan-crack)) |
| Damage Code | `MechanicOrderDetail.DamageName` (2026-08-16: kolom Name baru, sama pola) |
| Cause Code | `MechanicOrderDetail.CauseName` (2026-08-16: kolom Name baru, sama pola) |
| Action Remedy | `MechanicOrderDetail.ActionRemedyName` (2026-08-16: kolom Name baru, sama pola) |
| Priority | `MechanicOrderDetail.PriorityName` (2026-08-16: kolom Name baru, sama pola — resolve upstream di `TaskPersonalizedFinding`, propagate ke bawah, [lihat Poin 5](#poin-5-data-flow-defect-dan-crack)) |
| Defect Notes | `MechanicOrderDetail.DefectNotes` |
| Repair Duration | `MechanicOrderDetail.RepairDuration` |
| Repair Instructions | `MechanicOrderDetail.RepairInstruction` |
| Material (Number, Qty, UoM, Batch, dll) | `MechanicOrderMaterial` (list) — **`UoMCode` resolved (2026-08-16): tidak perlu companion Name**, tampil apa adanya (sudah human-readable, bukan ID yang butuh translasi) |
| Immediate Execution Status **(baru, 2026-08-16)** | `MechanicOrderDetail.IsImmediateExecutable` (kolom baru, propagate dari `TaskPersonalizedFinding.IsImmediateExecutable` yang sudah ada — snapshot-copy sederhana, bukan cross-service seperti `PriorityName`). Backfill row historis (ikut [prinsip backfill](#poin-6-duplicate-atau-correlation-handling) yang sama) — lebih sederhana dari kolom Name lain karena tinggal copy nilai boolean existing dari `TaskPersonalizedFinding`, tidak perlu resolve ke master data apapun. |
| Crack Description & Length **(baru, 2026-08-17 — khusus Crack)** | `MechanicOrderCrackIdentified` (list, tabel baru, gap yang baru ditemukan — [lihat Poin 5](#poin-5-data-flow-defect-dan-crack)) — cuma muncul kalau eMOL ini asalnya dari TaskKit Crack Defect, kosong/tidak ditampilkan untuk Defect biasa. |

**Revisi (2026-08-16) — `IsImmediateExecutable` SEKARANG ditampilkan, membatalkan keputusan lama:** sebelumnya sengaja di-exclude dengan alasan "context Finding, bukan atribut Order relevan" — **dibatalkan** setelah klarifikasi semantik ([lihat diskusi](#poin-1-trigger-dan-ui-create-defect-atau-crack)): field ini bukan sekadar niat/gate routing, tapi **pernyataan fakta eksekusi** ("mechanic sudah/sedang mengerjakan ini saat itu juga") — jadi genuinely relevan buat approver tahu status eksekusi saat review, bukan cuma konteks internal `maintenance-execution`. Ini juga jadi jawaban parsial untuk gap #1 di [Poin 9](#poin-9-approval-flow) (visibility status eksekusi) — approver sekarang bisa lihat `Yes`/`No` di View Detail Order, meski **belum menjawab verifikasi** (gap #2, masih perlu bukti pasca-perbaikan) atau **override** (gap #3).

**Asset/context header (2026-08-14) — source detail di-defer ke Poin 5 (Data Flow):**

`MechanicOrderSummaryId` **saat ini cuma keisi untuk Type='Additional'** — untuk Type='Inspection' masih NULL hari ini (confirmed by user/PM), meski 2 dokumen ([order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) & [maintenance-activity-type-enhancement.md](../../architecture/inspection-order/maintenance-activity-type-enhancement.md) 2.9a/2.10) sempat menyiratkan seragam — klaim dokumen kedua ternyata bagian dari rencana enhancement yang **belum diimplementasi**.

**Tapi ini belum menjawab pertanyaan sesungguhnya**: kandidat Order Phase 2 kita datang dari prinsip [form-centric](#order-integration-bersifat-form-centric-bukan-per-fitur) (Form dipanggil dari Inspection **maupun** PM Shutdown/BD Corrective/dst) — bukan cuma literal fitur "Inspection" yang jadi basis 2 dokumen di atas. Apakah `WorkOrderId` → `WorkOrder` (`maintenance-execution`) valid sebagai source Asset untuk **semua** fitur pemanggil Form, atau ada fitur yang datanya tidak lewat `WorkOrder` (mis. PM Shutdown/BD Corrective yang "Task/Backlog Execution tetap di `DPlanDB`", per [pm-shutdown-service-package.md](../phase1-service-package/pm-shutdown-service-package.md)) — **di-defer, dibahas detail di [Poin 5 — Data Flow Defect dan Crack](#poin-5-data-flow-defect-dan-crack)**, bagaimana defect/crack disimpan di `maintenance-execution` dan sync ke Order membentuk eMOL.

~~Catatan penting (2026-08-14): kemungkinan besar enhancement di maintenance-activity-type-enhancement.md akan benar-benar dikerjakan sebagai bagian dari Phase 2 ini untuk merapikan data flow-nya.~~ — **superseded (2026-08-17):** ternyata tidak diadopsi mentah-mentah. Phase 2 membangun kolom `OrderType`/`ActivityType`-nya **sendiri**, sengaja beda naming dari proposal enhancement itu ([lihat Poin 5](#poin-5-data-flow-defect-dan-crack)) — cuma **satu** bagian kecil dari enhancement itu yang ternyata relevan/live (`OrderTypeMaintenanceCategoryMapping`), bukan seluruh scope-nya. Jangan generalisasi "akan dikerjakan sebagai bagian Phase 2" — itu tidak terjadi seperti dibayangkan semula.

---

### Poin 2: Defect di Luar Pertanyaan Form (Additional Defect saat Eksekusi)

Skenario: mechanic ketemu defect yang tidak ada pertanyaan relevannya di form yang sedang dikerjakan (mis. sedang inspeksi engine, nemu retak di frame yang bukan bagian checklist hari itu). Baseline flow existing untuk kasus ini adalah **Additional Order** (lihat [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) — `Type='Additional'`, tanpa `WorkOrderId`/`TaskPersonalizedFindingId`, semua field diisi manual).

**Dua opsi:**

- **Opsi A — Reuse Additional Order existing.** Fully decoupled dari WorkOrder/Task, tidak ada perubahan skema. Trade-off: hilang traceability ke WorkOrder asal ditemukannya defect, mechanic harus re-entry manual data asset/context yang sebenarnya sudah dia pegang saat itu.
- **Opsi B — Mekanisme baru "Add Finding" di dalam form berjalan**, tetap link ke WorkOrder/Task aktif. Trade-off: konsisten dengan prinsip [form-centric](#order-integration-bersifat-form-centric-bukan-per-fitur) yang sudah ditetapkan.

**Resolved (2026-08-13) — blocker data model Opsi B ternyata sudah tidak ada:** `TaskPersonalizedFinding.FormSubmissionTabId`/`FormTaskCode`/`FormTaskNumber` (field yang menunjuk ke Question/Tab spesifik) **ternyata nullable, dan bisa NULL ketiganya sekaligus** — skema **sudah mendukung** Finding yang tidak nempel ke Question manapun. `TaskPersonalized` (parent wajib, FK tidak nullable) tetap harus ada — jadi Finding baru nempel ke `TaskPersonalized` yang **sedang aktif dikerjakan** (WorkOrder/Task konteks berjalan), cuma 3 field penunjuk Question itu dibiarkan NULL. Relasi ke Form tetap bisa di-derive lewat `TaskPersonalized → Task → FormSubmission`, jadi tidak ada informasi yang hilang. **Tidak perlu Task "catch-all" baru, tidak perlu perubahan skema.**

Dengan blocker ini hilang, **Opsi B jadi arah yang jelas lebih unggul** (traceability terjaga, tanpa cost skema) dibanding Opsi A (Additional Order, decoupled).

**Status: Final — Opsi B.** Open item: butuh **UI/entry-point khusus** buat trigger "Add Finding" saat eksekusi form — beda dari trigger existing yang nempel di dropdown per-Question ([Current State UI](#current-state--mobile-app-ui-v400)), karena defect di poin ini justru **tidak** berasal dari Question manapun. Masuk ke daftar "UI View detail" yang sudah dicatat di [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack).

**Entry-point — arahnya button "Additional Defect" di tab Summary (2026-08-15, arah awal, belum final):** dikonfirmasi dari screenshot Work Detail — form punya struktur multi-tab (mis. `Washing`/`Safety`/`ORR Test`/`Summary`), dengan **Summary** sebagai tab terakhir. Arah usulan: tambah button **"Additional Defect"** di tab Summary itu — natural fit karena Summary adalah titik review di akhir pengisian form, cocok jadi tempat "saya nemu defect lain di luar checklist". **Belum final** — butuh tim UI designer buat: (a) penempatan/layout button di tab Summary, dan (b) tampilan list-view detail setelah submit (bagaimana Additional Defect yang sudah diisi ditampilkan balik, mirip [indikator post-submit](#current-state--mobile-app-ui-v400) tapi levelnya di tab Summary, bukan per-row Form Task).

**Konfirmasi tambahan dari screenshot ini — struktur & color-coding konsisten dengan yang sudah didokumentasikan:** dropdown Condition untuk Crack Defect punya 4 opsi — `No Crack Identified` (hijau), `Crack Identified: Monitor` (merah), `Crack Identified: Repair Required` (merah), `Not Applicable` (oranye) — pola color-coding sama dengan yang dikonfirmasi di [Current State UI](#current-state--mobile-app-ui-v400) untuk Defect Check/Data Input.

---

## Fase B — Aktor

### Poin 3: Permission/Role Clarity (2026-08-17)

**Siapa bisa create Finding — bukan soal job title, tapi permission code (2026-08-17):** in-practice yang mengisi form adalah mechanic/foreman, tapi mekanisme akses Digiman+ **bukan hardcoded per role/job-title** — sistemnya berbasis **permission code**, siapapun yang **terassign** ke permission code tertentu dapat melakukan ability yang terkait. Jadi "mechanic/foreman/supervisor" di dokumen ini itu label informal untuk siapa yang *biasanya* di-assign permission tersebut, bukan pengecekan role yang di-hardcode di sistem — konsisten dengan [jawaban lama di Poin 6](#poin-6-duplicate-atau-correlation-handling) ("mengikuti permission yang sudah ada — tidak perlu permission baru").

**Form Approval vs Order Approval — struktur aktor (2026-08-17, sebagian perlu konfirmasi BPO):**
- **Form Approval: Supervisor.**
- **Order Approval: Supervisor → Planner** (kemungkinan 2 tingkat, **belum pasti — perlu konfirmasi ke BPO client**) — beda dari framing lama di dokumen ini yang selalu menyebut Order-approval sebagai gate tunggal "Planner" ([Poin 9](#poin-9-approval-flow) dan berbagai tempat lain). **Belum diubah ke seluruh dokumen** sampai dikonfirmasi — kalau benar 2 tingkat, ini berdampak ke desain approval flow eMOL (termasuk vehicle-approval) yang perlu direvisit.

**Apakah bisa rangkap — ya, murni soal assignment/konfigurasi (2026-08-17):** tidak ada pembatasan sistem — 1 user bisa terassign ke lebih dari 1 permission code sekaligus (mis. sekaligus Supervisor dan Planner), tergantung konfigurasi tenant/client masing-masing. Tidak perlu desain khusus untuk kasus ini — konsekuensi alami dari model permission-code-based di atas.

**Contoh permission code spesifik-fitur (2026-08-17):** untuk edit Finding/Defect-Crack pasca-submit, lihat `IAMS_Mobile_DefectCrack_Edit`/`_Edit_Others` (pola hierarkis parent-child) di [Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15)/[Poin 7](#poin-7-editability-window-sebelum-approval).

---

## Fase C — Data Model

*Jantung diskusi, paling banyak keputusan*

### Poin 4: Offline Behavior — Draft State (2026-08-15)

**Resolved — ada draft state:** user bisa simpan progress pengisian "Defect Identified" (termasuk multi-Tab Finding) **tanpa** trigger submit penuh, lalu submit final terpisah belakangan. Ini beda dari model yang sempat diasumsikan di [User Journey — Defect](#user-journey--defect-2026-08-13) (1 Save button = langsung submit final) — direvisi. **Trigger button-nya (2026-08-17, resolved):** [lihat Struktur Screen step 11](#struktur-screen-defect-identified) — jadi 2 tombol terpisah, "Save as Draft" (tanpa validasi mandatory) dan "Submit" (dengan validasi mandatory).

**Konsekuensi ke arsitektur "1 save = 1 service" ([Poin 5](#poin-5-data-flow-defect-dan-crack)):** draft save **tetap** tulis ke `maintenance-execution` saja (tidak berubah), tapi **publish ke topic cuma terjadi saat submit final**, bukan setiap kali draft disimpan — supaya `maintenance-order` tidak kebanjiran event dari progress yang belum final/masih berubah-ubah.

**Konsekuensi ke skema (confirmed 2026-08-15):** butuh **flag column baru** di `TaskPersonalizedFinding` (mis. `IsDraft`, bit) untuk menandakan mana yang masih draft, mana yang sudah submit — skema existing belum punya field ini (cuma `IsActive`, beda konsep, bukan lifecycle draft/submitted).

**Backfill (2026-08-15):** karena kolom ini baru, row `TaskPersonalizedFinding` **existing** (dari flow Inspection — Add Finding yang sudah production, tidak pernah punya konsep draft) perlu di-backfill — semua row lama **default `IsDraft=0`** (dianggap submitted/final), karena memang sudah final saat dibuat di bawah behavior lama yang tidak kenal draft sama sekali. Kemungkinan cukup lewat `DEFAULT 0` constraint saat `ALTER TABLE` (tidak perlu script backfill terpisah), tapi tetap dicatat sebagai langkah migrasi yang perlu diperhatikan.

**`IsDraft` cuma relevan sebelum submit pertama kali (2026-08-15):** begitu sebuah Finding sudah pernah submitted (`IsDraft=0`), edit berikutnya lewat window editability ([Poin 7](#poin-7-editability-window-sebelum-approval)) **tidak** bisa "save as draft" lagi — cuma 2 hasil yang mungkin: **submit ulang penuh** (berhasil, `IsDraft` tetap `0`) atau **batal/discard** perubahan (kembali ke state submitted terakhir, tidak ada perubahan tersimpan). Tidak ada state kedua "pernah submit tapi lagi setengah-edit" — supaya tidak perlu logic tambahan soal "menarik mundur" Order/eMOL yang mungkin sudah ter-sync ke `maintenance-order`.

**Resolved (2026-08-17) — hubungan dengan offline-first pattern:** 2 sumbu independen, bukan 1 mekanisme yang saling menggantikan. Offline-first pattern existing (`save/offline`, lihat [submission-flow-current-state.md](../../architecture/form/business-operational-form/submission-flow-current-state.md)) itu soal **resiliensi transport** — client generate GUID sendiri, retry-safe/idempotent by `ReferenceId`, jawab pertanyaan "kapan/bagaimana data sampai ke server". `IsDraft` jawab pertanyaan berbeda — "apakah datanya final secara bisnis" (siap dipublish ke `maintenance-order`). Draft-save **reuse mekanisme transport offline-first yang sama** (idempotent, retry-safe), tapi `IsDraft` tetap flag bisnis independen di atasnya — **compose, bukan duplikat**.

**Resolved (2026-08-17) — skenario offline penuh (create → draft berkali-kali → submit, device tidak pernah online sampai submit):** karena publish digate oleh **isi request itu sendiri** (`IsDraft=0` di request yang menang), bukan asumsi konektivitas real-time, hasil akhirnya sama persis baik draft→submit terjadi cepat sambil online, maupun burst-replay dari antrean offline berhari-hari kemudian — publish tetap jalan **tepat sekali**, di request yang bawa `IsDraft=0`, terlepas berapa draft-save mendahuluinya. Konsekuensi yang perlu di-enforce: **client wajib enforce lokal** aturan "tidak ada draft setelah submit pertama" (sudah ditetapkan di atas) — begitu user tap Submit (meski masih offline, belum sempat sync), edit berikutnya di device yang sama langsung masuk jalur edit-window ([Poin 7](#poin-7-editability-window-sebelum-approval)), bukan "draft lagi" — supaya behavior lokal konsisten dengan apa yang akan terjadi begitu request itu benar-benar sampai server.

**Resolved (2026-08-17) — timing correlation check:** sudah terjawab dari desain [User Journey — Defect step 3](#user-journey--defect-2026-08-13) — tombol "Check Existing Defect/Crack" enabled murni dari state client-side (Component/SubComponent/DamageCode terisi), bukan dari hasil save apapun, search-nya live query begitu user tap — **tidak butuh Finding tersimpan/draft dulu**. Jadi pertanyaan "nunggu draft atau submit final" itu moot — mekanismenya sejak awal didesain independen dari draft/submit lifecycle (bisa jalan bahkan sebelum ada draft save pertama).

**Gap baru ditemukan & resolved (2026-08-17) — correlation check butuh data lokal supaya bisa jalan offline:** poin di atas assumsi ada koneksi (live query ke `maintenance-order`). Kalau device offline, tidak ada apa pun untuk di-query kecuali kandidat Order sudah di-cache ke lokal duluan. **Keputusan: cache kandidat lokal.** Kandidat `MOOpen`/`PoolingMOItem` (scoped by Asset/Site yang sedang dikerjakan user) di-sync ke device saat ada koneksi (mis. bareng saat buka WorkOrder/Task), supaya tombol "Check Existing" tetap bisa jalan offline terhadap data yang mungkin agak stale. **Trade-off staleness diterima secara sadar** — kandidat offline bisa saja sudah di-close/di-reuse oleh device lain sebelum device ini sempat re-sync, tapi risikonya dibatasi oleh Planner approval yang tetap jadi gate akhir sebelum keputusan reuse benar-benar berdampak. **Batas mitigasi ini (2026-08-19)** ([batas maknanya di Poin 5](#poin-5-data-flow-defect-dan-crack))**:** kalau user pilih kandidat basi, approver bisa **melihat dan memperbaikinya** — mengganti `ReuseOrderNumber` ke kandidat yang benar, atau membatalkan reuse jadi Order baru ([lihat Poin 9](#poin-9-approval-flow)). ~~approver masih bisa lihat & tolak~~ — **menolak belum bisa**, fitur reject baru ada di [Poin 10](#poin-10-rejectrework-flow). Untuk kandidat basi hal ini cukup, karena remedy-nya memang koreksi (tunjuk Order yang benar), bukan pembatalan. **Belum didesain (residual):** detail mekanisme sync-down (interval, trigger, scope payload persis) — dicatat sebagai open item implementasi, bukan open item desain lagi.

**Resolved (2026-08-17) — count badge:** cuma hitung Finding **submitted** (`IsDraft=0`) — draft **tidak** ikut dihitung. Alasan: badge itu sinyal "berapa Finding yang sudah settled"; kalau draft ikut dihitung, tabrakan makna dengan icon state #2 (warning/incomplete, [lihat model 3-state](#current-state--mobile-app-ui-v400)) yang sudah nunjukin "ada yang belum selesai di row ini" — mis. 1 Finding submitted + 1 draft, kalau badge nunjuk "2" user bisa salah kira row itu sudah clear padahal icon-nya masih warning. **Badge = count final, icon = overall completion signal** (termasuk nunjukin ada draft yang nge-block).

**Resolved (2026-08-17) — siapa yang bisa edit Finding (termasuk offline):** yang bisa edit Finding (baik online maupun offline) adalah **siapapun yang membuat (creator)** Finding itu, digate lewat permission code khusus **`IAMS_Mobile_DefectCrack_Edit`** — tetap butuh permission-nya di-assign, bukan cuma soal identitas creator semata (konsisten model [permission-code-based](#fase-b--aktor)). **Kasus bantu transaksi mandek:** Supervisor/Foreman yang mau bantu selesaikan Finding **milik orang lain** (mis. mechanic tidak available) butuh permission **terpisah** — **`IAMS_Mobile_DefectCrack_Edit_Others`**, **parent**-nya `IAMS_Mobile_DefectCrack_Edit` (pola hierarkis sama seperti permission existing lain, mis. `..._View_All_Site` yang parent-nya `..._View` — [lihat homepage-current-state.md](../../architecture/homepage/homepage-current-state.md); pola scope `_All_Site` sendiri tidak relevan/diabaikan di sini). Mekanisme edit-nya (offline-safe, idempotent) **sama** untuk kedua permission ini — bedanya cuma gate akses siapa yang boleh buka layarnya, bukan mekanisme tulis data.

**Resolved (2026-08-17) — race condition, 2 device edit Finding yang sama secara concurrent (mis. mechanic & Supervisor edit bersamaan di device masing-masing, sama-sama offline):** "last edit menang" tetap prinsip dasarnya — **bukan mekanisme baru**, konsisten pola full-overwrite yang sudah dipakai di seluruh app ini. Detail mekanismenya (termasuk kasus urutan **kedatangan** ke server terbalik dari urutan **edit** sebenarnya) didesain bareng logic upsert di [Poin 5](#poin-5-data-flow-defect-dan-crack), bagian "Kapan publish terjadi & consumer upsert".

---

### Poin 5: Data Flow Defect dan Crack

**Arah baru (2026-08-14) — Order Type & Activity Type pindah titik-tulis ke `maintenance-execution`:**

**Koreksi (2026-08-16) — klaim "Activity Type existing" di paragraf ini sebelumnya salah, sumbernya proposal bukan skema real:** kalimat asli menyamakan Order Type dan Activity Type sebagai "mekanisme existing" yang sama-sama direct-write ke `MechanicOrderList`. **Cuma Order Type (`CostTypeCode`) yang benar** — dikonfirmasi ada & existing di skema real ([maintenance-order-schema.md](../../architecture/database/maintenance-order-schema.md)). **`MechanicOrderList.ActivityType` TIDAK ADA sama sekali di skema real** — itu murni field yang diusulkan [maintenance-activity-type-enhancement.md](../../architecture/inspection-order/maintenance-activity-type-enhancement.md) 2.2–2.3/2.5 (proposal, belum rilis), bukan mekanisme yang berjalan hari ini. Konsisten dengan resolusi skema `TaskPersonalizedFinding` di bawah (poin ini juga, lihat tabel kolom baru) yang sudah benar sejak awal ("`ActivityTypeCode` — Baru — belum ada sama sekali di skema real saat ini") — paragraf ini yang tadinya tidak sinkron dengan itu.

Berbeda dari mekanisme existing hari ini (Order Type diisi user langsung di screen "Order Details"/"Complete Order", **direct write** ke `MechanicOrderList.CostTypeCode` — Activity Type per-eMOL **belum ada mekanismenya sama sekali** hari ini, lihat koreksi di atas) — untuk Phase 2 ini, arahnya:

1. Order Type & Activity Type **disimpan dulu di `maintenance-execution`** — kolom baru di `TaskPersonalizedFinding`, diisi lewat step/screen tersendiri di mobile (bukan digabung ke form "Defect Identified", tetap langkah terpisah).
2. **Baru setelah itu di-publish ke topic** (service bus).
3. `maintenance-order` **murni consumer** — create/update `MechanicOrderList` dari event, **tidak ada lagi direct write dari UI** ke `MechanicOrderList` untuk 2 field ini.

**Prinsip/alasan (2026-08-14):** menghindari 1 aksi save di UI harus **memanggil 2 service berbeda secara sinkron** (`maintenance-execution` + `maintenance-order` sekaligus/saling tunggu) — pola ini rawan **race condition** (partial failure, ordering tidak terjamin antar call). Solusinya: 1 save = 1 tulis ke **1 service saja** (`maintenance-execution`), baru event/topic yang mengalirkan ke `maintenance-order` secara async & decoupled — bukan dipanggil langsung dari UI/BE saat itu juga.

**Konsekuensi ke Material — resolved (2026-08-14):** prinsip di atas berarti **Material ikut pindah pola yang sama** — screen yang di-reuse (Order Type→Activity Type→Part, [User Journey — Defect](#user-journey--defect-2026-08-13)) submit-nya jadi **1 aksi save ke `maintenance-execution` saja** (bukan lagi direct call ke `material-save-api` yang menulis langsung ke `MechanicOrderMaterial` di `maintenance-order`) — supaya konsisten dengan alasan hindari dual-service-call di atas. Detail field/skema Material di sisi `maintenance-execution` belum didesain — dicatat sebagai open item.

**`MechanicOrderList.Type` — value baru `'Form'` (2026-08-14):** saat ini cuma 2 nilai (`'Inspection'`/`'Additional'`). Defect/crack dari Form Phase 2 ini **secara struktur mirip Inspection** (`WorkOrderId`+`TaskPersonalizedFindingId` tetap terisi, beda dari Additional yang keduanya NULL) — tapi trigger-nya bisa dari fitur manapun (Inspection/PM Shutdown/BD Corrective, prinsip [form-centric](#order-integration-bersifat-form-centric-bukan-per-fitur)), jadi label `'Inspection'` menyesatkan kalau dipakai apa adanya. Keputusan: **value baru `'Form'`**, konsisten dengan istilah "form-centric" yang sudah jadi prinsip dasar dokumen ini.

**Trade-off yang perlu diaudit (belum dikerjakan, dicatat sebagai open item):** beberapa titik di codebase yang branch berdasarkan `Type='Inspection'`/`Type='Additional'` perlu direview supaya `'Form'` di-treat benar (kemungkinan besar disamakan dengan `'Inspection'` karena struktur FK sama, tapi perlu dicek satu-satu):
- Material temp table matching ([order-emol-sap-sync.md 5.1](../../architecture/inspection-order/order-emol-sap-sync.md#51-a-lookup-poolingid-existing)) — filter `WorkOrderId+Type='Inspection' ATAU MechanicOrderSummaryId+Type='Additional'`.
- `PoolingMOItem` dmol join ([5.2](../../architecture/inspection-order/order-emol-sap-sync.md#52-bc-update-jika-ada-create-jika-tidak-ada--insert-ke-poolingmoitem)) — `ON (TaskPersonalizedFindingId=dmol.MolId AND Type='Inspection') OR (Id=dmol.MolId AND Type='Additional')`.
- `MechanicOrderList.Type` sendiri di-set saat create eMOL (kolom dikonfirmasi ada di skema real, [maintenance-order-schema.md](../../architecture/database/maintenance-order-schema.md)) — perlu logic baru untuk set `'Form'`.

**Consumer di `maintenance-order` — bukan cuma insert `MechanicOrderList` (2026-08-14):** saat consume event dari topic, consumer perlu **create `MechanicOrderSummary` (header) dulu**, baru `MechanicOrderList` (line) yang di-link ke situ. **Grouping: 1:1** — tiap defect/crack yang disubmit selalu bikin `MechanicOrderSummary` **baru sendiri**, dedicated per eMOL — **tidak** digrupkan per WorkOrder/Task seperti pola Inspection existing. **Ini berlaku untuk SEMUA Finding yang publish ke topic — termasuk reuse (2026-08-15, final setelah beberapa kali revisi, lihat riwayat di bawah)**, bukan cuma create-Order-baru.

**⚠️ Riwayat revisi (2026-08-15) — supaya jelas kenapa berubah 2x:** sempat disimpulkan "reuse TIDAK PERNAH membentuk eMOL baru" (cuma trigger `BacklogExecutionList` lokal) — alasannya waktu itu benar secara prinsip layanan (`maintenance-order` cuma urusan Order, eksekusi domain `maintenance-execution`), **tapi** ini menghilangkan safety net: tanpa eMOL baru, tidak ada gate Planner yang bisa cek keputusan reuse mechanic di lapangan sebelum benar-benar dieksekusi/di-TECO. Setelah didiskusikan ulang, **keputusan final: reuse TETAP membentuk eMOL baru** — supaya tetap lewat Planner approval sebagai preventive check — tapi dengan **behavior post-approval yang beda** dari eMOL normal (detail di bawah), supaya tidak menimbulkan masalah baru (duplicate candidate di correlation suggestion, dijelaskan di bawah).

**Resolved (2026-08-19) — batas makna "safety net"/gate Planner: korektif, bukan preventif-total.** Approval ini bisa **memperbaiki** tautan reuse yang salah sebelum Approve — approver boleh mengganti `ReuseOrderNumber` dan field lain, lalu Save ([lihat Poin 9](#poin-9-approval-flow)). Yang **tidak** bisa dilakukan: **menolak** eMOL yang seharusnya tidak ada sama sekali, karena fitur reject baru ada di [Poin 10](#poin-10-rejectrework-flow). Semua klaim di dokumen ini yang menggantungkan mitigasi ke "Planner sebagai gate" harus dibaca dalam batas ini: yang tertangkap adalah kesalahan yang bisa **dikoreksi**, bukan keputusan reuse yang sepenuhnya keliru.

**Mekanisme final — eMOL "vehicle approval" untuk reuse (2026-08-15):**
1. Consumer **create eMOL baru** (`MechanicOrderSummary`+`MechanicOrderList`+`Detail`+`Material`+`Evidence`) untuk Finding yang reuse Order lama juga — sama seperti Finding yang create Order baru. `MechanicOrderList` ini bawa **field baru `ReuseOrderNumber`** (propagate dari `TaskPersonalizedFinding.ReuseOrderNumber`) sebagai penanda "ini eMOL reuse, bukan Order baru genuine" — marker cukup di `MechanicOrderList`, tidak perlu diduplikasi ke `MechanicOrderSummary` (grouping tetap 1:1, cukup cek dari List-nya).
   - **`MechanicOrderDetail`/`MechanicOrderMaterial` tetap di-isi penuh** (Component/SubComponent/DamageCode/CauseCode/ActionRemedy/Priority/Order Type/Activity Type/Material dkk) — **snapshot-copy dari Order lama** yang di-reuse, bukan dibiarkan kosong. Konsisten dengan prinsip snapshot-at-creation yang sudah dipakai konsisten di seluruh sistem ini (`MechanicOrderDetail` selalu snapshot, bukan live-lookup) — supaya screen approval Planner bisa render eMOL ini **apa adanya dari tabelnya sendiri**, tidak perlu cross-reference ke Order lama/tabel lain/service lain cuma buat tampilkan data. "Read-only" yang dibahas sebelumnya itu soal **UI mobile** (user tidak bisa edit nilainya), bukan berarti data-nya tidak ditulis ke backend.
   - **`MechanicOrderSummary.Status` DAN `MechanicOrderList.Status` → langsung `Complete` (2026-08-15)** — karena eMOL ini dibuat sudah lengkap (full snapshot, bukan hasil pengisian bertahap oleh Planner/mechanic di UI), tidak perlu status "in-progress"/`Open` di keduanya — begitu terbentuk, langsung "pembuatan Order-nya selesai" dan trigger masuk antrian approval Planner. Berlaku sama untuk eMOL create-baru (bukan cuma reuse-vehicle) — begitu consumer selesai create Detail/Material/Evidence-nya, kedua Status langsung `Complete`, bukan `Open`.
2. eMOL ini **lewat Planner approval seperti biasa** (jalur Order-approval existing, tidak ada bypass) — Planner jadi checkpoint atas keputusan reuse mechanic, review data yang sama seperti Order lain (karena sudah full snapshot) — **korektif, bukan preventif-total** ([batas maknanya di Poin 5](#poin-5-data-flow-defect-dan-crack)): approver bisa memperbaiki tautan reuse sebelum Approve, tapi belum bisa menolak eMOL-nya.
3. **Post-approval, behaviornya beda** tergantung `ReuseOrderNumber` terisi atau tidak — dan **kalau terisi, dipecah lagi tergantung `IsImmediateExecutable` (2026-08-16, revisi — sebelumnya cabang `No` malah skip approval sama sekali, sekarang dibalik: SEMUA reuse lewat approval, cuma post-approval-nya yang beda)**:
   - **`ReuseOrderNumber` NULL (genuine Order baru)** → lanjut ke [Alur Sync ke SAP Post-Approval](../../architecture/inspection-order/order-emol-sap-sync.md#5-alur-sync-ke-sap-post-approval) seperti biasa — create `PoolingMOItem`/`SAPMOSyncOrder`, push jadi MO baru ke SAP.
   - **`ReuseOrderNumber` terisi (reuse) + `IsImmediateExecutable=Yes`** → **SKIP** total alur sync SAP normal — eMOL ini **tidak pernah** masuk `PoolingMOItem`/`SAPMOSyncOrder` sama sekali. Sebagai gantinya, approval men-trigger **`BacklogExecutionList`** (`maintenance-execution`, [Bagian 9.2](../../architecture/inspection-order/order-emol-sap-sync.md#92-cara-mo-backlog-dieksekusi)) mengarah ke Order **LAMA** (`WorkOrderId`+`MONumber` dari `ReuseOrderNumber`) — TECO ke SAP jalan dari situ, lewat pipeline existing yang sama.
   - **`ReuseOrderNumber` terisi (reuse) + `IsImmediateExecutable=No` (2026-08-16, baru)** — **SKIP** total alur sync SAP normal juga (sama seperti `Yes`, reuse tidak pernah sync SAP sebagai MO baru — mencegah duplicate candidate, [lihat Poin 6](#poin-6-duplicate-atau-correlation-handling)) — **tapi tidak trigger `BacklogExecutionList`** (belum ada eksekusi yang perlu di-TECO). eMOL ini **cuma jadi record approved** — bukti Planner sudah validasi & setuju defect ini memang sama dengan Order lama dan belum perlu dieksekusi sekarang. Order lama tetap open, tidak ada aksi lanjutan apapun sampai defect ini benar-benar dieksekusi (via Finding lain nanti, atau lewat jalur backlog normal).

**Kenapa harus skip `PoolingMOItem` untuk reuse — mencegah duplicate candidate di suggestion (2026-08-15):** kalau eMOL reuse ini ikut masuk `PoolingMOItem` lewat jalur normal, dia bakal punya Component/SubComponent/DamageCode **identik** dengan Order lama yang di-reuse — otomatis nongol lagi sebagai kandidat terpisah di [List Suggestion](#ui-view-detail--list-suggestion-order-lama-2026-08-14) untuk defect berikutnya, persis masalah duplicate yang [Poin 6](#poin-6-duplicate-atau-correlation-handling) coba hindari. Karena tidak pernah masuk `PoolingMOItem`, gap ini tertutup dengan sendirinya.

**`ReuseSAPOrderNumber` (sebelumnya "SAP MO Number manual") — dipakai di titik `BacklogExecutionList`, bukan langsung dari Finding:** kalau `MONo` Order lama NULL + butuh material (mandatory field, sudah dibahas di atas), nilai manual ini disimpan di `TaskPersonalizedFinding` → propagate ke eMOL reuse → dipakai sebagai `MONumber` saat create `BacklogExecutionList` post-approval (karena kolom itu **not null**). Sourcing lengkap `MONumber` ini (kapan pakai `ReuseSAPOrderNumber` langsung vs lookup lewat `ReuseOrderNumber`) — [lihat Poin 6](#poin-6-duplicate-atau-correlation-handling).

**Skema final kolom baru `MechanicOrderList` untuk Order Type/Activity Type (2026-08-15, resolved):** berlaku untuk **semua** eMOL Phase 2 (create baru maupun reuse-vehicle), bukan cuma reuse.

| Kolom | Tipe | Keterangan |
|---|---|---|
| `CostTypeCode` | varchar(64), null | **Sudah ada** (existing) — Order Type Code, tidak berubah. |
| `OrderTypeName` | varchar(128), null | **Baru** — companion Name untuk `CostTypeCode` yang sebelumnya cuma punya Code. Beda naming dari `MaterialCostTypeName` yang diusulkan di [enhancement 2.4](../../architecture/inspection-order/maintenance-activity-type-enhancement.md#24-skema-data--reuse-maintenancecategory--mapping-mn-baru) (dokumen itu masih rencana, belum live) — kalau enhancement itu suatu saat jadi diimplementasi, perlu rekonsiliasi nama kolom. |
| `ActivityTypeCode` | varchar(64), null | **Baru** — belum ada sama sekali di skema real saat ini. |
| `ActivityTypeName` | varchar(128), null | **Baru** — companion Name. |

**Scope note (2026-08-15):** `MechanicOrderSummary.Source` (3 nilai — Scheduled Inspection/Additional Inspection/Additional Order) **belum ada di skema real** — itu masih bagian rencana [maintenance-activity-type-enhancement.md](../../architecture/inspection-order/maintenance-activity-type-enhancement.md) yang belum diimplementasi. Desain di sini **menganggap field itu belum ada** — tidak perlu memutuskan nilai `Source` baru untuk eMOL Phase 2 ini sekarang. Kalau field itu suatu saat jadi live, revisit lagi apakah butuh nilai baru (mis. `'Form'`, konsisten dengan `MechanicOrderList.Type='Form'`).

**`Number` (`MechanicOrderSummary` & `MechanicOrderList`) — pakai generator/format existing, tidak ada prefix khusus untuk eMOL reuse (2026-08-15, confirmed via screenshot data production):** dikonfirmasi format real dari data — `MechanicOrderSummary.Number` prefix **`AOL-`**, `MechanicOrderList.Number` prefix **`IFD-`** (keduanya + YYMM + sequential). eMOL vehicle-approval (reuse) **pakai generator yang sama persis**, tidak ada prefix/format beda — pembeda cukup dari field `ReuseOrderNumber` (NULL = Order baru genuine, terisi = vehicle reuse), tidak perlu logic baru di generator Number.

**Konfirmasi tambahan dari data production (2026-08-15):**
- **`MechanicOrderSummaryId` NULL untuk semua row `Type='Inspection'`** — bukti konkret (bukan cuma pernyataan PM) yang mengonfirmasi ulang [koreksi sebelumnya](#ui-view-detail--view-detail-order-2026-08-14) soal klaim `maintenance-activity-type-enhancement.md` ("field ini selalu ada") — itu memang cuma rencana, belum live.
- **`DeleteReason` ada nilai `"double order"`** (berulang) dan `"sudah naik"` — validasi nyata bahwa masalah duplicate Order **sudah terjadi di lapangan hari ini**, dibersihkan manual — memperkuat urgensi mekanisme correlation [Poin 6](#poin-6-duplicate-atau-correlation-handling). `"sudah naik"` juga konsisten dengan pola [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack) (eskalasi dari level rendah ke critical).
- **`Status` values confirmed**: `Complete`/`Open` di `MechanicOrderList`, `Complete` di `MechanicOrderSummary` — `CompletedBy`/`CompletedDate` cuma terisi saat `Status='Complete'`, NULL saat `Open` — konsisten dengan pemahaman yang sudah dikoreksi (Complete = form Order selesai disubmit, bukan eksekusi fisik selesai).

**Kapan publish terjadi & consumer upsert (2026-08-15):** publish ke topic terjadi **tiap kali user tap Submit** — baik submit pertama kali maupun re-submit hasil edit ([Poin 7](#poin-7-editability-window-sebelum-approval), setelah `IsDraft=0`; draft save **tidak** publish, lihat [Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15)). Berlaku untuk **semua** Finding (create baru maupun reuse) — consumer perlu logic **upsert by `TaskPersonalizedFindingId`**:
- **Belum ada `MechanicOrderList` untuk `TaskPersonalizedFindingId` ini** → create `MechanicOrderSummary`+`MechanicOrderList`+`Detail`+`Material`+`Evidence` (behavior di atas, termasuk set `ReuseOrderNumber` kalau relevan).
- **Sudah ada** (event kedua dst, hasil edit) → **UPDATE** `MechanicOrderDetail`/`MechanicOrderMaterial`/`MechanicOrderEvidence` yang sudah ada, **tidak** create `Summary`/`List` baru, **tidak** re-trigger approval/post-approval action kalau sudah pernah jalan (idempotent).

**Untuk cabang `No`+reuse — REVERSED (2026-08-16):** sekarang **JUGA create eMOL** "vehicle approval" (publish full Order-event), sama persis dengan cabang `Yes` — bedanya cuma di post-approval action (`Yes` trigger `BacklogExecutionList`, `No` tidak ada aksi lanjutan, [lihat Poin 9](#poin-9-approval-flow)). ~~Update `MONo` Order lama (kalau SAP MO Number opsional diisi) sekarang ikut dalam payload publish penuh ini, bukan publish targeted terpisah lagi.~~ **Direvisi (2026-08-19):** input manual itu sudah tidak ada untuk kandidat ber-`PoolingMOItem` ([Poin 6](#poin-6-duplicate-atau-correlation-handling)), jadi tidak ada nilai `MONo` yang perlu dibawa balik dari cabang ini. Yang tetap berlaku: cabang `No` memakai **satu jenis publish penuh yang sama** dengan cabang `Yes`, tidak ada jalur publish targeted terpisah.

**Resolved (2026-08-17) — edit lock begitu approval tier pertama diproses, plus topic arah balik:** upsert di atas cuma aman selama Order-nya belum ada keputusan approval apapun yang diambil atas datanya. **Keputusan:** window edit ([Poin 7](#poin-7-editability-window-sebelum-approval)) **lock begitu tier PERTAMA di Order-approval chain sudah memproses** (bukan menunggu tier terakhir/status `Approved` penuh) — supaya tidak ada keputusan approval (sekalipun baru sebagian, dari tier awal) yang jadi berbasis data yang lalu berubah di bawahnya. Berlaku tier-agnostic, sama seperti desain approval lain di dokumen ini (1 atau 2 tier tidak mengubah mekanisme, [lihat Poin 9](#poin-9-approval-flow)) — yang jadi trigger adalah **aksi approval pertama tercatat**, bukan jumlah tier atau status akhir tertentu.

**Konsekuensi arsitektur — topic arah balik baru (`maintenance-order` → `maintenance-execution`):** `maintenance-execution` butuh tahu status ini untuk enforce lock di client/BE **tanpa** live cross-service lookup (melanggar prinsip snapshot yang sudah dipegang konsisten di seluruh dokumen ini). Dibutuhkan **topic baru arah sebaliknya** dari topic existing (mirror pola outbox/consumer yang sudah dipakai forward, `TopicPublishLog`/`TopicConsumeLog`) — `maintenance-order` publish event begitu **WorkflowTransaction pertama tercatat** di Order-approval chain eMOL manapun, `maintenance-execution` consume jadi flag lokal baru (mis. `TaskPersonalizedFinding.IsOrderApprovalLocked` atau serupa, nama final menyusul) — dipakai gate tombol edit di mobile. Detail skema kolom/nama topic belum final, dicatat sebagai kerja desain lanjutan, tapi arah mekanismenya sudah diputuskan.

**Diperluas (2026-08-17) — topic ini yang sama dipakai buat sinkron hasil edit approver, bukan cuma flag lock:** [Poin 9](#poin-9-approval-flow) memutuskan approver **juga bisa edit data mechanic** di titik approval — hasil edit itu perlu sinkron balik ke `maintenance-execution` juga. **Keputusan: 1 topic yang sama** (bukan topic terpisah), payload-nya diperluas bawa data hasil edit approver (kalau ada) sekalian dengan trigger lock-nya — konsisten prinsip "1 mekanisme, bukan cabang khusus". **Nama topic dibuat general** (bukan spesifik "lock", karena sekarang juga bawa data) — mis. `OrderApprovalSync` atau serupa, nama final menyusul saat implementasi. Trigger publish-nya **setiap aksi Approve** (bukan Save approver, [lihat detail Poin 9](#poin-9-approval-flow)) — beda dari flag lock yang trigger di **tier pertama** approval; kalau ada >1 tier, topic ini bisa publish >1 kali (tiap tier approve), flag lock cuma 1 kali (tier pertama).

**Resolved (2026-08-17) — race condition, 2 device edit Finding yang sama secara concurrent:** "last edit menang" tetap prinsip dasarnya (konsisten pola full-overwrite existing, tidak ada versioning/merge di app ini sejauh yang sudah ditemukan) — tapi **"last" berdasarkan waktu edit sebenarnya** (`ModifiedAt` dari device saat aksi edit terjadi), **bukan urutan kedatangan/sync ke server** — 2 hal ini bisa terbalik kalau device dengan edit lebih lama sempat online duluan (submit dulu) sementara device dengan edit lebih baru masih offline lalu baru sync belakangan.

Mekanisme: server bandingkan `ModifiedAt` **payload masuk** vs `ModifiedAt` **yang sudah tersimpan**. Kalau payload masuk **lebih stale** (edit-nya sebenarnya terjadi lebih dulu dari yang sudah tersimpan) → **tidak di-apply** (data server tidak ditimpa balik ke versi lama) — **tapi response tetap sukses** (bukan reject/409), supaya mobile app **tidak requeue** untuk retry (ini bukan transient failure, memang expected outcome yang tidak akan pernah beda hasilnya kalau diulang). Response bawa flag/message yang ditampilkan ke user, contoh copy:
- *"This defect/crack was already updated by someone else. Your changes weren't applied — please review the latest version before editing again."*
- Versi ringkas (toast): *"A newer update exists for this defect. Refresh to see it."*

Konsekuensi UX: app perlu **re-fetch versi terbaru dari server** begitu dapat sinyal ini, supaya user tidak terus kerja di atas data stale miliknya sendiri. Perubahan yang "kalah" **didiscard** (tidak ada merge/3-way-diff — konsisten prinsip simple-mechanism yang dipegang di seluruh dokumen ini); kalau user masih mau perubahan yang sama, tinggal re-edit dari versi terbaru. **Guard ini berlaku uniform** ke semua jalur tulis `TaskPersonalizedFinding` (draft-save, submit, resubmit) — 1 mekanisme konsisten, tidak ada cabang khusus per jalur.

**Open item:**
**Skema final kolom `TaskPersonalizedFinding` untuk Order Type/Activity Type (2026-08-15, resolved):**

| Kolom | Tipe | Keterangan |
|---|---|---|
| `OrderTypeCode` | varchar(64), null | Ref ke `MaterialCostType.Code` — sama master data dengan `MechanicOrderList.CostTypeCode` |
| `OrderTypeName` | varchar(128), null | Snapshot nama, resolve sekali saat dipilih/di-derive — bukan live-lookup |
| `ActivityTypeCode` | varchar(64), null | Ref ke `MaintenanceCategory.Code` — **catatan buat developer:** ambil dari master data `MaintenanceCategory` yang **relevan/current saat ini**, difilter lewat join `OrderTypeMaintenanceCategoryMapping.OrderTypeCode = <OrderTypeCode yang sudah dipilih>` → ambil `MaintenanceCategoryCode`-nya (skema dikonfirmasi live di [maintenance-order-schema.md](../../architecture/database/maintenance-order-schema.md), screenshot SSMS user 2026-08-16 — `Id`/`OrderTypeCode`/`MaintenanceCategoryCode`/`IsActive`/audit columns) — bukan snapshot/cache lama, resolve fresh di titik user pilih. **⚠️ Ini beda dari `ActivityTypeName` di bawah/`MechanicOrderList.ActivityType`** — mapping table-nya live, tapi kolom Name di `MaintenanceCategory` dan kolom `ActivityType`/`ActivityTypeName` di `MechanicOrderList` **masih belum live** ([dikonfirmasi 2026-08-16](#poin-5-data-flow-defect-dan-crack)) — jangan generalisasi "enhancement ini sudah live" ke seluruh scope-nya, cuma mapping table-nya yang confirmed. |
| `ActivityTypeName` | varchar(128), null | Snapshot nama, sama pola — resolve bareng `ActivityTypeCode` dari master data current di atas, bukan sumber terpisah. |
| `ComponentName` | varchar(128), null | **Baru (2026-08-16, direvisi dari resolusi awal Poin 6)** — companion Name untuk `ComponentCode` yang sudah ada. Resolve fresh & snapshot di titik user pilih, sama pola `ActivityTypeCode`/`Name`. |
| `SubComponentName` | varchar(128), null | **Baru**, sama pola — companion Name untuk `SubComponentCode`. |
| `DamageName` | varchar(128), null | **Baru**, sama pola — companion Name untuk `DamageCode`. |
| `CauseName` | varchar(128), null | **Baru**, sama pola — companion Name untuk `CauseCode`. |
| `ActionRemedyName` | varchar(128), null | **Baru**, sama pola — companion Name untuk `ActionRemedyCode`. |
| `PriorityName` | varchar(128), null | **Baru** — companion Name untuk `PriorityCode` yang sudah ada ([Struktur Screen "Defect Identified"](#struktur-screen-defect-identified) step 7). Master data Priority ada di **service Asset** (beda service dari `maintenance-execution`/`maintenance-order`) — tapi titik resolve-nya **sama** dengan 5 field di atas (fresh & snapshot saat user pilih dropdown), cross-service di sini cuma detail implementasi resolve upstream-nya, tidak mengubah mekanisme propagasi ke bawah. |
| `NoPartsRequired` | bit, **null** | **Baru (2026-08-16) — gap yang ke-catch user, sebelumnya kelewat.** Companion untuk `MechanicOrderList.NoPartsRequired` yang sudah ada ([order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) §4.3) — tanpa ini, `maintenance-execution` tidak punya cara menyatakan "declare tidak butuh material" buat Order baru (B1/B2), padahal field ini **load-bearing** untuk timing TECO ([tabel Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)) dan `PoolingMOItem` LEFT JOIN ([order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) §5.2). **UI: checkbox eksplisit "No parts required"**, terpisah dari list material (opsional untuk disentuh, tapi ada) — **default `0` di level aplikasi** kalau tidak disentuh sama sekali saat submit Finding baru (aman, konsisten dengan default existing `MechanicOrderList.NoPartsRequired`; mencegah "belum sempat isi material" salah diartikan "declare tidak butuh material"). Propagate ke `MechanicOrderList.NoPartsRequired` lewat publish/consume yang sudah ada, sama pola dengan field lain. **Nullable di DB, TIDAK di-backfill (2026-08-16, user)** — beda dari 6 kolom Name di atas (yang punya nilai historis yang bisa di-derive dari Code existing), konsep ini genuinely baru di `maintenance-execution`, tidak ada data lama yang bisa dijadikan dasar. Row historis (sebelum Phase 2) tetap `NULL` selamanya — bukan "tidak diketahui, dianggap 0", tapi "konsep ini belum ada saat itu". Default `0` di atas cuma berlaku untuk Finding **baru** yang lewat flow Phase 2 ke depan. |

**Semua 6 kolom Name di atas — resolve sekali di `maintenance-execution`, propagate uniform ke `MechanicOrderDetail` (2026-08-16, koreksi dari resolusi awal Poin 6):** sebelumnya 5 kolom Name (Component/SubComponent/Damage/Cause/ActionRemedy) di [Poin 6](#poin-6-duplicate-atau-correlation-handling) sempat digambarkan "resolve dari master data dalam domain `maintenance-order` sendiri" tanpa titik resolve yang jelas untuk record baru ke depan (cuma backfill data lama yang terspesifikasi) — **dikoreksi**: `TaskPersonalizedFinding` **sudah punya** `ComponentCode`/`SubComponentCode`/`DamageCode`/`CauseCode`/`ActionRemedyCode`/`PriorityCode` hari ini (Code-only) — dikonfirmasi dari **skema real** [maintenance-execution-schema.md](../../architecture/database/maintenance-execution-schema.md) (bukan dari dokumen `maintenance-activity-type-enhancement.md`, yang masih proposal/belum rilis — [current-state principle](#ui-view-detail--view-detail-order-2026-08-14) yang sama berlaku di sini juga), yang juga confirmed sama struktur dengan `MechanicOrderDetail` (`maintenance-order.MechanicOrderDetail` **snapshot-copy dari sini**, dikonfirmasi di dokumen yang sama). Jadi **keenam** kolom Name di atas resolve-nya **sama pola persis**, sekali di titik Finding dibuat, lalu **propagate lewat publish/consume yang sudah ada** ke `MechanicOrderDetail` (bukan di-resolve ulang di `maintenance-order`). Tidak ada mekanisme spesial buat field manapun — cross-service (Priority ke Asset) cuma detail implementasi resolve upstream, tidak mempengaruhi cara propagasi ke `MechanicOrderDetail`.

**Beda dari `OrderTypeCode`/`OrderTypeName`/`ActivityTypeCode`/`ActivityTypeName` di atas (2026-08-16, menjawab pertanyaan "disimpan di mana sebelum propagate"):** kedua field ini **disimpan di tabel yang sama** (`TaskPersonalizedFinding`), tapi beda karakter dari 6 field Name di atas — `TaskPersonalizedFinding` **skema real hari ini** ([maintenance-execution-schema.md](../../architecture/database/maintenance-execution-schema.md)) **sama sekali tidak punya** kolom Order Type/Activity Type dalam bentuk apapun (beda dari Component/SubComponent/Damage/Cause/ActionRemedy/Priority yang Code-nya sudah ada, cuma Name yang baru). Jadi `OrderTypeCode`/`OrderTypeName`/`ActivityTypeCode`/`ActivityTypeName` itu **genuinely kolom baru total** (Code **dan** Name sekaligus) — bukan cuma nambah companion Name ke Code yang sudah ada. Ini konsisten dengan [Arah baru (2026-08-14)](#poin-5-data-flow-defect-dan-crack) — titik-tulis Order Type/Activity Type memang baru dipindah ke `maintenance-execution` untuk Phase 2 ini, sebelumnya konsep ini cuma ada di `maintenance-order` (`MechanicOrderList.CostTypeCode`, langsung diisi user di screen "Order Details" existing). Mekanisme propagasi ke `MechanicOrderDetail`-nya tetap sama (resolve sekali, publish/consume) — cuma titik keberangkatannya beda: 6 field lain "nambah Name ke kolom Code existing", 2 field ini "kolom baru semua dari nol".

**Backfill keenam kolom Name ini** — lihat [Backfill data lama di Poin 6](#poin-6-duplicate-atau-correlation-handling), sudah mencakup `PriorityName` bareng 5 field lain (satu mekanisme uniform, bukan dibahas terpisah lagi di sini).

Naming sengaja tidak ikut pola legacy `CostTypeCode`/`MaterialCostTypeName` di `MechanicOrderList` (beban historis SAP) — karena ini kolom baru tanpa beban itu, dipakai nama yang self-describing sesuai label UI (Order Type/Activity Type). **Nullable di level DB** — cabang `No`+reuse tidak pernah menulis field ini sama sekali (per keputusan sebelumnya), jadi tidak bisa `not null`; validasi "wajib diisi sebelum submit" ada di level aplikasi/UI, bukan constraint DB.
- **List Material per defect — belum ada strukturnya sama sekali di `maintenance-execution` (2026-08-14, confirmed user).** Beda dari `OrderType`/`ActivityType` (cukup 1-2 kolom baru di `TaskPersonalizedFinding` yang existing), Material itu **1-to-many** per defect (bisa banyak part) — butuh **tabel baru** di `maintenance-execution` (setara `MechanicOrderMaterial` di sisi Order), bukan sekadar tambah kolom.
  - **Nama tabel & FK (2026-08-14): `TaskPersonalizedFindingMaterial`**, FK wajib `TaskPersonalizedFindingId` (bukan `TaskPersonalizedId`) — beda pola dari `TaskPersonalizedEvidence` (FK `TaskPersonalizedId` wajib + `TaskPersonalizedFindingId` nullable, karena Evidence bisa nempel langsung ke `TaskPersonalized` tanpa Finding spesifik). Material **selalu** terikat ke defect/Finding tertentu, tidak ada skenario "material tanpa defect" — jadi FK wajib ke Finding saja, mirror relasi `MechanicOrderMaterial.MechanicOrderListId` di sisi Order.
  - Field-nya kemungkinan mirror `MechanicOrderMaterial` (`MaterialNumber`/`Quantity`/`Batch`/`UoM`/dll, lihat [maintenance-order-schema.md](../../architecture/database/maintenance-order-schema.md)) tapi belum didesain skema persisnya, dan API `material-list-api.md`/`material-save-api.md` yang selama ini query langsung ke `maintenance-order` juga perlu direvisit sumbernya.
  - **`NoPartsRequired` — resolved (2026-08-16), TIDAK di tabel Material ini.** Field declare "tidak butuh material" itu levelnya **per-Finding** (mirror `MechanicOrderList.NoPartsRequired` yang levelnya per-eMOL, bukan per-baris `MechanicOrderMaterial`) — jadi ditaruh di `TaskPersonalizedFinding.NoPartsRequired`, bukan di `TaskPersonalizedFindingMaterial`. Detail lengkap & alasan load-bearing-nya ada di [skema kolom baru `TaskPersonalizedFinding`](#poin-5-data-flow-defect-dan-crack) di atas — sempat kelewat sampai di-catch user.
- ~~Timing pembuatan `MechanicOrderList`~~ — **resolved (2026-08-14)**: **near real-time**, bukan instant. Setelah `maintenance-execution` publish ke topic, consumer di `maintenance-order` jalan **polling, delay maksimal ~5 detik** (bukan push-triggered langsung) untuk create `MechanicOrderList` dari event. Konsekuensi: ada delay kecil (maks ~5 detik) antara user submit Order Type/Activity Type/Material di mobile sampai `MechanicOrderList` benar-benar terbentuk — relevan buat UX (mis. loading state) & buat asumsi timing di [List Suggestion Order Lama](#ui-view-detail--list-suggestion-order-lama-2026-08-14)/correlation kalau ada 2 defect nyaris bersamaan.
- ~~Scope: pola baru ini beneran baru, atau ada precedent?~~ — **resolved (2026-08-14)**: pola "simpan dulu di 1 service → publish topic → consumer polling" **bukan hal baru** di Digiman+ — sudah diimplementasi untuk **External Integration (ERP/SAP)**, yaitu outbox pattern `TopicPublishLog`/`TopicConsumeLog` yang sudah terdokumentasi di [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) Bagian 5.6f (`maintenance-order` → SAP). Phase 2 ini **mereplikasi pola yang sama** untuk boundary service berbeda (`maintenance-execution` → `maintenance-order`) — bukan topic/consumer yang sama persis (beda boundary), tapi arsitekturnya mengikuti precedent yang sudah terbukti jalan, bukan didesain dari nol.
- ~~Scope: Phase 2 saja atau juga menggantikan mekanisme Inspection existing?~~ — **resolved (2026-08-14)**: **cuma berlaku Phase 2**, khusus defect/crack yang dicatat dari **Form**. **Inspection tetap pakai API existing** — direct write Order Type (`CostTypeCode`) & Material ke `MechanicOrderList`/`MechanicOrderMaterial` via screen "Complete Order" ([material-save-api.md](../../architecture/inspection-order/material-save-api.md), dikonfirmasi ada di skema real) — belum diganti, karena Inspection butuh assessment lebih detail dulu sebelum dimigrasikan (beda karakteristik/dependency dari flow Form defect/crack yang baru). **Koreksi (2026-08-16):** referensi ke "Activity Type" di titik ini **dihapus** — `MechanicOrderList` tidak punya mekanisme Activity Type per-eMOL sama sekali hari ini (bukan cuma Phase 2 yang belum migrasi, tapi genuinely belum ada — [lihat koreksi di atas](#poin-5-data-flow-defect-dan-crack)), jadi tidak ada "existing" yang bisa dipertahankan buat field itu. **Migrasi Inspection ke pola publish-consume ini didesain sebagai kemungkinan masa depan**, dilakukan **setelah** flow Form defect/crack Phase 2 terbukti stabil di production — bukan bagian scope Phase 2 ini.

**Kenapa beda dari Inspection — akar penyebabnya beda desain UX, bukan keputusan sembarang (2026-08-14):**

- **Inspection existing**: Finding dan Order adalah **2 fitur/screen terpisah**. Inspection nemuin Finding/defect lewat screen "Inspection — Add Finding" (menghasilkan `TaskPersonalizedFinding`, trigger sync bentuk eMOL skeleton di `maintenance-order`), **lalu** mechanic lanjut ke screen **"Order"** yang terpisah (beda UI/UX) untuk benar-benar create Order (Order Type/Activity Type/Material via "Complete Order"). 2 screen terpisah secara natural menghasilkan 2 titik tulis terpisah ke waktu berbeda — pola direct-write ke `maintenance-order` di screen kedua itu masuk akal untuk struktur 2-screen ini.
- **Phase 2 Form defect/crack**: **disederhanakan jadi 1 UI saja** — capture defect/crack, Order Type/Activity Type, dan Material semuanya dalam **satu alur input**, bukan 2 fitur terpisah seperti Inspection. Karena cuma 1 aksi save, konsolidasi ke 1 service (`maintenance-execution` saja, baru publish-consume ke `maintenance-order`) jadi pilihan natural — menghindari 1 aksi save yang harus pecah jadi 2 call ke 2 service berbeda (alasan race condition yang sudah dibahas di atas).

Jadi bedanya bukan soal salah satu "lebih baik", tapi konsekuensi langsung dari jumlah UI touchpoint — Inspection 2 screen (2 titik tulis wajar terpisah), Form Phase 2 1 screen (1 titik tulis, konsolidasi ke 1 service).

**Belum dibahas tuntas (2026-08-14) — carry-over dari [Poin 1](#ui-view-detail--view-detail-order-2026-08-14):** bagaimana defect/crack dari Form (fitur apapun — Inspection/PM Shutdown/BD Corrective, prinsip [form-centric](#order-integration-bersifat-form-centric-bukan-per-fitur)) disimpan di `maintenance-execution` dan sync ke `maintenance-order` membentuk eMOL — termasuk apakah semua fitur pemanggil Form punya `WorkOrder` row yang sama (relevan buat Asset sourcing di View Detail Order), atau ada yang beda jalur (mis. PM Shutdown/BD Corrective, "Task/Backlog Execution tetap di `DPlanDB`" per Phase 1). ~~User menyebut kemungkinan besar enhancement maintenance-activity-type-enhancement.md akan dikerjakan sebagai bagian Phase 2 ini untuk merapikan data flow-nya.~~ — **superseded (2026-08-17)**: tidak terjadi seperti itu, [lihat catatan superseded di atas](#current-state--mobile-app-ui-v400) — Phase 2 bangun kolom sendiri, cuma `OrderTypeMaintenanceCategoryMapping` yang ternyata relevan.

#### Crack Order Lifecycle

**Crack — Order dibuat sejak tahap monitoring**

Crack yang terdeteksi sejak monitoring (crack masih sangat kecil) tetap **dibuatkan Order**, hanya saja dengan **priority rendah**.

**Crack — eskalasi ke critical saat inspeksi berikutnya**

Saat inspeksi berikutnya, crack yang sama bisa naik status jadi **critical**. Eksekusinya:

- Kalau Order dari temuan sebelumnya **masih open** → eksekusi pakai Order itu (bukan bikin baru).
- Kalau Order sebelumnya **sudah tidak open** → tetap push Order baru ke SAP.

> ~~Catatan (2026-08-12): pola reuse-Order ini kemungkinan generalisasi ke Defect biasa juga, tidak eksklusif Crack.~~ — **confirmed (2026-08-17), bukan lagi spekulasi:** pola reuse-Order ini justru dibangun sebagai mekanisme inti **Defect** itu sendiri (Sub-kasus A, Skenario 2 critical di [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)), lalu Crack journey mengikutinya ("Crack Journey confirmed ikut journey Defect", lihat paragraf di bawah) — bukan sebaliknya, dan bukan lagi "kemungkinan".

**Crack Journey — confirmed ikut journey Defect (2026-08-15):** setelah revisi [User Journey — Defect](#user-journey--defect-2026-08-13) (correlation jalan di kedua kondisi `IsImmediateExecutable`, bukan cuma `Yes`), open item lama soal "scope correlation Crack tidak bisa dibatasi ke `Yes` saja" **otomatis resolved** — Crack journey **sama** dengan Defect journey yang sudah difinalisasi, ditambah: 2 field khusus Crack (Crack Description + Crack Length table) di layar "Defect Identified".

**Resolved (2026-08-17) — TIDAK ada mapping/derivation apapun antara `Monitor`/`Repair Required` dengan `PriorityCode` atau `IsImmediateExecutable`:**
- **`Monitor`/`Repair Required` vs `PriorityCode` — 2 field independen, bukan derivasi.** Severity (Monitor/Repair Required) dan Priority itu **dimensi berbeda** — kombinasi apapun valid, mis. `Monitor` + `P1` ("semua orang perlu tetap awasi ini") itu masuk akal, bukan kontradiksi. Kalimat "priority derivation dari severity" di paragraf sebelumnya **keliru**, sudah dihapus — `PriorityCode` tetap dropdown bebas pilih user, tidak ada default/constraint dari pilihan Monitor/Repair Required.
- **`Monitor`/`Repair Required` vs `IsImmediateExecutable` — juga independen, tidak ada default/pembatasan.** Sistem **sengaja tidak membatasi** kombinasi apapun (mis. `Monitor` + `IsImmediateExecutable=Yes` tetap valid) — kondisi lapangan bisa sangat dinamis, keputusan eksekusi tetap sepenuhnya di tangan user, bukan didikte oleh severity Crack-nya.

Contoh reconstruct untuk cabang `IsImmediateExecutable=No` + ketemu & dipilih Order lama (Crack Monitor yang eskalasi tapi belum dieksekusi):
1. User jawab "Crack Identified: Monitor" → layar "Defect Identified" (dengan field Crack).
2. Isi Component/SubComponent/DamageCode + Crack Description/Length + evidence, `IsImmediateExecutable=No`.
3. Isi 3 field correlation key → button **"Check Existing Crack"** enabled → user tap → List Suggestion tampil.
4. User pilih Order lama yang match.
5. Section Order Type/Activity Type/Part **muncul, read-only**, dan **ditulis penuh** ke eMOL vehicle-approval (reversed 2026-08-16 — [lihat User Journey — Defect](#user-journey--defect-2026-08-13)).
6. Submit.
7. `TaskPersonalizedFinding` baru tersimpan (`IsDraft=0`), `ReuseOrderNumber` terisi — traceability "ditemukan lagi".
8. **Publish ke topic** → `maintenance-order` consume → create eMOL vehicle-approval (`MechanicOrderSummary`+`MechanicOrderList`+`Detail`+`Material`+`Evidence`, full snapshot dari Order lama) — sama seperti cabang `Yes`.
9. eMOL ini **lewat Planner approval seperti biasa**. Begitu approved: **tidak ada aksi lanjutan** (tidak trigger `BacklogExecutionList`, belum ada eksekusi) — cuma jadi record bahwa Planner sudah validasi & setuju defect ini sama dengan Order lama, belum perlu dieksekusi sekarang. Order lama tetap open, tidak disentuh.
10. **REVERSED (2026-08-16) — sekarang JUGA lewat Order-approval (Planner), tidak cuma Form approval.** Sebelumnya cabang `No`+reuse dianggap tidak butuh eMOL/Order-approval sama sekali — dibalik: alasannya, apapun hasil `IsImmediateExecutable`, keputusan reuse/execute-now/butuh-material tetap perlu divalidasi supervisor/planner, bukan cukup self-declared mechanic. Detail: [Poin 9 — Approval Flow](#poin-9-approval-flow). **Bukan Crack-exclusive** — berlaku sama untuk Defect biasa juga. **Sekarang SAMA dengan cabang `Yes`+reuse** soal create eMOL + Order-approval — bedanya cuma post-approval action (poin 9 di atas), bukan lagi soal ada/tidaknya approval.

#### Data Propagation Mapping — `maintenance-execution` → `maintenance-order` (2026-08-17, acuan developer)

Konsolidasi semua field mapping yang sudah dibahas terpisah-pisah di atas, jadi 1 acuan utuh. **Legenda:** 🆕 = kolom/tabel baru (belum ada di skema real hari ini), ✅ = kolom/tabel sudah ada (existing), 🔀 = arah propagasi terbalik (`maintenance-order` → `maintenance-execution`).

**1. `TaskPersonalizedFinding` → `MechanicOrderList` (header eMOL)**

| Kolom sumber (`TaskPersonalizedFinding`) | Status sumber | Kolom tujuan (`MechanicOrderList`) | Status tujuan | Catatan |
|---|---|---|---|---|
| `IsDraft` | 🆕 | — | — | **Tidak propagate sama sekali** — draft tidak pernah publish ke topic ([Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15)), Order hanya melihat state final (`IsDraft=0`). |
| `OrderTypeCode` | 🆕 | `CostTypeCode` | ✅ | Nama kolom beda kedua sisi (legacy naming di Order). |
| `OrderTypeName` | 🆕 | `OrderTypeName` | 🆕 | — |
| `ActivityTypeCode` | 🆕 | `ActivityTypeCode` | 🆕 | — |
| `ActivityTypeName` | 🆕 | `ActivityTypeName` | 🆕 | — |
| `ReuseOrderNumber` | 🆕 | `ReuseOrderNumber` | 🆕 | Reference ke `MechanicOrderList.Number` lokal, **dibaca dari `PoolingMOItem.EMOLNumber`** (value-nya sama, tidak perlu join balik ke `MechanicOrderList`) — **cuma terisi kalau kandidatnya punya row lokal** (precise-match candidate). NULL untuk kandidat `MOOpen`-only atau escape hatch. Bareng `ReuseSAPOrderNumber`, salah satunya non-NULL = marker vehicle-approval eMOL — [lihat mekanisme lengkap di Poin 6](#poin-6-duplicate-atau-correlation-handling). |
| `ReuseSAPOrderNumber` (sebelumnya `SAPMONumber`) | 🆕 | — (tidak langsung) | — | Nomor MO SAP — isinya beda sumber tergantung kondisi kandidat (manual/auto-derive, [lihat Poin 6](#poin-6-duplicate-atau-correlation-handling)). Tidak propagate langsung ke `MechanicOrderList` — dipakai sebagai `BacklogExecutionList.MONumber` post-approval, ~~**dan** update balik `PoolingMOItem`/`SAPMOSyncOrder` milik Order **lama** yang di-reuse~~ (**update balik tidak lagi punya pemicu, 2026-08-19** — [lihat catatan di Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)). |
| `NoPartsRequired` | 🆕 | `NoPartsRequired` | ✅ | Companion existing column di Order side. |
| `DeleteNotes` | ✅ | `DeleteReason` | ✅ | Nama kolom beda, soft-delete reason ([Poin 8](#poin-8-cancel-atau-delete-finding)). **Opsional** — boleh NULL di kedua sisi kalau user tidak mengisi alasan saat delete. |
| `IsActive` | ✅ | `IsActive` | ✅ | Soft-delete flag, cascade juga ke `MechanicOrderSummary` + semua child table ([Poin 8](#poin-8-cancel-atau-delete-finding)). |
| — | — | `Type` | ✅ | Bukan propagate dari kolom manapun — di-**set** consumer jadi value baru `'Form'` saat create ([lihat penjelasan](#poin-5-data-flow-defect-dan-crack)). |
| — | — | `Status` | ✅ | Bukan propagate — di-**set** consumer langsung `Complete` saat create (baik create-baru maupun reuse-vehicle). |

**2. `TaskPersonalizedFinding` → `MechanicOrderDetail` (detail per-line, snapshot-copy)**

| Kolom sumber | Status sumber | Kolom tujuan | Status tujuan | Catatan |
|---|---|---|---|---|
| `ComponentCode` | ✅ | `ComponentCode` | ✅ | — |
| `ComponentName` | 🆕 | `ComponentName` | 🆕 | Resolve sekali di execution, propagate — [lihat prinsip uniform](#poin-5-data-flow-defect-dan-crack). |
| `SubComponentCode` | ✅ | `SubComponentCode` | ✅ | — |
| `SubComponentName` | 🆕 | `SubComponentName` | 🆕 | Sama pola. |
| `DamageCode` | ✅ | `DamageCode` | ✅ | — |
| `DamageName` | 🆕 | `DamageName` | 🆕 | Sama pola. |
| `CauseCode` | ✅ | `CauseCode` | ✅ | — |
| `CauseName` | 🆕 | `CauseName` | 🆕 | Sama pola. |
| `ActionRemedyCode` | ✅ | `ActionRemedyCode` | ✅ | — |
| `ActionRemedyName` | 🆕 | `ActionRemedyName` | 🆕 | Sama pola. |
| `PriorityCode` | ✅ | `PriorityCode` | ✅ | — |
| `PriorityName` | 🆕 | `PriorityName` | 🆕 | Resolve upstream cross-service ke Asset, tapi propagasi ke Order tetap pola sama ([lihat detail](#poin-5-data-flow-defect-dan-crack)). |
| `DefectNotes` | ✅ | `DefectNotes` | ✅ | — |
| `RepairDuration` | ✅ | `RepairDuration` | ✅ | — |
| `RepairInstruction` | ✅ | `RepairInstruction` | ✅ | — |
| `IsImmediateExecutable` | ✅ | `IsImmediateExecutable` | 🆕 | Snapshot-copy sederhana (boolean), bukan cross-service — [lihat View Detail Order](#ui-view-detail--view-detail-order-2026-08-14). |

**3. `CrackIdentified` → `MechanicOrderCrackIdentified` (🆕 tabel baru sisi Order)**

| Kolom sumber (`CrackIdentified`, existing) | Kolom tujuan (`MechanicOrderCrackIdentified`, 🆕 tabel baru) |
|---|---|
| `CrackDescription` | `CrackDescription` |
| `CrackLength` | `CrackLength` |
| `PrevCrackLength` | `PrevCrackLength` |

FK: `MechanicOrderCrackIdentified.MechanicOrderListId` (not null, 1-to-many) — mirror `MechanicOrderMaterial`. **Tidak di-backfill** (tidak ada eMOL historis dari Crack finding, [lihat alasan](#struktur-screen-defect-identified)).

**4. `TaskPersonalizedFindingMaterial` (🆕 tabel baru sisi execution) → `MechanicOrderMaterial`**

Skema kolom persis **belum final** — kemungkinan mirror `MaterialNumber`/`Quantity`/`Batch`/`UoM`/dll ([lihat catatan](#poin-5-data-flow-defect-dan-crack)), dicatat sebagai kerja desain lanjutan. FK wajib `TaskPersonalizedFindingId`.

**5. `PoolingMOItem` (dalam service `maintenance-order`, same-service dari `MechanicOrderDetail` — bukan cross-service dari execution)**

| Kolom baru | Source |
|---|---|
| `ComponentCode` 🆕 | `MechanicOrderDetail.ComponentCode` |
| `SubComponentCode` 🆕 | `MechanicOrderDetail.SubComponentCode` |
| `DamageCodeValue` 🆕 | `MechanicOrderDetail.DamageCode` (nama beda dari `DamageCode` existing di `PoolingMOItem` yang isinya Name, [lihat alasan](#poin-6-duplicate-atau-correlation-handling)) |

**6. `TaskPersonalizedEvidence` (✅ existing) → `MechanicOrderEvidence` (✅ existing) — resolved (2026-08-17), sudah ada mekanismenya, bukan gap:**

| Kolom sumber | Status | Kolom tujuan | Status | Catatan |
|---|---|---|---|---|
| `Name` | ✅ | `Name` | ✅ | Snapshot-copy — **dikonfirmasi live di skema real** ([maintenance-order-schema.md](../../architecture/database/maintenance-order-schema.md), bukan proposal), pola sama dengan `MechanicOrderDetail`. |
| `ContentAddress` | ✅ | `ContentAddress` | ✅ | Sama pola. |

FK: `TaskPersonalizedEvidence.TaskPersonalizedFindingId` (nullable — evidence bisa nempel ke `TaskPersonalized` langsung tanpa Finding spesifik, tapi yang relevan buat propagasi ke Order cuma yang terikat ke Finding). **Ini pola existing yang sudah jalan hari ini** (buat eMOL Inspection) — consumer baru Phase 2 tinggal replikasi pola yang sama, bukan mekanisme baru. Menjawab open item lama "evidence/foto carry-over ke Order" ([checklist item 5](order-integration-checklist.md)).

**7. Arah terbalik 🔀 — `maintenance-order` → `maintenance-execution` (topic baru, belum final skemanya)**

`maintenance-order` publish event begitu **WorkflowTransaction pertama** tercatat di Order-approval chain manapun → `maintenance-execution` consume jadi flag lokal baru di `TaskPersonalizedFinding` (nama kolom final menyusul, sementara `IsOrderApprovalLocked`) — dipakai gate tombol Edit/Delete di mobile ([lihat mekanisme lengkap](#poin-7-editability-window-sebelum-approval)). **Satu-satunya arah propagasi yang tidak forward** dari semua yang dibahas di dokumen ini.

### Poin 6: Duplicate atau Correlation Handling

Foundational untuk keputusan reuse-Order di [Crack Order Lifecycle](#poin-5-data-flow-defect-dan-crack), dan juga relevan untuk skenario Defect critical-escalation ([Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)).

**Correlation key (2026-08-13):** Asset + Component + SubComponent + **DamageCode**. DamageCode ditambahkan ke key karena relasi `SubComponent ↔ DamageCode` di master data bersifat **many-to-many** (lihat [query_mapping_damage_code.sql](../../query/query_mapping_damage_code.sql) & [master data Damage](../../../BUMA-ID-project/master-data/damage-code-all.csv)) — 1 SubComponent yang sama bisa punya beberapa DamageCode valid berbeda (mis. "Crack" dan "Corroded" di lokasi fisik yang sama), jadi Asset+Component+SubComponent saja berisiko salah gabung dua temuan yang sebenarnya tidak related.

**Mekanisme pencarian (2026-08-13):** bukan auto-match, bukan full-manual — **sistem (FE mobile) search & suggest** kandidat Order relevan, lalu **manusia yang pilih & validasi final** dari suggestion itu (mengingat bisa ada >1 Order open yang match). Yang bisa melakukan pemilihan: **siapapun yang sedang mengerjakan form tersebut** (mechanic/foreman/supervisor/dst), mengikuti permission yang sudah ada — tidak perlu permission baru (lihat [Fase B](#fase-b--aktor)).

**Candidate scope (2026-08-14, direvisi 2026-08-19):** ~~cuma Order yang sudah lolos Planner approval — Order yang **masih pending approval** (belum diproses Planner, `PoolingMOItem` belum pernah ter-insert — lihat [Bagian 5, Alur Sync ke SAP](../../architecture/inspection-order/order-emol-sap-sync.md#5-alur-sync-ke-sap-post-approval), yang jalan **post-approval**) **di-exclude dari kandidat suggestion**. Konsisten dengan asumsi [Sub-kasus A Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack) bahwa Order lama yang direuse "sudah pernah lolos approval saat pertama kali dibuat".~~ **Resolved (2026-08-19):** kandidat di-drive dari union `PoolingMOItem` ∪ `MOOpen`, di-dedup lewat join `MOOpen.MONumber` → `SAPMOSyncOrder.MONo`. eMOL yang masih pending approval belum punya row di keduanya, jadi **tersaring dengan sendirinya** — tidak ada filter approval eksplisit di query. Kalau satu Order muncul di dua sisi, **identitas A1 yang dipakai**; sisi `MOOpen` hanya menyumbang status dan `MONumber`. Detail sourcing description per kondisi ada di [UI View Detail — List Suggestion Order Lama](#ui-view-detail--list-suggestion-order-lama-2026-08-14).

**`MOOpen` tidak hanya berisi MO yang masih open (2026-08-19)** — MO yang sudah TECO/closed di SAP tetap punya row di `MOOpen`. Karena itu candidate scope **meng-exclude status terminal (TECO/CLSD)**: Order seperti itu tidak akan pernah jadi REL, jadi TECO-nya akan ditolak selamanya sementara row `BacklogExecutionList` sudah terlanjur ter-insert tanpa ada yang membersihkan. **CRTD tidak di-exclude** — statusnya tinggal menunggu waktu, dan retry existing menyelesaikannya sendiri begitu Order jadi REL.

**⚠️ Accepted Risk (2026-08-19) — window pending approval tidak terlihat correlation.** Antara submit dan final approval, eMOL belum punya row di `PoolingMOItem` maupun `MOOpen`, jadi **tidak muncul sebagai kandidat**. Ini sisi lain dari "tersaring dengan sendirinya" di atas: penyaringannya benar, tapi berarti ada window buta. Kalau ada Finding lain untuk defect yang sama di komponen yang sama dalam window itu, correlation mengembalikan kosong dan terbentuk **Order kedua**. Paling merugikan di cabang `IsImmediateExecutable=Yes` — kerusakannya sudah diperbaiki, jadi Order kedua murni sampah.

**Diterima — dan sengaja tidak dijawab dengan mengetatkan sistem.** Mitigasinya ada di **people & process**: approval ditangani segera, dan mechanic di lapangan bekerja terkoordinasi, bukan sendiri-sendiri. Kalaupun terjadi, itu konsekuensi people & process, bukan cacat desain. Ini pilihan sadar, bukan kelalaian — **Digiman+ adalah tools, dan tools bukan satu-satunya pilar yang menentukan masalah bisnisnya selesai atau tidak.** Membatasi alur kerja lapangan (mis. mengunci jumlah Form aktif, atau memaksa SLA approval) demi menutup window ini akan menukar masalah kecil dengan hambatan operasional yang lebih besar.

**Guard teknisnya sudah diketahui, tapi masih future:** pencegahan penuh baru ada saat **fitur reject** tersedia ([Poin 10](#poin-10-rejectrework-flow), next MVP) — approver bisa membatalkan Order kedua yang seharusnya tidak ada, dengan **`Approval Remark` wajib diisi** sebagai alasannya. Sampai saat itu approver hanya bisa **mengoreksi** tautan reuse, tidak menolak eMOL-nya ([lihat batas makna gate di Poin 5](#poin-5-data-flow-defect-dan-crack)).

**Terpisah dari itu — bukti bahwa masalahnya nyata, bukan mekanisme guard-nya:** duplicate Order **sudah terjadi hari ini** tanpa fitur ini, dibersihkan manual lewat soft-delete dengan `DeleteReason` bernilai `"double order"` ([lihat temuan data Poin 5](#poin-5-data-flow-defect-dan-crack)). Itu jejak pembersihan setelah kejadian, bukan pencegahan — jangan disamakan dengan `Approval Remark` di atas. Kesimpulannya: correlation mengecilkan masalahnya secara signifikan, tidak menghilangkannya.

**Resolved (2026-08-17) — reuse TIDAK exclusive, 1 Order bisa direuse berkali-kali (dari user):** koreksi asumsi awal — sebelumnya sempat dianggap begitu 1 Order dipilih/di-reuse 1 Finding, Order itu "terpakai" buat Finding lain. **Ini salah** — 1 Order lama **boleh direuse berkali-kali oleh banyak Finding berbeda secara bersamaan**, itu bukan konflik (mis. beberapa laporan defect yang sama-sama valid nunjuk ke 1 Order/pekerjaan fisik yang sama). Satu-satunya yang bikin Order **tidak valid lagi** untuk direuse: **sudah punya `MONo` dari SAP DAN sudah dieksekusi** (masuk `BacklogExecutionList`) — persis kriteria **"`MOOpen` minus `BacklogExecutionList`"** yang sudah dipakai sebagai filter candidate-scope di atas (mekanisme Outstanding Backlog existing, [lihat di bawah](#poin-6-duplicate-atau-correlation-handling)) — bukan kriteria baru, cuma dikonfirmasi ulang di sini karena relevan buat edge case berikut.

**Resolved (2026-08-17) — edge case: reuse candidate jadi stale di antara "Check Existing" dan submit final:** karena search "Check Existing" cuma jalan sesaat (snapshot waktu itu), ada window dimana kandidat yang **valid saat dipilih** bisa jadi **sudah dieksekusi** (masuk `BacklogExecutionList` lewat Finding lain) sebelum submit final terjadi — realistis terjadi kalau draft dibiarkan lama ([Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15)) atau offline berhari-hari. **Keputusan: validasi ulang `ReuseOrderNumber` di titik submit final** (bukan cuma pas "Check Existing" awal) — pakai kriteria **yang sama persis** dengan candidate-scope search (`IsActive=1` DAN belum masuk `BacklogExecutionList`). Kalau sudah tidak valid → submit **di-block khusus bagian reuse ini** (beda dari conflict edit-vs-edit yang sukses-dengan-notif, [lihat Poin 5](#poin-5-data-flow-defect-dan-crack) — di sini datanya genuinely sudah tidak bisa dipakai lagi), user diarahkan re-run "Check Existing" atau lanjut sebagai Order baru. Berlaku juga tiap kali `ReuseOrderNumber` diubah lewat edit ([lihat Poin 7](#poin-7-editability-window-sebelum-approval)), bukan cuma submit pertama.

**Gap ditemukan & fixed — kandidat `MOOpen`-only tidak pernah bisa lolos filter Component/SubComponent/DamageCode (2026-08-14):** mekanisme search di atas (filter by Component+SubComponent+DamageCode) secara teknis butuh join ke `PoolingMOItem` (satu-satunya sumber field-field itu) — akibatnya kandidat yang **cuma ada di `MOOpen`** (tidak ada `PoolingMOItem`-nya, mis. skenario MO Backlog re-entry SAP, [Poin 13](order-integration-checklist.md#fase-e--integrasi)) **tidak akan pernah lolos filter ini**, karena `MOOpen` (data murni dari SAP) tidak punya Component/SubComponent/DamageCode sama sekali. "Case 3" yang tercatat di description-sourcing [List Suggestion Order Lama](#ui-view-detail--list-suggestion-order-lama-2026-08-14) sebelumnya jadi **dead path** kalau tidak diperbaiki.

**Fix — 2 jalur search terpisah, ditampilkan sebagai 2 section terpisah:**
1. **Jalur precise-match** (existing) — filter Asset+Component+SubComponent+DamageCode via join `PoolingMOItem`.
2. **Jalur broader-match** (baru) — filter cuma by **Asset Number + Site Code** (sinyal jauh lebih lemah, tidak coba match defect spesifik). **Dijalankan ke `PoolingMOItem` (`Equipment`+`SiteId`, filter longgar) DAN ke `MOOpen` (`AssetNumber`+`SiteCode`) sekaligus** — bukan cuma `MOOpen`. **Koreksi (2026-08-18):** `PoolingMOItem` punya kolom `Equipment`/`SiteId`, jadi kandidat yang **punya row lokal tapi tidak match presisi by defect** (Component/SubComponent/DamageCode beda dari defect yang lagi dicari) juga bisa muncul di section Broader Match, bukan eksklusif kandidat `MOOpen`-only. Hasil jalur ini **exclude kandidat yang sudah muncul di jalur precise-match** (supaya tidak dobel tampil di 2 section).

**Resolved (2026-08-18) — presentasi 2 section, bukan 1 list digabung:** di [List Suggestion Order Lama](#ui-view-detail--list-suggestion-order-lama-2026-08-14), kandidat dari kedua jalur **dikelompokkan spasial jadi 2 section terpisah** (mis. section "Precise Match" lalu section "Broader Match" di bawahnya) — bukan 1 list ter-interleave dengan badge inline saja. Lebih jelas secara visual buat user langsung tahu tingkat kepercayaan tiap grup tanpa perlu baca badge satu-satu, tetap konsisten dengan prinsip "manusia yang validasi final". **Butuh UI Designer** untuk layout persis 2 section ini (termasuk badge/label per section, empty state kalau salah satu section kosong).

**Yang berubah di Order lama kalau ketemu match (2026-08-13, final 2026-08-15 setelah beberapa kali revisi):** **tidak ada field `MechanicOrderList` LAMA yang diubah langsung.** Yang terjadi: eMOL **baru** dibentuk (snapshot data dari Order lama, jadi "vehicle" buat lewat Planner approval — safety net atas keputusan reuse, **korektif, bukan preventif-total** ([batas maknanya di Poin 5](#poin-5-data-flow-defect-dan-crack))), lalu **post-approval** trigger mekanisme "eksekusi MO Backlog" existing (create `BacklogExecutionList` di `maintenance-execution`, mengarah ke Order **lama**, TECO ke SAP jalan lewat pipeline yang sudah ada) — bukan sync SAP sebagai MO baru buat eMOL vehicle itu sendiri (supaya tidak duplicate). Detail lengkap ada di [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack) (Sub-kasus A) & [Poin 5](#poin-5-data-flow-defect-dan-crack).

**Gap teknis — DamageCode tidak sampai ke SAP, MO Backlog tidak ter-link ke source (2026-08-13):**

Concern besar: `DamageCode` (dan ternyata juga `Component`/`SubComponent`) **tidak dikirim ke SAP** — sudah teridentifikasi sebagai gap di [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) (Bagian 4/§204, Open Items §428): field ini tersimpan di `PoolingMOItem` tapi tidak ada mapping ke BAPI (`GI_HEADER`/`GI_OPER`/`GI_COMP`). Ditambah, data "MO Backlog" (outstanding Order yang dipakai user sehari-hari) **murni berasal dari SAP** (§436) dan tidak terlihat ada join-back terdokumentasi ke row `MechanicOrderList` asal.

**Current state — mekanisme Outstanding Backlog yang sudah ada (2026-08-13):** ternyata sebagian besar dari yang dibutuhkan correlation **sudah jalan hari ini**, dipakai fitur "backlog execution" di layar Inspection (inspector pilih & eksekusi MO Backlog langsung saat inspeksi):

- **`MOOpen`** (service `maintenance-order`, pure data SAP) = source list outstanding backlog.
- **`BacklogExecutionList`** (service `maintenance-execution`) = record completion; begitu ada row aktif untuk `MONumber` tertentu, MO itu hilang dari list outstanding.
- Filter **"`MOOpen` minus `BacklogExecutionList`"** ini **sudah ada & jalan** (lintas service `maintenance-order` ↔ `maintenance-execution`) — bukan sesuatu yang perlu dibangun baru untuk correlation kita.
- `MOOpen` dan `PoolingMOItem` **sama-sama di service `maintenance-order`** — jadi join di antara keduanya **same-service**, bukan cross-service.
- Mekanisme ini secara natural **cuma mempertimbangkan record yang sudah punya `MONo`** (masuk akal — `MOOpen` diisi dari SAP, jadi mustahil punya entri untuk Order yang belum pernah di-push).

**Resolusi (2026-08-13, dipersempit 2026-08-16 — pakai current-state schema, bukan digantungkan ke enhancement terpisah):** correlation ternyata tidak butuh DamageCode sampai ke SAP sama sekali, dan tidak perlu bangun pathway baru — kolom baru yang genuinely dibutuhkan cuma yang langsung dipakai correlation key (Asset+Component+SubComponent+DamageCode):

1. **Tambah 3 kolom Code baru di `PoolingMOItem`** — `ComponentCode`, `SubComponentCode`, `DamageCodeValue` (bukan `DamageCode` — nama itu sudah dipakai kolom existing yang **isinya Name**, bukan Code, lihat catatan di bawah). Source-nya dari `MechanicOrderDetail.ComponentCode`/`SubComponentCode`/`DamageCode` yang **sudah ada** ([5.2](../../architecture/inspection-order/order-emol-sap-sync.md#52-bc-update-jika-ada-create-jika-tidak-ada--insert-ke-poolingmoitem)) — tidak perlu kolom baru di `MechanicOrderDetail`, tinggal diikutkan di parameter insert ke `PoolingMOItem` yang belum include field ini hari ini.
2. **Join `MOOpen` ↔ `PoolingMOItem`** by `MONumber`/`MONo` (same-service, `maintenance-order`) — begitu ini ada, list outstanding backlog yang sudah ada otomatis bisa dipakai untuk correlation matching by DamageCode dkk, numpang ke filter `MOOpen`-minus-`BacklogExecutionList` yang sudah jalan.

**Kenapa kolom Code baru, tidak bisa reuse kolom existing (2026-08-16):** `PoolingMOItem` sudah punya kolom `Component`/`SubComponent`/`DamageGroup`/`DamageCode` hari ini — tapi insert query-nya ([5.2](../../architecture/inspection-order/order-emol-sap-sync.md#52-bc-update-jika-ada-create-jika-tidak-ada--insert-ke-poolingmoitem)) pakai parameter `@ComponentName1`/`@SubComponentName1`/`@DamageName1`, dan contoh payload SAP ([6.1](../../architecture/inspection-order/order-emol-sap-sync.md#61-contoh-payload-servicebus)) juga isinya Name (`"DamageCode": "Broken"`, bukan ID) — jadi kolom-kolom itu **sebenarnya menyimpan Name, bukan Code**, meski nama kolomnya menyesatkan. Correlation butuh match presisi berbasis **Code** (identifier stabil) — alasan `DamageCode` masuk correlation key sejak awal justru karena relasi SubComponent↔DamageCode di master data many-to-many, jadi Name (rawan ambigu/berubah) tidak cukup andal buat itu. Karena nama `DamageCode` sudah "kepakai" kolom Name existing, kolom Code aslinya dinamai **`DamageCodeValue`** supaya tidak tabrakan/breaking downstream (payload SAP yang sudah expect Name di situ tidak perlu diubah).

**Cause/ActionRemedy sengaja TIDAK ditambahkan ke `PoolingMOItem` (revisi dari resolusi lama, 2026-08-16):** bukan bagian correlation key, dan View Detail Order (satu-satunya tempat lain yang sempat mempertimbangkan pakai `PoolingMOItem`) sudah bypass total, join langsung ke `MechanicOrderDetail`/`MechanicOrderMaterial`/`MechanicOrderEvidence` ([lihat keputusan](#ui-view-detail--view-detail-order-2026-08-14)) — tidak ada consumer Phase 2 yang genuinely butuh field ini ada di `PoolingMOItem`. Prinsip current-state-schema yang sama dengan [catatan View Detail Order](#ui-view-detail--view-detail-order-2026-08-14): kalau ada kebutuhan nyata nanti, ditambahkan sebagai scope eksplisit saat itu, bukan pre-emptive.

**Resolved (2026-08-16, koreksi titik resolve — lihat [Poin 5](#poin-5-data-flow-defect-dan-crack)) — kolom Name baru di `MechanicOrderDetail` (beda tabel dari `PoolingMOItem` di atas):** tambah 5 kolom companion Name — `ComponentName`, `SubComponentName`, `DamageName`, `CauseName`, `ActionRemedyName` — mendampingi kolom Code yang sudah ada (`ComponentCode`/`SubComponentCode`/`DamageCode`/`CauseCode`/`ActionRemedyCode`). Alasan: **View Detail Order** ([lihat field table](#ui-view-detail--view-detail-order-2026-08-14)) nampilin kelima field ini ke user sebagai label, bukan raw Code — `MechanicOrderDetail` saat ini cuma punya kolom Code, jadi tanpa kolom Name ini butuh live-lookup ke master data tiap kali render, melanggar prinsip **snapshot-at-creation** yang dipakai konsisten di tempat lain (mis. `OrderTypeName`/`ActivityTypeName`). Semua 5 kolom ditambahkan sekaligus untuk konsistensi — Cause/Action Remedy ditampilkan dengan cara yang sama persis (Code-only saat ini) dengan Component/SubComponent/Damage di layar yang sama, jadi tidak masuk akal cuma sebagian yang dapat Name. **Titik resolve-nya bukan di `maintenance-order`** — companion Name yang sama juga ditambahkan ke `TaskPersonalizedFinding` ([lihat skema final Poin 5](#poin-5-data-flow-defect-dan-crack)), resolve sekali di titik Finding dibuat di `maintenance-execution`, lalu `MechanicOrderDetail` tinggal terima lewat propagate publish/consume yang sudah ada — bukan resolve independen di `maintenance-order`.

**Backfill data lama (2026-08-16, direvisi — ikut koreksi titik resolve di [Poin 5](#poin-5-data-flow-defect-dan-crack)) — semua row historis, bukan cuma data baru setelah rilis:**
- **`PoolingMOItem.ComponentCode`/`SubComponentCode`/`DamageCodeValue`** — backfill dengan **join balik ke `MechanicOrderDetail`** (`PoolingMOItem.EMOLNumber = MechanicOrderList.Number` → `MechanicOrderDetail.MechanicOrderListId`), **bukan** reverse-lookup dari teks Name yang sudah ada di `PoolingMOItem` sendiri (ambigu, itu justru masalah many-to-many yang mau dihindari). Coverage tergantung row `MechanicOrderDetail` historis + Code-nya masih utuh — wajar karena kolom Code itu memang sudah ada dari awal, tidak pernah hilang.
- **`TaskPersonalizedFinding.ComponentName`/`SubComponentName`/`DamageName`/`CauseName`/`ActionRemedyName`/`PriorityName`** — backfill di sini dulu (bukan langsung di `MechanicOrderDetail`), dengan resolve Code existing ke master data **saat ini** (one-time script, cross-service call ke Asset khusus `PriorityName` — bisa diterima karena sekali jalan, beda dari live-lookup per-request). Row dengan Code yang sudah deprecated/dihapus dari master data tetap NULL setelah backfill (tidak terhindarkan) — kalau volume-nya signifikan, perlu direview manual terpisah. Name hasil backfill pakai definisi master data hari ini, bukan snapshot histori persis saat Finding itu dibuat — limitasi wajar proses backfill, dicatat supaya tidak dianggap 100% akurat historis.
- **`MechanicOrderDetail.ComponentName`/`SubComponentName`/`DamageName`/`CauseName`/`ActionRemedyName`/`PriorityName`** — backfill dengan **propagate dari hasil backfill `TaskPersonalizedFinding` di atas** (join by `TaskPersonalizedFindingId`/`WorkOrderId`, pola sama dengan backfill `PoolingMOItem`) — **bukan** resolve independen kedua kalinya ke master data. Konsisten dengan prinsip "resolve sekali di upstream, propagate ke bawah" yang sekarang berlaku uniform untuk keenam field.
- **⚠️ Pengecualian — `TaskPersonalizedFinding.NoPartsRequired` TIDAK ikut prinsip "semua row historis" di atas (2026-08-16, user):** dibiarkan `NULL` untuk semua row lama, **tidak di-backfill sama sekali**. Beda karakter dari 6 field Name di atas — field-field itu punya Code existing yang bisa di-derive jadi Name, sementara `NoPartsRequired` itu **konsep yang genuinely baru** di `maintenance-execution`, tidak ada data historis apapun yang bisa dijadikan dasar (bukan soal "sulit di-derive", tapi memang tidak ada faktanya). `NULL` di sini artinya "konsep ini belum ada saat itu", bukan "tidak diketahui, dianggap 0". Detail skema & alasan load-bearing-nya di [Poin 5](#poin-5-data-flow-defect-dan-crack) di atas.

Rantai lengkap correlation "apakah Order masih open":

```
MechanicOrderList (Finding/Order asal, + DamageCode dkk via MechanicOrderDetail)
   → PoolingMOItem.PoolingId
      → SAPMOSyncOrder.MONo  (nomor MO dari SAP, NULL kalau belum sync)
         ≈ MOOpen.MONumber  (kalau masih ada di sini = masih outstanding, minus yang sudah di BacklogExecutionList)
```

- **`MONo` NULL** → belum sync ke SAP, masih di pipeline lokal Digiman+ → default **open**, kecuali ada state semacam Rejected/Cancelled di `MechanicOrderList` yang bikin dia mati meski `MONo` tidak pernah terisi. Ini satu-satunya bagian yang **genuinely baru** (tidak tercover mekanisme Outstanding Backlog existing, karena SAP tidak tahu apa-apa soal Order yang belum di-push).
- **`MONo` terisi** → status open/closed-nya **tinggal numpang** ke mekanisme Outstanding Backlog existing (`MOOpen` minus `BacklogExecutionList`) — tidak perlu logic baru sama sekali di sisi ini, cuma butuh join `PoolingMOItem` (poin 2 di atas) untuk dapat `DamageCodeValue` dkk-nya.

**Resolved (2026-08-17):** ya — `MechanicOrderList.IsActive=0` (soft-delete, [lihat Poin 8](#poin-8-cancel-atau-delete-finding)) adalah state yang harus dikecualikan dari "open" meski `MONo` masih NULL. Filter kandidat correlation/candidate-scope perlu tambahan syarat `IsActive=1`, bukan cuma soal `MONo` terisi/tidak.

#### `ReuseOrderNumber` & `ReuseSAPOrderNumber` — Mekanisme Lengkap Lintas Semua Kondisi Kandidat (2026-08-18, resolved)

Konsolidasi keputusan yang tersebar (Poin 1, di sini, dan diskusi List Suggestion) jadi 1 acuan — supaya konsisten dipakai developer terlepas kandidatnya ketemu lewat jalur mana.

**⚠️ Koreksi penting (2026-08-18) — determinannya "`PoolingMOItem` ada atau tidak", BUKAN "section Precise Match vs Broader Match":** sempat disederhanakan seolah section (badge) yang menentukan sourcing data — **itu keliru**. `PoolingMOItem` punya kolom `Equipment`/`SiteId`, jadi query broader-match (Asset+Site saja) dijalankan ke **`PoolingMOItem` juga**, bukan cuma `MOOpen` ([lihat fix di atas](#poin-6-duplicate-atau-correlation-handling)). Konsekuensinya: kandidat yang tampil di section **Broader Match** bisa saja tetap **punya row `PoolingMOItem`** (cuma tidak match presisi by defect code) — beda dari kandidat yang genuinely `MOOpen`-only (tidak punya `PoolingMOItem` sama sekali). Section di UI itu soal **tingkat kepercayaan match** (buat user), sourcing data (`ReuseOrderNumber`, Material) soal **ada tidaknya `PoolingMOItem`** — 2 hal yang independen, jangan disamakan.

**Prinsip dasar — 2 field, masing-masing 1 arti tetap, tidak pernah dobel makna:**

| Field | Arti | Terisi kalau |
|---|---|---|
| `ReuseOrderNumber` | Reference ke `MechanicOrderList.Number` **lokal** Digiman+, **dibaca dari `PoolingMOItem.EMOLNumber`** (value-nya sama, tidak perlu join balik ke `MechanicOrderList`) | Kandidat yang dipilih **punya row `PoolingMOItem`** — terlepas ketemu lewat jalur precise-match atau broader-match. NULL kalau tidak ada row `PoolingMOItem`. |
| `ReuseSAPOrderNumber` | Nomor MO **SAP** | Tergantung kondisi — lihat tabel per-kasus di bawah. |

**Per kondisi kandidat (determinan: keberadaan `PoolingMOItem`, bukan section list):**

| Kondisi | Bisa muncul di section | `ReuseOrderNumber` | `ReuseSAPOrderNumber` | Order Type/Activity Type/Material |
|---|---|---|---|---|
| `PoolingMOItem` ada, match presisi by defect code | Precise Match saja | `MechanicOrderList.Number` | ~~Kosong kalau `MONo` sudah ada — **manual, mandatory** kalau `MONo` masih NULL **dan** butuh material, opsional kalau tidak butuh material.~~ **Resolved (2026-08-19): selalu kosong** — tidak pernah diinput manual, selalu auto dari `SAPMOSyncOrder.MONo`. Kalau `MONo` masih NULL dan `IsImmediateExecutable=Yes` → **final approval** yang di-block ([Poin 7](#poin-7-editability-window-sebelum-approval)), bukan ditutup input manual dan bukan di-block di submit. | Ikut [tangga Sumber Data Order](#user-journey--defect-2026-08-13) — kalau Order sudah sync: Order Type/Activity Type dari `MOOpen`, Material dari `CheckPartOrder`. Kalau belum sync (`MONo` NULL): keduanya jatuh ke tingkat 2, Order Type/Activity Type dari `PoolingMOItem.MOType`/`PMActType`, Material dari `MechanicOrderMaterial`. |
| `PoolingMOItem` ada, TIDAK match presisi (cuma match Asset+Site) | Broader Match saja | `MechanicOrderList.Number` (**sama seperti baris di atas** — row lokal-nya tetap ada) | Sama seperti baris di atas — **selalu kosong**, tidak berubah karena posisi section. | Sama seperti baris di atas — posisi section tidak mengubah sourcing. |
| `PoolingMOItem` tidak ada sama sekali, `MOOpen` ada | Broader Match saja (satu-satunya cara ketemu) | **NULL** (tidak ada row lokal untuk direferensikan) | **Auto-derive dari `MOOpen.MONumber`** — tidak perlu input manual. | Ikut [tangga Sumber Data Order](#user-journey--defect-2026-08-13) — row `MOOpen` pasti ada (itu yang bikin kandidat ini ketemu), tapi tingkat 1 tetap dievaluasi **per field**: Order Type (`CostTypeCode`), Activity Type (`MaintenanceCategoryCode` — **bisa NULL**), Material (`CheckPartOrder` — bisa tidak ada row). Field yang kosong langsung jatuh ke **tingkat 3**, karena tingkat 2 tidak tersedia (tidak ada row di `maintenance-order`). |
| Keduanya tidak ada, tapi user tahu ada di SAP | — (escape hatch, bukan dari list) | **NULL** | **Manual oleh user** (mandatory saat checkbox dicentang, [lihat Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)). | Tergantung hasil lookup — ketemu → sama seperti A1/A2; tidak ketemu (A-manual) → tingkat 3, manual semua. |
| Keduanya tidak ada, genuinely Order baru | — (bukan kandidat) | NULL | NULL | Manual/editable (Order baru genuine). |

**Resolved (2026-08-19) — escape hatch adalah jalur penemuan alternatif, bukan mode data terpisah.** Sistem tetap mencoba lookup `MOOpen` + `CheckPartOrder` dengan MO Number yang diinput: ketemu → perilakunya mengikuti A1/A2 sepenuhnya; tidak ketemu → **A-manual**, user menentukan `NoPartsRequired`, Order Type, Activity Type, dan Material sendiri. Prinsipnya auto-detection dulu, manual hanya sebagai fallback saat auto-detection gagal.

**Lookup = 3 query ke tabel backend Digiman+** (hasil inbound sync SAP, bukan panggilan live ke SAP), dijalankan **by `MONumber` langsung** — melewati filter Asset/Site/DamageCode yang dipakai correlation search, karena justru kegagalan filter itulah alasan escape hatch dibutuhkan:

1. `MOOpen` by `MONumber` — Order ada? statusnya terminal (TECO/CLSD) atau tidak? sekalian Order Type/Activity Type
2. Join `SAPMOSyncOrder`/`PoolingMOItem` — ada row `PoolingMOItem` untuk MO ini? (A1 vs A2)
3. `CheckPartOrder` by `MONumber` — material line

**Klasifikasi adalah hasil lookup, bukan klaim client.** A2 dan A-manual identik di payload (`ReuseOrderNumber` NULL + `ReuseSAPOrderNumber` terisi) — itu tidak perlu dibedakan client, karena lookup yang menentukan: ketemu di `MOOpen` → A2, tidak ketemu → A-manual.

**Offline:** cache kandidat ([Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15)) sudah memuat `MOOpen`, jadi lookup bisa jalan offline terhadap cache yang sama — tinggal dicocokkan by `MONumber`. Perluas payload sync-down agar memuat `CheckPartOrder` untuk kandidat yang sama, supaya escape hatch berfungsi penuh offline tanpa mekanisme baru.

**Tidak ketemu saat offline = A-manual SEMENTARA**, bukan final. Server menjalankan lookup ulang di titik submit ([Poin 7](#poin-7-editability-window-sebelum-approval)); kalau ternyata ketemu, status naik jadi A1/A2 dan field di-derive ulang — input manual user **ditimpa**.

**Tidak ada flag dari client.** Sinyal untuk menjalankan validasi diambil dari terisinya `ReuseOrderNumber`/`ReuseSAPOrderNumber` di payload — pola sama dengan `IsDraft=0` yang men-gate publish: keputusan dari isi request, bukan dari asumsi state client. Flag akan berarti BE mempercayai klasifikasi client, padahal client offline justru yang paling mungkin salah.

**Penimpaan harus eksplisit**, lewat diff nilai kirim vs nilai derive. Response sukses (bukan reject), bawa daftar field yang berubah. Contoh copy:

> *"This Order was found in the ERP. Order Type, Activity Type, and Material have been updated to match it — please review before continuing."*

**Konsekuensi UI — keputusan lama perlu direvisi.** Entry point escape hatch tetap. Yang berubah: section Order Type/Activity Type/Part **tidak lagi langsung manual/editable** begitu escape hatch dipilih — ada langkah lookup di antaranya, dan hasilnya yang menentukan bentuk section (ketemu → read-only derived; tidak ketemu → manual/editable). Tiga hal butuh desain baru:

1. **Feedback state** setelah input MO Number — user harus tahu Order-nya ketemu atau tidak, dan kenapa field yang tadinya bisa diisi tiba-tiba terkunci.
2. **Klasifikasi bisa berubah setelah lookup** — escape hatch yang ternyata ketemu jadi A1/A2, dan field yang tadinya manual berubah jadi read-only derived. `MONo`-nya tetap pasti ada (dari `MOOpen.MONumber`), jadi escape hatch yang ketemu tidak pernah jatuh ke baris 3 matrix ([Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)).
3. **BE yang menentukan bentuk UI** (read-only vs editable), mobile merender sesuai hasil yang dikembalikan — mobile tidak boleh mengunci section berdasarkan tebakannya sendiri, supaya tidak ada dua sumber kebenaran untuk satu keputusan.

**Consumer logic (post-approval):**
- **Marker "ini eMOL reuse/vehicle-approval"**: `ReuseOrderNumber IS NOT NULL` **OR** `ReuseSAPOrderNumber IS NOT NULL` — bukan cek 1 field saja.
- **Sourcing `BacklogExecutionList.MONumber`**: kalau `ReuseSAPOrderNumber` terisi → pakai itu langsung. Kalau tidak (berarti `ReuseOrderNumber` yang terisi, `MONo` Order lama sudah diketahui) → ~~lookup `MechanicOrderList` via `ReuseOrderNumber` → ambil `SAPMOSyncOrder.MONo`-nya~~ **Resolved (2026-08-19):** `ReuseOrderNumber` diambil **langsung dari `PoolingMOItem.EMOLNumber`** (tidak perlu lookup `MechanicOrderList` — value-nya sama, [lihat sourcing di List Suggestion](#ui-view-detail--list-suggestion-order-lama-2026-08-14)). `MONo` **tetap** perlu lookup ke `SAPMOSyncOrder` atau `MOOpen.MONumber` — SAP MO Number tidak disimpan di `PoolingMOItem`.
- **~~Update balik ke Order lama~~ (isi `MONo` yang tadinya NULL) — tidak lagi punya pemicu (2026-08-19).** Syaratnya ada row `PoolingMOItem` untuk di-update (baris 1 & 2 di tabel atas), **dan** ada nilai untuk ditulis. Sejak input manual dihapus, baris 1 & 2 tidak pernah punya nilainya; sedangkan kandidat `MOOpen`-only dan escape hatch yang punya nilai justru tidak punya row untuk di-update. Tidak ada kondisi yang memenuhi keduanya.

**Resolved (2026-08-19, supersede aturan per-kondisi 2026-08-18) — Order Type/Activity Type/Material tidak lagi punya aturan sendiri per kondisi kandidat:** ketiganya memakai [tangga Sumber Data Order](#user-journey--defect-2026-08-13) yang sama. Yang berbeda antar kondisi cuma **tingkat mana yang tersedia**, bukan aturannya. Perlu dibaca per-field, karena tingkat 1 punya **dua tabel berbeda**: Order Type/Activity Type dari `MOOpen` (`CostTypeCode`, `MaintenanceCategoryCode`/`Name`), Material dari `CheckPartOrder` — keduanya tidak saling menggantikan. Untuk kandidat genuinely `MOOpen`-only (tidak punya `PoolingMOItem` sama sekali): row `MOOpen` pasti ada, tapi itu **tidak berarti ketiga field dapat tingkat 1** — `MaintenanceCategoryCode` bisa NULL dan `CheckPartOrder` bisa tidak punya row. Tingkat 2 tidak pernah tersedia untuk kondisi ini karena tidak ada row di `maintenance-order`, jadi field yang kosong di tingkat 1 langsung jatuh ke tingkat 3.

**Yang berubah dari aturan lama:** ~~Material `CheckPartOrder` kosong → fallback manual/editable, user declare sendiri, submit tetap lolos~~ — sekarang jatuh ke tingkat 3 dan `NoPartsRequired=No` di situ **blocking** ([lihat beda jenis blocking](#user-journey--defect-2026-08-13)). Prinsip lama "sistem tidak pernah block submit karena data tidak lengkap" **tidak lagi berlaku utuh** untuk material — tapi block-nya resolvable di tempat oleh mechanic, jadi bukan obstruksi.

**Code space terkonfirmasi sama (2026-08-19, dicek ke data PRD `MOOpen`):** `MOOpen.CostTypeCode` (mis. `MT01`) dan `MOOpen.MaintenanceCategoryCode` (mis. `BEX`, `CMT`) memang satu code space dengan `MechanicOrderList.CostTypeCode`/`ActivityTypeCode` **dan** turunannya di `PoolingMOItem.MOType`/`PMActType` (`MOType` di-copy dari `mol.CostTypeCode` saat insert staging) — konsisten dengan `BEX` yang dipakai sebagai fallback configurable `ActivityTypeCode` di [Poin 12](#poin-12-saperp-integration), dan dengan arah kirim Digiman+ → SAP ([`MOType` dari `mol.CostTypeCode`](../../architecture/inspection-order/order-emol-sap-sync.md#52-bc-update-jika-ada-create-jika-tidak-ada--insert-ke-poolingmoitem), [`PMActType` dari `MechanicOrderList.ActivityTypeCode`](#poin-12-saperp-integration)). Tidak ada konversi format yang perlu disiapkan.

**Tapi `MaintenanceCategoryCode`/`Name` bisa NULL** di `MOOpen` meski row-nya ada (terlihat di data PRD, sementara `CostTypeCode` terisi di semua row sampel). Untuk `Type='Form'`, Activity Type **mandatory & divalidasi di Submit** ([lihat sourcing `PMActType`](#poin-12-saperp-integration)) — jadi NULL di tingkat 1 tidak boleh dibiarkan kosong: A1 turun ke tingkat 2 (`PoolingMOItem.PMActType`), A2/A-manual turun ke tingkat 3 (user pilih sendiri). Fallback configurable `BEX` di [Poin 12](#poin-12-saperp-integration) **tidak dipakai di sini** — itu jaring pengaman untuk `Type='Inspection'`/`Additional`, bukan untuk `Type='Form'`.

### Poin 7: Editability Window Sebelum Approval

**Resolved (2026-08-15):** ya, mechanic **bisa edit** Finding miliknya sendiri (mis. salah ketik Defect Notes) setelah submit, tapi sebelum diproses Planner. Entry-point-nya **sama** dengan [tampilan post-submit](#current-state--mobile-app-ui-v400) — tap icon kaca pembesar (model 3-state — merah/oranye solid sesuai warna Condition saat sudah submitted, [lihat detail](#current-state--mobile-app-ui-v400)) di row **Form Task** (bukan "Bank Task"/"Task" — [lihat koreksi terminologi](#current-state--mobile-app-ui-v400)), navigasi balik ke screen "Defect Identified" yang sudah terisi — **detail behavior begitu landing di-refine di bawah (2026-08-17)**, tidak selalu "langsung editable" seperti draft awal kalimat ini.

**Resolved (2026-08-17) — batas window edit:** edit **lock begitu tier pertama Order-approval chain sudah memproses** (bukan tier akhir) — jawaban lengkap & alasan arsitekturnya (termasuk topic arah balik `maintenance-order`→`maintenance-execution` yang jadi konsekuensinya) ada di [Poin 5](#poin-5-data-flow-defect-dan-crack). Form-approval (Foreman/Supervisor) **tidak** relevan sebagai checkpoint lock di sini — 2 jalur approval tetap independen ([lihat Poin 9](#poin-9-approval-flow)); yang mengunci window edit spesifik adalah Order-approval.

**Resolved (2026-08-17) — siapa yang bisa edit:** creator Finding sendiri (`IAMS_Mobile_DefectCrack_Edit`), atau orang lain dengan permission `IAMS_Mobile_DefectCrack_Edit_Others` (mis. Supervisor bantu selesaikan transaksi mandek) — detail lengkap & rasional permission code ada di [Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15). Berlaku sama baik online maupun offline (mekanisme tulis identik, cuma beda gate akses).

**Resolved (2026-08-17) — behavior reopen, beda tergantung status Draft vs Submitted:** karena dalam 1 layar bisa ada >1 Tab Finding dengan status **berbeda-beda** (Finding #1 sudah submitted, Finding #2 masih draft, independen satu sama lain), status & behavior-nya harus per-Tab, bukan 1 status level-layar:

- **Draft** (`IsDraft=1`) → landing **langsung editable** (bukan view-mode dulu) — beda dari submitted di bawah. Alasan: draft secara definisi memang "belum selesai", risiko "kesentuh tidak sengaja" jauh lebih kecil dibanding data yang sudah final, dan tujuan buka draft hampir pasti untuk lanjut isi, bukan sekadar lihat.
- **Submitted, belum lock** (`IsDraft=0`, belum lewat tier pertama Order-approval, [lihat batas window di atas](#poin-7-editability-window-sebelum-approval)) → landing **view-only dulu** (read-only, semua field termasuk section Order Type/Activity Type/Part ditampilkan apa adanya sesuai kondisi submit — read-only kalau hasil reuse, atau read-only-view-of-manual-input kalau Order baru), tombol **Edit** & **Delete** ([Poin 8](#poin-8-cancel-atau-delete-finding)) muncul untuk masuk mode edit/delete. Alasan view-first: cegah user tidak sengaja mengubah data cuma karena mau **lihat** submission-nya — makin relevan sekarang ada `_Edit_Others`/`_Delete_Others` ([Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15)), lebih banyak orang bisa buka Finding orang lain.
- **Submitted, sudah lock** (lewat tier pertama Order-approval) → view-only, tombol Edit/Delete **hilang**, diganti pesan status.

**Resolved (2026-08-17) — tombol Cancel/Discard eksplisit saat mode Edit:** begitu tap Edit (masuk mode edit dari view-only di atas), butuh tombol **"Cancel"** eksplisit (selain "Save"/submit ulang) untuk **batal/discard** perubahan ([outcome yang sudah ditetapkan di Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15)) — kembali ke state submitted terakhir, tidak ada perubahan tersimpan, kembali ke mode view-only. Sebelumnya trigger UI-nya belum pernah didesain meski outcome-nya sudah disebut. **Butuh UI designer** untuk layout & posisinya.

**Resolved (2026-08-17) — fallback Activity Type kosong ([Poin 1](#user-journey--defect-2026-08-13)) mengikuti view/edit mode di atas, bukan enabled terus-menerus:** kasus reuse Order lama yang tidak punya `ActivityType` terisi bikin field itu **jadi enabled** meski sisa section-nya read-only — ini **cuma berlaku saat mode Edit** (bukan saat landing pertama di view-only, membingungkan kalau 1 field enabled di tengah state yang seharusnya semua read-only). Jadi: **view-only** → field ini juga ikut read-only sama seperti sisanya; **masuk mode Edit** → field ini kembali enabled sesuai fallback rule aslinya, field reuse-derived lain tetap read-only ([material saat reuse tetap read-only, edit di-defer](#poin-5-data-flow-defect-dan-crack)).

**Placement status Draft/Submitted — 2 tingkat:**
1. **Di Tab selector-nya sendiri** (step 1 [Struktur Screen](#struktur-screen-defect-identified), "Tab Finding #1/#2/...") — badge/label kecil per tab, supaya user bisa lihat status semua Finding sekilas tanpa buka satu-satu.
2. **Di dalam konten tab yang lagi aktif** — status chip/label di bagian atas konten (di bawah Tab selector, sebelum step 2 "Identitas user"), lebih detail: *"Draft"* / *"Submitted — pending review"* / *"Reviewed — locked"*.

**Catatan (2026-08-17) — butuh UI designer:** behavior & placement di atas sudah didefine lengkap, tampilan visual persis (styling badge/chip, layout Edit/Delete button, transisi view↔edit) **belum ada, perlu UI designer** untuk finalisasi — konsisten pola note lain di dokumen ini.

**Resolved (2026-08-17) — edit BISA mengubah pilihan reuse Order lama, bukan cuma field non-Order:** confirmed — selama masih dalam window edit (belum lock, [lihat batas window di atas](#poin-7-editability-window-sebelum-approval)), user boleh re-run "Check Existing", ganti kandidat reuse yang sudah dipilih, batalkan reuse (jadi Order baru), atau sebaliknya (dari tidak-reuse jadi reuse) — **tidak dibatasi cuma field non-Order** seperti Defect Notes. Konsekuensi: setiap kali `ReuseOrderNumber` berubah lewat edit, berlaku validasi ulang yang sama dengan submit pertama kali (kandidat harus masih `IsActive=1` di titik submit-edit, [terkait langsung ke edge case validasi stale-candidate](#poin-6-duplicate-atau-correlation-handling)) — bukan cuma dicek sekali di awal.

**Resolved (2026-08-19) — validasi reuse diperluas jadi 4 validasi, dan titiknya ditentukan oleh siapa yang bisa menindaklanjuti.** Yang tertulis di atas baru mencakup **satu** validasi (kandidat stale) dan cuma untuk jalur mechanic. Prinsipnya: **block hanya berguna di depan orang yang bisa menyelesaikannya** — block yang tidak actionable adalah obstruksi murni, karena user tidak punya informasi baru untuk diberikan.

| Validasi | Resolvable oleh | Titik |
|---|---|---|
| Kandidat stale (`IsActive=1`, belum masuk `BacklogExecutionList`) | Mechanic — re-run Check Existing, pilih lain, atau lanjut Order baru | Submit pertama, submit edit mechanic, Save approver |
| Material resolvable (lihat [tangga Sumber Data Order](#user-journey--defect-2026-08-13)) | Mechanic — input material manual | Submit pertama, submit edit mechanic, Save approver |
| Konsistensi field reuse (`ReuseOrderNumber` ↔ `ReuseSAPOrderNumber` menunjuk Order sama) | Sistem | Semua titik tulis |
| **`MONo` terisi** (kalau `IsImmediateExecutable=Yes`) | **Hanya approver** | **Final approval** |

**Kenapa `MONo` pindah dari submit mechanic ke approver — dua alasan, dan soal sinyal bukan yang utama:**

1. **Block di submit memaksa mechanic memalsukan catatan.** `IsImmediateExecutable` adalah **pernyataan fakta** (perbaikan sudah/sedang dikerjakan saat itu juga), bukan permintaan. Jalan keluar dari block-nya adalah "uncheck" — artinya menyuruh mechanic mencatat bahwa ia **tidak** mengerjakan pekerjaan yang sudah ia kerjakan. Tidak ada block lain di dokumen ini yang menuntut hal seperti itu.
2. **Mechanic tidak bisa menyelesaikannya.** Tidak ada aksi apa pun di lapangan yang membuat `MONo` datang lebih cepat. Approver bisa menunggu lalu mencoba approve lagi, atau memakai escape valve secara sadar. Mechanic tidak punya dua opsi itu — begitu submit, eMOL sudah lepas dari tangannya.

**Aturan turunan — dua peran `IsImmediateExecutable`.** Field ini memikul catatan fakta eksekusi **sekaligus** trigger TECO. Karena itu menurunkannya ke `No` punya dua arti yang berbeda, dan approver harus sadar sedang melakukan yang mana:

| Alasan approver menurunkan `IsImmediateExecutable` | Boleh? | Akibat |
|---|---|---|
| Mechanic salah declare — ternyata tidak dikerjakan saat itu | **Ya**, ini koreksi fakta | Tidak ada; catatannya memang jadi benar |
| `MONo` belum datang, approval tertahan | **Ya, sebagai escape valve** — supaya approval tidak pernah buntu total | Catatan fakta jadi tidak akurat, **dan** Order lama tetap open di SAP lalu muncul lagi sebagai outstanding backlog untuk pekerjaan yang fisiknya sudah selesai |

Dari sisi UI dua aksi ini identik, jadi **wajib ada pop-up konfirmasi** yang menyebut konsekuensinya, bukan sekadar "Are you sure?". Usulan copy:

> *"Turning this off will record the repair as not executed immediately. The Order will stay open and may reappear as outstanding backlog — even though the work is already done. Continue only if this is what you intend."*

**Open item (2026-08-19) — visibilitas eMOL yang menggantung.** Kalau `MONo` tidak pernah datang karena sync tersendat, approver **tidak punya cara tahu harus menunggu berapa lama** — dari layarnya, sync yang telat sebentar dan sync yang genuinely stuck terlihat sama. **Tidak buntu** (escape valve di atas selalu tersedia), tapi tanpa visibilitas approver akan cenderung memakai escape valve padahal cukup menunggu sebentar lagi — dan escape valve itulah yang menghasilkan catatan tidak akurat plus Order lama yang muncul lagi sebagai outstanding backlog. **Sifatnya sama dengan sync tersendat lainnya, jadi masuk monitoring umum, bukan desain khusus fitur ini.** Sejalan dengan itu: notifikasi in-app/email memang [out of scope Phase 2](#poin-8-cancel-atau-delete-finding), dan jalur perbaikan manual (input `MONo` oleh user) sudah dihapus di [Poin 6](#poin-6-duplicate-atau-correlation-handling) — jadi di dalam fitur ini tidak ada deteksi maupun perbaikan; keduanya bersandar ke monitoring umum. Residual sejenis sudah dicatat untuk scheduler B2 ([Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)).

Memecah field jadi dua (fakta vs trigger) sengaja **tidak** diambil di Phase 2 — itu mengembalikan kebutuhan menahan TECO sampai `MONo` datang, lengkap dengan watcher, retry, dan eskalasi. Terlalu mahal untuk kasus sesempit ini. Di luar baris 3 matrix ([Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)) dual-role-nya tidak pernah aktif: A2 dan A-manual selalu punya `MONumber`, B1/B2 mendapatkannya dari create-response.

**Resolved (2026-08-18) — mekanisme ganti kandidat reuse ke `TaskPersonalizedFindingMaterial`: hard delete baris lama, insert ulang (bukan diff/update per-baris):** begitu user ganti kandidat reuse (atau batalkan reuse jadi manual, atau sebaliknya), seluruh row `TaskPersonalizedFindingMaterial` lama untuk Finding itu **dihapus (hard delete)**, lalu baris baru di-insert sesuai kandidat/isian yang baru. **Alasan:** Material 1-to-many dengan jumlah baris yang bisa beda-beda antar kandidat (mis. Order A 3 baris material, Order B 5 baris) — matching/diff per-baris antar kandidat lama vs baru tidak ada gunanya, baris lama cuma snapshot turunan dari kandidat yang sedang dipilih saat itu, bukan entitas yang perlu di-track individual. Konsisten dengan prinsip **simple-mechanism/full-overwrite** yang sudah dipegang di seluruh dokumen ini (mis. race condition last-write-wins tanpa merge/diff, [lihat Poin 5](#poin-5-data-flow-defect-dan-crack)) — **hard delete cukup**, tidak perlu soft-delete (`IsActive`/reason) untuk baris Material transisional ini, beda dari soft-delete Finding-level di [Poin 8](#poin-8-cancel-atau-delete-finding) yang memang butuh audit trail. **Berlaku simetris di consumer `maintenance-order`** saat event hasil edit di-consume — `MechanicOrderMaterial` lama untuk eMOL itu di-replace dengan pola yang sama (delete+reinsert), bukan diff per-baris.

**Catatan — batasan scope vs Poin 10 (Reject/rework), bukan open item Poin 7 (2026-08-17):** Poin 7 di atas cuma cover mechanic **inisiatif sendiri** edit/delete Finding-nya (lewat Edit/Delete, [Poin 8](#poin-8-cancel-atau-delete-finding)) **sebelum** ada approver yang bertindak — sudah **fully resolved**, tidak ada open item tersisa untuk Poin 7 sendiri. **Poin 10 itu trigger yang beda sama sekali** — approver (Supervisor/Planner) **aktif menolak** Finding/Order saat review, bukan aksi mechanic — masih kosong total, open item-nya tercatat di **checklist item 10 sendiri**, bukan digantung di sini.

---

### Poin 8: Cancel atau Delete Finding

**Resolved (2026-08-17) — Delete (soft), bukan Cancel:** pembatalan total Finding (mechanic salah identifikasi/false positive) direalisasikan sebagai **soft-delete** — flip `IsActive=0` + isi `DeleteNotes` (`TaskPersonalizedFinding`) — **`DeleteNotes` diketik user di confirmation dialog dan bersifat OPSIONAL (2026-08-19)**, jadi boleh NULL; detail kontrolnya di [confirmation dialog di bawah](#poin-8-cancel-atau-delete-finding) — **bukan** hard delete maupun status "Cancelled" terpisah. **Skema sudah ada, tidak perlu kolom baru** — dikonfirmasi real di kedua sisi: `TaskPersonalizedFinding.DeleteNotes`+`IsActive` ([maintenance-execution-schema.md](../../architecture/database/maintenance-execution-schema.md)), `MechanicOrderList.DeleteReason`+`IsActive` ([maintenance-order-schema.md](../../architecture/database/maintenance-order-schema.md)) — soft-delete via `IsActive` sudah jadi pola konsisten di hampir semua tabel di kedua service.

**Resolved (2026-08-17) — permission, sama pola dengan Edit ([Poin 4](#poin-4-offline-behavior--draft-state-2026-08-15)):**
- **`IAMS_Mobile_DefectCrack_Delete`** — hapus Finding milik sendiri (creator).
- **`IAMS_Mobile_DefectCrack_Delete_Others`** — hapus Finding milik orang lain (mis. Supervisor bantu selesaikan transaksi mandek), **parent**-nya `IAMS_Mobile_DefectCrack_Delete` (pola hierarkis sama dengan permission Edit).

**Catatan (2026-08-17) — posisi tombol Delete belum ditentukan, butuh UI designer:** beda dari Edit ([lihat Poin 7](#poin-7-editability-window-sebelum-approval)) yang entry-point-nya sudah jelas (reuse navigasi icon existing), tombol/affordance **Delete belum punya tempat sama sekali** di desain UI saat ini — apakah di dalam screen "Defect Identified" (mis. icon trash di header/dekat Save), per-Tab-Finding (mis. swipe-to-delete di Tab Finding list), atau context menu terpisah — semuanya masih opsi terbuka, perlu UI designer untuk menentukan & finalisasi (sama seperti [confirmation dialog di atas](#poin-8-cancel-atau-delete-finding), ini juga soal tampilan, bukan mekanisme).

**Resolved (2026-08-17) — timing/lock, sama persis dengan Edit:** window delete **lock begitu tier pertama Order-approval chain sudah memproses** ([sama checkpoint dengan Poin 7](#poin-7-editability-window-sebelum-approval)) — bukan mekanisme terpisah. Setelah lock, tidak ada delete self-service lagi (perlu jalur approver/Poin 10, di luar scope ini).

**Resolved (2026-08-17) — sync/offline/race condition, sama mekanisme dengan Edit ([Poin 5](#poin-5-data-flow-defect-dan-crack)) dengan 1 pengecualian penting:** delete **bukan** konflik konten seperti edit-vs-edit (yang dibandingkan by `ModifiedAt`, [lihat Poin 5](#poin-5-data-flow-defect-dan-crack)) — delete itu mutasi **1 flag yang monoton & final** (begitu delete, tidak ada "dibatalkan" oleh edit yang lebih basi/lebih baru). Aturannya: **delete selalu ter-apply kapan pun dia sampai server**, terlepas timestamp atau urutan kedatangan dibanding edit yang bersaing — tapi **cuma flag delete yang disentuh** (`IsActive`/`DeleteNotes`), tidak full-overwrite field lain.

2 skenario konkret:
- **Delete sampai server duluan, edit menyusul** → edit sukses tanpa update apapun + pesan (beda dari pesan conflict generik edit-vs-edit, [lihat Poin 5](#poin-5-data-flow-defect-dan-crack) — ini eksplisit soal delete, bukan "ada versi lebih baru"):
  - Full (response API/dialog): *"This defect/crack has already been deleted by someone else. Your changes weren't applied."*
  - Toast (ringkas): *"This defect was already deleted. Your edit wasn't saved."*
- **Edit sampai server duluan (ter-apply), delete menyusul meski `ModifiedAt` delete lebih lama** → delete **tetap berhasil**, cuma update flag — konten tetap versi edit yang sudah tersimpan, statusnya jadi deleted.
- **Delete-vs-delete** (2 aktor delete Finding yang sama) → trivial idempotent, yang kedua datang no-op sukses (flag sudah `0`).

**Resolved (2026-08-17) — feedback setelah delete berhasil:** toast singkat *"Deleted"*, lalu **otomatis navigasi balik** ke Tab Finding list ([lihat filter+renumber](#current-state--mobile-app-ui-v400)) — Finding yang baru dihapus tidak lagi muncul di list itu.

**Resolved (2026-08-17) — cascade ke `maintenance-order`:** delete **lewat topic/publish yang sama** dengan edit (bukan channel terpisah, [lihat Poin 5](#poin-5-data-flow-defect-dan-crack)) — consumer set `MechanicOrderList.IsActive=0`+`DeleteReason` (dari `DeleteNotes`, **bisa NULL kalau user tidak mengisi alasan** — `IsActive=0` yang jadi sinyal delete-nya, bukan terisinya `DeleteReason`). Karena grouping eMOL **1:1** per Finding — tidak ada `MechanicOrderList` lain yang gantung ke `MechanicOrderSummary` yang sama — **`MechanicOrderSummary.IsActive` ikut di-set `0` juga**, bukan cuma List-nya, karena Summary itu eksis semata-mata untuk Finding ini.

**Resolved (2026-08-17) — cascade ke child table eMOL, bukan cuma List+Summary:** `MechanicOrderDetail`/`MechanicOrderMaterial`/`MechanicOrderCrackIdentified`/`MechanicOrderEvidence` (semua child yang nempel ke `MechanicOrderList` yang di-delete) **ikut di-flip `IsActive=0` juga**, eksplisit — bukan cuma andalkan join ke status parent (`MechanicOrderList`). Alasan: lebih aman dari bug "lupa cek status parent" di query masa depan, dan cost-nya kecil (sudah dalam 1 transaction consumer yang sama dengan update List/Summary di atas).

**Resolved (2026-08-17) — Finding yang masih draft (belum pernah submit):** delete cukup **local/execution-side saja**, tidak ada cascade — belum pernah publish ke topic sama sekali (`IsDraft` belum pernah `0`), jadi tidak ada eMOL yang perlu disentuh di `maintenance-order`.

**Konsekuensi ke Poin 6 — resolved:** menjawab [open item lama di Poin 6](#poin-6-duplicate-atau-correlation-handling) soal state Rejected/Cancelled di `MechanicOrderList` — `IsActive=0` dari mekanisme delete ini yang jadi state tersebut; filter candidate-scope correlation perlu syarat `IsActive=1` eksplisit.

**Feedback ke user saat konflik (2026-08-17, resolved):** pesan "sudah dihapus orang lain"/dkk itu **response API synchronous**, muncul cuma pas user aktif coba sync/submit saat itu juga (inline UI, mis. toast/banner). Tidak perlu mekanisme baru, sudah cukup dari response yang sudah didesain.

**Resolved (2026-08-17) — konfirmasi sebelum delete, jadi mitigasi utama (bukan mekanisme restore):** karena tidak ada undelete/restore, delete **wajib lewat confirmation dialog** dulu sebelum action jalan — cukup sebagai mitigasi, **tidak perlu** bangun mekanisme restore terpisah (konsisten prinsip "manusia validasi di titik krusial" yang dipegang di seluruh dokumen ini). Copy beda tergantung konsekuensi cascade-nya (supaya user paham dampak sebenarnya, bukan pesan generik):

**Resolved (2026-08-19) — alasan delete diketik user, tapi TIDAK mandatory:** dialog menyediakan satu field free text opsional; kalau dikosongkan, `DeleteNotes` (dan `DeleteReason` turunannya di `maintenance-order`) tetap NULL dan delete **tetap jalan**. Alasan tidak dimandatorikan: delete adalah aksi koreksi yang harus tetap ringan di lapangan — memaksa mengetik akan mendorong user mengisi asal-asalan, yang lebih buruk daripada kosong. Yang wajib tetap **konfirmasinya**, bukan alasannya. Beda dari `Approval Remark` saat reject ([Poin 10](#poin-10-rejectrework-flow)) yang **mandatory** — di sana approver membatalkan pekerjaan orang lain, jadi alasannya bagian dari akuntabilitas.

- **Finding masih draft** (belum pernah submit, tidak ada eMOL terkait):
  - Title: *"Delete this draft?"*
  - Body: *"This draft will be permanently deleted. This can't be undone."*
  - Input: **Reason — opsional**, free text. Label *"Reason (optional)"*, placeholder *"Why are you deleting this?"*
  - Buttons: **Cancel** / **Delete**
- **Finding sudah submitted** (ada eMOL/Order terkait, [lihat cascade](#poin-8-cancel-atau-delete-finding)) — **revisi copy (2026-08-17)**, hindari istilah "order" (bukan mental model mechanic, [konsisten alasan penamaan tombol "Check Existing Defect"](#user-journey--defect-2026-08-13)):
  - Title: *"Delete this defect/crack?"*
  - Body: *"This defect has already been submitted and may be in the approval process. Deleting it will cancel it completely. This can't be undone."*
  - Input: **Reason — opsional**, free text. Label *"Reason (optional)"*, placeholder *"Why are you deleting this?"*
  - Buttons: **Cancel** / **Delete**

**Catatan (2026-08-17):** copy & struktur (title/body/button) di atas itu konten/wording-nya saja — **tampilan visual dialog ini mengikuti existing design system Digiman+** (komponen dialog/modal yang sudah ada), **butuh UI designer** untuk finalisasi layout/style-nya, bukan didesain dari nol di sini.

**Out of scope (2026-08-17) — notifikasi (in-app/email):** seluruh scope terkait sistem notifikasi (push/in-app/email) **dihapus dari dokumen ini** — belum ada mekanisme notifikasi apapun di app hari ini, tidak dibahas di Phase 2 ini. Lihat juga catatan di [checklist](order-integration-checklist.md).

---

## Fase D — Proses/Workflow

### Poin 9: Approval Flow

**⚠️ Catatan terminologi (2026-08-17) — "Foreman/Supervisor" dan "Planner" di dokumen ini adalah shorthand untuk tingkat AKHIR dari approval chain, bukan aktor tunggal yang fixed:** dari [Fase B](#fase-b--aktor) — akses Digiman+ berbasis **permission code** (config), bukan hardcoded role, dan jumlah tingkat approval **configurable** (Form Approval kemungkinan `Supervisor` saja sebagai tingkat akhir, Order Approval kemungkinan **`Supervisor → Planner`**, 2 tingkat — masih perlu konfirmasi BPO client soal jumlah tingkat persisnya). Ini konsisten dengan frasa "berjenjang" yang sudah dipakai untuk Form Approval sejak awal — bukan kontradiksi baru, cuma belum eksplisit sebelumnya. **Implikasi ke seluruh dokumen ini:** setiap kali disebut "Planner approval"/"lewat Planner", baca sebagai **"approval chain mencapai tingkat akhir (final approval)"** — trigger downstream (`BacklogExecutionList`, sync SAP) terjadi saat chain **fully approved**, bukan terikat ke identitas aktor spesifik atau jumlah tingkat tertentu. Desain di dokumen ini **tidak bergantung** pada berapa tingkat approval-nya — 1 tingkat atau 2 tingkat sama-sama valid tanpa perubahan mekanisme.

#### Form Approval — sampai tingkat akhir (Supervisor)

Form (termasuk Finding/Defect di dalamnya) melalui approval berjenjang sampai tingkat akhir — **Supervisor** (lihat catatan terminologi di atas soal kemungkinan tingkat sebelumnya/Foreman).

#### Defect Biasa — Lanjut Jadi Order di SAP Tergantung Order Approval

Defect dibuat oleh **mechanic**, termasuk pengisian **material**. Apakah defect ini **dilanjutkan jadi Order di SAP** ditentukan oleh **Order Approval chain** (tingkat akhir: Planner, [lihat catatan terminologi](#poin-9-approval-flow)) — itu yang jadi gate approval Order sebelum push ke SAP.

> **Resolved (2026-08-13):** untuk Skenario 2 critical di [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack), gate Planner **tetap berlaku, tidak ada bypass** — approval cuma didekopel dari eksekusi fisik (non-blocking), bukan dihilangkan. Detail per sub-kasus (Order lama ada / tidak ada, butuh material atau tidak) ada di Poin 1.
>
> **✅ Dikuatkan (2026-08-15, final setelah beberapa kali revisi):** ini berlaku untuk **SEMUA** sub-kasus, **termasuk Sub-kasus A (reuse)** — sempat disimpulkan Sub-kasus A tidak perlu Planner approval sama sekali (karena tidak ada eMOL baru), tapi ini menghilangkan safety net atas keputusan reuse mechanic di lapangan (**korektif, bukan preventif-total** — ([batas maknanya di Poin 5](#poin-5-data-flow-defect-dan-crack))). **Keputusan final: Sub-kasus A JUGA membentuk eMOL baru** ("vehicle approval", full snapshot data dari Order lama — lihat [Poin 5](#poin-5-data-flow-defect-dan-crack)) yang lewat Planner approval seperti biasa — bedanya cuma di **behavior post-approval** (Sub-kasus A trigger `BacklogExecutionList` ke Order lama, bukan sync SAP sebagai MO baru — supaya tidak duplicate).

**Form Approval & Order Approval — 2 jalur independen, bukan nested (2026-08-15, keputusan MVP):** dikonfirmasi user — **Form approval** (Foreman/Supervisor, di atas) dan **Order approval** (Planner, existing pipeline untuk eMOL) itu **2 jalur terpisah yang jalan sendiri-sendiri**, bukan "Form Approval yang di dalamnya ada approval per-Order". **Berlaku untuk SEMUA sub-kasus** (A/B1/B2) — Order approval Planner + Form approval Foreman/Supervisor jalan independen/paralel untuk Finding manapun yang trigger eMOL.

**⚠️ REVERSED TOTAL (2026-08-16) — menjawab ulang open item lama soal "apakah reuse+`No` butuh approval baru" ([User Journey — Defect](#user-journey--defect-2026-08-13), [Crack Journey](#poin-5-data-flow-defect-dan-crack)):** keputusan sebelumnya ("cabang `No`+reuse tetap tidak ada Order-approval baru, cuma Form approval") **dibalik total**. Alasan (dari user): **apapun** defect/crack yang dihasilkan mechanic/foreman saat mengisi/eksekusi form, harus ada approval — untuk validasi 3 keputusan: benar reuse Order lama atau tidak, executed sekarang atau tidak, butuh material atau tidak. Keputusan itu **tanggung jawab level supervisor/planner**, bukan self-declared mechanic tanpa oversight independen.

**Keputusan final:** cabang `No`+reuse **SEKARANG JUGA membentuk eMOL baru** ("vehicle approval", mekanisme sama persis dengan `Yes`+reuse — [lihat Poin 5](#poin-5-data-flow-defect-dan-crack)) dan lewat Order-approval Planner. Jadi **setiap kombinasi reuse** (Yes maupun No) selalu bikin eMOL + Order-approval — tidak ada lagi cabang yang skip Order-approval karena alasan "belum dieksekusi sekarang". Bedanya cuma di **post-approval action**:
- `Yes` → trigger `BacklogExecutionList` ke Order lama (TECO jalan).
- `No` → **tidak ada aksi lanjutan** — eMOL cuma jadi record bahwa Planner sudah approve/validasi, Order lama tetap open apa adanya.

Baik `Yes` maupun `No` di kasus reuse **sama-sama skip sync SAP/`PoolingMOItem`** (mencegah duplicate candidate — alasan yang sama seperti sebelumnya, [lihat Poin 6](#poin-6-duplicate-atau-correlation-handling)).

**Deferred (2026-08-17, sebelumnya "Masih open" 2026-08-13) — ke next MVP:** UI approval — bagaimana SPV/Planner **melihat & bertindak** atas Order yang statusnya "sudah dieksekusi, approval post-hoc", termasuk apakah perlu indikator visual yang beda dari Order normal yang belum dieksekusi (relevan untuk Sub-kasus A & B1) — di-defer, bukan scope Phase 2 ini. Untuk Phase 2, approver tetap lihat data lewat layar view/edit standar ([lihat User Journey Approval Order di bawah](#poin-9-approval-flow)) tanpa indikator khusus post-hoc.

**Resolved (2026-08-17) — User Journey Approval Order:**

1. **1 Finding defect/crack = 1 Order = 1 approval** — grouping tetap konsisten dengan prinsip 1:1 yang sudah dipegang sejak [Poin 5](#poin-5-data-flow-defect-dan-crack), sekarang eksplisit dikonfirmasi berlaku juga di level approval (bukan cuma create eMOL).
2. **Layar approval default view-only, ada tombol Edit** — pola **sama persis** dengan reopen flow mechanic ([lihat Poin 7](#poin-7-editability-window-sebelum-approval)): approver landing di tampilan read-only dulu, baru tap **Edit** untuk masuk mode edit.
3. **Approver bisa edit SEMUA field yang diisi mechanic/foreman, di level approval manapun** (bukan cuma tier akhir) — alasan: approver adalah **gate terakhir yang menentukan validitas data** defect/crack — dalam arti **korektif**, yaitu berwenang mengubah nilai apa pun sebelum Approve, bukan berarti bisa menolak eMOL-nya ([batas maknanya di Poin 5](#poin-5-data-flow-defect-dan-crack)) — jadi tidak dibatasi cuma field non-Order seperti window edit mechanic ([beda dari Poin 7](#poin-7-editability-window-sebelum-approval), yang scope edit mechanic-nya dibatasi window sebelum lock). Termasuk `ReuseOrderNumber` ([lihat poin validasi di bawah](#poin-6-duplicate-atau-correlation-handling)).
   - **Resolved (2026-08-19) — menurunkan `IsImmediateExecutable` untuk melepas approval yang tertahan karena `MONo` belum datang wajib melewati pop-up konfirmasi** yang menyebut konsekuensinya, bukan sekadar "Are you sure?" — copy & alasannya di [Poin 7](#poin-7-editability-window-sebelum-approval). Dari sisi UI, aksi ini identik dengan koreksi fakta (mechanic salah declare), padahal akibatnya berbeda total.
   - **Resolved (2026-08-19) — mengubah `ReuseOrderNumber` memicu re-derive**, bukan sekadar mengganti satu field. Order Type, Activity Type, dan Material di-derive ulang dari Order yang baru lewat [tangga Sumber Data Order](#user-journey--defect-2026-08-13). Tanpa ini, `MechanicOrderList` (Order Type/Activity Type), `MechanicOrderMaterial` (Material), dan `MechanicOrderDetail` (Component/SubComponent/DamageCode dkk) tetap berisi snapshot Order **lama** sementara `ReuseOrderNumber` sudah menunjuk Order **lain** — eMOL jadi menggambarkan dua Order sekaligus. Mekanisme replace-nya mengikuti pola hard delete + insert ulang yang sudah ditetapkan di [Poin 7](#poin-7-editability-window-sebelum-approval), bukan diff per-baris.
   - **Tiga validasi tulis juga jalan di titik Save approver** — kandidat stale, material resolvable, dan konsistensi field reuse ([tabel validasi di Poin 7](#poin-7-editability-window-sebelum-approval)). Save approver adalah titik tulis penuh, bukan pengecualian.
4. **Mode Edit ada tombol Cancel/Discard dan Save** — konsisten pola yang sama dengan mode edit mechanic.
5. **Cancel/Discard maupun Save, keduanya balik ke mode view** — dari situ approver klik **Approve** sebagai aksi **terpisah** (bukan otomatis ter-approve begitu Save). Edit dan Approve adalah 2 aksi berbeda.
6. **Update balik ke `maintenance-execution` terjadi tiap aksi Approve** (bukan tiap Save) — lewat topic arah balik yang **sama** dengan flag lock ([lihat topic diperluas di Poin 5](#poin-5-data-flow-defect-dan-crack)), payload-nya bawa data hasil edit approver (kalau ada). Kalau chain approval >1 tier, tiap tier yang Approve trigger publish-nya sendiri — supaya `maintenance-execution` selalu selaras dengan versi terakhir yang di-approve (bukan cuma tier terakhir).

**Konsekuensi ke gap #3 di bawah (Override `IsImmediateExecutable`) — resolved:** kalau approver edit field ini sebelum Approve, efeknya **ganda sekaligus** — jadi **catatan final** (approver gate terakhir validitas data — korektif, [lihat batas maknanya](#poin-5-data-flow-defect-dan-crack)) **dan** **menentukan post-approval action ke depan** (`Yes`→trigger `BacklogExecutionList`, `No`→tidak, [lihat Poin 5](#poin-5-data-flow-defect-dan-crack)) — bukan pilih salah satu, dua-duanya berlaku otomatis dari 1 aksi edit yang sama.

**Race condition baru — mechanic edit (sebelum lock) vs approver edit (sebelum Approve) di data yang sama, hampir bersamaan — resolved (2026-08-17):** beda dari race condition sesama mechanic/`_Others` ([symmetric last-edit-time-menang, lihat Poin 5](#poin-5-data-flow-defect-dan-crack)) — di sini **approver SELALU menang**, bukan dibandingkan `ModifiedAt`. Kalau edit mechanic yang telat sampai server (mis. sempat offline) ternyata sudah keburu di-Approve, edit itu **tidak di-apply**, response tetap sukses (bukan reject/requeue) + pesan status, konsisten pola locked-state yang sudah ada ([lihat Poin 7](#poin-7-editability-window-sebelum-approval)).

**Rincian tambahan (2026-08-16) — 3 gap konkret yang muncul dari pertanyaan "bagaimana approver tahu defect ini sudah dieksekusi atau belum":**

1. ~~Visibility — approver tidak punya sinyal status eksekusi sama sekali.~~ — **resolved sebagian (2026-08-16)**: klarifikasi semantik `IsImmediateExecutable` ([lihat diskusi](#poin-1-trigger-dan-ui-create-defect-atau-crack)) mengungkap field ini sebenarnya **pernyataan fakta eksekusi** ("mechanic sudah/sedang mengerjakan saat itu juga"), bukan cuma deklarasi niat/trigger routing — jadi genuinely relevan buat approver. Keputusan lama "tidak dibawa ke `MechanicOrderDetail`" **dibatalkan** — kolom baru `MechanicOrderDetail.IsImmediateExecutable` ditambahkan, tampil di [View Detail Order](#ui-view-detail--view-detail-order-2026-08-14). **Masih parsial** — Untuk Sub-kasus A/B1, eksekusi fisik tetap **non-blocking** (mechanic bisa langsung kerja tanpa nunggu approval, [Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)), jadi flag `Yes` ini laporan self-declared mechanic, bukan konfirmasi independen — approver sekarang **tahu klaimnya**, tapi belum bisa **verifikasi** (gap #2 di bawah).
2. **Deferred (2026-08-17) ke next MVP — Verifikasi, tidak ada mekanisme bukti perbaikan pasca-eksekusi.** Evidence/foto yang ada hari ini ([Struktur Screen "Defect Identified"](#struktur-screen-defect-identified)) itu evidence **defect** (kondisi sebelum diperbaiki), diambil saat Finding dibuat — tidak ada alur "upload bukti setelah diperbaiki" yang didesain. Bahkan kalau ada status "sudah dieksekusi" (poin 1), approver belum punya cara verifikasi visual selain percaya laporan mechanic. **Untuk Phase 2, approver mengandalkan laporan self-declared mechanic apa adanya** (tanpa mekanisme verifikasi tambahan) — dicatat sebagai limitasi yang diterima sementara, bukan blocking.
3. ~~Override — belum ada mekanisme approver mengubah determinasi `IsImmediateExecutable` di titik approval.~~ — **resolved (2026-08-17)**: approver **bisa edit field ini** (termasuk dalam "semua field" yang bisa diedit approver, [lihat User Journey Approval Order di atas](#poin-9-approval-flow)) — efeknya **ganda sekaligus**, jadi catatan final **dan** menentukan post-approval action ke depan, bukan pilih salah satu (definisi yang sebelumnya ambigu di paragraf ini sekarang terjawab tuntas).

---

### Poin 10: Reject/Rework Flow

**Deferred (2026-08-17) — fitur reject di approval DI-DEFER ke next MVP, bukan scope Phase 2 ini:** saat ini **tidak ada tombol/aksi reject** di approval UI (Form-approval maupun Order-approval) — approval Phase 2 bersifat **binary: pending → approved saja**, tidak ada cabang ditolak. Konsekuensi: [state icon "Rejected"](#current-state--mobile-app-ui-v400) yang sudah di-defer sebelumnya **tetap tidak perlu didesain** di Phase 2 ini — tidak ada trigger yang bisa memunculkannya.

**3 fakta yang sudah diputuskan sekarang (buat referensi next MVP, meski fitur reject-nya sendiri belum dibangun):**
- Kalau Finding/Order **rejected** (nanti, saat fitur ini dibangun) → **tidak sync ke SAP maupun `PoolingMOItem`** sama sekali.
- **Tidak bisa resubmit** — rejected bersifat final/terminal, bukan status yang bisa diperbaiki lalu diajukan ulang lewat mekanisme Phase 2 ini.
- **Alasan reject disimpan di `Approval Remark` (2026-08-19)** — field pada **aksi approval**, bukan pada Finding/Order-nya, dan **bukan** `DeleteReason` (itu milik soft-delete Finding, [Poin 8](#poin-8-cancel-atau-delete-finding)). Sengaja **general**, dipakai untuk aksi approval apa pun, bukan field khusus reject. Yang khusus reject hanya **kewajibannya**: reject **mewajibkan** approver mengisi remark (kenapa di-reject), sementara pada Approve remark tetap opsional. Bedakan dari Remark milik mechanic di level Form Task ([lihat Struktur Screen](#struktur-screen-defect-identified)) — beda pengisi, beda titik, beda tabel.

Detail lain (siapa yang bisa reject, UI-nya seperti apa, skema persis `Approval Remark`, dst) **belum dibahas sama sekali** — genuinely di luar scope sampai next MVP.

---

## Fase E — Integrasi

### Poin 12: SAP/ERP Integration

Baseline: [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) — flow existing (Order approved → build `PoolingMOItem` → `SAPMOSyncOrder` → publish `TopicPublishLog` → Service Bus → BAPI call → SAP create MO). **Sebagian besar flow ini tidak berubah untuk Phase 2** — eMOL reuse-vehicle **skip total** flow ini ([sudah established](#poin-5-data-flow-defect-dan-crack)), jadi yang genuinely tersentuh cuma eMOL dari cabang `ReuseOrderNumber` NULL (Order baru genuine).

**Resolved (2026-08-17) — sourcing `PMActType` untuk `Type='Form'`:** langsung dari `MechanicOrderList.ActivityTypeCode` (kolom baru per-eMOL, [lihat mapping](#poin-5-data-flow-defect-dan-crack)) — bukan cross-service/header seperti Inspection/Additional existing (Bagian 4.2 baseline). Untuk `Type='Form'` sendiri tidak butuh fallback NULL — mandatory (`*`) & divalidasi di Submit.

**Resolved (2026-08-17) — fallback `ActivityTypeCode` NULL:** value configurable `BEX` di tabel `Configuration` (bukan hardcoded). Bukan proteksi untuk `Type='Form'` (sudah mandatory & divalidasi) — ini jaring pengaman untuk `Type='Inspection'`/`Additional`: (1) query build PMActType (Bagian 5.2 baseline) dimodifikasi nambah cabang `Type='Form'`, menyentuh query shared yang mereka pakai juga — risiko regresi; (2) sourcing PMActType existing mereka sendiri masih flawed/lagi di-redesign ([maintenance-activity-type-enhancement.md](../../architecture/inspection-order/maintenance-activity-type-enhancement.md), belum rilis) — kemungkinan ke depan mereka konvergen pakai `ActivityTypeCode` yang sama, fallback ini relevan selama transisi itu.

**Resolved (2026-08-17) — query filter 5.1/5.2/5.4 (baseline) perlu cabang `Type='Form'`:** semua 3 query ini masih pattern `Type='Inspection'` ATAU `Type='Additional'`, belum ada `Type='Form'` — **diperluas** jadi `Type IN ('Inspection','Form')` di sisi filter `WorkOrderId`-nya (bukan cabang terpisah), karena `Type='Form'` strukturnya mirip Inspection (`WorkOrderId` terisi). Berlaku untuk ketiganya (5.1 lookup `PoolingId`, 5.2 build insert `PoolingMOItem`, 5.4 create `SAPMOSyncOrder`) — sebelumnya cuma 5.1/5.2 yang ke-flag di [Poin 5](#poin-5-data-flow-defect-dan-crack), sekarang 5.4 ditambahkan juga.

**Catatan — bukan gap baru, sudah aman (2026-08-17):** gap existing "`Component`/`SubComponent`/`DamageCode` tidak sampai BAPI SAP" ([Bagian 6.2 baseline](../../architecture/inspection-order/order-emol-sap-sync.md#62-mapping-ke-bapi-sap-dilakukan-oleh-middleware)) **tidak perlu ditindaklanjuti** di scope Phase 2 — correlation kita sengaja tidak bergantung ke data SAP sama sekali ([lihat resolusi Poin 6](#poin-6-duplicate-atau-correlation-handling)), jadi gap lama ini tidak block apapun di desain kita.

### Poin 13: MO Backlog Re-entry Loop

**Resolved (2026-08-17) — TIDAK butuh perlakuan khusus, sudah aman lewat mekanisme existing:**

1. **eMOL reuse-vehicle tidak pernah masuk loop ini sama sekali** — skip total sync SAP ([Poin 5](#poin-5-data-flow-defect-dan-crack)), tidak pernah jadi Order baru yang dikirim ke SAP, tidak pernah balik sebagai MO Backlog dari jalur ini. Yang genuinely lewat SAP cuma cabang `ReuseOrderNumber` NULL (Order baru genuine, Sub-kasus B1/B2).
2. **Untuk Order baru genuine, begitu balik jadi `MOOpen`, tidak ada join-back terdokumentasi ke `MechanicOrderList` asal** (dikonfirmasi eksplisit di [baseline Bagian 9](../../architecture/inspection-order/order-emol-sap-sync.md#9-mo-backlog--inbound-flow-sap--digiman)) — praktisnya, begitu jadi `MOOpen`, MO **tidak dibedakan lagi** asalnya `Type='Form'`/`Inspection`/`Additional`, dieksekusi lewat 2 jalur existing ([Bagian 9.2 baseline](../../architecture/inspection-order/order-emol-sap-sync.md#92-cara-mo-backlog-dieksekusi)) tanpa logic khusus.
3. **Munculnya kembali sebagai candidate correlation ("Check Existing") untuk Finding lain di masa depan itu behavior yang diinginkan**, bukan bug — memang tujuan candidate-scope [Poin 6](#poin-6-duplicate-atau-correlation-handling).
4. **Eksekusi via "langsung saat Inspection" (Bagian 9.2 jalur 2 baseline)** — mekanisme `BacklogExecutionList` yang **sama persis** dengan yang sudah kita gantungi buat trigger post-approval reuse-vehicle ([Poin 5](#poin-5-data-flow-defect-dan-crack)). Jalur manapun yang men-trigger (otomatis dari approval kita, atau manual dari inspector lain pilih backlog), mekanismenya identik, tidak perlu logic beda.

**Kesimpulan:** Order dari flow Phase 2 (setelah lolos sync SAP) diperlakukan **identik** dengan Order dari sumber manapun begitu masuk siklus MO Backlog — tidak ada logic tambahan yang perlu dibangun.

## Fase F — Dashboard

**Deferred (2026-08-17) — di-defer ke next MVP, bukan scope Phase 2 ini.** Konsekuensi: **mekanisme percepatan/prioritas Sub-kasus B2** ([Poin 1](#poin-1-trigger-dan-ui-create-defect-atau-crack)) yang sebelumnya sengaja di-defer ke sini **ikut ke next MVP juga** — bukan lagi "nanti dibahas di fase ini" dalam Phase 2, karena fase-nya sendiri sudah di luar scope.

---

## Related Docs

- [order-integration-checklist.md](order-integration-checklist.md) — kerangka kerja & progress diskusi Phase 2 (14 poin, 6 fase)
- [pm-shutdown-service-package.md](../phase1-service-package/pm-shutdown-service-package.md) — phase 1, sumber deferred item yang jadi latar belakang phase 2 ini
- [form-builder.md](../../architecture/form/form-builder.md) — struktur TaskKit & Bank Task row (fakta current-state lengkap)
- [form-submission.md](../../architecture/form/form-submission.md) — schema `TaskPersonalizedFinding`, `TaskResponseLog`
- [maintenance-execution-schema.md](../../architecture/database/maintenance-execution-schema.md) — DDL real `TaskPersonalizedFinding`, `CrackIdentified`, `BacklogExecutionList`
- [maintenance-order-schema.md](../../architecture/database/maintenance-order-schema.md) — DDL real `MechanicOrderList`, `SAPMOSyncOrder`, `PoolingMOItem`, dll
- [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) — flow Order/eMOL existing, gap DamageCode/Component tidak sampai ke SAP
