# Order Integration — Requirement Discussion Checklist

Framework diskusi requirement Phase 2 Order Integration, dipecah jadi beberapa topik supaya diskusi tidak melebar dari konteks. Centang langsung di tempat kalau topik sudah dibahas tuntas & clear — bukan daily/outstanding task list, jadi tidak perlu dipindah ke section terpisah.

Urutan dikelompokkan jadi 6 fase berdasarkan dependency — fase awal menentukan scope & aktor, masuk ke jantung data model, lalu proses/workflow, integrasi, dan terakhir dashboard (baca dari hasil akhir semua keputusan sebelumnya).

*Last updated: 2026-08-13*

---

## Fase A — Scope & Trigger
*Apa saja yang bisa memicu Finding*

- [ ] **1. UI create defect/crack** — screen "Defect Identified", trigger per TaskKit/Question. Lihat [Poin 1](order-integration.md#poin-1-trigger-dan-ui-create-defect-atau-crack) — termasuk diskusi berjalan soal `IsImmediateExecutable` sebagai gate Order.
- [x] **2. Defect di luar pertanyaan form ("additional defect" saat eksekusi)** — final: mekanisme baru "Add Finding", nempel ke `TaskPersonalized` aktif dengan `FormTaskCode`/`FormSubmissionTabId`/`FormTaskNumber` NULL (skema sudah mendukung, tanpa perubahan). Sisa: UI entry-point khusus, tercatat di [Poin 1](order-integration.md#poin-1-trigger-dan-ui-create-defect-atau-crack) (UI View detail). Detail: [Poin 2](order-integration.md#poin-2-defect-di-luar-pertanyaan-form-additional-defect-saat-eksekusi).

## Fase B — Aktor

- [ ] **3. Permission/Role clarity** — siapa bisa create Finding (semua mechanic assign ke form?), siapa Foreman/Supervisor (form approval) vs Planner (Order approval), apakah bisa rangkap.

## Fase C — Data Model
*Jantung diskusi, paling banyak keputusan*

- [ ] **4. Offline behavior create Finding/Order** — apakah create Finding (yang trigger Order) perlu pola offline-first seperti fitur Phase 1 lainnya (submit offline → queue → sync). Cross-cutting dengan poin 1 & 5, ditaruh di sini karena scope trigger dari Fase A sudah lengkap.
- [ ] **5. Data flow of defect/crack** (Defect, Monitored Crack, Crack) — termasuk material handling, evidence/foto carry-over ke Order, dan konfirmasi multi-Finding dalam 1 pertanyaan (Tab Finding #1/#2, sudah ada di UI) tetap independen jadi eMOL masing-masing. Lihat [Poin 5](order-integration.md#poin-5-data-flow-defect-dan-crack).
- [x] **6. Duplicate/correlation handling** — correlation key = Asset + Component + SubComponent + DamageCode; sistem suggest kandidat, human (siapapun yang kerjakan form) yang pilih & validasi; Order lama tidak diubah, cukup di-close & sync SAP. Detail: [Poin 6](order-integration.md#poin-6-duplicate-atau-correlation-handling).
- [ ] **7. Editability window sebelum approval** — bisakah mechanic edit Finding miliknya sendiri (mis. salah ketik Defect Notes) setelah submit tapi sebelum diproses Planner. Beda dari poin 10 (Reject) — ini koreksi mandiri, bukan penolakan approver.
- [ ] **8. Cancel/Delete Finding** — pembatalan total Finding (mechanic salah identifikasi/false positive). Skema `TaskPersonalizedFinding.DeleteNotes`/`MechanicOrderList.DeleteReason` sudah ada, perlu diperjelas kapan dipakai.

## Fase D — Proses/Workflow

- [ ] **9. Approval of Defect/Crack** — Lihat [Poin 9](order-integration.md#poin-9-approval-flow). Butuh role dari Fase B + data model dari Fase C.
- [ ] **10. Reject/rework flow** — apa yang terjadi kalau Finding ditolak Foreman/Supervisor (form approval) atau Order ditolak Planner (sebelum SAP): status Rejected, bisa resubmit atau tidak. Cabang dari poin 9.
- [ ] **11. Notification** — siapa di-notify kapan: Planner tahu ada Order baru yang perlu direview, mechanic tahu Finding/Order-nya ditolak (poin 10).

## Fase E — Integrasi

- [ ] **12. SAP/ERP Integration** — Lihat [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) sebagai baseline flow existing. Baca dari Order yang sudah di-approve (Fase D).
- [ ] **13. MO Backlog re-entry loop** — perlakuan khusus saat Order dari flow ini kembali sebagai MO Backlog dari SAP (lihat [Bagian 9](../../architecture/inspection-order/order-emol-sap-sync.md#9-mo-backlog--inbound-flow-sap--digiman)), dibanding Order dari sumber lain.

## Fase F — Dashboard

- [ ] **14. Dampak ke Dashboard** — belum ada dokumen acuan, perlu digali dari nol. Baca dari hasil akhir semua keputusan di fase sebelumnya.
