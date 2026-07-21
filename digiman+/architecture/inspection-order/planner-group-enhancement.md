# Enhancement: Planner Group pada Order Approval

*Last updated: 2026-07-21*

---

**Feature:** Order / Approval Order (Digiman+)
**Client:** MKP
**Related doc:** [order-emol-sap-sync.md](order-emol-sap-sync.md) *(Bagian 6.2 — mapping BAPI `GI_HEADER` existing, dasar analisa dokumen ini)*

---

## 1. Latar Belakang

Request berasal dari client **MKP**, dicatat di [MOM 01-Jul-2026](../../../MKP-Project/2026-07-01-meeting-notes.md) poin #34–35: saat create Maintenance Order (MO) ke SAP, ada field **Planner Group** yang perlu diisi. Saat ini **Digiman+ sama sekali tidak mengirim field ini** — dikonfirmasi dari review mapping BAPI `GI_HEADER` existing di [order-emol-sap-sync.md](order-emol-sap-sync.md#62-mapping-ke-bapi-sap-dilakukan-oleh-middleware) (`ORDER_TYPE`, `PLANT`, `EQUIPMENT`, `START_DATE`, `SHORT_TEXT`, `LONG_TEXT`, `ORDERID`, `PMACTTYPE`, `SYSTCOND` — Planner Group tidak ada di daftar ini).

### Konteks Teknis SAP (Referensi Umum)

- Planner Group di SAP PM adalah master data (tabel `T024I`), **di-scope per Maintenance Planning Plant** (site) — bukan kode global lintas plant.
- Secara standar, Planner Group **auto-derive dari Equipment** (yang biasanya inherit dari Functional Location) saat order dibuat. Field ini tetap **editable di order header** — override manual adalah behavior standar SAP, bukan workaround.
- **Dikonfirmasi user (21 Jul 2026):** di SAP BUMA ID, Planner Group memang auto-derive dari mapping Equipment, dan override manual aman dilakukan (tidak harus sama dengan hasil mapping).
- SAP **tidak punya validasi bawaan** yang mengaitkan Planner Group tertentu dengan pembatasan material/komponen. Kalau ada aturan seperti itu, itu di luar standar SAP (custom validation atau murni SOP).
- Planner Group di SAP juga lazim dipakai untuk **otorisasi** (authorization object `I_INGRP`) — assignment ke user lewat role (`PFCG`), bukan lewat field default di user master. Karena itu, "planner group milik user" secara SAP artinya "grup yang boleh dia kerjakan" (authorization), bukan identitas/default tunggal.

### Kebutuhan Bisnis MKP

- Planner Group **K01** adalah milik **dispatcher** — order dengan Planner Group ini **tidak boleh pakai material** (aturan bisnis MKP, lihat Bagian 2.2).
- Planner (user) bisa punya lebih dari satu Planner Group.

### Catatan Penting

Digiman+ adalah platform yang dipakai lintas client — **enhancement apapun di sini berdampak ke semua tenant**, bukan cuma MKP. Desain di bawah ini disusun supaya tenant yang tidak butuh fitur ini (mis. BUMA) tidak terdampak sama sekali.

---

## 2. Keputusan & Scope

Ada dua opsi yang akan dipresentasikan ke client sebagai pilihan (lihat catatan penting di 2.3 sebelum menganggap keduanya setara/interchangeable).

### 2.1 Opsi 1 — Auto-Derive dari Equipment (SAP/Interface Side)

- **Effort Digiman+: 0** — tidak ada perubahan apapun di Digiman+. Field Planner Group tetap tidak dikirim (behavior sekarang), dan SAP yang menentukan nilainya dari mapping Equipment.
- **Konsekuensi:** Planner Group order 100% mengikuti hasil mapping Equipment di SAP, terlepas dari siapa atau proses apa yang membuat order tersebut. Skenario planner dengan >1 Planner Group jadi tidak relevan — identitas/pilihan planner tidak pernah dipakai untuk menentukan nilai ini.
- **Open item — perlu dikonfirmasi tim SAP MKP:**
  1. Apakah semua Equipment sudah termap ke Planner Group (tidak ada Equipment yang belum termap)?
  2. Apakah kode **K01** termap ke Equipment tertentu, atau tidak ada mapping Equipment untuk itu sama sekali?

