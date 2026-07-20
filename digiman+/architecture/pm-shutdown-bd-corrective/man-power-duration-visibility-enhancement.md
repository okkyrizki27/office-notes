# Enhancement: Visibility Duration/Man Power/Man Hours & Assignment Mechanic — PM Shutdown & BD Corrective

*Last updated: 2026-07-20*

---

**Feature:** PM Shutdown & BD Corrective (Digiman+)
**Related doc:** [../dplan/man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md), [../inspection-order/area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md)
**Effort summary lintas fitur:** [../area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md)

---

## 1. Latar Belakang

Hasil meeting dengan business (10 Jul 2026) terkait bagaimana kolom Duration/Man Power/Man Hours (dari Digiplan, lihat [man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md)) ditampilkan dan berinteraksi dengan proses assignment mechanic di eksekusi PM Shutdown & BD Corrective.

---

## 2. Keputusan yang Disepakati

### 2.1 Visibility di Card Task
- Duration, Man Power, **dan** Man Hours ketiga-tiganya ditampilkan di dalam card task PM Shutdown/BD Corrective — supaya pengawas (SPV) bisa langsung melihat visibility man power plan tanpa buka detail.

### 2.2 Assignment Mechanic Bebas Menyimpang dari Man Power Plan
- Assign-to tidak dibatasi harus persis sama dengan angka Man Power yang direncanakan — boleh lebih atau kurang.
- Kalau ada selisih antara jumlah mechanic yang di-assign vs Man Power plan, sistem **memberi warning**, dan user **wajib mengisi notes** alasan selisihnya sebelum lanjut.
- **✅ Level: leaf task (task tanpa child), bukan berdasarkan posisi struktural (diputuskan 20 Jul 2026)** — assignment mechanic, validasi selisih, dan `ManPowerVarianceReason` cuma berlaku di task yang **tidak punya child** (`DPTask` tanpa child lewat `ParentId`, lihat [digital-planning.md](../dplan/digital-planning.md)). Kriterianya murni **ada/tidaknya child**, bukan "level teratas vs level bawah" — task standalone di top-level yang tidak punya sub-task tetap leaf & executable, sebaliknya task yang punya child (di level manapun) bukan executable, statusnya roll-up otomatis dari children (sama seperti Duration = MAX dari children, lihat [man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md) 3.3). Konsisten dengan keputusan Component/Sub Component/Area yang juga leaf-only ([area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md) 2.4).
- **✅ Titik pengecekan selisih: saat Finish Execution, bukan real-time (diputuskan 20 Jul 2026)** — assignment mechanic boleh diubah-ubah bebas (tambah/kurang) tanpa warning apa pun di tengah proses. Pengecekan selisih vs Man Power plan baru dijalankan saat user coba **Finish Execution** — bukan live/recompute tiap kali assignment berubah. Lebih simpel secara implementasi (1 titik validasi di endpoint finish, bukan trigger reaktif di tiap aksi assign/unassign).
  - **⚠️ Klarifikasi penting (20 Jul 2026): "Finish Execution" itu aksi di level Plan/WorkOrder, bukan per-task** — 1 Plan bisa punya banyak leaf task/sub-task di bawahnya. Karena Man Power plan & assignment itu **per-leaf-task** (poin di atas), validasi saat Finish Execution **harus cek semua leaf task** di bawah Plan tersebut sekaligus, dan mewajibkan `ManPowerVarianceReason` untuk **setiap** leaf task yang punya gap — bukan 1 reason gabungan untuk seluruh Plan (secara data, tetap tersimpan per-task). Contoh: dari 5 task di 1 Plan, kalau 2 di antaranya gap, user diminta isi `ManPowerVarianceReason` untuk 2 task itu sebelum Finish Execution bisa lanjut.
  - **✅ UX: "Apply to All" sebagai opsi, bukan alur wajib (diputuskan 20 Jul 2026)** — di layar Finish Execution, user punya **2 cara isi yang setara, bebas dipilih**: (1) isi `ManPowerVarianceReason` **satu per satu** per task yang gap (kalau alasannya beda-beda tiap task), atau (2) isi **1 reason lalu "Apply to All"** ke semua task yang gap sekaligus (kalau alasannya sama, mis. "kekurangan mechanic karena 1 orang sakit"). Bukan "Apply to All duluan lalu override" — user bebas pilih jalur mana dari awal sesuai kebutuhan. Ini murni kemudahan input di UI; data yang tersimpan tetap 1 `ManPowerVarianceReason` per leaf task (bukan 1 field gabungan di level Plan), apapun cara isinya — tidak mengubah keputusan level data di atas.
