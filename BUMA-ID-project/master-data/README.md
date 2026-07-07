# Master Data — Finding Taxonomy (Damage / Cause / Action Remedy)

**Sumber:** Data client BUMA ID, diberikan langsung oleh user pada 2026-07-06 (bukan hasil query terhadap sistem MKP).

**Isi folder:**
- `damage-group-all.csv` / `damage-code-all.csv` — hierarki `DamageGroup → DamageCode`
- `cause-group-all.csv` / `cause-code-all.csv` — hierarki `CauseGroup → CauseCode`
- `action-remedy-all.csv` — flat list, **tidak** ada grouping (berbeda dari Damage/Cause yang dua level)

**Catatan:**
- Ketiga field ini (`DamageCode`, `CauseCode`, `ActionRemedyCode`) diisi di tabel `TaskPersonalizedFinding` saat inspector mencatat temuan (lihat `digiman+/architecture/form/form-submission.md`).
- Hanya `DamageCode` yang punya mapping ke `Model → Component → SubComponent` (lihat `digiman+/query/query_mapping_damage_code.sql`) — untuk mempermudah UX pemilihan saat inspector input defect. Cause Code dan Action Remedy tidak punya mapping serupa.
- `AR0010 = Repair` — relevan untuk business rule di `digiman+/report/transaction-report/gap-analysis/gap-analysis.md` (action item `MaterialStatus`/`canactiondigimandelete` override). Interpretasi ini masih perlu didiskusikan dengan tim technical sebelum dianggap final.
