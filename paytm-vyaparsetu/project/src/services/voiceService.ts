import { apiClient } from './apiClient';
import { UILedgerTransaction } from '../types';

export const voiceService = {
  // Post audio to Sarvam STT
  transcribe: async (audioBlob: Blob): Promise<{ transcript: string }> => {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'recording.webm');
    
    // We pass isFormData = true to apiClient.post
    const res = await apiClient.post('/voice/transcribe', formData, true);
    return { transcript: res.data.transcript };
  },

  // Log credit directly (backend extracts and inserts into ledger)
  logCredit: async (merchantId: string, transcript: string): Promise<UILedgerTransaction> => {
    const res = await apiClient.post('/voice/log-credit', {
      merchant_id: merchantId,
      raw_transcript: transcript
    });

    // The backend responds with txn_id, customer_id, new_balance, confirmation_audio_text, confirmation_audio_base64
    // We synthesize a UILedgerTransaction to add to the UI state immediately if needed, 
    // though the UI typically refetches recent-transactions anyway.
    return {
      txn_id: res.data.txn_id,
      merchant_id: merchantId,
      customer_id: res.data.customer_id,
      amount: res.data.amount || 0, // Fallback if backend doesn't return exact amount
      txn_type: 'CREDIT_ADDED',
      items: [],
      source: 'VOICE',
      extraction_confidence: 0.99,
      created_at: new Date().toISOString(),
      sync_status: 'PENDING',
      confirmation_audio_text: res.data.confirmation_audio_text,
      confirmation_audio_base64: res.data.confirmation_audio_base64
    };
  }
};
