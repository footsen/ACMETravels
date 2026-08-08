import csv
import json

input_file = 'ACME Travels.csv'
output_file = 'acme-travels.json'

data = []

with open(input_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    print("Headers:", reader.fieldnames)  # Debug: see exact header names

    for row in reader:
        entry = {
            'code': row.get('Code', '').strip(),
            'name': row.get('Name', '').strip(),
            'status': row.get('Status', '').strip(),
            'chris': row.get('Chris', '').strip().upper() == 'Y',
            'maggie': row.get('Maggie', '').strip().upper() == 'Y',
            'allyson': row.get('Allyson', '').strip().upper() == 'Y',
            'edward': row.get('Edward', '').strip().upper() == 'Y'
        }
        data.append(entry)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Converted {len(data)} entries. Check {output_file} for Curaçao / accented names.")
