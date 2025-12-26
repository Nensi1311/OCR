import pdfplumber
import pandas as pd
import time
import sys
import os

start_time = time.time()

file_path = "pdf/9682 Wrong Data Fetching DCB Bank (1).pdf"
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
    if not line:
        continue
    
    col0 = line[0] if len(line) > 0 else ""
    col1 = line[1] if len(line) > 1 else ""
    if(col0 is None or str(col0).strip() == "") and (col1 and "Closing Balance" in str(col1)):
        break

    raw_date = line[0] if len(line) > 0 else None

    if raw_date and str(raw_date).replace('/', '').replace('-', '').strip().isdigit():
       
        formatted_date = str(raw_date).replace('/', '-').strip()
        narration = line[1].replace('\n', ' ') if (len(line) > 1 and line[1]) else ""
        
        debit_val = line[3] if (len(line) > 3 and line[3]) else "0.00"
        credit_val = line[4] if (len(line) > 4 and line[4]) else "0.00"
        
        cheque_num = line[2].strip() if (len(line) > 2 and line[2]) else ""

        clean_debit = str(debit_val).strip()
        clean_credit = str(credit_val).strip()

        if clean_debit != '0.00' and clean_debit != '0' and clean_debit != '':
            Date.append(formatted_date)
            Desc.append(narration)
            Amount.append(clean_debit)
            Type.append("Dr")
            Cheque_No.append(cheque_num)

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

    print(f"Extracted transactions: {len(Date)}")
    print(f"Execution Time: {execution_time:.2f} seconds")
    print(f"Saved to {output_csv}")
    print("\n", df)