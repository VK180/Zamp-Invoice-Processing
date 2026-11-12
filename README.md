# Zamp AI Solutions Analyst Case Study — PS-1: Invoice Processing (PDF to Decision)

> **Submission for Zamp AI Solutions Analyst Placement Case Study (2026)**  
> **Author:** PV Sai Subhash  
> **Problem Statement:** PS-1 (Finance / AP) — *From PDF to Decision*  
> **Stack:** Python 3.11 (FastAPI, PyPDF, ReportLab, Pydantic) + React (Vite, Tailwind CSS, Lucide Icons)

---

## 1. Executive Summary: Why PS-1 & Why This Solution Gives an Unfair Edge

Zamp operates at the intersection of AI and mission-critical financial automation (sales tax, compliance, and accounts payable). In enterprise finance, errors carry direct financial liability: overpaying a price variance, disbursing duplicate funds, or approving ghost vendors directly damages the P&L.

### Why Choose PS-1?
1. **Direct Cultural & Product Fit with Zamp:** Finance and AP workflows are Zamp's core domain. Solving PS-1 directly proves domain mastery and commercial readiness.
2. **Objective Business ROI:** Unlike outreach copywriting (PS-3), AP automation has quantifiable financial metrics: duplicate fraud prevented ($ saved), percentage of zero-touch payments, and invoice processing cycle time reduced from days to under 200 milliseconds.
3. **Deterministic Rigor Over Hallucination:** In finance, LLMs should be used for unstructured document parsing, but **never** for financial math. This system combines hybrid optical parsing with deterministic 2-way matching, tolerance boundaries, and an immutable audit trail.

---

## 2. End-to-End System Architecture

The pipeline processes vendor invoices through 6 distinct, observable telemetry stages:

```
+---------------------------------------------------------------------------------------------------+
|                                 LIVE TELEMETRY PIPELINE (PS-1)                                   |
+---------------------------------------------------------------------------------------------------+
| [1. Ingestion]           -->  Accepts PDF uploads or 1-click synthetic invoices; streams bytes    |
| [2. Extraction]          -->  Hybrid parser extracts invoice #, dates, vendor, lines, taxes, totals|
| [3. Vendor Master Auth]  -->  Fuzzy alias lookup against ERP Master; validates Tax ID & Risk Tier |
| [4. 2-Way Match]         -->  Reconciles item codes, unit rates, quantities, and split PO balances|
| [5. Policy & Risk]       -->  Evaluates duplicate ledger, tolerance thresholds (+/-2%), dates     |
| [6. Decision & Action]   -->  AUTO_APPROVED, REVIEW_REQUIRED, or REJECTED + NetSuite webhook payload|
+---------------------------------------------------------------------------------------------------+
```

---

## 3. The 8 Built-In Test Scenarios & Edge Cases Matrix

As the prompt specifies: *"The edge cases you choose tell us how well you understand the problem."* This project provides 8 realistic test scenarios with pre-generated PDFs covering the core workflow and every real-world operational hazard:

| # | Scenario Title | File Name | Operational Challenge | Engine Behavior | Final Verdict |
|---|---|---|---|---|---|
| **0** | **Happy Path** | `1_Happy_Path_Apex_Exact_Match.pdf` | Clean annual software invoice matching PO-2026-101. | 100% 2-way match on lines & rates; approved vendor. | `AUTO_APPROVED` |
| **1** | **Unit Price Inflation** | `2_Edge_Case_Price_Breach_CloudScale.pdf` | Compute rate increased from $1,200 to $1,400 (+16.7%). Invoice is +$800 over PO. | Breaches 2.0% ($30) tolerance limit. Highlights item in red; auto-drafts vendor dispute email. | `REVIEW_REQUIRED` |
| **2** | **Split PO / Partial Delivery** | `3_Edge_Case_Split_PO_Partial_Freight.pdf` | Freight shipment 1 of 3 billed at $5,000 on a $15,000 master PO. | Recognizes valid partial fulfillment; decrements PO balance to $10,000 in ERP. | `AUTO_APPROVED` |
| **3** | **Duplicate Fraud Prevention** | `4_Edge_Case_Duplicate_CyberGuard.pdf` | Resubmission of invoice INV-CG-9942 already settled via ACH. | Intercepts duplicate invoice # and amount; blocks double payment. | `REJECTED` |
| **4** | **Rogue Spend & Missing PO** | `5_Edge_Case_Unapproved_Vendor_Missing_PO.pdf` | Invoice from unapproved foreign vendor with no PO reference. | Fails Vendor Master authentication; halts unbudgeted disbursement. | `REJECTED` |
| **5** | **Tolerance Absorption** | `6_Edge_Case_Minor_Variance_Within_Tolerance.pdf` | $18.50 ground freight added to $3,250 hardware PO (+0.57%). | Within PO allowable tolerance (+/-2.0% / $25.00). Auto-approves with audit note. | `AUTO_APPROVED` |
| **6** | **Cross-Vendor PO Hijacking** | `7_Edge_Case_Cross_Vendor_PO.pdf` | CloudScale attempts to bill against PO-2026-101 issued to Apex Software. | Detects cross-vendor PO misappropriation; blocks unauthorized drawdown. | `REJECTED` |
| **7** | **Missing Invoice Number** | `8_Edge_Case_Missing_Invoice_Number.pdf` | Invoice document omits mandatory Invoice Number identifier. | Flags data completeness violation; halts ERP posting pending vendor re-issue. | `REVIEW_REQUIRED` |

