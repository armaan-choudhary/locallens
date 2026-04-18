import React from 'react';
import type { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({ children, className = '' }) => {
  return (
    <span className={`bg-card shadow-sm border border-border rounded-4 px-2 py-[2px] font-mono text-[11px] text-textMuted ${className}`}>
      {children}
    </span>
  );
};

export default Badge;
