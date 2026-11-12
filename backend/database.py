import sqlite3
import os
import json
from typing import Optional, List, Dict, Tuple, Any
from copy import deepcopy

DB_FILE = os.path.join(os.path.dirname(__file__), "ap_procurement.db")

class DatabaseManager:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self, force_reset: bool = False):
        conn = self.get_connection()
        cur = conn.cursor()

        if force_reset:
            cur.execute("DROP TABLE IF EXISTS po_line_items")
            cur.execute("DROP TABLE IF EXISTS purchase_orders")
            cur.execute("DROP TABLE IF EXISTS vendors")
            cur.execute("DROP TABLE IF EXISTS historical_invoices")
            cur.execute("DROP TABLE IF EXISTS runs")

        # 1. Vendors Master Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vendors (
                vendor_id TEXT PRIMARY KEY,
                vendor_name TEXT NOT NULL,
                aliases TEXT NOT NULL, -- JSON list
                tax_id TEXT,
                payment_terms TEXT DEFAULT 'Net 30',
                bank_account TEXT,
                is_approved INTEGER DEFAULT 1,
                risk_rating TEXT DEFAULT 'LOW'
            )
        """)

        # 2. Purchase Orders Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                po_number TEXT PRIMARY KEY,
                vendor_name TEXT NOT NULL,
                po_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                billed_amount REAL DEFAULT 0.0,
                remaining_amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                status TEXT DEFAULT 'OPEN',
                tolerance_percentage REAL DEFAULT 2.0,
                tolerance_amount REAL DEFAULT 25.0
            )
        """)

        # 3. PO Line Items Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS po_line_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT NOT NULL,
                item_code TEXT NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY (po_number) REFERENCES purchase_orders (po_number)
            )
        """)

        # 4. Historical Paid Invoices Ledger (Prior Accounting Periods)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS historical_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT NOT NULL,
                vendor_name TEXT NOT NULL,
                invoice_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                po_number TEXT,
                status TEXT DEFAULT 'PAID',
                paid_at TEXT,
                check_or_transfer_ref TEXT
            )
        """)

        # 5. Processed Runs Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                invoice_filename TEXT NOT NULL,
                pdf_url TEXT,
                vendor_name TEXT NOT NULL,
                invoice_number TEXT NOT NULL,
                invoice_total REAL NOT NULL,
                po_number TEXT,
                decision_status TEXT NOT NULL,
                decision_reason TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                stages_json TEXT,
                reconciliation_json TEXT,
                policy_checks_json TEXT,
                extracted_data_json TEXT,
                vendor_notification_draft TEXT,
                erp_payload_json TEXT,
                ai_insights_json TEXT,
                is_manual_override INTEGER DEFAULT 0,
                override_notes TEXT
            )
        """)

        # Migration safe check
        try:
            cur.execute("ALTER TABLE runs ADD COLUMN ai_insights_json TEXT")
        except sqlite3.OperationalError:
            pass

        conn.commit()

        # Seed initial data if tables are empty
        cur.execute("SELECT COUNT(*) FROM vendors")
        if cur.fetchone()[0] == 0:
            self._seed_baseline_data(conn)

        conn.close()

    def _seed_baseline_data(self, conn):
        cur = conn.cursor()

        # Vendors
        vendors_data = [
            ("VEND-001", "Apex Software Solutions LLC", json.dumps(["Apex Software", "Apex Solutions", "Apex Software LLC", "Apex Software Solutions"]), "US-849201948", "Net 30", "JPMorgan Chase ****4821", 1, "LOW"),
            ("VEND-002", "CloudScale Infrastructure Corp", json.dumps(["CloudScale Corp", "CloudScale", "CloudScale Infrastructure", "CloudScale Inc"]), "US-392019402", "Net 30", "Silicon Valley Bank ****1092", 1, "LOW"),
            ("VEND-003", "Nexus Office Supplies & Hardware", json.dumps(["Nexus Office", "Nexus Supplies", "Nexus Office Supplies"]), "US-119283746", "Net 15", "Bank of America ****3301", 1, "LOW"),
            ("VEND-004", "CyberGuard Security Partners", json.dumps(["CyberGuard", "CyberGuard Security", "CyberGuard Partners"]), "US-992019283", "Net 30", "Wells Fargo ****9941", 1, "LOW"),
            ("VEND-005", "Global Freight & Express", json.dumps(["Global Freight", "Global Express Logistics", "Global Freight & Express Inc"]), "US-774029182", "Net 30", "Citibank ****5521", 1, "LOW"),
            ("VEND-999", "Blacklisted Off-Shore Shell LLC", json.dumps(["Off-Shore Shell", "Suspicious Shell LLC"]), "US-000000000", "Immediate", "Unknown Bank ****0000", 0, "BLOCKED")
        ]
        cur.executemany("INSERT INTO vendors VALUES (?, ?, ?, ?, ?, ?, ?, ?)", vendors_data)

        # Purchase Orders
        pos_data = [
            ("PO-2026-101", "Apex Software Solutions LLC", "2026-10-01", 12500.00, 0.0, 12500.00, "USD", "OPEN", 2.0, 50.00),
            ("PO-2026-102", "CloudScale Infrastructure Corp", "2026-10-05", 8400.00, 0.0, 8400.00, "USD", "OPEN", 2.0, 30.00),
            ("PO-2026-103", "Global Freight & Express", "2026-10-10", 15000.00, 0.0, 15000.00, "USD", "OPEN", 1.5, 50.00),
            ("PO-2026-104", "Nexus Office Supplies & Hardware", "2026-10-12", 3250.00, 0.0, 3250.00, "USD", "OPEN", 2.0, 25.00),
            ("PO-2026-105", "CyberGuard Security Partners", "2026-09-15", 6000.00, 6000.00, 0.0, "USD", "FULFILLED", 1.0, 20.00)
        ]
        cur.executemany("INSERT INTO purchase_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", pos_data)

        # PO Line Items
        po_lines = [
            ("PO-2026-101", "ITEM-01", "Enterprise SaaS Platform License (Annual)", 1.0, 9500.00, 9500.00),
            ("PO-2026-101", "ITEM-02", "Priority 24/7 SLA Support Tier", 1.0, 3000.00, 3000.00),
            ("PO-2026-102", "CLD-01", "Dedicated Cloud Compute Instances (c6i.4xlarge)", 4.0, 1200.00, 4800.00),
            ("PO-2026-102", "CLD-02", "Managed PostgreSQL Database Cluster", 2.0, 1800.00, 3600.00),
            ("PO-2026-103", "FRT-01", "Q1 International Air Freight Logistics", 3.0, 5000.00, 15000.00),
            ("PO-2026-104", "HW-01", "Ergonomic Standing Desks - Pro Edition", 5.0, 450.00, 2250.00),
            ("PO-2026-104", "HW-02", "USB-C UltraWide 34-inch Monitors", 2.0, 500.00, 1000.00),
            ("PO-2026-105", "SEC-01", "Annual SOC2 Type II Penetration Testing", 1.0, 6000.00, 6000.00)
        ]
        cur.executemany("INSERT INTO po_line_items (po_number, item_code, description, quantity, unit_price, total_price) VALUES (?, ?, ?, ?, ?, ?)", po_lines)

        # Historical Invoices Ledger (Prior Accounting Periods already settled)
        hist_data = [
            ("INV-CG-9942", "CyberGuard Security Partners", "2026-10-15", 6000.00, "PO-2026-105", "PAID", "2026-10-16T14:22:00Z", "ACH-9821734"),
            ("INV-HIST-881", "Apex Software Solutions LLC", "2026-09-01", 2500.00, "PO-2025-089", "PAID", "2026-09-05T09:15:00Z", "ACH-7729101"),
            ("INV-NX-4412", "Nexus Office Supplies & Hardware", "2026-09-20", 1200.00, "PO-2025-095", "PAID", "2026-09-22T10:00:00Z", "WIRE-110294")
        ]
        cur.executemany("INSERT INTO historical_invoices (invoice_number, vendor_name, invoice_date, total_amount, po_number, status, paid_at, check_or_transfer_ref) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", hist_data)

        conn.commit()

    def reset(self):
        self.init_db(force_reset=True)

    def get_all_pos(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM purchase_orders")
        pos = []
        for r in cur.fetchall():
            po_dict = dict(r)
            cur.execute("SELECT item_code, description, quantity, unit_price, total_price FROM po_line_items WHERE po_number = ?", (po_dict["po_number"],))
            po_dict["line_items"] = [dict(li) for li in cur.fetchall()]
            pos.append(po_dict)
        conn.close()
        return pos

    def get_all_vendors(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM vendors")
        vendors = []
        for r in cur.fetchall():
            vd = dict(r)
            vd["aliases"] = json.loads(vd["aliases"])
            vd["is_approved"] = bool(vd["is_approved"])
            vendors.append(vd)
        conn.close()
        return vendors

    def get_historical_invoices(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM historical_invoices ORDER BY id DESC")
        hist = [dict(r) for r in cur.fetchall()]
        conn.close()
        return hist

    def get_po(self, po_number: Optional[str]) -> Optional[Dict[str, Any]]:
        if not po_number:
            return None
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM purchase_orders WHERE UPPER(po_number) = UPPER(?)", (po_number.strip(),))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        po = dict(row)
        cur.execute("SELECT item_code, description, quantity, unit_price, total_price FROM po_line_items WHERE UPPER(po_number) = UPPER(?)", (po_number.strip(),))
        po["line_items"] = [dict(li) for li in cur.fetchall()]
        conn.close()
        return po

    def find_vendor(self, vendor_name: Optional[str]) -> Tuple[Optional[Dict[str, Any]], float]:
        if not vendor_name:
            return None, 0.0
        query = vendor_name.strip().lower()
        all_v = self.get_all_vendors()

        for v in all_v:
            if v["vendor_name"].lower() == query:
                return v, 1.0

        for v in all_v:
            for alias in v["aliases"]:
                if alias.lower() == query:
                    return v, 0.98
                if alias.lower() in query or query in alias.lower():
                    return v, 0.90

        for v in all_v:
            clean_master = v["vendor_name"].lower().replace("llc", "").replace("inc", "").replace("corp", "").strip()
            clean_q = query.replace("llc", "").replace("inc", "").replace("corp", "").strip()
            if clean_master in clean_q or clean_q in clean_master:
                return v, 0.85

        return None, 0.0

    def find_po_fallback(self, vendor_name: Optional[str], total_amount: float) -> Tuple[Optional[Dict[str, Any]], str]:
        vendor, _ = self.find_vendor(vendor_name)
        if not vendor:
            return None, "Vendor could not be verified in master database"

        all_pos = self.get_all_pos()
        matching_pos = [po for po in all_pos if po["vendor_name"].lower() == vendor["vendor_name"].lower() and po["status"] in ["OPEN", "PARTIALLY_BILLED"]]

        if not matching_pos:
            return None, f"No active open POs found for vendor '{vendor['vendor_name']}'"

        for po in matching_pos:
            diff = abs(po["total_amount"] - total_amount)
            pct_diff = (diff / po["total_amount"]) * 100.0 if po["total_amount"] else 100.0
            if pct_diff <= po["tolerance_percentage"] or diff <= po["tolerance_amount"]:
                return po, f"Inferred matching PO '{po['po_number']}' based on vendor match and amount within {po['tolerance_percentage']}% tolerance."

        if len(matching_pos) == 1 and total_amount <= matching_pos[0]["remaining_amount"]:
            return matching_pos[0], f"Inferred matching PO '{matching_pos[0]['po_number']}' as single open PO for vendor with sufficient remaining balance (${matching_pos[0]['remaining_amount']:,.2f})."

        return None, f"Multiple or non-matching open POs exist for vendor '{vendor['vendor_name']}'. Manual PO selection required."

    def check_duplicate(self, vendor_name: Optional[str], invoice_number: Optional[str], total_amount: float) -> Optional[Dict[str, Any]]:
        if not invoice_number:
            return None

        clean_inv = invoice_number.strip().upper()
        vendor, _ = self.find_vendor(vendor_name)
        v_name = vendor["vendor_name"].lower() if vendor else (vendor_name.strip().lower() if vendor_name else "")

        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM historical_invoices")
        rows = cur.fetchall()
        conn.close()

        for r in rows:
            hist_inv = r["invoice_number"].strip().upper()
            hist_vendor = r["vendor_name"].strip().lower()
            hist_amt = r["total_amount"]

            # Exact invoice # and vendor match
            if clean_inv == hist_inv and (not v_name or v_name in hist_vendor or hist_vendor in v_name):
                return dict(r)

            # Typo invoice number match with identical amount and vendor
            if v_name and (v_name in hist_vendor or hist_vendor in v_name) and abs(hist_amt - total_amount) < 0.01:
                if clean_inv.replace("-", "").replace(" ", "") == hist_inv.replace("-", "").replace(" ", ""):
                    return dict(r)

        return None

    def record_approved_invoice(self, invoice_number: str, po_number: Optional[str], vendor_name: str, amount: float):
        conn = self.get_connection()
        cur = conn.cursor()

        # Insert into historical ledger
        cur.execute("""
            INSERT INTO historical_invoices (invoice_number, vendor_name, invoice_date, total_amount, po_number, status, paid_at, check_or_transfer_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_number,
            vendor_name,
            "2026-11-04",
            amount,
            po_number,
            "APPROVED",
            "Pending Disbursement",
            "ERP-AUTO-ACH"
        ))

        # Update PO remaining amount
        if po_number:
            cur.execute("SELECT total_amount, billed_amount FROM purchase_orders WHERE UPPER(po_number) = UPPER(?)", (po_number.strip(),))
            po_row = cur.fetchone()
            if po_row:
                new_billed = po_row["billed_amount"] + amount
                new_remaining = max(0.0, po_row["total_amount"] - new_billed)
                new_status = "FULFILLED" if new_remaining <= 0.01 else "PARTIALLY_BILLED"
                cur.execute("""
                    UPDATE purchase_orders
                    SET billed_amount = ?, remaining_amount = ?, status = ?
                    WHERE UPPER(po_number) = UPPER(?)
                """, (new_billed, new_remaining, new_status, po_number.strip()))

        conn.commit()
        conn.close()

    def record_run(self, run_data: Dict[str, Any]):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO runs (
                id, timestamp, invoice_filename, pdf_url, vendor_name,
                invoice_number, invoice_total, po_number, decision_status,
                decision_reason, confidence_score, stages_json,
                reconciliation_json, policy_checks_json, extracted_data_json,
                vendor_notification_draft, erp_payload_json, ai_insights_json, is_manual_override, override_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_data.get("id"),
            run_data.get("timestamp"),
            run_data.get("invoice_filename"),
            run_data.get("pdf_url"),
            run_data.get("vendor_name"),
            run_data.get("invoice_number"),
            run_data.get("invoice_total"),
            run_data.get("po_number"),
            run_data.get("decision_status"),
            run_data.get("decision_reason"),
            run_data.get("confidence_score"),
            json.dumps(run_data.get("stages", [])),
            json.dumps(run_data.get("reconciliation", {})),
            json.dumps(run_data.get("policy_checks", [])),
            json.dumps(run_data.get("extracted_data", {})),
            run_data.get("vendor_notification_draft"),
            json.dumps(run_data.get("erp_payload", {})),
            json.dumps(run_data.get("ai_insights", {})),
            1 if run_data.get("is_manual_override") else 0,
            run_data.get("override_notes")
        ))
        conn.commit()
        conn.close()

    def get_all_runs(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM runs ORDER BY timestamp DESC")
        runs = []
        for r in cur.fetchall():
            rd = dict(r)
            rd["stages"] = json.loads(rd["stages_json"]) if rd.get("stages_json") else []
            rd["reconciliation"] = json.loads(rd["reconciliation_json"]) if rd.get("reconciliation_json") else None
            rd["policy_checks"] = json.loads(rd["policy_checks_json"]) if rd.get("policy_checks_json") else []
            rd["extracted_data"] = json.loads(rd["extracted_data_json"]) if rd.get("extracted_data_json") else None
            rd["erp_payload"] = json.loads(rd["erp_payload_json"]) if rd.get("erp_payload_json") else {}
            rd["ai_insights"] = json.loads(rd["ai_insights_json"]) if rd.get("ai_insights_json") else None
            rd["is_manual_override"] = bool(rd.get("is_manual_override"))
            runs.append(rd)
        conn.close()
        return runs

    def update_run_review(self, run_id: str, action: str, notes: str, reviewer: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None

        current = dict(row)
        new_status = current["decision_status"]
        override_text = f"Manual {action} by {reviewer}: {notes}"

        if action == "APPROVE_OVERRIDE":
            new_status = "AUTO_APPROVED"
            # Update ERP PO
            self.record_approved_invoice(
                invoice_number=current["invoice_number"],
                po_number=current["po_number"],
                vendor_name=current["vendor_name"],
                amount=current["invoice_total"]
            )
        elif action == "REJECT":
            new_status = "REJECTED"

        cur.execute("""
            UPDATE runs
            SET decision_status = ?, is_manual_override = 1, override_notes = ?
            WHERE id = ?
        """, (new_status, override_text, run_id))
        conn.commit()
        conn.close()

        # Fetch updated
        all_runs = self.get_all_runs()
        return next((r for r in all_runs if r["id"] == run_id), None)

db_manager = DatabaseManager()
