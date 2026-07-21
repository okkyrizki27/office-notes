# Meeting Notes — MKP - Digiman+ SEMAR Integration (Ticket, Down Code, Unscheduled/Scheduled Flow)

**Date:** 08 July 2026
**Topic:** MKP - Digiman+ Integration dengan SEMAR (Ticket Lifecycle, Down Code, Job Codes, Unscheduled & Scheduled Service Flow)
**With:** SEMAR

---

## Attendees

**MKP:**
- Rina
- Melina
- Daniel
- Tim SEMAR (HO)
- Tim SEMAR (Site)

**BTECH:**
- Alimudin
- Faisal
- Okky
- Indro

## Agenda

1. Ticket lifecycle & ownership di SEMAR
2. Down Code & Job Codes
3. Sinkronisasi master data SEMAR ↔ SAP ↔ Digiman+
4. Notification & MO timing
5. Flow Unscheduled Service (SEMAR → Digiman+ → SAP)
6. Flow Scheduled Service
7. TECO & Order Type

## Discussion

### 1. Ticket Lifecycle & Ownership (SEMAR)

- Dispatcher membuat ticket di SEMAR dari open sampai close; damage code, cause code, dan field lain wajib diisi sebelum ticket di-close. _(#1)_
- Dispatcher plant yang mengisi detail activity (termasuk damage code, cause code, dll), namun **closing ticket tetap dilakukan oleh dispatcher-engineer**. _(#4)_
- Dispatcher plant membuat ticket **scheduled** di SEMAR satu hari sebelumnya (one day before). _(#5)_
- Ticket Type ada dua: **Normal** dan **Re-Work**. Re-Work adalah pekerjaan berulang atas pekerjaan sebelumnya, biasanya bersifat unscheduled. _(#6)_
- Outstanding administration perlu ditambahkan ke flow chart. _(#21)_

#### Ticket Header Fields

- **Subject:** judul ticket.
- **Deskripsi:** detail pekerjaan / activity.

#### Ticket State Flow (Down Type & Status)

| Tahap | Aktor | Down Type | Status | Catatan |
|---|---|---|---|---|
| Laporan awal | Operator | To be down | Open | Laporan awal, masih perlu dipastikan |
| Dicek, ternyata bukan breakdown | Mechanic | To be down | Invalid | Jika mechanic cek dan tidak jadi breakdown |
| Dibatalkan | Operator | To be down | Cancel | Jika laporan di-cancel oleh operator |
| Dikonfirmasi breakdown | Mechanic | Breakdown | Open | Start Down Time otomatis saat perubahan status ini — **ini yang diambil Digiman+** |
| Selesai dikerjakan mechanic | Plant | Breakdown | Close Ready | **Dipakai Digiman+ untuk notif finish** |
| Siap dipakai | Dispatcher Engineer | Breakdown | Ready | — |

- WO SAP: opsional (tidak wajib diisi di ticket).
- Location: ada field-nya.
- Ready Estimasi Original: masih opsional, ada kolom revisi juga.
- Finish (Ready): diinput oleh Plant.

#### Input Activity di SEMAR

1. Component Group → Component
2. Component Category
3. Component Item → Sub Component
4. Part (opsional)
5. Labour Code, Spv, Mechanic (bisa lebih dari satu), Job Detail — jarang diisi

#### Input Delay di SEMAR

1. Delay Type
2. Start Delay Time — saat delay di-stop, end time bisa diedit
3. Location Destination
4. Deskripsi

Setelah delay pertama di-stop, user bisa menambahkan delay lagi.

### 2. Down Code & Job Codes

- Down Code terdiri dari: _(#7)_
  1. **Schedule**
  2. **Unschedule**
  3. **GET** (Ground Engaging Tools) → termasuk kategori Schedule
  4. **Plant Damage** → sama dengan Accident
  5. **Accident** → Activity Type
  6. **Tyre** → Activity Type
  7. **Opportunity** → pekerjaan apapun yang dikerjakan di luar jam kerja
- Job Codes berikut **wajib diisi di SEMAR sebelum closing ticket**: _(#11)_
  - Failure Code
  - Diagnosis Code
  - Reason Code
  - Finding Code
  - Labour Code
  - Action Code

### 3. Sinkronisasi Master Data (SEMAR ↔ SAP ↔ Digiman+)

- Data component hierarchy di SEMAR **sama** dengan SAP. Namun Damage, Cause, dan Action Remedy **berbeda**, meski mirip-mirip — perlu mapping. _(#3)_ _(lih. juga poin sinkronisasi Damage/Cause/Action Remedy dari tim SAP di [2026-07-01-meeting-notes.md](2026-07-01-meeting-notes.md) — kemungkinan perlu disatukan/di-cross-check.)_
- Data activity dan delay di SEMAR: **tidak masalah jika tidak diisi**, karena saat ini tidak ada report yang membutuhkan data tersebut. _(#9)_
- Perlu digambarkan report apa saja yang saat ini dipakai, baik di level site maupun level management, sebelum menentukan field mana yang wajib. _(#10)_
- **Open item:** Jika Failure Mode di-maintain di Digiman+, SEMAR perlu di-enhance — timeline belum ditentukan. _(#12)_

### 4. Notification & MO Timing

- Plant membuat notification dan MO di SAP **delayed** (tidak real-time) — dicatat sebagai temuan yang berdampak ke timing data masuk ke Digiman+. _(#2)_

### 5. Flow Unscheduled Service (SEMAR → Digiman+ → SAP)

- Alur: Ticket Unscheduled (SEMAR) → Digiman+ auto create planning → Digiman+ mengirim ke SAP (Create Order). _(#14)_
- Flow di Digiplan: Create Order Unscheduled → assign ke mechanic → add material → approval. _(#15)_
- **1 line operation = 1 task di Digiman+.** Harapannya setiap mechanic menyelesaikan task, sistem mengirim confirmation data per line operation ke SAP. _(#16)_
- Untuk sementara, data service unscheduled di Digiman+ bersumber dari SEMAR, sementara user **tetap manual** create notification dan WO dari SAP (belum otomatis end-to-end). _(#17)_

### 6. Flow Scheduled Service

- Data scheduled dari SEMAR dan SAP akan dipetakan (mapping) oleh Middleware, kemudian dikirim ke Digiman+. _(#18)_
- WO Scheduled diharapkan bisa di-TECO juga ke SAP. _(#20)_

### 7. TECO & Order Type

- TECO MO diharapkan berlaku untuk header planning, baik untuk service scheduled maupun unscheduled. _(#13)_
- **Open question:** Order type "Others" saat ini di-hide — apakah memungkinkan untuk menambahkan order type lain? _(#19)_

## Decisions

- Dispatcher membuat & menutup ticket di SEMAR end-to-end; damage/cause code dll wajib diisi sebelum close, closing tetap oleh dispatcher-engineer. _(#1, #4)_
- Ticket scheduled dibuat dispatcher plant satu hari sebelumnya. _(#5)_
- Ticket Type: Normal & Re-Work. _(#6)_
- Down Code & Job Codes ditetapkan sesuai daftar di atas; Job Codes wajib diisi sebelum closing ticket. _(#7, #11)_
- Ticket state flow (Down Type/Status) ditetapkan sesuai tabel di atas; status **Breakdown/Open** = trigger start downtime yang diambil Digiman+, status **Breakdown/Close Ready** = dipakai Digiman+ untuk notif finish. _(#8)_
- Data activity & delay SEMAR boleh kosong untuk saat ini — tidak ada report yang bergantung padanya. _(#9)_
- Flow Unscheduled Service: SEMAR → Digiman+ auto create planning → Digiman+ create order ke SAP; 1 line operation = 1 task Digiman+, confirmation dikirim per line operation. _(#14, #15, #16)_
- Sementara ini, data unscheduled service Digiman+ bersumber dari SEMAR, tapi user tetap manual create notif & WO dari SAP. _(#17)_
- Data scheduled dari SEMAR & SAP dipetakan Middleware sebelum masuk ke Digiman+. _(#18)_
- WO Scheduled & TECO MO header planning diharapkan berlaku untuk scheduled maupun unscheduled. _(#13, #20)_
- Outstanding administration ditambahkan ke flow. _(#21)_

## Open Items (perlu dibahas lebih lanjut)

| # | Item | Catatan |
|---|------|---------|
| 1 | Plant membuat notif & MO di SAP delayed | Berdampak ke timing data ke Digiman+ _(#2)_ |
| 2 | Mapping Damage/Cause/Action Remedy: SEMAR vs SAP | Mirip-mirip tapi beda — perlu mapping _(#3)_ |
| 3 | Gambaran report yang dipakai saat ini (site & management) | Diperlukan sebelum menentukan field wajib _(#10)_ |
| 4 | Enhancement SEMAR untuk Failure Mode yang di-maintain di Digiman+ | Timeline belum ditentukan _(#12)_ |
| 5 | Penambahan order type selain yang di-hide ("Others") | Apakah memungkinkan? _(#19)_ |

## Action Items

| # | Task | PIC | Due Date |
|---|------|-----|----------|
| 1 | Buat mapping Damage/Cause/Action Remedy antara SEMAR dan SAP | TBD | TBD |
| 2 | Kumpulkan gambaran report existing (site & management level) yang bergantung pada data SEMAR | TBD | TBD |
| 3 | Tentukan timeline enhancement SEMAR untuk Failure Mode dari Digiman+ | TBD | TBD |
| 4 | Investigasi kemungkinan menambahkan order type selain "Others" | TBD | TBD |
| 5 | Update flow chart: ticket state flow, outstanding administration, unscheduled & scheduled service flow | TBD | TBD |
| 6 | Implement auto create planning dari ticket unscheduled SEMAR ke Digiman+ → create order ke SAP | TBD | TBD |
| 7 | Implement confirmation per line operation ke SAP saat mechanic done task | TBD | TBD |
| 8 | Implement mapping data scheduled (SEMAR + SAP) di Middleware ke Digiman+ | TBD | TBD |
| 9 | Implement TECO untuk WO Scheduled & header planning (scheduled + unscheduled) | TBD | TBD |

## Next Session (Lanjut Besok)

- Scheduled yang tidak ada notification untuk equipment INACT.
- Scenario ticket dan notification dari SEMAR ke Digiman+.

## Notes

- Dokumen ini menyusun ulang 21 poin catatan mentah menjadi kelompok tematik untuk memudahkan pelacakan; nomor asli dicantumkan dalam tanda kurung `(#n)` di setiap poin untuk cross-check.
- Meeting ini melibatkan pihak SEMAR — mohon lengkapi daftar attendees termasuk perwakilan SEMAR.
- Ada dua item yang eksplisit dicatat untuk dilanjutkan di sesi berikutnya — lihat bagian "Next Session" di atas.
- Attendees, PIC, dan due date pada Action Items belum terisi — mohon dilengkapi.

