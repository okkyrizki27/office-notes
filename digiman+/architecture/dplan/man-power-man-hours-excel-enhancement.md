# Enhancement: Man Power & Man Hours di Excel Template Upload Daily Plan

*Last updated: 2026-07-10*

---

**Service:** `dplan`
**SQL DB:** `DPlanDB`
**Related doc:** [digital-planning.md](digital-planning.md)
**Effort summary lintas fitur:** [../area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md)

---

## 1. Latar Belakang

Kolom **Man Power** (jumlah orang) dan **Man Hours** (hasil kalkulasi `Duration × Man Power`) sudah ada di UI dan database Daily Plan, tetapi **belum bisa diisi lewat template Excel** — proses download/upload template Excel saat ini hardcode ke kolom fixed saja dan belum pernah mengakomodasi dynamic column dari mekanisme `DPColumn`/`DPValue`.

Dokumen ini merangkum hasil assessment effort untuk mengakomodasi kedua kolom ini di alur Excel template upload/download.

> **Scope terkait**: Excel template juga perlu mengakomodir kolom **Component**, **Sub Component**, **Area** (dari enhancement [area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md)) — bukan cuma Man Power/Man Hours yang dibahas di dokumen ini. Masalah teknis dasarnya sama (kolom dinamis lewat `DPColumn`/`DPValue` belum terakomodasi di Excel), tapi Component/Sub Component/Area punya kompleksitas tambahan karena cara pengisiannya dropdown dari Master Data (bukan input bebas seperti Man Power) — representasi dropdown/master-data-lookup ini di Excel belum didesain, lihat open item di dokumen tersebut.

---

## 2. Arsitektur & Mekanisme Existing

Sudah didokumentasikan lengkap di **[digital-planning.md](digital-planning.md)**: schema `DigitalPlanning`/`DPTask`/`DPColumn`/`DPValue`, relasi antar tabel, mekanisme pembuatan Daily Plan (8 langkah), serta precedent business-logic khusus per kolom (Duration rollup parent-child). Dokumen ini hanya merujuk ke sana — tidak diduplikasi di sini.

**Ringkasan poin yang paling relevan untuk enhancement ini:**
- Excel template upload/download **saat ini hardcode ke kolom fixed saja** — belum pernah mengakomodasi kolom dinamis dari `DPColumn`/`DPValue` (lihat langkah 7–8 mekanisme pembuatan plan).
- `DPColumn` di-snapshot per plan saat dibuat, bukan live dari Template — relevan untuk backward compatibility.
- Duration sudah punya precedent logic khusus (rollup parent-child) — jadi precedent bagi desain Man Hours di bagian berikut.

---

## 3. Desain yang Disepakati

### 3.1 Man Power
- **Mandatory dan tidak dapat di-disable** di setiap Template — beda perlakuan dari kolom custom biasa (Duration/Start/Finish/dst yang masih bisa di-toggle/dihapus lewat Config → Custom Column). Man Power **selalu ada** di semua Template.
  - *(Revisi dari keputusan sebelumnya yang menyamakan Man Power dengan kolom custom biasa — direvisi karena Man Hours butuh Man Power selalu tersedia agar kalkulasinya valid, lihat 3.2.)*
- Tetap tersimpan di `DPValue` lewat mekanisme dynamic column yang sama (EAV), hanya toggle "bisa didisable"-nya yang berbeda.
- **Efek ke Template Config UI**: perlu guardrail baru — tombol *Is Shown* toggle dan *Action* (delete) untuk baris Man Power & Man Hours di layar Config → Custom Column harus dinonaktifkan/disembunyikan khusus untuk 2 kolom ini.
- **Posisi/urutan kolom (`Sequence`)**: mengikuti mekanisme normal — bisa diatur bebas oleh admin di Config → Custom Column, sama seperti kolom lain. Tidak ada aturan posisi fixed khusus untuk Man Power/Man Hours.
- **Scope rollout: tidak retroactive.** Perubahan ini **hanya berlaku untuk transaksi/plan yang dibuat setelah fitur ini dirilis** — template dan plan existing sebelum rilis **tidak perlu** ditambahkan Man Power/Man Hours secara retroactive, dan **tidak perlu backfill** data historis. Ini menyederhanakan scope migrasi (lihat Bagian 4).
- **Wajib diisi, harus lebih dari 0, dan integer.** *(Hasil meeting dengan business, 10 Jul 2026)* — konfirmasi dari business untuk 3 pertanyaan yang sebelumnya open:
  - Man Power tidak boleh kosong/null — mandatory.
  - Man Power tidak boleh `0` — harus lebih besar dari 0.
  - Man Power harus bilangan bulat (integer) — tidak boleh desimal.
  - *(Menggantikan open question sebelumnya soal default value, zero-allowed, dan decimal-allowed — lihat perubahan Bagian 5.)*

