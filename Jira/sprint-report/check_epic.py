# -*- coding: utf-8 -*-
import json, os, urllib.request, base64, sys
sys.stdout.reconfigure(encoding='utf-8')

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def extract_text(node):
    if not node: return ''
    if node.get('type') == 'text': return node.get('text', '')
    result = []
    for c in node.get('content', []):
        t = extract_text(c)
        if t.strip(): result.append(t)
    return ' '.join(result)

req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4275?fields=summary,description,status',
    headers=headers)
resp = urllib.request.urlopen(req)
d = json.loads(resp.read())
f = d['fields']

print('SUMMARY:', f['summary'])
print('STATUS:', f['status']['name'])
print()
desc = f.get('description')
if not desc:
    print('DESCRIPTION: (kosong / null)')
else:
    text = extract_text(desc)
    print('DESCRIPTION (preview 1000 chars):')
    print(text[:1000])
