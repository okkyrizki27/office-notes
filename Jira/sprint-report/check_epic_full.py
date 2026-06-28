# -*- coding: utf-8 -*-
import json, os, urllib.request, base64, sys
sys.stdout.reconfigure(encoding='utf-8')

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def extract_text(node, indent=0):
    if not node: return ''
    ntype = node.get('type','')
    if ntype == 'text': return node.get('text','')
    if ntype == 'heading':
        level = node.get('attrs',{}).get('level',2)
        text = ''.join(extract_text(c) for c in node.get('content',[]))
        return f'\n{"#"*level} {text}\n'
    if ntype in ('paragraph','tableCell','tableHeader'):
        text = ''.join(extract_text(c) for c in node.get('content',[]))
        return text + '\n'
    if ntype == 'listItem':
        text = ''.join(extract_text(c) for c in node.get('content',[]))
        return f'  - {text.strip()}\n'
    if ntype == 'tableRow':
        cells = [extract_text(c).strip() for c in node.get('content',[])]
        return ' | '.join(cells) + '\n'
    result = ''
    for c in node.get('content',[]):
        result += extract_text(c, indent)
    return result

req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4275?fields=summary,description',
    headers=headers)
resp = urllib.request.urlopen(req)
d = json.loads(resp.read())
f = d['fields']

print('=== TITLE ===')
print(f['summary'])
print()
print('=== FULL DESCRIPTION ===')
desc = f.get('description')
if desc:
    print(extract_text(desc))
else:
    print('(kosong)')
