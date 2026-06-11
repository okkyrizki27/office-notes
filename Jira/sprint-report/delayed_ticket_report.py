"""
Delayed and Reopen Ticket Report
Run: python delayed_ticket_report.py
Output: delayed_ticket_report_YYYYMMDD.md / .html / .pdf

Logic:
  1. Hitung baseline rata-rata cycle time (To Do -> DEV DONE) per Story Point,
     terpisah untuk MKP Team (Migration/Migrating Digiplan) dan
     BUMA ID Team (Release 4.0.x / 3.1.0), dari 5 sprint terakhir yang closed.
  2. Untuk setiap active sprint, ambil ticket yang statusnya "In Progress".
  3. Hitung berapa lama ticket sudah berada di "In Progress" (sejak keluar
     dari To Do/Backlog).
  4. Bandingkan dengan baseline rata-rata untuk SP & team yang sesuai.
  5. Ticket dianggap "delayed" jika waktu berjalan > baseline rata-rata.
"""

import urllib.request, base64, json, os, subprocess, re
from datetime import datetime, timezone

DONE_STATUSES     = {"Done", "Closed", "QA PASSED"}
PROGRESS_STATUSES = {"In Progress", "DEV DONE", "QA TEST", "Re-open"}
TODO_STATUSES     = {"To Do", "Backlog"}

TARGET_SP = [1, 2, 3, 5, 8]
BASELINE_SPRINT_COUNT = 5  # jumlah sprint closed terakhir per tim untuk baseline

BOARD_ID = 93
PROJECT  = "IAMS30"

# ── CONFIG / AUTH ─────────────────────────────────────────────────────────────
def _load_jira_credentials():
    token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "token", "jira-api-token.md")
    with open(token_file, encoding="utf-8") as f:
        content = f.read()
    def _val(key):
        m = re.search(rf'^{key}="([^"]+)"', content, re.MULTILINE)
        if not m:
            raise ValueError(f"{key} not found in jira-api-token.md")
        return m.group(1)
    return _val("JIRA_EMAIL"), _val("JIRA_TOKEN"), _val("JIRA_URL")

EMAIL, TOKEN, BASE_URL = _load_jira_credentials()
_CREDS = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()

