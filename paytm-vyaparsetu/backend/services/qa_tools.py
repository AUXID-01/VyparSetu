from enum import Enum
from datetime import date, datetime, timedelta, time
from typing import Optional, Any, Tuple, List, Dict
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from sqlalchemy import func
import re

from db.models import Customer, Distributor, Invoice, InvoiceLineItem, LedgerTransaction, SettlementDailyRollup

# ---------------------------------------------------------
# 1. Enums & Pydantic Argument Schemas
# ---------------------------------------------------------

class DateRange(str, Enum):
    TODAY = "TODAY"
    YESTERDAY = "YESTERDAY"
    THIS_WEEK = "THIS_WEEK"
    LAST_WEEK = "LAST_WEEK"
    LAST_7_DAYS = "LAST_7_DAYS"
    THIS_MONTH = "THIS_MONTH"
    LAST_MONTH = "LAST_MONTH"

def normalize_date_range(date_range: DateRange, reference_date: Optional[date] = None) -> Tuple[datetime, datetime]:
    ref_date = reference_date or date.today()
    ref_dt = datetime.combine(ref_date, time.min)
    
    if date_range == DateRange.TODAY:
        start = ref_dt
        end = start + timedelta(days=1)
    elif date_range == DateRange.YESTERDAY:
        start = ref_dt - timedelta(days=1)
        end = ref_dt
    elif date_range == DateRange.THIS_WEEK:
        start = ref_dt - timedelta(days=ref_dt.weekday())
        end = start + timedelta(days=7)
    elif date_range == DateRange.LAST_WEEK:
        end = ref_dt - timedelta(days=ref_dt.weekday())
        start = end - timedelta(days=7)
    elif date_range == DateRange.LAST_7_DAYS:
        # today + previous 6 calendar days
        start = ref_dt - timedelta(days=6)
        end = ref_dt + timedelta(days=1)
    elif date_range == DateRange.THIS_MONTH:
        start = ref_dt.replace(day=1)
        # advance to next month, subtract 1 sec to find last day? No, just replace month and set to 1st.
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
    elif date_range == DateRange.LAST_MONTH:
        if ref_dt.month == 1:
            end = ref_dt.replace(year=ref_dt.year - 1, month=12, day=1)
        else:
            end = ref_dt.replace(month=ref_dt.month - 1, day=1)
        
        if end.month == 1:
            start = end.replace(year=end.year - 1, month=12, day=1)
        else:
            start = end.replace(month=end.month - 1, day=1)
        # End is the 1st of the current month
        end = ref_dt.replace(day=1)
    else:
        # Default to TODAY
        start = ref_dt
        end = start + timedelta(days=1)

    return start, end

class CustomerDueQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_name: str

class CustomerTransactionsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_name: str
    date_range: DateRange = DateRange.LAST_7_DAYS

class SkuPriceTrendQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_name: str
    days: int = Field(default=60, ge=1, le=365)

class SupplierPayoutQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    distributor_name: str
    date_range: DateRange = DateRange.LAST_WEEK

class SupplierInvoiceQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    distributor_name: str
    date_range: DateRange = DateRange.LAST_WEEK

class DailyBalanceQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_date: Optional[date] = None

# ---------------------------------------------------------
# 2. Entity Resolvers
# ---------------------------------------------------------

def resolve_customer(db: Session, merchant_id: str, customer_name: str) -> Tuple[Optional[Customer], bool, List[str]]:
    clean_name = customer_name.strip().lower()
    
    # 1. Exact / Case-insensitive match on display_name or canonical_key
    exact_matches = db.query(Customer).filter(
        Customer.merchant_id == merchant_id,
        (func.lower(Customer.display_name) == clean_name) | (Customer.canonical_key == clean_name)
    ).all()
    
    if len(exact_matches) == 1:
        return exact_matches[0], False, [exact_matches[0].display_name]
    
    # 2. Fallback to ILIKE
    ilike_matches = db.query(Customer).filter(
        Customer.merchant_id == merchant_id,
        Customer.display_name.ilike(f"%{clean_name}%")
    ).all()
    
    if len(ilike_matches) == 1:
        return ilike_matches[0], False, [ilike_matches[0].display_name]
    
    if len(ilike_matches) > 1:
        names = [m.display_name for m in ilike_matches]
        return None, True, names
        
    # 3. Fuzzy fallback using pg_trgm
    fuzzy_matches = db.query(Customer).filter(
        Customer.merchant_id == merchant_id,
        Customer.display_name.op('%')(clean_name)
    ).all()
    
    if len(fuzzy_matches) == 1:
        return fuzzy_matches[0], False, [fuzzy_matches[0].display_name]
    
    if len(fuzzy_matches) > 1:
        names = [m.display_name for m in fuzzy_matches]
        return None, True, names

    return None, False, []


