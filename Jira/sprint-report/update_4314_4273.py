import json, os, urllib.request, base64

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def p(text): return {'type':'paragraph','content':[{'type':'text','text':text}]}
def h(level, text): return {'type':'heading','attrs':{'level':level},'content':[{'type':'text','text':text}]}
def cb(text): return {'type':'codeBlock','attrs':{},'content':[{'type':'text','text':text}]}
def li(text): return {'type':'listItem','content':[{'type':'paragraph','content':[{'type':'text','text':text}]}]}
def ul(*items): return {'type':'bulletList','content':list(items)}

# Fetch existing description of IAMS30-4314
req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4314?fields=summary,description',
    headers=headers
)
resp = urllib.request.urlopen(req)
existing = json.loads(resp.read())
print('Current 4314 summary:', existing['fields']['summary'])

# Append "Form not available" error state to 4314 description
# Build updated description: existing content + new section
existing_content = existing['fields'].get('description', {}).get('content', [])

additional_content = [
    h(2, 'Additional: Form not available error state'),
    p('Edge case: Task and FormSubmission records exist, but the Cosmos snapshot was NOT created (form was archived between plan SUBMIT and consumer processing). The form card appears in Tab Form but the form cannot be opened.'),
    h(3, 'Error state behavior when tapping form card'),
    ul(
        li('Detect: FormSubmissionId is available but Cosmos snapshot fetch returns 404 or empty.'),
        li('Do NOT navigate to form renderer.'),
        li('Show inline error on the form card (or a dialog): "Form not available. Please contact your admin."'),
        li('Form card remains visible in the list — mechanic can see the form name and mandatory/optional badge, but cannot open it.'),
    ),
    h(3, 'Acceptance Criteria (additional)'),
    ul(
        li('When tapping a form card whose Cosmos snapshot does not exist, navigation is prevented.'),
        li('Error message shown: "Form not available. Please contact your admin."'),
        li('Other form cards in the list are unaffected and still openable.'),
        li('Widget test: snapshot-not-found case shows error message and does not navigate.'),
    ),
]

updated_desc = {
    'type': 'doc', 'version': 1,
    'content': existing_content + additional_content
}

payload = json.dumps({'fields': {'description': updated_desc}}).encode()
req2 = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4314',
    data=payload, headers=headers, method='PUT'
)
resp2 = urllib.request.urlopen(req2)
print('IAMS30-4314 updated:', resp2.status)

# ===================== IAMS30-4273 — add form card error state AC =====================
req3 = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4273?fields=summary,description',
    headers=headers
)
resp3 = urllib.request.urlopen(req3)
existing_4273 = json.loads(resp3.read())
existing_content_4273 = existing_4273['fields'].get('description', {}).get('content', [])
print('Current 4273 summary:', existing_4273['fields']['summary'])

additional_4273 = [
    h(2, 'Additional: Error states for form cards'),
    h(3, 'Form not available state'),
    ul(
        li('A form card may exist (Task + FormSubmission created) but the Cosmos snapshot is missing (form archived between plan submit and processing).'),
        li('Form card should still be visible in the list with the correct name and mandatory badge.'),
        li('Status badge: show "Not Available" (distinct from Not filled / In Progress / Complete).'),
        li('Tapping such a card shows: "Form not available. Please contact your admin." — no navigation to form renderer.'),
    ),
    h(3, 'packageSyncStatus = pending state'),
    ul(
        li('When packageSyncStatus = "pending": show a full-tab message: "Service package sync in progress, wait for a moment."'),
        li('Finish Execution button disabled with hint: "Form package is not yet available. Please try again later or contact your admin."'),
        li('No form card list shown during pending state.'),
    ),
    h(3, 'Acceptance Criteria (additional)'),
    ul(
        li('Form card with missing Cosmos snapshot shows "Not Available" badge — not a regular status.'),
        li('Tapping a "Not Available" form card shows error message, no navigation.'),
        li('packageSyncStatus = pending shows loading/pending message and blocks Finish Execution button.'),
        li('Widget tests cover both error states.'),
    ),
]

updated_desc_4273 = {
    'type': 'doc', 'version': 1,
    'content': existing_content_4273 + additional_4273
}

payload2 = json.dumps({'fields': {'description': updated_desc_4273}}).encode()
req4 = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4273',
    data=payload2, headers=headers, method='PUT'
)
resp4 = urllib.request.urlopen(req4)
print('IAMS30-4273 updated:', resp4.status)
