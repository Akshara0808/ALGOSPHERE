"""
OCR Service – wraps Tesseract OCR and pdf2image for receipt text extraction.
"""
import os
import requests
import pytesseract
from PIL import Image
import numpy as np

try:
    import cv2
except Exception:
    cv2 = None

OCR_API_URL = "https://ocr-api.hazex.workers.dev/"

def extract_text(filepath: str, tesseract_cmd: str = None) -> str:
    """
    Send receipt image to Hazex OCR API and return extracted text
    """

    try:
        with open(filepath, "rb") as f:
            files = {"file": f}
            response = requests.post(OCR_API_URL, files=files)

        if response.status_code != 200:
            raise RuntimeError(f"OCR API failed: {response.text}")

        data = response.json()

        # API format: {"error": false, "text": "..."}
        if data.get("error"):
            raise RuntimeError("OCR API returned an error")

        return data.get("text", "")

    except Exception as e:
        raise RuntimeError(f"OCR API error: {e}")
    
def _extract_from_image(filepath: str) -> str:
    """Run Tesseract on a single image file."""
    img = Image.open(filepath)
    img = _preprocess_image(img)
    return _extract_text_with_multiple_psm(img)


def _extract_from_pdf(filepath: str) -> str:
    """Convert PDF pages to images then run OCR on each page.
    Requires Poppler on Windows: https://github.com/oschwartz10612/poppler-windows/releases
    Extract and add the bin/ folder to PATH, or set POPPLER_PATH env variable.
    """
    import os
    from pdf2image import convert_from_path

    # Common Windows Poppler locations to try automatically
    poppler_candidates = [
        r"C:\poppler\Library\bin",
        r"C:\poppler\bin",
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files\poppler\bin",
        r"C:\tools\poppler\Library\bin",
    ]
    # Also check env variable
    poppler_path = os.getenv("POPPLER_PATH")
    if not poppler_path:
        for candidate in poppler_candidates:
            if os.path.exists(candidate):
                poppler_path = candidate
                break

    try:
        kwargs = {"dpi": 300}
        if poppler_path:
            kwargs["poppler_path"] = poppler_path
        pages = convert_from_path(filepath, **kwargs)
    except Exception as e:
        raise RuntimeError(
            f"PDF conversion failed. Poppler is required on Windows.\n"
            f"Download: https://github.com/oschwartz10612/poppler-windows/releases\n"
            f"Extract it and set POPPLER_PATH=C:\\poppler\\Library\\bin in your .env\n"
            f"Original error: {e}"
        )

    all_text = []
    for page in pages:
        page = _preprocess_image(page)
        text = _extract_text_with_multiple_psm(page)
        all_text.append(text.strip())

    return "\n\n--- PAGE BREAK ---\n\n".join(all_text)


def _preprocess_image(img: Image.Image) -> Image.Image:
    """Preprocess image to improve OCR accuracy on noisy receipts.

    Steps:
    - Convert to grayscale
    - Denoise
    - Contrast enhancement
    - Adaptive thresholding
    - Upscale for tiny text
    """
    gray = img.convert("L")

    if cv2 is None:
        return gray

    arr = np.array(gray)

    denoised = cv2.fastNlMeansDenoising(arr, None, 15, 7, 21)
    enhanced = cv2.equalizeHist(denoised)
    thresh = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )
    upscaled = cv2.resize(thresh, None, fx=1.8, fy=1.8, interpolation=cv2.INTER_CUBIC)
    return Image.fromarray(upscaled)


def _extract_text_with_multiple_psm(img: Image.Image) -> str:
    """Run OCR with multiple page segmentation modes and pick best output."""
    configs = [
        "--oem 3 --psm 6",
        "--oem 3 --psm 4",
        "--oem 3 --psm 11",
    ]
    candidates = []

    for config in configs:
        text = pytesseract.image_to_string(img, config=config).strip()
        score = len([line for line in text.splitlines() if line.strip()])
        candidates.append((score, text))

    best = max(candidates, key=lambda x: x[0])[1] if candidates else ""
    return best.strip()
