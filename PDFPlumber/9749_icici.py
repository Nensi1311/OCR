import pdfplumber
import pandas as pd
import time
import re
import os

start_time = time.time()

file_path = "pdf/9749 Wrong Process 2 (1).pdf"
file_name = os.path.splitext(os.path.basename(file_path))[0]

output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

DATE_RE = re.compile(r'\d{2}-\d{2}-\d{4}')
AMOUNT_RE = re.compile(r'-?[\d,]+\.\d{2}')

COL_DATE = (20, 70)
COL_CHQ = (70, 125)
COL_PARTICULARS = (130, 335)
COL_DEPOSIT = (370, 440)
COL_WITHDRAW = (450, 500)

transactions = []
current_txn = None
narration_words = []
chq_words = []

with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        words = page.extract_words(use_text_flow=True)

        for w in words:
            text = w["text"].strip()
            x0 = w["x0"]

            if not text:
                continue

            if COL_DATE[0] <= x0 <= COL_DATE[1] and DATE_RE.fullmatch(text):

                if current_txn:
                    current_txn["Description"] = " ".join(narration_words).strip()
                    current_txn["Cheque_No"] = " ".join(chq_words).strip()
                    transactions.append(current_txn)

                narration_words = []
                chq_words = []

                current_txn = {
                    "Date": text,
                    "Cheque_No": "",
                    "Description": "",
                    "Amount": 0.0,
                    "Type": ""
                }

            elif COL_CHQ[0] <= x0 <= COL_CHQ[1]:
                chq_words.append(text)

            elif COL_PARTICULARS[0] <= x0 <= COL_PARTICULARS[1]:
                narration_words.append(text)

            elif COL_DEPOSIT[0] <= x0 <= COL_DEPOSIT[1] and AMOUNT_RE.fullmatch(text):
                if current_txn:
                    current_txn["Amount"] = float(text.replace(',', ''))
                    current_txn["Type"] = "Cr"

            elif COL_WITHDRAW[0] <= x0 <= COL_WITHDRAW[1] and AMOUNT_RE.fullmatch(text):
                if current_txn:
                    current_txn["Amount"] = float(text.replace(',', ''))
                    current_txn["Type"] = "Dr"

if current_txn:
    current_txn["Description"] = " ".join(narration_words).strip()
    current_txn["Cheque_No"] = " ".join(chq_words).strip()
    transactions.append(current_txn)

df = pd.DataFrame(transactions)
output_csv = os.path.join(output_dir, f"{file_name}.csv")
df.to_csv(output_csv, index=False)

end_time = time.time()   
execution_time = end_time - start_time

print(f"\nExtracted transactions: {len(df)}")
print(f"Execution time: {execution_time:.2f} seconds")
print(f"Saved to {output_csv}")
print("\n", df)