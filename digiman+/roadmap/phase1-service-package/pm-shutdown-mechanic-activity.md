# PM Shutdown — Mechanic Activity Tracking

Dokumen ini merangkum diskusi tentang pencatatan aktivitas mechanic saat mengerjakan form di PM Shutdown, untuk kebutuhan mechanic activity report.

*Last updated: 2026-06-22*

---

## Konsep

Setiap mechanic direcord aktivitasnya setiap kali masuk dan keluar dari form. Satu mechanic bisa punya multiple session dalam satu form (berbeda shift atau berbeda hari).

**Perbedaan dengan Submit:**
| Aksi | Keterangan |
|------|------------|
| **Start** | Mechanic mulai mengerjakan form (masuk) |
| **Finish/Close** | Mechanic keluar dari form sementara — bisa kembali lagi |
| **Submit** | Form selesai secara final — tidak bisa kembali |

---

## Tabel Existing: TaskPersonalizedLog

Tidak perlu tabel baru. Activity log disimpan di tabel `TaskPersonalizedLog` yang sudah ada di `maintenance-execution` SQL, dengan tambahan satu kolom:

```
TaskPersonalizedLog  (existing)
  ├── Id
  ├── TaskPersonalizedId  ← FK ke TaskPersonalized (yang sudah berisi TaskId + UserCode)
  ├── StartDate           ← device timestamp saat klik "Start/Mulai"
  ├── EndDate             ← device timestamp saat klik "Finish/Close", nullable
  ├── ShiftName           ← [KOLOM BARU] shift saat StartDate
  ├── UserFullName        ← [KOLOM BARU] nama lengkap mechanic saat sesi dibuat (snapshot dari UserEmploymentProfile)
  ├── SiteCode            ← [KOLOM BARU] kode site mechanic saat sesi dibuat (snapshot dari UserEmploymentProfile)
  ├── SiteName            ← [KOLOM BARU] nama site saat sesi dibuat (snapshot)
  ├── SectionId           ← [KOLOM BARU] section mechanic saat sesi dibuat (snapshot dari UserEmploymentProfile)
  ├── SectionName         ← [KOLOM BARU] nama section saat sesi dibuat (snapshot)
  ├── IsActive
  ├── CreatedBy / CreatedAt
  ├── ModifiedBy / ModifiedAt
  └── LastSynced*
```

> `UserFullName`, `SiteCode`, `SiteName`, `SectionId`, `SectionName` disimpan sebagai **snapshot saat sesi dibuat** — bukan diambil real-time dari `UserEmploymentProfile`. Tujuannya:
> 1. **Mechanic pindah site/section** — data historis tetap mencerminkan posisi saat aktivitas terjadi
> 2. **Mechanic resign** — meski record dihapus dari `UserEmploymentProfile`, data aktivitas historis tetap lengkap dan bisa ditampilkan di report tanpa join ke tabel user
> 3. **Efisiensi reporting** — tidak perlu join ke tabel lain untuk mendapatkan nama, site, dan section
>
> Untuk kebutuhan reporting, join ke `TaskPersonalized` untuk mendapatkan `TaskId` dan `UserCode`.

---

## Trigger "Start/Mulai"

> **Catatan deduplication — dua tabel, dua aturan berbeda:**
> - `TaskPersonalized` → upsert by `TaskId + UserCode` — **1 record per mechanic per task, selamanya**. Tidak bergantung shift.
> - `TaskPersonalizedLog` → deduplication by `TaskPersonalizedId + ShiftName` — **max 1 open session per mechanic per shift**. Mechanic bisa punya multiple record jika beda shift.

> **Catatan:** `TaskPersonalized` **tidak dibuat saat klik Mulai**. Digiman+ sudah punya fitur **Assign to / Assign to Me** untuk Task — `TaskPersonalized` dibuat melalui fitur tersebut sebelum mechanic membuka form. Yang dibuat saat klik Mulai hanya `TaskPersonalizedLog`.

### Klik pertama (first time mechanic buka form di shift ini)
1. `TaskPersonalized` → sudah ada (dibuat via Assign to / Assign to Me)
2. Buat `TaskPersonalizedLog` record baru (StartDate = device timestamp, ShiftName = shift saat ini)

### Klik berikutnya (shift berbeda atau hari berbeda)
1. `TaskPersonalized` → tidak berubah
2. Close previous open `TaskPersonalizedLog` session → set EndDate = shift end time berdasarkan StartDate sesi sebelumnya
3. Buat `TaskPersonalizedLog` record baru

### Klik di shift yang sama
`TaskPersonalized` → tidak berubah.
`TaskPersonalizedLog` → **tidak membuat record baru** — open session di shift yang sama sudah ada (cek: EndDate IS NULL + ShiftName sama). Mechanic langsung masuk ke form.

