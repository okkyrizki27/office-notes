import json, os, urllib.request, base64

auth = os.environ['JIRA_EMAIL'] + ':' + os.environ['JIRA_API_TOKEN']
auth_b64 = base64.b64encode(auth.encode()).decode()
headers = {'Authorization': f'Basic {auth_b64}', 'Content-Type': 'application/json', 'Accept': 'application/json'}

def p(text): return {'type':'paragraph','content':[{'type':'text','text':text}]}
def h(level, text): return {'type':'heading','attrs':{'level':level},'content':[{'type':'text','text':text}]}
def cb(text): return {'type':'codeBlock','attrs':{},'content':[{'type':'text','text':text}]}
def li(text): return {'type':'listItem','content':[{'type':'paragraph','content':[{'type':'text','text':text}]}]}
def ul(*items): return {'type':'bulletList','content':list(items)}
def ol(*items): return {'type':'orderedList','content':list(items)}
def table_row(*cells, header=False):
    ct = 'tableHeader' if header else 'tableCell'
    return {'type':'tableRow','content':[{'type':ct,'attrs':{},'content':[{'type':'paragraph','content':[{'type':'text','text':str(c)}]}]} for c in cells]}
def table(*rows): return {'type':'table','attrs':{'isNumberColumnEnabled':False,'layout':'default'},'content':list(rows)}

def put(key, payload_dict):
    data = json.dumps(payload_dict).encode()
    req = urllib.request.Request(
        f'https://bukittechnology.atlassian.net/rest/api/3/issue/{key}',
        data=data, headers=headers, method='PUT'
    )
    resp = urllib.request.urlopen(req)
    print(f'Updated {key}: {resp.status}')

