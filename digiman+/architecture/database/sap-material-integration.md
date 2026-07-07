# SAP → Digiman+ Material Integration

Dokumen ini menjelaskan integrasi data material dari SAP ke Digiman+, di mana data material di Digiman+ diambil dari beberapa tabel master SAP.

## Tabel SAP yang Digunakan

### Data Master Material

| Tabel    | Tujuan Penggunaan                                                            |
| -------- | ----------------------------------------------------------------------------- |
| **MARA** | Mengambil informasi master material.                                          |
| **MAKT** | Mengambil nama atau deskripsi material.                                       |
| **MARC** | Mengambil site/plant tempat material tersedia.                                |
| **MBEW** | Mengambil harga material.                                                     |
| **MARD** | Mengambil storage location dan informasi stok material.                       |
| **AUSP** | Mengambil mapping material terhadap model unit atau atribut klasifikasi lain. |
| **CABN** | Menerjemahkan karakteristik yang digunakan pada data klasifikasi di AUSP.      |

### Data Batch Material

| Tabel    | Deskripsi                                                                                                    |
| -------- | ------------------------------------------------------------------------------------------------------------- |
| **MCHA** | Master data batch per material (batch master): nomor batch, tanggal produksi, tanggal kedaluwarsa, dll.       |
| **MCHB** | Stok batch per plant dan storage location: jumlah stok untuk setiap batch.                                    |
| **MCH1** | Batch master lintas plant (cross-plant batch), jika konfigurasi SAP menggunakan cross-plant batch management. |

---

## Diagram Relasi

### Master Material, Plant, Harga, Stok & Batch

```
            MARA
       ┌──────┼────────────┐
       │      │            │
     MAKT   MARC         MBEW
              │
              ▼
            MARD
              │
              ▼
            MCHB
              ▲
              │
            MCHA
```

> `MCH1` (cross-plant batch) belum masuk ke alur di atas — hanya relevan jika konfigurasi SAP menggunakan cross-plant batch management. Perlu dikonfirmasi lebih lanjut bagaimana posisinya relatif terhadap MCHA/MCHB.

### Klasifikasi Material

```
     MARA
       │
       ▼
     AUSP
       │
       ▼
     CABN
```

---

*Last updated: 2026-07-06*
