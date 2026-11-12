import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from typing import Optional, List, Dict, Tuple
from models import PurchaseOrder, POLineItem, VendorMaster, RiskRating
from database import db_manager

class ProcurementDatabase:
    """
    Production-grade SQLite-backed ERP procurement database interface.
    Persists vendors, purchase orders, line items, historical ledgers, and run audits.
    """
    def reset(self):
        db_manager.reset()

    def get_all_pos(self) -> List[PurchaseOrder]:
        raw_pos = db_manager.get_all_pos()
        pos = []
        for r in raw_pos:
            lines = [POLineItem(**li) for li in r["line_items"]]
            pos.append(PurchaseOrder(
                po_number=r["po_number"],
                vendor_name=r["vendor_name"],
                po_date=r["po_date"],
                total_amount=r["total_amount"],
                billed_amount=r["billed_amount"],
                remaining_amount=r["remaining_amount"],
                currency=r["currency"],
                status=r["status"],
                tolerance_percentage=r["tolerance_percentage"],
                tolerance_amount=r["tolerance_amount"],
                line_items=lines
            ))
        return pos

    def get_all_vendors(self) -> List[VendorMaster]:
        raw_v = db_manager.get_all_vendors()
        return [VendorMaster(
            vendor_id=v["vendor_id"],
            vendor_name=v["vendor_name"],
            aliases=v["aliases"],
            tax_id=v["tax_id"],
            payment_terms=v["payment_terms"],
            bank_account=v["bank_account"],
            is_approved=v["is_approved"],
            risk_rating=RiskRating(v["risk_rating"])
        ) for v in raw_v]

    def get_historical_invoices(self) -> List[Dict]:
        return db_manager.get_historical_invoices()

    def get_po(self, po_number: Optional[str]) -> Optional[PurchaseOrder]:
        raw = db_manager.get_po(po_number)
        if not raw:
            return None
        lines = [POLineItem(**li) for li in raw["line_items"]]
        return PurchaseOrder(
            po_number=raw["po_number"],
            vendor_name=raw["vendor_name"],
            po_date=raw["po_date"],
            total_amount=raw["total_amount"],
            billed_amount=raw["billed_amount"],
            remaining_amount=raw["remaining_amount"],
            currency=raw["currency"],
            status=raw["status"],
            tolerance_percentage=raw["tolerance_percentage"],
            tolerance_amount=raw["tolerance_amount"],
            line_items=lines
        )

    def find_vendor(self, vendor_name: Optional[str]) -> Tuple[Optional[VendorMaster], float]:
        raw_v, conf = db_manager.find_vendor(vendor_name)
        if not raw_v:
            return None, conf
        return VendorMaster(
            vendor_id=raw_v["vendor_id"],
            vendor_name=raw_v["vendor_name"],
            aliases=raw_v["aliases"],
            tax_id=raw_v["tax_id"],
            payment_terms=raw_v["payment_terms"],
            bank_account=raw_v["bank_account"],
            is_approved=raw_v["is_approved"],
            risk_rating=RiskRating(raw_v["risk_rating"])
        ), conf

    def find_po_fallback(self, vendor_name: Optional[str], total_amount: float) -> Tuple[Optional[PurchaseOrder], str]:
        raw_po, note = db_manager.find_po_fallback(vendor_name, total_amount)
        if not raw_po:
            return None, note
        lines = [POLineItem(**li) for li in raw_po["line_items"]]
        po = PurchaseOrder(
            po_number=raw_po["po_number"],
            vendor_name=raw_po["vendor_name"],
            po_date=raw_po["po_date"],
            total_amount=raw_po["total_amount"],
            billed_amount=raw_po["billed_amount"],
            remaining_amount=raw_po["remaining_amount"],
            currency=raw_po["currency"],
            status=raw_po["status"],
            tolerance_percentage=raw_po["tolerance_percentage"],
            tolerance_amount=raw_po["tolerance_amount"],
            line_items=lines
        )
        return po, note

    def check_duplicate(self, vendor_name: Optional[str], invoice_number: Optional[str], total_amount: float) -> Optional[Dict]:
        return db_manager.check_duplicate(vendor_name, invoice_number, total_amount)

    def record_approved_invoice(self, invoice_number: str, po_number: Optional[str], vendor_name: str, amount: float):
        db_manager.record_approved_invoice(invoice_number, po_number, vendor_name, amount)

db = ProcurementDatabase()
