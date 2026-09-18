import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, CheckCircle2, ArrowRight, Code2, Database, Zap, Sparkles, Clock, ScanLine, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { AuthModal } from '../components/auth/AuthModal';
import { useAuth } from '../contexts/AuthContext';


const DEMO_SCENARIOS = [
  {
    icon: Mic,
    color: 'sage',
    inputText: '"Record ₹2,400 from Suresh"',
    confirmTitle: 'Action Confirmed',
    confirmIcon: CheckCircle2,
    confirmIconColor: 'text-positive',
    confirmAvatar: 'S',
    confirmName: 'Suresh',
    confirmAmount: '+₹2,400',
    confirmAmountColor: 'text-positive',
    syncText: 'Syncing with ledger in background...'
  },
  {
    icon: ScanLine,
    color: 'teal',
    inputText: 'Extracting line items from Challan...',
    confirmTitle: 'Challan Extracted',
    confirmIcon: CheckCircle2,
    confirmIconColor: 'text-teal-600',
    confirmAvatar: 'C',
    confirmName: 'Total Invoice',
    confirmAmount: '₹14,500',
    confirmAmountColor: 'text-ink-800',
    syncText: 'Checking prices against history...'
  },
  {
    icon: Sparkles,
    color: 'amber',
    inputText: 'Analyzing recent vendor pricing...',
    confirmTitle: 'Price Increase Alert',
    confirmIcon: AlertTriangle,
    confirmIconColor: 'text-amber-500',
    confirmAvatar: '!',
    confirmName: 'Sugar (50kg)',
    confirmAmount: '+₹12/kg',
    confirmAmountColor: 'text-amber-600',
    syncText: 'Generating comparison report...'
  },
  {
    icon: Clock,
    color: 'indigo',
    inputText: '"How much does Ramesh owe me?"',
    confirmTitle: 'Ledger Fetched',
    confirmIcon: CheckCircle2,
    confirmIconColor: 'text-indigo-500',
    confirmAvatar: 'R',
    confirmName: 'Ramesh Dues',
    confirmAmount: '₹5,200',
    confirmAmountColor: 'text-danger',
    syncText: 'Fetching latest real-time state...'
  }
];

