# Workcard List Sync Logic

Dokumen ini mendefinisikan logic pengambilan data workcard list di Digiman+ untuk **PM Shutdown** dan **BD Corrective**.

*Last updated: 2026-07-27*

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

## Local Cleanup — Client-Side Pruning (SUBMIT & IN PROGRESS yang Aged Out)

> ✅ **Section ini ditambahkan 2026-07-27**, hasil review lanjutan, dan sudah disetujui untuk masuk scope. Dicatat sebagai addendum di [IAMS30-4422](https://bukittechnology.atlassian.net/browse/IAMS30-4422) — di luar scope asli ticket tsb (yang membahas full-refresh-signal saat `LastSyncDate` basi), jadi ditulis sebagai kondisi terpisah di sana.

**Masalah:** Workcard SUBMIT/IN PROGRESS yang lama tidak disentuh (`ModifiedUtcDate` tidak pernah ter-update) tidak akan pernah tertangkap oleh delta sync (`ModifiedUtcDate >= LastSyncDate`) — karena "keluar dari window N hari" itu bukan event perubahan data, murni berlalunya waktu. Akibatnya device bisa terus menyimpan workcard yang sebetulnya sudah basi (kalau di-Fresh-Install hari ini, tidak akan muncul lagi), tapi tidak pernah dibersihkan lewat mekanisme delta sync biasa.

**Prinsip:** kalau sebuah record lokal **tidak akan lolos syarat Fresh Install kalau dicek hari ini, hapus dia dari device.** Berlaku untuk semua status yang dievaluasi Fresh Install berdasarkan tanggal — `SUBMIT` dan `IN PROGRESS`. `FINISH`/`CANCEL` tidak perlu masuk sini karena sudah ditangani terpisah lewat delta sync berbasis perubahan status (lihat [After Last Sync](#after-last-sync)).

**Solusi — pruning dilakukan di client, bukan lewat query delta BE:**

1. **Exposure baru diperlukan** — nilai `N` (`LAST_DAY_RANGE`, lihat [Konfigurasi Range](#konfigurasi-range)) saat ini belum di-expose ke mobile. Perlu ditambahkan lewat config/settings endpoint.
2. Setiap sync, FE menghapus record lokal yang sudah keluar dari window N hari — menggunakan **field acuan yang sama persis dengan logic Fresh Install** per status (bukan cuma `ModifiedUtcDate`):

| Status | Kondisi | Field Acuan untuk Prune |
|---|---|---|
| `SUBMIT` | — | `ProjectFinish < today - N hari` → hapus lokal |
| `IN PROGRESS` | `NotifNo` terisi **dan** `FinishBreakdown` terisi | `FinishBreakdown < today - N hari` → hapus lokal |
| `IN PROGRESS` | `NotifNo` terisi, `FinishBreakdown` NULL | `ModifiedUtcDate < today - N hari` → hapus lokal |
| `IN PROGRESS` | `NotifNo` NULL | `ModifiedUtcDate < today - N hari` → hapus lokal |

3. Ini murni pembersihan lokal — **tidak perlu round-trip ke BE** untuk keputusan hapusnya, karena device sudah punya semua data (record lokal + nilai `N`) untuk menentukan sendiri record mana yang sudah tidak relevan.
4. Beda mekanisme dari penghapusan `FINISH`/`CANCEL` di [After Last Sync](#after-last-sync) — itu dipicu **perubahan status** (di-drive server lewat delta sync), sementara ini dipicu **berlalunya waktu** (di-drive client, independen dari perubahan data apapun).

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