def get(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {_CREDS}", "Accept": "application/json"
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def sp(fields):
    v = fields.get("customfield_10016")
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def parse_dt(s):
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")

def status_transitions(issue):
    histories = issue.get("changelog", {}).get("histories", [])
    transitions = []
    for h in histories:
        created = h["created"]
        for item in h.get("items", []):
            if item["field"] == "status":
                transitions.append((created, item.get("fromString"), item.get("toString")))
    transitions.sort(key=lambda t: t[0])
    return transitions

# ── FETCH ISSUES (with changelog) ────────────────────────────────────────────
def fetch_sprint_issues(sprint_id):
    issues = []
    start_at = 0
    while True:
        url = (f"{BASE_URL}/rest/agile/1.0/sprint/{sprint_id}/issue"
               f"?fields=status,customfield_10016,issuetype"
               f"&expand=changelog&maxResults=50&startAt={start_at}")
        res = get(url)
        batch = res.get("issues", [])
        issues += batch
        total = res.get("total", 0)
        start_at += len(batch)
        if start_at >= total or not batch:
            break
    return issues

def fetch_sprint_issues_full(sprint_id):
    issues = []
    start_at = 0
    while True:
        url = (f"{BASE_URL}/rest/agile/1.0/sprint/{sprint_id}/issue"
               f"?fields=status,customfield_10016,summary,assignee,priority,created"
               f"&expand=changelog&maxResults=50&startAt={start_at}")
        res = get(url)
        batch = res.get("issues", [])
        issues += batch
        total = res.get("total", 0)
        start_at += len(batch)
        if start_at >= total or not batch:
            break
    return issues

# ── BASELINE: cycle time To Do -> DEV DONE per SP ────────────────────────────
def compute_dev_done_hours(issue):
    start_time = None
    end_time = None
    for created, from_s, to_s in status_transitions(issue):
        if start_time is None and from_s in TODO_STATUSES and (
            to_s in PROGRESS_STATUSES or to_s in DONE_STATUSES
        ):
            start_time = created
        if end_time is None and to_s == "DEV DONE":
            end_time = created
    if start_time is None or end_time is None:
        return None
    delta = parse_dt(end_time) - parse_dt(start_time)
    hours = delta.total_seconds() / 3600
    return hours if hours >= 0 else None

def build_baseline(sprint_map):
    data = {sp_val: [] for sp_val in TARGET_SP}
    for sprint_id in sprint_map:
        for issue in fetch_sprint_issues(sprint_id):
            sp_val = sp(issue["fields"])
            if sp_val not in TARGET_SP:
                continue
            h = compute_dev_done_hours(issue)
            if h is not None:
                data[sp_val].append(h)
    baseline = {}
    for sp_val, vals in data.items():
        baseline[sp_val] = (sum(vals) / len(vals)) if vals else None
    return baseline

# ── IN PROGRESS TICKETS: time since entered progress ─────────────────────────
def count_reopens(issue):
    """Number of times the ticket was moved back to 'Re-open' status."""
    return sum(1 for _, _, to_s in status_transitions(issue) if to_s == "Re-open")

def time_in_progress_hours(issue, sprint_start=None):
    """Hours since the ticket entered progress, capped to sprint start (whichever is more recent)."""
    start_time = None
    for created, from_s, to_s in status_transitions(issue):
        if start_time is None and from_s in TODO_STATUSES and (
            to_s in PROGRESS_STATUSES or to_s in DONE_STATUSES
        ):
            start_time = created
    if start_time is None:
        # Tidak pernah pindah dari To Do/Backlog -> pakai created date
        start_time = issue["fields"]["created"]
    if sprint_start is not None and parse_dt(sprint_start) > parse_dt(start_time):
        start_time = sprint_start
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    delta = now - parse_dt(start_time)
    return delta.total_seconds() / 3600, start_time

# ── MAIN ──────────────────────────────────────────────────────────────────────
def team_for_sprint(name, baselines=None):
    key = "MKP Team" if "Digiplan" in name else "BUMA ID Team"
    if baselines is None:
        return key
    return key, baselines[key]

print("Fetching sprints...")
all_sprints = []
start_at = 0
while True:
    res = get(f"{BASE_URL}/rest/agile/1.0/board/{BOARD_ID}/sprint?maxResults=50&startAt={start_at}")
    vals = res.get("values", [])
    all_sprints += vals
    if res.get("isLast", True) or not vals:
        break
    start_at += 50

active_sprints = [s for s in all_sprints if s["state"] == "active"]
closed_sprints = [s for s in all_sprints if s["state"] == "closed"]
closed_sprints.sort(key=lambda x: x.get("endDate", ""), reverse=True)

mkp_closed  = [s for s in closed_sprints if team_for_sprint(s["name"]) == "MKP Team"][:BASELINE_SPRINT_COUNT]
buma_closed = [s for s in closed_sprints if team_for_sprint(s["name"]) == "BUMA ID Team"][:BASELINE_SPRINT_COUNT]

print(f"Baseline sprints (MKP Team): {[s['name'] for s in mkp_closed]}")
print(f"Baseline sprints (BUMA ID Team): {[s['name'] for s in buma_closed]}")

print("Building baseline (MKP Team)...")
baseline_mkp = build_baseline({s["id"]: s["name"] for s in mkp_closed})
print("Building baseline (BUMA ID Team)...")
baseline_buma = build_baseline({s["id"]: s["name"] for s in buma_closed})

baselines = {"MKP Team": baseline_mkp, "BUMA ID Team": baseline_buma}

delayed_by_sprint = []
for sprint_obj in active_sprints:
    team_name, baseline = team_for_sprint(sprint_obj["name"], baselines)
    print(f"Checking '{sprint_obj['name']}' ({team_name})...")
    issues = fetch_sprint_issues_full(sprint_obj["id"])
    rows = []
    for issue in issues:
        f = issue["fields"]
        if f["status"]["name"] != "In Progress":
            continue
        sp_val = sp(f)
        elapsed_h, start_time = time_in_progress_hours(issue, sprint_obj.get("startDate"))
        baseline_h = baseline.get(sp_val) if sp_val in TARGET_SP else None
        if baseline_h is None:
            status_flag = "no-baseline"
            delay_days = None
        elif elapsed_h > baseline_h:
            status_flag = "delayed"
            delay_days = (elapsed_h - baseline_h) / 24
        else:
            status_flag = "ontrack"
            delay_days = None

        rows.append({
            "key": issue["key"],
            "summary": f["summary"][:70] + ("..." if len(f["summary"]) > 70 else ""),
            "assignee": (f.get("assignee") or {}).get("displayName", "Unassigned"),
            "priority": (f.get("priority") or {}).get("name", "-"),
            "sp": sp_val,
            "started": start_time[:10],
            "sprint_start": sprint_obj.get("startDate", "")[:10],
            "elapsed_days": elapsed_h / 24,
            "baseline_days": (baseline_h / 24) if baseline_h is not None else None,
            "delay_days": delay_days,
            "status_flag": status_flag,
        })

    reopen_rows = []
    for issue in issues:
        f = issue["fields"]
        reopen_count = count_reopens(issue)
        if reopen_count > 0:
            reopen_rows.append({
                "key": issue["key"],
                "summary": f["summary"][:70] + ("..." if len(f["summary"]) > 70 else ""),
                "status": f["status"]["name"],
                "assignee": (f.get("assignee") or {}).get("displayName", "Unassigned"),
                "priority": (f.get("priority") or {}).get("name", "-"),
                "reopen_count": reopen_count,
            })

    delayed_by_sprint.append({
        "sprint": sprint_obj,
        "team": team_name,
        "rows": rows,
        "reopen_rows": reopen_rows,
    })

# ── BUILD MARKDOWN ────────────────────────────────────────────────────────────
today   = datetime.now().strftime("%d %B %Y")
today_f = datetime.now().strftime("%Y%m%d")
lines = []

lines.append("# Delayed and Reopen Ticket Report")
lines.append(f"**Generated:** {today}  |  **Project:** {PROJECT}  |  **Board:** IAMS 3.0\n")
lines.append("Report ini membandingkan waktu ticket berstatus **In Progress** saat ini "
              "dengan rata-rata historis waktu pengerjaan **To Do → DEV DONE** "
              "(5 sprint terakhir per tim) untuk Story Point yang sama. "
              "Ticket dianggap **delayed** jika sudah In Progress lebih lama dari rata-rata tersebut.\n")
lines.append("---\n")

# Baseline tables
lines.append("## Baseline Rata-rata (To Do -> DEV DONE)\n")
lines.append("| Story Point | MKP Team (hari) | BUMA ID Team (hari) |")
lines.append("|-------------|------------------|----------------------|")
for sp_val in TARGET_SP:
    m = baseline_mkp.get(sp_val)
    b = baseline_buma.get(sp_val)
    m_str = f"{m/24:.2f}" if m is not None else "-"
    b_str = f"{b/24:.2f}" if b is not None else "-"
    lines.append(f"| {sp_val} | {m_str} | {b_str} |")
lines.append("")
lines.append("---\n")

total_delayed = 0
for d in delayed_by_sprint:
    sprint_obj = d["sprint"]
    rows = d["rows"]
    delayed_rows = [r for r in rows if r["status_flag"] == "delayed"]
    ontrack_rows = [r for r in rows if r["status_flag"] == "ontrack"]
    nobase_rows  = [r for r in rows if r["status_flag"] == "no-baseline"]
    total_delayed += len(delayed_rows)

    lines.append(f"## {sprint_obj['name']} — {d['team']}\n")
    lines.append(f"Total ticket In Progress: **{len(rows)}**  |  "
                  f"Delayed: **{len(delayed_rows)}**  |  "
                  f"On Track: **{len(ontrack_rows)}**  |  "
                  f"No Baseline (SP di luar 1/2/3/5/8): **{len(nobase_rows)}**\n")

    if delayed_rows:
        lines.append("### 🔴 Delayed Tickets\n")
        lines.append("| Key | Summary | Assignee | SP | Started | Sprint Start | Elapsed (hari) | Baseline (hari) | Delay (hari) | Priority |")
        lines.append("|-----|---------|----------|----|---------|--------------|-----------------|-------------------|---------------|----------|")
        for r in sorted(delayed_rows, key=lambda x: -x["delay_days"]):
            lines.append(
                f"| [{r['key']}]({BASE_URL}/browse/{r['key']}) | {r['summary']} | {r['assignee']} | "
                f"{r['sp']:.0f} | {r['started']} | {r['sprint_start']} | {r['elapsed_days']:.1f} | "
                f"{r['baseline_days']:.1f} | {r['delay_days']:.1f} | {r['priority']} |"
            )
        lines.append("")
    else:
        lines.append("Tidak ada ticket yang delayed di sprint ini.\n")

    if ontrack_rows:
        lines.append("### 🟢 On Track Tickets\n")
        lines.append("| Key | Summary | Assignee | SP | Started | Elapsed (hari) | Baseline (hari) | Priority |")
        lines.append("|-----|---------|----------|----|---------|-----------------|-------------------|----------|")
        for r in sorted(ontrack_rows, key=lambda x: -x["elapsed_days"]):
            lines.append(
                f"| [{r['key']}]({BASE_URL}/browse/{r['key']}) | {r['summary']} | {r['assignee']} | "
                f"{r['sp']:.0f} | {r['started']} | {r['elapsed_days']:.1f} | "
                f"{r['baseline_days']:.1f} | {r['priority']} |"
            )
        lines.append("")

    if nobase_rows:
        lines.append("### ⚪ No Baseline (SP tidak termasuk 1/2/3/5/8)\n")
        lines.append("| Key | Summary | Assignee | SP | Started | Elapsed (hari) | Priority |")
        lines.append("|-----|---------|----------|----|---------|-----------------|----------|")
        for r in sorted(nobase_rows, key=lambda x: -x["elapsed_days"]):
            sp_str = f"{r['sp']:.0f}" if r["sp"] is not None else "-"
            lines.append(
                f"| [{r['key']}]({BASE_URL}/browse/{r['key']}) | {r['summary']} | {r['assignee']} | "
                f"{sp_str} | {r['started']} | {r['elapsed_days']:.1f} | {r['priority']} |"
            )
        lines.append("")

    reopen_rows = d["reopen_rows"]
    if reopen_rows:
        lines.append("### 🔁 Reopened Tickets\n")
        lines.append("| Key | Summary | Status | Assignee | Reopen Count | Priority |")
        lines.append("|-----|---------|--------|----------|--------------|----------|")
        for r in sorted(reopen_rows, key=lambda x: -x["reopen_count"]):
            lines.append(
                f"| [{r['key']}]({BASE_URL}/browse/{r['key']}) | {r['summary']} | {r['status']} | "
                f"{r['assignee']} | {r['reopen_count']} | {r['priority']} |"
            )
        lines.append("")
    else:
        lines.append("Tidak ada ticket yang pernah reopen di sprint ini.\n")

    lines.append("---\n")

lines.append(f"**Total ticket delayed (semua sprint aktif): {total_delayed}**\n")
lines.append("---")
lines.append(f"*Auto-generated by delayed_ticket_report.py — {today}*")

md_content = "\n".join(lines)

# ── SAVE ──────────────────────────────────────────────────────────────────────
out_dir  = os.path.dirname(os.path.abspath(__file__))
html_dir = os.path.join(out_dir, "html")
md_dir   = os.path.join(out_dir, "md")
pdf_dir  = os.path.join(out_dir, "pdf")
for d_ in (html_dir, md_dir, pdf_dir):
    os.makedirs(d_, exist_ok=True)

md_file = os.path.join(md_dir, f"delayed_ticket_report_{today_f}.md")
with open(md_file, "w", encoding="utf-8") as f:
    f.write(md_content)
print(f"\nMarkdown saved: {md_file}")

# ── HTML ──────────────────────────────────────────────────────────────────────
html_file = os.path.join(html_dir, f"delayed_ticket_report_{today_f}.html")
pdf_file  = os.path.join(pdf_dir, f"Delayed Ticket Report {today_f}.pdf")

def md_to_html(md):
    html_lines = []
    in_table = False
    for line in md.split("\n"):
        if line.startswith("### "): html_lines.append(f"<h3>{line[4:]}</h3>"); continue
        if line.startswith("## "):  html_lines.append(f"<h2>{line[3:]}</h2>"); continue
        if line.startswith("# "):   html_lines.append(f"<h1>{line[2:]}</h1>"); continue

        if line.strip() == "---":
            if in_table: html_lines.append("</table>"); in_table = False
            html_lines.append("<hr>"); continue

        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c.replace("-", "").replace(":", "")) == set() for c in cells):
                continue
            if not in_table:
                html_lines.append('<table>')
                in_table = True
                tag = "th"
            else:
                tag = "td"

            def fmt_cell(c):
                c = re.sub(r'`([^`]+)`', r'<code>\1</code>', c)
                c = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', c)
                c = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', c)
                c = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', c)
                return c

            html_lines.append("<tr>" + "".join(f"<{tag}>{fmt_cell(c)}</{tag}>" for c in cells) + "</tr>")
            continue
        else:
            if in_table: html_lines.append("</table>"); in_table = False

        line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
        line = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', line)
        line = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', line)
        line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', line)

        if line.strip() == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p>{line}</p>")

    if in_table:
        html_lines.append("</table>")
    return "\n".join(html_lines)

