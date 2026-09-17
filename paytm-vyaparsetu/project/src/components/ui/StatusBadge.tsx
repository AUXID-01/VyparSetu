import React from 'react';
import { CheckCircle2, CircleDashed, XCircle } from 'lucide-react';
import { OutboxStatus } from '../../types';

interface StatusBadgeProps {
  status: OutboxStatus | 'FULLY_RECORDED';
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  if (status === 'PENDING') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-medium" title="Background sync in progress">
        <CircleDashed className="w-3.5 h-3.5 animate-[spin_3s_linear_infinite]" />
        <span>{label || 'Syncing'}</span>
      </div>
    );
  }

  if (status === 'SYNCED' || status === 'FULLY_RECORDED') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-mint-50 text-sage-600 text-xs font-medium">
        <CheckCircle2 className="w-3.5 h-3.5" />
        <span>{label || (status === 'FULLY_RECORDED' ? 'Fully recorded' : 'Recorded')}</span>
      </div>
    );
  }

  if (status === 'FAILED') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-50 text-danger text-xs font-medium" title="Your transaction is safely recorded. Background sync will retry automatically.">
        <XCircle className="w-3.5 h-3.5" />
        <span>{label || 'Sync delayed'}</span>
      </div>
    );
  }

  return null;
};
