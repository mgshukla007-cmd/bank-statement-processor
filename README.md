# 🏦 Bank Statement Processing & Classification System
## 🚀 Live Demo

**Try it here:** https://bank-statement-proces-sor.streamlit.app/

> Note: OCR (scanned PDFs) is disabled in the demo. Text-based PDFs work fully.

An end-to-end prototype that ingests bank statement PDFs (text-based **or** scanned), extracts account & transaction data, classifies transactions **without using any LLM**, and exports structured CSV / Excel files.

---

## 🎯 Problem Statement

Banks issue statements in wildly different formats — some are digital text PDFs, others are scanned images. Financial teams waste hours manually copying data into spreadsheets and categorising transactions.

This system solves that by:
1. Accepting **any** bank statement PDF
2. Auto-detecting whether it's **text-based or image-based**
3. Extracting **account details** and **transactions** reliably
4. Classifying transactions using **non-LLM** approaches (rules + traditional ML)
5. Exporting structured data to **CSV and Excel**

---

## 🏗️ Architecture

```
            ┌─────────────────┐
            │  Upload PDF     │
            └────────┬────────┘
                     │
         ┌───────────▼────────────┐
         │  PDF Type Detector     │  ← pdfplumber text sampling
         │  (text-based / image)  │
         └───────┬────────┬───────┘
                 │        │
        ┌────────▼──┐  ┌──▼──────────┐
        │ pdfplumber│  │  OCR Path    │  ← pdf2image + Tesseract @ 300 DPI
        │ Text      │  │  (scanned)   │
        └────────┬──┘  └──────┬───────┘
                 │            │
                 └─────┬──────┘
                       │
              ┌────────▼──────────┐
              │  Parser (regex +  │
              │  balance-delta)   │
              └────────┬──────────┘
                       │
              ┌────────▼──────────┐
              │  Classifier        │  ← Rules first → ML fallback
              │  (Non-LLM)         │     TF-IDF + Logistic Regression
              └────────┬───────────┘
                       │
              ┌────────▼───────────┐
              │  Export (CSV/XLSX) │
              └────────────────────┘
```

---

## ✨ Key Features

| Feature | Implementation |
|---|---|
| Auto PDF type detection | Sample text length via `pdfplumber` |
| OCR fallback for scanned PDFs | `pdf2image` + `pytesseract` at 300 DPI |
| Account info extraction | Regex patterns for holder, A/C no, IFSC |
| Transaction extraction | Line-level regex + column heuristics |
| **Debit vs Credit detection** | **Balance-delta logic (ground truth)** |
| **Non-LLM classification** | **Rule keywords → ML (TF-IDF + LogReg)** |
| Export | CSV + Excel via pandas / openpyxl |
| Web UI | Streamlit with download buttons |
| Debug transparency | Raw extracted text shown in expander |

---

## 🧠 Why Balance-Delta for Debit/Credit?

The most reliable signal for whether a transaction is debit or credit is **how the balance changed**:

- Balance ↑ by exactly the transaction amount → **credit**
- Balance ↓ by exactly the transaction amount → **debit**

This is more reliable than keyword matching (which fails on descriptions like `SALARY CREDITED` vs `SALARY DEBITED`) and handles missing rows gracefully by using the *direction* of movement.

---

## 🚫 No LLMs Used

The brief explicitly prohibits LLMs for classification. This system uses:

1. **Heuristic rules** — 10 categories with keyword lists (Food, Transport, Shopping, Utilities, Salary, Transfer, ATM, Bills & EMI, Healthcare, Entertainment)
2. **Traditional ML** — `TfidfVectorizer(ngram_range=(1,2))` + `LogisticRegression` trained on ~40 labelled descriptions

Rules handle ~75% of common Indian bank transactions with zero latency; ML handles unseen descriptions.

---

## 📂 Project Structure

