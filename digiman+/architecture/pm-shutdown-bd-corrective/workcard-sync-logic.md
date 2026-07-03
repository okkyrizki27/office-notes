# Workcard List Sync Logic

Dokumen ini mendefinisikan logic pengambilan data workcard list di Digiman+ untuk **PM Shutdown** dan **BD Corrective**.

*Last updated: 2026-07-03*

---

## Fresh Install

Data diambil berdasarkan status dengan filter tanggal masing-masing. Data dibatasi dalam range **2 bulan terakhir** menggunakan field tanggal yang relevan per status.

| Status | Kondisi | Field Tanggal | Filter |
|--------|---------|---------------|--------|
| `SUBMIT` | — | `ProjectFinish` | `>= today - 2 bulan` |
| `IN PROGRESS` | NotifNo IS NOT NULL **dan** FinishBreakdown terisi | `FinishBreakdown` | `>= today - 2 bulan` |
| `IN PROGRESS` | NotifNo IS NOT NULL **dan** FinishBreakdown NULL | — | Semua data |
| `IN PROGRESS` | NotifNo IS NULL | — | Semua data |
| `FINISH` / `CANCEL` | — | — | ❌ Tidak diambil |

**Catatan:**
- `ProjectFinish` selalu terisi saat status `SUBMIT`
- `FinishBreakdown` bisa kosong meski NotifNo sudah terisi → jika null, diambil semua (belum ada target finish)
- `IN PROGRESS` + NotifNo IS NULL → semua data karena belum ada target finish

---

## After Last Sync

Hanya data yang berubah sejak sync terakhir (`ModifiedUtcDate >= LastSyncDate`). `FINISH` dan `CANCEL` diambil agar bisa di-remove dari device, tapi **tidak ditampilkan** di list.

| Status | Kondisi | Filter |
|--------|---------|--------|
| `SUBMIT` | — | `ModifiedUtcDate >= LastSyncDate` |
| `IN PROGRESS` | NotifNo IS NOT NULL | `ModifiedUtcDate >= LastSyncDate` |
| `IN PROGRESS` | NotifNo IS NULL | `ModifiedUtcDate >= LastSyncDate` |
| `FINISH` | — | `ModifiedUtcDate >= LastSyncDate` — diambil untuk di-remove dari device, **tidak ditampilkan** |
| `CANCEL` | — | `ModifiedUtcDate >= LastSyncDate` — diambil untuk di-remove dari device, **tidak ditampilkan** |

---

## Berlaku untuk

- PM Shutdown workcard list
- BD Corrective workcard list
