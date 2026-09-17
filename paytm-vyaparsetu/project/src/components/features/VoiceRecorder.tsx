import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, CheckCircle2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { StatusBadge } from '../ui/StatusBadge';
import { voiceService } from '../../services/voiceService';

export const VoiceRecorder: React.FC = () => {
  const [state, setState] = useState<'IDLE' | 'LISTENING' | 'UNDERSTANDING' | 'CONFIRM' | 'RECORDED'>('IDLE');
  const [extracted, setExtracted] = useState<any>(null);
  const [recordedTxn, setRecordedTxn] = useState<any>(null);

  const startRecording = async () => {
    setState('LISTENING');
    // Simulate recording time
    setTimeout(async () => {
      setState('UNDERSTANDING');
      const { transcript } = await voiceService.transcribe();
      const data = await voiceService.extract(transcript);
      setExtracted(data);
      setState('CONFIRM');
    }, 2000);
  };

  const handleConfirm = async () => {
    // 1. Instantly log it on the frontend (FAST PATH)
    const txn = await voiceService.logCredit(extracted);
    setRecordedTxn(txn);
    setState('RECORDED');

    // Reset after a while
    setTimeout(() => {
      setState('IDLE');
      setExtracted(null);
      setRecordedTxn(null);
    }, 5000);
  };

  return (
    <div className="bg-white rounded-3xl shadow-float p-6 w-[360px] border border-sage-100 relative overflow-hidden">
      <AnimatePresence mode="wait">
        {state === 'IDLE' && (
          <motion.div
            key="idle"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex flex-col items-center justify-center py-4"
          >
            <button 
              onClick={startRecording}
              className="w-20 h-20 rounded-full bg-gradient-sage text-sage-600 shadow-soft flex items-center justify-center hover:scale-105 transition-transform relative group"
            >
              <div className="absolute inset-0 rounded-full bg-sage-200 opacity-0 group-hover:animate-ping-slow" />
              <Mic className="w-8 h-8 relative z-10" />
            </button>
            <p className="mt-4 text-ink-500 font-medium">Tap to record credit</p>
          </motion.div>
        )}

        {state === 'LISTENING' && (
          <motion.div
            key="listening"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-4"
          >
            <div className="flex items-center gap-1.5 h-20">
              {[1, 2, 3, 4, 5].map((i) => (
                <motion.div
                  key={i}
                  className="w-1.5 bg-sage-500 rounded-full"
                  animate={{ height: [12, 40, 12] }}
                  transition={{
                    repeat: Infinity,
                    duration: 0.8,
                    delay: i * 0.1,
                    ease: "easeInOut"
                  }}
                />
              ))}
            </div>
            <p className="mt-4 text-sage-600 font-medium animate-pulse">Listening...</p>
          </motion.div>
        )}

        {state === 'UNDERSTANDING' && (
          <motion.div
            key="understanding"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-10"
          >
            <div className="w-8 h-8 border-3 border-sage-200 border-t-sage-500 rounded-full animate-spin" />
            <p className="mt-4 text-ink-500 font-medium">Understanding...</p>
          </motion.div>
        )}

        {state === 'CONFIRM' && extracted && (
          <motion.div
            key="confirm"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex flex-col"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-teal-50 flex items-center justify-center text-sage-600">
                <Mic className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-semibold text-ink-800">Confirm details</h4>
                <p className="text-xs text-ink-400">Please review before saving</p>
              </div>
            </div>

            <div className="bg-cream-50 rounded-xl p-4 mb-5 space-y-3">
              <div className="flex justify-between">
                <span className="text-ink-400 text-sm">Customer</span>
                <span className="font-medium text-ink-800">{extracted.customer_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-400 text-sm">Amount</span>
                <span className="font-semibold text-danger text-lg">₹{extracted.amount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-400 text-sm">Items</span>
                <span className="font-medium text-ink-700">{extracted.items.join(', ')}</span>
              </div>
            </div>

            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => setState('IDLE')}>Edit</Button>
              <Button variant="primary" className="flex-1" onClick={handleConfirm}>Confirm Credit</Button>
            </div>
          </motion.div>
        )}

        {state === 'RECORDED' && recordedTxn && (
          <motion.div
            key="recorded"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center text-center py-6"
          >
            <div className="w-16 h-16 rounded-full bg-positive/10 flex items-center justify-center mb-4 text-positive">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-semibold text-ink-800 mb-1">Credit Recorded</h3>
            <p className="text-sm text-ink-500 mb-6">
              <span className="font-medium">{recordedTxn.customer_name || 'Customer'}</span>'s account credited with <span className="font-medium">₹{recordedTxn.amount}</span>.
            </p>
            
            {/* The crucial background sync indicator */}
            <StatusBadge status={recordedTxn.sync_status} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
