import React from 'react';

interface IngestionProgressProps {
  filename: string;
  currentPage: number;
  totalPages: number;
  stage: string;
}

const IngestionProgress: React.FC<IngestionProgressProps> = ({ 
  filename, 
  currentPage, 
  totalPages, 
  stage 
}) => {
  const percent = totalPages > 0 ? (currentPage / totalPages) * 100 : 0;
  
  return (
    <div className="w-full flex flex-col items-center justify-center h-[120px]">
      <div className="w-full h-[2px] bg-border relative overflow-hidden">
        <div 
          className="absolute top-0 left-0 h-full bg-muted10 transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
      
      <div className="mt-4 font-mono text-[13px] text-muted5 text-center">
        {stage} {filename} {totalPages > 0 ? `— page ${currentPage} of ${totalPages}` : ''}
      </div>
    </div>
  );
};

export default IngestionProgress;
