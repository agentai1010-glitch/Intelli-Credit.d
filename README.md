# 🏦 Intelli-Credit — AI-Powered Corporate Credit Appraisal Engine

> **From Data Paradox to Credit Clarity in 90 Seconds**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-intelli--credit--d.vercel.app-00d4ff?style=for-the-badge)](https://intelli-credit-d.vercel.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Intelli--Credit-181717?style=for-the-badge&logo=github)](https://github.com/Pratiksawant14/Intelli-Credit)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?style=for-the-badge)](https://vitejs.dev/)
[![LightGBM](https://img.shields.io/badge/ML-LightGBM%20%2B%20SHAP-brightgreen?style=for-the-badge)](https://lightgbm.readthedocs.io/)

---



## What is Intelli-Credit?

Intelli-Credit is an end-to-end AI-powered Credit Appraisal Engine built for Indian corporate lending. It automates the complete process of evaluating a loan application — from raw PDF document ingestion to generating a professional Credit Appraisal Memorandum (CAM) — in approximately 90 seconds.

It was built for the **Intelli-Credit Hackathon Challenge** under the theme: *"Next-Gen Corporate Credit Appraisal: Bridging the Intelligence Gap."*

**What it replaces:** A manual process that takes credit managers 3–4 weeks involving stitching together GST filings, bank statements, annual reports, regulatory checks, site visit notes, and management interviews.

**What it produces:** A complete APPROVE/REJECT/WATCHLIST decision with a specific loan limit, interest rate, SHAP-based explainability, and a structured CAM PDF — all with a traceable evidence chain.

---



## 7-Node AI Pipeline

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  1. DOCUMENT    │────▶│  2. FEATURE          │────▶│  3. GST             │
│     INGESTION   │     │     INTELLIGENCE     │     │     RECONCILIATION  │
│                 │     │                      │     │                     │
│ Smart OCR +     │     │ Transparent feature  │     │ GSTR-2A vs GSTR-3B  │
│ Classification  │     │ engineering from     │     │ vs Bank Statement   │
│ of 5 doc types  │     │ raw documents        │     │ cross-validation    │
└─────────────────┘     └──────────────────────┘     └─────────────────────┘
                                                                │
                                                                ▼
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  7. CAM         │◀────│  6. EXTERNAL         │◀────│  4. LIGHTGBM        │
│     GENERATION  │     │     INTELLIGENCE     │     │     CREDIT SCORING  │
│                 │     │                      │     │                     │
│ Professional    │     │ MCA + eCourts +      │     │ SHAP explainability │
│ PDF via         │     │ RBI + IBBI +         │     │ 6 features, score   │
│ ReportLab + LLM │     │ News crawl           │     │ 0-100 + loan terms  │
└─────────────────┘     └──────────────────────┘     └─────────────────────┘
                                      ▲
                                      │
                        ┌──────────────────────┐
                        │  5. QUALITATIVE      │
                        │     ADJUSTMENTS      │
                        │                      │
                        │ Human-in-the-loop    │
                        │ analyst input form   │
                        │ with live score      │
                        └──────────────────────┘
```

---

## Key Features

### 🔍 Smart Document Ingestion
- Classifies 7 Indian financial document types automatically
- Extracts key financials from scanned PDFs using pytesseract OCR
- Natively handles Indian number formatting: `3,85,00,000` → `₹3.85Cr`
- Validates all fields with 100% Match indicator per document

### 🧠 Feature Intelligence Report
- Shows exactly how each document translates into ML features **before** the model runs
- 6 feature cards with formulas, source documents, and health indicators
- Complete transparency: no black box inputs

### ⚠️ GST Fraud Reconciliation
- Detects **CIRCULAR_TRADING_RISK**: ITC claimed vs available gap > 20%
- Detects **REVENUE_MISMATCH**: GST turnover vs bank credits discrepancy
- Detects **SUSPICIOUS_TRANSACTIONS**: Round-figure recurring amounts
- Computes reconciliation score: `100 - sum(penalties) = GST health score`

### 📊 Explainable ML Credit Scoring
- LightGBM model trained on 500 realistic Indian corporate samples
- SHAP TreeExplainer shows exactly which feature drove the score
- Loan pricing engine: MCLR base + risk premium based on score band
- Improvement counterfactuals: "Reduce D/E ratio 0.59→0.47 = +5.8 pts"

### 👤 Human-in-the-Loop Qualitative Adjustments
- 6-input analyst form: capacity utilization, management quality, site visit, industry outlook, collateral, litigation
- Live animated score circle — updates instantly as analyst clicks
- Every adjustment documented with audit trail in CAM

### 🌐 External Intelligence Research Agent
- Crawls 4 Indian regulatory databases concurrently via `asyncio.gather`
- MCA Portal, eCourts Services, RBI Defaulter List, IBBI Insolvency
- 6-month news sweep with semantic NLP tagging (STABLE, NO_ADVERSE_NEWS, CRITICAL_FLAG)
- FAISS vector search for semantic similarity matching

### 📄 Automated CAM PDF Generation
- 8-section banking-standard Credit Appraisal Memorandum
- Five Cs structure: Character, Capacity, Capital, Collateral, Conditions
- LLM narrative synthesis (OpenAI GPT-4 / Google Gemini)
- Complete score waterfall table: LightGBM Base → GST → Qualitative → Regulatory → Final

### 🗂️ Report History
- Immutable audit ledger of all generated CAMs stored in Supabase
- Download any previous CAM PDF at any time

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React (Vite) + Tailwind CSS + Recharts + React Router |
| Backend | FastAPI (Python) + JWT Auth + Pydantic |
| OCR / Parsing | PyMuPDF + pdfplumber + pytesseract + spaCy NER |
| ML Engine | LightGBM + SHAP TreeExplainer + scikit-learn |
| Research Agent | httpx async + BeautifulSoup + SentenceTransformers + FAISS |
| Entity Matching | RapidFuzz |
| CAM Generation | OpenAI GPT-4 / Google Gemini + ReportLab |
| Database | Supabase (PostgreSQL + pgvector) |
| Deployment | Vercel (frontend) + Railway (backend) |

---

## Project Structure

```text
Intelli-Credit.d/
│
├── frontend/                          # React + Vite frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── UploadPage.jsx               # Node 1: Document Ingestion
│   │   │   ├── FeatureIntelligenceReport.jsx# Node 2: Feature Intelligence Report
│   │   │   ├── ScoreView.jsx                # Node 3: Credit Scoring Dashboard
│   │   │   ├── QualitativeInputPage.jsx     # Node 4: Qualitative Adjustments
│   │   │   ├── EvidenceTimeline.jsx         # Node 5: External Evidence
│   │   │   ├── CAMGenerator.jsx             # Node 6: CAM Generation
│   │   │   └── HistoryView.jsx              # Node 7: Report History
│   │   ├── components/
│   │   │   └── Layout.jsx                   # 7-step Sidebar pipeline tracker
│   │   └── App.jsx                          # Root router mapping all 7 nodes
│   └── package.json
│
├── api/                               # FastAPI scalable endpoints
│   ├── upload_routes.py               # Handles multipart PDF parsing & ingestion
│   ├── score_routes.py                # Intercepts features for LightGBM scoring
│   ├── cam_routes.py                  # Generates LLM summaries & ReportLab PDFs
│   ├── recommendation_routes.py       # SHAP Counterfactual calculations
│   └── regulatory_routes.py           # Indian compliance checker
│
├── ml_engine/                         # Machine Learning Core Logic
│   ├── features.py                    # Financial engineering (Debt/Equity, ratios)
│   ├── model.py                       # LightGBM Builder, Synthesizer & Predictor
│   ├── explain.py                     # SHAP TreeExplainer feature weights
│   ├── gst_reconciler.py              # Rule-based GST circular-trading detection
│   └── smart_parser.py                # LLM & Regex NLP Extraction orchestrator
│
├── model_artifacts/
│   └── mock_model.txt                 # Active trained LightGBM Booster
│
├── research_agent/                    # Crawls Indian regulatory sources
├── ocr_pipeline/                      # Pytesseract OCR extraction logic
├── config/                            # Environment settings (Supabase, API keys)
├── main.py                            # FastAPI entry point
│
├── mock_documents/                    # ✅ TEST DOCUMENTS — USE THESE
│   ├── mock_annual_report.pdf         # Annual Report FY2025 — Sharma Textile
│   ├── mock_bank_statement.pdf        # HDFC Bank Statement Apr-Sep 2024
│   ├── mock_gstr3b.pdf                # GSTR-3B Return (GST filings)
│   ├── mock_gstr2a.pdf                # GSTR-2A Return (supplier ITC)
│   └── mock_sanction_letter.pdf       # SBI Sanction Letter ₹5Cr CC
│
└── README.md
```

## Quick Start — Test with Mock Documents

The fastest way to see Intelli-Credit working is to use the **live deployed application** with the mock documents already included in this repository.

### Step 1 — Open the Live App

Go to: **https://intelli-credit-d.vercel.app/**

### Step 2 — Download the Mock Documents

All 5 test documents are in the `/mock_documents/` folder of this repository:

```
mock_documents/
├── mock_annual_report.pdf      ← Upload this first
├── mock_bank_statement.pdf     ← Upload this second
├── mock_gstr3b.pdf             ← Upload this third
├── mock_gstr2a.pdf             ← Upload this fourth
└── mock_sanction_letter.pdf    ← Upload this fifth
```

[⬇️ Download all 5 mock documents as ZIP](mock_documents/)

### Step 3 — Run Through the Pipeline

1. **Document Ingestion** — Drag and drop all 5 PDFs → Click **"Run Smart Pipeline"**
   - Expected: All 5 documents show **100% Match** with correct extracted values
   - Annual Report: Revenue ₹42.50Cr | EBITDA ₹6.10Cr | PAT ₹2.80Cr
   - Bank Statement: Credits ₹3.55Cr | Closing ₹12.45L
   - GSTR-3B: Turnover ₹3.85Cr | ITC Claimed ₹58.00L
   - GSTR-2A: ITC Available ₹42.00L | Suppliers: 34
   - Sanction Letter: Exposure ₹5.00Cr | Rate 11.5% | CASH CREDIT

2. **Feature Intelligence** — Click **"Check Eligibility Score"**
   - Expected: 6 feature cards with computed values
   - GST Bank Match: **0.58 — FRAUD RISK DETECTED** (3 flags visible)
   - Debt-Equity: **0.586 — HEALTHY LEVERAGE**
   - Working Capital: **₹5.80Cr — POSITIVE BUFFER**

3. **Credit Scoring** — Click **"Run ML Scoring Engine"**
   - Expected: Score **91 / APPROVE**
   - SHAP Waterfall: Only `gst_bank_match` shows RED bar
   - Loan terms: ₹7.65Cr @ 10% for 12 months

4. **Qualitative Adjustments** — Adjust analyst inputs, click **"Apply & Continue"**
   - Try: Management = Average, Litigation = Yes, Industry = Favorable
   - Expected: Score drops to ~72 with live animation

5. **External Evidence** — Click **"Crawl & Index"**
   - Expected: All Sources Clean, Regulatory Score 80/100

6. **CAM Generation** — Click **"Synthesize CAM Document"**
   - Expected: Full 4-page PDF CAM with APPROVE decision, ₹7.65Cr limit

---

## Mock Documents (Included in Repo)

These 5 documents are synthetic but realistic representations of Indian corporate financial documents for **Sharma Textile Mills Pvt. Ltd.**, a mid-sized textile manufacturer from Surat, Gujarat.

### What Each Document Contains

| Document | Key Data Points | Hidden Signal |
|----------|----------------|---------------|
| `mock_annual_report.pdf` | Revenue ₹42.50Cr, EBITDA ₹6.10Cr, Net Worth ₹14Cr, Debt ₹8.2Cr | Clean financials, improving 3-year trend |
| `mock_bank_statement.pdf` | Credits ₹3.55Cr, Debits ₹3.43Cr, Closing ₹12.45L | 3x round ₹50L transactions → SUSPICIOUS_TRANSACTIONS flag |
| `mock_gstr3b.pdf` | Turnover ₹3.85Cr, Output Tax ₹69.30L, ITC Claimed ₹58L | ITC claimed > available → CIRCULAR_TRADING_RISK flag |
| `mock_gstr2a.pdf` | ITC Available ₹42L, 34 suppliers | Cross-validated against GSTR-3B: 38.1% gap |
| `mock_sanction_letter.pdf` | ₹5Cr CC at 11.5% from SBI | Existing exposure benchmark |



## Full Setup Guide

### Prerequisites

- Python 3.9+
- Node.js 18+
- Tesseract OCR installed (`sudo apt install tesseract-ocr` on Linux)
- Supabase account (for database)
- OpenAI API key OR Google Gemini API key (for CAM narrative)

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Pratiksawant14/Intelli-Credit.git
cd Intelli-Credit/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your keys:
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_supabase_anon_key
# OPENAI_API_KEY=your_openai_key (or GEMINI_API_KEY)
# JWT_SECRET=your_jwt_secret

# Start the backend server
uvicorn main:app --reload --port 8000
```

Backend will be running at: `http://localhost:8000`
API docs available at: `http://localhost:8000/docs`

### Frontend Setup

```bash
# In a new terminal
cd Intelli-Credit/frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local:
# VITE_API_BASE_URL=http://localhost:8000

# Start the dev server
npm run dev
```

Frontend will be running at: `http://localhost:5173`

### Verify Installation

```bash
# Test backend health
curl http://localhost:8000/health

# Expected response:
# {"status": "ok", "model": "loaded", "version": "1.0"}
```



## Live Links

| Resource | URL |
|----------|-----|
| 🌐 Live Application | https://intelli-credit-d.vercel.app/ |
| 💻 GitHub Repository |https://github.com/agentai1010-glitch/Intelli-Credit.d |
| 🎥 Demo Video | https://drive.google.com/file/d/1RRicK-j2nS4Srpwnlw1I0AEn6fjhwJnz/view?usp=sharing |

---

## Team



> *"Intelli-Credit doesn't just answer 'Should we lend?' — it answers 'WHY — with evidence.'"*
