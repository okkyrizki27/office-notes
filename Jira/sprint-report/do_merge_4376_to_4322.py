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

# ── New merged description for IAMS30-4322 ──────────────────────────────────
merged_desc = {
    'type': 'doc', 'version': 1, 'content': [

        h(2, 'Background'),
        p('Ticket ini mencakup dua aksi berurutan yang dilakukan mechanic sebelum bisa mengisi form di PM Shutdown:'),
        ul(
            li('1. Assign to Me — mechanic mendaftarkan diri ke form (membuat TaskPersonalized). Fitur ini sudah ada di Digiman+ untuk task execution; perlu diverifikasi apakah bisa di-reuse atau perlu di-enhance untuk context PM Shutdown Form Package.'),
            li('2. Slide to Start (Mulai) — setelah assign, mechanic membuka form dan slide untuk mulai mengisi. Aksi ini membuat TaskPersonalizedLog session dan menangani auto-close sesi sebelumnya jika shift berganti.'),
            li('3. Finish — mechanic menutup form sementara tanpa submit. Menutup TaskPersonalizedLog session dengan EndDate = actual tap time.'),
        ),
        p('Ketiga aksi ini offline-first dan saling berkaitan erat dalam satu flow, sehingga dikelola dalam satu ticket.'),

        h(2, 'Bagian A — Assign to Me (TaskPersonalized)'),

        h(3, 'Langkah 1: Investigasi existing API (WAJIB sebelum implementasi)'),
        p('Fitur "Assign to Me" / "Assign to" sudah ada di Digiman+. Developer harus investigasi terlebih dahulu:'),
        ul(
            li('Temukan endpoint existing yang menangani pembuatan / upsert TaskPersonalized.'),
            li('Apakah endpoint sudah upsert by TaskId + UserCode (idempotent)?'),
            li('Apakah bisa dipanggil dari Tab Form mobile untuk context PM Shutdown Form Package tanpa perubahan?'),
            li('Apakah ada validasi tambahan yang perlu ditambahkan (Task.Status = Complete/Approved harus ditolak)?'),
        ),

        h(3, 'Langkah 2: Pilih pendekatan berdasarkan investigasi'),
        table(
            table_row('Kondisi', 'Pendekatan', header=True),
            table_row(
                'Existing API sudah handle semua requirement, tidak ada risiko breaking',
                'REUSE — pastikan mobile memanggil endpoint yang benar. Dokumentasikan di PR.'
            ),
            table_row(
                'Existing API mendekati requirement tapi perlu perubahan kecil backward-compatible',
                'ENHANCE — modifikasi endpoint existing. Pastikan test existing tetap hijau.'
            ),
            table_row(
                'Existing API terlalu berbeda atau perubahan akan breaking existing callers',
                'NEW API — buat endpoint baru (misal POST /api/tasks/{taskId}/assign-to-me) yang idempotent.'
            ),
        ),

        h(3, 'Requirement fungsional Assign to Me (apapun pendekatannya)'),
        ul(
            li('Upsert by TaskId + UserCode — idempotent. Assign berkali-kali dari device berbeda tidak menghasilkan duplikasi TaskPersonalized.'),
            li('UserCode dari authenticated JWT — mechanic tidak bisa assign ke user lain.'),
            li('Task.Status = Complete atau Approved → tolak dengan 400.'),
            li('TenantCode isolation dari JWT.'),
            li('Offline: TaskPersonalized dibuat lokal saat offline, di-sync ke server via upsert saat koneksi tersedia.'),
        ),

        h(2, 'Bagian B — Slide to Start / Mulai (TaskPersonalizedLog)'),

        h(3, 'Client-side logic saat tap Mulai'),
        cb(
            'function handleStartTap(taskPersonalizedId, deviceTimestamp, siteCode):\n'
            '  currentShift = getShift(deviceTimestamp, siteCode)  // from local SiteShift cache\n\n'
            '  // 1. Cek: ada open session di shift yang sama?\n'
            '  openSameShift = TaskPersonalizedLog.find(\n'
            '    taskPersonalizedId, ShiftName=currentShift.Name, EndDate=null\n'
            '  )\n'
            '  if openSameShift: return  // skip, langsung masuk form\n\n'
            '  // 2. Auto-close session dari shift lain (jika ada)\n'
            '  openOther = TaskPersonalizedLog.find(taskPersonalizedId, EndDate=null)\n'
            '  if openOther:\n'
            '    prevShift = getShift(openOther.StartDate, siteCode)\n'
            '    openOther.EndDate = calculateShiftEnd(openOther.StartDate, prevShift)\n'
            '    queue UPDATE openOther\n\n'
            '  // 3. Buat session baru\n'
            '  queue INSERT TaskPersonalizedLog(\n'
            '    taskPersonalizedId,\n'
            '    StartDate=deviceTimestamp,\n'
            '    ShiftName=currentShift.Name,\n'
            '    UserFullName=currentUser.fullName,   // snapshot\n'
            '    SiteCode=currentUser.siteCode,       // snapshot\n'
            '    SiteName=currentUser.siteName,       // snapshot\n'
            '    SectionId=currentUser.sectionId,     // snapshot\n'
            '    SectionName=currentUser.sectionName  // snapshot\n'
            '  )\n'
            '  // Semua operasi dikirim dalam satu batch saat sync'
        ),
        p('Catatan: 6 snapshot columns (ShiftName, UserFullName, SiteCode, SiteName, SectionId, SectionName) harus dikirim ke server saat sync — sesuai scope IAMS30-4321 dan IAMS30-4364.'),

        h(2, 'Bagian C — Finish (close session sementara)'),
        cb(
            'function handleFinishTap(taskPersonalizedId, deviceTimestamp):\n'
            '  openSession = TaskPersonalizedLog.find(taskPersonalizedId, EndDate=null)\n'
            '  if not openSession: return  // no-op\n\n'
            '  openSession.EndDate = deviceTimestamp  // actual tap time, bukan shift end\n'
            '  queue UPDATE openSession'
        ),
        p('Berbeda dari auto-close (shift end time): explicit Finish tap menggunakan waktu aktual tap. PRD Skenario 10: mechanic tap Finish pukul 19:00 meski shift berakhir 18:00 → EndDate = 19:00.'),

        h(2, 'Business Rules (gabungan)'),
        ul(
            li('Assign to Me harus dilakukan sebelum Mulai bisa diakses — form card hanya bisa dibuka (view) sebelum assign.'),
            li('Mulai muncul setiap kali mechanic yang sudah assign membuka form (bukan hanya pertama kali).'),
            li('Deduplication TaskPersonalizedLog: max 1 open session per mechanic per shift (by TaskPersonalizedId + ShiftName where EndDate IS NULL).'),
            li('Finish hanya menutup session tanpa submit form — mechanic bisa Mulai lagi di shift yang sama atau berikutnya.'),
            li('Semua operasi fully offline — di-queue dalam satu batch sync.'),
        ),

        h(2, 'Acceptance Criteria'),
        ul(
            li('Assign to Me: hasil investigasi existing API terdokumentasi di PR. Pendekatan dipilih (reuse/enhance/new) dengan alasan.'),
            li('Assign to Me idempotent: memanggil dua kali tidak duplikasi TaskPersonalized.'),
            li('Assign ke Task yang sudah Complete/Approved dikembalikan 400.'),
            li('Slide to Start: membuat TaskPersonalizedLog session baru dengan 6 snapshot fields terisi.'),
            li('Slide to Start di shift yang sama: no-op (tidak buat session baru).'),
            li('Slide to Start di shift berbeda: auto-close session lama (EndDate = shift end time), buat session baru.'),
            li('Finish tap: set EndDate = actual timestamp pada open session. No-op jika tidak ada open session.'),
            li('Semua aksi bekerja offline — di-queue dan sync ke server saat koneksi tersedia.'),
            li('Tidak ada regression pada existing Assign to Me / task assignment flow yang sudah berjalan.'),
        ),
    ]
}

