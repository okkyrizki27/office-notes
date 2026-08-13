# My Work

Dokumen ini merangkum diskusi awal (rough assessment) tentang fitur **My Work** di Digiman+ — layar mobile untuk Mechanic dan Foreman mencatat aktivitas kerja hariannya (planned maupun ad-hoc), termasuk fit to work sebelum bekerja. Data yang tercatat di sini menjadi sumber utama bagi [Mechanic Activity Report (eMAR)](mechanic-activity-report.md) — My Work adalah layer capture harian, eMAR adalah layer rollup periodik + approval di atasnya.

*Last updated: 2026-08-13*

---

## Konsep

Setiap hari, Mechanic/Foreman membuka My Work untuk melihat pekerjaan yang di-plan-kan untuknya (dari Digiplan) sekaligus mencatat aktivitas yang dikerjakan — baik yang sudah direncanakan maupun yang tidak. Satu baris My Work = satu sesi aktivitas (mirip grain `TaskPersonalizedLog` yang sudah ada).

| Atribut | Nilai |
|---------|-------|
| Target user | Mechanic, Foreman |
| Platform | Mobile only |
| Konektivitas | Online only |
| Cakupan waktu | Hari ini, kemarin, besok — selama data tersedia di sistem |

---

## Jenis Aktivitas

| Tipe | Source | Keterangan |
|------|--------|------------|
| **Maintenance — planned** | Assignment dari Digiplan | Task yang sudah di-plan-kan untuk tanggal/equipment tertentu. **Mekanisme assignment belum final** — lihat Open Items |
| **Maintenance — ad-hoc** | Manual, ditambahkan user | Aktivitas maintenance di luar plan (mis. corrective mendadak) |
| **Non Maintenance** | Manual, ditambahkan user | Aktivitas non-unit (cleaning workshop, meeting, dll) |

Taksonomi ini selaras dengan kategori Maintenance/Non Maintenance yang sudah didefinisikan di eMAR — tidak perlu kategori baru.

---

## Data yang Dicapture

| Field | Mandatory | Keterangan |
|-------|-----------|------------|
| User ID | ✅ | Mechanic/Foreman yang login (individual account) |
| Activity Type | ✅ | Maintenance / Non Maintenance |
| Task Description | ✅ | Nama task/form (jika dari plan) atau deskripsi manual |
| Unit/Equipment | ✅ untuk Maintenance | Wajib pilih unit/WO nyata (bukan freeform) — lihat catatan auto-match di Open Items |
| Duration | - | Kalkulasi otomatis dari Start–End |
| Start – End | ✅ (planned), editable untuk actual | Actual bisa berbeda dari planned saat konfirmasi selesai |
| Remarks | ❌ | Catatan bebas |
| Location | ❌ (maybe) | Belum ada precedent GPS/geofencing di app lain — backlog candidate |

---

## Fit to Work

Pengisian fit to work dilakukan sebelum user mulai bekerja. Rekomendasi: reuse arsitektur Form/Question/FormSubmission yang sudah ada (bukan objek baru), konsisten dengan pola Order Integration yang hook di layer Form generik.

Open question: gate ini berlaku **per shift** (sekali per hari kerja) atau **per assignment** (setiap kali mulai task baru)?

---

## Konfirmasi Selesai & Auto-Match

- Start–End yang di-plan-kan tetap editable untuk mencatat actual saat user konfirmasi assignment selesai.
- Auto-match: sistem bisa mencocokkan otomatis by unit number / WO number terhadap data Inspection atau Form Submission yang sudah ada, untuk mengurangi konfirmasi manual.
- Auto-match hanya bisa jalan jika baris My Work punya referensi unit/WO yang valid — karena itu entry Maintenance (planned maupun ad-hoc) **wajib** memilih unit/WO nyata, bukan input teks bebas. Freeform text hanya untuk Non Maintenance (yang memang tidak perlu di-match).

---

## Data Model (Draf Awal — perlu validasi tim engineering)

| Kebutuhan | Sumber existing | Catatan |
|-----------|------------------|---------|
| Task planned + self-assign | `TaskPersonalized` (existing) | Model saat ini pull-based ("Assign to Me") — lihat Open Items soal push assignment |
| Sesi aktivitas system-sourced | `TaskPersonalizedLog` (existing) | StartDate/EndDate, ShiftName, Site/Section snapshot sudah ada |
| Aktivitas manual (ad-hoc Maintenance + Non Maintenance) | **Baru** | Entity baru sejenis `TaskPersonalizedLog` tapi tidak wajib FK ke Task — perlu UserCode, ActivityType, Description, AssetNumber/WorkOrderNumber (nullable untuk Non Maintenance), StartDate/EndDate, Remarks, Status |
| Fit to Work | Reuse `FormSubmission` | Bukan tabel baru |

