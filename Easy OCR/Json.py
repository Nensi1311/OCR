from openai import OpenAI
import os
import re
import json

# Guard against local shadowing of stdlib json
if hasattr(json, "__file__") and json.__file__ and json.__file__.endswith(os.sep + "json.py"):
    raise RuntimeError("A local file named 'json.py' is shadowing the standard json module. Please rename it (e.g., to 'json_utils.py').")

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "Output")
JSON_DIR = os.path.join(BASE_DIR, "JSON")
os.makedirs(JSON_DIR, exist_ok=True)

OPENROUTER_API_KEY = "YOUR_KEY"
if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("PUT_"):
    raise RuntimeError("Please set OPENROUTER_API_KEY in send_to_openrouter.py before running.")

# Initialize client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

MODEL = "openai/gpt-4o-mini"


def normalize_ocr_text(text: str) -> str:
    # Replace common replacement chars and non-printables
    text = text.replace("\uFFFD", " ").replace("�", " ")
    # Normalize whitespace
    text = text.replace("\r", "\n")
    text = re.sub(r"\t+", " ", text)
    text = re.sub(r"\u00A0", " ", text)  # non-breaking space
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


def parse_text_file(txt_path: str) -> dict:
    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read()

    extracted_text = normalize_ocr_text(raw_text)
    prompt = build_prompt(extracted_text)

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You convert raw bank statement text into strict JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        # If supported by the model, this enforces a JSON object response
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content if completion.choices else "{}"

    # Try to coerce to JSON
    try:
        data = json.loads(content)
    except Exception:
        # Fallback to empty
        data = {"transactions": []}

    # Ensure structure
    if not isinstance(data, dict):
        data = {"transactions": []}
    if "transactions" not in data or not isinstance(data["transactions"], list):
        data["transactions"] = []

    # Best-effort normalization of fields
    normalized = []
    for t in data["transactions"]:
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

        # Final cleanup of description
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


