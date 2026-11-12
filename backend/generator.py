import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "sample_invoices")
os.makedirs(SAMPLES_DIR, exist_ok=True)

def create_invoice_pdf(
    filename: str,
    vendor_name: str,
    vendor_address: str,
    vendor_tax_id: str,
    vendor_email: str,
    invoice_number: str,
    invoice_date: str,
    due_date: str,
    po_reference: str,
    line_items: list,
    subtotal: float,
    tax: float,
    total: float,
    notes: str = ""
):
    pdf_path = os.path.join(SAMPLES_DIR, filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0f2249"),
        fontName="Helvetica-Bold"
    )
    
    vendor_title_style = ParagraphStyle(
        'VendorTitle',
        parent=styles['Heading2'],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#155ed9"),
        fontName="Helvetica-Bold"
    )

    normal_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )

    bold_style = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold"
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0284c7"),
        fontName="Helvetica-Bold"
    )

    elements = []

    # Header section: Vendor Info left, Invoice Title and Metadata right
    header_data = [
        [
            Paragraph(f"<b>{vendor_name}</b><br/>{vendor_address}<br/>Tax ID: {vendor_tax_id}<br/>Contact: {vendor_email}", normal_style),
            Paragraph(f"<font color='#155ed9' size=20><b>INVOICE</b></font><br/><br/>"
                      f"<b>Invoice #:</b> {invoice_number}<br/>"
                      f"<b>Date:</b> {invoice_date}<br/>"
                      f"<b>Due Date:</b> {due_date}<br/>"
                      f"<b>PO Ref:</b> <b>{po_reference if po_reference else 'N/A (Missing)'}</b>", normal_style)
        ]
    ]

    header_table = Table(header_data, colWidths=[300, 230])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))

    # Bill To section
    bill_to_data = [
        [
            Paragraph("<b>BILL TO:</b><br/>Acme Corporation Inc.<br/>Accounts Payable Division<br/>100 Innovation Way, Suite 400<br/>San Francisco, CA 94105<br/>ap@acmecorp.com", normal_style),
            Paragraph(f"<b>PAYMENT TERMS:</b> Net 30<br/><b>CURRENCY:</b> USD ($)<br/><b>REMITTANCE:</b> Wire / ACH Transfer", normal_style)
        ]
    ]
    bill_to_table = Table(bill_to_data, colWidths=[300, 230])
    bill_to_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(bill_to_table)
    elements.append(Spacer(1, 20))

    # Line Items Table
    table_data = [
        [
            Paragraph("<b>Item / Description</b>", bold_style),
            Paragraph("<b>Qty</b>", bold_style),
            Paragraph("<b>Unit Price</b>", bold_style),
            Paragraph("<b>Total</b>", bold_style)
        ]
    ]

    for item in line_items:
        table_data.append([
            Paragraph(f"<b>{item.get('code', '')}</b> {item['desc']}", normal_style),
            Paragraph(f"{item['qty']:.1f}", normal_style),
            Paragraph(f"${item['price']:,.2f}", normal_style),
            Paragraph(f"${item['total']:,.2f}", normal_style)
        ])

    items_table = Table(table_data, colWidths=[300, 50, 90, 90])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f2249")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))

    # Summary Totals Section
    summary_data = [
        ["", Paragraph("<b>Subtotal:</b>", normal_style), f"${subtotal:,.2f}"],
        ["", Paragraph("<b>Tax / Freight:</b>", normal_style), f"${tax:,.2f}"],
        ["", Paragraph("<b>TOTAL DUE (USD):</b>", bold_style), f"${total:,.2f}"]
    ]
    summary_table = Table(summary_data, colWidths=[300, 140, 90])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEABOVE', (1,2), (2,2), 1, colors.HexColor("#0f2249")),
    ]))
    elements.append(summary_table)

    if notes:
        elements.append(Spacer(1, 15))
        note_p = Paragraph(f"<b>Vendor Remarks / Delivery Notes:</b><br/>{notes}", normal_style)
        note_table = Table([[note_p]], colWidths=[530])
        note_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#eff6ff")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#bfdbfe")),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(note_table)

    elements.append(Spacer(1, 25))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
    elements.append(Paragraph("Thank you for your business. Remit electronic ACH payments to JP Morgan Chase, Routing: 021000021. For billing queries email ap-inquiries@vendor.com", normal_style))

    doc.build(elements)
    print(f"Generated PDF: {pdf_path}")
    return pdf_path

