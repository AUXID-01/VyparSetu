import { db } from './database';

export const dashboardService = {
  getKPIs: () => {
    const totalDues = db.transactions
      .filter(t => t.txn_type === 'CREDIT_ADDED')
      .reduce((sum, t) => sum + t.amount, 0)
      -
      db.transactions
      .filter(t => t.txn_type === 'CREDIT_PAID')
      .reduce((sum, t) => sum + t.amount, 0);

    const todayCollections = db.transactions
      .filter(t => t.txn_type === 'CREDIT_PAID' && new Date(t.created_at).toDateString() === new Date().toDateString())
      .reduce((sum, t) => sum + t.amount, 0);

    const txnTodayCount = db.transactions
      .filter(t => new Date(t.created_at).toDateString() === new Date().toDateString())
      .length;

    const pendingSettlements = db.invoices
      .filter(i => !i.is_paid)
      .reduce((sum, i) => sum + i.total_amount, 0);

    return {
      outstandingDues: totalDues > 0 ? totalDues : 124800, // Using mock value if db empty
      outstandingTrend: '+8.4%',
      todayCollections: todayCollections > 0 ? todayCollections : 38450,
      collectionsTrend: '+12.2%',
      transactionsToday: txnTodayCount > 0 ? txnTodayCount : 128,
      pendingSettlements: pendingSettlements > 0 ? pendingSettlements : 42600,
      pendingCount: db.invoices.filter(i => !i.is_paid).length || 3
    };
  }
};
