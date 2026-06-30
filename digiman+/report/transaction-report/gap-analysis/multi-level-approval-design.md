# Desain: Multi-Level Approval di D'Order Result & Ordering Compliance

**Konteks:** Order (eMOL) saat ini disetujui lewat satu `WorkflowTransaction` per Order. Aplikasi Digiman+ sekarang mendukung approval **berjenjang** (1, 2, atau lebih level) lewat tabel `WorkflowTransactionStep` + master `WorkflowStep`. View `vw_report_iams_f_am_digiman_dorder.sql` saat ini hanya membaca `WorkflowTransaction` header (satu status, satu approver, satu tanggal) — belum aware terhadap step-level ini. Dokumen ini desain perubahannya.

---

## 1. Hierarki Data (Confirmed)

```
1 Inspection (WO)        = N Findings              = 1 Order
1 Finding                = 1 eMOL
1 Order                  = 1 WorkflowTransaction
1 WorkflowTransaction    = N WorkflowTransactionStep
1 WorkflowTransactionStep → 1 WorkflowStep (master: nama level, urutan, min approver)
```

**Implikasi penting:** Approval terjadi di level **Order**, bukan di level eMOL. Semua eMOL di bawah Order yang sama berbagi approval chain yang identik. Grain view utama (`dorder`, per-eMOL) **tidak boleh diturunkan** ke per-step — itu akan membuat satu eMOL terlihat seperti punya banyak approval padahal approval-nya milik Order induknya.

---

## 2. Skema Sumber (Confirmed)

**`WorkflowTransaction`** (header — lihat detail lengkap di [architecture/workflow.md](../../../architecture/workflow.md))
| Kolom Relevan | Keterangan |
|---|---|
| `Id` | PK, target join dari `WorkflowTransactionStep.WorkflowTransactionId` |
| `ReferenceTransactionId` | Sama dengan yang dipakai SQL existing (`workorderid` / `mechanicordersummaryid`) |
| `TransactionType` | **Tabel ini polymorphic** — perlu filter tambahan di join (lihat Bagian 6) |
| `CurrentWorkflowStepId` | FK ke `WorkflowStep` — **langsung menunjuk level yang sedang pending**, menyederhanakan perhitungan `ApprovalCurrentLevel` (tidak perlu aggregasi `MIN(StepOrder)` dari step) |
| `WorkflowSiteId` | Tersedia langsung di header, bisa dipakai untuk lookup total level config jika dibutuhkan |

**`WorkflowTransactionStep`**
| Kolom | Keterangan |
|---|---|
| `Id` | PK |
| `WorkflowTransactionId` | FK ke header `WorkflowTransaction` |
| `WorkflowStepId` | FK ke master `WorkflowStep` |
| `Status` | `Submitted` (step 0) → `In Progress` → `Approved` |
| `IsActive` | |
| `CreatedAt`, `CreatedBy` | |
| `ModifiedAt`, `ModifiedBy` | Saat `Status` berubah jadi `Approved`, ini adalah tanggal & approver level tersebut |

**`WorkflowStep`** (master, contoh data untuk satu `WorkflowSiteId`)
| Id | WorkflowSiteId | Name | StepOrder | MinApprover |
|---|---|---|---|---|
| 10 | 3 | User Submit | 0 | 0 |
| 11 | 3 | SPV Approval | 1 | 1 |

`StepOrder` menentukan urutan level. `WorkflowSiteId` mengindikasikan **jumlah level approval bisa berbeda per site** — site lain bisa punya 2, 3, atau lebih level setelah Submit. *(Lookup eksplisit ke master per site belum diperlukan sekarang — lihat asumsi di bawah.)*

---

## 3. State Machine

1. **Submit** → satu baris `WorkflowTransactionStep` untuk step `StepOrder=0` dibuat dengan `Status='Submitted'`. **Bersamaan**, seluruh step berikutnya (sesuai jumlah `WorkflowStep` master untuk workflow tersebut) langsung dibuat semua dengan `Status='In Progress'` — bukan dibuat satu per satu saat gilirannya tiba. Header `WorkflowTransaction.Status` ikut menjadi `In Progress`.
2. **Approve di level N** → baris step dengan `StepOrder=N` berubah dari `In Progress` → `Approved`, tercatat di `ModifiedBy`/`ModifiedAt`. Header tetap `In Progress` selama masih ada step yang belum `Approved`.
3. **Belum ada fitur reject** — alur hanya maju (`Submitted`/`In Progress` → `Approved`), tidak ada percabangan mundur/revisi yang perlu ditangani report saat ini.
4. **Selesai** → ketika seluruh step `StepOrder ≥ 1` berstatus `Approved`, header `WorkflowTransaction.Status` berubah dari `In Progress` menjadi `Complete` — **Confirmed**, konsisten dengan perilaku yang **sudah dipakai** SQL saat ini (`coalesce(wft1.status, wft2.status) = 'Complete'`) dan tidak berubah.

