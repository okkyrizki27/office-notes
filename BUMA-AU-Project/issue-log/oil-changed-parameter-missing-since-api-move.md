# Oil Changed Parameter Missing Since Move to API

| | |
|---|---|
| **Project** | BUMA AU |
| **Reported by** | Benedict Panizza |
| **Date Raised** | 2026-08-04 06:42 AM WIB |
| **Priority** | P3 |
| **Status** | Done |
| **Jira Ticket** | [BAA-13511](https://bukittechnology.atlassian.net/browse/BAA-13511) (parent: [BAA-13445](https://bukittechnology.atlassian.net/browse/BAA-13445)) |
| **Assignee** | Agus Setiadi |
| **Date Done** | 2026-08-07 |

## Description

In the Oil Sample tool tip, the **Oil Changed** parameter has not been present since the move to the API (previously sourced from the web scrapper). Reporter suspects it is not a site-entry issue, because if site teams don't fill it out correctly, SOS lab defaults the Oil Changed parameter to "No" (i.e. it would still show a value, just possibly wrong — not blank).

Reported together with the sibling issue [SOS Note — Escaped HTML Entities Not Rendered](sos-note-html-entity-rendering.md) in the same "Oil Data Bug" email thread.

## Investigation Note

The underlying API data (`from-api/sos_2026-07-06.json`, flattened into `sos_samples_flat.csv`) **does** contain this field as `fluid_changed` (`Y`/`N` values, populated). So the value is not missing from the API source — the tool tip is likely not mapping/reading `fluid_changed` from the API response. Needs check on the tool tip's data-binding logic post-API-migration.

Root cause confirmed during the fix: the API returns `Y`/`N`, while the tool tip's existing logic expected the previous source's `Yes`/`No` values — a conversion step was missing after the API migration.

## Timeline

| Date/Time (WIB) | By | Action | Ball moves to |
|---|---|---|---|
| 2026-08-04 06:42 AM | Benedict Panizza | Raises "Oil Data Bug" — reports two minor bugs together: Oil Changed parameter missing (this issue) and SOS Note escaped HTML entities (sibling issue). | Bukit Technology Support |
| 2026-08-04 08:46 AM | Okky (BukitTech) | Acknowledges: "We will investigate this issue." | Bukit Technology Support |
| 2026-08-07 12:25 AM | Okky (BukitTech) | Reports both fixes already done in UAT; asks whether a CAB is required for these minor fixes, or if the logic can just be updated in the pipeline. | Benedict Panizza |
| 2026-08-07 05:08 AM | Benedict Panizza | Agrees no CAB is needed — remediation of an implementation that already had a CAB (the original API implementation); asks Okky to outline the changes made. | Bukit Technology Support |
| 2026-08-07 08:35 AM* | Benedict Panizza | "I am happy for that to be implemented." *(Printed timestamp precedes the 11:34 AM email below in the source thread, though content-wise it reads as a reply to it — captured as printed, not re-sequenced.)* | Bukit Technology Support |
| 2026-08-07 11:34 AM | Okky (BukitTech) | Outlines the fix: (1) added conversion logic for the API's `Y`/`N` response into the previous `Yes`/`No` values for Oil Changed; (2) implemented an HTML tag remover for the oil analysis sample Note (fixes the sibling issue). States will deploy to PRD shortly if no objection. | Benedict Panizza |
| 2026-08-07 01:18 PM | Okky (BukitTech) | Confirms rectification implemented in PRD; shares before/after IronPortal dashboard screenshots (Oil Changed field now shows "No" instead of blank); requests Benedict's validation. | Benedict Panizza |

## Resolution

Fix deployed to PRD 2026-08-07. Reporter confirmed the issue is closed as of this email thread.

## SLA Notes

- Priority P3 → Response/Restore clock runs on Business Hours/Business Days only (excludes weekend).
- SLA-pause window: **2026-08-07 12:25 AM → 05:08 AM** (~4h43m) while BukitTech waited on Benedict/BUMA's decision on whether a CAB was required.
- Restore achieved well within the P3 target (≤5 Hari Kerja): raised 2026-08-04 (Tue), fix already validated in UAT by 2026-08-07 (Fri) — within 3 business days (Wed–Fri).

## Reference Screenshot

Tool tip example (Lab Number 23502532, unit SMU 80859, sample 24/07/2026) shows `Oil Changed :` with no value rendered (pre-fix).
