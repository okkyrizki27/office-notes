"""Create subtasks for IAMS30-4234 based on agreed steps."""

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

def post(url, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Basic {CREDS}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

PARENT = "IAMS30-4234"
PREFIX = "[PRD Issue] [Piket]"

STEPS = [
    "Data pareto cek possibility nya, apakah bisa di pindah ke Digiman+ -subcomponentdamage?",
    "Tarik dan compare 1 sample model mapping pareto antara dexecute dengan table di Digiman+",
    "Compare response API nya",
    "ReferenceId transaksi pakai apa? paretoId/code?",
    "Cek ke Digiman Transaction Dashboard",
    "Buat ticket development",
    "Development to resolve the issue",
    "Testing",
]

for i, step in enumerate(STEPS, 1):
    payload = {
        "fields": {
            "project":   {"key": "IAMS30"},
            "parent":    {"key": PARENT},
            "summary":   f"{PREFIX} {step}",
            "issuetype": {"name": "Sub Task"},
            "priority":  {"name": "Highest"},
        }
    }
    result = post(f"{BASE_URL}/rest/api/3/issue", payload)
    key = result.get("key")
    print(f"  [{i}] {key} — {step[:60]}...")
