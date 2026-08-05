# Digiman+ Integration Interface Specification for MKP

> Sumber: *I3-Digiman+ Integration Interface Specification for MKP-050826-033923.pdf*

## Document History

| Version | Release Date | Summary |
| --- | --- | --- |
| 1.0 | 29-Dec-2025 | Initial version |
| 2.0 | 06-Jul-2026 | Merge some APIs create and update; add some additional fields in some APIs |

## 1. Introduction

Dokumen ini menjelaskan framework integrasi antara Digiman+ dan sistem eksternal (ERP seperti SAP/Oracle, atau third-party lain). Tujuan dokumen:

- Menjelaskan mekanisme integrasi
- Mendefinisikan struktur data yang dibutuhkan
- Menjelaskan spesifikasi API
- Menjabarkan kebutuhan teknis & konfigurasi dari sisi client
- Memastikan kesiapan sebelum implementasi integrasi

Ditujukan untuk membantu client memahami cara kerja integrasi, mengidentifikasi field wajib & kebutuhan konfigurasi, serta menemukan gap informasi/prasyarat teknis sebelum mulai integrasi.

## 2. Integration Overview

### 2.1 Integration Capability

Digiman+ mendukung pertukaran data dengan sistem eksternal melalui HTTP:

- **Outbound Integration**: data dari Digiman+ → sistem eksternal
- **Inbound Integration**: data dari sistem eksternal → Digiman+

### 2.2 Integration Technology

- **Integration Type**: REST API
- **Data Format**: JSON
- **Communication Protocol**: HTTPS

### 2.3 Authentication & Access Control

1. **API Key Authentication** — semua request wajib menyertakan API Key yang valid di header `X-API-Key`. Request tanpa API Key valid akan ditolak. API Key di-provide oleh tim Digiman+ (client tidak generate sendiri).
2. **IP Whitelisting** — akses API dibatasi hanya untuk IP client yang sudah terdaftar. Client wajib menyediakan:
   - Public IP address(es) yang dipakai untuk API calls
   - IP per environment (UAT dan Production)

   Whitelisting dilakukan oleh tim Digiman+ berdasarkan IP yang disediakan client tersebut. Request dari IP yang tidak di-whitelist akan diblokir di level network.

### 2.4 Base URL per Environment

Nilai `base_url` yang dipakai di seluruh endpoint Inbound API pada dokumen ini (section 6) mengacu ke tabel berikut:

| Environment | Base URL |
| --- | --- |
| Dev | `https://cst-shared-apm-dev-001.azure-api.net/integration/external-integration/` |

> Catatan: base URL di atas sudah termasuk path `integration/external-integration/`, jadi endpoint tiap API (mis. `.../employee`, `.../asset`) tinggal ditambahkan langsung tanpa mengulang path tersebut.

## 3. Terminology

| Term | Definition |
| --- | --- |
| Digiman+ | SaaS platform dari BTECH untuk manajemen aktivitas asset maintenance. |
| External System | Sistem pihak ketiga mana pun yang terintegrasi dengan Digiman+. |
| Integration | Mekanisme teknis pertukaran data terstruktur antara Digiman+ dan sistem eksternal via REST API over HTTPS dengan payload JSON. |
| Inbound Integration | Data flow yang berasal dari sistem eksternal dan diproses oleh Digiman+. |
| Outbound Integration | Data flow yang berasal dari Digiman+ dan dikirim ke sistem eksternal. |
| API Key | Secret key unik yang diberikan ke sistem eksternal untuk otentikasi request ke Digiman+ API. |
| IP Whitelisting | Kontrol keamanan level network yang membatasi akses API hanya ke IP client yang sudah disetujui. |

## 4. High Level Architecture

Alur integrasi: **Digiman+ ⇄ Client Middleware ⇄ Client System (SAP / Oracle / dll.)**

- **Inbound** (Client → Digiman+, via middleware): Employee, Asset/Equipment, Asset/Equipment Status, Material, Maintenance Order Backlog, Notification
- **Outbound** (Digiman+ → Client, via middleware): Complete MO Inspection, Close & Delete MO Inspection, Backlog Execution, Create Maintenance Order

---

## 5. Outbound API Specifications

Outbound = Digiman+ memanggil API milik client.

### 5.1 Backlog Execution

| | |
| --- | --- |
| **API Endpoint** | `{Backlog Execution Client's API}` |
| **Description** | Dipanggil saat backlog dieksekusi oleh mekanik. |
| **Method** | POST |
| **Header** | `Content-Type: application/json` |

**Request**

```json
{
  "MONumber": [
    "1104499011",
    "1104499012",
    "1104499013",
    "1104499014"
  ]
}
```

**Expected Response**

