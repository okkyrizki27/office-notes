# -*- coding: utf-8 -*-
import json, os, urllib.request, base64, sys
sys.stdout.reconfigure(encoding='utf-8')

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
        print(f'  Created: {result["key"]} -- {summary[:70]}')
    except urllib.error.HTTPError as e:
        print(f'  Error: {e.code}', e.read().decode()[:200])

consumer_flow = (
    '// maintenance-execution Service Bus consumer:\n'
    '[1] Fetch cst-iams-sqldb-services-asset:\n'
    '      AssetModelCode, AssetModelName, SectionTypeCode\n'
    '      berdasarkan AssetNumber dari event\n\n'
    '[2] Per FormCode dalam PlanForms:\n'
    '      Fetch maintenance-strategy: FormId, FormName, Version\n'
    '      (IsActive=1, ambil versi aktif)\n\n'
    '[3] SQL upsert WorkOrder (idempotent by PlanId)\n\n'
    '[4] SQL upsert Task + FormSubmission (idempotent by PlanId + FormCode)\n\n'
    '[5] Per FormSubmission -- Cosmos snapshot:\n'
    '      DELETE existing docs (safety for retry)\n'
    '      Cosmos Transactional Batch (partition: FormSubmissionId):\n'
    '        INSERT tab1_doc, tab2_doc, ... (all-or-nothing)\n\n'
    'Edge case -- Form di-archive SETELAH SUBMIT tapi SEBELUM consumer process:\n'
    '  Task + FormSubmission tetap dibuat (FormName dari event payload sebagai fallback)\n'
    '  Cosmos snapshot TIDAK dibuat\n'
    '  Mobile tampilkan "Form not available. Please contact your admin."\n\n'
    'Jika consumer gagal -> Service Bus retry\n'
    'Step [3][4] idempotent (upsert) -> aman di-retry\n'
    'Step [5] delete-then-reinsert -> aman di-retry\n'
    'Irrecoverable -> Dead-Letter Queue -> alert ops'
)

