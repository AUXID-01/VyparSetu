import React from 'react';
import { Card } from '../components/ui/Card';
import { MessageSquare, CreditCard, Bell, ShieldAlert } from 'lucide-react';

export const Automation: React.FC = () => {
  const workflows = [
    {
      name: "Payment Link Dispatch",
      status: "Active",
      trigger: "Confirmed credit via Voice/Manual",
      action: "Sends WhatsApp payment link",
      icon: MessageSquare,
      color: "bg-teal-50 text-teal-600"
    },
    {
      name: "Vendor Payout",
      status: "Active",
      trigger: "Settlement approved by Merchant",
      action: "Initiates payout workflow via Paytm",
      icon: CreditCard,
      color: "bg-sage-50 text-sage-600"
    },
    {
      name: "Low Balance Alert",
      status: "Active",
      trigger: "Wallet balance drops below threshold",
      action: "Notifies merchant immediately",
      icon: Bell,
      color: "bg-amber-50 text-amber-600"
    },
    {
      name: "Error Monitoring",
      status: "Active",
      trigger: "Any workflow failure",
      action: "Alerts engineering team",
      icon: ShieldAlert,
      color: "bg-danger/10 text-danger"
    }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-ink-800">Automation Center</h1>
        <p className="text-ink-500 mt-1">Background workflows powered by n8n. These run quietly without slowing you down.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {workflows.map((wf, i) => (
          <Card key={i} className="flex flex-col h-full hover:border-sage-300 transition-colors">
            <div className="flex items-start justify-between mb-6">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${wf.color}`}>
                <wf.icon className="w-6 h-6" />
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-positive/10 text-positive text-xs font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-positive animate-pulse-soft" />
                {wf.status}
              </div>
            </div>
            
            <h3 className="text-lg font-semibold text-ink-800 mb-4">{wf.name}</h3>
            
            <div className="mt-auto space-y-3">
              <div>
                <div className="text-xs font-medium text-ink-400 uppercase tracking-wider mb-1">Trigger</div>
                <div className="text-sm font-medium text-ink-700 bg-cream-50 py-1.5 px-3 rounded-lg">{wf.trigger}</div>
              </div>
              <div className="flex justify-center py-1">
                <div className="w-px h-4 bg-cream-200" />
              </div>
              <div>
                <div className="text-xs font-medium text-ink-400 uppercase tracking-wider mb-1">Action</div>
                <div className="text-sm font-medium text-ink-700 bg-cream-50 py-1.5 px-3 rounded-lg">{wf.action}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
