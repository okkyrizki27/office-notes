# Digiman+ Architecture — Enhancement Catalog

*Last updated: 2026-07-21*

Index ini melacak semua dokumen **enhancement/proposal** di bawah `digiman+/architecture/` — supaya begitu jumlahnya bertambah, status pending/in-progress/partial tidak hilang di antara dokumen reference (schema, permission, current-state, dsb).

**Di luar scope index ini:** `digiman+/roadmap/` sudah punya sistem tracking sendiri (README per phase folder) — tidak didobel di sini.

**Belum ada di index ini:** kolom Related Jira — menyusul setelah struktur ini stabil.

---

## Status Legend

| Status | Arti |
|---|---|
| 📝 Internal Draft | Sudah ditulis, belum divalidasi ke tim technical dan/atau belum dikonfirmasi ke business/client |
| 📤 Proposed | Sudah dikirim ke stakeholder/client (email/proposal), menunggu approval |
| ✅ Confirmed (Business) | Keputusan/scope sudah disepakati di meeting business/client |
| 🔨 In Progress | Development berjalan |
| ◐ Partially Done | Sebagian scope selesai & live, sisanya masih pending |
| ✔️ Done | Selesai & live di production |
| ⏸️ Deferred | Sengaja ditunda (bukan dibatalkan) |

---

## Catalog

### Area of Unit & Man Power *(initiative gabungan, 3 dokumen enhancement)*

**Client:** BUMA — PIC Sunardi

| Dokumen | Fitur/Service | Status | Last Updated |
|---|---|---|---|
| [inspection-order/area-of-unit-man-power-enhancement.md](inspection-order/area-of-unit-man-power-enhancement.md) | Inspection, Order, Approval Order | ✅ Confirmed (Business) | 2026-07-20 |
| [dplan/man-power-man-hours-excel-enhancement.md](dplan/man-power-man-hours-excel-enhancement.md) | Digiplan (Excel template) | ✅ Confirmed (Business) | 2026-07-10 |
| [pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md](pm-shutdown-bd-corrective/man-power-duration-visibility-enhancement.md) | PM Shutdown, BD Corrective | ✅ Confirmed (Business) | 2026-07-20 |

- Effort estimate gabungan: [area-of-unit-man-power-effort-summary.md](area-of-unit-man-power-effort-summary.md) (2026-07-20)
- Client proposal terkirim: `area-of-unit-enhancement-proposal.html/pdf`, `man-power-duration-enhancement-proposal.html/pdf` (2026-07-21)

### Maintenance Activity Type & Integrasi Inspection→Order

**Client:** BUMA — PIC Sunardi

| Dokumen | Status | Last Updated |
|---|---|---|
| [inspection-order/maintenance-activity-type-enhancement.md](inspection-order/maintenance-activity-type-enhancement.md) | ✅ Confirmed (Business) | 2026-07-17 |

- Effort estimate: [inspection-order/maintenance-activity-type-effort-summary.md](inspection-order/maintenance-activity-type-effort-summary.md) — 48 SP (2026-07-20)
- Client proposal terkirim: `inspection-order/maintenance-activity-type-effort-proposal.html/pdf` (2026-07-21)

### Workcard Sync Improvement

**Client:** BUMA — PIC Sunardi

| Dokumen | Status | Last Updated |
|---|---|---|
| [pm-shutdown-bd-corrective/workcard-sync-logic.md](pm-shutdown-bd-corrective/workcard-sync-logic.md) | ✅ Confirmed (Business) — disetujui Uda Sunardi via email 2026-07-06 10:45 | 2026-07-21 |

- Client export: `pm-shutdown-bd-corrective/workcard-sync-improvement.html`, `Workcard_Sync_Improvement.pdf` (2026-07-03)

### Storage Location & Planner Group *(dibundel — 2 enhancement kecil, 1 rilis/sprint)*

**Client:** MKP (kedua enhancement) — Storage Location diimplementasi tanpa toggle per-tenant, jadi berlaku semua tenant

