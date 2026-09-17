import { db, sleep } from './database';
import { CURRENT_MERCHANT } from '../data/merchants';
import { UIInvoice, InvoiceLineItem } from '../types';

export const challanService = {
  // Simulates POST /v1/challan/extract
  extract: async (file: File) => {
    await sleep(1500); // Simulate OCR extraction
    return {
      distributor_name_guess: 'Amul Distributor - Sector 4',
      line_items: [
        { sku: 'Dahi 200g pouch', quantity: 50, unit_price: 30.00 },
        { sku: 'Amul Butter 100g', quantity: 20, unit_price: 48.00 }
      ],
      total_amount: 2460.00,
      extraction_confidence: 0.88
    };
  },

  // Simulates POST /v1/challan/confirm
  confirm: async (extractedData: any): Promise<{ invoice: UIInvoice, rate_alerts: any[], remaining_after: number }> => {
    // 1. Resolve distributor
    const canonicalKey = extractedData.distributor_name_guess.toLowerCase().trim();
    let distributor = db.distributors.find(d => d.canonical_key === canonicalKey);
    
    if (!distributor) {
      distributor = {
        distributor_id: `dis_${Math.random().toString(16).slice(2, 8)}`,
        merchant_id: CURRENT_MERCHANT.merchant_id,
        name: extractedData.distributor_name_guess,
        upi_id: null,
        canonical_key: canonicalKey,
        created_at: new Date().toISOString()
      };
      db.distributors.push(distributor);
    }

    // 2. Create Invoice
    const invoiceId = `inv_${Math.random().toString(16).slice(2, 8)}`;
    const invoice: UIInvoice = {
      invoice_id: invoiceId,
      merchant_id: CURRENT_MERCHANT.merchant_id,
      distributor_id: distributor.distributor_id,
      invoice_date: new Date().toISOString(),
      total_amount: extractedData.total_amount,
      is_paid: false,
      paid_at: null,
      payout_reference: null,
      created_at: new Date().toISOString(),
      sync_status: 'PENDING'
    };
    
    db.invoices.unshift(invoice);

    // 3. Create Line Items
    extractedData.line_items.forEach((item: any) => {
      db.invoiceLines.push({
        line_item_id: `lin_${Math.random().toString(16).slice(2, 8)}`,
        invoice_id: invoiceId,
        distributor_id: distributor.distributor_id,
        sku: item.sku,
        quantity: item.quantity,
        unit_price: item.unit_price
      });
    });

    // 4. INSTANT Rate Check (Fast Path)
    // Simulating finding a previous price for Dahi
    const rate_alerts = [];
    if (extractedData.line_items.find((i: any) => i.sku === 'Dahi 200g pouch' && i.unit_price > 28.50)) {
      rate_alerts.push({
        sku: 'Dahi 200g pouch',
        previous_price: 28.50,
        current_price: 30.00,
        delta: 1.50
      });
    }

    db.notify();

    // 5. Trigger Background Sync
    challanService.simulateBackgroundSync(invoiceId);

    return {
      invoice,
      rate_alerts,
      remaining_after: 5200 - extractedData.total_amount // Mock available balance
    };
  },

  simulateBackgroundSync: async (invoiceId: string) => {
    await sleep(4000);
    const inv = db.invoices.find(i => i.invoice_id === invoiceId);
    if (inv) {
      inv.sync_status = 'SYNCED';
      db.notify();
    }
  },

  // Simulates POST /v1/challan/settle
  settle: async (invoiceId: string) => {
    await sleep(800); // Simulate API call to initiate
    // n8n Webhook will process it in background. We'll simulate the webhook callback here.
    setTimeout(() => {
      const inv = db.invoices.find(i => i.invoice_id === invoiceId);
      if (inv) {
        inv.is_paid = true;
        inv.paid_at = new Date().toISOString();
        inv.payout_reference = 'PAYTM-REF-123';
        db.notify();
      }
    }, 3000);

    return { payout_status: 'INITIATED' };
  }
};