```json
[
  {
    "MONumber": "1104499011",
    "SAPStatus": "1",
    "SAPText": "Order has been CLOSED|Save log history success",
    "ModifiedUtcDate": "2026-01-15T14:44:37.8770544+00:00"
  }
]
```

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| MONumber (request) | Array list of varchar | No | List Maintenance Order number yang dieksekusi |
| MONumber (response) | varchar | No | Maintenance Order number — satu per item hasil |
| SAPStatus | varchar | No | Integration status: 1 = Success, 2 = Failed |
| SAPText | varchar | No | Message from SAP Integration |
| ModifiedUtcDate | Datetime (ISO 8601) | No | Date time |

### 5.2 Create Maintenance Order

| | |
| --- | --- |
| **API Endpoint** | `{Create MO Client's API}` |
| **Description** | Dipanggil saat order di-approve. |
| **Method** | POST |
| **Header** | `Content-Type: application/json` |

**Request**

```json
[
  {
    "EMolNumber": "IFD-2602001584",
    "SupervisorId": 1100800565,
    "Body": [
      {
        "Id": 4807,
        "SiteId": 2009,
        "PoolingId": 4628,
        "MOType": "MT01",
        "MODescription": "P1-Flushing AC Function Internal ",
        "PMActType": "IH7",
        "Equipment": "DAVV40022",
        "BasicStartDate": "2026-03-11T07:54:21.293",
        "MaterialNumber": "1740467",
        "MaterialQuantity": "2.00",
        "Batch": "",
        "MOCreatedBy": "2009OBH.supervisor01@protonmail.com",
        "AttachmentUrl": "https://digiman-dev.bukittechnology.com/order-list/material-order?workOrderId=20356&assetNumber=DAVV40022&taskPersonalizedFindingId=5391&molNumber=IFD-2602001584",
        "SLoc": "WH01",
        "MoDescriptionLong": "Model Unit : A40-G\nKode Unit : DAVV40022\nDamage : Air Leaks-Internal\nInspector : 2009OBH.supervisor01"
      }
    ]
  }
]
```

**Expected Response**

```json
[
  {
    "MONumber": "1105239395",
    "SAPStatus": "1",
    "SAPText": "Success Create MO: 1105239395 and log history",
    "ModifiedUtcDate": "2026-01-15T14:44:37.8770544+00:00"
  }
]
```

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| EMolNumber | varchar | No | Electronic mechanic order number |
| SupervisorId | numeric | No | Supervisor Identity Number |
| Body | array | No | List of MO detail records yang akan dibuat |
| Body.Id | integer | No | Synchronization Id |
| Body.SiteId | numeric | No | Site Id |
| Body.PoolingId | integer | No | Pooling Id |
| Body.MOType | varchar | No | Maintenance/Work order type. Bervariasi per client, butuh konfigurasi. |
| Body.MODescription | varchar | No | Maintenance Order / Work Order Description |
| Body.PMActType | varchar | No | Plant Maintenance Activity Type. Bervariasi per client, butuh konfigurasi. |
| Body.Equipment | varchar | No | Equipment number |
| Body.BasicStartDate | Datetime (ISO 8601) | No | Tanggal mulai |
| Body.MaterialNumber | varchar | No | Material number |
| Body.MaterialQuantity | varchar | No | Material Order Quantity |
| Body.Batch | varchar | Yes | Batch of material |
| Body.MOCreatedBy | varchar | No | User code pembuat order |
| Body.AttachmentUrl | varchar | No | Evidence of finding |
| Body.SLoc | varchar | No | Storage location material |
| Body.MoDescriptionLong | varchar | No | Deskripsi panjang MO/WO |
| MONumber (response) | varchar | No | MO number yang digenerate ERP |
| SAPStatus (response) | varchar | No | 1 = Success, 2 = Failed |
| SAPText (response) | varchar | No | Message dari SAP Integration |
| ModifiedUtcDate (response) | Datetime (ISO 8601) | No | Date time |

---

## 6. Inbound API Specifications

Inbound = client memanggil API Digiman+.

### 6.1 Employee

> **Update:** integrasi ini sebelumnya bernama "User" — endpoint dan root field JSON berubah dari `user`/`users` menjadi `employee`/`employees`. Field `userCode` tetap dipertahankan namanya (tidak berubah jadi `employeeCode`). Ditambahkan `positionCode`, `levelCode`, `levelName`; `siteId`→`siteCode`, `departmentId`→`departmentCode`, `sectionId`→`sectionCode` di-rename dari akhiran `Id` menjadi `Code`.

**Description**: Upsert employee — matched by `employees.userCode`; kalau sudah ada → update, kalau belum → create. Mendukung single & bulk.

| | |
| --- | --- |
| **API Endpoint** | `base_url/employee` |
| **Method** | POST |

**Request**

