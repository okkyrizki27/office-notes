# Order Integration — Requirement Discussion Checklist

Framework diskusi requirement Phase 2 Order Integration, dipecah jadi beberapa topik supaya diskusi tidak melebar dari konteks. Centang langsung di tempat kalau topik sudah dibahas tuntas & clear — bukan daily/outstanding task list, jadi tidak perlu dipindah ke section terpisah.

Urutan dikelompokkan jadi 6 fase berdasarkan dependency — fase awal menentukan scope & aktor, masuk ke jantung data model, lalu proses/workflow, integrasi, dan terakhir dashboard (baca dari hasil akhir semua keputusan sebelumnya).

*Last updated: 2026-08-11*

---

## Fase A — Scope & Trigger
*Apa saja yang bisa memicu Finding*

- [ ] **1. UI create defect/crack** — screen "Defect Identified", trigger per TaskKit/Question. Lihat [Current State — Mobile App UI](order-integration.md#current-state--mobile-app-ui-v400).
- [ ] **2. Defect di luar pertanyaan form ("additional defect" saat eksekusi)** — mechanic ketemu defect yang tidak ada pertanyaan relevannya di form yang sedang dikerjakan. Pakai flow Additional Order existing (terpisah, tanpa konteks WorkOrder/Task), atau perlu mekanisme baru "Add Finding" di dalam form yang tetap link ke WorkOrder/Task berjalan? Ini persis skenario asal Phase 2 ("field team menemukan pekerjaan tak terduga").

## Fase B — Aktor

- [ ] **3. Permission/Role clarity** — siapa bisa create Finding (semua mechanic assign ke form?), siapa Foreman/Supervisor (form approval) vs Planner (Order approval), apakah bisa rangkap.

## Fase C — Data Model
*Jantung diskusi, paling banyak keputusan*

- [ ] **4. Offline behavior create Finding/Order** — apakah create Finding (yang trigger Order) perlu pola offline-first seperti fitur Phase 1 lainnya (submit offline → queue → sync). Cross-cutting dengan poin 1 & 5, ditaruh di sini karena scope trigger dari Fase A sudah lengkap.
- [ ] **5. Data flow of defect/crack** (Defect, Monitored Crack, Crack) — termasuk material handling, evidence/foto carry-over ke Order, dan konfirmasi multi-Finding dalam 1 pertanyaan (Tab Finding #1/#2, sudah ada di UI) tetap independen jadi eMOL masing-masing. Lihat [Crack Order Lifecycle](order-approval-flow.md#crack-order-lifecycle).
- [ ] **6. Duplicate/correlation handling** — correlation key untuk "temuan yang sama" (Asset + Component + SubComponent?) — foundational untuk keputusan reuse-Order di Crack Lifecycle yang sudah ditulis di poin 5, sengaja dibahas setelahnya karena butuh gambaran umum data flow dulu.
- [ ] **7. Editability window sebelum approval** — bisakah mechanic edit Finding miliknya sendiri (mis. salah ketik Defect Notes) setelah submit tapi sebelum diproses Planner. Beda dari poin 10 (Reject) — ini koreksi mandiri, bukan penolakan approver.
- [ ] **8. Cancel/Delete Finding** — pembatalan total Finding (mechanic salah identifikasi/false positive). Skema `TaskPersonalizedFinding.DeleteNotes`/`MechanicOrderList.DeleteReason` sudah ada, perlu diperjelas kapan dipakai.

## Fase D — Proses/Workflow

- [ ] **9. Approval of Defect/Crack** — Lihat [Approval Flow](order-approval-flow.md#approval-flow). Butuh role dari Fase B + data model dari Fase C.
- [ ] **10. Reject/rework flow** — apa yang terjadi kalau Finding ditolak Foreman/Supervisor (form approval) atau Order ditolak Planner (sebelum SAP): status Rejected, bisa resubmit atau tidak. Cabang dari poin 9.
- [ ] **11. Notification** — siapa di-notify kapan: Planner tahu ada Order baru yang perlu direview, mechanic tahu Finding/Order-nya ditolak (poin 10).

## Fase E — Integrasi

- [ ] **12. SAP/ERP Integration** — Lihat [order-emol-sap-sync.md](../../architecture/inspection-order/order-emol-sap-sync.md) sebagai baseline flow existing. Baca dari Order yang sudah di-approve (Fase D).
- [ ] **13. MO Backlog re-entry loop** — perlakuan khusus saat Order dari flow ini kembali sebagai MO Backlog dari SAP (lihat [Bagian 9](../../architecture/inspection-order/order-emol-sap-sync.md#9-mo-backlog--inbound-flow-sap--digiman)), dibanding Order dari sumber lain.

## Fase F — Dashboard

- [ ] **14. Dampak ke Dashboard** — belum ada dokumen acuan, perlu digali dari nol. Baca dari hasil akhir semua keputusan di fase sebelumnya.
