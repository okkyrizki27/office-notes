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
- **Scope rollout: tidak retroactive.** Perubahan ini **hanya berlaku untuk transaksi/plan yang dibuat setelah fitur ini dirilis** — template dan plan existing sebelum rilis **tidak perlu** ditambahkan Man Power/Man Hours secara retroactive, dan **tidak perlu backfill** data historis. Ini menyederhanakan scope migrasi — tidak ada baris "data migration/backfill" di estimasi effort (lihat [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md)).
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
- **Koreksi penting (10 Jul 2026):** konsep Sequence, Serial, Paralel **sudah punya model data sendiri** — tabel `DPPredecessor` (`FromTask`, `ToTask`, `Type`, `Lag`, lihat [digital-planning.md](digital-planning.md)) sudah ada saat ini, bukan konsep baru yang perlu dibangun. Jadi assessment yang tersisa **bukan riset "bagaimana menangkap struktur predecessor"**, melainkan **finalisasi formula perhitungan** — bagaimana `Type` (FS/SS/FF/SF atau setara) dan `Lag` diterjemahkan jadi rumus rollup Man Power/Man Hours (mis. jalur serial dijumlahkan, cabang paralel diambil yang terbesar, dst). Ini menurunkan estimasi effort "Dengan logic penuh" secara signifikan dibanding perkiraan sebelumnya — lihat perbandingan skenario "Dengan" vs "Tanpa" di [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md).
- **Trigger recalculate otomatis** — confirmed: setiap kali ada perubahan struktur task yang memengaruhi rollup parent (tambah child baru, hapus child, atau re-parenting/pindah parent), sistem harus **otomatis** memicu recalculate nilai turunan (Duration MAX, dan Man Power/Man Hours sesuai formula yang nanti diputuskan) di parent terkait — tidak menunggu aksi eksplisit lain dari user.

---

*(Estimasi SP/mandays untuk dokumen ini dipisah ke [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) — 20 Jul 2026, pola yang sama dengan [maintenance-activity-type-enhancement.md](../inspection-order/maintenance-activity-type-enhancement.md).)*

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
- [../area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) — estimasi SP/mandays/sprint untuk dokumen ini
