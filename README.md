# AlgoSphere – Intelligent Expense Manager

> Turn receipts into financial insights using OCR + GPT-4.

## Tech Stack

| Layer       | Technology                |
|-------------|---------------------------|
| Frontend    | HTML · CSS · JavaScript   |
| Backend     | Python – Flask            |
| OCR         | Tesseract OCR             |
| AI Parsing  | OpenAI GPT-4o-mini        |
| Database    | MongoDB                   |
| PDF Reports | ReportLab                 |

## Features

- **User auth** – JWT-secured signup & login
- **Receipt upload** – drag-and-drop JPG / PNG / PDF
- **OCR extraction** – Tesseract reads every character
- **AI parsing** – GPT-4 structures vendor, date, items, total, tax, category
- **Dashboard** – spending statistics with Chart.js visualisations
- **PDF reports** – download monthly expense reports

## Prerequisites

1. **Python 3.10+**
2. **MongoDB** running locally on `mongodb://localhost:27017`
3. **Tesseract OCR** installed:
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - Keep default install path `C:\Program Files\Tesseract-OCR\tesseract.exe`
4. **OpenAI API key** with GPT-4 access

## Quick Start

```bash
# 1. Clone & enter directory
cd ALGOSPHERE

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
copy .env.example .env
# Edit .env and fill in MONGO_URI, JWT_SECRET_KEY, OPENAI_API_KEY, TESSERACT_CMD

# 5. Run the app
python app.py

Open **http://localhost:5000** in your browser.

## Environment Variables

| Variable          | Description                          | Example                              |
|-------------------|--------------------------------------|--------------------------------------|
| `MONGO_URI`       | MongoDB connection string            | `mongodb://localhost:27017/algosphere`|
| `JWT_SECRET_KEY`  | Secret key for JWT signing           | any-random-string                    |
| `OPENAI_API_KEY`  | OpenAI API key                       | `sk-…`                               |
| `TESSERACT_CMD`   | Path to tesseract executable         | `C:/Program Files/Tesseract-OCR/tesseract.exe` |
| `UPLOAD_FOLDER`   | Folder for uploaded images           | `uploads`                            |
