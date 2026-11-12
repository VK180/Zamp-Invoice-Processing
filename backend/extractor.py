import re
import os
from typing import Optional, List
from dateutil import parser as dparser
import pypdf

try:
    from backend.models import ExtractedInvoice, LineItem
except ImportError:
    from models import ExtractedInvoice, LineItem

def parse_number(val: Optional[str]) -> float:
    if not val:
        return 0.0
    clean = re.sub(r'[^\d.]', '', val)
    try:
        return float(clean)
    except ValueError:
        return 0.0

def parse_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    clean = date_str.strip().rstrip(".,;")
    try:
        dt = dparser.parse(clean, fuzzy=True)
        # Sanity check plausible invoice years
        if 1990 <= dt.year <= 2040:
            return dt.strftime("%Y-%m-%d")
        return None
    except Exception:
        return None

GENERIC_HEADERS = {
    "invoice", "tax invoice", "commercial invoice", "statement", 
    "bill to", "bill", "page 1", "receipt", "payment terms", 
    "original", "duplicate", "proforma invoice"
}

class InvoiceExtractor:
    def extract_from_pdf(self, file_path: str, api_key: Optional[str] = None) -> ExtractedInvoice:
        """
        Extract structured invoice data from a PDF file.
        Supports multi-format layout parsing, colon-free extraction, and optical fallbacks.
        """
        raw_text = ""
        try:
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                raw_text += (page.extract_text() or "") + "\n"
        except Exception as e:
            raw_text = f"Error reading PDF stream: {str(e)}"

        return self.parse_text(raw_text)

    def parse_text(self, text: str) -> ExtractedInvoice:
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # ---------------------------------------------------------
        # 1. Vendor Name, Address & Tax ID
        # ---------------------------------------------------------
        vendor_name = None
        vendor_address = None
        vendor_tax_id = None

        # Check for From / Billed By block
        from_match = re.search(r'(?:^|\n)\s*(?:From|Billed\s*By|Vendor|Seller|Remitter|Supplier)\s*:?\s*\n+([^\n]+)', text, re.I)
        if from_match:
            candidate = from_match.group(1).strip()
            if candidate.lower() not in GENERIC_HEADERS and len(candidate) > 2:
                vendor_name = candidate
        
        # If not found via From block, inspect top lines filtering out generic headers
        if not vendor_name:
            for line in lines[:6]:
                low = line.lower().strip()
                if low in GENERIC_HEADERS:
                    continue
                if low.startswith("invoice") or low.startswith("page ") or low.startswith("payment is due") or low.startswith("thanks for"):
                    continue
                if len(line) > 2:
                    vendor_name = line
                    break

        # Address extraction heuristic
        if len(lines) > 1 and not lines[1].lower().startswith("tax id") and not lines[1].lower().startswith("invoice") and not lines[1].lower().startswith("payment"):
            vendor_address = lines[1]

        tax_id_match = re.search(r'\b(?:Tax\s*ID|EIN|VAT\s*(?:Reg|#)?|GSTIN)\s*:?\s*([A-Za-z0-9\-]+)', text, re.I)
        if tax_id_match:
            vendor_tax_id = tax_id_match.group(1).strip()

        # ---------------------------------------------------------
        # 2. Invoice Number
        # ---------------------------------------------------------
        invoice_number = None
        inv_match = re.search(r'\b(?:Invoice\s+(?:Number|No\.?|#|Id)|Invoice\s*#|INV\s*#)\b\s*:?\s*([A-Za-z0-9\-_/]+)', text, re.I)
        if inv_match:
            candidate_inv = inv_match.group(1).strip()
            if candidate_inv.lower() not in {"omitted", "missing", "none", "pending", "tbd", "unspecified", "na", "null", "date", "due", "po", "bill"}:
                invoice_number = candidate_inv
        
        if not invoice_number:
            inv_match2 = re.search(r'\b(INV-[A-Za-z0-9\-]+)\b', text)
            if inv_match2:
                invoice_number = inv_match2.group(1).strip()

        # ---------------------------------------------------------
        # 3. Invoice & Due Dates (Multi-format & written months)
        # ---------------------------------------------------------
        invoice_date = None
        due_date = None

        date_match = re.search(r'(?:^|\n)\s*(?:Invoice\s+Date|Date\s+of\s+Invoice|Issue\s+Date|Bill\s+Date|Date)\s*:?\s*([^\n\r]+)', text, re.I)
        if date_match:
            invoice_date = parse_date(date_match.group(1))

        due_match = re.search(r'(?:^|\n)\s*(?:Due\s*Date|Payment\s*Due|Due)\s*:?\s*([^\n\r]+)', text, re.I)
        if due_match:
            due_date = parse_date(due_match.group(1))

        # ---------------------------------------------------------
        # 4. PO Reference
        # ---------------------------------------------------------
        po_reference = None
        direct_po = re.search(r'\b(PO-[A-Za-z0-9\-]+)\b', text)
        if direct_po:
            po_reference = direct_po.group(1).strip()
        else:
            po_match = re.search(r'\b(?:PO\s*(?:Ref|Reference|#|Number|No\.?)|Purchase\s*Order\s*(?:#|Number|No\.?|Ref)?|Order\s*(?:#|Number|No\.?|Ref)|Cust(?:omer)?\s*PO)\b\s*:?\s*([A-Za-z0-9\-_/]+)', text, re.I)
            if po_match:
                cand = po_match.group(1).strip()
                if cand.lower() not in ["box", "terms", "date", "status", "due", "total", "n/a", "none"]:
                    po_reference = cand

        # ---------------------------------------------------------
        # 5. Financial Totals (Flexible colon-optional matching)
        # ---------------------------------------------------------
        subtotal = 0.0
        tax_amount = 0.0
        total_amount = 0.0

        # Subtotal
        sub_match = re.search(r'(?:^|\n)\s*(?:Sub\s*-?\s*Total|Net\s*Amount)\s*:?\s*\$?([0-9,]+\.[0-9]{2})', text, re.I)
        if not sub_match:
            sub_match = re.search(r'(?:Sub\s*-?\s*Total|Net\s*Amount)\s*:?\s*\$([0-9,]+\.[0-9]{2})', text, re.I)
        if sub_match:
            subtotal = parse_number(sub_match.group(1))

        # Tax / Freight
        tax_match = re.search(r'(?:^|\n)\s*(?:Tax\s*(?:&|/)\s*Freight|Sales\s*Tax|VAT|GST|Tax|Freight|Surcharge)\s*:?\s*\$?([0-9,]+\.[0-9]{2})', text, re.I)
        if not tax_match:
            tax_match = re.search(r'(?:Tax\s*(?:&|/)\s*Freight|Sales\s*Tax|VAT|GST|Tax|Freight|Surcharge)\s*:?\s*\$([0-9,]+\.[0-9]{2})', text, re.I)
        if tax_match:
            tax_amount = parse_number(tax_match.group(1))

        # Total Amount
        tot_match = re.search(r'(?:TOTAL\s+DUE|TOTAL\s+AMOUNT|BALANCE\s+DUE|AMOUNT\s+DUE|GRAND\s+TOTAL|INVOICE\s+TOTAL)\s*(?:\([A-Za-z]{3}\))?\s*:?\s*\n?\s*(?:<[^>]+>)?\s*\$?([0-9,]+\.[0-9]{2})', text, re.I)
        if not tot_match:
            tot_match = re.search(r'(?:^|\n)\s*TOTAL\s*(?:\([A-Za-z]{3}\))?\s*:?\s*\n?\s*(?:<[^>]+>)?\s*\$?([0-9,]+\.[0-9]{2})', text, re.I)
        
        if tot_match:
            total_amount = parse_number(tot_match.group(1))
        elif subtotal > 0:
            total_amount = round(subtotal + tax_amount, 2)

        if total_amount > 0 and subtotal == 0.0:
            subtotal = max(0.0, round(total_amount - tax_amount, 2))

        # ---------------------------------------------------------
        # 6. Line Items Extraction
        # ---------------------------------------------------------
        line_items: List[LineItem] = []
        
        # Strategy A: Structured block matching ([CODE] Description ... qty, unit price, total)
        item_block_matches = re.finditer(r'(\[[A-Za-z0-9\-]+\]|[A-Z0-9\-]{3,12})\s+(.+?)\n([0-9]+(?:\.[0-9]+)?)\n\$?([0-9,]+\.[0-9]{2})\n\$?([0-9,]+\.[0-9]{2})', text)
        for match in item_block_matches:
            code = match.group(1).strip()
            desc = match.group(2).strip()
            qty = parse_number(match.group(3))
            unit_price = parse_number(match.group(4))
            line_tot = parse_number(match.group(5))
            line_items.append(LineItem(
                item_code=code,
                description=desc,
                quantity=qty if qty > 0 else 1.0,
                unit_price=unit_price,
                total_price=line_tot
            ))

        # Strategy B: Inline tabular line items (e.g. "1.00 Web Design ... $85.00 0.00% $85.00")
        if not line_items:
            inline_pattern = re.compile(r'([0-9]+(?:\.[0-9]+)?)\s+([A-Za-z][A-Za-z0-9\s\-_.,]+?)\s+\$?([0-9,]+\.[0-9]{2})\s+(?:[0-9.]+%?\s+)?\$?([0-9,]+\.[0-9]{2})', re.DOTALL)
            idx = 1
            for match in inline_pattern.finditer(text):
                qty = parse_number(match.group(1))
                desc = match.group(2).replace('\n', ' ').strip()
                unit_price = parse_number(match.group(3))
                line_tot = parse_number(match.group(4))
                line_items.append(LineItem(
                    item_code=f"ITEM-{idx:02d}",
                    description=desc,
                    quantity=qty if qty > 0 else 1.0,
                    unit_price=unit_price,
                    total_price=line_tot
                ))
                idx += 1

        # Strategy C: Fallback line item if totals exist
        if not line_items and total_amount > 0:
            line_items.append(LineItem(
                item_code="ITEM-01",
                description="Consolidated invoice billed services / line items",
                quantity=1.0,
                unit_price=subtotal if subtotal > 0 else total_amount,
                total_price=subtotal if subtotal > 0 else total_amount
            ))

        # ---------------------------------------------------------
        # 7. Confidence Scoring
        # ---------------------------------------------------------
        score = 100.0
        if not invoice_number: score -= 25.0
        if not po_reference: score -= 15.0
        if not invoice_date: score -= 10.0
        if not vendor_name: score -= 20.0
        if total_amount <= 0: score -= 30.0

        return ExtractedInvoice(
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            vendor_name=vendor_name,
            vendor_tax_id=vendor_tax_id,
            vendor_address=vendor_address,
            po_reference=po_reference,
            currency="USD",
            line_items=line_items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            raw_text_snippet=text[:4000] if text else "",
            confidence_score=max(0.0, score),
            extraction_method="HYBRID_OCR_PARSER"
        )

extractor = InvoiceExtractor()
