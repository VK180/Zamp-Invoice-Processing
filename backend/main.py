import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)
import time
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import csv
import io

try:
    from backend.models import (
        ExtractedInvoice, DecisionStatus, StageStatus, StageLog,
        RunRecord, DecisionOutput
    )
    from backend.procurement_db import db
    from backend.database import db_manager
    from backend.llm_engine import llm_engine
    from backend.extractor import extractor
    from backend.matching_engine import matching_engine
    from backend.decision_engine import decision_engine
except ImportError:
    from models import (
        ExtractedInvoice, DecisionStatus, StageStatus, StageLog,
        RunRecord, DecisionOutput
    )
    from procurement_db import db
    from database import db_manager
    from llm_engine import llm_engine
    from extractor import extractor
    from matching_engine import matching_engine
    from decision_engine import decision_engine

app = FastAPI(
    title="Zamp AP Invoice Processing Intelligence API",
    description="Automated 2-way matching, tolerance policy evaluation, and decision engine for vendor invoices",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "sample_invoices")
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Run history in-memory store
RUN_HISTORY: List[RunRecord] = []

SAMPLE_SCENARIOS = [
    {
        "filename": "1_Happy_Path_Apex_Exact_Match.pdf",
        "title": "Happy Path: Clean 100% 2-Way Match",
        "vendor": "Apex Software Solutions LLC",
        "po_number": "PO-2026-101",
        "total": 12500.00,
        "expected_status": "AUTO_APPROVED",
        "badge_color": "emerald",
        "description": "Standard software contract invoice. All line items, unit prices, and PO references match ERP records exactly with an approved vendor."
    },
    {
        "filename": "2_Edge_Case_Price_Breach_CloudScale.pdf",
        "title": "Edge Case 1: Unit Price Inflation > Tolerance",
        "vendor": "CloudScale Infrastructure Corp",
        "po_number": "PO-2026-102",
        "total": 9200.00,
        "expected_status": "REVIEW_REQUIRED",
        "badge_color": "amber",
        "description": "Vendor billed compute instances at $1,400/unit instead of contract $1,200/unit (+16.7%). Total exceeds authorized PO by +$800 (+9.5%), breaching the 2% tolerance limit."
    },
    {
        "filename": "3_Edge_Case_Split_PO_Partial_Freight.pdf",
        "title": "Edge Case 2: Split PO / Partial Delivery",
        "vendor": "Global Freight & Express",
        "po_number": "PO-2026-103",
        "total": 5000.00,
        "expected_status": "AUTO_APPROVED",
        "badge_color": "blue",
        "description": "Partial delivery 1 of 3 billed at $5,000 against a $15,000 master PO. System auto-approves and dynamically updates remaining PO balance to $10,000."
    },
    {
        "filename": "4_Edge_Case_Duplicate_CyberGuard.pdf",
        "title": "Edge Case 3: Duplicate Invoice / Fraud Prevention",
        "vendor": "CyberGuard Security Partners",
        "po_number": "PO-2026-105",
        "total": 6000.00,
        "expected_status": "REJECTED",
        "badge_color": "rose",
        "description": "Resubmission of invoice INV-CG-9942 which was already settled via ACH. System detects duplicate across historical ledger and rejects before double payment occurs."
    },
    {
        "filename": "5_Edge_Case_Unapproved_Vendor_Missing_PO.pdf",
        "title": "Edge Case 4: Rogue Spend & Unapproved Vendor",
        "vendor": "Shadow AI Labs Inc",
        "po_number": "None",
        "total": 4200.00,
        "expected_status": "REJECTED",
        "badge_color": "rose",
        "description": "Rogue vendor not registered in ERP Vendor Master with missing PO reference. System halts processing, flags compliance risk, and auto-drafts vendor inquiry."
    },
    {
        "filename": "6_Edge_Case_Minor_Variance_Within_Tolerance.pdf",
        "title": "Edge Case 5: Minor Freight Surcharge within Tolerance",
        "vendor": "Nexus Office Supplies & Hardware",
        "po_number": "PO-2026-104",
        "total": 3268.50,
        "expected_status": "AUTO_APPROVED",
        "badge_color": "emerald",
        "description": "Invoice adds an $18.50 ground freight surcharge on a $3,250 order (+0.57% variance). Because PO permits up to 2.0% ($25.00), it auto-approves with an audit note."
    },
    {
        "filename": "7_Edge_Case_Cross_Vendor_PO.pdf",
        "title": "Edge Case 6: Cross-Vendor PO Misappropriation",
        "vendor": "CloudScale Infrastructure Corp",
        "po_number": "PO-2026-101",
        "total": 12500.00,
        "expected_status": "REJECTED",
        "badge_color": "rose",
        "description": "CloudScale bills against PO-2026-101 which is legally authorized for Apex Software Solutions. Cross-vendor billing is strictly rejected."
    },
    {
        "filename": "8_Edge_Case_Missing_Invoice_Number.pdf",
        "title": "Edge Case 7: Missing Mandatory Invoice Number",
        "vendor": "Apex Software Solutions LLC",
        "po_number": "PO-2026-101",
        "total": 12500.00,
        "expected_status": "REVIEW_REQUIRED",
        "badge_color": "amber",
        "description": "Invoice omits mandatory Invoice Number identifier. ERP posting halted; requires vendor correction before remittance."
    }
]

