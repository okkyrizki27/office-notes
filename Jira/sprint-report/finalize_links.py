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
    # Parent-Child: inward = child ("is child of"), outward = parent ("is parent of")
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

# Link IAMS30-4375 and IAMS30-4376 to EPIC IAMS30-4275 using "Relates" (id: 10003)
link_issues('IAMS30-4375', 'IAMS30-4275', 10003)
link_issues('IAMS30-4376', 'IAMS30-4275', 10003)

# Also add comments to new tickets noting their EPIC context
add_comment('IAMS30-4375',
    'Ticket ini adalah bagian dari EPIC IAMS30-4275 (Form Packaging PM Shutdown). '
    'Dibuat sebagai hasil gap review — PlanForm table adalah prerequisite critical yang '
    'belum ada ticketnya. Epic Link tidak bisa diset via API; mohon PO/Scrum Master '
    'assign ke EPIC IAMS30-4275 secara manual dan masukkan ke sprint yang sama.'
)
add_comment('IAMS30-4376',
    'Ticket ini adalah bagian dari EPIC IAMS30-4275 (Form Packaging PM Shutdown). '
    'Dibuat sebagai hasil gap review — Assign to Me BE API adalah critical missing flow '
    'yang belum ada ticketnya. Epic Link tidak bisa diset via API; mohon PO/Scrum Master '
    'assign ke EPIC IAMS30-4275 secara manual dan masukkan ke sprint yang sama.'
)

# Summary comment on EPIC
add_comment('IAMS30-4275',
    '📋 Gap Review Complete. Berikut ringkasan semua perubahan yang dilakukan:\n\n'
    'TICKETS YANG DIUPDATE:\n'
    '• IAMS30-4321: Diperluas dari ShiftName saja menjadi 6 kolom snapshot (ShiftName, UserFullName, SiteCode, SiteName, SectionId, SectionName). Subtask 4338 dan 4339 diupdate.\n'
    '• IAMS30-4359: Subtask baru IAMS30-4364 — API accept 6 snapshot fields.\n'
    '• IAMS30-4324: 3 subtask baru (IAMS30-4365, 4366, 4367) — DDL migration Task+TaskPersonalized, migration script SMU, Dapper updates + 1:N audit.\n'
    '• IAMS30-4266: Subtask baru IAMS30-4368 — fix DigitalPlanning.MaintenanceCategoryName.\n'
    '• IAMS30-4272: Subtask baru IAMS30-4369 — pre-submit confirmation popup + form availability check.\n'
    '• IAMS30-4322: Subtask baru IAMS30-4370 — Finish tap handler (close session dengan actual timestamp).\n'
    '• IAMS30-4358: Subtask baru IAMS30-4371 — mobile conflict notification UX.\n'
    '• IAMS30-4267: Subtask baru IAMS30-4372 — packageSyncStatus field di work card detail response.\n'
    '• IAMS30-4324: Subtask baru IAMS30-4373 — WorkOrder.Status -> In Progress on first sync.\n'
    '• IAMS30-4264: Subtask baru IAMS30-4374 — migration script FormSubmission backfill.\n'
    '• IAMS30-4314 (subtask dari 4274): Ditambah error state "Form not available" AC.\n'
    '• IAMS30-4273: Ditambah error states (form not available + packageSyncStatus pending).\n\n'
    'TICKETS BARU:\n'
    '• IAMS30-4375: [BE] Create PlanForm Table in DPlanDB + DRAFT Form Assignment CRUD API — CRITICAL prerequisite.\n'
    '• IAMS30-4376: [BE] Assign to Me API (POST /api/tasks/{taskId}/assign-to-me) — CRITICAL missing flow.\n\n'
    'TICKET DIPINDAHKAN:\n'
    '• IAMS30-4276: Ditandai untuk dipindahkan ke EPIC lain (kemungkinan IAMS30-4155 Order Improvement). Mohon PO/Scrum Master update Epic Link secara manual.'
)
