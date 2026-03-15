import React from 'react';
import { NavLink } from 'react-router-dom';

const Topbar: React.FC = () => {
  return (
    <header className="fixed top-0 left-0 right-0 h-[48px] bg-base border-b border-[#1c1c1f] px-[24px] flex items-center justify-between z-50">
      <div className="flex items-center gap-2">
        <span className="font-inter font-medium text-[14px] text-white tracking-[-0.01em]">LocalLens</span>
      </div>
      
      <nav className="flex items-center gap-1">
        <NavLink 
          to="/ingest" 
          className={({ isActive }) => 
            `px-3 py-1 text-[13px] transition-colors rounded hover:text-muted10 ${isActive ? 'text-white' : 'text-muted5'}`
          }
        >
          Ingest
        </NavLink>
        <NavLink 
          to="/query" 
          className={({ isActive }) => 
            `px-3 py-1 text-[13px] transition-colors rounded hover:text-muted10 ${isActive ? 'text-white' : 'text-muted5'}`
          }
        >
          Search
        </NavLink>
      </nav>
    </header>
  );
};

export default Topbar;
