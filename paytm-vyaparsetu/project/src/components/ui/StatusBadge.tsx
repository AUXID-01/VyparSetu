import React from 'react';
import { CheckCircle2, Clock, XCircle } from 'lucide-react';

interface StatusBadgeProps {
  status?: string;
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const normalized = (status || '').toUpperCase();

  if (normalized === 'DUE' || normalized === 'UNPAID') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200 text-xs font-semibold">
        <Clock className="w-3.5 h-3.5" />
        <span>{label || 'Udhaar Due'}</span>
      </div>
    );
  }

  if (normalized === 'CLEARED' || normalized === 'PAID') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
        <CheckCircle2 className="w-3.5 h-3.5" />
        <span>{label || 'Cleared'}</span>
      </div>
    );
  }

  if (normalized === 'FAILED') {
    return (
      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-50 text-danger text-xs font-medium">
        <XCircle className="w-3.5 h-3.5" />
        <span>{label || 'Sync delayed'}</span>
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium">
      <CheckCircle2 className="w-3.5 h-3.5" />
      <span>{label || (normalized === 'FULLY_RECORDED' ? 'Fully recorded' : 'Recorded')}</span>
    </div>
  );
};
