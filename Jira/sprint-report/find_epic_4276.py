import json, os, urllib.request, base64

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

# Find EPICs in IAMS30 that might be related to Additional Mechanic Order / Inspection
payload = json.dumps({
    "jql": 'project=IAMS30 AND issuetype=Epic ORDER BY created DESC',
    "maxResults": 20,
    "fields": ["summary", "status"]
}).encode()
req = urllib.request.Request('https://bukittechnology.atlassian.net/rest/api/3/search/jql', data=payload, headers=headers, method='POST')
resp = urllib.request.urlopen(req)
d = json.loads(resp.read())
print("Recent EPICs in IAMS30:")
for i in d.get('issues', []):
    print(i['key'], '--', i['fields']['summary'])
