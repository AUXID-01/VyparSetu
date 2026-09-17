import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  noPadding?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, className = '', noPadding = false, ...props }) => {
  return (
    <div 
      className={`bg-white rounded-2xl shadow-card border border-cream-200 overflow-hidden ${noPadding ? '' : 'p-5 sm:p-6'} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
