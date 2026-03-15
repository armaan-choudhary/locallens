import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDocuments } from '../api/client';
import Button from '../components/shared/Button';

const OnboardingPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkDocs = async () => {
      const docs = await getDocuments();
      if (docs && docs.length > 0) {
        navigate('/ingest');
      } else {
        setLoading(false);
      }
    };
    checkDocs();
  }, [navigate]);

  if (loading) return null;

  const features = [
    {
      title: '100% Offline',
      desc: 'No data leaves your device.'
    },
    {
      title: 'Verified Citations',
      desc: 'Every answer traced to exact page coordinates.'
    },
    {
      title: 'Text + Images',
      desc: 'Searches diagrams and scans, not just plain text.'
    }
  ];

  return (
    <div className="max-w-[420px] mx-auto pt-[96px] animate-in fade-in duration-700">
      <div className="mb-2">
        <h1 className="font-inter font-medium text-[22px] text-white">LocalLens</h1>
      </div>
      
      <div className="mb-[32px]">
        <p className="font-inter font-normal text-[14px] text-muted7">
          Your private document search.<br />
          Everything runs locally on your machine.
        </p>
      </div>
      
      <div className="border-t border-[#1c1c1f] mb-[32px]" />
      
      <div className="flex flex-col mb-[32px]">
        {features.map((f, i) => (
          <div key={i} className="flex gap-3 py-[14px] border-b border-raised last:border-0 items-start">
            <span className="text-muted4 text-[14px] mt-[3px]">→</span>
            <div className="flex flex-col">
              <span className="text-muted14 font-medium text-[14px]">{f.title}</span>
              <span className="text-muted7 font-normal text-[13px]">{f.desc}</span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="border-t border-[#1c1c1f] mb-[32px]" />
      
      <Button 
        variant="primary" 
        className="w-full h-[42px]"
        onClick={() => navigate('/ingest')}
      >
        Import Your First PDF
      </Button>
      
      <div className="mt-6 text-center text-muted4 text-[12px]">
        No accounts. No API keys. No internet required.
      </div>
    </div>
  );
};

export default OnboardingPage;
