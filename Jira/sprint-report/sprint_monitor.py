"""
Digiman+ Sprint Monitor
Run: python sprint_monitor.py
Output: sprint_report_YYYYMMDD.md + sprint_report_YYYYMMDD.pdf
"""

import urllib.request, base64, json, os, subprocess, sys, re
from datetime import datetime, timezone
from collections import defaultdict

# ── CONFIG ────────────────────────────────────────────────────────────────────
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
BOARD_ID = 93
PROJECT  = "IAMS30"
VELOCITY_SPRINTS = 5   # jumlah sprint terakhir untuk hitung velocity

DONE_STATUSES     = {"Done", "Closed", "QA PASSED"}
PROGRESS_STATUSES = {"In Progress", "DEV DONE", "QA TEST", "Re-open"}
TODO_STATUSES     = {"To Do", "Backlog"}

# ── HELPERS ───────────────────────────────────────────────────────────────────
def get(url):
    creds = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {creds}", "Accept": "application/json"
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def pct(a, b): return round(a / b * 100) if b else 0

def days_left(end_str):
    if not end_str: return None
    end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
    return (end - datetime.now(timezone.utc)).days

def status_group(status):
    if status in DONE_STATUSES:     return "done"
    if status in PROGRESS_STATUSES: return "progress"
    return "todo"

def sp(fields):
    v = fields.get("customfield_10016")
    return float(v) if v else 0.0

def bar(p, width=20):
    filled = round(p / 100 * width)
    return "█" * filled + "░" * (width - filled)

def fmt_date(s):
    return s[:10] if s else "-"

# ── FETCH ALL SPRINTS ────────────────────────────────────────────────────────
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
future_sprints = [s for s in all_sprints if s["state"] == "future"][:6]

# Sort closed by end date descending
closed_sprints.sort(key=lambda x: x.get("endDate",""), reverse=True)

# ── FETCH SPRINT ISSUES ───────────────────────────────────────────────────────
def fetch_issues(sprint_id):
    issues = []
    start_at = 0
    while True:
        res = get(f"{BASE_URL}/rest/agile/1.0/sprint/{sprint_id}/issue"
                  f"?maxResults=100&startAt={start_at}"
                  f"&fields=summary,status,assignee,priority,issuetype,customfield_10016")
        batch = res.get("issues", [])
        issues += batch
        if len(batch) < 100:
            break
        start_at += 100
    return issues

def process_issues(issues):
    done = prog = todo = 0
    done_sp = prog_sp = todo_sp = 0.0
    assignees = defaultdict(lambda: {"done":0,"progress":0,"todo":0,"sp":0.0})
    ticket_list = []

    for i in issues:
        f  = i["fields"]
        st = f["status"]["name"]
        g  = status_group(st)
        pts = sp(f)
        person = (f.get("assignee") or {}).get("displayName","Unassigned")

        if g == "done":        done += 1; done_sp += pts
        elif g == "progress":  prog += 1; prog_sp += pts
        else:                  todo += 1; todo_sp += pts

        assignees[person][g]   += 1
        assignees[person]["sp"] += pts

        ticket_list.append({
            "key":      i["key"],
            "summary":  f["summary"][:72] + ("..." if len(f["summary"]) > 72 else ""),
            "status":   st,
            "group":    g,
            "assignee": person,
            "priority": (f.get("priority") or {}).get("name","-"),
            "type":     (f.get("issuetype") or {}).get("name","-"),
            "sp":       pts,
        })

    total    = done + prog + todo
    total_sp = done_sp + prog_sp + todo_sp
    return {
        "total": total, "done": done, "progress": prog, "todo": todo,
        "total_sp": total_sp, "done_sp": done_sp, "prog_sp": prog_sp, "todo_sp": todo_sp,
        "pct_done": pct(done, total), "pct_sp": pct(done_sp, total_sp),
        "assignees": dict(assignees),
        "tickets": ticket_list,
    }

# ── VELOCITY ─────────────────────────────────────────────────────────────────
print(f"Calculating velocity from last {VELOCITY_SPRINTS} closed sprints...")
velocity_data = []
for sp_obj in closed_sprints[:VELOCITY_SPRINTS]:
    sid = sp_obj["id"]
    issues = fetch_issues(sid)
    done_issues = [i for i in issues if status_group(i["fields"]["status"]["name"]) == "done"]
    completed_sp = sum(sp(i["fields"]) for i in done_issues)
    completed_count = len(done_issues)
    velocity_data.append({
        "name": sp_obj["name"],
        "end":  fmt_date(sp_obj.get("endDate","")),
        "done_tickets": completed_count,
        "done_sp": completed_sp,
    })

