# Enhancement: Area of Unit & Man Power — Inspection & Order

*Last updated: 2026-07-10*

---

**Feature:** Inspection & Order (Digiman+)
**Related doc:** [../dplan/digital-planning.md](../dplan/digital-planning.md), [../dplan/man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md)
**Effort summary lintas fitur:** [../area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md)

---

## 1. Latar Belakang

Hasil meeting dengan business (10 Jul 2026) terkait penambahan konsep **Area of Unit** — pemetaan lokasi kerusakan/pekerjaan ke tingkat component/sub-component suatu asset — dan **Man Power**, serta enhancement terkait di beberapa fitur: Inspection, Order, Approval Order, dan Digiplan.

---

## 2. Keputusan & Scope

### 2.1 Penamaan Field
- Nama field/kolom yang disepakati: **"Area"** of unit (bukan "Compartment" — istilah lama yang digantikan).

### 2.2 Master Data Mapping Area of Unit ↔ Component/Sub-Component
- **Master data Component↔Sub-Component sudah ada** — yang perlu dibuat baru hanyalah **mapping Area ke kombinasi Component-Sub Component** tersebut (bukan membangun 3 level master data dari nol).
- **Component-SubComponent existing itu ter-mapping ke Model of Equipment/Asset Model** *(dikonfirmasi 10 Jul 2026)* — bukan master list flat global. Artinya kombinasi Component-SubComponent yang valid **berbeda-beda tergantung Asset Model** unit yang diinspeksi/di-plan.
- **Relasi many-to-many** *(dikonfirmasi 10 Jul 2026)*: 1 kombinasi Component-SubComponent bisa terpetakan ke **beberapa** Area, dan 1 Area juga bisa berlaku untuk **beberapa** kombinasi Component-SubComponent. Jadi bukan hierarki 1:N yang rapi (Area → Component → SubComponent), melainkan **tabel mapping/junction M:N** antara Area dan kombinasi Component-SubComponent.
- **⚠️ Belum diklarifikasi**: apakah mapping Area↔Component-SubComponent yang baru ini juga **ikut scoped per Asset Model** (mengikuti pola Component-SubComponent existing), atau Area bersifat **generik lintas Asset Model** (nama Area yang sama berlaku sama di semua model unit)? Ini menentukan struktur tabel mapping baru — kalau ikut per-Asset-Model, mapping-nya jadi 4 dimensi (Asset Model, Component, SubComponent, Area), bukan cuma 3. Perlu diklarifikasi sebelum Master Data UI (di bawah) didesain, karena ini menentukan skema & kompleksitas maintenance datanya.
- Perlu dibuat **Master Data UI baru** khusus untuk mapping M:N ini.
- **Service: `services-asset`** *(dikonfirmasi 11 Jul 2026)* — Master Data ini akan dikembangkan di service **Asset**, konsisten dengan lokasi master data Component-SubComponent existing yang juga ada di service yang sama (lihat data source `mkp_services_asset` yang dipakai di `vw_report_iams_inspection_results.sql`, tabel `assetmodel`, `component`, `subcomponent`, dst).
- **Yang maintain mapping ini** *(dikonfirmasi 10 Jul 2026)*: **admin di HO (Head Office)** — siapapun dengan role admin HO bisa maintain, dibatasi lewat **permission code** (bukan role/user spesifik yang di-hardcode).
- **Penyimpanan data transaksi: by value, bukan by ID reference** *(dikonfirmasi 10 Jul 2026)* — Component/Sub Component/Area yang tersimpan di data transaksi (Finding, eMOL, `PoolingMOItem`, `DPValue` di Digiplan, dst) disimpan sebagai **nilai/snapshot pada saat transaksi terjadi** (mis. nama Component sebagai text), **bukan** sebagai foreign key/ID yang mereferensikan baris Master Data. Konsekuensinya: kalau mapping Master Data berubah/dihapus di kemudian hari, **data transaksi historis tidak terpengaruh sama sekali** — tetap merepresentasikan kondisi valid saat transaksi itu terjadi, tidak jadi stale/orphan. Ini prinsip yang perlu diikuti di semua titik penyimpanan field ini (Inspection, Additional Order, `PoolingMOItem`, Digiplan).
- Enhance transaksi terkait untuk menggunakan mapping ini di: **Inspection**, **Order**, **Approval Order**.
- **Urutan cascading dropdown (dikonfirmasi 10 Jul 2026)**: **Component → Sub Component → Area**, sesuai urutan yang sudah berjalan di Inspection saat ini — dan karena Component sendiri sudah difilter oleh Asset Model unit yang dipilih, urutan lengkapnya efektifnya **Asset Model (dari data unit) → Component → Sub Component → Area**. Digiplan mengikuti urutan yang sama begitu kolom-kolomnya tersedia (lihat 2.4).
- **Auto-fill Area dari MO Backlog tidak bisa didapat dari Component/SubComponent saja** *(dikonfirmasi 10 Jul 2026)* — karena M:N, kombinasi Component-SubComponent **tidak cukup untuk menentukan Area secara unik**. `Area` **wajib dikirim eksplisit** sebagai field tersendiri lewat pipeline Order→SAP→MO Backlog (bukan di-derive ulang dari Component/SubComponent saat data kembali) — memperkuat kenapa Area harus benar-benar jadi field sendiri di assessment SAP (2.5), bukan sekadar "ikut" Component/SubComponent.

