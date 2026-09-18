from enum import Enum
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field

class ChallanType(str, Enum):
    FORMAL_GST = "FORMAL_GST"
    CARBON_COPY_BOOK = "CARBON_COPY_BOOK"
    THERMAL_POS_ROLL = "THERMAL_POS_ROLL"
    DOT_MATRIX_CONTINUOUS = "DOT_MATRIX_CONTINUOUS"
    HANDWRITTEN_SCRAP = "HANDWRITTEN_SCRAP"
    UNKNOWN = "UNKNOWN"

class CaptureMedium(str, Enum):
    DIRECT_UPLOAD = "DIRECT_UPLOAD"
    CAMERA_PHOTO = "CAMERA_PHOTO"
    WHATSAPP_FORWARD = "WHATSAPP_FORWARD"

class PackagingDirection(str, Enum):
    RECEIVED = "RECEIVED"
    RETURNED = "RETURNED"

class PaymentHandleType(str, Enum):
    UPI = "UPI"
    PHONE = "PHONE"
    BANK = "BANK"

# --- Stage A Schema ---
class PreprocessedImageMeta(BaseModel):
    original_format: str
    original_dimensions: Tuple[int, int]
    was_rotated: bool
    contrast_enhanced: bool
    resized_to: Tuple[int, int]
    grayscale_variant_created: bool

# --- Stage B Schema ---
class OCRGroundingResult(BaseModel):
    full_text: str
    text_blocks: List[dict] = Field(default_factory=list)
    avg_confidence: float
    used: bool

# --- Stage C Schemas ---
class LineItem(BaseModel):
    raw_text: str
    canonical_item_name: str
    quantity: float
    unit: str
    unit_rate: float
    line_total: float
    hsn_code: Optional[str] = None
    is_free_scheme: bool = False
    item_confidence: float

class PackagingAdjustment(BaseModel):
    item_name: str
    direction: str
    quantity: int

class PaymentHandle(BaseModel):
    handle_type: str
    value: str

class TaxBreakdown(BaseModel):
    cgst: Optional[float] = None
    sgst: Optional[float] = None
    igst: Optional[float] = None
    cess: Optional[float] = None

class ChallanExtractionResult(BaseModel):
    challan_type: str
    capture_medium: str
    challan_number: Optional[str] = None
    challan_date: Optional[str] = None
    distributor_name_raw: str
    distributor_gstin: Optional[str] = None
    vehicle_number: Optional[str] = None
    e_way_bill_number: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)
    packaging_adjustments: List[PackagingAdjustment] = Field(default_factory=list)
    payment_handle: Optional[PaymentHandle] = None
    subtotal: float
    tax: TaxBreakdown = Field(default_factory=TaxBreakdown)
    additional_charges: float = 0.0
    total_payable: float
    metadata_confidence: float
    line_items_confidence: float
    overall_confidence: float

# --- Stage D Schema ---
class ConfirmedLineItem(BaseModel):
    raw_text: str
    canonical_item_name: str
    quantity: float
    unit: str
    unit_rate: float
    line_total: float
    hsn_code: Optional[str] = None
    is_free_scheme: bool = False

class ConfirmedChallanInput(BaseModel):
    challan_type: str
    capture_medium: str
    challan_number: Optional[str] = None
    challan_date: Optional[str] = None
    distributor_name_raw: str
    distributor_gstin: Optional[str] = None
    vehicle_number: Optional[str] = None
    e_way_bill_number: Optional[str] = None
    line_items: List[ConfirmedLineItem] = Field(default_factory=list)
    packaging_adjustments: List[PackagingAdjustment] = Field(default_factory=list)
    payment_handle: Optional[PaymentHandle] = None
    subtotal: float
    tax: TaxBreakdown = Field(default_factory=TaxBreakdown)
    additional_charges: float = 0.0
    total_payable: float