class ProcessSampleRequest(BaseModel):
    sample_filename: str

class ReviewActionRequest(BaseModel):
    action: str  # "APPROVE_OVERRIDE", "REJECT", "REQUEST_CORRECTION"
    notes: str
    reviewer: str = "AP Specialist"

@app.api_route("/api/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat(), "service": "Zamp AP Decision Engine"}

@app.get("/api/samples")
def get_sample_scenarios():
    return SAMPLE_SCENARIOS

@app.get("/api/samples/{filename:path}/pdf")
@app.get("/api/pdf/{filename:path}")
def serve_sample_pdf(filename: str):
    clean_name = os.path.basename(filename)
    path = os.path.join(SAMPLES_DIR, clean_name)
    if not os.path.exists(path):
        path = os.path.join(UPLOADS_DIR, clean_name)
    if not os.path.exists(path):
        # Fallback: search for partial match in uploads or samples
        for d in [UPLOADS_DIR, SAMPLES_DIR]:
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.lower().endswith(clean_name.lower()) or clean_name.lower() in f.lower():
                        path = os.path.join(d, f)
                        break
            if os.path.exists(path):
                break
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"PDF file '{clean_name}' not found")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=os.path.basename(path),
        content_disposition_type="inline"
    )

@app.get("/api/procurement/pos")
def get_purchase_orders():
    return db.get_all_pos()

@app.get("/api/procurement/vendors")
def get_vendors():
    return db.get_all_vendors()

@app.get("/api/procurement/history-ledger")
def get_historical_ledger():
    return db.get_historical_invoices()

@app.post("/api/reset")
def reset_system():
    db.reset()
    return {"message": "SQLite Procurement database and run history successfully reset to baseline."}

class LLMConfigRequest(BaseModel):
    provider: str  # "gemini", "openai", "autonomous"
    api_key: str
    model_name: Optional[str] = None

@app.get("/api/llm/config")
def get_llm_config():
    return llm_engine.get_config()

@app.post("/api/llm/config")
def update_llm_config(body: LLMConfigRequest):
    llm_engine.update_config(body.provider, body.api_key, body.model_name)
    return llm_engine.get_config()

