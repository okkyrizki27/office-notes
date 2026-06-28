import json, os, urllib.request, base64

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

# First check the field names for Epic Link
req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4276?fields=summary,customfield_10014',
    headers=headers
)
resp = urllib.request.urlopen(req)
d = json.loads(resp.read())
print('Current Epic Link (customfield_10014):', d['fields'].get('customfield_10014'))

# Update Epic Link to IAMS30-4155
payload = json.dumps({
    'fields': {
        'customfield_10014': 'IAMS30-4155'
    }
}).encode()
req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4276',
    data=payload, headers=headers, method='PUT'
)
try:
    resp = urllib.request.urlopen(req)
    print('IAMS30-4276 moved to IAMS30-4155. Status:', resp.status)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print('Error:', e.code, body[:500])
