import React from 'react';

interface ProgressBarProps {
  progress: number;
  label?: string;
  subLabel?: string;
  isIndeterminate?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showPercentage?: boolean;
  color?: 'success' | 'error' | 'accent' | 'default';
}

/** Linear progress indicator with support for labels and indeterminate state */
const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  label,
  subLabel,
  isIndeterminate = false,
  size = 'md',
  showPercentage = false,
  color = 'default',
}) => {
  const sizeClasses = {
    sm: 'h-[2px]',
    md: 'h-[4px]',
    lg: 'h-[8px]',
  };

  const colorClasses = {
    success: 'bg-success shadow-glow',
    error: 'bg-error shadow-glow',
    accent: 'bg-accent shadow-glow',
    default: 'bg-accent shadow-glow'
  };

  const bgClass = colorClasses[color] || colorClasses.default;

  return (
    <div className="w-full flex flex-col gap-2">
      {(label || showPercentage) && (
        <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-wider">
          <span className="text-textMuted">{label}</span>
          {showPercentage && !isIndeterminate && (
            <span className="font-bold text-textPrimary">{Math.round(progress)}%</span>
          )}
        </div>
      )}
      
      <div className={`w-full ${sizeClasses[size]} bg-black/5 rounded-full overflow-hidden border border-black/5 relative`}>
        {isIndeterminate ? (
          <div className={`absolute top-0 bottom-0 left-0 w-1/3 ${bgClass} rounded-full animate-indeterminate-progress`} />
        ) : (
          <div 
            className={`h-full ${bgClass} rounded-full transition-all duration-500 ease-out`}
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        )}
      </div>

      {subLabel && (
        <div className="font-mono text-[9px] text-textMuted italic">
          {subLabel}
        </div>
      )}
    </div>
  );
};

export default ProgressBar;
