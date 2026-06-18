"""
Create Jira Ticket
Usage: python create_jira_ticket.py
Reads credentials from Jira/token/jira-api-token.md
"""

import urllib.request, base64, json, re, os

# ── credentials ──────────────────────────────────────────────────────────────
token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "Jira", "token", "jira-api-token.md")
with open(token_file, encoding="utf-8") as f:
    content = f.read()

def _val(key):
    m = re.search(rf'^{key}="([^"]+)"', content, re.MULTILINE)
    if not m:
        raise ValueError(f"{key} not found")
    return m.group(1)

EMAIL    = _val("JIRA_EMAIL")
TOKEN    = _val("JIRA_TOKEN")
BASE_URL = _val("JIRA_URL")
CREDS    = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()

def get(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {CREDS}", "Accept": "application/json"
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def post(url, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Basic {CREDS}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# ── lookup assignee ───────────────────────────────────────────────────────────
users = get(f"{BASE_URL}/rest/api/3/user/search?query=Dian+Heryana")
assignee_id = None
for u in users:
    if "dian" in u.get("displayName", "").lower():
        assignee_id = u["accountId"]
        print(f"Assignee found: {u['displayName']} ({assignee_id})")
        break

if not assignee_id:
    print("WARNING: Assignee not found, ticket will be unassigned.")

# ── lookup parent issue (Production Issue) ────────────────────────────────────
parent_res = post(f"{BASE_URL}/rest/api/3/search/jql", {
    "jql": 'project=IAMS30 AND summary~"Production Issue" ORDER BY created DESC',
    "fields": ["summary", "issuetype"],
    "maxResults": 5,
})
parent_key = None
for issue in parent_res.get("issues", []):
    print(f"Parent candidate: {issue['key']} — {issue['fields']['summary']}")
    if "production issue" in issue["fields"]["summary"].lower():
        parent_key = issue["key"]
        break

# ── build description (Atlassian Document Format) ────────────────────────────
steps = [
    "Data pareto cek possibility nya, apakah bisa di pindah ke Digiman+ -subcomponentdamage?",
    "Tarik dan compare 1 sample model mapping pareto antara dexecute dengan table di Digiman+",
    "Compare response API nya",
    "ReferenceId transaksi pakai apa? paretoId/code?",
    "Cek ke Digiman Transaction Dashboard",
    "Buat ticket development",
    "Development to resolve the issue",
    "Testing",
]

description_adf = {
    "type": "doc",
    "version": 1,
    "content": [
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": "Agreed step to resolve:", "marks": [{"type": "strong"}]}]
        },
        {
            "type": "orderedList",
            "content": [
                {
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": s}]}]
                }
                for s in steps
            ]
        }
    ]
}

# ── payload ───────────────────────────────────────────────────────────────────
summary = "[PRD Issue] [Piket] Error Endpoint /api/masterdatafailure/offline/component-subcomponent-damagecode/list dengan Status Code 400."

payload = {
    "fields": {
        "project":   {"key": "IAMS30"},
        "summary":   summary,
        "issuetype": {"name": "Bug"},
        "priority":  {"name": "Highest"},
        "description": description_adf,
    }
}

if assignee_id:
    payload["fields"]["assignee"] = {"accountId": assignee_id}

if parent_key:
    payload["fields"]["parent"] = {"key": parent_key}
    print(f"Parent set to: {parent_key}")

# ── create ────────────────────────────────────────────────────────────────────
result = post(f"{BASE_URL}/rest/api/3/issue", payload)
ticket_key = result.get("key")
print(f"\nTicket created: {ticket_key}")
print(f"URL: {BASE_URL}/browse/{ticket_key}")
