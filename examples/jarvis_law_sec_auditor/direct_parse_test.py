"""
Direct test of HTML Form 4 parsing - outputs to file
"""
from pathlib import Path
from bs4 import BeautifulSoup
import re
import json

test_file = Path("memory/sec_filings_archive/0000320187_4_2019-12-31_000112760219035995.xml")

print("Loading file...")
with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

soup = BeautifulSoup(content, 'html.parser')

print("Finding tables...")
tables = soup.find_all('table')
print(f"Found {len(tables)} tables")

# Find Table I
table1 = None
for table in tables:
    if 'Non-Derivative Securities' in table.get_text():
        table1 = table
        print("\nFound Table I (Non-Derivative)")
        break

if table1:
    rows = table1.find_all('tr')
    print(f"Table I has {len(rows)} rows")
    
    # Find data rows (skip headers)
    data_rows = []
    for i, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 8:  # Data rows have many cells
            cell_texts = [c.get_text(strip=True) for c in cells]
            # Skip if it's a header row
            if 'Transaction' not in cell_texts[0] and 'Title' not in cell_texts[0]:
                data_rows.append((i, cells, cell_texts))
    
    print(f"\nFound {len(data_rows)} data rows")
    
    # Parse each data row
    transactions = []
    for row_num, cells, cell_texts in data_rows:
        print(f"\n--- Row {row_num} ---")
        for j, text in enumerate(cell_texts[:11]):  # First 11 columns
            print(f"  Col {j}: [{text}]")
        
        # Parse transaction
        trans = {}
        
        # Col 0: Security
        if cell_texts[0]:
            trans['security'] = cell_texts[0]
        
        # Col 1: Date
        if cell_texts[1]:
            date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', cell_texts[1])
            if date_match:
                m, d, y = date_match.groups()
                trans['date'] = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        
        # Col 3: Code
        if len(cell_texts) > 3 and re.match(r'^[PSADXMFIGJ]$', cell_texts[3]):
            trans['code'] = cell_texts[3]
        
        # Col 5: Shares
        if len(cell_texts) > 5:
            shares = cell_texts[5].replace(',', '')
            if re.match(r'^\d+\.?\d*$', shares):
                trans['shares'] = shares
        
        # Col 6: A/D
        if len(cell_texts) > 6 and cell_texts[6] in ['A', 'D']:
            trans['acq_disp'] = cell_texts[6]
        
        # Col 7: Price
        if len(cell_texts) > 7:
            price = re.sub(r'[^\d.]', '', cell_texts[7])
            if price and re.match(r'^\d+\.?\d*$', price):
                trans['price'] = price
        
        # Col 8: Shares After
        if len(cell_texts) > 8:
            shares_after = cell_texts[8].replace(',', '')
            if re.match(r'^\d+\.?\d*$', shares_after):
                trans['shares_after'] = shares_after
        
        # Col 9: D/I
        if len(cell_texts) > 9 and cell_texts[9] in ['D', 'I']:
            trans['direct_indirect'] = cell_texts[9]
        
        transactions.append(trans)
        print(f"  Parsed: {trans}")
    
    # Save to file
    output = {
        'file': test_file.name,
        'table1_rows': len(data_rows),
        'transactions': transactions
    }
    
    output_file = Path("memory/calibration_runs/direct_parse_test.json")
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n\nSaved to: {output_file}")
    print(f"Extracted {len(transactions)} transactions")

else:
    print("ERROR: Could not find Table I")