---

## Auto-Close FinishedAt

Jika mechanic tidak klik "Finish/Close", ada dua trigger auto-close:

| Trigger | Behavior |
|---------|----------|
| Mechanic klik "Start" sesi baru (shift berbeda) | Close sesi sebelumnya → `EndDate = shift end time` pada tanggal StartDate sesi tersebut |
| Form disubmit | Close semua sesi yang masih open → `EndDate = min(shift end time, submit time)` |

Submit adalah **safety net** — menangkap sesi terakhir yang tidak di-close via trigger pertama.

---

## Shift Data: Tabel SiteShift

Tabel baru di `maintenance-execution` DB (di-seed one-time dari Tenant DB):

```
SiteShift
  ├── Id
  ├── TenantCode
  ├── SiteCode
  ├── Name
  ├── StartShift    ← time (e.g., 06:00)
  ├── EndShift      ← time (e.g., 18:00), explicit — tidak di-derive runtime
  └── IsActive
```

**Contoh data:**
| SiteCode | Name | StartShift | EndShift |
|----------|------|-----------|---------|
| 2009 | Day Shift | 06:00 | 18:00 |
| 2009 | Night Shift | 18:00 | 06:00 |

### Logika Penentuan Shift dari Timestamp
```
06:00 – 17:59 → Day Shift
18:00 – 05:59 (next day) → Night Shift
```

### Logic Next-Day untuk EndShift
Tidak ada kolom `IsNextDay`. Derivasi di code:
```
if EndShift < StartShift → shift melewati tengah malam → FinishedAt date = StartedAt date + 1
if EndShift > StartShift → same day → FinishedAt date = StartedAt date
```

**Seed:** One-time untuk MVP. Tidak ada sync otomatis dari Tenant DB.

---

## Offline Behavior

- Semua timestamp (`StartDate`, `EndDate`) menggunakan device clock — konsisten dengan known limitation timestamp offline
- Record dibuat lokal saat offline, di-queue untuk sync

### Auto-Close Mechanism — Client-Side
Auto-close adalah mekanisme baru yang dibangun di client. Saat mechanic klik "Start" sesi baru, client secara lokal:
1. Hitung `EndDate` sesi sebelumnya = shift end time berdasarkan `StartDate` sesi tersebut
2. Queue dua operasi sekaligus: **update** Session lama (set EndDate) + **create** Session baru
3. Kedua operasi dikirim ke server dalam satu batch saat sync

Server hanya menerima dan menyimpan data — tidak ada logic deteksi auto-close di server side.

### Activity Records Setelah Form Complete
`TaskPersonalizedLog` records dari mechanic yang masih offline saat form disubmit **tetap diterima saat sync**, selama `StartDate < submitted time`. Activity records adalah historical log — tidak mempengaruhi form content, tidak pernah ditolak.

---

## Simulasi Data

### Setup
- Site 2009, Day Shift 06:00–18:00, Night Shift 18:00–06:00
- Form: Task ID = T001
- Mechanic A (UserCode: mech_A), Mechanic B (UserCode: mech_B)

---

### Skenario 1: Single mechanic, klik Finish dengan benar
```
08:00  Mechanic A klik Start  → TaskFormActivity (mech_A, 08:00, null, Day Shift)
10:30  Mechanic A klik Finish → TaskFormActivity (mech_A, 08:00, 10:30, Day Shift)
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 08:00 | 10:30 | Day Shift |

---

### Skenario 2: Mechanic klik Start berkali-kali di shift yang sama
```
08:00  Mechanic A klik Start → record dibuat
09:30  Mechanic A klik Start lagi (sama shift) → SKIP, tidak buat record baru
11:00  Mechanic A klik Start lagi (sama shift) → SKIP
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 08:00 | null | Day Shift |

---

### Skenario 3: Mechanic lupa Finish, buka lagi di shift berikutnya
```
[2026-06-22]
08:00  Mechanic A klik Start → record 1 dibuat (Day Shift)
       (lupa klik Finish)

[2026-06-23]
07:00  Mechanic A klik Start (Day Shift) →
       → prevSession ditemukan (record 1, FinishedAt null)
       → auto-close record 1: FinishedAt = 2026-06-22 18:00
       → buat record 2
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 08:00 | **2026-06-22 18:00** | Day Shift |
| 2 | T001 | mech_A | 2026-06-23 07:00 | null | Day Shift |

---

### Skenario 4: Night Shift melewati tengah malam, auto-close via Submit
```
[2026-06-22]
20:00  Mechanic A klik Start → record dibuat (Night Shift)
       (lupa klik Finish)