**Konsekuensi desain:** karena semua step *pre-created* sejak submit, **total level** dan **level saat ini** bisa dihitung langsung dari baris `WorkflowTransactionStep` yang sudah ada — tidak perlu join terpisah ke master `WorkflowStep` per `WorkflowSiteId` untuk tahu "berapa total level seharusnya". Join ke `WorkflowStep` tetap diperlukan untuk dapat `StepOrder` (urutan) dan `Name` (nama level), tapi bukan untuk menghitung total.

---

## 4. Desain Perubahan Report

### A. View utama `dorder` — grain tidak berubah (tetap per-eMOL)

Ganti kolom approval single-level (`ApprovalName`, `ApprovalDateUTC`, `ModifiedUtdDate`) dengan ringkasan multi-level:

| Kolom Baru | Definisi | Sumber |
|---|---|---|
| `ApprovalTotalLevel` | Jumlah step approval (StepOrder ≥ 1) untuk `WorkflowTransactionId` Order ini | `COUNT(*)` step WHERE StepOrder > 0 |
| `ApprovalApprovedLevel` | Jumlah step yang sudah `Approved` | `SUM(CASE WHEN Status='Approved' THEN 1 ELSE 0 END)` |
| `ApprovalCurrentLevel` | Level yang sedang pending | `WorkflowTransaction.CurrentWorkflowStepId → WorkflowStep.StepOrder` — **langsung dari header**, tidak perlu aggregasi `MIN(StepOrder)` dari step |
| `ApprovalCurrentLevelName` | Nama level yang sedang pending (role, bukan nama orang — lihat catatan di bawah) | `WorkflowTransaction.CurrentWorkflowStepId → WorkflowStep.Name` |
| `FinalApprovedBy` | Nama approver level terakhir, **hanya terisi jika semua level Approved** (header Complete) | `ModifiedBy` step dengan `StepOrder` tertinggi, `Status='Approved'` |
| `FinalApprovedDate` | Tanggal approval level terakhir | `ModifiedAt` step tersebut |
| `SubmittedBy` *(opsional — untuk didiskusikan)* | Siapa yang submit Order ini | `CreatedBy` dari step `StepOrder=0` ("User Submit") |
| `SubmittedDate` *(opsional — untuk didiskusikan)* | Kapan Order disubmit | `CreatedAt` dari step `StepOrder=0` — **bukan** `ModifiedAt`, karena step Submit tidak mengalami transisi status lanjutan, jadi yang relevan adalah kapan baris itu dibuat |

> **Disederhanakan:** `WorkflowTransaction` header punya kolom `CurrentWorkflowStepId` yang menunjuk langsung ke level yang sedang pending — `ApprovalCurrentLevel`/`ApprovalCurrentLevelName` tinggal join sekali ke `WorkflowStep`, tidak perlu hitung `MIN(StepOrder) WHERE Status='In Progress'` dari `WorkflowTransactionStep` seperti rencana awal. `ApprovalTotalLevel` dan `ApprovalApprovedLevel` tetap perlu aggregasi dari `WorkflowTransactionStep` karena header tidak menyimpan keduanya.

> **Confirmed:** Siapa yang approve diambil langsung dari `ModifiedBy` (nama) dan `ModifiedAt` (tanggal) di `WorkflowTransactionStep` — cukup untuk `ApprovedBy`/`ApprovedDate` di view detail maupun `FinalApprovedBy`/`FinalApprovedDate` di `dorder`. Saat status masih `In Progress`, `ModifiedBy` **masih NULL** — kolom ini hanya terisi begitu step benar-benar `Approved`.
>
> **Target approver di level pending sengaja tidak ditampilkan** — bukan keterbatasan data, tapi keputusan bisnis: satu level bisa punya lebih dari satu user yang eligible untuk approve (selaras dengan `MinApprover` di master `WorkflowStep`), jadi tidak ada satu "nama target" yang representatif untuk ditampilkan. `ApprovalCurrentLevelName` cukup menampilkan nama **level/role** (misal "SPV Approval"), bukan nama orang.
>
> **`SubmittedBy`/`SubmittedDate` masih opsional** — belum diputuskan, ditambahkan ke desain sebagai bahan diskusi kalau-kalau dashboard butuh tahu siapa yang memulai pengajuan Order, terpisah dari siapa yang approve. Tidak ada biaya teknis besar untuk menambahkannya (cukup satu join tambahan ke step `StepOrder=0`), jadi keputusan murni berdasarkan kebutuhan dashboard.