### 2.3 Inspection, Additional Inspection & Additional Order
- Saat create finding (Inspection), saat ini **sudah ada** field **Component**, **Sub Component**, dan **Duration**.
- **Tambah field Area of Unit dan Man Power** di create finding — melengkapi 3 field yang sudah ada.
- **Additional Inspection memakai layar yang sama persis dengan Inspection** *(dikonfirmasi 11 Jul 2026)* — satu-satunya perbedaan adalah Additional Inspection bisa dibuat **kapan saja** (ad-hoc), sementara Inspection biasa hanya lewat jadwal (scheduled). Karena form create-finding-nya identik, **tidak perlu effort/baris terpisah** untuk Additional Inspection — penambahan Area + Man Power di form Inspection (baris di atas) otomatis berlaku untuk Additional Inspection juga.
- **Additional Order tetap perlu field yang sama secara terpisah** *(dikonfirmasi 10 Jul 2026)* — beda dengan Additional Inspection, Additional Order adalah **layar/form yang berbeda** dari Inspection (jalur kedua pembuatan eMOL tanpa finding, lihat [order-emol-sap-sync.md](order-emol-sap-sync.md) Bagian 2), jadi field Component, Sub Component, Area, Duration, Man Power perlu ditambahkan terpisah di layar **create Additional Order**. Kalau tidak, MO Backlog yang asalnya dari Additional Order akan selalu kosong untuk field-field tersebut — merusak tujuan utama enhancement ini (auto-fill di Digiplan).
- **Nilai ini otomatis terbawa ke edit eMOL** *(dikonfirmasi 10 Jul 2026)* — pola-nya **carry-forward-with-override**, bukan re-input terpisah: nilai yang diisi saat create Finding/Additional Order **otomatis muncul** di layar edit eMOL (bukan kosong/harus diisi ulang), dan tetap bisa diubah di titik itu kalau perlu. Pola yang sama berlaku sampai ke Order Approval (2.6) — satu nilai mengalir maju dengan kesempatan override di tiap checkpoint, bukan beberapa copy independen yang perlu disinkronkan manual.

