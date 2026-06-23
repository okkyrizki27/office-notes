# PM Shutdown — Form Execution Process

Dokumen ini merangkum diskusi tentang proses eksekusi form di PM Shutdown — mencakup multi-mechanic collaboration, sync mechanism, conflict resolution, dan submit flow.

*Last updated: 2026-06-22*

---

## Konteks

Satu form dalam bundle dapat diisi oleh **beberapa mechanic sekaligus**, semua menggunakan mode **offline-first**. Pembagian kerja antar mechanic dilakukan secara operasional (oleh Supervisor, Foreman, atau mechanic sendiri) — tidak di-enforce oleh sistem.

---

## Conflict Resolution

### Locking Strategy: Optimistic Locking
Tidak ada lock saat field dibuka. Conflict dideteksi saat sync.

### Granularitas Conflict: Per Field
Setiap field menyimpan:
```
field: {
  value: ...,
  timestamp: [waktu mechanic input di device],
  updated_by: [mechanic identity]
}
```

### Resolution Strategy: First Write Wins
Field yang diisi lebih awal (berdasarkan timestamp) yang menang. Field dari mechanic yang sync belakangan di-discard jika field tersebut sudah diisi lebih awal oleh mechanic lain.

### Known Limitation
Timestamp menggunakan **device clock** saat input — bisa tidak akurat jika device clock tidak sinkron. Risiko ini **acceptable** dan dicatat sebagai known limitation.

---

## Sync Mechanism

### Granularitas Sync: Per Field + Batching

- **Granularitas data**: per field (hanya field yang berubah/dirty)
- **Granularitas koneksi**: satu batch request per sync session
- Client tracks dirty fields saat offline
- Saat sync: semua dirty fields dari semua tab dikirim dalam **satu request**
- Server memproses per field (first-write-wins), mengembalikan satu response
- Client update local state berdasarkan response

### Idempotency Key & Timestamp Collision
Idempotency key per field: `fieldId + timestamp`. Jika dua mechanic menginput field yang sama dengan **timestamp identik** (akibat device clock tidak sinkron):
- **Sync pertama yang tiba** → diproses, nilai tersimpan
- **Sync berikutnya dengan timestamp sama** → dianggap **berhasil** (no-op, tidak error, tidak overwrite)
- Konsisten dengan silent discard approach yang sudah ditetapkan

**Keuntungan:**
- Satu network round trip — cocok untuk koneksi intermittent di area tambang
- Data kecil — hanya field yang berubah, bukan seluruh tab
- Tidak ada false conflict — mechanic yang edit field berbeda di tab yang sama tidak conflict

**Trade-off:**
Implementasi client-side lebih kompleks (track dirty fields per field, bukan per dokumen).

### UX Saat Conflict
- Sync dianggap **berhasil** (bukan error/gagal)
- Tampilkan **proper message** untuk field yang tidak tersimpan

Contoh: *"Sync berhasil. 2 field tidak tersimpan karena sudah diisi lebih awal oleh Mechanic A."*

### Sistem Tidak Tracking Device
Sistem tidak perlu tahu device mana saja yang sedang mengerjakan form yang sama. Koordinasi sepenuhnya tanggung jawab operasional mechanic dan supervisor.

---

## Submit Form

### Aturan Submit
- Submit dilakukan **sekali** oleh **satu mechanic sebagai perwakilan**
- Tidak ada submit per tab
- Pre-condition: **semua mandatory fields terisi** di device submitter

### Submit Bisa Offline
| Skenario | Behavior |
|----------|----------|
| Single mechanic, full offline | ✅ Bisa submit offline — di-queue, dikirim ke server saat ada koneksi |
| Multiple mechanic | Semua mechanic sync dulu secara operasional, baru satu mechanic submit |

### Validasi Mandatory Fields
- **Client-side** — cek mandatory fields berdasarkan data di device → submit button enabled/disabled
- **Server validate** saat sync sebagai final check (bukan blocker untuk offline submit)

### Review Sebelum Submit
Mechanic perwakilan dapat mereview form sebelum submit melalui **fitur summary** yang sudah ada di Form Submission.

---

## Design Decisions

