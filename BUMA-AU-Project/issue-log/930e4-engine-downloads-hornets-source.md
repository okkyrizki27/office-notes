# 930E-4 Engine Downloads — Source Confirmation (Cummins / Hornets)

| | |
|---|---|
| **Project** | BUMA AU |
| **Reported by** | Benedict Panizza |
| **Date Raised** | 2026-07-20 06:48 AM WIB |
| **Priority** | N/A (Inquiry — not an Incident/Defect) |
| **Status** | Answered — Awaiting Benedict/BUMA decision |
| **Waiting On** | Benedict Panizza / BUMA (to confirm whether they want to proceed with the excavator Cummins data enhancement) |

## Description

Benedict originally asked whether IronPortal has any built-in logic to handle a Cummins engine data export from an excavator (EX0798), and if not, what Cummins data IronPortal can currently handle — he wanted excavator engine data exports similar to the VIMS downloads, given the criticality of these components. This evolved into a question of whether the existing 930E-4 (Cummins) engine download flow into IronPortal could be extended to excavator engines (also Cummins), and whether all 930E-4 engine downloads currently come from Hornets.

## Timeline

| Date/Time (WIB) | By | Action | Ball moves to |
|---|---|---|---|
| 2026-07-20 06:48 AM | Benedict Panizza (→ Agus Setiadi, cc Okky) | Raises issue: attaches a Cummins engine data export from excavator EX0798. Asks if IronPortal has built-in logic to handle this file; if not, what Cummins data IronPortal can handle currently. Wants excavator engine data exports similar to VIMS downloads, given the criticality of these components. | Bukit Technology Support |
| 2026-07-23 09:50 AM | Okky (BukitTech) | Replies: IronPortal has no built-in logic to handle this Cummins data export; current implementation only supports VIMS data. Attaches the current VIMS dataset IronPortal can process. | Benedict Panizza |
| 2026-07-24 04:51 AM | Benedict Panizza | Follow-up: "How does it ingest some of the 930E-4 engine downloads then? These are Cummins engines." | Bukit Technology Support |
| 2026-07-24 → 07-27 (exact time not captured) | Okky (BukitTech) | Explains the current VIMS data integration architecture in IronPortal (SharePoint download → manual VIMSpc 2015 extract → manual upload to ADLS Gen2 → pipeline to Serverless SQL → transformation → Power BI reporting), with architecture diagram. Asks whether Benedict is planning to handle 930E-4 Cummins downloads on BUMA's side via a pipeline similar to VIMS. Notes uncertainty that this would be a straightforward match, since VIMS is Caterpillar's proprietary system and its logic likely can't be applied 1:1 to Komatsu 930E-4's Cummins engine data. | Benedict Panizza |
| 2026-07-27 10:13 AM | Benedict Panizza | Clarifies: "The 930E-4 engine downloads (Cummins) already flow into IronPortal. I was more asking whether this could just be applied to the excavator engines (Cummins). Or are all the 930E-4 engine downloads from Hornets?" | Bukit Technology Support |
| 2026-08-11 09:28 AM | Okky (BukitTech, cc Agus Setiadi, Herianto Salim) | Sends full answer (see Outcome below). | Benedict Panizza / BUMA |

## Outcome (sent to Benedict, 2026-08-11)

1. The 930E-4 engine data flowing into IronPortal is pulled from the EQP website via a scheduled web scraper. That scraper is currently not working, as the EQP website itself is no longer available — the last EQP data received was **19 May 2026**.
2. Parameters from the excavator's Cummins engine download were compared against what the 930E-4 EQP model in IronPortal expects (see Parameter Compatibility Analysis below) — only ~41% match confidently as-is; the rest need further verification before a full match can be confirmed.
3. Bringing the excavator's Cummins engine data in similarly to how VIMS data is handled is possible, but would need to be scoped and managed as an enhancement/variation rather than under existing support.

Benedict has not yet replied to confirm whether BUMA wants to proceed with option 3.

**Note:** point 1 above is the first time the EQP scraper outage (no new 930E-4 engine data since 19 May 2026) has been disclosed to BUMA in writing. Since it's now visible to the client on this thread, it may be worth a separate decision on whether this needs its own tracked issue (was previously deferred — see conversation history) — flagging in case Benedict follows up asking about it directly.

## Parameter Compatibility Analysis (2026-08-11)

Compared a sample excavator Cummins engine download (`TL-20260701-054704 SMU 41817.csv`, EX798 RH) against the 22 unique ENGINE-component EQP parameters IronPortal expects for 930E-4 HPI. Findings:

- **Likely compatible (direct or unit-convert match):** Engine Oil Pressure, Engine Oil Temp, Engine Coolant Temp, Engine Oil Filter Differential Pressure (already pre-calculated in source), Engine Speed, Fuel Rate, Atmospheric Pressure, Blow-by/Crankcase Pressure. These have a plausible 1:1 raw sensor source; would need unit conversion (psi→kg/cm2, kPa→mmAq, etc.) and MAX/MIN/AVE aggregation to produce the EQP values.
- **Confirmed gap:** Ambient Temperature (AVE/MAX/MIN) — no ambient temp sensor at all in this download.
- **Unconfirmed assumptions (need engine documentation, not inferable from column names):**
  - Boost LB/RB Press — which of "Intake Manifold Pressure Sensor 1" vs "2" is Left Bank vs Right Bank.
  - Exhaust Temp MAX(LF/LM/LR/RF/RM/RR) — the excavator download reports 16 individual per-cylinder exhaust temps, but the EQP model wants 6 bank-zone MAX values; needs a cylinder-to-zone grouping specific to this engine's layout.
- **Derivable but not direct:** ENG OIL PRESS@HI/LO IDLE MIN — needs engine-speed-state detection logic (not a raw column) on top of the continuous Engine Oil Pressure / Engine Speed data.
- **Open pipeline question (not answerable from the CSV alone):** this file is a manual Cummins INSITE export (3-min sample rate, one-off SMU snapshot). Unknown whether the existing 930E-4 EQP ingestion pipeline reads this same INSITE format or a different automated feed — determines whether extending to excavators is parser reuse or a new integration. Moot in practice for now, since the EQP feed itself is currently down.

**Conclusion:** parameter concepts mostly line up (41% confident match, up to ~86% pending confirmation of the boost-bank and exhaust cylinder-zone mappings), but this is secondary to the fact that the underlying EQP pipeline for the *existing* 930E-4 fleet has had no new data since 19 May 2026 — extending a currently non-functional pipeline to excavators isn't practical until that's resolved.

## Outstanding / Next Steps

- Awaiting Benedict/BUMA's decision on whether to proceed with the excavator Cummins data enhancement (option 3).
- If it proceeds: confirm the boost-bank (LB/RB) and exhaust cylinder-to-zone mapping assumptions with whoever built the 930E-4 EQP parser, and fix/replace the EQP web scraper first.
- Decide whether the EQP scraper outage (no data since 19 May 2026) needs its own tracked issue now that it's been disclosed to BUMA.