**Contoh nilai per skenario:**

| Skenario | `ApprovalCurrentLevel` | `ApprovalCurrentLevelName` | `FinalApprovedBy` | `FinalApprovedDate` |
|---|---|---|---|---|
| Baru submit, pending di level 1 | `1` | `SPV Approval` | `NULL` | `NULL` |
| Sudah lewat level 1, pending di level 2 | `2` | `Manager Approval` | `NULL` | `NULL` |
| Semua level Approved (Order Complete) | `NULL` | `NULL` | `Budi Santoso` | `2026-06-28 14:32:00` |

`ApprovalCurrentLevel*` dan `FinalApproved*` **saling eksklusif** — selama Order masih berjalan, hanya `ApprovalCurrentLevel*` yang terisi; begitu selesai, berbalik jadi hanya `FinalApproved*` yang terisi (karena `CurrentWorkflowStepId` kembali NULL saat Complete).

### B. View baru — audit trail per Order per Step

**Tujuan:** Ringkasan di `dorder` (Bagian A) hanya menjawab "saat ini ada di level berapa" dan "siapa yang approve terakhir" — tidak bisa menjawab pertanyaan yang butuh **seluruh riwayat chain**, misalnya:
- Siapa yang approve di level 1, kapan? (bukan cuma level terakhir)
- Order ini macet di level mana, dan sudah berapa lama?
- Level mana yang paling sering jadi bottleneck (rata-rata durasi antar level, lintas banyak Order)?
- Audit trail lengkap untuk satu Order tertentu saat ada pertanyaan/komplain dari business.

View ini menjawab itu dengan grain **per Order per level** — satu Order dengan 3 level approval akan menghasilkan 3 baris (bukan 1 baris seperti di `dorder`), masing-masing menyimpan status, approver, dan tanggal level tersebut. Dipakai sebagai **drill-through page** di PBI: user klik satu eMOL di tabel utama → lihat detail Order-nya → tampil seluruh approval chain di halaman terpisah ini, tanpa mengubah grain tabel utama yang tetap per-eMOL.

`vw_report_iams_f_am_digiman_order_approval_detail` (nama usulan) — satu baris per Order per level **approval saja** (`StepOrder ≥ 1`). Step `StepOrder=0` ("User Submit") **tidak** masuk ke audit trail ini — sudah diputuskan untuk dikeluarkan, datanya (jika dibutuhkan) cukup lewat `SubmittedBy`/`SubmittedDate` di ringkasan `dorder` (lihat di atas), bukan sebagai baris tambahan di sini.

| Kolom | Keterangan |
|---|---|
| Order identifier (`WorkorderId`/`MechanicOrderSummaryId`, dan `MONo` untuk display) | Key ke Order, sama seperti yang dipakai `dorder` saat ini untuk join `workflowtransaction` |
| `ApprovalLevel` | `WorkflowStep.StepOrder` |
| `ApprovalLevelName` | `WorkflowStep.Name` |
| `StepStatus` | `Submitted` / `In Progress` / `Approved` |
| `ApprovedBy` | `ModifiedBy` → lookup nama, hanya terisi saat `Approved` |
| `ApprovedDate` | `ModifiedAt`, hanya terisi saat `Approved` |
| `IsCurrentStep` | `1` jika ini level `In Progress` dengan `StepOrder` terkecil di antara yang `In Progress` untuk Order tsb |

PBI bisa drill-through dari satu eMOL di `dorder` → Order-nya → lihat seluruh approval chain di view ini (cocok untuk halaman "Ordering Compliance" yang memang berfokus ke status approval, bukan ke detail material).

---

## 5. Conceptual SQL Outline

*(Nama tabel/kolom mengikuti konvensi `openrowset` yang sudah dipakai view existing — disesuaikan dengan path Delta Lake aktual saat implementasi.)*

