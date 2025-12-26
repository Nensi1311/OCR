import pdfplumber
import pandas as pd
import time
import re
import os

start_time = time.time()

file_path = "pdf/9821 only one entry is being fecthed (2).pdf"
file_name = os.path.splitext(os.path.basename(file_path))[0]

output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

DATE_RE = re.compile(r"\d{2}-\d{2}-\d{4}")
AMOUNT_RE = re.compile(r"[\d,]+\.\d{2}\((Cr|Dr)\)")

COL_DATE = (20, 80)
COL_PARTICULARS = (80, 270)
COL_CHQ = (270, 380)
COL_AMOUNT = (380, 480)

transactions = []
current_txn = None
narration_words = []
chq_words = []

stop_parsing = False
prev_text = ""

with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        words = page.extract_words(use_text_flow=True)
        # print(words)
        for w in words:
            text = w["text"].strip()
            x0 = w["x0"]

            if not text:
                continue

            if prev_text.lower() == "statement" and text.lower() == "summary":
                stop_parsing = True
                
                if narration_words and narration_words[-1].lower() == "statement":
                    narration_words.pop()
                break

            prev_text = text

            if COL_DATE[0] <= x0 <= COL_DATE[1] and DATE_RE.fullmatch(text):

                if current_txn:
                    current_txn["Description"] = " ".join(narration_words).strip()
                    current_txn["Cheque_No"] = " ".join(chq_words).strip()
                    transactions.append(current_txn)

                narration_words = []
                chq_words = []

                current_txn = {
                    "Date": text,
                    "Description": "",
                    "Cheque_No": "",
                    "Amount": "",
                    "Type": ""
                }

            elif COL_PARTICULARS[0] <= x0 <= COL_PARTICULARS[1]:
                if current_txn:
                    narration_words.append(text)

            elif COL_CHQ[0] <= x0 <= COL_CHQ[1]:
                if current_txn:
                    chq_words.append(text)

            elif COL_AMOUNT[0] <= x0 <= COL_AMOUNT[1] and AMOUNT_RE.fullmatch(text):
                if current_txn:
                    amt = text.replace(",", "")
                    current_txn["Amount"] = float(amt[:-4])
                    current_txn["Type"] = "Cr" if "Cr" in text else "Dr"
        
        if stop_parsing:
            break

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