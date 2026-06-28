import json, os, urllib.request, base64

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def p(text): return {'type':'paragraph','content':[{'type':'text','text':text}]}
def h(level, text): return {'type':'heading','attrs':{'level':level},'content':[{'type':'text','text':text}]}
def cb(text): return {'type':'codeBlock','attrs':{},'content':[{'type':'text','text':text}]}
def li(text): return {'type':'listItem','content':[{'type':'paragraph','content':[{'type':'text','text':text}]}]}
def ul(*items): return {'type':'bulletList','content':list(items)}

desc = {
    'type': 'doc', 'version': 1, 'content': [
        h(2, 'Background'),
        p('Before the Planner submits a plan with a form package, the system must show a confirmation popup that: (1) displays all selected forms, and (2) checks whether each form is still available in maintenance-strategy. If any form is unavailable, the Confirm button is disabled until the Planner removes that form or re-activates it in Form Builder. This prevents plans from being submitted with broken form references — which would cause mechanics to see "Form not available" errors in the field.'),
        h(2, 'Context: when this popup appears'),
        p('Triggered when the Planner clicks the primary Submit / Create button after completing the Choose Form step (Step 2). This replaces or extends the existing submit confirmation (if any).'),
        h(2, 'Popup Content'),
        ul(
            li('Title: "Confirm Plan Submission"'),
            li('Body: list of all selected forms, each showing: form name, Mandatory/Optional badge, availability status.'),
            li('Availability status per form: checking (loading), Available (green), Not Available (red + reason).'),
            li('Footer: Cancel button (always enabled) + Confirm button (enabled only when all forms are Available).'),
        ),
        h(2, 'Form Availability Rules'),
        p('A form is considered NOT AVAILABLE if any of the following is true:'),
        ul(
            li('Not found in maintenance-strategy at all (hard deleted).'),
            li('IsActive = 0 (deactivated).'),
            li('Status = Archived.'),
        ),
        p('If the Planner has no forms selected (empty package), skip the availability check — Confirm button is enabled immediately.'),
        h(2, 'API call for availability check'),
        cb('GET /api/maintenance-strategy/forms/availability?formIds=uuid1,uuid2,...\n\nResponse:\n[\n  { "formId": "uuid1", "isAvailable": true },\n  { "formId": "uuid2", "isAvailable": false, "reason": "Form is archived" }\n]'),
        p('Note: this API endpoint may need to be created. Coordinate with BE if not yet available.'),
        h(2, 'UX Flow'),
        ul(
            li('1. Planner clicks Submit/Create.'),
            li('2. Popup opens showing form list with "checking..." status per form.'),
            li('3. FE calls availability check API.'),
            li('4. Each form updates to Available or Not Available.'),
            li('5. If all available: Confirm enabled. Planner clicks Confirm -> existing create plan API called.'),
            li('6. If any not available: Confirm stays disabled. Planner must go back and remove the unavailable form(s) from the package.'),
        ),
        h(2, 'Acceptance Criteria'),
        ul(
            li('Confirmation popup appears when Planner clicks Submit after Choose Form step.'),
            li('All selected forms are listed with their Mandatory/Optional badge.'),
            li('Availability check API is called for all forms in the list.'),
            li('Forms that are unavailable show a red Not Available status with reason.'),
            li('Confirm button is disabled if any form is Not Available.'),
            li('Confirm button is enabled when all forms are Available (or no forms selected).'),
            li('Clicking Confirm proceeds with the existing create plan API call (IAMS30-4272 base scope).'),
            li('Clicking Cancel closes the popup without submitting.'),
        ),
    ]
}

payload = json.dumps({
    'fields': {
        'project': {'id': '10173'},
        'parent': {'key': 'IAMS30-4272'},
        'summary': 'Pre-submit confirmation popup: show form list + availability check, block Confirm if any form unavailable',
        'description': desc,
        'issuetype': {'id': '10262'},
    }
}).encode()

req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue',
    data=payload, headers=headers, method='POST'
)
try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    print('Created:', result.get('key'))
except urllib.error.HTTPError as e:
    print('Error:', e.code, e.read().decode()[:400])