### 3.2 Man Hours
- Sama seperti Man Power: **mandatory dan tidak dapat di-disable** di setiap Template — supaya kombinasi Man Hours tanpa Man Power (atau tanpa Duration) tidak pernah terjadi.
- **Tidak editable** — baik di grid maupun Excel, Man Hours **read-only** untuk user. Nilainya murni hasil kalkulasi `Duration × Man Power`, dihitung dan disimpan (upsert ke `DPValue`) oleh backend.
  - **Efek ke grid UI**: cell Man Hours perlu di-disable dari edit langsung (beda perlakuan dari kolom dinamis lain yang semuanya editable oleh user) — perlu flag khusus di level UI/`DPColumn` untuk menandai kolom ini non-editable.
  - **Efek ke Excel**: kolom Man Hours tetap **ditampilkan** di template (sebagai informasi), tapi nilai yang diisi user di cell tersebut **diabaikan secara silent saat upload** (tidak dianggap error/tidak menolak baris) — sistem tetap lanjut memproses baris tersebut dan otomatis overwrite dengan hasil kalkulasi ulang, tidak menerima nilai dari file.
  - Alasan: kalau diterima sebagai input mentah, ada risiko integritas data — nilai yang diupload/diketik user bisa tidak match `Duration × Man Power`, dan sistem harus menambah validasi ekstra untuk menangkap ketidaksesuaian itu. Read-only menghilangkan risiko ini sepenuhnya.
- **Keputusan desain:** logic kalkulasi ini dibuat sebagai **special-case khusus untuk kolom Man Hours** (bukan generic formula engine) — konsisten dengan pendekatan Duration yang juga sudah punya logic khusus (rollup parent-child). Tidak perlu investasi ke arah formula engine generic karena belum ada kebutuhan kolom kalkulasi lain selain ini.
- **Titik pemicu recalculate** — harus konsisten di **dua entry point**:
  1. Grid: saat user edit Duration atau Man Power langsung di grid
  2. Excel upload: saat Duration atau Man Power ter-update lewat import
  - Rekomendasi teknis: kalkulasi ini dibuat sebagai **1 shared service/function** (misal `RecalculateManHours(taskId)`) yang dipanggil dari kedua jalur di atas, supaya tidak ada 2 implementasi kalkulasi yang bisa divergen.
- **⚠️ Risiko urutan trigger (dependency antar-rollup)** — Duration di parent task punya rollup sendiri (`MAX` dari children, lihat 3.3). Man Hours butuh nilai Duration yang **sudah final** untuk dihitung. Kalau Duration salah satu child berubah, urutan proses **harus**: (1) rollup Duration parent selesai dulu → (2) baru recalculate Man Hours parent dijalankan, memakai Duration parent yang sudah ter-update. Kalau kedua proses ini jalan independen/tidak berurutan, ada risiko Man Hours parent kehitung memakai Duration lama (stale). Ini perlu jadi perhatian eksplisit saat desain teknis, bukan asumsi otomatis konsisten.
- **Satuan & presisi** — Duration bersatuan **jam (Hours)**, dibulatkan ke **1 angka desimal** (`decimal(18,1)`) — jadi hasil kalkulasi `Duration × Man Power` secara literal memang merepresentasikan Man-Hours (jam-orang), tidak perlu konversi satuan tambahan. Presisi/pembulatan hasil Man Hours sendiri (berapa angka desimal) masih tergantung jawaban open question soal tipe data Man Power (integer vs desimal) — lihat Bagian 5.

