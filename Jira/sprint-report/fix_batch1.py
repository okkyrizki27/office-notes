# -*- coding: utf-8 -*-
import json, os, urllib.request, base64, sys
sys.stdout.reconfigure(encoding='utf-8')

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def p(t): return {'type':'paragraph','content':[{'type':'text','text':t}]}
def h(l,t): return {'type':'heading','attrs':{'level':l},'content':[{'type':'text','text':t}]}
def cb(t): return {'type':'codeBlock','attrs':{},'content':[{'type':'text','text':t}]}
def li(t): return {'type':'listItem','content':[{'type':'paragraph','content':[{'type':'text','text':t}]}]}
def ul(*i): return {'type':'bulletList','content':list(i)}
def tr(*cells, hdr=False):
    ct = 'tableHeader' if hdr else 'tableCell'
    return {'type':'tableRow','content':[{'type':ct,'attrs':{},'content':[p(str(c))]} for c in cells]}
def tbl(*rows): return {'type':'table','attrs':{'isNumberColumnEnabled':False,'layout':'default'},'content':list(rows)}

def put(key, fields):
    data = json.dumps({'fields': fields}).encode()
    req = urllib.request.Request(
        f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}',
        data=data, headers=headers, method='PUT')
    resp = urllib.request.urlopen(req)
    print(f'PUT {key}: {resp.status}')

def post_subtask(parent, summary, desc):
    data = json.dumps({'fields': {
        'project': {'id': '10173'},
        'parent': {'key': parent},
        'summary': summary,
        'description': desc,
        'issuetype': {'id': '10262'},
    }}).encode()
    req = urllib.request.Request('https://bukittechnology.atlassian.net/rest/api/3/issue',
        data=data, headers=headers, method='POST')
    try:
        resp = urllib.request.urlopen(req)
        r = json.loads(resp.read())
        print(f'  SUBTASK {r["key"]}: {summary[:65]}')
        return r['key']
    except urllib.error.HTTPError as e:
        print(f'  ERROR: {e.code}', e.read().decode()[:200])

def post_comment(key, text):
    data = json.dumps({'body':{'type':'doc','version':1,'content':[p(text)]}}).encode()
    req = urllib.request.Request(
        f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}/comment',
        data=data, headers=headers, method='POST')
    resp = urllib.request.urlopen(req)
    print(f'COMMENT {key}: {resp.status}')

def post_link(inward, outward, link_id):
    data = json.dumps({
        'type': {'id': str(link_id)},
        'inwardIssue': {'key': inward},
        'outwardIssue': {'key': outward},
    }).encode()
    req = urllib.request.Request('https://bukittechnology.atlassian.net/rest/api/3/issueLink',
        data=data, headers=headers, method='POST')
    try:
        resp = urllib.request.urlopen(req)
        print(f'LINK {inward} duplicates {outward}: {resp.status}')
    except urllib.error.HTTPError as e:
        print(f'  LINK ERROR: {e.code}', e.read().decode()[:150])

