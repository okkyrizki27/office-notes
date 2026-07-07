# Perbandingan Data Oil Sample Analysis: Web Scrapper vs API

> **Update 2026-07-06:** API sudah di-re-fetch dengan `-Depth 10` pada `ConvertTo-Json`. Bug lama (nested object jadi `System.Object[]` sehingga nilai test kosong) sudah **teratasi** — field `test[].result` sekarang berisi nilai numerik aktual. Perbandingan di bawah menggunakan pasangan unit yang sama (bukan unit berbeda seperti versi sebelumnya).

## Sample yang Dibandingkan

Satu-satunya `unit_no` yang muncul di kedua sumber data adalah **DZ0957** (Caterpillar D11T, serial AMA00589), kompartemen yang sama: **ENGINE PRIMARY - DIESEL (101)**. Karena sample date berbeda jauh (data web dari Mei 2020, data API dari Juni 2026), nilai wajar berbeda — tujuan perbandingan ini adalah memverifikasi bahwa **struktur & ketersediaan nilai** API sudah setara dengan web, bukan mencocokkan angka.

| | Web Scrapper | API |
|---|---|---|
| **Lab No / Sample ID** | 14758637 | 23384934 |
| **Unit No** | DZ0957 | DZ0957 |
| **Serial No** | AMA00589 | AMA00589 |
| **Equipment** | Caterpillar D11T | Caterpillar D11T |
| **Compartment** | ENGINE PRIMARY - DIESEL | ENGINE PRIMARY - DIESEL |
| **Sample Date** | 02/05/2020 | 2026-06-25 |
| **Oil Type/Grade** | 15W40 (Mobil Delvac Modern Extreme) | TOTAL RUBIA WORKS 5000 10W40 |
| **Evaluation** | A | A |

---

## Perbandingan Elemen Analisis

### ICP — Inductively Coupled Plasma (Wear Metals & Additives)

> Mengukur kandungan logam dan aditif dalam oli dalam satuan ppm.

| Element | Web (2020) | API (2026) | Keterangan |
|---|---|---|---|
| Cu (Copper) | `<1` | `<1` | Bearing wear indicator |
| Fe (Iron) | `10` | `8` | Ferrous wear |
| Cr (Chromium) | `<1` | `<1` | Ring/liner wear |
| Pb (Lead) | `<1` | `<1` | Bearing wear |
| Al (Aluminium) | `<1` | `2` | Piston/housing wear |
| Si (Silicon) | `5` | `8` | Dust/dirt contamination |
| Sn (Tin) | `<1` | `<1` | Bearing wear |
| Ni (Nickel) | `<1` | `<1` | Wear indicator |
| Na (Sodium) | `4` | `3` | Coolant leak indicator |
| K (Potassium) | `1` | `4` | Coolant leak indicator |
| Mo (Molybdenum) | `206` | `<1` | Additive/wear |
| Ca (Calcium) | `2917` | `1308` | Detergent additive |
| Mg (Magnesium) | `155` | `625` | Additive |
| P (Phosphorus) | `1078` | `619` | Anti-wear additive |
| Zn (Zinc) | `1246` | `681` | ZDDP additive |
| Ti (Titanium) | `<1` | `<1` | Wear indicator |
| Sb (Antimony) | `<1` | `<1` | Wear indicator |
| V (Vanadium) | `<1` | `<1` | Wear indicator |
| B (Boron) | `74` | `55` | Additive/coolant |
| Ag (Silver) | `<1` | `<1` | Wear indicator |
| Mn (Manganese) | `<1` | `<1` | Wear indicator |
| Cd (Cadmium) | `<1` | `<1` | Wear indicator |
| Ba (Barium) | `<1` | `<1` | Additive |
| Li (Lithium) | `<1` | `<1` | Grease contamination |
| In (Indium) | ❌ tidak ada kolom | `<1` | **API only** — tidak ada padanan kolom di web |
| Bi (Bismuth) | ❌ tidak ada kolom | `<1` | **API only** — tidak ada padanan kolom di web |
| **Subtotal ICP** | **24 elemen** | **26 elemen** | API kini punya nilai lengkap + 2 elemen tambahan |

Selisih nilai (mis. Mo 206 vs `<1`, Ca 2917 vs 1308) wajar karena beda merek/formulasi oli antar sample (Mobil Delvac vs Total Rubia) dan beda 6 tahun waktu sampling, bukan indikasi bug.

### Visc — Viscosity

| Parameter | Web (2020) | API (2026) | Keterangan |
|---|---|---|---|
| v40 (Viscosity @ 40°C) | `113` cSt | ❌ (kompartemen ini tidak mengembalikan v40, hanya v100+VI) | Konsistensi viskositas |
| v100 (Viscosity @ 100°C) | `13.8` cSt | `12.5` cSt | Viskositas operasional |
| vi (Viscosity Index) | `121` | `147` | Stabilitas viskositas terhadap suhu |
| **Subtotal Visc** | **3 parameter** | **2 parameter bernilai** | API tidak selalu mengembalikan v40 tergantung hasil analisis lab |

### FTIR — Fourier Transform Infrared

| Parameter | Web (2020) | API (2026) | Keterangan |
|---|---|---|---|
| ust (Soot/Carbon) | `8` | `8` | Produk pembakaran |
| uoxi (Oxidation) | `16` | `15` | Degradasi oksidasi oli |
| usul (Sulfation) | `22` | `22` | Sulfur contamination |
| unit (Nitration) | `8` | `<1` | Nitrogen contamination |
| **Subtotal FTIR** | **4 parameter** | **4 parameter bernilai** | ✅ Cocok penuh secara struktur |

