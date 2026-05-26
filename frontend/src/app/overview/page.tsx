"use client";

import React from 'react';
import { useAnalysis } from '@/hooks/useAnalysis';
import { SynthesisPanel } from '@/components/SynthesisPanel';
import { NarrativeTracker } from '@/components/NarrativeTracker';

export default function OverviewPage() {
  const { ticker, setTicker, agents, synthesis, isAnalyzing, analyzeTicker } = useAnalysis();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) analyzeTicker(ticker);
  };

  return (
    <main className="pt-24 pb-24 min-h-screen relative overflow-hidden">
      {/* Ambient Background Effect */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden flex items-center justify-center opacity-30">
        <div className="absolute w-[800px] h-[800px] rounded-full bg-primary/5 blur-[120px] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"></div>
        <div className="absolute w-[400px] h-[400px] rounded-full bg-error/5 blur-[80px] top-1/4 left-3/4"></div>
      </div>

      <div className="relative z-10 max-w-container-max mx-auto px-margin-mobile md:px-margin-desktop space-y-gutter">
        {/* Ticker Search Bar Section */}
        <div className="flex flex-col items-center justify-center mb-16 text-center w-full max-w-3xl mx-auto pt-8">
          <form onSubmit={handleSearch} className="flex w-full gap-4 flex-col sm:flex-row">
            <input 
              className="flex-1 bg-surface-overlay border border-glass-border-dim rounded-full px-6 py-4 text-primary font-body-lg focus:outline-none focus:border-primary transition-colors w-full" 
              placeholder="Enter ticker symbol (e.g. AAPL, TSLA, NVDA)" 
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              disabled={isAnalyzing}
            />
            <button 
              type="submit"
              disabled={isAnalyzing}
              className="bg-[#4f46e5] hover:bg-[#4338ca] text-white font-label-caps text-label-caps px-8 py-4 sm:py-0 rounded-full transition-colors flex items-center justify-center whitespace-nowrap disabled:opacity-50"
            >
              {isAnalyzing ? (
                <span className="material-symbols-outlined animate-spin text-[20px]">sync</span>
              ) : (
                'Analyze'
              )}
            </button>
          </form>
          <p className="mt-4 font-label-caps text-on-surface-variant opacity-70">Powered by 5 specialized AI agents</p>
        </div>

        <header className="mb-12">
          <div className="inline-flex items-center justify-center px-4 py-1.5 rounded-full border border-white/20 bg-surface-overlay backdrop-blur-md mb-6">
            <span className="font-label-caps text-label-caps text-primary tracking-widest">Synthesis Panel</span>
          </div>
          <h2 className="font-headline-md text-display-lg-mobile md:text-display-lg text-primary mb-4">Overview</h2>
          <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl">Aggregate intelligence from specialized agents analyzing multiple dimensions.</p>
        </header>

        {synthesis && (
          <SynthesisPanel synthesis={synthesis} agents={agents} />
        )}

        {Object.keys(agents).length > 0 && (
          <div className="bg-surface-overlay backdrop-blur-[50px] rounded-xl p-8 liquid-glass mt-gutter">
            <div className="flex justify-between items-end mb-8 border-b border-glass-border-dim pb-6">
              <div>
                <h3 className="font-headline-md text-[32px] text-primary mb-2">Agent Confidence Matrix</h3>
                <p className="font-body-md text-on-surface-variant">Individual agent scoring distribution (-1.0 to +1.0)</p>
              </div>
            </div>
            <NarrativeTracker agents={agents} />
          </div>
        )}
      </div>
    </main>
  );
}
