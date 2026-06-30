# Digiman Transaction Report — Gap Analysis & Discussion Document

**Tujuan dokumen:** Merangkum hasil analisa teknis terhadap 5 halaman Digiman Transaction Report (skema `[am]`, Synapse/SQL Serverless) menjadi temuan gap, usulan solusi, dan daftar konfirmasi yang dibutuhkan dari business stakeholder. Dokumen ini dipakai sebagai bahan diskusi bersama tim engineer/developer dan business stakeholder.

**Scope:** D'Inspect Result, D'Order Result, Inspection Compliance, Ordering Compliance, Lead Time Report — total 5 view SQL (`vw_report_iams_inspection_results`, `vw_report_iams_f_am_digiman_dorder`, `vw_report_iams_get_molist`, `vw_report_iams_get_assignment`, `vw_report_iams_f_am_digiman_leadtime`).

**Cara membaca:** Setiap halaman report dibahas dengan struktur yang sama — Business Question, tabel Gap & Proposed Solution (diurutkan severity), Business Rules yang sudah dikonfirmasi, dan pertanyaan terbuka untuk bisnis. Bagian Cross-Cutting Issues di awal merangkum masalah yang berulang di lebih dari satu view — ini yang paling berdampak jika diperbaiki karena efeknya menyebar ke beberapa report sekaligus. Chapter 5 berbeda sifat dari chapter 1–4: bukan gap dari kondisi existing, melainkan desain perbaikan (improvement) untuk mengikuti kapabilitas baru aplikasi (multi-level approval).

---

## Executive Summary

| Report Page | View(s) | Total Issues | High | Medium | Low | Pending Confirmation |
|---|---|:---:|:---:|:---:|:---:|:---:|
| D'Inspect Result | `vw_report_iams_inspection_results` | 6 | 0 | 3 | 3 | 0 |
| D'Order Result & Ordering Compliance | `vw_report_iams_f_am_digiman_dorder` | 17 | 2 | 9 | 5 | 1 |
| Inspection Compliance | `vw_report_iams_get_molist` + `vw_report_iams_get_assignment` | 13 | 3 | 5 | 5 | 0 |
| Lead Time Report | `vw_report_iams_f_am_digiman_leadtime` | 10 | 0 | 4 | 6 | 0 |
| **Cross-Cutting (lintas view)** | Semua view | 7 | 4 | 2 | 1 | 0 |

**Highlight utama:**
- 4 dari 7 masalah cross-cutting berkategori **High** — perbaikan di sini berdampak ke lebih dari satu report sekaligus, sehingga sebaiknya diprioritaskan sebelum perbaikan per-view.
- Tidak ada gap yang menyebabkan data salah secara fatal — sebagian besar adalah **silent drop** (data hilang tanpa error) atau **inkonsistensi penamaan/timezone** yang berisiko menyesatkan saat membaca angka KPI.
- Beberapa hal sudah dikonfirmasi disengaja oleh business owner (lihat bagian "Business Rules Confirmed" tiap halaman) — tidak perlu didiskusikan ulang.

---

## Cross-Cutting Issues (Lintas View)

Masalah berikut muncul di lebih dari satu view. Memperbaikinya sekali akan berdampak ke seluruh report.

