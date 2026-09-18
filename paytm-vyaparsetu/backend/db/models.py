from sqlalchemy import (
    Column,
    String,
    Text,
    Numeric,
    Boolean,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Merchant(Base):
    __tablename__ = "merchants"

    merchant_id = Column(Text, primary_key=True)
    shop_name = Column(Text, nullable=False)
    owner_name = Column(Text, nullable=False)
    phone = Column(Text, nullable=False, unique=True)
    cognee_dataset = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    customers = relationship("Customer", back_populates="merchant")
    distributors = relationship("Distributor", back_populates="merchant")
    ledger_transactions = relationship("LedgerTransaction", back_populates="merchant")
    invoices = relationship("Invoice", back_populates="merchant")
    settlement_rollups = relationship("SettlementDailyRollup", back_populates="merchant")
    outbox_events = relationship("OutboxEvent", back_populates="merchant")
    insight_cache_entries = relationship("InsightCache", back_populates="merchant")
    alerts = relationship("Alert", back_populates="merchant")


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Text, primary_key=True)
    merchant_id = Column(Text, ForeignKey("merchants.merchant_id"), nullable=False)
    display_name = Column(Text, nullable=False)
    canonical_key = Column(Text, nullable=False)
    phone = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    merchant = relationship("Merchant", back_populates="customers")
    ledger_transactions = relationship("LedgerTransaction", back_populates="customer")

    __table_args__ = (
        UniqueConstraint("merchant_id", "canonical_key", name="uq_customer_merchant_canonical"),
    )


class Distributor(Base):
    __tablename__ = "distributors"

    distributor_id = Column(Text, primary_key=True)
    merchant_id = Column(Text, ForeignKey("merchants.merchant_id"), nullable=False)
    name = Column(Text, nullable=False)
    upi_id = Column(Text, nullable=True)
    canonical_key = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    merchant = relationship("Merchant", back_populates="distributors")
    invoices = relationship("Invoice", back_populates="distributor")
    invoice_line_items = relationship("InvoiceLineItem", back_populates="distributor")

    __table_args__ = (
        UniqueConstraint("merchant_id", "canonical_key", name="uq_distributor_merchant_canonical"),
    )


