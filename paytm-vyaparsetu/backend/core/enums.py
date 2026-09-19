from enum import Enum

class StrEnum(str, Enum):
    """Base string enum for python compatibility."""
    def __str__(self) -> str:
        return str(self.value)

class TxnType(StrEnum):
    CREDIT_ADDED = "CREDIT_ADDED"
    CREDIT_PAID = "CREDIT_PAID"

class LedgerSource(StrEnum):
    VOICE = "VOICE"
    MANUAL = "MANUAL"

class OutboxStatus(StrEnum):
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"

class OutboxEventType(StrEnum):
    CREDIT_ADDED = "CREDIT_ADDED"
    INVOICE_CREATED = "INVOICE_CREATED"
    SETTLEMENT_ROLLUP = "SETTLEMENT_ROLLUP"
    CUSTOMER_PAYMENT_SETTLED = "CUSTOMER_PAYMENT_SETTLED"

class InsightType(StrEnum):
    RATE_TREND = "RATE_TREND"
    QA_ANSWER = "QA_ANSWER"
    SUPPLIER_SUMMARY = "SUPPLIER_SUMMARY"

class AlertType(StrEnum):
    RATE_SPIKE = "RATE_SPIKE"
    LOW_BALANCE = "LOW_BALANCE"

class PayoutStatus(StrEnum):
    INITIATED = "INITIATED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

class QuerySource(StrEnum):
    CACHE = "CACHE"
    LIVE = "LIVE"
