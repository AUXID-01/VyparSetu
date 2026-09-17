import { motion, useReducedMotion } from 'framer-motion';
import { CheckCircle2 } from 'lucide-react';

interface AnimatedCheckProps {
  size?: number;
  className?: string;
}

export function AnimatedCheck({ size = 24, className = '' }: AnimatedCheckProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={shouldReduceMotion ? false : { scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={shouldReduceMotion ? { duration: 0.01 } : { type: 'spring', stiffness: 260, damping: 20 }}
      className={className}
    >
      <CheckCircle2 size={size} className="text-sage-500" />
    </motion.div>
  );
}
