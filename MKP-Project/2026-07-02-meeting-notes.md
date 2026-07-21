# Meeting Notes — MKP - Digiman+ WO Mapping, Planning Flow & Auto TECO

**Date:** 02 July 2026
**Topic:** MKP - Digiman+ WO/Operation Mapping, Planning & Notification Flow, Auto TECO ke SAP

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

1. Mapping WO & Operation structure
2. Flow create plan & notification
3. Material di mobile & Maintenance Order Form (MOF)
4. Execution permission & flow pekerjaan tidak dapat dilakukan
5. Auto TECO WO ke SAP & skenario failed
6. Otorisasi & monitoring

## Discussion

### 1. WO / Operation Mapping

- Mapping WO selain WO activity backlog — diharapkan tidak manual kalau memungkinkan. _(#1)_
- Sistem perlu mengakomodir WO dengan operation lebih dari satu, di mana tiap operation bisa menjadi subtask. _(#2)_
- Di mobile, material bisa dimunculkan — dikonfirmasi di level operation. _(#3)_

### 2. Flow Create Plan & Notification

- Flow create plan perlu didetailkan per type, sampai ke tahap akhir. _(#4)_
- Status planning ditambahkan ke flow, termasuk apakah bisa di-edit atau tidak. _(#5)_
- Judul flowchart perlu diupdate. _(#6)_
- Input notification number pada saat create planning di sisi Planner — untuk scheduled service, dipertimbangkan apakah bisa dibuat opsional (tidak wajib). **Concern:** Workcenter tidak mengenal notification number, mereka hanya mengenal list pekerjaan. _(#7)_
- Notification untuk scheduled service akan dibuatkan interface sendiri di SAP sebagai source data notifikasi scheduled service untuk Digiman+. _(#19)_
- **Open item:** Notification untuk unscheduled service bersumber dari SEMAR — perlu didiskusikan lebih lanjut. _(#20)_
- PM V service cukup dibuat sebagai sub process saja di flow chart, dan tidak perlu link ke reservasi. _(#11)_
- Flow untuk kasus pekerjaan yang tidak dapat dilakukan, beserta pengisian remark, perlu digambarkan di flow chart. _(#13)_

### 3. Material di Mobile & Maintenance Order Form (MOF)

- Show materials list di task/backlog — item ini sudah ada di roadmap. _(#8)_
- **Phase 1:** proses execution tetap print MOF (Maintenance Order Form), karena task di mobile belum memunculkan material. _(#9)_
- **Next phase** (timeline belum ditentukan): setelah item show material list (#8) selesai, print MOF tidak diperlukan lagi. _(#10)_

### 4. Execution Permission & Flow Pekerjaan Tidak Dapat Dilakukan

- Perlu dicek apakah untuk aksi "finish execution" sudah ada permission code khusus atau belum. _(#12)_

### 5. Auto TECO WO ke SAP

- Flow return material perlu diperbaiki terlebih dahulu, sebelum proses auto teco WO backlog ke SAP. _(#14)_
- Auto TECO WO ke SAP — di SAP, proses ini sekaligus melakukan NOCO terhadap notifikasinya. _(#15)_
- Skenario failed TECO (belum tergambar di flow), berdasarkan kombinasi user status & system status: _(#16)_
  - **a.** User status **P010** & system status **CNF** → langsung TECO.
  - **b.** User status **P010** & system status **bukan CNF** → cek semua control key di semua operation:
    - Jika semua control key **PM02** → langsung teco.
    - Selain itu → belum boleh teco, hasilnya **failed**.
  - **c.** Untuk WO yang berhasil di-TECO langsung di SAP, response dari interface SAP harus **sukses disertai message**, agar Digiman+ bisa menggunakan response tersebut untuk update status transaksi menjadi sudah TECO.
- User diharapkan bisa melihat log auto teco MO (current status, failed, success, message). Untuk create MO, log ini sudah ada di Inspection Monitoring page (web) — perlu dipastikan apakah additional order sudah muncul juga di log tersebut atau belum. _(#18)_

### 6. Otorisasi & Monitoring

- Otorisasi display price di Inspection Monitoring (web) belum disegregasi — saat ini semua role kemungkinan bisa melihat price yang sama. _(#17)_

## Decisions

- WO dengan operation lebih dari satu diakomodir, operation menjadi subtask. _(#2)_
- Mobile menampilkan material dengan konfirmasi di level operation. _(#3)_
- Phase 1: execution tetap print MOF karena mobile belum menampilkan material; print MOF baru dihapus di next phase setelah show material list (#8) selesai. _(#9, #10)_
- PM V service dibuat sub process saja, tidak link ke reservasi. _(#11)_
- Flow return material diperbaiki dulu sebelum auto teco WO backlog ke SAP. _(#14)_
- Auto TECO WO ke SAP sekaligus melakukan NOCO notifikasi di SAP. _(#15)_
- Aturan skenario failed TECO (user status/system status/control key) ditetapkan sesuai poin 16.a–c. _(#16)_
- Notification scheduled service dibuatkan interface sendiri di SAP sebagai source data untuk Digiman+. _(#19)_

## Open Items (perlu dibahas lebih lanjut)

| # | Item | Catatan |
|---|------|---------|
| 1 | Mapping WO selain WO activity backlog | Diharapkan tidak manual — perlu dicari solusinya _(#1)_ |
| 2 | Input notification number optional saat create planning (scheduled service) | Concern: Workcenter tidak mengenal notification number _(#7)_ |
| 3 | Permission code khusus untuk finish execution | Perlu dicek sudah ada atau belum _(#12)_ |
| 4 | Otorisasi display price di Inspection Monitoring (web) | Belum disegregasi per role _(#17)_ |
| 5 | Additional order di log auto teco monitoring page | Perlu dipastikan sudah muncul atau belum _(#18)_ |
| 6 | Notification unscheduled service dari SEMAR | Need more discussion _(#20)_ |

## Action Items

| # | Task | PIC | Due Date |
|---|------|-----|----------|
| 1 | Cari solusi mapping WO non-backlog-activity agar tidak manual | TBD | TBD |
| 2 | Update flowchart: detail create plan per type, tambah status planning + editability, update judul flowchart | TBD | TBD |
| 3 | Gambar flow pekerjaan tidak dapat dilakukan + pengisian remark | TBD | TBD |
| 4 | Diskusi opsi notification number optional saat create planning scheduled service (concern Workcenter) | TBD | TBD |
| 5 | Implement show materials list di task/backlog (roadmap) | TBD | TBD |
| 6 | Hapus requirement print MOF di next phase setelah item #5 selesai | TBD | TBD |
| 7 | Cek permission code khusus untuk finish execution | TBD | TBD |
| 8 | Perbaiki flow return material sebelum auto teco WO backlog ke SAP | TBD | TBD |
| 9 | Implement auto teco WO ke SAP + NOCO notif sekaligus | TBD | TBD |
| 10 | Implement skenario failed teco (rules 16.a-c) + pastikan response sukses+message untuk update status di Digiman+ | TBD | TBD |
| 11 | Segregasi otorisasi display price di Inspection Monitoring (web) | TBD | TBD |
| 12 | Pastikan additional order tampil di log auto teco monitoring page (web) | TBD | TBD |
| 13 | Buat interface SAP sendiri untuk notification scheduled service sebagai source data Digiman+ | TBD | TBD |
| 14 | Lanjutkan diskusi notification unscheduled service dari SEMAR | TBD | TBD |

## Notes

- Dokumen ini menyusun ulang 20 poin catatan mentah menjadi kelompok tematik untuk memudahkan pelacakan; nomor asli dicantumkan dalam tanda kurung `(#n)` di setiap poin untuk cross-check.
- Lanjutan dari diskusi sebelumnya: [2026-07-01-meeting-notes.md](2026-07-01-meeting-notes.md).
- Attendees, PIC, dan due date pada Action Items belum terisi — mohon dilengkapi.

