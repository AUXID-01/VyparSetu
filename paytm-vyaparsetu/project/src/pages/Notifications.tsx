import React, { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { AlertTriangle, AlertCircle, XOctagon, CheckCircle2, Loader2, ArrowRight } from 'lucide-react';
import { apiClient } from '../services/apiClient';

export interface AlertData {
  alert_id: string;
  alert_type: string;
  is_read: boolean;
  details: any;
  created_at: string;
}

export const Notifications: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get('/alerts');
      if (res.data) setAlerts(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const markAsRead = async (alertId: string) => {
    try {
      await apiClient.patch(`/alerts/${alertId}/read`, {});
      setAlerts(prev => prev.map(a => a.alert_id === alertId ? { ...a, is_read: true } : a));
    } catch (err) {
      console.error(err);
    }
  };

  const getAlertIconAndStyle = (type: string) => {
    switch (type) {
      case 'RATE_SPIKE':
        return { icon: AlertTriangle, color: 'text-amber-600 bg-amber-50', border: 'border-amber-200' };
      case 'PAYOUT_FAILED':
        return { icon: AlertCircle, color: 'text-red-500 bg-red-50', border: 'border-red-200' };
      case 'SYSTEM_ERROR':
        return { icon: XOctagon, color: 'text-rose-700 bg-rose-50', border: 'border-rose-300' };
      default:
        return { icon: AlertCircle, color: 'text-ink-500 bg-cream-100', border: 'border-cream-200' };
    }
  };

  const renderAlertDetails = (a: AlertData) => {
    if (a.alert_type === 'RATE_SPIKE') {
      return (
        <div className="text-sm text-ink-600 mt-1">
          Price for <span className="font-semibold text-ink-800">{a.details.sku}</span> increased by 
          <span className="font-semibold text-amber-600"> ₹{a.details.delta?.toFixed(2)}</span>. 
          Previous: ₹{a.details.previous_price}, Current: ₹{a.details.current_price}.
        </div>
      );
    }
    if (a.alert_type === 'PAYOUT_FAILED') {
      return (
        <div className="text-sm text-ink-600 mt-1">
          Payout of <span className="font-semibold text-red-600">₹{a.details.amount}</span> failed. 
          Reason: <span className="italic">{a.details.failure_reason || 'Unknown'}</span>
        </div>
      );
    }
    if (a.alert_type === 'SYSTEM_ERROR') {
      return (
        <div className="text-sm text-ink-600 mt-1">
          Workflow: <span className="font-semibold">{a.details.workflow_name}</span>. 
          Error: <span className="italic text-rose-600">{a.details.error_message}</span>
        </div>
      );
    }
    return <div className="text-sm text-ink-600 mt-1">Check details in system.</div>;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink-800">Notifications & Alerts</h1>
        <p className="text-ink-500 mt-1">Review system alerts, rate spikes, and workflow failures.</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-ink-400">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
      ) : alerts.length === 0 ? (
        <div className="p-12 text-center text-ink-400 border border-dashed rounded-xl border-cream-300">
          No alerts found.
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map(a => {
            const { icon: Icon, color, border } = getAlertIconAndStyle(a.alert_type);
            return (
              <Card key={a.alert_id} className={`p-4 border ${a.is_read ? 'opacity-75 bg-cream-50' : 'bg-white'} ${border} shadow-sm flex items-start gap-4 transition-opacity`}>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <h3 className="font-semibold text-ink-800 tracking-tight">
                      {a.alert_type.replace('_', ' ')}
                    </h3>
                    <span className="text-xs text-ink-400 font-medium">
                      {new Date(a.created_at).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' })}
                    </span>
                  </div>
                  {renderAlertDetails(a)}
                </div>
                {!a.is_read && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="shrink-0 text-xs py-1 px-3 mt-1"
                    onClick={() => markAsRead(a.alert_id)}
                  >
                    Mark as Read
                  </Button>
                )}
                {a.is_read && (
                  <div className="mt-1 flex items-center text-xs font-semibold text-positive">
                    <CheckCircle2 className="w-4 h-4 mr-1" /> Read
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
