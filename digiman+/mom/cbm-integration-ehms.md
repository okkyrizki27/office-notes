# MOM: CBM Integration with EHMS

**Date:** 2026-05-25 (Session 1) | 2026-06-03 (Session 2)

---

## Integration Points

1. **Integration via Topic:** Digiman+ publish data ke topic (Btech), EHMS consume topic.
2. EHMS consume semua topic meskipun data master belum available di EHMS.
3. Jika ada equipment pindah site, EHMS perlu assess cara nampilin data history CBM di dashboard.

## Expected Flow MO Service

- MO Service sync to Digiman : status **Release**
- Planner buat Planning di Digiplan, mapping MO service terhadap planning tersebut.
- Eksekusi → proses input CBM
- Execution finish
- Publish data CBM ke topic *(MO Service belum tentu sudah TECO)*
- EHMS consume topic → taruh table staging
- EHMS mengolah data dari staging *(assess lebih lanjut)*

## Notes & Constraints

5. Di Digiman+ backlog execution baru activity type: **BEX**, belum ada EHM dan ACT. Future enhancement.
6. **TECO Date** tidak dikirim dari Digiman+.
7. **SMU** di Digiman+ belum ada validasi range perubahan setiap service-nya.
8. Format date: **ISO string**.
9. Mapping CBM Threshold terkait dari transaksi Digiman+ akan ada di dalam Topic bersamaan value dan rating untuk transaksi tersebut.
10. Bagaimana dengan data master CBM Threshold untuk transaksi selain dari Digiman+? Data master CBM Threshold EHMS sync dari Digiman+ *(perlu assess lebih lanjut)*.

    Sumber input data CBM:
    - Service Sheet (PSCS) : Digiman+
    - Uploader
    - EHM via uploader
    - ACT via uploader
    - Revise data CBM
    - Pengecekan under carriage

11. Value dan rating data transaksi yang dari Digiman+ tidak perlu dikompare lagi di master data CBM Threshold EHMS. Jika memungkinkan, di view user menampilkan reference master data threshold yang digunakan saat transaksi itu terjadi *(perlu assess lebih lanjut)*.

---

## Session 2 — 2026-06-03

### Component & Equipment Mapping

1. Mapping Equipment to Component di EHMS diambil dari SAP. Di Digiman+ dimaintain sendiri. Perlu disepakati dengan BPO flow setup mapping component jika suatu saat ada model baru.
2. Digiman+ dapat mempertimbangkan membuat API untuk integrasi data component mapping *(future)*.
3. Monitoring CBM sampai level **Component**, tidak perlu sampai level sub component. Namun dari Digiman+ tetap akan mengirim data inputan user (CBM) sampai level sub component jika ada, beserta task key.

### Data & Integration Scope

4. **Data master integration** *(future journey)*.
5. **Bank task integration** *(future journey)*.
6. **Follow up action integration / intervention** *(future journey)*.

### Mapping & Validation Rules

7. **Area** diisi dengan Sub Component dari Digiman+ jika ada.
8. Mapping component to area **jangan divalidasi saat integrasi** — EHMS akan memproses dari table staging.
9. **CBM Parameter**: Digiman+ copy dari EHMS untuk BUMA ID.

### Task Key & Description

10. **Task Key EHMS** masuk ke `external_code` di Digiman+.
11. Digiman+ kirim data transaksi ke EHMS — task key diambil dari `external_code` jika ada.
12. **Task Description** untuk initial Digiman+ disamakan dengan EHMS.

### CBM Task Types

13. 3 tipe task CBM di EHMS saat ini:
    - **Manual Rating**: A, B, C, X
    - **Measurement**: decimal (2 digit)
    - **Physical Condition**: Good, Damage, Missing

### Data Fields yang Dikirim

14. **UOM** tetap dikirim dari Digiman+.
15. **IsSampleTaken**: `1` jika data diisi oleh user, `0` selain itu.
16. **Rating** dikirim beserta **threshold** yang digunakan saat transaksi.

### Next Discussion

17. Bentuk/struktur data JSON yang akan dikirim Digiman+ ke EHMS *(menunggu development Digiman+)*.
