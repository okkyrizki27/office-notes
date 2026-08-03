# Material List API — Current State (Create Order)

*Last updated: 2026-07-31*

---

**Feature:** Order (Digiman+) — Create Order, aksi **"Add Part"** (pilih material untuk eMOL)
**Service:** `maintenance-order`
**Related doc:** [order-emol-sap-sync.md](order-emol-sap-sync.md) *(Bagian 4.3 — Material Opsional per eMOL)*, [storage-location-planner-group-enhancement.md](storage-location-planner-group-enhancement.md) *(Bagian A — konfirmasi endpoint belum bawa field Sloc)*
**Sumber:** HTTP capture (Alice HTTP Inspector, app "Digiman+ Dev" mobile build 28) + BE code, di-share user 2026-07-31

---

## 1. Endpoint

```
GET /maintenance-order/api/material/{id}/list
```

- `{id}` — **`MechanicOrderListId`** (eMOL, dikonfirmasi user 2026-07-31). Contoh capture: `3038`.
- Dipanggil saat user membuka aksi **"Add Part"** di layar create order (jalur Inspection maupun Additional Order — lihat [order-emol-sap-sync.md](order-emol-sap-sync.md) 4.3, [storage-location-planner-group-enhancement.md](storage-location-planner-group-enhancement.md) A.1).

### Query Params

| Param | Contoh | Keterangan |
|---|---|---|
| `ver` | `v1` | versi API |
| `siteCode` | `2009` | site user login |
| `sectionTypeCode` | `OBH` | section user |
| `ranking` | *(kosong)* | filter ranking material (`MaterialRanking.Code` — E/A/dst) |
| `keyword` | *(kosong)* | filter pencarian by Number/Description |
| `page` | `1` | pagination |
| `pageSize` | `10` | pagination |

### Headers relevan

- `X-Section-Type-Code`, `X-Is-Non-Section`, `X-Is-Null-Section`, `X-Is-Leader` — context section user, kemungkinan dipakai untuk filter/permission (konsisten dengan pola scoping site/section yang sudah ada di service lain)
- `Authorization: Bearer <JWT>` — token user standar (Azure B2C)

---

## 2. Response

```json
{
  "title": "Success",
  "statusCode": 200,
  "result": {
    "addedParts": [ /* material yang SUDAH ditambahkan ke eMOL ini */ ],
    "partsToAdd": [ /* hasil pencarian material yang BISA ditambahkan (paginated) */ ],
    "addedPartsCount": 1
  }
}
```

- **`addedParts`** — material yang sudah ter-attach ke eMOL/order ini, `Selected=1` di query BE (Bagian 3) — direct read dari `MechanicOrderMaterial` (di-enrich `Stock` dari master `Material` via join by `MaterialNumber`+`BatchCode`). Item di sini punya field `quantity`, yang **tidak muncul** di item `partsToAdd`.
- **`partsToAdd`** — hasil search/list material master yang tersedia untuk ditambahkan, di-filter oleh `keyword`/`ranking` dan di-paginate oleh `page`/`pageSize`. Berisi **baris duplikat per material number** (beda `batchCode`).
- **`addedPartsCount`** — total count `addedParts` (independen dari pagination `partsToAdd`).

### Field per Material Item

| Field | Contoh | Keterangan |
|---|---|---|
| `number` | `"1740467"` | Material Number |
| `description` | `"ABSORBER,SOUND (OBS)"` | Material Description |
| `ranking` | `"E"` / `"A"` | `MaterialRanking.Code` |
| `unitOfMeasurement` | `"EA"` / `"KIT"` | UoM |
| `cost` | `427.6` | harga — **sumbernya beda tergantung `Selected`** (lihat Bagian 3): `MechanicOrderMaterial.Cost` (snapshot saat material ditambahkan) untuk item yang sudah ditambahkan, `Material.MAP` (Moving Average Price, master data) untuk item yang belum ditambahkan. `0` pada beberapa baris `batchCode="REPAIRED"` di sample ini kemungkinan MAP material tsb memang `0` di master data |
| `stock` | `0` | stok |
| `batchCode` | `"NEW"` / `"REPAIRED"` / `""` | valuation type/batch |
| `rankingTextColor` / `rankingBackgroundColor` | `"#CC9A06"` / `"#FFF3CD"` | warna label ranking, dari master data `MaterialRanking` |
| `currency` | `""` | currency code (kosong di semua contoh) |
| `quantity` | `1` | **hanya ada di item `addedParts`** |

