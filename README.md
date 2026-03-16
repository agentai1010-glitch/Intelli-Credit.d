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

**What it produces:** A complete APPROVE/REJECT/WATCHLIST decision with a specific loan limit, interest rate, SHAP-based explainability, a structured CAM PDF, and a conversational Credit Intelligence Chatbot — all with a traceable evidence chain.

---

## 8-Node AI Pipeline

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  1. DOCUMENT    │────▶│  2. EXTERNAL         │────▶│  3. GST             │
│     INGESTION   │     │     INTELLIGENCE     │     │     RECONCILIATION  │
│                 │     │                      │     │                     │
│ Sarvam Vision + │     │ Google News live     │     │ GSTR-2A vs GSTR-3B  │
│ Gemini 2.0 Flash│     │ crawl — adverse news │     │ vs Bank Statement   │
│ 200k context    │     │ feeds LightGBM       │     │ cross-validation    │
└─────────────────┘     └──────────────────────┘     └─────────────────────┘
                                                                │
                                                                ▼
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  4. FEATURE     │────▶│  5. LIGHTGBM         │────▶│  6. QUALITATIVE     │
│     INTELLIGENCE│     │     CREDIT SCORING   │     │     ADJUSTMENT      │
│                 │     │                      │     │                     │
│ 6 ML features   │     │ SHAP explainability  │     │ Human-in-the-loop   │
│ computed from   │     │ score 0-100 +        │     │ analyst input with  │
│ verified data   │     │ loan terms           │     │ live score update   │
└─────────────────┘     └──────────────────────┘     └─────────────────────┘
         │                                                       │
         ▼                                                       ▼