---

## 4. Quickstart Guide (Running Locally)

### Prerequisites
- Python 3.10+
- Node.js 18+ (Node 20+ supported)

### 1-Click Launch (Recommended)
Simply execute the launcher script in the workspace root:

```bash
# On Windows PowerShell:
python run_app.py

# Or run the batch file:
./start.bat
```

The script automatically:
1. Generates all 6 realistic test invoice PDFs via ReportLab.
2. Serves both the FastAPI backend and compiled React UI simultaneously on:
   - **Live Web Interface:** `http://127.0.0.1:8000`
   - **Interactive API Docs:** `http://127.0.0.1:8000/docs`

---

## 5. Deliverable 2: 5-Minute Demo Video Script & Storyboard

This script is structured second-by-second to record your Loom screen recording:

* **[0:00 – 0:45] Context & Problem Statement**
  * *Narration:* "Hi everyone! I’m presenting my solution for Zamp’s PS-1: Accounts Payable Invoice Intelligence. Mid-sized companies receive hundreds of PDF invoices monthly. Tired AP staff waste hours comparing numbers against purchase orders in spreadsheets, leading to expensive mistakes: overpaying price increases, duplicate disbursements, or paying unapproved vendors. Here is our live system."
* **[0:45 – 1:45] Happy Path (Apex Software)**
  * *Narration:* "Clicking the 'Happy Path' button: in real-time, the 6-stage telemetry stepper ingests the PDF, extracts the line items and metadata, authenticates the vendor in ERP Master, performs 2-way matching against PO-2026-101, validates tolerance and duplicate checks, and outputs an AUTO-APPROVED verdict with confidence 99%."
  * *On Screen:* Point out the green verdict badge, line item reconciliation table, and the NetSuite ERP JSON payload.
* **[1:45 – 2:45] Edge Case 1: Price Breach (CloudScale)**
  * *Narration:* "What happens on a Friday afternoon when a vendor quietly hikes prices? I trigger CloudScale. The vendor billed compute at $1,400 instead of our contracted $1,200 (+16.7%), causing an $800 breach over our PO’s 2% tolerance limit. Notice the system doesn’t crash or blindly pay: it halts, flags REVIEW REQUIRED, highlights the line variance in red, and auto-generates a ready-to-send dispute email to the vendor."
  * *On Screen:* Show the red 'Price Breach' tag in the line item table and switch to the 'Vendor Inquiry Draft' tab.
* **[2:45 – 3:30] Edge Cases 2 & 3: Split POs & Duplicate Fraud**
  * *Narration:* "Vendors frequently split POs across multiple shipments. Triggering Global Freight: $5,000 billed against a $15,000 master PO. The engine auto-approves and updates the remaining balance in ERP to $10,000. Next, CyberGuard: an invoice resubmitted after being paid last month. Our historical ledger catches it instantly, rejecting the $6,000 duplicate before double payment occurs."
* **[3:30 – 4:45] Dashboard & Human-in-the-Loop Override**
  * *Narration:* "Finally, switching to our AP Operations Dashboard: CFOs and controllers get real-time visibility into auto-approval rates, total spend disbursed, and fraud prevented. If an AP Specialist receives manager sign-off for that CloudScale price hike, they simply click 'Review', enter the audit authorization, and commit the override directly to ERP."

---

## 6. Live Interview & Technical Defense FAQ

### Q1: Why not let an LLM make the financial decision directly?
> **Answer:** In enterprise finance, LLMs should be used for *unstructured perception* (extracting messy layouts and noisy OCR text), but **never** for financial math or disbursement decisions. Price calculations, duplicate checks, and tolerance bounds must be enforced by verified deterministic rules to eliminate hallucinations and ensure 100% audit compliance.

### Q2: How does this scale to 50,000 invoices per month?
> **Answer:** Ingestion and OCR parsing run as asynchronous worker tasks (e.g. Celery / AWS SQS). Rule evaluation runs in `<10ms` per invoice in memory. High-confidence happy paths (~70-80%) auto-disburse straight to ERP, while human AP analysts only touch the 20% exception queue.

### Q3: How do you handle non-PO invoices (e.g. utilities, rent)?
> **Answer:** In the fallback PO matching stage, if no PO reference is found, the system checks whether the vendor has a recurring non-PO spend authorization policy (e.g., standard monthly rent up to $10k). If yes, it routes to GL coding approval; if no, it flags for AP manager sign-off.