```json
{
  "employees": [
    {
      "userCode": "mkpinspector01@protonmail.com",
      "fullName": "mkpinspector01",
      "employeeId": "0000895",
      "positionCode": "C01",
      "positionName": "Supervisor",
      "levelCode": "3A",
      "levelName": "3A",
      "siteCode": "1001",
      "siteName": "Sesayap",
      "departmentCode": "PLT",
      "departmentName": "Plant",
      "sectionCode": "S001",
      "sectionName": "Hauler",
      "isActive": true
    }
  ]
}
```

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| employees | array | No | List of employee records (bulk supported) |
| employees.userCode | varchar(64) | No | Unique user identifier; must be unique |
| employees.fullName | varchar(150) | No | Full name of the employee |
| employees.employeeId | varchar(50) | No | Employee ID (NIK) |
| employees.positionCode | varchar(64) | Yes | Kode posisi/jabatan employee |
| employees.positionName | varchar(64) | Yes | Nama posisi/jabatan employee |
| employees.levelCode | varchar(64) | Yes | Kode level employee |
| employees.levelName | varchar(64) | Yes | Nama level employee |
| employees.siteCode | varchar(64) | No | Site tempat employee ditugaskan. Jika kode belum terdaftar, akan otomatis di-insert ke master data. |
| employees.siteName | varchar(64) | No | Nama site |
| employees.departmentCode | varchar(64) | No | Department identifier (referensi saja). Jika kode belum terdaftar, akan otomatis di-insert ke master data. |
| employees.departmentName | varchar(64) | No | Nama department |
| employees.sectionCode | varchar(64) | No | User Section identifier. Jika kode belum terdaftar, akan otomatis di-insert ke master data.|
| employees.sectionName | varchar(64) | No | Section name |
| employees.isActive | boolean | No | true = active, false = inactive |

**Response**

- HTTP 200 - Success:
```json
{
  "status": "success",
  "totalData": 1,
  "successCount": 1,
  "failedCount": 0,
  "results": [
    { "userCode": "mkpinspector01@protonmail.com", "status": "success" }
  ]
}
```
- HTTP 200 - Partial Success:
```json
{
  "status": "success",
  "totalData": 2,
  "successCount": 1,
  "failedCount": 1,
  "results": [
    { "userCode": "mkpinspector01@protonmail.com", "status": "success" },
    { "userCode": "mkpinspector02@protonmail.com", "status": "failed", "errorCode": "ERR-0017" }
  ]
}
```
- HTTP 400:
```json
{
  "status": "error",
  "totalData": 1,
  "successCount": 0,
  "failedCount": 1,
  "results": [
    { "userCode": "mkpinspector01@protonmail.com", "status": "failed", "errorCode": "ERR-0017" }
  ]
}
```
- HTTP 403: `{ "errorCode": "ERR-0006" }`
- HTTP 500: `{ "errorCode": "ERR-0007" }`

### 6.2 Asset

#### 6.2.1 Asset

**Description**: Upsert asset — matched by `assets.assetNumber`. Mendukung single & bulk.

| | |
| --- | --- |
| **API Endpoint** | `base_url/asset` |
| **Method** | POST |

**Request**

```json
{
  "assets": [
    {
      "assetNumber": "EXC00031",
      "siteCode": "1001",
      "siteName": "Sesayap",
      "sectionTypeCode": "OBL",
      "sectionTypeName": "Loader",
      "assetCategoryCode": "A",
      "assetTypeCode": "EXC",
      "assetTypeName": "Excavator",
      "assetBrandCode": "KOM",
      "assetBrandName": "KOMATSU",
      "assetModelCode": "PC2000-8",
      "assetModelName": "PC2000-8",
      "assetClassName": "EXA 200 TON CLASS",
      "assetVariantName": "EXA 200 TON CLASS",
      "isActive": true
    }
  ]
}
```

