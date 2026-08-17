# IronForms 930E Electrical Service — Comm Brush Replace Button Error (a4–a8)

| | |
|---|---|
| **ID** | BUMA-LOG-008 |
| **Project** | BUMA AU |
| **Reported by** | Will Mullany |
| **Cc** | Justin Shaw, Traven Hooper, Benedict Panizza, Scott McBryde, Stuart Cameron, DL Blackwater Reliability |
| **Date Raised** | 2026-06-25 09:08 WIB |
| **Priority** | P3 |
| **Status** | Done |
| **Jira Ticket** | — |
| **Handled by** | Okky / Pradya (Bukit Technology Support) |
| **Waiting On** | — (fix deployed 2026-08-10; awaiting Will's confirmation on his end if any issue resurfaces) |
| **Source** | [sources/ironforms-930e-brush-replace-button-error.pdf](sources/ironforms-930e-brush-replace-button-error.pdf) (covers messages through 2026-08-06 08:58 AM only; the 2026-08-10 RCA/fix entries are not covered by this source) |
| **Last Verified** | 2026-08-17 (partial — see Source note) |

## Description

On the 930E-4 electrical service sheet in IronForms, the **Replace** button for Comm Brush items **a4–a8** does not work correctly:

- When a brush measurement is out of spec and the user clicks **Replace**, an **"Out Of Range"** error pops up then disappears after 1–2 seconds.
- The item is still evaluated/flagged as **out of spec** even after Replace is pressed, so the electrician ends up replacing the brush anyway.
- Because Replace effectively fails, sparkies are forced to enter a measurement lower than the previous value as a workaround, which makes every subsequent data point redundant — important service information is lost, and a defect/intervention is raised unnecessarily.
- Confirmed by Will (2026-07-06) to affect **all 930E electrical service sections, for all machines**, not just a specific unit.

## Timeline

| Date/Time (WIB) | By | Action | Ball moves to |
|---|---|---|---|
| 2026-06-25 09:08 AM | Will Mullany | Raises issue: a5–a8 Replace button throws an unknown error (both retarder grid box sections). Forced to enter measurement below Prev. Value as workaround. | Bukit Technology Support |
| 2026-06-25 01:35 PM† | Okky (BukitTech) | Acknowledges, will check root cause. | Bukit Technology Support |
| 2026-06-26 07:47 AM | Will Mullany | "Thanks Okky, greatly appreciated." | Bukit Technology Support |
| 2026-06-26 04:42 PM† | Pradya (BukitTech) | Reports Replace button worked in non-prod when a bad value/rating (C/X) was entered; asks Will to confirm the expected flow (measure → enter Current Value → click Replace → enter Replacement value). | Will Mullany |
| 2026-06-26 04:52 PM | Will Mullany | Confirms the replace flow is correct; clarifies the error is specific to **a4–a8** (not a1–a3); asks whether testing covered all of a1–a8. | Bukit Technology Support |
| 2026-06-29 09:47 AM† | Pradya (BukitTech) | Clarifies non-prod's previous data only goes up to **A4**, so could only test the replace scenario up to that point (Rating X). Notes Replace logic is intended to behave identically across A1–A8. | Will Mullany |
| 2026-06-29 10:03 AM | Will Mullany | Explains that in production, since sparkies can't click Replace, they enter `0` as the last measurement instead (screenshot provided). | Bukit Technology Support |
| 2026-06-29 10:18 AM† | Pradya (BukitTech) | Requests a screen recording, plus **WO number** and **Equipment Number** for the affected service. | Will Mullany |
| 2026-07-06 11:50 AM† | Will Mullany | Confirms this affects all 930E electrical service sections, on all machines. | Bukit Technology Support |
| 2026-07-15 10:34 AM | Will Mullany | Asks why non-prod's previous data stops at A4 when prod has data for all brushes; asks if non-prod can be updated to mirror prod so the actual failing scenario can be tested. | Bukit Technology Support |
| 2026-07-16 04:04 PM† | Pradya (BukitTech) | Still trying to reproduce the production scenario in non-prod for A5–A8; will follow up. | Bukit Technology Support |
| 2026-08-06 07:58 AM | Will Mullany | Sends concrete reproduction — WO **4267274**, Equipment **DT0768**, 500hr service (confirmed consistent across all 930E trucks): (1) out-of-spec measurement entered on Brush 6 (reference value 44mm, entered 11mm) → correctly flagged "Out of spec"; (2) Replace button pressed; (3) "Out Of Range" error pops up, disappears after 1–2 seconds; (4) brush still evaluated as out of spec — electrician replaces it anyway, defect/intervention raised unnecessarily. Offers to share full videos via shared folder (too large to attach); attaches network HAR log of the replicated fault. | Bukit Technology Support |
| 2026-08-06 08:58 AM | Pradya (BukitTech) | Acknowledges receipt of the detailed info/attachments, confirms the team will investigate the root cause and follow up. | Bukit Technology Support |
| 2026-08-10 03:18 PM‡ | Pradya (BukitTech) | Sends RCA (attached): root cause identified as the **A5–A8 task configuration** needing an update. Plans to apply the config update same day, will notify Will once done. | Bukit Technology Support |
| 2026-08-10 05:31 PM‡ | Pradya (BukitTech) | Confirms configuration has been updated; sends PVT ("PVT - Fixing Cannot Replace - 100826.pdf") for the updated configuration. Asks Will to try it and report any issues. | Will Mullany |

† *Printed in the source thread as 04:35 PM, 07:42 PM, 12:47 PM, 01:18 PM, and 02:50 PM respectively — all are quoted headers Will Mullany's own Outlook generated at reply-time (Blackwater, Queensland — AEST/UTC+10), 3h ahead of Okky/Pradya's WIB. Each corrected by −3h. This also fixes the previously-unresolved inversion between the "04:52 PM" and "07:42 PM" rows: Pradya's flow-confirmation email (corrected to 04:42 PM) now correctly precedes Will's 04:52 PM reply, rather than appearing to follow it. Cross-checked against all 13 messages in the thread — every corrected timestamp falls into a clean, non-contradictory chronological order with no exceptions.*

‡ *These two entries are from a later portion of the thread not covered by the source PDF re-verified on 2026-08-17 — timestamps not re-checked against the AEST/WIB correction and may need the same treatment if the underlying email becomes available.*

## SLA Notes

- Root cause: A5–A8 task configuration was incorrect, blocking the Replace flow for those brush items. RCA sent and configuration fix deployed 2026-08-10.
- Periods where the ball was with **Will Mullany / BUMA** — 2026-06-29 10:18 AM → 2026-07-06 11:50 AM (screen recording/WO number requested, ~7 days), 2026-07-15 10:34 AM → 07-16 04:04 PM (non-prod data gap, ~1 day) — should be treated as SLA-pause windows once SLA is calculated, since BukitTech was blocked waiting on confirmation/info from BUMA. (The 06-26 Pradya→Will exchange is now only ~10 minutes apart once corrected, not a meaningful pause window.)
- Elapsed from raise (2026-06-25 09:08 AM) to fix deployed (2026-08-10 05:31 PM) is well past the P3 Final Resolution Target (≤45 calendar days) — largely attributable to the repro/config gap between non-prod (data only to A4) and prod (data through A8), which required BukitTech to update non-prod to reproduce A5–A8 before diagnosing the root cause.

## Outstanding / Next Steps

- None — fix deployed with RCA and PVT provided 2026-08-10. Re-open if Will reports the Replace button still fails on his end.

## Revision History

- **2026-08-17:** Re-verified 13 messages against the archived source PDF (through 2026-08-06 08:58 AM). Corrected 5 timestamps (all Will-quoted AEST headers, −3h each) and reordered one row (06-26 04:42 PM / 04:52 PM) — every corrected timestamp now falls into a clean, non-contradictory chronological order with zero exceptions, resolving a previously-unexplained inversion. SLA pause-window notes recalculated accordingly. The 2026-08-10 RCA/fix entries remain unverified — no source PDF covers that portion of the thread yet.
