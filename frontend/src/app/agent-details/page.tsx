"use client";

import React from 'react';
import { useAnalysis } from '@/hooks/useAnalysis';
import { AgentCard } from '@/components/AgentCard';

export default function AgentDetailsPage() {
  const { ticker, setTicker, agents, isAnalyzing, analyzeTicker } = useAnalysis();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) analyzeTicker(ticker);
  };

  const agentKeys = ['fundamentals', 'sentiment', 'technical', 'insider', 'macro'];

  return (
    <main className="pt-24 pb-24 px-margin-mobile md:px-margin-desktop max-w-container-max mx-auto w-full min-h-screen relative z-10">
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
      </div>

      <header className="mb-16 card-enter" style={{ animationDelay: '0.1s' }}>
        <h1 className="font-display-lg-mobile md:font-display-lg text-primary mb-4 italic">Agent Details</h1>
        <p className="font-body-lg text-on-surface-variant max-w-2xl">Deep dive into the specialized RAG agents driving the consensus model. Each agent analyzes a unique vector of market data to construct a comprehensive view.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">
        {agentKeys.map((key) => (
          <div key={key} className="liquid-glass border border-glass-border-dim rounded-xl overflow-hidden shadow-2xl">
            <AgentCard 
              name={key} 
              ticker={ticker} 
              data={agents[key]} 
              isLoading={isAnalyzing} 
            />
          </div>
        ))}
      </div>
    </main>
  );
}