| Field | Type | Nullable | Description | SAP Table | Remarks |
| --- | --- | --- | --- | --- | --- |
| assets | array | No | List of asset records (bulk supported) | | |
| assets.assetNumber | varchar(200) | No | Unique asset identifier | EQUI-EQUNR | |
| assets.siteCode | varchar(64) | No | Site tempat equipment ditugaskan. Jika kode belum terdaftar, akan otomatis di-insert ke master data. | ILOA-SWERK | |
| assets.siteName | varchar(64) | No | Nama site | | |
| assets.sectionTypeCode | varchar(64) | No | Equipment Section/area identifier equipment. Tidak diproses jika belum terdaftar.| ILOA-BEBER | contoh: 201 |
| assets.sectionTypeName | varchar(512) | No | Nama section/area (pasangan sectionTypeCode) | T357-FING | contoh: Hauler |
| assets.assetCategoryCode | varchar(64) | Yes | Asset category code. Tidak diproses jika belum terdaftar. | EQUI-EQTYP | contoh: H, M |
| assets.assetCategoryName | varchar | Yes | Nama category (pasangan assetCategoryCode — keduanya wajib atau tidak sama sekali) | T370T-TYPTX | contoh: Heavy Equipment, Machines |
| assets.assetTypeCode | varchar(64) | Yes | Asset type code (pasangan assetTypeName) | EQUI-EQART | contoh: 01, 02 |
| assets.assetTypeName | varchar (trunc. 200) | Yes | Asset type name. Tidak diproses jika belum terdaftar. | T370K-EARTX | contoh: Excavator |
| assets.assetBrandCode | varchar(64) | No | Asset brand code (pasangan assetBrandName). Required. | AUSP-ATWRT / EQUI-HERST | contoh: KOMATSU |
| assets.assetBrandName | varchar(128) | No | Asset brand name. Tidak diproses jika belum terdaftar. | AUSP-ATWRT / EQUI-HERST | contoh: KOMATSU |
| assets.assetModelCode | varchar(64) | No | Asset model code (pasangan assetModelName). Required. | AUSP-ATWRT / EQUI-TYPBZ | contoh: PC2000-8 |
| assets.assetModelName | varchar(50) | No | Asset model name. Tidak diproses jika belum terdaftar. | AUSP-ATWRT / EQUI-TYPBZ | contoh: PC2000-8 |
| assets.assetClassCode | varchar(64) | Yes | Asset class code (pasangan assetClassName) | TBD — konfirmasi tim SAP | **Tidak Pakai** |
| assets.assetClassName | varchar(128) | Yes | Asset class name. Tidak diproses jika belum terdaftar. | AUSP-ATWRT | **Tidak Pakai** |
| assets.assetVariantCode | varchar(64) | Yes | Asset variant code (pasangan assetVariantName) | | **Tidak dipakai** |
| assets.assetVariantName | varchar (trunc. 200) | Yes | Asset variant name. Tidak diproses jika belum terdaftar. | AUSP-ATWRT | **→ tidak dipakai** |
| assets.assetOwnershipCode | varchar(64) | Yes | Asset ownership code | TBD — konfirmasi tim SAP | |
| assets.isActive | boolean | Yes | Optional, default true bila diomit | Dikirim dari SAP true/false berdasarkan status equipment | INAC atau DLFL = false |

> **Catatan:** `assetClassCode`/`assetClassName` dan `assetVariantCode`/`assetVariantName` ditandai **Tidak Pakai** khusus untuk konteks MKP (SAP MKP tidak menggunakan konsep class/variant ini). Field-nya tetap Nullable=Yes secara skema, jadi aman baik dikirim maupun tidak — contoh payload di atas menampilkan value hanya untuk ilustrasi format, bukan berarti field ini aktif dipakai MKP.

**Response**: sama pola dengan Employee API (`assetNumber` sebagai key), HTTP 200 Success/Partial Success, 400, 403 (`ERR-0006`), 500 (`ERR-0007`).

#### 6.2.2 Asset Status

**Description**: Registrasi status operasional equipment di Digiman+, sebagai historical log kondisi unit.

> **Catatan:** Client hanya perlu mengirim status **terakhir (last status)** setiap kali terjadi perubahan status — tidak perlu mengirim ulang seluruh histori status equipment di setiap request.

| | |
| --- | --- |
| **API Endpoint** | `base_url/asset-status` |
| **Method** | POST |

**Request**

```json
{
  "assetStatus": [
    {
      "trDate": "2024-10-14T00:00:00+07:00",
      "assetNumber": "BDCT10003",
      "status": "IN OPERATION"
    }
  ]
}
```

| Field | Type | Nullable | Description | SAP Table | Remarks |
| --- | --- | --- | --- | --- | --- |
| assetStatus | array | No | Collection of asset status records | | |
| assetStatus.trDate | datetime (ISO 8601) | No | Effective date/time status di source system, dengan timezone | JCDS-UDATE | |
| assetStatus.assetNumber | varchar(50) | No | Unique asset number. Tidak diproses jika belum terdaftar. | EQUI-EQUNR | |
| assetStatus.status | varchar(20) | No | Status: 1. IN OPERATION, 2. IDLE, 3. RETIRED | JEST-STAT | EQUI-OBJNR = JEST-OBJNR where JEST-INACT = NULL And JEST-STAT = 'I*' |

**Response**:
- HTTP 200 - Success: `{"status":"success","totalData":1,"successCount":1,"failedCount":0,"results":[{"assetNumber":"BDCT10003","trDate":"2024-10-14T00:00:00+07:00"}]}`
- HTTP 200 - Partial Success: hasil per item, item gagal punya `errorCode` (contoh `ERR-0014`)
- HTTP 400: `status: "error"` dengan `errorCode` per item
- HTTP 403: `ERR-0006`
- HTTP 500: `ERR-0007`

### 6.3 Material

#### 6.3.1 Material

**Description**: Upsert material — matched by `materials.materialNumber`. Mendukung single & bulk.

| | |
| --- | --- |
| **API Endpoint** | `base_url/material` |
| **Method** | POST |

**Request**