┌─────────────────┐                               ┌─────────────────────┐
│  8. CREDIT      │◀──────────────────────────────│  7. CAM             │
│     INTELLIGENCE│                               │     GENERATION      │
│     CHATBOT     │                               │                     │
│                 │                               │ Gemini 2.0 Flash    │
│ PageIndex +     │                               │ 8-section banking   │
│ GPT-4o Mini     │                               │ standard PDF        │
└─────────────────┘                               └─────────────────────┘
```

---

## Key Features

### 🔍 Smart Document Ingestion
- **Sarvam Vision** — India's sovereign AI model trained on 22 Indian languages handles Gujarati, Hindi, Marathi scripts and scanned PDFs natively
- **Gemini 2.0 Flash** — 200,000 character context window for deep financial extraction from large annual reports
- **Denomination-aware** — automatically detects Crores, Lakhs, Thousands from table headers and converts to absolute rupees
- Proven on real 309-page NBFC annual report (Vivriti Capital FY2024-25)

### 🌐 External Intelligence — Real-Time Adverse Media
- Google News RSS crawl searches 5 targeted regulatory queries per company
- Adverse findings feed **directly into LightGBM as `legal_flag_count` feature** — not patched after scoring
- Live test: Found IDBI Bank NCLT insolvency plea against Zee Entertainment (Economic Times, March 2026)
- Government portals (MCA, eCourts, RBI, IBBI) shown with honest ACCESS_RESTRICTED status

### ⚠️ GST Fraud Reconciliation
- Detects **CIRCULAR_TRADING_RISK**: ITC claimed vs available gap > 20%
- Detects **REVENUE_MISMATCH**: GST turnover vs bank credits discrepancy
- Detects **SUSPICIOUS_TRANSACTIONS**: Round-figure recurring amounts
- Computes reconciliation score: `100 - sum(penalties) = GST health score`

### 📊 Explainable ML Credit Scoring
- LightGBM model trained on 500 realistic Indian corporate samples
- SHAP TreeExplainer shows exactly which feature drove the score
- Loan pricing engine: MCLR base + risk premium based on score band
- Improvement counterfactuals: "Resolve litigation = +18 pts, Fix GST = +7-9 pts"

### 👤 Human-in-the-Loop Qualitative Adjustments
- 6-input analyst form: capacity utilization, management quality, site visit, industry outlook, collateral, litigation
- Live animated score circle — updates instantly as analyst clicks
- Every adjustment documented with audit trail in CAM

### 📄 Automated CAM PDF Generation
- 8-section banking-standard Credit Appraisal Memorandum generated by **Gemini 2.0 Flash in 10 seconds**
- Five Cs structure: Character, Capacity, Capital, Collateral, Conditions
- Includes: Auditor opinion, 3-year revenue trend, sector classification, complete SHAP waterfall
- Complete score journey: LightGBM Base → GST → Qualitative → Regulatory → Final

### 💬 Credit Intelligence Chatbot (Node 8)
- Post-CAM conversational explainability powered by **PageIndex + GPT-4o Mini**
- Analysts ask questions in plain English — answers cite specific numbers from uploaded documents
- 4 starter questions pre-loaded: GST score, revenue trend, improvement paths, auditor opinion
- Confidence badges: HIGH (PageIndex cited) / MEDIUM (credit context fallback)
- Example: *"Why was the GST score 0.58?"* → cites -20pts ITC gap, -7pts mismatch, -15pts suspicious transactions

### 🗂️ Report History
- Immutable audit ledger of all generated CAMs stored in Supabase
- Download any previous CAM PDF at any time

---

## Two-Company Differentiation — Proof of Live Intelligence

| Feature | Sharma Textile Mills | Zee Entertainment |
|---------|---------------------|-------------------|
| Credit Score | **91 — APPROVE** | **27 — REJECT** |
| Working Capital | ₹5.80 Cr | ₹14.70 Cr |
| Debt/Equity | 0.586x | 0.641x |
| GST Match | 0.58 | 0.57 |
| Legal Flags | 0 | 5 (3 doc + 2 news) |
| Interest Rate | 10% | Rejected |
| Adverse News | 0 articles | 2 articles (NCLT) |

Same AI engine. Different data. Completely different decisions.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React (Vite) + Tailwind CSS + Recharts + React Router |
| Backend | FastAPI (Python) + JWT Auth + Pydantic |
| OCR / Extraction | Sarvam Vision API + Gemini 2.0 Flash (200k context) + PyMuPDF + pdfplumber + pytesseract (fallback) |
| ML Engine | LightGBM + SHAP TreeExplainer + scikit-learn |
| External Intelligence | Google News RSS + httpx async + sentence-transformers + pgvector |
| Entity Matching | spaCy NER + RapidFuzz |
| CAM Generation | Gemini 2.0 Flash via OpenRouter + ReportLab |
| Chatbot | PageIndex AI + GPT-4o Mini via OpenRouter |
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
│   │   │   ├── EvidenceTimeline.jsx         # Node 2: External Intelligence
│   │   │   ├── FeatureIntelligenceReport.jsx# Node 4: Feature Intelligence
│   │   │   ├── ScoreView.jsx                # Node 5: Credit Scoring Dashboard
│   │   │   ├── QualitativeInputPage.jsx     # Node 6: Qualitative Adjustments
│   │   │   ├── CAMGenerator.jsx             # Node 7: CAM Generation + Chatbot
│   │   │   └── HistoryView.jsx              # Report History
│   │   ├── components/
│   │   │   ├── CreditChatbot.jsx            # Node 8: Credit Intelligence Chatbot
│   │   │   └── Layout.jsx                   # 8-step sidebar pipeline tracker
│   │   └── App.jsx
│   └── package.json
│
├── api/                               # FastAPI endpoints
│   ├── upload_routes.py               # Document ingestion + background PageIndex
│   ├── score_routes.py                # LightGBM scoring
│   ├── cam_routes.py                  # Gemini 2.0 Flash CAM synthesis
│   ├── chatbot_routes.py              # Credit Intelligence Chatbot
│   ├── recommendation_routes.py       # SHAP counterfactuals
│   └── regulatory_routes.py          # Google News crawl
│
├── ml_engine/                         # Machine Learning Core
│   ├── features.py                    # 6 ML feature engineering
│   ├── model.py                       # LightGBM predictor
│   ├── explain.py                     # SHAP TreeExplainer
│   ├── gst_reconciler.py              # GST fraud detection
│   ├── smart_parser.py                # Gemini 2.0 Flash LLM extraction
│   └── pageindex_extractor.py         # PageIndex chatbot integration
│
├── ocr_pipeline/                      # Document extraction
│   ├── ocr_utils.py                   # Smart routing (Sarvam → Gemini → fallback)
│   └── sarvam_client.py               # Sarvam Vision API client
│
├── chatbot/                           # Credit Intelligence Chatbot
│   ├── credit_chatbot.py              # PageIndex + GPT-4o Mini chain
│   └── context_builder.py             # Rich credit context builder
│
├── research_agent/                    # External Intelligence
│   └── regulatory_crawler.py          # Google News RSS crawl
│
├── mock_documents/                    # Test documents
│   ├── mock_annual_report.pdf         # Sharma Textile Mills FY2025
│   ├── mock_bank_statement.pdf        # HDFC Bank Statement
│   ├── mock_gstr3b.pdf                # GSTR-3B Return
│   ├── mock_gstr2a.pdf                # GSTR-2A Return
│   ├── mock_sanction_letter.pdf       # SBI Sanction Letter
│   └── zee/                           # Zee Entertainment test documents
│
└── README.md
```

---

## Quick Start — Test with Mock Documents

### Step 1 — Open the Live App

Go to: **https://intelli-credit-d.vercel.app/**

### Step 2 — Download Mock Documents

