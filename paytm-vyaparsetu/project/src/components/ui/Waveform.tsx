import { motion, useReducedMotion } from 'framer-motion';

interface WaveformProps {
  active: boolean;
  bars?: number;
}

export function Waveform({ active, bars = 5 }: WaveformProps) {
  const shouldReduceMotion = useReducedMotion();

  if (!active) {
    return (
      <div className="flex items-center justify-center gap-1 h-12">
        {Array.from({ length: bars }).map((_, i) => (
          <div key={i} className="h-1 w-1 rounded-full bg-ink-200" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center gap-1.5 h-12">
      {Array.from({ length: bars }).map((_, i) => (
        <motion.div
          key={i}
          className="w-1 rounded-full bg-sage-500"
          initial={{ height: 4 }}
          animate={
            shouldReduceMotion
              ? { height: 20 }
              : {
                  height: [8, 32, 12, 28, 6],
                }
          }
          transition={{
            duration: 0.8,
            repeat: Infinity,
            repeatType: 'reverse',
            delay: i * 0.1,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  );
}