```json
{
  "materials": [
    {
      "materialNumber": "01-085785-9",
      "materialName": "SLEEVE,SPECTRUM ADJUSTMENT,BR",
      "batchCode": "NEW",
      "siteCode": "1001",
      "sectionTypeCode": "OBH",
      "uomCode": "EA",
      "assetModelCode": "740C",
      "storageLocation": "WHA1",
      "currency": "USD",
      "map": 14.32,
      "mapLocalCurr": 234217.92,
      "stock": 25,
      "ranking": "E",
      "isActive": true
    }
  ]
}
```

| Field | Type | Nullable | Description | SAP Table | Remarks |
| --- | --- | --- | --- | --- | --- |
| materials | array | No | List of material records (bulk supported) | | |
| materials.materialNumber | varchar(200) | No | Unique material identifier | MARA-MATNR | |
| materials.materialName | varchar(200) | No | Material description/name | MARA-MAKTX | |
| materials.batchCode | varchar(64) | No | Batch identifier. Contoh: NEW, REPAIRED, string kosong | MBEW-BWTAR | MARA-MATNR = MBEW-MATNR |
| materials.siteCode | varchar(64) | No | Site tempat material berada. Tidak diproses jika belum terdaftar. | MBEW-BWKEY | |
| materials.sectionTypeCode | varchar(64) | No | Section type code. Tidak diproses jika belum terdaftar. | AUSP-ATWRT | 1) get equipment dari material master: AUSP-ATINN='EQP_MOD_OEM*' and AUSP-ATWRT=[material model]; 2) get hierarki (loader/hauler): AUSP-ATINN='EQP_MOD_HIR' and AUSP-OBJEK=[1] |
| materials.uomCode | varchar(64) | Yes | Unit of measurement. Tidak diproses jika belum terdaftar. | MARA-MEINS | |
| materials.assetModelCode | varchar(64) | Yes | Asset model code. Tidak diproses jika belum terdaftar. | AUSP-ATWRT | ATINN='MODEL_UNIT' |
| materials.storageLocation | varchar(64) | Yes | Storage location material | MARD-LGORT | |
| materials.currency | varchar(5) | Yes | Currency harga material | CKMLCR-WAERS | CKMLRCURTP=10 |
| materials.map | float | Yes | Moving average price / cost | CKMLCR-PVPRS | contoh 14.32 |
| materials.mapLocalCurr | float | Yes | Cost dalam local currency | CKMLCR-PVPRS | CKMLRCURTP=40 |
| materials.stock | float | Yes | Current stock quantity | MARD-LABST | |
| materials.ranking | varchar(64) | Yes | Ranking material (A, B, C, dst.) | MARC-MAABC | |
| materials.isActive | boolean | Yes | Activate/inactivate material. Optional, default true | MARC-LVORM | |

**Response**: pola sama (key `materialNumber`), HTTP 200/400/403(`ERR-0006`)/500(`ERR-0007`).

### 6.4 Backlog

#### 6.4.1 Backlog

**Description**: Registrasi **Pending Work Order** baru beserta material yang dibutuhkan, dalam satu langkah integrasi.

| | |
| --- | --- |
| **API Endpoint** | `base_url/backlog` |
| **Method** | POST |

**Request**

```json
{
  "backlogs": [
    {
      "moNumber": "1105152450",
      "moDescription": "Replace hose compressor",
      "siteCode": "1001",
      "assetNumber": "EXCT61016",
      "orderType": "MT01",
      "assetModelCode": "6015B",
      "assetTypeCode": "EXC",
      "maintenanceCategoryCode": "BEX",
      "maintenanceCategoryName": "Breakdown Excavator",
      "object": "IDLER LH",
      "reservationNumber": "1234567890",
      "moCreatedDate": "2024-01-08T08:00:00+07:00",
      "moCreatedBy": "SAP",
      "moUpdatedDate": "2024-01-08T09:00:00+07:00",
      "moUpdatedBy": "SAP",
      "moReleaseDate": "2024-01-09T08:00:00+07:00",
      "moTecoDate": null,
      "moClosedDate": null,
      "moPlanCost": 500000.00,
      "moActualCost": 0.00,
      "moStatus": "OPEN",
      "isActive": true,
      "materials": [
        {
          "materialNumber": "MAT-001",
          "materialName": "Hydraulic Hose",
          "batch": "NEW",
          "orderQuantity": 1.00,
          "uom": "PCS",
          "storageLocation": "WH01",
          "prStatus": "CREATED",
          "prNumber": "12345",
          "poNumber": "98765",
          "orderStatus": "OPEN",
          "grStatus": "PARTIAL",
          "grQuantity": 1.00,
          "grNumber": "77889",
          "giNumber": "77889",
          "giDate": "2024-01-10T08:00:00+07:00",
          "giStatus": "PARTIAL",
          "giQuantity": 1.00,
          "estCost": 500000.00,
          "isActive": true
        }
      ]
    }
  ]
}
```

