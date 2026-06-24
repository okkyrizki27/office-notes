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

def text(t, bold=False):
    node = {"type": "text", "text": t}
    if bold:
        node["marks"] = [{"type": "strong"}]
    return node

def paragraph(*nodes):
    return {"type": "paragraph", "content": list(nodes)}

def heading(level, t):
    return {"type": "heading", "attrs": {"level": level}, "content": [text(t)]}

def bullet_list(items):
    return {
        "type": "bulletList",
        "content": [
            {"type": "listItem", "content": [paragraph(text(i))]}
            for i in items
        ]
    }

def ordered_list(items):
    return {
        "type": "orderedList",
        "content": [
            {"type": "listItem", "content": [paragraph(text(i))]}
            for i in items
        ]
    }

description_adf = {
    "type": "doc",
    "version": 1,
    "content": [
        heading(2, "Bug Description"),
        paragraph(text(
            "Setelah penambahan form IIR ke dalam sistem, form WICOPE Check yang seharusnya "
            "tampil seluruhnya hanya menampilkan 3 item di tampilan UI. "
            "Hal ini juga terkonfirmasi dari response API yang hanya mengembalikan 3 form WICOPE Check, "
            "bukan jumlah yang seharusnya."
        )),

        heading(2, "Steps to Reproduce"),
        ordered_list([
            "Login ke aplikasi dengan akun yang memiliki akses ke form WICOPE Check.",
            "Navigasi ke halaman yang menampilkan daftar form WICOPE Check.",
            "Perhatikan jumlah form yang tampil di UI — hanya muncul 3.",
            "Cek response API pada endpoint yang mengambil data form WICOPE Check — response hanya mengembalikan 3 data.",
        ]),

        heading(2, "Expected Behavior"),
        paragraph(text(
            "Semua form WICOPE Check yang terdaftar seharusnya tampil di UI dan "
            "dikembalikan secara lengkap oleh response API."
        )),

        heading(2, "Actual Behavior"),
        paragraph(text(
            "Hanya 3 form WICOPE Check yang muncul di UI dan di response API, "
            "meskipun seharusnya lebih dari 3."
        )),

        heading(2, "Root Cause Hypothesis"),
        paragraph(text(
            "Diduga ada konflik atau pembatasan (limit/filter) yang tidak disengaja setelah "
            "penambahan form IIR — kemungkinan berdampak pada query atau logika pengambilan data form WICOPE Check."
        )),

        heading(2, "Impact"),
        bullet_list([
            "Pengguna tidak dapat mengakses seluruh form WICOPE Check yang tersedia.",
            "Data yang ditampilkan tidak akurat dan tidak lengkap.",
        ]),

        heading(2, "Additional Notes"),
        bullet_list([
            "Bug ini muncul setelah penambahan form IIR — perlu dicek apakah ada side effect terhadap logika fetch form WICOPE Check.",
            "Perlu dilakukan investigasi pada layer API dan database query.",
        ]),
    ]
}

payload = {
    "fields": {
        "project":     {"key": "IAMS30"},
        "summary":     "Setelah ditambah form IIR, form WICOPE Check hanya muncul 3 di tampilan UI, terlihat juga dari response API hanya muncul 3.",
        "issuetype":   {"name": "Bug"},
        "priority":    {"name": "Highest"},
        "assignee":    {"accountId": "62b029e8dcafd965c5dc9b53"},
        "fixVersions": [{"id": "13485"}],
        "description": description_adf,
        "customfield_10020": 5740,  # Sprint ID: 4.0.1 - Improve and Fix
    }
}

result = post(f"{BASE_URL}/rest/api/3/issue", payload)
ticket_key = result.get("key")
print(f"Ticket created: {ticket_key}")
print(f"URL: {BASE_URL}/browse/{ticket_key}")
