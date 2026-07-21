# Meeting Notes — MKP - Digiman+ Confirmation, Unit Status & Material Master Data

**Date:** 09 July 2026
**Topic:** MKP - Digiman+ Confirmation Reporting, Unit/Equipment Status & Notification Sourcing, Material & Damage/Cause/Action Remedy Master Data

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

1. Ekspektasi confirmation reporting (mechanic, per-mechanic ke SAP)
2. Unit/Equipment status & notification sourcing (SEMAR/SAP)
3. Terminologi: Backlog → Task
4. Material master data (structure, volume, section)
5. Damage/Cause/Action Remedy master data integration

## Discussion

### 1. Ekspektasi Confirmation Reporting

- Ekspektasi: mechanic benar-benar melakukan actual report confirmation start dan end pekerjaan (bukan sekadar formalitas). _(#1)_
- Ekspektasi: data konfirmasi pekerjaan yang dikirim ke SAP bisa dilakukan **per mechanic**. _(#2)_

### 2. Unit/Equipment Status & Notification Sourcing

- Unit dan unit status ditarik dari SAP: **all status**. _(#3)_
- Unit status **INACT** belum tentu memiliki data SEMAR. Sumber data notifikasi ke Digiman+ dipetakan sebagai berikut: _(#4)_
  - **a.** Ticket SEMAR → untuk kasus **unscheduled**.
  - **b.** Ticket SEMAR dan notif → untuk kasus **scheduled**.
  - **c.** Notif saja → untuk **equipment INACT**.
- Case: ticket scheduled yang lupa input WO (karena field WO di SEMAR sifatnya opsional): _(#5)_
  - **Temporary solution:** diselesaikan lewat SOP.
  - **Opsi enhancement:** SEMAR dibuat mandatory input WO khusus untuk ticket scheduled.
  - **Worst case:** jika WO tetap tidak diinput, ticket tidak masuk ke Digiman+ — _catatan asli terpotong di sini ("akan tetapi..."), perlu klarifikasi kelanjutannya ke MKP._

### 3. Terminologi

- Label **"Backlog"** di Digiman+ diubah menjadi **"Task"**. _(#6)_

### 4. Material Master Data

- Struktur data material: 1 Material = N Material Group; 5 Batch (valuation type); 9-11 Sloc; scope site **Sesayap** saja. _(#7)_
  - Contoh volume: spare part ±500.000 data yang punya stock (tabel **MARD**), belum termasuk yang hanya ada di **MARA**. Dikalikan 4 batch (tanpa damage), dikalikan section — ini adalah gambaran estimasi volume data material yang akan masuk ke Digiman+.
- Material **Section Type Code** bersumber dari SAP — berlaku juga untuk Equipment, **bukan** digenerate di middleware. _(#8)_
- Material **AssetModelCode** akan di-assess di sisi SAP. _(#9)_
- Equipment **Section Type Name**: perlu dicek dulu kebutuhannya di Digiman+. _(#10)_
- Tampilan **MM03 BUMA** sudah dishare oleh Pak Indro sebagai referensi. _(#13)_
- **Open item (MKP internal discussion):** kemungkinan `SectionTypeCode` Equipment dan Material di SAP = Model Unit — masih dibahas internal di MKP. _(#14)_
- `SectionTypeCode` Equipment dan User section relasinya bisa **many-to-many**. _(#15)_

### 5. Damage/Cause/Action Remedy Master Data

- Master data Damage Code, Cause Code, dan Action Remedy dari SAP membutuhkan pembangunan API integration. _(#11)_
- Mapping Damage Code/Cause Code/Action Remedy ke component/subcomponent tetap dilakukan di sisi Digiman+. _(#12)_
- _(Lanjutan topik dari [2026-07-01-meeting-notes.md](2026-07-01-meeting-notes.md) #8 dan [2026-07-08-meeting-notes.md](2026-07-08-meeting-notes.md) #3 — kini sudah lebih jelas: sumbernya API dari SAP, mapping ke component/subcomponent tetap di Digiman+.)_

## Decisions

- Unit & unit status ditarik dari SAP untuk semua status. _(#3)_
- Sumber data notifikasi ke Digiman+: ticket SEMAR (unscheduled), ticket SEMAR + notif (scheduled), notif saja (equipment INACT). _(#4)_
- Label "Backlog" diubah menjadi "Task". _(#6)_
- Material Section Type Code bersumber dari SAP (termasuk untuk Equipment), tidak digenerate di middleware. _(#8)_
- AssetModelCode material di-assess di sisi SAP. _(#9)_
- Master data Damage/Cause/Action Remedy dari SAP akan diintegrasikan lewat API; mapping ke component/subcomponent tetap di Digiman+. _(#11, #12)_
- SectionTypeCode Equipment ↔ User section bisa many-to-many. _(#15)_

## Ekspektasi (dari MKP, belum tentu jadi keputusan teknis final)

- Mechanic actual report confirmation start & end pekerjaan. _(#1)_
- Data konfirmasi pekerjaan ke SAP bisa per mechanic. _(#2)_

## Open Items (perlu dibahas lebih lanjut)

| # | Item | Catatan |
|---|------|---------|
| 1 | Case scheduled ticket lupa input WO (worst case) | Catatan asli terpotong — perlu klarifikasi kelanjutan poin ke MKP _(#5)_ |
| 2 | Kebutuhan Equipment Section Type Name di Digiman+ | Perlu dicek _(#10)_ |
| 3 | SectionTypeCode Equipment/Material = Model Unit? | Masih MKP internal discussion _(#14)_ |

## Action Items

| # | Task | PIC | Due Date |
|---|------|-----|----------|
| 1 | Evaluasi implementasi actual confirmation start/end per mechanic | TBD | TBD |
| 2 | Implement pengiriman data konfirmasi pekerjaan ke SAP per mechanic | TBD | TBD |
| 3 | Klarifikasi ke MKP: kelanjutan worst-case scheduled ticket tanpa WO (catatan terpotong) | TBD | TBD |
| 4 | Evaluasi opsi enhancement SEMAR: mandatory WO untuk ticket scheduled | TBD | TBD |
| 5 | Rename label "Backlog" menjadi "Task" di UI Digiman+ | TBD | TBD |
| 6 | Build struktur data material (Material Group, Batch/valuation type, Sloc, Site) sesuai estimasi volume | TBD | TBD |
| 7 | Konsumsi Material Section Type Code dari SAP untuk Material & Equipment | TBD | TBD |
| 8 | Cek kebutuhan Equipment Section Type Name di Digiman+ | TBD | TBD |
| 9 | Build API integration Damage/Cause/Action Remedy dari SAP | TBD | TBD |
| 10 | Implement mapping Damage/Cause/Action Remedy ke component/subcomponent di Digiman+ | TBD | TBD |
| 11 | Review tampilan MM03 BUMA (referensi dari Pak Indro) | TBD | TBD |
| 12 | Follow up hasil diskusi internal MKP: SectionTypeCode Equipment/Material = Model Unit | MKP | TBD |
| 13 | Implement relasi many-to-many SectionTypeCode Equipment ↔ User section | TBD | TBD |

## Notes

- Dokumen ini menyusun ulang 15 poin catatan mentah menjadi kelompok tematik untuk memudahkan pelacakan; nomor asli dicantumkan dalam tanda kurung `(#n)` di setiap poin untuk cross-check.
- Poin #4 (sumber notifikasi ke Digiman+ berdasarkan status unit) menjawab dua item "Next Session" yang tercatat di [2026-07-08-meeting-notes.md](2026-07-08-meeting-notes.md): scheduled tanpa notif untuk equipment INACT, dan scenario ticket & notif dari SEMAR ke Digiman+.
- Poin #5 memiliki kalimat yang terpotong di catatan asli ("...akan tetapi") — dicatat apa adanya, perlu klarifikasi ke MKP sebelum dianggap final.
- Attendees, PIC, dan due date pada Action Items belum terisi — mohon dilengkapi.

