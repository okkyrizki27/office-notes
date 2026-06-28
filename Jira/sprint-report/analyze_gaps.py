# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('all_tickets.json', encoding='utf-8') as fp:
    tickets = json.load(fp)

# Print each ticket + subtask summary for review
for t in tickets:
    print(f'\n{"="*70}')
    print(f'[{t["key"]}] {t["summary"]}')
    print(f'TYPE: {t["type"]} | STATUS: {t["status"]}')
    print(f'DESC ({len(t["desc"])} chars):')
    print(t["desc"][:600] if t["desc"] else '(EMPTY)')
    for s in t['subtasks']:
        print(f'\n  >> [{s["key"]}] {s["summary"]}')
        print(f'     DESC ({len(s["desc"])} chars):')
        print('     ' + (s["desc"][:400] if s["desc"] else '(EMPTY)'))
