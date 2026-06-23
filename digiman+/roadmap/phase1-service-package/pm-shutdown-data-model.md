# PM Shutdown — Data Model Changes

Dokumen ini merangkum perubahan data model yang dibutuhkan untuk mendukung fitur service bundle dan multi-mechanic form execution di PM Shutdown.

*Last updated: 2026-06-22*

---

## Ringkasan Perubahan

| Table | Perubahan |
|-------|-----------|
| `Task` | Tambah kolom SMU + perubahan Status flow |
| `TaskPersonalized` | Hapus kolom SMU, tambah `StartedAt`, support N records per Task |
| `FormSubmission` | Tambah kolom `IsMandatory` |
| `TaskMechanic` | ~~Tidak jadi~~ — TaskPersonalized sudah support N records |

---

## WorkOrder

### Status Flow
```
Open → In Progress → Complete
```

| Status | Trigger |
|--------|---------|
| `Open` | WorkOrder dibuat saat sync dari dplan |
| `In Progress` | Mechanic pertama klik "Mulai" pada form apapun dalam bundle |
| `Complete` | Finish Execution dilakukan oleh Supervisor/Foreman/Mechanic |

---

## Task

### Kolom Baru
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `MachineSMUValue` | - | Dipindah dari TaskPersonalized — 1 nilai per service execution |
| `MachineSMUAddress` | - | Dipindah dari TaskPersonalized |

### Status Flow
```
Open → In Progress → Complete → Approved
```

| Status | Trigger |
|--------|---------|
| `Open` | Task dibuat saat Planner save bundle |
| `In Progress` | Saat sync: TaskPersonalized mechanic pertama masuk → gunakan `StartedAt` terkecil |
| `Complete` | Saat satu mechanic submit form |
| `Approved` | Setelah approval workflow selesai |

> **Catatan:** Jika Task dibuat offline dan sync belakangan, `In Progress` menggunakan `StartedAt` terkecil dari semua TaskPersonalized yang ada — bukan berdasarkan urutan sync.

---

## TaskPersonalized

### 1 Task = N TaskPersonalized
Setiap mechanic yang mengerjakan form memiliki record TaskPersonalized sendiri. Dibuat saat mechanic klik **"Mulai"** untuk pertama kali — subsequent open oleh mechanic yang sama tidak membuat record baru.

### Kolom Dihapus
| Kolom | Keterangan |
|-------|------------|
| `MachineSMUValue` | Dipindah ke Task |
| `MachineSMUAddress` | Dipindah ke Task |

### Kolom Baru
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `StartedAt` | DateTime | Device timestamp saat mechanic klik "Mulai" |

### Deduplication
Server melakukan **upsert** berdasarkan `TaskId + UserCode` — mencegah duplikasi jika mechanic klik Mulai di lebih dari satu device.

### "Mulai" Button — Atomic Action
Klik "Mulai" adalah satu aksi yang sekaligus membuat dua record lokal:

**TaskPersonalized** (hanya jika belum ada untuk mechanic ini di task ini):
1. Membuat TaskPersonalized record lokal
2. Set `IsPrecautionConfirmed = true`
3. Set `StartedAt` = device timestamp saat klik
4. Set `Status = In Progress`

**TaskFormActivity** (setiap klik "Mulai" di shift baru):
5. Jika tidak ada open session di shift yang sama → buat TaskFormActivity record baru (StartedAt = device timestamp, ShiftName = shift saat ini)
6. Jika ada open session di shift sebelumnya → client auto-close session tersebut (set FinishedAt = shift end time), lalu buat TaskFormActivity baru

Semua operasi di-queue dalam satu batch sync — tidak ada sync terpisah per operasi.

### Status per TaskPersonalized
| Kondisi | Status |
|---------|--------|
| Mechanic membuka form dan mulai mengisi | `In Progress` |
| Form disubmit (oleh siapapun) | `Complete` — semua TaskPersonalized pada Task tersebut diupdate |

### Offline Behavior
- Klik "Mulai" saat offline → record dibuat lokal, di-queue untuk sync
- Saat sync: server upsert berdasarkan `TaskId + UserCode`
- `Task.Status → In Progress` menggunakan `StartedAt` terkecil dari semua record yang masuk

---

## FormSubmission

### Kolom Baru
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `IsMandatory` | Boolean | Ditentukan oleh Planner saat assign form ke bundle |

---

## Breaking Changes & Migration

| Perubahan | Impact | Action |
|-----------|--------|--------|
| `MachineSMUValue` & `MachineSMUAddress` pindah dari TaskPersonalized → Task | Data existing di TaskPersonalized perlu dimigrate ke Task | Migration script diperlukan |
| TaskPersonalized: 1 Task bisa N records | Logic yang mengasumsikan 1 Task = 1 TaskPersonalized perlu direview | Audit existing queries & business logic |

---

## Catatan Arsitektur

- `StartedAt` = device clock (bisa tidak akurat) — acceptable risk, konsisten dengan known limitation timestamp offline yang sudah didokumentasikan
- `CreatedAt` = server timestamp saat sync — berbeda dari `StartedAt` karena offline gap
- Submit form → masuk approval workflow (sama seperti Form Submission)
- **Finish Execution gate** — validasi dari dua sumber berbeda:
  1. **Backlog execution selesai** → query `dPlan` (existing, tidak berubah)
  2. **Semua mandatory form Complete** → query `maintenance-execution`: semua `Task` di WorkOrder tersebut dimana `FormSubmission.IsMandatory = true` harus memiliki `Task.Status = Complete`
- `FormSubmission` tidak memiliki kolom Status — status form execution direpresentasikan oleh `Task.Status`
