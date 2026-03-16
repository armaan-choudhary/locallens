import React from 'react';

interface ProgressBarProps {
  progress: number;
  label?: string;
  subLabel?: string;
  isIndeterminate?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showPercentage?: boolean;
}

/** Linear progress indicator with support for labels and indeterminate state */
const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  label,
  subLabel,
  isIndeterminate = false,
  size = 'md',
  showPercentage = false,
}) => {
  const sizeClasses = {
    sm: 'h-[2px]',
    md: 'h-[4px]',
    lg: 'h-[8px]',
  };

  return (
    <div className="w-full flex flex-col gap-2">
      {(label || showPercentage) && (
        <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-wider">
          <span className="text-muted5">{label}</span>
          {showPercentage && !isIndeterminate && (
            <span className="font-bold text-white">{Math.round(progress)}%</span>
          )}
        </div>
      )}
      
      <div className={`w-full ${sizeClasses[size]} bg-white/5 rounded-full overflow-hidden border border-white/5 relative`}>
        {isIndeterminate ? (
          <div className={`absolute top-0 bottom-0 left-0 w-1/3 bg-white shadow-[0_0_12px_rgba(255,255,255,0.2)] rounded-full animate-indeterminate-progress`} />
        ) : (
          <div 
            className={`h-full bg-white shadow-[0_0_12px_rgba(255,255,255,0.2)] rounded-full transition-all duration-500 ease-out`}
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        )}
      </div>

      {subLabel && (
        <div className="font-mono text-[9px] text-muted4 italic">
          {subLabel}
        </div>
      )}
    </div>
  );
};

export default ProgressBar;
