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
    cell_type = 'tableHeader' if header else 'tableCell'
    return {'type':'tableRow','content':[{'type':cell_type,'attrs':{},'content':[{'type':'paragraph','content':[{'type':'text','text':str(c)}]}]} for c in cells]}
def table(*rows): return {'type':'table','attrs':{'isNumberColumnEnabled':False,'layout':'default'},'content':list(rows)}

# ===================== GAP-C4: PlanForm Table =====================
planform_ddl = (
    "CREATE TABLE [dbo].[PlanForm] (\n"
    "  [Id]           UNIQUEIDENTIFIER NOT NULL DEFAULT NEWSEQUENTIALID(),\n"
    "  [PlanId]        UNIQUEIDENTIFIER NOT NULL,  -- FK to DigitalPlanning\n"
    "  [FormId]        UNIQUEIDENTIFIER NOT NULL,  -- FK to Form in maintenance-strategy\n"
    "  [FormName]      NVARCHAR(255)    NOT NULL,  -- snapshot at assign time, refreshed at SUBMIT\n"
    "  [IsMandatory]   BIT              NOT NULL DEFAULT 0,\n"
    "  [IsDeleted]     BIT              NOT NULL DEFAULT 0,  -- soft delete on unassign\n"
    "  [CreatedAt]     DATETIME         NOT NULL DEFAULT GETUTCDATE(),\n"
    "  [CreatedBy]     NVARCHAR(255)    NOT NULL,\n"
    "  [ModifiedAt]    DATETIME         NULL,\n"
    "  [ModifiedBy]    NVARCHAR(255)    NULL,\n"
    "  CONSTRAINT [PK_PlanForm] PRIMARY KEY CLUSTERED ([Id]),\n"
    "  CONSTRAINT [FK_PlanForm_Plan] FOREIGN KEY ([PlanId])\n"
    "    REFERENCES [dbo].[DigitalPlanning] ([Id])\n"
    ")"
)

desc_planform = {
    'type': 'doc', 'version': 1, 'content': [
        h(2, 'Background'),
        p('Currently, IAMS30-4266 (Extend Create Digital Planning) accepts form assignment in the create request and immediately creates Task + FormSubmission + Cosmos snapshot — there is no persistent storage for form assignments during DRAFT phase. This means: (1) Planners cannot add or remove forms after initial plan creation while still in DRAFT, and (2) packageSyncStatus logic (which compares PlanForm count vs Task count) has no source of truth in dplan DB.'),
        p('This ticket creates the PlanForm table in DPlanDB and implements the DRAFT lifecycle API endpoints.'),
        h(2, 'Scope'),
        ul(
            li('Service: dplan (Services.iAMS.DPlan or equivalent)'),
            li('Database: DPlanDB'),
            li('Table: dbo.PlanForm'),
        ),
        h(2, 'Schema'),
        cb(planform_ddl),
        h(2, 'API Endpoints'),
        table(
            table_row('Method', 'Endpoint', 'Description', header=True),
            table_row('POST', '/api/digitalPlanning/{planId}/forms', 'Add one or more forms to a DRAFT plan. Upsert by PlanId+FormId.'),
            table_row('PUT', '/api/digitalPlanning/{planId}/forms/{formId}', 'Update IsMandatory for an assigned form (DRAFT only).'),
            table_row('DELETE', '/api/digitalPlanning/{planId}/forms/{formId}', 'Soft-delete (IsDeleted=1) a form from assignment (DRAFT only).'),
            table_row('GET', '/api/digitalPlanning/{planId}/forms', 'List all active (IsDeleted=0) form assignments for a plan.'),
        ),
        h(2, 'Business Rules'),
        ul(
            li('All write operations (add, update, delete) are only allowed when plan status = DRAFT. Return 400 if plan is SUBMIT or higher.'),
            li('Unassigning a form uses soft delete (IsDeleted=1) — never hard delete.'),
            li('FormName is stored at assignment time (snapshot). Re-fetched from maintenance-strategy at plan SUBMIT time to ensure latest name.'),
            li('Upsert by PlanId+FormId: if form already exists (IsDeleted=0), update IsMandatory. If exists with IsDeleted=1, restore it (IsDeleted=0).'),
            li('GET endpoint returns only IsDeleted=0 records.'),
            li('TenantCode isolation enforced from JWT.'),
        ),
        h(2, 'Integration with IAMS30-4266'),
        p('After this table is in place, IAMS30-4266 (Extend Create Digital Planning) should be updated to: (1) read form assignments from PlanForm table instead of the request body, and (2) trigger the Task+FormSubmission+Cosmos snapshot creation from PlanForm records. Coordinate with assignee of IAMS30-4266.'),
        h(2, 'Acceptance Criteria'),
        ul(
            li('PlanForm table created in DPlanDB with correct schema.'),
            li('POST endpoint adds forms to DRAFT plan — upsert by PlanId+FormId.'),
            li('PUT endpoint updates IsMandatory for DRAFT plan forms.'),
            li('DELETE endpoint soft-deletes form from DRAFT plan.'),
            li('GET endpoint returns only active (IsDeleted=0) forms.'),
            li('All write operations blocked when plan status is not DRAFT — returns 400.'),
            li('Integration tests: add, update, soft-delete, restore; attempt write on SUBMIT plan returns 400.'),
        ),
    ]
}

