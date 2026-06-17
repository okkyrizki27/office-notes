# Jira Ticket Creation Template

Gunakan template ini setiap kali minta Claude membuat ticket Jira.
Cukup copy-paste dan isi field-nya, lalu kirim ke Claude.

---

## Template

```
- Project        : (key Jira, e.g. BAA, IAMS30, CRF)
- Parent         : (key ticket parent/epic, e.g. BAA-13445) — opsional
- Sprint ID      : (nomor sprint, e.g. 2132) — opsional
- Board          : (nama board, e.g. BAA board) — opsional
- Issue Type     : (Story / Task / Bug / Sub-task — default: Story)
- Prefix         : (e.g. [IronPortal] [PBI]) — opsional
- Summary/Title  : (judul singkat ticket)
- Detail         : (deskripsi singkat apa yang perlu dilakukan)
- Objective      : (user story: As a ..., I can ...) — opsional tapi dianjurkan
- Assignee       : (nama lengkap assignee)
- Priority       : (Highest / High / Medium / Low — default: Medium) — opsional
- Story Points   : (angka SP) — opsional
```

---

## Keterangan Field

| Field | Wajib | Keterangan |
|-------|-------|------------|
| Project | ✅ | Key project Jira (BAA, IAMS30, CRF, dll) |
| Parent | ❌ | Key Epic atau parent ticket |
| Sprint ID | ❌ | Nomor ID sprint (bukan nama sprint) |
| Board | ❌ | Nama board, hanya untuk referensi |
| Issue Type | ❌ | Default: Story (new feature) |
| Prefix | ❌ | Tag di depan summary, e.g. [IronPortal] [PBI] |
| Summary/Title | ✅ | Judul ticket yang jelas dan singkat |
| Detail | ✅ | Penjelasan singkat apa yang harus dikerjakan |
| Objective | ❌ | User story format untuk kejelasan scope |
| Assignee | ✅ | Nama lengkap orang yang akan mengerjakan |
| Priority | ❌ | Default: Medium |
| Story Points | ❌ | Estimasi kompleksitas (1, 2, 3, 5, 8, 13) |

---

## Contoh Penggunaan

```
- Project        : BAA
- Parent         : BAA-13445
- Sprint ID      : 2132
- Board          : BAA board
- Issue Type     : Story
- Prefix         : [IronPortal] [PBI]
- Summary/Title  : Add VisionLink and 3DP Hornet Sync Data Monitoring
- Detail         : Add monitoring page for VisionLink and 3DP Hornet daily sync
- Objective      : As an admin, I can monitor sync data from VisionLink and 3DP Hornet 
                   and follow up quickly if data is not synced to IronPortal
- Assignee       : Herianto Salim
- Priority       : Medium
- Story Points   : 3
```

---

*Referensi ticket yang dibuat Claude: [[feedback-jira-ticket-creation]]*