avg_velocity_sp     = sum(v["done_sp"] for v in velocity_data) / len(velocity_data) if velocity_data else 0
avg_velocity_tickets = sum(v["done_tickets"] for v in velocity_data) / len(velocity_data) if velocity_data else 0

# ── CARRIED OVER TICKETS ─────────────────────────────────────────────────────
print("Checking carried over tickets...")
# Get the last closed sprint's incomplete tickets per active sprint team
# We identify carried over by finding tickets in current sprint that were NOT done in prev sprint

def get_carried_over(active_sprint, all_closed):
    """
    Carried over = tickets in current sprint yang PERNAH ada di sprint sebelumnya
    dan tidak selesai di sprint sebelumnya.
    We check sprint history via changelog.
    Alternative: check if ticket key exists in last closed sprint issues.
    """
    if not all_closed:
        return []

    # Get tickets from last 2 closed sprints
    prev_incomplete_keys = set()
    for prev_sp in all_closed[:2]:
        prev_issues = fetch_issues(prev_sp["id"])
        for i in prev_issues:
            if status_group(i["fields"]["status"]["name"]) != "done":
                prev_incomplete_keys.add(i["key"])

    # Current sprint tickets that appeared in prev sprint as incomplete
    curr_issues = fetch_issues(active_sprint["id"])
    carried = []
    for i in curr_issues:
        if i["key"] in prev_incomplete_keys:
            f = i["fields"]
            carried.append({
                "key":      i["key"],
                "summary":  f["summary"][:72] + ("..." if len(f["summary"]) > 72 else ""),
                "status":   f["status"]["name"],
                "group":    status_group(f["status"]["name"]),
                "assignee": (f.get("assignee") or {}).get("displayName","Unassigned"),
                "sp":       sp(f),
            })
    return carried

# ── MAIN FETCH ────────────────────────────────────────────────────────────────
print(f"Found {len(active_sprints)} active sprint(s). Fetching details...")
sprint_data = []
for sp_obj in active_sprints:
    print(f"  -> {sp_obj['name']}")
    issues  = fetch_issues(sp_obj["id"])
    data    = process_issues(issues)
    carried = get_carried_over(sp_obj, closed_sprints)
    data["sprint"]  = sp_obj
    data["carried"] = carried
    sprint_data.append(data)

# ── BUILD MARKDOWN ────────────────────────────────────────────────────────────
today   = datetime.now().strftime("%d %B %Y")
today_f = datetime.now().strftime("%Y%m%d")
lines   = []

lines.append(f"# Digiman+ Sprint Monitor Report")
lines.append(f"**Generated:** {today}  |  **Project:** {PROJECT}  |  **Board:** IAMS 3.0\n")
lines.append("---\n")

# ── ACTIVE SPRINTS ────────────────────────────────────────────────────────────
lines.append(f"## Active Sprints ({len(active_sprints)})\n")

