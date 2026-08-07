# Maintiva — Product Ecosystem & Rebrand

Dokumen ini merekam diskusi awal soal **Maintiva**: rebrand & perluasan Digiman+ menjadi platform enterprise yang lebih besar. Isinya masih tahap visi/business & UX — belum masuk pembahasan teknis (arsitektur/implementasi menyusul di diskusi berikutnya).

*Last updated: 2026-08-07*

---

## Konteks

Digiman+ akan direbrand menjadi bagian dari **Maintiva Platform** — bukan diganti, tapi dibesarkan cakupannya:

- **Maintiva** = brand payung (umbrella) untuk seluruh ekosistem produk.
- **Digiman+** menjadi salah satu produk di dalamnya, dengan nama baru **Maintiva Core**.
- Sebagian produk lain di ekosistem (lihat tabel di bawah) **sudah ada di tempat lain saat ini** dan perlu dimigrasi/diintegrasi ke bawah payung Maintiva — belum dirinci produk mana saja & statusnya (menyusul).

Referensi visual: diagram "Product Ecosystem" (dibagikan user, 2026-08-07) — belum disimpan sebagai file di repo ini, hanya jadi acuan diskusi.

---

## Struktur Produk

| Produk | Kategori | Fungsi |
|---|---|---|
| **Maintiva Core** *(ex-Digiman+)* | Asset & Work Management | Asset registry & hierarchy, work order management, preventive maintenance, inventory & spare parts, technician & contractor mgmt, maintenance planning & scheduling |
| **Maintiva Pulse** | Asset Health Monitoring System | Real-time condition monitoring, health scoring & degradation tracking, anomaly detection, component diagnostics, health trends & alerts |
| **Maintiva Agent** | AI Virtual Agent (Analysis & RCA) | AI-powered analysis & correlation, Root Cause Analysis (RCA), knowledge learning engine, natural language assistant, rekomendasi & next-best actions |
| **Maintiva Predict** | Failure & Risk Prediction | Failure prediction, risk scoring & forecasting, Remaining Useful Life (RUL), what-if scenario analysis, proactive maintenance recommendations |
| **Maintiva Insight** | Reporting & Business Intelligence | Interactive dashboards, KPI & performance monitoring, custom reports, trend & analytics views, executive & operational visibility |
| **Maintiva Config** | Configuration & Low-Code Platform | Form Builder, Workflow Builder, CBM Configuration, Maintenance Strategy Builder, Business Rules Engine, Notification & Alert Configuration, Role & Permission Management, UI & Master Data Configuration |
| **Maintiva Connect** | Data Platform & Integration Hub | Unify & govern data lintas sumber (SAP/ERP, CMMS/EAM, IoT Sensors, SCADA, Historian, MES, Mobile Apps, Excel/CSV, REST API, third-party systems) |

## Akses per Persona (dari diagram)

| Persona | Produk yang diakses |
|---|---|
| HQ Asset Management Team (Strategy, Planning & Oversight) | Core, Pulse, Agent, Predict, Insight *(full suite)* |
| Mechanics, Fitters, Supervisors (Execution & Feedback) | Core, Insight |
| HQ Site Reliability Engineers (Reliability & Performance Improvement) | Pulse, Predict, Agent, Insight *(tanpa Core)* |

Belum dikonfirmasi apakah pembagian akses ini final atau masih indikatif dari diagram positioning saja.

---

## Keputusan & Constraint yang Sudah Dipegang

- **Diskusi Maintiva difokuskan ke business & UI/UX dulu** — pembahasan teknis (arsitektur, data model, integrasi) sengaja ditunda ke sesi berikutnya.
- **Constraint "not SAP-minded" tetap berlaku** ([[digiman-not-sap-minded]]): core model Maintiva (khususnya Core/ex-Digiman+) tetap dirancang standalone, SAP hanya jadi salah satu titik integrasi (lewat Connect) — bukan pusat model data. Constraint ini dikonfirmasi user masih berlaku walau saat ini **belum tercapai** di implementasi existing.
- Sebagian produk ekosistem (di luar Core) **sudah eksis di tempat lain** — perlu proses migrasi/integrasi, bukan full-greenfield build. Detail per-produk belum dibahas.

---

## Index Dokumen

- [homepage-landing-page.md](homepage-landing-page.md) — diskusi homepage platform (logged-in) & struktur marketing/landing page (logged-out), model Jira/Atlassian/Lark

---

## Open Items (untuk diskusi berikutnya)

1. Inventarisasi produk yang sudah eksis di luar Digiman+ (Pulse/Agent/Predict/Insight/Config/Connect) — apa saja, siapa user-nya sekarang, statusnya seperti apa.
2. Konfirmasi apakah pembagian akses per-persona di diagram sudah final.
3. Apakah rebrand Digiman+ → Maintiva Core hanya penamaan internal, atau customer-facing juga berubah (logo, login screen, nama app).