### 3.3 Hierarki (Parent-Child)
- Duration di level parent = **MAX** (nilai terbesar) dari Duration semua children — pola existing (bukan sum/total; kemungkinan merefleksikan child task yang berjalan paralel, jadi durasi parent mengikuti child yang paling lama).
- Karena Duration parent bukan angka independen (hasil turunan dari children), logic Man Power dan Man Hours di level parent **belum bisa diasumsikan mengikuti pola yang sama** (baik itu disamakan dengan Duration, atau pola lain seperti sum, atau tidak relevan sama sekali di level parent).
- **Arahan business (meeting 10 Jul 2026):** perhitungan Man Power di level parent perlu di-**assess** dengan mempertimbangkan kondisi **predecessor, serial, dan paralel** antar child task (logic-nya kemungkinan berbeda tergantung apakah child berjalan berurutan atau bersamaan) — **atau, untuk sementara, dikosongkan dulu** (parent tidak punya nilai Man Power sendiri) sambil assessment berjalan. Ini **masih belum final** — assessment predecessor/serial/paralel ini jadi item lanjutan, belum keputusan akhir. Lihat Bagian 5.
- **Koreksi penting (10 Jul 2026):** konsep Sequence, Serial, Paralel **sudah punya model data sendiri** — tabel `DPPredecessor` (`FromTask`, `ToTask`, `Type`, `Lag`, lihat [digital-planning.md](digital-planning.md)) sudah ada saat ini, bukan konsep baru yang perlu dibangun. Jadi assessment yang tersisa **bukan riset "bagaimana menangkap struktur predecessor"**, melainkan **finalisasi formula perhitungan** — bagaimana `Type` (FS/SS/FF/SF atau setara) dan `Lag` diterjemahkan jadi rumus rollup Man Power/Man Hours (mis. jalur serial dijumlahkan, cabang paralel diambil yang terbesar, dst). Ini menurunkan estimasi effort "Dengan logic penuh" secara signifikan dibanding perkiraan sebelumnya — lihat revisi di 4.0.1.
- **Trigger recalculate otomatis** — confirmed: setiap kali ada perubahan struktur task yang memengaruhi rollup parent (tambah child baru, hapus child, atau re-parenting/pindah parent), sistem harus **otomatis** memicu recalculate nilai turunan (Duration MAX, dan Man Power/Man Hours sesuai formula yang nanti diputuskan) di parent terkait — tidak menunggu aksi eksplisit lain dari user.

---

## 4. Scope Perubahan & Estimasi Effort

*(SP dikalibrasi ke skala Fibonacci `[1,2,3,5,8]` — konvensi tim BUMA ID, lihat metodologi kalibrasi di [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md). Mandays dihitung dari rasio throughput ~0.98 mandays/SP — basis 5 sprint terakhir, konsisten dengan basis velocity yang dipakai untuk estimasi jumlah sprint.)*

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| Template Config UI: guardrail Man Power & Man Hours tidak bisa di-disable/dihapus | Kecil–Sedang | 2 | 2.0 | Nonaktifkan toggle *Is Shown* & tombol delete khusus 2 baris ini di layar Config → Custom Column |
| Grid UI: cell Man Hours read-only (tidak bisa diedit langsung) | Kecil–Sedang | 2 | 2.0 | Beda perlakuan dari kolom dinamis lain yang semuanya editable; perlu flag khusus di level UI/`DPColumn` |
| Grid: edit Duration/Man Power → trigger recalculate & save Man Hours | Sedang | 3 | 2.9 | Titik sentuh baru di endpoint save/update task grid |
| Excel export: tampilkan Man Power & Man Hours | Kecil–Sedang | 2 | 2.0 | Karena mandatory di semua template baru (dan tidak retroactive), resolve `ColumnId` konsisten selalu ada untuk plan baru — plan lama tetap pakai template lama tanpa kolom ini |
| Excel import: parse & validasi Man Power, upsert ke `DPValue` | Sedang | 3 | 2.9 | Validasi tipe/`IsMandatory` dari metadata `DPColumn` |
| Excel import: hitung & upsert Man Hours setelah Man Power tersimpan | Sedang | 3 | 2.9 | Reuse shared service yang sama dengan grid-save |
| Auto-recalculate saat struktur task berubah (add/delete child, re-parenting) | Sedang | 3 | 2.9 | Trigger rollup parent (Duration/Man Power/Man Hours) otomatis; **urutan proses harus dijaga** — rollup Duration parent selesai dulu, baru Man Hours parent dihitung ulang (lihat 3.2) |
| Testing Man Power/Man Hours (grid edit, excel upload, kombinasi ada/tidaknya kolom, hierarki parent-child, bulk) | Sedang–Besar | 5 | 4.9 | Dua entry point (grid + excel) harus konsisten hasil kalkulasinya |
| **Subtotal Man Power/Man Hours (baseline)** | | **23** | **~23** | ⚠️ Lebih tinggi dari estimasi top-down sebelumnya (8–13 SP) — penjumlahan Fibonacci per baris (bottom-up) cenderung menghasilkan total lebih besar dibanding estimasi top-down holistik; lihat catatan metodologi di [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) |

