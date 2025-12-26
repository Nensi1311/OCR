from pdf2image import convert_from_path
import pytesseract
from tqdm import tqdm
import time
import os

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
            print("Converting PDF to images...")
            # Convert PDF to images (one image per page)
            images = convert_from_path(pdf_path)
            print(f"PDF converted to {len(images)} page(s).")
            
            print("Running OCR...")
            all_text = []
            
            for i, image in enumerate(images):
                print(f"Processing page {i+1}/{len(images)}...")
                
                # Run OCR on each page
                page_text = pytesseract.image_to_string(image, lang='eng')
                
                if page_text.strip():
                    all_text.append(f"--- Page {i+1} ---")
                    all_text.append(page_text.strip())
                    all_text.append("")  # Empty line between pages

            # Write output
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(all_text))

            print(f"Saved extracted text to: {output_path}")

        except Exception as e:
            print(f"An error occurred processing '{pdf_filename}': {e}")
            continue

print("\nOCR processing completed!")