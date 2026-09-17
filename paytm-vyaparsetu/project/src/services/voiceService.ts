import { db, sleep } from './database';
import { CURRENT_MERCHANT } from '../data/merchants';
import { UILedgerTransaction } from '../types';

export const voiceService = {
  // Simulates Sarvam STT
  transcribe: async (): Promise<{ transcript: string }> => {
    await sleep(600); // Network delay
    return { transcript: 'Suresh ke khate mein do sau chalis rupaye likh lo dahi aur tel ke.' };
  },

  // Simulates NLP extraction
  extract: async (transcript: string) => {
    await sleep(400); // Simulate processing
    return {
      customer_name: 'Suresh',
      amount: 240,
      items: ['Dahi', 'Tel'],
      type: 'CREDIT_ADDED'
    };
  },

  // Simulates POST /v1/voice/log-credit (FAST PATH)
  logCredit: async (extractedData: any): Promise<UILedgerTransaction> => {
    // 1. Resolve customer
    const canonicalKey = extractedData.customer_name.toLowerCase().trim();
    let customer = db.customers.find(c => c.canonical_key === canonicalKey);
    
    if (!customer) {
      customer = {
        customer_id: `cus_${Math.random().toString(16).slice(2, 8)}`,
        merchant_id: CURRENT_MERCHANT.merchant_id,
        display_name: extractedData.customer_name,
        canonical_key: canonicalKey,
        phone: null,
        created_at: new Date().toISOString()
      };
      db.customers.push(customer);
    }

    // 2. Create Ledger Transaction instantly
    const txn: UILedgerTransaction = {
      txn_id: `txn_${Math.random().toString(16).slice(2, 8)}`,
      merchant_id: CURRENT_MERCHANT.merchant_id,
      customer_id: customer.customer_id,
      amount: extractedData.amount,
      txn_type: extractedData.type,
      items: extractedData.items,
      source: 'VOICE',
      extraction_confidence: 0.91,
      created_at: new Date().toISOString(),
      sync_status: 'PENDING'
    };
    
    db.transactions.unshift(txn); // Prepend for UI
    db.notify();

    // 3. Trigger Background Sync (BACKGROUND PATH - Do not await)
    voiceService.simulateBackgroundSync(txn.txn_id);
    voiceService.simulatePaymentLinkDispatch(customer.display_name, extractedData.amount);

    return txn;
  },

  // Simulates n8n outbox poller picking up the pending row
  simulateBackgroundSync: async (txnId: string) => {
    // Wait for 3-5 seconds to simulate Cognee indexing delay
    await sleep(3000 + Math.random() * 2000);
    
    const txn = db.transactions.find(t => t.txn_id === txnId);
    if (txn) {
      txn.sync_status = 'SYNCED';
      db.notify();
    }
  },

  simulatePaymentLinkDispatch: async (customerName: string, amount: number) => {
     // Simulate sending WhatsApp message via n8n
     await sleep(2000);
     // We can hook this into a notification service later
     console.log(`[Automation] Payment link sent to ${customerName} for ₹${amount}`);
  }
};
