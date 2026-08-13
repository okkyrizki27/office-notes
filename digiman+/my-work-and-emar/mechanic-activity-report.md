# Mechanic Activity Report — Phase 4

Dokumen ini merangkum diskusi tentang fitur Electronic Mechanic Activity Report di Digiman+ — timesheet bulanan yang disubmit mechanic dan diapprove oleh supervisor.

*Last updated: 2026-06-22*

---

## Konsep

Setiap bulan, mechanic menyusun dan mengsubmit **activity report** yang merangkum seluruh aktivitas kerjanya selama periode tersebut. Report ini menjadi dasar perhitungan allowance dan kebutuhan reporting lainnya.

---

## Kategori Aktivitas

| Kategori | Keterangan | Source |
|----------|------------|--------|
| **Maintenance** | Semua pekerjaan terkait unit: service rutin, backlog execution, inspection, dll. | TaskPersonalizedLog (otomatis) + manual input |
| **Non Maintenance** | Aktivitas di luar pekerjaan unit: training, safety briefing, admin, standby, dll. | Manual input saja |

---

## Baseline Jam Kerja

Baseline adalah target jam kerja harian yang dikonfigurasi per site oleh **Admin HO**. Digunakan sebagai pembanding terhadap jam aktual mechanic dalam satu periode laporan.

### Konfigurasi

| Field | Keterangan |
|-------|------------|
| `SiteCode` | Site yang berlaku |
| `HoursPerDay` | Target jam kerja per hari (misal: 10 jam) |
| `EffectiveFrom` | Tanggal mulai berlaku — historis terjaga jika baseline berubah |
| `IsActive` | Soft flag |
| `CreatedBy / CreatedAt` | Audit |

> Konfigurasi dilakukan oleh Admin HO. Satu site bisa punya satu baseline aktif. Jika baseline berubah, laporan historis menggunakan baseline yang berlaku pada periode laporan tersebut (`EffectiveFrom`).

### Perhitungan

```
Expected Hours = HoursPerDay × jumlah hari kerja dalam periode
                 (hari kerja = hari kalender - weekend - hari libur nasional)

Actual Hours   = total durasi semua aktivitas dalam periode

Deviasi        = Actual - Expected
                 → positif (+x jam) jika melebihi baseline
                 → negatif (-y jam) jika belum memenuhi baseline

Utilization Rate = (Actual / Expected) × 100%
```

---

## Data yang Ditampilkan

### Header / Identitas

| Data | Sumber |
|------|--------|
| Nama mechanic | UserEmploymentProfile |
| Employee ID | UserEmploymentProfile |
| Jabatan | UserEmploymentProfile |
| Site | UserEmploymentProfile |
| Section | UserEmploymentProfile |
| Periode (bulan & tahun) | Input saat buat report |
| Status | Draft / Submitted / Approved |

### Monthly Summary

| Data | Keterangan |
|------|------------|
| Total Jam Maintenance | Jumlah durasi semua baris kategori Maintenance |
| Total Jam Non Maintenance | Jumlah durasi semua baris kategori Non Maintenance |
| Total Jam Keseluruhan (Actual) | Gabungan keduanya |
| Expected Hours | `HoursPerDay` × hari kerja dalam periode (dari baseline site) |
| Deviasi | Actual − Expected → ditampilkan sebagai `+x jam` atau `−y jam` |
| Utilization Rate | `(Actual / Expected) × 100%` |

### Daily Detail

Setiap baris = satu sesi aktivitas:

| Kolom | Mandatory | Keterangan |
|-------|-----------|------------|
| Tanggal | ✅ | |
| Shift | ✅ | Day Shift / Night Shift |
| Kategori | ✅ | Maintenance / Non Maintenance |
| Unit / Equipment | ✅ Maintenance / ❌ Non Maintenance | Nomor unit |
| Aktivitas | ✅ | Nama form (system) atau deskripsi manual |
| Mulai | ✅ | StartDate dari TaskPersonalizedLog atau input manual |
| Selesai | ✅ | EndDate dari TaskPersonalizedLog atau input manual |
| Durasi | - | Kalkulasi otomatis Selesai − Mulai |
| Source | - | `system` / `manual` |

---

## Contoh Data

### Header

| Field | Nilai |
|-------|-------|
| Nama | Agus Priyanto |
| Employee ID | 10028706 |
| Jabatan | Mechanic |
| Site | ADT |
| Section | Heavy Equipment |
| Periode | Juni 2026 |
| Status | Draft |

### Monthly Summary

