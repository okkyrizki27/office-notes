# Issue Log — BUMA AU

Daftar issue seputar project BUMA AU, dipertukarkan lewat email antara BUMA (`@buma.com.au`) dan Bukit Technology Support (`@bukittechnology.com`). Issue yang belum punya tanggal raise resmi ditandai **Date Raised: TBD** di masing-masing dokumen — update begitu tersedia.

## Sumber Data & Keterbatasan

Timeline, ball-tracking, dan pause window SLA di issue-log ini **direkonstruksi dari email correspondence** (Outlook, dicetak/screenshot oleh Okky), **bukan** export langsung dari ITSM Tool (Jira Support Desk). `support@bukittechnology.com` saat ini **belum auto-sync** ke Jira (tidak ada email-to-ticket automation atau auto status change), jadi tidak ada jaminan timestamp/status di sini identik dengan yang tercatat di Jira untuk issue yang punya tiket.

Ini dipakai sebagai sumber acuan kerja untuk saat ini karena memang belum ada rekonsiliasi otomatis ke ITSM. Implikasinya:
- **Pause SLA** ditentukan dengan menilai isi tiap email terhadap 2 syarat di Schedule 3 klausul 3.2(d): (i) menunggu info/akses/approval dari BUMA AU, atau (ii) dependency pihak ketiga di luar kendali Bukit. ini penilaian manual kami berdasar isi korespondensi, bukan status field resmi yang di-toggle di tiket saat itu terjadi.
- Untuk issue yang **ada nomor Jira Ticket**-nya, kalau suatu saat perlu dipakai untuk dispute/laporan resmi ke BUMA, sebaiknya dicek-silang ke histori status tiket asli (created date, status transitions) — bisa saja berbeda dari yang direkonstruksi di sini.
- Untuk issue yang **belum ada nomor Jira Ticket** (ditandai "—" di tabel di bawah), belum ada rekaman formal di ITSM sama sekali per definisi kontrak klausul 3.2(a)(ii) — perlu dibuatkan tiket kalau mau menutup gap ini.

## Konvensi Pencatatan

- **Date Raised** = timestamp email **pertama** dalam thread yang me-raise issue tersebut, lengkap sampai jam (bukan tanggal saja). Arahnya menentukan siapa **Reported by**:
  - Default: `@buma.com.au` → `@bukittechnology.com` (BUMA lapor ke BukitTech) → Reported by = orang BUMA.
  - Bisa terbalik: kalau BukitTech proaktif menemukan/melaporkan issue duluan (`@bukittechnology.com` → `@buma.com.au`) → Reported by = orang BukitTech, Date Raised = timestamp email BukitTech itu.
- **Timezone default: WIB (UTC+7)** — timestamp "Sent"/"Date" di Outlook mengikuti timezone si *penerima/viewer* email (Jakarta), bukan timezone si pengirim. Jangan tebak timezone dari lokasi kantor pengirim (mis. BUMA Australia = AEST) — tetap pakai WIB kecuali dinyatakan lain.
- Kalau sumbernya berupa history email/thread, catat **timeline lengkap dengan jam** di tiap dokumen issue (bukan cuma ringkasan), plus tandai di setiap langkah **siapa yang sedang pegang bola** (BukitTech vs BUMA) — pakai field "Waiting On" dan/atau kolom "Ball moves to" di tabel timeline. Ini penting karena **SLA bisa di-pause** saat BukitTech menunggu konfirmasi/info dari BUMA (mis. WO number, screen recording) — tanpa detail jam + ball-tracking, durasi SLA efektif tidak bisa dihitung akurat.
- **Priority (P1–P4)** mengikuti definisi Schedule 3 §4.1 di [deed of variation](../new-agreement/deed%20of%20variation%20(terjemahan).md#41-definisi-prioritas): P1/P2 = fungsi kritis terganggu/hilang **tanpa** workaround yang layak; P3 = fungsi non-kritis terganggu, atau fungsi kritis terganggu **namun ada workaround**; P4 = dampak rendah/kosmetik. Item yang sebenarnya bukan Incident/Defect (Service Request, pertanyaan/inquiry) ditandai **N/A** — skema P1–P4 tidak berlaku untuk itu. P1/P2 clock jalan terus (termasuk weekend); P3/P4 clock hanya Hari/Jam Kerja.

| Issue | Priority | Status | Jira Ticket |
|---|---|---|---|
| [Error Uploading Parameter EHMS Master Data](ehms-master-data-upload-error.md) | P3 | UAT Done | [BAA-13509](https://bukittechnology.atlassian.net/browse/BAA-13509) |
| [Task Cylinder Height — Defect Not Created When Result Out of Spec](cylinder-height-defect-not-created.md) | N/A (working as designed) | Done | — |
| [IronPortal — Revert Filtering Data (Exclude Intervention Data Older Than 1 Year)](ironportal-revert-filtering-intervention-data.md) | P3 | Open | — |
| [Oil Changed Parameter Missing Since Move to API](oil-changed-parameter-missing-since-api-move.md) | P3 | Done | [BAA-13511](https://bukittechnology.atlassian.net/browse/BAA-13511) |
| [SOS Note — Escaped HTML Entities Not Rendered](sos-note-html-entity-rendering.md) | P4 | Done | [BAA-13512](https://bukittechnology.atlassian.net/browse/BAA-13512) |
| [IronForms Service Sheets Incorrectly Opened](ironforms-service-sheets-incorrectly-opened.md) | N/A (Service Request) | Done | — |
| [930E-4 Engine Downloads — Source Confirmation (Cummins / Hornets)](930e4-engine-downloads-hornets-source.md) | N/A (Inquiry) | Answered — Awaiting Benedict/BUMA decision | — |
| [IronForms 930E Electrical Service — Comm Brush Replace Button Error (a4–a8)](ironforms-930e-brush-replace-button-error.md) | P3 | Done | — |
| [IronPortal Historical Page — Slow Performance, No Data on Filter, Download All Error](ironportal-historical-slow-download-error.md) | N/A (Deprecated feature) | Done | — |
| [Blackwater — Clear Backlog of 598 Pending "Normal Interventions"](blackwater-normal-interventions-pending-evaluation.md) | N/A (Service Request) | Done | [BAA-13514](https://bukittechnology.atlassian.net/browse/BAA-13514) |
