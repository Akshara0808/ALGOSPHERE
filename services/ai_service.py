"""
AI Service – uses OpenAI to parse raw OCR text into structured receipt data.
Falls back to a local rule-based parser if the API is unavailable.
"""
import json
import re
from openai import OpenAI


SYSTEM_PROMPT = """You are an expert receipt parser. Given raw OCR text from a receipt, extract structured data and return ONLY a valid JSON object (no markdown, no code fences, just pure JSON).

The JSON must follow this exact schema:
{
  "vendor": "string (store/restaurant name)",
  "date": "string (YYYY-MM-DD format, or empty string if not found)",
  "items": [
    {"name": "string", "qty": number, "price": number}
  ],
  "total": number (final amount paid, excluding tax if shown separately),
  "tax": number (tax amount, 0 if not found),
  "category": "string (one of: Food & Dining, Groceries, Shopping, Healthcare, Transportation, Entertainment, Utilities, Travel, Education, Other)"
}

Rules:
- All prices must be numbers (not strings).
- Assume Indian receipts by default and interpret currency as INR unless clearly stated otherwise.
- If a field is missing from the receipt, use sensible defaults: empty string for text, 0 for numbers, empty array for items.
- Infer the category from the vendor name and purchased items.
- Date must be in YYYY-MM-DD format.
- Return ONLY the JSON object, nothing else.
"""

# Models to try in order of preference
_MODELS = ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-3.5-turbo-0125"]


def parse_receipt_with_ai(raw_text: str, openai_api_key: str) -> dict:
    """Send raw OCR text to OpenAI and return a structured receipt dict.
    Tries multiple models in sequence and falls back to a local parser if all fail.
    """
    placeholder = "sk-your-openai-api-key-here"
    if not openai_api_key or openai_api_key.strip() == placeholder:
        # No valid key – use local parser
        return _local_parse(raw_text)

    last_error = None

    try:
        client = OpenAI(api_key=openai_api_key)
    except Exception as e:
        result = _local_parse(raw_text)
        result["_ai_warning"] = f"OpenAI client init failed ({e}). Used local parser."
        return result

    for model in _MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Parse this receipt:\n\n{raw_text}"},
                ],
                temperature=0,
                max_tokens=1000,
            )

            content = response.choices[0].message.content.strip()

            # Strip accidental markdown code fences
            content = re.sub(r"^```[a-z]*\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
            content = content.strip()

            return json.loads(content)

        except json.JSONDecodeError as e:
            last_error = f"AI returned invalid JSON using {model}: {e}"
            break  # JSON error is not a model-availability issue, don't retry
        except Exception as e:
            last_error = str(e)
            # If model not found or permission error, try next model
            if any(k in str(e).lower() for k in ("model", "not found", "does not exist", "permission")):
                continue
            # Otherwise (auth error, quota, network) – fall back to local
            break

    # All models failed – use local parser and tag the result
    result = _local_parse(raw_text)
    result["_ai_warning"] = f"OpenAI unavailable ({last_error}). Used local parser."
    return result


# ---------------------------------------------------------------------------
# Local rule-based fallback parser (no API required)
# ---------------------------------------------------------------------------
def _local_parse(raw_text: str) -> dict:
    """Extract basic receipt fields using regex heuristics."""
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    # Vendor – first non-empty line
    vendor = lines[0] if lines else "Unknown"

    # Date – look for common date patterns
    date = ""
    date_patterns = [
        r"\b(\d{4}[-/]\d{2}[-/]\d{2})\b",
        r"\b(\d{2}[-/]\d{2}[-/]\d{4})\b",
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",
    ]
    for pat in date_patterns:
        m = re.search(pat, raw_text, re.IGNORECASE)
        if m:
            date = m.group(1)
            break

    # Total – look for the largest currency amount
    amounts = re.findall(r"(?:total|amount|grand total|net amount|bill amount)[^\d]*(\d+[\d,]*\.?\d*)", raw_text, re.IGNORECASE)
    if not amounts:
        amounts = re.findall(r"(?:₹|rs\.?|inr)?\s*(\d{1,9}(?:,\d{2,3})*\.\d{2})", raw_text, re.IGNORECASE)
    total = max((float(a.replace(",", "")) for a in amounts), default=0.0)

    # Tax
    tax_match = re.search(r"(?:tax|gst|cgst|sgst|igst|vat|hst)[^\d]*(\d+[\d,]*\.?\d*)", raw_text, re.IGNORECASE)
    tax = float(tax_match.group(1).replace(",", "")) if tax_match else 0.0

    # Items – lines that look like  "item name  $price"
    items = []
    item_pattern = re.compile(r"^(.+?)\s+(?:₹|rs\.?|inr|\$)?\s*(\d+[\d,]*\.\d{2})$", re.IGNORECASE)
    for line in lines[1:]:
        m = item_pattern.match(line)
        if m:
            name, price = m.group(1).strip(), float(m.group(2).replace(",", ""))
            if price < total or total == 0:
                items.append({"name": name, "qty": 1, "price": price})

    # Category – keyword-based inference
    category = _infer_category(vendor + " " + raw_text)

    return {
        "vendor":   vendor,
        "date":     date,
        "items":    items[:20],   # cap at 20
        "total":    round(total, 2),
        "tax":      round(tax, 2),
        "category": category,
    }


def _infer_category(text: str) -> str:
    text = text.lower()
    mapping = {
        "Food & Dining":    ["restaurant", "cafe", "coffee", "pizza", "burger", "diner", "bistro", "sushi", "grill", "eatery", "dining"],
        "Groceries":        ["grocery", "supermarket", "market", "whole foods", "walmart", "costco", "aldi", "kroger", "safeway", "produce"],
        "Healthcare":       ["pharmacy", "medical", "clinic", "hospital", "drug", "health", "dental", "cvs", "walgreens"],
        "Transportation":   ["uber", "lyft", "taxi", "fuel", "petrol", "gas station", "shell", "bp", "parking", "metro", "train"],
        "Shopping":         ["amazon", "mall", "store", "shop", "retail", "clothing", "electronics", "fashion"],
        "Entertainment":    ["cinema", "movie", "theatre", "netflix", "spotify", "game", "concert", "event"],
        "Utilities":        ["electric", "water", "gas", "internet", "phone", "utility", "bill"],
        "Travel":           ["hotel", "airbnb", "flight", "airline", "booking", "travel", "resort"],
        "Education":        ["school", "university", "college", "course", "book", "stationery", "tuition"],
    }
    for category, keywords in mapping.items():
        if any(kw in text for kw in keywords):
            return category
    return "Other"
