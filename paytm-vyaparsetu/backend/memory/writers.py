"""
memory/writers.py
Writes transactional facts to Cognee Cloud.
Enforces the strict Pydantic ontology before delegating to the graph client.
"""

from memory.ontology import Customer, Transaction, Distributor, Invoice, LineItem
from memory.graph_client import add_payload
from core.logging import get_logger

logger = get_logger("memory.writers")

async def remember_transaction(dataset_name: str, payload: dict) -> bool:
    """
    Ingests canonical payload from outbox CREDIT_ADDED event.
    Payload shape expected: txn_id, customer_id, merchant_id, amount
    """
    try:
        # Note: In a real system, we might need display_name for the Customer if we don't have it.
        # Assuming the caller/payload can provide a minimal placeholder or actual name.
        # For our test dataset, we will just pass generic display_name if missing.
        cust = Customer(
            customer_id=payload.get("customer_id", "unknown"),
            merchant_id=payload.get("merchant_id", "unknown"),
            display_name=payload.get("customer_name", "Unknown Customer")
        )
        
        txn = Transaction(
            txn_id=payload.get("txn_id", "unknown"),
            customer_id=cust.customer_id,
            amount=payload.get("amount", 0.0),
            txn_type=payload.get("txn_type", "CREDIT_ADDED")
        )
        
        # We pass a list of pydantic models to cognee
        # cognee will extract entities and relationships from these schema instances
        data_to_add = [cust, txn]
        
        logger.info(f"Writing transaction {txn.txn_id} to '{dataset_name}'")
        return await add_payload(dataset_name, data_to_add)
        
    except Exception as e:
        logger.error(f"Failed to map transaction to ontology: {e}")
        return False

async def remember_invoice(dataset_name: str, payload: dict) -> bool:
    """
    Ingests canonical payload from outbox INVOICE_CREATED event.
    Payload shape expected: invoice_id, distributor_id, merchant_id, total_amount, line_items
    """
    try:
        dist = Distributor(
            distributor_id=payload.get("distributor_id", "unknown"),
            merchant_id=payload.get("merchant_id", "unknown"),
            name=payload.get("distributor_name", "Unknown Distributor")
        )
        
        inv = Invoice(
            invoice_id=payload.get("invoice_id", "unknown"),
            distributor_id=dist.distributor_id,
            invoice_date=payload.get("invoice_date", "1970-01-01"),
            total_amount=payload.get("total_amount", 0.0)
        )
        
        data_to_add = [dist, inv]
        
        # Map line items if available
        line_items_data = payload.get("line_items", [])
        for item in line_items_data:
            li = LineItem(
                invoice_id=inv.invoice_id,
                sku=item.get("sku", "Unknown SKU"),
                quantity=item.get("quantity", 1),
                unit_price=item.get("unit_price", 0.0)
            )
            data_to_add.append(li)
            
        logger.info(f"Writing invoice {inv.invoice_id} with {len(line_items_data)} line items to '{dataset_name}'")
        return await add_payload(dataset_name, data_to_add)
        
    except Exception as e:
        logger.error(f"Failed to map invoice to ontology: {e}")
        return False
