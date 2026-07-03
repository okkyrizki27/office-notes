# Digiman+ Current State

Dokumen ini merangkum kondisi arsitektur dan fitur Digiman+ saat ini sebagai dasar diskusi roadmap ke depan.

*Last updated: 2026-06-23*

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
| `maintenance-execution` | `cst-iams-sqldb-maintenance-execution` | SQL | Workorder, Task, submission data |
| `maintenance-execution` | `MaintenanceExecution` | Cosmos DB | Form submission per tab (JSON) |
| `maintenance-strategy` | `cst-iams-sqldb-maintenance-strategy` | SQL | Metadata form: nama, versioning, konfigurasi |
| `maintenance-strategy` | `MaintenanceStrategy` | Cosmos DB | Form template dalam bentuk JSON (per tab) |
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

## Form

- [Form Builder](form/form-builder.md) — tabel SQL, schema Form & FormAssetAssignment, versioning, Cosmos DB, Form Type
- [Form Submission](form/form-submission.md) — data structure submission, flow submission & approval

---

## Integrasi Workflow ↔ Form

Konfigurasi integrasi dilakukan melalui table `BusinessOperationalForm` di `maintenance-execution` SQL.

---

## Homepage

- [Homepage Revamp](homepage/homepage-revamp.md) — sections, formula count Needs Attention, kriteria per kategori (Inspection / PM Shutdown / BD Corrective), Settings, permission (post Release 4.0.0)

---

## PM Shutdown & BD Corrective

- [Workcard Sync Logic](pm-shutdown-bd-corrective/workcard-sync-logic.md) — logic pengambilan data workcard list (fresh install vs after last sync)
- [PM Shutdown Page Revamp](pm-shutdown-bd-corrective/pm-shutdown-page-revamp.md) — kriteria data list, perubahan filter, permission (post Release 4.0.0)
- [BD Corrective Page Revamp](pm-shutdown-bd-corrective/bd-corrective-page-revamp.md) — kriteria data list, perubahan filter, permission (post Release 4.0.0)
- [Outstanding Administration](pm-shutdown-bd-corrective/outstanding-administration.md) — sub-fitur di PM Shutdown & BD Corrective: kriteria data outstanding task, filter Settings, permission scope

---

## Catatan Penting untuk Diskusi Roadmap

- Offline-first adalah capability yang sudah ada dan harus dipertimbangkan di setiap diskusi fitur baru
- Form Submission saat ini bersifat single-user linear — tidak ada kolaborasi atau handoff antar user dalam satu form
- Form Submission bersifat self-service pooling — user memilih sendiri, tidak di-assign per instance
- `maintenance-execution` menjadi titik temu antara `workflow` dan `maintenance-strategy`
- Workflow Builder masih dalam tahap awal (BE/DB only) — belum ada UI
