# Maintiva — Homepage (Logged-in) & Landing Page (Logged-out)

Dokumen ini merekam diskusi soal dua topik terkait tapi berbeda: **homepage platform** setelah user login, dan **struktur marketing/landing page** saat user belum login. Masih tahap konsep, belum ada keputusan final — untuk dilanjutkan di sesi berikutnya.

*Last updated: 2026-08-07*

Konteks umum: [README.md](README.md)

---

## A. Homepage Platform (Logged-in)

Homepage yang dimaksud di sini adalah **halaman utama ekosistem Maintiva setelah login** — bukan homepage per-produk yang sudah ada (mis. homepage mobile Digiman+ existing, lihat [current-state](../digiman+/architecture/homepage/homepage-current-state.md): pattern "Needs Attention" aggregate per Inspection/PM Shutdown/BD Corrective, permission-based section visibility).

### Dua Arah yang Dibahas

1. **Pure Launcher** — homepage cuma jadi switcher: tampil tile/card per produk yang user punya akses (sesuai tabel persona di README), klik salah satu masuk ke homepage produk tersebut. Simpel, tapi butuh 2 klik untuk sampai ke konten.
2. **Aggregated Dashboard** — homepage menampilkan ringkasan lintas-produk (mis. alert kesehatan asset dari Pulse + risk score dari Predict + overdue task dari Core, semua dalam satu view), dengan tile produk sebagai navigasi sekunder.

### Rekomendasi (belum final, masih didiskusikan)

Condong ke **Aggregated Dashboard** — alasannya value proposition Maintiva adalah "connected suite", pure launcher cuma jadi folder berisi 5 app dan tidak menunjukkan itu. Pattern "Needs Attention" di homepage Digiman+ existing juga sudah membuktikan user merespons baik ke aggregated triage view, bukan menu semata.

Tradeoff: build complexity jauh lebih besar — perlu definisikan apa yang "homepage-worthy" dari tiap produk (Pulse/Predict/Agent/Insight) dan menjaga kurasinya per role, dibanding tile statis yang jauh lebih ringan dikerjakan.

**Belum diputuskan user** — perlu dilanjutkan.

---

## B. Marketing / Landing Page (Logged-out)

Model referensi: **Jira/Atlassian & Lark** — brand payung dengan landing page sendiri, tiap produk juga punya landing page sendiri yang saling terhubung.

### Struktur yang Diinginkan

**Kondisi belum login:**
- `maintiva.[domain]` = master landing page, memperkenalkan seluruh ekosistem produk, link ke landing page tiap produk.
- Tiap produk (Core, Pulse, Agent, Predict, Insight, dst) punya **landing page sendiri** — bisa jadi entry point independen, tidak harus lewat master page dulu.
- **Semua landing page harus bisa terindex di Google (SEO)** — supaya user bisa masuk ke ekosistem Maintiva dari pintu manapun (search by product-specific keyword, bukan cuma brand "Maintiva").
- Walaupun user landing di halaman produk tertentu, harus tetap mudah paham bahwa produk ini bagian dari ekosistem Maintiva, dan ada produk lain yang bisa dieksplorasi — reference pattern: **Lark** (product switcher/cross-link antar Docs, Base, Meetings, dst tanpa kehilangan konteks "masih di Lark").
- CTA konsisten di semua halaman: **Request Demo** (atau setara).

**Kondisi sudah login:**
- User diarahkan fokus ke produknya masing-masing (bukan ke marketing page).
- Tetap ada jalan untuk kembali ke halaman marketing/landing page kalau user mau explore produk lain.

### Open Questions (belum diputuskan, untuk sesi berikutnya)

1. **Root domain behavior** — apakah `maintiva.[domain]` murni marketing page (seperti `atlassian.com` yang terpisah dari `jira.com`), atau satu domain dengan redirect kontekstual (logged-in → app, logged-out → suite overview)?
2. **Request Demo funnel** — satu funnel gabungan untuk semua produk, atau tiap produk punya qualification flow sendiri (berpengaruh ke cara sales handle leads)?
3. **Level "ecosystem awareness" signal** di halaman produk — persistent top bar/switcher (seperti Lark) atau cukup footer-level mention?
4. Keputusan final untuk bagian A (Pure Launcher vs Aggregated Dashboard) di atas.
