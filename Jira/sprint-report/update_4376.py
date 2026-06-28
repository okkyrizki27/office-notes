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
    ct = 'tableHeader' if header else 'tableCell'
    return {'type':'tableRow','content':[{'type':ct,'attrs':{},'content':[{'type':'paragraph','content':[{'type':'text','text':str(c)}]}]} for c in cells]}
def table(*rows): return {'type':'table','attrs':{'isNumberColumnEnabled':False,'layout':'default'},'content':list(rows)}

desc = {
    'type': 'doc', 'version': 1, 'content': [
        h(2, 'Background'),
        p('Saat mechanic tap "Assign to Me" di 3-dot menu form card (Tab Form workcard mobile), sistem perlu membuat record TaskPersonalized yang menghubungkan mechanic ke Task tersebut. Ini adalah prerequisite sebelum mechanic bisa buka dan isi form.'),
        p('Fitur "Assign to Me" / "Assign to" sudah ADA di Digiman+ untuk task execution yang existing. Kemungkinan besar sudah ada endpoint yang menangani assignment TaskPersonalized. Ticket ini bukan untuk langsung buat API baru, melainkan untuk memastikan existing API bisa digunakan untuk use case PM Shutdown Form Package, atau di-enhance jika perlu.'),
        h(2, 'Langkah 1 — Investigasi existing API (WAJIB dilakukan terlebih dahulu)'),
        p('Sebelum membuat atau memodifikasi apapun, developer harus:'),
        ul(
            li('Cari endpoint existing yang menangani "Assign to Me" atau pembuatan TaskPersonalized (bisa di Services.iAMS.MaintenanceExec atau PM Shutdown controller).'),
            li('Periksa: apakah endpoint tersebut sudah melakukan upsert by TaskId + UserCode (idempotent)?'),
            li('Periksa: apakah endpoint sudah bisa dipanggil dari Tab Form mobile untuk context PM Shutdown form package?'),
            li('Periksa: apakah ada validasi yang perlu ditambahkan (contoh: Task.Status = Complete/Approved harus ditolak)?'),
            li('Periksa: apakah ada field baru yang perlu diset saat assign (StartedAt sudah bukan di sini — StartedAt di-set saat tap Mulai, bukan saat Assign to Me).'),
        ),
        h(2, 'Langkah 2 — Pilih pendekatan berdasarkan investigasi'),
        table(
            table_row('Kondisi hasil investigasi', 'Pendekatan', header=True),
            table_row(
                'Existing API sudah handle semua requirement (upsert, validasi, response) dan tidak ada risiko breaking',
                'REUSE: cukup pastikan mobile memanggil endpoint yang benar. Tidak perlu perubahan BE. Update dokumentasi/PR notes.'
            ),
            table_row(
                'Existing API mendekati requirement tapi perlu perubahan kecil (tambah validasi, tambah field response, dll)',
                'ENHANCE: modifikasi endpoint existing dengan perubahan backward-compatible. Pastikan ada test untuk behavior baru tanpa merusak yang lama.'
            ),
            table_row(
                'Existing API terlalu berbeda atau perubahan akan breaking existing callers',
                'NEW API: buat endpoint baru (contoh: POST /api/tasks/{taskId}/assign-to-me) yang idempotent dan terpisah dari existing flow.'
            ),
        ),
        h(2, 'Requirement fungsional (apapun pendekatannya)'),
        p('Endpoint yang digunakan harus memenuhi:'),
        ul(
            li('Upsert by TaskId + UserCode — idempotent. Tap Assign to Me berkali-kali dari device berbeda tidak menghasilkan duplikasi TaskPersonalized.'),
            li('UserCode diambil dari authenticated JWT — mechanic tidak bisa assign ke user lain melalui action ini.'),
            li('Jika Task.Status = Complete atau Approved: kembalikan 400 — tidak bisa assign ke form yang sudah selesai.'),
            li('TenantCode isolation dari JWT.'),
            li('Offline-first: mobile membuat TaskPersonalized record lokal saat offline, endpoint dipanggil saat sync. Upsert memastikan tidak ada duplikasi.'),
        ),
        h(2, 'Response yang dibutuhkan mobile'),
        cb(
            '{\n'
            '  "taskPersonalizedId": "guid",\n'
            '  "taskId": "guid",\n'
            '  "userCode": "string",\n'
            '  "assignedAt": "datetime"\n'
            '}'
        ),
        h(2, 'Acceptance Criteria'),
        ul(
            li('Investigasi existing API terdokumentasi di PR description: endpoint yang ditemukan, pendekatan yang dipilih, alasannya.'),
            li('Mechanic bisa assign diri ke form (TaskPersonalized dibuat/di-upsert) melalui Tab Form PM Shutdown.'),
            li('Assign to Me idempotent: memanggil dua kali tidak menghasilkan dua record.'),
            li('Assign ke Task.Status Complete/Approved dikembalikan 400.'),
            li('Offline: assignment yang dibuat lokal bisa di-sync ke server tanpa duplikasi.'),
            li('Tidak ada regression pada existing Assign to Me / task assignment flow yang sudah berjalan.'),
        ),
    ]
}

payload = json.dumps({
    'fields': {
        'summary': '[BE] Form Package — Assign to Me: Investigate existing API, reuse/enhance/new untuk upsert TaskPersonalized',
        'description': desc,
    }
}).encode()

req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4376',
    data=payload, headers=headers, method='PUT'
)
resp = urllib.request.urlopen(req)
print('IAMS30-4376 updated:', resp.status)
