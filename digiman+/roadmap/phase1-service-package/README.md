# Phase 1 — PM Shutdown Service Package

Index dokumen phase 1: menghadirkan **package form** (Service Sheet, Welding Form, RTO, dll.) ke PM Shutdown — sebelumnya PM Shutdown cuma handle backlog execution, tanpa dokumentasi terstruktur untuk pekerjaan selama service berlangsung.

*Last updated: 2026-08-06*

---

## Dokumen

| Dokumen | Topik | Last Updated |
|---|---|---|
| [pm-shutdown-service-package.md](pm-shutdown-service-package.md) | Konsep Service Package, peran Planner, Choose Form Modal (UI), mandatory vs additional form | 2026-06-26 |
| [pm-shutdown-form-execution.md](pm-shutdown-form-execution.md) | Eksekusi form: multi-mechanic collaboration, conflict resolution (optimistic locking, first-write-wins), sync mechanism, submit flow, Finish Execution gate | 2026-06-22 |
| [pm-shutdown-data-model.md](pm-shutdown-data-model.md) | Perubahan schema (`PlanForm` baru, `Task`/`TaskPersonalized`/`FormSubmission`), SUBMIT flow lintas service (dplan → maintenance-execution via Service Bus, Outbox Pattern) | 2026-06-22 |
| [pm-shutdown-mechanic-activity.md](pm-shutdown-mechanic-activity.md) | Activity tracking per mechanic (`TaskPersonalizedLog` + shift), trigger Start/Finish, auto-close, simulasi 13 skenario | 2026-06-22 |
| [pm-shutdown-mechanic-identity.md](pm-shutdown-mechanic-identity.md) | Keputusan: individual account per mechanic (vs shared account per section) | 2026-06-22 |
| [PRD-PM-Shutdown-Phase1.html](PRD-PM-Shutdown-Phase1.html) | PRD formal — konsolidasi dokumen-dokumen di atas | — |

---

## Status Ringkas

Desain sudah matang — sebagian besar keputusan di dokumen-dokumen di atas ditandai ✅ Dikonfirmasi. Item yang sengaja **di-defer ke MVP berikutnya**:

- Modifikasi package dari lapangan (field) — [pm-shutdown-service-package.md](pm-shutdown-service-package.md#open-items)
- Form reopen setelah submit — [pm-shutdown-form-execution.md](pm-shutdown-form-execution.md#edge-cases--decisions)
- **Skenario field team menemukan pekerjaan tak terduga** — jadi latar belakang [phase 2 (Order Integration)](../phase2-order-integration/)

## Catatan

- `pm-shutdown-form-behavior.md` (dokumen field validation/attachment behavior) sempat direncanakan di phase 1 tapi dihapus 2026-08-06, dinyatakan tidak relevan untuk saat ini — referensi ke dokumen ini di `pm-shutdown-form-execution.md` sudah disesuaikan.
