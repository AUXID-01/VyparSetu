const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));
export const insightService = {
  ask: async (question: string) => {
    // If it's a simple, pre-cached question, return fast
    if (question.toLowerCase().includes('how much') || question.toLowerCase().includes('total')) {
      await sleep(300);
      return {
        answer: 'Based on your records, your total outstanding dues are currently ₹1,24,800. Suresh Kumar owes the most (₹4,820).',
        source: 'CACHE'
      };
    }

    // Otherwise, simulate a deep Cognee analysis query
    await sleep(4000);
    return {
      answer: 'Over the last two months, Amul pricing has increased by 7.8% on average. Three specific SKUs (Dahi, Butter, and Cheese) account for most of this increase. You might want to consider stocking alternative brands for these high-velocity items.',
      source: 'LIVE'
    };
  }
};
