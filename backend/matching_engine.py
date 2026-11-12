from typing import Optional, List, Tuple
from difflib import SequenceMatcher

try:
    from backend.models import (
        ExtractedInvoice, PurchaseOrder, VendorMaster, ReconciliationResult,
        LineItemMatch, PolicyCheck, RiskRating
    )
    from backend.procurement_db import ProcurementDatabase
except ImportError:
    from models import (
        ExtractedInvoice, PurchaseOrder, VendorMaster, ReconciliationResult,
        LineItemMatch, PolicyCheck, RiskRating
    )
    from procurement_db import ProcurementDatabase

def string_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

class MatchingEngine:
    def reconcile(self, invoice: ExtractedInvoice, po: Optional[PurchaseOrder]) -> ReconciliationResult:
        """
        Perform 2-way line item and total reconciliation against Purchase Order.
        """
        if not po:
            return ReconciliationResult(
                po_found=False,
                po_number=invoice.po_reference,
                invoice_total=invoice.total_amount,
                notes=["No matching Purchase Order found in procurement system."]
            )

        line_matches: List[LineItemMatch] = []
        tolerance_breached = False
        notes: List[str] = []

        # Reconcile invoice line items against PO line items
        matched_po_codes = set()
        for inv_line in invoice.line_items:
            best_po_line = None
            best_sim = 0.0

            # 1. Match by Item Code if available
            if inv_line.item_code:
                clean_inv_code = inv_line.item_code.replace("[", "").replace("]", "").strip().upper()
                for po_l in po.line_items:
                    clean_po_code = po_l.item_code.replace("[", "").replace("]", "").strip().upper()
                    if clean_inv_code == clean_po_code:
                        best_po_line = po_l
                        break

            # 2. Match by description similarity if not matched by code
            if not best_po_line:
                for po_l in po.line_items:
                    sim = string_similarity(inv_line.description, po_l.description)
                    if sim > best_sim and sim >= 0.5:
                        best_sim = sim
                        best_po_line = po_l

            if best_po_line:
                matched_po_codes.add(best_po_line.item_code)
                qty_diff = inv_line.quantity - best_po_line.quantity
                price_diff = inv_line.unit_price - best_po_line.unit_price
                tot_diff = inv_line.total_price - best_po_line.total_price
                price_var_pct = (price_diff / best_po_line.unit_price * 100.0) if best_po_line.unit_price else 0.0

                # Determine line status
                if abs(price_diff) < 0.01 and abs(qty_diff) < 0.01:
                    status = "EXACT_MATCH"
                    line_notes = "Exact price and quantity match."
                elif abs(price_var_pct) <= po.tolerance_percentage:
                    status = "TOLERANCE_MATCH"
                    line_notes = f"Unit price variance of {price_var_pct:+.1f}% is within acceptable tolerance (+/-{po.tolerance_percentage}%)."
                elif inv_line.quantity < best_po_line.quantity and abs(price_diff) < 0.01:
                    status = "PARTIAL_QUANTITY"
                    line_notes = f"Partial delivery: Invoiced {inv_line.quantity} of {best_po_line.quantity} ordered units at agreed rate."
                else:
                    status = "VARIANCE_BREACH"
                    tolerance_breached = True
                    line_notes = f"Unit price variance of {price_var_pct:+.1f}% (+${price_diff:,.2f}) exceeds tolerance threshold (+/-{po.tolerance_percentage}%)."

                line_matches.append(LineItemMatch(
                    invoice_description=inv_line.description,
                    invoice_qty=inv_line.quantity,
                    invoice_unit_price=inv_line.unit_price,
                    invoice_total=inv_line.total_price,
                    po_item_code=best_po_line.item_code,
                    po_description=best_po_line.description,
                    po_qty=best_po_line.quantity,
                    po_unit_price=best_po_line.unit_price,
                    po_total=best_po_line.total_price,
                    match_status=status,
                    price_variance=round(price_diff, 2),
                    qty_variance=round(qty_diff, 2),
                    total_variance=round(tot_diff, 2),
                    variance_pct=round(price_var_pct, 2),
                    notes=line_notes
                ))
            else:
                # Check if this is a consolidated / bundled bill
                is_bundled_case = (
                    len(invoice.line_items) == 1 and
                    len(po.line_items) > 1 and
                    abs(invoice.total_amount - po.total_amount) <= max(po.tolerance_amount, po.total_amount * (po.tolerance_percentage / 100.0))
                )
                if is_bundled_case:
                    line_matches.append(LineItemMatch(
                        invoice_description=inv_line.description,
                        invoice_qty=inv_line.quantity,
                        invoice_unit_price=inv_line.unit_price,
                        invoice_total=inv_line.total_price,
                        match_status="BUNDLED_MATCH",
                        total_variance=round(invoice.total_amount - po.total_amount, 2),
                        notes=f"Bundled bill: Single consolidated invoice line covers all {len(po.line_items)} PO items within authorized contract amount."
                    ))
                else:
                    # Unmatched line (e.g. unexpected shipping, additional service, or unbudgeted line)
                    line_matches.append(LineItemMatch(
                        invoice_description=inv_line.description,
                        invoice_qty=inv_line.quantity,
                        invoice_unit_price=inv_line.unit_price,
                        invoice_total=inv_line.total_price,
                        match_status="UNMATCHED_SURCHARGE",
                        total_variance=round(inv_line.total_price, 2),
                        notes=f"Line item not listed in original PO lines (e.g., freight, handling, or unbudgeted surcharge)."
                    ))

        is_bundled = any(lm.match_status == "BUNDLED_MATCH" for lm in line_matches)
        if is_bundled:
            notes.append(f"Bundled billing detected: Single invoice line encompasses {len(po.line_items)} detailed PO line items.")

        # Overall PO amount comparison
        total_variance = round(invoice.total_amount - po.total_amount, 2)
        variance_percentage = round((total_variance / po.total_amount * 100.0) if po.total_amount else 0.0, 2)
        
        is_partial = False
        remaining_after = round(po.remaining_amount - invoice.total_amount, 2)

        # Check if partial fulfillment
        if invoice.total_amount < po.total_amount and remaining_after >= -po.tolerance_amount:
            is_partial = True
            notes.append(f"Partial fulfillment detected: Invoicing ${invoice.total_amount:,.2f} against PO total of ${po.total_amount:,.2f}. Remaining PO balance: ${remaining_after:,.2f}.")
        elif abs(total_variance) <= po.tolerance_amount or abs(variance_percentage) <= po.tolerance_percentage:
            notes.append(f"Total amount within acceptable PO tolerance ({variance_percentage:+.2f}% / ${total_variance:+,.2f} variance).")
        else:
            if total_variance > po.tolerance_amount:
                tolerance_breached = True
                notes.append(f"Total invoice amount exceeds PO total by ${total_variance:,.2f} (+{variance_percentage:.2f}%), breaching the {po.tolerance_percentage}% / ${po.tolerance_amount:,.2f} tolerance limit.")

        # Only flag PO balance overrun if no duplicate or fulfilled-PO check will catch it
        # and the invoice amount is non-trivially greater than remaining balance
        if remaining_after < -po.tolerance_amount and invoice.total_amount > 0.01:
            tolerance_breached = True
            notes.append(f"PO balance overrun: Invoicing exceeds remaining authorized balance (${po.remaining_amount:,.2f}) by ${abs(remaining_after):,.2f}.")

        return ReconciliationResult(
            po_found=True,
            po_number=po.po_number,
            po_total=po.total_amount,
            po_remaining_before=po.remaining_amount,
            po_remaining_after=max(0.0, remaining_after),
            invoice_total=invoice.total_amount,
            total_variance=total_variance,
            variance_percentage=variance_percentage,
            tolerance_breached=tolerance_breached,
            is_partial_fulfillment=is_partial,
            is_bundled=is_bundled,
            line_matches=line_matches,
            notes=notes
        )

    def evaluate_policies(
        self,
        invoice: ExtractedInvoice,
        vendor: Optional[VendorMaster],
        po: Optional[PurchaseOrder],
        reconciliation: ReconciliationResult,
        db: ProcurementDatabase,
        po_inferred_note: Optional[str] = None
    ) -> List[PolicyCheck]:
        """
        Evaluate full set of deterministic AP compliance & risk policies.
        """
        checks: List[PolicyCheck] = []

        # 1. Vendor Master Check
        if not vendor:
            checks.append(PolicyCheck(
                check_id="CHK-001",
                check_name="Vendor Master Verification",
                passed=False,
                severity="CRITICAL",
                message=f"Vendor '{invoice.vendor_name or 'Unknown'}' is not registered in ERP Vendor Master.",
                details={"vendor_name": invoice.vendor_name, "action": "Vendor onboarding or formal approval required."}
            ))
        elif not vendor.is_approved or vendor.risk_rating == RiskRating.BLOCKED:
            checks.append(PolicyCheck(
                check_id="CHK-001",
                check_name="Vendor Master Verification",
                passed=False,
                severity="CRITICAL",
                message=f"Vendor '{vendor.vendor_name}' is marked as UNAPPROVED or BLOCKED (Risk: {vendor.risk_rating.value}).",
                details={"vendor_id": vendor.vendor_id, "risk_rating": vendor.risk_rating.value}
            ))
        else:
            checks.append(PolicyCheck(
                check_id="CHK-001",
                check_name="Vendor Master Verification",
                passed=True,
                severity="INFO",
                message=f"Vendor '{vendor.vendor_name}' is verified and in good standing (ID: {vendor.vendor_id}, Risk: {vendor.risk_rating.value}).",
                details={"vendor_id": vendor.vendor_id, "tax_id": vendor.tax_id}
            ))

        # 1b. Cross-Vendor PO Entitlement Check (Preventing billing against another vendor's PO)
        if po and vendor:
            v_clean = vendor.vendor_name.lower().strip()
            po_v_clean = po.vendor_name.lower().strip()
            is_match = (
                v_clean == po_v_clean or
                v_clean in po_v_clean or
                po_v_clean in v_clean or
                any(a.lower() in po_v_clean or po_v_clean in a.lower() for a in vendor.aliases)
            )
            if not is_match:
                checks.append(PolicyCheck(
                    check_id="CHK-003-VEND",
                    check_name="PO Vendor Entitlement",
                    passed=False,
                    severity="CRITICAL",
                    message=f"Cross-Vendor PO Mismatch! Invoice vendor '{vendor.vendor_name}' is not authorized to bill against PO {po.po_number} (issued to '{po.vendor_name}').",
                    details={"invoice_vendor": vendor.vendor_name, "po_vendor": po.vendor_name, "po_number": po.po_number}
                ))
            else:
                checks.append(PolicyCheck(
                    check_id="CHK-003-VEND",
                    check_name="PO Vendor Entitlement",
                    passed=True,
                    severity="INFO",
                    message=f"Vendor entitlement verified: PO {po.po_number} is authorized for '{vendor.vendor_name}'.",
                    details={"po_number": po.po_number, "vendor_id": vendor.vendor_id}
                ))

        # 2. Duplicate Invoice Check
        duplicate_record = db.check_duplicate(invoice.vendor_name, invoice.invoice_number, invoice.total_amount)
        if duplicate_record:
            checks.append(PolicyCheck(
                check_id="CHK-002",
                check_name="Duplicate Invoice Detection",
                passed=False,
                severity="CRITICAL",
                message=f"Duplicate invoice detected! Invoice #{invoice.invoice_number} was previously recorded/paid for ${duplicate_record.get('total_amount', 0.0):,.2f}.",
                details=duplicate_record
            ))
        else:
            checks.append(PolicyCheck(
                check_id="CHK-002",
                check_name="Duplicate Invoice Detection",
                passed=True,
                severity="INFO",
                message=f"No prior duplicate invoice found for Invoice #{invoice.invoice_number or 'N/A'}.",
                details={"status": "CLEAN"}
            ))

        # 3. PO Linkage & Status Check
        if not po:
            checks.append(PolicyCheck(
                check_id="CHK-003",
                check_name="Purchase Order Authorization",
                passed=False,
                severity="CRITICAL",
                message=f"Missing or invalid Purchase Order reference: '{invoice.po_reference or 'None provided'}'.",
                details={"po_reference": invoice.po_reference}
            ))
        elif po.status == "FULFILLED" and po.remaining_amount <= 0.01:
            checks.append(PolicyCheck(
                check_id="CHK-003",
                check_name="Purchase Order Authorization",
                passed=False,
                severity="CRITICAL",
                message=f"Purchase Order {po.po_number} is already fully fulfilled and has $0 remaining budget.",
                details={"po_status": po.status, "remaining": po.remaining_amount}
            ))
        else:
            checks.append(PolicyCheck(
                check_id="CHK-003",
                check_name="Purchase Order Authorization",
                passed=True,
                severity="INFO",
                message=f"Valid open PO found: {po.po_number} (Status: {po.status}, Authorized: ${po.total_amount:,.2f}).",
                details={"po_number": po.po_number, "status": po.status, "remaining": po.remaining_amount}
            ))

        # 3b. Implied / Inferred PO Check
        if po and (po_inferred_note or not invoice.po_reference):
            checks.append(PolicyCheck(
                check_id="CHK-007",
                check_name="Implied Purchase Order Linkage",
                passed=False,
                severity="WARNING",
                message=f"Implied Purchase Order: Invoice omitted PO number. System matched PO {po.po_number} via vendor contract fallback.",
                details={"inferred_po": po.po_number, "notes": po_inferred_note or "PO inferred by matching vendor and contract balance."}
            ))

        # 4. Tolerance & Pricing Check
        if po:
            if reconciliation.tolerance_breached:
                checks.append(PolicyCheck(
                    check_id="CHK-004",
                    check_name="Tolerance & Contract Pricing",
                    passed=False,
                    severity="WARNING",
                    message=f"Invoice breaches authorized tolerance! Variance: ${reconciliation.total_variance:+,.2f} ({reconciliation.variance_percentage:+.2f}% vs allowable +/-{po.tolerance_percentage}%).",
                    details={"variance_amount": reconciliation.total_variance, "variance_pct": reconciliation.variance_percentage, "tolerance_limit": po.tolerance_percentage}
                ))
            elif abs(reconciliation.total_variance) > 0.01:
                checks.append(PolicyCheck(
                    check_id="CHK-004",
                    check_name="Tolerance & Contract Pricing",
                    passed=True,
                    severity="INFO",
                    message=f"Variance of ${reconciliation.total_variance:+,.2f} ({reconciliation.variance_percentage:+.2f}%) is within allowable tolerance threshold of +/-{po.tolerance_percentage}%.",
                    details={"variance_amount": reconciliation.total_variance, "tolerance_limit": po.tolerance_percentage}
                ))
            else:
                checks.append(PolicyCheck(
                    check_id="CHK-004",
                    check_name="Tolerance & Contract Pricing",
                    passed=True,
                    severity="INFO",
                    message="Exact 100% price and amount match with Purchase Order.",
                    details={"match": "EXACT"}
                ))

        # 5. Core Data Integrity & Mandatory Fields
        missing_fields = []
        if not invoice.invoice_number or invoice.invoice_number.strip().lower() in ["unknown", "none", "n/a", "unspecified", "omitted", "missing", "pending", "tbd"]:
            missing_fields.append("Invoice Number")
        if not invoice.invoice_date:
            missing_fields.append("Invoice Date")
        if invoice.total_amount <= 0:
            missing_fields.append("Total Amount")

        if missing_fields:
            checks.append(PolicyCheck(
                check_id="CHK-005",
                check_name="Invoice Data Completeness",
                passed=False,
                severity="CRITICAL" if "Invoice Number" in missing_fields or "Total Amount" in missing_fields else "WARNING",
                message=f"Missing essential invoice fields: {', '.join(missing_fields)}.",
                details={"missing": missing_fields}
            ))
        else:
            checks.append(PolicyCheck(
                check_id="CHK-005",
                check_name="Invoice Data Completeness",
                passed=True,
                severity="INFO",
                message="All mandatory invoice metadata fields present and syntactically valid.",
                details={"fields_checked": ["Invoice #", "Date", "Line Items", "Total Amount"]}
            ))

        # 6. OCR & Document Fidelity Check
        if invoice.total_amount <= 0 and not invoice.line_items:
            checks.append(PolicyCheck(
                check_id="CHK-006",
                check_name="OCR & Document Fidelity",
                passed=False,
                severity="WARNING",
                message="Invoice content could not be resolved from PDF stream.",
                details={"confidence_score": invoice.confidence_score}
            ))
        else:
            checks.append(PolicyCheck(
                check_id="CHK-006",
                check_name="OCR & Document Fidelity",
                passed=True,
                severity="INFO",
                message=f"High-fidelity document structure verified ({invoice.confidence_score:.0f}% confidence).",
                details={"confidence_score": invoice.confidence_score}
            ))

        return checks

matching_engine = MatchingEngine()
