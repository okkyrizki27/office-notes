# Workflow & Approval

*Last updated: 2026-06-30*

> **Status:** Belum lengkap — baru mencatat apa yang sudah dikonfirmasi terkait multi-level approval. Akan ditambah seiring diskusi berlanjut.

---

## Overview

Approval di Digiman+ berjalan berjenjang (multi-level) lewat tiga tabel:

```
WorkflowTransaction      — header, satu per transaksi yang butuh approval (misal satu Order/eMOL)
WorkflowTransactionStep  — satu baris per level approval untuk transaksi tersebut
WorkflowStep             — master, definisi level/urutan per WorkflowSiteId
```

Satu `WorkflowTransaction` punya **N** `WorkflowTransactionStep` (satu per level, sesuai jumlah `WorkflowStep` yang terdaftar untuk site tersebut). Jumlah level **bisa berbeda per site** karena `WorkflowStep` punya kolom `WorkflowSiteId`.

---

## Skema Tabel (Confirmed)

### `WorkflowTransaction` (header)
| Kolom | Keterangan |
|---|---|
| `Id` | PK — ini yang direferensikan `WorkflowTransactionStep.WorkflowTransactionId` |
| `WorkflowSiteId` | Site/tenant context untuk workflow ini — bisa langsung dipakai untuk lookup total level di master `WorkflowStep` tanpa perlu derive dari sitecode Order |
| `ReferenceTransactionId` | ID transaksi bisnis yang di-approve (misal `workorderid` atau `mechanicordersummaryid` untuk Order) — ini kolom yang dipakai SQL existing untuk join |
| `TransactionType` | **Tabel ini polymorphic/shared** — dipakai untuk lebih dari satu jenis transaksi, bukan cuma Order approval. `ReferenceTransactionId` saja tidak unik secara global, harus dikombinasikan dengan `TransactionType` |
| `CurrentWorkflowStepId` | FK ke `WorkflowStep` — **menunjuk langsung ke level yang sedang pending**, tidak perlu dihitung dari aggregasi step |
| `Name` | Nama workflow/transaksi |
| `Payload` | Data tambahan (kemungkinan JSON), belum relevan untuk report |
| `Status` | Status keseluruhan transaksi |
| `LastAction` | Aksi terakhir yang terjadi |
| `IsActive`, `CreatedAt`, `CreatedBy`, `ModifiedAt`, `ModifiedBy` | Audit standar |

> ⚠️ **Risk ditemukan:** SQL existing (`vw_report_iams_f_am_digiman_dorder.sql`) join ke `workflowtransaction` hanya via `ReferenceTransactionId` (`mol.workorderid = wft1.referencetransactionid`), **tanpa filter `TransactionType`**. Karena tabel ini shared antar jenis transaksi, ada risiko false-positive match jika `ReferenceTransactionId` numerik kebetulan sama dengan transaksi jenis lain. Perlu ditambahkan filter `TransactionType = '<kode untuk Order approval>'` di semua join ke tabel ini.

### `WorkflowTransactionStep`
| Kolom | Keterangan |
|---|---|
| `Id` | PK |
| `WorkflowTransactionId` | FK ke header `WorkflowTransaction` |
| `WorkflowStepId` | FK ke master `WorkflowStep` |
| `Status` | `Submitted` (step 0) → `In Progress` → `Approved` |
| `IsActive` | |
| `CreatedAt`, `CreatedBy` | |
| `ModifiedAt`, `ModifiedBy` | Terisi saat `Status` berubah jadi `Approved` — siapa & kapan approve level tersebut. **Masih NULL selama `In Progress`.** |

### `WorkflowStep` (master)
Contoh data untuk satu `WorkflowSiteId`:

| Id | WorkflowSiteId | Name | StepOrder | MinApprover |
|---|---|---|---|---|
| 10 | 3 | User Submit | 0 | 0 |
| 11 | 3 | SPV Approval | 1 | 1 |

- `StepOrder` — urutan level (0 = submit, 1 = level approval pertama, dst).
- `MinApprover` — aturan otorisasi: satu level punya sekelompok target user yang eligible, tapi cukup **N orang** (nilai `MinApprover`) dari grup itu yang approve untuk level tersebut dianggap selesai. **Bukan** berarti ada N baris `WorkflowTransactionStep` per level — tetap satu baris per level, `ModifiedBy` terisi nama siapapun dari grup yang memenuhi syarat approve.

---

## State Machine (Confirmed)

1. **Submit** — satu baris `WorkflowTransactionStep` untuk `StepOrder=0` dibuat dengan `Status='Submitted'`. **Bersamaan**, seluruh step berikutnya (sejumlah `WorkflowStep` master untuk site tersebut) langsung dibuat semua dengan `Status='In Progress'` — bukan dibuat satu-satu saat gilirannya tiba. Konsekuensi: total level & level mana yang sedang pending bisa langsung dihitung dari baris yang sudah ada, tanpa perlu lookup terpisah ke master `WorkflowStep` per site.
2. **Approve di level N** — baris step `StepOrder=N` berubah dari `In Progress` → `Approved`, `ModifiedBy`/`ModifiedAt` terisi.
3. **Belum ada fitur reject/revisi** — alur hanya maju. Tidak ada percabangan mundur ke step sebelumnya.
4. **Selesai** — ketika seluruh step `StepOrder ≥ 1` sudah `Approved`, header `WorkflowTransaction.Status` diasumsikan otomatis menjadi `Complete` *(belum diverifikasi eksplisit — lihat Open Questions)*.

**Target approver di level pending tidak ditampilkan ke user/report** — keputusan disengaja, karena satu level bisa punya lebih dari satu user eligible (selaras `MinApprover`), sehingga tidak ada satu "nama target" yang representatif. Yang ditampilkan cukup nama level/role (`WorkflowStep.Name`), bukan nama orang, sampai level itu benar-benar di-approve.

---

## Open Questions

- ~~Nama kolom PK header `WorkflowTransaction`~~ — **Resolved.** `Id`, dikonfirmasi dari schema lengkap di atas.
- ~~Kode/value `TransactionType` untuk Order approval~~ — **Resolved.** `'Mechanic Order'`.
- ~~Apakah `CurrentWorkflowStepId` ikut berubah jadi NULL saat selesai~~ — **Resolved.** Ya, kembali jadi NULL setelah `Complete`.
- Apakah step `StepOrder=0` ("User Submit") perlu ditampilkan di laporan/audit trail sebagai baris pertama (siapa submit, kapan), atau cukup level approval (`StepOrder ≥ 1`) saja yang relevan untuk report.

---

## Penerapan di Report

Detail desain perubahan report (D'Order Result & Ordering Compliance) untuk menampilkan status multi-level approval ini: [gap-analysis/multi-level-approval-design.md](../report/transaction-report/gap-analysis/multi-level-approval-design.md).

---

## Konfigurasi Workflow

TBD

---

## Integrasi dengan Form Submission

Lihat: [Form Submission](form/form-submission.md) — section Flow Submission & Approval.
