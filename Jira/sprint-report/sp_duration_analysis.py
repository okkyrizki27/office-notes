"""
Analisa rata-rata waktu pengerjaan (cycle time) per Story Point,
dipisah per tim:
  - MKP Team    = sprint "Migration/Migrating Digiplan - Sx"
  - BUMA ID Team = sprint "Release ... - Sx" (4.0.x dan 3.1.0)

Cycle time = waktu dari transisi status pertama keluar dari
To Do/Backlog (masuk In Progress/Dev Done/QA Test/Re-open)
sampai transisi terakhir ke status Done/Closed/QA PASSED.
"""

import urllib.request
import base64
import json
import os
import re
import statistics
from datetime import datetime

DONE_STATUSES = {"Done", "Closed", "QA PASSED"}
PROGRESS_STATUSES = {"In Progress", "DEV DONE", "QA TEST", "Re-open"}
TODO_STATUSES = {"To Do", "Backlog"}

TARGET_SP = [1, 2, 3, 5, 8]

MKP_SPRINTS = {
    5670: "Migration Digiplan - S5",
    5604: "Migration Digiplan - S4",
    5505: "Migrating Digiplan - S3",
    5405: "Migrating Digiplan - S2",
    5172: "Migrating Digiplan - S1",
}

BUMA_SPRINTS = {
    5739: "Release 4.0.0 - S3",
    5738: "Release 4.0.0 - S2",
    5538: "Release 4.0.0 - S1",
    5372: "Release 3.1.0 (Sprint 2)",
    5238: "Release 3.1.0 (Sprint 1)",
}


def _load_jira_credentials():
    token_file = os.path.join("..", "token", "jira-api-token.md")
    with open(token_file, encoding="utf-8") as f:
        content = f.read()

    def _val(key):
        m = re.search(rf'^{key}="([^"]+)"', content, re.MULTILINE)
        return m.group(1)

    return _val("JIRA_EMAIL"), _val("JIRA_TOKEN"), _val("JIRA_URL")


EMAIL, TOKEN, BASE_URL = _load_jira_credentials()
_CREDS = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()


def get(url):
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Basic {_CREDS}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def sp(fields):
    val = fields.get("customfield_10016")
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def parse_dt(s):
    # Jira datetime format: 2026-06-05T10:23:45.123+0700
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")


def fetch_sprint_issues(sprint_id):
    issues = []
    start_at = 0
    while True:
        url = (
            f"{BASE_URL}/rest/agile/1.0/sprint/{sprint_id}/issue"
            f"?fields=status,customfield_10016,issuetype"
            f"&expand=changelog&maxResults=50&startAt={start_at}"
        )
        res = get(url)
        batch = res.get("issues", [])
        issues += batch
        total = res.get("total", 0)
        start_at += len(batch)
        if start_at >= total or not batch:
            break
    return issues


def compute_cycle_time(issue):
    """Return cycle time (To Do -> DEV DONE) in hours, or None if cannot be determined."""
    histories = issue.get("changelog", {}).get("histories", [])
    # histories are returned newest-first by Jira; sort oldest-first
    transitions = []
    for h in histories:
        created = h["created"]
        for item in h.get("items", []):
            if item["field"] == "status":
                transitions.append(
                    (created, item.get("fromString"), item.get("toString"))
                )
    transitions.sort(key=lambda t: t[0])

    start_time = None
    end_time = None
    for created, from_s, to_s in transitions:
        if start_time is None and from_s in TODO_STATUSES and (
            to_s in PROGRESS_STATUSES or to_s in DONE_STATUSES
        ):
            start_time = created
        if end_time is None and to_s == "DEV DONE":
            end_time = created  # keep first transition into DEV DONE

    if start_time is None or end_time is None:
        return None

    delta = parse_dt(end_time) - parse_dt(start_time)
    hours = delta.total_seconds() / 3600
    if hours < 0:
        return None
    return hours


def analyze(team_name, sprint_map):
    # data[sp_value] = list of cycle times in hours
    data = {sp_val: [] for sp_val in TARGET_SP}

    for sprint_id, sprint_name in sprint_map.items():
        issues = fetch_sprint_issues(sprint_id)
        for issue in issues:
            fields = issue["fields"]
            sp_val = sp(fields)
            if sp_val not in TARGET_SP:
                continue
            ct = compute_cycle_time(issue)
            if ct is not None:
                data[sp_val].append(ct)

    print(f"\n=== {team_name} ===")
    print(f"{'SP':>4} | {'n':>4} | {'avg (hari)':>11} | {'avg (jam)':>10} | {'median (hari)':>13}")
    print("-" * 55)
    for sp_val in TARGET_SP:
        vals = data[sp_val]
        if not vals:
            print(f"{sp_val:>4} | {0:>4} | {'-':>11} | {'-':>10} | {'-':>13}")
            continue
        avg_h = statistics.mean(vals)
        med_h = statistics.median(vals)
        print(
            f"{sp_val:>4} | {len(vals):>4} | {avg_h/24:>11.2f} | {avg_h:>10.1f} | {med_h/24:>13.2f}"
        )

    return data


if __name__ == "__main__":
    analyze("MKP Team (Migration Digiplan)", MKP_SPRINTS)
    analyze("BUMA ID Team (Release 4.0.x / 3.1.0)", BUMA_SPRINTS)
