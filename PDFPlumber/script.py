import pdfplumber
import os.path
import time
import PyPDF2
import xlsxwriter
from datetime import datetime
import shutil
import pandas as pd
import xlrd
import csv 
import re
from tempfile import TemporaryFile
import collections

import sys
ACCPTED_DOCUMENT_MOVE_PATH = sys.argv[1]

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
        # invoice_words_list = page.extract_words()
        # if invoice_words_list is not None:
        #     TOTAL_TEXT = TOTAL_TEXT + invoice_words_list

        # text_content = page.extract_text()
        # if text_content is not None:
        #     lines = text_content.split('\n')
        #     TOTAL_TEXT = TOTAL_TEXT + lines

        # lines_list = page.extract_text_lines()
        # if lines_list is not None:
        #     for line_dict in lines_list:
        #         text_line = line_dict['text'] 
        #         line_columns = text_line.split() 
        #         TOTAL_TEXT.append(line_columns)

        invoice_pdf_table = page.extract_table()
        if invoice_pdf_table is not None:
            TOTAL_TEXT = TOTAL_TEXT + invoice_pdf_table
            
        page.flush_cache()
        del page

print(TOTAL_TEXT)

for line in TOTAL_TEXT:
    # print(line)
    if line[0] is not None and "Date" in line[0]:
        continue
    else:
        if ('-' in line[0] or '/' in line[0]) and len(line) > 3 :
            Date.append(line[0][:10].replace('/','-'))
            Desc.append(line[3])
            if line[-3] != '':
                Type.append('debit')
                Amount.append(line[-3].replace(',','').replace('\n','').replace(' ','').replace('INR',''))
            if line[-2] != '':
                Type.append('credit')
                Amount.append(line[-2].replace(',','').replace('\n','').replace(' ','').replace('INR',''))
            Cheque_No.append(line[2])

print(Date,Desc,Amount,Type,Cheque_No)

print("Date :",len(Date))
print("Desc :", len(Desc))
print("Amount :",len(Amount))
print("Type :",len(Type))
print("Cheque_No :",len(Cheque_No))

NO_CSV = []

for date in Date:
    if (len(date)!=10):
        print(date)
        NO_CSV.append(0)   

if len(Type) <1:
    NO_CSV.append(2)
if len(Desc) <1:
    NO_CSV.append(3)

print("NO_CSV :",NO_CSV)

if len(NO_CSV) < 1:
    data = {"Date": Date, "Description": Desc, "Amount": Amount, "Type": Type}
    df = pd.DataFrame(data)
    df.to_excel(f"{file_name}.xlsx", index=False)
    df.to_csv(f"{file_name}.csv", index=False, header=True)