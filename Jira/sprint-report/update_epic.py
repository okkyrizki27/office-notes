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

desc = {'type':'doc','version':1,'content':[

    # ── 1. Overview ──────────────────────────────────────────────────────────
    h(2,'1. Overview'),
    h(3,'1.1 Background'),
    p('PM Shutdown di Digiman+ saat ini hanya menangani backlog execution — temuan inspeksi yang dimasukkan ke scheduled service. Tidak ada dokumentasi terstruktur tentang pekerjaan yang dilakukan selama service berlangsung.'),
    p('Di lapangan, setiap scheduled service memiliki package form (service sheet, welding form, RTO, dll) yang wajib diisi mechanic sebelum unit dikembalikan ke operasional. Tab Form di workcard PM Shutdown mobile belum ada dan perlu diimplementasi.'),
    p('Phase 1 mengintegrasikan Form Builder ke dalam flow PM Shutdown: Planner assign package form saat membuat plan di Digiplan (web), mechanic mengisi form di lapangan (mobile, offline-first), dan Finish Execution di-gate oleh kelengkapan mandatory form.'),

    h(3,'1.2 Scope'),
    tbl(
        tr('Area','Komponen','Status', hdr=True),
        tr('Web (Digiplan)','Choose Form modal di Create Plan','New'),
        tr('Web (Digiplan)','Get form list by equipment model + service type (2 grup)','New'),
        tr('Web (Digiplan)','Extend Create Plan — simpan PlanForm ke DPlanDB','New'),
        tr('Web (Digiplan)','Pre-SUBMIT validation popup + form availability check','New'),
        tr('dplan BE','PlanForm table di DPlanDB (DRAFT CRUD + lock setelah SUBMIT)','New'),
        tr('dplan BE','Outbox table di DPlanDB + background relay job','New'),
        tr('dplan BE','Publish PlanSubmitted event ke Azure Service Bus','New'),
        tr('dplan BE','Fix DigitalPlanning.MaintenanceCategoryName','Modified'),
        tr('maintenance-execution BE','Service Bus consumer — upsert WorkOrder, Task, FormSubmission, Cosmos snapshot','New'),
        tr('maintenance-execution BE','Alter table FormSubmission — tambah FormName + IsMandatory','Modified'),
        tr('maintenance-execution BE','Alter table TaskPersonalizedLog — tambah 6 kolom snapshot','Modified'),
        tr('maintenance-execution BE','Alter table Task — tambah MachineSMUValue + MachineSMUAddress','Modified'),
        tr('maintenance-execution BE','Alter table TaskPersonalized — tambah StartedAt, hapus SMU cols, support 1:N','Modified'),
        tr('maintenance-execution BE','Migration script: pindah SMU data dari TaskPersonalized ke Task','New'),
        tr('maintenance-execution BE','Create table SiteShift + initial seed dari Tenant DB','New'),
        tr('maintenance-execution BE','Extend GET workcard detail (online + offline) — tambah forms array + packageSyncStatus','Modified'),
        tr('maintenance-execution BE','Extend POST finish execution — tambah mandatory form gate','Modified'),
        tr('maintenance-execution BE','Update Task.Status In Progress on TaskPersonalized sync (MIN StartedAt)','New'),
        tr('maintenance-execution BE','Update WorkOrder.Status In Progress on first TaskPersonalized sync','New'),
        tr('maintenance-execution BE','Auto-close TaskPersonalizedLog on form submit (safety net)','New'),
        tr('maintenance-execution BE','Submit Form endpoint — validate mandatory, Task.Status=Complete, approval workflow','New'),
        tr('maintenance-execution BE','Manual re-sync SiteShift (admin trigger)','New'),
        tr('Mobile','Tab Form — list form card, summary bar, status badge, 3-dot menu','New'),
        tr('Mobile','Tap form card — render form dari Cosmos snapshot','New'),
        tr('Mobile','Assign to Me flow','New / Enhanced'),
        tr('Mobile','Mulai (Slide to Start) — create + auto-close TaskPersonalizedLog session','New'),
        tr('Mobile','Finish tap — close TaskPersonalizedLog session dengan actual timestamp','New'),
        tr('Mobile','Submit Form UI — tap Submit, Summary review, confirm dialog, offline queue','New'),
        tr('Mobile','Per-field sync + batching + conflict notification','New'),
        tr('Mobile','SiteShift local cache dari offline sync response','New'),
    ),

    h(3,'1.3 Out of Scope (Phase 1 MVP)'),
    ul(
        li('Modifikasi package form dari lapangan oleh field team'),
        li('Form reopen setelah submit — deferred to next MVP'),
        li('Admin trigger re-copy Cosmos snapshot setelah form di-un-archive — deferred'),
        li('SiteShift update mechanism otomatis jika jadwal shift berubah (manual admin re-sync tersedia)'),
        li('Dashboard monitoring compliance mechanic per individu — deferred'),
        li('Mechanic account provisioning (operasional, bukan engineering ticket)'),
    ),

    # ── 2. Persona & Role ────────────────────────────────────────────────────
    h(2,'2. Persona & Role'),
    tbl(
        tr('Persona','Platform','Aksi utama', hdr=True),
        tr('Planner','Digiplan Web','Buat plan, pilih package form, set mandatory/optional per form'),
        tr('Mechanic','Digiman+ Mobile (device pribadi)','Assign to Me, tap Mulai, isi form, tap Finish, submit form'),
        tr('Supervisor / Foreman','Digiman+ Mobile','Review progress, lakukan Finish Execution'),
        tr('Mechanic (dengan permission)','Digiman+ Mobile','Finish Execution jika memiliki permission PM_Shutdown_Finish_Execution'),
        tr('Admin HO','Digiplan Web','Trigger re-sync SiteShift'),
    ),
    p('Semua mechanic, foreman, dan supervisor menggunakan individual account (email/UPN masing-masing) — tidak ada shared account.'),

    # ── 3. Architecture ──────────────────────────────────────────────────────
    h(2,'3. Arsitektur: Outbox Pattern + Azure Service Bus'),
    p('Proses plan SUBMIT melibatkan 3 database lintas service. Untuk menjamin atomicity dan resilience, downstream processing ke maintenance-execution dilakukan async via Azure Service Bus.'),
    cb(
        'dplan (saat Planner submit plan):\n'
        '  1. Validate: cek ketersediaan semua FormCode di maintenance-strategy\n'
        '  2. Resolve FormCode -> FormName terbaru\n'
        '  3. Dalam SATU DB transaction:\n'
        '       UPDATE DigitalPlanning.Status = SUBMIT\n'
        '       INSERT dbo.Outbox { EventType=PlanSubmitted, Payload=..., Status=Pending }\n'
        '     -> COMMIT (atomic)\n'
        '  4. Background relay job: poll Outbox (Pending) -> publish ke Service Bus -> mark Published\n\n'
        'Azure Service Bus (async, retry-able):\n'
        '  - Max Delivery Count: 5\n'
        '  - Lock Duration: 5 menit\n'
        '  - Backoff: Exponential 30s, 1m, 2m, 4m\n'
        '  - DLQ setelah attempt ke-5 -> alert ops\n\n'
        'maintenance-execution consumer:\n'
        '  1. Fetch asset detail dari cst-iams-sqldb-services-asset\n'
        '  2. Fetch FormId/FormName/Version per FormCode dari maintenance-strategy\n'
        '  3. Upsert WorkOrder (idempotent by PlanId)\n'
        '  4. Upsert Task + FormSubmission (idempotent by PlanId + FormCode)\n'
        '  5. Cosmos snapshot per FormSubmission (delete-then-reinsert, idempotent)\n'
        '  Edge case: FormCode di-archive setelah SUBMIT ->\n'
        '    Task + FormSubmission tetap dibuat (FormName dari event payload sebagai fallback)\n'
        '    Cosmos snapshot TIDAK dibuat\n'
        '    Mobile: "Form not available. Please contact your admin."'
    ),

    # ── 4. User Flow ─────────────────────────────────────────────────────────
    h(2,'4. User Flow'),
    h(3,'4.1 Planner — Assign Form Package di Digiplan Web'),
    ul(
        li('Buka Create Daily Planning modal, isi field plan.'),
        li('Klik "Choose Form" (aktif setelah Equipment dipilih).'),
        li('Sistem fetch form list dari maintenance-strategy: Group 1 (match model + service type), Group 2 (match model only).'),
        li('Service sheet untuk kombinasi model + service hour yang matching ditampilkan dengan isSuggestedMandatory=true sebagai hint — Planner bebas override.'),
        li('Planner pilih form (multi-select), set toggle Mandatory/Optional per form.'),
        li('Klik Continue -> pre-SUBMIT validation popup: cek availability setiap FormCode. Form tidak available (hard deleted / IsActive=0 / Archived) -> Confirm disabled.'),
        li('Planner klik Confirm -> plan disimpan, package terkunci. PlanForm tidak bisa diubah setelah ini.'),
    ),

    h(3,'4.2 Mechanic — Eksekusi Form di Mobile'),
    ul(
        li('Buka workcard PM Shutdown -> Tab Form aktif di sebelah Tab Backlog.'),
        li('Lihat list form card: nama form, badge Mandatory/Optional, status (Belum diisi / In Progress / Submitted), assignee chips.'),
        li('Tap ··· -> pilih "Assign to Me" -> TaskPersonalized dibuat (upsert by TaskId+UserCode).'),
        li('Tap form card (hanya bisa jika sudah assign) -> form terbuka read-only.'),
        li('Tap "Mulai" (Slide to Start) -> resolve shift dari SiteShift cache -> buat TaskPersonalizedLog session -> form jadi editable.'),
        li('Isi form per field -> auto-save, sync via debounce 3s + background timer 30s.'),
        li('Tap "Finish" (keluar sementara) -> EndDate session = actual tap time -> kembali bisa Start lagi nanti.'),
        li('Tap "Submit" -> review via Summary -> confirm -> Task.Status = Complete -> masuk approval workflow.'),
    ),

    h(3,'4.3 Supervisor/Foreman — Finish Execution'),
    ul(
        li('Validasi client-side: (1) semua backlog task selesai, (2) semua mandatory form Task.Status = Complete.'),
        li('Jika belum terpenuhi -> button Finish Execution disabled dengan hint.'),
        li('Jika packageSyncStatus = pending -> Finish Execution di-block: "Form package belum tersedia."'),
        li('Finish Execution bisa dilakukan offline -> di-queue -> server final validation saat sync.'),
    ),

    # ── 5. Functional Requirements ───────────────────────────────────────────
    h(2,'5. Functional Requirements'),
    h(3,'5.1 Form Suggestion Grouping'),
    tbl(
        tr('Grup','Filter','Keterangan', hdr=True),
        tr('Grup 1','Equipment Model + Service Type','Paling relevan, ditampilkan lebih atas'),
        tr('Grup 2','Equipment Model only','Tambahan, tanpa filter service type'),
    ),
    p('Service sheet yang matching Equipment Model + Service Hour ditampilkan dengan isSuggestedMandatory=true (hint ke FE). Authority IsMandatory sepenuhnya ada di Planner — ini hanya suggestion awal.'),

    h(3,'5.2 Tab Form Mobile — packageSyncStatus'),
    tbl(
        tr('Kondisi','packageSyncStatus','UX Mobile', hdr=True),
        tr('PlanForm (IsDeleted=0) count = 0','none','Empty state biasa. Finish Execution tidak terpengaruh.'),
        tr('PlanForm count > 0, Task count = 0','pending','"Service package sync in progress." Finish Execution BLOCKED.'),
        tr('Task count > 0','ready','Tampilkan list form card.'),
    ),

    h(3,'5.3 Multi-Mechanic & Conflict Resolution'),
    ul(
        li('N mechanic bisa assign ke 1 form dan mengisi secara bersamaan.'),
        li('Strategy: Optimistic Locking — tidak ada lock saat field dibuka.'),
        li('Granularitas conflict: per field (bukan per tab, bukan per dokumen).'),
        li('Resolution: First Write Wins by device timestamp (fieldId + timestamp sebagai idempotency key).'),
        li('Timestamp collision: sync pertama diproses, berikutnya no-op (tidak error, tidak overwrite).'),
        li('Conflict UX: "Sync berhasil. X field tidak tersimpan karena sudah diisi lebih awal oleh [nama mechanic]."'),
        li('Auto-sync: debounce 3s setelah input (upload dirty + download latest) + background timer 30s (download only).'),
    ),

    h(3,'5.4 Activity Tracking Rules'),
    ul(
        li('TaskPersonalized: 1 record per mechanic per form (upsert by TaskId+UserCode). Dibuat saat Assign to Me.'),
        li('TaskPersonalizedLog: max 1 open session per mechanic per shift (dedup by TaskPersonalizedId+ShiftName where EndDate IS NULL).'),
        li('Auto-close session: dijalankan client-side. Server hanya menerima dan menyimpan — tidak ada logic auto-close di server.'),
        li('Activity records (TaskPersonalizedLog) TETAP DITERIMA setelah Task.Status=Complete, selama StartDate < Task.CompletedAt (historical log).'),
        li('Form content (field values) DITOLAK setelah Task.Status=Complete — form sudah final.'),
        li('Task.Status -> In Progress menggunakan MIN(StartedAt) dari semua TaskPersonalized (termasuk yang sync belakangan).'),
    ),

    h(3,'5.5 Finish Execution'),
    ul(
        li('Gate: backlog execution selesai (existing) + semua Task dengan FormSubmission.IsMandatory=true memiliki Status=Complete.'),
        li('Optional form tidak memblokir Finish Execution.'),
        li('Bisa dilakukan offline (client-side validation) -> di-queue -> server final validation saat sync.'),
        li('Access: Supervisor/Foreman selalu bisa. Mechanic bisa jika memiliki permission PM_Shutdown_Finish_Execution.'),
        li('DueDate WorkOrder: informasi saja — tidak memblokir Finish Execution.'),
    ),

    # ── 6. Data Model ────────────────────────────────────────────────────────
    h(2,'6. Data Model'),
    h(3,'6.1 Tabel Baru'),
    tbl(
        tr('Tabel','Service / DB','Keterangan', hdr=True),
        tr('dbo.PlanForm','dplan / DPlanDB','Simpan form assignment per plan selama DRAFT. Terkunci setelah SUBMIT.'),
        tr('dbo.Outbox','dplan / DPlanDB','Outbox Pattern untuk relay PlanSubmitted event ke Service Bus.'),
        tr('dbo.SiteShift','maintenance-execution','Konfigurasi shift per site. Di-seed one-time dari Tenant DB.'),
    ),

    h(3,'6.2 Tabel yang Dimodifikasi'),
    tbl(
        tr('Tabel','Service','Perubahan', hdr=True),
        tr('DigitalPlanning','dplan','Fix: simpan MaintenanceCategoryName saat plan dibuat (join ke MaintenanceCategory).'),
        tr('Task','maintenance-execution','Tambah MachineSMUValue (NVARCHAR, NULL), MachineSMUAddress (NVARCHAR, NULL). Dipindah dari TaskPersonalized.'),
        tr('TaskPersonalized','maintenance-execution','Tambah StartedAt (DATETIME, NULL). Hapus MachineSMUValue dan MachineSMUAddress. Support 1:N per Task.'),
        tr('FormSubmission','maintenance-execution','Tambah FormName (NVARCHAR, NULL), IsMandatory (BIT, default 0).'),
        tr('TaskPersonalizedLog','maintenance-execution','Tambah 6 kolom snapshot: ShiftName, UserFullName, SiteCode, SiteName, SectionId, SectionName. Semua nullable, immutable setelah created.'),
    ),

    h(3,'6.3 Migration Scripts'),
    ul(
        li('Pindah MachineSMUValue/Address dari TaskPersonalized ke Task sebelum drop column (copy data existing terlebih dahulu).'),
        li('FormSubmission: backfill IsMandatory=0 untuk existing records (FormName dibiarkan NULL).'),
        li('Audit semua query yang mengasumsikan 1 Task = 1 TaskPersonalized (sekarang 1:N).'),
    ),

    h(3,'6.4 Relasi Data'),
    cb(
        'WorkOrder (1) -> PlanId -> dplan\n'
        '  L__ Task (N)                       -- 1 Task per form yang di-assign\n'
        '        L__ FormSubmission (1)        -- FormId, FormName, Version, IsMandatory\n'
        '              L__ [Cosmos snapshot]   -- template JSON, linked by FormSubmissionId\n'
        '        L__ TaskPersonalized (N)      -- 1 record per mechanic (upsert by TaskId+UserCode)\n'
        '              L__ TaskPersonalizedLog (N)  -- 1 record per sesi per shift'
    ),

    h(3,'6.5 Status Flow'),
    tbl(
        tr('Entitas','Status Flow','Trigger penting', hdr=True),
        tr('Task','Open -> In Progress -> Complete -> Approved','In Progress: MIN(StartedAt) dari TaskPersonalized. Complete: first submit wins.'),
        tr('WorkOrder','Open -> In Progress -> Complete','In Progress: first TaskPersonalized sync. Complete: Finish Execution.'),
    ),

    # ── 7. API Summary ───────────────────────────────────────────────────────
    h(2,'7. API Summary'),
    tbl(
        tr('Endpoint','Method','Service','Status', hdr=True),
        tr('GET form list by equipment model + service type','GET','maintenance-strategy','New'),
        tr('POST /api/digitalPlanning/create/:userId','POST','dplan','Modified — tambah PlanForm save + Outbox entry'),
        tr('GET /api/work-card/detail','GET','maintenance-execution','Modified — tambah forms array + packageSyncStatus'),
        tr('GET /api/work-card/detail-offline-mode','GET','maintenance-execution','Modified — tambah forms array + delta sync + SiteShift data'),
        tr('POST /api/tasks/{taskId}/assign-to-me','POST','maintenance-execution','New / Enhanced (investigasi existing dulu)'),
        tr('POST /api/form-submissions/{id}/sync','POST','maintenance-execution','New — per-field sync dengan First Write Wins'),
        tr('POST /api/form-submissions/{id}/submit','POST','maintenance-execution','New — final submit, Task.Status=Complete, approval workflow'),
        tr('POST /api/task-personalized-logs','POST','maintenance-execution','New/Enhanced — insert TaskPersonalizedLog dengan 6 snapshot fields'),
        tr('POST /api/executionplanning/finish/:userId','POST','maintenance-execution','Modified — tambah mandatory form gate'),
        tr('POST SiteShift re-sync (admin)','POST','maintenance-execution','New'),
    ),

    h(3,'7.1 packageSyncStatus di response workcard detail'),
    p('Field packageSyncStatus (string: "none" | "pending" | "ready") di-derive runtime — tidak perlu kolom DB baru. Logic: PlanForm(IsDeleted=0).count=0 -> none; count>0 tapi Task.count=0 -> pending; Task.count>0 -> ready.'),

    # ── 8. Business Rules ────────────────────────────────────────────────────
    h(2,'8. Business Rules'),
    tbl(
        tr('No','Rule', hdr=True),
        tr('1','Submit tanpa form package dibolehkan — Tab Form empty, Finish Execution tidak terblokir.'),
        tr('2','Package terkunci setelah plan di-SUBMIT — semua write ke PlanForm di-block dengan 400.'),
        tr('3','Service sheet untuk matching Equipment Model + Service Hour diberi isSuggestedMandatory=true sebagai hint. Authority IsMandatory sepenuhnya di Planner.'),
        tr('4','Multi-assign dibolehkan — N mechanic bisa assign ke 1 form.'),
        tr('5','TaskPersonalized upsert by TaskId+UserCode — tidak ada duplikasi meski assign dari beberapa device.'),
        tr('6','Form render dari Cosmos snapshot di maintenance-execution — bukan real-time dari maintenance-strategy.'),
        tr('7','Cosmos snapshot dibuat saat plan SUBMIT (via consumer) — bukan saat form pertama dibuka.'),
        tr('8','FormName disimpan di Task.Name dan FormSubmission.FormName — tidak perlu cross-service call saat get list.'),
        tr('9','Submit per form, independen antar form dalam package.'),
        tr('10','First Write Wins per field by device timestamp (fieldId+timestamp = idempotency key).'),
        tr('11','Timestamp collision: sync pertama diproses, berikutnya no-op.'),
        tr('12','First Submit Wins — duplicate submit idempotent, return 200.'),
        tr('13','Finish Execution di-gate oleh mandatory form — optional form tidak memblokir.'),
        tr('14','Offline-first penuh — semua aksi (assign, mulai, isi, submit, finish) bisa dilakukan tanpa koneksi.'),
        tr('15','Auto-close TaskPersonalizedLog dijalankan client-side — server hanya terima dan simpan.'),
        tr('16','Auto-close via Submit (safety net): EndDate = min(shift end time, submit time).'),
        tr('17','Task.Status In Progress menggunakan MIN(StartedAt) dari semua TaskPersonalized.'),
        tr('18','Activity records (TaskPersonalizedLog) selalu diterima selama StartDate < Task.CompletedAt.'),
        tr('19','Form content ditolak jika sync setelah Task.Status=Complete.'),
        tr('20','SiteShift di-seed ke maintenance-execution — tidak cross-service call saat runtime.'),
        tr('21','DueDate WorkOrder: informasi saja, tidak ada enforcement atau blocking.'),
    ),

    # ── 9. Permissions ───────────────────────────────────────────────────────
    h(2,'9. Permissions'),
    tbl(
        tr('Permission Code','Deskripsi','Platform', hdr=True),
        tr('IAMS_Mobile_PMShutdown_Form_Assign','Mechanic dapat assign diri ke form (Assign to Me)','Mobile'),
        tr('PM_Shutdown_Finish_Execution','Mechanic dapat melakukan Finish Execution','Mobile'),
        tr('IAMS_Admin_SiteShift_Sync','Admin dapat trigger re-sync SiteShift dari Tenant DB','Web'),
    ),

    # ── 10. Edge Cases ───────────────────────────────────────────────────────
    h(2,'10. Edge Cases'),
    tbl(
        tr('Edge Case','Keputusan', hdr=True),
        tr('Plan disimpan tanpa form (Choose Form tidak diisi)','Valid — packageSyncStatus=none, Finish Execution tidak terblokir.'),
        tr('Semua form Optional, tidak ada Mandatory','Finish Execution tidak terblokir oleh form gate.'),
        tr('Service sheet tidak ada di Form Builder','Tidak ada blocker — plan tetap bisa disimpan dan dieksekusi.'),
        tr('Form di-archive setelah SUBMIT tapi sebelum consumer proses','Task+FormSubmission dibuat (FormName dari event payload). Cosmos snapshot tidak dibuat. Mobile: "Form not available."'),
        tr('Mechanic sync activity record setelah Task Complete','Diterima jika StartDate < Task.CompletedAt. Ditolak jika StartDate >= CompletedAt.'),
        tr('Mechanic sync form content setelah Task Complete','Ditolak — form sudah final.'),
        tr('Duplicate submit oleh 2 mechanic bersamaan','First submit wins. Submit kedua: 200 (idempotent).'),
        tr('packageSyncStatus=pending saat Finish Execution','Finish Execution di-block: "Form package belum tersedia."'),
        tr('SiteShift tidak ada di local cache saat Mulai','Fallback: buat session dengan ShiftName=null.'),
        tr('SiteCode mechanic tidak match dengan SiteShift','Gunakan default site dari konfigurasi.'),
        tr('Mechanic tap Mulai berkali-kali di shift yang sama','Tidak buat record baru — open session shift sama sudah ada (dedup).'),
        tr('Mechanic lanjut kerja ke shift berikutnya tanpa Finish','Auto-close via tap Mulai di shift baru, atau via Submit sebagai safety net.'),
        tr('DueDate WorkOrder terlewati','Informasi saja — tidak memblokir Finish Execution.'),
        tr('Tenant DB unreachable saat re-sync SiteShift','Return error — SiteShift tidak berubah.'),
        tr('Service Bus Standard tier (bukan Premium)','Exponential backoff via workaround scheduled re-enqueue. Konfirmasi tier sebelum deploy.'),
        tr('IAMS30-4276 (Activity Type LOV)','BUKAN bagian dari EPIC ini. Harus dipindahkan ke EPIC yang sesuai (kemungkinan IAMS30-4155 Order Improvement). Epic Link update manual diperlukan.'),
    ),

]}

data = json.dumps({'fields': {
    'summary': 'Form Packaging PM Shutdown — Phase 1',
    'description': desc,
}}).encode()
req = urllib.request.Request(
    'https://bukittechnology.atlassian.net/rest/api/3/issue/IAMS30-4275',
    data=data, headers=headers, method='PUT')
resp = urllib.request.urlopen(req)
print('EPIC updated:', resp.status)
