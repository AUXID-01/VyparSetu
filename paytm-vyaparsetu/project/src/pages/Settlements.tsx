import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { challanService } from '../services/challanService';
import { FileText, CheckCircle2, AlertTriangle, ArrowRight, Loader2, ArrowUpRight } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { toast } from 'react-hot-toast';

export const Settlements: React.FC = () => {
  const { t } = useLanguage();
  const [settlements, setSettlements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'SUCCESSFUL' | 'PENDING'>('ALL');
  const [retryingIds, setRetryingIds] = useState<Set<string>>(new Set());
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchSettlements = async () => {
    try {
      setLoading(true);
      const data = await challanService.getSettlements();
      setSettlements(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to fetch settlements');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettlements();
  }, []);

  const handleRetry = async (invoiceId: string) => {
    setRetryingIds(prev => new Set(prev).add(invoiceId));
    setErrorMsg(null);
    try {
      const result = await challanService.settle(invoiceId);
      if (result.payout_status === 'FAILED') {
        toast.error(`Payout Queued / Failed: ${result.failure_reason || 'Unknown error'}`);
      } else {
        toast.success(`Payout Disbursed (UTR: ${result.payout_reference || 'Pending'})`);
      }
      await fetchSettlements(); // Refresh the list
    } catch (err: any) {
      setErrorMsg(err.message || 'Retry failed due to insufficient balance.');
      toast.error('Retry failed due to insufficient balance.');
    } finally {
      setRetryingIds(prev => {
        const next = new Set(prev);
        next.delete(invoiceId);
        return next;
      });
    }
  };

  const formatCurrency = (val: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(val);
  const formatDate = (dateStr: string) => new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });

  const filteredSettlements = settlements.filter(s => {
    if (filter === 'SUCCESSFUL') return s.is_paid;
    if (filter === 'PENDING') return !s.is_paid;
    return true;
  });

  return (
    <div className="max-w-5xl mx-auto space-y-8 h-full overflow-y-auto pb-20">
      <div>
        <h1 className="text-2xl font-semibold text-ink-800">Settlements</h1>
        <p className="text-ink-500 mt-1">Review your payout history and pending distributor settlements.</p>
      </div>

      <div className="flex gap-2 bg-cream-50 p-1 rounded-xl w-fit">
        <button
          onClick={() => setFilter('ALL')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filter === 'ALL' ? 'bg-white shadow-sm text-ink-800' : 'text-ink-500 hover:text-ink-700'}`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('SUCCESSFUL')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filter === 'SUCCESSFUL' ? 'bg-white shadow-sm text-ink-800' : 'text-ink-500 hover:text-ink-700'}`}
        >
          Successful
        </button>
        <button
          onClick={() => setFilter('PENDING')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filter === 'PENDING' ? 'bg-white shadow-sm text-ink-800' : 'text-ink-500 hover:text-ink-700'}`}
        >
          Pending
        </button>
      </div>

      {errorMsg && (
        <div className="bg-danger/10 text-danger px-4 py-3 rounded-xl text-sm font-medium border border-danger/20 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {errorMsg}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20 text-ink-400">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
      ) : filteredSettlements.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-16 text-center border-dashed border-2">
          <div className="w-16 h-16 bg-cream-50 rounded-2xl flex items-center justify-center mb-4">
            <FileText className="w-8 h-8 text-ink-300" />
          </div>
          <h3 className="text-lg font-medium text-ink-800 mb-1">No settlements found</h3>
          <p className="text-ink-500">There are no {filter === 'ALL' ? '' : filter.toLowerCase()} settlements in your history.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredSettlements.map((settlement) => (
            <Card key={settlement.invoice_id} className="flex flex-col md:flex-row items-start md:items-center justify-between p-5 gap-4">
              <div className="flex items-start gap-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${settlement.is_paid ? 'bg-positive/10 text-positive' : 'bg-amber-100 text-amber-600'}`}>
                  {settlement.is_paid ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-ink-800">{settlement.distributor_name}</h3>
                    {settlement.challan_type && (
                      <span className="bg-cream-100 text-ink-500 text-[10px] font-semibold px-1.5 py-0.5 rounded">
                        {settlement.challan_type.replace(/_/g, ' ')}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-ink-500">
                    {settlement.is_paid ? `Paid on ${formatDate(settlement.paid_at)}` : `Extracted on ${formatDate(settlement.created_at)}`}
                  </p>
                  {settlement.payout_reference && (
                    <p className="text-xs text-ink-400 mt-1 font-mono">Ref: {settlement.payout_reference}</p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-6 w-full md:w-auto mt-4 md:mt-0 justify-between md:justify-end">
                <div className="text-left md:text-right">
                  <div className="text-sm text-ink-500 mb-0.5">Amount</div>
                  <div className="text-lg font-bold text-ink-800">{formatCurrency(settlement.total_amount)}</div>
                </div>

                {!settlement.is_paid && (
                  <Button 
                    variant="primary" 
                    className="min-w-[140px]"
                    disabled={retryingIds.has(settlement.invoice_id)}
                    onClick={() => handleRetry(settlement.invoice_id)}
                  >
                    {retryingIds.has(settlement.invoice_id) ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Retrying</>
                    ) : (
                      <>Retry Payout <ArrowUpRight className="w-4 h-4 ml-2" /></>
                    )}
                  </Button>
                )}
                
                {settlement.is_paid && (
                  <div className="min-w-[140px] text-right text-sm font-medium text-positive flex items-center justify-end gap-1">
                    Settled Successfully
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