def resolve_distributor(db: Session, merchant_id: str, distributor_name: str) -> Tuple[Optional[Distributor], bool, List[str]]:
    clean_name = distributor_name.strip().lower()
    
    exact_matches = db.query(Distributor).filter(
        Distributor.merchant_id == merchant_id,
        (func.lower(Distributor.name) == clean_name) | (Distributor.canonical_key == clean_name)
    ).all()
    
    if len(exact_matches) == 1:
        return exact_matches[0], False, [exact_matches[0].name]
        
    ilike_matches = db.query(Distributor).filter(
        Distributor.merchant_id == merchant_id,
        Distributor.name.ilike(f"%{clean_name}%")
    ).all()
    
    if len(ilike_matches) == 1:
        return ilike_matches[0], False, [ilike_matches[0].name]
        
    if len(ilike_matches) > 1:
        names = [m.name for m in ilike_matches]
        return None, True, names
        
    # Fuzzy fallback using pg_trgm
    fuzzy_matches = db.query(Distributor).filter(
        Distributor.merchant_id == merchant_id,
        Distributor.name.op('%')(clean_name)
    ).all()
    
    if len(fuzzy_matches) == 1:
        return fuzzy_matches[0], False, [fuzzy_matches[0].name]
        
    if len(fuzzy_matches) > 1:
        names = [m.name for m in fuzzy_matches]
        return None, True, names

    return None, False, []

def resolve_sku(db: Session, merchant_id: str, item_name: str) -> Tuple[Optional[str], bool, List[str]]:
    clean_item = item_name.strip().lower()
    
    pack_size_match = re.search(r'(\d+(?:\.\d+)?\s*(?:g|kg|l|ml|litre|liter|gm|gram|piece|pc|box)s?)\b', clean_item)
    pack_size_constraint = pack_size_match.group(1).replace(' ', '') if pack_size_match else None
    
    def filter_by_pack_size(candidates: List[str]) -> List[str]:
        if not pack_size_constraint:
            return candidates
        filtered = []
        for sku in candidates:
            sku_pack_match = re.search(r'(\d+(?:\.\d+)?\s*(?:g|kg|l|ml|litre|liter|gm|gram|piece|pc|box)s?)\b', sku.lower())
            sku_pack = sku_pack_match.group(1).replace(' ', '') if sku_pack_match else None
            if sku_pack:
                if sku_pack == pack_size_constraint:
                    filtered.append(sku)
            else:
                filtered.append(sku)
        return filtered

    # 1. Exact match
    exact_matches = db.query(InvoiceLineItem.sku).join(Invoice).filter(
        Invoice.merchant_id == merchant_id,
        func.lower(InvoiceLineItem.sku) == clean_item
    ).distinct().all()
    exact_skus = [s[0] for s in exact_matches]
    if len(exact_skus) == 1:
        return exact_skus[0], False, exact_skus

    # 2. ILIKE match
    ilike_matches = db.query(InvoiceLineItem.sku).join(Invoice).filter(
        Invoice.merchant_id == merchant_id,
        (func.lower(InvoiceLineItem.sku).ilike(f"%{clean_item}%")) | 
        (func.lower(InvoiceLineItem.raw_text).ilike(f"%{clean_item}%"))
    ).distinct().all()
    ilike_skus = [s[0] for s in ilike_matches]
    
    if ilike_skus:
        filtered = filter_by_pack_size(ilike_skus)
        if len(filtered) == 1:
            return filtered[0], False, filtered
        if len(filtered) > 1:
            return None, True, filtered
            
    # 3. Fuzzy match
    fuzzy_matches = db.query(InvoiceLineItem.sku).join(Invoice).filter(
        Invoice.merchant_id == merchant_id,
        InvoiceLineItem.sku.op('%')(clean_item)
    ).distinct().all()
    fuzzy_skus = [s[0] for s in fuzzy_matches]
    
    if fuzzy_skus:
        filtered = filter_by_pack_size(fuzzy_skus)
        if len(filtered) == 1:
            return filtered[0], False, filtered
        if len(filtered) > 1:
            return None, True, filtered
            
    return None, False, []

