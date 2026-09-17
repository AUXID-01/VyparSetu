import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mic, CheckCircle2, ArrowRight, Code2, Database, Zap, Sparkles, Clock } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const LandingPage: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-cream-100 font-sans text-ink-800 selection:bg-sage-200">
      
      {/* Navbar */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled ? 'bg-white/80 backdrop-blur-md shadow-sm border-b border-cream-200 py-3' : 'bg-transparent py-5'}`}>
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-sage-500 flex items-center justify-center">
              <span className="text-white font-bold text-lg">V</span>
            </div>
            <span className="font-semibold text-xl tracking-tight text-ink-800">VyaparSetu</span>
          </div>
          
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-ink-600">
            <a href="#product" className="hover:text-ink-800 transition-colors">Product</a>
            <a href="#how-it-works" className="hover:text-ink-800 transition-colors">How it works</a>
            <a href="#integration" className="hover:text-ink-800 transition-colors">Integration</a>
          </div>

          <Link to="/dashboard">
            <Button>Open Dashboard</Button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-16">
        <div className="flex-1 space-y-6 text-center lg:text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-sage-50 text-sage-600 font-medium text-sm border border-sage-100">
            <Sparkles className="w-4 h-4" /> Merchant intelligence, without the complexity.
          </div>
          <h1 className="text-5xl lg:text-7xl font-bold tracking-tight text-balance leading-[1.1]">
            Your business conversations, <span className="text-sage-600">turned into action.</span>
          </h1>
          <p className="text-lg text-ink-500 max-w-2xl mx-auto lg:mx-0 leading-relaxed text-balance">
            Record credit, process challans, track dues, automate settlements, and understand your business — without slowing down the counter.
          </p>
          <div className="flex items-center justify-center lg:justify-start gap-4 pt-4">
            <Link to="/dashboard">
              <Button size="lg" className="h-14 px-8 text-base shadow-lg shadow-sage-500/20">Explore Dashboard</Button>
            </Link>
            <a href="#how-it-works">
              <Button size="lg" variant="ghost" className="h-14 px-8 text-base">See How It Works</Button>
            </a>
          </div>
        </div>

        {/* Hero Interactive Visual */}
        <div className="flex-1 w-full max-w-md relative">
          <div className="absolute inset-0 bg-gradient-sage rounded-[2.5rem] transform rotate-3 opacity-50 blur-xl" />
          <div className="bg-white rounded-[2rem] border border-cream-200 shadow-float p-8 relative z-10 flex flex-col items-center">
            
            <div className="w-full flex justify-between items-center mb-12">
              <div className="w-12 h-3 bg-cream-200 rounded-full" />
              <div className="w-8 h-8 rounded-full bg-cream-100" />
            </div>

            {/* Simulated Interaction sequence using CSS animation delays for simplicity in Landing Page */}
            <div className="relative w-full aspect-square flex flex-col items-center justify-center">
               
               <div className="w-24 h-24 rounded-full bg-sage-50 text-sage-500 flex items-center justify-center shadow-inner mb-6 relative">
                 <Mic className="w-10 h-10" />
                 <div className="absolute inset-0 rounded-full border-2 border-sage-200 animate-ping" />
               </div>

               <div className="text-center space-y-2 relative h-16 w-full">
                 <motion.div 
                    initial={{ opacity: 1 }} animate={{ opacity: [1, 0] }} transition={{ delay: 2, duration: 0.5 }}
                    className="absolute inset-0"
                  >
                   <p className="text-sage-600 font-medium">Listening...</p>
                 </motion.div>
                 
                 <motion.div 
                    initial={{ opacity: 0 }} animate={{ opacity: [0, 1] }} transition={{ delay: 2.5, duration: 0.5 }}
                    className="absolute inset-0 flex flex-col items-center"
                  >
                   <p className="text-ink-800 font-semibold text-lg flex items-center justify-center gap-2">
                     <CheckCircle2 className="w-5 h-5 text-positive" /> Confirmed
                   </p>
                   <p className="text-ink-500 text-sm mt-1">₹2,400 credit recorded</p>
                 </motion.div>
               </div>
            </div>

            <motion.div 
               initial={{ opacity: 0 }} animate={{ opacity: [0, 1] }} transition={{ delay: 3, duration: 0.5 }}
               className="w-full bg-cream-50 rounded-xl p-3 flex items-center gap-3 mt-4"
            >
              <div className="w-2 h-2 rounded-full bg-sage-400 animate-pulse" />
              <span className="text-xs font-medium text-ink-500">Syncing in background...</span>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Product Story */}
      <section id="how-it-works" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold text-ink-800 mb-4">From conversation to confirmed action.</h2>
            <p className="text-ink-500">A system designed around the reality of a busy merchant counter. Fast when you need it, smart when you don't.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-8 rounded-3xl bg-cream-50 border border-cream-100">
              <div className="w-12 h-12 rounded-xl bg-white text-ink-700 flex items-center justify-center mb-6 shadow-sm font-bold text-xl">01</div>
              <h3 className="text-xl font-semibold text-ink-800 mb-3">Speak naturally</h3>
              <p className="text-ink-500 leading-relaxed">No strict commands. Just talk the way you normally do with your customers. VyaparSetu understands context and intent.</p>
            </div>
            
            <div className="p-8 rounded-3xl bg-cream-50 border border-cream-100">
              <div className="w-12 h-12 rounded-xl bg-white text-ink-700 flex items-center justify-center mb-6 shadow-sm font-bold text-xl">02</div>
              <h3 className="text-xl font-semibold text-ink-800 mb-3">Confirm instantly</h3>
              <p className="text-ink-500 leading-relaxed">Your ledger updates immediately. You never have to wait for the system to process or generate an answer before confirming a transaction.</p>
            </div>

            <div className="p-8 rounded-3xl bg-sage-50 border border-sage-100">
              <div className="w-12 h-12 rounded-xl bg-white text-sage-600 flex items-center justify-center mb-6 shadow-sm font-bold text-xl">03</div>
              <h3 className="text-xl font-semibold text-ink-800 mb-3">Keep working</h3>
              <p className="text-ink-500 leading-relaxed">Deeper analysis, rate checking, and AI syncing happens quietly in the background. You're already helping the next customer.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Integration Blueprint */}
      <section id="integration" className="py-24 bg-ink-900 text-cream-50 overflow-hidden relative">
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-sage-500/50 to-transparent" />
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-ink-800 text-sage-300 font-medium text-sm border border-ink-700">
              <Code2 className="w-4 h-4" /> Built for developers
            </div>
            <h2 className="text-3xl lg:text-4xl font-bold tracking-tight text-white">Integration Blueprint</h2>
            <p className="text-ink-300 leading-relaxed text-lg text-balance">
              VyaparSetu ships as a documented API and embeddable widget. Paytm's existing merchant app can call it directly rather than adopting a new platform.
            </p>
            
            <div className="bg-ink-800/50 border border-ink-700 rounded-2xl p-6 font-mono text-sm overflow-x-auto text-ink-300">
              <div className="flex text-sage-400 mb-2">// VyaparSetu API Contract</div>
              <div className="flex gap-4 mb-2"><span className="text-teal-400">POST</span> <span>/v1/voice/log-credit</span></div>
              <div className="flex gap-4 mb-2"><span className="text-teal-400">POST</span> <span>/v1/challan/extract</span></div>
              <div className="flex gap-4 mb-4"><span className="text-teal-400">GET</span> <span>/v1/query/summary</span></div>
              <div className="flex text-ink-500">// Background Webhooks (n8n)</div>
              <div className="flex gap-4 mb-2"><span className="text-amber-400">POST</span> <span>/webhook/payment-link</span></div>
              <div className="flex gap-4"><span className="text-amber-400">POST</span> <span>/webhook/vendor-payout</span></div>
            </div>
          </div>

          <div className="relative">
            {/* Architecture Visual */}
            <div className="absolute inset-0 bg-gradient-to-tr from-sage-500/20 to-teal-500/20 rounded-full blur-[100px]" />
            <div className="relative grid grid-cols-2 gap-4">
               
               <div className="col-span-2 bg-ink-800 border border-ink-700 rounded-2xl p-6 flex items-center gap-4 text-white z-20">
                 <div className="w-12 h-12 rounded-xl bg-ink-700 flex items-center justify-center"><CheckCircle2 className="w-6 h-6 text-positive" /></div>
                 <div>
                   <div className="font-semibold text-lg">Merchant App</div>
                   <div className="text-sm text-ink-400">Synchronous & Fast</div>
                 </div>
               </div>
               
               <div className="flex justify-center -my-2 z-10"><div className="w-0.5 h-8 bg-ink-700" /></div>
               <div className="flex justify-center -my-2 z-10"><div className="w-0.5 h-8 bg-ink-700" /></div>

               <div className="bg-ink-800 border border-ink-700 rounded-2xl p-6 text-center text-white z-20 relative">
                 <div className="absolute top-2 right-2 flex items-center gap-1 text-[10px] text-sage-400 font-bold tracking-wider uppercase"><Zap className="w-3 h-3" /> Fast Path</div>
                 <Database className="w-8 h-8 mx-auto text-sage-500 mb-3" />
                 <div className="font-medium">PostgreSQL Ledger</div>
               </div>

               <div className="bg-ink-800 border border-ink-700 rounded-2xl p-6 text-center text-white z-20 relative opacity-80">
                 <div className="absolute top-2 right-2 flex items-center gap-1 text-[10px] text-ink-400 font-bold tracking-wider uppercase"><Clock className="w-3 h-3" /> Async</div>
                 <Sparkles className="w-8 h-8 mx-auto text-teal-500 mb-3" />
                 <div className="font-medium">n8n + Cognee</div>
               </div>

            </div>
          </div>

        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-ink-400 text-sm border-t border-cream-200">
        <p>Built for the Hackathon. Designed for Merchants.</p>
      </footer>
    </div>
  );
};
