import { 
  Customer, UILedgerTransaction, Distributor, UIInvoice, 
  InvoiceLineItem, Alert 
} from '../types';
import { 
  INITIAL_CUSTOMERS, INITIAL_TRANSACTIONS, INITIAL_DISTRIBUTORS, 
  INITIAL_INVOICES, INITIAL_INVOICE_LINES, INITIAL_ALERTS 
} from '../data/store';

// In-memory database singleton
class Database {
  customers: Customer[] = [...INITIAL_CUSTOMERS];
  transactions: UILedgerTransaction[] = [...INITIAL_TRANSACTIONS];
  distributors: Distributor[] = [...INITIAL_DISTRIBUTORS];
  invoices: UIInvoice[] = [...INITIAL_INVOICES];
  invoiceLines: InvoiceLineItem[] = [...INITIAL_INVOICE_LINES];
  alerts: Alert[] = [...INITIAL_ALERTS];

  // Listeners for UI updates
  private listeners: (() => void)[] = [];

  subscribe(listener: () => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notify() {
    this.listeners.forEach(l => l());
  }
}

export const db = new Database();

export const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