export const LandingPage: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [demoState, setDemoState] = useState<{ phase: 'IDLE' | 'LISTENING' | 'CONFIRMED', scenario: number }>({ phase: 'IDLE', scenario: 0 });
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    let currentScenario = 0;
    
    const cycle = () => {
      setDemoState({ phase: 'LISTENING', scenario: currentScenario });
      setTimeout(() => {
        setDemoState({ phase: 'CONFIRMED', scenario: currentScenario });
        setTimeout(() => {
          setDemoState({ phase: 'IDLE', scenario: currentScenario });
          currentScenario = (currentScenario + 1) % DEMO_SCENARIOS.length;
        }, 3500);
      }, 3500);
    };
    
    const interval = setInterval(cycle, 9000);
    cycle(); // start immediately
    return () => clearInterval(interval);
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

          <Button onClick={() => isAuthenticated ? navigate('/dashboard') : setIsAuthModalOpen(true)}>
            Open Dashboard
          </Button>
        </div>
      </nav>


      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-16">
        <motion.div 
          initial={{ opacity: 0, x: -30 }} 
          animate={{ opacity: 1, x: 0 }} 
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="flex-1 space-y-6 text-center lg:text-left"
        >
          <motion.div 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-sage-50 text-sage-600 font-medium text-sm border border-sage-100"
          >
            <Sparkles className="w-4 h-4" /> Merchant intelligence, without the complexity.
          </motion.div>
          <h1 className="text-5xl lg:text-7xl font-bold tracking-tight text-balance leading-[1.1]">
            Your business conversations, <span className="text-sage-600">turned into action.</span>
          </h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
            className="text-lg text-ink-500 max-w-2xl mx-auto lg:mx-0 leading-relaxed text-balance"
          >
            Record credit, process challans, track dues, automate settlements, and understand your business — without slowing down the counter.
          </motion.p>
          <motion.div 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
            className="flex items-center justify-center lg:justify-start gap-4 pt-4"
          >
            <Button size="lg" onClick={() => isAuthenticated ? navigate('/dashboard') : setIsAuthModalOpen(true)} className="h-14 px-8 text-base shadow-lg shadow-sage-500/20 hover:scale-105 transition-transform">Explore Dashboard</Button>
            <a href="#how-it-works">
              <Button size="lg" variant="ghost" className="h-14 px-8 text-base hover:bg-cream-200 transition-colors">See How It Works</Button>
            </a>
          </motion.div>
        </motion.div>

        {/* Hero Interactive Visual */}
        <motion.div 
          initial={{ opacity: 0, x: 30 }} 
          animate={{ opacity: 1, x: 0 }} 
          transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
          className="flex-1 w-full max-w-md relative"
        >
          <div className="absolute inset-0 bg-gradient-sage rounded-[2.5rem] transform rotate-3 opacity-50 blur-xl" />
          <div className="bg-white rounded-[2rem] border border-cream-200 shadow-float p-8 relative z-10 flex flex-col items-center">
            
            <div className="absolute top-0 inset-x-0 h-1 bg-cream-100 rounded-t-[2rem] overflow-hidden">
               <motion.div 
                 animate={{ x: ['-200%', '200%'] }} 
                 transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
                 className={`w-1/2 h-full bg-${DEMO_SCENARIOS[demoState.scenario].color}-500 blur-sm`}
               />
            </div>

            <div className="w-full flex justify-between items-center mb-10 mt-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-cream-200 hover:bg-danger transition-colors cursor-pointer" />
                <div className="w-3 h-3 rounded-full bg-cream-200 hover:bg-amber-400 transition-colors cursor-pointer" />
                <div className="w-3 h-3 rounded-full bg-cream-200 hover:bg-positive transition-colors cursor-pointer" />
              </div>
              
              <div className={`flex items-center gap-2 px-3 py-1 rounded-full border shadow-sm transition-colors duration-500
                ${demoState.phase === 'LISTENING' ? `bg-${DEMO_SCENARIOS[demoState.scenario].color}-50 text-${DEMO_SCENARIOS[demoState.scenario].color}-600 border-${DEMO_SCENARIOS[demoState.scenario].color}-200` 
                : 'bg-cream-50 text-ink-400 border-cream-200'}`}
              >
                <div className={`w-2 h-2 rounded-full transition-colors duration-500
                  ${demoState.phase === 'LISTENING' ? `bg-${DEMO_SCENARIOS[demoState.scenario].color}-500 animate-ping` : 'bg-ink-300'}`} 
                />
                <span className="text-[10px] font-bold uppercase tracking-wider">
                   {demoState.phase === 'IDLE' ? 'System Ready' : demoState.phase === 'LISTENING' ? 'Active' : 'Standby'}
                </span>
              </div>
            </div>

            {/* Simulated Interaction sequence using CSS animation delays for simplicity in Landing Page */}
            <div className="relative w-full h-64 flex flex-col items-center justify-center">
               
              <motion.div 
                animate={{ 
                  scale: demoState.phase === 'LISTENING' ? [1, 1.1, 1] : 1,
                  boxShadow: demoState.phase === 'LISTENING' 
                    ? [`0px 0px 0px 0px var(--tw-shadow-color)`, `0px 0px 0px 20px rgba(0,0,0,0)`, `0px 0px 0px 0px rgba(0,0,0,0)`] 
                    : 'none'
                }}
                transition={{ duration: 1.5, repeat: demoState.phase === 'LISTENING' ? Infinity : 0 }}
                className={`w-24 h-24 rounded-full flex items-center justify-center shadow-inner mb-8 transition-colors duration-500 z-10 
                  ${demoState.phase === 'LISTENING' ? `bg-${DEMO_SCENARIOS[demoState.scenario].color}-100 text-${DEMO_SCENARIOS[demoState.scenario].color}-600 shadow-${DEMO_SCENARIOS[demoState.scenario].color}-400/50` : 'bg-cream-100 text-ink-400'}`}
              >
                {React.createElement(DEMO_SCENARIOS[demoState.scenario].icon, { className: "w-10 h-10" })}
              </motion.div>

              <div className="h-24 w-full flex flex-col items-center justify-start relative">
                <AnimatePresence mode="wait">
                  {demoState.phase === 'IDLE' && (
                    <motion.div key="idle" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="text-ink-400 text-sm">
                      Waiting for input...
                    </motion.div>
                  )}
                  {demoState.phase === 'LISTENING' && (
                    <motion.div key="listening" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="text-center w-full">
                      <div className="flex items-center justify-center gap-1 mb-3">
                        {[1, 2, 3, 4, 5].map(i => (
                          <motion.div key={i} animate={{ height: [8, 20, 8] }} transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }} className={`w-1.5 bg-${DEMO_SCENARIOS[demoState.scenario].color}-400 rounded-full`} />
                        ))}
                      </div>
                      <p className={`text-${DEMO_SCENARIOS[demoState.scenario].color}-700 font-medium font-serif italic text-lg px-4 truncate`}>
                        {DEMO_SCENARIOS[demoState.scenario].inputText}
                      </p>
                    </motion.div>
                  )}
                  {demoState.phase === 'CONFIRMED' && (
                    <motion.div key="confirmed" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }} className="flex flex-col items-center w-full px-4">
                      <div className={`flex items-center gap-2 font-semibold text-lg mb-3 ${DEMO_SCENARIOS[demoState.scenario].confirmIconColor}`}>
                        {React.createElement(DEMO_SCENARIOS[demoState.scenario].confirmIcon, { className: "w-6 h-6" })} 
                        {DEMO_SCENARIOS[demoState.scenario].confirmTitle}
                      </div>
                      <div className="bg-white border border-cream-200 shadow-sm rounded-xl px-4 py-2 flex items-center gap-4 w-full max-w-[240px]">
                         <div className={`w-10 h-10 rounded-full bg-${DEMO_SCENARIOS[demoState.scenario].color}-50 text-${DEMO_SCENARIOS[demoState.scenario].color}-600 flex items-center justify-center font-bold text-sm shrink-0`}>
                           {DEMO_SCENARIOS[demoState.scenario].confirmAvatar}
                         </div>
                         <div className="text-left flex-1 min-w-0">
                           <div className="text-xs text-ink-500 truncate">{DEMO_SCENARIOS[demoState.scenario].confirmName}</div>
                           <div className={`text-sm font-bold ${DEMO_SCENARIOS[demoState.scenario].confirmAmountColor}`}>
                             {DEMO_SCENARIOS[demoState.scenario].confirmAmount}
                           </div>
                         </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            <div className="h-12 w-full mt-4">
              <AnimatePresence>
                {demoState.phase === 'CONFIRMED' && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }}
                    className="w-full bg-cream-50 rounded-xl p-3 flex items-center justify-center gap-3"
                  >
                    <div className={`w-2 h-2 rounded-full bg-${DEMO_SCENARIOS[demoState.scenario].color}-400 animate-pulse`} />
                    <span className="text-xs font-medium text-ink-500 truncate">{DEMO_SCENARIOS[demoState.scenario].syncText}</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Product Story */}
      <section id="how-it-works" className="py-24 bg-white overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center max-w-2xl mx-auto mb-16"
          >
            <h2 className="text-3xl font-bold text-ink-800 mb-4">From conversation to confirmed action.</h2>
            <p className="text-ink-500">A system designed around the reality of a busy merchant counter. Fast when you need it, smart when you don't.</p>
          </motion.div>

          <motion.div 
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={{
              visible: { transition: { staggerChildren: 0.2 } },
              hidden: {}
            }}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            <motion.div 
              variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
              whileHover={{ y: -8 }}
              className="p-8 rounded-3xl bg-cream-50 border border-cream-100 transition-shadow hover:shadow-lg hover:shadow-cream-200"
            >
              <div className="w-12 h-12 rounded-xl bg-white text-ink-700 flex items-center justify-center mb-6 shadow-sm font-bold text-xl">01</div>
              <h3 className="text-xl font-semibold text-ink-800 mb-3">Speak naturally</h3>
              <p className="text-ink-500 leading-relaxed">No strict commands. Just talk the way you normally do with your customers. VyaparSetu understands context and intent.</p>
            </motion.div>
            
            <motion.div 
              variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
              whileHover={{ y: -8 }}
              className="p-8 rounded-3xl bg-cream-50 border border-cream-100 transition-shadow hover:shadow-lg hover:shadow-cream-200"
            >
              <div className="w-12 h-12 rounded-xl bg-white text-ink-700 flex items-center justify-center mb-6 shadow-sm font-bold text-xl">02</div>
              <h3 className="text-xl font-semibold text-ink-800 mb-3">Confirm instantly</h3>
              <p className="text-ink-500 leading-relaxed">Your ledger updates immediately. You never have to wait for the system to process or generate an answer before confirming a transaction.</p>
            </motion.div>

            <motion.div 
              variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
              whileHover={{ y: -8 }}
              className="p-8 rounded-3xl bg-sage-50 border border-sage-100 transition-shadow hover:shadow-lg hover:shadow-sage-200/50"
            >
              <div className="w-12 h-12 rounded-xl bg-white text-sage-600 flex items-center justify-center mb-6 shadow-sm font-bold text-xl">03</div>
              <h3 className="text-xl font-semibold text-ink-800 mb-3">Keep working</h3>
              <p className="text-ink-500 leading-relaxed">Deeper analysis, rate checking, and AI syncing happens quietly in the background. You're already helping the next customer.</p>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Integration Blueprint */}
      <section id="integration" className="py-24 bg-ink-900 text-cream-50 overflow-hidden relative">
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-sage-500/50 to-transparent" />
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          
          <motion.div 
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8 }}
            className="space-y-6"
          >
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
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative"
          >
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
          </motion.div>

        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-ink-400 text-sm border-t border-cream-200">
        <p>Built for the Hackathon. Designed for Merchants.</p>
      </footer>
      
      <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} />
    </div>
  );
};