# ─────────────────────────────────────────────────────────────────────────────
# 1. IAMS30-4358: Update title + full description
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 1. IAMS30-4358 ===')
put('IAMS30-4358', {
    'summary': '[BE] Form Package — Per-Field Sync: First Write Wins, Batching, Conflict Resolution, Auto-Sync, dan Submit Form',
    'description': {'type':'doc','version':1,'content':[
        h(2,'Background'),
        p('Beberapa mechanic bisa mengisi satu form bersamaan secara offline-first. Sistem harus mengelola sinkronisasi per-field (bukan per-dokumen), mendeteksi dan meresolusi konflik, serta menangani Submit Form sebagai aksi final yang mengunci form.'),

        h(2,'A — Per-Field Save & Sync'),
        h(3,'Granularitas sync: per field + batching'),
        p('Client hanya mengirim field yang berubah (dirty fields). Semua dirty fields dikirim dalam satu batch request per sync session — satu network round trip.'),
        cb(
            'POST /api/form-submissions/{formSubmissionId}/sync\n'
            'Body: {\n'
            '  requestId: uuid,         // idempotency per batch\n'
            '  fields: [\n'
            '    { tabId, fieldId, value, timestamp, updatedBy },\n'
            '    ...\n'
            '  ]\n'
            '}\n\n'
            'Response: {\n'
            '  accepted: [fieldId, ...],\n'
            '  rejected: [{ fieldId, reason: "already_written_by_other", writtenBy: "Mechanic A" }]\n'
            '}'
        ),

        h(3,'Conflict resolution: First Write Wins per field'),
        p('Setiap field di Cosmos menyimpan: value, timestamp (device clock saat input), updatedBy.'),
        cb(
            '// Server-side conflict resolution per field:\n'
            'IF existing.timestamp < incoming.timestamp:\n'
            '  DISCARD incoming  // existing wins\n'
            '  REPORT field sebagai "rejected" ke client\n'
            'ELIF existing.timestamp == incoming.timestamp:\n'
            '  DISCARD incoming  // no-op, dianggap berhasil (idempotency)\n'
            'ELSE:\n'
            '  UPDATE field dengan incoming value  // incoming wins'
        ),
        p('Known limitation: timestamp menggunakan device clock — bisa tidak akurat. Acceptable risk karena kemungkinan dua mechanic mengisi field yang sama di momen identik sangat kecil di lapangan tambang.'),

        h(3,'Idempotency key & timestamp collision'),
        ul(
            li('Idempotency key per field: fieldId + timestamp.'),
            li('Jika dua mechanic submit field yang sama dengan timestamp identik (device clock tidak sinkron): sync pertama diproses, sync berikutnya dianggap berhasil (no-op) — tidak overwrite, tidak error.'),
            li('Setiap batch diberi unique requestId. Partial failure -> retry batch yang sama -> server tidak proses field yang sudah diproses (idempotent by fieldId+timestamp).'),
        ),

        h(3,'Auto-sync triggers (aktif saat ada koneksi)'),
        tbl(
            tr('Trigger','Aksi','Interval', hdr=True),
            tr('After input (debounce)','Upload dirty fields + download latest dari server','3 detik setelah input terakhir'),
            tr('Background timer','Download latest saja (tanpa upload jika tidak ada dirty)','Setiap 30 detik'),
        ),
        p('Auto-sync aktif hanya saat ada koneksi. Timer 30 detik mempengaruhi battery — trade-off yang sudah diterima.'),

        h(3,'Visibility antar mechanic'),
        p('Mechanic bisa saling melihat progress pengisian rekannya secara near real-time per field (bukan per tab). Auto-sync yang aktif setiap 3-30 detik memastikan update dari mechanic lain terlihat tanpa perlu persistent connection.'),

        h(3,'Sistem tidak tracking device'),
        p('Sistem tidak perlu tahu device mana saja yang sedang mengerjakan form yang sama. Koordinasi sepenuhnya tanggung jawab operasional mechanic dan supervisor.'),

        h(2,'B — Submit Form (aksi final)'),
        p('Submit dilakukan SEKALI oleh SATU mechanic sebagai perwakilan. Submit mengunci form secara final — tidak bisa diubah setelah submit. Lihat subtask IAMS30-TBD untuk implementasi endpoint submit.'),

        h(3,'Rules'),
        ul(
            li('Submit dilakukan sekali oleh satu mechanic — berlaku untuk semua mechanic yang mengerjakan form tersebut.'),
            li('Pre-condition: semua mandatory fields terisi di device mechanic yang akan submit (validasi client-side).'),
            li('Submit bisa offline — di-queue, dikirim ke server saat koneksi tersedia.'),
            li('Duplicate submit (dua mechanic submit bersamaan): yang pertama tiba di server yang berlaku (first submit wins by server receive time).'),
            li('Post-submit: Task.Status = Complete, form masuk approval workflow (sama seperti Form Submission existing).'),
        ),

        h(3,'Review sebelum submit'),
        p('Mechanic perwakilan dapat mereview form sebelum submit melalui fitur Summary yang sudah ada di Form Submission (reuse existing).'),

        h(2,'Access Control'),
        tbl(
            tr('Siapa','Aksi yang diperbolehkan', hdr=True),
            tr('Semua user dengan akses PM Shutdown workcard','Assign to Me, buka form (view), tap Start, isi form, sync'),
            tr('Mechanic yang sudah assign + tap Start','Isi dan submit form'),
            tr('Supervisor / Foreman','Finish Execution'),
            tr('Mechanic dengan permission PM_Shutdown_Finish_Execution','Finish Execution'),
        ),

        h(2,'Acceptance Criteria'),
        ul(
            li('Sync endpoint menerima batch field updates dan memproses First Write Wins per field.'),
            li('Rejected fields dikembalikan dalam response dengan alasan.'),
            li('Batch idempotent: mengirim batch yang sama dua kali tidak menghasilkan perubahan data.'),
            li('Timestamp collision: field dengan timestamp identik dianggap no-op, tidak error.'),
            li('Auto-sync debounce 3s aktif setelah input. Timer 30s untuk background pull.'),
            li('Conflict notification UX ditangani oleh IAMS30-4371.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 2. IAMS30-4358: Subtask BE — Submit Form endpoint
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 2. Subtask Submit Form BE under IAMS30-4358 ===')
post_subtask('IAMS30-4358',
    'BE: Submit Form endpoint — validate mandatory fields server-side, Task.Status=Complete, approval workflow',
    {'type':'doc','version':1,'content':[
        h(2,'Background'),
        p('Setelah mechanic tap Submit, mobile mengirim request ke server. Server harus: (1) validate semua mandatory fields terisi, (2) update Task.Status=Complete, (3) trigger approval workflow, (4) auto-close open TaskPersonalizedLog sessions (ditangani oleh IAMS30-4343).'),
        h(2,'Endpoint'),
        cb('POST /api/form-submissions/{formSubmissionId}/submit'),
        h(2,'Processing'),
        ul(
            li('[1] Validate: Task.Status bukan Complete atau Approved (tolak jika sudah final).'),
            li('[2] Validate mandatory fields server-side: semua field dengan isMandatory=true di Cosmos harus terisi. Jika ada yang kosong: return 400 dengan list field yang belum terisi.'),
            li('[3] UPDATE Task.Status = Complete, Task.CompletedAt = server timestamp.'),
            li('[4] Trigger approval workflow (sama seperti Form Submission existing).'),
            li('[5] Auto-close open TaskPersonalizedLog sessions: ditangani oleh handler IAMS30-4343 (min(shiftEnd, submitTime)).'),
        ),
        h(2,'Duplicate submit handling'),
        ul(
            li('Jika Task.Status sudah Complete saat request diterima: return 200 (idempotent, bukan error).'),
            li('First submit wins — jika dua mechanic submit bersamaan, yang pertama tiba di server yang mengubah status. Yang kedua mendapat 200 (sudah Complete).'),
        ),
        h(2,'Offline behavior'),
        ul(
            li('Submit bisa dilakukan offline. Mobile queue-kan request.'),
            li('Saat sync: server melakukan final validation. Jika mandatory fields tidak lengkap di server (mechanic lain belum sync), return 400 — mobile menampilkan error.'),
        ),
        h(2,'Acceptance Criteria'),
        ul(
            li('Submit berhasil: Task.Status = Complete, approval workflow triggered.'),
            li('Submit pada Task yang sudah Complete: return 200 idempotent.'),
            li('Submit dengan mandatory fields tidak lengkap: return 400 dengan detail fields yang kurang.'),
            li('Test: normal submit, duplicate submit, mandatory incomplete, offline-then-sync.'),
        ),
    ]}
)
