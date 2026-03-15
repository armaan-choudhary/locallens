import React, { useEffect, useRef } from 'react';
import { Terminal } from 'lucide-react';

interface LogPanelProps {
  logs: string[];
}

interface ParsedLine {
  type: 'ok' | 'err' | 'info' | 'dim';
  text: string;
}

const parseLine = (log: string): ParsedLine => {
  if (/✓|done|complete|stored|success/i.test(log)) return { type: 'ok',   text: log };
  if (/✗|fail|error/i.test(log))                    return { type: 'err',  text: log };
  if (/embed|ocr|extract|parsing|indexing/i.test(log)) return { type: 'info', text: log };
  return { type: 'dim', text: log };
};

const colourMap = {
  ok:   'terminal-line-ok',
  err:  'terminal-line-err',
  info: 'terminal-line-info',
  dim:  'terminal-line-dim',
};

const LogPanel: React.FC<LogPanelProps> = ({ logs }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <Terminal className="w-[12px] h-[12px] text-muted4" />
        <span className="font-mono text-[9px] text-muted4 uppercase tracking-[0.12em]">
          Pipeline Log
        </span>
      </div>
      <div ref={scrollRef} className="terminal-panel">
        {logs.length === 0 ? (
          <span className="terminal-line-dim italic">Waiting for ingestion…</span>
        ) : (
          logs.map((log, i) => {
            const { type, text } = parseLine(log);
            return (
              <div key={i} className={colourMap[type]}>
                {text}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default LogPanel;
