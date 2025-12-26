from openai import OpenAI
import os
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

# Guard against local shadowing of stdlib json
if hasattr(json, "__file__") and json.__file__ and json.__file__.endswith(os.sep + "Json.py"):
    raise RuntimeError("A local file named 'Json.py' is shadowing the standard json module. Please rename it (e.g., to 'json_utils.py').")

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "Output")
JSON_DIR = os.path.join(BASE_DIR, "JSON")
os.makedirs(JSON_DIR, exist_ok=True)

OPENROUTER_API_KEY = "YOUR_KEY"
if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("PUT_"):
    raise RuntimeError("Please set OPENROUTER_API_KEY in Json.py before running.")

# Initialize client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

MODEL = "openai/gpt-4o-mini"

def normalize_ocr_text(text: str) -> str:
    text = text.replace("\uFFFD", " ").replace("�", " ")
    text = text.replace("\r", "\n")
    text = re.sub(r"\t+", " ", text)
    text = re.sub(r"\u00A0", " ", text)  
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()

def build_prompt(extracted_text: str) -> str:
    return (
        "You are a financial statement parser. "
        "Extract bank transaction rows from the provided text, where columns may wrap across multiple lines. "
        "Descriptions are often split across lines; reconstruct the full description without truncating tokens like 'NEFT/UTIBN6' and include beneficiary/payee names. "
        "Return ONLY valid JSON with the following exact structure: "
        "{\n"
        "  \"transactions\": [\n"
        "    {\n"
        "      \"date\": string,\n"
        "      \"description\": string,\n"
        "      \"amount\": number,\n"
        "      \"type\": \"credit\"|\"debit\",\n"
        "      \"balance\": number|null\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- If description spans multiple lines, join them with single spaces (do not drop middle parts).\n"
        "- Keep helpful punctuation like '/' '-' '&' and account/reference numbers.\n"
        "- If balance not present, set it to null. Use '.' as decimal separator.\n"
        "- Do not add any commentary or code fences. Output pure JSON only.\n\n"
        "Text to parse begins below:\n\n" + extracted_text
    )

def build_chunk_prompt(chunk_text: str, chunk_index: int, total_chunks: int) -> str:
    return (
        "You are a financial statement parser. "
        "Extract bank transaction rows ONLY from this chunk of a larger statement. "
        f"This is chunk {chunk_index + 1} of {total_chunks}. "
        "Columns may wrap across multiple lines; join wrapped description lines into a single description without dropping tokens. "
        "Return ONLY valid JSON with the exact structure: {\n"
        "  \"transactions\": [\n"
        "    {\n"
        "      \"date\": string,\n"
        "      \"description\": string,\n"
        "      \"amount\": number,\n"
        "      \"type\": \"credit\"|\"debit\",\n"
        "      \"balance\": number|null\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- If description spans multiple lines, join with single spaces (keep '/' '-' '&' and refs).\n"
        "- If balance not present in this chunk, set it to null. Use '.' as decimal.\n"
        "- Do not add commentary or code fences. Output pure JSON only.\n\n"
        "Chunk text begins below:\n\n" + chunk_text
    )

def chunk_text(text: str, max_chars: int = 15000, overlap: int = 500) -> List[str]:
    if max_chars <= 0:
        return [text]
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + max_chars, text_len)
        slice_text = text[start:end]
        if end < text_len:
            nl_pos = slice_text.rfind("\n")
            if nl_pos != -1 and nl_pos > max_chars * 0.7:
                end = start + nl_pos
                slice_text = text[start:end]
        chunks.append(slice_text)
        if end == text_len:
            break
        start = max(0, end - overlap)
    return chunks

def parse_text_file(txt_path: str) -> dict:
    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read()

    extracted_text = normalize_ocr_text(raw_text)

    chunks = chunk_text(extracted_text, max_chars=15000, overlap=700)

    def extract_json_object(text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            parts = stripped.split("```")
            if len(parts) >= 3:
                stripped = parts[1] if parts[1].strip() else parts[2]
        start = stripped.find("{")
        if start == -1:
            return "{}"
        brace = 0
        for i, ch in enumerate(stripped[start:], start=start):
            if ch == '{':
                brace += 1
            elif ch == '}':
                brace -= 1
                if brace == 0:
                    return stripped[start:i+1]
        return "{}"

    def call_llm_on_chunk(idx: int, chunk: str) -> List[dict]:
        prompt = build_chunk_prompt(chunk, idx, len(chunks))
        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You convert raw bank statement text chunks into strict JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content if completion.choices else "{}"
            payload = extract_json_object(content)
            data = json.loads(payload)
        except Exception:
            data = {"transactions": []}

        if not isinstance(data, dict):
            data = {"transactions": []}
        if "transactions" not in data or not isinstance(data["transactions"], list):
            data["transactions"] = []
        return data["transactions"]

    collected: List[dict] = []
    max_workers = min(8, len(chunks)) if len(chunks) > 0 else 1
    if len(chunks) <= 1:
        collected = call_llm_on_chunk(0, chunks[0])
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(call_llm_on_chunk, i, c): i for i, c in enumerate(chunks)}
            for _ in as_completed(futures):
                pass  
            results_ordered: List[List[dict]] = [None] * len(chunks)  
            for future, i in list(futures.items()):
                try:
                    results_ordered[i] = future.result()
                except Exception:
                    results_ordered[i] = []
            for part in results_ordered:
                if part:
                    collected.extend(part)

    normalized: List[dict] = []
    for t in collected:
        if not isinstance(t, dict):
            continue
        date = t.get("date") if isinstance(t.get("date"), str) else None
        description = t.get("description") if isinstance(t.get("description"), str) else None
        amount = t.get("amount")
        tx_type = t.get("type")
        balance = t.get("balance")

        def to_number(val):
            if val is None:
                return None
            if isinstance(val, (int, float)):
                return float(val)
            try:
                return float(str(val).replace(",", ""))
            except Exception:
                return None

        amount_num = to_number(amount)
        balance_num = to_number(balance)

        tx_type_norm = None
        if isinstance(tx_type, str):
            s = tx_type.strip().lower()
            if s in ("credit", "debit"):
                tx_type_norm = s

        if isinstance(description, str):
            description = re.sub(r"\s+", " ", description).strip()

        normalized.append(
            {
                "date": date,
                "description": description,
                "amount": amount_num if amount_num is not None else None,
                "type": tx_type_norm,
                "balance": balance_num if balance_num is not None else None,
            }
        )

    return {"transactions": normalized}

def main():
    txt_files = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith(".txt")]
    if not txt_files:
        print("No .txt files found in 'Output' directory. Run extraction first.")
        return

    print(f"Found {len(txt_files)} text file(s) to process.")

    for txt_filename in txt_files:
        txt_path = os.path.join(OUTPUT_DIR, txt_filename)
        base_name = os.path.splitext(txt_filename)[0]
        json_path = os.path.join(JSON_DIR, base_name + ".json")

        print(f"Processing: {txt_filename}")
        try:
            data = parse_text_file(txt_path)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved JSON to: {json_path}")
        except Exception as e:
            print(f"Failed to process {txt_filename}: {e}")

if __name__ == "__main__":
    main()