### 4.0.1 Perbandingan Effort: Rollup Man Power/Man Hours di Level Parent — "Dengan" vs "Tanpa" Predecessor/Serial/Paralel

*(Permintaan client: estimasi effort untuk 2 skenario — logic predecessor/serial/paralel diimplementasikan penuh, vs parent dikosongkan dulu.)*

> **Revisi 10 Jul 2026**: estimasi di bawah diturunkan signifikan dari perkiraan awal, setelah dikonfirmasi bahwa tabel `DPPredecessor` (`FromTask`, `ToTask`, `Type`, `Lag`) **sudah ada** dan memodelkan konsep Sequence/Serial/Paralel dengan baik (lihat [digital-planning.md](digital-planning.md)). Risiko terbesar sebelumnya (harus membangun/menangkap struktur predecessor dari nol) **tidak berlaku** — yang tersisa murni soal formula & implementasi traversal-nya.

| Skenario | SP | Mandays | Penjelasan |
|---|---|---|---|
| **Tanpa** — parent dikosongkan dulu (opsi interim) | **1** | **1.0** | Ini **sudah jadi asumsi baseline** di subtotal Bagian 4 di atas — jadi effort tambahannya minimal, cuma perlu pastikan UI grid & Excel menampilkan kosong/dash (bukan error atau `0`) di baris parent untuk Man Power & Man Hours, dan Man Hours parent otomatis ikut kosong (karena butuh Man Power). Tidak butuh assessment lanjutan untuk opsi ini. |
| **Dengan** — logic penuh predecessor/serial/paralel (menggunakan `DPPredecessor` existing) | **8** (di luar 3 SP assessment/finalisasi formula yang sudah dihitung terpisah) | **7.8** (di luar ~2.9 mandays assessment) | Effort utamanya: (1) traversal graph `DPPredecessor` (`FromTask`→`ToTask` per `Type`/`Lag`) untuk tentukan jalur serial vs cabang paralel per parent task; (2) implementasi formula rollup (mis. serial dijumlahkan, paralel diambil terbesar — final ditentukan saat assessment); (3) integrasi ke shared service `RecalculateManHours`/rollup existing; (4) edge case (predecessor tidak lengkap, referensi melingkar); (5) testing. Lebih kecil dari estimasi awal karena data model dependency-nya **sudah ada**, bukan perlu dibangun. |

**Rekomendasi ke client**: opsi "Tanpa" (interim) hampir tidak menambah cost dan bisa dirilis bersamaan dengan Man Power/Man Hours utama; opsi "Dengan" logic penuh sekarang **jauh lebih terjangkau** dari perkiraan sebelumnya (karena `DPPredecessor` sudah ada) — bisa dipertimbangkan untuk masuk rilis pertama sekalian, tidak harus ditunda ke fase terpisah, tergantung urgensi bisnisnya.

**+ 3 SP (~2.9 mandays) untuk assessment/finalisasi formula predecessor/serial/paralel** (menentukan rumus rollup berdasarkan `Type`/`Lag` di `DPPredecessor`, terlepas dari opsi mana yang akhirnya dipilih untuk rilis pertama).

### 4.1 Tambahan: Component, Sub Component, Area *(10 Jul 2026)*

| Komponen | Kompleksitas | SP | Mandays | Catatan |
|---|---|---|---|---|
| `DPColumn`: tambah 3 kolom baru (Component, Sub Component, Area) sebagai custom column | Kecil | 1 | 1.0 | Tidak mandatory/non-disable seperti Man Power/Man Hours — custom column biasa, lebih simpel |
| Grid UI: 3 dropdown baru dengan cascading Component→Sub Component→Area dari Master Data | Sedang | 3 | 2.9 | Butuh komponen cascading-dropdown baru, fetch dari API Master Data ([area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md) 2.2) |
| Auto-fill saat user pilih MO Backlog: isi Component/Sub Component/Area/Duration/Man Power | Sedang | 3 | 2.9 | Termasuk graceful handling kalau kolom tidak ada di Plan (skip field yang tidak ada `DPColumn`-nya, lihat 3.4 area-of-unit doc) |
| Excel export: tampilkan 3 kolom baru | Kecil | 1 | 1.0 | Kolom text biasa (bukan dropdown Excel), sama pola dengan Man Power |
| Excel import: parse & validasi kombinasi terhadap Master Data (reject + warning kalau tidak match) | Sedang | 3 | 2.9 | Beda dari Man Hours (silent-overwrite) — di sini baris ditolak dengan warning jelas |
| Testing Component/Sub Component/Area (grid, excel, MO Backlog auto-fill, graceful-handling kolom hilang) | Sedang | 3 | 2.9 | |
| **Subtotal Component/Sub Component/Area** | | **14** | **~14** | |