| # | Issue | View Terdampak | Severity | Proposed Solution |
|---|-------|----------------|:---:|---|
| 1 | **Timezone tidak konsisten** — sebagian view pakai UTC murni, sebagian konversi via `site.utcoffset`, satu view pakai hardcode `UTC+7` | `get_molist` (UTC), `get_assignment` (utcoffset), `leadtime` (`load_date` hardcode +7), `dorder` (utcoffset konsisten) | <span class="sev-high">High</span> | Tetapkan satu standar timezone untuk seluruh view: gunakan `site.utcoffset` di semua tempat yang melakukan overdue-check atau date-display, hapus hardcode `+7`. Butuh keputusan bisnis: apakah semua site memang WIB, atau perlu per-site offset. |
| 2 | **`tenantcode = 'MKP'` hardcoded** di join `sectiontype`/`site` | `inspection_results`, `dorder`, `get_molist`, `get_assignment`, `leadtime` (5 dari 5 view) | <span class="sev-high">High</span> | Jika Digiman+ direncanakan multi-tenant, parameterisasi `tenantcode` (misal via session context atau view per-tenant). Jika dipastikan single-tenant selamanya, dokumentasikan eksplisit sebagai keputusan arsitektur agar tidak dianggap bug saat tenant baru onboard. |
| 3 | **Filter `isactive` pada tabel `user` tidak konsisten** — beberapa view tampilkan user nonaktif (historis), beberapa tidak | Tampil: `inspection_results`, `leadtime`. Tidak tampil: `dorder`, `get_molist`/`get_assignment` | <span class="sev-medium">Medium</span> | Tetapkan kebijakan baku: report historis (siapa yang mengerjakan apa) sebaiknya **tidak** filter `isactive` agar nama tetap muncul meski user di-deactivate kemudian. Terapkan konsisten di semua view atau dokumentasikan alasan per-view jika memang harus berbeda. |
| 4 | **Status resolution via config CSV → silent drop** jika ada kombinasi status baru di sistem yang belum terdaftar di `config_mapping_wo_status.csv` / `config_mapping_mol_status.csv` | `get_molist`, `get_assignment`, `leadtime` (WO status), `dorder` (MOL status) | <span class="sev-high">High</span> | Tambahkan baris fallback `'Unknown'`/`'Unmapped'` di config CSV untuk kombinasi yang tidak match, atau buat monitoring terpisah yang menghitung berapa WO/MOL yang gagal resolve status — agar tim aware ketika ada status baru ditambahkan di aplikasi tapi config belum diupdate. |
| 5 | **`SELECT DISTINCT` sebagai satu-satunya safeguard duplikasi** dari join fan-out (multiple finding, multiple TP, dll) | `inspection_results`, `leadtime` | <span class="sev-medium">Medium</span> | `DISTINCT` tidak efektif jika baris berbeda di satu kolom numerik saja (misal leadtime). Review join yang berpotensi fan-out, pertimbangkan window function/aggregation eksplisit alih-alih bergantung pada DISTINCT di akhir query. |
| 6 | **Kolom bernama "Utc" tapi nilainya sudah local time** — membingungkan bagi yang membaca laporan tanpa konteks SQL | `get_assignment` (`CreatedUtcDate`, `SubmittedUtcDate`), `dorder` (`SubmittedUtcDateUTC`, `ApprovalDateUTC`) | <span class="sev-low">Low</span> | Rename kolom mengikuti isinya yang sebenarnya (`CreatedLocalDate`, dst), atau tambahkan kolom UTC terpisah dengan suffix konsisten. Perubahan nama kolom perlu koordinasi dengan tim PBI (breaking change). |
| 7 | **Kolom placeholder NULL** tersebar di banyak view (SAP fields, `Notes`, `CompletedUtcDate`, dll) tanpa timeline kapan akan diisi | `inspection_results` (11 kolom), `get_molist` (8 kolom), `get_assignment` (2 kolom), `dorder` (`Notes`) | <span class="sev-low">Low</span> | Konfirmasi roadmap: apakah integrasi SAP/field ini akan diisi dalam waktu dekat? Jika tidak ada rencana, evaluasi penghapusan kolom untuk mengurangi kebingungan konsumen report. |

---

## 1. D'Inspect Result

**View:** `am.vw_report_iams_inspection_results`
**Business Question:** Apa saja temuan defect/kerusakan dari hasil inspeksi unit yang sudah diselesaikan inspector?

### Gap & Proposed Solution