| Kategori | Total Jam |
|----------|-----------|
| Maintenance | 142 jam |
| Non Maintenance | 16 jam |
| **Total Actual** | **158 jam** |
| Expected (10 jam × 22 hari kerja) | 220 jam |
| **Deviasi** | **−62 jam** |
| **Utilization Rate** | **71.8%** |

### Daily Detail

| Tanggal | Shift | Kategori | Unit | Aktivitas | Mulai | Selesai | Durasi | Source |
|---------|-------|----------|------|-----------|-------|---------|--------|--------|
| 2026-06-02 | Day Shift | Maintenance | HDKM78002 | Service Sheet 500hrs | 08:00 | 11:30 | 3.5 jam | system |
| 2026-06-02 | Day Shift | Maintenance | HDKM78002 | Welding Form | 13:00 | 15:00 | 2 jam | system |
| 2026-06-03 | Day Shift | Maintenance | HDKM78003 | Service Sheet 250hrs | 07:30 | 10:00 | 2.5 jam | system |
| 2026-06-03 | Night Shift | Maintenance | HDCT890002 | Backlog Execution | 19:00 | 23:00 | 4 jam | system |
| 2026-06-05 | Day Shift | Non Maintenance | — | Safety Briefing bulanan | 08:00 | 09:00 | 1 jam | manual |
| 2026-06-10 | Night Shift | Maintenance | HDKM78003 | Service Sheet 1000hrs | 20:00 | 00:30 | 4.5 jam | system |
| 2026-06-15 | Day Shift | Non Maintenance | HDCT890002 | Standby — menunggu parts | 10:00 | 13:00 | 3 jam | manual |

---

## Data Backend (tidak ditampilkan langsung)

| Data | Keterangan |
|------|------------|
| `TaskPersonalizedLogId` | FK ke log jika source = system, untuk traceability |
| `SubmittedAt` | Timestamp saat mechanic submit |
| `ApprovedBy` | UserCode supervisor yang approve |
| `ApprovedAt` | Timestamp saat approved |

---

## Kebutuhan UI Tambahan (untuk Estimasi Effort)

Mockup yang sudah ada meng-cover: list bulanan mechanic ([report-design-mechanic-mobile.html](report-design-mechanic-mobile.html)), walkthrough per-hari dengan add/edit/delete manual ([report-design-mechanic-day-detail.html](report-design-mechanic-day-detail.html)), dan detail + approve/reject approver ([report-design-approver-web.html](report-design-approver-web.html)). Yang **belum** ada mockup-nya:

| # | Layar | Deskripsi | Catatan |
|---|-------|-----------|---------|
| 1 | Form/modal "Tambah Manual" itu sendiri | Mockup hanya menampilkan tombolnya, bukan form input-nya (field, validasi, unit picker) | **Kemungkinan sama** dengan layar "Tambah Aktivitas" di [my-work.md](my-work.md) — lihat catatan cross-cutting di bawah |
| 2 | Ganti Periode | Mockup punya tombol "Ganti ›" tapi UI pemilihan periode (kalender/list bulan) belum didesain | |
| 3 | Riwayat Report (periode lampau) | List report mechanic dari periode-periode sebelumnya berikut statusnya | |
| 4 | State Rejected + edit-resubmit | Mechanic melihat komentar penolakan supervisor, edit, lalu submit ulang | Tergantung keputusan open item "kebijakan editing setelah submit" |
| 5 | Approver — Inbox/Queue | List semua report yang menunggu approval supervisor ini | Breadcrumb "Activity Reports" di [report-design-approver-web.html](report-design-approver-web.html) mengimplikasikan halaman ini ada, tapi belum didesain |
| 6 | Approver — Bulk approve | Approve beberapa report sekaligus | Nice-to-have, perlu keputusan scope |
| 7 | Admin HO — Config Baseline Jam Kerja | CRUD `HoursPerDay` per site dengan histori `EffectiveFrom` | Konsep data sudah ada di dokumen ini (bagian Baseline Jam Kerja), UI-nya belum sama sekali |
| 8 | Notifikasi (submit/approve/reject) | | Dependency sama dengan yang dicatat di [my-work.md](my-work.md) |
| 9 | Export PDF/Excel | Open item lama, UI (tombol, pilihan format) belum didesain | |

---

## Kebutuhan Backend (untuk Estimasi Effort)