def generate_all_samples():
    print("Generating comprehensive test invoice PDFs...")

    # 1. Happy Path: Apex Software Solutions LLC (Matches PO-2026-101 exactly)
    create_invoice_pdf(
        filename="1_Happy_Path_Apex_Exact_Match.pdf",
        vendor_name="Apex Software Solutions LLC",
        vendor_address="742 Evergreen Terrace, Suite 100, Austin, TX 78701",
        vendor_tax_id="US-849201948",
        vendor_email="billing@apexsoftware.com",
        invoice_number="INV-2026-0881",
        invoice_date="2026-10-14",
        due_date="2026-11-14",
        po_reference="PO-2026-101",
        line_items=[
            {"code": "[ITEM-01]", "desc": "Enterprise SaaS Platform License (Annual)", "qty": 1.0, "price": 9500.00, "total": 9500.00},
            {"code": "[ITEM-02]", "desc": "Priority 24/7 SLA Support Tier", "qty": 1.0, "price": 3000.00, "total": 3000.00}
        ],
        subtotal=12500.00,
        tax=0.00,
        total=12500.00,
        notes="Annual contract renewal per master services agreement executed under PO-2026-101."
    )

    # 2. Edge Case 1: CloudScale Infrastructure Corp (Price variance breaches 2% tolerance)
    create_invoice_pdf(
        filename="2_Edge_Case_Price_Breach_CloudScale.pdf",
        vendor_name="CloudScale Infrastructure Corp",
        vendor_address="500 Cloud Parkway, Seattle, WA 98101",
        vendor_tax_id="US-392019402",
        vendor_email="ar@cloudscale.io",
        invoice_number="INV-CS-4190",
        invoice_date="2026-10-18",
        due_date="2026-11-18",
        po_reference="PO-2026-102",
        line_items=[
            {"code": "[CLD-01]", "desc": "Dedicated Cloud Compute Instances (c6i.4xlarge)", "qty": 4.0, "price": 1400.00, "total": 5600.00}, # PO rate was $1,200 (+$200/unit = +16.7%)
            {"code": "[CLD-02]", "desc": "Managed PostgreSQL Database Cluster", "qty": 2.0, "price": 1800.00, "total": 3600.00}
        ],
        subtotal=9200.00,
        tax=0.00,
        total=9200.00, # PO Total was $8,400. Variance = +$800 (+9.52%)
        notes="Notice: Compute instance rates updated pursuant to Q4 energy surcharge adjustment."
    )

    # 3. Edge Case 2: Global Freight & Express (Split PO / Partial Fulfillment)
    create_invoice_pdf(
        filename="3_Edge_Case_Split_PO_Partial_Freight.pdf",
        vendor_name="Global Freight & Express",
        vendor_address="1200 Terminal Way, Newark, NJ 07114",
        vendor_tax_id="US-774029182",
        vendor_email="finance@globalfreight.com",
        invoice_number="INV-GF-7710-P1",
        invoice_date="2026-10-20",
        due_date="2026-11-20",
        po_reference="PO-2026-103",
        line_items=[
            {"code": "[FRT-01]", "desc": "Q1 International Air Freight Logistics - Partial Delivery 1 of 3", "qty": 1.0, "price": 5000.00, "total": 5000.00}
        ],
        subtotal=5000.00,
        tax=0.00,
        total=5000.00, # Billed $5k out of $15k PO. Remaining balance will be $10k.
        notes="Partial shipment 1 of 3 delivered and signed. Remaining 2 shipments scheduled for next month."
    )

    # 4. Edge Case 3: CyberGuard Security Partners (Duplicate Invoice submission)
    create_invoice_pdf(
        filename="4_Edge_Case_Duplicate_CyberGuard.pdf",
        vendor_name="CyberGuard Security Partners",
        vendor_address="88 Wall Street, New York, NY 10005",
        vendor_tax_id="US-992019283",
        vendor_email="billing@cyberguard-security.com",
        invoice_number="INV-CG-9942", # Already paid in ERP on 2026-10-16!
        invoice_date="2026-10-15",
        due_date="2026-11-15",
        po_reference="PO-2026-105",
        line_items=[
            {"code": "[SEC-01]", "desc": "Annual SOC2 Type II Penetration Testing", "qty": 1.0, "price": 6000.00, "total": 6000.00}
        ],
        subtotal=6000.00,
        tax=0.00,
        total=6000.00,
        notes="Duplicate submission - please verify payment status if already remitted."
    )

    # 5. Edge Case 4: Shadow AI Labs Inc (Unapproved Vendor & Missing PO)
    create_invoice_pdf(
        filename="5_Edge_Case_Unapproved_Vendor_Missing_PO.pdf",
        vendor_name="Shadow AI Labs Inc",
        vendor_address="Unknown Address, Remote PO Box 99, Tortola, BVI",
        vendor_tax_id="FOREIGN-PENDING",
        vendor_email="crypto-billing@shadow-ai-labs.xyz",
        invoice_number="INV-UNAUTH-882",
        invoice_date="2026-10-22",
        due_date="2026-10-29",
        po_reference="", # Missing PO!
        line_items=[
            {"code": "[UNLISTED]", "desc": "Experimental H100 Cluster Compute Time (Unbudgeted)", "qty": 1.0, "price": 4200.00, "total": 4200.00}
        ],
        subtotal=4200.00,
        tax=0.00,
        total=4200.00,
        notes="Urgent payment required. No PO provided by internal requester."
    )

    # 6. Edge Case 5: Nexus Office Supplies (Minor Shipping Variance within 2% Tolerance)
    create_invoice_pdf(
        filename="6_Edge_Case_Minor_Variance_Within_Tolerance.pdf",
        vendor_name="Nexus Office Supplies & Hardware",
        vendor_address="45 Industrial Boulevard, Chicago, IL 60607",
        vendor_tax_id="US-119283746",
        vendor_email="orders@nexusoffice.com",
        invoice_number="INV-NX-5021",
        invoice_date="2026-10-25",
        due_date="2026-11-25",
        po_reference="PO-2026-104",
        line_items=[
            {"code": "[HW-01]", "desc": "Ergonomic Standing Desks - Pro Edition", "qty": 5.0, "price": 450.00, "total": 2250.00},
            {"code": "[HW-02]", "desc": "USB-C UltraWide 34-inch Monitors", "qty": 2.0, "price": 500.00, "total": 1000.00},
            {"code": "[SHIP]", "desc": "Standard Ground Courier Freight Handling", "qty": 1.0, "price": 18.50, "total": 18.50}
        ],
        subtotal=3250.00,
        tax=18.50,
        total=3268.50, # PO Total is $3,250.00. Variance = $18.50 (0.57% <= 2.0% tolerance, <= $25 tolerance amount)
        notes="Delivery completed via standard ground carrier. $18.50 fuel surcharged as permitted under terms."
    )

    # 7. Edge Case 6: Cross-Vendor PO Mismatch (CloudScale billing against Apex Software's PO-2026-101)
    create_invoice_pdf(
        filename="7_Edge_Case_Cross_Vendor_PO.pdf",
        vendor_name="CloudScale Infrastructure Corp",
        vendor_address="500 Cloud Way, San Francisco, CA 94105",
        vendor_tax_id="US-392019402",
        vendor_email="billing@cloudscale.io",
        invoice_number="INV-CS-CROSS-991",
        invoice_date="2026-10-26",
        due_date="2026-11-26",
        po_reference="PO-2026-101", # Belongs to Apex Software Solutions!
        line_items=[
            {"code": "[CLD-01]", "desc": "Dedicated Cloud Compute Instances (Misattributed PO)", "qty": 1.0, "price": 12500.00, "total": 12500.00}
        ],
        subtotal=12500.00,
        tax=0.00,
        total=12500.00,
        notes="Security test: Vendor cites valid PO belonging to another company."
    )

    # 8. Edge Case 7: Missing Invoice Number (Mandatory metadata omission)
    create_invoice_pdf(
        filename="8_Edge_Case_Missing_Invoice_Number.pdf",
        vendor_name="Apex Software Solutions LLC",
        vendor_address="100 Innovation Way, Suite 400, Austin, TX 78701",
        vendor_tax_id="US-849201948",
        vendor_email="ar@apexsoftware.com",
        invoice_number="", # Missing invoice number!
        invoice_date="2026-10-27",
        due_date="2026-11-27",
        po_reference="PO-2026-101",
        line_items=[
            {"code": "[ITEM-01]", "desc": "Enterprise SaaS Platform License (Annual)", "qty": 1.0, "price": 9500.00, "total": 9500.00},
            {"code": "[ITEM-02]", "desc": "Priority 24/7 SLA Support Tier", "qty": 1.0, "price": 3000.00, "total": 3000.00}
        ],
        subtotal=12500.00,
        tax=0.00,
        total=12500.00,
        notes="Notice: Invoice number omitted from billing template."
    )

    print("All sample invoice PDFs generated successfully!")

if __name__ == "__main__":
    generate_all_samples()
