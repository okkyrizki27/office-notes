# -*- coding: utf-8 -*-
import json, os, urllib.request, base64, sys, time
sys.stdout.reconfigure(encoding='utf-8')

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def extract(node):
    if not node: return ''
    t = node.get('type','')
    if t == 'text': return node.get('text','')
    if t == 'hardBreak': return '\n'
    parts = [extract(c) for c in node.get('content',[])]
    joined = ' | '.join(p for p in parts if p.strip())
    if t == 'heading': return f'[H{node.get("attrs",{}).get("level",2)}] {joined}'
    if t == 'listItem': return f'- {joined}'
    if t in ('tableCell','tableHeader'): return joined
    if t == 'tableRow': return ' || '.join(parts)
    return joined

def get_full(key, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}?fields=summary,description,subtasks,issuetype,status',
                headers=headers)
            resp = urllib.request.urlopen(req, timeout=30)
            return json.loads(resp.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                raise e

# Get all children of EPIC
payload = json.dumps({
    "jql": 'project=IAMS30 AND "Epic Link"=IAMS30-4275',
    "maxResults": 60,
    "fields": ["summary","status","issuetype","subtasks"]
}).encode()
req = urllib.request.Request('https://bukittechnology.atlassian.net/rest/api/3/search/jql',
    data=payload, headers=headers, method='POST')
resp = urllib.request.urlopen(req)
children = json.loads(resp.read()).get('issues', [])
print(f'Found {len(children)} child tickets')

output = []
for i, issue in enumerate(children):
    key = issue['key']
    time.sleep(0.5)
    d = get_full(key)
    f = d['fields']
    desc = extract(f.get('description') or {})
    row = {
        'key': key,
        'type': f['issuetype']['name'],
        'status': f['status']['name'],
        'summary': f['summary'],
        'desc': desc,
        'subtasks': []
    }
    for s in f.get('subtasks', []):
        sk = s['key']
        time.sleep(0.3)
        sd = get_full(sk)
        sf = sd['fields']
        sdesc = extract(sf.get('description') or {})
        row['subtasks'].append({
            'key': sk,
            'summary': sf['summary'],
            'desc': sdesc,
        })
    output.append(row)
    print(f'[{i+1}/{len(children)}] {key} OK — {len(row["subtasks"])} subtasks')

with open('all_tickets.json', 'w', encoding='utf-8') as fp:
    json.dump(output, fp, ensure_ascii=False, indent=2)
print('\nSaved to all_tickets.json')
print(f'Total subtasks: {sum(len(t["subtasks"]) for t in output)}')
