import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { insightService } from '../services/insightService';
import { useAuth } from '../contexts/AuthContext';
import { Search, Sparkles, TrendingUp, AlertCircle, ArrowRight, Clock } from 'lucide-react';

export const Insights: React.FC = () => {
  const { auth } = useAuth();
  const [query, setQuery] = useState('');
  const [state, setState] = useState<'IDLE' | 'THINKING' | 'ANSWERED'>('IDLE');
  const [answer, setAnswer] = useState<{ text: string, source: string, latency: number } | null>(null);

  const handleAsk = async (e?: React.FormEvent, directQuery?: string) => {
    if (e) e.preventDefault();
    const q = directQuery || query;
    if (!q.trim() || !auth.merchantId) return;
    
    setQuery(q);
    setState('THINKING');
    try {
      const res = await insightService.ask(auth.merchantId, q);
      setAnswer({ text: res.answer, source: res.source, latency: res.generated_in_ms });
    } catch (err) {
      console.error(err);
      setAnswer({ text: "Sorry, I couldn't analyze that right now.", source: "ERROR", latency: 0 });
    }
    setState('ANSWERED');
  };

  const predefinedInsights = [
    {
      title: "Supplier Pricing Trend",
      description: "Amul pricing has increased 7.8% over the last two months.",
      icon: TrendingUp,
      color: "text-amber-600 bg-amber-50"
    },
    {
      title: "Credit Exposure",
      description: "Outstanding credit has increased 12% this month. Three customers account for 40% of dues.",
      icon: AlertCircle,
      color: "text-sage-600 bg-sage-50"
    },
    {
      title: "High Velocity Items",
      description: "Dahi and Refined Oil are your fastest moving SKUs this week.",
      icon: Sparkles,
      color: "text-teal-600 bg-teal-50"
    }
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-ink-800">Business Insights</h1>
        <p className="text-ink-500 mt-1">Deep analysis and trends from your ledger history.</p>
      </div>

      {/* Smart Query Box */}
      <Card className="bg-gradient-to-br from-sage-50/50 to-white border-sage-100">
        <form onSubmit={handleAsk} className="relative">
          <Search className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-sage-500" />
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about your business... e.g. 'Which supplier increased prices the most?'" 
            className="w-full pl-12 pr-32 py-4 bg-white border border-sage-200 rounded-2xl text-base focus:outline-none focus:ring-2 focus:ring-sage-500/20 focus:border-sage-400 transition-all placeholder:text-ink-300 shadow-soft"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2">
            <Button type="submit" size="sm" disabled={!query.trim() || state === 'THINKING'}>
              Analyze
            </Button>
          </div>
        </form>

        {state === 'THINKING' && (
          <div className="mt-6 p-6 rounded-2xl bg-white/60 border border-sage-100 flex flex-col items-center justify-center animate-fade-in">
             <div className="flex items-center gap-1.5 h-12 mb-2">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="w-2 h-2 bg-sage-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            <p className="text-sage-700 font-medium">Checking your business history...</p>
            <p className="text-sm text-sage-500 mt-1">This deeper analysis takes a moment.</p>
          </div>
        )}

        {state === 'ANSWERED' && answer && (
          <div className="mt-6 p-6 rounded-2xl bg-white border border-sage-200 shadow-soft animate-slide-up relative">
            <div className="absolute top-4 right-4 flex items-center gap-3">
              <div className="flex items-center gap-1.5 px-2 py-1 bg-cream-50 rounded-md text-xs font-medium text-ink-400">
                 <Clock className="w-3 h-3" />
                 {answer.latency} ms
              </div>
              <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-bold ${answer.source === 'CACHE' ? 'bg-positive/10 text-positive' : answer.source === 'LIVE' ? 'bg-blue-100 text-blue-600' : 'bg-danger/10 text-danger'}`}>
                 {answer.source === 'CACHE' ? 'CACHE' : answer.source === 'LIVE' ? 'LIVE' : 'ERROR'}
              </div>
            </div>
            <h3 className="text-lg font-semibold text-ink-800 mb-3 flex items-center gap-2">
               <Sparkles className="w-5 h-5 text-sage-500" />
               Analysis Ready
            </h3>
            <p className="text-ink-700 leading-relaxed text-balance">
              {answer.text}
            </p>
          </div>
        )}
      </Card>

      {/* Pre-calculated Insight Cards */}
      <h3 className="text-lg font-semibold text-ink-800 pt-4">Recent Discoveries</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {predefinedInsights.map((insight, i) => (
          <Card 
            key={i} 
            className="hover:-translate-y-1 transition-transform cursor-pointer group"
            onClick={() => handleAsk(undefined, insight.title)}
          >
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${insight.color}`}>
              <insight.icon className="w-5 h-5" />
            </div>
            <h4 className="font-medium text-ink-800 mb-2">{insight.title}</h4>
            <p className="text-sm text-ink-500 leading-relaxed">{insight.description}</p>
            <div className="mt-4 flex items-center text-sm font-medium text-sage-600 opacity-0 group-hover:opacity-100 transition-opacity">
               Explore <ArrowRight className="w-4 h-4 ml-1" />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
