"""
End of Sprint Report
Run: python end_of_sprint_report.py [team] [sprint_name]
  team        : "buma" or "mkp" (default: buma)
  sprint_name : partial sprint name to match (default: active now)

Output: EOS_<Team>_<SprintName>_<date>.html / .pdf
"""

import urllib.request, base64, json, os, subprocess, re, sys, html as html_lib
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
DONE_STATUSES      = {"Done", "Closed", "QA PASSED"}
PROGRESS_STATUSES  = {"In Progress", "DEV DONE", "QA TEST", "Re-open"}
TODO_STATUSES      = {"To Do", "Backlog"}
IN_PROGRESS_STATUS = "In Progress"
QA_TEST_STATUS     = "QA TEST"
DEV_DONE_STATUS    = "DEV DONE"
QA_PASSED_STATUS   = "QA PASSED"

QA_KEYWORDS  = {"qa", "test", "regress", "bug"}
TESTER_FIELD = "customfield_10438"

QA_TEAMS = {
    "BUMA ID Team": ["Gita Riskayanti", "Muhammad Zaqi Ghifari"],
    "MKP Team":     ["Andrian Sebayang", "Muhammad Zul Fikar", "Gita Riskayanti"],
}

TEAM_COLORS = {
    "BUMA ID Team": {
        "primary": "#8FAD82",
        "light":   "#EEF4EB",
        "dark":    "#5C7A52",
        "text":    "#3A5233",
    },
    "MKP Team": {
        "primary": "#7BA3C0",
        "light":   "#EAF2F8",
        "dark":    "#4A7A9B",
        "text":    "#2C5F7A",
    },
}

ID_HOLIDAYS = {
    datetime(2026,  1,  1).date(),
    datetime(2026,  1, 16).date(),
    datetime(2026,  2, 17).date(),
    datetime(2026,  3, 19).date(),
    datetime(2026,  4,  3).date(),
    datetime(2026,  5,  1).date(),
    datetime(2026,  5, 14).date(),
    datetime(2026,  5, 27).date(),
    datetime(2026,  6,  1).date(),
    datetime(2026,  6, 16).date(),
    datetime(2026,  8, 17).date(),
    datetime(2026,  8, 25).date(),
    datetime(2026, 12, 25).date(),
}

TARGET_SP             = [1, 2, 3, 5, 8]
BASELINE_SPRINT_COUNT = 5
BOARD_ID              = 93
PROJECT               = "IAMS30"

# ── AUTH ──────────────────────────────────────────────────────────────────────
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
        for item in h.get("items", []):
            if item["field"] == "status":
                transitions.append((h["created"], item.get("fromString"), item.get("toString")))
    transitions.sort(key=lambda t: t[0])
    return transitions

def business_hours_between(start, end):
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

def business_days_count(start_date, end_date):
    count = 0
    current = start_date
    while current < end_date:
        if current.weekday() < 5 and current not in ID_HOLIDAYS:
            count += 1
        current += timedelta(days=1)
    return count

def compute_status_segments(issue, target_status, sprint_start_dt=None):
    """Sum business hours spent in target_status across all occurrences.
    If sprint_start_dt given, enter_time is capped to sprint start
    when the ticket entered the status before the sprint began."""
    transitions = status_transitions(issue)
    total_hours = 0.0
    enter_time  = None
    for created, from_s, to_s in transitions:
        if to_s == target_status:
            enter_time = created
        elif from_s == target_status and enter_time is not None:
            start = parse_dt(enter_time)
            if sprint_start_dt and start.date() < sprint_start_dt:
                start = datetime.combine(sprint_start_dt, datetime.min.time())
            end = parse_dt(created)
            if end > start:
                total_hours += business_hours_between(start, end)
            enter_time = None
    if enter_time is not None:
        start = parse_dt(enter_time)
        if sprint_start_dt and start.date() < sprint_start_dt:
            start = datetime.combine(sprint_start_dt, datetime.min.time())
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if now > start:
            total_hours += business_hours_between(start, now)
    return total_hours

def compute_dev_done_range(issue):
    start_time = end_time = None
    for created, from_s, to_s in status_transitions(issue):
        if start_time is None and from_s in TODO_STATUSES and (
            to_s in PROGRESS_STATUSES or to_s in DONE_STATUSES
        ):
            start_time = created
        if to_s == DEV_DONE_STATUS:
            end_time = created
    return start_time, end_time

