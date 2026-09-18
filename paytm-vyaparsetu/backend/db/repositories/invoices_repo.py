from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime

from db.models import Invoice, InvoiceLineItem, InvoicePackagingAdjustment, InvoiceExtractionAudit
from core.ids import generate_id
from vision.schemas import ConfirmedChallanInput, ConfirmedLineItem, PackagingAdjustment
from core.logging import get_logger

logger = get_logger("db.invoices_repo")

def insert_confirmed_invoice(db: Session, merchant_id: str, distributor_id: str, input_data: ConfirmedChallanInput) -> Invoice:
    invoice_id = generate_id("inv_")
    
    # Parse date if available
    inv_date = None
    if input_data.challan_date:
        try:
            inv_date = datetime.strptime(input_data.challan_date, "%Y-%m-%d").date()
        except ValueError:
            inv_date = datetime.utcnow().date()
    else:
        inv_date = datetime.utcnow().date()
        
    payment_handle_type = input_data.payment_handle.handle_type if input_data.payment_handle else None
    payment_handle_value = input_data.payment_handle.value if input_data.payment_handle else None
    
    invoice = Invoice(
        invoice_id=invoice_id,
        merchant_id=merchant_id,
        distributor_id=distributor_id,
        invoice_date=inv_date,
        total_amount=input_data.total_payable,
        is_paid=False,
        challan_type=input_data.challan_type,
        capture_medium=input_data.capture_medium,
        challan_number=input_data.challan_number,
        distributor_gstin=input_data.distributor_gstin,
        vehicle_number=input_data.vehicle_number,
        payment_handle_type=payment_handle_type,
        payment_handle_value=payment_handle_value,
        tax_cgst=input_data.tax.cgst,
        tax_sgst=input_data.tax.sgst,
        tax_igst=input_data.tax.igst,
        additional_charges=input_data.additional_charges
    )
    
    db.add(invoice)
    logger.info(f"💾 [DB Write] Created Invoice: {invoice_id} for Amount: {invoice.total_amount}")
    return invoice

def insert_line_items(db: Session, invoice_id: str, distributor_id: str, line_items: List[ConfirmedLineItem]) -> List[InvoiceLineItem]:
    inserted_items = []
    for item in line_items:
        line_item_id = generate_id("lin_")
        
        # Normalize SKU
        normalized_sku = item.canonical_item_name.strip() if item.canonical_item_name else "Unknown Item"
        
        db_item = InvoiceLineItem(
            line_item_id=line_item_id,
            invoice_id=invoice_id,
            distributor_id=distributor_id,
            sku=normalized_sku,
            quantity=item.quantity,
            unit_price=item.unit_rate,
            raw_text=item.raw_text,
            unit=item.unit,
            hsn_code=item.hsn_code,
            is_free_scheme=item.is_free_scheme
        )
        db.add(db_item)
        inserted_items.append(db_item)
        
    logger.info(f"💾 [DB Write] Created {len(inserted_items)} Line Items for Invoice {invoice_id}")
    return inserted_items

def insert_packaging_adjustments(db: Session, invoice_id: str, adjustments: List[PackagingAdjustment]):
    for adj in adjustments:
        adjustment_id = generate_id("pkg_")
        db_adj = InvoicePackagingAdjustment(
            adjustment_id=adjustment_id,
            invoice_id=invoice_id,
            item_name=adj.item_name.strip(),
            direction=adj.direction,
            quantity=adj.quantity
        )
        db.add(db_adj)
    if adjustments:
        logger.info(f"💾 [DB Write] Created {len(adjustments)} Packaging Adjustments for Invoice {invoice_id}")

def insert_extraction_audit(
    db: Session, 
    invoice_id: str, 
    ocr_raw_text: str, 
    vision_llm_raw_response: dict, 
    model_used: str, 
    escalated: bool = False, 
    edited_fields: Optional[List[str]] = None
):
    audit_id = generate_id("aud_")
    audit = InvoiceExtractionAudit(
        audit_id=audit_id,
        invoice_id=invoice_id,
        ocr_raw_text=ocr_raw_text,
        vision_llm_raw_response=vision_llm_raw_response,
        model_used=model_used,
        escalated=escalated,
        merchant_edited_fields=edited_fields or []
    )
    db.add(audit)
    logger.info(f"💾 [DB Write] Created Extraction Audit {audit_id} for Invoice {invoice_id}")

def get_last_price(db: Session, distributor_id: str, sku: str, exclude_invoice_id: str) -> Optional[float]:
    """
    Returns the previous unit_price for the given sku from the same distributor.
    """
    result = db.query(InvoiceLineItem.unit_price).join(Invoice).filter(
        InvoiceLineItem.distributor_id == distributor_id,
        func.lower(InvoiceLineItem.sku) == sku.strip().lower(),
        Invoice.invoice_id != exclude_invoice_id
    ).order_by(
        desc(Invoice.invoice_date),
        desc(Invoice.created_at)
    ).first()
    
    logger.info(f"🔍 [DB Read] Fetched last price for SKU '{sku}' (Distributor: {distributor_id})")
    if result:
        return float(result[0])
    return None