| # | Item | Jenis | Deskripsi | Catatan |
|---|------|-------|-----------|---------|
| 1 | Entity "report envelope" (mis. `McActivityReport`) | **Keputusan desain, bukan cuma tabel** | Dokumen ini baru mencatat field `SubmittedAt`/`ApprovedBy`/`ApprovedAt` tanpa nama entity konkret — perlu entity first-class untuk Status (Draft/Submitted/Approved/Rejected) + Period per mechanic, agar Approve/Reject/Comment punya tempat nempel | Rejected juga perlu keputusan: apakah reopen editing untuk periode lampau tanpa mengganggu data yang sedang dicatat di periode berjalan? |
| 2 | Baseline hours config | Tabel + CRUD API | `SiteCode`/`HoursPerDay`/`EffectiveFrom`/`IsActive` — struktur sudah dijelaskan di atas, API & permission belum discope | |
| 3 | Submit API | API baru | Lock manual entries periode berjalan, hitung summary (Total/Maintenance/NonMaintenance/Expected/Deviasi/Utilization), buat/update report envelope, notify supervisor | |
| 4 | Approve/Reject API | API baru | Update status envelope, simpan comment, notify mechanic | Lihat catatan reopen-editing di item #1 |
| 5 | Aggregasi Management Productivity | **Pertanyaan arsitektur, bukan cuma effort** | Cross-section/individu (Site→Section→Level→Individual) atas ratusan mechanic | Semua "report" lain di repo ini (`report/transaction-report`, dll.) dibangun sebagai SQL view di atas curated data lake (`openrowset`/Synapse), bukan halaman app dengan API OLTP. Apakah Management Productivity View **sama pola-nya** (BI report/Power BI) atau **benar-benar halaman app baru** dengan RBAC Site Manager vs HO? Keputusan ini mengubah effort secara signifikan — sebaiknya diputuskan sebelum estimasi |
| 6 | Integrasi DWS (`dplan.Dws`) | Integrasi lintas service | Perlu untuk deteksi hari Off/shift per mechanic per periode (gap-detection "hari kerja belum ada aktivitas" + denominator Utilization Rate) | Belum ada wiring cross-DB (`maintenance-execution`/reporting membaca `dplan.Dws`) di dokumentasi manapun yang ditemukan |
| 7 | Notifikasi | Integrasi | Dependency sama dengan yang dicatat di [my-work.md](my-work.md) | |
| 8 | Export service (PDF/Excel) | Servis baru | Kemungkinan besar **bukan reuse** — proses PDF internal yang ada (render HTML→PDF via headless Chrome) untuk dokumen kerja tim, bukan generation dari dalam app | |
| 9 | Job lock/deadline submission | Scheduled job | Hanya relevan jika open item "batas waktu submit" diputuskan ada | |

> **Cross-cutting dengan My Work:** BE #1-3 dan UI #1 kemungkinan besar berbagi implementasi dengan `UserActivityLog` dan endpoint "Tambah Aktivitas" yang dicatat di [my-work.md](my-work.md) — jangan diestimasi dua kali sebagai fitur terpisah.

---

## Open Items

- [x] Baseline jam kerja — per hari, per site, dikonfigurasi Admin HO. Ditampilkan sebagai Expected vs Actual + Deviasi (+/-) + Utilization Rate
- [ ] Apakah utilization rate perlu dipecah per kategori (Maintenance vs Non Maintenance), atau cukup total?
- [ ] Approval flow detail — single level supervisor atau bisa bertahap ke superintendent?
- [ ] Platform approval — web atau mobile?
- [ ] Kebijakan editing setelah submit — apakah mechanic bisa recall/edit report yang sudah Submitted?
- [ ] Lock setelah Approved — mekanisme amendment jika ada koreksi pasca approval?
- [ ] Batas waktu submit — apakah ada deadline submit per bulan?
- [ ] Aktivitas lintas bulan — sesi yang mulai akhir bulan dan selesai awal bulan berikutnya masuk bulan mana?
- [ ] Sub-kategori Non Maintenance — flat atau perlu rincian (training, briefing, standby, dll)?
- [ ] Supervisor notes — apakah supervisor bisa tambahkan komentar saat approve?
- [ ] Kebijakan device mechanic — gadget pribadi atau difasilitasi perusahaan?
- [x] Daily Work Schedule (DWS) integration → dikerjakan di Phase 4
- [x] Section mechanic disimpan sebagai snapshot di `TaskPersonalizedLog` — `SectionId` + `SectionName` (Phase 1)
- [x] Site mechanic disimpan sebagai snapshot di `TaskPersonalizedLog` — `SiteCode` + `SiteName` (Phase 1)
- [x] Nama mechanic disimpan sebagai snapshot `UserFullName` di `TaskPersonalizedLog` — data tetap tersedia meski mechanic resign dan dihapus dari UserEmploymentProfile (Phase 1)
- [x] Tidak ada kategorisasi form — semua aktivitas dari sistem otomatis = Maintenance
