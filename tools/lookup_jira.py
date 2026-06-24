import urllib.request, base64, json, re, os

token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "Jira", "token", "jira-api-token.md")
with open(token_file, encoding="utf-8") as f:
    content = f.read()

def _val(key):
    m = re.search(rf'^{key}="([^"]+)"', content, re.MULTILINE)
    return m.group(1)

EMAIL    = _val("JIRA_EMAIL")
TOKEN    = _val("JIRA_TOKEN")
BASE_URL = _val("JIRA_URL")
CREDS    = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()

def get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {CREDS}", "Accept": "application/json"})
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

# Lookup board ID for IAMS30
boards = get(f"{BASE_URL}/rest/agile/1.0/board?projectKeyOrId=IAMS30")
for b in boards.get("values", []):
    board_id = b.get("id")
    board_name = b.get("name")
    print(f"Board: {board_name} | {board_id}")

    # Lookup sprints for this board
    sprints = get(f"{BASE_URL}/rest/agile/1.0/board/{board_id}/sprint?state=active,future")
    for s in sprints.get("values", []):
        print(f"  Sprint: {s.get('name')} | {s.get('id')} | {s.get('state')}")

# Lookup fix version via JQL
res = post(f"{BASE_URL}/rest/api/3/search/jql", {
    "jql": 'project=IAMS30 AND fixVersion="4.0.1" ORDER BY created DESC',
    "fields": ["fixVersions"],
    "maxResults": 1,
})
for issue in res.get("issues", []):
    for v in issue["fields"].get("fixVersions", []):
        print(f"Fix Version: {v.get('name')} | {v.get('id')}")
