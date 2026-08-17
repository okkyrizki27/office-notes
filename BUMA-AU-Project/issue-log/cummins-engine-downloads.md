# 930E-4 Engine Downloads — Source Confirmation (Cummins / Hornets)

| | |
|---|---|
| **ID** | BUMA-LOG-007 |
| **Project** | BUMA AU |
| **Reported by** | Benedict Panizza |
| **Date Raised** | 2026-07-20 06:48 AM WIB |
| **Priority** | N/A (Inquiry — not an Incident/Defect) |
| **Status** | Open — Bukit Technology Support to respond |
| **Waiting On** | Bukit Technology Support (Okky) — owes (1) the enhancement scope Benedict asked for, and (2) a reply on the new EQP→MyFleet webscraper question |
| **Source** | [sources/cummins-engine-downloads.pdf](sources/cummins-engine-downloads.pdf) |
| **Last Verified** | 2026-08-17 |

## Description

Benedict originally asked whether IronPortal has any built-in logic to handle a Cummins engine data export from an excavator (EX0798), and if not, what Cummins data IronPortal can currently handle — he wanted excavator engine data exports similar to the VIMS downloads, given the criticality of these components. This evolved into a question of whether the existing 930E-4 (Cummins) engine download flow into IronPortal could be extended to excavator engines (also Cummins), and whether all 930E-4 engine downloads currently come from Hornets.

As of 2026-08-11, the thread has continued past the original "full answer": Benedict asked for a scope of the enhancement to weigh up options, Okky agreed to provide it, and separately Benedict raised a related but distinct question — Komatsu has transitioned to **MyFleet** (successor condition-data source, exportable via Excel), and he's asking whether anyone has given Okky account access to look at replacing the (currently broken) EQP webscraper with a MyFleet webscraper as part of regular IronPortal maintenance.

## Timeline

| Date/Time (WIB) | By | Action | Ball moves to |
|---|---|---|---|
| 2026-07-20 06:48 AM | Benedict Panizza (→ Agus Setiadi, cc Okky) | Raises issue: attaches a Cummins engine data export from excavator EX0798. Asks if IronPortal has built-in logic to handle this file; if not, what Cummins data IronPortal can handle currently. Wants excavator engine data exports similar to VIMS downloads, given the criticality of these components. | Bukit Technology Support |
| 2026-07-23 06:50 AM† | Okky (BukitTech) | Replies: IronPortal has no built-in logic to handle this Cummins data export; current implementation only supports VIMS data. Attaches the current VIMS dataset IronPortal can process. | Benedict Panizza |
| 2026-07-24 04:51 AM | Benedict Panizza | Follow-up: "How does it ingest some of the 930E-4 engine downloads then? These are Cummins engines." | Bukit Technology Support |
| 2026-07-27 09:39 AM† | Okky (BukitTech) | Explains the current VIMS data integration architecture in IronPortal (SharePoint download → manual VIMSpc 2015 extract → manual upload to ADLS Gen2 → pipeline to Serverless SQL → transformation → Power BI reporting), with architecture diagram. Asks whether Benedict is planning to handle 930E-4 Cummins downloads on BUMA's side via a pipeline similar to VIMS. Notes uncertainty that this would be a straightforward match, since VIMS is Caterpillar's proprietary system and its logic likely can't be applied 1:1 to Komatsu 930E-4's Cummins engine data. | Benedict Panizza |
| 2026-07-27 10:13 AM | Benedict Panizza | Clarifies: "The 930E-4 engine downloads (Cummins) already flow into IronPortal. I was more asking whether this could just be applied to the excavator engines (Cummins). Or are all the 930E-4 engine downloads from Hornets?" | Bukit Technology Support |
| 2026-08-11 09:29 AM† | Okky (BukitTech, cc Agus Setiadi, Herianto Salim) | Sends full answer (see Outcome below). | Benedict Panizza / BUMA |
| 2026-08-11 09:46 AM | Benedict Panizza | "Are you able to provide a scope of an enhancement so we can weigh up the options?" | Bukit Technology Support |
| 2026-08-11 09:52 AM† | Okky (BukitTech) | "Yes, I am. I will update you once it's done." | Bukit Technology Support |
| 2026-08-11 11:55 AM | Benedict Panizza (cc Agus Setiadi, Herianto Salim) | New, related question in the same thread: Komatsu has transitioned to **MyFleet**, where a lot of the condition data is still available/exportable via Excel. Asks whether anyone has given Okky account details to look into transitioning the EQP webscraper to a MyFleet webscraper as part of regular IronPortal platform maintenance. | Bukit Technology Support |

