# Digiman+ Current State

Dokumen ini merangkum kondisi arsitektur dan fitur Digiman+ saat ini sebagai dasar diskusi roadmap ke depan.

*Last updated: 2026-06-21*

---

## Feature Overview

| Fitur | Platform | Service | Status | Actor |
|-------|----------|---------|--------|-------|
| Digiplan | Web | `dplan` | Existing | Planner (scope saat ini: backlog execution) |
| PM Shutdown | Mobile | `maintenance-execution` | Existing | Supervisor, Foreman |
| Form Builder | Web | `maintenance-strategy` | Existing | Form Builder Engineer, Admin HO |
| Workflow Builder | Web | `workflow` | Planned (BE/DB only) | Form Builder Engineer, Admin HO |
| Form Submission | Mobile | `maintenance-execution` | Existing | User Site, Supervisor, Foreman, Mechanic |
| Approval | Mobile | - | Existing | User dengan akses menu approval |

---

## Service & Database

| Service | Database | Tipe | Keterangan |
|---------|----------|------|------------|
| `dplan` | dplan | - | Digiplan — perencanaan |
| `maintenance-execution` | maintenance-execution | SQL | Workorder, Task, submission data |
| `maintenance-execution` | maintenance-execution | Cosmos DB | Form submission per tab (JSON) |
| `maintenance-strategy` | Maintenance Strategy | SQL | Metadata form: nama, versioning, konfigurasi |
| `maintenance-strategy` | Maintenance Strategy | Cosmos DB | Form template dalam bentuk JSON |
| `workflow` | workflow | - | Workflow Builder |

---

## Scope Digiplan Saat Ini

Scheduled service plan yang dihandle `dplan` saat ini **hanya backlog execution**:
- **Backlog** = temuan hasil inspeksi
- Temuan tersebut dimasukkan ke dalam scheduled service untuk perbaikan (repair)

Artinya Digiplan belum menghandle jenis scheduled service selain backlog.

---

## Catatan Arsitektur

### PM Shutdown — Pure Proxy
PM Shutdown berada di service `maintenance-execution`, namun API-nya hanya membungkus API `dplan`. Tidak ada data PM Shutdown yang disimpan di database `maintenance-execution`. Seluruh data hidup di `dplan`.

Kondisi ini terjadi karena Digiplan awalnya dibangun sebagai aplikasi terpisah dari Digiman+. Perbaikan arsitektur ini membutuhkan effort yang sangat besar sehingga diputuskan untuk dipertahankan.

### Dua Database per Service
`maintenance-execution` dan `maintenance-strategy` keduanya menggunakan dua jenis database:
- **SQL** → data terstruktur, relasional, metadata
- **Cosmos DB** → dokumen JSON fleksibel (form template / form submission per tab)

---

## Data Structure — Form Submission

### SQL (`maintenance-execution`)
```
Workorder
  └── Task  (berisi FormSubmissionId)
        └── TaskPersonalized  ← data user yang submit
              └── TaskPersonalizedFinding
                        └── FindingEvidence
```

### Cosmos DB (`maintenance-execution`)
```
1 file JSON = 1 tab di dalam form
└── setiap file berisi FormSubmissionId
```

### Relasi SQL ↔ Cosmos
`Task.FormSubmissionId` ←→ `CosmosJSON.FormSubmissionId`

1 Task → N file JSON (N = jumlah tab di form)

---

## Integrasi Workflow ↔ Form

Konfigurasi integrasi dilakukan melalui table `BusinessOperationalForm` di `maintenance-execution` SQL.

---

## Flow — Form Submission & Approval

1. Admin HO membuat form di **Form Builder** (web)
2. Form dikonfigurasi agar muncul di menu **Form Submission** (mobile)
3. User yang memiliki akses memilih form dari list (self-service pooling)
4. User mengisi form dan submit — support **offline-first**
5. Satu form diisi oleh **satu user** dari awal sampai submit (single-user, linear)
6. Setelah submit → masuk ke **Approval Workflow**
7. Jumlah step approval ditentukan oleh konfigurasi workflow
8. Setelah semua step selesai → **Fully Approved**

---

## Catatan Penting untuk Diskusi Roadmap

- Offline-first adalah capability yang sudah ada dan harus dipertimbangkan di setiap diskusi fitur baru
- Form Submission saat ini bersifat single-user linear — tidak ada kolaborasi atau handoff antar user dalam satu form
- Form Submission bersifat self-service pooling — user memilih sendiri, tidak di-assign per instance
- `maintenance-execution` menjadi titik temu antara `workflow` dan `maintenance-strategy`
- Workflow Builder masih dalam tahap awal (BE/DB only) — belum ada UI
