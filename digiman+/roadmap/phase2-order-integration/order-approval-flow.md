# Order Approval Flow & Crack Order Lifecycle

Dokumen ini merekam poin diskusi lanjutan phase 2 seputar Order Integration: alur approval dari Form sampai Order masuk SAP, serta lifecycle Order khusus untuk Crack Defect.

*Recorded: 2026-08-06*

---

## Approval Flow

### 1. Form Approval — sampai Foreman/Supervisor

Form (termasuk Finding/Defect di dalamnya) melalui approval berjenjang sampai level **Foreman/Supervisor**.

### 2. Defect biasa — lanjut jadi Order di SAP tergantung Planner

Defect dibuat oleh **mechanic**, termasuk pengisian **material**. Apakah defect ini **dilanjutkan jadi Order di SAP** ditentukan oleh **Planner** — Planner adalah gate approval Order sebelum push ke SAP.

---

## Crack Order Lifecycle

### 3. Crack — Order dibuat sejak tahap monitoring

Crack yang terdeteksi sejak monitoring (crack masih sangat kecil) tetap **dibuatkan Order**, hanya saja dengan **priority rendah**.

### 4. Crack — eskalasi ke critical saat inspeksi berikutnya

Saat inspeksi berikutnya, crack yang sama bisa naik status jadi **critical**. Eksekusinya:

- Kalau Order dari temuan sebelumnya **masih open** → eksekusi pakai Order itu (bukan bikin baru).
- Kalau Order sebelumnya **sudah tidak open** → tetap push Order baru ke SAP.

---

## Related Docs

- [order-integration.md](order-integration.md) — dokumen utama phase 2 (trigger, current-state UI, open items)
