import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, CheckCircle2, Square } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';
import { apiClient } from '../../services/apiClient';
import { useAuth } from '../../contexts/AuthContext';

export const VoiceRecorder: React.FC = () => {
  const [state, setState] = useState<'IDLE' | 'LISTENING' | 'UNDERSTANDING' | 'RECORDED' | 'ERROR'>('IDLE');
  const [recordedTxn, setRecordedTxn] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState('');
  
  const { auth } = useAuth();
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        await processAudio(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setState('LISTENING');
    } catch (err) {
      console.error("Error accessing microphone:", err);
      setErrorMsg("Could not access microphone");
      setState('ERROR');
      setTimeout(() => setState('IDLE'), 3000);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && state === 'LISTENING') {
      mediaRecorderRef.current.stop();
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    setState('UNDERSTANDING');
    try {
      const formData = new FormData();
      if (!auth.merchantId) throw new Error("Not authenticated");
      
      formData.append('merchant_id', auth.merchantId);
      // Fastapi expects a file named 'audio'
      formData.append('audio', audioBlob, 'recording.webm');
      
      const res = await apiClient.post('/voice/log-credit-from-audio', formData, true);
      
      if (res.data) {
        setRecordedTxn(res.data);
        setState('RECORDED');
        
        if (res.data.confirmation_audio_b64) {
          const audio = new Audio("data:audio/wav;base64," + res.data.confirmation_audio_b64);
          audio.play();
        }
        
        setTimeout(() => {
          setState('IDLE');
          setRecordedTxn(null);
        }, 5000);
      }
    } catch (err: any) {
      console.error("Audio processing failed:", err);
      setErrorMsg(err.message || "Failed to process audio");
      setState('ERROR');
      setTimeout(() => setState('IDLE'), 4000);
    }
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
                  transition={{ repeat: Infinity, duration: 0.8, delay: i * 0.1, ease: "easeInOut" }}
                />
              ))}
            </div>
            
            <button 
              onClick={stopRecording}
              className="mt-6 w-12 h-12 rounded-full bg-danger/10 text-danger flex items-center justify-center hover:bg-danger/20 transition-colors"
            >
              <Square className="w-4 h-4 fill-current" />
            </button>
            <p className="mt-2 text-sage-600 font-medium text-sm">Tap to stop</p>
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
            <p className="mt-4 text-ink-500 font-medium text-sm">Transcribing Audio & Extracting...</p>
          </motion.div>
        )}

        {state === 'ERROR' && (
          <motion.div
            key="error"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center py-4 text-center"
          >
            <div className="w-12 h-12 rounded-full bg-danger/10 flex items-center justify-center mb-3 text-danger">
              <span className="text-xl font-bold">!</span>
            </div>
            <p className="text-danger font-semibold text-sm mb-2">Processing Error</p>
            <div className="w-full bg-danger/5 p-3 rounded-xl border border-danger/20 text-left mb-4 text-xs text-danger break-words max-h-28 overflow-y-auto">
              {errorMsg}
            </div>
            <button
              onClick={() => { setState('IDLE'); setErrorMsg(''); }}
              className="text-xs font-medium text-ink-600 hover:text-ink-900 underline"
            >
              Try Again
            </button>
          </motion.div>
        )}

        {state === 'RECORDED' && recordedTxn && (
          <motion.div
            key="recorded"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center text-center py-4"
          >
            <div className="w-12 h-12 rounded-full bg-positive/10 flex items-center justify-center mb-2 text-positive">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-ink-800 mb-2">Credit Recorded</h3>
            
            {recordedTxn.transcript && (
              <div className="w-full bg-sage-50 p-2.5 rounded-xl border border-sage-200 text-left mb-3">
                <span className="text-[10px] uppercase tracking-wider font-semibold text-sage-600 block mb-0.5">Real-Time Transcription</span>
                <p className="text-xs text-ink-800 italic">"{recordedTxn.transcript}"</p>
              </div>
            )}

            {recordedTxn.extracted && (
              <div className="flex flex-wrap gap-1.5 justify-center mb-3 text-xs font-medium">
                {recordedTxn.extracted.customer_name && (
                  <span className="bg-sage-100 text-sage-800 px-2 py-0.5 rounded-md">👤 {recordedTxn.extracted.customer_name}</span>
                )}
                {recordedTxn.extracted.amount > 0 && (
                  <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-md">₹{recordedTxn.extracted.amount}</span>
                )}
                {recordedTxn.extracted.items?.map((item: string, idx: number) => (
                  <span key={idx} className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded-md">🛒 {item}</span>
                ))}
              </div>
            )}

            <p className="text-xs text-ink-500 mb-3">
              New balance: <span className="font-semibold text-ink-800">₹{recordedTxn.new_balance}</span>
            </p>
            <StatusBadge status="RECORDED" label="Recorded" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
