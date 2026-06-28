import json, os, urllib.request, base64

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def p(text): return {'type':'paragraph','content':[{'type':'text','text':text}]}
def h(level, text): return {'type':'heading','attrs':{'level':level},'content':[{'type':'text','text':text}]}
def cb(text): return {'type':'codeBlock','attrs':{},'content':[{'type':'text','text':text}]}
def li(text): return {'type':'listItem','content':[{'type':'paragraph','content':[{'type':'text','text':text}]}]}
def ul(*items): return {'type':'bulletList','content':list(items)}

fix_sql = (
    "-- On INSERT or UPDATE DigitalPlanning:\n"
    "SELECT Name AS MaintenanceCategoryName\n"
    "FROM DPlanDB.dbo.MaintenanceCategory\n"
    "WHERE MaintenanceCategoryCode = @MaintenanceCategoryCode\n\n"
    "-- Store result in DigitalPlanning.MaintenanceCategoryName\n"
    "-- If no match found, store NULL (do not throw error)"
)

desc = {
    'type': 'doc', 'version': 1, 'content': [
        h(2, 'Background'),
        p('DigitalPlanning.MaintenanceCategoryName is currently always NULL — only MaintenanceCategoryCode is saved. This causes WorkOrder.MaintenanceCategoryName in maintenance-execution to also be empty, breaking category display and reporting on mobile.'),
        h(2, 'Fix'),
        p('On every INSERT or UPDATE of a DigitalPlanning record, perform a JOIN to MaintenanceCategory and save the Name to MaintenanceCategoryName.'),
        cb(fix_sql),
        h(2, 'Scope'),
        ul(
            li('Service: dplan (Services.iAMS.DPlan or equivalent)'),
            li('Table: DPlanDB.dbo.DigitalPlanning'),
            li('Lookup table: DPlanDB.dbo.MaintenanceCategory'),
        ),
        h(2, 'Rules'),
        ul(
            li('Fix applies to new records only — no backfill of existing records (acceptable per PRD).'),
            li('If MaintenanceCategoryCode has no matching MaintenanceCategory record, store NULL without error.'),
            li('This fix must be in place before plan creation with form package is deployed, so the PlanSubmitted event (or sync API call) includes a valid MaintenanceCategoryName.'),
        ),
        h(2, 'Acceptance Criteria'),
        ul(
            li('When a new DigitalPlanning record is created with a valid MaintenanceCategoryCode, MaintenanceCategoryName is populated.'),
            li('If MaintenanceCategoryCode has no match in MaintenanceCategory, MaintenanceCategoryName is NULL and no error is thrown.'),
            li('Existing DigitalPlanning records are unaffected.'),
            li('WorkOrder.MaintenanceCategoryName in maintenance-execution is non-null for plans created after this fix.'),
        ),
    ]
}

payload = json.dumps({
    'fields': {
        'project': {'id': '10173'},
        'parent': {'key': 'IAMS30-4266'},
        'summary': 'Fix: populate DigitalPlanning.MaintenanceCategoryName on INSERT/UPDATE via MaintenanceCategory join',
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