### 2.4 Digiplan
- Tambah kolom **Component**, **Sub Component**, **Area** — mengikuti pola yang sama seperti di Inspection, sebagai dynamic column baru lewat mekanisme `DPColumn`/`DPValue` (lihat [digital-planning.md](../dplan/digital-planning.md)).
- **Level/scope**: **per-task (leaf level)** — sama seperti Duration/Man Power, setiap task punya nilai Component/Sub Component/Area sendiri (bukan diisi sekali di header Plan). Relevan karena satu Plan bisa mencakup pekerjaan di banyak component/area berbeda.
- **Cara pengisian**: **dropdown**, diambil dari Master Data mapping Area of Unit → Component/Sub-Component (lihat 2.2) — bukan free text manual. Urutan cascading dropdown **Component → Sub Component → Area**, sama seperti di Inspection (lihat 2.2). Berlaku **konsisten untuk kedua kasus**: (1) task yang berasal dari MO Backlog — nilai auto-fill dari data MO Backlog (lihat 2.5); (2) task/subtask yang **tidak** berasal dari MO Backlog — user input manual **lewat dropdown Master Data yang sama**, bukan free text, supaya datanya tetap konsisten/tervalidasi terlepas dari sumbernya. *(Dikonfirmasi ulang 10 Jul 2026 — sempat diangkat kembali sebagai open question, jawabannya tetap dropdown dari Master Data.)* Ini berarti pengembangan kolom ini **bergantung** pada Master Data UI (2.2) selesai/tersedia lebih dulu.
- **Mandatory/disable**: **custom column biasa** — bisa di-toggle (*Is Shown*) dan dihapus oleh admin lewat Config → Custom Column, **beda perlakuan dari Man Power/Man Hours** yang mandatory & non-disable (lihat [man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md) 3.1). *(Dikonfirmasi 10 Jul 2026 — bukan kontradiksi dengan kegunaan kolom ini menerima data MO Backlog: berbeda dengan Man Power/Man Hours yang mandatory karena ada dependency kalkulasi (`Man Hours = Duration × Man Power`), Component/Sub Component/Area murni informasional tanpa dependency kalkulasi, jadi tidak butuh jaminan "selalu ada". Karena kolom Daily Plan pada dasarnya dinamis, logic yang men-treatment MO Backlog juga harus dinamis — lihat catatan graceful-handling di bawah.)*
- **Graceful handling saat kolom tidak ada di Plan**: kalau Template yang dipakai suatu Plan **tidak** punya kolom Component/Sub Component/Area (di-hide/dihapus admin), sementara MO Backlog yang dipilih user membawa data untuk field-field itu — sistem **harus bisa menghandle situasi ini**, bukan mewajibkan kolom harus selalu ada. Behavior-nya: field yang tidak ada `DPColumn`-nya di Plan tersebut **cukup diabaikan/tidak disimpan** (bukan error, bukan auto-create kolom baru di Plan) — sisanya (field yang memang ada kolomnya) tetap ter-fill normal.
- *(Data ini bisa langsung terisi otomatis saat user pilih MO Backlog di Digiplan — lihat 2.5 untuk kenapa dan bagaimana. Prinsip arsitektur terkait — lihat [digital-planning.md](../dplan/digital-planning.md) Bagian "Prinsip Arsitektur".)*
- **Excel template upload/download juga perlu mengakomodir 3 kolom ini** — bukan cuma Duration/Man Power/Man Hours (lihat [man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md)). *(Dikonfirmasi 10 Jul 2026 — sebelumnya open question, sekarang jelas: ya, dibutuhkan.)*
- **Validasi saat upload (dikonfirmasi 10 Jul 2026)**: kombinasi nilai Component/Sub Component/Area yang di-upload user divalidasi terhadap Master Data mapping (2.2). Kalau kombinasinya **tidak sesuai/tidak ditemukan** di Master Data, **baris tersebut ditolak** (bukan diproses dengan nilai salah, dan bukan silent-ignore seperti perlakuan Man Hours di [man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md) 3.2) — user diberi **warning yang jelas** (baris mana, kombinasi apa yang tidak valid) supaya bisa memperbaiki data dan upload ulang.
- **Representasi di Excel (dikonfirmasi 10 Jul 2026)**: cell Component/Sub Component/Area di template Excel berupa **kolom text biasa** untuk saat ini — **bukan** Excel data-validation dropdown. Validasi terhadap Master Data baru dilakukan saat upload (lihat poin di atas), bukan dicegah di level cell Excel.

