import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { VoiceRecorder } from '../components/features/VoiceRecorder';
import { StatusBadge } from '../components/ui/StatusBadge';
import { ArrowUpRight, ArrowDownRight, Clock, Receipt, ScanLine, Mic } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { useLanguage } from '../contexts/LanguageContext';
import { apiClient } from '../services/apiClient';
import { useAuth } from '../contexts/AuthContext';

export const Dashboard: React.FC = () => {
  const { t } = useLanguage();
  const { auth } = useAuth();
  const [kpis, setKpis] = useState({
    outstandingDues: 0,
    todayCollections: 0,
    pendingSettlements: 0,
    pendingCount: 0,
    transactionsToday: 0
  });
  const [recentTxns, setRecentTxns] = useState<any[]>([]);

  const fetchData = async () => {
    if (!auth.merchantId) return;
    try {
      const today = new Date().toISOString().split('T')[0];
      const summaryRes = await apiClient.get(`/query/daily-summary?merchant_id=${auth.merchantId}&date=${today}`);
      const txnsRes = await apiClient.get(`/query/recent-transactions?merchant_id=${auth.merchantId}&limit=5`);
      
      setKpis({
        outstandingDues: summaryRes.data.total_credits_added - summaryRes.data.total_payments_received,
        todayCollections: summaryRes.data.total_payments_received,
        pendingSettlements: 0, // Pending settlement is challan flow
        pendingCount: 0, 
        transactionsToday: txnsRes.data.length
      });
      setRecentTxns(txnsRes.data);
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // refresh every 10s
    return () => clearInterval(interval);
  }, [auth.merchantId]);

  const formatCurrency = (val: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);


  return (
    <div className="max-w-6xl mx-auto space-y-8">
      
      {/* Quick Attention Area */}
      {kpis.pendingCount > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start sm:items-center justify-between flex-col sm:flex-row gap-4">
          <div className="flex items-center gap-3 text-amber-800">
            <Clock className="w-5 h-5 text-amber-600" />
            <div>
              <span className="font-semibold">{kpis.pendingCount} {t('dashboard.attention')}</span>
              <span className="text-sm ml-2 opacity-80">{t('dashboard.attention.sub')}</span>
            </div>
          </div>
          <Button variant="outline" size="sm" className="bg-white border-amber-200 text-amber-700 hover:bg-amber-100 hover:border-amber-300">
            {t('dashboard.review')}
          </Button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <div className="text-sm font-medium text-ink-500 mb-2">{t('kpi.dues')}</div>
          <div className="flex items-end justify-between">
            <div className="text-2xl font-bold text-ink-800">{formatCurrency(kpis.outstandingDues)}</div>
          </div>
          <Link to="/dashboard/customers" className="text-xs font-semibold text-sage-600 hover:text-sage-800 hover:underline mt-2 inline-block">
            {t('kpi.dues.sub')} &rarr;
          </Link>
        </Card>

        <Card>
          <div className="text-sm font-medium text-ink-500 mb-2">{t('kpi.collections')}</div>
          <div className="flex items-end justify-between">
            <div className="text-2xl font-bold text-ink-800">{formatCurrency(kpis.todayCollections)}</div>
          </div>
          <Link to="/dashboard/transactions" className="text-xs font-semibold text-sage-600 hover:text-sage-800 hover:underline mt-2 inline-block">
            {t('kpi.collections.sub')}: {kpis.transactionsToday} &rarr;
          </Link>
        </Card>

        <Card>
          <div className="text-sm font-medium text-ink-500 mb-2">{t('kpi.pending')}</div>
          <div className="text-2xl font-bold text-ink-800">{formatCurrency(kpis.pendingSettlements)}</div>
          <div className="text-xs text-ink-400 mt-2">{kpis.pendingCount} {t('kpi.pending.sub')}</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Col: Activity */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Quick Actions */}
          <div>
            <h3 className="text-lg font-semibold text-ink-800 mb-4">{t('quick.title')}</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <a href="#assistant" className="flex flex-col items-center justify-center p-4 rounded-2xl bg-white border border-cream-200 shadow-soft hover:shadow-card hover:-translate-y-0.5 transition-all group">
                <div className="w-10 h-10 rounded-full bg-sage-50 text-sage-600 flex items-center justify-center mb-3 group-hover:bg-sage-100 transition-colors">
                  <Mic className="w-5 h-5" />
                </div>
                <span className="text-sm font-medium text-ink-700">{t('quick.credit')}</span>
              </a>
              <Link to="/dashboard/challans" className="flex flex-col items-center justify-center p-4 rounded-2xl bg-white border border-cream-200 shadow-soft hover:shadow-card hover:-translate-y-0.5 transition-all group">
                <div className="w-10 h-10 rounded-full bg-teal-50 text-teal-600 flex items-center justify-center mb-3 group-hover:bg-teal-100 transition-colors">
                  <ScanLine className="w-5 h-5" />
                </div>
                <span className="text-sm font-medium text-ink-700">{t('quick.challan')}</span>
              </Link>
              <Link to="/dashboard/transactions" className="flex flex-col items-center justify-center p-4 rounded-2xl bg-white border border-cream-200 shadow-soft hover:shadow-card hover:-translate-y-0.5 transition-all group">
                <div className="w-10 h-10 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3 group-hover:bg-indigo-100 transition-colors">
                  <Receipt className="w-5 h-5" />
                </div>
                <span className="text-sm font-medium text-ink-700">{t('quick.payment')}</span>
              </Link>
              <Link to="/dashboard/customers" className="flex flex-col items-center justify-center p-4 rounded-2xl bg-white border border-cream-200 shadow-soft hover:shadow-card hover:-translate-y-0.5 transition-all group">
                <div className="w-10 h-10 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mb-3 group-hover:bg-amber-100 transition-colors">
                  <Clock className="w-5 h-5" />
                </div>
                <span className="text-sm font-medium text-ink-700">{t('quick.dues')}</span>
              </Link>
            </div>
          </div>

          {/* Live Activity */}
          <Card className="flex-1">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-ink-800">{t('activity.title')}</h3>
              <Link to="/dashboard/transactions" className="text-xs font-semibold text-sage-600 hover:text-sage-800 hover:underline">
                View All Transactions &rarr;
              </Link>
            </div>
            {recentTxns.length === 0 ? (
              <div className="text-center py-8 text-ink-400 text-sm">{t('activity.empty')}</div>
            ) : (
              <div className="space-y-4">
                {recentTxns.map(txn => {
                  const isCredit = txn.txn_type === 'CREDIT_ADDED';
                  return (
                    <div key={txn.txn_id} className="flex items-center justify-between p-4 rounded-xl hover:bg-cream-50 transition-colors border border-transparent hover:border-cream-200">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isCredit ? 'bg-danger/10 text-danger' : 'bg-positive/10 text-positive'}`}>
                          {isCredit ? <ArrowUpRight className="w-5 h-5" /> : <ArrowDownRight className="w-5 h-5" />}
                        </div>
                        <div>
                          <div className="font-semibold text-ink-800">{txn.customer_name || 'Unknown'}</div>
                          <div className="text-sm text-ink-500">{isCredit ? t('activity.credit') : t('activity.payment')} &bull; {new Date(txn.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                        </div>
                      </div>
                      <div className="text-right flex flex-col items-end gap-1.5">
                        <div className={`font-bold ${isCredit ? 'text-danger' : 'text-positive'}`}>
                          {isCredit ? '+' : '-'}{formatCurrency(txn.amount)}
                        </div>
                        <StatusBadge status={txn.sync_status || 'RECORDED'} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>

        {/* Right Col: Voice Assistant */}
        <div className="flex flex-col gap-6" id="assistant">
          <div className="sticky top-6">
            <h3 className="text-lg font-semibold text-ink-800 mb-4 px-2">{t('assistant.title')}</h3>
            <VoiceRecorder />
          </div>
        </div>

      </div>
    </div>
  );
};