def execute_pipeline(pdf_path: str, target_filename: str, pdf_url: Optional[str] = None) -> RunRecord:
    """
    Core pipeline logic executed for any invoice PDF.
    """
    stages: List[StageLog] = []

    # =========================================================================
    # STAGE 1: INGESTION & DOCUMENT PARSING
    # =========================================================================
    s1_start = time.time()
    try:
        file_size_kb = os.path.getsize(pdf_path) / 1024.0
        stages.append(StageLog(
            stage_id="stage_1_ingest",
            stage_name="Document Ingestion & OCR Parsing",
            status=StageStatus.SUCCESS,
            message=f"PDF ingested successfully ({file_size_kb:.1f} KB). Text streams and layout tokens extracted.",
            duration_ms=int((time.time() - s1_start) * 1000),
            details={"filename": target_filename, "file_size_kb": round(file_size_kb, 1)}
        ))
    except Exception as e:
        stages.append(StageLog(
            stage_id="stage_1_ingest",
            stage_name="Document Ingestion & OCR Parsing",
            status=StageStatus.FAILED,
            message=f"Failed to ingest document: {str(e)}",
            duration_ms=int((time.time() - s1_start) * 1000)
        ))
        raise HTTPException(status_code=500, detail=f"Ingestion failure: {str(e)}")

    # =========================================================================
    # STAGE 2: DATA & LINE ITEM EXTRACTION
    # =========================================================================
    s2_start = time.time()
    try:
        extracted: ExtractedInvoice = extractor.extract_from_pdf(pdf_path)
        extracted, llm_telemetry = llm_engine.extract_with_llm(extracted.raw_text_snippet or "", extracted)
        stages.append(StageLog(
            stage_id="stage_2_extract",
            stage_name="Financial Entity & Line Item Extraction (LLM + Optical)",
            status=StageStatus.SUCCESS,
            message=(
                f"Extracted Invoice #{extracted.invoice_number or 'UNKNOWN'}, "
                f"Date: {extracted.invoice_date or 'N/A'}, "
                f"PO Ref: {extracted.po_reference or 'None'}, "
                f"Total: ${extracted.total_amount:,.2f} with {len(extracted.line_items)} line item(s). "
                f"Method: {extracted.extraction_method}."
            ),
            duration_ms=int((time.time() - s2_start) * 1000),
            details={
                "invoice_number": extracted.invoice_number,
                "invoice_date": extracted.invoice_date,
                "due_date": extracted.due_date,
                "vendor_name": extracted.vendor_name,
                "total_amount": extracted.total_amount,
                "line_items_count": len(extracted.line_items),
                "confidence_score": extracted.confidence_score,
                "llm_telemetry": llm_telemetry
            }
        ))
    except Exception as e:
        stages.append(StageLog(
            stage_id="stage_2_extract",
            stage_name="Financial Entity & Line Item Extraction (LLM + Optical)",
            status=StageStatus.FAILED,
            message=f"Extraction failed: {str(e)}",
            duration_ms=int((time.time() - s2_start) * 1000)
        ))
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")

    # =========================================================================
    # STAGE 3: VENDOR MASTER VERIFICATION
    # =========================================================================
    s3_start = time.time()
    vendor, vendor_confidence = db.find_vendor(extracted.vendor_name)
    if vendor and vendor.is_approved:
        stages.append(StageLog(
            stage_id="stage_3_vendor",
            stage_name="Vendor Master & ERP Verification",
            status=StageStatus.SUCCESS,
            message=f"Vendor '{vendor.vendor_name}' authenticated in ERP Vendor Master (ID: {vendor.vendor_id}, Match Confidence: {vendor_confidence*100:.0f}%).",
            duration_ms=int((time.time() - s3_start) * 1000),
            details={"vendor_id": vendor.vendor_id, "official_name": vendor.vendor_name, "risk_rating": vendor.risk_rating.value}
        ))
    elif vendor and not vendor.is_approved:
        stages.append(StageLog(
            stage_id="stage_3_vendor",
            stage_name="Vendor Master & ERP Verification",
            status=StageStatus.FAILED,
            message=f"Vendor '{vendor.vendor_name}' found but is marked as UNAPPROVED/BLOCKED (Risk Rating: {vendor.risk_rating.value}).",
            duration_ms=int((time.time() - s3_start) * 1000),
            details={"vendor_id": vendor.vendor_id, "is_approved": False}
        ))
    else:
        stages.append(StageLog(
            stage_id="stage_3_vendor",
            stage_name="Vendor Master & ERP Verification",
            status=StageStatus.WARNING,
            message=f"Vendor '{extracted.vendor_name or 'Unspecified'}' not registered in ERP Vendor Master.",
            duration_ms=int((time.time() - s3_start) * 1000),
            details={"vendor_found": False}
        ))

    # =========================================================================
    # STAGE 4: PURCHASE ORDER RECONCILIATION
    # =========================================================================
    s4_start = time.time()
    po = db.get_po(extracted.po_reference)
    po_inferred_note = None

    if not po and extracted.vendor_name:
        po, po_inferred_note = db.find_po_fallback(extracted.vendor_name, extracted.total_amount)

    reconciliation = matching_engine.reconcile(extracted, po)
    
    if reconciliation.po_found:
        msg = f"Linked to PO {po.po_number} (PO Total: ${po.total_amount:,.2f}, Remaining: ${reconciliation.po_remaining_before:,.2f}). "
        if reconciliation.tolerance_breached:
            po_status = StageStatus.WARNING
            msg += f"Variance of ${reconciliation.total_variance:+,.2f} ({reconciliation.variance_percentage:+.2f}%) exceeds tolerance threshold!"
        elif reconciliation.is_partial_fulfillment:
            po_status = StageStatus.SUCCESS
            msg += f"Partial delivery verified. Remaining PO balance will be ${reconciliation.po_remaining_after:,.2f}."
        else:
            po_status = StageStatus.SUCCESS
            msg += "Line items and totals match PO terms."

        stages.append(StageLog(
            stage_id="stage_4_po",
            stage_name="Purchase Order 2-Way Reconciliation",
            status=po_status,
            message=msg,
            duration_ms=int((time.time() - s4_start) * 1000),
            details={
                "po_number": po.po_number,
                "po_total": po.total_amount,
                "invoice_total": extracted.total_amount,
                "total_variance": reconciliation.total_variance,
                "tolerance_breached": reconciliation.tolerance_breached,
                "is_partial": reconciliation.is_partial_fulfillment,
                "inferred_note": po_inferred_note
            }
        ))
    else:
        stages.append(StageLog(
            stage_id="stage_4_po",
            stage_name="Purchase Order 2-Way Reconciliation",
            status=StageStatus.WARNING,
            message=f"No matching active PO found for reference '{extracted.po_reference or 'None'}'.",
            duration_ms=int((time.time() - s4_start) * 1000),
            details={"po_reference": extracted.po_reference}
        ))

    # =========================================================================
    # STAGE 5: POLICY & RISK CHECKS
    # =========================================================================
    s5_start = time.time()
    policy_checks = matching_engine.evaluate_policies(extracted, vendor, po, reconciliation, db, po_inferred_note=po_inferred_note)
    failed_checks = [c for c in policy_checks if not c.passed]
    
    stages.append(StageLog(
        stage_id="stage_5_policy",
        stage_name="AP Policy & Duplicate Risk Verification",
        status=StageStatus.FAILED if any(c.severity == "CRITICAL" for c in failed_checks) else (StageStatus.WARNING if failed_checks else StageStatus.SUCCESS),
        message=f"Evaluated {len(policy_checks)} core AP rules. {len(policy_checks) - len(failed_checks)} passed, {len(failed_checks)} flagged.",
        duration_ms=int((time.time() - s5_start) * 1000),
        details={"checks_summary": [{"name": c.check_name, "passed": c.passed, "severity": c.severity} for c in policy_checks]}
    ))

    # =========================================================================
    # STAGE 6: DECISION ENGINE & ERP ACTION
    # =========================================================================
    s6_start = time.time()
    decision: DecisionOutput = decision_engine.evaluate(extracted, vendor, po, reconciliation, policy_checks)

    # If AUTO-APPROVED, update DB (record invoice and update PO balance)
    if decision.status == DecisionStatus.AUTO_APPROVED:
        db.record_approved_invoice(
            invoice_number=extracted.invoice_number or f"INV-{uuid.uuid4().hex[:6]}",
            po_number=po.po_number if po else None,
            vendor_name=extracted.vendor_name or "Unknown",
            amount=extracted.total_amount
        )

    stages.append(StageLog(
        stage_id="stage_6_decision",
        stage_name="Autonomous Decision & Action Generation",
        status=StageStatus.SUCCESS if decision.status == DecisionStatus.AUTO_APPROVED else (StageStatus.WARNING if decision.status == DecisionStatus.REVIEW_REQUIRED else StageStatus.FAILED),
        message=f"Outcome: {decision.status.value} (Confidence: {decision.confidence_score:.0f}%, Risk Score: {decision.risk_score}/100). {decision.recommended_action}",
        duration_ms=int((time.time() - s6_start) * 1000),
        details={"status": decision.status.value, "risk_score": decision.risk_score, "confidence": decision.confidence_score}
    ))

    # Generate AI Cognitive Auditor Insights
    ai_insights = llm_engine.generate_ai_audit_insights(
        extracted=extracted,
        po=po,
        reconciliation=reconciliation,
        vendor=vendor,
        decision_verdict=decision.status.value
    )

    # Compile Run Record
    run_record = RunRecord(
        id=f"RUN-{int(time.time()*1000)}-{uuid.uuid4().hex[:4]}",
        timestamp=datetime.utcnow().isoformat(),
        invoice_filename=target_filename,
        pdf_url=pdf_url,
        vendor_name=extracted.vendor_name or "Unknown Vendor",
        invoice_number=extracted.invoice_number or "UNSPECIFIED",
        invoice_total=extracted.total_amount,
        po_number=po.po_number if po else extracted.po_reference,
        decision_status=decision.status,
        decision_reason=decision.summary_reason,
        confidence_score=decision.confidence_score,
        stages=stages,
        reconciliation=reconciliation,
        policy_checks=policy_checks,
        extracted_data=extracted,
        vendor_notification_draft=decision.vendor_notification_draft,
        erp_payload=decision.erp_payload,
        ai_insights=ai_insights
    )

    # Persist in SQLite
    db_manager.record_run(run_record.model_dump())
    return run_record

