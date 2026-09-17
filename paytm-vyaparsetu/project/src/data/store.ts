import { Customer, UILedgerTransaction, Distributor, UIInvoice, Alert, InvoiceLineItem } from '../types';

export const INITIAL_CUSTOMERS: Customer[] = [
  {
    customer_id: 'cus_7f3d21',
    merchant_id: 'mer_a1b2c3',
    display_name: 'Suresh Kumar',
    canonical_key: 'suresh kumar',
    phone: '+919876543211',
    created_at: '2026-09-02T10:00:00Z'
  },
  {
    customer_id: 'cus_8a9b0c',
    merchant_id: 'mer_a1b2c3',
    display_name: 'Anita Traders',
    canonical_key: 'anita traders',
    phone: '+919876543212',
    created_at: '2026-09-03T11:00:00Z'
  }
];

export const INITIAL_TRANSACTIONS: UILedgerTransaction[] = [
  {
    txn_id: 'txn_1a2b3c',
    merchant_id: 'mer_a1b2c3',
    customer_id: 'cus_7f3d21',
    amount: 850,
    txn_type: 'CREDIT_ADDED',
    items: ['Rice 5kg', 'Dal 2kg'],
    source: 'VOICE',
    extraction_confidence: 0.95,
    created_at: '2026-09-10T14:30:00Z',
    sync_status: 'SYNCED'
  },
  {
    txn_id: 'txn_2b3c4d',
    merchant_id: 'mer_a1b2c3',
    customer_id: 'cus_7f3d21',
    amount: 500,
    txn_type: 'CREDIT_PAID',
    items: [],
    source: 'MANUAL',
    extraction_confidence: null,
    created_at: '2026-09-12T09:15:00Z',
    sync_status: 'SYNCED'
  }
];

export const INITIAL_DISTRIBUTORS: Distributor[] = [
  {
    distributor_id: 'dis_1x2y3z',
    merchant_id: 'mer_a1b2c3',
    name: 'Amul Distributor',
    upi_id: 'amul.dist@paytm',
    canonical_key: 'amul distributor',
    created_at: '2026-09-01T10:00:00Z'
  }
];

export const INITIAL_INVOICES: UIInvoice[] = [];
export const INITIAL_INVOICE_LINES: InvoiceLineItem[] = [];

export const INITIAL_ALERTS: Alert[] = [];
