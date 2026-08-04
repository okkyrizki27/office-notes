# Jira Projects Reference

Referensi project, board, dan issue type ID Jira yang sudah pernah dipakai. File ini ada di folder OneDrive (`Jira/`) supaya bisa diakses dari device manapun — beda dengan memory Claude Code yang tersimpan lokal per-device.

Kredensial API: `Jira/token/jira-api-token.md` (`JIRA_EMAIL`, `JIRA_TOKEN`, `JIRA_URL`).

---

## IAMS30 — IAMS 3.0 (BUMA ID / MKP)

URL: https://bukittechnology.atlassian.net/browse/IAMS30

| ID | Name | Subtask | Hierarchy Level |
|----|------|---------|-----------------|
| `10258` | Story | false | 0 |
| `10259` | Task | false | 0 |
| `10260` | Bug | false | 0 |
| `10261` | Epic | false | 1 |
| `10262` | Sub Task | true | -1 |
| `10523` | Testing | false | 0 |

---

## BAA — BUMA AU AM

- Project name: **BUMA AU AM**, key: **BAA** (id `10134`)
- Board: **BAA Board**, Id: `40`
- Epic **[BAA-13445](https://bukittechnology.atlassian.net/browse/BAA-13445)** — "PRD Improvement and Issue Support" — parent untuk ticket-ticket dari dokumentasi `BUMA-AU-Project/PRD-issues/`

| ID | Name | Subtask | Hierarchy Level |
|----|------|---------|-----------------|
| `10000` | Epic | false | 1 |
| `10015` | Story (new feature) | false | 0 |
| `10203` | Change Request | false | 0 |
| `10205` | Documentation | false | 0 |
| `10011` | Bug | false | 0 |
| `10009` | Task | false | 0 |
| `10204` | Testing | false | 0 |
| `10010` | Sub-task | true | -1 |
| `10200` | Bug-intest | true | -1 |
| `10231` | Sub-test | true | -1 |

---

## Cara Pakai

- Pakai `issuetype.id` langsung dari tabel di atas saat create ticket — tidak perlu fetch `/rest/api/3/issue/createmeta` ulang.
- Cari `accountId` assignee via `/rest/api/3/user/search?query=<nama>` sebelum create (belum ada tabel roster accountId di sini).
- Kalau project belum ada di file ini, fetch createmeta dan **tambahkan ke file ini** supaya tersedia di device lain juga — jangan hanya simpan ke memory.