---

## Relasi dengan Digiplan — Gap Penting

Requirement mengasumsikan Digiplan sudah bisa menampilkan "assignment" (tanggal + equipment + pekerjaan) per mechanic. Saat ini **belum ada mekanisme push-assignment** di Digiplan/maintenance-execution — WorkOrder/Task dibuat terikat ke equipment+form+tanggal, bukan ke orang spesifik; assignment ke mechanic terjadi self-service lewat "Assign to Me". Dua opsi:

1. **Pull (existing)** — My Work menampilkan task yang sudah di-*self-assign* oleh mechanic. Buildable sekarang, tapi lebih tepat disebut "My Tasks" daripada "assignment yang di-plan-kan".
2. **Push (baru)** — Foreman/Planner meng-assign mechanic ke task tertentu di muka. Butuh data model baru + UI baru, dan keputusan siapa yang berwenang assign serta di tahap mana (saat Plan DRAFT di dplan, atau setelah Task terbentuk di maintenance-execution).

Requirement "berapa jam user tersebut bekerja di situ" (planned hours per person) juga bergantung pada opsi mana yang dipilih, dan pada penyelesaian isu Man Power/Man Hours per-individu yang masih open di enhancement lain (rollup predecessor/serial/parallel belum diputuskan).

---

## Kebutuhan UI Tambahan (untuk Estimasi Effort)

Belum ada mockup untuk My Work — daftar berikut inventarisasi layar yang kemungkinan dibutuhkan, di luar konsep yang sudah dibahas di atas.

| # | Layar | Deskripsi | Catatan |
|---|-------|-----------|---------|
| 1 | My Work — Hari Ini (Home) | List assignment hari berjalan (planned + manual), grouped by status, summary jam planned vs actual | Entry point dari Homepage — perlu tile/permission baru, lihat [homepage-current-state.md](../architecture/homepage/homepage-current-state.md) |
| 2 | Navigasi Tanggal (Kemarin/Hari Ini/Besok) | Prev/next day navigation | **Reuse langsung** — pola ini sudah ada persis di [report-design-mechanic-day-detail.html](report-design-mechanic-day-detail.html) milik eMAR (day-nav, progress dots, prev/next). Kemungkinan besar satu komponen dipakai bersama |
| 3 | Detail Assignment | Tap satu assignment → detail lengkap (deskripsi, unit, planned vs actual start-end, remarks, status) | |
| 4 | Tambah Aktivitas Non Maintenance (manual) | Form: activity type, description, start-end, remarks | Sama persis dengan "+ Tambah Manual" di eMAR — lihat catatan cross-cutting di bawah |
| 5 | Tambah Aktivitas Maintenance ad-hoc | Form sama seperti #4, plus **unit/WO picker** (search & pilih WorkOrder/unit nyata) | Komponen search unit/WO **belum ada dokumentasi reuse** di repo ini — perlu konfirmasi ke tim engineering apakah BD Corrective/PM Shutdown sudah punya komponen search asset yang bisa dipakai ulang |
| 6 | Edit/Delete entry manual | Sebelum hari dikonfirmasi/dikunci | Sudah ada contoh UI-nya di day-detail eMAR (`.btn-edit`/`.btn-delete`) |
| 7 | Fit to Work | Form sebelum mulai kerja | Rekomendasi reuse Form Builder rendering engine — bukan layar custom baru |
| 8 | Blocked state — Fit to Work belum diisi | State saat user coba mulai kerja tapi fit to work belum lengkap | |
| 9 | Konfirmasi Actual Start/Done | Aksi + edit actual start-end per assignment | |
| 10 | Prompt Auto-Match | Banner/modal saat sistem mendeteksi assignment sudah match dengan Inspection/Form Submission — user tinggal konfirmasi | |
| 11 | Empty state (tidak ada assignment / hari Off) | | |
| 12 | Blocking state — tidak ada koneksi | Karena online-only, perlu state eksplisit "tidak bisa mencatat aktivitas tanpa koneksi" — pola ini **belum ada** di modul lain (PM Shutdown/Inspection semua offline-first) | Terkait langsung dengan open item online-only di atas |
| 13 | (Kondisional) Foreman — Assignment Board | Layar Foreman untuk assign mechanic ke task/tanggal tertentu | **Hanya relevan jika opsi push-assignment dipilih** (lihat "Relasi dengan Digiplan — Gap Penting"). Scope besar, sebaiknya diestimasi terpisah dari MVP |

---

## Kebutuhan Backend (untuk Estimasi Effort)

