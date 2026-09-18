import React, { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Button } from '../components/ui/Button';
import { Search, RefreshCw, Mic, CheckCircle2, ArrowDownRight, ArrowUpRight } from 'lucide-react';
import { apiClient } from '../services/apiClient';
import { useAuth } from '../contexts/AuthContext';

export interface TxnData {
  txn_id: string;
  customer_id: string;
  customer_name: string;
  amount: number;
  txn_type: string;
  source?: string;
  items?: string[];
  extraction_confidence?: number;
  created_at: string;
}

export const Transactions: React.FC = () => {
  const { auth } = useAuth();
  const [txns, setTxns] = useState<TxnData[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'ALL' | 'CREDIT_ADDED' | 'CREDIT_PAID'>('ALL');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchTxns = async () => {
    if (!auth.merchantId) return;
    try {
      setRefreshing(true);
      const res = await apiClient.get(`/query/recent-transactions?merchant_id=${auth.merchantId}&limit=100`);
      if (res.data) {
        setTxns(res.data);
      }
    } catch (err) {
      console.error("Failed to fetch transactions", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTxns();
  }, [auth.merchantId]);

  const filteredTxns = txns.filter(t => {
    const matchesSearch = 
      t.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.txn_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'ALL' || t.txn_type === filterType;
    return matchesSearch && matchesType;
  });

  const totalCredits = txns
    .filter(t => t.txn_type === 'CREDIT_ADDED')
    .reduce((sum, t) => sum + t.amount, 0);

  const totalPayments = txns
    .filter(t => t.txn_type === 'CREDIT_PAID')
    .reduce((sum, t) => sum + t.amount, 0);

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink-800">Transaction History</h1>
          <p className="text-sm text-ink-500 mt-1">Audit log of all voice recorded credits, payments, and system entries.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchTxns}
            disabled={refreshing}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="text-xs font-semibold text-ink-400 uppercase tracking-wider mb-2">Total Transactions</div>
          <div className="text-2xl font-bold text-ink-800">{txns.length}</div>
          <div className="text-xs text-ink-400 mt-1">Recorded via Voice & API</div>
        </Card>

        <Card>
          <div className="text-xs font-semibold text-ink-400 uppercase tracking-wider mb-2">Total Credits Added</div>
          <div className="text-2xl font-bold text-danger">{formatCurrency(totalCredits)}</div>
          <div className="text-xs text-ink-400 mt-1">Logged to customer accounts</div>
        </Card>

        <Card>
          <div className="text-xs font-semibold text-ink-400 uppercase tracking-wider mb-2">Total Payments Received</div>
          <div className="text-2xl font-bold text-positive">{formatCurrency(totalPayments)}</div>
          <div className="text-xs text-ink-400 mt-1">Collected settlements</div>
        </Card>
      </div>

      {/* Search & Tabs */}
      <div className="bg-white p-4 rounded-2xl border border-cream-200 shadow-soft flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative flex-1 w-full sm:max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
          <input 
            type="text"
            placeholder="Search by customer name or Txn ID..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-cream-50 border border-cream-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sage-500/20 focus:border-sage-300"
          />
        </div>

        <div className="flex items-center gap-1 bg-cream-100 p-1 rounded-xl text-xs font-semibold text-ink-600">
          <button
            onClick={() => setFilterType('ALL')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${filterType === 'ALL' ? 'bg-white text-ink-800 shadow-xs' : 'hover:text-ink-900'}`}
          >
            All
          </button>
          <button
            onClick={() => setFilterType('CREDIT_ADDED')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${filterType === 'CREDIT_ADDED' ? 'bg-white text-ink-800 shadow-xs' : 'hover:text-ink-900'}`}
          >
            Credits (+ Udhaar)
          </button>
          <button
            onClick={() => setFilterType('CREDIT_PAID')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${filterType === 'CREDIT_PAID' ? 'bg-white text-ink-800 shadow-xs' : 'hover:text-ink-900'}`}
          >
            Payments (- Paid)
          </button>
        </div>
      </div>

      {/* Transactions Table */}
      <Card className="overflow-hidden p-0">
        {loading ? (
          <div className="p-12 text-center text-ink-400">Loading transactions...</div>
        ) : filteredTxns.length === 0 ? (
          <div className="p-12 text-center text-ink-400">
            {searchTerm || filterType !== 'ALL' ? 'No transactions matching your filter' : 'No transactions recorded yet. Tap the microphone on the dashboard to record your first credit.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-ink-700 border-collapse">
              <thead>
                <tr className="bg-cream-50 border-b border-cream-200 text-xs text-ink-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-6">Transaction ID</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Type & Source</th>
                  <th className="py-3 px-4">Items / Note</th>
                  <th className="py-3 px-4 text-center">Confidence</th>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-6 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cream-100">
                {filteredTxns.map((t) => {
                  const isCredit = t.txn_type === 'CREDIT_ADDED';
                  return (
                    <tr key={t.txn_id} className="hover:bg-cream-50/50 transition-colors">
                      <td className="py-4 px-6 font-mono text-xs text-ink-500 font-medium">
                        {t.txn_id}
                      </td>
                      <td className="py-4 px-4 font-semibold text-ink-800">
                        {t.customer_name}
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-1.5">
                          <span className={`w-2 h-2 rounded-full ${isCredit ? 'bg-danger' : 'bg-positive'}`} />
                          <span className="text-xs font-medium">
                            {isCredit ? 'Credit Added' : 'Payment Received'}
                          </span>
                          {t.source === 'VOICE' && (
                            <span className="bg-sage-100 text-sage-800 text-[10px] font-semibold px-1.5 py-0.5 rounded flex items-center gap-1">
                              <Mic className="w-3 h-3" /> VOICE
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        {t.items && t.items.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {t.items.map((item, idx) => (
                              <span key={idx} className="bg-amber-50 text-amber-800 border border-amber-200 text-[11px] px-2 py-0.5 rounded-md">
                                🛒 {item}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-ink-300 text-xs italic">-</span>
                        )}
                      </td>
                      <td className="py-4 px-4 text-center">
                        <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-semibold px-2 py-0.5 rounded-md">
                          {Math.round((t.extraction_confidence || 0.92) * 100)}%
                        </span>
                      </td>
                      <td className="py-4 px-4 text-xs text-ink-400">
                        {new Date(t.created_at).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' })}
                      </td>
                      <td className={`py-4 px-6 text-right font-bold text-base ${isCredit ? 'text-danger' : 'text-positive'}`}>
                        {isCredit ? '+' : '-'}{formatCurrency(t.amount)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};
