# Meeting Notes — MKP - Digiman+ Order, Material & Approval Workflow

**Date:** 01 July 2026
**Topic:** MKP - Digiman+ Backlog Execution, Order/Material Flow, dan Approval Workflow

---

## Attendees

**MKP:**
- Rina
- Melina
- Daniel

**BTECH:**
- Alimudin
- Faisal
- Okky
- Hamsya
- Robert

## Agenda

1. Flow chart eksekusi backlog (Order, Inspection, Material)
2. Work Order / Operation structure & sinkronisasi dengan SAP
3. Alur material: reservasi, good issue, dan return
4. Interface SAP untuk create Order & Notification
5. Approval / planner workflow
6. Sinkronisasi master data (damage/cause/action remedy, employee)
7. Testing phase & roadmap

## Discussion

### 1. Backlog Execution & Flow Chart

- Flow chart eksekusi backlog harus menggambarkan detail proses action yang dilakukan, bukan hanya high-level. _(#1)_
- Inspeksi tanpa temuan tetap harus digambarkan di flow. _(#7)_
- "Executable now" — finding yang tidak membentuk order — harus tergambar di flowchart. _(#20)_
- Perlu ditambahkan alur di Order yang berasal dari Inspection, dan sebaliknya sub-process Order ditambahkan di sisi Inspection. _(#19)_
- Setelah planner create WO di SAP dan review WO tersebut, langkah berikutnya (inspection & eksekusi) harus tergambar jelas di flow. _(#36)_
- Data backlog yang masuk ke Digiman+ mencakup **all backlog**, termasuk WO yang bukan di-create oleh Digiman+. Cut-off data backlog akan direview sebelum go live. _(#9)_

### 2. Work Order / Operation Structure

- Prinsip **1 WO = 1 Operation**, mengikuti WO activity type — berlaku baik untuk backlog yang tergenerate dari Digiman+ maupun yang dibuat manual oleh user. _(#2)_
- System Condition dari sisi Digiman+ **selalu 0**. Jika di SAP ada Teco MO dengan system condition bukan 0, itu tidak masalah (tidak perlu di-handle khusus). _(#17)_
- Case Equipment dengan status **INST** dan **INACT** masuk ke skenario testing yang wajib dilakukan pada testing phase. _(#18)_
- **Open item:** Teco dan NOCO perlu dibahas lebih lanjut di sesi berikutnya. _(#39)_

### 3. Alur Material (Reservasi, Good Issue, Return)

- Jika butuh material, mechanic wajib ambil material **sebelum** inspeksi, dengan melakukan good issue di SAP (warehouse) terlebih dahulu, membawa reservasi yang sudah di-print oleh planner. _(#4)_
- Return material **hanya berlaku** untuk material yang sudah melalui proses good issue. _(#5)_
- Contoh perhitungan: MO mat A = 10, reservasi mat A = 7, good issue mat A = 7. Jika yang terpasang hanya 5, maka perlu return material sebanyak 2 — ditambahkan sebagai line operation return baru di WO SAP. _(#6)_
- Jika ada material return, planner create line operation return baru. Interface SAP harus bisa mendeteksi status WO (sudah confirmation atau belum) dan membaca line operation-nya — jika WO belum confirmation, sistem harus feedback failed ke Digiman+. _(#3)_
- Perlu enhancement untuk handle **material group** (contoh: HD785, Common for All Komatsu, Consumable) — perlu dicek lebih lanjut. _(#14)_
- Perlu enhancement search material berdasarkan Material Group atau part number. _(#15)_
- Integrasi data material dengan Digiman+ diharapkan **near real time**. _(#12)_

### 4. Material Belum Teregister di SAP

- Skenario new material number yang belum terdaftar di SAP: perlu enhancement agar mechanic bisa menambahkan part number yang belum register, atau sementara pakai workaround **Double MAR** (input di Digiman+ dan manual di form kertas). _(#26)_
- Registrasi material number tetap dilakukan di SAP. Digiman+ hanya mengizinkan user input material yang belum teregister; approval planner adalah titik di mana planner baru melakukan registrasi ke SAP. _(#37)_
- Expected behavior: untuk material yang belum teregister, approval **berhenti di Planner** — planner harus register material tersebut ke SAP terlebih dahulu, data baru sync ke Digiman+, kemudian material tersebut diedit di order. _(#28)_
- Flow Order perlu digambarkan dalam **2 varian**: with material dan without material, masing-masing juga dipecah lagi dengan/tanpa enhancement terkait material yang belum teregister. _(#27, #32)_

### 5. Interface SAP: Create Order & Notification

- Enhancement: pengiriman data create order harus disertai juga pengiriman data untuk create notification. _(#29)_
- Interface SAP memastikan create order dengan material menghasilkan **user status P002 / system status REL**, dan tanpa material menghasilkan **user status P01 / system status REL**. _(#30)_
- Notification status = **NOPR**, **ORAS**. _(#31)_
- Notification fields akan dikirimkan oleh tim SAP. _(#33)_
- Jika enhancement create notification dijalankan, sistem perlu meng-grab notification number dari message response. _(#38)_

### 6. Approval & Planner Workflow

- Approve order boleh melakukan edit — hal ini perlu dimasukkan ke flow chart. _(#21)_
- **Open question:** apakah validasi double order bisa dilakukan tanpa perlu dipindah dulu sebelum submit? _(#22)_
- Approval order terdiri dari **4 layer**: Foreman → Supervisor → Planner → Superintendent. Perlu perubahan configuration workflow untuk mengakomodasi ini. _(#24)_
- Validasi double order tetap dibutuhkan untuk sementara waktu, sampai workflow improvement (approve, revise, reject) selesai dikembangkan. _(#25)_
- Planner Group **K01** adalah milik dispatcher — order dengan planner group ini tidak boleh menggunakan material. _(#34)_
- Planner group ditentukan berdasarkan user, namun ada user yang memiliki lebih dari satu planner group. Dua opsi dipertimbangkan: mapping di level user, atau di section of equipment. Digiman+ perlu enhancement di layar approval agar planner bisa memilih planner group jika dia punya lebih dari satu. _(#35)_
- Workflow enhancement (approval 4 layer, revise/reject, dsb.) ditargetkan selesai **end of this year (2026)**. _(#23)_

### 7. Master Data Sync

- Damage Code, Cause Code, dan Action Remedy akan dikirim oleh tim SAP — perlu proses sinkronisasi dengan data Digiman+. _(#8)_
- Data Employee bersumber dari **HRIS SEMAR**. _(#13)_

### 8. Testing Phase

- Testing phase diharapkan dilakukan **on-site**. _(#11)_
- Case Equipment INST/INACT wajib masuk skenario testing (lihat juga bagian 2). _(#18)_

### 9. Roadmap / Future Development

- Diharapkan order type selain backlog bisa dihandle oleh Digiman+, dan operational bisa lebih dari satu — dicatat sebagai **very future development**, bukan scope saat ini. _(#16)_

## Decisions

- 1 WO = 1 Operation, mengikuti WO activity type, berlaku untuk backlog dari Digiman+ maupun manual. _(#2)_
- Return material hanya berlaku untuk material yang sudah di-good issue. _(#5)_
- Mechanic wajib good issue material (bawa reservasi print planner) sebelum inspeksi. _(#4)_
- System Condition dari Digiman+ selalu 0. _(#17)_
- Data backlog yang masuk Digiman+ = all backlog termasuk WO non-Digiman+; cut-off direview sebelum go live. _(#9)_
- Approval order 4 layer: Foreman, Supervisor, Planner, Superintendent. _(#24)_
- Double order validation tetap dipertahankan sampai workflow enhancement selesai. _(#25)_
- Planner Group K01 (dispatcher) tidak boleh pakai material. _(#34)_
- Interface SAP: create with material → user status P002/system status REL; without material → user status P01/system status REL. _(#30)_
- Notification status = NOPR, ORAS. _(#31)_
- Registrasi material number tetap di SAP; Digiman+ hanya input material belum-register sampai titik approval planner. _(#37)_
- Employee data bersumber dari HRIS SEMAR. _(#13)_
- Workflow enhancement (approval, revise/reject) ditargetkan selesai end of 2026. _(#23)_
- Order type selain backlog + operational lebih dari satu dicatat sebagai very future development, bukan scope saat ini. _(#16)_

## Open Items (perlu dibahas lebih lanjut)

| # | Item | Catatan |
|---|------|---------|
| 1 | Tim technical MKP (SAP maupun middleware) | Akan diputuskan segera _(#10)_ |
| 2 | Validasi double order — bisa tidak dipindah sebelum submit? | Pertanyaan terbuka _(#22)_ |
| 3 | Planner group mapping — di level user atau section of equipment? | Opsi masih dibahas _(#35)_ |
| 4 | Teco dan NOCO | Perlu dibahas lagi di sesi berikutnya _(#39)_ |

## Action Items

| # | Task | PIC | Due Date |
|---|------|-----|----------|
| 1 | Flow chart eksekusi backlog: detail action, inspeksi tanpa temuan, executable-now tanpa order, sub-process Order↔Inspection, next step setelah planner review WO di SAP | TBD | TBD |
| 2 | Enhancement handle material group (HD785, Common for All Komatsu, Consumable) | TBD | TBD |
| 3 | Enhancement search material by Material Group / part number | TBD | TBD |
| 4 | Enhancement material unregistered di SAP (mechanic tambah part number / workaround Double MAR) + approval stop di Planner untuk registrasi | TBD | TBD |
| 5 | Flow Order 2 varian (with/without material) x (with/without enhancement unregistered material) | TBD | TBD |
| 6 | Enhancement create notification bersamaan dengan create order (termasuk grab notification number) | TBD | TBD |
| 7 | Update configuration workflow approval 4 layer + pilihan planner group jika user punya lebih dari satu | TBD | TBD |
| 8 | Integrasi data material near real time dengan Digiman+ | TBD | TBD |
| 9 | Tentukan tim technical MKP (SAP & middleware) | MKP | Segera |
| 10 | Bahas ulang Teco & NOCO | TBD | TBD |
| 11 | Siapkan testing phase on-site, termasuk skenario wajib Case Equipment INST/INACT | TBD | TBD |

## Notes

- Dokumen ini menyusun ulang 39 poin catatan mentah menjadi kelompok tematik untuk memudahkan pelacakan; nomor asli dicantumkan dalam tanda kurung `(#n)` di setiap poin untuk cross-check.
- Attendees, PIC, dan due date pada Action Items belum terisi — mohon dilengkapi.