### F — Fuel Dilution

| Parameter | Web (2020) | API (2026) | Keterangan |
|---|---|---|---|
| f (Fuel %) | `<2.0` % | `<2.0` % | Fuel masuk ke oli |
| **Subtotal F** | **1 parameter** | **1 parameter bernilai** | ✅ Cocok, sama persis |

### Wat — Water Content

| Parameter | Web (2020) | API (2026) | Keterangan |
|---|---|---|---|
| wat (Water %) | `<0.1` % | `0.1` % | Kandungan air dalam oli |
| **Subtotal Wat** | **1 parameter** | **1 parameter bernilai** | ✅ Cocok |

### PQ — Particle Quantifier

| Parameter | Web (2020) | API (2026) | Keterangan |
|---|---|---|---|
| pq | `<1` | `<1` | Indeks partikel ferrous magnetik |
| **Subtotal PQ** | **1 parameter** | **1 parameter bernilai** | ✅ Cocok, sama persis |

### DEP — Debris Evaluation Program

| Parameter | Web (2020) | API (2026) | Keterangan |
|---|---|---|---|
| dep | `N--B` | `N--B` | Kode evaluasi debris (Normal-Brass) |
| **Subtotal DEP** | **1 parameter** | **1 parameter bernilai** | ✅ Cocok, sama persis |

---

## Rekapitulasi

| Analysis Type | ID di API | Jumlah Parameter (Web) | Ada Nilai di API? | Ada di Web? |
|---|---|---|---|---|
| ICP | `ICP` | 24 elemen | ✅ 26 nilai (2 elemen tambahan) | ✅ |
| Viscosity | `Visc` | 3 parameter | ✅ 2 nilai (v40 kadang tidak muncul) | ✅ |
| FTIR | `FTIR` | 4 parameter | ✅ 4 nilai | ✅ |
| Fuel Dilution | `F` | 1 parameter | ✅ 1 nilai | ✅ |
| Water | `Wat` | 1 parameter | ✅ 1 nilai | ✅ |
| Particle Quantifier | `PQ` | 1 parameter | ✅ 1 nilai | ✅ |
| Debris Eval | `DEP` | 1 parameter | ✅ 1 nilai | ✅ |
| **Total (ENGINE)** | **7 types** | **35 parameter** | **✅ 36 nilai** | **✅ 35 nilai** |

### Analysis Type di API yang TIDAK muncul di ENGINE (ada di kompartemen lain)

Sama seperti sebelumnya — ini bergantung jenis kompartemen, bukan bug:

| Analysis ID | Nama | Web Column | Biasa di Kompartemen |
|---|---|---|---|
| `ISO` | ISO Particle Count | `iso`, `pc4`, `pc6`, `pc10`, `pc14`, `pc50` | Hydraulic, Transmission |
| `PCT` | Particle Count Total | `pc4`–`pc50` | Hydraulic, Transmission |
| `Cond` | Conductivity | `ec` | Coolant |
| `Gly` | Glycol | `gly` | Coolant |
| `IC` | Ion Chromatography | `cl-`, `no2`, `no3`, `so4` | Coolant |
| `pH` | pH | `ph` | Coolant |
| `Odr` | Odour | `odour`, `odrodr` | Coolant |
| `PPT` | Precipitation Test | `pptamt`, `pptcol`, `pptmag`, `pptapp` | Coolant |
| `Sol` | Soluble Test | `solint`, `solcol`, `solapp`, `solfoam` | Coolant |
| `TH` | Total Hardness | `th` | Coolant |
| `WKF` | Karl Fischer Water | `wkf` | Hydraulic |
| `PEN` | Penetration | `pen` | Grease |
| `DP` | Drop Point | `dp` | Grease |

Data API terbaru (`from-api/sos_2026-07-06.json`, 219 samples) sudah mencakup kompartemen Hydraulic/Transmission (`ISO`, `PCT`) dan Grease (`WKF`, `PQ`, `DP`, `PEN`) — lihat `from-api/sos_sample_test_results.csv` untuk hasil per elemen di semua kompartemen.

---

## Kesimpulan

**Bug lama sudah teratasi.** Setelah re-fetch dengan `ConvertTo-Json -Depth 10`, field `analysis[].test[].result` di API sekarang berisi nilai numerik aktual, setara dengan data web scrapper. Terverifikasi pada sample DZ0957 (ENGINE PRIMARY - DIESEL): dari 35 parameter yang tersedia di web, 34 punya padanan bernilai di API (hanya `v40` yang kadang tidak dikembalikan tergantung hasil analisis lab), plus API menambahkan 2 elemen ICP (In, Bi) yang tidak ada kolomnya di web scrapper.

**API kini setara atau lebih kaya** dibanding web scrapper: selain nilai elemen, API juga menyediakan metadata level kompartemen (sump capacity, fluid change/sample interval, tanggal receive/process, nama interpreter) yang tidak ada di data web.

**Rekomendasi:** API (`from-api/sos_2026-07-06.json` dan turunannya: `sos_samples_flat.csv`, `sos_sample_analysis.csv`, `sos_sample_test_results.csv`) sudah bisa dijadikan sumber data utama menggantikan web scrapper.
