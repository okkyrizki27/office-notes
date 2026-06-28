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

subtasks = [
    # GAP-M1: Finish tap handler under IAMS30-4322
    {
        'parent': 'IAMS30-4322',
        'summary': 'Finish tap handler: close TaskPersonalizedLog session with actual EndDate + queue sync',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Background'),
                p('After tapping "Mulai" (Start) and filling a form, a mechanic can exit the form temporarily without submitting — this is the "Finish" action. Tapping Finish must close the current open TaskPersonalizedLog session with EndDate = actual tap time. This differs from auto-close (which uses shift end time): explicit Finish means the mechanic knows exactly when they stopped.'),
                h(2, 'UX'),
                p('A "Finish" button/action is shown inside the form detail screen (alongside or below the form content), accessible to an assigned mechanic who has already tapped Mulai. It is hidden when the form is already Complete (submitted).'),
                h(2, 'Client-side logic'),
                cb(
                    'function handleFinishTap(taskPersonalizedId, deviceTimestamp):\n'
                    '  openSession = TaskPersonalizedLog.find(\n'
                    '    taskPersonalizedId, EndDate=null\n'
                    '  )\n'
                    '  if not openSession: return  // no open session, no-op\n\n'
                    '  openSession.EndDate = deviceTimestamp  // actual tap time\n'
                    '  queue UPDATE openSession\n'
                    '  // queued in batch sync — not sent immediately'
                ),
                h(2, 'Key distinction from auto-close'),
                ul(
                    li('Auto-close (via Start in new shift) -> EndDate = shift end time of the previous session.'),
                    li('Explicit Finish tap -> EndDate = actual device timestamp of the tap.'),
                    li('PRD Scenario 10: mechanic taps Finish at 19:00 even though shift ended at 18:00 -> EndDate = 19:00 (actual), not 18:00.'),
                ),
                h(2, 'Offline behavior'),
                ul(
                    li('Fully offline. EndDate set locally with device clock.'),
                    li('Queued in same batch sync as other operations.'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('Tapping Finish sets EndDate = device timestamp on the open TaskPersonalizedLog session.'),
                    li('If no open session exists, Finish tap is a no-op.'),
                    li('EndDate from explicit Finish tap is the actual tap time — not shift end time.'),
                    li('Form remains openable after Finish (mechanic can tap Mulai again to create a new session in the same or next shift).'),
                    li('Update is queued for batch sync and works fully offline.'),
                    li('Widget test: Finish sets EndDate correctly; Finish with no open session is no-op.'),
                ),
            ]
        }
    },
    # GAP-M2: Conflict notification under IAMS30-4358
    {
        'parent': 'IAMS30-4358',
        'summary': 'Mobile: show conflict notification for fields rejected by First Write Wins on sync response',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Background'),
                p('When a mechanic syncs form field data, the server responds with which fields were accepted and which were rejected (already filled earlier by another mechanic — First Write Wins). The mobile client must surface this to the mechanic clearly, without treating it as an error.'),
                h(2, 'Server response structure'),
                cb(
                    '{\n'
                    '  "accepted": ["fieldId1", "fieldId3"],\n'
                    '  "rejected": [\n'
                    '    { "fieldId": "fieldId2", "reason": "already_written_by_other", "writtenBy": "Mechanic A" }\n'
                    '  ]\n'
                    '}'
                ),
                h(2, 'UX behavior'),
                ul(
                    li('Sync is considered SUCCESSFUL even if some fields are rejected — no error state.'),
                    li('If rejected list is non-empty: show a dismissible info banner/snackbar.'),
                    li('Message format: "Sync successful. {N} field(s) were not saved as they were already filled earlier by {mechanic name(s)}."'),
                    li('Rejected fields are visually reverted on screen to the value from the server (the winning value).'),
                    li('Mechanic does not need to take any action — this is informational only.'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('After sync, if rejected list is empty: no notification shown.'),
                    li('After sync, if rejected list is non-empty: info banner shown with correct count and mechanic name(s).'),
                    li('Rejected field values are replaced on screen with the server-winning value.'),
                    li('Sync is not shown as failed or errored when rejections exist.'),
                    li('Banner is dismissible by the mechanic.'),
                    li('Widget test: rejected fields trigger banner; empty rejected list shows no banner.'),
                ),
            ]
        }
    },
    # GAP-M3: packageSyncStatus under IAMS30-4267 — update existing subtask description
    # We'll create a new subtask since 4293 exists but needs explicit packageSyncStatus scope
    {
        'parent': 'IAMS30-4267',
        'summary': 'Add packageSyncStatus field to work card detail response DTO (none / pending / ready)',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Background'),
                p('The mobile Tab Form needs to distinguish three states when displaying the form package. These states are derived server-side from the relationship between PlanForm records and Task records — the mobile client should not implement this derivation logic itself.'),
                h(2, 'packageSyncStatus derivation logic'),
                table(
                    table_row('Condition', 'packageSyncStatus', 'Mobile UX', header=True),
                    table_row('PlanForm WHERE IsDeleted=0 count = 0', 'none', 'Tab Form empty state — no forms assigned. Finish Execution not blocked by forms.'),
                    table_row('PlanForm WHERE IsDeleted=0 count > 0, Task count = 0', 'pending', '"Service package sync in progress, wait for a moment." Finish Execution BLOCKED.'),
                    table_row('Task count > 0', 'ready', 'Show form card list normally.'),
                ),
                p('Note: use PlanForm WHERE IsDeleted=0 (exclude soft-deleted). Do NOT count hard-deleted or soft-deleted PlanForm records.'),
                h(2, 'Response DTO addition'),
                cb(
                    '// Add to Plan.Shared or top-level work card detail response:\n'
                    '"packageSyncStatus": "none" | "pending" | "ready"'
                ),
                h(2, 'Implementation notes'),
                ul(
                    li('Derived at runtime — no new DB column needed.'),
                    li('Query: count PlanForm (IsDeleted=0) and Task records for the PlanId.'),
                    li('If PlanId has no PlanForm records at all -> "none".'),
                    li('If PlanForm records exist but Task count = 0 -> "pending" (consumer not yet processed).'),
                    li('If Task count > 0 -> "ready".'),
                    li('If packageSyncStatus = "pending": Finish Execution endpoint must also block (handled in IAMS30-4269).'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('packageSyncStatus field present in GET /api/work-card/detail response.'),
                    li('Returns "none" when plan has no form assignment.'),
                    li('Returns "pending" when plan has form assignment but Task not yet created.'),
                    li('Returns "ready" when Tasks are present.'),
                    li('Unit test covers all 3 states.'),
                ),
            ]
        }
    },
    # GAP-M4: WorkOrder In Progress under IAMS30-4324
    {
        'parent': 'IAMS30-4324',
        'summary': 'Update WorkOrder.Status to In Progress on first TaskPersonalized sync for that WorkOrder',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Background'),
                p('When the first mechanic assigns themselves to a form and syncs their TaskPersonalized record, the parent WorkOrder status must transition from Open to In Progress. This signals that execution has started. The transition is triggered by the first TaskPersonalized sync for any Task belonging to that WorkOrder — not by a separate explicit action.'),
                h(2, 'Logic'),
                cb(
                    '-- On TaskPersonalized sync (upsert):\n'
                    'IF WorkOrder.Status = "Open"\n'
                    '  AND at least 1 TaskPersonalized record now exists for any Task in this WorkOrder:\n'
                    '  UPDATE WorkOrder SET Status = "In Progress"\n\n'
                    '-- Status is idempotent: if already In Progress or Complete, do not downgrade.'
                ),
                h(2, 'Scope'),
                ul(
                    li('Service: Services.iAMS.MaintenanceExec'),
                    li('Triggered inside the TaskPersonalized upsert handler (same handler extended in IAMS30-4324 base scope).'),
                    li('WorkOrder.Status transition: Open -> In Progress only. Never downgrade from In Progress or Complete.'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('WorkOrder.Status changes to In Progress on the first TaskPersonalized sync for that WorkOrder.'),
                    li('Second or subsequent TaskPersonalized syncs do not change WorkOrder.Status if already In Progress.'),
                    li('WorkOrder.Status is never downgraded from In Progress or Complete by this logic.'),
                    li('Test: Open WorkOrder -> first sync -> In Progress; second sync -> still In Progress; Complete WorkOrder -> sync -> still Complete.'),
                ),
            ]
        }
    },
    # GAP-M5: Migration script for FormSubmission backfill under IAMS30-4264
    {
        'parent': 'IAMS30-4264',
        'summary': 'Migration: backfill FormName=NULL and IsMandatory=0 for existing FormSubmission records after ALTER TABLE',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Background'),
                p('When FormName and IsMandatory columns are added to FormSubmission (IAMS30-4264 base scope), existing records will have NULL for both. For IsMandatory this is acceptable behavior (defaults to 0 / not mandatory). For FormName the NULL is also acceptable per PRD (existing data does not need backfill). However, a migration script should confirm no unintended side effects and set IsMandatory = 0 for any NULLs to enforce the default.'),
                h(2, 'Script'),
                cb(
                    '-- After ALTER TABLE: set IsMandatory default for existing rows\n'
                    'UPDATE dbo.FormSubmission\n'
                    'SET IsMandatory = 0\n'
                    'WHERE IsMandatory IS NULL;\n\n'
                    '-- FormName left as NULL for existing records (acceptable per PRD)\n\n'
                    '-- Verify:\n'
                    'SELECT COUNT(*) AS should_be_zero FROM dbo.FormSubmission WHERE IsMandatory IS NULL;'
                ),
                h(2, 'Rules'),
                ul(
                    li('IsMandatory must be non-null after migration — default 0 for existing rows.'),
                    li('FormName stays NULL for existing rows — no backfill needed.'),
                    li('Script is idempotent.'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('No existing FormSubmission records have IsMandatory = NULL after migration.'),
                    li('Verification query returns 0.'),
                    li('FormName remains NULL for pre-existing records — no error.'),
                    li('New FormSubmission records created after this change have FormName and IsMandatory populated correctly.'),
                ),
            ]
        }
    },
]

for s in subtasks:
    payload = json.dumps({
        'fields': {
            'project': {'id': '10173'},
            'parent': {'key': s['parent']},
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
        print('Created:', result.get('key'), 'under', s['parent'], '--', s['summary'][:60])
    except urllib.error.HTTPError as e:
        print('Error under', s['parent'], ':', e.code, e.read().decode()[:300])