```
bank-statement-processor/
├── app.py                  # Streamlit UI
├── src/
│   ├── __init__.py
│   ├── pdf_reader.py      # PDF type detection + text extraction
│   ├── ocr_engine.py      # OCR fallback for scanned PDFs
│   ├── parser.py          # Regex parsing + balance-delta logic
│   ├── classifier.py      # Rule + ML classification (non-LLM)
│   └── exporter.py        # CSV / Excel export
├── data/                   # (gitignored) sample PDFs
├── outputs/                # (gitignored) generated CSV/Excel
├── tests/                  # pytest tests
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Setup

### 1. Clone & enter the repo
```bash
git clone <your-repo-url>
cd bank-statement-processor
```

### 2. Create virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR (system-level)
- **Windows**: https://github.com/UB-Mannheim/tesseract/wiki
- **Mac**: `brew install tesseract`
- **Linux**: `sudo apt install tesseract-ocr`

> If Tesseract is not on PATH on Windows, uncomment the config line in `src/ocr_engine.py` and set the correct path.

### 5. Run the app
```bash
streamlit run app.py
```
The UI opens at `http://localhost:8501`.

---

## 🧪 Testing the Pipeline (without UI)

```python
from src.parser import parse_transactions
text = """
15/01/2024 SWIGGY ORDER 450.00 12340.50
16/01/2024 SALARY CREDITED 50000.00 62340.50
"""
for t in parse_transactions(text):
    print(t)
```

Expected:
```python
{'date': '15/01/2024', 'description': 'SWIGGY ORDER', 'debit': 450.0, 'credit': None, 'balance': 12340.50}
{'date': '16/01/2024', 'description': 'SALARY CREDITED', 'debit': None, 'credit': 50000.0, 'balance': 62340.50}
```

---

## 🛡️ Real-World Scenarios Handled

| Scenario | Handling Strategy |
|---|---|
| Scanned / image-based PDF | OCR fallback at 300 DPI |
| Multi-bank layouts | Positional column heuristics + keyword hints |
| Description contains value date twice | Regex strips leading secondary date |
| Missing previous row (e.g. skipped "DISCOUNT ON FUEL") | Balance **direction** (not exact match) drives classification |
| Standalone "CR" / "DR" | Word-boundary regex |
| Prefix forms ("CREDITED", "DEPOSITED", "WITHDRAWN") | Prefix-based regex (no word boundary needed) |
| Unknown merchant | ML classifier fallback (TF-IDF + LogReg) |
| Empty / corrupted page | Line skip with `continue`, no crash |
| Password-protected PDF | Exception caught, user informed via UI |

---

## ⚠️ Limitations & Future Work

**Current limitations:**
- **OCR**: Tesseract OCR is optional. If not installed on the host machine, image-based (scanned) PDFs will return no text — the app degrades gracefully with a clear message. To enable OCR: install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki and set its path in `src/ocr_engine.py`.
- **Parser**: Tuned for common Indian bank layouts (HDFC, ICICI, SBI, Standard Chartered) and simple UK-style statements. Some layout variations (e.g. Standard Chartered 2019) may not extract the account holder name — the fallback cascade handles most cases but not all.
- **ML training set**: ~40 samples. Accuracy improves with real labelled data.
- **Not integrated**: `camelot`/`tabula` table extraction (planned).
- **Multi-currency**: not yet normalized.

**Roadmap:**
- Layout config file per bank (declarative, no code change to add a bank)
- `camelot` table extraction for structured PDFs
- Expand ML training set (target ≥ 500 samples)
- Docker + CI/CD
- Feedback loop: user corrections retrain the classifier

---

## 📊 Sample Results

Given a real 4-page Standard Chartered statement (2019):

- **25 transactions** extracted
- **100% correct debit/credit split** using balance-delta logic
- **ATM withdrawals** correctly categorised as `ATM`
- **NEFT credit (₹67,148)** correctly identified as `credit` (balance increased)
- **CSV + Excel** exported with account info attached

---

## 👤 Author

**Er.Maharshi Shukla**  
Data Science / AI Engineering  
Created as a submission for Befree Global company for AI & Automation assessment round.
