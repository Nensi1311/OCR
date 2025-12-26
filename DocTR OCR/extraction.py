from doctr.models import ocr_predictor
from doctr.io import DocumentFile
from tqdm import tqdm
import time
import os

# Load model
print("Loading OCR model...")
model = ocr_predictor(pretrained=True)
print("Model loaded successfully.")

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "PDF")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

if not pdf_files:
    print("No PDF files found in 'PDF' directory.")
else:
    print(f"Found {len(pdf_files)} PDF file(s) in 'PDF' directory.")

    for pdf_filename in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_filename)
        output_basename = os.path.splitext(pdf_filename)[0] + ".txt"
        output_path = os.path.join(OUTPUT_DIR, output_basename)

        print(f"\nProcessing: {pdf_filename}")
        try:
            print("Reading PDF document...")
            doc = DocumentFile.from_pdf(pdf_path)
            print("PDF document loaded successfully.")
            print("Running OCR...")
            for _ in tqdm(range(10), desc="Processing", ncols=100):
                time.sleep(0.1)

            # Run OCR
            result = model(doc)

            # Collect text
            lines_out = []
            for page in result.pages:
                for block in page.blocks:
                    for line in block.lines:
                        line_text = " ".join([word.value for word in line.words])
                        if line_text:
                            lines_out.append(line_text)

            # Write output
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines_out))

            print(f"Saved extracted text to: {output_path}")

        except Exception as e:
            print(f"An error occurred processing '{pdf_filename}': {e}")
            continue