def create_subtask(parent_key, summary, desc):
    data = json.dumps({
        'fields': {
            'project': {'id': '10173'},
            'parent': {'key': parent_key},
            'summary': summary,
            'description': desc,
            'issuetype': {'id': '10262'},
        }
    }).encode()
    req = urllib.request.Request(
        'https://bukittechnology.atlassian.net/rest/api/3/issue',
        data=data, headers=headers, method='POST'
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print(f'  Created subtask {result["key"]}: {summary[:70]}')
        return result['key']
    except urllib.error.HTTPError as e:
        print(f'  Error: {e.code}', e.read().decode()[:200])

# ═══════════════════════════════════════════════════════════════════════════════
# 1. UPDATE IAMS30-4266 — title + description
# ═══════════════════════════════════════════════════════════════════════════════
event_payload = (
    'PlanSubmitted {\n'
    '  PlanId,\n'
    '  PlanName,                // DPlanDB.DigitalPlanning.PlanName\n'
    '  ProjectStart,            // DPlanDB.DigitalPlanning.ProjectStart\n'
    '  SiteId,                  // DPlanDB.DigitalPlanning.SiteId\n'
    '  MaintenanceCategoryCode, // DPlanDB.DigitalPlanning.MaintenanceCategoryCode\n'
    '  MaintenanceCategoryName, // DPlanDB.DigitalPlanning.MaintenanceCategoryName (setelah fix IAMS30-4368)\n'
    '  AssetNumber,             // DPlanDB.DPEquipment.Equipment\n'
    '  PlanForms: [\n'
    '    { FormCode, IsMandatory }  // FormCode (bukan FormId) — versi di-resolve oleh consumer\n'
    '  ]\n'
    '}'
)

consumer_flow = (
    '// maintenance-execution Service Bus consumer:\n'
    '[1] Fetch cst-iams-sqldb-services-asset:\n'
    '      AssetModelCode, AssetModelName, SectionTypeCode\n'
    '      berdasarkan AssetNumber dari event\n\n'
    '[2] Per FormCode dalam PlanForms:\n'
    '      Fetch maintenance-strategy: FormId, FormName, Version\n'
    '      (IsActive=1, ambil versi aktif)\n\n'
    '[3] SQL upsert WorkOrder (idempotent by PlanId):\n'
    '      PlanId, Description=PlanName, ScheduleStartDate=ProjectStart,\n'
    '      SiteCode=SiteId, AssetNumber, AssetModelCode, AssetModelName,\n'
    '      SectionTypeCode, MaintenanceCategoryCode, MaintenanceCategoryName,\n'
    '      Source="Digiplan"\n\n'
    '[4] SQL upsert Task + FormSubmission (idempotent by PlanId + FormCode):\n'
    '      Task.Name = FormName (dari step 2)\n'
    '      FormSubmission.FormId, FormSubmission.FormName, FormSubmission.IsMandatory\n\n'
    '[5] Per FormSubmission — Cosmos snapshot:\n'
    '      DELETE existing docs (safety for retry)\n'
    '      Cosmos Transactional Batch (partition: FormSubmissionId):\n'
    '        INSERT tab1_doc, tab2_doc, ... (all-or-nothing)\n\n'
    'Edge case — Form di-archive SETELAH SUBMIT tapi SEBELUM consumer process:\n'
    '  → Step [2] FormCode tidak ditemukan (IsActive=0 / Archived)\n'
    '  → Task + FormSubmission tetap dibuat (FormName dari PlanForm.FormName sebagai fallback)\n'
    '  → Cosmos snapshot TIDAK dibuat (skip step [5])\n'
    '  → Mechanic melihat "Form not available. Please contact your admin."\n\n'
    'Retry & DLQ:\n'
    '  Jika consumer gagal → Service Bus retry otomatis\n'
    '  Step [3][4] idempotent (upsert) → aman di-retry\n'
    '  Step [5] delete-then-reinsert → aman di-retry\n'
    '  Irrecoverable → Dead-Letter Queue → alert ops'
)

outbox_flow = (
    '// Dalam SATU DB transaction di DPlanDB:\n'
    '1. Resolve FormCode → maintenance-strategy.Form (IsActive=1) → FormName terbaru\n'
    '2. UPDATE PlanForm.FormName dengan nama terbaru\n'
    '3. UPDATE DigitalPlanning.Status = \'SUBMIT\'\n'
    '4. INSERT dbo.Outbox {\n'
    '     EventType = \'PlanSubmitted\',\n'
    '     Payload   = <PlanSubmitted JSON>,\n'
    '     Status    = \'Pending\'\n'
    '   }\n'
    '→ COMMIT (atomic)\n\n'
    '// Background relay job (dplan):\n'
    'LOOP:\n'
    '  rows = SELECT * FROM dbo.Outbox WHERE Status = \'Pending\'\n'
    '  FOR EACH row:\n'
    '    publish(row.Payload) → Azure Service Bus\n'
    '    UPDATE dbo.Outbox SET Status = \'Published\' WHERE Id = row.Id\n'
    '  IF publish gagal → log + retry pada iterasi berikutnya\n'
    '  // Jika DB COMMIT sukses, event PASTI eventually ter-publish'
)

desc_4266 = {
    'type': 'doc', 'version': 1, 'content': [
        h(2, 'Background'),
        p('Saat Planner submit plan dengan form package di Digiplan, sistem harus memproses form assignment ke maintenance-execution (create WorkOrder, Task, FormSubmission, Cosmos snapshot). Proses ini melibatkan 3 database lintas service, sehingga pendekatan synchronous HTTP call rentan terhadap partial failure yang sulit di-rollback.'),
        p('Tim setuju menggunakan Outbox Pattern + Azure Service Bus untuk menjamin atomicity dan resilience.'),

        h(2, 'Arsitektur: Outbox Pattern + Service Bus'),
        h(3, 'dplan — saat Planner submit plan (DRAFT → SUBMIT)'),
        ul(
            li('[0] Pre-SUBMIT Validation: cek ketersediaan setiap FormCode (lihat IAMS30-4369 untuk FE popup).'),
            li('[1] Resolve FormCode → maintenance-strategy.Form (IsActive=1) → FormName terbaru.'),
            li('[2] UPDATE PlanForm.FormName.'),
            li('[3] Dalam SATU DB transaction: UPDATE DigitalPlanning.Status = SUBMIT + INSERT ke Outbox table → COMMIT.'),
            li('[4] Background relay job: poll Outbox (Status=Pending) → publish PlanSubmitted event ke Azure Service Bus → mark Published.'),
        ),
        h(3, 'PlanSubmitted event payload'),
        cb(event_payload),
        p('Event hanya berisi data yang dplan tahu. FormId/FormName/Version dan asset detail di-resolve oleh consumer di maintenance-execution.'),
        h(3, 'maintenance-execution consumer'),
        cb(consumer_flow),

        h(2, 'Retry Policy (diterapkan di Service Bus subscription)'),
        table(
            table_row('Parameter', 'Value', 'Alasan', header=True),
            table_row('Max Delivery Count', '5', 'Cukup untuk transient failure. >5 biasanya indikasi bug permanen.'),
            table_row('Lock Duration', '5 menit', 'Cukup untuk 2 fetch + SQL upsert + Cosmos batch dalam satu attempt.'),
            table_row('Backoff', 'Exponential: 30s, 1m, 2m, 4m', 'Hindari hammer ke downstream service yang sedang recover.'),
            table_row('Dead-Letter Queue', 'Setelah attempt ke-5', 'Alert ke ops. Lebih baik cepat ke DLQ daripada mechanic menunggu berjam-jam.'),
        ),
        p('⚠️ Exponential backoff TIDAK tersedia native di Azure Service Bus Standard tier. Perlu Premium tier atau workaround via scheduled re-enqueue. Konfirmasi tier sebelum implementasi (lihat subtask IAMS30-TBD: Service Bus Tier Check).'),

        h(2, 'Perubahan dari desain sebelumnya'),
        ul(
            li('FormCode digunakan (bukan FormId + Version). Versi aktif di-resolve oleh consumer saat event diproses — bukan oleh FE saat Planner memilih form.'),
            li('IAMS30-4290 diupdate: DTO menggunakan FormCode + IsMandatory, bukan FormId + FormName + Version.'),
            li('IAMS30-4291 diupdate: handler dplan hanya menulis ke Outbox — tidak lagi memanggil MaintenanceExec API secara langsung.'),
            li('Consumer di maintenance-execution yang menangani seluruh downstream processing.'),
        ),

        h(2, 'Scope & Service'),
        ul(
            li('dplan: Outbox table DDL, relay job, handler update (Outbox write).'),
            li('maintenance-execution: Service Bus consumer, WorkOrder/Task/FormSubmission upsert, Cosmos snapshot.'),
            li('Azure Service Bus: topic/subscription setup, retry policy, DLQ.'),
        ),

        h(2, 'Acceptance Criteria'),
        ul(
            li('Plan SUBMIT selalu berhasil (status = SUBMIT di DPlanDB) bahkan jika maintenance-execution sedang down.'),
            li('PlanSubmitted event eventually di-publish ke Service Bus via relay job.'),
            li('Consumer memproses event: WorkOrder + Task + FormSubmission + Cosmos snapshot terbuat dengan benar.'),
            li('Step [3][4] consumer idempotent (upsert) — aman jika event diproses ulang.'),
            li('Step [5] consumer idempotent (delete-then-reinsert) — aman jika event diproses ulang.'),
            li('Jika consumer gagal 5x → masuk DLQ, alert ke ops.'),
            li('Edge case form archived: Task+FormSubmission terbuat, Cosmos snapshot skip, mechanic lihat "Form not available".'),
            li('packageSyncStatus = pending selama consumer belum selesai (lihat IAMS30-4372).'),
        ),
    ]
}

put('IAMS30-4266', {
    'fields': {
        'summary': '[BE] Form Package — Plan Submit: Outbox Pattern + PlanSubmitted Event → Azure Service Bus → maintenance-execution Consumer',
        'description': desc_4266,
    }
})

# ═══════════════════════════════════════════════════════════════════════════════
# 2. UPDATE IAMS30-4290 — DTO: FormCode bukan FormId
# ═══════════════════════════════════════════════════════════════════════════════
desc_4290 = {
    'type': 'doc', 'version': 1, 'content': [
        h(2, 'Context'),
        p('DTO untuk plan submit menggunakan FormCode (bukan FormId + Version). Planner tidak peduli versi — versi aktif di-resolve oleh consumer di maintenance-execution saat event diproses.'),
        h(2, 'Command / DTO — dplan side'),
        cb(
            'public class SubmitPlanCommand {\n'
            '  public Guid PlanId { get; set; }\n'
            '  // ... existing fields ...\n'
            '  public List<PlanFormItem> PlanForms { get; set; } = new();\n'
            '}\n\n'
            'public class PlanFormItem {\n'
            '  public string FormCode { get; set; }   // identitas form lintas versi\n'
            '  public bool IsMandatory { get; set; }  // ditentukan Planner\n'
            '}\n\n'
            '// Outbox event payload\n'
            'public class PlanSubmittedEvent {\n'
            '  public Guid PlanId { get; set; }\n'
            '  public string PlanName { get; set; }\n'
            '  public DateTime ProjectStart { get; set; }\n'
            '  public string SiteId { get; set; }\n'
            '  public string MaintenanceCategoryCode { get; set; }\n'
            '  public string MaintenanceCategoryName { get; set; }\n'
            '  public string AssetNumber { get; set; }\n'
            '  public List<PlanFormEventItem> PlanForms { get; set; }\n'
            '}\n\n'
            'public class PlanFormEventItem {\n'
            '  public string FormCode { get; set; }\n'
            '  public bool IsMandatory { get; set; }\n'
            '}'
        ),
        h(2, 'Acceptance Criteria'),
        ul(
            li('DTO menggunakan FormCode + IsMandatory (bukan FormId + FormName + Version).'),
            li('PlanSubmittedEvent payload sesuai struktur di atas.'),
            li('Unit test: DTO mapping dan event payload serialization.'),
        ),
    ]
}
put('IAMS30-4290', {'fields': {'summary': 'Update command/DTO: PlanForms menggunakan FormCode + IsMandatory (bukan FormId+Version)', 'description': desc_4290}})

# ═══════════════════════════════════════════════════════════════════════════════
# 3. UPDATE IAMS30-4291 — handler: tulis Outbox (bukan call MaintenanceExec API)
# ═══════════════════════════════════════════════════════════════════════════════
desc_4291 = {
    'type': 'doc', 'version': 1, 'content': [
        h(2, 'Context'),
        p('Handler plan submit di dplan tidak lagi memanggil MaintenanceExec HTTP API secara langsung. Sebagai gantinya, handler menulis ke Outbox table dalam satu DB transaction yang sama dengan SUBMIT status change. Relay job yang menangani publish ke Service Bus.'),
        h(2, 'Handler logic'),
        cb(outbox_flow),
        h(2, 'Perubahan dari desain sebelumnya'),
        ul(
            li('HAPUS: HTTP call ke maintenance-execution API.'),
            li('TAMBAH: INSERT ke dbo.Outbox dalam transaction yang sama dengan UPDATE DigitalPlanning.Status.'),
            li('Downstream processing (Task, FormSubmission, Cosmos) sepenuhnya ditangani oleh consumer di maintenance-execution — bukan di handler ini.'),
        ),
        h(2, 'Acceptance Criteria'),
        ul(
            li('Handler melakukan SUBMIT status change + Outbox INSERT dalam SATU DB transaction.'),
            li('Tidak ada HTTP call ke maintenance-execution dari handler ini.'),
            li('Jika transaction rollback (misal: FormCode tidak valid), Outbox entry tidak terbuat.'),
            li('Integration test: SUBMIT berhasil → Outbox entry terbuat dengan payload yang benar.'),
            li('Integration test: SUBMIT gagal (validasi) → Outbox entry tidak terbuat, status tidak berubah.'),
        ),
    ]
}
put('IAMS30-4291', {'fields': {'summary': 'Implement plan submit handler: write PlanSubmitted event ke Outbox table (dalam satu DB transaction dengan status SUBMIT)', 'description': desc_4291}})

# ═══════════════════════════════════════════════════════════════════════════════
# 4. UPDATE IAMS30-4292 — tests: update untuk async/Outbox behavior
# ═══════════════════════════════════════════════════════════════════════════════
desc_4292 = {
    'type': 'doc', 'version': 1, 'content': [
        h(2, 'Scope perubahan test'),
        p('Test suite untuk plan submit flow diupdate untuk mencerminkan arsitektur Outbox + Service Bus (bukan HTTP call ke MaintenanceExec).'),
        h(2, 'Test cases'),
        ul(
            li('Submit plan dengan forms: DigitalPlanning.Status = SUBMIT + Outbox entry terbuat dalam satu transaction.'),
            li('Submit plan tanpa forms (empty PlanForms): berhasil, Outbox entry tetap terbuat (consumer handle empty case).'),
            li('Outbox payload sesuai PlanSubmittedEvent schema (FormCode, bukan FormId).'),
            li('Transaction atomicity: jika Outbox INSERT gagal → DigitalPlanning.Status tidak berubah (rollback).'),
            li('Transaction atomicity: jika DigitalPlanning UPDATE gagal → Outbox tidak terbuat (rollback).'),
            li('Relay job: Outbox row dengan Status=Pending dipublish ke Service Bus → Status diupdate ke Published.'),
            li('Relay job: jika publish gagal → row tetap Pending, dicoba lagi pada iterasi berikutnya.'),
            li('Tidak ada HTTP call ke MaintenanceExec dalam test (mock harus dihapus/tidak dipakai).'),
            li('Regression: existing plan submit behavior (tanpa form package) tidak terganggu.'),
        ),
        h(2, 'Acceptance Criteria'),
        ul(
            li('Semua test cases di atas ada dan hijau.'),
            li('Tidak ada test yang mock HTTP call ke maintenance-execution.'),
            li('Coverage: happy path, partial failure, empty forms, relay job retry.'),
        ),
    ]
}
put('IAMS30-4292', {'fields': {'summary': 'Tests: plan submit Outbox atomicity, relay job publish/retry, payload schema, regression', 'description': desc_4292}})

# ═══════════════════════════════════════════════════════════════════════════════
# 5. SUBTASKS BARU di IAMS30-4266
# ═══════════════════════════════════════════════════════════════════════════════
new_subtasks = [
    {
        'summary': 'SSDT DDL: Create dbo.Outbox table in DPlanDB',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'File'),
                p('Database.iAMS.DPlan/dbo/Tables/Outbox.sql'),
                h(2, 'Schema'),
                cb(
                    'CREATE TABLE [dbo].[Outbox] (\n'
                    '  [Id]          UNIQUEIDENTIFIER NOT NULL DEFAULT NEWSEQUENTIALID(),\n'
                    '  [EventType]   NVARCHAR(100)    NOT NULL,  -- e.g. "PlanSubmitted"\n'
                    '  [Payload]     NVARCHAR(MAX)    NOT NULL,  -- JSON serialized event\n'
                    '  [Status]      NVARCHAR(20)     NOT NULL DEFAULT \'Pending\',\n'
                    '                                           -- "Pending" | "Published" | "Failed"\n'
                    '  [CreatedAt]   DATETIME         NOT NULL DEFAULT GETUTCDATE(),\n'
                    '  [PublishedAt] DATETIME         NULL,\n'
                    '  [Error]       NVARCHAR(MAX)    NULL,      -- last error message jika gagal\n'
                    '  CONSTRAINT [PK_Outbox] PRIMARY KEY CLUSTERED ([Id])\n'
                    ');\n\n'
                    '-- Index untuk relay job polling\n'
                    'CREATE INDEX [IX_Outbox_Status_CreatedAt]\n'
                    '  ON [dbo].[Outbox] ([Status], [CreatedAt]);'
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('Outbox table terbuat di DPlanDB dengan schema di atas.'),
                    li('Index IX_Outbox_Status_CreatedAt terbuat.'),
                    li('Deploy ke dev tanpa data loss.'),
                ),
            ]
        }
    },
    {
        'summary': 'Implement background relay job: poll dbo.Outbox → publish ke Azure Service Bus → mark Published',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Context'),
                p('Relay job adalah background service (hosted service / worker) di dplan yang secara periodik membaca Outbox rows dengan Status=Pending dan mempublishnya ke Azure Service Bus. Ini memastikan event eventually ter-publish meski ada transient failure saat SUBMIT.'),
                h(2, 'Logic'),
                cb(
                    '// Berjalan sebagai IHostedService atau BackgroundService di dplan\n'
                    'LOOP setiap N detik (configurable, default: 5s):\n'
                    '  pendingRows = SELECT TOP 10 * FROM dbo.Outbox\n'
                    '                WHERE Status = \'Pending\'\n'
                    '                ORDER BY CreatedAt ASC\n\n'
                    '  FOR EACH row:\n'
                    '    TRY:\n'
                    '      publish(topicName, row.EventType, row.Payload)\n'
                    '      UPDATE dbo.Outbox\n'
                    '        SET Status = \'Published\', PublishedAt = GETUTCDATE()\n'
                    '        WHERE Id = row.Id\n'
                    '    CATCH exception:\n'
                    '      UPDATE dbo.Outbox\n'
                    '        SET Error = exception.Message\n'
                    '        WHERE Id = row.Id\n'
                    '      // Status tetap "Pending" → dicoba lagi pada iterasi berikutnya\n'
                    '      log.Warning("Outbox relay failed for {row.Id}: {exception.Message}")'
                ),
                h(2, 'Configuration'),
                ul(
                    li('Topic name: configurable via appsettings (ServiceBus:PlanSubmittedTopic).'),
                    li('Poll interval: configurable (ServiceBus:RelayJobIntervalSeconds, default 5).'),
                    li('Batch size: configurable (ServiceBus:RelayJobBatchSize, default 10).'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('Relay job berjalan sebagai background service saat dplan startup.'),
                    li('Outbox row dengan Status=Pending dipublish ke Service Bus dan Status diupdate ke Published.'),
                    li('Jika publish gagal: Error field diupdate, Status tetap Pending, dicoba lagi.'),
                    li('Relay job tidak crash jika Service Bus tidak tersedia — log warning dan lanjutkan.'),
                    li('Unit test: publish berhasil → Published; publish gagal → tetap Pending + Error terupdate.'),
                ),
            ]
        }
    },
    {
        'summary': 'Service Bus: konfirmasi tier (Standard vs Premium), setup topic/subscription, implement retry policy + DLQ',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Context'),
                p('Retry policy yang disepakati membutuhkan exponential backoff. Azure Service Bus Standard tier TIDAK mendukung exponential backoff native — hanya tersedia di Premium tier atau via workaround (scheduled re-enqueue).'),
                h(2, 'Langkah 1: Konfirmasi tier Service Bus yang digunakan'),
                ul(
                    li('Cek Azure portal: tier yang aktif di environment dev, staging, dan production.'),
                    li('Jika Premium: gunakan built-in retry policy.'),
                    li('Jika Standard: implementasi exponential backoff via scheduled re-enqueue (lihat workaround di bawah).'),
                    li('Dokumentasikan keputusan di PR.'),
                ),
                h(2, 'Target retry policy'),
                table(
                    table_row('Parameter', 'Value', header=True),
                    table_row('Max Delivery Count', '5'),
                    table_row('Lock Duration', '5 menit'),
                    table_row('Backoff', 'Exponential: 30s, 1m, 2m, 4m'),
                    table_row('Dead-Letter Queue', 'Setelah attempt ke-5 → alert ops'),
                ),
                h(2, 'Workaround Standard tier: scheduled re-enqueue'),
                cb(
                    '// Jika Standard tier digunakan:\n'
                    '// Pada catch di consumer, hitung delay berdasarkan delivery count\n'
                    '// lalu schedule message kembali ke queue\n'
                    'int deliveryCount = message.DeliveryCount;\n'
                    'var delays = new[] { 30, 60, 120, 240 }; // detik\n'
                    'if (deliveryCount <= delays.Length) {\n'
                    '  var delay = TimeSpan.FromSeconds(delays[deliveryCount - 1]);\n'
                    '  await sender.ScheduleMessageAsync(message.Clone(), DateTimeOffset.UtcNow + delay);\n'
                    '  await receiver.CompleteMessageAsync(message); // complete original\n'
                    '} else {\n'
                    '  await receiver.DeadLetterMessageAsync(message, "MaxRetriesExceeded");\n'
                    '}'
                ),
                h(2, 'DLQ monitoring'),
                ul(
                    li('Setup alert (Azure Monitor / Application Insights) ketika DLQ message count > 0.'),
                    li('Alert target: ops channel (Slack/email/Teams — sesuai konfigurasi team).'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('Service Bus tier terdokumentasi di PR.'),
                    li('Topic dan subscription untuk PlanSubmitted event terbuat di semua environment.'),
                    li('Retry policy diterapkan (Max 5, Lock 5 menit, exponential backoff via native atau workaround).'),
                    li('Pesan yang gagal 5x masuk DLQ.'),
                    li('Alert terkonfigurasi untuk DLQ.'),
                ),
            ]
        }
    },
    {
        'summary': 'maintenance-execution: implement Service Bus consumer — upsert WorkOrder, Task, FormSubmission, Cosmos snapshot (idempotent)',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Context'),
                p('Consumer ini subscribe ke Service Bus topic PlanSubmitted dan melakukan seluruh downstream processing di maintenance-execution: create WorkOrder, Task, FormSubmission, dan copy Cosmos snapshot dari maintenance-strategy.'),
                h(2, 'Consumer flow'),
                cb(consumer_flow),
                h(2, 'Idempotency — kritis untuk retry safety'),
                ul(
                    li('WorkOrder: upsert by PlanId. Jika sudah ada, update fields — jangan duplikasi.'),
                    li('Task: upsert by PlanId + FormCode. Jika sudah ada, skip.'),
                    li('FormSubmission: upsert by TaskId. Jika sudah ada, skip.'),
                    li('Cosmos snapshot: DELETE existing docs (by FormSubmissionId) → INSERT fresh. Aman di-retry.'),
                ),
                h(2, 'Edge case: FormCode tidak ditemukan di maintenance-strategy'),
                ul(
                    li('Terjadi jika form di-archive setelah plan SUBMIT tapi sebelum consumer process.'),
                    li('Task + FormSubmission tetap dibuat menggunakan FormName dari event payload (fallback).'),
                    li('Cosmos snapshot TIDAK dibuat untuk form tersebut.'),
                    li('Mobile akan menampilkan "Form not available. Please contact your admin." untuk form card tersebut.'),
                    li('Consumer TIDAK throw exception untuk kasus ini — proses forms lain tetap berjalan.'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('Consumer subscribe dan process PlanSubmitted event dari Service Bus.'),
                    li('WorkOrder, Task, FormSubmission terbuat dengan field yang benar.'),
                    li('Cosmos snapshot terbuat per FormSubmission (per tab).'),
                    li('Semua step idempotent — consumer aman di-retry.'),
                    li('Edge case form archived: Task+FormSubmission terbuat, Cosmos skip, tidak throw exception.'),
                    li('Integration test: event diproses → semua records terbuat dengan benar.'),
                    li('Integration test: consumer menerima event duplikat (retry simulation) → tidak ada data ganda.'),
                    li('Integration test: FormCode tidak ditemukan → partial success (form lain tetap diproses).'),
                ),
            ]
        }
    },
]

print('\nCreating new subtasks for IAMS30-4266:')
for s in new_subtasks:
    create_subtask('IAMS30-4266', s['summary'], s['desc'])