# Update IAMS30-4322 title + description
payload = json.dumps({
    'fields': {
        'summary': '[MOBILE] Form Package — Assign to Me, Slide to Start (Mulai), dan Finish: TaskPersonalized & TaskPersonalizedLog Management',
        'description': merged_desc,
    }
}).encode()

req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4322',
    data=payload, headers=headers, method='PUT'
)
resp = urllib.request.urlopen(req)
print('IAMS30-4322 updated:', resp.status)

# Add subtask for the BE Assign to Me investigation
subtask_desc = {
    'type': 'doc', 'version': 1, 'content': [
        h(2, 'Tujuan'),
        p('Investigasi dan implementasi backend untuk Assign to Me di context PM Shutdown Form Package. Fitur Assign to Me sudah ada di Digiman+ — jangan langsung buat API baru sebelum investigasi.'),
        h(2, 'Langkah'),
        ul(
            li('1. Cari endpoint existing yang menangani upsert TaskPersonalized (Assign to Me / Assign to).'),
            li('2. Evaluasi: apakah bisa dipakai as-is, perlu di-enhance, atau harus buat baru (jika risiko breaking).'),
            li('3. Implementasi sesuai pendekatan yang dipilih.'),
            li('4. Pastikan: upsert by TaskId+UserCode (idempotent), tolak Task.Status Complete/Approved (400), TenantCode isolation.'),
            li('5. Dokumentasikan keputusan di PR description.'),
        ),
        h(2, 'Acceptance Criteria'),
        ul(
            li('Endpoint yang digunakan terdokumentasi di PR (reuse / enhance / new — beserta alasan).'),
            li('Assign to Me idempotent — tidak duplikasi TaskPersonalized.'),
            li('Task Complete/Approved dikembalikan 400.'),
            li('Tidak ada regression pada existing flow.'),
        ),
    ]
}

subtask_payload = json.dumps({
    'fields': {
        'project': {'id': '10173'},
        'parent': {'key': 'IAMS30-4322'},
        'summary': 'BE: Investigasi + implementasi Assign to Me untuk PM Shutdown Form Package (reuse/enhance/new TaskPersonalized upsert)',
        'description': subtask_desc,
        'issuetype': {'id': '10262'},
    }
}).encode()

req2 = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue',
    data=subtask_payload, headers=headers, method='POST'
)
resp2 = urllib.request.urlopen(req2)
result2 = json.loads(resp2.read())
print('Subtask created:', result2.get('key'))

# Comment on IAMS30-4376 to note it's been merged
comment_payload = json.dumps({
    'body': {
        'type': 'doc', 'version': 1, 'content': [
            p('Konten ticket ini telah di-merge ke IAMS30-4322 ([MOBILE] Form Package — Assign to Me, Slide to Start, dan Finish). Ticket ini akan dihapus oleh PO. Tidak perlu ada aksi lebih lanjut di sini.')
        ]
    }
}).encode()
req3 = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4376/comment',
    data=comment_payload, headers=headers, method='POST'
)
resp3 = urllib.request.urlopen(req3)
print('Comment on IAMS30-4376:', resp3.status)
