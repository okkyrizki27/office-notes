# PM Shutdown — Service Package

Dokumen ini merangkum diskusi tentang gap dan arah pengembangan fitur PM Shutdown terkait service sheet dan package form.

*Last updated: 2026-06-22*

---

## Gap Saat Ini

PM Shutdown saat ini hanya menghandle **backlog execution** — temuan inspeksi yang dimasukkan ke scheduled service. Tidak ada dokumentasi terstruktur tentang pekerjaan yang dilakukan selama service berlangsung.

Di kondisi aktual lapangan (sebelum digitalisasi), setiap scheduled service memiliki **package form** yang harus diisi. Ini belum terakomodasi di Digiman+. Tab Form di workcard PM Shutdown mobile **sudah ada tapi masih hidden/belum diimplementasi**.

---

## Konsep: Service Package

Di industri heavy equipment mining, scheduled service berbasis periodical service hour: **250 hrs, 500 hrs, 1000 hrs, 2000 hrs**.

Untuk setiap service execution, ada package form yang terdiri dari:

```
Package: Unit X @ [Service Hour]
├── Service Sheet     → MANDATORY (jika mapping ada di Form Builder)
├── Welding Form      → Additional
├── Tyre R&I Form     → Additional
├── Return to Operation (RTO) → Additional
└── ... form lainnya
```

### Mandatory vs Additional
- **Service Sheet**: auto-selected sistem berdasarkan Equipment Model × Service Hour — sistem set `IsMandatory = true` sebagai **default suggestion**
- **Form lainnya**: sistem suggest berdasarkan model atau model + service hour (keduanya ditampilkan), atau Planner search sendiri

**Authority `IsMandatory` sepenuhnya ada di Planner** — sistem hanya memberi suggestion default. Planner dapat mengubah nilai mandatory/opsional untuk semua form termasuk service sheet.

---

## Peran Planner

Planner adalah **pemilik scope pekerjaan** — mengetahui unit, interval, pekerjaan yang akan dilakukan, dan durasi. Dari informasi tersebut, Planner menentukan komposisi package form di Digiplan (web).

---

## Arsitektur Data

### Struktur Penyimpanan

| Data | Service | DB | Keterangan |
|------|---------|-----|------------|
| Service plan, PlanId | `dplan` | dplan | Existing |
| WorkOrder | `maintenance-execution` | SQL | PlanId referensi ke dplan |
| Task | `maintenance-execution` | SQL | **1 Task per form yang diassign** |
| FormSubmission | `maintenance-execution` | SQL | 1 per Task — berisi FormId, Version, IsMandatory *(kolom baru)* |
| Template snapshot | `maintenance-execution` | Cosmos | Full JSON di-copy dari maintenance-strategy saat plan berpindah ke status SUBMIT, linked by FormSubmissionId |
| Form template (source) | `maintenance-strategy` | Cosmos | Master template, tidak berubah |
| Form metadata | `maintenance-strategy` | SQL | Tidak berubah |

### Relasi
```
WorkOrder (1)  →  PlanId  →  dplan
  └── Task (N)                         → 1 Task per form
        └── FormSubmission (1)         → snapshot terbentuk di sini
              └── [Cosmos: template JSON per tab, linked by FormSubmissionId]
```

---

## Snapshot Mechanism

Snapshot terbentuk **saat plan berpindah ke status SUBMIT (DRAFT → SUBMIT)**, bukan saat form pertama dibuka di lapangan.

**Yang terjadi saat plan di-SUBMIT:**
1. Task dibuat di SQL (1 per form)
2. FormSubmission dibuat di SQL (FormId, Version, IsMandatory)
3. FormSubmissionId terbentuk
4. Full template JSON di-copy dari `maintenance-strategy` Cosmos → `maintenance-execution` Cosmos (linked by FormSubmissionId)

**Mengapa snapshot di sini:** Menyelesaikan masalah offline-first — template sudah tersedia di maintenance-execution sebelum tim turun ke lapangan, tidak perlu fetch real-time saat di lapangan.

---

## Design Decisions

| Keputusan | Detail |
|-----------|--------|
| Submit tanpa form assignment dibolehkan | Plan bisa di-SUBMIT meski tidak ada form yang di-assign — Tab Form di mobile kosong, Finish Execution tidak diblokir |
| Form assignment terkunci setelah SUBMIT | Setelah plan di-SUBMIT, tidak bisa tambah, ubah, maupun hapus form assignment |
| Pre-SUBMIT validation popup | Sistem cek ketersediaan semua FormCode di maintenance-strategy sebelum Planner bisa Confirm submit. Form dianggap tidak available jika: tidak ditemukan sama sekali (hard deleted), `IsActive = 0`, atau `Status = 'Archived'`. Form yang tidak available harus dihapus dari assignment — kecuali jika masih bisa di-aktifkan/un-archive di Form Builder |
| Jika service sheet tidak ada di Form Builder | Tidak ada blocker — Planner tetap bisa submit plan, eksekusi tetap bisa complete. Prinsip: konsistensi across flow |
| Filter form suggestion | Menampilkan form berdasarkan model saja DAN model + service hour — keduanya ditampilkan |
| Modifikasi package dari lapangan (field) | **Deferred to next MVP** |

---

## Evolusi API `maintenance-execution`

**Sebelum:**
PM Shutdown API = pure proxy ke dplan (tidak ada logic/data sendiri)

**Setelah:**
PM Shutdown API = **aggregator**:
- dplan → service plan info (existing proxy)
- maintenance-execution DB → Task + FormSubmission + Cosmos snapshot

Response ke mobile menggabungkan keduanya untuk ditampilkan di workcard.

---

## Workcard PM Shutdown (Mobile)

```
Workcard
├── Tab: Backlog  → existing (backlog execution dari dplan)
└── Tab: Form     → NEW — menampilkan package forms
      └── List form: nama form, mandatory/opsional, status (belum diisi / in-progress / submitted)
```

### Tombol Start & Akses Pengisian Form

| Kondisi | Tombol Start | Bisa Isi Form? |
|---------|-------------|----------------|
| Mechanic belum assign diri ke form | Tidak muncul | ❌ Tidak — hanya bisa lihat |
| Mechanic sudah assign, belum tap Start | ✅ Muncul | ❌ Tidak — form read-only sampai Start di-tap |
| Mechanic sudah assign, sudah tap Start | ✅ Muncul setiap buka form | ✅ Ya — bisa mengisi form |
| Form sudah di-Submit | Tidak muncul | ❌ Tidak — form final, read-only |

> Form card selalu bisa dibuka oleh siapapun untuk dilihat. Namun untuk mengisi, mechanic harus sudah assign diri **dan** sudah tap Start.

---

## Open Items

- [ ] Desain UX Planner untuk package composition di Digiplan (web)
- [ ] Desain UX Tab Form di workcard mobile (list form, status indicator)
- [x] Enforcement mandatory form saat eksekusi → **blocking** — Finish Execution tidak bisa dilakukan sampai semua mandatory form status `Complete` (lihat `pm-shutdown-form-execution.md`)
- [ ] Skenario field team menemukan pekerjaan tak terduga → **next MVP**
- [ ] Konfirmasi: apakah ada data package config yang perlu disimpan di dplan DB juga, atau cukup di maintenance-execution