### 4.2 Total Bagian 4

*(SP: 1 angka pasti hasil kalibrasi Fibonacci per baris, bukan range. Mandays dihitung dengan rasio ~0.98 mandays/SP — basis 5 sprint terakhir tim BUMA ID, konsisten dengan basis velocity sprint, lihat [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md).)*

| Skenario Rilis | Total (SP) | Total (Mandays) |
|---|---|---|
| **Tanpa** logic penuh (parent dikosongkan dulu) — Man Power/Man Hours baseline (23) + assessment (3) + Component/Sub Component/Area (14) | **40 SP** | **~39 mandays** |
| **Dengan** logic penuh predecessor/serial/paralel (pakai `DPPredecessor` existing) — baseline (23) + assessment (3) + implementasi penuh (8) + Component/Sub Component/Area (14) | **48 SP** | **~47 mandays** |

**Selisih "Dengan" vs "Tanpa": 8 SP (~5 mandays) tambahan** kalau business memilih implementasi logic predecessor/serial/paralel penuh sejak rilis pertama, dibanding opsi interim (parent kosong). Selisih ini jauh lebih kecil dari perkiraan awal karena data model dependency (`DPPredecessor`) **sudah ada**, bukan perlu dibangun dari nol.

*(Titik tengah = midpoint dari range, dipakai sebagai 1 angka representatif untuk komunikasi ke client — bukan skenario optimis. Lihat [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) untuk konteks lengkap.)*

*Catatan: estimasi berdasarkan deskripsi arsitektur dari pemilik produk, tanpa akses langsung ke source code — perlu divalidasi oleh engineer yang pegang codebase `dplan`, terutama soal performa batch-upsert `DPValue` untuk plan dengan jumlah task besar.*

---

## 5. Open Questions (Perlu Dibahas dengan Business)

> Update 10 Jul 2026: 3 dari 4 open question sebelumnya (default value, zero-allowed, decimal-allowed untuk Man Power) sudah **resolved** lewat meeting dengan business — lihat Bagian 3.1 ("Wajib diisi, harus lebih dari 0, dan integer"). Item PM Shutdown & BD Corrective juga sudah resolved — lihat [man-power-duration-visibility-enhancement.md](../pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md); Order Approval resolved — lihat [area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md) 2.6. Sisa 1 item masih open, statusnya berubah dari "open question" murni menjadi "assessment in-progress" (arah sudah diberi business, detail teknisnya belum final):

- **Logic Man Power & Man Hours di level parent task** — business sudah memberi arahan (bukan lagi murni open question tanpa arah): perhitungan perlu **di-assess** dengan mempertimbangkan kondisi **predecessor, serial, dan paralel** antar child task, **atau untuk sementara dikosongkan dulu** (parent tidak punya nilai sendiri) sambil assessment berjalan. Yang masih perlu di-follow-up sebelum desain final/development:
  - Assessment teknis: bagaimana sistem membedakan child yang predecessor/serial vs paralel untuk keperluan rollup Man Power (apakah dari data `Predecessor` yang sudah ada di `DPTask`/kolom terkait, atau perlu data tambahan)?
  - Kalau assessment belum selesai saat development harus mulai, apakah opsi "dikosongkan dulu" (parent tanpa nilai Man Power/Man Hours) diambil sebagai interim solution untuk rilis pertama, dengan rencana revisit setelah assessment predecessor/serial/paralel selesai?

---

## 6. Referensi
- [digital-planning.md](digital-planning.md) — schema `DigitalPlanning`, `DPTask`, `DPColumn`, `DPValue`, mekanisme pembuatan Daily Plan, precedent business-logic Duration rollup
- [../inspection-order/area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md) — Order Approval (validasi Man Power & Duration oleh SPV), Area of Unit, dan enhancement Inspection/Order lain yang terkait
- [../pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md](../pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md) — visibility Duration/Man Power/Man Hours di card task & assignment mechanic di PM Shutdown/BD Corrective