[2026-06-23]
05:00  Form disubmit (submit time = 05:00) →
       → handleFormSubmit: cari open sessions
       → record ditemukan (StartedAt = 2026-06-22 20:00, Night Shift)
       → shift end Night Shift = 2026-06-23 06:00
       → FinishedAt = min(2026-06-23 06:00, 2026-06-23 05:00) = 2026-06-23 05:00
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 20:00 | **2026-06-23 05:00** | Night Shift |

---

### Skenario 5: Multi-mechanic, mix Finish dan auto-close via Submit
```
[2026-06-22]
08:00  Mechanic A klik Start → record A1 (Day Shift)
08:30  Mechanic B klik Start → record B1 (Day Shift)
10:00  Mechanic A klik Finish → record A1 FinishedAt = 10:00
       (Mechanic B tidak klik Finish)
11:00  Mechanic B submit form (submit time = 11:00) →
       → handleFormSubmit: record B1 masih open
       → shift end Day Shift = 18:00
       → FinishedAt B1 = min(18:00, 11:00) = 11:00
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 08:00 | 2026-06-22 10:00 | Day Shift |
| 2 | T001 | mech_B | 2026-06-22 08:30 | **2026-06-22 11:00** | Day Shift |

> Rule `min(shift end, submit time)` berlaku sama untuk single mechanic — submit sebelum shift end → submit time yang dipakai.

---

### Skenario 6: First time Start — TaskPersonalized + TaskFormActivity dibuat bersamaan
```
[Mechanic A belum pernah buka form T001]
08:00  Mechanic A klik Start →
       → TaskPersonalized dibuat (mech_A, IsPrecautionConfirmed=true, Status=In Progress)
       → TaskFormActivity record 1 dibuat

[Mechanic A buka form lagi di hari berikutnya, shift sama]
08:30  Mechanic A klik Start (Day Shift, hari berikutnya) →
       → TaskPersonalized TIDAK dibuat lagi (sudah ada)
       → prevSession ditemukan → auto-close record 1: FinishedAt = 2026-06-22 18:00
       → TaskFormActivity record 2 dibuat
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 08:00 | **2026-06-22 18:00** | Day Shift |
| 2 | T001 | mech_A | 2026-06-23 08:30 | null | Day Shift |

---

### Skenario 7: Mechanic klik Finish lalu Start lagi di shift yang sama
```
08:00  Mechanic A klik Start → record 1 (Day Shift, open)
10:00  Mechanic A klik Finish → record 1 FinishedAt = 10:00
       (pergi makan siang, kembali lagi)
13:00  Mechanic A klik Start (Day Shift) →
       → cek open session Day Shift → tidak ada (record 1 sudah FinishedAt)
       → buat record 2 (Day Shift, open)
15:00  Mechanic A klik Finish → record 2 FinishedAt = 15:00
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 08:00 | 2026-06-22 10:00 | Day Shift |
| 2 | T001 | mech_A | 2026-06-22 13:00 | 2026-06-22 15:00 | Day Shift |

---

### Skenario 8: Mechanic lanjut kerja ke Night Shift, klik Start lagi (auto-close via Start)
```
16:00  Mechanic A klik Start (Day Shift) → record 1 (open)
       (lanjut kerja melewati shift — tidak klik Finish, klik Start lagi di Night Shift)
19:00  Mechanic A klik Start (Night Shift) →
       → open session ditemukan: record 1 (Day Shift)
       → auto-close record 1: FinishedAt = 2026-06-22 18:00 (Day Shift end)
       → buat record 2 (Night Shift, open)
22:00  Mechanic A klik Finish → record 2 FinishedAt = 22:00
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 16:00 | **2026-06-22 18:00** | Day Shift |
| 2 | T001 | mech_A | 2026-06-22 19:00 | 2026-06-22 22:00 | Night Shift |

---