† *Printed in the source thread as 09:50 AM, 12:39 PM, 12:29 PM, and 12:52 PM respectively — all quoted headers Benedict's own Outlook generated at reply-time (Queensland, AEST/UTC+10), 3h ahead of Okky's WIB. Each corrected by −3h. This also resolves the two rows previously logged as "exact time not captured" (now precisely 2026-07-27 09:39 AM) and estimated "09:28 AM" (now precisely 09:29 AM) — both now confirmed against the actual source thread.*

## Outcome (sent to Benedict, 2026-08-11)

1. The 930E-4 engine data flowing into IronPortal is pulled from the EQP website via a scheduled web scraper. That scraper is currently not working, as the EQP website itself is no longer available — the last EQP data received was **19 May 2026**.
2. Parameters from the excavator's Cummins engine download were compared against what the 930E-4 EQP model in IronPortal expects (see Parameter Compatibility Analysis below) — only ~41% match confidently as-is; the rest need further verification before a full match can be confirmed.
3. Bringing the excavator's Cummins engine data in similarly to how VIMS data is handled is possible, but would need to be scoped and managed as an enhancement/variation rather than under existing support.

**Update (2026-08-11):** Benedict replied same day asking Okky to provide a scope of the enhancement so BUMA can weigh up the options — not yet a decision to proceed, but a request for the info needed to decide. Okky agreed ("Yes, I am. I will update you once it's done.") — the enhancement scope is now outstanding from Bukit Technology Support's side, not BUMA's.

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

- **Bukit Technology Support owes Benedict an enhancement scope** (requested 2026-08-11 09:46 AM, agreed to by Okky at 09:52 AM) for the excavator Cummins data integration (option 3), so BUMA can weigh up whether to proceed.
- **Bukit Technology Support also owes a reply** to Benedict's 2026-08-11 11:55 AM question: has anyone received account details to look into transitioning the EQP webscraper to a **MyFleet** webscraper (Komatsu's successor platform to EQP) as part of regular IronPortal maintenance? This is a live, more immediate alternative to fixing/replacing the broken EQP scraper — worth cross-referencing before scoping the enhancement above, since a MyFleet-based rebuild could resolve both the stale-930E-4-data problem and (per Benedict's original ask) plausibly extend to excavators too.
- If the excavator enhancement proceeds: confirm the boost-bank (LB/RB) and exhaust cylinder-to-zone mapping assumptions with whoever built the 930E-4 EQP parser.
- Decide whether the EQP scraper outage (no data since 19 May 2026) needs its own tracked issue now that it's been disclosed to BUMA — the MyFleet question above may effectively supersede this.

## Revision History

- **2026-08-17:** Renamed from `930e4-engine-downloads-hornets-source.md` to `cummins-engine-downloads.md` to match the actual email subject line. Re-verified against a fuller source PDF: corrected 4 timestamps (all Benedict-quoted AEST headers, −3h each), pinned down 2 previously-fuzzy/estimated timestamps precisely, and discovered the thread continued 3 messages past what was originally logged — status flipped from "Answered — Awaiting Benedict/BUMA decision" to "Open — Bukit Technology Support to respond," since Benedict had in fact replied asking for an enhancement scope, and separately raised a new question about transitioning to Komatsu's MyFleet platform.
