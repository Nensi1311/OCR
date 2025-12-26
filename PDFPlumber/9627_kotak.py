import pdfplumber
import pandas as pd
import time
import re
import os

start_time = time.time()

file_path = "pdf/9627 bank narration mismatch (1).pdf"
file_name = os.path.splitext(os.path.basename(file_path))[0]

output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

COL_DATE_DAY = (75, 85)
COL_DATE_MON = (85, 100)
COL_DATE_YEAR = (100, 120)
COL_DESC = (140, 280)
COL_CHQ = (285, 340)
COL_DEBIT = (350, 410)
COL_CREDIT = (410, 465)

DAY_RE = re.compile(r'^\d{1,2}$')
YEAR_RE = re.compile(r'^\d{4}$')
AMOUNT_RE = re.compile(r'[+-]?[\d,]+\.\d{2}')

transactions = []
current_txn = None

date_parts = []
desc_words = []
chq_words = []

with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        words = page.extract_words(use_text_flow=True)
        # print(words)
        for w in words:
            text = w["text"].strip()
            x0 = w["x0"]

            if not text:
                continue

            if COL_DATE_DAY[0] <= x0 <= COL_DATE_DAY[1] and DAY_RE.fullmatch(text):
                date_parts = [text]

            elif COL_DATE_MON[0] <= x0 <= COL_DATE_MON[1] and text.isalpha():
                if len(date_parts) == 1:
                    date_parts.append(text.upper())

            elif COL_DATE_YEAR[0] <= x0 <= COL_DATE_YEAR[1] and YEAR_RE.fullmatch(text):
                if len(date_parts) == 2:
                    date_parts.append(text)

                    raw_date = " ".join(date_parts)

                    if current_txn:
                        current_txn["Description"] = " ".join(desc_words).strip()
                        current_txn["ChQ_No"] = " ".join(chq_words).strip()
                        transactions.append(current_txn)

                    current_txn = {
                        "Date": raw_date,
                        "Description": "",
                        "ChQ_No": "",
                        "Amount": 0.00,
                        "Type": ""
                    }

                    desc_words = []
                    chq_words = []
                    date_parts = []

            elif COL_DESC[0] <= x0 <= COL_DESC[1]:
                if current_txn:
                    desc_words.append(text)

            elif COL_CHQ[0] <= x0 <= COL_CHQ[1]:
                if current_txn:
                    chq_words.append(text)

            elif COL_DEBIT[0] <= x0 <= COL_DEBIT[1] and AMOUNT_RE.fullmatch(text):
                if current_txn:
                    current_txn["Amount"] = float(text.replace(',', ''))
                    current_txn["Type"] = "Dr"

            elif COL_CREDIT[0] <= x0 <= COL_CREDIT[1] and AMOUNT_RE.fullmatch(text):
                if current_txn:
                    current_txn["Amount"] = float(text.replace(',', ''))
                    current_txn["Type"] = "Cr"

if current_txn:
    current_txn["Description"] = " ".join(desc_words).strip()
    current_txn["ChQ_No"] = " ".join(chq_words).strip()
    transactions.append(current_txn)

df = pd.DataFrame(transactions)

output_csv = os.path.join(output_dir, f"{file_name}.csv")
df.to_csv(output_csv, index=False)

end_time = time.time()   
execution_time = end_time - start_time

print(f"\nExtracted transactions: {len(df)}")
print(f"Execution Time: {execution_time:.2f} seconds")
print(f"Saved to {output_csv}")
print("\n", df)