- **✅ Lokasi penyimpanan notes: service `dplan`/`DPlanDB` (diputuskan 20 Jul 2026)** — bukan di database `maintenance-execution` sendiri, karena sekarang semua data execution PM Shutdown/BD Corrective mengambil/membungkus service `dplan` sebagai sumber datanya. Kemungkinan lewat mekanisme `DPColumn`/`DPValue` yang sama dengan Man Power/Man Hours (lihat [man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md)).
- **✅ Field terpisah, bukan reuse existing remark (diputuskan 20 Jul 2026)** — nama field **`ManPowerVarianceReason`**, spesifik untuk alasan selisih (variance) Man Power plan vs actual assignment, bukan field notes generik. Alasan: kalau reuse field remark yang general-purpose, validasi "wajib isi kalau ada selisih" jadi ambigu (tidak bisa dibedakan remark yang memang menjawab variance vs catatan lain yang kebetulan sudah terisi), dan reporting/audit trail jadi kotor. Field khusus lebih bersih & tidak menambah effort signifikan (kolom baru lewat `DPColumn` yang mekanismenya sudah dibangun untuk fitur ini).

### 2.3 Dua Skenario Mandatory-nya Assignment
Tergantung jenis eksekusi:
1. **Umum (non-backlog-with-MO)** — assignment mechanic boleh kosong; kalau kosong, sistem hanya kasih **warning untuk awareness**, tapi user tetap bisa Finish Execution meski assignment belum diisi.
2. **Backlog execution** (atau task yang punya MO reference) — assignment mechanic **mandatory**, minimal harus terisi 1 mechanic per leaf task, sebelum Finish Execution bisa dilakukan (konsisten dengan klarifikasi di 2.2: validasi jalan per-leaf-task, dicek semua sebelum Plan/WorkOrder bisa di-finish).

Alasan pembedaan: assignment ke mechanic di mobile app saat ini memang tidak selalu jadi langkah wajib secara umum, tapi untuk task yang terhubung ke MO (backlog execution) assignment perlu lebih ketat karena terhubung ke tracking actual effort di SAP.

---

*(Estimasi SP/mandays untuk dokumen ini dipisah ke [area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) — 20 Jul 2026, pola yang sama dengan [maintenance-activity-type-enhancement.md](../inspection-order/maintenance-activity-type-enhancement.md).)*

---

## 4. Open Items / Belum Dibahas

- ~~Detail teknis flag "selisih Man Power vs assignment" — apakah dihitung real-time saat assign, atau divalidasi saat finish task.~~ — **✅ resolved 20 Jul 2026**: divalidasi saat finish task (1 titik validasi gate), bukan real-time. Lihat 2.2.
- ~~UI/UX detail warning + notes (2.2) — apakah notes ini disimpan sebagai field terpisah atau masuk ke existing notes/remark task.~~ — **✅ resolved 20 Jul 2026**: field terpisah, `ManPowerVarianceReason`, disimpan di service `dplan`/`DPlanDB`. Lihat 2.2.
- ~~Impact ke Digiman Transaction Report — dibahas next phase~~ *(dicatat 16 Jul 2026)* — **✅ resolved 20 Jul 2026, jadi moot/not applicable**: dicek ke [README.md](../../report/transaction-report/README.md) Data Sources, tidak ada satupun dari 5 view Digiman Transaction Report yang query ke schema `dplan`. Data di dokumen ini (Duration/Man Power/Man Hours visibility, `ManPowerVarianceReason`) semuanya hidup di service `dplan`/`DPlanDB` (2.2) — tidak pernah masuk ke tabel yang jadi sumber report, jadi tidak ada dampak ke report sama sekali. Lihat [area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md) 2.7 untuk keputusan report-impact yang genuinely berlaku (Area/Man Power/Duration/Man Hours dari Inspection & Order, bukan dari Digiplan/PM Shutdown).

---

## 5. Referensi
- [../dplan/man-power-man-hours-excel-enhancement.md](../dplan/man-power-man-hours-excel-enhancement.md) — sumber Duration/Man Power/Man Hours (Digiplan)
- [../inspection-order/area-of-unit-man-power-enhancement.md](../inspection-order/area-of-unit-man-power-enhancement.md)
- [../area-of-unit-man-power-effort-summary.md](../area-of-unit-man-power-effort-summary.md) — estimasi SP/mandays untuk dokumen ini
