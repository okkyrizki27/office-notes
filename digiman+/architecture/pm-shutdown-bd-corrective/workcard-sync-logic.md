# Workcard List Sync Logic

Dokumen ini mendefinisikan logic pengambilan data workcard list di Digiman+ untuk **PM Shutdown** dan **BD Corrective**.

*Last updated: 2026-06-23*

---

## Fresh Install

Data diambil berdasarkan status dengan filter tanggal masing-masing. CANCEL tidak diambil karena workcard sudah tidak perlu dikerjakan.

| Status | Kondisi | Filter |
|--------|---------|--------|
| `SUBMIT` | — | `ProjectFinish >= today - 2 bulan` |
| `IN PROGRESS` | NotifNo IS NOT NULL | `FinishBreakdown IS NULL OR FinishBreakdown >= today - 2 bulan` |
| `IN PROGRESS` | NotifNo IS NULL | Semua data |
| `CANCEL` | — | ❌ Tidak diambil |

**Catatan:**
- `ProjectFinish` selalu terisi saat status `SUBMIT`
- `FinishBreakdown` bisa kosong meski NotifNo sudah terisi → tetap diambil jika null
- `IN PROGRESS` + NotifNo IS NULL → semua data karena belum ada target finish

---

## After Last Sync

Hanya data yang berubah sejak sync terakhir. CANCEL diambil agar bisa di-remove dari device, tapi **tidak ditampilkan** di list.

| Status | Kondisi | Filter |
|--------|---------|--------|
| `SUBMIT` | — | `ModifiedUtcDate >= LastSyncDate` |
| `IN PROGRESS` | NotifNo IS NOT NULL | `ModifiedUtcDate >= LastSyncDate` |
| `IN PROGRESS` | NotifNo IS NULL | `ModifiedUtcDate >= LastSyncDate` |
| `CANCEL` | — | `ModifiedUtcDate >= LastSyncDate` — diambil untuk di-remove dari device, **tidak ditampilkan** |

---

## Berlaku untuk

- PM Shutdown workcard list
- BD Corrective workcard list