```sql
workflowtransaction as (
    select id, referencetransactionid, transactiontype, currentworkflowstepid, [status]
    from openrowset(bulk 'assetmanagement/mkp/mkp_workflow/workflowtransaction/', ...)
    where isactive = 1
    and transactiontype = 'Mechanic Order'
),
workflowtransactionstep as (
    select id, workflowtransactionid, workflowstepid, [status], modifiedat, modifiedby
    from openrowset(bulk 'assetmanagement/mkp/mkp_workflow/workflowtransactionstep/', ...)
    where isactive = 1
),
workflowstep as (
    select id, workflowsiteid, name, steporder
    from openrowset(bulk 'assetmanagement/mkp/mkp_workflow/workflowstep/', ...)
    where isactive = 1
),
step_detail as (
    select
        wts.workflowtransactionid,
        ws.steporder,
        ws.name as stepname,
        wts.[status] as stepstatus,
        wts.modifiedby as stepapprovedby,
        wts.modifiedat as stepapproveddate
    from workflowtransactionstep wts
    inner join workflowstep ws on wts.workflowstepid = ws.id
    where ws.steporder > 0   -- exclude step "User Submit"
),
step_summary as (
    -- hanya untuk total & approved count; current level diambil dari header, bukan dari sini
    select
        workflowtransactionid,
        count(*) as approvaltotallevel,
        sum(case when stepstatus = 'Approved' then 1 else 0 end) as approvalapprovedlevel,
        max(case when stepstatus = 'Approved' then steporder end) as maxapprovedlevel
    from step_detail
    group by workflowtransactionid
),
current_level as (
    -- current level & nama level langsung dari header, tidak perlu aggregasi.
    -- INNER JOIN sengaja dipakai: saat Order Complete, CurrentWorkflowStepId
    -- kembali NULL, jadi baris ini otomatis tidak match (tidak perlu CASE WHEN tambahan)
    select
        wft.id as workflowtransactionid,
        ws.steporder as approvalcurrentlevel,
        ws.name as approvalcurrentlevelname
    from workflowtransaction wft
    inner join workflowstep ws on wft.currentworkflowstepid = ws.id
)
-- final_approval: join step_detail where steporder = maxapprovedlevel (per workflowtransactionid)
--                  dan header status = 'Complete', ambil stepapprovedby/stepapproveddate
```

`dorder` lalu LEFT JOIN `step_summary` dan `current_level` via `WorkflowTransactionId` yang sama dengan yang dipakai `wft1`/`wft2` saat ini (header `WorkflowTransaction.Id`), dengan tambahan filter `TransactionType` pada CTE `workflowtransaction` di atas.

---

## 6. Asumsi yang Perlu Diverifikasi ke Engineer

- ~~PK header `WorkflowTransaction`~~ — **Resolved.** `Id`, dikonfirmasi dari schema lengkap (lihat [architecture/workflow.md](../../../architecture/workflow.md)).
- ~~`MinApprover` di master `WorkflowStep` belum ditangani~~ — **Resolved.** Aturan otorisasi level-aplikasi, tidak mengubah cara `step_summary` menghitung (tetap satu baris step per level). Lihat detail di `architecture/workflow.md`.
- ~~Kode `TransactionType` untuk Order approval belum diketahui~~ — **Resolved.** `'Mechanic Order'`. Sudah dimasukkan ke filter CTE `workflowtransaction` di Bagian 5. **Catatan implementasi:** join existing di SQL production (`mol.workorderid = wft1.referencetransactionid`) saat ini belum memfilter `TransactionType` — perlu ditambahkan saat perubahan ini diimplementasikan, bukan cuma untuk fitur baru tapi juga memperbaiki risk di logic yang sudah ada.
- ~~Perilaku `CurrentWorkflowStepId` saat Complete~~ — **Resolved.** Kembali NULL. CTE `current_level` di Bagian 5 sudah memanfaatkan ini (INNER JOIN otomatis tidak match untuk Order yang sudah selesai, tanpa perlu CASE WHEN tambahan).
- ~~Step `StepOrder=0` ("User Submit") di audit trail~~ — **Decided.** View detail (`order_approval_detail`) hanya berisi level approval (`StepOrder ≥ 1`), step Submit dikeluarkan.
- **Open Question (bahan diskusi dengan engineer):** Apakah `SubmittedBy`/`SubmittedDate` perlu diadopsi sebagai kolom di `dorder`? Desain teknisnya sudah siap (lihat tabel di Bagian 4A — cukup satu join tambahan ke step `StepOrder=0`), tapi belum diputuskan apakah dashboard benar-benar butuh ini. Sengaja dibiarkan terbuka untuk dibahas bersama tim engineer, bukan diputuskan sepihak di dokumen ini.

---

## 7. Status

Seluruh asumsi teknis di Bagian 6 sudah resolved. Satu open question tersisa — adopsi `SubmittedBy`/`SubmittedDate` — sengaja dibawa ke diskusi dengan tim engineer, bukan diputuskan di dokumen ini. Belum ada perubahan yang dibuat ke `vw_report_iams_f_am_digiman_dorder.sql` — menunggu hasil diskusi tersebut sebelum implementasi final.