> ⚠️ **Tidak ada field Storage Location (Sloc)** di response ini — baik di `addedParts` maupun `partsToAdd`. Ini jadi **konfirmasi konkret pertama (raw response)** untuk klaim yang sudah tercatat di [storage-location-planner-group-enhancement.md](storage-location-planner-group-enhancement.md) A.1: *"Endpoint list BE belum membawa field Sloc (tidak diproyeksikan ke DTO)"* — meski kolom `StorageLocation` sudah ada di tabel master `Material` ([maintenance-order-schema.md](../database/maintenance-order-schema.md#L140)).
> **Dikonfirmasi di level SQL (Bagian 3, `filteredMaterialSql`)**: `mp.StorageLocation` memang **tidak ada di SELECT list** query yang baca tabel `Material` — jadi bukan sekadar "belum diproyeksikan ke DTO" di layer atas, tapi sudah tidak diambil sejak query-nya sendiri.

---

## 3. Backend Logic — `GetMaterialsForMolAsync`

*Sumber: BE code, di-share user 2026-07-31 (bukan hasil reverse-engineering dari response — ini logic aslinya).*

Method ini query dua sumber lalu digabung:

- **`MechanicMaterials`** CTE — baca `MechanicOrderMaterial` `WHERE MechanicOrderListId = @MolId AND IsActive = 1`. Ini material yang **sudah** ditambahkan ke eMOL ini (data transaksi).
- **`FilteredMaterial`** CTE — baca master `Material` `WHERE SectionTypeCode = @SectionType AND SiteId = @SiteId AND IsActive = 1` (+ `Keyword` opsional). Ini katalog material yang **bisa** ditambahkan (master data, discoverable lewat search).

Digabung di **`FinalResults`** (UNION ALL dua branch):
1. Dari `MechanicMaterials` LEFT JOIN `FilteredMaterial` (match `MaterialNumber` + `BatchCode`) LEFT JOIN `MaterialRanking` → `Selected = 1`, `Cost` dari `MechanicOrderMaterial.Cost` (snapshot transaksi).
2. Dari `FilteredMaterial` LEFT JOIN `MaterialRanking`, **`WHERE NOT EXISTS`** di `MechanicMaterials` (match `MaterialNumber` + `BatchCode`) → `Selected = 0`, `Cost` dari `Material.MAP` (master data).

Lalu **`Dedup`** — `ROW_NUMBER() OVER (PARTITION BY Number, BatchCode, SectionTypeCode, SiteId ORDER BY CreatedAt DESC)`, ambil `rn = 1`. Filter `Ranking` (kalau ada) diterapkan setelah dedup ini. Hasil akhir diurutkan `Selected DESC, Description` lalu di-paginate dengan `OFFSET`/`FETCH NEXT` (kalau `PageSize` diisi).

```sql
WITH MechanicMaterials AS (
    SELECT moo.Quantity, ISNULL(moo.BatchCode, '') AS BatchCode, moo.Cost, moo.UoMCode, moo.Currency,
           moo.MaterialNumber, moo.MaterialDescription, moo.MaterialRanking
    FROM [dbo].[MechanicOrderMaterial] moo
    WHERE moo.MechanicOrderListId = @MolId AND moo.IsActive = 1
    -- + AND (moo.MaterialDescription LIKE @Keyword OR moo.MaterialNumber LIKE @Keyword) kalau ada Keyword
),
FilteredMaterial AS (
    SELECT mp.SectionTypeCode, mp.SiteId, mp.Number, mp.Description,
           mp.BatchCode, mp.Ranking, mp.Stock, mp.UoMCode, mp.Currency, mp.MAP, mp.CreatedAt
    FROM [dbo].[Material] mp
    WHERE mp.SectionTypeCode = @SectionType AND mp.SiteId = @SiteId AND mp.IsActive = 1
    -- + AND (mp.Description LIKE @Keyword OR mp.Number LIKE @Keyword) kalau ada Keyword
),
FinalResults AS (
    SELECT mr.TextColor AS RankingTextColor, mr.BackgroundColor AS RankingBackgroundColor,
           mo.Quantity, mo.UoMCode AS UnitOfMeasurement, mo.Currency, mo.Cost, mp.Stock,
           mp.SectionTypeCode, mp.SiteId, mp.CreatedAt,
           mo.MaterialNumber AS Number, mo.MaterialDescription AS Description, mo.MaterialRanking AS Ranking,
           ISNULL(mo.BatchCode, '') AS BatchCode, 1 AS Selected
    FROM MechanicMaterials mo
    LEFT JOIN FilteredMaterial mp ON mo.MaterialNumber = mp.Number AND ISNULL(mo.BatchCode, '') = ISNULL(mp.BatchCode, '')
    LEFT JOIN [dbo].[MaterialRanking] mr ON mr.Code = mo.MaterialRanking

    UNION ALL

    SELECT mr.TextColor, mr.BackgroundColor, NULL AS Quantity, mp.UoMCode, mp.Currency, mp.MAP AS Cost, mp.Stock,
           mp.SectionTypeCode, mp.SiteId, mp.CreatedAt,
           mp.Number, mp.Description, mp.Ranking, mp.BatchCode, 0 AS Selected
    FROM FilteredMaterial mp
    LEFT JOIN [dbo].[MaterialRanking] mr ON mr.Code = mp.Ranking
    WHERE NOT EXISTS (
        SELECT 1 FROM MechanicMaterials mo
        WHERE mo.MaterialNumber = mp.Number AND mo.BatchCode = mp.BatchCode
    )
),
Dedup AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY Number, BatchCode, SectionTypeCode, SiteId ORDER BY CreatedAt DESC) AS rn
    FROM FinalResults
)
SELECT * FROM Dedup WHERE rn = 1 -- + AND Ranking = @Ranking kalau ada filter Ranking
ORDER BY Selected DESC, Description
OFFSET @Offset ROWS FETCH NEXT @DataSize ROWS ONLY -- kalau PageSize diisi
```

**Poin penting yang berubah dari asumsi sebelumnya di dokumen ini:**
- **`Cost` bukan field tunggal dari 1 sumber** — beda tergantung `Selected` (lihat tabel field Bagian 2).
- **Match "sudah ditambahkan vs belum"** dilakukan by `MaterialNumber + BatchCode` (bukan by row Sloc) — konsisten dengan `Dedup` yang juga tidak membedakan Sloc.
- **`StorageLocation` sudah hilang dari titik paling awal** (`FilteredMaterial` tidak men-select `mp.StorageLocation` sama sekali), bukan cuma "belum di-expose ke DTO".

---

## 4. Worked Example — Dampak Nyata Dedup Salah Dimensi

*Data uji di-share user 2026-07-31 (bukan konfirmasi data produksi live) — 1 material (`01-278902`, "BODY,OUTLET,LINCOLN PMV GREASE") dengan banyak baris master `Material`, dipakai untuk trace manual logic Bagian 3. Skenario: user buka create order di **site 2009, section OBH, model unit AM0035**.*

**Langkah 1 — `WHERE SiteId=2009 AND SectionTypeCode='OBH'`** (`AssetModelCode` **tidak** ada di filter ini): dari 42 baris data uji, **6 baris** lolos:

| Id | BatchCode | AssetModelCode | MAP | CreatedAt |
|---|---|---|---|---|
| 1281328 | *(kosong)* | AM0035 | 89,34 | 2025-08-16 |
| 1281331 | NEW | AM0035 | 86,83 | 2025-08-16 |
| 1281334 | REPAIRED | AM0040 | 0 | 2025-08-16 |
| 2134502 | NEW | AM0095 | 86,83 | 2026-06-23 |
| 2151516 | *(kosong)* | AM0041 | 89,34 | 2026-06-23 |
| 2180885 | REPAIRED | AM0035 | 0 | 2026-06-23 |

Perhatikan: 4 `AssetModelCode` berbeda ikut lolos (AM0035, AM0040, AM0095, AM0041) — bukan cuma AM0035 yang sedang di-order.

**Langkah 2 — `Dedup` (`PARTITION BY Number, BatchCode, SectionTypeCode, SiteId ORDER BY CreatedAt DESC`, ambil `rn=1`)**. `Number`/`SiteId`/`SectionTypeCode` sama untuk ke-6 baris ini, jadi partisi efektifnya cuma per `BatchCode`:

| BatchCode | Kandidat (kalah vs menang) | Pemenang (`rn=1`) |
|---|---|---|
| *(kosong)* | 1281328 (AM0035, 2025-08-16) vs 2151516 (**AM0041**, 2026-06-23) | **2151516 — AM0041** |
| NEW | 1281331 (AM0035, 2025-08-16) vs 2134502 (**AM0095**, 2026-06-23) | **2134502 — AM0095** |
| REPAIRED | 1281334 (AM0040, 2025-08-16) vs 2180885 (**AM0035**, 2026-06-23) | **2180885 — AM0035** |

**Hasil: 3 baris muncul di FE** (asumsi material ini belum ada di `MechanicOrderMaterial` untuk eMOL 3038, jadi ketiganya masuk `partsToAdd`).

**Kenapa ini signifikan**: dari 3 baris yang tampil untuk order unit **AM0035**, cuma **1** (`REPAIRED`, id `2180885`) yang kebetulan benar berasal dari row AM0035. Dua lainnya (`""` dan `NEW`) menampilkan Cost dari row **AM0041** dan **AM0095** — unit yang sama sekali berbeda dari yang sedang di-order — semata karena `CreatedAt`-nya lebih baru. Ini bukan cuma soal Sloc hilang (temuan Sloc-collapse di Bagian 2/5 malah **tidak kelihatan** di sample ini, karena `StorageLocation` untuk `SiteId=2009` kebetulan semuanya `NULL` di data uji) — melainkan bukti konkret bahwa **`Cost`/`Stock` yang tampil ke user bisa berasal dari row `AssetModelCode` yang sama sekali tidak relevan dengan unit yang sedang di-order**, karena `AssetModelCode` tidak ada di `WHERE` filter maupun partition key `Dedup`.

> **Kesimpulan: model unit (`AssetModelCode`) tidak mempengaruhi hasil sama sekali** — bukan cuma "kurang akurat", tapi memang **tidak pernah dipakai** di titik manapun dalam query ini (bukan di `WHERE`, bukan di `PARTITION BY`). Baris master `Material` mana yang menang dedup ditentukan murni oleh `CreatedAt` paling baru untuk kombinasi `Number+BatchCode+SectionTypeCode+SiteId` yang sama, terlepas dari `AssetModelCode`-nya. Dikonfirmasi lewat capture asli di Bagian 4.1 (request untuk AM0035, tapi Cost 2 dari 3 baris nyatanya berasal dari row AM0041/AM0095).

### 4.1 Response JSON — ✅ Dikonfirmasi Penuh via Capture Asli (2026-07-31)

User memanggil endpoint ini beneran dengan skenario di atas dan share screenshot response asli (Alice HTTP Inspector) — **jumlah baris (3), urutan (`""`→`NEW`→`REPAIRED`), `cost` (89.34 / 86.83 / 0), `stock` (`0` semua), dan `addedPartsCount: 0`** match persis dengan hasil trace manual di Bagian 4 (termasuk `batchCode: "REPAIRED"` di baris ke-3, yang di capture pertama sempat terpotong). Prediksi row count & winner `Dedup` di Bagian 4 **terbukti benar 100%** — JSON di bawah bukan lagi simulasi, sudah full match dengan response asli.

Satu koreksi dari capture asli terhadap dugaan awal saya: **`stock` TIDAK di-omit saat `Material.Stock` di DB bernilai `NULL`** — field ini tetap muncul eksplisit sebagai **`"stock": 0`**. Beda perilaku dari `quantity` (yang memang ter-omit total kalau `NULL`, lihat Bagian 2) — kemungkinan properti `Stock` di response DTO bertipe non-nullable (`int`/`float`, bukan `int?`/`float?`), jadi Dapper diam-diam fallback ke default value `0` saat sumbernya `DBNull`, alih-alih di-omit dari JSON seperti `Quantity` yang nullable.

```json
{
  "title": "Success",
  "statusCode": 200,
  "result": {
    "addedParts": [],
    "partsToAdd": [
      {
        "number": "01-278902",
        "description": "BODY,OUTLET,LINCOLN PMV GREASE",
        "ranking": "E",
        "unitOfMeasurement": "EA",
        "cost": 89.34,
        "stock": 0,
        "batchCode": "",
        "rankingTextColor": "#CC9A06",
        "rankingBackgroundColor": "#FFF3CD",
        "currency": ""
      },
      {
        "number": "01-278902",
        "description": "BODY,OUTLET,LINCOLN PMV GREASE",
        "ranking": "E",
        "unitOfMeasurement": "EA",
        "cost": 86.83,
        "stock": 0,
        "batchCode": "NEW",
        "rankingTextColor": "#CC9A06",
        "rankingBackgroundColor": "#FFF3CD",
        "currency": ""
      },
      {
        "number": "01-278902",
        "description": "BODY,OUTLET,LINCOLN PMV GREASE",
        "ranking": "E",
        "unitOfMeasurement": "EA",
        "cost": 0,
        "stock": 0,
        "batchCode": "REPAIRED",
        "rankingTextColor": "#CC9A06",
        "rankingBackgroundColor": "#FFF3CD",
        "currency": ""
      }
    ],
    "addedPartsCount": 0
  }
}
```

Semua field di JSON di atas (termasuk `ranking: "E"`, warna label, `batchCode` tiap baris, dan `addedPartsCount: 0`) **sudah dikonfirmasi lewat 2 screenshot capture** (2026-07-31) — tidak ada lagi bagian yang berstatus asumsi/simulasi untuk skenario spesifik ini.

### 4.2 Skenario Hipotetis — Data Stale (Model Unit Di-remove dari Mapping)

*Pertanyaan hipotetis user (2026-07-31): kalau master `Material` **stale** — 1 `StorageLocation` yang sama punya 2 baris `Stock` berbeda karena baris lama untuk model unit yang sudah di-remove dari mapping belum ke-cleanup — berapa row yang muncul?*

**Jumlah row tetap 3** (untuk skenario material di Bagian 4) — **tidak bertambah**. Baris stale ini cuma menambah **kandidat** ke partition `BatchCode` yang sudah ada (karena `Number`/`SectionTypeCode`/`SiteId`-nya sama, dan asumsinya `BatchCode`-nya juga sama dengan salah satu grup yang sudah ada) — bukan bikin partition baru. `Dedup` tetap cuma meloloskan 1 pemenang per partition, siapapun kandidatnya.

Yang berubah bukan **jumlah** row, tapi **risiko row mana yang menang**:
- Pemenang ditentukan murni oleh `CreatedAt` paling baru — `Dedup` **tidak mengecek `IsActive`/validitas mapping model-material sama sekali** di titik ini (`IsActive=1` cuma jadi syarat masuk `WHERE` filter, bukan tiebreaker `ROW_NUMBER`).
- Kalau baris stale (mapping yang sudah tidak berlaku) `CreatedAt`-nya kebetulan lebih baru dari baris valid (mis. akibat urutan batch sync SAP→Digiman+), **baris stale itu yang menang** — Cost/Stock yang salah tampil ke user.
- Ini **lebih tajam** dari temuan Bagian 5 (beda Sloc/AssetModelCode) karena di sini **`StorageLocation`-nya identik** — bukti bahwa masalahnya bukan cuma "Sloc/model beda", tapi memang **tidak ada signal apapun di query ini yang membedakan data valid vs stale** selain `CreatedAt`.

---

## 5. Observasi

- **Duplikasi baris per `batchCode`** terlihat jelas di `partsToAdd`: material `"1740467"` muncul 2x (`REPAIRED` dan kosong), `"1379425"` muncul 3x (`REPAIRED`, `NEW`, kosong), `"6560-01-1160"` muncul 3x (kosong, `NEW`, `REPAIRED`). Berdasarkan logic SQL di Bagian 3, ini **duplikasi yang disengaja/valid** — beda `BatchCode` = beda partition key di `Dedup`, jadi memang tetap tampil sebagai baris terpisah (by design, dilabeli beda di UI).
- **⚠️ Koreksi terhadap A.1**: [storage-location-planner-group-enhancement.md](storage-location-planner-group-enhancement.md) A.1 menyatakan *"Material list picker sudah menampilkan duplikat per-baris (tanpa dedup)"*. Berdasarkan SQL di Bagian 3, klaim ini **kurang tepat** — CTE `Dedup` **memang melakukan dedup**, tapi partition key-nya `(Number, BatchCode, SectionTypeCode, SiteId)` — **tidak termasuk StorageLocation maupun AssetModelCode** (lihat worked example Bagian 4). Konsekuensinya: kalau 1 material+batch punya beberapa baris Sloc (dan/atau AssetModelCode) berbeda di master `Material`, query ini **akan mengembalikan cuma 1 baris** (dipilih via `ROW_NUMBER() ... ORDER BY CreatedAt DESC` — baris `Material` dengan `CreatedAt` paling baru yang menang, bukan pilihan/konteks user). Artinya bug-nya bukan "tidak ada dedup" tapi **"dedup terjadi di dimensi yang salah"** — Sloc dan AssetModelCode-nya hilang/collapse secara silent, termasuk `Stock`/`Cost` yang ikut terbawa dari baris yang menang tsb. **Perlu dikonfirmasi ulang ke tim technical untuk update A.1** — di luar scope dokumen ini untuk mengubah dokumen enhancement tsb.
- `cost = 0` konsisten muncul di semua baris dengan `batchCode="REPAIRED"` pada sample HTTP capture (Bagian 2, 3 dari 3) — baris ini adalah `partsToAdd` (`Selected=0`), jadi `cost` di sini bersumber dari `Material.MAP`, bukan dari transaksi. Kemungkinan MAP material `REPAIRED` tsb memang `0` di master data — baru observasi dari 1 sample call, belum general rule (tapi konsisten juga dengan worked example Bagian 4, di mana kedua baris `REPAIRED` di data uji juga MAP `0`).
- **Filter list tidak di-scope per Asset/Equipment** — `filteredMaterialSql` cuma filter by `SiteId` + `SectionTypeCode` (+ `Keyword`/`Ranking` opsional). Tidak ada filter by `AssetModelCode`/Equipment meski kolom itu ada di `Material` ([maintenance-order-schema.md](../database/maintenance-order-schema.md#L138)) — material picker menampilkan **seluruh katalog material 1 site+section**, bukan yang relevan ke asset spesifik yang sedang di-order. Dibuktikan konkret di worked example Bagian 4.

---

## 6. Open Items

- **Di mana `addedParts`/`partsToAdd`/`addedPartsCount` di-split?** — `GetMaterialsForMolAsync` (Bagian 3) mengembalikan **satu list gabungan** (`Selected=1` dan `Selected=0` campur, diurutkan `Selected DESC, Description`, di-paginate bareng lewat `OFFSET`/`FETCH`). Splitting jadi 2 array + count terpisah di response JSON (Bagian 2) pasti terjadi di layer lain (Controller/mapper) yang tidak ada di snippet ini — belum ditelusuri.
- **Dead code: `countQtyMoreThanZero`** — di awal method ada query `SELECT COUNT(1) FROM MechanicOrderMaterial WHERE MechanicOrderListId = @MolId` (tanpa filter `IsActive`, beda dari `mechanicMaterialsSql` yang punya `AND moo.IsActive = 1`), hasilnya disimpan ke `countQtyMoreThanZero` tapi **variable ini tidak dipakai lagi di method ini** (tidak masuk return value). Kalau ternyata dipakai di caller (mis. sebagai sumber `addedPartsCount`) lewat jalur lain yang tidak terlihat di snippet ini, ada **risiko mismatch**: `addedPartsCount` bisa lebih besar dari jumlah `addedParts` yang benar-benar tampil (karena tidak filter `IsActive`, ikut menghitung baris material yang sudah soft-deleted). Kalau memang tidak dipakai sama sekali, ini pure dead code (query terbuang tiap request). Perlu ditelusuri ke pemanggil `GetMaterialsForMolAsync`.
- **`ranking` query param kosong di contoh capture** — belum ada sample call dengan filter ranking terisi untuk verifikasi behavior filter tersebut.

---

## Referensi
- [order-emol-sap-sync.md](order-emol-sap-sync.md) — flow eMOL & Material (Bagian 4.3)
- [storage-location-planner-group-enhancement.md](storage-location-planner-group-enhancement.md) — Bagian A, enhancement Storage Location pada Create Order (bergantung pada endpoint ini)
- [../database/maintenance-order-schema.md](../database/maintenance-order-schema.md) — schema `Material`, `MechanicOrderMaterial`, `MaterialRanking`
