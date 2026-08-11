# IronPortal Historical Page — Slow Performance, No Data on Filter, Download All Error

| | |
|---|---|
| **Project** | BUMA AU |
| **Reported by** | Benedict Panizza |
| **Date Raised** | 2026-08-10 11:13 AM WIB |
| **Priority** | N/A (Deprecated feature — not a Defect) |
| **Status** | Done |
| **Jira Ticket** | — |
| **Handled by** | Okky / Pradya (Bukit Technology Support) |
| **Waiting On** | — (Bukit Technology Support to decide/schedule removing Historical page from Admin role access, per Pradya's proposal) |

## Description

The IronPortal **Historical** page has three related problems reported by Benedict:

- The page is slow overall, particularly when choosing filters (Site, Group, Model, Equipment, Component).
- With filters set to Site = **Blackwater**, Group = **Dump Truck**, Model = **930E-4 HPI**, Equipment = **DT0700**, Component = **ENGINE**, the results table returns **No Data** (showing 0 to 0 of 0 entries) — unclear whether this is expected for that combination or a bug.
- Clicking **Download All** produces a **file extension error** instead of downloading.

## Timeline

| Date/Time (WIB) | By | Action | Ball moves to |
|---|---|---|---|
| 2026-08-10 11:13 AM | Benedict Panizza | Raises issue: Historical page slow (especially filters); no data returned for the filter combination above; Download All throws a file extension error. Screenshot attached. | Bukit Technology Support |
| 2026-08-10 11:58 AM | Okky (BukitTech) | Acknowledges, will investigate root cause and keep Benedict updated. | Bukit Technology Support |
| 2026-08-11 01:18 PM | Pradya (BukitTech) | Explains root cause: the IronPortal Historical page should no longer be available — it's been replaced by the Dynamic Graph feature. It's currently still reachable only because it's accessible to users with the Admin role; proposes removing it from Admin access to ensure consistency across the system. Notes the API backing the Historical page was already decommissioned when Dynamic Graph went live, so the page's filter and download functionality are no longer supported (explains both the "No Data" filter result and the Download All file extension error). | Benedict Panizza |
| 2026-08-11 10:20 AM | Benedict Panizza | "Thank you for that explanation. I will keep that in mind." *(Note: timestamp as printed in the Outlook thread is earlier than Pradya's 01:18 PM message it replies to — logged as printed, order not re-sequenced, same caveat as seen in other threads.)* | Bukit Technology Support |

## SLA Notes

- Root cause: Historical page is a deprecated feature (superseded by Dynamic Graph) still reachable via Admin role, with its backing API already decommissioned — not a functional defect, but a leftover access/cleanup item.
- Benedict acknowledged the explanation; no further action needed from BUMA side.

## Outstanding / Next Steps

- Bukit Technology Support to decide/schedule removing the Historical page from Admin role access, per Pradya's proposal, to ensure consistency across the system.
