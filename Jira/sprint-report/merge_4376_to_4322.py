import json, os, urllib.request, base64

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def p(text): return {'type':'paragraph','content':[{'type':'text','text':text}]}
def h(level, text): return {'type':'heading','attrs':{'level':level},'content':[{'type':'text','text':text}]}
def cb(text): return {'type':'codeBlock','attrs':{},'content':[{'type':'text','text':text}]}
def li(text): return {'type':'listItem','content':[{'type':'paragraph','content':[{'type':'text','text':text}]}]}
def ul(*items): return {'type':'bulletList','content':list(items)}
def table_row(*cells, header=False):
    ct = 'tableHeader' if header else 'tableCell'
    return {'type':'tableRow','content':[{'type':ct,'attrs':{},'content':[{'type':'paragraph','content':[{'type':'text','text':str(c)}]}]} for c in cells]}
def table(*rows): return {'type':'table','attrs':{'isNumberColumnEnabled':False,'layout':'default'},'content':list(rows)}

# Fetch current IAMS30-4322
req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4322?fields=summary,description,subtasks',
    headers=headers
)
resp = urllib.request.urlopen(req)
d4322 = json.loads(resp.read())
print('4322 summary:', d4322['fields']['summary'])
existing_content = d4322['fields'].get('description', {}).get('content', [])
subtasks_4322 = d4322['fields'].get('subtasks', [])
print('Existing subtasks:', [s['key'] + ' ' + s['fields']['summary'] for s in subtasks_4322])
