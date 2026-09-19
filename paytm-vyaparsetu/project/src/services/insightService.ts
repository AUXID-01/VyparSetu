import { apiClient } from './apiClient';

export const insightService = {
  ask: async (merchantId: string, question: string) => {
    const res = await apiClient.post('/query/ask', { merchant_id: merchantId, question });
    return res.data;
  }
};
