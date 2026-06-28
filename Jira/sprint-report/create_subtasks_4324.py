import json, os, urllib.request, base64

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def p(text): return {'type':'paragraph','content':[{'type':'text','text':text}]}
def h(level, text): return {'type':'heading','attrs':{'level':level},'content':[{'type':'text','text':text}]}
def cb(text): return {'type':'codeBlock','attrs':{},'content':[{'type':'text','text':text}]}
def li(text): return {'type':'listItem','content':[{'type':'paragraph','content':[{'type':'text','text':text}]}]}
def ul(*items): return {'type':'bulletList','content':list(items)}

migration_sql = (
    "-- Run AFTER Task.sql deployed, BEFORE TaskPersonalized.sql updated\n"
    "UPDATE t\n"
    "SET t.MachineSMUValue = sub.MachineSMUValue,\n"
    "    t.MachineSMUAddress = sub.MachineSMUAddress\n"
    "FROM dbo.Task t\n"
    "INNER JOIN (\n"
    "  SELECT TaskId,\n"
    "         MAX(MachineSMUValue) AS MachineSMUValue,\n"
    "         MAX(MachineSMUAddress) AS MachineSMUAddress\n"
    "  FROM dbo.TaskPersonalized\n"
    "  WHERE MachineSMUValue IS NOT NULL OR MachineSMUAddress IS NOT NULL\n"
    "  GROUP BY TaskId\n"
    ") sub ON sub.TaskId = t.Id\n"
    "WHERE t.MachineSMUValue IS NULL;\n\n"
    "-- Verify (should return 0):\n"
    "SELECT COUNT(*) AS should_be_zero\n"
    "FROM dbo.Task t\n"
    "INNER JOIN dbo.TaskPersonalized tp ON tp.TaskId = t.Id\n"
    "WHERE (tp.MachineSMUValue IS NOT NULL OR tp.MachineSMUAddress IS NOT NULL)\n"
    "  AND t.MachineSMUValue IS NULL;"
)

subtasks = [
    {
        'summary': 'SSDT DDL: Task (add MachineSMUValue/Address) + TaskPersonalized (add StartedAt, remove SMU cols)',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Files'),
                ul(
                    li('Database.iAMS.MaintenanceExec/dbo/Tables/Task.sql'),
                    li('Database.iAMS.MaintenanceExec/dbo/Tables/TaskPersonalized.sql'),
                ),
                h(2, 'Task.sql — Add before CONSTRAINT line'),
                cb('[MachineSMUValue]    NVARCHAR(100) NULL,\n[MachineSMUAddress]  NVARCHAR(100) NULL,'),
                h(2, 'TaskPersonalized.sql — Add StartedAt, Remove SMU cols'),
                cb('[StartedAt] DATETIME NULL,'),
                p('Remove MachineSMUValue and MachineSMUAddress lines from CREATE TABLE definition (SSDT — never write DROP COLUMN manually).'),
                h(2, 'Deployment Order'),
                ul(
                    li('1. Deploy Task.sql (add SMU cols) — must be BEFORE migration script.'),
                    li('2. Run migration script (copy SMU data TaskPersonalized to Task).'),
                    li('3. Deploy TaskPersonalized.sql (add StartedAt, remove SMU) — AFTER migration script.'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('Task has MachineSMUValue and MachineSMUAddress columns (nullable).'),
                    li('TaskPersonalized has StartedAt column (nullable DateTime).'),
                    li('TaskPersonalized no longer has MachineSMUValue and MachineSMUAddress.'),
                    li('Deployed to dev without data loss.'),
                ),
            ]
        }
    },
    {
        'summary': 'Migration script: copy MachineSMUValue/Address from TaskPersonalized to Task before column drop',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Purpose'),
                p('Copy existing SMU values from TaskPersonalized to the corresponding Task record before removing the columns from TaskPersonalized. Must run between the two SSDT deployments.'),
                h(2, 'Script'),
                cb(migration_sql),
                h(2, 'Execution Steps'),
                ul(
                    li('1. Run in dev — verify COUNT = 0 from verification query.'),
                    li('2. Run in staging — verify.'),
                    li('3. Include in production deployment runbook between the two SSDT deploys.'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('All Task records that had corresponding TaskPersonalized SMU data are populated after migration.'),
                    li('Verification query returns 0.'),
                    li('Script is idempotent (safe to run twice without side effects).'),
                ),
            ]
        }
    },
    {
        'summary': 'Dapper updates: Task (add SMU cols), TaskPersonalized (add StartedAt, remove SMU), 1:N audit',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Service'),
                p('Services.iAMS.MaintenanceExec'),
                h(2, 'Task — Dapper changes'),
                ul(
                    li('Add MachineSMUValue and MachineSMUAddress to Task SELECT column lists and DTO/entity mapping.'),
                    li('Add to INSERT/UPDATE bindings where the field is written.'),
                ),
                h(2, 'TaskPersonalized — Dapper changes'),
                ul(
                    li('Add StartedAt to INSERT bindings — set on first Mulai tap, never updated.'),
                    li('Add StartedAt to SELECT column lists and DTO.'),
                    li('Remove MachineSMUValue and MachineSMUAddress from ALL TaskPersonalized queries (SELECT, INSERT, UPDATE).'),
                    li('Search entire codebase for TaskPersonalized MachineSMU references and remove all occurrences.'),
                ),
                h(2, '1:N Query Audit'),
                ul(
                    li('Find all Dapper queries using FirstOrDefault or SingleOrDefault on TaskPersonalized filtered only by TaskId (without UserCode) — these assume 1 record per Task.'),
                    li('Update each to handle N records per Task correctly.'),
                    li('Document all updated queries in the PR description.'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('No MachineSMU* references remain in TaskPersonalized queries.'),
                    li('StartedAt is correctly written on INSERT and returned in reads.'),
                    li('Task SMU columns readable via Dapper queries.'),
                    li('1:N audit complete — all affected queries documented and updated.'),
                    li('All existing tests pass with no regressions.'),
                ),
            ]
        }
    },
]

for s in subtasks:
    payload = json.dumps({
        'fields': {
            'project': {'id': '10173'},
            'parent': {'key': 'IAMS30-4324'},
            'summary': s['summary'],
            'description': s['desc'],
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
        print('Created:', result.get('key'), '--', s['summary'][:70])
    except urllib.error.HTTPError as e:
        print('Error:', e.code, e.read().decode()[:300])
