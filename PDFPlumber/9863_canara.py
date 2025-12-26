import pdfplumber
import pandas as pd
import time
import sys
import os

start_time = time.time()

file_path = "pdf/9863 DR-CR Issue Canara Bank (1).pdf"
file_name = os.path.splitext(os.path.basename(file_path))[0] 

output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

TOTAL_TEXT = []
Date = []
Desc = []
Amount = []
Type = []
Cheque_No = []

with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        table = page.extract_table()
        if table:
            TOTAL_TEXT.extend(table)
        page.flush_cache()

# print(TOTAL_TEXT)

for line in TOTAL_TEXT:
    if not line or len(line) < 4:
        continue
        
    raw_date = line[1]
    
    if raw_date is None:
        continue

    raw_date = str(raw_date).replace('/', '-').replace('—', '-').strip()
    
    if not raw_date[:1].isdigit():
        continue

    formatted_date = raw_date 
    parts = raw_date.split('-')
    
    if len(parts) == 3:
        if parts[1].isalpha():
            months = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08', 
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            m = months.get(parts[1].lower())
            if m:
                year = parts[2]
                if len(year) == 2:
                    year = '20' + year
                formatted_date = f"{parts[0]}-{m}-{year}"
            else:
                continue

    debit_val = line[-3] if line[-3] is not None else "0.00"
    credit_val = line[-2] if line[-2] is not None else "0.00"
    
    narration = line[2].replace('\n', ' ') if line[2] else ""
    cheque_num = "" 
    
    clean_debit = str(debit_val).replace(',', '').strip()
    if clean_debit != '0.00' and clean_debit != '0' and clean_debit != '':
        Date.append(formatted_date)
        Desc.append(narration)
        Amount.append(clean_debit)
        Type.append("Dr")
        Cheque_No.append(cheque_num)

    clean_credit = str(credit_val).replace(',', '').strip()
    if clean_credit != '0.00' and clean_credit != '0' and clean_credit != '':
        Date.append(formatted_date)
        Desc.append(narration)
        Amount.append(clean_credit)
        Type.append("Cr")
        Cheque_No.append(cheque_num)

if len(Date) > 0:
    data_dict = {
        "Date": Date, 
        "Description": Desc,
        "ChequeNo": Cheque_No, 
        "Amount": Amount, 
        "Type": Type,
    }
    df = pd.DataFrame(data_dict)
    output_csv = os.path.join(output_dir, f"{file_name}.csv")
    df.to_csv(output_csv, index=False, header=True)

    end_time = time.time()  
    execution_time = end_time - start_time

    print(f"\nExtracted transactions: {len(Date)}")
    print(f"Execution Time: {execution_time:.2f} seconds")
    print(f"Saved to {output_csv}")
    print("\n", df)