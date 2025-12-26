import pdfplumber
import pandas as pd
import re
import sys
import os

# ACCPTED_DOCUMENT_MOVE_PATH = sys.argv[1]
# with open('{}FILE NAME.txt'.format(ACCPTED_DOCUMENT_MOVE_PATH), 'r') as file:
#     data = file.read().strip()

file_path = "pdf/9778 Canara Mobile Bank Narration Issue (1).pdf"
file_name = file_path[:-4] 

output_dir = "output"
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

date_pattern = re.compile(r'^\s*(\d{2}-\d{2}-\d{4})')
amount_pattern = re.compile(r'(-?[\d,]+\.\d{2})')

transactions = []
current_txn = None
ignore_narration = False 
previous_balance = 0.0

with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
            
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "Closing Balance" in line:
                ignore_narration = True
                continue

            if "Opening Balance" in line:
                bals = amount_pattern.findall(line)
                if bals:
                    try:
                        previous_balance = float(bals[-1].replace(',', ''))
                    except:
                        pass
                continue

            date_match = date_pattern.match(line)
            
            if date_match:
                ignore_narration = False 
                
                if current_txn:
                    transactions.append(current_txn)
        
                date_str = date_match.group(1)
   
                amounts = amount_pattern.findall(line)
                
                txn_amount = "0.00"
                txn_type = "Dr" 
                current_balance = 0.0
                
                if len(amounts) >= 1:
                    if len(amounts) >= 2:
                        amt_str = amounts[-2]
                        bal_str = amounts[-1]
                    else:
                        amt_str = amounts[0]
                        bal_str = "0.00"

                    try:
                        val_amount = float(amt_str.replace(',', ''))
                        current_balance = float(bal_str.replace(',', ''))
                        
                        if current_balance > previous_balance:
                            txn_type = "Cr"
                        elif current_balance < previous_balance:
                            txn_type = "Dr"
                        else:
                            if "UPI/CR" in line or "NEFT CR" in line or "DEPOSIT" in line:
                                txn_type = "Cr"
                            else:
                                txn_type = "Dr"

                        txn_amount = str(val_amount) 
                        previous_balance = current_balance 
                    except ValueError:
                        pass
                
                amt_match = amount_pattern.search(line)
                
                raw_middle_text = ""
                if amt_match:
                    amount_start_index = amt_match.start()
                    raw_middle_text = line[10:amount_start_index].strip()
                else:
                    raw_middle_text = line[10:].strip()

                narration_part = raw_middle_text
                
                current_txn = {
                    "Date": date_str,
                    "Description": narration_part,
                    "Amount": txn_amount,
                    "Type": txn_type,
                    # "ChequeNo": "" 
                }
                
            else:
                if current_txn and not ignore_narration:
                    current_txn["Description"] += " " + line

if current_txn:
    transactions.append(current_txn)

print(f"Extracted: {len(transactions)} transactions")

if len(transactions) > 0:
    df = pd.DataFrame(transactions)
    output_csv = os.path.join(output_dir,f"{file_name}.csv")
    df.to_csv(output_csv, index=False, header=True)
    print(f"Saved to {output_csv}")
    print(df)