def count_reopens(issue):
    return sum(1 for _, _, to_s in status_transitions(issue) if to_s == "Re-open")

def last_reopen_date(issue):
    last = None
    for created, _, to_s in status_transitions(issue):
        if to_s == "Re-open":
            last = created
    return last[:10] if last else None

def is_qa_ticket(summary):
    return any(kw in summary.lower() for kw in QA_KEYWORDS)

def get_qa_tester(issue, team_name):
    f            = issue["fields"]
    summary      = f.get("summary", "")
    assignee     = (f.get("assignee") or {}).get("displayName", "Unassigned")
    qa_team      = QA_TEAMS.get(team_name, [])

    if is_qa_ticket(summary):
        return assignee if assignee in qa_team else "QA Samaran"

    testers = f.get(TESTER_FIELD) or []
    for tester in testers:
        name = tester.get("displayName") if isinstance(tester, dict) else None
        if name:
            return name if name in qa_team else "QA Samaran"

    return assignee if assignee in qa_team else "QA Samaran"

# ── FETCH ─────────────────────────────────────────────────────────────────────
def fetch_sprint_issues(sprint_id):
    fields = f"status,customfield_10016,summary,assignee,priority,created,{TESTER_FIELD}"
    issues, start_at = [], 0
    while True:
        url = (f"{BASE_URL}/rest/agile/1.0/sprint/{sprint_id}/issue"
               f"?fields={fields}&expand=changelog&maxResults=50&startAt={start_at}")
        res   = get(url)
        batch = res.get("issues", [])
        issues += batch
        total  = res.get("total", 0)
        start_at += len(batch)
        if start_at >= total or not batch:
            break
    return issues

# ── BASELINE ──────────────────────────────────────────────────────────────────
def build_dev_qa_baseline(sprints):
    # Map issue key → (issue, sprint_start_dt) attributed to the sprint where DEV DONE occurred
    issues_with_sprint = {}
    for s in sprints:
        s_start_dt = parse_dt(s["startDate"]).date() if s.get("startDate") else None
        s_end_dt   = parse_dt(s["endDate"]).date()   if s.get("endDate")   else None
        for issue in fetch_sprint_issues(s["id"]):
            key = issue["key"]
            if key in issues_with_sprint:
                continue  # already attributed to an earlier sprint
            _, dev_done_time = compute_dev_done_range(issue)
            if dev_done_time and s_start_dt and s_end_dt:
                done_date = parse_dt(dev_done_time).date()
                if s_start_dt <= done_date <= s_end_dt:
                    issues_with_sprint[key] = (issue, s_start_dt)
            elif key not in issues_with_sprint:
                issues_with_sprint[key] = (issue, s_start_dt)

    dev_data = {v: [] for v in TARGET_SP}
    qa_data  = {v: [] for v in TARGET_SP}
    for issue, sprint_start_dt in issues_with_sprint.values():
        sp_val = sp(issue["fields"])
        if sp_val not in TARGET_SP:
            continue
        _, end_time = compute_dev_done_range(issue)
        if end_time is None:
            continue
        dev_h = compute_status_segments(issue, IN_PROGRESS_STATUS, sprint_start_dt)
        qa_h  = compute_status_segments(issue, QA_TEST_STATUS, sprint_start_dt)
        if dev_h > 0: dev_data[sp_val].append(dev_h)
        if qa_h  > 0: qa_data[sp_val].append(qa_h)

    dev_bl = {v: (sum(x)/len(x) if x else None) for v, x in dev_data.items()}
    qa_bl  = {v: (sum(x)/len(x) if x else None) for v, x in qa_data.items()}
    return dev_bl, qa_bl

def build_velocity_history(sprints):
    result = []
    for s in sprints:
        issues  = fetch_sprint_issues(s["id"])
        done_sp = sum((sp(i["fields"]) or 0) for i in issues
                      if i["fields"]["status"]["name"] in DONE_STATUSES)
        result.append((s["name"], done_sp))
    return result