All 5 test documents are in the `/mock_documents/` folder:

```
mock_documents/
├── mock_annual_report.pdf
├── mock_bank_statement.pdf
├── mock_gstr3b.pdf
├── mock_gstr2a.pdf
└── mock_sanction_letter.pdf
```

### Step 3 — Run Through the Pipeline

1. **Document Ingestion** — Upload all 5 PDFs → Click **"Run Smart Pipeline"**
   - Annual Report: Revenue ₹42.50Cr | EBITDA ₹6.10Cr | Net Worth ₹14Cr
   - Bank Statement: Credits ₹3.55Cr | Closing ₹12.45L
   - GSTR-3B: Turnover ₹3.85Cr | ITC Claimed ₹58.00L
   - GSTR-2A: ITC Available ₹42.00L | Suppliers: 34
   - Sanction Letter: Exposure ₹5.00Cr | Rate 11.5% | CASH CREDIT

2. **External Intelligence** — Google News crawl fires automatically
   - Expected: 0 adverse findings for Sharma Textile → legal_flag_count unchanged

3. **Feature Intelligence** — 6 feature cards computed
   - GST Bank Match: **0.58 — FRAUD RISK DETECTED** (3 flags)
   - Debt-Equity: **0.586 — HEALTHY LEVERAGE**
   - Working Capital: **₹5.80Cr — POSITIVE BUFFER**

4. **Credit Scoring** — Click **"Run ML Scoring Engine"**
   - Expected: Score **91 / APPROVE**
   - Loan terms: ₹7.65Cr @ 10% for 12 months

5. **Qualitative Adjustments** — Management = Average, Litigation = Yes, Industry = Favorable
   - Expected: Score drops to ~72 with live animation

6. **CAM Generation** — Click **"Synthesize CAM Document"**
   - Expected: Full CAM PDF with APPROVE decision, ₹7.65Cr limit
   - Includes: Auditor opinion, revenue trend FY2023→FY2025, SHAP drivers

7. **Credit Chatbot** — Ask *"Why was the GST score 0.58?"*
   - Expected: Specific answer citing -20pts, -7pts, -15pts with source badge

---

## Mock Documents — Hidden Signals

| Document | Key Data | Hidden Signal |
|----------|----------|---------------|
| `mock_annual_report.pdf` | Revenue ₹42.50Cr, Net Worth ₹14Cr, Debt ₹8.2Cr | Unqualified auditor opinion, 3-year growth trend |
| `mock_bank_statement.pdf` | Credits ₹3.55Cr, Closing ₹12.45L | 3x round ₹50L transactions → SUSPICIOUS_TRANSACTIONS |
| `mock_gstr3b.pdf` | Turnover ₹3.85Cr, ITC Claimed ₹58L | ITC claimed > available → CIRCULAR_TRADING_RISK |
| `mock_gstr2a.pdf` | ITC Available ₹42L, 34 suppliers | 38.1% ITC gap confirmed |
| `mock_sanction_letter.pdf` | ₹5Cr CC at 11.5% from SBI | Existing exposure benchmark |

Expected output: Credit Score **91 / APPROVE** | Loan **₹7.65Cr @ 10% p.a.** | Tenure **12 months**

---

## Full Setup Guide

### Prerequisites

- Python 3.9+
- Node.js 18+
- Tesseract OCR (`sudo apt install tesseract-ocr` on Linux)
- Supabase account
- OpenRouter API key (for Gemini 2.0 Flash + GPT-4o Mini)
- Sarvam AI API key
- PageIndex API key

### Backend Setup

```bash
git clone https://github.com/Pratiksawant14/Intelli-Credit.git
cd Intelli-Credit

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env:
# SUPABASE_URL=your_supabase_url
# SUPABASE_KEY=your_supabase_anon_key
# OPENAI_API_KEY=sk-or-v1-xxxx  (OpenRouter key)
# SARVAM_API_KEY=your_sarvam_key
# PAGEINDEX_API_KEY=your_pageindex_key
# JWT_SECRET=your_jwt_secret

uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install

cp .env.example .env.local
# VITE_API_BASE_URL=http://localhost:8000

npm run dev
```

### Verify Installation

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok", "model": "loaded", "version": "1.0"}
```

---

## Live Links

| Resource | URL |
|----------|-----|
| 🌐 Live Application | https://intelli-credit-d.vercel.app/ |
| 💻 GitHub Repository | https://github.com/Pratiksawant14/Intelli-Credit |
| 🎥 Demo Video | https://drive.google.com/file/d/1RRicK-j2nS4Srpwnlw1I0AEn6fjhwJnz/view?usp=sharing |

---

> *"Intelli-Credit doesn't just answer 'Should we lend?' — it answers 'WHY — with evidence.'"*
