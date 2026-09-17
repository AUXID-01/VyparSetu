export type Merchant = {
  merchant_id: string;
  shop_name: string;
  owner_name: string;
  phone: string;
  cognee_dataset: string;
  created_at: string;
};

export type Customer = {
  customer_id: string;
  merchant_id: string;
  display_name: string;
  canonical_key: string;
  phone: string | null;
  created_at: string;
};

export type Distributor = {
  distributor_id: string;
  merchant_id: string;
  name: string;
  upi_id: string | null;
  canonical_key: string;
  created_at: string;
};

export type LedgerTransaction = {
  txn_id: string;
  merchant_id: string;
  customer_id: string;
  amount: number;
  txn_type: 'CREDIT_ADDED' | 'CREDIT_PAID';
  items: string[];
  source: 'VOICE' | 'MANUAL';
  extraction_confidence: number | null;
  created_at: string;
};

export type Invoice = {
  invoice_id: string;
  merchant_id: string;
  distributor_id: string;
  invoice_date: string;
  total_amount: number;
  is_paid: boolean;
  paid_at: string | null;
  payout_reference: string | null;
  created_at: string;
};

export type InvoiceLineItem = {
  line_item_id: string;
  invoice_id: string;
  distributor_id: string;
  sku: string;
  quantity: number;
  unit_price: number;
};

export type OutboxStatus = 'PENDING' | 'SYNCED' | 'FAILED';

export type OutboxEvent = {
  event_id: string;
  merchant_id: string;
  event_type: 'CREDIT_ADDED' | 'INVOICE_CREATED' | 'SETTLEMENT_ROLLUP';
  payload: any;
  status: OutboxStatus;
  attempt_count: number;
  created_at: string;
  synced_at: string | null;
};

export type AlertType = 'RATE_SPIKE' | 'LOW_BALANCE';

export type Alert = {
  alert_id: string;
  merchant_id: string;
  alert_type: AlertType;
  details: any;
  is_read: boolean;
  created_at: string;
};

// UI Specific Types
export type UILedgerTransaction = LedgerTransaction & {
  sync_status: OutboxStatus;
};

export type UIInvoice = Invoice & {
  sync_status: OutboxStatus;
};
