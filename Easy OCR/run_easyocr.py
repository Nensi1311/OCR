from tqdm import tqdm
import os
import time
import io
from typing import List

try:
    import easyocr
except Exception as _e:  
    raise SystemExit("EasyOCR is not installed. Install with: pip install easyocr") from _e

try:
    import fitz  
except Exception as _e:  
    raise SystemExit("PyMuPDF is not installed. Install with: pip install pymupdf") from _e

try:
    import numpy as np
    from PIL import Image
except Exception as _e:  
    raise SystemExit("Pillow and NumPy are required. Install with: pip install pillow numpy") from _e


def load_reader():
    gpu_available = False
    try:  
        import torch  

        gpu_available = torch.cuda.is_available()
    except Exception:
        gpu_available = False

    print("Loading EasyOCR model (gpu=" + str(gpu_available) + ")...")
    reader = easyocr.Reader(["en"], gpu=gpu_available)
    print("Model loaded successfully.")
    return reader


def pdf_page_to_numpy_images(pdf_path: str, zoom: float = 2.0):
    doc = fitz.open(pdf_path)
    try:
        for page_idx in range(doc.page_count):
            page = doc.load_page(page_idx)
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            png_bytes = pix.tobytes("png")
            pil_img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
            image_np = np.array(pil_img)
            yield image_np
    finally:
        doc.close()


def extract_text_with_easyocr(pdf_path: str, reader: "easyocr.Reader"):
    lines_out: List[str] = []

    page_images = list(pdf_page_to_numpy_images(pdf_path))
    for _ in tqdm(range(len(page_images)), desc="Processing", ncols=100):
        time.sleep(0.1)

    for page_img in page_images:
        try:
            texts = reader.readtext(page_img, detail=0, paragraph=True)
        except Exception:
            texts = reader.readtext(page_img, detail=0)

        for t in texts:
            t = t.strip()
            if t:
                lines_out.append(t)

        if lines_out and lines_out[-1] != "":
            lines_out.append("")

    return lines_out


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_dir = os.path.join(base_dir, "PDF")
    output_dir = os.path.join(base_dir, "Output")
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.isdir(pdf_dir):
        print("'PDF' directory not found.")
        return

    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in 'PDF' directory.")
        return

    print(f"Found {len(pdf_files)} PDF file(s) in 'PDF' directory.")
    reader = load_reader()

    for pdf_filename in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        output_basename = os.path.splitext(pdf_filename)[0] + ".txt"
        output_path = os.path.join(output_dir, output_basename)

        print(f"\nProcessing: {pdf_filename}")
        try:
            print("Reading PDF document and running OCR...")
            lines_out = extract_text_with_easyocr(pdf_path, reader)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines_out))

            print(f"Saved extracted text to: {output_path}")
        except Exception as e:
            print(f"An error occurred processing '{pdf_filename}': {e}")
            continue


if __name__ == "__main__":
    main()