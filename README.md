# Autonomous Accounts Payable (AP) Invoice Processing Engine

An end-to-end automated invoice processing and 2-way matching engine that transforms unstructured vendor PDF invoices into auditable procurement decisions (`AUTO_APPROVED`, `REVIEW_REQUIRED`, `REJECTED`).

 **Live Deployment:** [https://zamp-invoice-processing.onrender.com](https://zamp-invoice-processing.onrender.com)  

---

## 1. Problem Overview

Accounts Payable (AP) teams in mid-sized to enterprise organizations receive hundreds of vendor invoices each month—predominantly as email attachments in varying PDF formats. Human review is slow, prone to fatigue, and vulnerable to costly financial mistakes:

- **Layout & Format Diversity:** Clean digital PDFs, scanned/degraded images, varying table layouts, embedded vs. separated taxes, and explicit vs. implied PO references.
- **Complex Procurement Logic:** Matching invoices against purchase orders requires enforcing contract unit rates, multi-line tolerances (e.g., $\pm 2.0\%$), split-PO partial shipments, and preventing duplicate disbursements.
- **Unstructured to Structured Decisioning:** Systems must not only extract line items, but also authenticate the vendor, perform line-by-line reconciliation, check historical ledgers, and explain every decision with an immutable audit trail.

This engine solves these challenges through a hybrid architecture combining LLM semantic parsing (Azure OpenAI GPT-4o / Google Gemini) with deterministic financial validation rules and a stateful ERP procurement database.

---

## 2. Architecture & Ingestion Pipeline

The pipeline processes invoices through 6 observable telemetry stages:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   INVOICE PROCESSING PIPELINE                                   │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
  [Stage 1: Document Ingestion]
     │── Ingests PDF streams via drag-and-drop upload or preloaded test scenarios
     └── Extracts raw text streams, structural coordinates, and document metadata
  [Stage 2: Financial Entity & Line Item Extraction]
     │── Primary: Cloud LLM (Azure OpenAI GPT-4o / Google Gemini) for semantic schema extraction
     └── Resilient Fallback: Autonomous Cognitive Parser (deterministic regex & layout heuristics)
  [Stage 3: Vendor Master Authentication]
     │── Authenticates legal vendor against ERP Vendor Master (tax IDs, payment terms, DBA aliases)
     └── Blocks rogue / unapproved suppliers before financial evaluation
  [Stage 4: Purchase Order 2-Way Reconciliation]
     │── Reconciles invoice line items against active PO items, contract rates, and quantities
     └── Handles partial shipments, remaining budget tracking, and contract rate tolerances
  [Stage 5: Autonomous Policy Checks]
     │── CHK-001: Vendor Master Registration
     │── CHK-002: Historical Duplicate Invoice Detection
     │── CHK-003: PO Authorization & Balance Availability
     │── CHK-003-VEND: Cross-Vendor PO Misappropriation
     │── CHK-004: Tolerance & Contract Pricing Boundaries
     │── CHK-005: Mandatory Invoice Metadata Completeness
     └── CHK-006: Document Structure & Line Item Fidelity
  [Stage 6: Decision & Action Dispatch]
     │── AUTO_APPROVED   ──> Generates ERP Webhook / ACH disbursement payload
     │── REVIEW_REQUIRED ──> Flags variance, highlights lines in red, auto-drafts vendor inquiry email
     └── REJECTED        ──> Halts payment, logs fraud/duplicate prevention in ERP ledger
```

---

## 3. Supported Scenarios & Edge Cases

The system ships with 8 realistic, pre-generated invoice PDFs covering standard operations and real-world edge cases:

| Scenario | Sample Invoice | Operational Challenge | Engine Behavior | Verdict |
| :--- | :--- | :--- | :--- | :---: |
| **Happy Path** | `1_Happy_Path_Apex_Exact_Match.pdf` | Clean annual software invoice matching authorized PO-2026-101. | 100% exact 2-way match across line items, prices, and quantities. | `AUTO_APPROVED` |
| **Price Breach** | `2_Edge_Case_Price_Breach_CloudScale.pdf` | Vendor increases compute rate from $1,200 to $1,400 (+16.7%), +$800 over PO. | Breaches allowable 2.0% ($30) tolerance limit; highlights variance in red and auto-drafts dispute email. | `REVIEW_REQUIRED` |
| **Split PO Delivery** | `3_Edge_Case_Split_PO_Partial_Freight.pdf` | Freight shipment 1 of 3 billed at $5,000 against a $15,000 master contract. | Validates partial delivery; decrements PO balance to $10,000 in ERP ledger. | `AUTO_APPROVED` |
| **Duplicate Prevention** | `4_Edge_Case_Duplicate_CyberGuard.pdf` | Resubmission of invoice #INV-CG-9942 already settled in prior accounting cycle. | Intercepts duplicate invoice # in ERP paid history; blocks duplicate disbursement. | `REJECTED` |
| **Unapproved Vendor** | `5_Edge_Case_Unapproved_Vendor_Missing_PO.pdf` | Invoice from unapproved vendor with no PO reference. | Fails Vendor Master authentication; halts unbudgeted payment. | `REJECTED` |
| **Within Tolerance** | `6_Edge_Case_Minor_Variance_Within_Tolerance.pdf` | $18.50 ground freight surcharge added to a $3,250 hardware order (+0.57%). | Evaluates within allowable tolerance threshold (+/-2.0% / $25.00); auto-approves with audit note. | `AUTO_APPROVED` |
| **Cross-Vendor PO** | `7_Edge_Case_Cross_Vendor_PO.pdf` | CloudScale attempts to bill against PO-2026-101 legally issued to Apex Software. | Detects cross-vendor PO misappropriation; prevents unauthorized budget drawdown. | `REJECTED` |
| **Missing Invoice #** | `8_Edge_Case_Missing_Invoice_Number.pdf` | Vendor document omits mandatory Invoice Number identifier. | Flags completeness violation; halts ERP posting pending vendor re-issue. | `REVIEW_REQUIRED` |

---

## 4. Key Capabilities

- **Hybrid Extraction Architecture:** Supports live cloud LLMs (Azure OpenAI GPT-4o, Google Gemini) for semantic understanding, backed by an autonomous local parser that prevents pipeline downtime if external APIs are unreachable.
- **Stateful ERP Database:** Built-in SQLite procurement database (`ap_procurement.db`) modeling active purchase orders, approved vendor registries, and historical payment ledgers.
- **Human-In-The-Loop (HITL) Review:** Interactive review modal allowing AP specialists to inspect line-item discrepancies, enter audit justifications, and execute manual overrides.
- **AP Analytics Dashboard:** Real-time visibility into auto-approval rates, total disbursed spend, prevented duplicate/fraud volume, and downloadable CSV audit logs.
- **Embedded PDF Viewer:** Full visual preview of the original vendor PDF alongside extracted entities and reconciliation tables.

---

## 5. Technology Stack

- **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Document Processing:** PyPDF (stream extraction), ReportLab (test generation)
- **Database:** SQLite 3 (transactional, persistent)
- **AI / LLM Integration:** Azure OpenAI (GPT-4o), Google Gemini Developer API
- **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons

---

## 6. Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI application, routing, and pipeline orchestration
│   ├── models.py               # Pydantic schemas (Invoice, LineItem, PO, Decision)
│   ├── database.py             # SQLite manager, ERP tables, and historical ledger
│   ├── extractor.py            # Optical & heuristic layout extractor
│   ├── llm_engine.py           # Azure OpenAI / Gemini LLM integration with fallback
│   ├── matching_engine.py      # 2-way PO line item reconciliation & policy checks
│   ├── decision_engine.py      # Decision logic, rationale generation, and action dispatch
│   ├── generator.py            # Synthetic PDF invoice generator for test scenarios
│   └── sample_invoices/        # Pre-generated PDF test documents
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main layout, navigation, and state management
│   │   ├── components/
│   │   │   ├── LiveRunStudio.jsx   # Live pipeline stepper & reconciliation view
│   │   │   ├── DashboardView.jsx   # AP metrics, run history, and CSV export
│   │   │   ├── ErpExplorer.jsx     # ERP Master Explorer (POs, Vendors, Ledger)
│   │   │   ├── ReviewModal.jsx     # Human-In-The-Loop specialist override modal
│   │   │   └── AiConfigModal.jsx   # LLM provider & API key settings modal
│   │   └── index.css           # Tailwind CSS styles
│   └── dist/                   # Production-compiled React frontend
├── run_app.py                  # Single-command launcher (backend + frontend)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable configuration template
└── README.md
```

---

## 7. Quickstart Guide

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ (optional, only needed if rebuilding frontend assets)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/VK180/Zamp-Invoice-Processing.git
   cd Zamp-Invoice-Processing
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

   Configure your LLM provider credentials in `.env`:
   ```env
   # OpenAI / Azure OpenAI Configuration
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your-api-key-here
   OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai/v1
   LLM_MODEL=gpt-4o

   # Or Google Gemini Configuration
   # LLM_PROVIDER=gemini
   # GEMINI_API_KEY=your-gemini-key-here
   # LLM_MODEL=gemini-flash-lite-latest

   # Policy Configuration
   AP_TOLERANCE_PERCENTAGE=2.0
   ```

   *(Note: If no API key is provided, the system runs automatically using the Autonomous Cognitive Parser).*

---

### Running the Application

Launch the unified server with a single command:

```bash
python run_app.py
```

The application will be live at:
- **Live Cloud Deployment:** [https://zamp-invoice-processing.onrender.com](https://zamp-invoice-processing.onrender.com)
- **Local Application:** `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation:** `http://127.0.0.1:8000/docs`

---

## 8. API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/invoices/process` | Upload and process an invoice PDF document |
| `POST` | `/api/invoices/process-sample` | Process one of the 8 pre-loaded scenario invoices |
| `GET` | `/api/invoices/history` | Retrieve processing history and aggregate AP metrics |
| `GET` | `/api/invoices/export/csv` | Download complete audit trail as CSV |
| `POST` | `/api/invoices/{id}/review` | Submit human specialist review action / override |
| `GET` | `/api/procurement/pos` | Retrieve active Purchase Orders and balances |
| `GET` | `/api/procurement/vendors` | Retrieve Vendor Master directory |
| `GET` | `/api/procurement/history-ledger`| Retrieve historical paid invoices ledger |
| `POST` | `/api/reset` | Reset ERP balances and run history to baseline |
| `GET` | `/api/llm/config` | Retrieve current LLM provider and status |
| `POST` | `/api/llm/config` | Update LLM configuration dynamically |