for d in sprint_data:
    sp_obj = d["sprint"]
    dl     = days_left(sp_obj.get("endDate"))
    if dl is None:         dl_str = "-"
    elif dl < 0:           dl_str = f"OVERDUE ({abs(dl)} hari)"
    elif dl == 0:          dl_str = "Berakhir hari ini!"
    else:                  dl_str = f"{dl} hari lagi"

    lines.append(f"### {sp_obj['name']}")
    lines.append(f"**Period:** {fmt_date(sp_obj.get('startDate'))} → {fmt_date(sp_obj.get('endDate'))}  |  **Deadline:** {dl_str}\n")

    # Progress table
    lines.append("| Metric | Tickets | Story Points |")
    lines.append("|--------|---------|--------------|")
    lines.append(f"| Total | {d['total']} | {d['total_sp']:.0f} SP |")
    lines.append(f"| Done / QA Passed | {d['done']} ({d['pct_done']}%) | {d['done_sp']:.0f} SP ({d['pct_sp']}%) |")
    lines.append(f"| In Progress / Dev Done / QA Test | {d['progress']} | {d['prog_sp']:.0f} SP |")
    lines.append(f"| To Do | {d['todo']} | {d['todo_sp']:.0f} SP |")
    lines.append(f"| **Progress** | `{bar(d['pct_done'])}` {d['pct_done']}% | `{bar(d['pct_sp'])}` {d['pct_sp']}% |")
    lines.append("")

    # Carried over
    if d["carried"]:
        lines.append(f"**Carried Over Tickets ({len(d['carried'])}) — dibawa dari sprint sebelumnya:**\n")
        lines.append("| Key | Summary | Status | Assignee | SP |")
        lines.append("|-----|---------|--------|----------|----|")
        for t in d["carried"]:
            icon = "🔄" if t["group"] == "progress" else ("✅" if t["group"] == "done" else "📋")
            lines.append(f"| [{t['key']}]({BASE_URL}/browse/{t['key']}) | {t['summary']} | {t['status']} | {t['assignee']} | {t['sp']:.0f} |")
        lines.append("")
    else:
        lines.append("**Carried Over:** Tidak ada ticket yang dibawa dari sprint sebelumnya.\n")

    # Assignee breakdown
    lines.append("**Breakdown per Assignee:**\n")
    lines.append("| Assignee | Done | Progress | To Do | Total | SP |")
    lines.append("|----------|------|----------|-------|-------|----|")
    for name, cnt in sorted(d["assignees"].items(), key=lambda x: -(x[1]["done"]+x[1]["progress"]+x[1]["todo"])):
        total_p = cnt["done"] + cnt["progress"] + cnt["todo"]
        lines.append(f"| {name} | {cnt['done']} | {cnt['progress']} | {cnt['todo']} | {total_p} | {cnt['sp']:.0f} |")
    lines.append("")

    # Tickets not done
    not_done = [t for t in d["tickets"] if t["group"] != "done"]
    if not_done:
        lines.append(f"**Tickets belum selesai ({len(not_done)}):**\n")
        lines.append("| Key | Summary | Status | Assignee | SP | Priority |")
        lines.append("|-----|---------|--------|----------|----|---------|")
        for t in sorted(not_done, key=lambda x: (x["group"]!="progress", x["assignee"])):
            icon = "🔄" if t["group"] == "progress" else "📋"
            lines.append(f"| [{t['key']}]({BASE_URL}/browse/{t['key']}) | {icon} {t['summary']} | {t['status']} | {t['assignee']} | {t['sp']:.0f} | {t['priority']} |")
        lines.append("")

    lines.append("---\n")

# ── VELOCITY ─────────────────────────────────────────────────────────────────
lines.append(f"## Velocity (Last {VELOCITY_SPRINTS} Closed Sprints)\n")
lines.append(f"**Avg Completed Tickets:** {avg_velocity_tickets:.1f} per sprint  |  **Avg Story Points:** {avg_velocity_sp:.1f} SP per sprint\n")
lines.append("| Sprint | End Date | Completed Tickets | Completed SP |")
lines.append("|--------|----------|-------------------|-------------|")
for v in velocity_data:
    lines.append(f"| {v['name']} | {v['end']} | {v['done_tickets']} | {v['done_sp']:.0f} |")
lines.append("")

# ── UPCOMING SPRINTS ──────────────────────────────────────────────────────────
if future_sprints:
    lines.append("## Upcoming Sprints\n")
    lines.append("| Sprint | Start | End |")
    lines.append("|--------|-------|-----|")
    for s in future_sprints:
        lines.append(f"| {s['name']} | {fmt_date(s.get('startDate'))} | {fmt_date(s.get('endDate'))} |")
    lines.append("")

lines.append("---")
lines.append(f"*Auto-generated by sprint_monitor.py — {today}*")

md_content = "\n".join(lines)

# ── SAVE MARKDOWN ─────────────────────────────────────────────────────────────
out_dir  = os.path.dirname(os.path.abspath(__file__))
pdf_dir  = os.path.join(out_dir, "pdf")
html_dir = os.path.join(out_dir, "html")
md_dir   = os.path.join(out_dir, "md")
for d in (pdf_dir, html_dir, md_dir):
    os.makedirs(d, exist_ok=True)

md_file  = os.path.join(md_dir, f"sprint_report_{today_f}.md")
with open(md_file, "w", encoding="utf-8") as f:
    f.write(md_content)
print(f"\nMarkdown saved: {md_file}")

