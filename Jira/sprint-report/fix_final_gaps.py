# -*- coding: utf-8 -*-
import json, os, urllib.request, base64, sys, time
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
    time.sleep(0.5)

def get_desc(key):
    req = urllib.request.Request(
        f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}?fields=description',
        headers=headers)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())['fields'].get('description', {}).get('content', [])

# ─────────────────────────────────────────────────────────────────────────────
# GAP 1: IAMS30-4302 — Remove filter panel & Asset Type, add search input
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== GAP 1: IAMS30-4302 — Fix: remove filter panel, add search input ===')
put('IAMS30-4302', {
    'summary': 'ChooseFormModal.vue: form table (no filter panel), multi-select, mandatory toggle, search input',
    'description': {'type':'doc','version':1,'content':[
        h(2,'Service'),
        p('Frontend.Web.DigitalPlanning'),
        h(2,'Design Note (PENTING)'),
        p('Asset Type column dan Filter Panel telah DIHAPUS dari design final (sesuai IAMS30-4270). '
          'Pengganti filter adalah search input di dalam modal. Implementasi harus mengikuti design final, bukan spec awal.'),
        h(2,'Build ChooseFormModal.vue'),
        h(3,'Table columns (final design)'),
        ul(
            li('Checkbox — multi-select'),
            li('Form Name — nama form dari response API'),
            li('Asset Model — model aset yang di-tag ke form'),
            li('Service Type — tipe service (nullable)'),
            li('Maintenance Category Type — kategori maintenance'),
            li('Mandatory — toggle per baris, default OFF untuk semua form'),
        ),
        p('Kolom Asset Type TIDAK ada — dihapus dari design.'),
        h(3,'Search input'),
        ul(
            li('Input text "Search form name..." di atas tabel.'),
            li('Filtering dilakukan CLIENT-SIDE dari list yang sudah difetch — tidak trigger API call baru.'),
            li('Filter berdasarkan Form Name (case-insensitive, partial match).'),
            li('Filter TIDAK mereset selection state — form yang sudah dicentang tetap tercentang meski tersembunyi sementara oleh filter.'),
            li('Ketika search dibersihkan, semua form tampil kembali beserta selection state-nya.'),
        ),
        h(3,'Multi-select'),
        ul(
            li('Checkbox per baris, tidak ada minimum selection — save dengan 0 form dipilih valid.'),
            li('Select All / Deselect All tidak diperlukan untuk Phase 1.'),
        ),
        h(3,'Mandatory toggle'),
        ul(
            li('Toggle per baris, default OFF.'),
            li('isSuggestedMandatory=true dari API response: pre-set toggle ke ON sebagai hint untuk service sheet. Planner tetap bebas override.'),
            li('Toggle state tersimpan di-state lokal modal, tidak call API.'),
        ),
        h(3,'Group display'),
        ul(
            li('Grup 1 (match model + service type) ditampilkan lebih atas dari Grup 2.'),
            li('Section header optional: "Suggested for this service type" / "Other available forms".'),
        ),
        h(3,'Empty state'),
        p('"No forms available for the selected equipment." jika API return empty.'),
        h(3,'Loading & error state'),
        ul(
            li('Loading spinner selama fetch.'),
            li('Error state dengan tombol Retry jika API gagal.'),
        ),
        h(2,'Acceptance Criteria'),
        ul(
            li('Tidak ada filter panel, tidak ada kolom Asset Type.'),
            li('Search input memfilter form list client-side tanpa trigger API call.'),
            li('Search tidak mereset selection state.'),
            li('isSuggestedMandatory=true dari response men-pre-set toggle Mandatory ke ON.'),
            li('Grup 1 tampil di atas Grup 2.'),
            li('Submit dengan 0 form valid — modal bisa di-save tanpa pilih form.'),
            li('Unit test: search filter, selection preserved saat filter aktif, toggle state per baris.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# GAP 2: IAMS30-4308 — Align FE request body: formCode+isMandatory, not formId+version
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== GAP 2: IAMS30-4308 — Fix: formCode+isMandatory (not formId+version) ===')
put('IAMS30-4308', {
    'summary': 'Extend create plan API call: include forms array (formCode + isMandatory) from modal state',
    'description': {'type':'doc','version':1,'content':[
        h(2,'Service'),
        p('Frontend.Web.DigitalPlanning'),
        h(2,'Context — FormCode bukan FormId'),
        p('Request body menggunakan FormCode (bukan FormId + Version). Ini adalah design decision: '
          'Planner tidak peduli versi spesifik — mereka peduli "form ini". Versi aktif di-resolve '
          'oleh consumer di maintenance-execution saat event diproses. FormCode tersedia dari response '
          'GET form list (field formCode).'),
        h(2,'Extended request body'),
        cb(
            'POST /api/digitalPlanning/create/:userId\n\n'
            '// Tambahan field:\n'
            '"forms": [\n'
            '  {\n'
            '    "formCode": "string",    // dari response GET form list — BUKAN formId\n'
            '    "isMandatory": boolean   // dari state toggle per baris di modal\n'
            '  },\n'
            '  ...\n'
            ']\n\n'
            '// Jika tidak ada form dipilih:\n'
            '"forms": []   // selalu kirim field "forms", tidak pernah omit'
        ),
        h(2,'Implementation'),
        ul(
            li('Map setiap form yang dipilih di modal ke { formCode, isMandatory }.'),
            li('formCode diambil dari response GET form list (bukan formId, bukan hardcoded).'),
            li('isMandatory diambil dari toggle state per baris di ChooseFormModal.'),
            li('Kirim forms: [] jika Planner tidak memilih form atau modal tidak dibuka.'),
            li('JANGAN kirim formId, formName, atau version — ini tidak dibutuhkan oleh BE.'),
        ),
        h(2,'Acceptance Criteria'),
        ul(
            li('Request body menyertakan forms array dengan formCode + isMandatory per item.'),
            li('formCode berasal dari GET form list response, bukan hardcoded atau diambil dari formId.'),
            li('isMandatory mencerminkan state toggle per baris (bukan global toggle).'),
            li('forms: [] dikirim jika tidak ada form dipilih.'),
            li('formId, formName, version TIDAK ada di request body.'),
            li('Unit test: forms array dengan 2 form dipilih; forms: [] saat tidak ada pilihan; isMandatory per baris sesuai toggle state.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# GAP 3: IAMS30-4265 + 4287 — Add formCode to response + manual search note
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== GAP 3: IAMS30-4265 + 4287 — Add formCode to response ===')
existing_4265 = get_desc('IAMS30-4265')
put('IAMS30-4265', {
    'description': {'type':'doc','version':1,'content': existing_4265 + [
        h(2,'Response Fields — Wajib Menyertakan formCode'),
        p('Response harus menyertakan formCode (bukan hanya formId) karena FE akan mengirim formCode '
          '(bukan formId) saat menyimpan form package ke BE. Ini adalah design decision: '
          'version di-resolve oleh consumer, bukan oleh FE saat Planner pilih.'),
        cb(
            '// Response per form item:\n'
            '{\n'
            '  "group": 1,                    // 1 = match model+serviceType; 2 = match model only\n'
            '  "formCode": "string",           // WAJIB — dipakai FE untuk request body\n'
            '  "formId": "guid",              // boleh disertakan untuk kebutuhan display/tracking\n'
            '  "formName": "string",          // nama form untuk display\n'
            '  "assetModel": "string",\n'
            '  "serviceType": "string|null",\n'
            '  "maintenanceCategoryType": "string|null",\n'
            '  "isSuggestedMandatory": boolean  // true untuk service sheet yang matching\n'
            '}'
        ),
        h(2,'Manual Search — Client-Side Filtering'),
        p('Manual search untuk menemukan form di luar suggestion (Group 1 dan Group 2) dilakukan '
          'CLIENT-SIDE oleh FE — bukan via parameter tambahan ke endpoint ini.'),
        ul(
            li('FE fetch form list SEKALI saat modal dibuka (dengan equipmentModel + serviceType).'),
            li('Search input di modal memfilter list yang sudah difetch berdasarkan formName.'),
            li('Tidak ada endpoint tambahan untuk search. Tidak perlu parameter "searchTerm" di API ini.'),
        ),
        h(2,'Acceptance Criteria (tambahan)'),
        ul(
            li('Response menyertakan field formCode per item.'),
            li('Group 1 items muncul sebelum Group 2 dalam array (atau ada field "group" untuk FE sort).'),
            li('isSuggestedMandatory=true untuk form bertipe service sheet yang matching model+serviceType.'),
            li('Test: formCode tersedia di response; group split benar; isSuggestedMandatory service sheet.'),
        ),
    ]}
})

time.sleep(0.5)
existing_4287 = get_desc('IAMS30-4287')
put('IAMS30-4287', {
    'description': {'type':'doc','version':1,'content': existing_4287 + [
        h(2,'Response DTO — formCode wajib disertakan'),
        p('GetFormListResponse harus menyertakan formCode sebagai field wajib. '
          'FE menggunakan formCode (bukan formId) untuk mengirim ke request body saat save plan.'),
        cb(
            'public class FormListItemResponse {\n'
            '  public int Group { get; set; }               // 1 atau 2\n'
            '  public string FormCode { get; set; }         // WAJIB\n'
            '  public Guid FormId { get; set; }             // untuk referensi\n'
            '  public string FormName { get; set; }\n'
            '  public string? AssetModel { get; set; }\n'
            '  public string? ServiceType { get; set; }\n'
            '  public string? MaintenanceCategoryType { get; set; }\n'
            '  public bool IsSuggestedMandatory { get; set; } // true untuk service sheet matching\n'
            '}'
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# GAP 4: IAMS30-4312 — Add packageSyncStatus=pending disabled state
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== GAP 4: IAMS30-4312 — Add pending disabled state ===')
existing_4312 = get_desc('IAMS30-4312')
put('IAMS30-4312', {
    'description': {'type':'doc','version':1,'content': existing_4312 + [
        h(2,'packageSyncStatus=pending — Disabled State Tambahan'),
        p('Finish Execution button memiliki DUA kondisi disabled yang berbeda, dengan pesan berbeda:'),
        tbl(
            tr('Kondisi','Button State','Pesan hint', hdr=True),
            tr('packageSyncStatus = "pending"',
               'Disabled',
               '"Form package is not yet available. Please try again later or contact your admin."'),
            tr('packageSyncStatus = "ready" + ada mandatory form belum Complete',
               'Disabled',
               '"⚠ X mandatory form belum submitted"'),
            tr('packageSyncStatus = "none" (tidak ada form package)',
               'Enabled (existing gate berlaku)',
               '—'),
            tr('packageSyncStatus = "ready" + semua mandatory Complete',
               'Enabled',
               '—'),
        ),
        p('packageSyncStatus=pending artinya PlanForm ada di DPlanDB tapi Task belum terbuat '
          '(consumer belum selesai proses). Ini kondisi transient — biasanya berlangsung singkat. '
          'Mechanic harus menunggu atau menghubungi admin jika berlangsung lama.'),
        h(3,'Implementasi di Isar'),
        p('Field packageSyncStatus disertakan dalam response forms array dari server '
          '(lihat IAMS30-4372). Store di FormCard Isar schema. Gunakan untuk logic button guard.'),
        h(2,'Updated Acceptance Criteria'),
        ul(
            li('packageSyncStatus=pending: Finish Execution disabled dengan pesan "Form package not yet available".'),
            li('packageSyncStatus=ready + mandatory incomplete: disabled dengan pesan "X mandatory form belum submitted".'),
            li('packageSyncStatus=none: Finish Execution tidak terpengaruh oleh form gate.'),
            li('Widget test: semua 4 kondisi button state di atas.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# GAP 5: IAMS30-4383 — Add Task.Name = FormName mapping
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== GAP 5: IAMS30-4383 — Add Task.Name = FormName ===')
existing_4383 = get_desc('IAMS30-4383')
put('IAMS30-4383', {
    'description': {'type':'doc','version':1,'content': existing_4383 + [
        h(2,'Field Mapping Detail — Task.Name = FormName'),
        p('Saat consumer membuat Task untuk setiap form dalam PlanForms, field Task.Name HARUS '
          'diisi dengan FormName yang di-resolve dari maintenance-strategy (bukan dari event payload). '
          'Ini penting karena Task.Name digunakan untuk menampilkan nama form di list task tanpa '
          'cross-service call ke maintenance-strategy.'),
        cb(
            '// Step [2] resolve per FormCode:\n'
            'var form = await maintenanceStrategy.GetFormByCode(formCode, isActive: true);\n'
            '// form.FormId, form.FormName, form.Version\n\n'
            '// Step [4] upsert Task:\n'
            'await db.UpsertTask(new Task {\n'
            '  PlanId       = event.PlanId,\n'
            '  FormCode     = formCode,\n'
            '  Name         = form.FormName,   // <-- Task.Name = FormName dari maintenance-strategy\n'
            '  Status       = "Open",\n'
            '  WorkOrderId  = workOrderId\n'
            '});\n\n'
            '// Edge case: FormCode tidak ditemukan (form archived)\n'
            '// -> Task.Name = PlanForm.FormName dari event payload sebagai fallback'
        ),
        p('FormName juga disimpan di FormSubmission.FormName (dua tempat) untuk menghindari '
          'cross-service call saat get list form di workcard detail.'),
        h(2,'Acceptance Criteria (tambahan)'),
        ul(
            li('Task.Name diisi dengan FormName dari maintenance-strategy setelah resolve FormCode.'),
            li('Jika FormCode tidak ditemukan di maintenance-strategy (archived): Task.Name = FormName dari event payload (fallback).'),
            li('FormSubmission.FormName juga diisi dengan nilai yang sama.'),
            li('Test: Task.Name sesuai FormName dari maintenance-strategy; fallback test saat FormCode tidak ditemukan.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# GAP 6: IAMS30-4271 + 4305 — Clarify manual search = client-side
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== GAP 6: IAMS30-4271 + 4305 — Clarify manual search approach ===')
existing_4271 = get_desc('IAMS30-4271')
put('IAMS30-4271', {
    'description': {'type':'doc','version':1,'content': existing_4271 + [
        h(2,'Manual Search — Client-Side Filtering'),
        p('Selain melihat form suggestion (Group 1 dan Group 2), Planner bisa melakukan '
          'manual search untuk menemukan form di luar suggestion.'),
        ul(
            li('Manual search TIDAK memerlukan API call baru. FE melakukan client-side filtering '
               'pada list yang sudah difetch menggunakan search input di dalam modal.'),
            li('Endpoint GET form list (IAMS30-4265) TIDAK perlu parameter searchTerm.'),
            li('Filtering berdasarkan formName, case-insensitive, partial match.'),
            li('Filter tidak mereset selection state — form yang dipilih tetap dipilih meski tersembunyi.'),
            li('Ini berarti fetchnya SEKALI saat modal dibuka, bukan setiap karakter search diketik.'),
        ),
    ]}
})

time.sleep(0.5)
existing_4305 = get_desc('IAMS30-4305')
put('IAMS30-4305', {
    'description': {'type':'doc','version':1,'content': existing_4305 + [
        h(2,'Manual Search — Client-Side Only'),
        p('Hook ini fetch form list SEKALI saat modal dibuka. '
          'Manual search oleh Planner untuk menemukan form di luar suggestion '
          'dilakukan SEPENUHNYA client-side — tidak ada API call tambahan untuk search.'),
        ul(
            li('Hook tidak menerima atau mengirim parameter searchTerm ke API.'),
            li('FE filter list lokal menggunakan search input state dari modal.'),
            li('Cache hit saat re-open modal (equipment tidak berubah) masih berlaku — list yang difetch SEKALI bisa difilter berkali-kali client-side.'),
        ),
    ]}
})

print('\nAll gaps fixed.')
