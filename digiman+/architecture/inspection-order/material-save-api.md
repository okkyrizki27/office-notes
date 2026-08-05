# Material Save API — Current State (Add Part saat Create Order)

*Last updated: 2026-08-05*

---

**Feature:** Order (Digiman+) — Create Order, aksi **"Add Part"** (submit pilihan material ke eMOL)
**Service:** `maintenance-order`
**Related doc:** [material-list-api.md](material-list-api.md) *(API GET pasangannya — search/list material yang bisa ditambahkan)*, [order-emol-sap-sync.md](order-emol-sap-sync.md) *(Bagian 4.3 — Material Opsional per eMOL)*
**Sumber:** BE code (`SaveMolMaterialOrderCommandHandler`), di-share user 2026-08-05

---

## 1. Ringkasan

Handler untuk `SaveMolMaterialOrderCommand` — dipanggil saat user submit pilihan material di eMOL (aksi "Add Part"). Request berisi **seluruh list material yang dipilih user untuk 1 eMOL** (`MolId` + `MaterialOrders[]`) — bukan single-item add, tapi full-list replace yang di-diff terhadap data existing di `MechanicOrderMaterial`: baru → insert, masih ada → update, sudah tidak ada di request → soft delete.

Setelah diff selesai, handler baca ulang total (`molCount`, `totalAmount`) dan publish event `UpdateOrderFinding` ke service bus untuk update ringkasan finding di transaksi induk (WorkOrder atau `MechanicOrderSummary`).

---

## 2. Alur — 3 Fase, 2 Koneksi DB Terpisah

### Fase 1 — Diff & Write (transaksi 1, `MechanicOrderMaterial`)

1. Baca existing `MechanicOrderMaterial` by `MolId` (`GetByMolId`).
2. **Create** — item di request yang belum ada di existing (`!existingOrders.IsExistByRequest(p, MolId)`) → `CreateAsync`.
3. **Update** — item existing yang masih ada di request (`existingOrders.Where(request.Request.ContainsMaterialOrder)`) → `UpdateAsync`. Payload-nya cuma item yang matched (`existingOrders.IsExistByRequest`).
4. **Delete** — item existing yang **tidak lagi** ada di request (`!request.Request.ContainsMaterialOrder(p)`) → `DeleteAsync` by `Id` (soft delete, konsisten dengan `GetByMolId` yang baca `IsActive = 1` di API GET, lihat [material-list-api.md](material-list-api.md) Bagian 3).
5. Audit log untuk ketiga aksi (`CreateNewDataAuditLogRequest`, `CreateAuditLogRequest(Update)`, `CreateAuditLogRequest(Delete)`) di-insert dalam transaksi yang sama.
6. Commit.

> **Matching key create/update/delete** pakai extension method `IsExistByRequest`/`ContainsMaterialOrder` — implementasinya **tidak ada di snippet ini**. Berdasarkan pola API GET (material by `MaterialNumber`+`BatchCode`), kemungkinan match key-nya sama, tapi ini **asumsi, belum dikonfirmasi**.

### Fase 2 — Recompute Total (transaksi 2, connection baru)

Baca ulang `MechanicOrderList` by `MolId`, lalu cabang tergantung status "naik level" eMOL-nya:

| Kondisi (`mechanicOrder.WorkOrderId`) | Sumber agregat | `molCount` |
|---|---|---|
| `null` atau `0` (belum naik ke WorkOrder) | `GetBySummaryId(MechanicOrderSummaryId)` → SUM(`TotalCost`) | `GetWithDetailBySummaryAsync(MechanicOrderSummaryId).Count` |
| terisi | `GetByWorkOrderId(WorkOrderId)` → SUM(`TotalCost`) | `CountByWorkOrderAsync(WorkOrderId)` |