# ── LEADERBOARDS ──────────────────────────────────────────────────────────────
def build_dev_leaderboard(issues, sprint_start_dt, sprint_end_dt, team_name):
    if not (sprint_start_dt and sprint_end_dt):
        return []
    qa_team = QA_TEAMS.get(team_name, [])
    lb = defaultdict(float)
    for issue in issues:
        f = issue["fields"]
        if (f.get("status") or {}).get("name", "") not in DONE_STATUSES:
            continue
        assignee = (f.get("assignee") or {}).get("displayName", "Unassigned")
        if assignee in qa_team:
            continue
        sp_val = sp(f) or 0
        for created, _, to_s in status_transitions(issue):
            if to_s == DEV_DONE_STATUS:
                if sprint_start_dt <= parse_dt(created).date() <= sprint_end_dt:
                    lb[assignee] += sp_val
                    break
    return sorted(lb.items(), key=lambda x: -x[1])

def build_qa_leaderboard(issues, sprint_start_dt, sprint_end_dt, team_name):
    if not (sprint_start_dt and sprint_end_dt):
        return []
    lb = defaultdict(float)
    for issue in issues:
        f = issue["fields"]
        if (f.get("status") or {}).get("name", "") not in DONE_STATUSES:
            continue
        sp_val = sp(f) or 0
        tester = get_qa_tester(issue, team_name)
        for created, _, to_s in status_transitions(issue):
            if to_s == QA_PASSED_STATUS:
                if sprint_start_dt <= parse_dt(created).date() <= sprint_end_dt:
                    lb[tester] += sp_val
                    break
    # Sort: real QA first, QA Samaran last
    real_qa = sorted(((k, v) for k, v in lb.items() if k != "QA Samaran"), key=lambda x: -x[1])
    samaran = [("QA Samaran", lb["QA Samaran"])] if lb.get("QA Samaran") else []
    return real_qa + samaran

# ── HTML COMPONENTS ───────────────────────────────────────────────────────────
def progress_arc_svg(pct, color, size=110):
    pct = max(0, min(100, pct))
    r   = 40
    cx  = cy = size // 2
    circ = 2 * 3.14159 * r
    dash = circ * pct / 100
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#e8e8e8" stroke-width="9"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="9"'
            f' stroke-dasharray="{dash:.1f} {circ-dash:.1f}"'
            f' stroke-dashoffset="{circ*0.25:.1f}" stroke-linecap="round"/>'
            f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="17"'
            f' font-weight="bold" fill="{color}">{pct:.0f}%</text></svg>')

def champion_box(rows, assignee_key, color, label="ticket"):
    if not rows:
        return '<p class="empty-note">Tidak ada data — semua bersih! 🎉</p>'
    counts = defaultdict(int)
    for r in rows:
        counts[r[assignee_key]] += 1
    lb = sorted(counts.items(), key=lambda x: -x[1])
    champ_name, champ_cnt = lb[0]
    medals = ["🥈", "🥉"]
    runners_up = lb[1:5]
    lb_html = "".join(
        f'<div class="lb-item">{medals[i] if i < 2 else f"#{i+2}"}&nbsp;'
        f'<span class="lb-name">{html_lib.escape(n)}</span>'
        f'<span class="lb-count">{c} {label}{"s" if c > 1 else ""}</span></div>'
        for i, (n, c) in enumerate(runners_up)
    ) if runners_up else ""
    return (f'<div class="champion-box" style="border-color:{color};">'
            f'<div class="champion-header" style="background:{color};">🏆 CHAMPION</div>'
            f'<div class="champion-content">'
            f'<div class="champion-main">'
            f'<span class="crown">👑</span>'
            f'<span class="champion-name">{html_lib.escape(champ_name)}</span>'
            f'<span class="champion-badge" style="background:{color};">'
            f'{champ_cnt} {label}{"s" if champ_cnt > 1 else ""}</span>'
            f'</div><div class="leaderboard">{lb_html}</div></div></div>')

def leaderboard_cards(data, color):
    if not data:
        return '<p class="empty-note">Belum ada data. 🦗</p>'
    medals = ["🥇", "🥈", "🥉"]
    return "".join(
        f'<div class="lb-card" style="border-left:4px solid {color};">'
        f'<span class="lb-rank">{medals[i] if i < 3 else f"#{i+1}"}</span>'
        f'<span class="lb-person">{html_lib.escape(name)}</span>'
        f'<span class="lb-sp" style="color:{color};">{val:.0f} SP</span></div>'
        for i, (name, val) in enumerate(data)
    )

