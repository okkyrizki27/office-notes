# Workcard List Sync Logic

Dokumen ini mendefinisikan logic pengambilan data workcard list di Digiman+ untuk **PM Shutdown** dan **BD Corrective**.

*Last updated: 2026-07-21*

---

## Status Dokumen

> ✅ **Rencana perbaikan di dokumen ini sudah dikonfirmasi/disetujui stakeholder** — Uda Sunardi menyetujui via email pada **2026-07-06 10:45**, setelah proposal terkirim 2026-07-03. Ref: [IAMS30-4419](https://bukittechnology.atlassian.net/browse/IAMS30-4419)
>
> Seluruh konten di bawah — kecuali section [Data Scope (Permission-based)](#data-scope-permission-based), yang sudah mencerminkan kondisi production saat ini — merupakan desain yang **disetujui tapi belum diimplementasi di code**. Ticket: [IAMS30-4420](https://bukittechnology.atlassian.net/browse/IAMS30-4420), [IAMS30-4421](https://bukittechnology.atlassian.net/browse/IAMS30-4421), [IAMS30-4422](https://bukittechnology.atlassian.net/browse/IAMS30-4422), [IAMS30-4423](https://bukittechnology.atlassian.net/browse/IAMS30-4423)

---

## Konfigurasi Range

Range hari diambil dari table `Setting` di **DPlanDB**:

| SettingCategory | SettingCode | SettingName (nilai saat ini) |
|-----------------|-------------|------------------------------|
| `WORKCARD_DIGIMAN+` | `LAST_DAY_RANGE` | `30` |

Semua filter tanggal di bawah menggunakan nilai ini sebagai `N` (jumlah hari).

---

## Fresh Install

Data dibatasi dalam range **N hari terakhir** menggunakan field tanggal yang paling relevan per kondisi.

| Status | Kondisi | Field Tanggal | Filter |
|--------|---------|---------------|--------|
| `SUBMIT` | — | `ProjectFinish` | `>= today - N hari` |
| `IN PROGRESS` | NotifNo IS NOT NULL **dan** FinishBreakdown terisi | `FinishBreakdown` | `>= today - N hari` |
| `IN PROGRESS` | NotifNo IS NOT NULL **dan** FinishBreakdown NULL | `ModifiedUtcDate` | `>= today - N hari` |
| `IN PROGRESS` | NotifNo IS NULL | `ModifiedUtcDate` | `>= today - N hari` |
| `FINISH` / `CANCEL` | — | — | ❌ Tidak diambil |

**Catatan:**
- `ProjectFinish` dipakai untuk `SUBMIT` karena `ModifiedUtcDate` bisa jauh ke belakang (saat workcard dibuat), sementara `ProjectFinish` masih dalam range relevan
- `ModifiedUtcDate` dipakai untuk INPROGRESS tanpa target finish — sebagai proxy aktivitas terakhir workcard

---

## After Last Sync

Hanya data yang berubah sejak sync terakhir. `FINISH` dan `CANCEL` diambil agar bisa di-remove dari device, tapi **tidak ditampilkan** di list.

### Kondisi Normal (LastSyncDate >= today - N hari)

Filter: `ModifiedUtcDate >= LastSyncDate`

| Status | Filter |
|--------|--------|
| `SUBMIT` | `ModifiedUtcDate >= LastSyncDate` |
| `IN PROGRESS` | `ModifiedUtcDate >= LastSyncDate` |
| `FINISH` | `ModifiedUtcDate >= LastSyncDate` — diambil untuk di-remove dari device, **tidak ditampilkan** |
| `CANCEL` | `ModifiedUtcDate >= LastSyncDate` — diambil untuk di-remove dari device, **tidak ditampilkan** |

### Kondisi LastSyncDate Terlalu Lama (LastSyncDate < today - N hari)

Jika user tidak membuka aplikasi lebih dari N hari, data di device dianggap stale sepenuhnya → **gunakan Fresh Install logic** (full refresh, replace data lokal di device).

Ini menghindari delta yang terlalu besar dan memastikan data stale terbersihkan.

---

## Data Scope (Permission-based)

Filter berdasarkan site dan section user diapply di level BE — bukan hanya di tampilan FE. BE menentukan scope data berdasarkan permission code user:

| Permission | Perilaku |
|------------|----------|
| Basic — Section ID ter-mapping ke Section Type | Hanya sync task dari section yang sesuai |
| Basic — Section ID tidak ter-mapping | Sync task dari semua section |
| All Site | Sync task dari semua site |

| Tipe | Permission Code |
|------|-----------------|
| Basic | `IAMS_Mobile_Shutdown_View` |
| All Site | `IAMS_Mobile_Shutdown_View_All_Site` (parent: `IAMS_Mobile_Shutdown_View`) |

Mapping section dilakukan melalui `OrganizationUnit` sebagai jembatan antara `User.SectionId` dan `Asset.SectionTypeCode`. Lihat [User → Asset Section Hierarchy](../../architecture/database/user-asset-relation.md).

---

## Berlaku untuk

- PM Shutdown workcard list
- BD Corrective workcard list
