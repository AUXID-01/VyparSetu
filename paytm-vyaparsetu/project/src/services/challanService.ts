import { apiClient } from './apiClient';
import { UIInvoice, InvoiceLineItem } from '../types';

export const challanService = {
  // POST /api/v1/challan/extract
  extract: async (file: File) => {
    const formData = new FormData();
    const merchantId = localStorage.getItem('merchantId');
    if (!merchantId) throw new Error('Not authenticated');
    
    formData.append('merchant_id', merchantId);
    formData.append('image', file);
    
    console.log(`🔍 [Challan Service] Extracting challan image (size: ${file.size} bytes)`);
    const res = await apiClient.post('/challan/extract', formData, true);
    console.log(`🧮 [Challan Service] Extraction pipeline result:`, res.data);
    return res.data;
  },

  // POST /api/v1/challan/confirm
  confirm: async (extractedData: any): Promise<{ invoice: UIInvoice, rate_alerts: any[], settlement: { balance_available: number, remaining_after: number } }> => {
    const merchantId = localStorage.getItem('merchantId');
    if (!merchantId) throw new Error('Not authenticated');

    const payload = {
      merchant_id: merchantId,
      data: extractedData
    };

    console.log(`🔍 [Challan Service] Confirming extracted data:`, payload);
    const res = await apiClient.post('/challan/confirm', payload);
    const data = res.data;
    console.log(`📥 [Challan Service] Confirmed and received settlement details:`, data);

    // Backend returns invoice_id, rate_alerts, settlement
    const invoice: UIInvoice = {
      invoice_id: data.invoice_id,
      merchant_id: merchantId,
      distributor_id: 'dis_unknown', // Backend handles distributor
      invoice_date: new Date().toISOString(),
      total_amount: data.settlement.invoice_total,
      is_paid: false,
      paid_at: null,
      payout_reference: null,
      created_at: new Date().toISOString(),
      sync_status: 'PENDING'
    };

    return {
      invoice,
      rate_alerts: data.rate_alerts,
      settlement: data.settlement
    };
  },

  // POST /api/v1/challan/settle
  settle: async (invoiceId: string) => {
    console.log(`💸 [Challan Service] Settling invoice: ${invoiceId}`);
    const res = await apiClient.post('/challan/settle', { invoice_id: invoiceId });
    console.log(`📥 [Challan Service] Settle result:`, res.data);
    return { payout_status: res.data.payout_status };
  },

  // GET /api/v1/query/settlements
  getSettlements: async () => {
    const merchantId = localStorage.getItem('merchantId');
    if (!merchantId) throw new Error('Not authenticated');

    const res = await apiClient.get(`/query/settlements?merchant_id=${merchantId}`);
    return res.data;
  }
};
