import { motion, useReducedMotion } from 'framer-motion';

interface AnimatedNumberProps {
  value: number;
  prefix?: string;
  suffix?: string;
  className?: string;
  decimals?: number;
}

export function AnimatedNumber({ value, prefix = '', suffix = '', className, decimals = 0 }: AnimatedNumberProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.span
      className={className}
      initial={shouldReduceMotion ? false : { opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Counter value={value} prefix={prefix} suffix={suffix} decimals={decimals} />
    </motion.span>
  );
}

function Counter({ value, prefix, suffix, decimals }: Omit<AnimatedNumberProps, 'className'>) {
  const shouldReduceMotion = useReducedMotion();
  const display = value.toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });

  if (shouldReduceMotion) {
    return (
      <>
        {prefix}
        {display}
        {suffix}
      </>
    );
  }

  return (
    <motion.span
      key={value}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
      {prefix}
      {display}
      {suffix}
    </motion.span>
  );
}
