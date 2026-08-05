# Digiman+ Integration API — Employee

> Diambil dari: [digiman-integration-interface-spec-mkp.md](digiman-integration-interface-spec-mkp.md) (section 2.3, 2.4, 6.1, 7.1)

## Authentication

- Semua request wajib menyertakan API Key yang valid di header **`X-API-Key`**. Request tanpa API Key valid akan ditolak.
- API Key di-provide oleh tim Digiman+ (client tidak generate sendiri).
- Akses API juga dibatasi via **IP Whitelisting** — hanya request dari IP yang sudah didaftarkan (per environment: UAT & Production) yang diizinkan. Request dari IP yang tidak di-whitelist akan diblokir di level network.

## Base URL

| Environment | Base URL |
| --- | --- |
| Dev | `https://cst-shared-apm-dev-001.azure-api.net/integration/external-integration/` |

> UAT & Production: belum tersedia (TBD).

## Employee

**Description**: Upsert employee — matched by `employees.userCode`; kalau sudah ada → update, kalau belum → create. Mendukung single & bulk submission.

> **Catatan:** integrasi ini sebelumnya bernama "User" — endpoint dan root field JSON berubah dari `user`/`users` menjadi `employee`/`employees`. Field `userCode` tetap dipertahankan namanya (tidak berubah jadi `employeeCode`).

| | |
| --- | --- |
| **API Endpoint** | `base_url/employee` |
| **Method** | POST |
| **Header** | `Content-Type: application/json`, `X-API-Key: {api_key}` |

### Request

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
| employees.sectionCode | varchar(64) | No | Section identifier. Jika kode belum terdaftar, akan otomatis di-insert ke master data. |
| employees.sectionName | varchar(64) | No | Section name |
| employees.isActive | boolean | No | true = active, false = inactive |

### Response

**HTTP 200 - Success**

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

**HTTP 200 - Partial Success**

```json
{
  "status": "success",
  "totalData": 2,
  "successCount": 1,
  "failedCount": 1,
  "results": [
    { "userCode": "mkpinspector01@protonmail.com", "status": "success" },
    { "userCode": "mkpinspector02@protonmail.com", "status": "failed", "errorCode": "ERR-0001" }
  ]
}
```

**HTTP 400**

```json
{
  "status": "error",
  "totalData": 1,
  "successCount": 0,
  "failedCount": 1,
  "results": [
    { "userCode": "mkpinspector01@protonmail.com", "status": "failed", "errorCode": "ERR-0001" }
  ]
}
```

**HTTP 403**: `{ "errorCode": "ERR-0006" }`

**HTTP 500**: `{ "errorCode": "ERR-0007" }`

### Error Codes (relevan untuk Employee API)

| Code | Description |
| --- | --- |
| ERR-0001 | The specified tenant code is not registered in the system master data. |
| ERR-0003 | The specified department code is not registered in the system master data. |
| ERR-0004 | The specified section code is not registered in the system master data. |
| ERR-0005 | A user with the same user code already exists in the system. |
| ERR-0006 | Access to this API is forbidden due to insufficient permissions. |
| ERR-0007 | An internal server error occurred while processing the request. |
| ERR-0017 | The specified user code is not registered in the system. |

---

*Last updated: 2026-08-05*
