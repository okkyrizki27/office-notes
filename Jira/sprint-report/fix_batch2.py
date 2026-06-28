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
        'project': {'id': '10173'}, 'parent': {'key': parent},
        'summary': summary, 'description': desc, 'issuetype': {'id': '10262'},
    }}).encode()
    req = urllib.request.Request('https://bukittechnology.atlassian.net/rest/api/3/issue',
        data=data, headers=headers, method='POST')
    try:
        resp = urllib.request.urlopen(req)
        r = json.loads(resp.read())
        print(f'  SUBTASK {r["key"]}: {summary[:65]}')
    except urllib.error.HTTPError as e:
        print(f'  ERROR: {e.code}', e.read().decode()[:200])

def get_desc(key):
    req = urllib.request.Request(
        f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}?fields=description',
        headers=headers)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())['fields'].get('description', {}).get('content', [])

def post_comment(key, text):
    data = json.dumps({'body':{'type':'doc','version':1,'content':[p(text)]}}).encode()
    req = urllib.request.Request(
        f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}/comment',
        data=data, headers=headers, method='POST')
    resp = urllib.request.urlopen(req)
    print(f'COMMENT {key}: {resp.status}')

def post_link(inward, outward, link_id):
    data = json.dumps({'type':{'id':str(link_id)},'inwardIssue':{'key':inward},'outwardIssue':{'key':outward}}).encode()
    req = urllib.request.Request('https://bukittechnology.atlassian.net/rest/api/3/issueLink',
        data=data, headers=headers, method='POST')
    try:
        resp = urllib.request.urlopen(req)
        print(f'LINK {inward} dup {outward}: {resp.status}')
    except urllib.error.HTTPError as e:
        print(f'  LINK ERROR: {e.code}', e.read().decode()[:150])

# ─────────────────────────────────────────────────────────────────────────────
# 3. IAMS30-4274: Subtask MOBILE — Submit Form UI
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 3. Subtask Submit Form MOBILE under IAMS30-4274 ===')
post_subtask('IAMS30-4274',
    'MOBILE: Submit Form UI — tap Submit, Summary review, confirm dialog, offline queue',
    {'type':'doc','version':1,'content':[
        h(2,'Background'),
        p('Setelah mechanic selesai mengisi form, salah satu mechanic (perwakilan) melakukan Submit. Submit mengunci form secara final. Sebelum submit, mechanic bisa review via Summary. Seluruh flow ini harus bekerja offline.'),
        h(2,'UI Flow'),
        ul(
            li('[1] Mechanic tap tombol "Submit" di form detail screen (hanya muncul jika mechanic sudah assign dan sudah tap Start).'),
            li('[2] Sistem cek client-side: semua mandatory fields terisi di local device? Jika belum: tampilkan daftar fields yang belum terisi, tombol Submit disabled.'),
            li('[3] Sebelum submit final: tampilkan Summary screen (reuse existing Form Submission summary component) untuk review seluruh isian form.'),
            li('[4] Mechanic tap "Confirm Submit" di Summary screen.'),
            li('[5] Request Submit dikirim ke server (POST /api/form-submissions/{id}/submit). Jika offline: di-queue, dikirim saat koneksi tersedia.'),
            li('[6] Setelah submit berhasil: form card di Tab Form menampilkan status "Complete", form terbuka dalam read-only mode.'),
        ),
        h(2,'State management'),
        tbl(
            tr('Kondisi','Tombol Submit', hdr=True),
            tr('Mechanic belum assign atau belum tap Start','Tidak muncul'),
            tr('Ada mandatory field yang belum terisi (per local data)','Muncul tapi disabled, dengan hint'),
            tr('Semua mandatory field terisi','Enabled'),
            tr('Form sudah di-Submit (Complete)','Tidak muncul, form read-only'),
        ),
        h(2,'Duplicate submit handling di mobile'),
        p('Jika dua mechanic sama-sama tap Submit saat offline: keduanya meng-queue request. Yang pertama tiba di server yang berlaku. Yang kedua akan mendapat response 200 (idempotent) — tidak ada error ditampilkan ke user.'),
        h(2,'Acceptance Criteria'),
        ul(
            li('Tombol Submit muncul hanya untuk mechanic yang sudah assign dan tap Start.'),
            li('Tombol Submit disabled jika ada mandatory field kosong (berdasarkan local data), dengan hint fields yang kurang.'),
            li('Summary screen tampil sebelum confirm submit — reuse existing component.'),
            li('Submit bekerja offline: di-queue dan dikirim saat koneksi tersedia.'),
            li('Setelah submit: form card status = Complete, form read-only.'),
            li('Widget test: disabled state, enabled state, offline queue behavior.'),
        ),
    ]}
)

