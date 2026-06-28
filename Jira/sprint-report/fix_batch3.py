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
# 8. IAMS30-4377 (PlanForm subtask): form lock after SUBMIT + empty-submit allowed
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 8. IAMS30-4377 — form lock + empty submit ===')
existing = get_desc('IAMS30-4377')
put('IAMS30-4377', {
    'description': {'type':'doc','version':1,'content': existing + [
        h(2,'Business Rules Tambahan'),

        h(3,'Submit tanpa form assignment dibolehkan'),
        p('Plan bisa di-SUBMIT meski tidak ada form yang di-assign (PlanForm kosong atau semua IsDeleted=1). Dalam kondisi ini:'),
        ul(
            li('Tab Form di mobile menampilkan empty state — tidak ada form card.'),
            li('Finish Execution tidak diblokir oleh form gate (packageSyncStatus = "none").'),
            li('Tidak ada error, tidak ada warning — ini adalah flow yang valid.'),
        ),

        h(3,'Form assignment terkunci setelah SUBMIT'),
        p('Begitu plan berpindah ke status SUBMIT (atau lebih tinggi), SEMUA write operation ke PlanForm diblokir:'),
        tbl(
            tr('Operation','DRAFT','SUBMIT / INPROGRESS / FINISH / CANCEL', hdr=True),
            tr('Tambah form (POST)','Diperbolehkan','DITOLAK — return 400'),
            tr('Update IsMandatory (PUT)','Diperbolehkan','DITOLAK — return 400'),
            tr('Hapus form (DELETE soft)','Diperbolehkan','DITOLAK — return 400'),
            tr('Baca daftar form (GET)','Diperbolehkan','Diperbolehkan (read-only)'),
        ),
        p('Error message saat write di-block: "Form package cannot be modified after plan is submitted." (HTTP 400)'),
        p('Ini berlaku untuk SEMUA pihak termasuk Planner sendiri — tidak ada override.'),

        h(2,'Acceptance Criteria (tambahan)'),
        ul(
            li('Submit plan tanpa form assignment: berhasil, packageSyncStatus = "none", Finish Execution tidak terblokir.'),
            li('Write operation pada plan SUBMIT: return 400 dengan pesan yang tepat.'),
            li('Write operation pada plan DRAFT: berhasil.'),
            li('Read operation pada plan SUBMIT: berhasil (read-only tidak terblokir).'),
            li('Test: empty submit flow, lock enforcement pada tiap endpoint (POST/PUT/DELETE).'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 9. IAMS30-4274: Assign+Start prerequisite rule + read-only
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 9. IAMS30-4274 — Assign+Start prerequisite ===')
existing = get_desc('IAMS30-4274')
put('IAMS30-4274', {
    'description': {'type':'doc','version':1,'content': existing + [
        h(2,'Prerequisite untuk Mengisi Form: Assign to Me DAN Tap Start'),
        p('Form card SELALU bisa dibuka (tap untuk view) oleh semua user yang punya akses PM Shutdown workcard. Namun untuk bisa mengisi (edit) form, ada dua prerequisite yang harus dipenuhi:'),
        tbl(
            tr('Kondisi','Yang Bisa Dilakukan', hdr=True),
            tr('Mechanic belum Assign to Me','Buka form untuk VIEW saja. Form read-only. Tombol Start tidak muncul.'),
            tr('Sudah Assign to Me, belum tap Start','Buka form untuk VIEW. Tombol Start muncul. Form masih read-only sampai Start di-tap.'),
            tr('Sudah Assign to Me DAN sudah tap Start','Buka form dan ISI form. Tombol Start muncul setiap kali membuka form.'),
            tr('Form sudah di-Submit (Complete)','Buka form untuk VIEW saja. Form read-only permanen. Tombol Start tidak muncul.'),
        ),
        h(3,'Behavior tap form card per kondisi'),
        ul(
            li('Belum Assign to Me: tap form card -> buka form dalam read-only mode. Tombol Start tidak ada. Mechanic bisa melihat template form tapi tidak bisa mengetik.'),
            li('Sudah Assign to Me, belum Start: tap form card -> buka form dalam read-only mode. Tombol Start muncul di bawah. Tap Start -> form menjadi editable.'),
            li('Sudah Start: tap form card -> buka form langsung editable. Tombol Start tetap muncul (untuk tracking sesi saat dibuka kembali).'),
            li('Form Complete: tap form card -> buka form dalam read-only mode permanent. Badge "Complete" pada form card.'),
        ),
        h(3,'Mengapa dua langkah (Assign + Start)?'),
        ul(
            li('Assign to Me: mencatat mechanic sebagai pengerjaan form (membuat TaskPersonalized). Sistem tahu siapa yang bertanggung jawab.'),
            li('Tap Start: sesi kerja dimulai dan dicatat (membuat TaskPersonalizedLog). Digunakan untuk activity tracking dan laporan aktivitas.'),
        ),
        h(2,'Acceptance Criteria (tambahan)'),
        ul(
            li('User yang belum Assign to Me: form terbuka read-only, tidak ada tombol Start, tidak bisa mengetik.'),
            li('User yang sudah Assign, belum Start: form terbuka read-only, tombol Start muncul, form jadi editable setelah Start.'),
            li('Form Complete: selalu read-only untuk semua user, tombol Start tidak ada.'),
            li('Widget test: read-only state, Start button visibility, editable state setelah Start.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 10. IAMS30-4340: 6 snapshot fields dalam sync payload
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 10. IAMS30-4340 — 6 snapshot fields in sync payload ===')
existing = get_desc('IAMS30-4340')
put('IAMS30-4340', {
    'description': {'type':'doc','version':1,'content': existing + [
        h(2,'6 Snapshot Fields — Wajib Disertakan dalam Sync Payload'),
        p('Saat client mengirim TaskPersonalizedLog session ke server (via IAMS30-4359), payload HARUS menyertakan 6 snapshot fields yang diambil dari data lokal user pada saat session dibuat (bukan real-time dari server):'),
        tbl(
            tr('Field','Sumber data di mobile','Nullable', hdr=True),
            tr('shiftName','Hasil getShift() dari SiteShift local cache','No — selalu ada (dari cache atau default)'),
            tr('userFullName','Local user profile (dari login session)','No'),
            tr('siteCode','Local user profile','No'),
            tr('siteName','Local user profile','Yes'),
            tr('sectionId','Local user profile','Yes'),
            tr('sectionName','Local user profile','Yes — bisa NULL jika tidak ada di profil'),
        ),
        p('Snapshot diambil SAAT SESSION DIBUAT (saat tap Mulai), bukan saat sync. Tujuannya: jika mechanic pindah site/section setelah session dibuat, data historis tetap mencerminkan posisi saat aktivitas terjadi.'),
        h(3,'Integrasi dengan handleStartTap'),
        cb(
            'function handleStartTap(taskPersonalizedId, deviceTimestamp, siteCode):\n'
            '  currentShift = getShift(deviceTimestamp, siteCode)  // dari SiteShift cache\n'
            '  currentUser = getLocalUserProfile()                   // dari login session\n\n'
            '  // ... dedup + auto-close logic ...\n\n'
            '  // Buat session baru dengan snapshot:\n'
            '  queue INSERT TaskPersonalizedLog(\n'
            '    taskPersonalizedId = taskPersonalizedId,\n'
            '    startDate     = deviceTimestamp,\n'
            '    endDate       = null,\n'
            '    shiftName     = currentShift.Name,\n'
            '    userFullName  = currentUser.fullName,\n'
            '    siteCode      = currentUser.siteCode,\n'
            '    siteName      = currentUser.siteName,\n'
            '    sectionId     = currentUser.sectionId,\n'
            '    sectionName   = currentUser.sectionName   // nullable\n'
            '  )'
        ),
        h(2,'Acceptance Criteria (tambahan)'),
        ul(
            li('handleStartTap mengambil 6 snapshot fields dari local user profile dan SiteShift cache pada saat session dibuat.'),
            li('Semua 6 fields disertakan dalam payload saat sync ke server.'),
            li('Snapshot tidak diupdate saat session di-close (auto-close atau Finish tap) — EndDate saja yang berubah.'),
            li('Unit test: session payload mengandung 6 fields dengan nilai dari local profile; sectionName nullable ditest dengan nilai NULL.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 11. IAMS30-4380: Mark duplicate of 4381
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 11. IAMS30-4380 — mark duplicate ===')
post_link('IAMS30-4380', 'IAMS30-4381', 10002)  # Duplicate link type
post_comment('IAMS30-4380',
    'DUPLIKAT dari IAMS30-4381. Ticket ini terbuat dua kali karena bug pada script pembuatan subtask (UnicodeEncodeError menyebabkan print statement gagal, namun API call sudah berhasil membuat ticket). '
    'Silakan close/resolve ticket ini sebagai Duplicate. Gunakan IAMS30-4381 sebagai referensi yang valid.'
)
put('IAMS30-4380', {
    'summary': '[DUPLICATE of IAMS30-4381] Relay job: poll dbo.Outbox -> publish ke Azure Service Bus -> mark Published',
})

# ─────────────────────────────────────────────────────────────────────────────
# 12. IAMS30-4266: Tambah empty-package rule di description
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 12. IAMS30-4266 — empty-package rule ===')
existing = get_desc('IAMS30-4266')
put('IAMS30-4266', {
    'description': {'type':'doc','version':1,'content': existing + [
        h(2,'Rule: Submit Tanpa Form Package Dibolehkan'),
        p('Plan bisa di-SUBMIT meski tidak ada form yang di-assign. Dalam kondisi ini:'),
        ul(
            li('PlanForm tidak ada (atau semua IsDeleted=1): PlanSubmitted event tetap di-publish, tetapi array PlanForms kosong [].'),
            li('Consumer di maintenance-execution menerima event dengan PlanForms kosong: WorkOrder tetap dibuat, tidak ada Task/FormSubmission/Cosmos yang dibuat.'),
            li('packageSyncStatus = "none" (bukan "pending") — karena PlanForm count = 0, bukan karena consumer belum jalan.'),
            li('Tab Form di mobile: empty state biasa. Finish Execution tidak terblokir oleh form gate.'),
        ),
        p('Ini adalah flow yang valid dan tidak boleh dianggap error di sisi manapun (dplan, Service Bus, consumer, mobile).'),
        h(3,'Acceptance Criteria (tambahan)'),
        ul(
            li('Submit plan tanpa form: PlanSubmitted event published dengan PlanForms=[].'),
            li('Consumer memproses event dengan PlanForms=[]: WorkOrder dibuat, tidak ada Task/FormSubmission/Cosmos.'),
            li('packageSyncStatus = "none" untuk plan tanpa form assignment.'),
            li('Test: submit empty plan end-to-end -> WorkOrder terbuat, tidak ada Task, packageSyncStatus=none.'),
        ),
    ]}
})

print('\nBatch 3 done.')