# ── GENERATE HTML ─────────────────────────────────────────────────────────────
def generate_html(team_name, sprint_obj, issues, dev_bl, qa_bl, velocity_history):
    color             = TEAM_COLORS[team_name]
    sprint_name       = sprint_obj["name"]
    sprint_name_safe  = html_lib.escape(sprint_name)
    sprint_start      = sprint_obj.get("startDate", "")[:10]
    sprint_end        = sprint_obj.get("endDate",   "")[:10]
    sprint_start_dt = parse_dt(sprint_obj["startDate"]).date() if sprint_obj.get("startDate") else None
    sprint_end_dt   = parse_dt(sprint_obj["endDate"]).date()   if sprint_obj.get("endDate")   else None
    today_date = datetime.now().date()

    if sprint_start_dt and sprint_end_dt:
        total_days   = business_days_count(sprint_start_dt, sprint_end_dt + timedelta(days=1))
        elapsed_days = business_days_count(sprint_start_dt, min(today_date, sprint_end_dt) + timedelta(days=1))
        day_pct = (elapsed_days / total_days * 100) if total_days else 0
    else:
        total_days = elapsed_days = 0; day_pct = 0

    # Status counts
    buckets = {"done": [0, 0.0], "progress": [0, 0.0], "todo": [0, 0.0]}
    for issue in issues:
        s = (issue["fields"].get("status") or {}).get("name", "")
        v = sp(issue["fields"]) or 0
        if   s in DONE_STATUSES:      bucket = "done"
        elif s in PROGRESS_STATUSES:  bucket = "progress"
        elif s in TODO_STATUSES:      bucket = "todo"
        else: continue
        buckets[bucket][0] += 1; buckets[bucket][1] += v

    total_t      = sum(c[0] for c in buckets.values())
    total_sp_val = sum(c[1] for c in buckets.values())
    done_t       = buckets["done"][0]
    done_sp_val  = buckets["done"][1]
    done_pct_t   = (done_t / total_t * 100)           if total_t > 0      else 0
    done_pct_sp  = (done_sp_val / total_sp_val * 100) if total_sp_val > 0 else 0

    def safe(text, max_len=70):
        text = html_lib.escape(str(text or ""))
        return (text[:max_len] + "...") if len(text) > max_len else text

    # Outstanding
    outstanding = sorted([
        {"key":      i["key"],
         "summary":  safe(i["fields"].get("summary", ""), 70),
         "status":   html_lib.escape((i["fields"].get("status") or {}).get("name", "-")),
         "assignee": safe((i["fields"].get("assignee") or {}).get("displayName", "Unassigned")),
         "sp":       sp(i["fields"]),
         "priority": html_lib.escape((i["fields"].get("priority") or {}).get("name", "-"))}
        for i in issues
        if (i["fields"].get("status") or {}).get("name", "") not in DONE_STATUSES
    ], key=lambda x: {"Highest":0,"High":1,"Medium":2,"Low":3,"Lowest":4}.get(x["priority"], 99))

    # Reopened
    reopen_rows = sorted([
        {"key":          i["key"],
         "summary":      safe(i["fields"].get("summary", ""), 70),
         "status":       html_lib.escape((i["fields"].get("status") or {}).get("name", "-")),
         "assignee":     safe((i["fields"].get("assignee") or {}).get("displayName", "Unassigned")),
         "reopen_count": count_reopens(i),
         "last_reopen":  last_reopen_date(i) or "-",
         "priority":     html_lib.escape((i["fields"].get("priority") or {}).get("name", "-"))}
        for i in issues if count_reopens(i) > 0
    ], key=lambda x: -x["reopen_count"])

    # Leaderboards
    dev_lb = build_dev_leaderboard(issues, sprint_start_dt, sprint_end_dt, team_name)
    qa_lb  = build_qa_leaderboard(issues, sprint_start_dt, sprint_end_dt, team_name)

    # Delayed
    qa_team     = QA_TEAMS.get(team_name, [])
    dev_delayed = []
    qa_delayed  = []
    for issue in issues:
        f      = issue["fields"]
        sp_val = sp(f)
        _, dev_done_time = compute_dev_done_range(issue)
        if dev_done_time is None:
            continue
        assignee = safe((f.get("assignee") or {}).get("displayName", "Unassigned"))
        tester   = safe(get_qa_tester(issue, team_name))
        priority = (f.get("priority") or {}).get("name", "-")
        summary  = safe(f.get("summary", ""), 65)

        dev_h  = compute_status_segments(issue, IN_PROGRESS_STATUS, sprint_start_dt)
        dev_b  = dev_bl.get(sp_val) if sp_val in TARGET_SP else None
        if dev_b and dev_h > dev_b:
            dev_delayed.append({"key": issue["key"], "summary": summary,
                                 "assignee": assignee, "sp": sp_val, "priority": priority,
                                 "actual_days": dev_h/24, "baseline_days": dev_b/24,
                                 "delay_days": (dev_h-dev_b)/24})

        qa_h = compute_status_segments(issue, QA_TEST_STATUS, sprint_start_dt)
        qa_b  = qa_bl.get(sp_val) if sp_val in TARGET_SP else None
        if qa_b and qa_h > qa_b:
            qa_delayed.append({"key": issue["key"], "summary": summary,
                                "assignee": tester, "sp": sp_val, "priority": priority,
                                "actual_days": qa_h/24, "baseline_days": qa_b/24,
                                "delay_days": (qa_h-qa_b)/24,
                                "is_qa_team": tester in qa_team})

    dev_delayed.sort(key=lambda x: -x["delay_days"])
    qa_delayed.sort(key=lambda x: -x["delay_days"])

    # ── TABLE HELPERS ─────────────────────────────────────────────────────────
    def th(*h):
        return "<tr>" + "".join(f"<th>{x}</th>" for x in h) + "</tr>"

    def tr(*cells):
        return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

    def empty(cols, msg):
        return f'<tr><td colspan="{cols}" class="empty-td">{msg}</td></tr>'

    def link(key):
        return f'<a href="{BASE_URL}/browse/{key}">{key}</a>'

    def sp_s(v):
        return f"{v:.0f}" if v else "-"

    out_rows_html = "".join(
        tr(link(r["key"]), r["summary"], r["status"], r["assignee"], sp_s(r["sp"]), r["priority"])
        for r in outstanding
    ) or empty(6, "Semua ticket sudah Done! 🎉")

    re_rows_html = "".join(
        tr(link(r["key"]), r["summary"], r["status"], r["assignee"],
           r["reopen_count"], r["last_reopen"], r["priority"])
        for r in reopen_rows
    ) or empty(7, "Tidak ada ticket yang reopen! 💪")

    d_header = th("Key", "Summary", "Assignee", "SP", "Actual (hari)", "Baseline (hari)", "Delay", "Priority")

    def delayed_rows(rows):
        return "".join(
            tr(link(r["key"]), r["summary"], r["assignee"], sp_s(r["sp"]),
               f"{r['actual_days']:.1f}", f"{r['baseline_days']:.1f}",
               f'<span class="delay-badge">+{r["delay_days"]:.1f}</span>', r["priority"])
            for r in rows
        ) or empty(8, "Tidak ada delayed ticket! 🚀")

    vel_rows_html = "".join(
        (f'<tr class="current-row"><td>S{i+1}</td><td>{html_lib.escape(n)} &nbsp;<b>← current</b></td><td><b>{v:.0f} SP</b></td></tr>'
         if n == sprint_name else
         f'<tr><td>S{i+1}</td><td>{html_lib.escape(n)}</td><td><b>{v:.0f} SP</b></td></tr>')
        for i, (n, v) in enumerate(velocity_history)
    )

    today_str = datetime.now().strftime("%d %B %Y %H:%M:%S")

    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>End of Sprint — {sprint_name_safe} — {team_name}</title>