# ---------------------------------------------------------
# 3. Deterministic Business Query Implementations
# ---------------------------------------------------------

def tool_get_customer_due(db: Session, merchant_id: str, args: CustomerDueQuery) -> dict:
    customer, is_ambiguous, matches = resolve_customer(db, merchant_id, args.customer_name)
    if is_ambiguous:
        return {"status": "ambiguous", "message": f"Multiple customers found matching '{args.customer_name}'", "candidates": matches}
    if not customer:
        return {"status": "not_found", "message": f"Customer '{args.customer_name}' not found."}

    from sqlalchemy import case
    balance = db.query(
        func.sum(
            case(
                (LedgerTransaction.txn_type == 'CREDIT_ADDED', LedgerTransaction.amount),
                (LedgerTransaction.txn_type == 'CREDIT_PAID', -LedgerTransaction.amount),
                else_=0
            )
        )
    ).filter(
        LedgerTransaction.customer_id == customer.customer_id,
        LedgerTransaction.merchant_id == merchant_id
    ).scalar() or 0.0

    last_txn = db.query(LedgerTransaction).filter(
        LedgerTransaction.customer_id == customer.customer_id,
        LedgerTransaction.merchant_id == merchant_id
    ).order_by(LedgerTransaction.created_at.desc()).first()
    
    last_date = last_txn.created_at.isoformat() if last_txn else None

    return {
        "status": "success",
        "data": {
            "customer": customer.display_name,
            "outstanding_due": float(balance),
            "last_transaction_date": last_date
        }
    }

def tool_get_customer_transactions(db: Session, merchant_id: str, args: CustomerTransactionsQuery) -> dict:
    customer, is_ambiguous, matches = resolve_customer(db, merchant_id, args.customer_name)
    if is_ambiguous:
        return {"status": "ambiguous", "message": f"Multiple customers found", "candidates": matches}
    if not customer:
        return {"status": "not_found", "message": f"Customer '{args.customer_name}' not found."}

    start_dt, end_dt = normalize_date_range(args.date_range)
    
    txns = db.query(LedgerTransaction).filter(
        LedgerTransaction.customer_id == customer.customer_id,
        LedgerTransaction.merchant_id == merchant_id,
        LedgerTransaction.created_at >= start_dt,
        LedgerTransaction.created_at < end_dt
    ).order_by(LedgerTransaction.created_at.desc()).limit(50).all()
    
    txn_list = []
    for t in txns:
        txn_list.append({
            "date": t.created_at.isoformat(),
            "txn_type": t.txn_type,
            "amount": float(t.amount),
            "items": t.items
        })

    return {
        "status": "success",
        "data": {
            "customer": customer.display_name,
            "transactions": txn_list,
            "period": args.date_range.value
        }
    }

def tool_get_sku_price_trend(db: Session, merchant_id: str, args: SkuPriceTrendQuery) -> dict:
    resolved_sku, is_ambiguous, matches = resolve_sku(db, merchant_id, args.item_name)
    if is_ambiguous:
        return {"status": "ambiguous", "message": f"Multiple items found matching '{args.item_name}'", "candidates": matches}
    if not resolved_sku:
        return {"status": "not_found", "message": f"No items found matching '{args.item_name}'"}
    
    cutoff_dt = datetime.now() - timedelta(days=args.days)
    
    items = db.query(
        InvoiceLineItem.sku,
        InvoiceLineItem.unit_price,
        Invoice.invoice_date,
        Distributor.name
    ).join(Invoice).join(
        Distributor, Invoice.distributor_id == Distributor.distributor_id
    ).filter(
        Invoice.merchant_id == merchant_id,
        InvoiceLineItem.sku == resolved_sku,
        Invoice.invoice_date >= cutoff_dt.date()
    ).order_by(Invoice.invoice_date.asc()).all()
    
    if not items:
        return {"status": "not_found", "message": f"No purchase history for '{args.item_name}' in the last {args.days} days."}
    
    history = []
    distributors = set()
    for i in items:
        history.append({
            "date": i.invoice_date.isoformat(),
            "price": float(i.unit_price),
            "distributor": i.name,
            "sku": i.sku
        })
        distributors.add(i.name)
        
    oldest_price = float(items[0].unit_price)
    latest_price = float(items[-1].unit_price)
    
    if len(distributors) > 1:
        absolute_delta = None
        percentage_change = None
    else:
        absolute_delta = latest_price - oldest_price
        percentage_change = round((absolute_delta / oldest_price * 100), 2) if oldest_price > 0 else 0.0
        
    return {
        "status": "success",
        "data": {
            "item_searched": args.item_name,
            "matched_skus": [resolved_sku],
            "oldest_price": oldest_price,
            "latest_price": latest_price,
            "absolute_delta": absolute_delta,
            "percentage_change": percentage_change,
            "history": history
        }
    }

