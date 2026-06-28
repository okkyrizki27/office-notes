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

# Fetch current description
req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4275?fields=description',
    headers=headers)
resp = urllib.request.urlopen(req)
current = json.loads(resp.read())
existing_content = current['fields']['description']['content']

# Append addendum nodes
addendum = [
    h(2, '11. Addendum — Keputusan Desain & Edge Cases Tambahan'),

    h(3, '11.1 FormCode bukan FormId — Design Decision'),
    p('PlanForm menyimpan FormCode (bukan FormId + Version). Alasan: Planner tidak peduli versi spesifik — mereka peduli "form ini". Versi aktif di-resolve saat plan di-SUBMIT oleh consumer.'),
    ul(
        li('Saat Planner pilih form di Choose Form modal: yang disimpan adalah FormCode.'),
        li('Saat plan di-SUBMIT: FormCode di-resolve ke FormId + FormName + Version aktif dari maintenance-strategy (IsActive=1).'),
        li('Jika form mendapat versi baru antara DRAFT dan SUBMIT: snapshot menggunakan versi terbaru — intended behavior.'),
        li('PlanSubmitted event payload menggunakan FormCode, bukan FormId. Consumer yang resolve ke FormId/Version.'),
    ),

    h(3, '11.2 Planner Manual Search di Choose Form'),
    p('Selain melihat form suggestion (Group 1 dan Group 2), Planner juga bisa melakukan pencarian manual untuk menemukan form di luar kedua grup tersebut. Search input tersedia di dalam Choose Form modal.'),
    ul(
        li('Search by form name — case-insensitive, partial match.'),
        li('Result dari search tidak terbagi per grup — semua form yang match ditampilkan.'),
        li('Planner dapat mencentang form dari hasil search dan menggabungkannya dengan form dari suggestion.'),
    ),

    h(3, '11.3 Auto-Save & Crash Recovery'),
    p('Semua input form di-save secara otomatis ke local storage device setiap kali mechanic mengisi field. Jika device crash atau app ditutup paksa, tidak ada data yang hilang — mechanic bisa membuka form kembali dan melanjutkan dari titik terakhir.'),
    ul(
        li('Auto-save terjadi per field — setiap keystroke / perubahan nilai disimpan lokal secara real-time.'),
        li('Dirty fields (belum di-sync ke server) tetap tersimpan lokal hingga berhasil di-sync.'),
        li('Ini berlaku untuk kondisi offline maupun online.'),
    ),

    h(3, '11.4 SiteShift Overnight Shift Logic'),
    p('SiteShift menyimpan StartShift dan EndShift sebagai waktu (TIME, bukan DATETIME). Untuk shift yang melewati tengah malam, penentuan tanggal EndDate menggunakan logika berikut:'),
    cb(
        'if SiteShift.EndShift < SiteShift.StartShift:\n'
        '    // overnight shift (e.g. Night Shift 18:00 - 06:00)\n'
        '    EndDate.date = StartDate.date + 1 day\n'
        'else:\n'
        '    // same-day shift (e.g. Day Shift 06:00 - 18:00)\n'
        '    EndDate.date = StartDate.date\n\n'
        'EndDate.time = SiteShift.EndShift\n\n'
        '// Contoh:\n'
        '// Night Shift: StartShift=18:00, EndShift=06:00\n'
        '// Session dimulai 22 Jun 20:00 (Night Shift)\n'
        '// EndShift (06:00) < StartShift (18:00) -> overnight\n'
        '// EndDate = 23 Jun 06:00'
    ),
    p('Tidak ada kolom IsNextDay di SiteShift — logika ini di-derive di code berdasarkan perbandingan EndShift vs StartShift.'),

    h(3, '11.5 FormSubmission Tidak Punya Kolom Status'),
    p('FormSubmission tidak memiliki kolom Status. Status form execution sepenuhnya direpresentasikan oleh Task.Status:'),
    tbl(
        tr('Task.Status', 'Makna untuk form', hdr=True),
        tr('Open', 'Form belum ada mechanic yang assign atau mulai mengisi'),
        tr('In Progress', 'Ada mechanic yang sudah assign dan mulai mengisi'),
        tr('Complete', 'Form telah di-submit oleh satu mechanic sebagai perwakilan'),
        tr('Approved', 'Form telah melalui approval workflow'),
    ),
    p('Implikasi: untuk menentukan status form di Tab Form mobile, mobile membaca Task.Status — bukan field terpisah di FormSubmission.'),

    h(3, '11.6 WorkOrder Tidak Bisa Di-Cancel Setelah Eksekusi Mulai'),
    p('Jika plan sudah berstatus INPROGRESS (eksekusi sudah dimulai di lapangan), Planner tidak bisa membatalkan plan tersebut. Ini mencegah race condition antara Planner yang mencoba cancel dan mechanic yang sedang mengisi form di lapangan.'),
    ul(
        li('Cancel hanya bisa dilakukan selama plan masih berstatus DRAFT atau SUBMIT.'),
        li('Setelah plan INPROGRESS: tidak ada aksi cancel yang tersedia untuk Planner.'),
        li('Ini adalah behavior existing — tidak ada perubahan di Phase 1.'),
    ),
]

updated_content = existing_content + addendum
data = json.dumps({'fields': {
    'description': {'type': 'doc', 'version': 1, 'content': updated_content}
}}).encode()

req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4275',
    data=data, headers=headers, method='PUT')
resp = urllib.request.urlopen(req)
print('EPIC patched:', resp.status)
