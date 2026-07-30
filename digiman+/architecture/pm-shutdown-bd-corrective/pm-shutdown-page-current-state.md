# PM Shutdown Page Revamp — Current State

Dokumen ini mendeskripsikan kondisi halaman list **PM Shutdown** di Mobile Digiman+ pasca revamp (Release 4.0.0).

*Last updated: 2026-07-03*
*Referensi Jira: [IAMS30-3603](https://bukittechnology.atlassian.net/browse/IAMS30-3603)*

---

## Kriteria Data List PM Shutdown

Data yang ditampilkan di halaman list PM Shutdown:

| Field | Nilai |
|-------|-------|
| `Status` | `IN ('SUBMIT', 'INPROGRESS')` — status `SUBMIT` ditampilkan sebagai **"Open"** di UI |
| `ExecutionType` | `IN ('Schedule', 'Other')` |
| `IsActive` | `= 1` |
| `NotifNoStatus` | **NOT contains** `NOCO` (dari Settings `EXECUTION_NOTIFSTATUS` / `NOTIF_STATUS_EXCLUDED_FROM_INPROGRESS`) |
| `UnitStatus` | contains `IDWP`, `INPR` (dari Settings `EXECUTION_UNITSTATUS` / `UNIT_INPROGRESS`) |

> `NotifNoStatus` di sini **NOT contains** — ini kebalikan dari Outstanding Administration yang **contains**. List utama menampilkan workcard yang **belum** outstanding; Outstanding Administration menampilkan yang **sudah** outstanding.

---

## API & Sync Logic

PM Shutdown dan sub-fitur Outstanding Administration **menggunakan satu API yang sama**. Pembedaan antara list utama dan Outstanding Administration dilakukan di sisi client berdasarkan filter `NotifNoStatus` (NOT contains vs contains) dari data yang sudah tersync.

Sync logic: lihat [Workcard Sync Logic](workcard-sync-logic.md).

---

## Perubahan Filter (vs sebelum revamp)

| Filter | Perubahan |
|--------|-----------|
| **Past Due** | Dipindah dari "Schedule Start by" → jadi filter tersendiri + tampilkan **total count** |
| **Today** | Sama seperti Past Due |
| **Status** | Nama lama: "Work Status" → sekarang "Status" |
| **Dihapus** | RFU, Progress, Priority, Delays Reported |

> Kriteria **Past Due** dan **Due Today** mengikuti kriteria list utama (status Open saja).

---

## Sub-Fitur: Outstanding Administration

Halaman PM Shutdown menampilkan informasi/count **Outstanding Administration** sebagai widget tersendiri.

Outstanding Administration adalah workcard PM Shutdown yang sudah melewati batas notif — kriteria datanya **berbeda** dari list utama, khususnya pada `NotifNoStatus` (contains vs NOT contains). Detail lengkap: [Outstanding Administration](outstanding-administration.md).

---

## Permission

| Tipe | Permission Code |
|------|-----------------|
| Basic | `IAMS_Mobile_Shutdown_View` |
| All Site | `IAMS_Mobile_Shutdown_View_All_Site` (parent: `IAMS_Mobile_Shutdown_View`) |

### Data Scope (Permission-based)

| Permission | Perilaku |
|------------|----------|
| Basic — Section ID ter-mapping ke Section Type | Hanya tampilkan task dari section yang sesuai |
| Basic — Section ID tidak ter-mapping | Tampilkan semua section |
| All Site | Tampilkan task dari semua site |