def tool_get_supplier_payout_summary(db: Session, merchant_id: str, args: SupplierPayoutQuery) -> dict:
    distributor, is_ambiguous, matches = resolve_distributor(db, merchant_id, args.distributor_name)
    if is_ambiguous:
        return {"status": "ambiguous", "message": "Multiple distributors found", "candidates": matches}
    if not distributor:
        return {"status": "not_found", "message": f"Supplier '{args.distributor_name}' not found."}
        
    start_dt, end_dt = normalize_date_range(args.date_range)
    
    result = db.query(
        func.sum(Invoice.total_amount).label("total_spend"),
        func.count(Invoice.invoice_id).label("invoice_count")
    ).filter(
        Invoice.merchant_id == merchant_id,
        Invoice.distributor_id == distributor.distributor_id,
        Invoice.invoice_date >= start_dt.date(),
        Invoice.invoice_date < end_dt.date()
    ).first()
    
    return {
        "status": "success",
        "data": {
            "distributor": distributor.name,
            "total_spend": float(result.total_spend or 0.0),
            "invoice_count": result.invoice_count or 0,
            "period": args.date_range.value
        }
    }

def tool_get_supplier_invoice_details(db: Session, merchant_id: str, args: SupplierInvoiceQuery) -> dict:
    distributor, is_ambiguous, matches = resolve_distributor(db, merchant_id, args.distributor_name)
    if is_ambiguous:
        return {"status": "ambiguous", "message": "Multiple distributors found", "candidates": matches}
    if not distributor:
        return {"status": "not_found", "message": f"Supplier '{args.distributor_name}' not found."}
        
    start_dt, end_dt = normalize_date_range(args.date_range)
    
    invoices = db.query(Invoice).filter(
        Invoice.merchant_id == merchant_id,
        Invoice.distributor_id == distributor.distributor_id,
        Invoice.invoice_date >= start_dt.date(),
        Invoice.invoice_date < end_dt.date()
    ).order_by(Invoice.invoice_date.desc(), Invoice.created_at.desc()).limit(1).all()
    
    if not invoices:
        return {"status": "not_found", "message": f"No invoices found for {distributor.name} in {args.date_range.value}"}
        
    latest = invoices[0]
    line_items = db.query(InvoiceLineItem).filter(
        InvoiceLineItem.invoice_id == latest.invoice_id
    ).all()
    
    items_breakdown = []
    for item in line_items:
        items_breakdown.append({
            "sku": item.sku,
            "quantity": float(item.quantity),
            "unit_price": float(item.unit_price),
            "line_total": float(item.quantity * item.unit_price)
        })
        
    return {
        "status": "success",
        "data": {
            "distributor": distributor.name,
            "invoice_date": latest.invoice_date.isoformat(),
            "total_amount": float(latest.total_amount),
            "items": items_breakdown
        }
    }

def tool_get_daily_operational_balance(db: Session, merchant_id: str, args: DailyBalanceQuery) -> dict:
    target = args.target_date if args.target_date else date.today()
    
    rollup = db.query(SettlementDailyRollup).filter(
        SettlementDailyRollup.merchant_id == merchant_id,
        SettlementDailyRollup.rollup_date == target
    ).first()
    
    if not rollup:
        return {
            "status": "success", 
            "data": {
                "date": target.isoformat(),
                "upi_collection": 0.0,
                "payout_total": 0.0,
                "net_balance": 0.0,
                "message": "No settlement data for this date."
            }
        }
        
    return {
        "status": "success",
        "data": {
            "date": rollup.rollup_date.isoformat(),
            "upi_collection": float(rollup.upi_collection_total),
            "payout_total": float(rollup.payout_total),
            "net_balance": float(rollup.net_balance)
        }
    }

# ---------------------------------------------------------
# 4. Groq / OpenAI Compatible JSON Tool Definitions
# ---------------------------------------------------------

