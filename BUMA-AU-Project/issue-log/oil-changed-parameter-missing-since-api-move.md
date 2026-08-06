# Oil Changed Parameter Missing Since Move to API

| | |
|---|---|
| **Project** | BUMA AU |
| **Reported by** | Benedict Panizza |
| **Date Raised** | 2026-08-04 |
| **Status** | Open |
| **Jira Ticket** | [BAA-13511](https://bukittechnology.atlassian.net/browse/BAA-13511) (parent: [BAA-13445](https://bukittechnology.atlassian.net/browse/BAA-13445)) |
| **Assignee** | Agus Setiadi |

## Description

In the Oil Sample tool tip, the **Oil Changed** parameter has not been present since the move to the API (previously sourced from the web scrapper). Reporter suspects it is not a site-entry issue, because if site teams don't fill it out correctly, SOS lab defaults the Oil Changed parameter to "No" (i.e. it would still show a value, just possibly wrong — not blank).

## Investigation Note

The underlying API data (`from-api/sos_2026-07-06.json`, flattened into `sos_samples_flat.csv`) **does** contain this field as `fluid_changed` (`Y`/`N` values, populated). So the value is not missing from the API source — the tool tip is likely not mapping/reading `fluid_changed` from the API response. Needs check on the tool tip's data-binding logic post-API-migration.

## Reference Screenshot

Tool tip example (Lab Number 23502532, unit SMU 80859, sample 24/07/2026) shows `Oil Changed :` with no value rendered.
