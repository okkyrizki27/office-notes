# Mechanic Productivity Report — Management View

Dokumen ini merangkum diskusi tentang management view dari Mechanic Activity Report — laporan produktivitas high-level yang menampilkan agregasi data timesheet per section, level, dan individu.

*Last updated: 2026-06-23*

---

## Target User

| User | Scope |
|------|-------|
| **Site Manager** | Hanya bisa melihat data di site-nya sendiri |
| **HO** | Bisa melihat semua site dan membandingkan antar site |

---

## Grouping Hierarchy

```
Site → Section → Level → Individual
```

---

## Data Level / Jabatan

| LevelId | LevelName | Keterangan |
|---------|-----------|------------|
| 2 | Mechanic | Personel lapangan level mechanic |
| 3 | Foreman | Setara mechanic, posisi lebih senior |
| 4 | Supervisor | Setara mechanic, posisi paling senior |

> Semua level (2, 3, 4) melakukan pekerjaan lapangan dan masuk ke productivity report. Level hanya menunjukkan senioritas, bukan perbedaan jenis pekerjaan.

Nama LevelName tidak perlu mencantumkan site (cukup "Mechanic", bukan "Mechanic ADT"). Site disimpan di kolom terpisah.

---

## Contoh Section

| Section |
|---------|
| OB Hauler |
| OB Loader |
| SGE |
| Coal Transport |

---

## Metric Produktivitas

| Metric | Keterangan | Formula |
|--------|------------|---------|
| **Total Jam** | Total jam kerja seluruh aktivitas | Σ durasi semua baris aktivitas |
| **Jam Maintenance** | Total jam kategori Maintenance | Σ durasi baris Maintenance |
| **Jam Non Maintenance** | Total jam kategori Non Maintenance | Σ durasi baris Non Maintenance |
| **Utilization Rate** | Proporsi jam produktif (Maintenance) | Jam Maintenance ÷ Total jam kerja terjadwal (hari Off dikeluarkan dari perhitungan) |
| **Jumlah personel aktif** | Personel yang sudah submit report | Count status Submitted / Approved |

> Metric tambahan bisa ditambahkan seiring kebutuhan berkembang.

---

## Struktur Halaman (Site Manager View)

### 1. Filter Bar
- Periode (default: periode aktif)
- Section (default: Semua)
- Level (default: Semua)
- Status Report (Semua / Approved / Submitted / Draft)

### 2. Summary Strip
Angka agregat untuk seluruh scope yang dipilih:
- Total personel
- Total jam
- Total jam Maintenance
- Total jam Non Maintenance
- Average utilization rate

### 3. Section Cards
Satu card per section, menampilkan:
- Nama section
- Jumlah personel & jumlah yang sudah submit
- **Utilization rate** + progress bar (warna: hijau ≥75%, kuning 60–74%, merah <60%)
- Jam Maintenance, Jam Non Maintenance, Total Jam
- Breakdown jumlah per level (Mechanic / Foreman / Supervisor)
- Link "Lihat detail personel"

### 4. Individual Table
Tabel semua personel dalam scope filter, dengan kolom:
- Nama & Employee ID
- Level
- Section
- Utilization rate (dengan mini bar)
- Jam Maintenance
- Jam Non Maintenance
- Total Jam
- Status Report
- Link ke detail report individu (buka Approver View)

---

## HO View

Sama dengan Site Manager View, dengan tambahan:
- Filter **Site** (bisa pilih semua atau spesifik)
- Section cards diganti / dilengkapi **Site cards** untuk compare antar site
- Drill down: Site → Section → Level → Individual

---

## Warna Utilization Rate

| Range | Warna | Makna |
|-------|-------|-------|
| ≥ 75% | 🟢 Hijau | Produktivitas tinggi |
| 60–74% | 🟡 Kuning | Perlu perhatian |
| < 60% | 🔴 Merah | Produktivitas rendah |

---

## Source Data

Management report dihitung dari **Mechanic Activity Report yang sudah disubmit atau diapprove**. Report berstatus Draft tidak masuk perhitungan.

### Catatan Data

| Data | Source | Keterangan |
|------|--------|------------|
| StartDate / EndDate | `TaskPersonalizedLog` | Dari Phase 1 |
| ShiftName | `TaskPersonalizedLog` | Dari Phase 1 |
| UserFullName | `TaskPersonalizedLog` | Snapshot saat sesi dibuat — tetap tersedia meski mechanic resign dan dihapus dari UserEmploymentProfile |
| SiteCode + SiteName | `TaskPersonalizedLog` | Snapshot saat sesi dibuat — akurat meski mechanic pindah site |
| SectionId + SectionName | `TaskPersonalizedLog` | Snapshot saat sesi dibuat — akurat meski mechanic pindah section |
| UserCode | via `TaskPersonalized` | |
| Unit / Equipment | via `Task` → `WorkOrder` | |
| Kategori | Semua dari sistem = **Maintenance**. Non Maintenance = manual input mechanic saja | Tidak ada kategorisasi form di Phase 1 |
| Daily Work Schedule | **Dikerjakan di Phase 4** | Integrasi DWS untuk mengetahui hari Off / shift per mechanic |

---

## Open Items

- [ ] Definisi "jam kerja terjadwal" — berapa jam per shift yang dianggap standar? (misal: Day Shift = 10 jam, Night Shift = 10 jam) untuk menghitung denominator Utilization Rate
- [x] Hari Off dari Daily Work Schedule dikeluarkan dari perhitungan Utilization Rate
- [ ] Apakah HO view bisa export ke Excel / PDF?
- [ ] Threshold utilization rate — 75% dan 60% perlu dikonfirmasi ke management apakah sesuai standar perusahaan
- [ ] Apakah perlu notifikasi / alert jika ada section dengan utilization di bawah threshold?