| Keputusan | Detail |
|-----------|--------|
| Optimistic locking | Lebih cocok untuk offline-first dibanding pessimistic |
| First write wins | Berdasarkan device timestamp saat input |
| Device clock risk | Acceptable, dicatat sebagai known limitation |
| Silent discard conflict | Sync sukses + proper message untuk field yang kalah |
| No Supervisor override | Override menambah kompleksitas dan risiko data quality — yang melakukan pengukuran adalah mechanic |
| System tidak track devices | Koordinasi adalah tanggung jawab operasional, bukan sistem |
| Submit bisa offline | Offline-first berlaku penuh termasuk submit untuk single mechanic |
| Validasi mandatory client-side | Agar submit bisa dilakukan offline |

---

## Submit per Form & Finish Execution

Submission bersifat **per form**, bukan per bundle. Setiap form dalam bundle disubmit secara independen oleh mechanic masing-masing.

**Finish Execution** adalah gate di level WorkOrder — dilakukan oleh Supervisor/Foreman (atau Mechanic jika diberi permission):

| Validasi Finish Execution | Sekarang | Baru |
|--------------------------|----------|------|
| Backlog execution selesai | ✅ | ✅ |
| Semua mandatory form status `Complete` | ❌ | ✅ |

Optional form tidak memblokir Finish Execution.

### Finish Execution — Online vs Offline

Finish Execution **bisa dilakukan offline dan di-queue**, selama **validasi client-side terpenuhi** — data di local device menunjukkan semua mandatory form sudah submitted dan backlog execution selesai.

Sama dengan submit form: cek local data → kondisi terpenuhi → aksi diperbolehkan offline → di-queue → sync ke server setelah ada koneksi.

> Prinsip: offline-first berlaku penuh untuk semua aksi termasuk Finish Execution. Client-side check adalah gate — user tidak perlu online selama data lokalnya memenuhi syarat.

### Post-Submit
Setelah form disubmit → masuk ke **approval workflow** (sama seperti Form Submission).

---

## Sync Reliability

### Retry Mechanism
Digiman+ sudah memiliki retry mechanism yang dipertahankan. Ditambah prinsip **idempotent batch**:
- Setiap sync batch diberi unique request ID
- Jika partial failure → retry batch yang sama
- Server menggunakan `fieldId + timestamp` sebagai idempotency key
- Field yang sudah diproses tidak diproses ulang meski batch dikirim ulang → tidak ada data ganda

---

## Access Control & Time Constraint

| Aspek | Keputusan |
|-------|-----------|
| Siapa yang bisa buka/isi/submit form | Semua user dengan akses PM Shutdown workcard |
| Finish Execution | Supervisor/Foreman — Mechanic bisa jika diberi permission |
| DueDate WorkOrder | Informasi saja, tidak ada enforcement sistem |

---

## Edge Cases & Decisions

| Edge Case | Keputusan |
|-----------|-----------|
| Auto-save & crash recovery | Sudah diimplementasi — data tersimpan lokal secara otomatis |
| Duplicate submission | First submit wins by timestamp — sama seperti conflict resolution field. Submit kedua ditolak |
| WorkOrder cancel saat form sedang diisi | Tidak bisa terjadi — jika plan sudah start eksekusi, Planner tidak bisa cancel |
| Form reopen setelah submit | **Deferred to next MVP** |
| Mechanic sakit/pergi, data belum sync | **Behavior berbeda per jenis data** (keputusan desain eksplisit): (1) **Form content** (field values) → **ditolak** jika sync setelah form status `Complete` — data tidak boleh mengubah form yang sudah final; (2) **Activity records** (`TaskPersonalizedLog`) → **diterima** selama `StartDate < submitted time` — activity adalah historical log, tidak mempengaruhi form content, selalu valid |
| Visibility antar mechanic | Mechanic bisa saling melihat progress sampai level field — bukan per tab. Mechanic B dapat melihat field mana saja yang sudah diisi Mechanic A beserta identitasnya. **Mekanisme: auto-sync kombinasi dua trigger (aktif hanya saat ada koneksi):** (1) After input + debounce 3 detik → upload dirty fields + download latest; (2) Background timer 30 detik → download latest meski tidak ada input baru. Near real-time tanpa persistent connection. Trade-off: interval timer mempengaruhi battery |
| Field validation range & attachment | → dibahas di [Form Behavior](pm-shutdown-form-behavior.md) |

---

## Open Items

- [ ] Desain UX proper message saat conflict — format dan placement notifikasi
- [ ] Progress indicator mandatory fields di device (berapa field sudah terisi dari yang diketahui device)
- [ ] Flow detail: submit offline → queue → sync ke server → server final validation
- [x] Auto-sync trigger: **debounce 3 detik** setelah input, **timer interval 30 detik** background pull