subtasks = [
    {
        'summary': 'Relay job: poll dbo.Outbox (Pending) -> publish ke Azure Service Bus -> mark Published',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Context'),
                p('Relay job adalah background service (IHostedService/BackgroundService) di dplan yang secara periodik membaca Outbox rows Status=Pending dan mempublishnya ke Azure Service Bus.'),
                h(2, 'Logic'),
                cb(
                    '// Berjalan sebagai BackgroundService di dplan\n'
                    'LOOP setiap N detik (default: 5s, configurable):\n'
                    '  pendingRows = SELECT TOP 10 * FROM dbo.Outbox\n'
                    '                WHERE Status = \'Pending\'\n'
                    '                ORDER BY CreatedAt ASC\n\n'
                    '  FOR EACH row:\n'
                    '    TRY:\n'
                    '      await serviceBus.PublishAsync(row.EventType, row.Payload)\n'
                    '      UPDATE dbo.Outbox\n'
                    '        SET Status=\'Published\', PublishedAt=GETUTCDATE()\n'
                    '        WHERE Id = row.Id\n'
                    '    CATCH exception:\n'
                    '      UPDATE dbo.Outbox SET Error=exception.Message WHERE Id=row.Id\n'
                    '      // Status tetap Pending -- retry iterasi berikutnya\n'
                    '      log.Warning("Relay failed for {row.Id}: {exception.Message}")'
                ),
                h(2, 'Configuration (appsettings)'),
                ul(
                    li('ServiceBus:PlanSubmittedTopic -- nama topic'),
                    li('ServiceBus:RelayJobIntervalSeconds -- default 5'),
                    li('ServiceBus:RelayJobBatchSize -- default 10'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('Relay job berjalan sebagai background service saat dplan startup.'),
                    li('Outbox Status=Pending dipublish ke Service Bus dan Status diupdate ke Published.'),
                    li('Jika publish gagal: Error field diupdate, Status tetap Pending, dicoba lagi iterasi berikutnya.'),
                    li('Relay job tidak crash jika Service Bus tidak tersedia -- log warning dan lanjutkan.'),
                    li('Unit test: publish berhasil -> Published; publish gagal -> tetap Pending + Error terupdate.'),
                ),
            ]
        }
    },
    {
        'summary': 'Service Bus setup: konfirmasi tier, topic/subscription, retry policy (Max 5, Lock 5min, exponential), DLQ alert',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Konteks penting'),
                p('Exponential backoff TIDAK tersedia native di Azure Service Bus Standard tier. Perlu konfirmasi tier sebelum implementasi.'),
                h(2, 'Langkah 1: Konfirmasi tier'),
                ul(
                    li('Cek Azure portal: tier aktif di dev, staging, dan production.'),
                    li('Premium tier: gunakan built-in retry dengan exponential backoff.'),
                    li('Standard tier: implementasi workaround via scheduled re-enqueue (lihat kode di bawah).'),
                    li('Dokumentasikan keputusan di PR.'),
                ),
                h(2, 'Target retry policy'),
                table(
                    table_row('Parameter', 'Value', header=True),
                    table_row('Max Delivery Count', '5'),
                    table_row('Lock Duration', '5 menit'),
                    table_row('Backoff', 'Exponential: 30s, 1m, 2m, 4m'),
                    table_row('DLQ', 'Setelah attempt ke-5, alert ke ops'),
                ),
                h(2, 'Workaround Standard tier: scheduled re-enqueue'),
                cb(
                    'var delays = new[] { 30, 60, 120, 240 }; // detik\n'
                    'int deliveryCount = args.Message.DeliveryCount;\n'
                    'if (deliveryCount < delays.Length) {\n'
                    '  var delay = TimeSpan.FromSeconds(delays[deliveryCount - 1]);\n'
                    '  await sender.ScheduleMessageAsync(args.Message.Clone(),\n'
                    '    DateTimeOffset.UtcNow + delay);\n'
                    '  await args.CompleteMessageAsync(args.Message);\n'
                    '} else {\n'
                    '  await args.DeadLetterMessageAsync(args.Message, "MaxRetriesExceeded");\n'
                    '}'
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('Tier Service Bus terdokumentasi di PR.'),
                    li('Topic dan subscription PlanSubmitted terbuat di semua environment.'),
                    li('Retry policy diterapkan (Max 5, Lock 5 menit, exponential via native atau workaround).'),
                    li('Pesan gagal 5x masuk DLQ.'),
                    li('Alert terkonfigurasi ketika DLQ message count > 0.'),
                ),
            ]
        }
    },
    {
        'summary': 'maintenance-execution: Service Bus consumer -- upsert WorkOrder, Task, FormSubmission, Cosmos snapshot (idempotent)',
        'desc': {
            'type': 'doc', 'version': 1, 'content': [
                h(2, 'Context'),
                p('Consumer subscribe ke PlanSubmitted event dan menangani seluruh downstream processing di maintenance-execution. Semua step harus idempotent karena consumer bisa dipanggil ulang oleh Service Bus retry.'),
                h(2, 'Consumer flow'),
                cb(consumer_flow),
                h(2, 'Idempotency rules'),
                ul(
                    li('WorkOrder: upsert by PlanId -- jika sudah ada, update fields, jangan duplikasi.'),
                    li('Task: upsert by PlanId + FormCode -- jika sudah ada, skip.'),
                    li('FormSubmission: upsert by TaskId -- jika sudah ada, skip.'),
                    li('Cosmos: DELETE existing docs by FormSubmissionId, lalu INSERT fresh. Aman di-retry.'),
                ),
                h(2, 'Edge case: FormCode tidak ditemukan di maintenance-strategy'),
                ul(
                    li('Terjadi jika form di-archive setelah plan SUBMIT tapi sebelum consumer process.'),
                    li('Task + FormSubmission tetap dibuat, FormName diambil dari event payload (fallback).'),
                    li('Cosmos snapshot TIDAK dibuat untuk form tersebut.'),
                    li('Consumer TIDAK throw exception -- form lain dalam event tetap diproses.'),
                ),
                h(2, 'Acceptance Criteria'),
                ul(
                    li('Consumer subscribe dan process PlanSubmitted event.'),
                    li('WorkOrder, Task, FormSubmission terbuat dengan field yang benar.'),
                    li('Cosmos snapshot terbuat per FormSubmission (per tab).'),
                    li('Semua step idempotent -- event duplikat tidak menghasilkan data ganda.'),
                    li('Edge case form archived: Task+FormSubmission terbuat, Cosmos skip, tidak throw.'),
                    li('Integration test: event diproses -> semua records terbuat.'),
                    li('Integration test: event duplikat -> tidak ada data ganda.'),
                    li('Integration test: FormCode tidak ditemukan -> partial success, form lain tetap diproses.'),
                ),
            ]
        }
    },
]

print('Creating remaining subtasks for IAMS30-4266:')
for s in subtasks:
    create_subtask('IAMS30-4266', s['summary'], s['desc'])