**Header fields**

| Field | Type | Nullable | Description | SAP Table | Remarks |
| --- | --- | --- | --- | --- | --- |
| backlogs | array | No | List of MO backlog records (bulk supported) | | |
| backlogs.moNumber | varchar(12) | No | Unique MO number dari sistem eksternal | AUFK-AUFNR | |
| backlogs.moDescription | varchar(250) | No | Deskripsi pekerjaan maintenance | AUFK-KTEXT | |
| backlogs.siteCode | varchar(4) | No | Site/plant code. Numeric only 1–4 digit (mis. "1001"). Tidak diproses jika belum terdaftar. | AUFK-WERKS | |
| backlogs.assetNumber | varchar(20) | No | Identifier asset/equipment terkait. Data ditolak jika equipment belum terdaftar di Digiman+. | EQUI-EQUNR | |
| backlogs.orderType | varchar(20) | Yes | Maintenance order type (mis. MT01). Tidak diproses jika belum terdaftar. | AUFK-AUART | |
| backlogs.assetModelCode | varchar(50) | Yes | Asset model code | TBD — konfirmasi tim SAP | |
| backlogs.assetTypeCode | varchar(100) | Yes | Asset type code. Tidak diproses jika belum terdaftar. | EQUI-EQART | |
| backlogs.maintenanceCategoryCode | varchar(16) | No | Kode kategori maintenance activity (PM, BEX, dll). Tidak diproses jika belum terdaftar. | AFIH-ILART | AUFK-AUFNR = AFIH-AUFNR |
| backlogs.maintenanceCategoryName | varchar(100) | Yes | Nama kategori (pasangan maintenanceCategoryCode) | TBD — konfirmasi tim SAP | → PM Activity Type |
| backlogs.object | varchar(50) | Yes | Technical Object Type, Main Component | EQUI-EQART | AFIH-EQUNR = EQUI-EQUNR |
| backlogs.reservationNumber | varchar(19) | Yes | Reservation number. Numeric characters only. | TBD — konfirmasi tim SAP | Numeric only (^\d+$), Int64 |
| backlogs.moCreatedDate | datetime | No | Tanggal MO dibuat di source system, ISO 8601 | AUFK-ERDAT | |
| backlogs.moCreatedBy | varchar(100) | Yes | User/system pembuat MO | AUFK-ERNAM | |
| backlogs.moUpdatedDate | datetime | Yes | Tanggal MO terakhir diupdate | AUFK-AEDAT | |
| backlogs.moUpdatedBy | varchar(100) | Yes | User/system yang terakhir update MO | AUFK-AENAM | |
| backlogs.moReleaseDate | datetime | Yes | Tanggal MO dirilis untuk eksekusi | AFKO-FTRMI | AUFK-AUFNR = AFKO-AUFNR |
| backlogs.moTecoDate | datetime | Yes | Tanggal MO TECO (technically complete) | AUFK-IDAT2 | |
| backlogs.moClosedDate | datetime | Yes | Tanggal MO ditutup administratif | AUFK-IDAT3 | |
| backlogs.moPlanCost | decimal(18,2) | Yes | Planned/estimated cost | COSP-WTG* | AUFK-AUFNR = COSP-'*OBJNR', COSP-VRGNG = 'KPPP' |
| backlogs.moActualCost | decimal(18,2) | Yes | Actual cost | COSP-WTG* | AUFK-AUFNR = COSP-'*OBJNR', COSP-VRGNG = 'COIN' |
| backlogs.moStatus | varchar(100) | Yes | 1. OPEN, 2. RELEASED, 3. COMPLETED, 4. CLOSED, 5. DELETED | JEST-STAT | AUFK-OBJNR = JEST-OBJNR where JEST-INACT = NULL And JEST-STAT = 'I*' |
| backlogs.isActive | boolean | No | true = MO aktif, false = MO tidak aktif | JEST-STAT | True = I0001, I0002, I0045, I0046, atau I0327. False = I0043 |

**Material array fields (`backlogs.materials`)**