| # | Item | Jenis | Deskripsi | Catatan |
|---|------|-------|-----------|---------|
| 1 | `UserActivityLog` (nama sementara) | Tabel baru | Aktivitas manual (Maintenance ad-hoc + Non Maintenance) — UserCode, ActivityType, Description, AssetNumber/WorkOrderNumber (nullable), StartDate/EndDate, Remarks, Status, snapshot fields (UserFullName/Site/Section, mengikuti pola `TaskPersonalizedLog`) | |
| 2 | `GET /my-work?date=` | API baru | Feed gabungan: `TaskPersonalized`/`TaskPersonalizedLog` (system) + `UserActivityLog` (manual) untuk satu user+tanggal | Perlu service-layer join lintas tabel existing + tabel baru |
| 3 | CRUD manual activity | API baru | Create/update/delete `UserActivityLog`, dibatasi selama belum dikonfirmasi/di-submit | |
| 4 | Confirm actual start/done | API baru | Update actual Start/End pada assignment (system maupun manual) | |
| 5 | Unit/WorkOrder search | API baru atau reuse | Untuk picker di item UI #5 | **Perlu konfirmasi**: apakah endpoint search asset sudah ada (dipakai BD Corrective dll.) sebelum diasumsikan butuh dibangun dari nol |
| 6 | Fit to Work | Reuse `FormSubmission` + API kecil baru | Submit form + endpoint cek "sudah diisi hari/shift ini?" untuk gating | |
| 7 | Auto-match engine | Integrasi baru (event-driven atau scheduled job) | Listen ke event completion Inspection/Form Submission, cocokkan by (UserCode + AssetNumber/WorkOrderNumber + tanggal/shift) ke assignment My Work yang masih open, lalu flag/pre-fill actual end | Cross-service (Inspection + Form Submission + My Work) — bukan pekerjaan kecil |
| 8 | Permission & Homepage integration | RBAC + BE kecil | Permission code baru (pola `IAMS_Mobile_*_View`), logic count untuk tile Homepage | |
| 9 | (Kondisional) Push-assignment | Tabel + API baru | `Assignment` (Foreman→Mechanic→Task→Tanggal) + notifikasi ke mechanic ter-assign | Hanya jika opsi push dipilih — lihat item UI #13 |
| 10 | Notifikasi (reminder fit-to-work, auto-match prompt) | Integrasi | **Dependency tidak diketahui** — tidak ditemukan dokumentasi push notification service di platform ini; perlu konfirmasi apakah infra-nya sudah ada (ini kemungkinan dependency platform-level, bukan effort khusus My Work) | |

> **Catatan positif:** karena My Work online-only, **tidak perlu** offline sync queue (upsert-by-device, batch sync, dedup) seperti pola `TaskPersonalized`/`TaskPersonalizedLog` di PM Shutdown — ini mengurangi effort BE dibanding modul eksekusi lain, tapi trade-off-nya adalah risiko UX yang sudah dicatat di Open Items (blocking di area minim sinyal).

> **Cross-cutting dengan eMAR:** Item UI #4/#5 (Tambah Aktivitas) dan BE #1-3 di atas **kemungkinan besar adalah fitur yang sama** dengan tombol "+ Tambah Manual" di [mechanic-activity-report.md](mechanic-activity-report.md) — jangan diestimasi dua kali sebagai fitur terpisah. Lihat catatan yang sama di dokumen eMAR.

---

## Open Items

- [ ] Push vs pull assignment dari Digiplan — menentukan besar scope My Work secara signifikan (lihat bagian Gap di atas)
- [ ] Planned hours per mechanic — tergantung penyelesaian Man Power/Man Hours per-individu (enhancement terpisah, masih open)
- [ ] Apakah Supervisor juga pakai My Work untuk log aktivitas sendiri, atau hanya berperan sebagai approver di eMAR? (eMAR saat ini mencakup Level 2/3/4 termasuk Supervisor sebagai pengisi report)
- [ ] Fit to Work — gate per shift atau per assignment?
- [ ] Online-only — apakah ini deliberate tradeoff MVP? Seluruh flow eksekusi lain (PM Shutdown, Inspection, TaskPersonalized) offline-first; online-only berisiko memblokir mechanic mulai kerja di area minim sinyal. Perlu konfirmasi ke ops/business.
- [ ] Location — perlu GPS/geofencing atau cukup catatan manual? (ditandai "maybe" oleh requirement awal)
- [ ] Grouping "hari" untuk view kemarin/besok — berdasarkan shift-start-date (konsisten dengan pola auto-close `TaskPersonalizedLog`) atau calendar date? Relevan untuk night shift yang lintas tengah malam
- [ ] Entity baru untuk manual/ad-hoc activity — struktur final, nama tabel, dan siapa yang mengonsumsinya selain eMAR
