# IronForms 930E Electrical Service — Comm Brush Replace Button Error (a4–a8)

| | |
|---|---|
| **Project** | BUMA AU |
| **Reported by** | Will Mullany |
| **Cc** | Justin Shaw, Traven Hooper, Benedict Panizza, Scott McBryde, Stuart Cameron, DL Blackwater Reliability |
| **Date Raised** | 2026-06-25 09:08 WIB |
| **Priority** | P3 |
| **Status** | Open — being investigated by Bukit Technology Support |
| **Jira Ticket** | — |
| **Handled by** | Okky / Pradya (Bukit Technology Support) |
| **Waiting On** | Bukit Technology Support (as of 2026-08-06 08:58 WIB — investigating root cause) |

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
| 2026-06-25 04:35 PM | Okky (BukitTech) | Acknowledges, will check root cause. | Bukit Technology Support |
| 2026-06-26 07:47 AM | Will Mullany | "Thanks Okky, greatly appreciated." | Bukit Technology Support |
| 2026-06-26 04:52 PM | Will Mullany | Confirms the replace flow is correct; clarifies the error is specific to **a4–a8** (not a1–a3); asks whether testing covered all of a1–a8. | Bukit Technology Support |
| 2026-06-26 07:42 PM | Pradya (BukitTech) | Reports Replace button worked in non-prod when a bad value/rating (C/X) was entered; asks Will to confirm the expected flow (measure → enter Current Value → click Replace → enter Replacement value). *(Note: this message logically precedes the 04:52 PM one above — timestamps as printed in the Outlook thread, order not re-sequenced.)* | Will Mullany |
| 2026-06-29 10:03 AM | Will Mullany | Explains that in production, since sparkies can't click Replace, they enter `0` as the last measurement instead (screenshot provided). | Bukit Technology Support |
| 2026-06-29 12:47 PM | Pradya (BukitTech) | Clarifies non-prod's previous data only goes up to **A4**, so could only test the replace scenario up to that point (Rating X). Notes Replace logic is intended to behave identically across A1–A8. | Will Mullany |
| 2026-06-29 01:18 PM | Pradya (BukitTech) | Requests a screen recording, plus **WO number** and **Equipment Number** for the affected service. | Will Mullany |
| 2026-07-06 02:50 PM | Will Mullany | Confirms this affects all 930E electrical service sections, on all machines. | Bukit Technology Support |
| 2026-07-15 10:34 AM | Will Mullany | Asks why non-prod's previous data stops at A4 when prod has data for all brushes; asks if non-prod can be updated to mirror prod so the actual failing scenario can be tested. | Bukit Technology Support |
| 2026-07-16 07:04 PM | Pradya (BukitTech) | Still trying to reproduce the production scenario in non-prod for A5–A8; will follow up. | Bukit Technology Support |
| 2026-08-06 07:58 AM | Will Mullany | Sends concrete reproduction — WO **4267274**, Equipment **DT0768**, 500hr service (confirmed consistent across all 930E trucks): (1) out-of-spec measurement entered on Brush 6 (reference value 44mm, entered 11mm) → correctly flagged "Out of spec"; (2) Replace button pressed; (3) "Out Of Range" error pops up, disappears after 1–2 seconds; (4) brush still evaluated as out of spec — electrician replaces it anyway, defect/intervention raised unnecessarily. Offers to share full videos via shared folder (too large to attach); attaches network HAR log of the replicated fault. | Bukit Technology Support |
| 2026-08-06 08:58 AM | Pradya (BukitTech) | Acknowledges receipt of the detailed info/attachments, confirms the team will investigate the root cause and follow up. | Bukit Technology Support |

## SLA Notes

- Clock is currently on **Bukit Technology Support** (waiting on root-cause investigation since 2026-08-06 08:58 AM WIB).
- Periods where the ball was with **Will Mullany / BUMA** (e.g. 2026-06-26 07:42 PM → 04:52 PM same-day exchange, 2026-06-29 01:18 PM → 07-06 02:50 PM, 2026-07-15 → 07-16) should be treated as SLA-pause windows once SLA is calculated, since BukitTech was blocked waiting on confirmation/info from BUMA.

## Outstanding / Next Steps

- Bukit Technology Support to confirm root cause using the HAR log + reproduction steps from the 2026-08-06 email.
- Need to set up a shared folder for Will to upload the full reproduction videos (too large for email).
- Confirm whether non-production environment has since been updated to mirror production data (A1–A8) so BukitTech can fully test the fix.
