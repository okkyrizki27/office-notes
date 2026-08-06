# Business Operational Form — SQL/Cosmos Data Consistency Issue (Step 2: Update Tab)

*Last updated: 2026-08-06*

**Status:** Known issue, belum ada mitigasi
**Service:** `maintenance-execution`

---

## Ringkasan

Saat user mengisi tab form (mis. tab General) di Business Operational Form, mobile mengirim data ke **2 API terpisah** yang masing-masing menulis ke database berbeda (SQL dan Cosmos DB). Kedua API ini **tidak dikoordinasikan lewat 1 transaksi/mekanisme apa pun** — masing-masing bisa sukses atau gagal secara independen. Kalau salah satu gagal sementara yang lain sukses, data di SQL dan Cosmos jadi **divergen**: dua sumber data yang seharusnya mendeskripsikan WorkOrder yang sama, tapi isinya beda cerita — dan tidak ada mekanisme yang mendeteksi atau memperbaiki kondisi ini secara otomatis.

---

## Konteks Teknis

Step "user mengisi tab General" terdiri dari 2 API call:

| API | Endpoint | Handler |
|---|---|---|
| **2.1** | `POST /workorder/additional/business-operational/{workOrderId}/save/offline` | `SaveBoAdditionalWoDataOfflineCommandHandler` |
| **2.2** | `POST /form-submission/structure/tab?submissionTabId={id}` | `SaveFormSubmissionStructureCommandHandler` |

Dari pembacaan source code kedua handler ini, ternyata ada **3 titik commit independen** (bukan cuma "SQL vs Cosmos" sebagai 2 blok), karena 2.2 sendiri bukan 1 operasi atomic — di dalamnya ada 2 sub-langkah berurutan (SQL commit dulu, baru Cosmos):

| Unit | Endpoint API | Sub-proses dalam handler | Yang ditulis | Sifat |
|---|---|---|---|---|
| **A** | 2.1 — `save/offline` | `SaveBoAdditionalWoDataOfflineCommandHandler` (1 SQL transaction) | `WorkOrder.AssetModelCode/AssetModelName/AssetNumber/SiteCode/SectionTypeCode`, `TaskPersonalized.UserCode` (semua record di bawah WorkOrder tsb), `FormSubmission.AssetBrandCode/AssetTypeCode/AssetVariantCode` | Atomic (all-or-nothing) di dalam dirinya sendiri |
| **B** | 2.2 — `form-submission/structure/tab` | Sub-step 1 (SQL transaction, commit lebih dulu) | `FormSubmissionTab.IsCompleted`, `ModifiedAt`/`ModifiedBy` | Atomic sendiri, commit sebelum C dieksekusi |
| **C** | 2.2 — `form-submission/structure/tab` (endpoint sama dengan B, 1 call yang sama) | Sub-step 2 (Cosmos upsert, setelah B commit) | `FormSubmissionStructure.Sections` — jawaban form penuh, termasuk section "Asset Information" (`ASSETNUMBER`) dan "Nama Observer" (`LABOURPERSONNEL`) yang **secara fakta duplikat** dari apa yang ditulis unit A | Upsert Cosmos, **tidak ikut rollback** kalau gagal setelah B sudah commit |

**Poin penting:** section "Asset Information" & "Nama Observer" di Cosmos (unit C) dan kolom asset/personnel di SQL (unit A) merepresentasikan **fakta yang sama** (asset yang dipilih, siapa personnel-nya) tapi ditulis lewat 2 jalur yang sepenuhnya independen. Ini yang membuat kegagalan parsial jadi masalah nyata, bukan cuma isu teoretis — begitu salah satu unit gagal, SQL dan Cosmos benar-benar "bercerita" data yang berbeda untuk WorkOrder yang sama.

Unit B dan C tidak bisa gagal dalam kombinasi "B gagal, C sukses" — C hanya dieksekusi setelah blok SQL transaction B selesai tanpa exception; kalau B melempar exception, transaksinya rollback dan eksekusi tidak akan sampai ke langkah C.

---

## Skenario Kegagalan

| # | A (SQL: WorkOrder/TaskPersonalized/FormSubmission) | B (SQL: FormSubmissionTab.IsCompleted) | C (Cosmos: FormSubmissionStructure.Sections) | Dampak |
|---|---|---|---|---|
| 1 | ✅ Sukses | ❌ Tidak jalan | ❌ Tidak jalan | `WorkOrder`/`TaskPersonalized`/`FormSubmission` sudah reflect asset & personnel baru. Tapi `FormSubmissionTab.IsCompleted` tetap `false`, dan `Sections` di Cosmos masih versi lama — fitur **View History** (kemungkinan besar render dari Cosmos `FormSubmissionStructure`, belum diverifikasi langsung ke handler-nya) akan menampilkan jawaban stale, meski listing WorkOrder sudah menampilkan asset yang benar. |
| 2 | ✅ Sukses | ✅ Sukses | ❌ Gagal | Sama seperti #1 di sisi `WorkOrder`, tapi lebih berbahaya: `IsCompleted = true` (sistem menganggap tab ini selesai) padahal `Sections` masih stale — tidak ada sinyal apa pun ke user/sistem bahwa data sebenarnya belum tersimpan dengan benar. |
| 3 | ❌ Gagal | ✅ Sukses | ✅ Sukses | `Sections` di Cosmos sudah reflect jawaban baru (termasuk asset yang dipilih user). Tapi `WorkOrder.AssetNumber` dan `TaskPersonalized.UserCode` masih nilai lama — listing WorkOrder tampil salah, dan fitur assignment/filter apa pun yang berbasis `TaskPersonalized.UserCode` (mis. "tugas saya") tidak akan menemukan mechanic yang sebenarnya ditugaskan lewat form. |
| 4 | ❌ Gagal | ✅ Sukses | ❌ Gagal | Gabungan gejala #1 dan #3 sekaligus: `WorkOrder`/`TaskPersonalized` stale (seperti #3) **dan** `Sections` juga stale meski `IsCompleted = true` (seperti #2) — kombinasi paling membingungkan untuk debug karena 3 sumber data (`WorkOrder`, flag `IsCompleted`, `Sections`) bisa saling kontradiksi. |
| 5 | ❌ Gagal | ❌ Tidak jalan | ❌ Tidak jalan | Tidak ada state yang berubah sama sekali — paling konsisten secara data, tapi isian user hilang total tanpa jejak, kecuali ada mekanisme retry di sisi mobile (offline-first) yang menangani ini — belum diverifikasi ada/tidaknya di source code yang sudah dibaca. |

---

## Root Cause

3 unit commit independen (A, B, C), tersebar di 2 API call terpisah, tanpa:
- Distributed transaction, saga, atau outbox pattern yang mengikat ketiganya jadi 1 unit logis
- Retry otomatis kalau salah satu unit gagal setelah unit lain sukses
- Reconciliation job yang bisa mendeteksi WorkOrder dengan state SQL/Cosmos yang sudah divergen

---

## Open Questions

- Apakah mobile punya mekanisme retry/offline-queue untuk skenario #1, #2, #4, #5 di atas, atau kegagalan ini silent dari sisi user?
- Fitur **View History** — perlu diverifikasi apakah benar render dari Cosmos `FormSubmissionStructure`, dan apakah ada fallback ke SQL kalau data Cosmos tidak lengkap/tidak ada.
- Apakah ada monitoring/alerting existing yang bisa mendeteksi kondisi divergensi ini di production saat ini?
