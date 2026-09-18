from uuid import uuid4

def generate_id(prefix: str) -> str:
    """
    Generate a short, prefixed, human-readable ID using 6 hex characters.
    Example: generate_id('mer_') -> 'mer_a1b2c3'
    """
    return f"{prefix}{uuid4().hex[:6]}"

def generate_merchant_id() -> str:
    return generate_id("mer_")

def generate_customer_id() -> str:
    return generate_id("cus_")

def generate_distributor_id() -> str:
    return generate_id("dis_")

def generate_txn_id() -> str:
    return generate_id("txn_")

def generate_invoice_id() -> str:
    return generate_id("inv_")

def generate_line_item_id() -> str:
    return generate_id("lin_")

def generate_outbox_id() -> str:
    return generate_id("obx_")

def generate_alert_id() -> str:
    return generate_id("alt_")

def generate_packaging_adjustment_id() -> str:
    return generate_id("pkg_")

def generate_extraction_audit_id() -> str:
    return generate_id("aud_")

def generate_settlement_id(rollup_date_str: str, merchant_id: str) -> str:
    """
    Deterministic settlement rollup ID based on date and merchant.
    Example: set_2026-09-16_mer_a1b2c3
    """
    return f"set_{rollup_date_str}_{merchant_id}"