# ─────────────────────────────────────────────────────────────────────────────
# 4. IAMS30-4359: Full description
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 4. IAMS30-4359 — Full description ===')
put('IAMS30-4359', {
    'summary': '[BE] Form Package — API Insert TaskPersonalizedLog Session (with 6 Snapshot Fields)',
    'description': {'type':'doc','version':1,'content':[
        h(2,'Background'),
        p('Setiap kali mechanic tap "Mulai" (Start) pada form di PM Shutdown, mobile client membuat TaskPersonalizedLog session record secara lokal dan meng-queue-nya untuk sync ke server. API ini adalah endpoint yang menerima data session tersebut dari mobile.'),
        p('Prinsip penting: server hanya menerima dan menyimpan data — tidak ada logic auto-close atau deteksi shift di server. Semua logic tersebut dijalankan di client (lihat IAMS30-4322 dan IAMS30-4340).'),

        h(2,'Endpoint'),
        cb(
            'POST /api/task-personalized-logs\n\n'
            'Body (per session):\n'
            '{\n'
            '  "taskPersonalizedId": "guid",\n'
            '  "startDate": "datetime",       // device clock saat tap Mulai\n'
            '  "endDate": "datetime|null",     // null jika session masih open, atau sudah di-close client-side\n'
            '  "shiftName": "string",          // e.g. "Day Shift" — snapshot saat session dibuat\n'
            '  "userFullName": "string",       // snapshot dari UserEmploymentProfile\n'
            '  "siteCode": "string",           // snapshot\n'
            '  "siteName": "string",           // snapshot\n'
            '  "sectionId": "string",          // snapshot\n'
            '  "sectionName": "string|null"    // snapshot, nullable\n'
            '}'
        ),
        p('Catatan: mobile mengirim sessions dalam batch sync yang sama dengan operasi lain (Assign to Me, field updates). Tidak ada sync terpisah per operasi.'),

        h(2,'Server-side behavior'),
        ul(
            li('Server INSERT record ke TaskPersonalizedLog dengan semua field yang dikirim.'),
            li('Jika session dengan Id yang sama sudah ada (retry): UPDATE EndDate dan fields yang berubah (upsert by Id).'),
            li('6 snapshot fields (ShiftName, UserFullName, SiteCode, SiteName, SectionId, SectionName) disimpan as-is dari request — server tidak lookup ke UserEmploymentProfile.'),
            li('Semua 6 snapshot fields nullable: jika tidak dikirim, simpan NULL (backward compatibility untuk mobile build lama).'),
            li('startDate dan endDate menggunakan device clock — server tidak overwrite dengan server timestamp.'),
        ),

        h(2,'Activity records setelah form Complete'),
        p('TaskPersonalizedLog dari mechanic yang masih offline saat form di-submit TETAP DITERIMA saat sync, selama StartDate < submitted time. Activity records adalah historical log yang tidak mempengaruhi form content dan tidak pernah ditolak.'),
        cb(
            '// Rule penerimaan:\n'
            'IF record.startDate < task.completedAt:\n'
            '  ACCEPT  // historical, simpan apa adanya\n'
            'ELSE:\n'
            '  REJECT  // startDate setelah submit time, tidak masuk akal'
        ),

        h(2,'Relationship dengan tickets lain'),
        ul(
            li('IAMS30-4321 + subtask IAMS30-4338: DDL 6 kolom baru di TaskPersonalizedLog.'),
            li('IAMS30-4364: Update request body untuk accept 6 snapshot fields.'),
            li('IAMS30-4322 + IAMS30-4340: Client-side logic yang menghasilkan data yang dikirim ke endpoint ini.'),
            li('IAMS30-4323: Auto-close via Submit — juga menggunakan endpoint ini untuk update EndDate sessions yang masih open.'),
        ),

        h(2,'Acceptance Criteria'),
        ul(
            li('API menerima session data dan menyimpan ke TaskPersonalizedLog dengan benar.'),
            li('6 snapshot fields tersimpan as-is dari request (tidak di-lookup server-side).'),
            li('Semua 6 fields nullable — request tanpa fields tidak error (backward compat).'),
            li('Session dengan StartDate < completedAt diterima bahkan setelah Task.Status = Complete.'),
            li('Upsert by session Id: idempotent, retry aman.'),
            li('Test: insert normal, insert after Complete (accepted), insert after Complete (rejected — startDate > completedAt), retry idempotency.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 5. IAMS30-4265: Update description — suggestion grouping + default IsMandatory
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 5. IAMS30-4265 — suggestion grouping ===')
existing = get_desc('IAMS30-4265')
put('IAMS30-4265', {
    'description': {'type':'doc','version':1,'content': existing + [
        h(2,'Form Suggestion Grouping (wajib diimplementasi)'),
        p('Response harus mengembalikan form dalam DUA grup terurut — Grup 1 lebih relevan, ditampilkan lebih atas di FE:'),
        tbl(
            tr('Grup','Filter','Deskripsi', hdr=True),
            tr('Grup 1','Equipment Model + Service Type match','Form yang di-mapping ke kombinasi model DAN service type yang bersangkutan. Paling relevan.'),
            tr('Grup 2','Equipment Model only','Form yang di-mapping ke model saja, tanpa filter service type.'),
        ),
        p('Planner juga bisa melakukan pencarian manual untuk menemukan form di luar kedua grup tersebut.'),
        h(2,'Default IsMandatory untuk Service Sheet'),
        p('Jika response mengandung form bertipe Service Sheet (mapping ke Equipment Model + Service Hour yang sesuai), server harus menyertakan flag isSuggestedMandatory=true sebagai hint ke FE. FE menampilkan toggle IsMandatory dalam posisi ON sebagai default suggestion.'),
        p('Authority IsMandatory sepenuhnya ada di Planner — flag ini hanya suggestion awal. Planner bebas mengubah nilai IsMandatory untuk semua form termasuk service sheet.'),
        h(3,'Contoh response structure'),
        cb(
            '[\n'
            '  {\n'
            '    "group": 1,\n'
            '    "formCode": "SS-HD785-250",\n'
            '    "formName": "Service Sheet HD785 250H",\n'
            '    "isSuggestedMandatory": true   // hint: service sheet, default mandatory\n'
            '  },\n'
            '  {\n'
            '    "group": 1,\n'
            '    "formCode": "TYRE-HD785",\n'
            '    "formName": "Tyre R&I Form HD785",\n'
            '    "isSuggestedMandatory": false\n'
            '  },\n'
            '  {\n'
            '    "group": 2,\n'
            '    "formCode": "WELDING-GEN",\n'
            '    "formName": "Welding Form",\n'
            '    "isSuggestedMandatory": false\n'
            '  }\n'
            ']'
        ),
        h(3,'Acceptance Criteria (tambahan)'),
        ul(
            li('Response mengembalikan field "group" dengan nilai 1 atau 2 per form.'),
            li('Grup 1 selalu mendahului Grup 2 dalam response array.'),
            li('Service sheet yang matching Equipment Model + Service Type diberi isSuggestedMandatory=true.'),
            li('Form di luar kedua grup tidak dikembalikan (Planner cari via manual search).'),
            li('Test: serviceType provided -> Grup 1 dan 2 populated; serviceType null -> semua masuk Grup 2; model tidak match -> empty result.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 6. IAMS30-4269: Finish Execution offline + access control + DueDate
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 6. IAMS30-4269 — Finish Execution offline + access control ===')
existing = get_desc('IAMS30-4269')
put('IAMS30-4269', {
    'description': {'type':'doc','version':1,'content': existing + [
        h(2,'Finish Execution — Offline Behavior'),
        p('Finish Execution bisa dilakukan offline. Validasi dilakukan di sisi device (client-side) menggunakan data lokal:'),
        ul(
            li('Cek lokal: backlog execution selesai? + semua mandatory form Task.Status = Complete?'),
            li('Jika kondisi terpenuhi: aksi Finish Execution dibolehkan offline.'),
            li('Aksi di-queue dan dikirim ke server saat koneksi tersedia.'),
            li('Server melakukan final validation saat sync. Jika tidak sesuai: server reject + notify mobile.'),
        ),
        p('Prinsip: offline-first berlaku penuh. Client-side check adalah gate — user tidak perlu online selama data lokal memenuhi syarat.'),

        h(2,'packageSyncStatus = pending memblokir Finish Execution'),
        p('Jika packageSyncStatus = "pending" (ada PlanForm tapi Task belum terbuat): Finish Execution di-block dengan pesan: "Form package is not yet available. Please try again later or contact your admin."'),

        h(2,'Access Control'),
        tbl(
            tr('Siapa','Finish Execution', hdr=True),
            tr('Supervisor / Foreman','Selalu bisa'),
            tr('Mechanic','Bisa jika memiliki permission PM_Shutdown_Finish_Execution yang dikonfigurasi di level akses user'),
        ),
        p('Permission Finish Execution untuk Mechanic dikonfigurasi di level akses user — bukan per workcard atau per site. Mengikuti sistem permission management yang sudah ada di Digiman+.'),

        h(2,'DueDate WorkOrder'),
        p('DueDate WorkOrder bersifat informasi saja — tidak ada enforcement atau blocking otomatis jika DueDate terlewati. Mechanic dan Supervisor tetap bisa melanjutkan dan menyelesaikan eksekusi setelah DueDate.'),

        h(2,'Acceptance Criteria (tambahan)'),
        ul(
            li('Finish Execution dapat dilakukan offline jika validasi client-side terpenuhi, dan di-queue ke server.'),
            li('packageSyncStatus = pending: Finish Execution di-block di server dengan error message yang sesuai.'),
            li('Mechanic tanpa permission PM_Shutdown_Finish_Execution mendapat 403 dari server.'),
            li('DueDate lewat: tidak memblokir Finish Execution — informasi saja.'),
            li('Test: offline finish (success), packageSyncStatus pending (blocked), mechanic without permission (403), DueDate overdue (no block).'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 7. IAMS30-4323: Activity records diterima setelah form Complete
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 7. IAMS30-4323 — activity records setelah Complete ===')
existing = get_desc('IAMS30-4323')
put('IAMS30-4323', {
    'description': {'type':'doc','version':1,'content': existing + [
        h(2,'Penting: Activity Records Setelah Form Complete'),
        p('TaskPersonalizedLog records dari mechanic yang masih offline saat form di-submit TETAP DITERIMA saat sync, bahkan setelah Task.Status = Complete. Ini berbeda dari form content (field values) yang ditolak setelah Complete.'),
        tbl(
            tr('Jenis Data','Jika sync setelah form Complete','Alasan', hdr=True),
            tr('Form content (field values)','DITOLAK — form sudah final, tidak bisa diubah','Form final tidak boleh dimodifikasi'),
            tr('Activity records (TaskPersonalizedLog)','DITERIMA selama StartDate < submitTime','Historical log, tidak mempengaruhi form content'),
        ),
        p('Rule penerimaan activity record setelah Complete: StartDate < Task.CompletedAt. Record dengan StartDate >= CompletedAt tidak masuk akal secara kronologis dan ditolak.'),
        h(2,'Implikasi untuk auto-close handler'),
        p('Auto-close handler ini (EndDate = min(shiftEnd, submitTime)) hanya berjalan pada saat submit — bukan saat sync activity records pasca-Complete. Server harus tetap menerima UPDATE EndDate pada session yang sudah ada, bahkan jika Task sudah Complete, selama data tersebut adalah penutupan sesi yang valid secara kronologis.'),
        h(2,'Acceptance Criteria (tambahan)'),
        ul(
            li('TaskPersonalizedLog INSERT dengan StartDate < Task.CompletedAt diterima meski Task sudah Complete.'),
            li('TaskPersonalizedLog INSERT dengan StartDate >= Task.CompletedAt ditolak dengan 400.'),
            li('UPDATE EndDate pada session yang ada diterima meski Task sudah Complete (untuk mechanic yang sync terlambat).'),
            li('Test: late sync activity record (accepted), activity record after Complete with valid StartDate (accepted), invalid StartDate (rejected).'),
        ),
    ]}
})

print('\nBatch 2 done.')
