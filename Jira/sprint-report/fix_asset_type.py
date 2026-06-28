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

def put(key, fields, retries=3):
    data = json.dumps({'fields': fields}).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}',
                data=data, headers=headers, method='PUT')
            resp = urllib.request.urlopen(req, timeout=30)
            print(f'PUT {key}: {resp.status}')
            time.sleep(0.8)
            return
        except Exception as e:
            if attempt < retries-1:
                time.sleep(3)
            else:
                print(f'FAILED {key}: {e}')

def get_desc(key):
    req = urllib.request.Request(
        f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}?fields=description,summary',
        headers=headers)
    resp = urllib.request.urlopen(req, timeout=30)
    d = json.loads(resp.read())
    return d['fields'].get('description', {}).get('content', []), d['fields'].get('summary','')

# ─────────────────────────────────────────────────────────────────────────────
# 1. IAMS30-4270 — Update: asset type column + filter panel termasuk
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 1. IAMS30-4270 ===')
existing, summ = get_desc('IAMS30-4270')
put('IAMS30-4270', {
    'summary': '[FE] Form Bundle — Choose Form: Step 2 Stepper in Create Plan Modal dengan Filter Panel, Asset Type, dan Mandatory Toggle',
    'description': {'type':'doc','version':1,'content':[
        h(2,'Background'),
        p('Sebagai bagian dari Form Bundle Integration untuk PM Shutdown, Planner perlu memilih '
          'beberapa form sekaligus saat membuat plan. Choose Form diimplementasikan sebagai '
          'Step 2 dari stepper di dalam modal Create Daily Planning yang sudah ada.'),
        p('Planner perlu bisa melihat Asset Type dari setiap form agar bisa memilih form yang '
          'tepat untuk unit yang akan di-service. Filter Panel tersedia untuk memfilter list '
          'berdasarkan Asset Type, Asset Model, dan Service Type.'),

        h(2,'Objective'),
        p('Implementasi Step 2 dari modal Create Daily Planning — menampilkan tabel form selection '
          'dengan kolom Asset Type, filter panel, mandatory toggle per baris, dan search input, '
          'sehingga Planner dapat menyusun form bundle sebelum menyimpan plan.'),

        h(2,'Scope'),
        ul(
            li('Product: Digiplan Web'),
            li('Modal: Create Daily Planning — Step 2 (Choose Form)'),
            li('Depends on: IAMS30-4265 (BE get form list), IAMS30-4271 (FE fetch hook)'),
        ),

        h(2,'UI Components'),

        h(3,'Tabel Form'),
        tbl(
            tr('Kolom','Type','Keterangan', hdr=True),
            tr('Checkbox','Boolean','Multi-select per baris. Tidak ada minimum selection.'),
            tr('Form Name','String','Nama form dari response API.'),
            tr('Asset Type','String','Tipe aset (Heavy Equipment, Light Vehicle, dll). Penting untuk Planner memastikan form sesuai unit.'),
            tr('Asset Model','String','Model aset yang di-tag ke form.'),
            tr('Service Type','String','Tipe service. Nullable.'),
            tr('Maintenance Category Type','String','Kategori maintenance.'),
            tr('Mandatory','Toggle (Boolean)','Default OFF. isSuggestedMandatory=true dari API men-pre-set ke ON sebagai hint.'),
        ),

        h(3,'Filter Panel'),
        p('Filter panel tersedia di sisi kiri atau atas tabel untuk memfilter list berdasarkan:'),
        ul(
            li('Asset Type — dropdown multi-select dari daftar asset type yang ada di list'),
            li('Asset Model — dropdown atau search dari daftar asset model yang ada di list'),
            li('Service Type — dropdown dari daftar service type yang ada di list'),
        ),
        ul(
            li('Filter dilakukan CLIENT-SIDE dari list yang sudah difetch — tidak trigger API call baru.'),
            li('Filter TIDAK mereset selection state — form yang sudah dicentang tetap tercentang meski tersembunyi oleh filter.'),
            li('Ketika filter dibersihkan, semua form tampil kembali beserta selection state-nya.'),
        ),

        h(3,'Search Input'),
        p('Di samping filter panel, tersedia search input untuk pencarian form by name:'),
        ul(
            li('Filtering client-side, case-insensitive, partial match pada Form Name.'),
            li('Tidak trigger API call baru.'),
            li('Tidak mereset selection state.'),
            li('Planner bisa kombinasikan search + filter panel sekaligus.'),
        ),

        h(3,'Suggestion Grouping'),
        ul(
            li('Grup 1 (match Equipment Model + Service Type) ditampilkan lebih atas — lebih relevan.'),
            li('Grup 2 (match Equipment Model saja) ditampilkan di bawah Grup 1.'),
            li('Section header per grup: e.g. "Suggested for this service type" / "Other available forms".'),
            li('isSuggestedMandatory=true dari API → toggle Mandatory di-pre-set ke ON sebagai hint. Planner bebas override.'),
        ),

        h(3,'Empty & Loading States'),
        ul(
            li('Loading spinner selama fetch.'),
            li('Error state + tombol Retry jika API gagal.'),
            li('"No forms available for the selected equipment." jika API return empty.'),
            li('"No results match your filter." jika filter/search tidak ada hasil.'),
        ),

        h(3,'Post-Save State'),
        ul(
            li('Setelah Planner klik Save di modal Choose Form: modal tertutup.'),
            li('Create Plan modal menampilkan summary: "X form selected (Y mandatory)".'),
            li('Button label berubah dari "Choose Form" ke "Edit Form".'),
            li('"Edit Form" disabled setelah Planner klik Continue (plan tersimpan, package terkunci).'),
        ),

        h(2,'Business Rules'),
        ul(
            li('Tidak ada minimum selection — save dengan 0 form dipilih valid.'),
            li('Filter dan search tidak mereset selection state.'),
            li('Toggle Mandatory adalah per-form, bukan global.'),
            li('Package terkunci setelah plan tersimpan — tidak bisa diubah lagi.'),
        ),

        h(2,'Acceptance Criteria'),
        ul(
            li('Tabel menampilkan kolom: Checkbox, Form Name, Asset Type, Asset Model, Service Type, Maintenance Category Type, Mandatory.'),
            li('Filter panel tersedia dengan filter Asset Type, Asset Model, Service Type.'),
            li('Filter client-side: tidak trigger API call, tidak mereset selection.'),
            li('Search input client-side by form name.'),
            li('Grup 1 tampil di atas Grup 2.'),
            li('isSuggestedMandatory=true dari API → toggle Mandatory pre-set ke ON.'),
            li('Save dengan 0 form valid.'),
            li('Summary label di Create Plan modal menampilkan count yang benar.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 2. IAMS30-4302 — Revert: tambahkan kembali filter panel + asset type column
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 2. IAMS30-4302 ===')
put('IAMS30-4302', {
    'summary': 'ChooseFormModal.vue: tabel dengan Asset Type, filter panel, multi-select, mandatory toggle, search input',
    'description': {'type':'doc','version':1,'content':[
        h(2,'Service'),
        p('Frontend.Web.DigitalPlanning'),

        h(2,'Build ChooseFormModal.vue'),

        h(3,'Table columns'),
        tbl(
            tr('Kolom','Source','Keterangan', hdr=True),
            tr('Checkbox','—','Multi-select per baris'),
            tr('Form Name','formName','Nama form dari API'),
            tr('Asset Type','assetType','Tipe aset — penting untuk Planner memilih form yang sesuai unit'),
            tr('Asset Model','assetModel','Model aset'),
            tr('Service Type','serviceType','Nullable'),
            tr('Maintenance Category Type','maintenanceCategoryType','Nullable'),
            tr('Mandatory','isMandatory (state)','Toggle per baris, default OFF. Pre-set ON jika isSuggestedMandatory=true dari API.'),
        ),

        h(3,'Filter Panel (client-side)'),
        p('Filter panel di sisi kiri atau atas tabel. Semua filter beroperasi CLIENT-SIDE '
          'dari list yang sudah difetch — tidak trigger API call baru.'),
        ul(
            li('Filter "Asset Type": multi-select dari asset type yang tersedia di list.'),
            li('Filter "Asset Model": multi-select dari asset model yang tersedia di list.'),
            li('Filter "Service Type": multi-select dari service type yang tersedia di list.'),
            li('Filter TIDAK mereset selection state — form yang dipilih tetap terpilih meski tersembunyi.'),
            li('Ketika filter dibersihkan: semua form tampil kembali dengan selection state tetap.'),
        ),

        h(3,'Search Input (client-side)'),
        ul(
            li('Input text "Search form name..." di atas tabel.'),
            li('Filter client-side berdasarkan Form Name, case-insensitive, partial match.'),
            li('Tidak trigger API call baru.'),
            li('Tidak mereset selection state.'),
            li('Bisa dikombinasikan dengan filter panel.'),
        ),

        h(3,'Multi-select'),
        ul(
            li('Checkbox per baris.'),
            li('Tidak ada minimum selection — save dengan 0 form dipilih valid.'),
        ),

        h(3,'Mandatory Toggle'),
        ul(
            li('Toggle per baris, default OFF.'),
            li('Jika isSuggestedMandatory=true dari API: pre-set toggle ke ON sebagai hint (service sheet).'),
            li('Planner bebas override semua toggle.'),
            li('Toggle state disimpan di local state modal.'),
        ),

        h(3,'Suggestion Grouping'),
        ul(
            li('Grup 1 (match model + service type) tampil di atas Grup 2.'),
            li('Section header per grup untuk membedakan secara visual.'),
        ),

        h(3,'Empty & Edge States'),
        ul(
            li('"No forms available." jika API return empty.'),
            li('"No results match your filter." jika filter/search tidak ada hasil.'),
            li('Loading spinner selama fetch. Error state + Retry jika fetch gagal.'),
        ),

        h(2,'Acceptance Criteria'),
        ul(
            li('Kolom Asset Type tampil di tabel.'),
            li('Filter panel tersedia (Asset Type, Asset Model, Service Type) — client-side, tidak trigger API.'),
            li('Filter tidak mereset selection state.'),
            li('Search input tersedia — client-side, tidak trigger API.'),
            li('isSuggestedMandatory=true dari response men-pre-set toggle Mandatory ke ON.'),
            li('Grup 1 di atas Grup 2 dalam tabel.'),
            li('Save dengan 0 form valid.'),
            li('Unit test: filter client-side, selection preserved saat filter aktif, toggle state per baris.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 3. IAMS30-4271 — Remove "no filter panel" note, add proper description
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 3. IAMS30-4271 ===')
put('IAMS30-4271', {
    'summary': '[FE] Form Bundle — Fetch Form List on Enter Step 2 (Choose Form)',
    'description': {'type':'doc','version':1,'content':[
        h(2,'Background'),
        p('Saat Planner masuk ke Step 2 (Choose Form) dari modal Create Daily Planning, sistem '
          'harus fetch daftar form yang relevan dari BE. Fetch dipicu saat Step 2 menjadi aktif.'),

        h(2,'Objective'),
        p('Implementasi API call untuk fetch form list saat Planner masuk Step 2, '
          'dengan parameter equipmentModel dan serviceType dari Step 1.'),

        h(2,'Scope'),
        ul(
            li('Product: Digiplan Web'),
            li('Trigger: Step 2 menjadi aktif (Choose Form diklik)'),
            li('Depends on: IAMS30-4265 (BE endpoint)'),
        ),

        h(2,'Fetch Behavior'),
        ul(
            li('GET dipanggil saat Planner klik "Choose Form" — BUKAN saat Equipment field berubah.'),
            li('Parameter: equipmentModel (required, dari field Equipment di Step 1), serviceType (optional, dari field Activity Type).'),
            li('Response berisi form list dengan grouping (Group 1 + Group 2), assetType, formCode, isSuggestedMandatory, dll.'),
            li('Loading state ditampilkan selama fetch.'),
            li('Error state + Retry jika fetch gagal.'),
        ),

        h(2,'Client-Side Filtering & Search'),
        p('Setelah fetch, filter panel dan search input di modal beroperasi CLIENT-SIDE '
          'dari list yang sudah difetch:'),
        ul(
            li('Filter panel (Asset Type, Asset Model, Service Type): filter client-side, tidak trigger fetch baru.'),
            li('Search input (by Form Name): filter client-side, tidak trigger fetch baru.'),
            li('Planner bisa kombinasikan filter panel + search sekaligus.'),
            li('Filter/search tidak mereset selection state.'),
        ),

        h(2,'Cache Strategy'),
        ul(
            li('List di-cache setelah fetch pertama.'),
            li('Jika modal ditutup dan dibuka lagi tanpa ganti Equipment: gunakan cache (tidak fetch ulang).'),
            li('Jika Equipment diganti: invalidate cache, fetch baru.'),
        ),

        h(2,'Acceptance Criteria'),
        ul(
            li('Fetch dipicu saat "Choose Form" diklik, bukan saat Equipment berubah.'),
            li('Loading dan error state berjalan dengan benar.'),
            li('Cache hit saat re-open modal dengan equipment yang sama.'),
            li('Cache invalidated saat Equipment berubah.'),
            li('Response includes assetType, formCode, group, isSuggestedMandatory.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 4. IAMS30-4305 — Remove "no filter panel" note, update properly
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 4. IAMS30-4305 ===')
put('IAMS30-4305', {
    'summary': 'useFormList TanStack Query hook: trigger on Choose Form click, param derivation, loading/error states',
    'description': {'type':'doc','version':1,'content':[
        h(2,'Scope'),
        p('Frontend.Web.DigitalPlanning — TanStack Query hook untuk form list.'),

        h(2,'Trigger'),
        p('"Choose Form" button click — BUKAN perubahan Equipment field.'),
        p('Per IAMS30-4271: "GET dipanggil saat Planner klik Choose Form, bukan saat Equipment dipilih."'),

        h(2,'Hook Implementation'),
        cb(
            'useFormList(equipmentModel: string, serviceType: string | null, enabled: boolean)\n\n'
            '// enabled = true hanya saat Choose Form modal dibuka\n'
            '// equipmentModel dan serviceType dari Step 1 state\n\n'
            '// Returns:\n'
            '// - data: FormListItem[] (dengan group, formCode, formName, assetType,\n'
            '//                         assetModel, serviceType, maintenanceCategoryType,\n'
            '//                         isSuggestedMandatory)\n'
            '// - isLoading, isError, refetch'
        ),

        h(2,'Cache Strategy'),
        ul(
            li('Cache key: ["form-list", equipmentModel, serviceType]'),
            li('Pertama kali "Choose Form" diklik dengan equipment X: GET fired, result cached.'),
            li('Re-open modal (equipment sama): cache hit, tidak fetch ulang.'),
            li('Equipment berubah: cache invalidated untuk key lama, fetch baru untuk key baru.'),
        ),

        h(2,'Client-Side Filtering'),
        p('Filter panel (Asset Type, Asset Model, Service Type) dan search input di modal '
          'beroperasi CLIENT-SIDE dari data yang sudah difetch oleh hook ini. '
          'Hook TIDAK menerima atau mengirim parameter filter/search ke API — '
          'filtering dilakukan di layer modal, bukan di hook.'),

        h(2,'Acceptance Criteria'),
        ul(
            li('Tidak ada fetch saat Equipment field berubah (enabled=false).'),
            li('Fetch terjadi saat modal dibuka (enabled=true).'),
            li('Cache hit saat re-open modal dengan equipment yang sama.'),
            li('Cache invalidated saat Equipment berubah.'),
            li('Loading dan error state ter-expose dari hook.'),
            li('Response data menyertakan: group, formCode, formName, assetType, assetModel, serviceType, maintenanceCategoryType, isSuggestedMandatory.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 5. IAMS30-4265 — Tambah assetType ke response fields
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 5. IAMS30-4265 — Ensure assetType in response ===')
existing_4265, _ = get_desc('IAMS30-4265')
# Find if assetType already mentioned; it was appended previously
# Let's update the response DTO description to be definitive
put('IAMS30-4265', {
    'summary': '[BE] Form Package — Get Form List by Equipment Model and Service Type (with Asset Type, Grouping, isSuggestedMandatory)',
    'description': {'type':'doc','version':1,'content': existing_4265 + [
        h(2,'Response Fields — Lengkap'),
        p('Response harus menyertakan semua field berikut agar FE dapat '
          'menampilkan tabel dengan kolom Asset Type dan filter panel:'),
        cb(
            '// Response per form item:\n'
            '[\n'
            '  {\n'
            '    "group": 1,                         // 1 = match model+serviceType; 2 = match model only\n'
            '    "formCode": "string",               // WAJIB — dipakai FE untuk request body\n'
            '    "formId": "guid",                   // untuk referensi\n'
            '    "formName": "string",               // untuk display di tabel\n'
            '    "assetType": "string",              // WAJIB — untuk kolom Asset Type dan filter panel\n'
            '    "assetModel": "string|null",        // untuk kolom Asset Model dan filter\n'
            '    "serviceType": "string|null",       // untuk kolom Service Type dan filter\n'
            '    "maintenanceCategoryType": "string|null",  // untuk kolom Maintenance Category Type\n'
            '    "isSuggestedMandatory": boolean     // true untuk service sheet yang matching\n'
            '  },\n'
            '  ...\n'
            ']'
        ),
        p('assetType WAJIB ada di response karena:'),
        ul(
            li('Ditampilkan sebagai kolom "Asset Type" di tabel Choose Form (IAMS30-4302).'),
            li('Digunakan sebagai opsi filter panel "Asset Type" di Choose Form modal.'),
            li('Membantu Planner memastikan form yang dipilih sesuai dengan tipe unit yang akan di-service.'),
        ),
    ]}
})

# ─────────────────────────────────────────────────────────────────────────────
# 6. IAMS30-4287 — Tambah assetType ke response DTO
# ─────────────────────────────────────────────────────────────────────────────
print('\n=== 6. IAMS30-4287 — Add assetType to response DTO ===')
existing_4287, _ = get_desc('IAMS30-4287')
put('IAMS30-4287', {
    'description': {'type':'doc','version':1,'content': existing_4287 + [
        h(2,'Response DTO — FormListItemResponse (complete)'),
        p('DTO harus menyertakan assetType karena FE membutuhkannya untuk kolom tabel '
          'dan filter panel client-side:'),
        cb(
            'public class FormListItemResponse {\n'
            '  public int Group { get; set; }                        // 1 atau 2\n'
            '  public string FormCode { get; set; }                  // WAJIB — untuk request body\n'
            '  public Guid FormId { get; set; }                      // untuk referensi\n'
            '  public string FormName { get; set; }                  // display\n'
            '  public string AssetType { get; set; }                 // WAJIB — kolom + filter\n'
            '  public string? AssetModel { get; set; }               // kolom + filter\n'
            '  public string? ServiceType { get; set; }              // kolom + filter\n'
            '  public string? MaintenanceCategoryType { get; set; }  // kolom\n'
            '  public bool IsSuggestedMandatory { get; set; }        // toggle hint\n'
            '}'
        ),
        p('AssetType diambil dari mapping form di maintenance-strategy — '
          'setiap form di-tag ke asset type tertentu.'),
    ]}
})

print('\nAll ticket updates done.')
