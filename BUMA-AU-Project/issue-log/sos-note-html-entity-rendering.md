# SOS Note — Escaped HTML Entities Not Rendered

| | |
|---|---|
| **Project** | BUMA AU |
| **Reported by** | Benedict Panizza |
| **Date Raised** | 2026-08-04 06:42 AM WIB |
| **Priority** | P4 |
| **Status** | Done |
| **Jira Ticket** | [BAA-13512](https://bukittechnology.atlassian.net/browse/BAA-13512) (parent: [BAA-13445](https://bukittechnology.atlassian.net/browse/BAA-13445)) |
| **Assignee** | Agus Setiadi |
| **Date Done** | 2026-08-07 |

## Description

Minor text rendering issue in the SOS Note field of the Oil Sample tool tip. The string `&lt;strong&gt;Suggested Action:&lt;/strong&gt;` should render as **Suggested Action:** (bold), but instead the literal escaped characters are shown as-is.

Requested fix — either:
1. Decode/render the entities so the text displays as intended (bold "Suggested Action:"), **or**
2. Strip those characters from the SOS Note string entirely.

Reported together with the sibling issue [Oil Changed Parameter Missing Since Move to API](oil-changed-parameter-missing-since-api-move.md) in the same "Oil Data Bug" email thread.

## Investigation Note

Confirmed in the raw API data (`from-api/sos_2026-07-06.json`, `interpretation` field) — the lab's source text itself contains the double-encoded entity `&lt;strong&gt;Suggested Action:&lt;/strong&gt;` (i.e. `<strong>` tags that were HTML-escaped before being stored). Example:

> "Viscosity is consistent with oil type indicated. Nickel is high. ... Other test results appear acceptable. &lt;strong&gt;Suggested Action:&lt;/strong&gt; Inspect the magnetic plug for abnormal debris. ..."

This is present across multiple samples' `interpretation` text, not a one-off. Since it's already escaped in the source, the tool tip needs to unescape once (to get real `<strong>` tags) before rendering as HTML, or strip the tag text per option 2 above.

Fix implemented: option 2 — an HTML tag remover was applied to the oil analysis sample Note.

## Timeline

Same thread as the sibling issue — full back-and-forth documented in [oil-changed-parameter-missing-since-api-move.md](oil-changed-parameter-missing-since-api-move.md#timeline); key milestones for this specific fix:

| Date/Time (WIB) | By | Action | Ball moves to |
|---|---|---|---|
| 2026-08-04 06:42 AM | Benedict Panizza | Raises "Oil Data Bug" — reports two minor bugs together: SOS Note escaped HTML entities (this issue) and Oil Changed parameter missing (sibling issue). | Bukit Technology Support |
| 2026-08-04 08:46 AM | Okky (BukitTech) | Acknowledges: "We will investigate this issue." | Bukit Technology Support |
| 2026-08-07 12:25 AM | Okky (BukitTech) | Reports both fixes already done in UAT; asks whether a CAB is required for these minor fixes. | Benedict Panizza |
| 2026-08-07 05:08 AM | Benedict Panizza | Agrees no CAB is needed; asks Okky to outline the changes made. | Bukit Technology Support |
| 2026-08-07 11:34 AM | Okky (BukitTech) | Outlines the fix: implemented an HTML tag remover for the oil analysis sample Note (plus the sibling issue's fix). Will deploy to PRD shortly if no objection. | Benedict Panizza |
| 2026-08-07 01:18 PM | Okky (BukitTech) | Confirms rectification implemented in PRD; requests Benedict's validation. | Benedict Panizza |

## Resolution

HTML tag remover deployed to PRD 2026-08-07. Reporter confirmed the issue is closed as of this email thread.

## SLA Notes

- Priority P4 → Response/Restore clock runs on Business Hours/Business Days only (excludes weekend).
- SLA-pause window: **2026-08-07 12:25 AM → 05:08 AM** (~4h43m) while BukitTech waited on Benedict/BUMA's decision on whether a CAB was required.
- Restore well within the P4 target (≤10 Hari Kerja): raised 2026-08-04 (Tue), fix live in PRD by 2026-08-07 (Fri) — 3 business days.

## Reference Screenshot

Tool tip example (Lab Number 23502532) — SOS Note shows literal `&lt;strong&gt;Suggested Action:&lt;/strong&gt;` inline in the note text (pre-fix).
