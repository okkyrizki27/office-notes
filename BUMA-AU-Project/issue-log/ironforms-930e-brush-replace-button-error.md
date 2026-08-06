# IronForms 930E Electrical Service — Comm Brush Replace Button Error (a4–a8)

| | |
|---|---|
| **Project** | BUMA AU |
| **Reported by** | Will Mullany |
| **Cc** | Justin Shaw, Traven Hooper, Benedict Panizza, Scott McBryde, Stuart Cameron, DL Blackwater Reliability |
| **Date Raised** | 2026-06-25 |
| **Status** | Open — being investigated by Bukit Technology Support |
| **Jira Ticket** | — |
| **Handled by** | Okky / Pradya (Bukit Technology Support) |

## Description

On the 930E-4 electrical service sheet in IronForms, the **Replace** button for Comm Brush items **a4–a8** does not work correctly:

- When a brush measurement is out of spec and the user clicks **Replace**, an **"Out Of Range"** error pops up then disappears after 1–2 seconds.
- The item is still evaluated/flagged as **out of spec** even after Replace is pressed, so the electrician ends up replacing the brush anyway.
- Because Replace effectively fails, sparkies are forced to enter a measurement lower than the previous value as a workaround, which makes every subsequent data point redundant — important service information is lost, and a defect/intervention is raised unnecessarily.
- Confirmed by Will (2026-07-06) to affect **all 930E electrical service sections, for all machines**, not just a specific unit.

## Timeline

- **2026-06-25** — Will raises the issue: a5–a8 Replace button throws an unknown error (both retarder grid box sections). Okky (BukitTech) acknowledges and will check root cause.
- **2026-06-26** — Pradya reports the Replace button worked in their non-production test when a bad value/rating (C/X) was entered, and asks Will to confirm the expected flow (measure → enter Current Value → click Replace → enter Replacement value). Will confirms the flow is correct but clarifies the error is specific to **a4–a8** (not a1–a3), and asks Pradya to confirm testing covered all of a1–a8.
- **2026-06-29** — Will explains that in production, since sparkies can't click Replace, they enter `0` as the last measurement instead (screenshot provided). Pradya explains their non-production environment's previous data only goes up to **A4**, so they could only test the replace scenario up to that point (Rating X). Pradya notes the Replace logic is intended to behave identically across A1–A8 and requests a screen recording to help identify the cause. Also requests **WO number** and **Equipment Number** for the affected service.
- **2026-07-06** — Will confirms this affects all 930E electrical service sections, on all machines.
- **2026-07-15** — Will asks why non-prod's available previous data stops at A4 when prod has data for all brushes, and whether non-prod can be updated to mirror prod so the actual failing scenario can be tested.
- **2026-07-16** — Pradya still trying to reproduce the production scenario in non-prod for A5–A8; will follow up.
- **2026-08-06 (7:58 AM)** — Will sends a concrete reproduction with WO **4267274**, Equipment **DT0768**, 500hr service (confirmed consistent across all 930E trucks):
  1. Out-of-spec measurement entered on Brush 6 (spec 44mm, entered 11mm) → correctly flagged "Out of spec".
  2. Replace button pressed.
  3. "Out Of Range" error pops up, disappears after 1–2 seconds.
  4. Brush is still evaluated as out of spec — electrician replaces the brush anyway, and a defect/intervention is raised unnecessarily.
  Videos of the reproduction offered via shared folder (too large to attach); a network HAR log of the replicated fault was attached.
- **2026-08-06 (8:58 AM)** — Pradya (BukitTech) acknowledges receipt of the detailed info/attachments, confirms the team will investigate the root cause and follow up.

## Outstanding / Next Steps

- Bukit Technology Support to confirm root cause using the HAR log + reproduction steps from the 2026-08-06 email.
- Need to set up a shared folder for Will to upload the full reproduction videos (too large for email).
- Confirm whether non-production environment has since been updated to mirror production data (A1–A8) so BukitTech can fully test the fix.