### 2.5 Assess Integrasi ke SAP
- **Tujuan assessment**: memastikan data **Component, Sub Component, Area, Duration, Man Power** ikut **dikirim ke SAP saat create Order** (BAPI call, lihat [order-emol-sap-sync.md](order-emol-sap-sync.md) Bagian 5–6) — bukan cuma disimpan lokal di Digiman+.
- **PIC assessment: Faiza** — Faiza adalah pihak **client**, yang akan berkoordinasi langsung dengan tim SAP internal client-nya untuk assessment ini (bukan tim Digiman+/tim BE). Feasibility teknis di sisi SAP (custom Z-field vs numpang di field text existing) jadi tanggung jawab pembahasan client dengan tim SAP mereka.
- **Kondisi saat ini (gap)**: `Component` dan `Sub Component` **sudah** ikut terbawa sampai ke `PoolingMOItem` (lihat [order-emol-sap-sync.md](order-emol-sap-sync.md) Bagian 5.2), tapi **belum** di-mapping/dikirim ke SAP lewat BAPI saat create Order (lihat mapping `GI_HEADER`/`GI_OPER`/`GI_COMP` di Bagian 6.2 — belum ada field ini). `Area`, `Duration`, `Man Power` juga belum ada sama sekali di `PoolingMOItem`/payload/mapping BAPI.
- **Alasan/manfaat**: kalau data-data ini berhasil dikirim ke SAP saat create Order, maka saat MO tersebut **kembali ke Digiman+ sebagai MO Backlog** (flow inbound, lihat [order-emol-sap-sync.md](order-emol-sap-sync.md) Bagian 9), data Component/Sub Component/Area/Duration/Man Power itu **ikut kembali** bersama MO Backlog-nya. Efeknya: saat user membuat Daily Plan di Digiplan dan memilih MO Backlog, field **Component, Sub Component, Area, Duration, Man Power langsung terisi otomatis** dari data MO Backlog — user tidak perlu input manual lagi di Digiplan.
- **Auto-fill ini tetap bisa di-edit** *(dikonfirmasi 10 Jul 2026)* — nilai Component/Sub Component/Area/Duration/Man Power yang auto-fill dari MO Backlog **bukan read-only**. User yang membuat Plan tetap bisa mengubah nilainya, dengan asumsi user (planner) bisa menganalisa dan menyesuaikan dengan kondisi terkini di lapangan (nilai dari MO Backlog adalah plan awal, bukan keputusan final yang mengikat).
- **Edit di Digiplan murni satu arah** *(dikonfirmasi 10 Jul 2026)* — kalau user mengubah nilai auto-fill ini di Digiplan, perubahan tersebut **tidak sync balik** ke Order/eMOL asal maupun ke SAP. Konsisten dengan prinsip "Digiplan tidak integrasi ke Order" — data mengalir satu arah (Order/eMOL → SAP → MO Backlog → Digiplan), edit di Digiplan berhenti di Digiplan.
- **Beda dengan sync status cancel MO** *(dikonfirmasi 10 Jul 2026)* — perlu dibedakan dari mekanisme di atas: kalau MO di SAP di-**cancel**, **sudah ada** mekanisme existing yang membuat MO Backlog terkait di Digiman+ ikut ter-update/dihapus. Jadi "satu arah" di atas khusus untuk **edit value** (Component/SubComponent/Area/Duration/Man Power) yang tidak sync balik — bukan berarti status/lifecycle MO (cancel) juga tidak ter-sync; status cancel tetap ter-refresh normal lewat mekanisme yang sudah ada.
- *(Ini murni soal memperluas jalur Order/eMOL → SAP yang sudah ada — Digiplan sendiri **tidak** melakukan integrasi/panggilan apapun ke SAP maupun ke Order. Ini juga alasan sebenarnya kenapa Digiplan tidak perlu integrasi langsung dengan Order — lihat [digital-planning.md](../dplan/digital-planning.md) Bagian "Prinsip Arsitektur".)*

### 2.6 Order Approval
- Saat approval Order oleh SPV, SPV **memvalidasi** nilai Man Power dan Duration yang sudah diisi — tapi **tetap bisa mengubah** nilainya di titik approval ini (bukan read-only/lock).
- **Component, Sub Component, Area juga ikut divalidasi & bisa diedit** di titik approval yang sama *(dikonfirmasi 10 Jul 2026)* — perlakuan konsisten dengan Man Power/Duration, bukan cuma 2 field itu saja. SPV jadi checkpoint terakhir untuk kelima field ini sebelum data dikirim ke SAP.
- **Aturan validasi & mekanisme input tetap sama persis** *(dikonfirmasi 10 Jul 2026)* — bukan form terpisah yang lebih longgar. SPV tunduk pada aturan yang sama seperti di titik lain: Man Power tetap **wajib, integer, `>0`** (2.3/3.1), dan Component/Sub Component/Area tetap lewat **dropdown Master Data dengan cascading Component→Sub Component→Area** (2.2/2.4), bukan free text.

---

## 3. Scope Perubahan & Estimasi Effort