| Dokumen | Fitur/Service | Status | Last Updated |
|---|---|---|---|
| [inspection-order/storage-location-planner-group-enhancement.md](inspection-order/storage-location-planner-group-enhancement.md) *(Bagian A)* | Create Order — material picker "Add Part": tampil & simpan Sloc | 📝 Internal Draft | 2026-07-21 |
| [inspection-order/storage-location-planner-group-enhancement.md](inspection-order/storage-location-planner-group-enhancement.md) *(Bagian B)* | Order Approval (Planner Group) | 📝 Internal Draft — 2 opsi disiapkan untuk proposal, menunggu konfirmasi tim SAP MKP | 2026-07-21 |

- Effort estimate gabungan: [inspection-order/storage-location-planner-group-effort-summary.md](inspection-order/storage-location-planner-group-effort-summary.md) — **23 SP / ~27 mandays / 1 sprint** (Storage Location 9 + Planner Group Opsi 2 14; Opsi 1 = 0), baseline BUMA ID; **~3 sprint** kalau tim baru "BUMA ID Modified" (2026-07-21)
- Client proposal (draft): `inspection-order/storage-location-planner-group-proposal.html` / `.pdf` (2026-07-21)

### Form / IIR External API Integration

**Client:** BUMA - PIC Vicky Setiawan

| Dokumen | Status | Last Updated |
|---|---|---|
| [form/form-iir-external-api-design.md](form/form-iir-external-api-design.md) | 📝 Internal Draft (dinyatakan eksplisit di dokumen: "belum diimplementasi") | 2026-07-13 |

---

## Reference Docs (bukan enhancement, tidak ditrack di sini)

Dokumen berikut sengaja **tidak** masuk katalog karena isinya deskripsi kondisi *sekarang* (current-state/reference), bukan proposal yang pending:

- `current-state.md`, `permission.md`, `workflow.md`
- `database/*-schema.md`, `database/new-model-checklist.md`, `database/sap-material-integration.md`
- `form/form-builder.md`, `form/form-submission.md`, `form/IIR-Form-Submission-API-Documentation.*`
- `inspection-order/order-emol-sap-sync.md` *(eksplisit ditandai "referensi teknis, bukan dokumen enhancement" di effort summary)*
- `homepage/homepage-revamp.md`, `pm-shutdown-bd-corrective/bd-corrective-page-revamp.md`, `pm-shutdown-bd-corrective/pm-shutdown-page-revamp.md`, `pm-shutdown-bd-corrective/outstanding-administration.md` — meski namanya mengandung "revamp", isinya "Current State" pasca-release 4.0.0 (sudah live, sudah ada referensi Jira yang closed)

---

## Observasi dari Penyusunan Index Ini

1. **Penamaan "-revamp.md" ambigu** — tiga dokumen di `pm-shutdown-bd-corrective/` dan `homepage/` pakai suffix "-revamp" tapi isinya current-state (sudah selesai), bukan proposal pending. Kalau nanti ada enhancement baru dengan pola nama serupa, ini berpotensi bikin bingung mana yang pending vs sudah live — pertimbangkan konvensi nama yang lebih eksplisit (mis. `-current-state.md` vs `-enhancement.md`).

*(2 observasi lain — status basi di `maintenance-activity-type-enhancement.md` dan `workcard-sync-logic.md` — sudah dikonfirmasi & header dokumen sumbernya sudah disinkronkan, 21 Jul 2026.)*

---

## Cara Menjaga Index Ini Tetap Akurat

- Setiap kali status sebuah enhancement berubah (mis. dari Internal Draft → Proposed, atau Confirmed → In Progress), update kolom Status di tabel yang relevan.
- Setiap kali membuat dokumen enhancement baru, tambahkan baris ke tabel initiative yang sesuai (atau bikin section initiative baru kalau belum ada).
- Kolom Related Jira akan ditambahkan menyusul.
