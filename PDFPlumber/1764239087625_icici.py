import pdfplumber
import pandas as pd
import time
import os
import re

start_time = time.time()

file_path = "pdf/1764239087625 BANK STATEMENT OCT 2025.pdf"
file_name = os.path.splitext(os.path.basename(file_path))[0]

output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

Date = []
Desc = []
Amount = []
Type = []
Cheque_No = []

DATE_RE = re.compile(r'^\d{2}[-/]\d{2}[-/]\d{4}$')

with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        if not tables:
            continue

        for table in tables:
            for line in table:

                if not line or len(line) < 9:
                    continue

                line = [cell.strip() if cell else "" for cell in line]

                raw_date = line[2]

                if not raw_date or not DATE_RE.match(raw_date.strip()):
                    continue

                formatted_date = raw_date.replace('/', '-')
                cheque_num = line[4]
                narration = line[5].replace('\n', ' ')
                txn_type = line[6]
                amount = line[7].replace(',', '')

                if txn_type not in ("CR", "DR") or amount == "":
                    continue

                Date.append(formatted_date)
                Desc.append(narration)
                Cheque_No.append(cheque_num)
                Amount.append(amount)
                Type.append("Cr" if txn_type == "CR" else "Dr")

df = pd.DataFrame({
        "Date": Date,
        "Description": Desc,
        "Cheque No": Cheque_No,
        "Amount": Amount,
        "Type": Type
    })

output_csv = os.path.join(output_dir, f"{file_name}.csv")
df.to_csv(output_csv, index=False, header=True)

end_time = time.time()   
execution_time = end_time - start_time

print(f"\nExtracted transactions: {len(Date)}")
print(f"Execution Time: {execution_time:.2f} seconds")
print(f"Saved to {output_csv}")
print("\n", df)