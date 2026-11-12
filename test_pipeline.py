import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
from database import db_manager
from procurement_db import db

# Clean DB reset for reproducible test run
db_manager.reset()

from extractor import extractor
from matching_engine import matching_engine
from decision_engine import decision_engine
from llm_engine import llm_engine

samples = os.path.join(os.path.dirname(__file__), 'backend', 'sample_invoices')
results = []
print("=" * 80)
print("FULL PS-1 PIPELINE TEST — ALL 8 SCENARIOS")
print("=" * 80)

for f in sorted(os.listdir(samples)):
    if not f.endswith('.pdf'):
        continue
    pdf_path = os.path.join(samples, f)
    try:
        extracted = extractor.extract_from_pdf(pdf_path)
        extracted, _ = llm_engine.extract_with_llm(extracted.raw_text_snippet or '', extracted)
        vendor, vconf = db.find_vendor(extracted.vendor_name)
        po = db.get_po(extracted.po_reference)
        po_inferred_note = None
        if not po and extracted.vendor_name:
            po, po_inferred_note = db.find_po_fallback(extracted.vendor_name, extracted.total_amount)
        reconciliation = matching_engine.reconcile(extracted, po)
        policy_checks = matching_engine.evaluate_policies(extracted, vendor, po, reconciliation, db, po_inferred_note=po_inferred_note)
        decision = decision_engine.evaluate(extracted, vendor, po, reconciliation, policy_checks)
        
        status = decision.status.value
        amt = extracted.total_amount
        vname = extracted.vendor_name or 'N/A'
        invnum = extracted.invoice_number or 'N/A'
        ponum = po.po_number if po else (extracted.po_reference or 'None')
        failed_checks = [c for c in policy_checks if not c.passed]
        
        results.append((f, status, amt))
        print(f"\n[{status}] {f}")
        print(f"  Vendor   : {vname} (match conf: {vconf:.0%})")
        print(f"  Invoice# : {invnum}  |  Total: ${amt:,.2f}")
        print(f"  PO Ref   : {ponum}")
        print(f"  Checks   : {len(policy_checks)} total, {len(failed_checks)} flagged")
        if failed_checks:
            for c in failed_checks:
                print(f"    - [{c.severity}] {c.check_name}: {c.message[:80]}")
        print(f"  Decision : {decision.summary_reason[:100]}")
        
    except Exception as e:
        results.append((f, 'ERROR', 0))
        print(f"\n[ERROR] {f}: {e}")
        import traceback
        traceback.print_exc()

print()
print("=" * 80)
print("SUMMARY OF ALL 8 SCENARIOS")
print("=" * 80)
expected = {
    '1_Happy_Path': 'AUTO_APPROVED',
    '2_Edge_Case_Price_Breach': 'REVIEW_REQUIRED',
    '3_Edge_Case_Split_PO': 'AUTO_APPROVED',
    '4_Edge_Case_Duplicate': 'REJECTED',
    '5_Edge_Case_Unapproved': 'REJECTED',
    '6_Edge_Case_Minor_Variance': 'AUTO_APPROVED',
    '7_Edge_Case_Cross_Vendor_PO': 'REJECTED',
    '8_Edge_Case_Missing_Invoice_Number': 'REVIEW_REQUIRED',
}
all_passed = True
for fname, status, amt in results:
    exp = next((v for k, v in expected.items() if k in fname), 'UNKNOWN')
    icon = 'PASS' if status == exp else 'FAIL'
    if status != exp:
        all_passed = False
    print(f"  [{icon}] {fname[:55]}: {status} (expected: {exp}) | ${amt:,.2f}")

print()
print("OVERALL:", "ALL 8 SCENARIOS PASS!" if all_passed else "SOME FAILURES — CHECK ABOVE")