### Skenario 9: Multi-mechanic, multiple session, submit sebagai safety net
```
[2026-06-22 — Day Shift]
08:00  Mechanic A Start → record A1 (open)
08:30  Mechanic B Start → record B1 (open)
10:00  Mechanic A Finish → record A1 FinishedAt = 10:00

[2026-06-22 — Night Shift]
19:00  Mechanic A Start (Night Shift) →
       → tidak ada open session Day Shift untuk A (sudah closed)
       → buat record A2 (Night Shift, open)
21:00  Mechanic B Start (Night Shift) →
       → open session B1 (Day Shift) ditemukan
       → auto-close B1: FinishedAt = 2026-06-22 18:00
       → buat record B2 (Night Shift, open)

[2026-06-23 — 02:00]
02:00  Mechanic A submit form (submit time = 02:00) →
       → handleFormSubmit: A2 dan B2 masih open (Night Shift, end = 06:00)
       → A2 FinishedAt = min(2026-06-23 06:00, 2026-06-23 02:00) = 2026-06-23 02:00
       → B2 FinishedAt = min(2026-06-23 06:00, 2026-06-23 02:00) = 2026-06-23 02:00
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 08:00 | 2026-06-22 10:00 | Day Shift |
| 2 | T001 | mech_B | 2026-06-22 08:30 | **2026-06-22 18:00** | Day Shift |
| 3 | T001 | mech_A | 2026-06-22 19:00 | **2026-06-23 02:00** | Night Shift |
| 4 | T001 | mech_B | 2026-06-22 21:00 | **2026-06-23 02:00** | Night Shift |

---

### Skenario 10: Start dan Finish di shift berbeda — mechanic klik Finish sendiri
```
16:00  Mechanic A klik Start (Day Shift) → record 1 (open, ShiftName = Day Shift)
       (selesai kerja tapi lupa klik Finish)
19:00  Mechanic A klik Finish (sudah Night Shift) →
       → record 1 FinishedAt = 19:00 (actual Finish click time)
       → ShiftName tetap Day Shift (mengikuti StartedAt)
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 16:00 | **2026-06-22 19:00** | Day Shift |

> Berbeda dari Skenario 8 dimana mechanic klik Start lagi di shift baru (trigger auto-close). Di sini mechanic langsung klik Finish — FinishedAt = waktu aktual klik, bukan shift end time.

---

### Skenario 11: Submit setelah shift end — lupa Finish, submit di shift berikutnya (shift end menang)
```
08:00  Mechanic A klik Start (Day Shift, end = 18:00)
       (selesai kerja tapi lupa klik Finish)
19:00  Form disubmit di Night Shift →
       → shift end Day Shift = 18:00, submit time = 19:00
       → FinishedAt = min(18:00, 19:00) = 18:00
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 08:00 | **2026-06-22 18:00** | Day Shift |

---

### Skenario 12: Night Shift happy path — Start dan Finish dalam Night Shift

**Case A: Finish sebelum tengah malam**
```
20:00  Mechanic A klik Start (Night Shift) → record 1 (open)
23:00  Mechanic A klik Finish →
       → record 1 FinishedAt = 23:00 (same date)
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 20:00 | 2026-06-22 23:00 | Night Shift |

**Case B: Finish setelah tengah malam (masih Night Shift)**
```
20:00  Mechanic A klik Start (Night Shift) → record 1 (open)
03:00  Mechanic A klik Finish (dini hari, masih Night Shift) →
       → record 1 FinishedAt = 03:00 next day
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 20:00 | **2026-06-23 03:00** | Night Shift |

---

### Skenario 13: Start Day Shift hari ke-1, lupa Finish, submit di hari ke-2 shift berbeda
```
[2026-06-22]
08:00  Mechanic A klik Start (Day Shift, end = 18:00) → record 1 (open)
       (selesai kerja, lupa klik Finish)

[2026-06-23]
19:00  Form disubmit di Night Shift (submit time = 2026-06-23 19:00) →
       → handleFormSubmit: record 1 masih open
       → shift StartedAt = Day Shift, end = 2026-06-22 18:00
       → FinishedAt = min(2026-06-22 18:00, 2026-06-23 19:00) = 2026-06-22 18:00
```
| Id | TaskId | UserCode | StartedAt | FinishedAt | ShiftName |
|----|--------|----------|-----------|------------|-----------|
| 1 | T001 | mech_A | 2026-06-22 08:00 | **2026-06-22 18:00** | Day Shift |

> Meski submit terjadi di hari dan shift yang berbeda, FinishedAt tetap mengacu pada shift end dari StartedAt — bukan dari waktu submit.

---

## Open Items

- [ ] Duration kalkulasi di DB atau di aplikasi?
- [ ] Mekanisme sync SiteShift jika shift schedule berubah setelah MVP
- [ ] **Kebijakan device mechanic** — apakah mechanic diperbolehkan menggunakan gadget pribadi untuk input data di Digiman+, atau perusahaan yang memfasilitasi perangkat? Ini berpengaruh pada: (1) provisioning akun, (2) flow login/logout per shift jika shared device, (3) keamanan data di lapangan
- [x] Bagaimana handle jika ShiftId/SiteCode mechanic tidak match dengan SiteShift yang ada → gunakan **default site** dari configuration
- [x] Tidak perlu tabel baru — gunakan `TaskPersonalizedLog` yang sudah ada, tambah kolom `ShiftName`