# ===================== GAP-C7: Assign to Me BE API =====================
desc_assign = {
    'type': 'doc', 'version': 1, 'content': [
        h(2, 'Background'),
        p('When a mechanic taps "Assign to Me" in the 3-dot menu of a form card (Tab Form on mobile workcard), the system must create a TaskPersonalized record linking the mechanic to the Task. This is a prerequisite for the mechanic to open and fill the form. Without this API, the entire form execution flow is blocked — mechanics cannot assign themselves.'),
        h(2, 'Endpoint'),
        cb('POST /api/tasks/{taskId}/assign-to-me'),
        h(2, 'Request'),
        cb('// No request body needed — authenticated user from JWT is the mechanic\n// taskId from path param'),
        h(2, 'Processing'),
        cb(
            '// Upsert by TaskId + UserCode (idempotent)\n'
            'MERGE dbo.TaskPersonalized AS target\n'
            'USING (SELECT @TaskId AS TaskId, @UserCode AS UserCode) AS source\n'
            'ON target.TaskId = source.TaskId AND target.UserCode = source.UserCode\n'
            'WHEN NOT MATCHED THEN\n'
            '  INSERT (Id, TaskId, UserCode, Status, CreatedBy, CreatedAt)\n'
            '  VALUES (NEWID(), @TaskId, @UserCode, \'InProgress\', @UserCode, GETUTCDATE())\n'
            'WHEN MATCHED THEN\n'
            '  UPDATE SET ModifiedAt = GETUTCDATE(), ModifiedBy = @UserCode;'
        ),
        h(2, 'Business Rules'),
        ul(
            li('Idempotent: calling Assign to Me multiple times (from different devices) results in exactly 1 TaskPersonalized record per mechanic per task.'),
            li('UserCode taken from authenticated JWT — mechanic cannot assign to another user via this endpoint.'),
            li('Task must belong to a WorkOrder accessible to the authenticated user (same site/tenant).'),
            li('If Task.Status = Complete or Approved, return 400 — cannot assign to a completed form.'),
            li('TenantCode isolation enforced.'),
        ),
        h(2, 'Response'),
        cb(
            '// 200 OK (already assigned) or 201 Created (newly assigned)\n'
            '{\n'
            '  "taskPersonalizedId": "guid",\n'
            '  "taskId": "guid",\n'
            '  "userCode": "string",\n'
            '  "assignedAt": "datetime"\n'
            '}'
        ),
        h(2, 'Offline behavior'),
        p('Mobile creates a TaskPersonalized record locally when tapping "Assign to Me" offline. This endpoint is called when syncing. The upsert ensures no duplicate is created if multiple devices sync the same assignment.'),
        h(2, 'Acceptance Criteria'),
        ul(
            li('POST /api/tasks/{taskId}/assign-to-me creates a TaskPersonalized record for the authenticated user.'),
            li('Calling the endpoint twice with the same user + task returns 200 with existing record — no duplicate created.'),
            li('Returns 404 if taskId not found or not accessible to the user.'),
            li('Returns 400 if Task.Status is Complete or Approved.'),
            li('Unit tests: first assign (201), duplicate assign (200), completed task (400), unauthorized task (404).'),
        ),
    ]
}

new_tickets = [
    {
        'summary': '[BE] Form Package — Create PlanForm Table in DPlanDB + DRAFT Form Assignment CRUD API',
        'desc': desc_planform,
        'epic': 'IAMS30-4275',
    },
    {
        'summary': '[BE] Form Package — Assign to Me: Create/Upsert TaskPersonalized (POST /api/tasks/{taskId}/assign-to-me)',
        'desc': desc_assign,
        'epic': 'IAMS30-4275',
    },
]

for t in new_tickets:
    payload = json.dumps({
        'fields': {
            'project': {'id': '10173'},
            'summary': t['summary'],
            'description': t['desc'],
            'issuetype': {'id': '10259'},  # Task
            'customfield_10014': t['epic'],  # Epic Link
        }
    }).encode()
    req = urllib.request.Request(
        'https://bukittechnology.atlassian.net/rest/api/3/issue',
        data=payload, headers=headers, method='POST'
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print('Created:', result.get('key'), '--', t['summary'][:70])
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print('Error:', e.code, body[:400])
        # Try without Epic Link field
        payload2 = json.dumps({
            'fields': {
                'project': {'id': '10173'},
                'summary': t['summary'],
                'description': t['desc'],
                'issuetype': {'id': '10259'},
            }
        }).encode()
        req2 = urllib.request.Request(
            'https://bukittechnology.atlassian.net/rest/api/3/issue',
            data=payload2, headers=headers, method='POST'
        )
        try:
            resp2 = urllib.request.urlopen(req2)
            result2 = json.loads(resp2.read())
            print('Created (without epic link):', result2.get('key'), '--', t['summary'][:70])
        except urllib.error.HTTPError as e2:
            print('Error2:', e2.code, e2.read().decode()[:300])
