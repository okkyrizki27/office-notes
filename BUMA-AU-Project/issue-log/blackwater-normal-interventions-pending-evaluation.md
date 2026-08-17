# Blackwater — Clear Backlog of 598 Pending "Normal Interventions"

| | |
|---|---|
| **ID** | BUMA-LOG-010 |
| **Project** | BUMA AU |
| **Reported by** | Benedict Panizza |
| **Date Raised** | 2026-08-12 12:52 PM WIB |
| **Priority** | N/A (Service Request — bulk data cleanup, not an Incident/Defect) |
| **Status** | Open — Scope agreed, execution not confirmed |
| **Date Done** | — |
| **Jira Ticket** | [BAA-13514](https://bukittechnology.atlassian.net/browse/BAA-13514) |
| **Handled by** | Okky (Bukit Technology Support) |
| **Waiting On** | Bukit Technology Support to confirm the decline was executed against the agreed scope |
| **Source** | [sources/blackwater-normal-interventions-pending-evaluation.pdf](sources/blackwater-normal-interventions-pending-evaluation.pdf) |
| **Last Verified** | 2026-08-17 |

## Description

Benedict requests Bukit Technology Support clear the backlog of 598 "Normal Interventions" pending evaluation at Blackwater, noting it is almost all outdated and the large backlog is stopping new ones from being actioned appropriately/promptly.

Screenshot attached (Interventions dashboard, Site = Blackwater) showing Pending Evaluation counts by severity:

| Severity | Total | Pending Evaluation | Actioned |
|---|---|---|---|
| CRITICAL | 90 | 1 | 89 |
| CAUTION | 148 | 61 | 438 |
| NORMAL | 1885 | 598 | 262 |
| IN REVIEW | 438 | 0 | 438 |

**Correction (2026-08-17):** an earlier version of this doc logged the request as resolved by a bulk decline at 2026-08-12 01:44 PM covering all 598 records. A fuller copy of the email thread ("decline normal interventions.pdf") shows that timestamp/action is **not** in the correspondence, and the actually-agreed scope is narrower than "all 598" — see Timeline and Resolution below.

## Timeline

| Date/Time (WIB) | By | Action | Ball moves to |
|---|---|---|---|
| 2026-08-12 12:52 PM | Benedict Panizza | Raises request: clear the 598 Normal Interventions pending evaluation at Blackwater; most are outdated and the backlog is blocking timely actioning of new ones. Cc Marius Zeil-Rolfe. Screenshot attached (severity breakdown above). | Bukit Technology Support |
| 2026-08-12 01:30 PM | Okky (BukitTech) | Acknowledges: "Sure, we will proceed with this request as soon as possible." | Bukit Technology Support |
| 2026-08-12 01:52 PM† | Okky (BukitTech) | Reports back after checking the data: oldest record dates back to **11-Aug-2025**. Shares IronPortal dashboard (Blackwater, NORMAL category, 598 Pending Evaluation, all other status columns "-") with the itemized record list (component, equipment no., WO number, intervention creation date). Asks Benedict to confirm scope — remove all of it, or keep the last month and only remove older data — and clarifies **the data cannot actually be removed, only its status can be updated to "Declined."** | Benedict Panizza / Marius Zeil-Rolfe |
| 2026-08-12 02:26 PM | Marius Zeil-Rolfe | "Please clear all the data and leave the last month for me to clear with justifications. Decline status is good, thanks." | Bukit Technology Support |

† *Printed in the source thread as "4:52 PM" — but that text is the quoted header Marius's own Outlook generated when he hit reply, rendered in his account's timezone (BUMA staff are Queensland-based, AEST/UTC+10, no daylight saving). Okky is WIB (UTC+7), a flat 3h behind. Corrected: 4:52 PM AEST − 3h = **1:52 PM WIB**, which resolves the apparent inversion — the thread is fully sequential once converted, no re-sequencing needed.*

## Resolution

Agreed scope (per Marius's reply): **decline all pending-evaluation Normal Interventions except the last month's**, which Marius will clear himself separately with justifications. Confirmed mechanism: status change to "Declined," since the records cannot be truly deleted.

**Not yet confirmed done** — this thread has no follow-up email showing Bukit Technology Support actually executed the decline against this agreed scope. The previously logged "declined at 01:44 PM, all 598" resolution is unsupported by this correspondence and has been retracted pending a real execution-confirmation email (or reconciliation against the Jira ticket [BAA-13514](https://bukittechnology.atlassian.net/browse/BAA-13514) history, since email here isn't synced to Jira per the [issue-log conventions](README.md#sumber-data--keterbatasan)).

## Revision History

- **2026-08-17:** Re-verified against the archived source PDF. Retracted the previously-logged "declined at 01:44 PM, all 598" resolution — unsupported by the actual thread — and corrected the agreed scope (all pending-evaluation records *except* the last month's, which Marius handles separately). Corrected one timestamp (04:52 PM → 01:52 PM) and reordered two rows, resolving a previously-unexplained inversion. Status reverted from Done to Open pending real execution confirmation.