| Field | Type | Nullable | Description | SAP Table | Remarks |
| --- | --- | --- | --- | --- | --- |
| materials | array | Yes | List material terkait backlog | | |
| materials.materialNumber | varchar(50) | No | Identifier material | RESB-MATNR | RESB-AUFNR = AUFK-AUFNR |
| materials.materialName | varchar(100) | No | Deskripsi material | MAKT-MAKTX | MAKT-MATNR = RESB-MATNR |
| materials.batch | varchar(50) | No | Klasifikasi usage material (NEW, REPLACE, dll; bisa kosong) | RESB-CHARG | RESB-AUFNR = AUFK-AUFNR |
| materials.orderQuantity | decimal(18,2) | Yes | Quantity yang dipesan/direservasi | RESB-BDMNG | RESB-AUFNR = AUFK-AUFNR |
| materials.uom | varchar(50) | No | Unit of measure (PCS, EA, SET) | RESB-MEINS | RESB-AUFNR = AUFK-AUFNR |
| materials.storageLocation | varchar(50) | Yes | Storage location material | RESB-LGORT | RESB-AUFNR = AUFK-AUFNR |
| materials.prStatus | varchar(64) | Yes | Status Purchase Requisition (CREATED, APPROVED) | EBAN-FRGKZ | Lihat logika Release Strategy di dokumen asli |
| materials.prNumber | varchar(19) | Yes | Nomor Purchase Requisition. Numeric only. | EBAN-BANFN | EBAN-ZZ_AUFNR = AUFK-AUFNR |
| materials.poNumber | varchar(19) | Yes | Nomor Purchase Order. Numeric only. | EKKO-EBELN | Step 1: EBAN-BANFN where EBAN-ZZ_AUFNR = AUFK-AUFNR; Step 2: EKKO-EBELN = EBAN-EBELN |
| materials.orderStatus | varchar(16) | Yes | Status order terkait supply material | EKKO-FRGKE | Lihat logika Release Strategy di dokumen asli |
| materials.grStatus | varchar(64) | Yes | Status Goods Receipt | EKPO-ELIKZ | "FULL RECEIVED" jika EKPO-ELIKZ=X dan EKPO-LOEKZ=blank, else "PARTIAL" |
| materials.grQuantity | decimal(18,2) | Yes | Quantity diterima via Goods Receipt | MATDOC-MENGE | MATDOC-MBLNR = materials.giNumber |
| materials.grNumber | varchar(40) | Yes | Nomor dokumen Goods Receipt (free text) | MATDOC-MBLNR | MATDOC-EBELN = EKKO-EBELN where MATDOC-SMBLN=blank and MATDOC-CANCELLED=blank and MATDOC-BWART='101' |
| materials.giNumber | varchar(40) | Yes | Nomor dokumen Goods Issue (free text) | MATDOC-MBLNR | MATDOC-AUFNR = AUFK-AUFNR where MATDOC-SMBLN=blank and MATDOC-CANCELLED=blank and MATDOC-BWART='261' |
| materials.giDate | datetime | Yes | Tanggal transaksi Goods Issue, ISO 8601 | MATDOC-BUDAT + MATDOC-CPUTM | MATDOC-MBLNR = materials.giNumber |
| materials.giStatus | varchar(64) | Yes | Status Goods Issue (PARTIAL/COMPLETE) | RESB-KZEAR | Partial jika RESB-KZEAR != X; Complete jika RESB-KZEAR = X, where RESB-AUFNR = AUFK-AUFNR |
| materials.giQuantity | decimal(18,2) | Yes | Quantity issued via Goods Issue | MATDOC-MENGE | MATDOC-AUFNR = AUFK-AUFNR |
| materials.estCost | decimal(18,2) | Yes | Estimated cost material | COSP-WTG* | AUFK-AUFNR = COSP-'*OBJNR', COSP-VRGNG = 'KPPP' |
| materials.isActive | boolean | No | true/false status aktif material record | MARC-LVORM | |

**Response** (perhatikan key berbeda dari API lain: `totalRecords`/`successRecords`/`failedRecords`):

- HTTP 200 - Success:
```json
{"status":"success","totalRecords":1,"successRecords":1,"failedRecords":0,"results":[{"moNumber":"1105152450","status":"success"}]}
```
- HTTP 200 - Partial Success: item gagal punya `errorCode` (mis. `ERR-0002`)
- HTTP 400: `status:"error"` dengan `totalData/successCount/failedCount`
- HTTP 403: `ERR-0006`
- HTTP 500: `ERR-0007`

### 6.5 Breakdown Notification

#### 6.5.1 Breakdown Notification

**Description**: Upsert breakdown notification — matched by `breakdownNotifications.notification`; kalau sudah ada → update, kalau belum → create. Mendukung single & bulk. Hanya ada satu API (POST) untuk create maupun update.

| | |
| --- | --- |
| **API Endpoint** | `base_url/breakdown-notification` |
| **Method** | POST |

**Request**

```json
{
  "breakdownNotifications": [
    {
      "notification": "810002225968",
      "notificationStatus": "IN PROGRESS",
      "breakdownDescription": "Hydraulic hose leakage",
      "siteCode": "1001",
      "assetNumber": "DT777001",
      "assetModelCode": "777D",
      "breakdownType": "Unscheduled",
      "hmBreakdown": 58008.78,
      "breakdownStartDate": "2026-01-19T08:26:57+08:00",
      "breakdownEndDate": null,
      "rfuEstimateDate": "2026-01-19T17:00:00+08:00",
      "location": "TA BARAT",
      "isCloseBreakdown": false,
      "isActive": true
    }
  ]
}
```

