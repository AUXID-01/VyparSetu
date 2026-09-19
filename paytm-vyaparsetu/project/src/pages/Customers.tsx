import React, { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Button } from '../components/ui/Button';
import { Search, UserCheck, ArrowUpRight, DollarSign, RefreshCw, ShoppingBag, Plus, Link as LinkIcon, Loader2 } from 'lucide-react';
import { apiClient } from '../services/apiClient';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-hot-toast';

export interface CustomerData {
  customer_id: string;
  display_name: string;
  phone: string;
  total_due: number;
  total_credits: number;
  total_paid: number;
  last_active: string;
  items_summary: string[];
}

export const Customers: React.FC = () => {
  const { auth } = useAuth();
  const [customers, setCustomers] = useState<CustomerData[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [paymentAmount, setPaymentAmount] = useState('');
  const [recordingPayment, setRecordingPayment] = useState(false);

  const fetchCustomers = async () => {
    if (!auth.merchantId) return;
    try {
      setRefreshing(true);
      const res = await apiClient.get(`/query/customers?merchant_id=${auth.merchantId}`);
      if (res.data) {
        setCustomers(res.data);
      }
    } catch (err) {
      console.error("Failed to fetch customers", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCustomerId || !paymentAmount || parseFloat(paymentAmount) <= 0) return;
    try {
      setRecordingPayment(true);
      await apiClient.post('/ledger/record-payment', {
        customer_id: selectedCustomerId,
        amount: parseFloat(paymentAmount)
      });
      toast.success("Payment recorded successfully!");
      setShowPaymentModal(false);
      setPaymentAmount('');
      setSelectedCustomerId('');
      fetchCustomers();
    } catch (err: any) {
      toast.error(err.message || "Failed to record payment");
    } finally {
      setRecordingPayment(false);
    }
  };

  const copyPaymentLink = (customer: CustomerData) => {
    const link = `https://paytm.me/mock-${customer.customer_id.slice(-6)}`;
    navigator.clipboard.writeText(link);
    toast.success(`Copied payment link for ${customer.display_name}`);
  };

  useEffect(() => {
    fetchCustomers();
  }, [auth.merchantId]);

  const filteredCustomers = customers.filter(c => 
    c.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.customer_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalOutstanding = customers.reduce((sum, c) => sum + (c.total_due > 0 ? c.total_due : 0), 0);
  const activeCount = customers.length;
  const highDueCount = customers.filter(c => c.total_due >= 500).length;

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink-800">Customer Udhaar Ledger</h1>
          <p className="text-sm text-ink-500 mt-1">Real-time balances and credit history for all registered customers.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <Button 
            variant="primary" 
            size="sm" 
            onClick={() => setShowPaymentModal(true)}
            className="flex items-center gap-2"
          >
            <DollarSign className="w-4 h-4" />
            <span>Record Payment</span>
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchCustomers}
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
          <div className="text-xs font-semibold text-ink-400 uppercase tracking-wider mb-2">Total Customer Dues</div>
          <div className="text-2xl font-bold text-danger">{formatCurrency(totalOutstanding)}</div>
          <div className="text-xs text-ink-400 mt-1">Aggregated across {activeCount} customer accounts</div>
        </Card>

        <Card>
          <div className="text-xs font-semibold text-ink-400 uppercase tracking-wider mb-2">Total Accounts</div>
          <div className="text-2xl font-bold text-ink-800">{activeCount}</div>
          <div className="text-xs text-ink-400 mt-1">Canonical identity records</div>
        </Card>

        <Card>
          <div className="text-xs font-semibold text-ink-400 uppercase tracking-wider mb-2">High Due Accounts (≥ ₹500)</div>
          <div className="text-2xl font-bold text-amber-600">{highDueCount}</div>
          <div className="text-xs text-ink-400 mt-1">Requires follow-up / reminder</div>
        </Card>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white p-4 rounded-2xl border border-cream-200 shadow-soft flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-400" />
          <input 
            type="text"
            placeholder="Search by customer name or ID..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-cream-50 border border-cream-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sage-500/20 focus:border-sage-300"
          />
        </div>
        <div className="text-xs text-ink-400 font-medium">
          Showing {filteredCustomers.length} of {customers.length} accounts
        </div>
      </div>

      {/* Customers Table / Cards */}
      <Card className="overflow-hidden p-0">
        {loading ? (
          <div className="p-12 text-center text-ink-400">Loading customer accounts...</div>
        ) : filteredCustomers.length === 0 ? (
          <div className="p-12 text-center text-ink-400">
            {searchTerm ? `No customers matching "${searchTerm}"` : 'No customers recorded yet. Record a voice credit from the dashboard to auto-create customers.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-ink-700 border-collapse">
              <thead>
                <tr className="bg-cream-50 border-b border-cream-200 text-xs text-ink-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-6">Customer</th>
                  <th className="py-3 px-4">Canonical ID</th>
                  <th className="py-3 px-4">Purchased Items</th>
                  <th className="py-3 px-4 text-right">Total Credit</th>
                  <th className="py-3 px-4 text-right">Net Due</th>
                  <th className="py-3 px-6 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cream-100">
                {filteredCustomers.map((cust) => (
                  <tr key={cust.customer_id} className="hover:bg-cream-50/50 transition-colors">
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-sage-100 text-sage-700 font-bold flex items-center justify-center text-sm">
                          {cust.display_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-semibold text-ink-800">{cust.display_name}</div>
                          <div className="text-xs text-ink-400">
                            Last active: {new Date(cust.last_active).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' })}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-4 font-mono text-xs text-ink-500">
                      {cust.customer_id}
                    </td>
                    <td className="py-4 px-4">
                      {cust.items_summary && cust.items_summary.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {cust.items_summary.map((item, idx) => (
                            <span key={idx} className="bg-amber-50 text-amber-800 border border-amber-200 text-[11px] px-2 py-0.5 rounded-md">
                              🛒 {item}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-ink-300 text-xs italic">No items listed</span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right font-medium text-ink-600">
                      {formatCurrency(cust.total_credits)}
                    </td>
                    <td className="py-4 px-4 text-right font-bold text-base">
                      <div className="flex items-center justify-end gap-2">
                        {cust.total_due > 0 && (
                          <button 
                            onClick={() => copyPaymentLink(cust)}
                            className="p-1.5 text-ink-400 hover:text-sage-600 hover:bg-sage-50 rounded-lg transition-colors"
                            title="Copy Payment Link"
                          >
                            <LinkIcon className="w-4 h-4" />
                          </button>
                        )}
                        <span className={cust.total_due > 0 ? 'text-danger' : 'text-positive'}>
                          {formatCurrency(cust.total_due)}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-center">
                      <StatusBadge status={cust.total_due > 0 ? 'DUE' : 'CLEARED'} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Record Payment Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-ink-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md p-6 animate-scale-up">
            <h3 className="text-xl font-semibold text-ink-800 mb-4">Record Customer Payment</h3>
            <form onSubmit={handleRecordPayment} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ink-700 mb-1">Select Customer</label>
                <select 
                  className="w-full px-4 py-2 bg-cream-50 border border-cream-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sage-500/20"
                  value={selectedCustomerId}
                  onChange={(e) => setSelectedCustomerId(e.target.value)}
                  required
                >
                  <option value="">-- Choose Customer --</option>
                  {customers.filter(c => c.total_due > 0).map(c => (
                    <option key={c.customer_id} value={c.customer_id}>
                      {c.display_name} (Due: {formatCurrency(c.total_due)})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-ink-700 mb-1">Amount Received (₹)</label>
                <input 
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  placeholder="e.g. 500"
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  className="w-full px-4 py-2 bg-cream-50 border border-cream-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sage-500/20"
                />
              </div>
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-cream-100">
                <Button variant="outline" type="button" onClick={() => setShowPaymentModal(false)}>Cancel</Button>
                <Button variant="primary" type="submit" disabled={recordingPayment || !selectedCustomerId || !paymentAmount}>
                  {recordingPayment ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Confirm Payment
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};
