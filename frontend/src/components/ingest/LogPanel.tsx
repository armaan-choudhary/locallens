import React, { useEffect, useRef } from 'react';

interface LogPanelProps {
  logs: string[];
}

const LogPanel: React.FC<LogPanelProps> = ({ logs }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="mt-4">
      <div 
        ref={scrollRef}
        className="bg-base border border-border rounded-6 p-3 max-h-[120px] overflow-y-auto font-mono text-[12px] text-muted5 flex flex-col gap-1"
      >
        {logs.map((log, i) => {
          let prefix = '⟳';
          if (log.includes('Complete') || log.includes('Done') || log.includes('✓')) prefix = '✓';
          if (log.includes('Error') || log.includes('Failed') || log.includes('✗')) prefix = '✗';
          
          return (
            <div key={i} className="flex gap-2">
              <span className="shrink-0">{prefix}</span>
              <span>{log}</span>
            </div>
          );
        })}
        {logs.length === 0 && <div className="italic">Waiting for logs...</div>}
      </div>
    </div>
  );
};

export default LogPanel;