class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"

    txn_id = Column(Text, primary_key=True)
    merchant_id = Column(Text, ForeignKey("merchants.merchant_id"), nullable=False)
    customer_id = Column(Text, ForeignKey("customers.customer_id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    txn_type = Column(Text, nullable=False)
    items = Column(ARRAY(Text), nullable=False, server_default="{}")
    source = Column(Text, nullable=False)
    extraction_confidence = Column(Numeric(3, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    merchant = relationship("Merchant", back_populates="ledger_transactions")
    customer = relationship("Customer", back_populates="ledger_transactions")

    __table_args__ = (
        Index("idx_ledger_customer", "merchant_id", "customer_id"),
        Index("idx_ledger_date", "merchant_id", "created_at"),
    )


class Invoice(Base):
    __tablename__ = "invoices"

    invoice_id = Column(Text, primary_key=True)
    merchant_id = Column(Text, ForeignKey("merchants.merchant_id"), nullable=False)
    distributor_id = Column(Text, ForeignKey("distributors.distributor_id"), nullable=False)
    invoice_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    is_paid = Column(Boolean, nullable=False, default=False, server_default="false")
    paid_at = Column(DateTime(timezone=True), nullable=True)
    payout_reference = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Extended Challan Metadata
    challan_type = Column(Text, nullable=True)
    capture_medium = Column(Text, nullable=True)
    challan_number = Column(Text, nullable=True)
    distributor_gstin = Column(Text, nullable=True)
    vehicle_number = Column(Text, nullable=True)
    payment_handle_type = Column(Text, nullable=True)
    payment_handle_value = Column(Text, nullable=True)
    tax_cgst = Column(Numeric(10, 2), nullable=True)
    tax_sgst = Column(Numeric(10, 2), nullable=True)
    tax_igst = Column(Numeric(10, 2), nullable=True)
    additional_charges = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")

    merchant = relationship("Merchant", back_populates="invoices")
    distributor = relationship("Distributor", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice")
    packaging_adjustments = relationship("InvoicePackagingAdjustment", back_populates="invoice")
    extraction_audits = relationship("InvoiceExtractionAudit", back_populates="invoice")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    line_item_id = Column(Text, primary_key=True)
    invoice_id = Column(Text, ForeignKey("invoices.invoice_id"), nullable=False)
    distributor_id = Column(Text, ForeignKey("distributors.distributor_id"), nullable=False)
    sku = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False) # Changed to Numeric(10,2) to support float quantities (kg, crates)
    unit_price = Column(Numeric(10, 2), nullable=False)

    # Extended Line Item Metadata
    raw_text = Column(Text, nullable=True)
    unit = Column(Text, nullable=True)
    hsn_code = Column(Text, nullable=True)
    is_free_scheme = Column(Boolean, nullable=False, default=False, server_default="false")

    invoice = relationship("Invoice", back_populates="line_items")
    distributor = relationship("Distributor", back_populates="invoice_line_items")

    __table_args__ = (
        Index("idx_line_item_rate_lookup", "distributor_id", "sku", "invoice_id"),
    )


class InvoicePackagingAdjustment(Base):
    __tablename__ = "invoice_packaging_adjustments"

    adjustment_id = Column(Text, primary_key=True)
    invoice_id = Column(Text, ForeignKey("invoices.invoice_id"), nullable=False)
    item_name = Column(Text, nullable=False)
    direction = Column(Text, nullable=False)
    quantity = Column(Integer, nullable=False)

    invoice = relationship("Invoice", back_populates="packaging_adjustments")


class InvoiceExtractionAudit(Base):
    __tablename__ = "invoice_extraction_audit"

    audit_id = Column(Text, primary_key=True)
    invoice_id = Column(Text, ForeignKey("invoices.invoice_id"), nullable=False)
    ocr_raw_text = Column(Text, nullable=True)
    vision_llm_raw_response = Column(JSONB, nullable=False)
    model_used = Column(Text, nullable=False)
    escalated = Column(Boolean, nullable=False, default=False, server_default="false")
    merchant_edited_fields = Column(ARRAY(Text), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    invoice = relationship("Invoice", back_populates="extraction_audits")


class SettlementDailyRollup(Base):
    __tablename__ = "settlement_daily_rollups"

    rollup_id = Column(Text, primary_key=True)
    merchant_id = Column(Text, ForeignKey("merchants.merchant_id"), nullable=False)
    rollup_date = Column(Date, nullable=False)
    upi_collection_total = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")
    payout_total = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")
    net_balance = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")
    computed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    merchant = relationship("Merchant", back_populates="settlement_rollups")

    __table_args__ = (
        UniqueConstraint("merchant_id", "rollup_date", name="uq_settlement_merchant_date"),
    )


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    event_id = Column(Text, primary_key=True)
    merchant_id = Column(Text, ForeignKey("merchants.merchant_id"), nullable=False)
    event_type = Column(Text, nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(Text, nullable=False, default="PENDING", server_default="PENDING")
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    synced_at = Column(DateTime(timezone=True), nullable=True)

    merchant = relationship("Merchant", back_populates="outbox_events")

    __table_args__ = (
        Index(
            "idx_outbox_pending",
            "status",
            "created_at",
            postgresql_where=(status == "PENDING"),
        ),
    )


class InsightCache(Base):
    __tablename__ = "insight_cache"

    cache_key = Column(Text, primary_key=True)
    merchant_id = Column(Text, ForeignKey("merchants.merchant_id"), nullable=False)
    insight_type = Column(Text, nullable=False)
    result = Column(JSONB, nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    stale_after = Column(DateTime(timezone=True), nullable=False)

    merchant = relationship("Merchant", back_populates="insight_cache_entries")


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(Text, primary_key=True)
    merchant_id = Column(Text, ForeignKey("merchants.merchant_id"), nullable=False)
    alert_type = Column(Text, nullable=False)
    details = Column(JSONB, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    merchant = relationship("Merchant", back_populates="alerts")
