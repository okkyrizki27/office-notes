# -*- coding: utf-8 -*-
import json, os, urllib.request, base64, sys, time
sys.stdout.reconfigure(encoding='utf-8')

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def p(t): return {'type':'paragraph','content':[{'type':'text','text':t}]}
def h(l,t): return {'type':'heading','attrs':{'level':l},'content':[{'type':'text','text':t}]}
def li(t): return {'type':'listItem','content':[{'type':'paragraph','content':[{'type':'text','text':t}]}]}
def ul(*i): return {'type':'bulletList','content':list(i)}

def put(key, fields, retries=3):
    data = json.dumps({'fields': fields}).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}',
                data=data, headers=headers, method='PUT')
            resp = urllib.request.urlopen(req, timeout=30)
            print(f'PUT {key}: {resp.status}')
            return
        except Exception as e:
            if attempt < retries - 1:
                print(f'  Retry {attempt+1}...')
                time.sleep(3)
            else:
                print(f'  FAILED: {e}')

def get_desc(key, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}?fields=description',
                headers=headers)
            resp = urllib.request.urlopen(req, timeout=30)
            return json.loads(resp.read())['fields'].get('description', {}).get('content', [])
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
            else:
                return []

time.sleep(2)

# IAMS30-4271
existing_4271 = get_desc('IAMS30-4271')
time.sleep(1)
put('IAMS30-4271', {
    'description': {'type':'doc','version':1,'content': existing_4271 + [
        h(2,'Manual Search — Client-Side Filtering'),
        p('Selain melihat form suggestion (Group 1 dan Group 2), Planner bisa melakukan '
          'manual search untuk menemukan form di luar suggestion.'),
        ul(
            li('Manual search TIDAK memerlukan API call baru. FE filter client-side dari list yang sudah difetch.'),
            li('Endpoint GET form list (IAMS30-4265) TIDAK perlu parameter searchTerm.'),
            li('Filtering berdasarkan formName, case-insensitive, partial match.'),
            li('Filter tidak mereset selection state.'),
            li('Fetch SEKALI saat modal dibuka — search berulang tidak trigger fetch ulang.'),
        ),
    ]}
})

time.sleep(2)

# IAMS30-4305
existing_4305 = get_desc('IAMS30-4305')
time.sleep(1)
put('IAMS30-4305', {
    'description': {'type':'doc','version':1,'content': existing_4305 + [
        h(2,'Manual Search — Client-Side Only, No Extra API Call'),
        p('Hook ini fetch form list SEKALI saat modal dibuka. '
          'Manual search untuk menemukan form di luar suggestion dilakukan SEPENUHNYA client-side.'),
        ul(
            li('Hook TIDAK menerima atau mengirim parameter searchTerm ke API.'),
            li('FE filter list lokal menggunakan search input state dari modal.'),
            li('Cache hit saat re-open (equipment tidak berubah) tetap berlaku — list difetch sekali, difilter berkali-kali client-side.'),
        ),
    ]}
})

print('Gap 6 done.')
