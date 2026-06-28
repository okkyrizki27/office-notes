import json, os, urllib.request, base64

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def p(text): return {'type':'paragraph','content':[{'type':'text','text':text}]}

# Comment on IAMS30-4276
comment_4276 = {
    'body': {
        'type': 'doc', 'version': 1, 'content': [
            p('⚠️ Ticket ini tampaknya salah masuk ke EPIC IAMS30-4275 (Form Packaging PM Shutdown). Kontennya (Activity Type LOV separation untuk Additional Mechanic Order vs Additional Inspection) tidak berkaitan dengan form packaging.'),
            p('Mohon dipindahkan ke EPIC yang lebih sesuai, kemungkinan IAMS30-4155 (Order Improvement) atau IAMS30-4153 (Inspection Improvement). Epic Link tidak bisa diubah via API — mohon PO/Scrum Master update secara manual di Jira board.'),
        ]
    }
}

req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4276/comment',
    data=json.dumps(comment_4276).encode(), headers=headers, method='POST'
)
resp = urllib.request.urlopen(req)
print('Comment added to IAMS30-4276:', resp.status)

# Comment on IAMS30-4275 (EPIC)
comment_4275 = {
    'body': {
        'type': 'doc', 'version': 1, 'content': [
            p('📋 Gap Review Note: IAMS30-4276 ([Mobile] Separate Activity Type LOV Between Additional Mechanic Order and Additional Inspection) tampak salah masuk ke EPIC ini. Ticket tersebut tidak berkaitan dengan Form Packaging. Mohon PO/Scrum Master pindahkan ke EPIC yang sesuai (IAMS30-4155 Order Improvement atau IAMS30-4153 Inspection Improvement) dan keluarkan dari sprint tracking EPIC ini.'),
        ]
    }
}

req2 = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4275/comment',
    data=json.dumps(comment_4275).encode(), headers=headers, method='POST'
)
resp2 = urllib.request.urlopen(req2)
print('Comment added to IAMS30-4275:', resp2.status)
