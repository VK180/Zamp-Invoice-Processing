from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from backend.models import (
        ExtractedInvoice, PurchaseOrder, VendorMaster, ReconciliationResult,
        PolicyCheck, DecisionOutput, DecisionStatus
    )
except ImportError:
    from models import (
        ExtractedInvoice, PurchaseOrder, VendorMaster, ReconciliationResult,
        PolicyCheck, DecisionOutput, DecisionStatus
    )

class DecisionEngine:
    def evaluate(
        self,
        invoice: ExtractedInvoice,
        vendor: Optional[VendorMaster],
        po: Optional[PurchaseOrder],
        reconciliation: ReconciliationResult,
        policy_checks: List[PolicyCheck]
    ) -> DecisionOutput:
        critical_failures = [c for c in policy_checks if not c.passed and c.severity == "CRITICAL"]
        warnings = [c for c in policy_checks if not c.passed and c.severity == "WARNING"]

        rationale: List[str] = []
        vendor_email_draft = None
        erp_payload: Dict[str, Any] = {}

        # -------------------------------------------------------------
        # 1. EVALUATE REJECTION (Hard stop / fraud / invalid duplicate)
        # -------------------------------------------------------------
        duplicate_check = next((c for c in policy_checks if c.check_id == "CHK-002" and not c.passed), None)
        unapproved_vendor = next((c for c in policy_checks if c.check_id == "CHK-001" and not c.passed), None)
        po_vendor_mismatch = next((c for c in policy_checks if c.check_id == "CHK-003-VEND" and not c.passed), None)

        if duplicate_check:
            status = DecisionStatus.REJECTED
            risk_score = 95
            confidence = 99.0
            summary = f"REJECTED: Duplicate invoice submission. Invoice #{invoice.invoice_number} matches a previously processed invoice."
            rationale.append(f"Duplicate Detection: {duplicate_check.message}")
            if po:
                rationale.append(f"Associated PO {po.po_number} is already fulfilled (${po.billed_amount:,.2f} billed out of ${po.total_amount:,.2f}).")
            action = "Block payment, flag as duplicate in ERP, and notify vendor of previous settlement."
            
            vendor_email_draft = (
                f"Subject: Duplicate Invoice Notice - Invoice #{invoice.invoice_number}\n\n"
                f"Dear {vendor.vendor_name if vendor else 'Vendor'},\n\n"
                f"We received your invoice #{invoice.invoice_number} dated {invoice.invoice_date} for ${invoice.total_amount:,.2f}.\n"
                f"Our automated accounting system detected that this invoice has already been recorded and processed under PO {invoice.po_reference or 'reference'}.\n"
                f"No duplicate disbursement will be made. If you believe this is in error, please reply with remittance details.\n\n"
                f"Accounts Payable Operations Team"
            )

        elif po_vendor_mismatch:
            status = DecisionStatus.REJECTED
            risk_score = 99
            confidence = 99.0
            summary = (
                f"REJECTED: Purchase Order misappropriation. Vendor '{invoice.vendor_name}' "
                f"attempted to bill against PO {po.po_number} issued exclusively to '{po.vendor_name}'."
            )
            rationale.append(f"Cross-Vendor PO Security: {po_vendor_mismatch.message}")
            rationale.append(f"ERP Record: PO {po.po_number} belongs to '{po.vendor_name}', not '{invoice.vendor_name}'.")
            action = "Block payment immediately and alert Procurement Security of potential fraudulent PO usage."

            vendor_email_draft = (
                f"Subject: Unauthorized PO Reference Notice - Invoice #{invoice.invoice_number}\n\n"
                f"Dear Accounts Department,\n\n"
                f"We received invoice #{invoice.invoice_number} for ${invoice.total_amount:,.2f} citing Purchase Order {po.po_number}.\n"
                f"Our procurement records show that PO {po.po_number} was authorized exclusively for another supplier ('{po.vendor_name}').\n"
                f"Your company is not authorized to draw down funds from this Purchase Order.\n"
                f"Please verify your internal order records or contact your procurement buyer.\n\n"
                f"Accounts Payable Operations Team"
            )

        elif unapproved_vendor:
            status = DecisionStatus.REJECTED
            risk_score = 85
            confidence = 92.0
            summary = f"REJECTED: Unapproved vendor. '{invoice.vendor_name or 'Unknown'}' is not registered in ERP Vendor Master."
            rationale.append(f"Vendor Compliance: {unapproved_vendor.message}")
            if not invoice.po_reference:
                rationale.append("Procurement Linkage: No Purchase Order was referenced on this invoice.")
            action = "Reject invoice and route vendor through formal Procurement Onboarding & W-9 verification."

            vendor_email_draft = (
                f"Subject: Invoice Rejected - Vendor Not Registered ({invoice.vendor_name or 'Unregistered Vendor'})\n\n"
                f"Dear Accounts Department,\n\n"
                f"We received an invoice #{invoice.invoice_number or 'unspecified'} for ${invoice.total_amount:,.2f}. "
                f"However, your company '{invoice.vendor_name}' is not currently an approved vendor in our procurement directory, "
                f"and no authorized Purchase Order was found.\n\n"
                f"Please contact your business sponsor to complete the vendor registration process before re-submitting.\n\n"
                f"Accounts Payable Operations Team"
            )

        elif not po:
            status = DecisionStatus.REVIEW_REQUIRED
            risk_score = 70
            confidence = 88.0
            summary = f"MANUAL REVIEW REQUIRED: No matching Purchase Order found for Invoice #{invoice.invoice_number}."
            rationale.append(f"Procurement Linkage: Invoice references PO '{invoice.po_reference or 'None'}', which does not exist in ERP.")
            action = "Assign to AP Specialist to locate missing PO or obtain non-PO spend authorization."

            vendor_email_draft = (
                f"Subject: Missing PO Reference - Invoice #{invoice.invoice_number}\n\n"
                f"Dear {vendor.vendor_name if vendor else 'Vendor'},\n\n"
                f"We received invoice #{invoice.invoice_number} for ${invoice.total_amount:,.2f}. "
                f"However, we could not locate an approved Purchase Order ({invoice.po_reference or 'missing'}).\n"
                f"Please reply with your internal purchase contact or valid PO number.\n\n"
                f"Accounts Payable Operations Team"
            )

        # -------------------------------------------------------------
        # 1b. EVALUATE MANDATORY METADATA OMISSIONS (Missing invoice #)
        # -------------------------------------------------------------
        elif not invoice.invoice_number or invoice.invoice_number.strip().lower() in ["unknown", "none", "n/a", "unspecified", "omitted", "missing", "pending", "tbd"]:
            status = DecisionStatus.REVIEW_REQUIRED
            risk_score = 75
            confidence = 85.0
            summary = "MANUAL REVIEW REQUIRED: Missing mandatory Invoice Number. Invoices cannot be posted to ERP without a unique vendor invoice number."
            rationale.append("Metadata Compliance: Invoice document does not contain an invoice number or identifier.")
            if po:
                rationale.append(f"PO {po.po_number} is open, but payment remittance cannot be scheduled without invoice reference.")
            action = "Place on hold and request vendor re-issue invoice with valid invoice number."

            vendor_email_draft = (
                f"Subject: Missing Invoice Number Notice - Action Required\n\n"
                f"Dear {vendor.vendor_name if vendor else 'Vendor'},\n\n"
                f"We received an invoice dated {invoice.invoice_date or 'recent'} for ${invoice.total_amount:,.2f} under PO {po.po_number if po else 'contract'}.\n"
                f"However, the document does not display a valid Invoice Number. Our accounting system cannot register or remit payment without an official invoice number.\n"
                f"Please re-issue the invoice with a unique invoice number to avoid payment delay.\n\n"
                f"Accounts Payable Operations Team"
            )

        elif invoice.total_amount <= 0:
            status = DecisionStatus.REVIEW_REQUIRED
            risk_score = 65
            confidence = 80.0
            summary = "MANUAL REVIEW REQUIRED: Invoice total amount could not be determined ($0.00)."
            rationale.append("Validation Gate: Missing or invalid financial total on document.")
            action = "Route to AP Specialist for manual invoice valuation."

        # -------------------------------------------------------------
        # 2. EVALUATE VARIANCE / TOLERANCE BREACH
        # -------------------------------------------------------------
        elif reconciliation.tolerance_breached:
            status = DecisionStatus.REVIEW_REQUIRED
            risk_score = 60
            confidence = 94.0
            summary = (
                f"MANUAL REVIEW REQUIRED: Price variance exceeds tolerance limit. "
                f"Invoice total of ${invoice.total_amount:,.2f} is ${reconciliation.total_variance:+,.2f} "
                f"({reconciliation.variance_percentage:+.2f}%) over authorized PO {po.po_number} (limit: +/-{po.tolerance_percentage}%)."
            )
            rationale.append(f"PO Total: ${po.total_amount:,.2f} | Invoice Total: ${invoice.total_amount:,.2f} | Variance: ${reconciliation.total_variance:+,.2f}")
            for lm in reconciliation.line_matches:
                if lm.match_status == "VARIANCE_BREACH":
                    rationale.append(f"Line Item '{lm.invoice_description}': Invoiced at ${lm.invoice_unit_price:,.2f}/unit vs agreed contract rate of ${lm.po_unit_price:,.2f}/unit ({lm.variance_pct:+.1f}% variance).")
                elif lm.match_status == "UNMATCHED_SURCHARGE":
                    rationale.append(f"Unbudgeted line item: '{lm.invoice_description}' for ${lm.invoice_total:,.2f} was not on authorized PO.")

            action = f"Hold payment and request Buyer approval for the ${reconciliation.total_variance:,.2f} price discrepancy."

            vendor_email_draft = (
                f"Subject: Price Discrepancy on Invoice #{invoice.invoice_number} (PO {po.po_number})\n\n"
                f"Dear {vendor.vendor_name},\n\n"
                f"During automated 2-way matching for invoice #{invoice.invoice_number}, a price variance was flagged.\n"
                f"The invoice total of ${invoice.total_amount:,.2f} exceeds our authorized PO {po.po_number} by ${reconciliation.total_variance:,.2f}.\n"
                f"Specifically, the unit rate for line item(s) differed from our contractual agreement.\n"
                f"Please provide an updated invoice reflecting the agreed rates or contact your procurement buyer.\n\n"
                f"Accounts Payable Operations Team"
            )

        # -------------------------------------------------------------
        # 3. EVALUATE PARTIAL FULFILLMENT / SPLIT PO (AUTO-APPROVED)
        # -------------------------------------------------------------
        elif reconciliation.is_partial_fulfillment:
            status = DecisionStatus.AUTO_APPROVED
            risk_score = 10
            confidence = 98.0
            summary = (
                f"AUTO-APPROVED: Valid partial fulfillment against PO {po.po_number}. "
                f"Billed ${invoice.total_amount:,.2f} against PO total ${po.total_amount:,.2f}. "
                f"Remaining PO balance updated to ${reconciliation.po_remaining_after:,.2f}."
            )
            rationale.append(f"Split PO: Invoiced amount (${invoice.total_amount:,.2f}) is within authorized PO balance (${reconciliation.po_remaining_before:,.2f}).")
            rationale.append(f"Unit pricing for fulfilled lines matches agreed purchase order rates exactly.")
            rationale.append(f"ERP Status: PO {po.po_number} transitioned to PARTIALLY_BILLED with ${reconciliation.po_remaining_after:,.2f} remaining.")
            action = f"Queue automated disbursement of ${invoice.total_amount:,.2f} for upcoming batch run. Update PO remaining balance."

            erp_payload = {
                "transaction_type": "VENDOR_BILL",
                "vendor_id": vendor.vendor_id if vendor else "UNKNOWN",
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date,
                "due_date": invoice.due_date,
                "amount": invoice.total_amount,
                "currency": invoice.currency,
                "po_number": po.po_number,
                "po_balance_after": reconciliation.po_remaining_after,
                "gl_status": "POSTED_PENDING_PAYMENT",
                "payment_terms": vendor.payment_terms if vendor else invoice.payment_terms or "Net 30",
                "auto_disbursement_eligible": True
            }

        # -------------------------------------------------------------
        # 3b. EVALUATE BUNDLED BILLING (Single line covering multi-line PO)
        # -------------------------------------------------------------
        elif reconciliation.is_bundled:
            status = DecisionStatus.REVIEW_REQUIRED
            risk_score = 45
            confidence = 92.0
            summary = (
                f"MANUAL REVIEW REQUIRED: Bundled billing detected. "
                f"Vendor billed a single consolidated line item for ${invoice.total_amount:,.2f} "
                f"covering {len(po.line_items)} PO line items. AP line-item allocation sign-off required."
            )
            rationale.append(f"Bundled Bill: Single invoice line encompasses {len(po.line_items)} detailed PO lines.")
            rationale.append(f"Total Amount Alignment: Total of ${invoice.total_amount:,.2f} matches authorized PO total of ${po.total_amount:,.2f}.")
            rationale.append("Audit Requirement: Accounting policy mandates manual GL line-item allocation for bundled invoices.")
            action = "Assign to AP Specialist to allocate individual PO line-item amounts in ERP before approval."

        # -------------------------------------------------------------
        # 3c. EVALUATE IMPLIED / INFERRED PO (PO not on invoice)
        # -------------------------------------------------------------
        elif po and (not invoice.po_reference or invoice.po_reference.strip().upper() in ["NONE", "MISSING", "N/A"]):
            status = DecisionStatus.REVIEW_REQUIRED
            risk_score = 40
            confidence = 90.0
            summary = (
                f"MANUAL REVIEW REQUIRED: Implied Purchase Order linkage. "
                f"Invoice omitted PO number; system matched open PO {po.po_number} (${po.total_amount:,.2f}) "
                f"by vendor contract match. AP Specialist confirmation required."
            )
            rationale.append("PO Reference Omission: Invoice document does not contain an explicit PO number.")
            rationale.append(f"Contract Fallback: Successfully matched open PO {po.po_number} based on vendor '{vendor.vendor_name if vendor else 'Unknown'}' and contract amount.")
            rationale.append("Audit Requirement: Require human confirmation to prevent misallocating spend against open PO balances.")
            action = f"Confirm linkage to PO {po.po_number} with internal buyer and proceed with disbursement."

        # -------------------------------------------------------------
        # 4. EVALUATE EXACT OR WITHIN-TOLERANCE MATCH (AUTO-APPROVED)
        # -------------------------------------------------------------
        else:
            status = DecisionStatus.AUTO_APPROVED
            risk_score = 5
            confidence = 99.0
            if abs(reconciliation.total_variance) < 0.01:
                summary = f"AUTO-APPROVED: 100% exact 2-way match against PO {po.po_number}. All line items and prices match authorized contract."
                rationale.append("Line Items: Exact match on quantity and unit prices.")
                rationale.append("Vendor & Bank: Verified approved vendor with valid tax credentials.")
                rationale.append("Duplicate & Fraud: Zero duplicate matches found across historical ledger.")
            else:
                summary = (
                    f"AUTO-APPROVED (Within Tolerance): Total variance of ${reconciliation.total_variance:+,.2f} "
                    f"({reconciliation.variance_percentage:+.2f}%) is within permitted PO tolerance (+/-{po.tolerance_percentage}% / ${po.tolerance_amount:,.2f})."
                )
                rationale.append(f"Allowable tolerance threshold (+/-{po.tolerance_percentage}%) safely absorbed the ${reconciliation.total_variance:,.2f} minor variance.")
                rationale.append("Vendor in good standing. No duplicate records.")

            action = f"Queue automated disbursement of ${invoice.total_amount:,.2f} for upcoming payment batch."

            erp_payload = {
                "transaction_type": "VENDOR_BILL",
                "vendor_id": vendor.vendor_id if vendor else "UNKNOWN",
                "invoice_number": invoice.invoice_number,
                "invoice_date": invoice.invoice_date,
                "due_date": invoice.due_date,
                "amount": invoice.total_amount,
                "currency": invoice.currency,
                "po_number": po.po_number,
                "po_balance_after": reconciliation.po_remaining_after,
                "gl_status": "POSTED_PENDING_PAYMENT",
                "payment_terms": vendor.payment_terms if vendor else invoice.payment_terms or "Net 30",
                "auto_disbursement_eligible": True
            }

        return DecisionOutput(
            status=status,
            confidence_score=confidence,
            summary_reason=summary,
            detailed_rationale=rationale,
            reconciliation=reconciliation,
            policy_checks=policy_checks,
            risk_score=risk_score,
            recommended_action=action,
            vendor_notification_draft=vendor_email_draft,
            erp_payload=erp_payload
        )

decision_engine = DecisionEngine()