# ── GENERATE PDF ──────────────────────────────────────────────────────────────
html_file = os.path.join(html_dir, f"sprint_report_{today_f}.html")
pdf_file  = os.path.join(pdf_dir, f"Sprint Report {today_f}.pdf")

# Convert markdown tables to HTML
def md_to_html(md):
    html_lines = []
    in_table = False
    in_list  = False

    for line in md.split("\n"):
        # Heading
        if line.startswith("### "): html_lines.append(f"<h3>{line[4:]}</h3>"); continue
        if line.startswith("## "):  html_lines.append(f"<h2>{line[3:]}</h2>"); continue
        if line.startswith("# "):   html_lines.append(f"<h1>{line[2:]}</h1>"); continue

        # HR
        if line.strip() == "---":
            if in_table: html_lines.append("</table>"); in_table = False
            html_lines.append("<hr>"); continue

        # Table
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c.replace("-","").replace(":","")) == set() for c in cells):
                continue  # separator row
            if not in_table:
                html_lines.append('<table>')
                in_table = True
                tag = "th"
            else:
                tag = "td"
            html_lines.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
            continue
        else:
            if in_table: html_lines.append("</table>"); in_table = False

        # Code inline
        line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
        # Bold
        line = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', line)
        # Italic
        line = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', line)
        # Link
        line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', line)

        if line.strip() == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p>{line}</p>")

    return "\n".join(html_lines)

html_body = md_to_html(md_content)

html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Sprint Report {today_f}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.5pt; color: #1a1a1a; padding: 28px 36px; max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 18pt; color: #0078d4; border-bottom: 3px solid #0078d4; padding-bottom: 8px; margin-bottom: 6px; }}
  h2 {{ font-size: 13pt; color: #fff; background: #0078d4; padding: 6px 12px; border-radius: 3px; margin: 22px 0 10px; }}
  h3 {{ font-size: 11.5pt; color: #0078d4; border-left: 4px solid #0078d4; padding-left: 10px; margin: 18px 0 8px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 10pt; margin: 8px 0 14px; }}
  th {{ background: #0078d4; color: #fff; padding: 6px 10px; text-align: left; font-weight: 600; }}
  td {{ padding: 5px 10px; border-bottom: 1px solid #e0e0e0; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #f5f9ff; }}
  code {{ background: #f0f0f0; padding: 1px 5px; border-radius: 3px; font-family: Consolas, monospace; font-size: 9pt; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 16px 0; }}
  a {{ color: #0078d4; text-decoration: none; }}
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

# Convert to PDF via Word COM
try:
    import win32com.client
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(html_file)
    doc.SaveAs(pdf_file, 17)
    doc.Close()
    word.Quit()
    print(f"PDF saved:      {pdf_file}")
except Exception:
    # Fallback: PowerShell Word COM
    ps = f"""
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open('{html_file}')
$doc.SaveAs([ref]'{pdf_file}', [ref]17)
$doc.Close()
$word.Quit()
"""
    subprocess.run(["powershell", "-Command", ps], capture_output=True)
    if os.path.exists(pdf_file):
        print(f"PDF saved:      {pdf_file}")
    else:
        print("PDF generation failed — markdown report still available.")

# ── TERMINAL SUMMARY ─────────────────────────────────────────────────────────
print("\n" + "="*65)
for d in sprint_data:
    sp_obj = d["sprint"]
    dl = days_left(sp_obj.get("endDate"))
    dl_str = f"{dl}d left" if isinstance(dl, int) and dl >= 0 else "Overdue!"
    print(f"[{sp_obj['name']}]  {dl_str}")
    prog_bar = "#" * round(d['pct_done']/100*15) + "-" * (15 - round(d['pct_done']/100*15))
    sp_bar   = "#" * round(d['pct_sp']/100*15)   + "-" * (15 - round(d['pct_sp']/100*15))
    print(f"  Progress : [{prog_bar}] {d['pct_done']}% ({d['done']}/{d['total']} tickets)")
    print(f"  SP Done  : [{sp_bar}] {d['pct_sp']}% ({d['done_sp']:.0f}/{d['total_sp']:.0f} SP)")
    print(f"  Carried  : {len(d['carried'])} ticket(s)")
print(f"\nVelocity avg : {avg_velocity_tickets:.1f} tickets / {avg_velocity_sp:.1f} SP per sprint")
print("="*65)