| # | Issue | Severity | Proposed Solution |
|---|-------|:---:|---|
| 1 | `damagecodegroup` pakai **INNER JOIN** — finding dengan `damagecode` yang tidak match master data akan **hilang tanpa error** | <span class="sev-medium">Medium</span> | Ubah ke LEFT JOIN agar finding tetap muncul dengan damage info kosong, atau jalankan data quality check rutin untuk memastikan semua `damagecode` di transaksi sudah terdaftar di master. |
| 2 | `Date` (tanggal selesai inspeksi, local time) bisa NULL jika `sitecode` WO tidak match di tabel `site` | <span class="sev-medium">Medium</span> | Validasi coverage mapping `sitecode → site` secara berkala; pastikan semua site aktif terdaftar di master `site`. |
| 3 | `SELECT DISTINCT` sebagai dedup — lihat Cross-Cutting #5 | <span class="sev-medium">Medium</span> | Lihat solusi cross-cutting. |
| 4 | 11 kolom placeholder selalu NULL — lihat Cross-Cutting #7 | <span class="sev-low">Low</span> | Lihat solusi cross-cutting. |
| 5 | `user` tanpa filter `isactive` | <span class="sev-low">Low</span> | Sudah dikonfirmasi disengaja (lihat Business Rules). Tidak perlu tindakan, hanya perlu diseragamkan dengan view lain (Cross-Cutting #3). |
| 6 | `taskpersonalized` filter hanya `status = 'Complete'` — task yang masih `In Progress` tidak akan punya finding tampil | <span class="sev-low">Low</span> | Sudah sesuai desain (findings hanya valid setelah inspeksi selesai). Tidak perlu tindakan. |

### Business Rules (Confirmed)
- WO lifecycle: `Open → Pending → In Progress → Complete → Close`. Status `Close` = auto-close sistem karena tidak dieksekusi (bukan selesai) — filter `NOT IN ('Close','Cancelled')` sudah benar.
- Findings tampil real-time begitu inspector submit, baik WO `In Progress` maupun `Complete` — disengaja.
- `isimmediateexecutable = 1` tanpa priority → label `'CLOSE'` — menandakan quick-fix yang langsung diperbaiki saat inspeksi, bukan status WO closed.
- Inspector nonaktif tetap tampil — disengaja, report historis.
- Priority hanya diambil dari `group = 'Inspection'`.

### Open Questions for Business
- Apakah ada cara untuk memvalidasi bahwa semua `damagecode` transaksi sudah lengkap di master data, supaya INNER JOIN tidak diam-diam membuang finding?
- Apakah 11 kolom placeholder (RouteId, ComponentId, dll) ada di roadmap pengisian, atau aman dihapus dari view?

---

## 2. D'Order Result & Ordering Compliance

**View:** `am.vw_report_iams_f_am_digiman_dorder` *(dipakai untuk dua halaman report — D'Order Result dan Ordering Compliance)*
**Business Question:** Apa status spare part order (eMOL) dari temuan inspeksi maupun additional order, dari submission hingga approval, SAP push, dan GR/GI?

### Gap & Proposed Solution

| # | Issue | Severity | Proposed Solution |
|---|-------|:---:|---|
| 1 | `mechanicorderlist` filter `isactive` **dikomentari** — semua MOL masuk, hanya disaring via `correct_status` dari config | <span class="sev-high">High</span> | Lihat Cross-Cutting #4. Tambahkan fallback status agar kombinasi baru tidak silently dropped. |
| 2 | **SAP MO number prefix `'00'` hardcoded** (`concat('00', mono)`) untuk match ke `moapproval.monumber` — gagal silent jika tenant/site beda format SAP | <span class="sev-high">High</span> | Pindahkan prefix ke config per-site/tenant, atau validasi format MO number SAP di semua site sebelum mengandalkan hardcode ini. |
| 3 | `user` filter `isactive=1` — **inkonsisten** dengan view lain | <span class="sev-medium">Medium</span> | Lihat Cross-Cutting #3. |
| 4 | `canactiondigimandelete`, `canactionsappushdelete`, `cancreatemo`, `cancreatemowithnote` dihitung di CTE tapi **tidak masuk output view** | <span class="sev-medium">Medium</span> | Konfirmasi apakah field ini dipakai di layer aplikasi Digiman+ lain. Jika tidak, hapus dari CTE untuk mengurangi kompleksitas; jika ya, dokumentasikan dependency-nya. |
| 5 | `poolingstatus NOT IN ('MOJ','MOK')` — magic string tanpa dokumentasi arti | <span class="sev-medium">Medium</span> | Tambahkan kamus/glossary status pooling (MOJ, MOK, dst) di config atau dokumentasi terpisah agar tidak jadi tribal knowledge. |
| 6 | `moapproval` tanpa filter `isactive` — bisa ambil approval yang sudah tidak valid | <span class="sev-medium">Medium</span> | Tambahkan filter `isactive=1` kecuali ada alasan bisnis spesifik untuk menyertakan approval nonaktif. |
| 7 | `sapmosyncorder` tanpa filter `isactive` | <span class="sev-medium">Medium</span> | Sama seperti di atas — review apakah perlu filter `isactive=1`. |
| 8 | `moapprovaldate` dihitung dari **perbandingan string** `YYYYMMDD` — rapuh jika format SAP tidak konsisten | <span class="sev-medium">Medium</span> | Validasi format tanggal dari SAP source secara berkala, atau cast ke tipe date sebelum dibandingkan. |
| 9 | `sectiontype` hardcoded `tenantcode='MKP'` | <span class="sev-medium">Medium</span> | Lihat Cross-Cutting #2. |
| 10 | `SubComponentId` menyimpan `componentcode` (bukan subcomponent ID) — naming bug | <span class="sev-low">Low</span> | Perbaiki nama kolom atau isinya agar sesuai — perlu cek dampak ke konsumen (PBI) sebelum mengubah. |
| 11 | Kolom "UTC" sudah local time — lihat Cross-Cutting #6 | <span class="sev-low">Low</span> | Lihat solusi cross-cutting. |
| 12 | `Notes` selalu NULL | <span class="sev-low">Low</span> | Lihat Cross-Cutting #7. |
| 13 | `Aging` dihitung real-time (`DATEDIFF` terhadap `GETUTCDATE()`) | <span class="sev-low">Low</span> | Expected behavior untuk live dashboard — tidak perlu tindakan, hanya perlu disadari bahwa snapshot historis akan selalu menunjukkan aging terbaru saat query dijalankan. |
| 14 | Dual workflow `COALESCE(wft1.status, wft2.status)` | <span class="sev-low">Low</span> | Sudah aman by design (mutually exclusive). Tidak perlu tindakan. |
| 15 | `pvr1` vs `pvr2` COALESCE (validasi material vs detail) | <span class="sev-low">Low</span> | Sudah disengaja — material-level diutamakan. Tidak perlu tindakan. |
| 16 | `PriorityName` NULL untuk additional order | <span class="sev-low">Low</span> | Expected — additional order tidak punya finding sehingga tidak ada priority. Tidak perlu tindakan. |
| 17 | `MaterialStatus` (`'Add'`/`'Ok'`/`'Delete'`) — tujuan bisnisnya di report belum dikonfirmasi | <span class="sev-pending">Pending Confirmation</span> | **Perlu jawaban bisnis**: kolom ini dipakai untuk apa di PBI? `'Add'` = dibuat & dimodifikasi orang yang sama, `'Ok'` = dimodifikasi orang lain (kemungkinan supervisor). |

### Business Rules (Confirmed)
- MOL berasal dari dua sumber: **Inspeksi** (`summaryreference=0`, punya `workorderid`) atau **Additional Order** (`summaryreference=1`, tanpa WO).
- `correct_status=1` adalah gating filter utama berdasarkan `config_mapping_mol_status.csv` (kombinasi `mol_status` × `isactive` × `workflow_status` × `require_mono`).
- MOL bisa dengan atau tanpa material; pooling validation berlaku untuk keduanya dengan fallback material-level → detail-level.
- Special case: `actionremedycode='AR0010'` tanpa material → `canactiondigimandelete` di-override jadi `1`.

### Open Questions for Business
- **`MaterialStatus`** dipakai untuk visual/aksi apa di Power BI? *(lihat item Pending Confirmation di atas)*
- Apakah semua site/tenant memakai format SAP MO number dengan prefix `'00'`? Jika ada yang berbeda, ini akan silently broken.
- Apakah field `canactiondigimandelete` dkk memang sudah tidak terpakai di aplikasi, sehingga aman dihapus dari CTE?

---

## 3. Inspection Compliance

**Views:** `am.vw_report_iams_get_molist` (dimensi MO) + `am.vw_report_iams_get_assignment` (dimensi personel)
**Business Question:** Apakah setiap MO Inspection sudah dikerjakan oleh inspector yang ditugaskan, kapan dikerjakan, dan apa status aktualnya?

> Dua view ini saling melengkapi — `get_molist` fokus ke dimensi MO (equipment, section, status), `get_assignment` fokus ke dimensi personel (inspector, SPV, waktu). Consumer PBI men-join keduanya via `MOId = Id`.

### Gap & Proposed Solution

| # | Issue | View | Severity | Proposed Solution |
|---|-------|------|:---:|---|
| 1 | **Timezone overdue-check berbeda** — `get_molist` pakai UTC murni, `get_assignment` pakai local time via `utcoffset` | Lintas view | <span class="sev-high">High</span> | Lihat Cross-Cutting #1. WO yang sama bisa mendapat status berbeda (`INF/ING` vs `INA/INB`) di batas tengah malam. |
| 2 | **Sumber waktu "selesai" berbeda** — `get_molist` pakai `tp.modifiedat`, `get_assignment` pakai `max(taskpersonalizedlog.enddate)` | Lintas view | <span class="sev-high">High</span> | Tentukan satu sumber canonical. Jika `taskpersonalizedlog.enddate` dianggap lebih akurat (audit trail), tambahkan CTE yang sama ke `get_molist`. |
| 3 | **Tidak ada `TaskPersonalizedId`** di output `get_assignment` — join ke `get_molist` hanya via `MOId`, berisiko cartesian product untuk WO dengan banyak inspector | `get_assignment` | <span class="sev-high">High</span> | Tambahkan kolom `TaskPersonalizedId` ke output `get_assignment` agar PBI bisa join tepat per assignment, bukan per WO. |
| 4 | Site join via `d.siteid` (site inspector) — jika inspector tidak punya `siteid`, **seluruh datetime jadi NULL** dan baris hilang dari hasil | `get_assignment` | <span class="sev-medium">Medium</span> | Validasi data quality `useremploymentprofile.siteid` — pastikan semua inspector aktif punya siteid terisi. Pertimbangkan fallback ke `site` WO jika inspector tidak punya site. |
| 5 | `CTE site` diambil tapi **dead code** (tidak dipakai) | `get_molist` | <span class="sev-medium">Medium</span> | Hapus CTE yang tidak terpakai, atau terapkan `utcoffset` agar konsisten dengan `get_assignment` (selaras dengan solusi #1). |
| 6 | `MOUtcDate` = duplikat `ScheduleDate` (sama-sama `wo.schedulestartdate`, tidak ada konversi) | `get_molist` | <span class="sev-medium">Medium</span> | Klarifikasi maksud kolom — jika `MOUtcDate` seharusnya beda timezone dari `ScheduleDate`, perbaiki logic; jika tidak, hapus salah satu kolom. |
| 7 | `CompletedUtcDate` & `CompletedUtcDate22` selalu NULL | `get_assignment` | <span class="sev-medium">Medium</span> | Lihat Cross-Cutting #7 — konfirmasi roadmap pengisian atau hapus kolom. |
| 8 | `AssignedBy` naming misleading — isinya orang yang *di-assign*, bukan yang melakukan assign | `get_molist` | <span class="sev-low">Low</span> | Rename ke `InspectorId` untuk selaras dengan penamaan di `get_assignment`. |
| 9 | `ATWRT` = duplikat `SectionTypeName` | `get_molist` | <span class="sev-low">Low</span> | Pertahankan jika untuk kompatibilitas penamaan SAP; dokumentasikan alasannya agar tidak dianggap bug. |
| 10 | Kolom "Utc" sudah local time | `get_assignment` | <span class="sev-low">Low</span> | Lihat Cross-Cutting #6. |
| 11 | `SPVName` bisa berisi akun sistem (jika `tp.createdby` adalah scheduler/sistem) | `get_assignment` | <span class="sev-low">Low</span> | Validasi terhadap data aktual — exclude service account jika ditemukan. |
| 12 | 8 kolom SAP placeholder selalu NULL | `get_molist` | <span class="sev-low">Low</span> | Lihat Cross-Cutting #7. |
| 13 | `mincreatedat` (earliest assignment) dihitung lintas semua TP dalam satu task — semua inspector dalam task yang sama berbagi nilai yang identik | `get_molist` | <span class="sev-low">Low</span> | Dokumentasikan sebagai known limitation, atau ubah window function jika bisnis butuh nilai per-inspector. |

### Business Rules (Confirmed)
- Status resolusi (INA/INB/INE/INF/ING/INI) berdasarkan `config_mapping_wo_status.csv` — identik di kedua view.
- Granularitas: per WO per taskpersonalized — satu WO dengan N inspector menghasilkan N baris di masing-masing view.
- `tenantcode='MKP'` hardcoded — lihat Cross-Cutting #2.
- SPV didefinisikan sebagai `tp.createdby` (yang membuat record assignment).

### Open Questions for Business
- Timezone mana yang jadi acuan resmi untuk overdue check? *(lihat Cross-Cutting #1)*
- `taskpersonalizedlog.enddate` atau `tp.modifiedat` — mana yang jadi acuan KPI compliance untuk "waktu TP selesai"?
- Bagaimana cara PBI men-join kedua view saat ini? Apakah sudah ada handling untuk WO dengan banyak inspector?
- Apakah `config_wicope_manual.csv` seharusnya direferensikan di salah satu view ini, atau memang murni dipakai di layer PBI?

---

## 4. Lead Time Report

**View:** `am.vw_report_iams_f_am_digiman_leadtime`
**Business Question:** Berapa lama waktu yang dibutuhkan dari penugasan inspector hingga eMOL disetujui — diukur per tahapan: assignment → submit inspeksi → buat eMOL → approval.

> Sudah dikonfirmasi: laporan ini **by design** hanya menampilkan WO yang sudah menyelesaikan full cycle (approved). WO yang masih berjalan tidak akan muncul.

### Gap & Proposed Solution

| # | Issue | Severity | Proposed Solution |
|---|-------|:---:|---|
| 1 | `fullcycle_leadtime_target` sering NULL — join `lower(sectiontype.name) = lower(config.type_status)` bergantung pada kesamaan nama section type persis; beda tenant bisa beda nama | <span class="sev-medium">Medium</span> | *(Sudah dikonfirmasi sebagai risiko nyata.)* Bangun mapping table yang lebih robust (site + section type code, bukan name string) untuk target SLA, atau normalisasi penamaan section type di config per site. |
| 2 | Multiple `workflowtransaction Complete` per WO bisa menghasilkan baris ganda per siklus re-approval | <span class="sev-medium">Medium</span> | Profilasi data untuk memastikan apakah kasus ini benar terjadi. Jika ya, putuskan aturan: ambil approval terakhir (`MAX(modifiedat)`) saja per WO. |
| 3 | `SELECT DISTINCT` sebagai safeguard duplikasi — lihat Cross-Cutting #5 | <span class="sev-medium">Medium</span> | Lihat solusi cross-cutting. |
| 4 | TP tanpa finding → tidak akan pernah match ke `mechanicorderlist` → `leadtime_create_emol`, `leadtime_approval`, `fullcycle_leadtime` semua NULL | <span class="sev-medium">Medium</span> | *(Sudah dikonfirmasi sebagai expected behavior — WO tanpa finding memang tidak punya eMOL.)* Tidak perlu tindakan teknis, cukup dokumentasikan agar konsumen report tidak salah interpretasi NULL sebagai data hilang. |
| 5 | `leadtime_assignment` bisa negatif jika inspector ditugaskan sebelum `schedulestartdate` | <span class="sev-low">Low</span> | Tidak ada guard saat ini. Bisa ditambahkan flag "early assignment" di layer PBI, atau dibiarkan sebagai informasi valid (assignment lebih cepat dari rencana). |
| 6 | `load_date = dateadd(hour, 7, getutcdate())` — UTC+7 hardcoded | <span class="sev-low">Low</span> | Lihat Cross-Cutting #1. Ganti dengan offset dinamis per site jika ada site di luar WIB. |
| 7 | `date_id` = duplikat `schedule_date` | <span class="sev-low">Low</span> | Hapus salah satu kolom redundan (perlu cek dampak ke PBI sebelum diubah). |
| 8 | `workflowtransaction` join hanya via `referencetransactionid` tanpa filter tipe referensi — risiko false match jika ID dipakai entitas lain | <span class="sev-low">Low</span> | Tambahkan filter tipe referensi jika kolomnya tersedia di sumber data. |
| 9 | `inspection_submittedby` menyimpan usercode (bukan fullname) — representasi beda dengan kolom *by lainnya | <span class="sev-low">Low</span> | *(Sudah dikonfirmasi by design — satu baris = satu TP, jadi submittedby = inspector TP tersebut, bisa beda orang antar baris.)* Opsional: ubah ke fullname agar konsisten secara visual dengan `assignmentby`, `approvedby`, dll. |
| 10 | `TFCx3 = 72 jam` di `config_wicope_manual.csv` tidak terpakai (filter `type_id='TFC'` saja) | <span class="sev-low">Low</span> | *(Sudah dikonfirmasi sebagai dead configuration.)* Jadwalkan penghapusan baris `TFCx3` dari CSV pada siklus maintenance config berikutnya. |

### Business Rules (Confirmed)
- **Hanya WO yang sudah approved** yang tampil — INNER JOIN ke `workflowtransaction WHERE status='Complete'` adalah disengaja.
- **Granularitas per WO per TP per finding** — satu WO dengan beberapa inspector dan beberapa finding menghasilkan beberapa baris, ini expected.
- **`inspection_submittedby`** = usercode milik TP tersebut, valid karena satu inspeksi bisa dikerjakan lebih dari satu orang (multiple `taskpersonalized` per task) — setiap baris merepresentasikan satu assignment.
- Target SLA full cycle: 24 jam (`TFC`), berlaku untuk site/unit type yang match di config.
- `user` tanpa filter `isactive` — disengaja, report historis.

### Open Questions for Business
- Apakah semua site benar-benar di zona waktu WIB (UTC+7), atau ada site WITA/WIT yang butuh offset berbeda?
- Boleh dijadwalkan kapan baris `TFCx3` dihapus dari `config_wicope_manual.csv`?
- Apakah nama `sectiontype` per site sudah terstandarisasi, atau memang bervariasi antar tenant sehingga target SLA perlu pendekatan mapping yang berbeda?

---

## 5. Improvement Initiative: Multi-Level Approval

**View terdampak:** `am.vw_report_iams_f_am_digiman_dorder` (D'Order Result & Ordering Compliance)
**Sifat:** Bukan gap dari kondisi existing — ini desain perbaikan untuk mengikuti kapabilitas baru aplikasi Digiman+ yang sekarang mendukung approval **berjenjang** (1, 2, atau lebih level), bukan lagi satu level approval seperti yang dibaca SQL saat ini.

### Konteks

Order (eMOL) saat ini disetujui lewat satu `WorkflowTransaction` per Order. SQL existing hanya membaca header-nya (satu status, satu approver, satu tanggal) — belum aware terhadap step-level approval yang sekarang ada.

```
1 Inspection (WO)        = N Findings              = 1 Order
1 Finding                = 1 eMOL
1 Order                  = 1 WorkflowTransaction
1 WorkflowTransaction    = N WorkflowTransactionStep
1 WorkflowTransactionStep → 1 WorkflowStep (master: nama level, urutan, min approver)
```

Approval terjadi di level **Order**, bukan di level eMOL — semua eMOL di bawah Order yang sama berbagi approval chain yang identik. Grain `dorder` (per-eMOL) **tidak berubah** pada desain ini.

### State Machine (Ringkasan)

1. **Submit** — step `StepOrder=0` ("User Submit") dibuat dengan `Status='Submitted'`; bersamaan, seluruh step approval berikutnya langsung dibuat semua dengan `Status='In Progress'` (bukan satu-satu saat gilirannya tiba). Header `WorkflowTransaction.Status` ikut jadi `In Progress`.
2. **Approve di level N** — step `StepOrder=N` berubah `In Progress` → `Approved`, tercatat di `ModifiedBy`/`ModifiedAt`. Header tetap `In Progress` selama masih ada step yang belum `Approved`.
3. **Belum ada fitur reject** — alur hanya maju, tidak ada percabangan mundur/revisi.
4. **Selesai** — semua step `Approved` → header `WorkflowTransaction.Status` berubah jadi `Complete`, dan `CurrentWorkflowStepId` kembali NULL.

### Desain Perubahan (Ringkasan)

| Komponen | Perubahan |
|---|---|
| View `dorder` (grain tidak berubah, tetap per-eMOL) | Ganti kolom approval single-level (`ApprovalName`, `ApprovalDateUTC`) dengan ringkasan: `ApprovalTotalLevel`, `ApprovalApprovedLevel`, `ApprovalCurrentLevel`, `ApprovalCurrentLevelName`, `FinalApprovedBy`, `FinalApprovedDate` |
| View baru — audit trail | `vw_report_iams_f_am_digiman_order_approval_detail` (usulan nama) — satu baris per Order per level approval, untuk drill-through di PBI tanpa mengubah grain `dorder` |
| Penyederhanaan kunci | `WorkflowTransaction.CurrentWorkflowStepId` menunjuk langsung ke level pending — tidak perlu aggregasi `MIN(StepOrder)` dari step |

**Contoh nilai di `dorder` per skenario:**

| Skenario | `ApprovalCurrentLevel` | `ApprovalCurrentLevelName` | `FinalApprovedBy` | `FinalApprovedDate` |
|---|---|---|---|---|
| Baru submit, pending di level 1 | `1` | `SPV Approval` | `NULL` | `NULL` |
| Sudah lewat level 1, pending di level 2 | `2` | `Manager Approval` | `NULL` | `NULL` |
| Semua level Approved (Order Complete) | `NULL` | `NULL` | `Budi Santoso` | `2026-06-28 14:32:00` |

`ApprovalCurrentLevel*` dan `FinalApproved*` saling eksklusif — selama Order berjalan hanya yang pertama terisi, begitu selesai berbalik jadi hanya yang kedua terisi.

**Kenapa perlu view audit trail terpisah:** Ringkasan di `dorder` hanya menjawab "level berapa sekarang" dan "siapa approver terakhir" — tidak bisa menjawab pertanyaan yang butuh **seluruh riwayat chain**, misalnya siapa approve di level 1 (bukan cuma level terakhir), Order macet di level mana dan sudah berapa lama, atau level mana yang paling sering jadi bottleneck lintas banyak Order. View detail menjawab itu dengan grain per Order per level (satu Order 3 level → 3 baris), dipakai sebagai drill-through page di PBI tanpa mengubah grain tabel utama.

### Status Keputusan & Diskusi

| # | Topik | Status |
|---|---|:---:|
| 1 | PK header `WorkflowTransaction` = `Id` | <span class="sev-resolved">Resolved</span> |
| 2 | `MinApprover` tidak mengubah cara hitung (tetap 1 baris step per level) | <span class="sev-resolved">Resolved</span> |
| 3 | Kode `TransactionType` untuk Order approval = `'Mechanic Order'` | <span class="sev-resolved">Resolved</span> |
| 4 | `CurrentWorkflowStepId` kembali NULL setelah Complete | <span class="sev-resolved">Resolved</span> |
| 5 | Step "User Submit" dikeluarkan dari audit trail | <span class="sev-resolved">Decided</span> |
| 6 | Adopsi kolom `SubmittedBy`/`SubmittedDate` di `dorder` | <span class="sev-open">Open — bahas dengan engineer</span> |

**Catatan implementasi tambahan:** join existing SQL production ke `workflowtransaction` (`mol.workorderid = wft1.referencetransactionid`) saat ini **belum memfilter `TransactionType`** — karena tabel ini polymorphic/shared antar jenis transaksi, filter ini perlu ditambahkan saat implementasi, bukan hanya untuk fitur baru tapi juga memperbaiki risiko di logic yang sudah ada.

---

## Consolidated Action Items

Urutan berdasarkan severity — disarankan dikerjakan dari atas ke bawah.

| # | Report | Issue | Severity | Decision Needed From |
|---|--------|-------|:---:|---|
| 1 | Cross-Cutting | Timezone tidak konsisten antar view | <span class="sev-high">High</span> | Engineer + Business (konfirmasi zona waktu site) |
| 2 | Cross-Cutting | `tenantcode='MKP'` hardcoded di 5 view | <span class="sev-high">High</span> | Business (rencana multi-tenant?) |
| 3 | Cross-Cutting | Status resolution silent-drop jika status baru belum ada di config | <span class="sev-high">High</span> | Engineer (tambah fallback/monitoring) |
| 4 | D'Order Result | `mechanicorderlist` isactive dikomentari, hanya andalkan `correct_status` | <span class="sev-high">High</span> | Engineer |
| 5 | D'Order Result | SAP MO number prefix `'00'` hardcoded | <span class="sev-high">High</span> | Engineer + Business (konfirmasi format SAP per site) |
| 6 | Inspection Compliance | Timezone overdue-check beda antara `get_molist` & `get_assignment` | <span class="sev-high">High</span> | Engineer + Business |
| 7 | Inspection Compliance | Sumber "waktu selesai" beda (`modifiedat` vs log `enddate`) | <span class="sev-high">High</span> | Business (pilih sumber canonical) |
| 8 | Inspection Compliance | Tidak ada `TaskPersonalizedId` di `get_assignment` → risiko cartesian join | <span class="sev-high">High</span> | Engineer |
| 9 | D'Order Result | `MaterialStatus` — tujuan bisnis belum dikonfirmasi | <span class="sev-pending">Pending</span> | Business |
| 10 | Cross-Cutting & semua view | Filter `isactive` pada `user` tidak konsisten | <span class="sev-medium">Medium</span> | Business (tetapkan kebijakan baku) |
| 11 | Lead Time | `fullcycle_leadtime_target` sering NULL karena name-matching section type | <span class="sev-medium">Medium</span> | Engineer + Business |
| 12 | D'Inspect Result | INNER JOIN `damagecodegroup` — silent drop finding | <span class="sev-medium">Medium</span> | Engineer |
| 13 | D'Order Result | `canactiondigimandelete` dkk dihitung tapi tidak diekspos — dead code? | <span class="sev-medium">Medium</span> | Business + Engineer |
| 14 | D'Order Result | `poolingstatus` magic string `MOJ`/`MOK` tidak terdokumentasi | <span class="sev-medium">Medium</span> | Business |
| 15 | D'Order Result (Improvement) | Adopsi kolom `SubmittedBy`/`SubmittedDate` di `dorder` — lihat Chapter 5 | <span class="sev-open">Open</span> | Engineer + Business |
| *Sisanya* | Semua | Lihat tabel per-halaman di atas (Low severity / sudah confirmed) | <span class="sev-low">Low</span> | — |

---

*Dokumen ini disusun berdasarkan analisa SQL view per 2026-06-30. Detail teknis lengkap per view tersedia di file dokumentasi masing-masing pada folder `digiman+/report/transaction-report/`.*
