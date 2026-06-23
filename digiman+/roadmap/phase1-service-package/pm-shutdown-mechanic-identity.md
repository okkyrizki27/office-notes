# PM Shutdown — Mechanic Identity & Authentication

Dokumen ini merangkum diskusi tentang bagaimana mechanic diidentifikasi saat mengisi form di PM Shutdown mobile.

*Last updated: 2026-06-22*

---

## Konteks

Mechanic tidak memiliki user account individual di Digiman+. Namun mechanic sudah terdaftar sebagai employee di tabel `UserEmploymentProfile` dengan data berikut yang relevan:

- `UserCode` → email, **not null** untuk semua mechanic
- `EmployeeId` → unique identifier
- `PositionName` → nama posisi (tidak terstandarisasi, contoh: "Mechanic IPR", "Mechanic ADT", "Mechanic - Internal Repair IPR")
- `SectionId` / `SectionName` → section tempat mechanic bertugas
- `SiteId` → site lokasi kerja

### Catatan Data Quality
- `PositionName` tidak terstandarisasi — perlu pattern matching untuk filter mechanic
- `SectionId` tertentu memiliki lebih dari satu `SectionName` (data inconsistency)
- `SectionName` bisa NULL untuk beberapa record

---

## Dua Opsi

### Opsi 1: Shared User per Section + Mapping Config

Setiap section memiliki satu shared user account. Mechanic login menggunakan shared account section-nya, lalu memilih nama mereka sendiri dari list saat mengisi form.

**Contoh shared user:**
- `IPR_hauler_shared@bukitmakmur.com` → semua mechanic section Hauler
- `IPR_loader_shared@bukitmakmur.com` → semua mechanic section Loader
- dst.

**Mekanisme:**
- Config mapping: EmployeeId → SharedUserId (perlu dimaintain terpisah)
- List mechanic di-derive dari mapping config tersebut
- Saat mechanic memilih nama → activity direcord atas nama mechanic yang dipilih

| | |
|--|--|
| **Pro** | Cocok jika mechanic tidak punya device sendiri |
| **Con** | Perlu maintain config mapping — beban operasional |
| **Con** | Risiko mapping salah akibat data inconsistency di SectionName |
| **Con** | Session concurrency risk — satu shared account bisa login di banyak device bersamaan |
| **Con** | Self-declaration — mechanic bisa memilih nama yang salah |
| **Con** | Butuh tim IT untuk manage shared accounts |

---

### Opsi 2: Individual Account per Mechanic

Setiap mechanic login dengan akun individual menggunakan email (`UserCode`) yang sudah ada di sistem.

**Mekanisme:**
- `UserCode` (email) sudah not null untuk semua mechanic → foundation sudah tersedia
- Tinggal provisioning akun dari data yang sudah ada
- Tidak perlu config mapping tambahan

| | |
|--|--|
| **Pro** | `UserCode` (email) sudah ada dan not null — effort provisioning rendah |
| **Pro** | True authentication — tidak ada self-declaration risk |
| **Pro** | Tidak perlu config mapping tambahan |
| **Pro** | Audit trail solid — penting untuk compliance di mining industry |
| **Con** | Perlu account provisioning untuk banyak mechanic |
| **Con** | Jika mechanic tidak punya device sendiri, harus login/logout di shared device setiap shift |

---

## Pertimbangan Keputusan

Faktor penentu utama: **apakah mechanic punya device masing-masing atau shared device?**

- Jika mechanic punya device sendiri → **Opsi 2** lebih clean dan accountable
- Jika mechanic menggunakan shared device → kedua opsi bisa dipertimbangkan, tapi Opsi 2 tetap lebih defensible dari sisi compliance

**Rekomendasi awal:** Opsi 2 — karena `UserCode` sudah tersedia, tidak butuh config tambahan, dan audit trail lebih kuat untuk industri mining yang heavily regulated.

---

## Open Items

- [ ] Konfirmasi ke client: apakah mechanic punya device masing-masing atau shared device?
- [ ] Jika Opsi 1 dipilih: siapa yang bertanggung jawab maintain config mapping?
- [ ] Jika Opsi 2 dipilih: bagaimana proses provisioning akun mechanic (bulk atau per request)?
- [ ] Dashboard monitoring dan compliance report untuk track aktivitas mechanic (berlaku untuk kedua opsi)
