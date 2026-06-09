# Meeting Notes — Diskusi Integrasi Digiman+ ke WICOPE Dashboard

**Tanggal:** 20 Mei 2026  
**Agenda:** Diskusi tentang data integrasi Digiman+ ke WICOPE Dashboard delay

## Peserta

Rahimon, Laili, Febrina, Rico, Rengga, Faisal, Laila, Okky, Varian, Ivan

## Isi Diskusi

1. Ada 2 sumber data yang digunakan:
   - **Digital Planning** — ditarik langsung ke DB (pipeline setiap hari jam 05:00, 11:00, 17:00, 23:00)
   - **WICOPE Check, Washing Form, Inspection & Order** — melalui pipeline, lalu dipublish via API

2. Sudah ada notifikasi ke Teams group terkait *last update* data, namun belum terdapat keterangan *last sync*.

3. User belum memahami syarat-syarat agar data transaksi mereka masuk atau tersinkronisasi ke dashboard.

4. User kemungkinan tidak mengetahui bahwa dashboard tidak bersifat realtime.

## Data Flow: Digiman+ → WICOPE Dashboard

### Flow 1: WICOPE Check, Washing Form, Inspection & Order

```
[1] Digiman+
    └─ User mengisi form
    └─ Pastikan data sudah sync ke server

        ↓

[2] Pipeline Btech (setiap hari jam 04:00, 10:00, 16:00)
    └─ Memproses data WICOPE Check, Washing Form, Inspection & Order

        ↓

[3] Data Lake
    └─ Data disimpan dan siap dipublish via API

        ↓

[4] Pipeline BUMA (setiap hari jam 05:00, 11:00, 17:00, 23:00)
    └─ Menarik data dari API ke Dashboard

        ↓

[5] Data Transformasi
    └─ Data diolah/ditransformasi terlebih dahulu

        ↓

[6] WICOPE Dashboard
    └─ Data muncul di Dashboard (~1 jam setelah pipeline berjalan)
```

> **Estimasi delay total:** Jika pipeline Btech jam 04:00 → BUMA tarik jam 05:00 → muncul di Dashboard ~06:00

---

### Flow 2: Digital Planning

```
[1] DPlanDB
    └─ Sumber data Digital Planning

        ↓

[2] Pipeline Btech & BUMA (setiap hari jam 05:00, 11:00, 17:00, 23:00)
    └─ Ambil data dari DPlanDB → taruh di Staging
    └─ Data diolah dari Staging → ditaruh di Final Table
    └─ Ambil data dari Final Table

        ↓

[3] WICOPE Dashboard
    └─ Data muncul melalui proses transformasi data
```

## Action Items

| No | Action | PIC | Due Date |
|----|--------|-----|----------|
|    |        |     |          |

## Keputusan

-

## Next Steps

-
