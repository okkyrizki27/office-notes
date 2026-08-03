# Timeline Delivery — Digital Service Sheet (Digiman+)

*Terakhir diperbarui: 2026-08-03*

---

Dokumen ini merinci timeline delivery untuk **Digital Service Sheet** — Service Package, Form Input/Submission Behavior, Finding Form (Order Creation) Integration, CBM Task, Approval Workflow Integration, dan EHMS Integration — dengan target go-live **24 September 2026**.

**Gantt chart interaktif**: [claude.ai/code/artifact/ae32f370-e42b-4ef5-a271-4bbd79ab24d9](https://claude.ai/code/artifact/ae32f370-e42b-4ef5-a271-4bbd79ab24d9) — hover tooltip per item, dark mode. Update Artifact ini (bukan bikin baru) kalau ada perubahan timeline.

## Ringkasan

| | |
|---|---|
| **Mulai** | 25 Juni 2026 — selaras dengan sprint `S2 IAMS` |
| **Target Go-Live** | 24 September 2026 |
| **Durasi total** | 13 minggu |
| **Tim** | BUMA ID Team (Jira board `IAMS30`) |
| **Status saat ini** (per 3 Agu 2026) | Item 1 & 2 **in progress, on track** — selaras sprint aktif `S3 IAMS` (berjalan s/d 12 Agu 2026) |
| **Urutan scope** | Sequential: 1) Service Package → 2) Form Input/Submission → 3) Finding Form (Order Creation) → 4) CBM Task → 5) Approval Workflow (Form Approval) → 6) EHMS Integration |

## Master Timeline (13 Minggu)

| Minggu | Tanggal | Item | Catatan |
|---|---|---|---|
| 1–7 | 25 Jun – 12 Agu | 1. Service Package + 2. Form Input/Submission Behavior | Selaras sprint `S2 IAMS` (25 Jun–8 Jul) + `S3 IAMS` (30 Jul–12 Agu) — **in progress, on track** |
| 8 | 13–19 Agu | 3. Finding Form (Order Creation) Integration | |
| 9 | 20–26 Agu | 4. CBM Task | |
| 10 | 27 Agu–2 Sep | 5. Approval Workflow Integration (Form Approval) | |
| 11–12 | 3–16 Sep | 6. EHMS Integration for CBM Task | 2 minggu — dialokasikan lebih lebar karena open items di MOM CBM/EHMS (lihat Risiko) |
| 13 | 17–23 Sep | Release Preparation | Buffer sebelum go-live |
| — | **24 Sep** | 🚀 **Go-Live** | |

**Catatan penting**: rentang Minggu 1–7 sudah berjalan sejak ~6 minggu lalu (~45% dari total 13 minggu sudah lewat per tanggal dokumen ini dibuat) — Gantt ini merefleksikan progres aktual (item 1 & 2 sedang berjalan), bukan mulai dari nol.

## Scope per Item

### 1. Service Package
Integrasi Form dan Digiplan (Daily Plan), khususnya untuk **Scheduled Service**. Detail desain sudah ada: lihat [pm-shutdown-service-package.md](phase1-service-package/pm-shutdown-service-package.md) dan [PRD-PM-Shutdown-Phase1.html](phase1-service-package/PRD-PM-Shutdown-Phase1.html).

### 2. Form Input & Submission Behavior
Behavior input dan submission form — mode **online dan offline** — termasuk **Finish Execution**.

### 3. Finding Form (Order Creation) Integration
Integrasi Finding Form ke proses pembuatan Order (Order creation).

### 4. CBM Task
Task CBM (Condition Based Monitoring) — 3 tipe task: Manual Rating (A/B/C/X), Measurement (decimal), Physical Condition (Good/Damage/Missing). Lihat [cbm-integration-ehms.md](../mom/cbm-integration-ehms.md).

### 5. Approval Workflow Integration (Form Approval)
Integrasi alur approval untuk form yang sudah disubmit.

### 6. EHMS Integration for CBM Task
Publish data CBM ke EHMS via topic (Btech) — EHMS consume topic lalu diproses dari staging table. Detail flow & open items: [cbm-integration-ehms.md](../mom/cbm-integration-ehms.md).

> Item 3, 4, dan 5 belum punya dokumen desain terpisah di repo ini saat dokumen ini ditulis — dicatat sesuai definisi scope yang diberikan user, detail teknis menyusul saat sesi diskusi masing-masing dimulai.

## Risiko & Catatan Terbuka

1. **EHMS Integration (Item 6) punya dependency yang belum resolved.** Per MOM [cbm-integration-ehms.md](../mom/cbm-integration-ehms.md) (Session 2, 3 Jun 2026), struktur JSON payload yang dikirim Digiman+ ke EHMS masih **"menunggu development Digiman+"**, dan beberapa mapping (data master CBM Threshold untuk transaksi non-Digiman+, referensi threshold di view) masih ditandai "perlu assess lebih lanjut". 2 minggu yang dialokasikan (Minggu 11–12) mengasumsikan item-item ini sudah clear sebelum development dimulai — perlu dikonfirmasi ulang sebelum Minggu 11 supaya tidak jadi blocker mendadak.
2. **Tidak ada buffer/kontingensi di luar 1 minggu Release Preparation.** Berbeda dari timeline squad-baru sebelumnya ([squad-baru-release-timeline.md](../architecture/squad-baru-release-timeline.md)) yang menyisakan ~1 sprint slack sebagai kontingensi, jadwal 13 minggu ini terisi penuh sequential tanpa slack tambahan — keterlambatan di item manapun akan mendorong mundur go-live 24 Sep, kecuali item berikutnya bisa di-overlap.
3. **Cakupan Release Preparation (Minggu 13) belum dikonfirmasi** — apakah termasuk UAT sign-off dari client atau hanya deployment plan/release notes/rollback plan (seperti timeline squad-baru sebelumnya yang eksplisit "tanpa UAT sign-off").
4. **Item 3, 4, 5 masing-masing hanya dialokasikan 1 minggu** tanpa breakdown effort (SP/mandays) — durasi ini rough estimate berdasarkan kesepakatan pembagian minggu, bukan hasil sizing formal. Risiko understimate ada, terutama mengingat pengalaman proposal Digiman+ sebelumnya di mana asumsi scope awal beberapa kali ternyata salah setelah digali lebih dalam (lihat catatan koreksi di `squad-baru-release-timeline.md`).

## Referensi
- [pm-shutdown-service-package.md](phase1-service-package/pm-shutdown-service-package.md)
- [PRD-PM-Shutdown-Phase1.html](phase1-service-package/PRD-PM-Shutdown-Phase1.html)
- [cbm-integration-ehms.md](../mom/cbm-integration-ehms.md)
- [squad-baru-release-timeline.md](../architecture/squad-baru-release-timeline.md) — precedent format timeline delivery