<style>
  @page {{ size: A4 portrait; margin: 12mm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; color: #1a1a1a;
          padding: 0 260px; background: #f5f6f5; }}

  .report-header {{ background: linear-gradient(135deg, {color["primary"]}, {color["dark"]});
    color: #fff; padding: 28px 32px; border-radius: 10px; margin: 20px 0 16px;
    box-shadow: 0 4px 18px rgba(0,0,0,0.15); }}
  .report-header h1 {{ font-size: 22pt; font-weight: 800; margin-bottom: 5px; }}
  .report-header .sprint-name {{ font-size: 14pt; opacity: 0.9; margin-bottom: 4px; }}
  .report-header .meta {{ font-size: 9pt; opacity: 0.75; }}

  .stats-row {{ display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }}
  .stat-card {{ flex: 1; min-width: 90px; background: #fff; border-radius: 10px;
    padding: 14px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    text-align: center; border-top: 5px solid {color["primary"]}; }}
  .stat-num {{ font-size: 24pt; font-weight: 800; color: {color["dark"]}; line-height: 1; }}
  .stat-sp  {{ font-size: 9pt; color: #aaa; margin: 3px 0; }}
  .stat-label {{ font-size: 8pt; color: #888; text-transform: uppercase;
    letter-spacing: 0.5px; margin-top: 5px; }}

  .section {{ background: #fff; border-radius: 10px; padding: 20px 24px;
    margin-bottom: 14px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }}
  .section-title {{ font-size: 13pt; font-weight: 700; color: {color["dark"]};
    border-left: 5px solid {color["primary"]}; padding-left: 12px; margin-bottom: 14px; }}

  .completion-wrap {{ display: flex; align-items: center; gap: 28px; flex-wrap: wrap; }}
  .arc-item {{ text-align: center; }}
  .arc-label {{ font-size: 9.5pt; color: #555; font-weight: 600; margin-top: 5px; }}
  .day-bar-wrap {{ flex: 1; min-width: 180px; }}
  .day-bar-label {{ font-size: 9pt; color: #666; margin-bottom: 5px; }}
  .day-bar {{ background: #e8e8e8; border-radius: 8px; height: 20px; overflow: hidden; }}
  .day-bar-fill {{ height: 100%;
    background: linear-gradient(90deg, {color["primary"]}, {color["dark"]});
    border-radius: 8px; }}
  .day-bar-pct {{ font-size: 9pt; color: #aaa; margin-top: 3px; text-align: right; }}

  table {{ width: 100%; border-collapse: collapse; font-size: 9pt; margin-top: 6px; }}
  th {{ background: {color["primary"]}; color: #fff; padding: 7px 10px;
    text-align: left; font-weight: 600; }}
  td {{ padding: 6px 10px; border-bottom: 1px solid #eee; vertical-align: top; }}
  tr:nth-child(even) td {{ background: {color["light"]}; }}
  tr:hover td {{ background: #e4ede0; }}
  a {{ color: {color["dark"]}; text-decoration: none; font-weight: 600; }}
  .delay-badge {{ color: #c0392b; font-weight: 800; }}
  .empty-td {{ text-align: center; color: #bbb; font-style: italic; padding: 14px; }}
  .current-row td {{ background: {color["light"]}; font-weight: bold; }}
  .empty-note {{ color: #bbb; font-style: italic; font-size: 9.5pt; padding: 8px 0; }}

  .champion-box {{ border: 2px solid; border-radius: 10px; overflow: hidden; margin-bottom: 14px; }}
  .champion-header {{ color: #fff; padding: 10px 18px; font-size: 12pt;
    font-weight: 800; letter-spacing: 1px; }}
  .champion-content {{ padding: 16px 18px; }}
  .champion-main {{ display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }}
  .crown {{ font-size: 28pt; line-height: 1; }}
  .champion-name {{ font-size: 16pt; font-weight: 800; flex: 1; }}
  .champion-badge {{ color: #fff; padding: 4px 14px; border-radius: 20px;
    font-size: 10pt; font-weight: 700; white-space: nowrap; }}
  .leaderboard {{ display: flex; flex-direction: column; gap: 5px; }}
  .lb-item {{ display: flex; align-items: center; gap: 10px; padding: 6px 12px;
    background: #f5f5f5; border-radius: 6px; font-size: 9.5pt; }}
  .lb-name {{ flex: 1; font-weight: 600; }}
  .lb-count {{ color: #c0392b; font-weight: 700; }}

  .lb-cards {{ display: flex; flex-direction: column; gap: 8px; }}
  .lb-card {{ display: flex; align-items: center; gap: 14px; padding: 10px 16px;
    border-radius: 8px; background: #f9f9f9; }}
  .lb-rank {{ font-size: 16pt; width: 36px; text-align: center; }}
  .lb-person {{ flex: 1; font-size: 11pt; font-weight: 600; }}
  .lb-sp {{ font-size: 14pt; font-weight: 800; }}

  .footer {{ text-align: center; font-size: 8pt; color: #ccc; margin: 20px 0 16px;
    padding-top: 12px; border-top: 1px solid #eee; }}
  @media print {{
    body {{ padding: 0 20px; background: #fff; }}
    .report-header, th {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
</style>
</head>
<body>

<div class="report-header">
  <h1>End of Sprint Report</h1>
  <div class="sprint-name">{sprint_name_safe}</div>
  <div class="meta">{team_name} &nbsp;·&nbsp; {sprint_start} → {sprint_end} &nbsp;·&nbsp; Generated: {today_str}</div>
</div>

<div class="stats-row">
  <div class="stat-card">
    <div class="stat-num">{total_t}</div>
    <div class="stat-sp">{total_sp_val:.0f} SP</div>
    <div class="stat-label">Total</div>
  </div>
  <div class="stat-card">
    <div class="stat-num" style="color:#27ae60;">{done_t}</div>
    <div class="stat-sp">{done_sp_val:.0f} SP</div>
    <div class="stat-label">Done</div>
  </div>
  <div class="stat-card">
    <div class="stat-num" style="color:#e67e22;">{len(outstanding)}</div>
    <div class="stat-sp">{(buckets['progress'][1]+buckets['todo'][1]):.0f} SP</div>
    <div class="stat-label">Outstanding</div>
  </div>
  <div class="stat-card">
    <div class="stat-num" style="color:#c0392b;">{len(reopen_rows)}</div>
    <div class="stat-sp">&nbsp;</div>
    <div class="stat-label">Reopened</div>
  </div>
  <div class="stat-card">
    <div class="stat-num" style="color:#c0392b;">{len(dev_delayed)}</div>
    <div class="stat-sp">&nbsp;</div>
    <div class="stat-label">Delayed Dev</div>
  </div>
  <div class="stat-card">
    <div class="stat-num" style="color:#e67e22;">{len(qa_delayed)}</div>
    <div class="stat-sp">&nbsp;</div>
    <div class="stat-label">Delayed QA</div>
  </div>
</div>

<div class="section">
  <div class="section-title">📊 Completion Rate</div>
  <div class="completion-wrap">
    <div class="arc-item">
      {progress_arc_svg(done_pct_t, color["primary"])}
      <div class="arc-label">Tickets</div>
    </div>
    <div class="arc-item">
      {progress_arc_svg(done_pct_sp, color["dark"])}
      <div class="arc-label">Story Points</div>
    </div>
    <div class="day-bar-wrap">
      <div class="day-bar-label">⏱ Sprint Day Progress: <b>{elapsed_days} / {total_days} hari kerja</b></div>
      <div class="day-bar"><div class="day-bar-fill" style="width:{day_pct:.0f}%"></div></div>
      <div class="day-bar-pct">{day_pct:.0f}% hari sprint telah dilalui</div>
    </div>
  </div>
</div>

<div class="section">
  <div class="section-title">⏳ Outstanding Tickets <span style="font-weight:400;font-size:10pt;">({len(outstanding)} ticket)</span></div>
  <table><thead>{th("Key","Summary","Status","Assignee","SP","Priority")}</thead>
  <tbody>{out_rows_html}</tbody></table>
</div>

<div class="section">
  <div class="section-title">🔁 Reopened Tickets <span style="font-weight:400;font-size:10pt;">({len(reopen_rows)} ticket)</span></div>
  {champion_box(reopen_rows, "assignee", color["primary"])}
  <table><thead>{th("Key","Summary","Status","Assignee","Reopen","Last Reopen","Priority")}</thead>
  <tbody>{re_rows_html}</tbody></table>
</div>

<div class="section">
  <div class="section-title">📈 Velocity Trend</div>
  <table><thead>{th("#","Sprint","Completed SP")}</thead>
  <tbody>{vel_rows_html}</tbody></table>
</div>

<div class="section">
  <div class="section-title">🏅 Dev Leaderboard — Story Points Completed</div>
  <p style="font-size:9pt;color:#999;margin-bottom:12px;">Ticket yang mencapai DEV DONE dalam rentang sprint ini dan status akhir QA PASSED / Done.</p>
  <div class="lb-cards">{leaderboard_cards(dev_lb, color["primary"])}</div>
</div>

<div class="section">
  <div class="section-title">🏅 QA Leaderboard — Story Points Completed</div>
  <p style="font-size:9pt;color:#999;margin-bottom:12px;">Ticket yang mencapai QA PASSED dalam rentang sprint ini dan status akhir QA PASSED / Done.</p>
  <div class="lb-cards">{leaderboard_cards(qa_lb, color["dark"])}</div>
</div>

<div class="section">
  <div class="section-title">🔴 Delayed Tickets — Developer <span style="font-weight:400;font-size:10pt;">({len(dev_delayed)} ticket)</span></div>
  <p style="font-size:9pt;color:#999;margin-bottom:12px;">Total waktu In Progress vs baseline rata-rata per SP dari {BASELINE_SPRINT_COUNT} sprint closed terakhir.</p>
  {champion_box(dev_delayed, "assignee", color["primary"])}
  <table><thead>{d_header}</thead><tbody>{delayed_rows(dev_delayed)}</tbody></table>
</div>

<div class="section">
  <div class="section-title">🟠 Delayed Tickets — QA <span style="font-weight:400;font-size:10pt;">({len(qa_delayed)} ticket)</span></div>
  <p style="font-size:9pt;color:#999;margin-bottom:12px;">Total waktu QA TEST vs baseline rata-rata per SP dari {BASELINE_SPRINT_COUNT} sprint closed terakhir.</p>
  {champion_box([r for r in qa_delayed if r.get("is_qa_team")], "assignee", color["dark"])}
  <table><thead>{d_header}</thead><tbody>{delayed_rows(qa_delayed)}</tbody></table>
</div>

<div class="footer">Auto-generated by end_of_sprint_report.py — {today_str}</div>
</body>
</html>"""

# ── MAIN ──────────────────────────────────────────────────────────────────────
# Args: [team] [sprint_name]
# team: "buma" (default) or "mkp"
arg_team   = sys.argv[1].lower() if len(sys.argv) > 1 else "buma"
arg_sprint = sys.argv[2]          if len(sys.argv) > 2 else None

use_mkp    = arg_team == "mkp"
team_name  = "MKP Team" if use_mkp else "BUMA ID Team"
team_label = "MKP" if use_mkp else "BUMA_ID"

print("Fetching sprints...")
all_sprints, start_at_s = [], 0
while True:
    res  = get(f"{BASE_URL}/rest/agile/1.0/board/{BOARD_ID}/sprint?maxResults=50&startAt={start_at_s}")
    vals = res.get("values", [])
    all_sprints += vals
    if res.get("isLast", True) or not vals:
        break
    start_at_s += 50

closed_sprints = sorted(
    [s for s in all_sprints if s["state"] == "closed"],
    key=lambda x: x.get("endDate", ""), reverse=True
)
active_sprints = [s for s in all_sprints if s["state"] == "active"]

if use_mkp:
    team_closed = [s for s in closed_sprints if "Digiplan" in s["name"]]
    team_active = [s for s in active_sprints if "Digiplan" in s["name"]]
else:
    team_closed = [s for s in closed_sprints if "Digiplan" not in s["name"]]
    team_active = [s for s in active_sprints if "Digiplan" not in s["name"]]

team_all = team_active + team_closed  # active first when searching by name

if arg_sprint:
    matches = [s for s in team_all if arg_sprint.lower() in s["name"].lower()]
    target  = matches[0] if matches else (team_active[0] if team_active else team_closed[0])
else:
    target = team_active[0] if team_active else team_closed[0]

baseline_sprints = [s for s in team_closed if s["id"] != target["id"]][:BASELINE_SPRINT_COUNT]

print(f"Team            : {team_name}")
print(f"Target sprint   : {target['name']}")
print(f"Baseline sprints: {[s['name'] for s in baseline_sprints]}")

print("Building dev/QA baseline...")
dev_bl, qa_bl = build_dev_qa_baseline(baseline_sprints)

print("Fetching sprint issues...")
issues = fetch_sprint_issues(target["id"])

print("Building velocity history...")
velocity_history = build_velocity_history(list(reversed(baseline_sprints)) + [target])

print("Generating report...")
html_content = generate_html(team_name, target, issues, dev_bl, qa_bl, velocity_history)

safe_sprint = re.sub(r'[^\w\-]', '_', target['name'])
today_f     = datetime.now().strftime("%Y%m%d")
html_dir    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "html")
pdf_dir     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf")
os.makedirs(html_dir, exist_ok=True)
os.makedirs(pdf_dir,  exist_ok=True)

html_file = os.path.join(html_dir, f"EOS_{team_label}_{safe_sprint}_{today_f}.html")
pdf_file  = os.path.join(pdf_dir,  f"EOS {team_name} {target['name']} {today_f}.pdf")

with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"HTML saved: {html_file}")

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
file_url    = "file:///" + html_file.replace("\\", "/").replace(" ", "%20")
subprocess.run([chrome_path, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_file}", file_url], capture_output=True)
if os.path.exists(pdf_file):
    print(f"PDF saved:  {pdf_file}")
else:
    print("PDF generation failed — HTML still available.")
print("Done!")
