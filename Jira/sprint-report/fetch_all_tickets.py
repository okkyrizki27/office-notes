# -*- coding: utf-8 -*-
import json, os, urllib.request, base64, sys
sys.stdout.reconfigure(encoding='utf-8')

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def extract_text(node):
    if not node: return ''
    if isinstance(node, str): return node
    if node.get('type') == 'text': return node.get('text', '')
    result = []
    for c in node.get('content', []):
        t = extract_text(c)
        if t.strip(): result.append(t)
    return ' | '.join(result) if len(result) > 1 else (result[0] if result else '')

def get_issue(key):
    req = urllib.request.Request(
        f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}?fields=summary,description,subtasks,status,issuetype',
        headers=headers
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

# Get all children of EPIC
payload = json.dumps({
    "jql": 'project=IAMS30 AND "Epic Link"=IAMS30-4275',
    "maxResults": 60,
    "fields": ["summary", "status", "issuetype", "subtasks"]
}).encode()
req = urllib.request.Request('https://bukittechnology.atlassian.net/rest/api/3/search/jql',
    data=payload, headers=headers, method='POST')
resp = urllib.request.urlopen(req)
d = json.loads(resp.read())
issues = d.get('issues', [])
print(f'Total child tickets: {len(issues)}')
print()

# Also get IAMS30-4375 (PlanForm ticket - created without Epic Link)
extra = ['IAMS30-4375']

all_keys = [i['key'] for i in issues] + extra

for key in sorted(all_keys):
    issue = get_issue(key)
    f = issue['fields']
    desc_raw = f.get('description', {})
    desc_text = extract_text(desc_raw)[:300] if desc_raw else '(no description)'
    subtasks = f.get('subtasks', [])
    print(f'=== {key} [{f["issuetype"]["name"]}] [{f["status"]["name"]}]')
    print(f'    {f["summary"]}')
    print(f'    DESC: {desc_text}')
    if subtasks:
        for s in subtasks:
            sf = s['fields']
            print(f'    >> {s["key"]} [{sf["status"]["name"]}]: {sf["summary"]}')
    print()