`totalAmount` selalu dijumlah dari **`MechanicOrderMaterial.TotalCost`** — field terpisah dari `Cost` di schema ([maintenance-order-schema.md](../database/maintenance-order-schema.md#L100)), kemungkinan `Cost × Quantity`. **Belum dikonfirmasi di mana `TotalCost` ini dihitung** — tidak ada di handler ini, kemungkinan di repository `CreateAsync`/`UpdateAsync` atau AutoMapper profile.

### Fase 3 — Publish `UpdateOrderFinding`

```csharp
long referenceTransaction = 0;
if (mechanicOrder != null && mechanicOrder.WorkOrderId != null)
    referenceTransaction = mechanicOrder.WorkOrderId ?? 0;
else if (mechanicOrder != null && mechanicOrder.MechanicOrderSummaryId != null)
    referenceTransaction = mechanicOrder.MechanicOrderSummaryId ?? 0;

await _serviceBusPublisher.PublishUpdateOrderFinding(
    tenantCode: request.TenantCode,
    referenceTransaction,
    WorkflowTransactionTypeEnum.MechanicOrder.String(),
    molCount, totalAmount, request.Request.RequestedBy);
```

`referenceTransaction` = `WorkOrderId` kalau ada, fallback `MechanicOrderSummaryId`, kalau keduanya null tetap `0`.

---

## 3. Observasi

- ⚠️ **Dead object `serviceBusRequest`** — tepat sebelum publish, kode membentuk objek `UpdateOrderFindingCommand serviceBusRequest` lengkap (dengan `ReferenceTransactionId`, `TransactionType`, `TotalFinding`, `TotalAmount`) dan **log** isinya (`_logger.LogTrace("Update Finding : {RequestJson}", ...)`), tapi publish aktualnya (`PublishUpdateOrderFinding(...)`) pakai parameter positional terpisah — bukan `serviceBusRequest` itu. Kalau isinya kebetulan identik ini cuma object terbuang (alokasi + serialize percuma tiap request), tapi kalau suatu saat salah satu jalur diubah dan yang lain lupa di-sync, log akan menampilkan payload yang **beda** dari yang benar-benar dipublish — menyesatkan saat debugging.
- ⚠️ **`mechanicOrder == null` tidak di-guard** — kalau `MolId` tidak ketemu di transaksi 2 (`GetByIdAsync` return null), `referenceTransaction`/`molCount`/`totalAmount` tetap di nilai default (`0`/`0`/`0`), tapi kode **tetap lanjut** publish `UpdateOrderFinding` dengan `ReferenceTransactionId = 0`. Berpotensi kirim event "kosong"/salah ke konsumer downstream. Belum dicek apakah `MolId` sudah divalidasi exist di layer sebelumnya (Controller/validator) sehingga case ini sebenarnya unreachable.
- **2 transaksi terpisah, bukan 1 atom** — antara commit Fase 1 dan publish Fase 3 ada window non-atomic. Kalau proses crash setelah Fase 1 commit tapi sebelum publish berhasil, `MechanicOrderMaterial` sudah berubah tapi ringkasan finding (count/amount) di transaksi induk jadi **stale** sampai trigger update berikutnya. Tidak terlihat ada outbox pattern di sini (beda dengan `TopicPublishLog` yang dipakai di alur SAP sync, lihat [order-emol-sap-sync.md](order-emol-sap-sync.md) Bagian 5.6f) — kalau `PublishUpdateOrderFinding` publish langsung ke service bus tanpa outbox, ini exposed ke risiko "commit sukses, publish gagal" tanpa retry/reconciliation.
- **`UpdateOrderFinding` / konsep "Finding" di sini belum terdokumentasi** di tempat lain dalam notebook ini — beda dari `TaskPersonalizedFinding` (temuan inspeksi, lihat [[project_finding_taxonomy_master_data]] / `maintenance-execution` docs). Di konteks handler ini, "Finding" tampaknya istilah generik workflow untuk "ringkasan transaksi" (count + amount) yang di-update ke service lain (kemungkinan approval/workflow service) — perlu ditelusuri konsumernya kalau mau dokumentasi lengkap.

---

## 4. Open Items

- Konfirmasi matching key `IsExistByRequest`/`ContainsMaterialOrder` (asumsi: `MaterialNumber`+`BatchCode`, belum lihat implementasinya).
- Konfirmasi di mana `MechanicOrderMaterial.TotalCost` dihitung (`Cost × Quantity`?).
- Konfirmasi apakah `MolId` yang tidak ketemu (`mechanicOrder == null`) itu reachable di production, atau sudah pasti divalidasi sebelum handler ini dipanggil.
- Konfirmasi apakah `serviceBusRequest` object dead code murni, atau ada jalur lain yang memakainya yang tidak terlihat di snippet ini.
- Konfirmasi siapa consumer `UpdateOrderFinding` dan makna "Finding"/`TotalFinding` di konteks workflow ini (beda dari inspection Finding).

---

## Referensi
- [material-list-api.md](material-list-api.md) — API GET pasangannya (search/list material)
- [order-emol-sap-sync.md](order-emol-sap-sync.md) — Bagian 4.3 (Material Opsional per eMOL), Bagian 5.6f (outbox pattern `TopicPublishLog`)
- [../database/maintenance-order-schema.md](../database/maintenance-order-schema.md) — schema `MechanicOrderList`, `MechanicOrderMaterial`
