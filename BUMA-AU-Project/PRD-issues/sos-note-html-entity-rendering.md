# SOS Note — Escaped HTML Entities Not Rendered

| | |
|---|---|
| **Project** | BUMA AU |
| **Reported by** | Benedict Panizza |
| **Date Raised** | 2026-08-04 |
| **Status** | Open |
| **Jira Ticket** | [BAA-13512](https://bukittechnology.atlassian.net/browse/BAA-13512) (parent: [BAA-13445](https://bukittechnology.atlassian.net/browse/BAA-13445)) |
| **Assignee** | Agus Setiadi |

## Description

Minor text rendering issue in the SOS Note field of the Oil Sample tool tip. The string `&lt;strong&gt;Suggested Action:&lt;/strong&gt;` should render as **Suggested Action:** (bold), but instead the literal escaped characters are shown as-is.

Requested fix — either:
1. Decode/render the entities so the text displays as intended (bold "Suggested Action:"), **or**
2. Strip those characters from the SOS Note string entirely.

## Investigation Note

Confirmed in the raw API data (`from-api/sos_2026-07-06.json`, `interpretation` field) — the lab's source text itself contains the double-encoded entity `&lt;strong&gt;Suggested Action:&lt;/strong&gt;` (i.e. `<strong>` tags that were HTML-escaped before being stored). Example:

> "Viscosity is consistent with oil type indicated. Nickel is high. ... Other test results appear acceptable. &lt;strong&gt;Suggested Action:&lt;/strong&gt; Inspect the magnetic plug for abnormal debris. ..."

This is present across multiple samples' `interpretation` text, not a one-off. Since it's already escaped in the source, the tool tip needs to unescape once (to get real `<strong>` tags) before rendering as HTML, or strip the tag text per option 2 above.

## Reference Screenshot

Tool tip example (Lab Number 23502532) — SOS Note shows literal `&lt;strong&gt;Suggested Action:&lt;/strong&gt;` inline in the note text.
