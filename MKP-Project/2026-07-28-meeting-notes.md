# Meeting Notes — MKP - Digiman+ Master Data (Section, Ownership, System Status, Planner Group)

**Date:** 28 July 2026
**Topic:** MKP - Digiman+ Master Data: Non-Section Code, Ownership/Company Code, Equipment System Status Mapping, Terminologi Digiman+ vs SAP, Sub Equipment/Tyre, Material Master Data, Planner Group Master Data

---

## Attendees

**MKP:**
- Daniel
- Melina
- Rina

**BTECH:**
- Alimudin
- Faisal
- Okky
- Indro

## Agenda

1. Non-section code (unit & employee)
2. Section Type Code untuk material yang dipakai all model
3. Funloc Riung
4. Ownership (unit rental & company code)
5. Equipment System Status mapping
6. Terminologi Digiman+ vs SAP MKP
7. Sub Equipment & Tyre
8. Contoh data material (mapping ke Sloc, valuation type)
9. Planner Group master data
10. Rencana Section baru (CPP, Riung)
11. Pembatasan create order berdasarkan status

## Discussion

### 1. Non-Section Code

- Unit yang tidak punya section akan dibuatkan kode section **`MKP000`**. _(#1)_
- Employee yang tidak punya section juga disesuaikan, memakai kode **`S000`**. _(#2)_

### 2. Section Type Code untuk Material "All Model"

- **Open question:** kalau satu material dipakai untuk **semua model** (tidak spesifik ke satu model unit), Section Type Code-nya akan seperti apa? Diusulkan kemungkinan bisa dimapping ke **satu code khusus** (mis. `All` atau `Others`), sehingga material tersebut otomatis muncul di semua unit saat user memilih material — belum diputuskan final. _(#3)_

### 3. Funloc Riung

- Unit di **Riung** masih **under MKP**, cuma beda **Functional Location (funloc)** — ada funloc khusus untuk Riung di SAP. _(#4)_

### 4. Ownership

- **Unit rental:** dikonfirmasi **tidak perlu** dimaintain di Digiman+. _(#5.1)_
- **Company code / pembeda unit (mis. Riung):** masih didiskusikan apakah Digiman+ perlu ambil company code, atau cukup dibedakan lewat **Planner Group**. **Bu Melina akan cek kembali field apa yang tepat dari sisi SAP.** _(#5.2)_

### 5. Equipment System Status Mapping

Mapping status equipment SAP ke status Digiman+: _(#6)_

| System Status SAP | Kondisi Funloc | Bisa Buat WO/Order? | Status Digiman+ |
|---|---|---|---|
| **INST** | Terpasang di funloc | Bisa buat WO | **IN OPERATION** |
| **INAC** | Bisa/tidak bisa terpasang di funloc | Tidak bisa buat order/WO — standby | **IDLE** |
| **AVLB** | Tidak terpakai di funloc | Bisa buat WO | **IN OPERATION** |
| **DLFL** | Equipment tidak dipakai lagi (scrap, dihapus dari sistem) | — | **RETIRED** |

- **Open question:** apakah perlu ditambah status baru khusus untuk case **AVLB**? (Saat ini AVLB dan INST sama-sama dipetakan ke IN OPERATION meski kondisi funloc-nya beda — terpasang vs tidak terpakai.)

### 6. Terminologi Digiman+ vs SAP MKP

Pemetaan istilah hierarki asset: _(#7)_

| Digiman+ | SAP MKP |
|---|---|
| Asset Number | Equipment |
| Component | Sub Equipment |
| SubComponent | Component/BOM |

### 7. Sub Equipment & Tyre

- **Sub Equipment** saat ini **belum diaktifkan** mapping-nya di SAP MKP — belum jelas akan dimapping ke mana. _(#8)_
- **Tyre** (sebagai sub-equipment): pernah dimaintain di masa lalu, tapi **saat ini sudah tidak dimaintain lagi**. Ada wacana untuk dirapikan kembali, tapi belum ada informasi lebih lanjut. _(#9)_

### 8. Contoh Data Material

- Ditunjukkan contoh data material yang di-mapping dari master material ke **Sloc** dan **valuation type**. _(#10)_

### 9. Planner Group — Master Data

Struktur master data Planner Group yang akan dibangun: _(#11)_

| Field | Keterangan |
|---|---|
| **Planner Group Code** | Kode Planner Group |
| **Planner Group Name** | Nama Planner Group |
| **IsAllowedUsingMaterial** | Flag boleh/tidaknya Planner Group tersebut memakai material |

- Field **Planner Group** bersifat **mandatory** di layar **planner approval**.
- _(Catatan silang: `IsAllowedUsingMaterial` ini kemungkinan formalisasi dari aturan bisnis Planner Group **K01** yang "tidak boleh pakai material", yang sebelumnya dicatat sebagai aturan bisnis/SOP di [MOM 2026-07-01](2026-07-01-meeting-notes.md) poin #34 dan di [storage-location-planner-group-enhancement.md](../digiman+/architecture/inspection-order/storage-location-planner-group-enhancement.md) — sebelumnya enforcement rule ini eksplisit **tidak dibangun di Digiman+** (murni SOP manual). Field `IsAllowedUsingMaterial` di sini berpotensi mengubah itu jadi validasi berbasis data. Perlu cross-check ke tim terkait sebelum dianggap final.)_

### 10. Rencana Section Baru

- **CPP** akan di-treat sebagai section — **next** (belum dikerjakan, dibahas sesi berikutnya). _(#12)_
- **Riung** kemungkinan juga akan jadi section — **next** (belum dikerjakan, dibahas sesi berikutnya). _(#13)_

### 11. Pembatasan Create Order Berdasarkan Status

- Equipment dengan status **IDLE** atau **inactive** **tidak bisa** dipakai untuk create order — tidak muncul di pilihan dropdown saat create order. Dicatat sebagai **PR (perlu ditindaklanjuti/dicek)**. _(#14)_

## Decisions

- Non-section code unit: **`MKP000`**. _(#1)_
- Non-section code employee: **`S000`**. _(#2)_
- Unit Riung tetap under MKP, beda funloc saja (ada funloc khusus di SAP). _(#4)_
- Unit rental **tidak** dimaintain di Digiman+. _(#5.1)_
- System Status mapping SAP → Digiman+ ditetapkan sesuai tabel di atas (INST/AVLB → IN OPERATION, INAC → IDLE, DLFL → RETIRED). _(#6)_
- Terminologi Digiman+ ↔ SAP MKP: Asset Number=Equipment, Component=Sub Equipment, SubComponent=Component/BOM. _(#7)_
- Planner Group master data terdiri dari Code, Name, dan flag `IsAllowedUsingMaterial`; field ini mandatory di layar planner approval. _(#11)_
- CPP dan Riung berpotensi jadi section baru — keduanya **next**, belum dieksekusi sesi ini. _(#12, #13)_

## Open Items (perlu dibahas lebih lanjut)

| # | Item | Catatan |
|---|------|---------|
| 1 | Section Type Code untuk material "all model" | Diusulkan mapping ke code `All`/`Others` — belum diputuskan final _(#3)_ |
| 2 | Company code vs Planner Group untuk membedakan unit (mis. Riung) | Bu Melina cek field SAP yang tepat _(#5.2)_ |
| 3 | Status baru untuk case AVLB | Apakah perlu dipisah dari INST meski sama-sama IN OPERATION _(#6)_ |
| 4 | Sub Equipment dimapping ke mana di SAP MKP | Belum diaktifkan saat ini _(#8)_ |
| 5 | Tyre sub-equipment | Ada wacana dirapikan, belum ada info lanjutan _(#9)_ |
| 6 | Status IDLE/inactive tidak muncul di dropdown create order | Dicatat sebagai PR untuk dicek _(#14)_ |
| 7 | CPP sebagai section | Next session _(#12)_ |
| 8 | Riung sebagai section | Next session _(#13)_ |

## Action Items

| # | Task | PIC | Due Date |
|---|------|-----|----------|
| 1 | Cek field SAP yang tepat untuk membedakan unit (company code vs Planner Group), khusus kasus Riung | Melina | TBD |
| 2 | Evaluasi kebutuhan status baru untuk case AVLB | TBD | TBD |
| 3 | Klarifikasi mapping Sub Equipment di SAP MKP | TBD | TBD |
| 4 | Follow up rencana perapian data Tyre sub-equipment | TBD | TBD |
| 5 | Cek/PR: equipment status IDLE/inactive tidak muncul di dropdown create order | TBD | TBD |
| 6 | Build master data Planner Group (Code, Name, IsAllowedUsingMaterial) + mandatory field di planner approval screen | TBD | TBD |
| 7 | Putuskan mapping Section Type Code untuk material all-model (`All`/`Others`) | TBD | TBD |
| 8 | Lanjutkan pembahasan CPP sebagai section | TBD | Next session |
| 9 | Lanjutkan pembahasan Riung sebagai section | TBD | Next session |

## Notes

- Dokumen ini menyusun ulang 14 poin catatan mentah (termasuk sub-poin 5.1/5.2 dan daftar status di poin 6) menjadi kelompok tematik untuk memudahkan pelacakan; nomor asli dicantumkan dalam tanda kurung `(#n)` di setiap poin untuk cross-check.
- Poin #11 (Planner Group `IsAllowedUsingMaterial`) berkaitan langsung dengan pembahasan Planner Group di [MOM 2026-07-01](2026-07-01-meeting-notes.md) (#34–35) dan [storage-location-planner-group-enhancement.md](../digiman+/architecture/inspection-order/storage-location-planner-group-enhancement.md) — perlu di-cross-check apakah ini menggantikan pendekatan "enforcement lewat SOP" yang sebelumnya diputuskan di dokumen enhancement tersebut.
- Attendees, PIC, dan due date pada Action Items belum terisi lengkap — mohon dilengkapi.
