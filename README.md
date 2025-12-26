# OCR Project

A comprehensive OCR (Optical Character Recognition) project for extracting and processing text from bank statements and financial documents. This project provides multiple OCR solutions using different libraries and techniques, each optimized for different use cases.

## Project Structure

```
OCR/
├── README.md
├── DocTR OCR/
│   ├── extraction.py
│   ├── Json.py
│   ├── PDF/
│   │   └── *.pdf
│   ├── output/
│   │   └── *.txt
│   └── json/
│       └── *.json
├── Easy OCR/
│   ├── run_easyocr.py
│   ├── Json.py
│   ├── easyocr.ipynb
│   ├── PDF/
│   │   └── *.pdf
│   ├── output/
│   │   └── *.txt
│   └── json/
│       └── *.json
├── PDFPlumber/
│   ├── script.py
│   ├── test.py
│   ├── test2.py
│   ├── icici.py
│   ├── 1763717081981_airtel.py
│   ├── 1764239087625_icici.py
│   ├── 200_icici.py
│   ├── 9627_kotak.py
│   ├── 9682_DCB.py
│   ├── 9684_UBI.py
│   ├── 9749_icici.py
│   ├── 9764_icici.py
│   ├── 9778_canara.py
│   ├── 9784_IB.py
│   ├── 9821_kotak.py
│   ├── 9830_icici.py
│   ├── 9855_icici.py
│   ├── 9863_canara.py
│   ├── pdf/
│   │   └── *.pdf
│   └── output/
│       └── *.csv
└── Pytesseract OCR/
    ├── extraction.py
    ├── Json.py
    ├── requirements.txt
    ├── PDF/
    │   └── *.pdf
    ├── output/
    │   └── *.txt
    └── json/
        └── *.json
```

## echnologies Used

- **DocTR** - Deep Learning-based OCR model
- **EasyOCR** - Multi-language OCR library with GPU support
- **Pytesseract** - Python wrapper for Google's Tesseract OCR
- **PDFPlumber** - PDF parsing and table extraction
- **OpenAI/OpenRouter API** - AI-powered text parsing to JSON
- **Pandas** - Data manipulation and CSV generation

## Installation

### Prerequisites

- Python 3.7+
- Tesseract OCR installed on your system
  - **Windows**: Download from [GitHub Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)
  - **Linux**: `sudo apt-get install tesseract-ocr`
  - **macOS**: `brew install tesseract`

### Install Dependencies

#### Pytesseract OCR
```bash
cd "Pytesseract OCR"
pip install -r requirements.txt
```

Required packages:
- `pdf2image==1.16.3`
- `pytesseract==0.3.10`
- `tqdm==4.66.1`
- `Pillow==10.0.1`

#### DocTR OCR
```bash
cd "DocTR OCR"
pip install python-doctr
pip install tqdm
```

#### Easy OCR
```bash
cd "Easy OCR"
pip install easyocr
pip install pymupdf
pip install pillow numpy
pip install openai  # For Json.py
```

#### PDFPlumber
```bash
cd PDFPlumber
pip install pdfplumber pandas PyPDF2 xlsxwriter openpyxl
```

## Usage

### 1. DocTR OCR

**Purpose**: Deep learning-based OCR using DocTR models.

**Steps**:
1. Place PDF files in `DocTR OCR/PDF/` directory
2. Run text extraction:
   ```bash
   cd "DocTR OCR"
   python extraction.py
   ```
3. Text output saved to `DocTR OCR/output/` (lowercase)
4. (Optional) Convert to JSON using AI:
   ```bash
   python Json.py
   ```
   - Requires OpenRouter API key (edit `Json.py` to set `OPENROUTER_API_KEY`)
   - Note: `Json.py` reads from `Output/` directory - ensure directory names match or rename accordingly

### 2. Easy OCR

**Purpose**: Multi-language OCR with GPU support.

**Steps**:
1. Place PDF files in `Easy OCR/PDF/` directory
2. Run OCR extraction:
   ```bash
   cd "Easy OCR"
   python run_easyocr.py
   ```
3. Text output saved to `Easy OCR/Output/` (capitalized)
4. (Optional) Convert to JSON:
   ```bash
   python Json.py
   ```
   - Requires OpenRouter API key
   - Reads from `Output/` directory and saves to `json/` directory

**Note**: EasyOCR will automatically use GPU if available (CUDA), otherwise falls back to CPU.

### 3. Pytesseract OCR

**Purpose**: Traditional Tesseract OCR implementation.

**Steps**:
1. Place PDF files in `Pytesseract OCR/PDF/` directory
2. Run OCR extraction:
   ```bash
   cd "Pytesseract OCR"
   python extraction.py
   ```
3. Text output saved to `Pytesseract OCR/output/` (lowercase)
4. (Optional) Convert to JSON:
   ```bash
   python Json.py
   ```
   - Requires OpenRouter API key
   - Note: `Json.py` reads from `Output/` directory - ensure directory names match or rename accordingly

### 4. PDFPlumber

**Purpose**: Extract structured data (tables) from bank statement PDFs.

**Usage**:
- Each bank has specific extraction scripts (e.g., `icici.py`, `kotak.py`, `canara.py`)
- Place PDF files in `PDFPlumber/pdf/` directory
- Run the appropriate bank-specific script
- Output CSV files saved to `PDFPlumber/output/`

**Example**:
```bash
cd PDFPlumber
python icici.py  # For ICICI bank statements
```

**CSV Output Format**:
- Date
- Description
- Amount
- Type (credit/debit)
- Cheque_No (if available)

## Configuration

### OpenRouter API Key (for JSON conversion)

For the `Json.py` files in each OCR folder:

1. Open the `Json.py` file
2. Replace `OPENROUTER_API_KEY = "YOUR_KEY"` with your actual API key
3. Get your API key from [OpenRouter](https://openrouter.ai/)

**Default Model**: `openai/gpt-4o-mini`

You can change the model in `Json.py`:
```python
MODEL = "openai/gpt-4o-mini"  # Change to your preferred model
```

## Output Formats

### Text Output (.txt)
Raw extracted text from PDF documents, line by line.

### JSON Output (.json)
Structured transaction data (saved to `json/` directory in each OCR folder):
```json
{
  "transactions": [
    {
      "date": "2024-01-15",
      "description": "NEFT/UTIBN6 TRANSFER",
      "amount": 5000.00,
      "type": "credit",
      "balance": 15000.00
    }
  ]
}
```

### CSV Output (.csv)
Comma-separated values for bank transactions with columns:
- Date
- Description
- Amount
- Type (credit/debit)
- Cheque_No