OPERATIONAL_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_due",
            "description": "USE WHEN: The user asks for the total outstanding balance, credit, or 'udhaar' for a specific customer. DO NOT USE WHEN: Asking for overall daily collection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "The name of the customer."
                    }
                },
                "required": ["customer_name"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_transactions",
            "description": "USE WHEN: The user asks for a history or list of recent transactions (payments/credits) for a specific customer. DO NOT USE WHEN: Just asking for the balance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "The name of the customer."
                    },
                    "date_range": {
                        "type": "string",
                        "enum": ["TODAY", "YESTERDAY", "THIS_WEEK", "LAST_WEEK", "LAST_7_DAYS", "THIS_MONTH", "LAST_MONTH"],
                        "description": "The time period to query."
                    }
                },
                "required": ["customer_name"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_sku_price_trend",
            "description": "USE WHEN: The user asks for the rate, price, cost, or trend of a specific product/SKU over time. DO NOT USE WHEN: Asking about overall payout to a distributor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "The product or item name."
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back for price trends. Default is 60."
                    }
                },
                "required": ["item_name"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_supplier_payout_summary",
            "description": "USE WHEN: The user asks about total spending, payments, or payouts made to a specific supplier or distributor. DO NOT USE WHEN: Asking about specific items bought.",
            "parameters": {
                "type": "object",
                "properties": {
                    "distributor_name": {
                        "type": "string",
                        "description": "The name of the supplier or distributor."
                    },
                    "date_range": {
                        "type": "string",
                        "enum": ["TODAY", "YESTERDAY", "THIS_WEEK", "LAST_WEEK", "LAST_7_DAYS", "THIS_MONTH", "LAST_MONTH"],
                        "description": "The time period to query."
                    }
                },
                "required": ["distributor_name"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_supplier_invoice_details",
            "description": "USE WHEN: The user asks for details of the latest invoice or what was bought from a specific supplier. Returns the most recent matching supplier invoice within the requested date range, including its line items. DO NOT USE WHEN: Asking for total aggregate spend only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "distributor_name": {
                        "type": "string",
                        "description": "The name of the supplier or distributor."
                    },
                    "date_range": {
                        "type": "string",
                        "enum": ["TODAY", "YESTERDAY", "THIS_WEEK", "LAST_WEEK", "LAST_7_DAYS", "THIS_MONTH", "LAST_MONTH"],
                        "description": "The time period to query."
                    }
                },
                "required": ["distributor_name"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_operational_balance",
            "description": "USE WHEN: The user asks for the daily shop collection, payout totals, or net balance for a specific day. DO NOT USE WHEN: Asking about a specific customer or supplier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_date": {
                        "type": "string",
                        "description": "The specific date in YYYY-MM-DD format."
                    }
                },
                "required": [],
                "additionalProperties": False
            }
        }
    }
]

# ---------------------------------------------------------
# 5. Tool Dispatcher
# ---------------------------------------------------------

def execute_tool_call(db: Session, merchant_id: str, tool_name: str, arguments: dict) -> dict:
    try:
        if tool_name == "get_customer_due":
            args = CustomerDueQuery(**arguments)
            return tool_get_customer_due(db, merchant_id, args)
            
        elif tool_name == "get_customer_transactions":
            args = CustomerTransactionsQuery(**arguments)
            return tool_get_customer_transactions(db, merchant_id, args)
            
        elif tool_name == "get_sku_price_trend":
            args = SkuPriceTrendQuery(**arguments)
            return tool_get_sku_price_trend(db, merchant_id, args)
            
        elif tool_name == "get_supplier_payout_summary":
            args = SupplierPayoutQuery(**arguments)
            return tool_get_supplier_payout_summary(db, merchant_id, args)
            
        elif tool_name == "get_supplier_invoice_details":
            args = SupplierInvoiceQuery(**arguments)
            return tool_get_supplier_invoice_details(db, merchant_id, args)
            
        elif tool_name == "get_daily_operational_balance":
            args = DailyBalanceQuery(**arguments)
            return tool_get_daily_operational_balance(db, merchant_id, args)
            
        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
            
    except Exception as e:
        db.rollback()
        from core.logging import get_logger
        logger = get_logger("qa_tools")
        logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "code": "INTERNAL_QUERY_ERROR",
            "message": "Unable to retrieve the requested information."
        }
        