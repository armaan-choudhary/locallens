import React from 'react';
import type { ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost';
  size?: 'sm' | 'md';
  loading?: boolean;
  children: ReactNode;
}

const Button: React.FC<ButtonProps> = ({ 
  variant = 'primary', 
  size = 'md', 
  loading = false, 
  children, 
  className = '',
  ...props 
}) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-6 font-medium transition-colors focus:outline-none';
  
  const variants = {
    primary: 'bg-base border border-border text-white hover:bg-raised hover:border-muted4',
    ghost: 'bg-transparent border border-border text-muted7 hover:bg-raised hover:text-muted10',
  };
  
  const sizes = {
    sm: 'h-[30px] px-3 text-[13px]',
    md: 'h-[38px] px-4 text-[14px]',
  };
  
  return (
    <button 
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className} ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
      {children}
    </button>
  );
};

export default Button;
