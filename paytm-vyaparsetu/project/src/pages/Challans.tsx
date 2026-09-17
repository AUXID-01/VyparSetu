import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { StatusBadge } from '../components/ui/StatusBadge';
import { challanService } from '../services/challanService';
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, ArrowRight, Loader2 } from 'lucide-react';
import { db } from '../services/database';

export const Challans: React.FC = () => {
  const [state, setState] = useState<'IDLE' | 'EXTRACTING' | 'REVIEW' | 'CONFIRMED' | 'PAYING' | 'PAID'>('IDLE');
  const [extracted, setExtracted] = useState<any>(null);
  const [confirmData, setConfirmData] = useState<any>(null);

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setState('EXTRACTING');
      const data = await challanService.extract(e.target.files[0]);
      setExtracted(data);
      setState('REVIEW');
    }
  };

  const handleConfirm = async () => {
    const data = await challanService.confirm(extracted);
    setConfirmData(data);
    setState('CONFIRMED');
  };

  const handlePayout = async () => {
    setState('PAYING');
    await challanService.settle(confirmData.invoice.invoice_id);
    setState('PAID');
  };

  const formatCurrency = (val: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(val);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-ink-800">Challan Digitization</h1>
          <p className="text-ink-500 mt-1">Upload supplier invoices for instant extraction and rate checking.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left Column: Upload / Review / Confirm */}
        <div className="space-y-6">
          {state === 'IDLE' && (
            <Card className="flex flex-col items-center justify-center py-16 border-dashed border-2 border-cream-200 hover:border-sage-300 transition-colors cursor-pointer" onClick={handleUploadClick}>
              <input 
                type="file" 
                className="hidden" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                accept="image/*,.pdf"
              />
              <div className="w-16 h-16 rounded-full bg-cream-100 text-ink-400 flex items-center justify-center mb-4">
                <UploadCloud className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-medium text-ink-800">Upload Challan</h3>
              <p className="text-sm text-ink-400 mt-1 mb-6">Drop image or PDF here</p>
              <Button onClick={(e) => { e.stopPropagation(); handleUploadClick(); }}>Browse Files</Button>
            </Card>
          )}

          {state === 'EXTRACTING' && (
            <Card className="flex flex-col items-center justify-center py-16">
              <div className="w-16 h-16 relative mb-4">
                <div className="absolute inset-0 rounded-full border-4 border-sage-100" />
                <div className="absolute inset-0 rounded-full border-4 border-sage-500 border-t-transparent animate-spin" />
                <FileText className="w-6 h-6 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-sage-600" />
              </div>
              <h3 className="text-lg font-medium text-ink-800">Extracting details...</h3>
              <p className="text-sm text-ink-400 mt-1">Reading line items and amounts</p>
            </Card>
          )}

          {(state === 'REVIEW' || state === 'CONFIRMED' || state === 'PAYING' || state === 'PAID') && extracted && (
            <Card className="animate-fade-in relative overflow-hidden">
              {state !== 'REVIEW' && (
                 <div className="absolute top-0 right-0 p-4">
                    <StatusBadge status={confirmData?.invoice?.sync_status || 'PENDING'} />
                 </div>
              )}
              
              <div className="mb-6 pr-20">
                <div className="text-sm text-ink-400">Supplier</div>
                <div className="text-lg font-semibold text-ink-800">{extracted.distributor_name_guess}</div>
              </div>

              <div className="space-y-3 mb-6">
                <div className="text-sm font-medium text-ink-500 mb-2">Line Items</div>
                {extracted.line_items.map((item: any, i: number) => (
                  <div key={i} className="flex justify-between items-center text-sm border-b border-cream-100 pb-2">
                    <div>
                      <div className="font-medium text-ink-700">{item.sku}</div>
                      <div className="text-ink-400">{item.quantity} units @ {formatCurrency(item.unit_price)}</div>
                    </div>
                    <div className="font-semibold text-ink-800">
                      {formatCurrency(item.quantity * item.unit_price)}
                    </div>
                  </div>
                ))}
                <div className="flex justify-between items-center pt-2">
                  <div className="font-medium text-ink-700">Total Amount</div>
                  <div className="text-xl font-bold text-ink-800">{formatCurrency(extracted.total_amount)}</div>
                </div>
              </div>

              {state === 'REVIEW' && (
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1">Edit Details</Button>
                  <Button variant="primary" className="flex-1" onClick={handleConfirm}>Confirm & Save</Button>
                </div>
              )}

              {state !== 'REVIEW' && (
                <div className="flex items-center gap-2 text-positive bg-positive/10 px-4 py-3 rounded-xl">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-medium">Challan Confirmed</span>
                </div>
              )}
            </Card>
          )}
        </div>

        {/* Right Column: Instant Intelligence & Actions (Only visible after confirm) */}
        <div className="space-y-6">
          {(state === 'CONFIRMED' || state === 'PAYING' || state === 'PAID') && confirmData && (
            <>
              {/* INSTANT RATE CHECK - Fast Path intelligence */}
              {confirmData.rate_alerts.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 animate-slide-up">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-amber-800 mb-1">Price increase detected</h4>
                      <p className="text-sm text-amber-700 mb-3">
                        <span className="font-medium">{confirmData.rate_alerts[0].sku}</span> is <span className="font-semibold">{formatCurrency(confirmData.rate_alerts[0].delta)} higher</span> per unit than your previous purchase.
                      </p>
                      <button className="text-xs font-medium text-amber-800 hover:text-amber-900 bg-amber-100 hover:bg-amber-200 px-3 py-1.5 rounded-lg transition-colors">
                        View comparison
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Settlement Block */}
              <Card className="animate-slide-up" style={{ animationDelay: '0.1s' }}>
                <h3 className="font-semibold text-ink-800 mb-4">Settlement</h3>
                <div className="space-y-3 mb-6 bg-cream-50 p-4 rounded-xl">
                  <div className="flex justify-between text-sm">
                    <span className="text-ink-500">Invoice Amount</span>
                    <span className="font-medium text-ink-800">{formatCurrency(extracted.total_amount)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-ink-500">Available Balance</span>
                    <span className="font-medium text-ink-800">{formatCurrency(5200)}</span>
                  </div>
                  <div className="border-t border-cream-200 pt-2 flex justify-between text-sm">
                    <span className="text-ink-500">Remaining After</span>
                    <span className="font-semibold text-ink-800">{formatCurrency(confirmData.remaining_after)}</span>
                  </div>
                </div>

                {state === 'CONFIRMED' && (
                  <Button variant="primary" fullWidth onClick={handlePayout}>
                    Approve Payout <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                )}
                {state === 'PAYING' && (
                  <Button variant="outline" fullWidth disabled>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Processing payout...
                  </Button>
                )}
                {state === 'PAID' && (
                  <div className="flex items-center justify-center gap-2 text-positive py-2 font-medium">
                    <CheckCircle2 className="w-5 h-5" />
                    ₹{extracted.total_amount} settlement initiated
                  </div>
                )}
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
