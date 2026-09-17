import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Check, X } from 'lucide-react';
import { useEffect } from 'react';

export interface ToastData {
  id: string;
  title: string;
  subtitle: string;
  meta?: string;
  secondary?: string;
}

interface ToastProps {
  toast: ToastData | null;
  onDismiss: () => void;
}

export function Toast({ toast, onDismiss }: ToastProps) {
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(onDismiss, 4500);
    return () => clearTimeout(timer);
  }, [toast, onDismiss]);

  return (
    <AnimatePresence>
      {toast && (
        <motion.div
          initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 10, scale: 0.98 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="fixed bottom-6 right-6 z-50 w-full max-w-sm"
        >
          <div className="rounded-xl border border-ink-200 bg-white p-4 shadow-float">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-sage-100">
                <Check size={18} className="text-sage-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-ink-700">{toast.title}</p>
                <p className="text-sm text-ink-400">{toast.subtitle}</p>
                {toast.meta && <p className="mt-0.5 text-xs text-ink-300">{toast.meta}</p>}
                {toast.secondary && (
                  <p className="mt-2 flex items-center gap-1.5 text-xs text-teal-600">
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-teal-400 opacity-75" />
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-teal-500" />
                    </span>
                    {toast.secondary}
                  </p>
                )}
              </div>
              <button
                onClick={onDismiss}
                className="rounded-lg p-1 text-ink-300 transition-colors hover:text-ink-500"
                aria-label="Dismiss notification"
              >
                <X size={16} />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
