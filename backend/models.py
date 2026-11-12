from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class RiskRating(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKED = "BLOCKED"

class DecisionStatus(str, Enum):
    AUTO_APPROVED = "AUTO_APPROVED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"

class StageStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"

class LineItem(BaseModel):
    item_code: Optional[str] = None
    description: str
    quantity: float = 1.0
    unit_price: float
    total_price: float
    tax_rate: Optional[float] = 0.0
    tax_amount: Optional[float] = 0.0

class ExtractedInvoice(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_tax_id: Optional[str] = None
    vendor_address: Optional[str] = None
    po_reference: Optional[str] = None
    currency: str = "USD"
    line_items: List[LineItem] = Field(default_factory=list)
    subtotal: float = 0.0
    tax_amount: float = 0.0
    total_amount: float = 0.0
    payment_terms: Optional[str] = "Net 30"
    bank_account_number: Optional[str] = None
    raw_text_snippet: Optional[str] = None
    confidence_score: float = 95.0
    extraction_method: str = "HYBRID_OCR_PARSER"

class POLineItem(BaseModel):
    item_code: str
    description: str
    quantity: float
    unit_price: float
    total_price: float

class PurchaseOrder(BaseModel):
    po_number: str
    vendor_name: str
    po_date: str
    total_amount: float
    billed_amount: float = 0.0
    remaining_amount: float
    currency: str = "USD"
    status: str = "OPEN"  # OPEN, PARTIALLY_BILLED, FULFILLED
    line_items: List[POLineItem] = Field(default_factory=list)
    tolerance_percentage: float = 2.0  # Allowable price/total variance %
    tolerance_amount: float = 25.0    # Allowable absolute dollar variance

class VendorMaster(BaseModel):
    vendor_id: str
    vendor_name: str
    aliases: List[str] = Field(default_factory=list)
    tax_id: Optional[str] = None
    payment_terms: str = "Net 30"
    bank_account: Optional[str] = None
    is_approved: bool = True
    risk_rating: RiskRating = RiskRating.LOW

class StageLog(BaseModel):
    stage_id: str
    stage_name: str
    status: StageStatus = StageStatus.PENDING
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_ms: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)

class LineItemMatch(BaseModel):
    invoice_description: str
    invoice_qty: float
    invoice_unit_price: float
    invoice_total: float
    po_item_code: Optional[str] = None
    po_description: Optional[str] = None
    po_qty: Optional[float] = None
    po_unit_price: Optional[float] = None
    po_total: Optional[float] = None
    match_status: str  # EXACT_MATCH, TOLERANCE_MATCH, VARIANCE_BREACH, UNMATCHED, BUNDLED
    price_variance: float = 0.0
    qty_variance: float = 0.0
    total_variance: float = 0.0
    variance_pct: float = 0.0
    notes: str = ""

class ReconciliationResult(BaseModel):
    po_found: bool = False
    po_number: Optional[str] = None
    po_total: float = 0.0
    po_remaining_before: float = 0.0
    po_remaining_after: float = 0.0
    invoice_total: float = 0.0
    total_variance: float = 0.0
    variance_percentage: float = 0.0
    tolerance_breached: bool = False
    is_partial_fulfillment: bool = False
    is_bundled: bool = False
    line_matches: List[LineItemMatch] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

class PolicyCheck(BaseModel):
    check_id: str
    check_name: str
    passed: bool
    severity: str  # INFO, WARNING, CRITICAL
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

class DecisionOutput(BaseModel):
    status: DecisionStatus
    confidence_score: float
    summary_reason: str
    detailed_rationale: List[str]
    reconciliation: ReconciliationResult
    policy_checks: List[PolicyCheck]
    risk_score: int  # 0 to 100
    recommended_action: str
    vendor_notification_draft: Optional[str] = None
    erp_payload: Dict[str, Any] = Field(default_factory=dict)

class RunRecord(BaseModel):
    id: str
    timestamp: str
    invoice_filename: str
    pdf_url: Optional[str] = None
    vendor_name: str
    invoice_number: str
    invoice_total: float
    po_number: Optional[str] = None
    decision_status: DecisionStatus
    decision_reason: str
    confidence_score: float
    stages: List[StageLog] = Field(default_factory=list)
    reconciliation: Optional[ReconciliationResult] = None
    policy_checks: List[PolicyCheck] = Field(default_factory=list)
    extracted_data: Optional[ExtractedInvoice] = None
    vendor_notification_draft: Optional[str] = None
    erp_payload: Dict[str, Any] = Field(default_factory=dict)
    ai_insights: Optional[Dict[str, Any]] = None
    is_manual_override: bool = False
    override_notes: Optional[str] = None
