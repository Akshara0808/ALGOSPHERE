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
```

Open **http://localhost:5000** in your browser.

## Project Structure

```
ALGOSPHERE/
├── app.py                  # Flask app entry point
├── config.py               # Configuration
├── requirements.txt
├── .env.example            # Environment variable template
├── models/
│   ├── user.py             # User model + bcrypt auth
│   └── receipt.py          # Receipt model + aggregations
├── routes/
│   ├── auth.py             # /api/auth/signup · login · me
│   ├── receipts.py         # /api/receipts/   (CRUD + upload)
│   ├── dashboard.py        # /api/dashboard/stats
│   └── reports.py          # /api/reports/monthly
├── services/
│   ├── ocr_service.py      # Tesseract OCR wrapper
│   ├── ai_service.py       # OpenAI GPT-4 parser
│   └── pdf_service.py      # ReportLab PDF generator
├── utils/
│   └── helpers.py          # File validation helpers
├── templates/              # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html          # Landing page
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── upload.html
│   └── receipts.html
├── static/
│   ├── css/style.css
│   └── js/
│       ├── main.js         # Shared helpers, auth guard, toast
│       ├── auth.js
│       ├── dashboard.js
│       ├── upload.js
│       └── receipts.js
└── uploads/                # Uploaded receipt images (runtime)
```

## API Endpoints

| Method | Path                              | Auth | Description              |
|--------|-----------------------------------|------|--------------------------|
| POST   | `/api/auth/signup`                | No   | Register new user        |
| POST   | `/api/auth/login`                 | No   | Login, receive JWT       |
| GET    | `/api/auth/me`                    | Yes  | Current user info        |
| POST   | `/api/receipts/upload`            | Yes  | Upload & parse receipt   |
| GET    | `/api/receipts/`                  | Yes  | List user receipts       |
| GET    | `/api/receipts/<id>`              | Yes  | Get single receipt       |
| DELETE | `/api/receipts/<id>`              | Yes  | Delete receipt           |
| GET    | `/api/dashboard/stats`            | Yes  | Dashboard statistics     |
| GET    | `/api/reports/monthly?year=&month=`| Yes | Download PDF report      |
| GET    | `/api/reports/available`          | Yes  | List months with receipts|

## Environment Variables

| Variable          | Description                          | Example                              |
|-------------------|--------------------------------------|--------------------------------------|
| `MONGO_URI`       | MongoDB connection string            | `mongodb://localhost:27017/algosphere`|
| `JWT_SECRET_KEY`  | Secret key for JWT signing           | any-random-string                    |
| `OPENAI_API_KEY`  | OpenAI API key                       | `sk-…`                               |
| `TESSERACT_CMD`   | Path to tesseract executable         | `C:/Program Files/Tesseract-OCR/tesseract.exe` |
| `UPLOAD_FOLDER`   | Folder for uploaded images           | `uploads`                            |
