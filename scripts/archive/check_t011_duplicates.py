"""Check if T011 still has duplicate periods"""
import json

data = json.load(open('real_timetable.json', encoding='utf-8'))
t011_mon = [e for e in data if e['teacher_id'] == 'T011' and e['day_id'] == 'Mon']
t011_mon.sort(key=lambda x: x['period_id'])

print(f'T011 Monday entries: {len(t011_mon)}')
print()

for e in t011_mon:
    print(f"Period {e['period_id']}: {e['subject_id']:15s} | Class: {e['class_id']}")

periods = [e['period_id'] for e in t011_mon]
print(f'\nPeriods: {sorted(periods)}')

has_duplicates = len(periods) != len(set(periods))
print(f'Duplicates: {"YES" if has_duplicates else "NO"}')

if not has_duplicates:
    print('\n[SUCCESS] T011 has no duplicate periods!')
else:
    print('\n[WARNING] T011 still has duplicate periods')
