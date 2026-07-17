# Workflow & Approval

*Last updated: 2026-07-16*

> **Status:** Belum lengkap — baru mencatat apa yang sudah dikonfirmasi terkait multi-level approval. Akan ditambah seiring diskusi berlanjut.
>
> **DDL real tersedia (16 Jul 2026):** lihat [`database/workflow-schema.md`](database/workflow-schema.md) — dokumen ini (`workflow.md`) ditulis dari diskusi/konfirmasi bisnis-teknis, sebagian sudah **dikonfirmasi cocok** dengan DDL real, tapi ada **banyak tabel & kapabilitas yang belum tercakup di sini sama sekali** (`Workflow` master versioned, `WorkflowSite` sebagai mapping tersendiri, `WorkflowStepActionTransition` untuk conditional routing, `Delegation`, `WorkflowHistory`, dst) — lihat catatan ⚠️ di bawah dan section "Observasi Belum Dibahas" di dokumen schema tsb.

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
| `WorkflowSiteId` | Site/tenant context untuk workflow ini — bisa langsung dipakai untuk lookup total level di master `WorkflowStep` tanpa perlu derive dari sitecode Order. **⚠️ Koreksi (16 Jul 2026, dari DDL real)**: `WorkflowSiteId` bukan site code langsung — ini FK ke tabel mapping tersendiri `WorkflowSite` (`Id` PK sendiri, kolom `WorkflowId`+`SiteCode`), yang menghubungkan `Workflow` (master, versioned) ↔ site. Lihat [`workflow-schema.md`](database/workflow-schema.md#workflowsite). |
| `ReferenceTransactionId` | ID transaksi bisnis yang di-approve (misal `workorderid` atau `mechanicordersummaryid` untuk Order) — ini kolom yang dipakai SQL existing untuk join |
| `TransactionType` | **Tabel ini polymorphic/shared** — dipakai untuk lebih dari satu jenis transaksi, bukan cuma Order approval. `ReferenceTransactionId` saja tidak unik secara global, harus dikombinasikan dengan `TransactionType`. Nilai yang sudah diketahui: `'Mechanic Order'` untuk Order/eMOL approval |
| `CurrentWorkflowStepId` | FK ke `WorkflowStep` — **menunjuk langsung ke level yang sedang pending**, tidak perlu dihitung dari aggregasi step |
| `Name` | Nama workflow/transaksi |
| `Payload` | Data tambahan (kemungkinan JSON), belum relevan untuk report |
| `Status` | Status keseluruhan transaksi |
| `LastAction` | Jenis aksi terakhir pada transaksi ini — `Submit` atau `Approve`, tergantung step terakhir yang di-actioned oleh target user. Nilainya berubah seiring transaksi berjalan (mis. `Submit` saat baru disubmit, lalu jadi `Approve` begitu level pertama di-approve, dst) |
| `IsActive`, `CreatedAt`, `CreatedBy`, `ModifiedAt`, `ModifiedBy` | Audit standar |

> ⚠️ **Risk ditemukan:** SQL existing (`vw_report_iams_f_am_digiman_dorder.sql`) join ke `workflowtransaction` hanya via `ReferenceTransactionId` (`mol.workorderid = wft1.referencetransactionid`), **tanpa filter `TransactionType`**. Karena tabel ini shared antar jenis transaksi, ada risiko false-positive match jika `ReferenceTransactionId` numerik kebetulan sama dengan transaksi jenis lain. Perlu ditambahkan filter `TransactionType = 'Mechanic Order'` di semua join ke tabel ini untuk konteks Order approval.
>
> ⚠️ **Risk yang sama ditemukan juga di `vw_report_iams_f_am_digiman_leadtime.sql`** *(dicatat 16 Jul 2026)* — view ini join `workorder` ke `workflowtransaction` (`wo.id = wft.referencetransactionid`, dipakai untuk hitung `leadtime_approval`/`approved_date`) **tanpa filter `TransactionType`** juga. Sumber risk & fix yang sama seperti di atas — tambahkan `TransactionType = 'Mechanic Order'` di join tersebut.

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

Kolom lain (sama seperti dua tabel di atas): `IsActive`, `CreatedAt`, `CreatedBy`, `ModifiedAt`, `ModifiedBy` — audit standar, belum ada yang relevan untuk report.

- `StepOrder` — urutan level (0 = submit, 1 = level approval pertama, dst).
- `MinApprover` — aturan otorisasi: satu level punya sekelompok target user yang eligible, tapi cukup **N orang** (nilai `MinApprover`) dari grup itu yang approve untuk level tersebut dianggap selesai. **Bukan** berarti ada N baris `WorkflowTransactionStep` per level — tetap satu baris per level, `ModifiedBy` terisi nama siapapun dari grup yang memenuhi syarat approve.

---

## State Machine (Confirmed)

1. **Submit** — satu baris `WorkflowTransactionStep` untuk `StepOrder=0` dibuat dengan `Status='Submitted'`. **Bersamaan**, seluruh step berikutnya (sejumlah `WorkflowStep` master untuk site tersebut) langsung dibuat semua dengan `Status='In Progress'` — bukan dibuat satu-satu saat gilirannya tiba. Header `WorkflowTransaction.Status` ikut menjadi `In Progress` saat ini. Konsekuensi: total level & level mana yang sedang pending bisa langsung dihitung dari baris yang sudah ada, tanpa perlu lookup terpisah ke master `WorkflowStep` per site.
2. **Approve di level N** — baris step `StepOrder=N` berubah dari `In Progress` → `Approved`, `ModifiedBy`/`ModifiedAt` terisi. Header `WorkflowTransaction.Status` tetap `In Progress` selama masih ada step yang belum `Approved`.
3. **Belum ada fitur reject/revisi** — alur hanya maju. Tidak ada percabangan mundur ke step sebelumnya.
4. **Selesai** — ketika seluruh `WorkflowTransactionStep` (`StepOrder ≥ 1`) sudah `Approved`, header `WorkflowTransaction.Status` berubah dari `In Progress` menjadi `Complete`, dan `CurrentWorkflowStepId` kembali NULL.

> **⚠️ Perlu diverifikasi ulang (16 Jul 2026, dari DDL real)**: poin 3 di atas ("alur hanya maju, linear berdasarkan `StepOrder`") ditulis dari diskusi, tapi DDL real punya tabel `WorkflowStepActionTransition` dengan kolom `Condition` + `PriorityCondition` + `NextWorkflowStepId` — struktur khas **conditional/dynamic step routing**, bukan cuma `StepOrder + 1` linear. Belum jelas apakah kapabilitas ini aktif dipakai (mis. ada `Condition` non-trivial di data real) atau cuma skema yang disiapkan tapi belum diaktifkan. **Jangan asumsikan alur pasti linear** sampai ini dikonfirmasi ke engineer — lihat [`workflow-schema.md`](database/workflow-schema.md#workflowstepactiontransition).

**Target approver di level pending tidak ditampilkan ke user/report** — keputusan disengaja, karena satu level bisa punya lebih dari satu user eligible (selaras `MinApprover`), sehingga tidak ada satu "nama target" yang representatif. Yang ditampilkan cukup nama level/role (`WorkflowStep.Name`), bukan nama orang, sampai level itu benar-benar di-approve. *(Catatan 16 Jul 2026: tabel `WorkflowTransactionUser` di DDL real kemungkinan besar adalah data konkret target approver ini — datanya memang ada di DB, cuma sengaja tidak dipakai di UI/report per keputusan di atas.)*

---

## Open Questions

- Apakah step `StepOrder=0` ("User Submit") perlu ditampilkan di laporan/audit trail sebagai baris pertama (siapa submit, kapan), atau cukup level approval (`StepOrder ≥ 1`) saja yang relevan untuk report.
- **(Baru, 16 Jul 2026)** Apakah `WorkflowStepActionTransition` (conditional routing) aktif dipakai di production, atau murni skema yang disiapkan tapi belum diaktifkan? Menentukan apakah asumsi "alur linear" di State Machine di atas masih valid.
- ~~Apakah `Delegation`/`DelegationTransactionType` (delegasi approval antar user) sudah diperhitungkan dalam resolusi "siapa yang bisa approve" di runtime~~ — **✅ dijawab (16 Jul 2026)**: skema disiapkan untuk kebutuhan masa depan, **fiturnya belum pernah dibuild**. Jadi delegasi **tidak** memengaruhi resolusi approver saat ini — aman diabaikan dari logic/report manapun sampai fitur ini benar-benar diaktifkan.
- **(Baru, 16 Jul 2026)** `WorkflowHistory` (per-aksi, multi-baris) vs `WorkflowTransactionStep.ModifiedBy` (1 nilai, ke-overwrite) — mana yang jadi sumber audit trail yang benar untuk kebutuhan report ke depan? Perlu dicek apakah `WorkflowHistory` sudah dipakai di SQL manapun.

---

## Penerapan di Report

Detail desain perubahan report (D'Order Result & Ordering Compliance) untuk menampilkan status multi-level approval ini: [gap-analysis/multi-level-approval-design.md](../report/transaction-report/gap-analysis/multi-level-approval-design.md).

---

## Konfigurasi Workflow

Skema tabel konfigurasi (master) sudah tersedia lewat DDL real — lihat [`workflow-schema.md`](database/workflow-schema.md) section "Workflow Definition (Master)": `Workflow` (root, versioned) → `WorkflowSite` (mapping ke site) → `WorkflowStep` (level) → `WorkflowStepApprover` (siapa eligible per level) → `WorkflowStepAction`/`WorkflowActionProcess` (automated action per step, mis. webhook). Narasi bisnis/cara admin men-setup ini **masih TBD** — baru skema tabelnya yang diketahui, belum proses/UI konfigurasinya.

---

## Integrasi dengan Form Submission

Lihat: [Form Submission](form/form-submission.md) — section Flow Submission & Approval.
