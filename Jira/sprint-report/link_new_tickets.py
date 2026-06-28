import json, os, urllib.request, base64

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def p(text): return {'type':'paragraph','content':[{'type':'text','text':text}]}

def add_comment(ticket_key, text):
    payload = json.dumps({'body': {'type': 'doc', 'version': 1, 'content': [p(text)]}}).encode()
    req = urllib.request.Request(
        f'https://bukittechnology.atlassian.net/rest/api/3/issue/{ticket_key}/comment',
        data=payload, headers=headers, method='POST'
    )
    resp = urllib.request.urlopen(req)
    print(f'Comment on {ticket_key}:', resp.status)

def link_issues(inward_key, outward_key, link_type_id):
    payload = json.dumps({
        'type': {'id': str(link_type_id)},
        'inwardIssue': {'key': inward_key},
        'outwardIssue': {'key': outward_key},
    }).encode()
    req = urllib.request.Request(
        'https://bukittechnology.atlassian.net/rest/api/3/issueLink',
        data=payload, headers=headers, method='POST'
    )
    try:
        resp = urllib.request.urlopen(req)
        print(f'Linked {inward_key} <-> {outward_key}: {resp.status}')
    except urllib.error.HTTPError as e:
        print(f'Link error {inward_key}<->{outward_key}:', e.code, e.read().decode()[:200])

# Get available link types
req = urllib.request.Request('https://bukittechnology.atlassian.net/rest/api/3/issueLinkType', headers=headers)
resp = urllib.request.urlopen(req)
link_types = json.loads(resp.read())
for lt in link_types.get('issueLinkTypes', []):
    print('Link type:', lt['id'], lt['name'], '->', lt.get('inward'), '/', lt.get('outward'))