| Field | Type | Nullable | Description | SAP Table | Remarks |
| --- | --- | --- | --- | --- | --- |
| breakdownNotifications | array | No | List of breakdown notification records (bulk supported) | | |
| breakdownNotifications.notification | Varchar(12) | No | Nomor notifikasi unik, wajib unik di sistem | QMEL-QMNUM | |
| breakdownNotifications.notificationStatus | Varchar(20) | No | 1. OPEN, 2. IN PROGRESS, 3. COMPLETED, 4. DELETED | JEST-STAT | QMEL-QMNUM = JEST-OBJNR where JEST-INACT = NULL And JEST-STAT = 'I*' |
| breakdownNotifications.breakdownDescription | Varchar(200) | No | Deskripsi kerusakan/kegagalan equipment | QMEL-QMTXT | |
| breakdownNotifications.siteCode | Varchar(4) | No | Site lokasi breakdown. Tidak diproses jika belum terdaftar. | QMIH-IWERK | QMEL-QMNUM = QMIH-QMNUM |
| breakdownNotifications.assetNumber | Varchar(25) | No | Identifier equipment. Data ditolak jika equipment belum terdaftar di Digiman+. | EQUI-EQUNR | |
| breakdownNotifications.assetModelCode | Varchar(40) | Yes | Asset model code. Tidak diproses jika belum terdaftar. | AUSP-ATWRT | EQUI-EQUNR = AUSP.OBJEK where ATINN = EQP_MOD_OEM* |
| breakdownNotifications.breakdownType | varchar (free text) | Yes | Free text — Digiman+ memetakan server-side: "Unscheduled" → tipe Unscheduled, nilai lain default ke tipe Breakdown | ZIDMBD-BDSUBTYP | QMEL-QMNUM = ZIDMBD-QMNUM |
| breakdownNotifications.hmBreakdown | Decimal(13,2) | Yes | Hour meter saat breakdown terjadi | ZIDMBD-HM_BD | QMEL-QMNUM = ZIDMBD-QMNUM |
| breakdownNotifications.breakdownStartDate | Datetime | No | Tanggal/waktu mulai breakdown, ISO 8601 dengan timezone | QMIH-VIQMEL + QMIH-AUZTV | QMEL-QMNUM = QMIH-QMNUM |
| breakdownNotifications.breakdownEndDate | Datetime | Yes | Tanggal/waktu breakdown selesai, ISO 8601 dengan timezone. Null jika breakdown belum selesai (`isCloseBreakdown` = false). | QMIH-AUSBS + QMIH-AUZTB | |
| breakdownNotifications.rfuEstimateDate | Datetime | Yes | Estimasi tanggal/waktu equipment kembali beroperasi (Ready For Use), ISO 8601 dengan timezone | ZIDMBD-RFUESTDATE1 | QMEL-QMNUM = ZIDMBD-QMNUM |
| breakdownNotifications.location | Varchar(200) | Yes | Lokasi breakdown dalam site operasional | - | contoh: TA BARAT |
| breakdownNotifications.isCloseBreakdown | Boolean | No | true = breakdown sudah selesai/finish dan ditutup (closed), false = masih berlangsung/terbuka (open) | ZIDMBD-ISSTATBD | QMEL-QMNUM = ZIDMBD-QMNUM |
| breakdownNotifications.isActive | boolean | No | Status validitas data record (bukan status breakdown). true = data valid/aktif, false = record sudah di-cancel/delete (tidak valid) | JEST-STAT | True = I0061; False = I0060 OR I0062 |

**Response**: pola sama seperti API lain (key `notification`), HTTP 200/400/403(`ERR-0006`)/500(`ERR-0007`).

---

## 7. Glossary — 7.1 Error Code

| Code | Description |
| --- | --- |
| ERR-0001 | The specified tenant code is not registered in the system master data. |
| ERR-0002 | The specified site code is not registered in the system master data. |
| ERR-0003 | The specified department code is not registered in the system master data. |
| ERR-0004 | The specified section code is not registered in the system master data. |
| ERR-0005 | A user with the same user code already exists in the system. |
| ERR-0006 | Access to this API is forbidden due to insufficient permissions. |
| ERR-0007 | An internal server error occurred while processing the request. |
| ERR-0008 | The specified asset type code is not registered in the system master data. |
| ERR-0009 | The specified asset class code is not registered in the system master data. |
| ERR-0010 | The specified asset variant code is not registered in the system master data. |
| ERR-0011 | The specified asset model code is not registered in the system master data. |
| ERR-0012 | The specified asset brand code is not registered in the system master data. |
| ERR-0013 | The specified asset category code is not registered in the system master data. |
| ERR-0014 | The specified equipment identifier is not registered in the system. |
| ERR-0015 | The specified batch code is not registered in the system master data. |
| ERR-0016 | The specified unit of measure (UOM) code is not registered in the system master data. |
| ERR-0017 | The specified user code is not registered in the system. |

---

*Last updated: 2026-08-05*