*(SP dikalibrasi ke skala Fibonacci `[1,2,3,5,8]` — konvensi tim BUMA ID, lihat metodologi kalibrasi di [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md). Mandays dihitung dari rasio throughput ~0.98 mandays/SP — basis 5 sprint terakhir, konsisten dengan basis velocity yang dipakai untuk estimasi jumlah sprint.)*

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| Master Data UI baru (service `services-asset`): mapping Area ↔ Component-Sub Component (M:N) | Sedang–Besar | 5 | 4.9 | CRUD + validasi M:N; bisa naik ke 8 SP kalau ternyata perlu scoped per Asset Model (4 dimensi, lihat open item Bagian 4) — **belum final selama open item itu belum dijawab** |
| Permission code baru untuk maintain Master Data (admin HO) | Kecil | 1 | 1.0 | Setup permission code + assign ke role |
| Inspection & Additional Inspection: tambah field Area + Man Power di create finding | Kecil–Sedang | 2 | 2.0 | Component/Sub Component sudah ada, tinggal extend +2 field & cascading ke Area — 1 form yang sama berlaku untuk Inspection maupun Additional Inspection, tidak perlu effort terpisah |
| Additional Order: tambah field Component, Sub Component, Area, Duration, Man Power di create screen | Sedang | 3 | 2.9 | Field baru semua di layar ini (belum ada sebelumnya, layar terpisah dari Inspection) + cascading dropdown + validasi |
| Edit eMOL: carry-forward nilai dari Finding/Additional Order (auto-fill, tetap editable) | Kecil–Sedang | 2 | 2.0 | Passing value ke layar edit eMOL, bukan re-input |
| Order Approval: tambah validasi & edit Man Power, Duration, Component, Sub Component, Area | Sedang | 3 | 2.9 | UI baru di layar approval + reuse validasi yang sama (dropdown Master Data, Man Power integer >0) |
| `PoolingMOItem`/payload: tambah kolom Area, Duration, Man Power (Component/Sub Component sudah ada) | Sedang | 3 | 2.9 | Extend insert query (5.2) & payload (6.1) di [order-emol-sap-sync.md](order-emol-sap-sync.md) |
| Mapping BAPI: kirim Component, Sub Component, Area, Duration, Man Power ke SAP | **Belum bisa diestimasi** | — | — | Tergantung hasil assessment client dengan tim SAP mereka (2.5) — bisa kecil (numpang field text) atau besar/multi-sprint (custom Z-field, butuh kerja sisi SAP client di luar kontrol estimasi tim Digiman+) |
| MO Backlog inbound: parse balik Component, Sub Component, Area, Duration, Man Power dari SAP response | Sedang | 3 | 2.9 | Extend parsing/mapping saat pull MO Backlog |
| MO Backlog filter jadi konfigurasi per-client (bukan hardcode) | Sedang | 3 | 2.9 | Refactor filter Order Type/PM Activity Type jadi config per tenant |
| Testing end-to-end (Finding/Additional Order → eMOL → Approval → SAP → MO Backlog → Digiplan) | Besar | 8 | 7.8 | Banyak titik integrasi lintas service (`maintenance-execution`, `maintenance-order`, `dplan`), perlu test tiap checkpoint + regresi |
| **Total (di luar mapping BAPI)** | | **33** | **~32** | 1 angka pasti (bukan range) — hasil kalibrasi Fibonacci per baris |

*Catatan: estimasi berdasarkan deskripsi arsitektur dari pemilik produk, tanpa akses langsung ke source code — perlu divalidasi oleh engineer yang pegang codebase `maintenance-execution`/`maintenance-order`. Item Master Data UI dan mapping BAPI adalah 2 sumber ketidakpastian terbesar — keduanya bergantung pada jawaban open item yang belum final (lihat Bagian 4).*

---

## 4. Open Items / Belum Dibahas

- Assessment SAP integration (2.5) belum ada hasil — masih assignment ke Faiza.
- **Apakah mapping Area↔Component-SubComponent (2.2) ikut scoped per Asset Model** (mengikuti pola Component-SubComponent existing) **atau generik lintas Asset Model** — belum diklarifikasi. Menentukan apakah tabel mapping baru butuh 3 dimensi (Component, SubComponent, Area) atau 4 dimensi (+Asset Model).
- **Dependency urutan pengembangan**: karena Component/Sub Component/Area di Digiplan (2.4) diisi lewat dropdown dari Master Data mapping (2.2), Master Data UI itu perlu selesai/tersedia lebih dulu sebelum kolom Digiplan ini bisa dikembangkan penuh — urutan rilis/sprint perlu memperhitungkan dependency ini.
- Apakah Component/Sub Component/Area di level parent task punya rollup logic tersendiri (mengikuti pola Duration/Man Power) atau murni per-leaf tanpa agregasi ke parent? Belum dibahas.

---

## 5. Referensi
- [../dplan/digital-planning.md](../dplan/digital-planning.md)
- [../dplan/man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md)
- [order-emol-sap-sync.md](order-emol-sap-sync.md) — schema `MechanicOrderSummary`/`MechanicOrderList`, flow Order-eMOL → SAP sync, payload & mapping BAPI
