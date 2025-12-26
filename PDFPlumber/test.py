import pdfplumber
import os.path
import time
from datetime import datetime
import shutil
import pandas as pd
import csv
import re
from tempfile import TemporaryFile
import collections

import sys
ACCPTED_DOCUMENT_MOVE_PATH = sys.argv[1]
# ACCPTED_DOCUMENT_MOVE_PATH = r"ACCEPTED_DOCUMENT/"

with open('{}FILE NAME.txt'.format(ACCPTED_DOCUMENT_MOVE_PATH), 'r') as file:
    data = file.read()

file = data
file_name = file[:-4]

TOTAL_TEXT = []

Date = []
Desc = []
Amount = []
Type = []
Cheque_No = []

with pdfplumber.open(file) as read_invoice_pdf:
    pages = read_invoice_pdf.pages
    for page in pages:
        invoice_pdf_table = page.extract_table()
        if invoice_pdf_table is not None:
            TOTAL_TEXT = TOTAL_TEXT + invoice_pdf_table
# Clear the cache for the page to free up memory crucial for large PDFs or pdfplumber itslef not releasing memory
# This is a workaround for memory issues with pdfplumber
page.flush_cache()
del page

print(TOTAL_TEXT)

for line in TOTAL_TEXT:
    date = line[1]
    if date[:11][3:6].isalpha():
        date = date[:11].replace('/','-').replace('-','-').replace('—','-')
    else:
        date = date[:10].replace('/','-').replace('-','-').replace('—','-')

# Convert alpha month if present
months = {
'jan':'01','feb':'02','mar':'03','apr':'04','may':'05','jun':'06',
'jul':'07','aug':'08','sep':'09','oct':'10','nov':'11','dec':'12'
}

parts = date.split('-')
# print(parts)

if len(parts) == 3 and parts[2].isdigit()==True and len(parts[2])==2:
    parts[2] = '20' + parts[2]

if len(parts) == 3 and parts[1].isalpha():
    month = months.get(parts[1].lower(), parts[1])
    date = f"{parts[0]}-{month}-{parts[2]}"

if ('-' in date or '/' in date) and date.replace('-','').replace('/','').isdigit()==True:
    Date.append(date)
    Desc.append(line[2])
    if line[-3] != '0.00' and line[-3] != '0.0':
        Type.append('debit')
        Amount.append(line[-3].replace(',','').replace('\n','').replace(' ',''))
    if line[-2] != '0.00' and line[-2] != '0.0':
        Type.append('credit')
        Amount.append(line[-2].replace(',','').replace('\n','').replace(' ',''))

print(Date,Desc,Amount,Type,Cheque_No)

print("Date :",len(Date))
print("Desc :", len(Desc))
print("Amount :",len(Amount))
print("Type :",len(Type))
print("Cheque_No :",len(Cheque_No))

NO_CSV = []
# print(Date)
for date in Date:
    if (len(date)!=10) :
        print(date)
        NO_CSV.append(0)

if len(Type) <1:
    NO_CSV.append(2)
if len(Desc) <1:
    NO_CSV.append(3)

# print("NO_CSV :",NO_CSV)


if len(NO_CSV) < 1:
    data = {"Date": Date, "Description": Desc, "Amount": Amount, "Type": Type}
    df = pd.DataFrame(data)
    df.to_excel(f"{file_name}.xlsx", index=False)
    df.to_csv(f"{file_name}.csv", index=False, header=True)