"""
Delayed and Reopen Ticket Report
Run: python ORR_sprint_report.py
Output: Sprint_Report_YYYYMMDD.md / .html / Sprint Report YYYYMMDD.pdf

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
from datetime import datetime, timezone, timedelta

DONE_STATUSES     = {"Done", "Closed", "QA PASSED"}
PROGRESS_STATUSES = {"In Progress", "DEV DONE", "QA TEST", "Re-open"}
TODO_STATUSES     = {"To Do", "Backlog"}

# Hari libur nasional Indonesia 2026
ID_HOLIDAYS = {
    datetime(2026,  1,  1).date(),  # Tahun Baru Masehi
    datetime(2026,  1, 16).date(),  # Isra Mi'raj Nabi Muhammad SAW
    datetime(2026,  2, 17).date(),  # Tahun Baru Imlek 2577 Kongzili
    datetime(2026,  3, 19).date(),  # Hari Suci Nyepi
    datetime(2026,  4,  3).date(),  # Wafat Yesus Kristus
    datetime(2026,  5,  1).date(),  # Hari Buruh Internasional
    datetime(2026,  5, 14).date(),  # Kenaikan Yesus Kristus
    datetime(2026,  5, 27).date(),  # Idul Adha 1447 H
    datetime(2026,  6,  1).date(),  # Hari Lahir Pancasila
    datetime(2026,  6, 16).date(),  # Tahun Baru Islam 1448 H
    datetime(2026,  8, 17).date(),  # Hari Kemerdekaan RI
    datetime(2026,  8, 25).date(),  # Maulid Nabi Muhammad SAW
    datetime(2026, 12, 25).date(),  # Hari Natal
}

PRIORITY_ORDER = {"Highest": 0, "High": 1, "Medium": 2, "Low": 3, "Lowest": 4}
TODO_LIST_LIMIT = 3

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
def compute_dev_done_range(issue):
    """Returns (start_time, end_time) as raw timestamp strings, using the
    first To Do -> in-progress/done transition and the LAST -> DEV DONE
    transition (so reopened tickets count the full rework time)."""
    start_time = None
    end_time = None
    for created, from_s, to_s in status_transitions(issue):
        if start_time is None and from_s in TODO_STATUSES and (
            to_s in PROGRESS_STATUSES or to_s in DONE_STATUSES
        ):
            start_time = created
        if to_s == "DEV DONE":
            end_time = created
    return start_time, end_time

def business_days_count(start_date, end_date):
    """Count business days (excluding weekends and Indonesian holidays) from start_date up to (not including) end_date."""
    count = 0
    current = start_date
    while current < end_date:
        if current.weekday() < 5 and current not in ID_HOLIDAYS:
            count += 1
        current += timedelta(days=1)
    return count

def business_hours_between(start, end):
    """Hours between two datetimes, excluding weekends and Indonesian national holidays."""
    if end <= start:
        return 0.0
    total = 0.0
    current = start
    while current.date() <= end.date():
        next_day = datetime.combine(current.date() + timedelta(days=1), datetime.min.time())
        seg_end = min(next_day, end)
        if current.weekday() < 5 and current.date() not in ID_HOLIDAYS:
            total += (seg_end - current).total_seconds() / 3600
        current = next_day
    return total

def compute_dev_done_hours(issue):
    start_time, end_time = compute_dev_done_range(issue)
    if start_time is None or end_time is None:
        return None
    hours = business_hours_between(parse_dt(start_time), parse_dt(end_time))
    return hours if hours >= 0 else None

def build_baseline(sprints):
    """sprints: list of sprint objects (with id, startDate, endDate), oldest or newest order doesn't matter.

    Returns (baseline_by_sp, velocity_by_sprint_id, velocity_by_sp_and_sprint_id).
    baseline_by_sp: avg cycle hours (To Do -> DEV DONE) per Story Point.
    velocity_by_sprint_id: avg cycle days (To Do -> DEV DONE) per sprint, across TARGET_SP tickets.
    velocity_by_sp_and_sprint_id: avg cycle days (To Do -> DEV DONE) per sprint, per Story Point.

    Tickets that carry over multiple sprints are only counted once, attributed
    to the sprint whose date range contains the ticket's (last) DEV DONE time.
    """
    # Dedupe issues across sprints (carry-over tickets show up in multiple sprint queries)
    issues_by_key = {}
    for sprint_obj in sprints:
        for issue in fetch_sprint_issues(sprint_obj["id"]):
            issues_by_key[issue["key"]] = issue

    data = {sp_val: [] for sp_val in TARGET_SP}
    sprint_hours = {s["id"]: [] for s in sprints}
    sprint_hours_by_sp = {s["id"]: {sp_val: [] for sp_val in TARGET_SP} for s in sprints}

    for issue in issues_by_key.values():
        sp_val = sp(issue["fields"])
        if sp_val not in TARGET_SP:
            continue
        h = compute_dev_done_hours(issue)
        if h is None:
            continue
        data[sp_val].append(h)

        _, end_time = compute_dev_done_range(issue)
        end_dt = parse_dt(end_time)
        target_sprint_id = None
        for sprint_obj in sprints:
            start_d, end_d = sprint_obj.get("startDate"), sprint_obj.get("endDate")
            if start_d and end_d and parse_dt(start_d) <= end_dt <= parse_dt(end_d):
                target_sprint_id = sprint_obj["id"]
                break
        if target_sprint_id is not None:
            sprint_hours[target_sprint_id].append(h)
            sprint_hours_by_sp[target_sprint_id][sp_val].append(h)

    velocity_by_sprint_id = {}
    velocity_by_sp_and_sprint_id = {sp_val: {} for sp_val in TARGET_SP}
    for sprint_obj in sprints:
        sprint_id = sprint_obj["id"]
        vals = sprint_hours[sprint_id]
        velocity_by_sprint_id[sprint_id] = (sum(vals) / len(vals) / 24) if vals else None
        for sp_val in TARGET_SP:
            sp_vals = sprint_hours_by_sp[sprint_id][sp_val]
            velocity_by_sp_and_sprint_id[sp_val][sprint_id] = (sum(sp_vals) / len(sp_vals) / 24) if sp_vals else None

    baseline = {}
    for sp_val, vals in data.items():
        baseline[sp_val] = (sum(vals) / len(vals)) if vals else None
    return baseline, velocity_by_sprint_id, velocity_by_sp_and_sprint_id

# ── IN PROGRESS TICKETS: time since entered progress ─────────────────────────
def count_reopens(issue):
    """Number of times the ticket was moved back to 'Re-open' status."""
    return sum(1 for _, _, to_s in status_transitions(issue) if to_s == "Re-open")

def last_reopen_date(issue):
    """Date string (YYYY-MM-DD) of the most recent transition to 'Re-open', or None."""
    last = None
    for created, _, to_s in status_transitions(issue):
        if to_s == "Re-open":
            last = created
    return last[:10] if last else None

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
    hours = business_hours_between(parse_dt(start_time), now)
    return hours, start_time

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
baseline_mkp, velocity_mkp_by_id, velocity_mkp_by_sp_id = build_baseline(mkp_closed)
print("Building baseline (BUMA ID Team)...")
baseline_buma, velocity_buma_by_id, velocity_buma_by_sp_id = build_baseline(buma_closed)

baselines = {"MKP Team": baseline_mkp, "BUMA ID Team": baseline_buma}

# Velocity trend (oldest -> newest) for the last BASELINE_SPRINT_COUNT closed sprints per team
velocity_mkp  = [(s["name"], velocity_mkp_by_id[s["id"]])  for s in reversed(mkp_closed)]
velocity_buma = [(s["name"], velocity_buma_by_id[s["id"]]) for s in reversed(buma_closed)]

# Velocity trend per Story Point (oldest -> newest)
velocity_mkp_by_sp = {
    sp_val: [(s["name"], velocity_mkp_by_sp_id[sp_val][s["id"]]) for s in reversed(mkp_closed)]
    for sp_val in TARGET_SP
}
velocity_buma_by_sp = {
    sp_val: [(s["name"], velocity_buma_by_sp_id[sp_val][s["id"]]) for s in reversed(buma_closed)]
    for sp_val in TARGET_SP
}

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
                "is_new_today": last_reopen_date(issue) == datetime.now().strftime("%Y-%m-%d"),
            })

    todo_rows = []
    for issue in issues:
        f = issue["fields"]
        if f["status"]["name"] not in TODO_STATUSES:
            continue
        sp_val = sp(f)
        todo_rows.append({
            "key": issue["key"],
            "summary": f["summary"][:70] + ("..." if len(f["summary"]) > 70 else ""),
            "status": f["status"]["name"],
            "assignee": (f.get("assignee") or {}).get("displayName", "Unassigned"),
            "sp": sp_val,
            "priority": (f.get("priority") or {}).get("name", "-"),
        })

    sprint_start_dt = parse_dt(sprint_obj["startDate"]).date() if sprint_obj.get("startDate") else None
    sprint_end_dt   = parse_dt(sprint_obj["endDate"]).date()   if sprint_obj.get("endDate")   else None
    today_date = datetime.now().date()
    if sprint_start_dt and sprint_end_dt:
        total_sprint_days   = business_days_count(sprint_start_dt, sprint_end_dt + timedelta(days=1))
        elapsed_sprint_days = business_days_count(sprint_start_dt, min(today_date, sprint_end_dt) + timedelta(days=1))
        sprint_day_pct      = (elapsed_sprint_days / total_sprint_days * 100) if total_sprint_days else 0
    else:
        total_sprint_days = elapsed_sprint_days = None
        sprint_day_pct = 0

    status_counts = {"done": [0, 0.0], "progress": [0, 0.0], "todo": [0, 0.0]}
    for issue in issues:
        f = issue["fields"]
        status_name = f["status"]["name"]
        sp_val = sp(f) or 0
        if status_name in DONE_STATUSES:
            bucket = "done"
        elif status_name in PROGRESS_STATUSES:
            bucket = "progress"
        elif status_name in TODO_STATUSES:
            bucket = "todo"
        else:
            continue
        status_counts[bucket][0] += 1
        status_counts[bucket][1] += sp_val

    total_tickets = sum(c[0] for c in status_counts.values())
    total_sp = sum(c[1] for c in status_counts.values())
    progress_stats = {
        "total_tickets": total_tickets,
        "total_sp": total_sp,
        "done_tickets": status_counts["done"][0],
        "done_sp": status_counts["done"][1],
        "progress_tickets": status_counts["progress"][0],
        "progress_sp": status_counts["progress"][1],
        "todo_tickets": status_counts["todo"][0],
        "todo_sp": status_counts["todo"][1],
        "done_pct_tickets": (status_counts["done"][0] / total_tickets * 100) if total_tickets else 0,
        "done_pct_sp": (status_counts["done"][1] / total_sp * 100) if total_sp else 0,
        "total_sprint_days": total_sprint_days,
        "elapsed_sprint_days": elapsed_sprint_days,
        "sprint_day_pct": sprint_day_pct,
    }

    delayed_by_sprint.append({
        "sprint": sprint_obj,
        "team": team_name,
        "rows": rows,
        "reopen_rows": reopen_rows,
        "progress": progress_stats,
        "todo_rows": todo_rows,
    })

def progress_bar(pct):
    pct = max(0, min(100, pct))
    return (f'<div class="progress-bar"><div class="progress-fill" style="width:{pct:.0f}%"></div></div>'
            f'<span class="progress-pct">{pct:.0f}%</span>')

def velocity_line_chart_svg(series_a, series_b, label_a, label_b, color_a="#c0392b", color_b="#2c3e50"):
    """series_a/series_b: list of (sprint_name, avg_days_or_None), oldest -> newest."""
    width, height = 640, 260
    pad_l, pad_r, pad_t, pad_b = 45, 20, 24, 30
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    n = max(len(series_a), len(series_b), 1)
    vals = [v for _, v in series_a + series_b if v is not None]
    max_val = (max(vals) * 1.2) if vals else 1
    if max_val == 0:
        max_val = 1

    def x_pos(i):
        return pad_l + (plot_w * i / (n - 1) if n > 1 else plot_w / 2)

    def y_pos(v):
        return pad_t + plot_h * (1 - v / max_val)

    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
             f'style="width:100%;max-width:{width}px;font-family:Segoe UI, Arial, sans-serif;">']

    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        y = pad_t + plot_h * (1 - frac)
        val = max_val * frac
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" stroke="#e6e6e6" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l - 6}" y="{y + 3:.1f}" font-size="9" fill="#888" text-anchor="end">{val:.1f}</text>')

    for i in range(n):
        parts.append(f'<text x="{x_pos(i):.1f}" y="{height - 8}" font-size="9" fill="#888" text-anchor="middle">S{i + 1}</text>')

    def draw_series(series, color):
        pts = [(x_pos(i), y_pos(v), v) for i, (_, v) in enumerate(series) if v is not None]
        if len(pts) >= 2:
            points_str = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)
            parts.append(f'<polyline points="{points_str}" fill="none" stroke="{color}" stroke-width="2"/>')
        for x, y, v in pts:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>')
            parts.append(f'<text x="{x:.1f}" y="{y - 8:.1f}" font-size="9" fill="{color}" text-anchor="middle">{v:.1f}</text>')

    draw_series(series_a, color_a)
    draw_series(series_b, color_b)

    parts.append(f'<circle cx="{pad_l + 5}" cy="12" r="4" fill="{color_a}"/>')
    parts.append(f'<text x="{pad_l + 14}" y="16" font-size="10" fill="#1a1a1a">{label_a}</text>')
    parts.append(f'<circle cx="{pad_l + 150}" cy="12" r="4" fill="{color_b}"/>')
    parts.append(f'<text x="{pad_l + 159}" y="16" font-size="10" fill="#1a1a1a">{label_b}</text>')

    parts.append('</svg>')
    return "".join(parts)

# ── BUILD MARKDOWN ────────────────────────────────────────────────────────────
today   = datetime.now().strftime("%d %B %Y %H:%M")
today_s = datetime.now().strftime("%d %B %Y %H:%M:%S")
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

    lines.append("### 🔴 Delayed Tickets\n")
    if delayed_rows:
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
        lines.append("Selamat, tidak ada ticket yang delayed hari ini.\n")

    lines.append("### 🟢 On Track Tickets\n")
    if ontrack_rows:
        ontrack_sorted = sorted(ontrack_rows, key=lambda x: x["elapsed_days"] - x["baseline_days"], reverse=True)
        top_ontrack = ontrack_sorted[:TODO_LIST_LIMIT]
        remaining = len(ontrack_sorted) - len(top_ontrack)

        lines.append("| Key | Summary | Assignee | SP | Started | Elapsed (hari) | Baseline (hari) | Priority |")
        lines.append("|-----|---------|----------|----|---------|-----------------|-------------------|----------|")
        for r in top_ontrack:
            lines.append(
                f"| [{r['key']}]({BASE_URL}/browse/{r['key']}) | {r['summary']} | {r['assignee']} | "
                f"{r['sp']:.0f} | {r['started']} | {r['elapsed_days']:.1f} | "
                f"{r['baseline_days']:.1f} | {r['priority']} |"
            )
        lines.append("")
        if remaining > 0:
            lines.append(f"*...dan {remaining} ticket lainnya — lihat backlog di board.*\n")
    else:
        lines.append("Sepi banget di sini... gak ada ticket yang lagi on track. 🦗\n")

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
    lines.append("### 🔁 Reopened Tickets\n")
    if reopen_rows:
        lines.append("| Key | Summary | Status | Assignee | Reopen Count | Priority | New Today |")
        lines.append("|-----|---------|--------|----------|--------------|----------|-----------|")
        for r in sorted(reopen_rows, key=lambda x: (not x["is_new_today"], -x["reopen_count"])):
            flag = ('<span style="color:#fff;background:#c0392b;padding:1px 6px;border-radius:3px;'
                    'font-size:8pt;font-weight:bold;">NEW</span>') if r["is_new_today"] else ""
            lines.append(
                f"| [{r['key']}]({BASE_URL}/browse/{r['key']}) | {r['summary']} | {r['status']} | "
                f"{r['assignee']} | {r['reopen_count']} | {r['priority']} | {flag} |"
            )
        lines.append("")
    else:
        lines.append("Nihil! Gak ada ticket yang bolak-balik reopen — sekali jadi langsung mantap. 💪\n")

    prog = d["progress"]
    lines.append("### 📊 Current Progress Sprint\n")
    lines.append("| Metric | Tickets | Story Points |")
    lines.append("|--------|---------|--------------|")
    lines.append(f"| Total | {prog['total_tickets']} | {prog['total_sp']:.0f} SP |")
    lines.append(f"| Done / QA Passed | {prog['done_tickets']} ({prog['done_pct_tickets']:.0f}%) | {prog['done_sp']:.0f} SP ({prog['done_pct_sp']:.0f}%) |")
    lines.append(f"| In Progress / Dev Done / QA Test | {prog['progress_tickets']} | {prog['progress_sp']:.0f} SP |")
    lines.append(f"| To Do | {prog['todo_tickets']} | {prog['todo_sp']:.0f} SP |")
    lines.append(f"| **Progress (Tickets / SP)** | {progress_bar(prog['done_pct_tickets'])} | {progress_bar(prog['done_pct_sp'])} |")
    if prog["total_sprint_days"] is not None:
        lines.append(f"| **Sprint Day Progress** | {prog['elapsed_sprint_days']} / {prog['total_sprint_days']} hari kerja | {progress_bar(prog['sprint_day_pct'])} |")
    lines.append("")

    todo_rows = d["todo_rows"]
    lines.append("### 📋 To Do Tickets\n")
    if todo_rows:
        todo_sorted = sorted(
            todo_rows,
            key=lambda x: (PRIORITY_ORDER.get(x["priority"], 99), x["sp"] is None, -(x["sp"] or 0))
        )
        top_todo = todo_sorted[:TODO_LIST_LIMIT]
        remaining = len(todo_sorted) - len(top_todo)

        lines.append("| Key | Summary | Status | Assignee | SP | Priority |")
        lines.append("|-----|---------|--------|----------|----|----------|")
        for r in top_todo:
            sp_str = f"{r['sp']:.0f}" if r["sp"] is not None else "-"
            lines.append(
                f"| [{r['key']}]({BASE_URL}/browse/{r['key']}) | {r['summary']} | {r['status']} | "
                f"{r['assignee']} | {sp_str} | {r['priority']} |"
            )
        lines.append("")
        if remaining > 0:
            lines.append(f"*...dan {remaining} ticket lainnya — lihat backlog di board.*\n")
    else:
        lines.append("To Do list-nya kosong melompong. Semua udah jalan duluan, gas terus! 🚀\n")

    lines.append("---\n")

# Velocity trend chart (insight, ditampilkan di akhir report)
lines.append("## 📈 Insight: Velocity Trend — Rata-rata Cycle Time per Sprint (5 Sprint Terakhir)\n")
lines.append("Rata-rata waktu penyelesaian (To Do -> DEV DONE) dalam hari, dihitung per sprint "
              "untuk 5 sprint closed terakhir masing-masing tim, dipecah per Story Point. "
              "S1 = sprint tertua, S5 = sprint terbaru.\n")
lines.append("| # | MKP Team Sprint | BUMA ID Team Sprint |")
lines.append("|---|------------------|----------------------|")
for i in range(max(len(velocity_mkp), len(velocity_buma))):
    m_name = velocity_mkp[i][0] if i < len(velocity_mkp) else "-"
    b_name = velocity_buma[i][0] if i < len(velocity_buma) else "-"
    lines.append(f"| S{i + 1} | {m_name} | {b_name} |")
lines.append("")

for i in range(0, len(TARGET_SP), 2):
    pair = TARGET_SP[i:i + 2]
    cols = []
    for sp_val in pair:
        chart_svg = velocity_line_chart_svg(velocity_mkp_by_sp[sp_val], velocity_buma_by_sp[sp_val], "MKP Team", "BUMA ID Team")
        cols.append(f'<div class="chart-col"><h3>Story Point {sp_val}</h3>{chart_svg}</div>')
    lines.append('<div class="chart-row">' + "".join(cols) + '</div>')
    lines.append("")

lines.append("---\n")

lines.append(f"*Auto-generated by ORR_sprint_report.py — {today_s}*")

md_content = "\n".join(lines)

# ── SAVE ──────────────────────────────────────────────────────────────────────
out_dir  = os.path.dirname(os.path.abspath(__file__))
html_dir = os.path.join(out_dir, "html")
md_dir   = os.path.join(out_dir, "md")
pdf_dir  = os.path.join(out_dir, "pdf")
for d_ in (html_dir, md_dir, pdf_dir):
    os.makedirs(d_, exist_ok=True)

md_file = os.path.join(md_dir, f"Sprint_Report_{today_f}.md")
with open(md_file, "w", encoding="utf-8") as f:
    f.write(md_content)
print(f"\nMarkdown saved: {md_file}")

# ── HTML ──────────────────────────────────────────────────────────────────────
html_file = os.path.join(html_dir, f"Sprint_Report_{today_f}.html")
pdf_file  = os.path.join(pdf_dir, f"Sprint Report {today_f}.pdf")

def md_to_html(md):
    html_lines = []
    in_table = False
    for line in md.split("\n"):
        if line.startswith("### "): html_lines.append(f"<h3>{line[4:]}</h3>"); continue
        if line.startswith("## "):  html_lines.append(f"<h2>{line[3:]}</h2>"); continue
        if line.startswith("# "):   html_lines.append(f"<h1>{line[2:]}</h1>"); continue

        if line.strip() == "---":
            if in_table: html_lines.append("</tbody></table>"); in_table = False
            html_lines.append("<hr>"); continue

        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c.replace("-", "").replace(":", "")) == set() for c in cells):
                continue
            if not in_table:
                html_lines.append('<table><thead>')
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
            if tag == "th":
                html_lines.append("</thead><tbody>")
            continue
        else:
            if in_table: html_lines.append("</tbody></table>"); in_table = False

        line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
        line = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', line)
        line = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', line)
        line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', line)

        if line.strip() == "":
            html_lines.append("<br>")
        elif line.strip().startswith("<div"):
            html_lines.append(line)
        else:
            html_lines.append(f"<p>{line}</p>")

    if in_table:
        html_lines.append("</tbody></table>")
    return "\n".join(html_lines)

html_body = md_to_html(md_content)

html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Delayed and Reopen Ticket Report {today_f}</title>
<style>
  @page {{ size: A4 portrait; margin: 14mm; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; color: #1a1a1a; padding: 0 280px; margin: 0; }}
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
  .progress-bar {{ display: inline-block; width: 60%; height: 14px; background: #eee; border-radius: 3px; overflow: hidden; vertical-align: middle; margin-right: 6px; }}
  .progress-fill {{ height: 100%; background: #c0392b; }}
  .progress-pct {{ font-size: 9pt; vertical-align: middle; }}
  .chart-row {{ display: flex; gap: 16px; margin: 8px 0; page-break-inside: avoid; break-inside: avoid; }}
  .chart-col {{ flex: 1; min-width: 0; }}
  .chart-col h3 {{ margin-top: 0; }}
  @media print {{ h2, th {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }} body {{ padding: 0 40px; }} }}
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