### 2.2 Opsi 2 — Input Eksplisit di Digiman+ (Approval Planner)

| Aspek | Keputusan |
|---|---|
| Titik input | Saat **approval oleh Planner** (bukan saat create eMOL/order) |
| Wajib/opsional | **Mandatory** — approval tidak bisa lanjut tanpa mengisi Planner Group |
| Visibility fitur | **Toggle on/off per tenant** — satu flag, berlaku sama untuk semua site di bawah tenant tsb (bukan per site) |
| Master data Planner Group | Entity baru, **di-scope per Site**, **maintain manual lewat UI Admin** — bukan sync API dari SAP (eksplisit di luar scope saat ini) |
| Filtering dropdown | Difilter berdasarkan **Site user yang sedang login**. Aman dipakai karena approval order saat ini sudah dibatasi **per site per section** — tidak ada skenario approval lintas-site (dikonfirmasi user 21 Jul 2026) |
| Filtering tambahan by planner | **Tidak ada** — dropdown menampilkan semua Planner Group untuk site tsb, tidak dibatasi ke grup yang jadi hak planner yang approve |
| Enforcement rule K01/material | **Tidak dibangun di Digiman+** — tetap ditangani lewat SOP manual, di luar scope sistem |
| Outbound ke SAP | Digiman+ publish field baru **`PlannerGroup`** di payload outbound (message bus). Mapping ke field BAPI SAP aktual (`GI_HEADER`) jadi tanggung jawab middleware — di luar scope dokumen ini, konsisten dengan pola field lain yang sudah publish-only di [order-emol-sap-sync.md](order-emol-sap-sync.md#62-mapping-ke-bapi-sap-dilakukan-oleh-middleware) |

### 2.3 Catatan: Dua Opsi Ini Tidak Serta-Merta Saling Menggantikan

Opsi 1 dan Opsi 2 berpotensi menjawab kebutuhan yang berbeda, tergantung jawaban open item 2.1:

- Kalau K01 **memang murni atribut Equipment** (equipment tertentu selalu default ke K01, apapun proses pembuatan order-nya), Opsi 1 sudah cukup — tidak perlu Opsi 2 sama sekali.
- Kalau K01 **terkait proses pembuatan order** (mis. khusus order dari jalur dispatcher/SEMAR unscheduled, bukan equipment-nya), Opsi 1 tidak akan bisa membedakan itu — order untuk equipment yang sama akan selalu dapat Planner Group yang sama, siapapun/proses apapun yang membuatnya. Opsi 2 diperlukan untuk kasus ini.

Keputusan final antara "pilih salah satu" vs "kombinasi keduanya" diserahkan ke client MKP setelah open item 2.1 terjawab.

---

## 3. Effort & Tim Eksekusi

**Di luar scope dokumen ini** — effort/mandays sengaja tidak dibahas di sini karena tim technical yang akan mengeksekusi (baik di sisi MKP maupun BTech) belum ditentukan (lihat [MOM 01-Jul-2026](../../../MKP-Project/2026-07-01-meeting-notes.md) poin #10). Kalau nanti bagian tertentu masuk scope BTech, effort-nya akan didokumentasikan terpisah, mengikuti pola dokumen effort summary lain di catalog ini.

---

## 4. Open Items

| # | Item | Terkait |
|---|---|---|
| 1 | Kelengkapan mapping Equipment → Planner Group di SAP MKP (apakah ada yang belum termap) | Opsi 1 |
| 2 | Status mapping Equipment untuk kode K01 (termap ke equipment tertentu atau tidak sama sekali) | Opsi 1, juga menentukan relevansi Opsi 2 (lihat 2.3) |

---

## 5. Referensi

- [order-emol-sap-sync.md](order-emol-sap-sync.md) — mapping BAPI `GI_HEADER` existing (Bagian 6.2), dasar analisa field yang sudah/belum dikirim ke SAP
- [MOM 2026-07-01](../../../MKP-Project/2026-07-01-meeting-notes.md) — poin #34–35 (asal request), poin #10 (status tim technical MKP)