@app.post("/api/invoices/process-sample")
def process_sample(body: ProcessSampleRequest):
    pdf_path = os.path.join(SAMPLES_DIR, body.sample_filename)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"Sample file '{body.sample_filename}' not found")
    return execute_pipeline(pdf_path, body.sample_filename, f"/api/samples/{body.sample_filename}/pdf")

@app.post("/api/invoices/process")
async def process_invoice(file: UploadFile = File(...)):
    target_filename = file.filename or "uploaded_invoice.pdf"
    saved_name = f"{uuid.uuid4().hex[:8]}_{target_filename}"
    pdf_path = os.path.join(UPLOADS_DIR, saved_name)
    with open(pdf_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return execute_pipeline(pdf_path, target_filename, f"/api/samples/{saved_name}/pdf")

@app.get("/api/invoices/history")
def get_run_history():
    all_runs = db_manager.get_all_runs()
    total_runs = len(all_runs)
    auto_approved = sum(1 for r in all_runs if r.get("decision_status") == "AUTO_APPROVED")
    review_required = sum(1 for r in all_runs if r.get("decision_status") == "REVIEW_REQUIRED")
    rejected = sum(1 for r in all_runs if r.get("decision_status") == "REJECTED")
    total_dollar_volume = sum(r.get("invoice_total", 0.0) for r in all_runs)
    approved_dollar_volume = sum(r.get("invoice_total", 0.0) for r in all_runs if r.get("decision_status") == "AUTO_APPROVED")
    duplicate_saved_volume = sum(r.get("invoice_total", 0.0) for r in all_runs if r.get("decision_status") == "REJECTED" and "Duplicate" in r.get("decision_reason", ""))

    return {
        "stats": {
            "total_runs": total_runs,
            "auto_approved": auto_approved,
            "review_required": review_required,
            "rejected": rejected,
            "auto_approval_rate": round((auto_approved / total_runs * 100.0) if total_runs else 0.0, 1),
            "total_dollar_volume": round(total_dollar_volume, 2),
            "approved_dollar_volume": round(approved_dollar_volume, 2),
            "duplicate_prevented_volume": round(duplicate_saved_volume, 2)
        },
        "runs": all_runs
    }

@app.get("/api/invoices/export/csv")
def export_runs_csv():
    """Export full run history as a downloadable CSV for audit purposes."""
    all_runs = db_manager.get_all_runs()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "Run ID", "Timestamp", "Vendor Name", "Invoice Number", "Invoice File",
        "Invoice Total (USD)", "PO Number", "Decision Status", "Decision Reason",
        "Confidence Score (%)", "Risk Score", "Is Manual Override", "Override Notes"
    ])

    for r in all_runs:
        writer.writerow([
            r.get("id", ""),
            r.get("timestamp", ""),
            r.get("vendor_name", ""),
            r.get("invoice_number", ""),
            r.get("invoice_filename", ""),
            r.get("invoice_total", 0.0),
            r.get("po_number", ""),
            r.get("decision_status", ""),
            r.get("decision_reason", ""),
            r.get("confidence_score", 0.0),
            "",  # risk_score not stored directly in runs table
            "Yes" if r.get("is_manual_override") else "No",
            r.get("override_notes", "")
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=zamp_ap_audit_trail.csv"}
    )

@app.get("/api/invoices/{run_id}")
def get_run_detail(run_id: str):
    all_runs = db_manager.get_all_runs()
    record = next((r for r in all_runs if r["id"] == run_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Run record not found")
    return record

@app.post("/api/invoices/{run_id}/review")
def review_override(run_id: str, body: ReviewActionRequest):
    updated = db_manager.update_run_review(run_id, body.action, body.notes, body.reviewer)
    if not updated:
        raise HTTPException(status_code=404, detail="Run record not found")
    return {"status": "success", "updated_record": updated}

# Serve frontend build if available
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.api_route("/", methods=["GET", "HEAD"])
    def serve_frontend_index():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/{full_path:path}")
    def serve_spa_fallback(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        target_file = os.path.join(frontend_dist, full_path)
        if os.path.exists(target_file) and os.path.isfile(target_file):
            return FileResponse(target_file)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