html_body = md_to_html(md_content)

html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Delayed and Reopen Ticket Report {today_f}</title>
<style>
  @page {{ size: A4 landscape; margin: 14mm; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; color: #1a1a1a; padding: 0; margin: 0; }}
  h1 {{ font-size: 18pt; color: #c0392b; border-bottom: 3px solid #c0392b; padding-bottom: 8px; margin-bottom: 6px; }}
  h2 {{ font-size: 13pt; color: #fff; background: #c0392b; padding: 6px 12px; border-radius: 3px; margin: 22px 0 10px; page-break-after: avoid; break-after: avoid; }}
  h3 {{ font-size: 11.5pt; color: #c0392b; border-left: 4px solid #c0392b; padding-left: 10px; margin: 18px 0 8px; page-break-after: avoid; break-after: avoid; }}
  table {{ width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 9pt; margin: 8px 0 14px; }}
  th {{ background: #c0392b; color: #fff; padding: 6px 8px; text-align: left; font-weight: 600; word-wrap: break-word; }}
  td {{ padding: 5px 8px; border-bottom: 1px solid #e0e0e0; vertical-align: top; word-wrap: break-word; overflow-wrap: break-word; }}
  tr {{ page-break-inside: avoid; break-inside: avoid; }}
  tr:nth-child(even) td {{ background: #fdf2f0; }}
  code {{ background: #f0f0f0; padding: 1px 5px; border-radius: 3px; font-family: Consolas, monospace; font-size: 9pt; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 16px 0; }}
  a {{ color: #c0392b; text-decoration: none; }}
  p {{ margin: 4px 0; line-height: 1.6; }}
  b {{ color: #111; }}
  .footer {{ margin-top: 30px; font-size: 9pt; color: #888; text-align: center; border-top: 1px solid #ddd; padding-top: 8px; }}
  @media print {{ h2, th {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"HTML saved:     {html_file}")

# ── PDF via headless Chrome ───────────────────────────────────────────────────
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
file_url = "file:///" + html_file.replace("\\", "/").replace(" ", "%20")
result = subprocess.run(
    [chrome_path, "--headless", "--disable-gpu", "--no-pdf-header-footer",
     f"--print-to-pdf={pdf_file}", file_url],
    capture_output=True
)
if os.path.exists(pdf_file):
    print(f"PDF saved:      {pdf_file}")
else:
    print("PDF generation failed — markdown/HTML report still available.")

# ── TERMINAL SUMMARY ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
for d in delayed_by_sprint:
    delayed = [r for r in d["rows"] if r["status_flag"] == "delayed"]
    print(f"[{d['sprint']['name']}] ({d['team']}) - {len(delayed)} delayed / {len(d['rows'])} in progress")
print(f"Total delayed: {total_delayed}")
print("=" * 60)
